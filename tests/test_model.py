from copy import deepcopy

from oapi.model import Module

import os
from itertools import chain
from urllib.parse import urljoin

from urllib.request import Request, urlopen

import sob
from oapi.oas.references import Resolver
from oapi.oas.model import OpenAPI

OPENAPI_EXAMPLE_URL = (
    "https://raw.githubusercontent.com/OAI/OpenAPI-Specification/master/"
    "examples/"
)
LANGUAGE_TOOL_URL = (
    "https://languagetool.org/http-api/languagetool-swagger.json"
)


def test_languagetool() -> None:
    with urlopen(
        Request(LANGUAGE_TOOL_URL, headers={"User-agent": ""})
    ) as response:
        oa = OpenAPI(response)
        sob.test.json(oa)
        model = Module(oa)
        model_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "data",
            "languagetool.py"
        )
        if os.path.exists(model_path):
            with open(model_path, "r") as model_file:
                model_file_data = model_file.read()
                if not isinstance(model_file_data, str):
                    model_file_data = str(model_file_data, encoding="utf-8")
                assert str(model) == model_file_data
        else:
            model_string: str = str(model)
            if model_string.strip():
                with open(model_path, "w") as model_file:
                    model_file.write(model_string)
            else:
                raise ValueError()


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
        print(url)
        with urlopen(url) as response:
            oa = OpenAPI(response)
            sob.test.json(oa)
            oa2 = deepcopy(oa)
            assert sob.meta.url(oa) == sob.meta.url(oa2)
            Resolver(oa2).dereference()
            try:
                assert "$ref" not in str(oa2)
            except AssertionError as e:
                if e.args:
                    e.args = tuple(
                        chain((e.args[0] + "\n" + str(oa2),), e.args[1:])
                    )
                else:
                    e.args = (str(oa2),)
                raise e
            if oa2 != oa:
                sob.test.json(oa2)


def _test_magento_schemas() -> None:
    rp: str
    for rp in (
        "latest-2.0.schema.json",
        "latest-2.1.schema.json",
        "latest-2.2.schema.json",
    ):
        url: str = urljoin("http://devdocs.magento.com/swagger/schemas/", rp)
        print(url)
        with urlopen(url) as response:
            oa = OpenAPI(response)
            sob.test.json(oa)
            oa2 = deepcopy(oa)
            Resolver(oa2).dereference()
            if oa2 != oa:
                sob.test.json(oa2)


def _test_logic_broker_schemas() -> None:
    rp: str
    for rp in (
        "v1",
        "v2",
    ):
        url = urljoin("https://stage.commerceapi.io/swagger/docs/", rp)
        print(url)
        with urlopen(url) as response:
            oa = OpenAPI(response)
            sob.test.json(oa)
            oa2 = deepcopy(oa)
            Resolver(oa2).dereference()
            try:
                assert "$ref" not in sob.model.serialize(oa2)
            except AssertionError as e:
                if e.args:
                    e.args = tuple(
                        chain((e.args[0] + "\n" + repr(oa2),), e.args[1:])
                    )
                else:
                    e.args = (repr(oa2),)
                raise e
            if oa2 != oa:
                sob.test.json(oa2)


if __name__ == "__main__":
    _test_logic_broker_schemas()
    _test_magento_schemas()
    test_languagetool()
    test_openapi_examples()
