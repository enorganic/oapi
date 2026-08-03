from __future__ import annotations

import inspect
from collections.abc import Callable
from types import ModuleType

import pytest
from servers import Response, http_test_server

from oapi.oas.model import OpenAPI


@pytest.fixture
def security_schemes_client(
    generated_client_package: Callable[
        [OpenAPI], tuple[ModuleType, ModuleType]
    ],
) -> ModuleType:
    with open("tests/input-data/security-schemes.json") as f:
        open_api: OpenAPI = OpenAPI(f)
    _model_module, client_module = generated_client_package(open_api)
    return client_module


def test_init_bakes_in_the_first_api_key_schemes_location_and_name(
    security_schemes_client: ModuleType,
) -> None:
    """
    The OpenAPI document declares three `apiKey` security schemes
    (header/query/cookie) across different operations, but a generated
    `Client` has one shared `api_key_in`/`api_key_name` default pair --
    codegen picks the first `apiKey` scheme it encounters. Other
    locations remain reachable by passing `api_key_in`/`api_key_name`
    explicitly when constructing the client (see the query/cookie tests
    below), which isn't a bug -- a single client instance can only default
    to one location.
    """
    signature: inspect.Signature = inspect.signature(
        security_schemes_client.Client.__init__
    )
    assert signature.parameters["api_key_in"].default == "header"
    assert signature.parameters["api_key_name"].default == "X-Api-Key"


def test_init_bakes_in_oauth2_and_oidc_urls_from_the_security_schemes(
    security_schemes_client: ModuleType,
) -> None:
    signature: inspect.Signature = inspect.signature(
        security_schemes_client.Client.__init__
    )
    assert (
        signature.parameters["oauth2_token_url"].default
        == "https://example.com/oauth2/token"
    )
    assert (
        signature.parameters["oauth2_authorization_url"].default
        == "https://example.com/oauth2/authorize"
    )
    assert (
        signature.parameters["open_id_connect_url"].default
        == "https://example.com/.well-known/openid-configuration"
    )


def test_default_oauth2_flows_value_is_invalid(
    security_schemes_client: ModuleType,
) -> None:
    """
    Documents a real, verified, currently-unfixed codegen bug: a
    generated `Client` for an OpenAPI document with named OAuth2 flows
    cannot be instantiated with its own defaults. `_iter_oauth2_flows`
    (client.py) reads flow-type names via `sob.utilities.
    iter_properties_values(security_scheme.flows)`, which yields the
    Python-side (snake_case) *property* names of the generated
    `OAuthFlows` model -- e.g. `"authorization_code"` -- rather than the
    OpenAPI spec's own camelCase flow-type identifiers (`"authorization
    Code"`) that `Client.__init__`'s own validation (and its `Literal`
    parameter type) require. The baked-in default `oauth2_flows` tuple
    therefore fails that same validation immediately on construction,
    for *any* generated client whose OpenAPI document has a
    multi-word-named OAuth2 flow (`authorizationCode`/
    `clientCredentials` -- i.e. most real-world OAuth2 specs). The
    workaround (used by every other test in this file) is passing an
    explicit, valid `oauth2_flows` override. Not fixed here (out of
    this test-only initiative's scope) -- flagged to the user directly
    as well as documented here.
    """
    with pytest.raises(ValueError, match="oauth2_flows"):
        security_schemes_client.Client(url="http://example.com")


def test_api_key_header_authentication(
    security_schemes_client: ModuleType,
) -> None:
    with http_test_server(
        responses={
            ("GET", "/protected/api-key-header"): Response(
                body=b'{"name": "x"}'
            )
        }
    ) as server:
        client = security_schemes_client.Client(
            url=server.url, api_key="secret123", oauth2_flows=()
        )
        client.get_protected_api_key_header()
        assert server.requests[0].headers.get("X-Api-Key") == "secret123"


def test_api_key_query_authentication_with_an_explicit_location(
    security_schemes_client: ModuleType,
) -> None:
    with http_test_server(
        responses={
            ("GET", "/protected/api-key-query"): Response(
                body=b'{"name": "x"}'
            )
        }
    ) as server:
        client = security_schemes_client.Client(
            url=server.url,
            api_key="qkey",
            api_key_in="query",
            api_key_name="api_key",
            oauth2_flows=(),
        )
        client.get_protected_api_key_query()
        assert server.requests[0].query == "api_key=qkey"


def test_api_key_cookie_authentication_with_an_explicit_location(
    security_schemes_client: ModuleType,
) -> None:
    with http_test_server(
        responses={
            ("GET", "/protected/api-key-cookie"): Response(
                body=b'{"name": "x"}'
            )
        }
    ) as server:
        client = security_schemes_client.Client(
            url=server.url,
            api_key="ckey",
            api_key_in="cookie",
            api_key_name="api_key",
            oauth2_flows=(),
        )
        client.get_protected_api_key_cookie()
        assert server.requests[0].headers.get("Cookie") == "api_key=ckey"


def test_bearer_authentication(security_schemes_client: ModuleType) -> None:
    with http_test_server(
        responses={
            ("GET", "/protected/bearer"): Response(body=b'{"name": "x"}')
        }
    ) as server:
        client = security_schemes_client.Client(
            url=server.url, bearer_token="tok", oauth2_flows=()
        )
        client.get_protected_bearer()
        assert server.requests[0].headers.get("Authorization") == "Bearer tok"
