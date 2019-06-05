"""

Version 2x: https://swagger.io/docs/specification/2-0/basic-structure/
Version 3x: https://swagger.io/specification

"""

# region Compatibility

from __future__ import nested_scopes, generators, division, absolute_import, with_statement, \
   print_function, unicode_literals

from sob.utilities.compatibility import backport

backport()  # noqa

# endregion

from copy import deepcopy
from numbers import Number

try:
    import typing
    from typing import Union, Any
except ImportError:
    typing = Union = Any = None

import sob


class Object(sob.model.Object):

    def __init__(
        self,
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)


_object_hooks = sob.hooks.writable(Object)  # type: hooks.Object


def _object_before_setitem(self, key, value):
    # type: (Object, str, Any) -> Tuple[str, Any]
    """
    This hook allows for the use of extension attributes
    """

    if key[:2] == 'x-':
        # Look for a matching property, and if none exists--create one
        try:
            self._get_key_property_name(key)
        except KeyError:
            meta_ = sob.meta.writable(self)
            if meta_.properties is None:
                meta_.properties = sob.meta.Properties()
            property_name = sob.utilities.property_name(key)
            meta_.properties[property_name] = sob.properties.Property(name=key)

    return key, value


_object_hooks.before_setitem = _object_before_setitem


class Array(sob.model.Array):

    pass


class Dictionary(sob.model.Dictionary):

    pass


class Reference(Object):

    def __init__(
        self,
        _=None,  # type: Optional[typing.Mapping]
        ref=None,  # type: Optional[str]
    ):
        self.ref = ref
        super().__init__(_)


_reference_hooks = sob.hooks.writable(Reference)


def _reference_before_unmarshal(data):
    # type: (typing.Mapping) -> typing.Mapping
    """
    This prevents any attribute except `$ref` from being applied to references
    """

    if data and ('$ref' in data):
        for key in (set(data.keys()) - {'$ref'}):
            del data[key]

    return data


_reference_hooks.before_unmarshal = _reference_before_unmarshal


sob.meta.writable(Reference).properties = [
    ('ref', sob.properties.String(name='$ref'))
]


class Contact(Object):
    """
    https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.0.md#contactObject
    """

    def __init__(
        self,
        _=None,  # type: Optional[typing.Mapping]
        name=None,  # type: Optional[str]
        url=None,  # type: Optional[str]
        email=None,  # type: Optional[str]
    ):
        # type: (...) -> None
        self.name = name
        self.url = url
        self.email = email
        super().__init__(_)


sob.meta.writable(Contact).properties = [
    ('name', sob.properties.String()),
    ('url', sob.properties.String()),
    ('email', sob.properties.String()),
]


class License(Object):
    """
    https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.0.md#licenseObject
    """

    def __init__(
        self,
        _=None,  # type: Optional[typing.Mapping]
        name=None,  # type: Optional[str]
        url=None,  # type: Optional[str]
    ):
        # type: (...) -> None
        self.name = name
        self.url = url
        super().__init__(_)


sob.meta.writable(License).properties = [
    ('name', sob.properties.String(required=True)),
    ('url', sob.properties.String()),
]


class Info(Object):
    """
    https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.0.md#infoObject
    """

    def __init__(
        self,
        _=None,  # type: Optional[typing.Mapping]
        title=None,  # type: Optional[str]
        description=None,  # type: Optional[str]
        terms_of_service=None,  # type: Optional[str]
        contact=None,  # type: Optional[Contact]
        license_=None,  # type: Optional[License]
        version=None,  # type: Optional[str]
    ):
        # type: (...) -> None
        self.title = title
        self.description = description
        self.terms_of_service = terms_of_service
        self.contact = contact
        self.license_ = license_
        self.version = version
        super().__init__(_)


sob.meta.writable(Info).properties = [
    ('title', sob.properties.String(required=True)),
    ('description', sob.properties.String()),
    ('terms_of_service', sob.properties.String(name='termsOfService')),
    ('contact', sob.properties.Property(types=(Contact,))),
    ('license_', sob.properties.Property(types=(License,), name='license')),
    ('version', sob.properties.String(required=True)),
]


class Tag(Object):
    """
    https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.0.md#tagObject
    """

    def __init__(
        self,
        _=None,  # type: Optional[typing.Mapping]
        name=None,  # type: Optional[str]
        description=None,  # type: Optional[str]
        external_docs=None,  # type: Optional[ExternalDocumentation]
    ):
        # type: (...) -> None
        self.name = name
        self.description = description
        self.external_docs = external_docs
        super().__init__(_)


# Metadata definitions for `Tag` postponed until after `ExternalDocumentation` has been defined


class Link(Object):

    def __init__(
        self,
        _=None,  # type: Optional[typing.Mapping]
        rel=None,  # type: Optional[str]
        href=None,  # type: Optional[str]
    ):
        self.rel = rel
        self.href = href
        super().__init__(_)


sob.meta.writable(Link).properties = [
    ('rel', sob.properties.String()),
    ('href', sob.properties.String()),
]


