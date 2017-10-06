import collections
import json
from typing import Sequence
from urllib.request import urlopen
from warnings import warn

from marshmallow import ValidationError

from oapi.meta import get
from oapi.model import Object, OpenAPI, Schema, resolve_references


def discrepancies(a, b):
    # type: (Object, Object) -> dict
    differences = {}
    a_properties = set(get(a).properties.keys())
    b_properties = set(get(b).properties.keys())
    for p in a_properties | b_properties:
        try:
            av = getattr(a, p)
        except AttributeError:
            av = None
        try:
            bv = getattr(b, p)
        except AttributeError:
            bv = None
        if av != bv:
            differences[p] = (av, bv)
    return differences



def object_test(
    o  # type: Union[Object, Sequence]
):
    if isinstance(o, Object):
        t = type(o)
        string = str(o)
        try:
            assert string != ''
            reloaded = t(string)
            try:
                assert o == reloaded
                assert str(o) == str(reloaded)
            except AssertionError as e:
                print(string)
                print(type(o))
                print(type(reloaded))
                print()
                for k, v in discrepancies(o, reloaded).items():
                    a, b = v
                    print(k + ':')
                    print(repr(a))
                    #print(model.serialize(a))
                    print(repr(b))
                    #print(model.serialize(b))
                    print()
                raise e
        except ValidationError as e:
            warn(string)
            raise e
        reloaded_json = json.loads(string)
        keys = set()
        for n, p in get(o).properties.items():
            keys.add(p.name or n)
        for k in reloaded_json.keys():
            if k not in keys:
                raise KeyError(
                    '"%s" not found in dumped JSON: %s' % (
                        k,
                        string
                    )
                )
            object_test(getattr(o, n))
    elif isinstance(o, (collections.Iterable, dict)) and not isinstance(o, (str, bytes)):
        if isinstance(o, dict):
            for k, v in o.items():
                object_test(v)
        else:
            for oo in o:
                object_test(oo)


def test_json_schemas():
    for url in (
        'http://json-schema.org/schema',
        'http://json-schema.org/hyper-schema',
    ):
        print(url)
        with urlopen(url) as response:
            oa = Schema(response)
            object_test(oa)


def test_openapi_schemas():
    for url in (
        'https://raw.githubusercontent.com/OAI/OpenAPI-Specification/master/examples/v2.0/json/petstore-separate/spec/swagger.json',
        'https://raw.githubusercontent.com/OAI/OpenAPI-Specification/master/examples/v3.0/link-example.yaml',
        'https://raw.githubusercontent.com/OAI/OpenAPI-Specification/master/examples/v2.0/json/petstore-with-external-docs.json',
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
            object_test(oa)
            oa2 = resolve_references(oa)
            if oa2 != oa:
                object_test(oa2)


if __name__ == '__main__':
    test_json_schemas()
    test_openapi_schemas()