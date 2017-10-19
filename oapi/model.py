"""
Version 2x: https://swagger.io/docs/specification/2-0/basic-structure/
Version 3x: https://swagger.io/specification
"""

from __future__ import nested_scopes, generators, division, absolute_import, with_statement, print_function, \
    unicode_literals

from future import standard_library

standard_library.install_aliases()
from builtins import *
#

from collections import OrderedDict

import collections
from copy import deepcopy
from http.client import HTTPResponse
from itertools import chain
from numbers import Number
from urllib import request
from urllib.error import HTTPError
from urllib.parse import urlparse, urljoin

from jsonpointer import resolve_pointer

try:
    import typing
    from typing import Union, Any
except ImportError:
    typing = Union = Any = None

import serial
from serial import meta
from serial.model import deserialize, serialize, Object, Array, Dictionary

try:
    from builtins import RecursionError
except ImportError:
    class RecursionError(RuntimeError): pass


def resolve_references(
    data,  # type: Union[Object, Dictionary, Array]
    url=None,  # type: Optional[str]
    urlopen=request.urlopen,  # type: Union[typing.Callable, Sequence[typing.Callable]]
    root=None,  # type: Optional[Union[Object, Dictionary, Array]]
    _references=None,  # type: Optional[typing.Dict[str, Union[Object, Dictionary, Array]]]
):
    # type: (...) -> Union[Object, typing.Mapping, typing.Sequence]
    """
    Returns a deep copy of the ``data`` provided after recursively replacing ``oapi.model.Reference`` instances with the
    material referenced.

    Arguments:

        - data (Object|Dictionary|Array): A deserialized object or array.

        - url (str): The URL from where ``data`` was retrieved. The base URL for relative paths will be the directory
          above this URL, and this URL will be used to index _references in order to prevent cyclic recursion when
          mapping (external) bidirectional _references between two (or more) documents. For ``Object`` instances, if the
          URL is not provided, it will be inferred from the object's metadata where possible. Objects created from an
          instance of ``http.client.HTTPResponse`` will have had the source URL stored with it's metadata when the
          object was instantiated.

        - urlopen (``collections.Callable``): If provided, this should be a function taking one argument (a ``str``),
          which can be used in lieu of ``request.urlopen`` to retrieve a document and return an instance of a sub-class
          of ``IOBase`` (such as ``http.client.HTTPResponse``). This should be used if authentication is needed in order
          to retrieve external _references in the document, or if local file paths will be referenced instead of web
          URL's.

        - root (Object|Dictionary|Array): The root document to be used for resolving inline references. This argument
          is only needed if ``data`` is not a "root" object/element in a document (an object resulting from
          deserializing a document, as opposed to one of the child objects of that deserialized root object).
    """
    if _references is None:
        _references = {}

    def resolve_ref(
        ref,  # type: str
        ref_root,  # type: Union[Object, Sequence]
        ref_document_url=None,  # type: Optional[str]
        exclude=None,  # type: Optional[Set[str]]
    ):
        # print((ref, ref_document_url))
        if exclude is None:
            exclude = set()
        ref_added = False
        if ref[0] == '#':
            ref_document = ref_root
            ref_pointer = ref[1:]
        else:
            ref_parts = ref.split('#')
            ref_parts_url = ref_parts[0]
            if ref_document_url:
                parse_result = urlparse(ref_parts_url)
                if parse_result.scheme:
                    ref_document_url = ref_parts_url
                else:
                    ref_document_url = urljoin(
                        ref_document_url,
                        ref_parts_url.lstrip('/ ')
                    )
            else:
                ref_document_url = ref_parts_url
            if len(ref_parts) < 2:
                ref_pointer = None
            else:
                ref_pointer = '#'.join(ref_parts[1:])
            if ref_document_url in _references:
                if _references[ref_document_url] is None:
                    raise RecursionError()
                ref_document = deepcopy(_references[ref_document_url])
            else:
                try:
                    ref_document = deserialize(urlopen(ref_document_url))
                except HTTPError as http_error:
                    http_error.msg = http_error.msg + ': ' + ref_document_url
                    raise http_error
        if ref_pointer is None:
            ref_data = deepcopy(ref_document)
            ref_url_pointer = ref_document_url
            if ref_url_pointer not in _references:
                _references[ref_url_pointer] = None
                try:
                    ref_data = resolve_references(
                        ref_data,
                        root=ref_document,
                        urlopen=urlopen,
                        url=ref_document_url,
                        _references=_references
                    )
                    _references[ref_url_pointer] = ref_data
                    ref_added = True
                except RecursionError:
                    pass
        else:
            ref_url_pointer = '%s#%s' % (ref_document_url or '', ref_pointer)
            if ref_url_pointer in _references:
                if _references[ref_url_pointer] is None:
                    raise RecursionError()
                else:
                    ref_data = deepcopy(_references[ref_url_pointer])
            else:
                ref_data = deepcopy(resolve_pointer(ref_document, ref_pointer))
                _references[ref_url_pointer] = None
                try:
                    ref_data = resolve_references(
                        ref_data,
                        root=ref_document,
                        urlopen=urlopen,
                        url=ref_document_url,
                        _references=_references
                    )
                    _references[ref_url_pointer] = deepcopy(ref_data)
                    ref_added = True
                except RecursionError:
                    pass
        # print((ref_url_pointer, ref_added, serialize(ref_data)))
        # print()
        return ref_data, ref_document, ref_document_url, ref_added

    try:
        data = deepcopy(data)
    except TypeError as e:
        e.args = tuple(
            chain(
                (
                    '%s%s' % (
                        e.args[0] + '\n' if e.args else '',
                        serialize(data),
                    ),
                ),
                e.args[1:] if e.args else []
            )
        )
        raise e
    if root is None:
        root = serial.model.marshal(data)
    if isinstance(data, Reference):
        data, document, reference_url, references_added = resolve_ref(
            data.ref,
            ref_root=root,
            ref_document_url=url,
        )
        # if references_added:
        # data = resolve_references(
        #     data,
        #     root=document,
        #     urlopen=urlopen,
        #     url=reference_url,
        #     _references=_references
        # )
    elif isinstance(data, Object):
        m = meta.get(data)
        if url is None:
            if m.url:
                url = m.url
            elif m.path:
                url = m.path
                urlopen = open
        for pn, p in m.properties.items():
            v = getattr(data, pn)
            # print(v)
            if isinstance(v, Reference):
                v, document, reference_url, references_added = resolve_ref(
                    v.ref,
                    ref_root=root,
                    ref_document_url=url,
                )
                # if references_added:
                # v = resolve_references(
                #     v,
                #     root=document,
                #     urlopen=urlopen,
                #     url=reference_url,
                #     _references=_references
                # )
                setattr(data, pn, v)
            else:
                try:
                    v = resolve_references(
                        v,
                        root=root,
                        urlopen=urlopen,
                        url=url,
                        _references=_references
                    )
                except RecursionError:
                    pass
                setattr(data, pn, serial.model.marshal(v))
    elif isinstance(data, (Dictionary, dict, OrderedDict)):
        if data is root:
            raise ValueError(data)
        if '$ref' in data.keys():
            # print(data['$ref'])
            data, document, reference_url, references_added = resolve_ref(
                data['$ref'],
                ref_root=root,
                ref_document_url=url,
            )
            # if references_added:
            # data = resolve_references(
            #     data,
            #     root=document,
            #     urlopen=urlopen,
            #     url=reference_url,
            #     _references=_references
            # )
        else:
            for k, v in data.items():
                try:
                    data[k] = resolve_references(
                        v,
                        root=root,
                        urlopen=urlopen,
                        url=url,
                        _references=_references
                    )
                except RecursionError:
                    pass
    elif isinstance(data, (Array, collections.Sequence, collections.Set)) and not isinstance(data, (str, bytes)):
        if not isinstance(data, collections.MutableSequence):
            data = list(data)
        for i in range(len(data)):
            try:
                data[i] = resolve_references(
                    data[i],
                    root=root,
                    urlopen=urlopen,
                    url=url,
                    _references=_references
                )
            except RecursionError:
                pass
        # print(repr(data))
    return data