class Schema(Object):
    """
    https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.0.md#schemaObject
    http://json-schema.org

    Properties:

        - title (str)

        - description (str)

        - multiple_of (Number): The numeric value this schema describes should be divisible by this number.

        - maximum (Number): The number this schema describes should be less than or equal to this value, or less than
          this value, depending on the value of `exclusive_maximum`.

        - exclusive_maximum (bool): If `True`, the numeric instance described by this schema must be *less than*
          `maximum`. If `False`, the numeric instance described by this schema can be less than or *equal to*
          `maximum`.

        - minimum (Number): The number this schema describes should be greater than or equal to this value, or greater
          than this value, depending on the value of `exclusive_minimum`.

        - exclusive_minimum (bool): If `True`, the numeric instance described by this schema must be *greater than*
          `minimum`. If `False`, the numeric instance described by this schema can be greater than or *equal to*
          `minimum`.

        - max_length (int): The number of characters in the string instance described by this schema must be less than,
          or equal to, the value of this property.

        - min_length (int): The number of characters in the string instance described by this schema must be greater
          than, or equal to, the value of this property.

        - pattern (str): The string instance described by this schema should match this regular expression (ECMA 262).

        - items (Reference|Schema|[Schema]):

            - If `items` is a sub-schema--each item in the array instance described by this schema should be valid as
              described by this sub-schema.

            - If `items` is a sequence of sub-schemas, the array instance described by this schema should be equal in
              length to this sequence, and each value should be valid as described by the sub-schema at the
              corresponding index within this sequence of sub-schemas.

        - max_items (int): The array instance described by this schema should contain no more than this number of
          items.

        - min_items (int): The array instance described by this schema should contain at least this number of
          items.

        - unique_items (bool): The array instance described by this schema should contain only unique items.

        - max_properties (int)

        - min_properties (int)

        - sob.properties ({str:Schema}): Any sob.properties of the object instance described by this schema which
          correspond to a name in this mapping should be valid as described by the sub-schema corresponding to that name.

        - additional_properties (bool|Schema):

            - If `additional_properties` is `True`--sob.properties may be present in the object described by
              this schema with names which do not match those in `sob.properties`.

            - If `additional_properties` is `False`--all sob.properties present in the object described by this schema
              must correspond to a property matched in either `sob.properties`.

        - enum ([Any]): The value/instance described by this schema should be among those in this sequence.

        - type_ (str|[str]): The value/instance described by this schema should be of the value_types indicated
          (if this is a string), or *one of* the value_types indicated (if this is a sequence).

            - "null"
            - "boolean"
            - "object"
            - "array"
            - "number"
            - "string"

        - format_ (str|[str]):

            - "date-time": A date and time in the format YYYY-MM-DDThh:mm:ss.sTZD (eg 1997-07-16T19:20:30.45+01:00),
              YYYY-MM-DDThh:mm:ssTZD (eg 1997-07-16T19:20:30+01:00), or YYYY-MM-DDThh:mmTZD (eg 1997-07-16T19:20+01:00).
            - "email"
            - "hostname"
            - "ipv4"
            - "ipv6"
            - "uri"
            - "uriref": A URI or a relative reference.

        - all_of ([Schema]): The value/instance described by the schema should *also* be valid as
          described by all sub-schemas in this sequence.

        - any_of ([Schema]): The value/instance described by the schema should *also* be valid as
          described in at least one of the sub-schemas in this sequence.

        - one_of ([Schema]): The value/instance described by the schema should *also* be valid as
          described in one (but *only* one) of the sub-schemas in this sequence.

        - is_not (Schema): The value/instance described by this schema should *not* be valid as described by this
          sub-schema.

        - definitions ({str:Schema}): A dictionary of sub-schemas, stored for the purpose of referencing
          these sub-schemas elsewhere in the schema.

        - required ([str]): A list of attributes which must be present on the object instance described by this
          schema.

        - default (Any): The value presumed if the value/instance described by this schema is absent.

        The following sob.properties are specific to OpenAPI (not part of the core `JSON Schema <http://json-schema.org>`):

        - nullable (bool): If `True`, the value/instance described by this schema may be a null value (`None`).

        - discriminator (Discriminator): Adds support for polymorphism.

        - read_only (bool): If `True`, the property described may be returned as part of a response, but should not
          be part of a request.

        - write_only (bool): If `True`, the property described may be sent as part of a request, but should not
          be returned as part of a response.

        - xml (XML): Provides additional information describing XML representation of the property described by this
          schema.

        - external_docs (ExternalDocumentation)

        - example (Any)

        - definitions (Any)

        - depracated (bool): If `True`, the property or instance described by this schema should be phased out, as
          if will no longer be supported in future versions.
    """

    def __init__(
        self,
        _=None,  # type: Optional[typing.Mapping]
        title=None,  # type: Optional[str]
        description=None,  # type: Optional[str]
        multiple_of=None,  # type: Optional[Number]
        maximum=None,  # type: Optional[Number]
        exclusive_maximum=None,  # type: Optional[bool]
        minimum=None,  # type: Optional[Number]
        exclusive_minimum=None,  # type: Optional[bool]
        max_length=None,  # type: Optional[int]
        min_length=None,  # type: Optional[int]
        pattern=None,  # type: Optional[str]
        items=None,  # type: Optional[Reference, Schema, Sequence[Schema]]
        max_items=None,  # type: Optional[int]
        min_items=None,  # type: Optional[int]
        unique_items=None,  # type: Optional[bool]
        max_properties=None,  # type: Optional[int]
        min_properties=None,  # type: Optional[int]
        properties=None,  # type: Optional[typing.Mapping[str, Schema]]
        additional_properties=None,  # type: Optional[bool, Schema]
        enum=None,  # type: Optional[Sequence]
        type_=None,  # type: Optional[str, Sequence]
        format_=None,  # type: Optional[str, Sequence]
        all_of=None,  # type: Optional[Sequence[Schema]]
        any_of=None,  # type: Optional[Sequence[Schema]]
        one_of=None,  # type: Optional[Sequence[Schema]]
        is_not=None,  # type: Optional[Schema]
        definitions=None,  # type: Optional[typing.Mapping[Schema]]
        required=None,  # type: Optional[Sequence[str]]
        default=None,  # type: Optional[Any]
        discriminator=None,  # type: Optional[Union[Discriminator, str]]
        read_only=None,  # type: Optional[bool]
        write_only=None,  # type: Optional[bool]
        xml=None,  # type: Optional[XML]
        external_docs=None,  # type: Optional[ExternalDocumentation]
        example=None,  # type: Any
        deprecated=None,  # type: Optional[bool]
        links=None,  # type: Optional[Sequence[Link]]
        nullable=None,  # type: Optional[bool]
    ):
        self.title = title
        self.description = description
        self.multiple_of = multiple_of
        self.maximum = maximum
        self.exclusive_maximum = exclusive_maximum
        self.minimum = minimum
        self.exclusive_minimum = exclusive_minimum
        self.max_length = max_length
        self.min_length = min_length
        self.pattern = pattern
        self.items = items
        self.max_items = max_items
        self.min_items = min_items
        self.unique_items = unique_items
        self.max_properties = max_properties
        self.min_properties = min_properties
        self.properties = properties
        self.additional_properties = additional_properties
        self.enum = enum
        self.type_ = type_
        self.format_ = format_
        self.all_of = all_of
        self.any_of = any_of
        self.one_of = one_of
        self.is_not = is_not
        self.definitions = definitions
        self.required = required
        self.default = default
        self.discriminator = discriminator
        self.read_only = read_only
        self.write_only = write_only
        self.xml = xml
        self.external_docs = external_docs
        self.example = example
        self.deprecated = deprecated
        self.links = links
        self.nullable = nullable
        super().__init__(_)
        

# ...definitions are postponed until dependencies are defined


class Example(Object):
    """
    https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.0.md#exampleObject
    """

    def __init__(
        self,
        _=None,  # type: Optional[typing.Mapping]
        summary=None,  # type: Optional[str]
        description=None,  # type: Optional[str]
        value=None,  # type: Any
        external_value=None,  # type: Optional[str]
    ):
        self.summary = summary
        self.description = description
        self.value = value
        self.external_value = external_value
        super().__init__(_)


sob.meta.writable(Example).properties = [
    ('summary', sob.properties.String(versions=('openapi>=3.0',))),
    ('description', sob.properties.String(versions=('openapi>=3.0',))),
    ('value', sob.properties.Property(versions=('openapi>=3.0',))),
    ('external_value', sob.properties.String(name='externalValue', versions=('openapi>=3.0',))),
]


class Encoding(Object):

    """
    https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.0.md#encodingObject
    """

    def __init__(
        self,
        _=None,  # type: Optional[typing.Mapping]
        content_type=None,  # type: Optional[str]
        headers=None,  # type: Optional[typing.Mapping[str, Union[Header, Reference]]]
        style=None,  # type: Optional[str]
        explode=None,  # type: Optional[bool]
        allow_reserved=None,  # type: Optional[bool]
    ):
        self.content_type = content_type
        self.headers = headers
        self.style = style
        self.explode = explode
        self.allow_reserved = allow_reserved
        super().__init__(_)


# ...definitions for `Encoding` are delayed until after the `Headers` definition


class MediaType(Object):
    """
    https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.0.md#mediaTypeObject
    """

    def __init__(
        self,
        _=None,  # type: Optional[typing.Mapping]
        schema=None,  # type: Optional[Schema, Reference]
        example=None,  # type: Any
        examples=None,  # type: Union[typing.Mapping[str, Union[Example, Reference]]]
        encoding=None,  # type: Union[typing.Mapping[str, Union[Encoding, Reference]]]
    ):
        self.schema = schema
        self.example = example
        self.examples = examples
        self.encoding = encoding
        super().__init__(_)


sob.meta.writable(MediaType).properties = [
    ('schema', sob.properties.Property(types=(Reference, Schema), versions=('openapi>=3.0',))),
    ('example', sob.properties.Property(versions=('openapi>=3.0',))),
    ('examples', sob.properties.Dictionary(value_types=(Reference, Example), versions=('openapi>=3.0',))),
    ('encoding', sob.properties.Dictionary(value_types=(Reference, Encoding), versions=('openapi>=3.0',))),
]


class Items(Object):

    def __init__(
        self,
        _=None,  # type: Optional[typing.Mapping]
        type_=None,  # type: Optional[str]
        format_=None,  # type: Optional[str, Sequence]
        items=None,  # type: Optional[Items]
        collection_format=None,  # type: Optional[str]
        default=None,  # type: Optional[Any]
        maximum=None,  # type: Optional[numbers.Number]
        exclusive_maximum=None,  # type: Optional[bool]
        minimum=None,  # type: Optional[numbers.Number]
        exclusive_minimum=None,  # type: Optional[bool]
        max_length=None,  # type: Optional[int]
        min_length=None,  # type: Optional[int]
        pattern=None,  # type: Optional[str]
        max_items=None,  # type: Optional[str]
        min_items=None,  # type: Optional[str]
        unique_items=None,  # type: Optional[bool]
        enum=None,  # type: Optional[Sequence[str]]
        multiple_of=None,  # type: Optional[Number]
    ):
        self.type_ = type_
        self.format_ = format_
        self.items = items
        self.collection_format = collection_format
        self.default = default
        self.maximum = maximum
        self.exclusive_maximum = exclusive_maximum
        self.minimum = minimum
        self.exclusive_minimum = exclusive_minimum
        self.max_length = max_length
        self.min_length = min_length
        self.pattern = pattern
        self.max_items = max_items
        self.min_items = min_items
        self.unique_items = unique_items
        self.enum = enum
        self.multiple_of = multiple_of
        super().__init__(_)


