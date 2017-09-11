import collections
from typing import Sequence

import os
from urllib.request import urlopen

from marshmallow import ValidationError

from openswallow import open_api
from openswallow.model import OpenAPI, JSONObject, get_schema


def object_test(
    o  # type: Union[JSONObject, Sequence]
):
    if isinstance(o, JSONObject):
        string = str(o)
        try:
            assert string == str(get_schema(o)(strict=True, many=False).loads(string).data)
        except ValidationError as e:
            print(string)
            raise e
        for k, v in o:
            if k == 'paths':
                # for kk, vv in v.items():
                #     print(kk)
                #     print(vv.description)
                print('%s = %s' % (k, str(v)))
            object_test(v)
    elif isinstance(o, collections.Sequence) and not isinstance(o, (str, bytes)):
        for oo in o:
            object_test(oo)


def test_open_api():
    d = os.path.join(os.path.dirname(__file__), 'data')
    # for sd in os.listdir(d):
    #     sd = os.path.join(d, sd)
    #     if os.path.isdir(sd):
    #         for fn in os.listdir(sd):
    #             ext = fn.split('.')[-1].lower()
    #             if ext in ('json', 'yaml'):
    #                 p = os.path.join(sd, fn)
    #                 print(p)
    #                 with open(
    #                     p,
    #                     mode='r',
    #                     encoding='utf-8'
    #                 ) as f:
    #                     s = f.read()
    #                     # print(s)
    #                     oa = open_api(s)
    #                     object_test(oa)
    #
    with urlopen(
        'http://devdocs.magento.com/swagger/schemas/latest-2.2.schema.json'
        # 'https://raw.githubusercontent.com/magento/devdocs/develop/swagger/schemas/latest-2.2.schema.json'
    ) as response:
        oa = open_api(response)
        object_test(oa)
    # with urlopen('https://stage.commerceapi.io/swagger/docs/v1') as response:
    #     oa = open_api(response)
    #     object_test(oa)
    # with urlopen('https://stage.commerceapi.io/swagger/docs/v2') as response:
    #     oa = open_api(response)
    #     object_test(oa)


if __name__ == '__main__':
    test_open_api()