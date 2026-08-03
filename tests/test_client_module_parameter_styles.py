from __future__ import annotations

from collections.abc import Callable
from types import ModuleType

import pytest
from servers import Response, http_test_server

from oapi.oas.model import OpenAPI


@pytest.fixture
def parameter_styles_client(
    generated_client_package: Callable[
        [OpenAPI], tuple[ModuleType, ModuleType]
    ],
) -> ModuleType:
    with open("tests/input-data/parameter-styles.json") as f:
        open_api: OpenAPI = OpenAPI(f)
    _model_module, client_module = generated_client_package(open_api)
    return client_module


def test_path_simple_style(parameter_styles_client: ModuleType) -> None:
    with http_test_server(
        responses={("GET", "/path/simple/1,2,3"): Response(body=b"{}")}
    ) as server:
        client = parameter_styles_client.Client(url=server.url)
        client.get_path_simple_id(id_=[1, 2, 3])
        assert server.requests[0].path == "/path/simple/1,2,3"


def test_path_label_style(parameter_styles_client: ModuleType) -> None:
    with http_test_server(
        responses={("GET", "/path/label/.1.2.3"): Response(body=b"{}")}
    ) as server:
        client = parameter_styles_client.Client(url=server.url)
        client.get_path_label_id(id_=[1, 2, 3])
        assert server.requests[0].path == "/path/label/.1.2.3"


def test_path_matrix_style_raises_key_error(
    parameter_styles_client: ModuleType,
) -> None:
    """
    Documents a real, verified, currently-unfixed codegen bug: every
    generated method for a `matrix`-style path parameter crashes with
    `KeyError: 'id'`. `_represent_dictionary_parameter` (client.py)
    prepends the matrix delimiter to the *dictionary key* used for
    string formatting (`";id"`, since `_format_matrix_argument_value`'s
    own output already includes the full `;id=value` fragment), but the
    generated path template's `str.format(**{...})` placeholder is
    still the bare `{id}` from the OpenAPI path -- `"{id}".format(
    **{";id": ...})` cannot find an `"id"` key in the kwargs dict it was
    given (only `";id"` is present) and raises `KeyError`. This means
    matrix-style path parameters are completely unusable in any
    generated client. Not fixed here (out of this test-only
    initiative's scope) -- flagged to the user directly as well as
    documented here.
    """
    with http_test_server(responses={}) as server:
        client = parameter_styles_client.Client(url=server.url)
        with pytest.raises(KeyError, match="id"):
            client.get_path_matrix_id(id_=[1, 2, 3])


def test_query_form_style(parameter_styles_client: ModuleType) -> None:
    with http_test_server(
        responses={("GET", "/query/form"): Response(body=b"{}")}
    ) as server:
        client = parameter_styles_client.Client(url=server.url)
        client.get_query_form(ids=[1, 2, 3])
        assert server.requests[0].query == "ids=1,2,3"


def test_query_space_delimited_style(
    parameter_styles_client: ModuleType,
) -> None:
    with http_test_server(
        responses={("GET", "/query/space-delimited"): Response(body=b"{}")}
    ) as server:
        client = parameter_styles_client.Client(url=server.url)
        client.get_query_space_delimited(ids=[1, 2, 3])
        assert server.requests[0].query == "ids=1%202%203"


def test_query_pipe_delimited_style(
    parameter_styles_client: ModuleType,
) -> None:
    with http_test_server(
        responses={("GET", "/query/pipe-delimited"): Response(body=b"{}")}
    ) as server:
        client = parameter_styles_client.Client(url=server.url)
        client.get_query_pipe_delimited(ids=[1, 2, 3])
        assert server.requests[0].query == "ids=1|2|3"


def test_query_deep_object_style(parameter_styles_client: ModuleType) -> None:
    with http_test_server(
        responses={("GET", "/query/deep-object"): Response(body=b"{}")}
    ) as server:
        client = parameter_styles_client.Client(url=server.url)
        client.get_query_deep_object(filter_={"a": "1", "b": "2"})
        assert server.requests[0].query == "filter[a]=1&filter[b]=2"


def test_header_simple_style(parameter_styles_client: ModuleType) -> None:
    with http_test_server(
        responses={("GET", "/header/simple"): Response(body=b"{}")}
    ) as server:
        client = parameter_styles_client.Client(url=server.url)
        client.get_header_simple(x_ids=[1, 2])
        assert server.requests[0].headers.get("X-Ids") == "1,2"


def test_cookie_form_style(parameter_styles_client: ModuleType) -> None:
    with http_test_server(
        responses={("GET", "/cookie/form"): Response(body=b"{}")}
    ) as server:
        client = parameter_styles_client.Client(url=server.url)
        client.get_cookie_form(ids=[1, 2])
        assert server.requests[0].headers.get("Cookie") == "ids=1,2"