sob.meta.writable(Items).properties = [
    (
        'type_',
        sob.properties.Enumerated(
            name='type',
            values=(
                'array',
                'object',
                'file',
                'integer',
                'number',
                'string',
                'boolean'
            ),
            versions=('openapi<3.0')
        )
    ),
    (
        'format_',
        sob.properties.String(
            # values=lambda o: (
            #     None
            #     if o is None else
            #     ('int32', 'int64')
            #     if o.type_ == 'integer' else
            #     ('float', 'double')
            #     if o.type_ == 'number' else
            #     ('byte', 'binary', 'date', 'date-time', 'password')
            #     if o.type_ == 'string'
            #     else tuple()
            # ),
            name='format',
            versions=('openapi<3.0')
        )
    ),
    (
        'items',
        sob.properties.Property(types=(Items,), versions=('openapi<3.0'))
    ),
    (
        'collection_format',
        sob.properties.Enumerated(
            values=('csv', 'ssv', 'tsv', 'pipes'),
            name='collectionFormat',
            versions=('openapi<3.0')
        )
    ),
    (
        'default',
        sob.properties.Property()
    ),(
        'maximum',
        sob.properties.Number(versions=('openapi<3.0',))
    ),
    (
        'exclusive_maximum',
        sob.properties.Boolean(
            name='exclusiveMaximum',
            versions=('openapi<3.0',)
        )
    ),
    (
        'minimum',
        sob.properties.Number(versions=('openapi<3.0',))
    ),
    (
        'exclusive_minimum',
        sob.properties.Boolean(
            name='exclusiveMinimum',
            versions=('openapi<3.0',)
        )
    ),
    (
        'max_length',
        sob.properties.Integer(name='maxLength', versions=('openapi<3.0',))
    ),
    (
        'min_length',
        sob.properties.Integer(name='minLength', versions=('openapi<3.0',))
    ),
    (
        'pattern',
        sob.properties.String(versions=('openapi<3.0',))
    ),
    (
        'max_items',
        sob.properties.Integer(name='maxItems', versions=('openapi<3.0',))
    ),
    (
        'min_items',
        sob.properties.Integer(name='minItems', versions=('openapi<3.0',))
    ),
    (
        'unique_items',
        sob.properties.Boolean(
            name='uniqueItems',
            versions=('openapi<3.0',)
        )
    ),
    (
        'enum',
        sob.properties.Array(versions=('openapi<3.0',))
    ),
    (
        'multiple_of',
        sob.properties.Number(
            name='multipleOf',
            versions=('openapi<3.0',)
        )
    )
]


class Parameter(Object):
    """
    https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.0.md#parameterObject

    Properties:

        - name (str)

        - in_ (str):

            - "path"
            - "query"
            - "header"
            - "cookie"

        - description (str)

        - required (bool)

        - deprecated (bool)

        - allow_empty_value (bool): Sets the ability to pass empty-valued parameters. This is valid only for query
          parameters and allows sending a parameter with an empty value. The default value is `False`. If `style`
          is used, and if `behavior` is inapplicable (cannot be serialized), the value of `allow_empty_value` will
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

          Default values (based on value of `location`):

            - query: "form"
            - path: "simple"
            - header: "simple"
            - cookie: "form"

          https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.0.md#style-values-52

        - explode (bool): When this is `True`, array or object parameter values generate separate parameters for
          each value of the array or name-value pair of the map. For other value_types of parameters this property has no
          effect. When `style` is "form", the default value is `True`. For all other styles, the default value is
          `False`.

        - allow_reserved (bool): Determines whether the parameter value SHOULD allow reserved characters
          :/?#[]@!$&'()*+,;= (as defined by `RFC3986 <https://tools.ietf.org/html/rfc3986#section-2.2>`) to be included
          without percent-encoding. This property only applies to parameters with a location value of "query". The
          default value is `False`.

        - schema (Schema): The schema defining the type used for the parameter.

        - example (Any): Example of the media type. The example should match the specified schema and encoding
          sob.properties if present. The `example` parameter should not be present if `examples` is present. If
          referencing a `schema` which contains an example--*this* example overrides the example provided by the
          `schema`. To represent examples of media value_types that cannot naturally be represented in JSON or YAML, a
          string value can contain the example with escaping where necessary.

        - examples ({str:Example}): Examples of the media type. Each example should contain a value in the correct
          format, as specified in the parameter encoding. The `examples` parameter should not be present if
          `example` is present. If referencing a `schema` which contains an example--*these* example override the
          example provided by the `schema`. To represent examples of media value_types that cannot naturally be represented
          in JSON or YAML, a string value can contain the example with escaping where necessary.

          https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.0.md#format

        - content ({str:MediaType}): A map containing the representations for the parameter. The name is the media type
          and the value describing it. The map must only contain one entry.

    ...for version 2x compatibility:

        - type_ (str)

        - enum ([Any])
    """

    def __init__(
        self,
        _=None,  # type: Optional[typing.Mapping]
        name=None,  # type: Optional[str]
        in_=None,  # type: Optional[str]
        description=None,  # type: Optional[str]
        required=None,  # type: Optional[bool]
        deprecated=None,  # type: Optional[bool]
        allow_empty_value=None, # type: Optional[bool]
        style=None,  # type: Optional[str]
        explode=None, # type: Optional[bool]
        allow_reserved=None, # type: Optional[bool]
        schema=None, # type: Optional[Schema]
        example=None, # type: Any
        examples=None, # type: Optional[typing.Mapping[str, Example]]
        content=None,  # type: Optional[typing.Mapping[str, MediaType]]
        type_=None,  # type: Optional[str]
        default=None,  # type: Any
        maximum=None,  # type: Optional[numbers.Number]
        exclusive_maximum=None,  # type: Optional[bool]
        minimum=None,  # type: Optional[numbers.Number]
        exclusive_minimum=None,  # type: Optional[bool]
        max_length=None,  # type: Optional[int]
        min_length=None,  # type: Optional[int]
        pattern=None,  # type: Optional[str]
        max_items=None,  # type: Optional[str]
        min_items=None,  # type: Optional[str]
        unique_items=None,  # type: Optional[bool]
        format_=None,  # type: Optional[str]
        enum=None,  # type: Optional[Sequence[str]]
        multiple_of=None,  # type: Optional[Number]
        collection_format=None,  # type: Optional[str]
        items=None,  # type: Optional[Schema]
    ):
        self.name = name
        self.in_ = in_
        self.description = description
        self.required = required
        self.deprecated = deprecated
        self.allow_empty_value = allow_empty_value
        self.style = style
        self.explode = explode
        self.allow_reserved = allow_reserved
        self.schema = schema
        self.example = example
        self.examples = examples
        self.content = content
        self.type_ = type_
        self.default = default
        self.maximum = maximum
        self.exclusive_maximum = exclusive_maximum
        self.minimum = minimum
        self.exclusive_minimum = exclusive_minimum
        self.max_length = max_length
        self.min_length = min_length
        self.pattern = pattern
        self.max_items = max_items
        self.min_items = min_items
        self.unique_items = unique_items
        self.enum = enum
        self.multiple_of = multiple_of
        self.format_ = format_
        self.collection_format = collection_format
        self.items = items
        super().__init__(_)