class Reference(Object):

    def __init__(
        self,
        _=None,  # type: Optional[typing.Mapping]
        ref=None,  # type: Optional[str]
    ):
        self.ref = ref
        if _ is not None:
            if isinstance(_, HTTPResponse):
                meta.get(self).url = _.url
            if isinstance(_, (dict, str)):
                _ = deserialize(_)
                keys = set(_.keys())
                if ('$ref' in keys) and (_['$ref'] is not None):
                    for k in keys - {'$ref'}:
                        del _[k]
        super().__init__(_)


meta.get(Reference).properties = [
    ('ref', serial.properties.String(name='$ref'))
]


class Contact(Object):
    """
    https://swagger.io/specification/#contactObject
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


meta.get(Contact).properties = [
    ('name', serial.properties.String()),
    ('url', serial.properties.String()),
    ('email', serial.properties.String()),
]


class License(Object):
    """
    https://swagger.io/specification/#licenseObject
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


meta.get(License).properties = [
    ('name', serial.properties.String()),
    ('url', serial.properties.String()),
]


class Info(Object):
    """
    https://swagger.io/specification/#infoObject
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


meta.get(Info).properties = [
    ('title', serial.properties.String()),
    ('description', serial.properties.String()),
    ('terms_of_service', serial.properties.String(name='termsOfService')),
    ('contact', serial.properties.Object(types=(Contact,))),
    ('license_', serial.properties.Object(types=(License,), name='license')),
    ('version', serial.properties.String()),
]


class Tag(Object):
    """
    https://swagger.io/specification/#tagObject
    """

    def __init__(
        self,
        _=None,  # type: Optional[typing.Mapping]
        name=None,  # type: Optional[str]
        description=None,  # type: Optional[str]
    ):
        # type: (...) -> None
        self.name = name
        self.description = description
        super().__init__(_)


meta.get(Tag).properties = [
    ('name', serial.properties.String()),
    ('description', serial.properties.String()),
]


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


meta.get(Link).properties = [
    ('rel', serial.properties.String()),
    ('href', serial.properties.String()),
]


class Schema(Object):
    """
    https://swagger.io/specification/#schemaObject
    http://json-schema.org

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

        - items (Schema|[Schema]):

            - If ``items`` is a sub-schema--each item in the array instance described by this schema should be valid as
              described by this sub-schema.

            - If ``items`` is a sequence of sub-schemas, the array instance described by this schema should be equal in
              length to this sequence, and each value should be valid as described by the sub-schema at the
              corresponding index within this sequence of sub-schemas.

        - additional_items (Schema|bool): If ``additional_items`` is ``True``--the array instance described by
          this schema may contain additional values beyond those defined in ``items``.

        - max_items (int): The array instance described by this schema should contain no more than this number of
          items.

        - min_items (int): The array instance described by this schema should contain at least this number of
          items.

        - unique_items (bool): The array instance described by this schema should contain only unique items.

        - max_properties (int)

        - min_properties (int)

        - serial.properties ({str:Schema}): Any serial.properties of the object instance described by this schema which
          correspond to a name in this mapping should be valid as described by the sub-schema corresponding to that name.

        - pattern_properties (Schema): Any serial.properties of the object instance described by this schema which
          match a name in this mapping, when the name is evaluated as a regular expression, should be valid as described by
          the sub-schema corresponding to the matched name.

        - additional_properties (bool|Schema):

            - If ``additional_properties`` is ``True``--serial.properties may be present in the object described by
              this schema with names which do not match those in either ``serial.properties`` or ``pattern_properties``.

            - If ``additional_properties`` is ``False``--all serial.properties present in the object described by this schema
              must correspond to a property matched in either ``serial.properties`` or ``pattern_properties``.

        - dependencies ({str:{str:Schema|[str]}}):

            A dictionary mapping serial.properties of the object instance described by this schema to a mapping other
            serial.properties and either:

                - A sub-schema for validation of the second property when the first property is present on
                  the object instance described by this schema.
                - A list of serial.properties which must *also* be present when the first and second serial.properties are present on
                  the object instance described by this schema.

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

        The following serial.properties are specific to OpenAPI (not part of the core `JSON Schema <http://json-schema.org>`):

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

        - definitions (Any)

        - depracated (bool): If ``True``, the property or instance described by this schema should be phased out, as
          if will no longer be supported in future versions.
    """

    def __init__(
        self,
        _=None,  # type: Optional[typing.Mapping]
        schema=None,  # type: Optional[str]
        id_=None,  # type: Optional[str]
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
        items=None,  # type: Optional[Schema, Sequence[Schema]]
        additional_items=None,  # type: Optional[Schema, bool]
        max_items=None,  # type: Optional[int]
        min_items=None,  # type: Optional[int]
        unique_items=None,  # type: Optional[bool]
        max_properties=None,  # type: Optional[int]
        min_properties=None,  # type: Optional[int]
        properties=None,  # type: Optional[typing.Mapping[str, Schema]]
        pattern_properties=None,  # type: Optional[Schema]
        additional_properties=None,  # type: Optional[bool, Schema]
        dependencies=None,  # type: Optional[typing.Mapping[str, typing.Mapping[str, Union[Schema, Sequence[str]]]]]
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
        discriminator=None,  # type: Optional[Discriminator]
        read_only=None,  # type: Optional[bool]
        write_only=None,  # type: Optional[bool]
        xml=None,  # type: Optional[XML]
        external_docs=None,  # type: Optional[ExternalDocumentation]
        example=None,  # type: Any
        deprecated=None,  # type: Optional[bool]
        links=None,  # type: Optional[Sequence[Link]]
    ):
        self.schema = schema
        self.id_ = id_
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
        self.additional_items = additional_items
        self.max_items = max_items
        self.min_items = min_items
        self.unique_items = unique_items
        self.max_properties = max_properties
        self.min_properties = min_properties
        self.properties = properties
        self.pattern_properties = pattern_properties
        self.additional_properties = additional_properties
        self.dependencies = dependencies
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
        super().__init__(_)
        

# ...definitions are postponed until dependencies are defined


class Example(Object):
    """
    https://swagger.io/specification/#exampleObject
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


