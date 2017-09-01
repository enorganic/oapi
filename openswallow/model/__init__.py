import collections
from copy import copy
from numbers import Number
from typing import List, Union, Any

from marshmallow import missing, Schema

from openswallow.utilities import bases

Missing = type(missing)


class JSONObject(object):

    __schema__ = None

    def __iter__(self):
        for k in dir(self):
            if k[0] != '_':
                v = getattr(self, k)
                if not isinstance(v, (collections.Callable, Missing)):
                    yield k, v

    def __copy__(self):
        return self.__class__(**{
            k: copy(v) for k, v in self
        })

    def __str__(self):
        return self.__schema__(strict=True, many=False).dumps(self, many=False).data


class Info(JSONObject):

    def __init__(
        self,
        version=missing,  # type: Union[str, Missing]
        title=missing,  # type: Union[str, Missing]
    ):
        # type: (...) -> None
        self.version = version  # type: Union[str, Missing]
        self.title = title  # type: Union[str, Missing]


class Tag(JSONObject):

    def __init__(
        self,
        name=missing,  # type: Union[str, Missing]
        description=missing,  # type: Union[str, Missing]
    ):
        # type: (...) -> None
        self.name = name  # type: Union[str, Missing]
        self.description = description  # type: Union[str, Missing]


class Response(JSONObject):

    def __init__(
        self,

    ):
        # type: (...) -> None
        pass


class Responses(JSONObject):

    def __init__(
        self,
        success=missing,  # type: Union[Response, Missing]
        unauthorized=missing,  # type: Union[Response, Missing]
        default=missing,  # type: Union[Response, Missing]
    ):
        # type: (...) -> None
        self.success = success  # type: Union[Response, Missing]
        self.unauthorized = unauthorized  # type: Union[Response, Missing]
        self.default = default  # type: Union[Response, Missing]


class ServiceMethod(JSONObject):

    def __init__(
        self,
        operation_id=missing,  # type: Union[str, Missing],
        summary=missing,  # type: Union[str, Missing]
        produces=missing,  # type: Union[Sequence[str], Missing]
        responses=missing,  # type: Union[Responses, Missing]
    ):
        # type: (...) -> None
        self.operation_id = operation_id  # type: Union[str, Missing]
        self.summary = summary  # type: Union[str, Missing]
        self.produces = produces  # type: Union[Sequence[str], Missing]
        self.responses = responses  # type: Union[Responses, Missing]


class Service(JSONObject):

    def __init__(
        self,
        get=missing,  # type: Union[Method, Missing]
        put=missing,  # type: Union[Method, Missing]
        post=missing,  # type: Union[Method, Missing]
        delete=missing,  # type: Union[Method, Missing]
        patch=missing,  # type: Union[Method, Missing]
    ):
        # type: (...) -> None
        self.get = get  # type: Union[Method, Missing]
        self.put = put  # type: Union[Method, Missing]
        self.post = post  # type: Union[Method, Missing]
        self.delete = delete  # type: Union[Method, Missing]
        self.patch = patch  # type: Union[Method, Missing]


class Server(JSONObject):

    def __init__(
        self,
        url=None,  # type: Union[str, Missing]
        description=None,  # type: Union[str, Missing]
        variables=missing  # type: Union[Dict[str, ServerVariable], Missing]
    ):
        # type: (...) -> None
        self.url = url   # type: Union[str, Missing]
        self.description = description  # type: Union[str, Missing]
        self.variables = variables  # type: Union[Dict[str, ServerVariable], Missing]