sob.meta.writable(Parameter).properties = [
    ('name', sob.properties.String(required=True)),
    (
        'in_',
        sob.properties.Enumerated(
            values=('query', 'header', 'path', 'formData', 'body'),
            name='in',
            required=True
        )
    ),
    ('description', sob.properties.String()),
    ('required', sob.properties.Boolean()),
    ('deprecated', sob.properties.Boolean()),
    ('allow_empty_value', sob.properties.Boolean(name='allowEmptyValue')),
    ('style', sob.properties.String(versions=('openapi>=3.0',))),
    ('explode', sob.properties.Boolean(versions=('openapi>=3.0',))),
    ('allow_reserved', sob.properties.Boolean(name='allowReserved', versions=('openapi>=3.0',))),
    (
        'schema',
        sob.properties.Property(
            types=(Reference, Schema),
        )
    ),
    ('example', sob.properties.Property(versions=('openapi>=3.0',))),
    (
        'examples',
        sob.properties.Dictionary(
            value_types=(Reference, Example),
            versions=('openapi>=3.0',)
        )
    ),
    (
        'content',
        sob.properties.Dictionary(
            value_types=(MediaType,),
            versions=('openapi>=3.0')
        ),
    ),
    (
        'type_',
        sob.properties.Enumerated(
            values=(
                'array',
                'object',
                'file',
                'integer',
                'number',
                'string',
                'boolean'
            ),
            name='type',
            versions=('openapi<3.0',)
        )
    ),
    (
        'default',
        sob.properties.Property(
            versions=('openapi<3.0',)
        )
    ),
    (
        'maximum',
        sob.properties.Number(versions=('openapi<3.0',))
    ),
    (
        'exclusive_maximum',
        sob.properties.Boolean(
            name='exclusiveMaximum',
            versions=('openapi<3.0',)
        )
    ),
    (
        'minimum',
        sob.properties.Number(versions=('openapi<3.0',))
    ),
    (
        'exclusive_minimum',
        sob.properties.Boolean(
            name='exclusiveMinimum',
            versions=('openapi<3.0',)
        )
    ),
    (
        'max_length',
        sob.properties.Integer(name='maxLength', versions=('openapi<3.0',))
    ),
    (
        'min_length',
        sob.properties.Integer(name='minLength', versions=('openapi<3.0',))
    ),
    (
        'pattern',
        sob.properties.String(versions=('openapi<3.0',))
    ),
    (
        'max_items',
        sob.properties.Integer(name='maxItems', versions=('openapi<3.0',))
    ),
    (
        'min_items',
        sob.properties.Integer(name='minItems', versions=('openapi<3.0',))
    ),
    (
        'unique_items',
        sob.properties.Boolean(
            name='uniqueItems',
            versions=('openapi<3.0',)
        )
    ),
    (
        'enum',
        sob.properties.Array(versions=('openapi<3.0',))
    ),
    (
        'format_',
        sob.properties.String(
            # values=(
            #     'int32', 'int64',  # type_ == 'integer'
            #     'float', 'double',  # type_ == 'number'
            #     'byte', 'binary', 'date', 'date-time', 'password',  # type_ == 'string'
            # ),
            name='format',
            versions=('openapi<3.0')
        )
    ),
    (
        'collection_format',
        sob.properties.Enumerated(
            values=('csv', 'ssv', 'tsv', 'pipes', 'multi'),
            name='collectionFormat',
            versions=('openapi<3.0',)
        )
    ),
    (
        'items',
        sob.properties.Property(
            types=(Items,),
            versions=('openapi<3.0',)
        )
    ),
    (
        'multiple_of',
        sob.properties.Number(
            name='multipleOf',
            versions=('openapi<3.0',)
        )
    )
]


def _parameter_after_validate(o):
    # type: (Parameter) -> Parameter
    if (o.content is not None) and len(tuple(o.content.keys())) > 1:
        raise sob.errors.ValidationError(
            '`%s.content` may have only one mapped value.:\n%s' % (
                sob.utilities.qualified_name(type(o)), repr(o)
            )
        )
    if (o.content is not None) and (o.schema is not None):
        raise sob.errors.ValidationError(
            'An instance of `%s` may have a `schema` property or a `content` ' % sob.utilities.qualified_name(type(o)) +
            'property, but not *both*:\n' + repr(o)
        )
    if o.format_ in (
        'int32', 'int64',  # type_ == 'integer'
        'float', 'double',  # type_ == 'number'
        'byte', 'binary', 'date', 'date-time', 'password',  # type_ == 'string'
    ):
        if o.type_ == 'integer' and (
            o.format_ not in ('int32', 'int64', None)
        ):
            qn = sob.utilities.qualified_name(type(o))
            raise sob.errors.ValidationError(
                '"%s" in not a valid value for `%S.format_` in this circumstance. ' % (
                    o.format_,
                    qn
                ) +
                '`%s.format_` may be "int32" or "int64" when ' % qn +
                '`%s.type_` is "integer".' % qn
            )
        elif o.type_ == 'number' and (
            o.format_ not in ('float', 'double', None)
        ):
            qn = sob.utilities.qualified_name(type(o))
            raise sob.errors.ValidationError(
                '"%s" in not a valid value for `%s.format_` in this circumstance. ' % (o.format_, qn) +
                '`%s.format_` may be "float" or "double" when ' % qn +
                '`%s.type_` is "number".' % (qn, )
            )
        elif o.type_ == 'string' and (
            o.format_ not in ('byte', 'binary', 'date', 'date-time', 'password', None)
        ):
            qn = sob.utilities.qualified_name(type(o))
            raise sob.errors.ValidationError(
                '"%s" in not a valid value for `%s.format_` in this circumstance. ' % (o.format_, qn) +
                '`%s.format_` may be "byte", "binary", "date", "date-time" or "password" when ' % qn +
                '`%s.type_` is "string".' % (qn, )
            )
    return o


sob.hooks.writable(Parameter).after_validate = _parameter_after_validate


class Header(Object):

    def __init__(
        self,
        _=None,  # type: Optional[typing.Mapping]
        description=None,  # type: Optional[str]
        required=None,  # type: Optional[bool]
        deprecated=None,  # type: Optional[bool]
        allow_empty_value=None, # type: Optional[bool]
        style=None,  # type: Optional[str]
        explode=None, # type: Optional[bool]
        allow_reserved=None, # type: Optional[bool]
        schema=None, # type: Optional[Schema]
        example=None, # type: Any
        examples=None, # type: Optional[typing.Mapping[str, Example]]
        content=None,  # type: Optional[typing.Mapping[str, MediaType]]
        type_=None,  # type: Optional[str]
        default=None,  # type: Any
        maximum=None,  # type: Optional[numbers.Number]
        exclusive_maximum=None,  # type: Optional[bool]
        minimum=None,  # type: Optional[numbers.Number]
        exclusive_minimum=None,  # type: Optional[bool]
        max_length=None,  # type: Optional[int]
        min_length=None,  # type: Optional[int]
        pattern=None,  # type: Optional[str]
        max_items=None,  # type: Optional[str]
        min_items=None,  # type: Optional[str]
        unique_items=None,  # type: Optional[bool]
        format_=None,  # type: Optional[str]
        enum=None,  # type: Optional[Sequence[str]]
        multiple_of=None,  # type: Optional[Number]
        collection_format=None,  # type: Optional[str]
        items=None,  # type: Optional[Schema]
    ):
        self.description = description
        self.required = required
        self.deprecated = deprecated
        self.allow_empty_value = allow_empty_value
        self.style = style
        self.explode = explode
        self.allow_reserved = allow_reserved
        self.schema = schema
        self.example = example
        self.examples = examples
        self.content = content
        self.type_ = type_
        self.default = default
        self.maximum = maximum
        self.exclusive_maximum = exclusive_maximum
        self.minimum = minimum
        self.exclusive_minimum = exclusive_minimum
        self.max_length = max_length
        self.min_length = min_length
        self.pattern = pattern
        self.max_items = max_items
        self.min_items = min_items
        self.unique_items = unique_items
        self.enum = enum
        self.multiple_of = multiple_of
        self.format_ = format_
        self.collection_format = collection_format
        self.items = items
        super().__init__(_)

_header_meta = sob.meta.writable(Header)
_header_meta.properties = deepcopy(sob.meta.read(Parameter).properties)
del _header_meta.properties['name']
del _header_meta.properties['in_']
_header_meta.properties['schema'].versions = ('openapi>=3.0',)
_header_meta.properties['type_'].values = (
    'array',
    'integer',
    'number',
    'string',
    'boolean'
)
_header_meta.properties['items'].types = (Items,)
_header_meta.properties['items'].required = lambda o: True if o.type_ == 'array' else False
_header_meta.properties['required'].versions = ('openapi>=3.0',)
_header_meta.properties['deprecated'].versions = ('openapi>=3.0',)
_header_meta.properties['allow_empty_value'].versions = ('openapi>=3.0',)


