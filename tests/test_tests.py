from __future__ import annotations

import threading
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import pytest
import sob
from servers import Response, http_test_server

from oapi.oas.model import OpenAPI

# Covers tests/conftest.py, tests/servers.py, and tests/input-data/*.json
# -- test-support code with no src/oapi package-module counterpart.

# region conftest.py: generated_module_loader


def test_generated_module_loader_imports_real_module(
    generated_module_loader: Callable[..., ModuleType],
) -> None:
    module = generated_module_loader(
        "VALUE = 42\n\n\ndef greet(name: str) -> str:\n"
        "    return f'hi {name}'\n"
    )
    assert module.VALUE == 42
    assert module.greet("x") == "hi x"


# endregion

# region servers.py: http_test_server


def test_records_request_and_returns_static_response() -> None:
    with http_test_server(
        responses={
            ("GET", "/hello"): Response(
                status=201,
                body=b'{"ok":true}',
                headers={"Content-type": "application/json"},
            )
        }
    ) as server:
        with urlopen(f"{server.url}/hello?x=1") as response:
            assert response.status == 201
            assert response.read() == b'{"ok":true}'
            assert response.headers["Content-type"] == "application/json"
        assert len(server.requests) == 1
        recorded = server.requests[0]
        assert recorded.method == "GET"
        assert recorded.path == "/hello"
        assert recorded.query == "x=1"


def test_sequence_responses_are_consumed_then_repeat_last() -> None:
    with http_test_server(
        sequences={
            ("GET", "/flaky"): [
                Response(status=503),
                Response(status=503),
                Response(status=200, body=b'{"ok":true}'),
            ]
        }
    ) as server:
        statuses = []
        for _ in range(4):
            try:
                with urlopen(f"{server.url}/flaky") as response:
                    statuses.append(response.status)
            except HTTPError as error:
                statuses.append(error.code)
        assert statuses == [503, 503, 200, 200]


def test_dynamic_handler_computes_response_from_request() -> None:
    with http_test_server(
        handlers={
            ("POST", "/echo"): lambda request: Response(
                status=200, body=request.body
            )
        }
    ) as server:
        data = b'{"a":1}'
        request = Request(f"{server.url}/echo", data=data, method="POST")
        with urlopen(request) as response:
            assert response.read() == data


def test_server_thread_is_joined_on_exit() -> None:
    threads_before = threading.active_count()
    with http_test_server() as server:
        assert threading.active_count() == threads_before + 1
        port = server.server_address[1]
    assert threading.active_count() == threads_before
    with pytest.raises(URLError):
        urlopen(f"http://127.0.0.1:{port}/", timeout=1)


# endregion

# region tests/input-data/*.json: fixture validity

INPUT_DATA_PATH: Path = Path(__file__).absolute().parent / "input-data"


def test_parameter_styles_fixture_is_valid_openapi() -> None:
    with open(INPUT_DATA_PATH / "parameter-styles.json") as io_:
        open_api = OpenAPI(io_)
    sob.validate(open_api)
    assert open_api.paths is not None
    operation_ids = {
        operation.operation_id
        for path_item in open_api.paths.values()
        for operation in (
            path_item.get,
            path_item.post,
            path_item.put,
            path_item.patch,
            path_item.delete,
        )
        if operation is not None
    }
    assert operation_ids == {
        "getPathSimple",
        "getPathLabel",
        "getPathMatrix",
        "getQueryForm",
        "getQuerySpaceDelimited",
        "getQueryPipeDelimited",
        "getQueryDeepObject",
        "getHeaderSimple",
        "getCookieForm",
    }


def test_security_schemes_fixture_is_valid_openapi() -> None:
    with open(INPUT_DATA_PATH / "security-schemes.json") as io_:
        open_api = OpenAPI(io_)
    sob.validate(open_api)
    assert open_api.components is not None
    assert open_api.components.security_schemes is not None
    assert set(open_api.components.security_schemes.keys()) == {
        "apiKeyHeader",
        "apiKeyQuery",
        "apiKeyCookie",
        "httpBearer",
        "oauth2Password",
        "oauth2ClientCredentials",
        "oauth2AuthorizationCode",
        "oauth2Implicit",
        "openIdConnect",
    }


def test_multipart_request_body_fixture_is_valid_openapi() -> None:
    with open(INPUT_DATA_PATH / "multipart-request-body.json") as io_:
        open_api = OpenAPI(io_)
    sob.validate(open_api)
    assert open_api.paths is not None
    upload = open_api.paths["/upload"]
    assert upload.post is not None
    assert upload.post.operation_id == "postUpload"
    assert upload.post.request_body is not None
    assert "multipart/form-data" in upload.post.request_body.content


def test_polymorphic_schemas_fixture_is_valid_openapi() -> None:
    with open(INPUT_DATA_PATH / "polymorphic-schemas.json") as io_:
        open_api = OpenAPI(io_)
    sob.validate(open_api)
    assert open_api.components is not None
    assert open_api.components.schemas is not None
    assert set(open_api.components.schemas.keys()) == {
        "Status",
        "NamedEntity",
        "Pet",
        "Circle",
        "Square",
        "Shape",
        "EmailContact",
        "PhoneContact",
        "Contact",
    }


# endregion