class JSONSchematic(JSONObject):
    """
    Instances of this class represent a JSON validation schema, as defined on <http://json-schema.org> and
    <https://swagger.io/specification/#schemaObject>.

    Properties:

        - title (str)

        - description (str)

        - multiple_of (Number): The number this schema describes should be divisible by this number.

        - maximum (Number): The number this schema describes should be less than or equal to this value, or less than
          this value, depending on the value of ``exclusive_maximum``.

        - exclusive_maximum (bool): If ``True``, the numeric instance described by this schema must be *less than*
          ``maximum``. If ``False``, the numeric instance described by this schema can be less than or *equal to*
          ``maximum``.

        - minimum (Number): The number this schema describes should be greater than or equal to this value, or greater
          than this value, depending on the value of ``exclusive_minimum``.

        - exclusive_minimum (bool): If ``True``, the numeric instance described by this schema must be *greater than*
          ``minimum``. If ``False``, the numeric instance described by this schema can be greater than or *equal to*
          ``minimum``.

        - max_length (int): The number of characters in the string instance described by this schema must be less than,
          or equal to, the value of this property.

        - min_length (int): The number of characters in the string instance described by this schema must be greater
          than, or equal to, the value of this property.

        - pattern (str): The string instance described by this schema should match this regular expression (ECMA 262).

        - items (JSONSchematic|Sequence[JSONSchematic]):

            - If ``items`` is a sub-schema—each item in the array instance described by this schema should be valid as
              described by this sub-schema.

            - If ``items`` is a sequence of sub-schemas, the array instance described by this schema should be equal in
              length to this sequence, and each value should be valid as described by the sub-schema at the
              corresponding index within this sequence of sub-schemas.

        - additional_items (JSONSchematic|bool): If ``additional_items`` is ``True``—the array instance described by this schema may contain additional
          values beyond those defined in ``items``.

        - max_items (int): The array instance described by this schema should contain no more than this number of
          items.

        - min_items (int): The array instance described by this schema should contain at least this number of
          items.

        - unique_items (bool): The array instance described by this schema should contain only unique items.

        - max_properties (int)

        - min_properties (int)

        - properties (Dict[str, JSONSchematic]): Any properties of the object instance described by this schema which
          correspond to a key in this mapping should be valid as described by the sub-schema corresponding to that key.

        - pattern_properties (JSONSchematic): Any properties of the object instance described by this schema which
          match a key in this mapping, when the key is evaluated as a regular expression, should be valid as described by
          the sub-schema corresponding to the matched key.

        - additional_properties (bool|JSONSchematic):

            - If ``additional_properties`` is ``True``—properties may be present in the object described by
              this schema with names which do not match those in either ``properties`` or ``pattern_properties``.

            - If ``additional_properties`` is ``False``—all properties present in the object described by this schema
              must correspond to a property matched in either ``properties`` or ``pattern_properties``.

        - dependencies (Dict[str, Dict[str, Union[JSONSchematic, Sequence[str]]]]):

            A dictionary mapping properties of the object instance described by this schema to a mapping other
            properties and either:

                - A sub-schema for validation of the second property when the first property is present on
                  the object instance described by this schema.
                - A list of properties which must *also* be present when the first and second properties are present on
                  the object instance described by this schema.

        - enum (Sequence): The value/instance described by this schema should be among those in this sequence.

        - data_type (str|Sequence): The value/instance described by this schema should be of the types indicated
          (if this is a string), or *one of* the types indicated (if this is a sequence).

            - "null"
            - "boolean"
            - "object"
            - "array"
            - "number"
            - "string"

        - format (str|Sequence):

            - "date-time": A date and time in the format YYYY-MM-DDThh:mm:ss.sTZD (eg 1997-07-16T19:20:30.45+01:00),
              YYYY-MM-DDThh:mm:ssTZD (eg 1997-07-16T19:20:30+01:00), or YYYY-MM-DDThh:mmTZD (eg 1997-07-16T19:20+01:00).
            - "email"
            - "hostname"
            - "ipv4"
            - "ipv6"
            - "uri"
            - "uriref": A URI or a relative reference.

        - all_of (Sequence[JSONSchematic]): The value/instance described by the schema should *also* be valid as
          described by all sub-schemas in this sequence.

        - any_of (Sequence[JSONSchematic]): The value/instance described by the schema should *also* be valid as
          described in at least one of the sub-schemas in this sequence.

        - one_of (Sequence[JSONSchematic]): The value/instance described by the schema should *also* be valid as
          described in one (but *only* one) of the sub-schemas in this sequence.

        - not (JSONSchematic): The value/instance described by this schema should *not* be valid as described by this
          sub-schema.

        - definitions (Dict[JSONSchematic]): A dictionary of sub-schemas, stored for the purpose of referencing
          these sub-schemas elsewhere in the schema.

        - required (Sequence[str]): A list of attributes which must be present on the object instance described by this
          schema.

        - default (Any): The value presumed if the value/instance described by this schema is absent.
    """

    def __init__(
        self,
        title=missing,  # type: Union[str, Missing]
        description=missing,  # type: Union[str, Missing]
        multiple_of=missing,  # type: Union[Number, Missing]
        maximum=missing,  # type: Union[Number, Missing]
        exclusive_maximum=missing,  # type: Union[bool, Missing]
        minimum=missing,  # type: Union[Number, Missing]
        exclusive_minimum=missing,  # type: Union[bool, Missing]
        max_length=missing,  # type: Union[int, Missing]
        min_length=missing,  # type: Union[int, Missing]
        pattern=missing,  # type: Union[str, Missing]
        items=missing,  # type: Union[JSONSchematic, Sequence[JSONSchematic], Missing]
        additional_items=missing,  # type: Union[JSONSchematic, bool, Missing]
        max_items=missing,  # type: Union[int, Missing]
        min_items=missing,  # type: Union[int, Missing]
        unique_items=missing,  # type: Union[bool, Missing]
        max_properties=missing,  # type: Union[int, Missing]
        min_properties=missing,  # type: Union[int, Missing]
        properties=missing,  # type: Union[Dict[str, JSONSchematic], Missing]
        pattern_properties=missing,  # type: Union[JSONSchematic, Missing]
        additional_properties=missing,  # type: Union[bool, JSONSchematic, Missing]
        dependencies=missing,  # type: Union[Dict[str, Dict[str, Union[JSONSchematic, Sequence[str]]]], Missing]
        enum=missing,  # type: Union[Sequence, Missing]
        data_type=missing,  # type: Union[str, Sequence, Missing]
        format=missing,  # type: Union[str, Sequence, Missing]
        all_of=missing,  # type: Union[Sequence[JSONSchematic], Missing]
        any_of=missing,  # type: Union[Sequence[JSONSchematic], Missing]
        one_of=missing,  # type: Union[Sequence[JSONSchematic], Missing]
        is_not=missing,  # type: Union[JSONSchematic, Missing]
        definitions=missing,  # type: Union[Dict[JSONSchematic], Missing]
        required=missing,  # type: Union[Sequence[str], Missing]
        default=missing,  # type: Union[Any, Missing]
    ):
        self.title = title  # type: Union[str, Missing]
        self.description = description  # type: Union[str, Missing]
        self.multiple_of = multiple_of  # type: Union[Number, Missing]
        self.maximum = maximum  # type: Union[Number, Missing]
        self.exclusive_maximum = exclusive_maximum  # type: Union[bool, Missing]
        self.minimum = minimum  # type: Union[Number, Missing]
        self.exclusive_minimum = exclusive_minimum  # type: Union[bool, Missing]
        self.max_length = max_length  # type: Union[int, Missing]
        self.min_length = min_length  # type: Union[int, Missing]
        self.pattern = pattern  # type: Union[str, Missing]
        self.items = items  # type: Union[JSONSchematic, Sequence[JSONSchematic], Missing]
        self.additional_items = additional_items  # type: Union[JSONSchematic, bool, Missing]
        self.max_items = max_items  # type: Union[int, Missing]
        self.min_items = min_items  # type: Union[int, Missing]
        self.unique_items = unique_items  # type: Union[bool, Missing]
        self.max_properties = max_properties  # type: Union[int, Missing]
        self.min_properties = min_properties  # type: Union[int, Missing]
        self.properties = properties  # type: Union[Dict[str, JSONSchematic], Missing]
        self.pattern_properties = pattern_properties  # type: Union[JSONSchematic, Missing]
        self.additional_properties = additional_properties  # type: Union[bool, JSONSchematic, Missing]
        self.dependencies = dependencies  # type: Union[Dict[str, Dict[str, Union[JSONSchematic, Sequence[str]]]], Missing]
        self.enum = enum  # type: Union[Sequence, Missing]
        self.data_type = data_type  # type: Union[str, Sequence, Missing]
        self.format = format  # type: Union[str, Sequence, Missing]
        self.all_of = all_of  # type: Union[Sequence[JSONSchematic], Missing]
        self.any_of = any_of  # type: Union[Sequence[JSONSchematic], Missing]
        self.one_of = one_of  # type: Union[Sequence[JSONSchematic], Missing]
        self.is_not = is_not  # type: Union[JSONSchematic, Missing]
        self.definitions = definitions  # type: Union[Dict[JSONSchematic], Missing]
        self.required = required  # type: Union[Sequence[str], Missing]
        self.default = default  # type: Union[Any, Missing]