sob.meta.writable(Encoding).properties = [
    ('content_type', sob.properties.String(name='contentType')),
    ('headers', sob.properties.Dictionary(value_types=(Reference, Header))),
    ('style', sob.properties.String()),
    ('explode', sob.properties.Boolean()),
    ('allow_reserved', sob.properties.Boolean(name='allowReserved')),
]


class ServerVariable(Object):

    def __init__(
        self,
        _=None,  # type: Optional[typing.Mapping]
        enum=None,  # type: Optional[Sequence[str]]
        default=None,  # type: Optional[str]
        description=None,  # type: Optional[str]
    ):
        self.enum = enum
        self.default = default
        self.description = description
        super().__init__(_)


sob.meta.writable(ServerVariable).properties = [
    ('enum', sob.properties.Array(item_types=(str,))),
    ('default', sob.properties.String(required=True)),
    ('description', sob.properties.String()),
]


class Server(Object):
    """
    https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.0.md#serverObject
    """

    def __init__(
        self,
        _=None,  # type: Optional[typing.Mapping]
        url=None,  # type: Optional[str]
        description=None,  # type: Optional[str]
        variables=None  # type: Optional[typing.Mapping[str, ServerVariable]]
    ):
        # type: (...) -> None
        self.url = url
        self.description = description
        self.variables = variables
        super().__init__(_)


sob.meta.writable(Server).properties = [
    ('url', sob.properties.String(required=True)),
    ('description', sob.properties.String()),
    ('variables', sob.properties.Dictionary(value_types=(ServerVariable,))),
]


class Link_(Object):
    """
    https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.0.md#linkObject
    """

    def __init__(
        self,
        _=None,  # type: Optional[typing.Mapping]
        operation_ref=None,  # type: Optional[str]
        operation_id=None,  # type: Optional[str]
        parameters=None,  # type: Optional[typing.Mapping[str, Any]]
        request_body=None,  # type: Any
        description=None,  # type: Optional[str]
        server=None,  # type: Optional[Server]
    ):
        self.operation_ref = operation_ref
        self.operation_id = operation_id
        self.parameters = parameters
        self.request_body = request_body
        self.description = description
        self.server = server
        super().__init__(_)


sob.meta.writable(Link_).properties = [
    ('operation_ref', sob.properties.String(name='operationRef', versions=('openapi>=3.0',))),
    ('operation_id', sob.properties.String(name='operationId', versions=('openapi>=3.0',))),
    ('parameters', sob.properties.Dictionary(versions=('openapi>=3.0',))),
    ('request_body', sob.properties.Property(name='requestBody', versions=('openapi>=3.0',))),
    ('description', sob.properties.String(versions=('openapi>=3.0',))),
    ('server', sob.properties.Property(types=(Server,), versions=('openapi>=3.0',))),
]


class Response(Object):
    """
    https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.0.md#responseObject

    Properties:

        - description (str): A short description of the response. `CommonMark syntax<http://spec.commonmark.org/>` may
          be used for rich text representation.

        - headers ({str:Header|Reference}): Maps a header name to its definition (mappings are case-insensitive).

        - content ({str:Content|Reference}): A mapping of media value_types to `MediaType` instances describing potential
          payloads.

        - links ({str:Link_|Reference}): A map of operations links that can be followed from the response.
    """

    def __init__(
        self,
        _=None,  # type: Optional[typing.Mapping]
        description=None,  # type: Optional[str]
        schema=None,  # type: Optional[Schema]
        headers=None,  # type: Optional[typing.Mapping[str, Union[Header, Reference]]]
        examples=None,  # type: Optional[Dict[str, Any]]
        # example=None,  # type: Optional[Any]
        content=None,  # type: Optional[typing.Mapping[str, Union[Content, Reference]]]
        links=None,  # type: Optional[typing.Mapping[str, Union[Link, Reference]]]
    ):
        # type: (...) -> None
        self.description = description
        self.schema = schema
        self.headers = headers
        self.examples = examples
        # self.example = example
        self.content = content
        self.links = links
        super().__init__(_)


sob.meta.writable(Response).properties = [
    (
        'description',
        sob.properties.String()
    ),
    (
        'schema',
        sob.properties.Property(
            types=(Reference, Schema),
            versions=('openapi<3.0',)
        )
    ),
    (
        'headers',
        sob.properties.Dictionary(
            value_types=(Reference, Header)
        )
    ),
    (
        'examples',
        sob.properties.Dictionary(
            versions=('openapi<3.0',)
        )
    ),
    (
        'content',
        sob.properties.Dictionary(
            value_types=(Reference, MediaType),
            versions=('openapi>=3.0',)
        )
    ),
    (
        'links',
        sob.properties.Dictionary(
            value_types=(Reference, Link_),
            versions=('openapi>=3.0',)
        )
    ),
]


class ExternalDocumentation(Object):
    """
    Properties:

        - description (str)
        - url (str)
    """

    def __init__(
        self,
        _=None,  # type: Optional[typing.Mapping]
        description=None,  # type: Optional[str]
        url=None,  # type: Optional[str]
    ):
        self.description = description
        self.url = url
        super().__init__(_)


sob.meta.writable(ExternalDocumentation).properties = [
    ('description', sob.properties.String()),
    ('url', sob.properties.String(required=True)),
]


sob.meta.writable(Tag).properties = [
    ('name', sob.properties.String(required=True)),
    ('description', sob.properties.String()),
    ('external_docs', sob.properties.Property(types=(ExternalDocumentation,))),
]


class RequestBody(Object):

    def __init__(
        self,
        _=None,  # type: Optional[typing.Mapping]
        description=None,  # type: Optional[str]
        content=None,  # type: Optional[typing.Mapping[str, MediaType]]
        required=None,  # type: Optional[bool]
    ):
        self.description = description
        self.content = content
        self.required = required
        super().__init__(_)


sob.meta.writable(RequestBody).properties = [
    ('description', sob.properties.String(versions=('openapi>=3.0',))),
    ('content', sob.properties.Dictionary(value_types=(MediaType,), versions=('openapi>=3.0',))),
    ('required', sob.properties.Boolean(versions=('openapi>=3.0',))),
]


class Operation(Object):
    """
    https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.0.md#operationObject

    Describes a single API operation on a path.

    Properties:

        - tags ([str]):  A list of tags for API documentation control. Tags can be used for logical grouping of
          operations by resources or any other qualifier.

        - summary (str):  A short summary of what the operation does.

        - description (str): A verbose explanation of the operation behavior. `CommonMark <http://spec.commonmark.org>`
          syntax may be used for rich text representation.

        - external_docs (ExternalDocumentation):  Additional external documentation for this operation.

        - operation_id (str):  Unique string used to identify the operation. The ID must be unique among all operations
          described in the API. Tools and libraries may use the `operation_id` to uniquely identify an operation,
          therefore, it is recommended to follow common programming naming conventions.

        - parameters ([Parameter|Reference]):  A list of parameters that are applicable for this operation. If a
          parameter is already defined at the `PathItem`, the new definition will override it, but can never remove
          it.

        - request_body (RequestBody|Reference):  The request body applicable for this operation. The requestBody is only
          supported in HTTP methods where the HTTP 1.1 specification
          `RFC7231 <https://tools.ietf.org/html/rfc7231#section-4.3.1>` has explicitly defined semantics for request
          bodies.

        - responses (typing.Mapping[str, Response]):  A mapping of HTTP response codes to response schemas.

        - callbacks ({str:{str:PathItem}|Reference})

        - deprecated (bool)

        - security ([[str]])

        - servers ([Server])

    Version 2x Compatibility:

        - produces ([str]):
    """

    def __init__(
        self,
        _=None,  # type: Optional[typing.Mapping]
        tags=None,  # type: Optional[Sequence[str]]
        summary=None,  # type: Optional[str]
        description=None,  # type: Optional[str]
        external_docs=None,  # type: Optional[ExternalDocumentation]
        operation_id=None,  # type: Optional[str]
        parameters=None,  # type: Optional[Sequence[Union[Parameter, Reference]]]
        request_body=None,  # type: Optional[RequestBody, Reference]
        schemes=None,  # type: Optional[typing.Sequence[str]]
        deprecated=None,  # type: Optional[bool]
        responses=None,  # type: Optional[typing.Mapping[str, Response]]
        callbacks=None,  # type: Optional[typing.Mapping[str, Union[Callback, Refefence]]]
        security=None,  # type: Optional[Sequence[Dict[str, Sequence[str]]]]
        servers=None,  # type: Optional[Sequence[Server]]
        consumes=None,  # type: Optional[Sequence[str]]
        produces=None,  # type: Optional[Sequence[str]]
    ):
        # type: (...) -> None
        self.tags = tags
        self.summary = summary
        self.description = description
        self.external_docs = external_docs
        self.operation_id = operation_id
        self.parameters = parameters
        self.request_body = request_body
        self.responses = responses
        self.schemes = schemes
        self.deprecated = deprecated
        self.callbacks = callbacks
        self.security = security
        self.servers = servers
        self.consumes = consumes
        self.produces = produces
        super().__init__(_)


