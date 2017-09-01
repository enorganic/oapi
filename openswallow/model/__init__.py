import collections
from copy import copy
from numbers import Number
from typing import List, Union, Any

from marshmallow import missing, Schema

Missing = type(missing)


def get_schema(model):
    # type: (type) -> schemas.JSONObjectSchema
    return model.__schema__


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
        return get_schema(self)(strict=True, many=False).dumps(self, many=False).data


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


class Parameter(JSONObject):
    """
    Properties:

        - name (str)

        - location (str):

            - "path"
            - "query"
            - "header"
            - "cookie"

        - description (str)

        - required (bool)

        - depracated (bool)

        - allow_empty_value (bool): Sets the ability to pass empty-valued parameters. This is valid only for query
          parameters and allows sending a parameter with an empty value. The default value is ``False``. If ``style``
          is used, and if ``behavior`` is inapplicable (cannot be serialized), the value of ``allow_empty_value`` will
          be ignored.

        - style (str): Describes how the parameter value will be serialized, depending on the type of the parameter
          value.

            - "matrix": Path-style parameters defined by `RFC6570 <https://tools.ietf.org/html/rfc6570#section-3.2.7>`.
            - "label": Label-style parameters defined by `RFC6570 <https://tools.ietf.org/html/rfc6570#section-3.2.5>`.
            - "form": Form style parameters defined by `RFC6570 <https://tools.ietf.org/html/rfc6570#section-3.2.8>`.
            - "simple": Simple style parameters defined by
              `RFC6570 <https://tools.ietf.org/html/rfc6570#section-3.2.2>`.
            - "spaceDelimited": Space separated array values.
            - "pipeDelimited": Pipe separated array values.
            - "deepObject": Provides a simple way of rendering nested objects using form parameters.

          Default values (based on value of ``location``):

            - query: "form"
            - path: "simple"
            - header: "simple"
            - cookie: "form"

          https://swagger.io/specification/#style-values-52

        - explode (bool): When this is ``True``, array or object parameter values generate separate parameters for
          each value of the array or key-value pair of the map. For other types of parameters this property has no
          effect. When ``style`` is "form", the default value is ``True``. For all other styles, the default value is
          ``False``.

        - allow_reserved (bool): Determines whether the parameter value SHOULD allow reserved characters
          :/?#[]@!$&'()*+,;= (as defined by `RFC3986 <https://tools.ietf.org/html/rfc3986#section-2.2>`) to be included
          without percent-encoding. This property only applies to parameters with a location value of "query". The
          default value is ``False``.

        - schema (Schematic): The schema defining the type used for the parameter.

        - example (Any): Example of the media type. The example should match the specified schema and encoding
          properties if present. The ``example`` parameter should not be present if ``examples`` is present. If
          referencing a ``schema`` which contains an example—*this* example overrides the example provided by the
          ``schema``. To represent examples of media types that cannot naturally be represented in JSON or YAML, a
          string value can contain the example with escaping where necessary.

        - examples (Dict[str, Example]): Examples of the media type. Each example should contain a value in the correct
          format, as specified in the parameter encoding. The ``examples`` parameter should not be present if
          ``example`` is present. If referencing a ``schema`` which contains an example—*these* example override the
          example provided by the ``schema``. To represent examples of media types that cannot naturally be represented
          in JSON or YAML, a string value can contain the example with escaping where necessary.
    """

    def __init__(
        self,
        name=missing,  # type: Union[str, Missing]
        location=missing,  # type: Union[str, Missing]
        description=missing,  # type: Union[str, Missing]
        required=missing,  # type: Union[bool, Missing]
        depracated=missing,  # type: Union[bool, Missing]
        allow_empty_value=missing, # type: Union[bool, Missing]
        style=missing,  # type: Union[str, Missing]
        explode=missing, # type: Union[bool, Missing]
        allow_reserved=missing, # type: Union[bool, Missing]
        schema=missing, # type: Union[Schematic, Missing]
        example=missing, # type: Any
        examples=missing, # type: Union[Dict[str, Example], Missing]
    ):
        self.name = name  # type: Union[str, Missing]
        self.location = location  # type: Union[str, Missing]
        self.description = description  # type: Union[str, Missing]
        self.required = required  # type: Union[bool, Missing]
        self.depracated = depracated  # type: Union[bool, Missing]
        self.allow_empty_value = allow_empty_value  # type: Union[bool, Missing]
        self.style = style  # type: Union[str, Missing]
        self.explode = explode  # type: Union[bool, Missing]
        self.allow_reserved = allow_reserved  # type: Union[bool, Missing]
        self.schema = schema  # type: Union[Schematic, Missing]
        self.example = example  # type: Any
        self.examples = examples  # type: Union[Dict[str, Example], Missing]


