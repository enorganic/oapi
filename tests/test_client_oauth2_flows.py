from __future__ import annotations

import json as json_module
from urllib.error import HTTPError

import pytest
from servers import Response, http_test_server

from oapi.client import Client


def test_oauth2_password_flow_authenticates_and_caches_the_token() -> None:
    with http_test_server(
        responses={
            ("POST", "/token"): Response(
                status=200,
                body=json_module.dumps(
                    {
                        "token_type": "Bearer",
                        "access_token": "tok-pw",
                        "expires_in": 3600,
                    }
                ).encode(),
            ),
            ("GET", "/protected"): Response(status=200, body=b'{"ok": true}'),
        }
    ) as server:
        client: Client = Client(
            url=server.url,
            oauth2_client_id="cid",
            oauth2_username="user1",
            oauth2_password="pw1",
            oauth2_token_url=server.url + "/token",
        )
        with client.request("/protected", "GET") as response:
            response.read()
        assert (
            server.requests[-1].headers.get("Authorization") == "Bearer tok-pw"
        )
        token_requests_before: int = len(
            [
                request
                for request in server.requests
                if request.path == "/token"
            ]
        )
        with client.request("/protected", "GET") as response:
            response.read()
        token_requests_after: int = len(
            [
                request
                for request in server.requests
                if request.path == "/token"
            ]
        )
        # A second request reuses the cached token: no second POST /token.
        assert token_requests_after == token_requests_before


def test_oauth2_password_flow_requires_a_username() -> None:
    client: Client = Client(
        oauth2_token_url="http://example.com/token",
        oauth2_password="pw1",
    )
    with pytest.raises(RuntimeError, match="username"):
        client._request_oauth2_password_authorization()


def test_oauth2_password_flow_requires_a_password() -> None:
    client: Client = Client(
        oauth2_token_url="http://example.com/token",
        oauth2_username="user1",
    )
    with pytest.raises(RuntimeError, match="password"):
        client._request_oauth2_password_authorization()


def test_oauth2_password_flow_requires_a_token_url() -> None:
    client: Client = Client(
        open_id_connect_url="",
        oauth2_username="user1",
        oauth2_password="pw1",
    )
    with pytest.raises(RuntimeError, match="token URL"):
        client._request_oauth2_password_authorization()


def test_oauth2_password_flow_includes_the_configured_scope() -> None:
    with http_test_server(
        responses={
            ("POST", "/token"): Response(
                status=200,
                body=json_module.dumps(
                    {
                        "token_type": "Bearer",
                        "access_token": "t",
                        "expires_in": 3600,
                    }
                ).encode(),
            ),
        }
    ) as server:
        client: Client = Client(
            oauth2_client_id="cid",
            oauth2_username="u",
            oauth2_password="p",
            oauth2_token_url=server.url + "/token",
            oauth2_scope="read write",
        )
        with client._request_oauth2_password_authorization() as response:
            response.read()
        assert b"scope=read%20write" in server.requests[0].body


def test_oauth2_password_flow_follows_a_location_header_on_http_error() -> (
    None
):
    """
    On an `HTTPError`, `_request_oauth2_password_authorization` checks
    the error response's `Location` header and, if it differs from the
    current `oauth2_token_url`, updates `oauth2_token_url` and retries
    against the new URL. This uses the raw header value as the next
    request's full URL directly (no relative-URL resolution), so a real
    exercise of this branch needs an *absolute* URL in `Location`.
    """
    with http_test_server(responses={}) as server:
        server.responses[("POST", "/token")] = Response(
            status=401, headers={"Location": server.url + "/token2"}
        )
        server.responses[("POST", "/token2")] = Response(
            status=200,
            body=json_module.dumps(
                {
                    "token_type": "Bearer",
                    "access_token": "moved-token",
                    "expires_in": 3600,
                }
            ).encode(),
        )
        client: Client = Client(
            oauth2_client_id="cid",
            oauth2_username="u",
            oauth2_password="p",
            oauth2_token_url=server.url + "/token",
        )
        with client._request_oauth2_password_authorization() as response:
            data: bytes | str = response.read()
        assert b"moved-token" in (
            data if isinstance(data, bytes) else data.encode()
        )
        assert client.oauth2_token_url == server.url + "/token2"


