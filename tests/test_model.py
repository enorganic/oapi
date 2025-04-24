import os
import unittest
from contextlib import suppress
from copy import deepcopy
from itertools import chain
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urljoin
from urllib.request import Request

import sob

from oapi.model import Module, get_default_class_name_from_pointer
from oapi.oas.model import OpenAPI
from oapi.oas.references import Resolver, _urlopen

OPENAPI_EXAMPLE_URL = (
    "https://raw.githubusercontent.com/OAI/OpenAPI-Specification/3.1.1/"
    "examples/"
)
LANGUAGE_TOOL_URL = (
    "https://languagetool.org/http-api/languagetool-swagger.json"
)
TESTS_PATH: Path = Path(__file__).absolute().parent
REGRESSION_DATA_PATH: Path = TESTS_PATH / "regression-data"
INPUT_DATA_PATH: Path = TESTS_PATH / "input-data"
LANGUAGE_TOOL_PATH: Path = INPUT_DATA_PATH / "languagetool-swagger.json"


class TestModel(unittest.TestCase):
    @staticmethod
    def test_get_default_class_name_from_pointer() -> None:
        assert (
            get_default_class_name_from_pointer(
                pointer=(
                    "#/paths/~1directory~1sub-directory~1name/get/parameters/1"
                ),
                name="argument-name",
            )
            == "DirectorySubDirectoryNameGetArgumentName"
        )
        assert (
            get_default_class_name_from_pointer(
                pointer=(
                    "#/paths/~1directory~1sub-directory~1name/get/parameters/1"
                    "/item"
                ),
                name="argument-name",
            )
            == "DirectorySubDirectoryNameGetArgumentNameItem"
        )

    @staticmethod
    def test_openapi_examples() -> None:
        for relative_path in (
            "v2.0/json/petstore-separate/spec/swagger.json",
            "v3.0/link-example.yaml",
            "v2.0/json/petstore-with-external-docs.json",
            "v3.0/api-with-examples.yaml",
            "v3.0/petstore-expanded.yaml",
            "v3.0/petstore.yaml",
            "v3.0/uspto.yaml",
            "v3.0/callback-example.yaml",
            "v2.0/json/api-with-examples.json",
            "v2.0/json/petstore-expanded.json",
            "v2.0/json/petstore-minimal.json",
            "v2.0/json/petstore-with-external-docs.json",
            "v2.0/json/petstore.json",
            "v2.0/json/uber.json",
            "v2.0/yaml/api-with-examples.yaml",
            "v2.0/yaml/petstore-expanded.yaml",
            "v2.0/yaml/petstore-minimal.yaml",
            "v2.0/yaml/petstore-with-external-docs.yaml",
            "v2.0/yaml/petstore.yaml",
            "v2.0/yaml/uber.yaml",
        ):
            url: str = urljoin(OPENAPI_EXAMPLE_URL, relative_path)
            print(url)  # noqa: T201
            with _urlopen(url) as response:
                openapi: OpenAPI = OpenAPI(response)
                sob.validate(openapi)
                openapi2: OpenAPI = deepcopy(openapi)
                assert sob.get_model_url(openapi) == sob.get_model_url(
                    openapi2
                )
                Resolver(openapi2).dereference()
                try:
                    assert "$ref" not in str(openapi2)
                except AssertionError as assertion_error:
                    if assertion_error.args:
                        assertion_error.args = tuple(
                            chain(
                                (
                                    assertion_error.args[0]
                                    + "\n"
                                    + str(openapi2),
                                ),
                                assertion_error.args[1:],
                            )
                        )
                    else:
                        assertion_error.args = (str(openapi2),)
                    raise
                if openapi2 != openapi:
                    sob.validate(openapi2)

    @staticmethod
    def test_languagetool() -> None:
        with suppress(HTTPError):  # noqa: SIM117
            with _urlopen(
                Request(LANGUAGE_TOOL_URL, headers={"User-agent": ""})
            ) as response:
                with open(LANGUAGE_TOOL_PATH, "wb") as language_tool_io:
                    language_tool_io.write(response.read())  # type: ignore
        with open(LANGUAGE_TOOL_PATH) as language_tool_io:
            oa = OpenAPI(language_tool_io)
            sob.validate(oa)
            model = Module(oa)
            model_path: Path = REGRESSION_DATA_PATH / "languagetool.py"
            if model_path.exists():
                with open(model_path) as model_file:
                    model_file_data = model_file.read()
                    if not isinstance(model_file_data, str):
                        model_file_data = str(
                            model_file_data, encoding="utf-8"
                        )
                    assert str(model) == model_file_data
            else:
                if not REGRESSION_DATA_PATH.exists():
                    os.makedirs(REGRESSION_DATA_PATH, exist_ok=True)
                model_string: str = str(model)
                with open(model_path, "w") as model_file:
                    model_file.write(model_string)


if __name__ == "__main__":
    # unittest.main()
    TestModel.test_get_default_class_name_from_pointer()