class Header(JSONObject):
    """
    Properties:

        - description (str)

        - required (bool)

        - depracated (bool)

        - allow_empty_value (bool): Sets the ability to pass empty-valued parameters. This is valid only for query
          parameters and allows sending a parameter with an empty value. The default value is ``False``. If ``style``
          is used, and if ``behavior`` is inapplicable (cannot be serialized), the value of ``allow_empty_value`` will
          be ignored.

        - style (str): Describes how the parameter value will be serialized, depending on the type of the parameter
          value.

            - "matrix": Path-style parameters defined by `RFC6570 <https://tools.ietf.org/html/rfc6570#section-3.2.7>`.
            - "label": Label-style parameters defined by `RFC6570 <https://tools.ietf.org/html/rfc6570#section-3.2.5>`.
            - "form": Form style parameters defined by `RFC6570 <https://tools.ietf.org/html/rfc6570#section-3.2.8>`.
            - "simple": Simple style parameters defined by
              `RFC6570 <https://tools.ietf.org/html/rfc6570#section-3.2.2>`.
            - "spaceDelimited": Space separated array values.
            - "pipeDelimited": Pipe separated array values.
            - "deepObject": Provides a simple way of rendering nested objects using form parameters.

          Default value: "simple"

          https://swagger.io/specification/#style-values-52
    """

    def __init__(
        self,
        description=missing,  # type: Union[str, Missing]
        required=missing,  # type: Union[bool, Missing]
        depracated=missing,  # type: Union[bool, Missing]
        allow_empty_value=missing, # type: Union[bool, Missing]
        style=missing, # type: Union[str, Missing]
    ):
        self.description = description  # type: Union[str, Missing]
        self.required = required  # type: Union[bool, Missing]
        self.depracated = depracated  # type: Union[bool, Missing]
        self.allow_empty_value = allow_empty_value  # type: Union[bool, Missing]
        self.style = style  # type: Union[str, Missing]



class Headers(JSONObject):

    pass


class Content(JSONObject):

    pass


class Links(JSONObject):

    pass


class Response(JSONObject):

    def __init__(
        self,
        description=missing,  # type: Union[str, Missing]
        headers=missing,  # type: Union[Dict[str, Headers], Missing]
        content=missing,  # type: Union[Dict[str, Content], Missing]
        links=missing,  # type: Union[Dict[str, Links], Missing]
    ):
        # type: (...) -> None
        self.description = description  # type: Union[str, Missing]
        self.headers = headers  # type: Union[Dict[str, Headers], Missing]
        self.content = content  # type: Union[Dict[str, Content], Missing]
        self.links = links  # type: Union[Dict[str, Links], Missing]


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


class Discriminator(JSONObject):
    """
    Properties:

        - property_name (str): The name of the property which will hold the discriminating value.

        - mapping (dict): An object to hold mappings between payload values and schema names or references.

    https://swagger.io/specification/#discriminatorObject
    """

    def __init__(
        self,
        property_name=missing,  # type: Union[str, Missing]
        mapping=missing,  # type: Union[Dict[str], Missing]
    ):
        self.property_name = property_name  # type: Union[str, Missing]
        self.mapping = mapping  # type: Union[Dict[str], Missing]


class XMLMetadata(JSONObject):
    """
    Properties:

        - name (str): The element name.

        - name_space (str): The *absolute* URI of a namespace.

        - prefix (str): The prefix to be used with the name to reference the name-space.

        - attribute (bool): If ``True``, the property described is an attribute rather than a sub-element.

        - wrapped (bool): If ``True``, an array instance described by the schema will be wrapped by a tag (named
          according to the parent element's property, while ``name`` refers to the child element name).
    """

    def __init__(
        self,
        name=missing,  # type: Union[str, Missing]
        name_space=missing,  # type: Union[str, Missing]
        prefix=missing,  # type: Union[str, Missing]
        attribute=missing,  # type: Union[bool, Missing]
        wrapped=missing,  # type: Union[bool, Missing]
    ):
        self.name = name  # type: Union[str, Missing]
        self.name_space = name_space  # type: Union[str, Missing]
        self.prefix = prefix  # type: Union[str, Missing]
        self.attribute = attribute  # type: Union[bool, Missing]
        self.wrapped = wrapped  # type: Union[bool, Missing]


