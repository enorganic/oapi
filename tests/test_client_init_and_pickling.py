from __future__ import annotations

import pickle
import warnings
from http.cookiejar import CookieJar
from urllib.request import OpenerDirector

import pytest

from oapi.client import Client


def test_init_rejects_an_invalid_api_key_in() -> None:
    with pytest.raises(ValueError, match="api_key_in"):
        Client(api_key_in="bogus")  # type: ignore[arg-type]


def test_init_rejects_invalid_oauth2_flows() -> None:
    with pytest.raises(ValueError, match="oauth2_flows"):
        Client(oauth2_flows=("bogus",))  # type: ignore[arg-type]


def test_init_translates_openapi_2x_flow_names() -> None:
    client: Client = Client(oauth2_flows=("accessCode", "application"))
    # `Client.oauth2_flows` is annotated (in the real source, with a
    # `# type: ignore`) as a single `Literal[...] | None`, but the
    # actual runtime value assigned by `__init__` is always a tuple.
    assert client.oauth2_flows == (  # type: ignore[comparison-overlap]
        "authorizationCode",
        "clientCredentials",
    )


@pytest.mark.parametrize(
    "url_kwarg",
    [
        "url",
        "oauth2_authorization_url",
        "oauth2_token_url",
        "oauth2_refresh_url",
    ],
)
def test_init_rejects_a_non_http_scheme_url(url_kwarg: str) -> None:
    with pytest.raises(ValueError, match="ftp://bad"):
        Client(**{url_kwarg: "ftp://bad"})  # type: ignore[arg-type]


def test_init_allows_a_relative_url() -> None:
    client: Client = Client(url="/relative")
    assert client.url == "/relative"


def test_init_default_headers() -> None:
    client: Client = Client()
    assert client.headers == {
        "Accept": "application/json",
        "Content-type": "application/json",
    }


def test_opener_is_lazily_built_and_cached() -> None:
    client: Client = Client()
    opener_first: OpenerDirector = client._opener
    opener_second: OpenerDirector = client._opener
    assert opener_first is opener_second


def test_getstate_excludes_the_private_opener() -> None:
    client: Client = Client(url="http://example.com", user="u", password="p")
    state: dict[str, object] = client.__getstate__()
    assert "__opener" not in state
    assert state["url"] == "http://example.com"
    assert state["user"] == "u"


def test_setstate_reconstructs_a_client_via_init_kwargs() -> None:
    client: Client = Client(url="http://example.com", user="u", password="p")
    state: dict[str, object] = client.__getstate__()
    new_client: Client = Client.__new__(Client)
    new_client.__setstate__(dict(state))
    assert new_client.url == "http://example.com"
    assert new_client.user == "u"
    assert new_client.password == "p"
    assert isinstance(new_client._cookie_jar, CookieJar)


def test_pickle_round_trip_preserves_configuration() -> None:
    client: Client = Client(
        url="http://example.com", api_key="key123", api_key_name="X-KEY"
    )
    unpickled: Client = pickle.loads(pickle.dumps(client))
    assert type(unpickled) is Client
    assert unpickled.url == "http://example.com"
    assert unpickled.api_key == "key123"
    assert unpickled.api_key_name == "X-KEY"


def test_resurrect_client_warns_and_reconstructs_from_minimal_args() -> None:
    """
    `_resurrect_client` is a deprecated `__reduce__`-era un-pickling path
    (superseded by `__getstate__`/`__setstate__`). It calls
    `cls(*init_parameters)` positionally after popping the trailing
    `cookie_jar`/`oauth2_authorization_expires` values, but `Client.
    __init__` only accepts `url` positionally (every other parameter is
    keyword-only) -- so this method only actually works for the minimal
    pickled-state shape of `(url_or_nothing, cookie_jar, expires)`. It
    is exercised here with that minimal shape, matching what old
    pickled data (from before `__getstate__`/`__setstate__` existed)
    would have looked like for a client with only a `url` set.
    """
    with pytest.warns(DeprecationWarning, match="out of date"):
        client: Client = Client._resurrect_client(
            "http://example.com", CookieJar(), 0
        )
    assert client.url == "http://example.com"


def test_resurrect_client_with_no_positional_args() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        client: Client = Client._resurrect_client(CookieJar(), 0)
    assert client.url is None