def test_oauth2_password_flow_reraises_an_http_error_without_a_redirect() -> (
    None
):
    """
    When the token endpoint's error response has no `Location` header
    (or one equal to the current `oauth2_token_url`), there is nothing
    to retry against, and the original `HTTPError` is re-raised as-is.
    """
    with http_test_server(
        responses={("POST", "/token"): Response(status=401, body=b"nope")}
    ) as server:
        client: Client = Client(
            oauth2_client_id="cid",
            oauth2_username="u",
            oauth2_password="p",
            oauth2_token_url=server.url + "/token",
        )
        with pytest.raises(HTTPError) as excinfo:
            client._request_oauth2_password_authorization()
        assert excinfo.value.code == 401


def test_oauth2_client_credentials_flow_with_explicit_timeout() -> None:
    """
    `_request_oauth2_client_credentials_authorization` passes
    `timeout=self.timeout` to the opener unconditionally -- unlike
    `_request_oauth2_password_authorization`, it has no fallback for
    `self.timeout == 0` (the `Client` default). A `timeout=0` value
    means "non-blocking socket" to the stdlib socket layer, not "no
    timeout" -- so this flow only works with a real, non-zero `timeout`.
    See `test_oauth2_client_credentials_flow_with_default_timeout_fails`
    below for the real, current, broken default-timeout behavior.
    """
    with http_test_server(
        responses={
            ("POST", "/token"): Response(
                status=200,
                body=json_module.dumps(
                    {
                        "token_type": "Bearer",
                        "access_token": "tok-cc",
                        "expires_in": 3600,
                    }
                ).encode(),
            ),
            ("GET", "/protected"): Response(status=200, body=b'{"ok": true}'),
        }
    ) as server:
        client: Client = Client(
            url=server.url,
            oauth2_client_id="cid",
            oauth2_client_secret="csecret",
            oauth2_token_url=server.url + "/token",
            timeout=30,
        )
        with client.request("/protected", "GET") as response:
            response.read()
        assert (
            server.requests[-1].headers.get("Authorization") == "Bearer tok-cc"
        )
        assert (
            "grant_type=client_credentials" in server.requests[0].body.decode()
        )


def test_oauth2_client_credentials_flow_with_default_timeout_fails() -> None:
    """
    Documents a real, verified bug: with the `Client` default
    `timeout=0`, `_request_oauth2_client_credentials_authorization`
    passes `timeout=0` straight to `OpenerDirector.open`, which
    ultimately reaches `socket.create_connection` with a `0` timeout --
    Python's socket API treats `settimeout(0)` as "set the socket to
    non-blocking mode", not "no timeout", so the connect step raises
    immediately rather than actually connecting. Confirmed against a
    real local server (not a network flake): the exact same client
    configuration succeeds when constructed with a non-zero `timeout`
    (see the test above). This is real, current, unfixed behavior --
    documented here, not corrected.
    """
    with http_test_server(
        responses={
            ("POST", "/token"): Response(status=200, body=b"{}"),
        }
    ) as server:
        client: Client = Client(
            url=server.url,
            oauth2_client_id="cid",
            oauth2_client_secret="csecret",
            oauth2_token_url=server.url + "/token",
        )
        with pytest.raises(OSError):
            client._request_oauth2_client_credentials_authorization()


def test_oauth2_client_credentials_flow_requires_a_client_id() -> None:
    client: Client = Client(
        oauth2_token_url="http://example.com/token",
        oauth2_client_secret="csecret",
    )
    with pytest.raises(RuntimeError, match="client ID"):
        client._request_oauth2_client_credentials_authorization()


def test_oauth2_client_credentials_flow_requires_a_client_secret() -> None:
    client: Client = Client(
        oauth2_token_url="http://example.com/token",
        oauth2_client_id="cid",
    )
    with pytest.raises(RuntimeError, match="client secret"):
        client._request_oauth2_client_credentials_authorization()


def test_oauth2_client_credentials_flow_requires_a_token_url() -> None:
    client: Client = Client(
        open_id_connect_url="",
        oauth2_client_id="cid",
        oauth2_client_secret="s",
    )
    with pytest.raises(RuntimeError, match="token URL"):
        client._request_oauth2_client_credentials_authorization()


