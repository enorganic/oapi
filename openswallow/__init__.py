"""
An SDK/library for parsing OpenAPI (Swagger) 2.0 JSON specifications and generating python code representing the
data model as python classes (for both requests and responses). Output modules are dependent on ``marshmallow`` (as well
as this package) for parsing and serialization.
"""
import json
import typing
from collections import OrderedDict

import yaml

from openswallow.model import OpenAPI
from openswallow.model.schemas import OpenAPISchema


def open_api(
    data  # type: Optional[Union[typing.AnyStr, typing.IO]]
):
    """
    :param data: A JSON or YAML string, or a file (or file-like) object containing JSON or YAML.
    """
    if isinstance(data, str):
        pass
    elif hasattr(data, 'read'): # and isinstance(data.read, collections.Callable):
        data = data.read()
        if not isinstance(data, str):
            data = str(data, encoding='utf-8')
    else:
        raise TypeError(
            'This class can be initialized from a string or file (IO) object.'
        )
    try:
        data = json.loads(data, object_hook=OrderedDict)
    except json.JSONDecodeError as e:
        data = yaml.load(data)
    return OpenAPISchema(strict=True, many=False).load(data).data