# Property definitions for `Operation` deferred until after `PathItem` is defined


class PathItem(Object):
    """
    https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.0.md#pathItemObject
    """

    def __init__(
        self,
        _=None,  # type: Optional[typing.Mapping]
        summary=None,  # type: Optional[str]
        description=None,  # type: Optional[str]
        get=None,  # type: Optional[Operation]
        put=None,  # type: Optional[Operation]
        post=None,  # type: Optional[Operation]
        delete=None,  # type: Optional[Operation]
        options=None,  # type: Optional[Operation]
        head=None,  # type: Optional[Operation]
        patch=None,  # type: Optional[Operation]
        trace=None,  # type: Optional[Operation]
        servers=None,  # type: Optional[Sequence[Server]]
        parameters=None,  # type: Optional[Sequence[Parameter]]
    ):
        # type: (...) -> None
        self.summary = summary
        self.description = description
        self.get = get
        self.put = put
        self.post = post
        self.delete = delete
        self.options = options
        self.head = head
        self.patch = patch
        self.trace = trace
        self.servers = servers
        self.parameters = parameters
        super().__init__(_)


sob.meta.writable(PathItem).properties = [
    ('summary', sob.properties.String(versions=('openapi>=3.0',))),
    ('description', sob.properties.String(versions=('openapi>=3.0',))),
    ('get', sob.properties.Property(types=(Operation,))),
    ('put', sob.properties.Property(types=(Operation,))),
    ('post', sob.properties.Property(types=(Operation,))),
    ('delete', sob.properties.Property(types=(Operation,))),
    ('options', sob.properties.Property(types=(Operation,))),
    ('head', sob.properties.Property(types=(Operation,))),
    ('patch', sob.properties.Property(types=(Operation,))),
    ('trace', sob.properties.Property(types=(Operation,), versions=('openapi>=3.0',))),
    ('servers', sob.properties.Array(item_types=(Server,), versions=('openapi>=3.0',))),
    (
        'parameters',
        sob.properties.Array(
            item_types=(Reference, Parameter)
        )
    ),
]


class Callback(Dictionary):

    pass


sob.meta.writable(Callback).value_types = (PathItem,)


class Callbacks(Dictionary):

    pass


sob.meta.writable(Callbacks).value_types = (Reference, Callback)


class Responses(Dictionary):

    pass


sob.meta.writable(Responses).value_types = (
    sob.properties.Property(
        types=(Reference, Response),
        versions=('openapi>=3.0',)
    ),
    sob.properties.Property(
        types=(Response,),
        versions=('openapi<3.0',)
    )
)


sob.meta.writable(Operation).properties = [
    ('tags', sob.properties.Array(item_types=(str,))),
    ('summary', sob.properties.String()),
    ('description', sob.properties.String()),
    ('external_docs', sob.properties.Property(types=(ExternalDocumentation,), name='externalDocs')),
    ('operation_id', sob.properties.String(name='operationId')),
    ('consumes', sob.properties.Array(item_types=(str,),versions=('openapi<3.0',))),
    ('produces', sob.properties.Array(item_types=(str,),versions=('openapi<3.0',))),
    (
        'parameters',
        sob.properties.Array(
            item_types=(Reference, Parameter)
        )
    ),
    (
        'request_body',
        sob.properties.Property(
            types=(Reference, RequestBody),
            name='requestBody',
            versions=('openapi>=3.0',)
        )
    ),
    (
        'responses',
        sob.properties.Property(
            types=(Responses,),
            required=True
        )
    ),
    (
        'callbacks',
        sob.properties.Property(
            types=(
                Callbacks,
            ),
            versions=('openapi>=3.0',)
        )
    ),
    ('schemes', sob.properties.Array(item_types=(str,), versions=('openapi>=3.0',))),
    ('deprecated', sob.properties.Boolean()),
    (
        'security',
        sob.properties.Array(
            item_types=(
                sob.properties.Dictionary(
                    value_types=(
                        sob.properties.Array(
                            item_types=(str,)
                        ),
                    )
                ),
            )
        )
    ),
    ('servers', sob.properties.Array(item_types=(Server,), versions=('openapi>=3.0',)))
]


class Discriminator(Object):
    """
    https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.0.md#discriminatorObject

    Properties:

        - property_name (str): The name of the property which will hold the discriminating value.

        - mapping ({str:str}): An mappings of payload values to schema names or references.
    """

    def __init__(
        self,
        _=None,  # type: Optional[typing.Mapping]
        property_name=None,  # type: Optional[str]
        mapping=None,  # type: Optional[typing.Mapping[str, str]]
    ):
        self.property_name = property_name
        self.mapping = mapping
        super().__init__(_)


sob.meta.writable(Discriminator).properties = [
    ('property_name', sob.properties.String(name='propertyName', versions=('openapi>=3.0',))),
    ('mapping', sob.properties.Dictionary(value_types=(str,), versions=('openapi>=3.0',))),
]


class XML(Object):
    """
    https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.0.md#xmlObject

    Properties:

        - name (str): The element name.

        - name_space (str): The *absolute* URI of a namespace.

        - prefix (str): The prefix to be used with the name to reference the name-space.

        - attribute (bool): If `True`, the property described is an attribute rather than a sub-element.

        - wrapped (bool): If `True`, an array instance described by the schema will be wrapped by a tag (named
          according to the parent element's property, while `name` refers to the child element name).
    """

    def __init__(
        self,
        _=None,  # type: Optional[typing.Mapping]
        name=None,  # type: Optional[str]
        name_space=None,  # type: Optional[str]
        prefix=None,  # type: Optional[str]
        attribute=None,  # type: Optional[bool]
        wrapped=None,  # type: Optional[bool]
    ):
        self.name = name
        self.name_space = name_space
        self.prefix = prefix
        self.attribute = attribute
        self.wrapped = wrapped
        super().__init__(_)


sob.meta.writable(XML).properties = [
    ('name', sob.properties.String()),
    ('name_space', sob.properties.String(name='nameSpace')),
    ('prefix', sob.properties.String()),
    ('attribute', sob.properties.Boolean()),
    ('wrapped', sob.properties.Boolean()),
]


class OAuthFlow(Object):
    """
    https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.0.md#oauthFlowObject
    """

    def __init__(
        self,
        _=None,  # type: Optional[typing.Mapping]
        authorization_url=None,  # type: Optional[str]
        token_url=None,  # type: Optional[str]
        refresh_url=None,  # type: Optional[str]
        scopes=None,  # type: Optional[typing.Mapping[str, str]]
    ):
        self.authorization_url = authorization_url
        self.token_url = token_url
        self.refresh_url = refresh_url
        self.scopes = scopes
        super().__init__(_)


sob.meta.writable(OAuthFlow).properties = [
    ('authorization_url', sob.properties.String()),
    ('token_url', sob.properties.String(name='tokenUrl')),
    ('refresh_url', sob.properties.String(name='refreshUrl')),
    ('scopes', sob.properties.Dictionary(value_types=(str,))),
]


class OAuthFlows(Object):
    """
    https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.0.md#oauthFlowsObject
    """

    def __init__(
        self,
        _=None,  # type: Optional[typing.Mapping]
        implicit=None,  # type: Optional[OAuthFlow]
        password=None,  # type: Optional[OAuthFlow]
        client_credentials=None,  # type: Optional[OAuthFlow]
        authorization_code=None,  # type: Optional[OAuthFlow]
    ):
        self.implicit = implicit
        self.password = password
        self.client_credentials = client_credentials
        self.authorization_code = authorization_code
        super().__init__(_)