class ExternalDocumentation(JSONObject):
    """
    Properties:

        - description (str)
        - url (str)
    """

    def __init__(
        self,
        description=missing,  # type: Union[str, Missing]
        url=missing,  # type: Union[str, Missing]
    ):
        self.description = description  # type: Union[str, Missing]
        self.url = url  # type: Union[str, Missing]


class Schematic(JSONObject):
    """
    Instances of this class represent a JSON validation schema, as defined on <http://json-schema.org> and
    <https://swagger.io/specification/#schemaObject>.

    Properties:

        - title (str)

        - description (str)

        - multiple_of (Number): The numeric value this schema describes should be divisible by this number.

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

        - items (Schematic|Sequence[Schematic]):

            - If ``items`` is a sub-schema—each item in the array instance described by this schema should be valid as
              described by this sub-schema.

            - If ``items`` is a sequence of sub-schemas, the array instance described by this schema should be equal in
              length to this sequence, and each value should be valid as described by the sub-schema at the
              corresponding index within this sequence of sub-schemas.

        - additional_items (Schematic|bool): If ``additional_items`` is ``True``—the array instance described by
          this schema may contain additional values beyond those defined in ``items``.

        - max_items (int): The array instance described by this schema should contain no more than this number of
          items.

        - min_items (int): The array instance described by this schema should contain at least this number of
          items.

        - unique_items (bool): The array instance described by this schema should contain only unique items.

        - max_properties (int)

        - min_properties (int)

        - properties (Dict[str, Schematic]): Any properties of the object instance described by this schema which
          correspond to a key in this mapping should be valid as described by the sub-schema corresponding to that key.

        - pattern_properties (Schematic): Any properties of the object instance described by this schema which
          match a key in this mapping, when the key is evaluated as a regular expression, should be valid as described by
          the sub-schema corresponding to the matched key.

        - additional_properties (bool|Schematic):

            - If ``additional_properties`` is ``True``—properties may be present in the object described by
              this schema with names which do not match those in either ``properties`` or ``pattern_properties``.

            - If ``additional_properties`` is ``False``—all properties present in the object described by this schema
              must correspond to a property matched in either ``properties`` or ``pattern_properties``.

        - dependencies (Dict[str, Dict[str, Union[Schematic, Sequence[str]]]]):

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

        - all_of (Sequence[Schematic]): The value/instance described by the schema should *also* be valid as
          described by all sub-schemas in this sequence.

        - any_of (Sequence[Schematic]): The value/instance described by the schema should *also* be valid as
          described in at least one of the sub-schemas in this sequence.

        - one_of (Sequence[Schematic]): The value/instance described by the schema should *also* be valid as
          described in one (but *only* one) of the sub-schemas in this sequence.

        - is_not (Schematic): The value/instance described by this schema should *not* be valid as described by this
          sub-schema.

        - definitions (Dict[Schematic]): A dictionary of sub-schemas, stored for the purpose of referencing
          these sub-schemas elsewhere in the schema.

        - required (Sequence[str]): A list of attributes which must be present on the object instance described by this
          schema.

        - default (Any): The value presumed if the value/instance described by this schema is absent.

        The following properties are specific to OpenAPI (not part of the core `JSON Schema <http://json-schema.org>`):

        - nullable (bool): If ``True``, the value/instance described by this schema may be a null value (``None``).

        - discriminator (Discriminator): Adds support for polymorphism.

        - read_only (bool): If ``True``, the property described may be returned as part of a response, but should not
          be part of a request.

        - write_only (bool): If ``True``, the property described may be sent as part of a request, but should not
          be returned as part of a response.

        - xml (XML): Provides additional information describing XML representation of the property described by this
          schema.

        - external_docs (ExternalDocumentation)

        - example (Any)

        - depracated (bool): If ``True``, the property or instance described by this schema should be phased out, as
          if will no longer be supported in future versions.
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
        items=missing,  # type: Union[Schematic, Sequence[Schematic], Missing]
        additional_items=missing,  # type: Union[Schematic, bool, Missing]
        max_items=missing,  # type: Union[int, Missing]
        min_items=missing,  # type: Union[int, Missing]
        unique_items=missing,  # type: Union[bool, Missing]
        max_properties=missing,  # type: Union[int, Missing]
        min_properties=missing,  # type: Union[int, Missing]
        properties=missing,  # type: Union[Dict[str, Schematic], Missing]
        pattern_properties=missing,  # type: Union[Schematic, Missing]
        additional_properties=missing,  # type: Union[bool, Schematic, Missing]
        dependencies=missing,  # type: Union[Dict[str, Dict[str, Union[Schematic, Sequence[str]]]], Missing]
        enum=missing,  # type: Union[Sequence, Missing]
        data_type=missing,  # type: Union[str, Sequence, Missing]
        format=missing,  # type: Union[str, Sequence, Missing]
        all_of=missing,  # type: Union[Sequence[Schematic], Missing]
        any_of=missing,  # type: Union[Sequence[Schematic], Missing]
        one_of=missing,  # type: Union[Sequence[Schematic], Missing]
        is_not=missing,  # type: Union[Schematic, Missing]
        definitions=missing,  # type: Union[Dict[Schematic], Missing]
        required=missing,  # type: Union[Sequence[str], Missing]
        default=missing,  # type: Union[Any, Missing]
        discriminator=missing,  # type: Union[Discriminator, Missing]
        read_only=missing,  # type: Union[bool, Missing]
        write_only=missing,  # type: Union[bool, Missing]
        xml=missing,  # type: Union[XMLMetadata, Missing]
        external_docs=missing,  # type: Union[ExternalDocumentation, Missing]
        example=missing,  # type: Any
        depracated=missing,  # type: Union[bool, Missing]
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
        self.items = items  # type: Union[Schematic, Sequence[Schematic], Missing]
        self.additional_items = additional_items  # type: Union[Schematic, bool, Missing]
        self.max_items = max_items  # type: Union[int, Missing]
        self.min_items = min_items  # type: Union[int, Missing]
        self.unique_items = unique_items  # type: Union[bool, Missing]
        self.max_properties = max_properties  # type: Union[int, Missing]
        self.min_properties = min_properties  # type: Union[int, Missing]
        self.properties = properties  # type: Union[Dict[str, Schematic], Missing]
        self.pattern_properties = pattern_properties  # type: Union[Schematic, Missing]
        self.additional_properties = additional_properties  # type: Union[bool, Schematic, Missing]
        self.dependencies = dependencies  # type: Union[Dict[str, Dict[str, Union[Schematic, Sequence[str]]]], Missing]
        self.enum = enum  # type: Union[Sequence, Missing]
        self.data_type = data_type  # type: Union[str, Sequence, Missing]
        self.format = format  # type: Union[str, Sequence, Missing]
        self.all_of = all_of  # type: Union[Sequence[Schematic], Missing]
        self.any_of = any_of  # type: Union[Sequence[Schematic], Missing]
        self.one_of = one_of  # type: Union[Sequence[Schematic], Missing]
        self.is_not = is_not  # type: Union[Schematic, Missing]
        self.definitions = definitions  # type: Union[Dict[Schematic], Missing]
        self.required = required  # type: Union[Sequence[str], Missing]
        self.default = default  # type: Union[Any, Missing]
        self.discriminator = discriminator  # type: Union[Discriminator, Missing]
        self.read_only = missing  # type: Union[bool, Missing]
        self.write_only = read_only  # type: Union[bool, Missing]
        self.xml = xml  # type: Union[XMLMetadata, Missing]
        self.external_docs = external_docs  # type: Union[ExternalDocumentation, Missing]
        self.example = example  # type: Any
        self.depracated = depracated  # type: Union[bool, Missing]


class Components(JSONObject):

    def __init__(
        self,
        schemas=missing,  # type: Union[Dict[str, Union[JSONSchema, Reference]]]
        responses=missing,  # type: Union[Dict[str, Union[JSONSchema, Reference]]]
    ):
        schemas = schemas  # type: Union[Dict[str, Union[JSONSchema, Reference]]]


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


from openswallow.model import schemas


def set_schema(model, schema):
    # type: (type, type)
    if not issubclass(model, JSONObject):
        raise TypeError(
            'This function requires a sub-class of ``openswallow.model.JSONObject``, not ``%s``' % (
                repr(model)
            )
        )
    elif not issubclass(schema, schemas.JSONObjectSchema):
        raise TypeError(
            'This function requires a sub-class of ``openswallow.model.schemas.JSONObjectSchema``, not ``%s``' % (
                repr(schema)
            )
        )
    model.__schema__ = schema
    schema.__model__ = model


# Map schemas to objects


_schemas = {}

for _k in dir(schemas):
    _v = getattr(schemas, _k)
    if isinstance(_v, type) and (issubclass(_v, Schema)):
        _schemas[_k] = _v

for _k, _v in copy(locals()).items():
    if isinstance(_v, type) and (issubclass(_v, JSONObject)):
        _sn = _v.__name__ + 'Schema'
        if _sn in _schemas:
            _schema = _schemas[_sn]
            set_schema(_v, _schema)
        elif _sn != 'JSONObjectSchema':
            raise KeyError(_sn)
