from __future__ import annotations

from collections.abc import Callable
from types import ModuleType

import pytest
from servers import Response, http_test_server

from oapi.oas.model import OpenAPI


@pytest.fixture
def multipart_client(
    generated_client_package: Callable[
        [OpenAPI], tuple[ModuleType, ModuleType]
    ],
) -> ModuleType:
    with open("tests/input-data/multipart-request-body.json") as f:
        open_api: OpenAPI = OpenAPI(f)
    _model_module, client_module = generated_client_package(open_api)
    return client_module


def test_generated_multipart_method_raises_key_error(
    multipart_client: ModuleType,
) -> None:
    """
    Documents the same real, verified, currently-unfixed bug already
    covered directly against `Client.request()` in
    `tests/test_client_request_runtime.py`'s
    `test_request_multipart_crashes_missing_content_encoding_header`,
    confirmed here to also break *generated* multipart operations (the
    exact scenario `tests/input-data/multipart-request-body.json` was
    built to exercise, per the infrastructure plan): `_request_callback`
    calls `request.headers.get("Content-encoding")` expecting ordinary
    `dict.get` semantics, but a `MultipartRequest`'s custom `Headers`
    object re-raises `KeyError` when no `default` is passed and the key
    is missing -- which it always is for an ordinary multipart request.
    Every generated multipart operation is therefore unusable as-is.
    Not fixed here (out of this test-only initiative's scope) --
    flagged to the user directly as well as documented here.
    """
    with http_test_server(
        responses={("POST", "/upload"): Response(status=200, body=b"{}")}
    ) as server:
        client = multipart_client.Client(url=server.url)
        with pytest.raises(KeyError, match="Content-encoding"):
            client.post_upload(
                file=b"filedata", description="a file", tags=["a", "b"]
            )