def test_oauth2_client_credentials_flow_includes_the_configured_scope() -> (
    None
):
    with http_test_server(
        responses={
            ("POST", "/token"): Response(
                status=200,
                body=json_module.dumps(
                    {
                        "token_type": "Bearer",
                        "access_token": "t",
                        "expires_in": 3600,
                    }
                ).encode(),
            ),
        }
    ) as server:
        client: Client = Client(
            oauth2_client_id="cid",
            oauth2_client_secret="s",
            oauth2_token_url=server.url + "/token",
            oauth2_scope="read",
            timeout=30,
        )
        with client._request_oauth2_client_credentials_authorization() as (
            response
        ):
            response.read()
        assert b"scope=read" in server.requests[0].body


def test_oauth2_client_credentials_flow_follows_a_location_header() -> None:
    with http_test_server(responses={}) as server:
        server.responses[("POST", "/token")] = Response(
            status=401, headers={"Location": server.url + "/token2"}
        )
        server.responses[("POST", "/token2")] = Response(
            status=200,
            body=json_module.dumps(
                {
                    "token_type": "Bearer",
                    "access_token": "moved-token-cc",
                    "expires_in": 3600,
                }
            ).encode(),
        )
        client: Client = Client(
            oauth2_client_id="cid",
            oauth2_client_secret="s",
            oauth2_token_url=server.url + "/token",
            timeout=30,
        )
        with client._request_oauth2_client_credentials_authorization() as (
            response
        ):
            data: bytes | str = response.read()
        assert b"moved-token-cc" in (
            data if isinstance(data, bytes) else data.encode()
        )
        assert client.oauth2_token_url == server.url + "/token2"


def test_oauth2_client_credentials_flow_reraises_without_a_redirect() -> None:
    with http_test_server(
        responses={("POST", "/token"): Response(status=401, body=b"nope")}
    ) as server:
        client: Client = Client(
            oauth2_client_id="cid",
            oauth2_client_secret="s",
            oauth2_token_url=server.url + "/token",
            timeout=30,
        )
        with pytest.raises(HTTPError) as excinfo:
            client._request_oauth2_client_credentials_authorization()
        assert excinfo.value.code == 401


def test_get_oauth2_token_url_returns_the_explicit_url_unchanged() -> None:
    client: Client = Client(oauth2_token_url="http://example.com/token")
    assert client._get_oauth2_token_url() == "http://example.com/token"


def test_get_oauth2_token_url_discovers_via_oidc_with_timeout() -> None:
    """
    Like the client-credentials flow, OIDC discovery
    (`urlopen(url, timeout=self.timeout)`) passes `self.timeout`
    straight through with no fallback for `0` -- exercised here with an
    explicit non-zero `timeout` to get real, working coverage of the
    discovery logic itself (parsing `token_endpoint` out of the
    real HTTP response and caching it onto `self.oauth2_token_url`).
    """
    with http_test_server(
        responses={
            ("GET", "/.well-known/openid-configuration"): Response(
                status=200,
                body=json_module.dumps(
                    {"token_endpoint": "http://example.com/discovered"}
                ).encode(),
            ),
        }
    ) as server:
        client: Client = Client(url=server.url, timeout=30)
        token_url: str | None = client._get_oauth2_token_url()
        assert token_url == "http://example.com/discovered"
        # Cached onto the client -- a second call does not re-fetch.
        assert len(server.requests) == 1
        client._get_oauth2_token_url()
        assert len(server.requests) == 1


def test_get_oauth2_token_url_with_default_timeout_fails() -> None:
    """
    Documents the same real, verified `timeout=0` bug as
    `test_oauth2_client_credentials_flow_with_default_timeout_fails`,
    for OIDC discovery's own real network call.
    """
    with http_test_server(
        responses={
            ("GET", "/.well-known/openid-configuration"): Response(
                status=200, body=b"{}"
            ),
        }
    ) as server:
        client: Client = Client(url=server.url)
        with pytest.raises(OSError):
            client._get_oauth2_token_url()