class Components(JSONObject):

    def __init__(
        self,
        schemas=missing,  # type: Union[Dict[str, Union[JSONSchema, Reference]]]
    ):
        pass


class OpenAPI(JSONObject):

    def __init__(
        self,
        swagger=missing,  # type: Union[str, Missing]
        open_api=missing,  # type: Union[str, Missing]
        info=missing,  # type: Union[Info, Missing]
        host=missing,  # type: Union[str, Missing]
        servers=missing,  # type: Union[str, Missing]
        base_path=missing,  # type: Union[str, Missing]
        schemes=missing,  # type: Union[Sequence[str], Missing]
        tags=missing,  # type: Union[Dict[str, Tag], Missing]
        paths=missing,  # type: Union[Dict[str, Service], Missing]
        components=missing,  # type: Union[Components, Missing]
    ):
        # type: (...) -> None
        self.swagger = swagger  # type: Union[str, Missing]
        self.open_api = open_api  # type: Union[str, Missing]
        self.info = info  # type: Union[Info, Missing]
        self.host = host  # type: Union[str, Missing]
        self.servers = missing if servers is missing else list(servers)  # type: Union[List[Server], Missing]
        self.base_path = base_path  # type: Union[str, Missing]
        self.schemes = missing if schemes is missing else list(schemes)  # type: Union[List[str], Missing]
        self.tags = missing if tags is missing else tuple(t for t in tags)  # type: Union[Sequence[Tag], Missing]
        self.paths = paths  # type: Union[Dict[str, Service], Missing]
        self.components = components  # type: Union[Components, Missing]


# Map schemas to objects

from openswallow.model import schemas

_schemas = {}

for k in dir(schemas):
    v = getattr(schemas, k)
    if isinstance(v, type) and (Schema in bases(v)):
        _schemas[k] = v

for k, v in copy(locals()).items():
    if isinstance(v, type) and (JSONObject in bases(v)):
        sn = v.__name__ + 'Schema'
        if sn in _schemas:
            _schema = _schemas[sn]
            v.__schema__ = _schema
            _schema.__model__ = v
