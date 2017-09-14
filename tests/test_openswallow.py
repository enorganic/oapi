import collections
import json
from typing import Sequence

import os
from urllib.request import urlopen
from warnings import warn

from marshmallow import ValidationError

from oapi import open_api, json_schema
from oapi.model import OpenAPI, Object, get_schema, get_properties_values, JSONDict, JSONList, JSON


def object_test(
    o  # type: Union[Object, Sequence]
):
    if isinstance(o, Object):
        string = str(o)
        # print(string)
        try:
            assert string != ''
            schema_instance = get_schema(o)(strict=True, many=False)
            reloaded = schema_instance.loads(string).data
            assert string == str(reloaded)
        except ValidationError as e:
            warn(string)
            raise e
        reloaded_json = json.loads(string)
        # for k, v in get_schema(o)().fields.items():
        #     print('    field - %s: %s' % (k, str(v)))
        for k, v in get_properties_values(o):
            f = schema_instance.fields[k]
            n = f.load_from or f.name
            if n not in reloaded_json:
                raise KeyError(
                    '"%s" not found in dumped JSON: %s' % (
                        n,
                        string
                    )
                )
            object_test(v)
    elif isinstance(o, collections.Sequence) and not isinstance(o, (str, bytes)):
        for oo in o:
            object_test(oo)


def test_json_schema():
    # d = os.path.join(os.path.dirname(__file__), 'data', 'json')
    # for fn in os.listdir(d):
    #     if 'hyper' in fn:
    #         continue
    #     ext = fn.split('.')[-1].lower()
    #     if ext in ('json', 'yaml'):
    #         p = os.path.join(d, fn)
    #         print(p)
    #         with open(
    #             p,
    #             mode='r',
    #             encoding='utf-8'
    #         ) as f:
    #             s = f.read()
    #             print(s)
    #             oa = json_schema(s)
    #             for k, v in get_properties_values(oa):
    #                 print('%s = %s' % (k, str(v) if isinstance(v, JSON) else repr(v)))
    #             object_test(oa)
    #             print(oa)
    #
    for url in (
        'http://json-schema.org/schema',
    ):
        with urlopen(url) as response:
            try:
                oa = json_schema(response)
            except ValidationError as e:
                for i in range(len(e.fields)):
                    f = e.fields[i]
                    print(f.name)
                    print(e.data[f.load_from or f.name])
                    for p in dir(f):
                        if p[0] != '_':
                            v = getattr(f, p)
                            if not isinstance(v, collections.Callable):
                                print('    %s = %s' % (p, repr(v)))

                raise e
            for k, v in get_properties_values(oa):
                print('    %s = %s' % (k, str(v) if isinstance(v, JSON) else repr(v)))
            print(oa)
            object_test(oa)


def test_open_api():
    d = os.path.join(os.path.dirname(__file__), 'data', 'openapi')
    for sd in os.listdir(d):
        sd = os.path.join(d, sd)
        if os.path.isdir(sd):
            for fn in os.listdir(sd):
                if fn != 'api-with-examples.json':
                    continue
                ext = fn.split('.')[-1].lower()
                if ext in (
                    'json',
                    # 'yaml',
                ):
                    p = os.path.join(sd, fn)
                    print()
                    print(p)
                    with open(
                        p,
                        mode='r',
                        encoding='utf-8'
                    ) as f:
                        s = f.read()
                        # print(s)
                        oa = open_api(s)
                        #print(repr(oa))
                        print(oa)
                        object_test(oa)
    for url in (
        'http://devdocs.magento.com/swagger/schemas/latest-2.2.schema.json',
        'https://stage.commerceapi.io/swagger/docs/v1',
        'https://stage.commerceapi.io/swagger/docs/v2',
    ):
        with urlopen(url) as response:
            oa = open_api(response)
            print(oa)
            object_test(oa)


if __name__ == '__main__':
    # test_json_schema()
    test_open_api()