# region Backwards Compatibility
from __future__ import absolute_import, division, generators, nested_scopes, print_function, unicode_literals, \
    with_statement

from future import standard_library

standard_library.install_aliases()
from builtins import *
from future.utils import native_str
# endregion
import os
from itertools import chain
from urllib.parse import urljoin

from urllib.request import urlopen

import serial
from oapi.model import OpenAPI, Schema, resolve_references, Info


def test_openapi_examples():
    examples = (
        'v2.0/json/petstore-separate/spec/swagger.json',
        'v3.0/link-example.yaml',
        'v2.0/json/petstore-with-external-docs.json',
        'v3.0/api-with-examples.yaml',
        'v3.0/petstore-expanded.yaml',
        'v3.0/petstore.yaml',
        'v3.0/uber.yaml',
        'v3.0/callback-example.yaml',
        'v2.0/json/api-with-examples.json',
        'v2.0/json/petstore-expanded.json',
        'v2.0/json/petstore-minimal.json',
        'v2.0/json/petstore-with-external-docs.json',
        'v2.0/json/petstore.json',
        'v2.0/json/uber.json',
        'v2.0/yaml/api-with-examples.yaml',
        'v2.0/yaml/petstore-expanded.yaml',
        'v2.0/yaml/petstore-minimal.yaml',
        'v2.0/yaml/petstore-with-external-docs.yaml',
        'v2.0/yaml/petstore.yaml',
        'v2.0/yaml/uber.yaml',
    )
    for rp in examples:
        url = urljoin('https://raw.githubusercontent.com/OAI/OpenAPI-Specification/master/examples/', rp)
        print(url)
        with urlopen(url) as response:
            oa = OpenAPI(response)
            serial.test.json_object(oa)
            oa2 = resolve_references(oa)
            try:
                assert '$ref' not in serial.model.serialize(oa2)
            except AssertionError as e:
                if e.args:
                    e.args = tuple(chain(
                        (e.args[0] + '\n' + repr(oa2),),
                        e.args[1:]
                    ))
                else:
                    e.args = (repr(oa2),)
                raise e
            if oa2 != oa:
                serial.test.json(oa2)
    # for rp in examples:
    #     p = os.path.join(
    #         os.path.dirname(__file__),
    #         'data',
    #         rp
    #     )
    #     print(p)
    #     with open(p) as f:
    #         oa = OpenAPI(f)
    #         serial.model.validate(oa)
    #         serial.test.json(oa)
    #         oa2 = resolve_references(oa)
    #         try:
    #             assert '$ref' not in serial.model.serialize(oa2)
    #         except AssertionError as e:
    #             if e.args:
    #                 e.args = tuple(chain(
    #                     (e.args[0] + '\n' + repr(oa2),),
    #                     e.args[1:]
    #                 ))
    #             else:
    #                 e.args = (repr(oa2),)
    #             raise e
    #         if oa2 != oa:
    #             serial.test.json(oa2)


def test_magento_schemas():
    for rp in (
        'latest-2.0.schema.json',
        'latest-2.1.schema.json',
        'latest-2.2.schema.json',
    ):
        url = urljoin('http://devdocs.magento.com/swagger/schemas/', rp)
        print(url)
        with urlopen(url) as response:
            oa = OpenAPI(response)
            serial.test.json(oa)
            oa2 = resolve_references(oa)
            if oa2 != oa:
                serial.test.json(oa2)


def test_logic_broker_schemas():
    for rp in (
        'v1',
        'v2',
    ):
        url = urljoin('https://stage.commerceapi.io/swagger/docs/', rp)
        print(url)
        with urlopen(url) as response:
            oa = OpenAPI(response)
            serial.test.json(oa)
            oa2 = resolve_references(oa)
            try:
                assert '$ref' not in serial.model.serialize(oa2)
            except AssertionError as e:
                if e.args:
                    e.args = tuple(chain(
                        (e.args[0] + '\n' + repr(oa2),),
                        e.args[1:]
                    ))
                else:
                    e.args = (repr(oa2),)
                raise e
            if oa2 != oa:
                serial.test.json(oa2)


if __name__ == '__main__':
    test_openapi_examples()
    test_magento_schemas()
    test_logic_broker_schemas()