sob.meta.writable(OAuthFlows).properties = [
    ('implicit', sob.properties.Property(types=(OAuthFlow,), versions=('openapi>=3.0',))),
    ('password', sob.properties.Property(types=(OAuthFlow,), versions=('openapi>=3.0',))),
    (
        'client_credentials',
        sob.properties.Property(
            types=(OAuthFlow,),
            name='clientCredentials',
            versions=('openapi>=3.0',),
        )
    ),
    (
        'authorization_code',
        sob.properties.Property(
            types=(OAuthFlow,),
            name='authorizationCode',
            versions=('openapi>=3.0',)
        )
    ),
]


class Properties(Dictionary):

    pass


sob.meta.writable(Properties).value_types = (Reference, Schema)


class SecurityScheme(Object):
    """
    https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.0.md#requestBodyObject

    Properties:

        - type_ (str): https://tools.ietf.org/html/rfc7235#section-4

        - description (str)

        - name (str)

        - in_ (str)

        - scheme (str)

        - bearer_format (str)

        - flows (OAuthFlows)

        - open_id_connect_url (str)
    """

    def __init__(
        self,
        _=None,  # type: Optional[typing.Mapping]
        type_=None,  # type: Optional[str]
        description=None,  # type: Optional[str]
        name=None,  # type: Optional[str]
        in_=None,  # type: Optional[str]
        scheme=None,  # type: Optional[str]
        bearer_format=None,  # type: Optional[str]
        flows=None,  # type: Optional[OAuthFlows]
        open_id_connect_url=None,  # type: Optional[str]
        flow=None,  # type: Optional[str]
        authorization_url=None,  # type: Optional[str]
        scopes=None,  # type: Optional[str]
        token_url=None,  # type: Optional[str]
    ):
        self.type_ = type_
        self.description = description
        self.name = name
        self.in_ = in_
        self.scheme = scheme
        self.bearer_format = bearer_format
        self.flows = flows
        self.open_id_connect_url = open_id_connect_url
        self.flow = flow
        self.authorization_url = authorization_url
        self.scopes = scopes
        self.token_url = token_url
        super().__init__(_)


sob.meta.writable(SecurityScheme).properties = [
    (
        'type_',
        sob.properties.Enumerated(
            values=('apiKey', 'http', 'oauth2', 'openIdConnect'),
            name='type',
            required=True
        )
    ),
    ('description', sob.properties.String()),
    (
        'name',
        sob.properties.String(
            required=lambda o: True if o.type_ == 'apiKey' else False
        )
    ),
    (
        'in_',
        sob.properties.Property(
            types=(
                sob.properties.Enumerated(
                    values=('query', 'header', 'cookie'),
                    versions=('openapi>=3.0',)
                ),
                sob.properties.Enumerated(
                    values=('query', 'header'),
                    versions=('openapi<3.0',)
                ),
            ),
            name='in',
            required=lambda o: True if o.type_ == 'apiKey' else False
        )
    ),
    (
        'scheme',
        sob.properties.String(
            required=lambda o: True if o.type_ == 'http' else False,
            versions='openapi>=3.0'
        )
    ),
    ('bearer_format', sob.properties.String(name='bearerFormat')),
    (
        'flows',
        sob.properties.Property(
            types=(OAuthFlows,),
            required=lambda o: True if o.type_ == 'oauth2' else False,
            versions=('openapi>=3.0',)
        )
    ),
    (
        'open_id_connect_url',
        sob.properties.String(
            name='openIdConnectUrl',
            required=lambda o: True if o.type_ == 'openIdConnect' else False
        )
    ),
    (
        'flow',
        sob.properties.String(
            versions='openapi<3.0',
            required=lambda o: True if o.type_ == 'oauth2' else False
        )
    ),
    (
        'authorization_url',
        sob.properties.String(
            name='authorizationUrl',
            versions='openapi<3.0',
            required=lambda o: (
                True
                if o.type_ == 'oauth2' and o.flow in ('implicit', 'accessCode') else
                False
            )
        )
    ),
    (
        'token_url',
        sob.properties.String(
            name='tokenUrl',
            versions='openapi<3.0',
            required=lambda o: (
                True
                if o.type_ == 'oauth2' and o.flow in ('password', 'application', 'accessCode') else
                False
            )
        )
    ),
    (
        'scopes',
        sob.properties.Dictionary(
            value_types=(str,),
            versions='openapi<3.0',
            required=lambda o: True if o.type_ == 'oauth2' else False
        )
    )
]

sob.meta.writable(Schema).properties = [
    ('title', sob.properties.String()),
    ('description', sob.properties.String()),
    ('multiple_of', sob.properties.Number(name='multipleOf')),
    ('maximum', sob.properties.Number()),
    ('exclusive_maximum', sob.properties.Boolean(name='exclusiveMaximum')),
    ('minimum', sob.properties.Number()),
    ('exclusive_minimum', sob.properties.Boolean(name='exclusiveMinimum')),
    ('max_length', sob.properties.Integer(name='maxLength')),
    ('min_length', sob.properties.Integer(name='minLength')),
    ('pattern', sob.properties.String()),
    ('max_items', sob.properties.Integer(name='maxItems')),
    ('min_items', sob.properties.Integer(name='minItems')),
    ('unique_items', sob.properties.Boolean(name='uniqueItems')),
    (
        'items',
        sob.properties.Property(
            types=(
                Reference,
                Schema,
                sob.properties.Array(
                    item_types=(Reference, Schema)
                )
            )
        )
    ),
    ('max_properties', sob.properties.Integer(name='maxProperties')),
    ('min_properties', sob.properties.Integer(name='minProperties')),
    ('properties', sob.properties.Property(types=(Properties,))),
    (
        'additional_properties',
        sob.properties.Property(
            types=(Reference, Schema, bool),
            name='additionalProperties'
        )
    ),
    ('enum', sob.properties.Array()),
    (
        'type_',
        sob.properties.Property(
            types=(
                sob.properties.Array(
                    item_types=(
                        sob.properties.Enumerated(
                            values=(
                                'array',
                                'object',
                                'file',
                                'integer',
                                'number',
                                'string',
                                'boolean'
                            )
                        ),
                    )
                ),
                sob.properties.Enumerated(
                    values=(
                        'array',
                        'object',
                        'file',
                        'integer',
                        'number',
                        'string',
                        'boolean'
                    )
                )
            ),
            name='type'
        )
    ),
    (
        'format_',
        sob.properties.String(
            # values=(
            #     'int32', 'int64',
            #     'float', 'double',
            #     'byte', 'binary', 'date', 'date-time', 'password'
            # ),
            name='format'
        )
    ),
    ('required', sob.properties.Array(item_types=(sob.properties.String(),))),
    ('all_of', sob.properties.Array(item_types=(Reference, Schema), name='allOf')),
    ('any_of', sob.properties.Array(item_types=(Reference, Schema), name='anyOf')),
    ('one_of', sob.properties.Array(item_types=(Reference, Schema), name='oneOf')),
    ('is_not', sob.properties.Property(types=(Reference, Schema), name='isNot')),
    ('definitions', sob.properties.Property()),
    ('default', sob.properties.Property()),
    ('required', sob.properties.Array(item_types=(str,))),
    ('default', sob.properties.Property()),
    (
        'discriminator',
        sob.properties.Property(
            types=(
                sob.properties.Property(
                    types=(Discriminator,),
                    versions=('openapi>=3.0',),
                ),
                sob.properties.Property(
                    types=(str,),
                    versions=('openapi<3.0',)
                )
            )
        )
    ),
    ('read_only', sob.properties.Boolean()),
    ('write_only', sob.properties.Boolean(name='writeOnly', versions=('openapi>=3.0',))),
    ('xml', sob.properties.Property(types=(XML,))),
    ('external_docs', sob.properties.Property(types=(ExternalDocumentation,))),
    ('example', sob.properties.Property()),
    ('deprecated', sob.properties.Boolean(versions=('openapi>=3.0',))),
    ('links', sob.properties.Array(item_types=(Link,))),
    ('nullable', sob.properties.Boolean(versions=('openapi>=3.0',)))
]


