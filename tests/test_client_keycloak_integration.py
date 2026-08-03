from __future__ import annotations

import json
from urllib.error import HTTPError

import pytest

from oapi.client import Client


def _token_url(keycloak_url: str) -> str:
    return f"{keycloak_url}/realms/oapi-test/protocol/openid-connect/token"


def _oidc_discovery_url(keycloak_url: str) -> str:
    return f"{keycloak_url}/realms/oapi-test/.well-known/openid-configuration"


def test_oauth2_password_grant_against_a_real_keycloak(
    keycloak_url: str,
) -> None:
    """
    `password-grant-client` (a real, *public* Keycloak client, per
    `tests/keycloak/realm.json`) works with `oapi`'s password-grant
    implementation as-is: `_request_oauth2_password_authorization`
    never sends a `client_secret`, so the OAuth2 spec requires the
    client be public (or otherwise not require client authentication)
    for this flow to succeed against a real, spec-compliant server.
    """
    client: Client = Client(
        oauth2_client_id="password-grant-client",
        oauth2_username="testuser",
        oauth2_password="testpassword",
        oauth2_token_url=_token_url(keycloak_url),
        timeout=10,
    )
    with client._request_oauth2_password_authorization() as response:
        token_response: dict[str, object] = json.loads(response.read())
    assert token_response["token_type"] == "Bearer"
    assert isinstance(token_response["access_token"], str)


def test_oauth2_password_grant_rejects_wrong_credentials(
    keycloak_url: str,
) -> None:
    client: Client = Client(
        oauth2_client_id="password-grant-client",
        oauth2_username="testuser",
        oauth2_password="wrong-password",
        oauth2_token_url=_token_url(keycloak_url),
        timeout=10,
    )
    with pytest.raises(HTTPError) as excinfo:
        client._request_oauth2_password_authorization()
    assert excinfo.value.code == 401


def test_oauth2_client_credentials_grant_against_a_real_keycloak(
    keycloak_url: str,
) -> None:
    """
    `client-credentials-client` is a real, *confidential* Keycloak
    client with a service account enabled. `oapi` sends `client_id`/
    `client_secret` as form-body parameters (not HTTP Basic auth) --
    Keycloak's default client authenticator accepts both, so this
    succeeds against a real server without any special configuration.
    """
    client: Client = Client(
        oauth2_client_id="client-credentials-client",
        oauth2_client_secret="test-secret",
        oauth2_token_url=_token_url(keycloak_url),
        timeout=10,
    )
    with client._request_oauth2_client_credentials_authorization() as (
        response
    ):
        token_response: dict[str, object] = json.loads(response.read())
    assert token_response["token_type"] == "Bearer"
    assert isinstance(token_response["access_token"], str)


def test_oauth2_client_credentials_grant_rejects_a_wrong_secret(
    keycloak_url: str,
) -> None:
    client: Client = Client(
        oauth2_client_id="client-credentials-client",
        oauth2_client_secret="wrong-secret",
        oauth2_token_url=_token_url(keycloak_url),
        timeout=10,
    )
    with pytest.raises(HTTPError) as excinfo:
        client._request_oauth2_client_credentials_authorization()
    assert excinfo.value.code == 401


def test_oidc_discovery_derives_the_real_token_url(
    keycloak_url: str,
) -> None:
    client: Client = Client(
        open_id_connect_url=_oidc_discovery_url(keycloak_url),
        timeout=10,
    )
    assert client._get_oauth2_token_url() == _token_url(keycloak_url)


def test_client_credentials_grant_authenticates_a_real_protected_request(
    keycloak_url: str,
) -> None:
    """
    End-to-end: a `Client` configured for the client-credentials flow
    automatically fetches and attaches a real bearer token to a real
    request against Keycloak's own `/userinfo` endpoint (used here as
    a stand-in protected resource) -- confirming the token `oapi`
    obtains is genuinely accepted, not just successfully parsed.
    """
    client: Client = Client(
        url=keycloak_url,
        oauth2_client_id="client-credentials-client",
        oauth2_client_secret="test-secret",
        oauth2_token_url=_token_url(keycloak_url),
        oauth2_scope="openid",
        timeout=10,
    )
    with client.request(
        "/realms/oapi-test/protocol/openid-connect/userinfo", "GET"
    ) as response:
        userinfo: dict[str, object] = json.loads(response.read())
    assert userinfo["preferred_username"] == (
        "service-account-client-credentials-client"
    )


def test_client_credentials_grant_caches_the_token_across_requests(
    keycloak_url: str,
) -> None:
    client: Client = Client(
        url=keycloak_url,
        oauth2_client_id="client-credentials-client",
        oauth2_client_secret="test-secret",
        oauth2_token_url=_token_url(keycloak_url),
        oauth2_scope="openid",
        timeout=10,
    )
    with client.request(
        "/realms/oapi-test/protocol/openid-connect/userinfo", "GET"
    ) as response:
        response.read()
    first_authorization: str | None = client.headers.get("Authorization")
    with client.request(
        "/realms/oapi-test/protocol/openid-connect/userinfo", "GET"
    ) as response:
        response.read()
    second_authorization: str | None = client.headers.get("Authorization")
    assert first_authorization == second_authorization
