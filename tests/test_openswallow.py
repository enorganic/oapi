import collections
from typing import Sequence

from openswallow.model import OpenAPI, JSONObject, JSONDict


def object_test(
    o  # type: Union[JSONObject, Sequence]
):
    if isinstance(o, JSONDict):
        string = str(o)
        assert string == str(o.__schema__.loads(string).data)
        for k, v in o:
            object_test(v)
    elif isinstance(o, collections.Sequence) and not isinstance(o, (str, bytes)):
        for oo in o:
            object_test(oo)


def test_open_api(
    open_apis  # type: Sequence[OpenAPI]
):
    for open_api in open_apis:
        object_test(open_api)