"""
An SDK/library for parsing OpenAPI (Swagger) 2.0 - 3.0 JSON specifications, and generating python code representing the
data model as python classes (for both requests and responses). The name of this package is a portmanteau of "Open API",
"Swagger", and "Marshmallow".
"""
import json
import typing
from collections import OrderedDict
from warnings import warn

import yaml

from openswallow.model import OpenAPI
from openswallow.model.schemas import OpenAPISchema, SchematicSchema


def open_api(
    data  # type: Optional[Union[typing.AnyStr, typing.IO]]
):
    """
    :param data: A JSON or YAML string, or a file (or file-like) object containing JSON or YAML.
    """
    if isinstance(data, str):
        pass
    elif hasattr(data, 'read'):  # and isinstance(data.read, collections.Callable):
        data = data.read()
        if not isinstance(data, str):
            data = str(data, encoding='utf-8')
    else:
        raise TypeError(
            'This class can be initialized from a string or file (IO) object.'
        )
    try:
        data = json.loads(data, object_hook=OrderedDict)
    except json.JSONDecodeError:
        data = yaml.load(data)
    return OpenAPISchema(strict=True, many=False).load(data).data


def json_schema(
    data  # type: Optional[Union[typing.AnyStr, typing.IO]]
):
    """
    :param data: A JSON or YAML string, or a file (or file-like) object containing JSON or YAML.
    """
    if isinstance(data, str):
        pass
    elif hasattr(data, 'read'):  # and isinstance(data.read, collections.Callable):
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
    result = SchematicSchema(
        strict=True,
        many=False
    ).load(data)
    if result.errors:
        warn(repr(result.errors))
    return result.data





