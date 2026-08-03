from __future__ import annotations

from pathlib import Path

import sob

from oapi.oas.model import OpenAPI

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