def _schema_after_validate(o):
    # type: (Schema) -> Schema
    if o.format_ in (
        'int32', 'int64',  # type_ == 'integer'
        'float', 'double',  # type_ == 'number'
        'byte', 'binary', 'date', 'date-time', 'password',  # type_ == 'string'
    ):
        if o.type_ == 'integer' and (
            o.format_ not in ('int32', 'int64', None)
        ):
            qn = sob.utilities.qualified_name(type(o))
            raise sob.errors.ValidationError(
                '"%s" in not a valid value for `%s.format_` in this circumstance. ' % (o.format_, qn) +
                '`%s.format_` may be "int32" or "int64" when ' % qn +
                '`%s.type_` is "integer".' % (qn, )
            )
        elif o.type_ == 'number' and (
            o.format_ not in ('float', 'double', None)
        ):
            qn = sob.utilities.qualified_name(type(o))
            raise sob.errors.ValidationError(
                '"%s" in not a valid value for `%s.format_` in this circumstance. ' % (o.format_, qn) +
                '`%s.format_` may be "float" or "double" when ' % qn +
                '`%s.type_` is "number".' % (qn, )
            )
        elif o.type_ == 'string' and (
            o.format_ not in ('byte', 'binary', 'date', 'date-time', 'password', None)
        ):
            qn = sob.utilities.qualified_name(type(o))
            raise sob.errors.ValidationError(
                '"%s" in not a valid value for `%s.format_` in this circumstance. ' % (o.format_, qn) +
                '`%s.format_` may be "byte", "binary", "date", "date-time" or "password" when ' % qn +
                '`%s.type_` is "string".' % (qn, )
            )
    return o


sob.hooks.writable(Schema).after_validate = _schema_after_validate


class Schemas(Dictionary):

    pass


sob.meta.writable(Schemas).value_types = (Reference, Schema)


class Headers(Dictionary):

    pass


sob.meta.writable(Headers).value_types = (Reference, Header)


class Parameters(Dictionary):

    pass


sob.meta.writable(Parameters).value_types = (Reference, Parameter)


class Examples(Dictionary):

    pass


sob.meta.writable(Examples).value_types = (Reference, Example)


class RequestBodies(Dictionary):

    pass


sob.meta.writable(RequestBodies).value_types = (Reference, RequestBody)


class SecuritySchemes(Dictionary):

    pass


sob.meta.writable(SecuritySchemes).value_types = (Reference, SecurityScheme)


class Links(Dictionary):

    pass


sob.meta.writable(Links).value_types = (Reference, Link_)


class Components(Object):

    def __init__(
        self,
        _=None,  # type: Optional[typing.Mapping]
        schemas=None,  # type: Optional[Schemas]
        responses=None,  # type: Optional[Responses]
        parameters=None,  # type: Optional[Parameters]
        examples=None,  # type: Optional[Examples]
        request_bodies=None,  # type: Optional[RequestBodies]
        headers=None,  # type: Optional[Headers]
        security_schemes=None,  # type: Optional[SecuritySchemes]
        links=None,  # type: Optional[Links]
        callbacks=None,  # type: Union[typing.Mapping[str, Union[typing.Dict[str, PathItem], Reference]]]
    ):
        self.schemas = schemas
        self.responses = responses
        self.parameters = parameters
        self.examples = examples
        self.request_bodies = request_bodies
        self.headers = headers
        self.security_schemes = security_schemes
        self.links = links
        self.callbacks = callbacks
        super().__init__(_)


sob.meta.writable(Components).properties = [
    ('schemas', sob.properties.Property(types=(Schemas,))),
    ('responses', sob.properties.Property(types=(Responses,))),
    (
        'parameters',
        sob.properties.Property(types=(Parameters,))
    ),
    ('examples', sob.properties.Property(types=(Examples,))),
    ('request_bodies', sob.properties.Property(types=(RequestBodies,), name='requestBodies')),
    ('headers', sob.properties.Property(types=(Headers,))),
    ('security_schemes', sob.properties.Property(types=(SecuritySchemes,), name='securitySchemes')),
    ('links', sob.properties.Property(types=(Links,))),
    (
        'callbacks',
        sob.properties.Property(
            types=(Callbacks,)
        )
    ),
]


class Definitions(Dictionary):

    pass


sob.meta.writable(Definitions).value_types = (Schema,)


class Paths(Dictionary):

    pass


sob.meta.writable(Paths).value_types = (PathItem,)


class OpenAPI(Object):

    def __init__(
        self,
        _=None,  # type: Optional[typing.Mapping]
        openapi=None,  # type: Optional[str]
        info=None,  # type: Optional[Info]
        host=None,  # type: Optional[str]
        servers=None,  # type: Optional[Sequence[str]]
        base_path=None,  # type: Optional[str]
        schemes=None,  # type: Optional[Sequence[str]]
        tags=None,  # type: Optional[Sequence[Tag]]
        paths=None,  # type: Optional[typing.Mapping[str, PathItem]]
        components=None,  # type: Optional[Components]
        consumes=None,  # type: Any
        # 2.0 compatibility
        swagger=None,  # type: Optional[str]
        definitions=None,  # type: Optional[typing.Mapping[str, Object]]
        security_definitions=None,  # type: Optional[typing.Mapping[str, Union[Object, str]]]
        produces=None,  # type: Optional[typing.Collection[str]]
        external_docs=None,  # type: Optional[ExternalDocumentation]
        parameters=None,  # type: Optional[Dict[str, Parameter]]
        responses=None,  # type: Optional[Dict[str, Response]]
        security=None,  # type: Optional[Dict[str, typing.Sequence[str]]]
    ):
        # type: (...) -> None
        self.openapi = openapi
        self.info = info
        self.host = host
        self.servers = servers
        self.base_path = base_path
        self.schemes = schemes
        self.tags = tags
        self.paths = paths
        self.components = components
        self.consumes = consumes
        # 2.0 compatibility
        self.swagger = swagger
        self.definitions = definitions
        self.security_definitions = security_definitions
        self.produces = produces
        self.external_docs = external_docs
        self.parameters = parameters
        self.responses = responses
        self.security = security
        super().__init__(_)
        version = self.openapi or self.swagger
        if version is not None:
            sob.meta.version(self, 'openapi', version)


sob.meta.writable(OpenAPI).properties = [
    ('openapi', sob.properties.String(versions=('openapi>=3.0',), required=True)),
    ('info', sob.properties.Property(types=(Info,), required=True)),
    ('host', sob.properties.String(versions=('openapi<3.0',))),
    ('servers', sob.properties.Array(item_types=(Server,), versions=('openapi>=3.0',))),
    ('base_path', sob.properties.String(name='basePath', versions=('openapi<3.0',))),
    ('schemes', sob.properties.Array(item_types=(str,), versions=('openapi<3.0',))),
    ('tags', sob.properties.Array(item_types=(Tag,))),
    ('paths', sob.properties.Property(types=(Paths,), required=True)),
    ('components', sob.properties.Property(types=(Components,), versions=('openapi>=3.0',))),
    ('consumes', sob.properties.Array(item_types=(str,), versions=('openapi<3.0',))),
    ('swagger', sob.properties.String(versions=('openapi<3.0',), required=True)),
    (
        'definitions',
        sob.properties.Property(
            types=(Definitions,),
            versions=('openapi<3.0',)
        ),
    ),
    (
        'security_definitions',
        sob.properties.Property(
            types=(
                sob.properties.Dictionary(
                    value_types=(SecurityScheme,),
                    versions=('openapi<3.0',)
                ),
                sob.properties.Dictionary(
                    value_types=(Reference, SecurityScheme),
                    versions=('openapi>=3.0',)
                ),
            ),
            name='securityDefinitions',
        )
    ),
    ('produces', sob.properties.Array(item_types=(str,), versions=('openapi<3.0',)),),
    ('external_docs', sob.properties.Property(types=(ExternalDocumentation,), name='externalDocs')),
    (
        'parameters',
        sob.properties.Dictionary(
            value_types=(Parameter,),
            versions=('openapi<3.0',)
        )
    ),
    ('responses', sob.properties.Dictionary(value_types=(Response,), versions=('openapi<3.0',))),
    (
        'security',
        sob.properties.Dictionary(
            value_types=(
                sob.properties.Array(item_types=(str,)),
            ),
            versions=('openapi<3.0',)
        )
    ),
]
