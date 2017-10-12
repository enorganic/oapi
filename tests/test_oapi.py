from __future__ import nested_scopes, generators, division, absolute_import, with_statement, print_function,\
    unicode_literals

from itertools import chain

import yaml
from copy import deepcopy
from future import standard_library
standard_library.install_aliases()
from builtins import *

import collections
import json
from typing import Sequence
from urllib.request import urlopen
from warnings import warn

from marshmallow import ValidationError

from serial import meta, model, test
from oapi.model import OpenAPI, Schema, resolve_references


def test_json_schemas():
    for url in (
        'http://json-schema.org/schema',
        'http://json-schema.org/hyper-schema',
    ):
        print(url)
        with urlopen(url) as response:
            oa = Schema(response)
            test.json_object(oa)


def test_openapi_schemas():
    for url in (
        (
            'https://raw.githubusercontent.com/OAI/OpenAPI-Specification/master/examples/v2.0/json/' +
            'petstore-separate/spec/swagger.json'
        ),
        'https://raw.githubusercontent.com/OAI/OpenAPI-Specification/master/examples/v3.0/link-example.yaml',
        (
            'https://raw.githubusercontent.com/OAI/OpenAPI-Specification/master/examples/v2.0/json/' +
            'petstore-with-external-docs.json'
        ),
        'https://raw.githubusercontent.com/OAI/OpenAPI-Specification/master/examples/v3.0/api-with-examples.yaml',
        'https://raw.githubusercontent.com/OAI/OpenAPI-Specification/master/examples/v3.0/petstore-expanded.yaml',
        'https://raw.githubusercontent.com/OAI/OpenAPI-Specification/master/examples/v3.0/petstore.yaml',
        'https://raw.githubusercontent.com/OAI/OpenAPI-Specification/master/examples/v3.0/uber.yaml',
        'https://raw.githubusercontent.com/OAI/OpenAPI-Specification/master/examples/v2.0/json/api-with-examples.json',
        'https://raw.githubusercontent.com/OAI/OpenAPI-Specification/master/examples/v2.0/json/petstore-expanded.json',
        'https://raw.githubusercontent.com/OAI/OpenAPI-Specification/master/examples/v2.0/json/petstore-minimal.json',
        (
            'https://raw.githubusercontent.com/OAI/OpenAPI-Specification/master/examples/v2.0/json/' +
            'petstore-with-external-docs.json'
        ),
        'https://raw.githubusercontent.com/OAI/OpenAPI-Specification/master/examples/v2.0/json/petstore.json',
        'https://raw.githubusercontent.com/OAI/OpenAPI-Specification/master/examples/v2.0/json/uber.json',
        'https://raw.githubusercontent.com/OAI/OpenAPI-Specification/master/examples/v2.0/yaml/api-with-examples.yaml',
        'https://raw.githubusercontent.com/OAI/OpenAPI-Specification/master/examples/v2.0/yaml/petstore-expanded.yaml',
        'https://raw.githubusercontent.com/OAI/OpenAPI-Specification/master/examples/v2.0/yaml/petstore-minimal.yaml',
        (
            'https://raw.githubusercontent.com/OAI/OpenAPI-Specification/master/examples/v2.0/yaml/' +
            'petstore-with-external-docs.yaml'
        ),
        'https://raw.githubusercontent.com/OAI/OpenAPI-Specification/master/examples/v2.0/yaml/petstore.yaml',
        'https://raw.githubusercontent.com/OAI/OpenAPI-Specification/master/examples/v2.0/yaml/uber.yaml',
        'http://devdocs.magento.com/swagger/schemas/latest-2.0.schema.json',
        'http://devdocs.magento.com/swagger/schemas/latest-2.1.schema.json',
        'http://devdocs.magento.com/swagger/schemas/latest-2.2.schema.json',
        'https://stage.commerceapi.io/swagger/docs/v1',
        'https://stage.commerceapi.io/swagger/docs/v2',
    ):
        print(url)
        with urlopen(url) as response:
            oa = OpenAPI(response)
            test.json_object(oa)
            oa2 = resolve_references(oa)
            if oa2 != oa:
                test.json_object(oa2)


if __name__ == '__main__':
    # test_json_schemas()
    test_openapi_schemas()