meta.get(Example).properties = [
    ('summary', serial.properties.String()),
    ('description', serial.properties.String()),
    ('value', serial.properties.Property()),
    ('external_value', serial.properties.String(name='externalValue')),
]


class Encoding(Object):

    """
    https://swagger.io/specification/#encodingObject
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
    https://swagger.io/specification/#mediaTypeObject
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


meta.get(MediaType).properties = [
    ('schema', serial.properties.Object(types=(Reference, Schema))),
    ('example', serial.properties.Property()),
    ('examples', serial.properties.Dictionary(value_types=(Reference, Example))),
    ('encoding', serial.properties.Dictionary(value_types=(Reference, Encoding))),
]


class Header(Object):
    """
    https://swagger.io/specification/#headerObject

     Properties:

         - description (str)

         - required (bool)

         - deprecated (bool)

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
           each value of the array or name-value pair of the map. For other value_types of parameters this property has no
           effect. When ``style`` is "form", the default value is ``True``. For all other styles, the default value is
           ``False``.

         - allow_reserved (bool): Determines whether the parameter value SHOULD allow reserved characters
           :/?#[]@!$&'()*+,;= (as defined by `RFC3986 <https://tools.ietf.org/html/rfc3986#section-2.2>`) to be included
           without percent-encoding. This property only applies to parameters with a location value of "query". The
           default value is ``False``.

         - schema (Schema): The schema defining the type used for the parameter.

         - example (Any): Example of the media type. The example should match the specified schema and encoding
           serial.properties if present. The ``example`` parameter should not be present if ``examples`` is present. If
           referencing a ``schema`` which contains an example--*this* example overrides the example provided by the
           ``schema``. To represent examples of media value_types that cannot naturally be represented in JSON or YAML, a
           string value can contain the example with escaping where necessary.

         - examples (typing.Mapping[str, Example]): Examples of the media type. Each example should contain a value in the correct
           format, as specified in the parameter encoding. The ``examples`` parameter should not be present if
           ``example`` is present. If referencing a ``schema`` which contains an example--*these* example override the
           example provided by the ``schema``. To represent examples of media value_types that cannot naturally be represented
           in JSON or YAML, a string value can contain the example with escaping where necessary.

         - content ({str:MediaType}): A map containing the representations for the parameter. The name is the media type
           and the value describing it. The map must only contain one entry.
     """

    def __init__(
        self,
        _=None,  # type: Optional[typing.Mapping]
        description=None,  # type: Optional[str]
        required=None,  # type: Optional[bool]
        deprecated=None,  # type: Optional[bool]
        allow_empty_value=None,  # type: Optional[bool]
        style=None,  # type: Optional[str]
        explode=None,  # type: Optional[bool]
        allow_reserved=None,  # type: Optional[bool]
        schema=None,  # type: Optional[Schema]
        example=None,  # type: Any
        examples=None,  # type: Optional[typing.Mapping[str, Example]]
        content=None,  # type: Optional[typing.Mapping[str, MediaType]]
        # 2.0 Compatibility
        type_=None,  # type: Optional[str]
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
        super().__init__(_)


meta.get(Encoding).properties = [
    ('content_type', serial.properties.String(name='contentType')),
    ('headers', serial.properties.Dictionary(value_types=(Reference, Header))),
    ('style', serial.properties.String()),
    ('explode', serial.properties.Boolean()),
    ('allow_reserved', serial.properties.Boolean(name='allowReserved')),
]


meta.get(Header).properties = [
    ('description', serial.properties.String()),
    ('required', serial.properties.Boolean()),
    ('deprecated', serial.properties.Boolean()),
    ('allow_empty_value', serial.properties.Boolean(name='allowEmptyValue')),
    ('style', serial.properties.String()),
    ('explode', serial.properties.Boolean()),
    ('allow_reserved', serial.properties.Boolean(name='allowReserved')),
    ('schema', serial.properties.Object(types=(Schema,))),
    ('example', serial.properties.Property()),
    ('examples', serial.properties.Dictionary(value_types=(Example,))),
    ('content', serial.properties.Dictionary(value_types=(MediaType,))),
    ('type_', serial.properties.String(name='type', versions=('openapi<3.0',))),
]


class Parameter(Object):
    """
    https://swagger.io/specification/#parameterObject

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
          each value of the array or name-value pair of the map. For other value_types of parameters this property has no
          effect. When ``style`` is "form", the default value is ``True``. For all other styles, the default value is
          ``False``.

        - allow_reserved (bool): Determines whether the parameter value SHOULD allow reserved characters
          :/?#[]@!$&'()*+,;= (as defined by `RFC3986 <https://tools.ietf.org/html/rfc3986#section-2.2>`) to be included
          without percent-encoding. This property only applies to parameters with a location value of "query". The
          default value is ``False``.

        - schema (Schema): The schema defining the type used for the parameter.

        - example (Any): Example of the media type. The example should match the specified schema and encoding
          serial.properties if present. The ``example`` parameter should not be present if ``examples`` is present. If
          referencing a ``schema`` which contains an example--*this* example overrides the example provided by the
          ``schema``. To represent examples of media value_types that cannot naturally be represented in JSON or YAML, a
          string value can contain the example with escaping where necessary.

        - examples ({str:Example}): Examples of the media type. Each example should contain a value in the correct
          format, as specified in the parameter encoding. The ``examples`` parameter should not be present if
          ``example`` is present. If referencing a ``schema`` which contains an example--*these* example override the
          example provided by the ``schema``. To represent examples of media value_types that cannot naturally be represented
          in JSON or YAML, a string value can contain the example with escaping where necessary.

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
        # 2x compatibility
        type_=None,  # type: Optional[str]
        format_=None,  # type: Optional[str]
        enum=None,  # type: Optional[Sequence[str]]
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
        # 2x compatibility
        self.type_ = type_
        self.enum = enum
        self.format_ = format_
        self.collection_format = collection_format
        self.items = items
        super().__init__(_)


