from __future__ import annotations

import warnings
from urllib.request import Request

import pytest

from oapi.client import Client


def test_authenticate_request_adds_basic_authentication() -> None:
    client: Client = Client(user="alice", password="secret")
    request: Request = Request("http://example.com/foo")
    client._authenticate_request(request)
    assert request.get_header("Authorization") == "Basic YWxpY2U6c2VjcmV0"


def test_authenticate_request_adds_bearer_token() -> None:
    client: Client = Client(bearer_token="tok123")
    request: Request = Request("http://example.com/foo")
    client._authenticate_request(request)
    assert request.get_header("Authorization") == "Bearer tok123"


def test_authenticate_request_prefers_bearer_over_basic_when_both_set() -> (
    None
):
    """
    `_authenticate_request` applies Basic auth first, then Bearer --
    since both call `add_header("Authorization", ...)`, the second call
    (Bearer) wins for the real, final header value if both `user`/
    `password` and `bearer_token` are configured together.
    """
    client: Client = Client(
        user="alice", password="secret", bearer_token="tok123"
    )
    request: Request = Request("http://example.com/foo")
    client._authenticate_request(request)
    assert request.get_header("Authorization") == "Bearer tok123"


def test_api_key_authenticate_request_in_header() -> None:
    client: Client = Client(
        api_key="key123", api_key_name="X-API-KEY", api_key_in="header"
    )
    request: Request = Request("http://example.com/foo")
    client._authenticate_request(request)
    assert request.get_header("X-api-key") == "key123"


def test_api_key_authenticate_request_in_query_appends_to_existing() -> None:
    client: Client = Client(
        api_key="key123", api_key_name="apikey", api_key_in="query"
    )
    request: Request = Request("http://example.com/foo?a=1")
    client._authenticate_request(request)
    assert request.full_url == "http://example.com/foo?a=1&apikey=key123"


def test_api_key_authenticate_request_in_query_without_existing_query() -> (
    None
):
    client: Client = Client(
        api_key="key123", api_key_name="apikey", api_key_in="query"
    )
    request: Request = Request("http://example.com/foo")
    client._authenticate_request(request)
    assert request.full_url == "http://example.com/foo?apikey=key123"


def test_api_key_authenticate_request_in_cookie_without_existing_cookie() -> (
    None
):
    client: Client = Client(
        api_key="key123", api_key_name="session", api_key_in="cookie"
    )
    request: Request = Request("http://example.com/foo")
    client._authenticate_request(request)
    assert request.get_header("Cookie") == "session=key123"


def test_api_key_authenticate_request_in_cookie_appends_to_existing() -> None:
    client: Client = Client(
        api_key="key123", api_key_name="session", api_key_in="cookie"
    )
    request: Request = Request(
        "http://example.com/foo", headers={"Cookie": "existing=1"}
    )
    client._authenticate_request(request)
    assert request.get_header("Cookie") == "existing=1; session=key123"


def test_api_key_authenticate_request_in_query_requires_a_key() -> None:
    client: Client = Client(api_key_in="query")
    with pytest.raises(RuntimeError, match="No API key"):
        client._api_key_authenticate_request(Request("http://example.com/foo"))


def test_api_key_authenticate_request_in_header_requires_a_key() -> None:
    client: Client = Client(api_key_in="header")
    with pytest.raises(RuntimeError, match="No API key"):
        client._api_key_authenticate_request(Request("http://example.com/foo"))


def test_api_key_authenticate_request_rejects_an_invalid_api_key_in() -> None:
    """
    `Client.__init__` validates `api_key_in` up front, but
    `_api_key_authenticate_request` re-validates it independently (its
    `else` branch double-checks `self.api_key_in == "header"`) --
    reachable by mutating the attribute directly after construction,
    bypassing `__init__`'s guard.
    """
    client: Client = Client(api_key="x")
    client.api_key_in = "bogus"  # type: ignore[assignment]
    with pytest.raises(ValueError, match="bogus"):
        client._api_key_authenticate_request(Request("http://example.com/foo"))


def test_oauth2_authenticate_request_warns_for_unconfigured_flows() -> None:
    client: Client = Client(
        oauth2_flows=(
            "implicit",
            "password",
            "clientCredentials",
            "authorizationCode",
        )
    )
    request: Request = Request("http://example.com/foo")
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        client._oauth2_authenticate_request(request)
    messages: list[str] = [str(warning.message) for warning in caught]
    assert len(messages) == 4
    assert any("implicit" in message for message in messages)
    assert any(
        '"password" OAuth2 flow requires' in message for message in messages
    )
    assert any(
        '"clientCredentials" OAuth2 flow requires' in message
        for message in messages
    )
    assert any("authorizationCode" in message for message in messages)
    assert request.get_header("Authorization") is None


def test_oauth2_authenticate_request_does_nothing_when_unconfigured() -> None:
    client: Client = Client()
    request: Request = Request("http://example.com/foo")
    client._oauth2_authenticate_request(request)
    assert request.get_header("Authorization") is None