meta.get(Parameter).properties = [
    ('name', serial.properties.String()),
    ('in_', serial.properties.String(name='in')),
    ('description', serial.properties.String()),
    ('required', serial.properties.Boolean()),
    ('deprecated', serial.properties.Boolean()),
    ('allow_empty_value', serial.properties.Boolean()),
    ('style', serial.properties.String()),
    ('explode', serial.properties.Boolean()),
    ('allow_reserved', serial.properties.Boolean()),
    ('schema', serial.properties.Object(types=(Reference, Schema))),
    ('example', serial.properties.Property()),
    ('examples', serial.properties.Object(types=(Reference, Schema))),
    ('content', serial.properties.Object(types=(MediaType,))),
    # version 2x compatibility
    (
        'type_',
        serial.properties.Property(
            types=(
                serial.properties.Array(
                    item_types=(str,)
                ),
                str,
            ),
            name='type'
        )
    ),
    (
        'enum',
        serial.properties.Array()
    ),
    (
        'format_',
        serial.properties.String(name='format')
    ),
    (
        'collection_format',
        serial.properties.Enum(
            values=('csv', 'ssv', 'tsv', 'pipes', 'multi'),
            name='collectionFormat'
        )
    ),
    (
        'items',
        serial.properties.Object(
            types=(Reference, Schema),
            versions=('openapi<3.0',)
        )
    )
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


meta.get(ServerVariable).properties = [
    ('enum', serial.properties.Array(item_types=(str,))),
    ('default', serial.properties.String()),
    ('description', serial.properties.String()),
]


class Server(Object):
    """
    https://swagger.io/specification/#serverObject
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


meta.get(Server).properties = [
    ('url', serial.properties.String()),
    ('description', serial.properties.String()),
    ('variables', serial.properties.Dictionary(value_types=(ServerVariable,))),
]


class Link_(Object):
    """
    https://swagger.io/specification/#linkObject
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


meta.get(Link_).properties = [
    ('operation_ref', serial.properties.String(name='operationRef')),
    ('operation_id', serial.properties.String(name='operationId')),
    ('parameters', serial.properties.Dictionary(value_types=(str,))),
    ('request_body', serial.properties.Property(name='requestBody')),
    ('description', serial.properties.String()),
    ('server', serial.properties.Object(types=(Server,))),
]


class Response(Object):
    """
    https://swagger.io/specification/#responseObject

    Properties:

        - description (str): A short description of the response. `CommonMark syntax<http://spec.commonmark.org/>` may
          be used for rich text representation.

        - headers ({str:Header|Reference}): Maps a header name to its definition (mappings are case-insensitive).

        - content ({str:Content|Reference}): A mapping of media value_types to ``MediaType`` instances describing potential
          payloads.

        - links ({str:Link_|Reference}): A map of operations links that can be followed from the response.
    """

    def __init__(
        self,
        _=None,  # type: Optional[typing.Mapping]
        description=None,  # type: Optional[str]
        headers=None,  # type: Optional[typing.Mapping[str, Union[Header, Reference]]]
        content=None,  # type: Optional[typing.Mapping[str, Union[Content, Reference]]]
        links=None,  # type: Optional[typing.Mapping[str, Union[Link, Reference]]]
        # 2.0 compatibility
        schema=None,  # type: Optional[Schema]
        examples=None,  # type: Optional[Dict[str, Any]]
        example=None,  # type: Optional[Any]
    ):
        # type: (...) -> None
        self.description = description
        self.headers = headers
        self.content = content
        self.links = links
        # 2.0 compatibility
        self.schema = schema
        self.examples = examples
        self.example = example
        super().__init__(_)


meta.get(Response).properties = [
    (
        'description',
        serial.properties.String()
    ),
    (
        'headers',
        serial.properties.Dictionary(
            value_types=(Reference, Header)
        )
    ),
    (
        'content',
        serial.properties.Dictionary(
            value_types=(Reference, MediaType),
            versions=('openapi>=3.0',)
        )
    ),
    (
        'links',
        serial.properties.Dictionary(
            value_types=(Reference, Link_)
        )
    ),
    # 2.0 Compatibility
    (
        'schema',
        serial.properties.Object(
            types=(Reference, Schema),
            versions=('openapi<3.0',)
        )
    ),
    (
        'examples',
        serial.properties.Dictionary(
            versions=('openapi<3.0',)
        )
    ),
    (
        'example',
        serial.properties.Property(
            versions=('openapi<3.0',)
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


meta.get(ExternalDocumentation).properties = [
    ('description', serial.properties.String()),
    ('url', serial.properties.String()),
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


meta.get(RequestBody).properties = [
    ('description', serial.properties.String()),
    ('content', serial.properties.Dictionary(value_types=(MediaType,))),
    ('required', serial.properties.Boolean()),
]


class Operation(Object):
    """
    https://swagger.io/specification/#operationObject

    Describes a single API operation on a path.

    Properties:

        - tags ([str]):  A list of tags for API documentation control. Tags can be used for logical grouping of
          operations by resources or any other qualifier.

        - summary (str):  A short summary of what the operation does.

        - description (str): A verbose explanation of the operation behavior. `CommonMark <http://spec.commonmark.org>`
          syntax may be used for rich text representation.

        - external_docs (ExternalDocumentation):  Additional external documentation for this operation.

        - operation_id (str):  Unique string used to identify the operation. The ID must be unique among all operations
          described in the API. Tools and libraries may use the ``operation_id`` to uniquely identify an operation,
          therefore, it is recommended to follow common programming naming conventions.

        - parameters ([Parameter|Reference]):  A list of parameters that are applicable for this operation. If a
          parameter is already defined at the ``PathItem``, the new definition will override it, but can never remove
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
        deprecated=None,  # type: Optional[bool]
        responses=None,  # type: Optional[typing.Mapping[str, Response]]
        callbacks=None,  # type: Optional[typing.Mapping[str, Union[Callback, Refefence]]]
        security=None,  # type: Optional[Sequence[Dict[str, Sequence[str]]]]
        servers=None,  # type: Optional[Sequence[Server]]
        # Version 2x Compatibility
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
        self.deprecated = deprecated
        self.callbacks = callbacks
        self.security = security
        self.servers = servers
        # Version 2x Compatibility
        self.consumes = consumes
        self.produces = produces
        super().__init__(_)


# Property definitions for `Operation` deferred until after `PathItem` is defined


class PathItem(Object):
    """
    https://swagger.io/specification/#pathItemObject
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


meta.get(PathItem).properties = [
    ('summary', serial.properties.String()),
    ('description', serial.properties.String()),
    ('get', serial.properties.Object(types=(Operation,))),
    ('put', serial.properties.Object(types=(Operation,))),
    ('post', serial.properties.Object(types=(Operation,))),
    ('delete', serial.properties.Object(types=(Operation,))),
    ('options', serial.properties.Object(types=(Operation,))),
    ('head', serial.properties.Object(types=(Operation,))),
    ('patch', serial.properties.Object(types=(Operation,))),
    ('trace', serial.properties.Object(types=(Operation,))),
    ('servers', serial.properties.Array(item_types=(Server,))),
    (
        'parameters',
        serial.properties.Object(
            types=(Reference, Parameter)
        )
    ),
]


meta.get(Operation).properties = [
    ('tags', serial.properties.Array(item_types=(str,))),
    ('summary', serial.properties.String()),
    ('description', serial.properties.String()),
    ('external_docs', serial.properties.Object(types=(ExternalDocumentation,), name='externalDocs')),
    ('operation_id', serial.properties.String(name='operationId')),
    (
        'parameters',
        serial.properties.Property(
            types=(
                serial.properties.Array(
                    item_types=(Reference, Parameter),
                    versions=('openapi>=3.0',)
                ),
                serial.properties.Object(
                    types=(Reference, Parameter),
                    versions=('openapi<3.0',)
                )
            )
        )
    ),
    ('request_body', serial.properties.Object(types=(Reference, RequestBody), name='requestBody')),
    ('responses', serial.properties.Dictionary(value_types=(Response,))),
    ('deprecated', serial.properties.Boolean()),
    (
        'security',
        serial.properties.Array(
            item_types=(
                serial.properties.Dictionary(
                    value_types=(
                        serial.properties.Array(
                            item_types=(str,)
                        ),
                    )
                ),
            )
        )
    ),
    ('servers', serial.properties.Array(item_types=(Server,))),
    ('consumes', serial.properties.Array(item_types=(str,))),
    ('produces', serial.properties.Array(item_types=(str,))),
    (
        'callbacks',
        serial.properties.Dictionary(
            value_types=(
                serial.properties.Dictionary(
                    value_types=(PathItem,)
                )
            )
        )
    )
]


class Discriminator(Object):
    """
    https://swagger.io/specification/#discriminatorObject

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


meta.get(Discriminator).properties = [
    ('property_name', serial.properties.String(name='propertyName')),
    ('mapping', serial.properties.Dictionary(value_types=(str,))),
]


class XML(Object):
    """
    https://swagger.io/specification/#xmlObject

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


meta.get(XML).properties = [
    ('name', serial.properties.String()),
    ('name_space', serial.properties.String(name='nameSpace')),
    ('prefix', serial.properties.String()),
    ('attribute', serial.properties.Boolean()),
    ('wrapped', serial.properties.Boolean()),
]


class OAuthFlow(Object):
    """
    https://swagger.io/specification/#oauthFlowObject
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


meta.get(OAuthFlow).properties = [
    ('authorization_url', serial.properties.String()),
    ('token_url', serial.properties.String(name='tokenUrl')),
    ('refresh_url', serial.properties.String(name='refreshUrl')),
    ('scopes', serial.properties.Dictionary(value_types=(str,))),
]


class OAuthFlows(Object):
    """
    https://swagger.io/specification/#oauthFlowsObject
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


meta.get(OAuthFlows).properties = [
    ('implicit', serial.properties.Object(types=(OAuthFlow,))),
    ('password', serial.properties.Object(types=(OAuthFlow,))),
    ('client_credentials', serial.properties.Object(types=(OAuthFlow,), name='clientCredentials')),
    ('authorization_code', serial.properties.Object(types=(OAuthFlow,), name='authorizationCode')),
]


class SecurityScheme(Object):
    """
    https://swagger.io/specification/#requestBodyObject

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
        # 2.0 Compatibility
        flow=None,  # type: Optional[str]
        authorization_url=None,  # type: Optional[str]
        scopes=None,  # type: Optional[str]
    ):
        self.type_ = type_
        self.description = description
        self.name = name
        self.in_ = in_
        self.scheme = scheme
        self.bearer_format = bearer_format
        self.flows = flows
        self.open_id_connect_url = open_id_connect_url
        # 2.0 Compatibility
        self.flow = flow
        self.authorization_url = authorization_url
        self.scopes = scopes
        super().__init__(_)


meta.get(SecurityScheme).properties = [
    ('type_', serial.properties.String(name='type')),
    ('description', serial.properties.String()),
    ('name', serial.properties.String()),
    ('in_', serial.properties.String(name='in')),
    ('scheme', serial.properties.String()),
    ('bearer_format', serial.properties.String(name='bearerFormat')),
    ('flows', serial.properties.Object(types=(OAuthFlows,))),
    ('open_id_connect_url', serial.properties.String()),
    ('flow', serial.properties.String(versions='openapi<3.0')),
    ('authorization_url', serial.properties.String(name='authorizationUrl', versions='openapi<3.0')),
    ('scopes', serial.properties.Dictionary(value_types=(str,), versions='openapi<3.0'))
]

meta.get(Schema).properties = [
    ('schema', serial.properties.String(name='$schema')),
    ('id_', serial.properties.String(name='$id')),
    ('title', serial.properties.String()),
    ('description', serial.properties.String()),
    ('multiple_of', serial.properties.Number(name='multipleOf')),
    ('maximum', serial.properties.Number()),
    ('exclusive_maximum', serial.properties.Boolean(name='exclusiveMaximum')),
    ('minimum', serial.properties.Number()),
    ('exclusive_minimum', serial.properties.Boolean(name='exclusiveMinimum')),
    ('max_length', serial.properties.Integer(name='maxLength')),
    ('min_length', serial.properties.Integer(name='minLength')),
    ('pattern', serial.properties.String()),
    ('max_items', serial.properties.Integer(name='maxItems')),
    ('min_items', serial.properties.Integer(name='minItems')),
    ('unique_items', serial.properties.Boolean(name='uniqueItems')),
    (
        'items',
        serial.properties.Object(
            types=(
                Reference,
                Schema,
                serial.properties.Array(
                    item_types=(Reference, Schema)
                )
            )
        )
    ),
    (
        'additional_items',
        serial.properties.Object(
            types=(
                Schema,
                bool
            ),
            name='additionalItems'
        )
    ),
    ('max_properties', serial.properties.Integer(name='maxProperties')),
    ('min_properties', serial.properties.Integer(name='minProperties')),
    ('properties', serial.properties.Dictionary(value_types=(Reference, Schema,))),
    ('pattern_properties', serial.properties.Object(name='patternProperties')),
    ('additional_properties', serial.properties.Object(name='additionalProperties')),
    ('dependencies', serial.properties.Object(types=(Schema,), versions=('openapi<0.0',))),
    ('enum', serial.properties.Array()),
    (
        'type_',
        serial.properties.Property(
            types=(
                serial.properties.Array(
                    item_types=(str,)
                ),
                str
            ),
            name='type'
        )
    ),
    ('format_', serial.properties.String(name='format')),
    ('required', serial.properties.Array(item_types=(serial.properties.String(),))),
    ('all_of', serial.properties.Array(item_types=(Reference, Schema), name='allOf')),
    ('any_of', serial.properties.Array(item_types=(Reference, Schema), name='anyOf')),
    ('one_of', serial.properties.Array(item_types=(Reference, Schema), name='oneOf')),
    ('is_not', serial.properties.Object(types=(Reference, Schema), name='isNot')),
    ('definitions', serial.properties.Object()),
    ('default', serial.properties.Property()),
    ('required', serial.properties.Array(item_types=(str,))),
    ('default', serial.properties.Property()),
    ('discriminator', serial.properties.Object(types=(Discriminator,))),
    ('read_only', serial.properties.Boolean()),
    ('write_only', serial.properties.Boolean(name='writeOnly')),
    ('xml', serial.properties.Object(types=(XML,))),
    ('external_docs', serial.properties.Object(types=(ExternalDocumentation,))),
    ('example', serial.properties.Property()),
    ('deprecated', serial.properties.Boolean()),
    ('links', serial.properties.Array(item_types=(Link,))),
]


class Components(Object):

    def __init__(
        self,
        _=None,  # type: Optional[typing.Mapping]
        schemas=None,  # type: Union[typing.Mapping[str, Union[Schema, Reference]]]
        responses=None,  # type: Union[typing.Mapping[str, Union[Response, Reference]]]
        parameters=None,  # type: Union[typing.Mapping[str, Union[Parameter, Reference]]]
        examples=None,  # type: Union[typing.Mapping[str, Union[Example, Reference]]]
        request_bodies=None,  # type: Union[typing.Mapping[str, Union[RequestBody, Reference]]]
        headers=None,  # type: Union[typing.Mapping[str, Union[Header, Reference]]]
        security_schemes=None,  # type: Union[typing.Mapping[str, Union[SecurityScheme, Reference]]]
        links=None,  # type: Union[typing.Mapping[str, Union[Link_, Reference]]]
        callbacks=None,  # type: Union[typing.Mapping[str, Union[typing.Mapping[str, PathItem], Reference]]]
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


meta.get(Components).properties = [
    ('schemas', serial.properties.Dictionary(value_types=(Reference, Schema))),
    ('responses', serial.properties.Dictionary(value_types=(Reference, Response))),
    ('parameters', serial.properties.Dictionary(value_types=(Reference, Parameter))),
    ('examples', serial.properties.Dictionary(value_types=(Reference, Example))),
    ('request_bodies', serial.properties.Dictionary(value_types=(Reference, RequestBody))),
    ('headers', serial.properties.Dictionary(value_types=(Reference, Header))),
    ('security_schemes', serial.properties.Dictionary(value_types=(Reference, SecurityScheme), name='securitySchemes')),
    ('links', serial.properties.Dictionary(value_types=(Reference, Link_))),
    (
        'callbacks',
        serial.properties.Dictionary(
            value_types=(
                Reference,
                serial.properties.Dictionary(
                    value_types=(
                        PathItem,
                    )
                )
            )
        )
    ),
]


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
        super().__init__(_)
        version = self.openapi or self.swagger
        if version is not None:
            serial.model.version(self, 'openapi', version)


meta.get(OpenAPI).properties = [
    ('openapi', serial.properties.String(versions=('openapi>=3.0',))),
    ('info', serial.properties.Object(types=(Info,), required=True)),
    ('host', serial.properties.String()),
    ('servers', serial.properties.Array(item_types=(Server,))),
    ('base_path', serial.properties.String(name='basePath')),
    ('schemes', serial.properties.Array(item_types=(str,))),
    ('tags', serial.properties.Array(item_types=(Tag,))),
    ('paths', serial.properties.Dictionary(value_types=(PathItem,))),
    ('components', serial.properties.Object(types=(Components,))),
    ('consumes', serial.properties.Array(item_types=(str,))),
    ('swagger', serial.properties.String(versions=('openapi<3.0',))),
    (
        'definitions',
        serial.properties.Object(
            # versions=('openapi<3.0',)
        ),
    ),
    (
        'security_definitions',
        serial.properties.Dictionary(
            value_types=(SecurityScheme, str),
            name='securityDefinitions',
            versions=('openapi<3.0',)
        )
    ),
    ('produces', serial.properties.Array(item_types=(str,), versions=('openapi<3.0',)),),
    ('external_docs', serial.properties.Object(types=(ExternalDocumentation,), name='externalDocs'))
]
