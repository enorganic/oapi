"""
This module contains models describing objects defined by the [OpenAPI
Specification](https://github.com/OAI/OpenAPI-Specification). The root object,
`oapi.oas.OpenAPI` is capable of representing either an [OpenAPI 3
Document
](https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.1.1.md)
or an [OpenAPI 2 (Swagger) Document
](https://github.com/OAI/OpenAPI-Specification/blob/main/versions/2.0.md),
depending on the specification version identified in the document.
"""
from __future__ import annotations
import sob
import typing
from oapi._utilities import deprecated as _deprecated


if typing.TYPE_CHECKING:
    import decimal



class Callback(sob.Dictionary):

    def __init__(
        self,
        items: (
            sob.abc.Dictionary
            | typing.Mapping[
                str,
                PathItem
            ]
            | typing.Iterable[
                tuple[
                    str,
                    PathItem
                ]
            ]
            | sob.abc.Readable
            | str
            | bytes
            | None
        ) = None,
    ) -> None:
        super().__init__(items)


class Callbacks(sob.Dictionary):

    def __init__(
        self,
        items: (
            sob.abc.Dictionary
            | typing.Mapping[
                str,
                Reference
                | Callback
            ]
            | typing.Iterable[
                tuple[
                    str,
                    Reference
                    | Callback
                ]
            ]
            | sob.abc.Readable
            | str
            | bytes
            | None
        ) = None,
    ) -> None:
        super().__init__(items)


class Components(sob.Object):

    __slots__: tuple[str, ...] = (
        "schemas",
        "responses",
        "parameters",
        "examples",
        "request_bodies",
        "headers",
        "security_schemes",
        "links",
        "callbacks",
    )

    def __init__(
        self,
        _data: (
            sob.abc.Dictionary
            | typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ]
            | typing.Iterable[
                tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ]
            | sob.abc.Readable
            | typing.IO
            | str
            | bytes
            | None
        ) = None,
        schemas: (
            Schemas
            | None
        ) = None,
        responses: (
            Responses
            | None
        ) = None,
        parameters: (
            Parameters
            | None
        ) = None,
        examples: (
            Examples
            | None
        ) = None,
        request_bodies: (
            RequestBodies
            | None
        ) = None,
        headers: (
            Headers
            | None
        ) = None,
        security_schemes: (
            SecuritySchemes
            | None
        ) = None,
        links: (
            Links
            | None
        ) = None,
        callbacks: (
            Callbacks
            | None
        ) = None
    ) -> None:
        self.schemas: (
            Schemas
            | None
        ) = schemas
        self.responses: (
            Responses
            | None
        ) = responses
        self.parameters: (
            Parameters
            | None
        ) = parameters
        self.examples: (
            Examples
            | None
        ) = examples
        self.request_bodies: (
            RequestBodies
            | None
        ) = request_bodies
        self.headers: (
            Headers
            | None
        ) = headers
        self.security_schemes: (
            SecuritySchemes
            | None
        ) = security_schemes
        self.links: (
            Links
            | None
        ) = links
        self.callbacks: (
            Callbacks
            | None
        ) = callbacks
        super().__init__(_data)


class Contact(sob.Object):
    """
    [OpenAPI 3 Contact Object
    ](https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.1.1.md#
    contact-object)

    Attributes:
        name:
        url:
        email:
    """

    __slots__: tuple[str, ...] = (
        "name",
        "url",
        "email",
    )

    def __init__(
        self,
        _data: (
            sob.abc.Dictionary
            | typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ]
            | typing.Iterable[
                tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ]
            | sob.abc.Readable
            | typing.IO
            | str
            | bytes
            | None
        ) = None,
        name: (
            str
            | None
        ) = None,
        url: (
            str
            | None
        ) = None,
        email: (
            str
            | None
        ) = None
    ) -> None:
        self.name: (
            str
            | None
        ) = name
        self.url: (
            str
            | None
        ) = url
        self.email: (
            str
            | None
        ) = email
        super().__init__(_data)


class Definitions(sob.Dictionary):

    def __init__(
        self,
        items: (
            sob.abc.Dictionary
            | typing.Mapping[
                str,
                Schema
            ]
            | typing.Iterable[
                tuple[
                    str,
                    Schema
                ]
            ]
            | sob.abc.Readable
            | str
            | bytes
            | None
        ) = None,
    ) -> None:
        super().__init__(items)


class Discriminator(sob.Object):
    """
    [OpenAPI 3 Discriminator Object
    ](https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.1.1.md#
    discriminator-object)

    Attributes:
        property_name: The name of the property which will hold the
            discriminating value.
        mapping: An mappings of payload values to schema names or
            references.
    """

    __slots__: tuple[str, ...] = (
        "property_name",
        "mapping",
    )

    def __init__(
        self,
        _data: (
            sob.abc.Dictionary
            | typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ]
            | typing.Iterable[
                tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ]
            | sob.abc.Readable
            | typing.IO
            | str
            | bytes
            | None
        ) = None,
        property_name: (
            str
            | None
        ) = None,
        mapping: (
            typing.Mapping[
                str,
                str
            ]
            | None
        ) = None
    ) -> None:
        self.property_name: (
            str
            | None
        ) = property_name
        self.mapping: (
            typing.Mapping[
                str,
                str
            ]
            | None
        ) = mapping
        super().__init__(_data)


class Encoding(sob.Object):
    """
    [OpenAPI 3 Encoding Object
    ](https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.1.1.md#
    encoding-object)

    Attributes:
        content_type:
        headers:
        style:
        explode:
        allow_reserved:
    """

    __slots__: tuple[str, ...] = (
        "content_type",
        "headers",
        "style",
        "explode",
        "allow_reserved",
    )

    def __init__(
        self,
        _data: (
            sob.abc.Dictionary
            | typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ]
            | typing.Iterable[
                tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ]
            | sob.abc.Readable
            | typing.IO
            | str
            | bytes
            | None
        ) = None,
        content_type: (
            str
            | None
        ) = None,
        headers: (
            typing.Mapping[
                str,
                Reference
                | Header
            ]
            | None
        ) = None,
        style: (
            str
            | None
        ) = None,
        explode: (
            bool
            | None
        ) = None,
        allow_reserved: (
            bool
            | None
        ) = None
    ) -> None:
        self.content_type: (
            str
            | None
        ) = content_type
        self.headers: (
            typing.Mapping[
                str,
                Reference
                | Header
            ]
            | None
        ) = headers
        self.style: (
            str
            | None
        ) = style
        self.explode: (
            bool
            | None
        ) = explode
        self.allow_reserved: (
            bool
            | None
        ) = allow_reserved
        super().__init__(_data)


class Example(sob.Object):
    """
    [OpenAPI 3 Example Object
    ](https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.1.1.md#
    example-object)

    Attributes:
        summary:
        description:
        value:
        external_value:
    """

    __slots__: tuple[str, ...] = (
        "summary",
        "description",
        "value",
        "external_value",
    )

    def __init__(
        self,
        _data: (
            sob.abc.Dictionary
            | typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ]
            | typing.Iterable[
                tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ]
            | sob.abc.Readable
            | typing.IO
            | str
            | bytes
            | None
        ) = None,
        summary: (
            str
            | None
        ) = None,
        description: (
            str
            | None
        ) = None,
        value: (
            typing.Any
            | None
        ) = None,
        external_value: (
            str
            | None
        ) = None
    ) -> None:
        self.summary: (
            str
            | None
        ) = summary
        self.description: (
            str
            | None
        ) = description
        self.value: (
            typing.Any
            | None
        ) = value
        self.external_value: (
            str
            | None
        ) = external_value
        super().__init__(_data)


class Examples(sob.Dictionary):

    def __init__(
        self,
        items: (
            sob.abc.Dictionary
            | typing.Mapping[
                str,
                Reference
                | Example
            ]
            | typing.Iterable[
                tuple[
                    str,
                    Reference
                    | Example
                ]
            ]
            | sob.abc.Readable
            | str
            | bytes
            | None
        ) = None,
    ) -> None:
        super().__init__(items)


class ExternalDocumentation(sob.Object):
    """
    [OpenAPI 3 External Documentation Object
    ](https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.1.1.md#
    external-documentation-object)

    Attributes:
        description:
        url:
    """

    __slots__: tuple[str, ...] = (
        "description",
        "url",
    )

    def __init__(
        self,
        _data: (
            sob.abc.Dictionary
            | typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ]
            | typing.Iterable[
                tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ]
            | sob.abc.Readable
            | typing.IO
            | str
            | bytes
            | None
        ) = None,
        description: (
            str
            | None
        ) = None,
        url: (
            str
            | None
        ) = None
    ) -> None:
        self.description: (
            str
            | None
        ) = description
        self.url: (
            str
            | None
        ) = url
        super().__init__(_data)


class Header(sob.Object):
    """
    [OpenAPI 3 Header Object
    ](https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.1.1.md#
    header-object)

    Attributes:
        description:
        required:
        deprecated:
        allow_empty_value:
        style:
        explode:
        allow_reserved:
        schema:
        example:
        examples:
        content:
        type_:
        default:
        maximum:
        exclusive_maximum:
        minimum:
        exclusive_minimum:
        max_length:
        min_length:
        pattern:
        max_items:
        min_items:
        unique_items:
        enum:
        format_:
        collection_format:
        items:
        multiple_of:
    """

    __slots__: tuple[str, ...] = (
        "description",
        "required",
        "deprecated",
        "allow_empty_value",
        "style",
        "explode",
        "allow_reserved",
        "schema",
        "example",
        "examples",
        "content",
        "type_",
        "default",
        "maximum",
        "exclusive_maximum",
        "minimum",
        "exclusive_minimum",
        "max_length",
        "min_length",
        "pattern",
        "max_items",
        "min_items",
        "unique_items",
        "enum",
        "format_",
        "collection_format",
        "items",
        "multiple_of",
    )

    def __init__(
        self,
        _data: (
            sob.abc.Dictionary
            | typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ]
            | typing.Iterable[
                tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ]
            | sob.abc.Readable
            | typing.IO
            | str
            | bytes
            | None
        ) = None,
        description: (
            str
            | None
        ) = None,
        required: (
            bool
            | None
        ) = None,
        deprecated: (
            bool
            | None
        ) = None,
        allow_empty_value: (
            bool
            | None
        ) = None,
        style: (
            str
            | None
        ) = None,
        explode: (
            bool
            | None
        ) = None,
        allow_reserved: (
            bool
            | None
        ) = None,
        schema: (
            Reference
            | Schema
            | None
        ) = None,
        example: (
            typing.Any
            | None
        ) = None,
        examples: (
            typing.Mapping[
                str,
                Reference
                | Example
            ]
            | None
        ) = None,
        content: (
            typing.Mapping[
                str,
                MediaType
            ]
            | None
        ) = None,
        type_: (
            str
            | None
        ) = None,
        default: (
            typing.Any
            | None
        ) = None,
        maximum: (
            float
            | int
            | decimal.Decimal
            | None
        ) = None,
        exclusive_maximum: (
            bool
            | None
        ) = None,
        minimum: (
            float
            | int
            | decimal.Decimal
            | None
        ) = None,
        exclusive_minimum: (
            bool
            | None
        ) = None,
        max_length: (
            int
            | None
        ) = None,
        min_length: (
            int
            | None
        ) = None,
        pattern: (
            str
            | None
        ) = None,
        max_items: (
            int
            | None
        ) = None,
        min_items: (
            int
            | None
        ) = None,
        unique_items: (
            bool
            | None
        ) = None,
        enum: (
            typing.Sequence[
                sob.abc.MarshallableTypes | None
            ]
            | None
        ) = None,
        format_: (
            str
            | None
        ) = None,
        collection_format: (
            str
            | None
        ) = None,
        items: (
            Items
            | None
        ) = None,
        multiple_of: (
            float
            | int
            | decimal.Decimal
            | None
        ) = None
    ) -> None:
        self.description: (
            str
            | None
        ) = description
        self.required: (
            bool
            | None
        ) = required
        self.deprecated: (
            bool
            | None
        ) = deprecated
        self.allow_empty_value: (
            bool
            | None
        ) = allow_empty_value
        self.style: (
            str
            | None
        ) = style
        self.explode: (
            bool
            | None
        ) = explode
        self.allow_reserved: (
            bool
            | None
        ) = allow_reserved
        self.schema: (
            Reference
            | Schema
            | None
        ) = schema
        self.example: (
            typing.Any
            | None
        ) = example
        self.examples: (
            typing.Mapping[
                str,
                Reference
                | Example
            ]
            | None
        ) = examples
        self.content: (
            typing.Mapping[
                str,
                MediaType
            ]
            | None
        ) = content
        self.type_: (
            str
            | None
        ) = type_
        self.default: (
            typing.Any
            | None
        ) = default
        self.maximum: (
            float
            | int
            | decimal.Decimal
            | None
        ) = maximum
        self.exclusive_maximum: (
            bool
            | None
        ) = exclusive_maximum
        self.minimum: (
            float
            | int
            | decimal.Decimal
            | None
        ) = minimum
        self.exclusive_minimum: (
            bool
            | None
        ) = exclusive_minimum
        self.max_length: (
            int
            | None
        ) = max_length
        self.min_length: (
            int
            | None
        ) = min_length
        self.pattern: (
            str
            | None
        ) = pattern
        self.max_items: (
            int
            | None
        ) = max_items
        self.min_items: (
            int
            | None
        ) = min_items
        self.unique_items: (
            bool
            | None
        ) = unique_items
        self.enum: (
            typing.Sequence[
                sob.abc.MarshallableTypes | None
            ]
            | None
        ) = enum
        self.format_: (
            str
            | None
        ) = format_
        self.collection_format: (
            str
            | None
        ) = collection_format
        self.items: (
            Items
            | None
        ) = items
        self.multiple_of: (
            float
            | int
            | decimal.Decimal
            | None
        ) = multiple_of
        super().__init__(_data)


class Headers(sob.Dictionary):

    def __init__(
        self,
        items: (
            sob.abc.Dictionary
            | typing.Mapping[
                str,
                Reference
                | Header
            ]
            | typing.Iterable[
                tuple[
                    str,
                    Reference
                    | Header
                ]
            ]
            | sob.abc.Readable
            | str
            | bytes
            | None
        ) = None,
    ) -> None:
        super().__init__(items)


class Info(sob.Object):
    """
    [OpenAPI 3 Info Object
    ](https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.1.1.md#
    info-object)

    Attributes:
        title:
        description:
        terms_of_service:
        contact:
        license_:
        version:
    """

    __slots__: tuple[str, ...] = (
        "title",
        "description",
        "terms_of_service",
        "contact",
        "license_",
        "version",
    )

    def __init__(
        self,
        _data: (
            sob.abc.Dictionary
            | typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ]
            | typing.Iterable[
                tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ]
            | sob.abc.Readable
            | typing.IO
            | str
            | bytes
            | None
        ) = None,
        title: (
            str
            | None
        ) = None,
        description: (
            str
            | None
        ) = None,
        terms_of_service: (
            str
            | None
        ) = None,
        contact: (
            Contact
            | None
        ) = None,
        license_: (
            License
            | None
        ) = None,
        version: (
            str
            | None
        ) = None
    ) -> None:
        self.title: (
            str
            | None
        ) = title
        self.description: (
            str
            | None
        ) = description
        self.terms_of_service: (
            str
            | None
        ) = terms_of_service
        self.contact: (
            Contact
            | None
        ) = contact
        self.license_: (
            License
            | None
        ) = license_
        self.version: (
            str
            | None
        ) = version
        super().__init__(_data)


class Items(sob.Object):
    """
    [OpenAPI 2 Items Object
    ](https://github.com/OAI/OpenAPI-Specification/blob/main/versions/2.0.md#
    items-object)

    Attributes:
        type_:
        format_:
        items:
        collection_format:
        default:
        maximum:
        exclusive_maximum:
        minimum:
        exclusive_minimum:
        max_length:
        min_length:
        pattern:
        max_items:
        min_items:
        unique_items:
        enum:
        multiple_of:
    """

    __slots__: tuple[str, ...] = (
        "type_",
        "format_",
        "items",
        "collection_format",
        "default",
        "maximum",
        "exclusive_maximum",
        "minimum",
        "exclusive_minimum",
        "max_length",
        "min_length",
        "pattern",
        "max_items",
        "min_items",
        "unique_items",
        "enum",
        "multiple_of",
    )

    def __init__(
        self,
        _data: (
            sob.abc.Dictionary
            | typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ]
            | typing.Iterable[
                tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ]
            | sob.abc.Readable
            | typing.IO
            | str
            | bytes
            | None
        ) = None,
        type_: (
            str
            | None
        ) = None,
        format_: (
            str
            | None
        ) = None,
        items: (
            Items
            | None
        ) = None,
        collection_format: (
            str
            | None
        ) = None,
        default: (
            typing.Any
            | None
        ) = None,
        maximum: (
            float
            | int
            | decimal.Decimal
            | None
        ) = None,
        exclusive_maximum: (
            bool
            | None
        ) = None,
        minimum: (
            float
            | int
            | decimal.Decimal
            | None
        ) = None,
        exclusive_minimum: (
            bool
            | None
        ) = None,
        max_length: (
            int
            | None
        ) = None,
        min_length: (
            int
            | None
        ) = None,
        pattern: (
            str
            | None
        ) = None,
        max_items: (
            int
            | None
        ) = None,
        min_items: (
            int
            | None
        ) = None,
        unique_items: (
            bool
            | None
        ) = None,
        enum: (
            typing.Sequence[
                sob.abc.MarshallableTypes | None
            ]
            | None
        ) = None,
        multiple_of: (
            float
            | int
            | decimal.Decimal
            | None
        ) = None
    ) -> None:
        self.type_: (
            str
            | None
        ) = type_
        self.format_: (
            str
            | None
        ) = format_
        self.items: (
            Items
            | None
        ) = items
        self.collection_format: (
            str
            | None
        ) = collection_format
        self.default: (
            typing.Any
            | None
        ) = default
        self.maximum: (
            float
            | int
            | decimal.Decimal
            | None
        ) = maximum
        self.exclusive_maximum: (
            bool
            | None
        ) = exclusive_maximum
        self.minimum: (
            float
            | int
            | decimal.Decimal
            | None
        ) = minimum
        self.exclusive_minimum: (
            bool
            | None
        ) = exclusive_minimum
        self.max_length: (
            int
            | None
        ) = max_length
        self.min_length: (
            int
            | None
        ) = min_length
        self.pattern: (
            str
            | None
        ) = pattern
        self.max_items: (
            int
            | None
        ) = max_items
        self.min_items: (
            int
            | None
        ) = min_items
        self.unique_items: (
            bool
            | None
        ) = unique_items
        self.enum: (
            typing.Sequence[
                sob.abc.MarshallableTypes | None
            ]
            | None
        ) = enum
        self.multiple_of: (
            float
            | int
            | decimal.Decimal
            | None
        ) = multiple_of
        super().__init__(_data)


class License(sob.Object):
    """
    [OpenAPI 3 License Object
    ](https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.1.1.md#
    license-object)

    Attributes:
        name:
        url:
    """

    __slots__: tuple[str, ...] = (
        "name",
        "url",
    )

    def __init__(
        self,
        _data: (
            sob.abc.Dictionary
            | typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ]
            | typing.Iterable[
                tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ]
            | sob.abc.Readable
            | typing.IO
            | str
            | bytes
            | None
        ) = None,
        name: (
            str
            | None
        ) = None,
        url: (
            str
            | None
        ) = None
    ) -> None:
        self.name: (
            str
            | None
        ) = name
        self.url: (
            str
            | None
        ) = url
        super().__init__(_data)


class Link(sob.Object):

    __slots__: tuple[str, ...] = (
        "rel",
        "href",
    )

    def __init__(
        self,
        _data: (
            sob.abc.Dictionary
            | typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ]
            | typing.Iterable[
                tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ]
            | sob.abc.Readable
            | typing.IO
            | str
            | bytes
            | None
        ) = None,
        rel: (
            str
            | None
        ) = None,
        href: (
            str
            | None
        ) = None
    ) -> None:
        self.rel: (
            str
            | None
        ) = rel
        self.href: (
            str
            | None
        ) = href
        super().__init__(_data)


class LinkObject(sob.Object):
    """
    [OpenAPI 3 Link Object
    ](https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.1.1.md#
    link-object)

    Attributes:
        operation_ref:
        operation_id:
        parameters:
        request_body:
        description:
        server:
    """

    __slots__: tuple[str, ...] = (
        "operation_ref",
        "operation_id",
        "parameters",
        "request_body",
        "description",
        "server",
    )

    def __init__(
        self,
        _data: (
            sob.abc.Dictionary
            | typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ]
            | typing.Iterable[
                tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ]
            | sob.abc.Readable
            | typing.IO
            | str
            | bytes
            | None
        ) = None,
        operation_ref: (
            str
            | None
        ) = None,
        operation_id: (
            str
            | None
        ) = None,
        parameters: (
            typing.Mapping[
                str,
                sob.abc.MarshallableTypes | None
            ]
            | None
        ) = None,
        request_body: (
            typing.Any
            | None
        ) = None,
        description: (
            str
            | None
        ) = None,
        server: (
            Server
            | None
        ) = None
    ) -> None:
        self.operation_ref: (
            str
            | None
        ) = operation_ref
        self.operation_id: (
            str
            | None
        ) = operation_id
        self.parameters: (
            typing.Mapping[
                str,
                sob.abc.MarshallableTypes | None
            ]
            | None
        ) = parameters
        self.request_body: (
            typing.Any
            | None
        ) = request_body
        self.description: (
            str
            | None
        ) = description
        self.server: (
            Server
            | None
        ) = server
        super().__init__(_data)


class Links(sob.Dictionary):

    def __init__(
        self,
        items: (
            sob.abc.Dictionary
            | typing.Mapping[
                str,
                Reference
                | LinkObject
            ]
            | typing.Iterable[
                tuple[
                    str,
                    Reference
                    | LinkObject
                ]
            ]
            | sob.abc.Readable
            | str
            | bytes
            | None
        ) = None,
    ) -> None:
        super().__init__(items)


class MediaType(sob.Object):
    """
    [OpenAPI 3 Media Type Object
    ](https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.1.1.md#
    media-type-object)

    Attributes:
        schema:
        example:
        examples:
        encoding:
    """

    __slots__: tuple[str, ...] = (
        "schema",
        "example",
        "examples",
        "encoding",
    )

    def __init__(
        self,
        _data: (
            sob.abc.Dictionary
            | typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ]
            | typing.Iterable[
                tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ]
            | sob.abc.Readable
            | typing.IO
            | str
            | bytes
            | None
        ) = None,
        schema: (
            Reference
            | Schema
            | None
        ) = None,
        example: (
            typing.Any
            | None
        ) = None,
        examples: (
            typing.Mapping[
                str,
                Reference
                | Example
            ]
            | None
        ) = None,
        encoding: (
            typing.Mapping[
                str,
                Reference
                | Encoding
            ]
            | None
        ) = None
    ) -> None:
        self.schema: (
            Reference
            | Schema
            | None
        ) = schema
        self.example: (
            typing.Any
            | None
        ) = example
        self.examples: (
            typing.Mapping[
                str,
                Reference
                | Example
            ]
            | None
        ) = examples
        self.encoding: (
            typing.Mapping[
                str,
                Reference
                | Encoding
            ]
            | None
        ) = encoding
        super().__init__(_data)


class OAuthFlow(sob.Object):
    """
    [OpenAPI 3 Parameter Object
    ](https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.1.1.md#
    parameter-object)

    Attributes:
        authorization_url:
        token_url:
        refresh_url:
        scopes:
    """

    __slots__: tuple[str, ...] = (
        "authorization_url",
        "token_url",
        "refresh_url",
        "scopes",
    )

    def __init__(
        self,
        _data: (
            sob.abc.Dictionary
            | typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ]
            | typing.Iterable[
                tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ]
            | sob.abc.Readable
            | typing.IO
            | str
            | bytes
            | None
        ) = None,
        authorization_url: (
            str
            | None
        ) = None,
        token_url: (
            str
            | None
        ) = None,
        refresh_url: (
            str
            | None
        ) = None,
        scopes: (
            typing.Mapping[
                str,
                str
            ]
            | None
        ) = None
    ) -> None:
        self.authorization_url: (
            str
            | None
        ) = authorization_url
        self.token_url: (
            str
            | None
        ) = token_url
        self.refresh_url: (
            str
            | None
        ) = refresh_url
        self.scopes: (
            typing.Mapping[
                str,
                str
            ]
            | None
        ) = scopes
        super().__init__(_data)


class OAuthFlows(sob.Object):
    """
    [OpenAPI 3 OAuth Flows Object
    ](https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.1.1.md#
    oauth-flows-object)

    Attributes:
        implicit:
        password:
        client_credentials:
        authorization_code:
    """

    __slots__: tuple[str, ...] = (
        "implicit",
        "password",
        "client_credentials",
        "authorization_code",
    )

    def __init__(
        self,
        _data: (
            sob.abc.Dictionary
            | typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ]
            | typing.Iterable[
                tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ]
            | sob.abc.Readable
            | typing.IO
            | str
            | bytes
            | None
        ) = None,
        implicit: (
            OAuthFlow
            | None
        ) = None,
        password: (
            OAuthFlow
            | None
        ) = None,
        client_credentials: (
            OAuthFlow
            | None
        ) = None,
        authorization_code: (
            OAuthFlow
            | None
        ) = None
    ) -> None:
        self.implicit: (
            OAuthFlow
            | None
        ) = implicit
        self.password: (
            OAuthFlow
            | None
        ) = password
        self.client_credentials: (
            OAuthFlow
            | None
        ) = client_credentials
        self.authorization_code: (
            OAuthFlow
            | None
        ) = authorization_code
        super().__init__(_data)


class OpenAPI(sob.Object):
    """
    [OpenAPI 3 OpenAPI (root) Object
    ](https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.1.0.md#
    openapi-object)

    Attributes:
        openapi:
        info:
        json_schema_dialect:
        host:
        servers:
        base_path:
        schemes:
        tags:
        paths:
        components:
        consumes:
        swagger:
        definitions:
        security_definitions:
        produces:
        external_docs:
        parameters:
        responses:
        security:
    """

    __slots__: tuple[str, ...] = (
        "openapi",
        "info",
        "json_schema_dialect",
        "host",
        "servers",
        "base_path",
        "schemes",
        "tags",
        "paths",
        "components",
        "consumes",
        "swagger",
        "definitions",
        "security_definitions",
        "produces",
        "external_docs",
        "parameters",
        "responses",
        "security",
    )

    def __init__(
        self,
        _data: (
            sob.abc.Dictionary
            | typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ]
            | typing.Iterable[
                tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ]
            | sob.abc.Readable
            | typing.IO
            | str
            | bytes
            | None
        ) = None,
        openapi: (
            str
            | None
        ) = None,
        info: (
            Info
            | None
        ) = None,
        json_schema_dialect: (
            str
            | None
        ) = None,
        host: (
            str
            | None
        ) = None,
        servers: (
            typing.Sequence[
                Server
            ]
            | None
        ) = None,
        base_path: (
            str
            | None
        ) = None,
        schemes: (
            typing.Sequence[
                str
            ]
            | None
        ) = None,
        tags: (
            typing.Sequence[
                Tag
            ]
            | None
        ) = None,
        paths: (
            Paths
            | None
        ) = None,
        components: (
            Components
            | None
        ) = None,
        consumes: (
            typing.Sequence[
                str
            ]
            | None
        ) = None,
        swagger: (
            str
            | None
        ) = None,
        definitions: (
            Definitions
            | None
        ) = None,
        security_definitions: (
            SecuritySchemes
            | None
        ) = None,
        produces: (
            typing.Sequence[
                str
            ]
            | None
        ) = None,
        external_docs: (
            ExternalDocumentation
            | None
        ) = None,
        parameters: (
            typing.Mapping[
                str,
                Parameter
            ]
            | None
        ) = None,
        responses: (
            typing.Mapping[
                str,
                Response
            ]
            | None
        ) = None,
        security: (
            typing.Sequence[
                SecurityRequirement
            ]
            | None
        ) = None
    ) -> None:
        self.openapi: (
            str
            | None
        ) = openapi
        self.info: (
            Info
            | None
        ) = info
        self.json_schema_dialect: (
            str
            | None
        ) = json_schema_dialect
        self.host: (
            str
            | None
        ) = host
        self.servers: (
            typing.Sequence[
                Server
            ]
            | None
        ) = servers
        self.base_path: (
            str
            | None
        ) = base_path
        self.schemes: (
            typing.Sequence[
                str
            ]
            | None
        ) = schemes
        self.tags: (
            typing.Sequence[
                Tag
            ]
            | None
        ) = tags
        self.paths: (
            Paths
            | None
        ) = paths
        self.components: (
            Components
            | None
        ) = components
        self.consumes: (
            typing.Sequence[
                str
            ]
            | None
        ) = consumes
        self.swagger: (
            str
            | None
        ) = swagger
        self.definitions: (
            Definitions
            | None
        ) = definitions
        self.security_definitions: (
            SecuritySchemes
            | None
        ) = security_definitions
        self.produces: (
            typing.Sequence[
                str
            ]
            | None
        ) = produces
        self.external_docs: (
            ExternalDocumentation
            | None
        ) = external_docs
        self.parameters: (
            typing.Mapping[
                str,
                Parameter
            ]
            | None
        ) = parameters
        self.responses: (
            typing.Mapping[
                str,
                Response
            ]
            | None
        ) = responses
        self.security: (
            typing.Sequence[
                SecurityRequirement
            ]
            | None
        ) = security
        super().__init__(_data)
        version: str = self.openapi or self.swagger or ""
        if version:
            sob.version_model(self, "openapi", version)


class Operation(sob.Object):
    """
    [Open API 3 Operation Object
    ](https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.1.1.md#
    operation-object)

    Describes a single API operation on a path.

    Attributes:
        tags:  A list of tags for API documentation control. Tags can
            be used for logical grouping of operations by resources or any
            other qualifier.
        summary:  A short summary of what the operation does.
        description: A verbose explanation of the operation behavior. `
            CommonMark <http://spec.commonmark.org>` syntax may be used for
            rich text representation.
        external_docs:  Additional external
            documentation for this operation.
        operation_id:  Unique string used to identify the operation.
            The ID must be unique among all operations described in the API.
            Tools and libraries may use the `operation_id` to uniquely identify
            an operation, therefore, it is recommended to follow common
            programming naming conventions.
        parameters:  A list of parameters that are
            applicable for this operation. If a parameter is already defined at
            the `PathItem`, the new definition will override it, but can never
            remove it.
        request_body:  The request body applicable
            for this operation. The requestBody is only
            supported in HTTP methods where the HTTP 1.1 specification
            `RFC7231 <https://tools.ietf.org/html/rfc7231#section-4.3.1>` has
            explicitly defined semantics for request
            bodies.
        responses: A mapping of HTTP
            response codes to `Response` objects.
        callbacks:
        deprecated:
        security:
        servers:
        produces: (OpenAPI 2x only)
    """

    __slots__: tuple[str, ...] = (
        "tags",
        "summary",
        "description",
        "external_docs",
        "operation_id",
        "consumes",
        "produces",
        "parameters",
        "request_body",
        "responses",
        "callbacks",
        "schemes",
        "deprecated",
        "security",
        "servers",
    )

    def __init__(
        self,
        _data: (
            sob.abc.Dictionary
            | typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ]
            | typing.Iterable[
                tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ]
            | sob.abc.Readable
            | typing.IO
            | str
            | bytes
            | None
        ) = None,
        tags: (
            typing.Sequence[
                str
            ]
            | None
        ) = None,
        summary: (
            str
            | None
        ) = None,
        description: (
            str
            | None
        ) = None,
        external_docs: (
            ExternalDocumentation
            | None
        ) = None,
        operation_id: (
            str
            | None
        ) = None,
        consumes: (
            typing.Sequence[
                str
            ]
            | None
        ) = None,
        produces: (
            typing.Sequence[
                str
            ]
            | None
        ) = None,
        parameters: (
            typing.Sequence[
                Reference
            | Parameter
            ]
            | None
        ) = None,
        request_body: (
            Reference
            | RequestBody
            | None
        ) = None,
        responses: (
            Responses
            | None
        ) = None,
        callbacks: (
            Callbacks
            | None
        ) = None,
        schemes: (
            typing.Sequence[
                str
            ]
            | None
        ) = None,
        deprecated: (
            bool
            | None
        ) = None,
        security: (
            typing.Sequence[
                SecurityRequirement
            ]
            | None
        ) = None,
        servers: (
            typing.Sequence[
                Server
            ]
            | None
        ) = None
    ) -> None:
        self.tags: (
            typing.Sequence[
                str
            ]
            | None
        ) = tags
        self.summary: (
            str
            | None
        ) = summary
        self.description: (
            str
            | None
        ) = description
        self.external_docs: (
            ExternalDocumentation
            | None
        ) = external_docs
        self.operation_id: (
            str
            | None
        ) = operation_id
        self.consumes: (
            typing.Sequence[
                str
            ]
            | None
        ) = consumes
        self.produces: (
            typing.Sequence[
                str
            ]
            | None
        ) = produces
        self.parameters: (
            typing.Sequence[
                Reference
            | Parameter
            ]
            | None
        ) = parameters
        self.request_body: (
            Reference
            | RequestBody
            | None
        ) = request_body
        self.responses: (
            Responses
            | None
        ) = responses
        self.callbacks: (
            Callbacks
            | None
        ) = callbacks
        self.schemes: (
            typing.Sequence[
                str
            ]
            | None
        ) = schemes
        self.deprecated: (
            bool
            | None
        ) = deprecated
        self.security: (
            typing.Sequence[
                SecurityRequirement
            ]
            | None
        ) = security
        self.servers: (
            typing.Sequence[
                Server
            ]
            | None
        ) = servers
        super().__init__(_data)


class Parameter(sob.Object):
    """
    [OpenAPI 3 Parameter Object
    ](https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.1.1.md#
    parameter-object)
    | [OpenAPI 2 Parameter Object
    ](https://github.com/OAI/OpenAPI-Specification/blob/main/versions/2.0.md#
    parameter-object)

    Attributes:
        name:
        in_: "path", "query", "header", or "cookie"
        description:
        required:
        deprecated:
        allow_empty_value: Sets the ability to pass empty-valued
            parameters. This is valid only for query parameters and allows
            sending a parameter with an empty value. The default value is
            `False`. If `style` is used, and if `behavior` is inapplicable
            (cannot be serialized), the value of `allow_empty_value` will be
            ignored.
        style: Describes how the parameter value will be serialized,
            depending on the type of the parameter value (see:
            [Parameter Serialization
            ](https://swagger.io/docs/specification/serialization)).
            Valid values include: "matrix", "label", "form", "simple",
            "spaceDelimited", "pipeDelimited", and "deepObject".
            The default values vary by location (`in_`). For "query": "form",
            path: "simple", header: "simple", and cookie: "form".
        explode: When this is `True`, array or object parameter values
            generate separate parameters for each value of the array or
            name-value pair of the map. For other value_types of parameters
            this property has no effect. When `style` is "form", the default
            value is `True`. For all other styles, the default value is
            `False`.
        allow_reserved: Determines whether the parameter value SHOULD
            allow reserved characters :/?#[]@!$&'()*+,;= (as defined by
            [RFC3986](https://tools.ietf.org/html/rfc3986#section-2.2) to be
            included without percent-encoding. This property only applies to
            "query" parameters. The default value is `False`.
        schema: The schema defining the type used for the parameter.
        example: An example of the parameter's potential value—see
            [Working With Examples
            ](https://github.com/OAI/OpenAPI-Specification/blob/main/versions/
            3.1.1.md#working-with-examples).
            Either an `example` or `examples` parameter may be provided,
            but not both.
        examples: Examples of the parameter's potential values—see
            [Working With Examples
            ](https://github.com/OAI/OpenAPI-Specification/blob/main/versions/
            3.1.1.md#working-with-examples).
            Either an `example` or `examples` parameter may be provided,
            but not both.
        content: A mapping with a media type name and the object describing it.
            The mapping must only contain one entry. See
            [Fixed fields for use with content
            ](https://github.com/OAI/OpenAPI-Specification/blob/main/versions/
            3.1.1.md#fixed-fields-for-use-with-content).
        type_: (Open API 2x only)
        enum: (Open API 2x only)
        collection_format: (Open API 2x only) Determines the format of the
            array if `type_ == "array"`. Possible values include:

            -   csv: comma separated values foo,bar.
            -   ssv: space separated values foo bar.
            -   tsv: tab separated values foo    bar.
            -   pipes: pipe separated values foo|bar.
            -   multi: corresponds to multiple parameter instances instead of
                multiple values for a single instance foo=bar&foo=baz. This
                is valid only for parameters in "query" or "formData".
    """

    __slots__: tuple[str, ...] = (
        "name",
        "in_",
        "description",
        "required",
        "deprecated",
        "allow_empty_value",
        "style",
        "explode",
        "allow_reserved",
        "schema",
        "example",
        "examples",
        "content",
        "type_",
        "default",
        "maximum",
        "exclusive_maximum",
        "minimum",
        "exclusive_minimum",
        "max_length",
        "min_length",
        "pattern",
        "max_items",
        "min_items",
        "unique_items",
        "enum",
        "format_",
        "collection_format",
        "items",
        "multiple_of",
    )

    def __init__(
        self,
        _data: (
            sob.abc.Dictionary
            | typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ]
            | typing.Iterable[
                tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ]
            | sob.abc.Readable
            | typing.IO
            | str
            | bytes
            | None
        ) = None,
        name: (
            str
            | None
        ) = None,
        in_: (
            str
            | None
        ) = None,
        description: (
            str
            | None
        ) = None,
        required: (
            bool
            | None
        ) = None,
        deprecated: (
            bool
            | None
        ) = None,
        allow_empty_value: (
            bool
            | None
        ) = None,
        style: (
            str
            | None
        ) = None,
        explode: (
            bool
            | None
        ) = None,
        allow_reserved: (
            bool
            | None
        ) = None,
        schema: (
            Reference
            | Schema
            | None
        ) = None,
        example: (
            typing.Any
            | None
        ) = None,
        examples: (
            typing.Mapping[
                str,
                Reference
                | Example
            ]
            | None
        ) = None,
        content: (
            typing.Mapping[
                str,
                MediaType
            ]
            | None
        ) = None,
        type_: (
            str
            | None
        ) = None,
        default: (
            typing.Any
            | None
        ) = None,
        maximum: (
            float
            | int
            | decimal.Decimal
            | None
        ) = None,
        exclusive_maximum: (
            bool
            | None
        ) = None,
        minimum: (
            float
            | int
            | decimal.Decimal
            | None
        ) = None,
        exclusive_minimum: (
            bool
            | None
        ) = None,
        max_length: (
            int
            | None
        ) = None,
        min_length: (
            int
            | None
        ) = None,
        pattern: (
            str
            | None
        ) = None,
        max_items: (
            int
            | None
        ) = None,
        min_items: (
            int
            | None
        ) = None,
        unique_items: (
            bool
            | None
        ) = None,
        enum: (
            typing.Sequence[
                sob.abc.MarshallableTypes | None
            ]
            | None
        ) = None,
        format_: (
            str
            | None
        ) = None,
        collection_format: (
            str
            | None
        ) = None,
        items: (
            Items
            | None
        ) = None,
        multiple_of: (
            float
            | int
            | decimal.Decimal
            | None
        ) = None
    ) -> None:
        self.name: (
            str
            | None
        ) = name
        self.in_: (
            str
            | None
        ) = in_
        self.description: (
            str
            | None
        ) = description
        self.required: (
            bool
            | None
        ) = required
        self.deprecated: (
            bool
            | None
        ) = deprecated
        self.allow_empty_value: (
            bool
            | None
        ) = allow_empty_value
        self.style: (
            str
            | None
        ) = style
        self.explode: (
            bool
            | None
        ) = explode
        self.allow_reserved: (
            bool
            | None
        ) = allow_reserved
        self.schema: (
            Reference
            | Schema
            | None
        ) = schema
        self.example: (
            typing.Any
            | None
        ) = example
        self.examples: (
            typing.Mapping[
                str,
                Reference
                | Example
            ]
            | None
        ) = examples
        self.content: (
            typing.Mapping[
                str,
                MediaType
            ]
            | None
        ) = content
        self.type_: (
            str
            | None
        ) = type_
        self.default: (
            typing.Any
            | None
        ) = default
        self.maximum: (
            float
            | int
            | decimal.Decimal
            | None
        ) = maximum
        self.exclusive_maximum: (
            bool
            | None
        ) = exclusive_maximum
        self.minimum: (
            float
            | int
            | decimal.Decimal
            | None
        ) = minimum
        self.exclusive_minimum: (
            bool
            | None
        ) = exclusive_minimum
        self.max_length: (
            int
            | None
        ) = max_length
        self.min_length: (
            int
            | None
        ) = min_length
        self.pattern: (
            str
            | None
        ) = pattern
        self.max_items: (
            int
            | None
        ) = max_items
        self.min_items: (
            int
            | None
        ) = min_items
        self.unique_items: (
            bool
            | None
        ) = unique_items
        self.enum: (
            typing.Sequence[
                sob.abc.MarshallableTypes | None
            ]
            | None
        ) = enum
        self.format_: (
            str
            | None
        ) = format_
        self.collection_format: (
            str
            | None
        ) = collection_format
        self.items: (
            Items
            | None
        ) = items
        self.multiple_of: (
            float
            | int
            | decimal.Decimal
            | None
        ) = multiple_of
        super().__init__(_data)


class Parameters(sob.Dictionary):

    def __init__(
        self,
        items: (
            sob.abc.Dictionary
            | typing.Mapping[
                str,
                Reference
                | Parameter
            ]
            | typing.Iterable[
                tuple[
                    str,
                    Reference
                    | Parameter
                ]
            ]
            | sob.abc.Readable
            | str
            | bytes
            | None
        ) = None,
    ) -> None:
        super().__init__(items)


class PathItem(sob.Object):
    """
    [OpenAPI 3 Path Item Object
    ](https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.1.1.md#
    path-item-object)

    Attributes:
        summary:
        description:
        get:
        put:
        post:
        delete:
        options:
        head:
        patch:
        trace:
        servers:
        parameters:
    """

    __slots__: tuple[str, ...] = (
        "summary",
        "description",
        "get",
        "put",
        "post",
        "delete",
        "options",
        "head",
        "patch",
        "trace",
        "servers",
        "parameters",
    )

    def __init__(
        self,
        _data: (
            sob.abc.Dictionary
            | typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ]
            | typing.Iterable[
                tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ]
            | sob.abc.Readable
            | typing.IO
            | str
            | bytes
            | None
        ) = None,
        summary: (
            str
            | None
        ) = None,
        description: (
            str
            | None
        ) = None,
        get: (
            Operation
            | None
        ) = None,
        put: (
            Operation
            | None
        ) = None,
        post: (
            Operation
            | None
        ) = None,
        delete: (
            Operation
            | None
        ) = None,
        options: (
            Operation
            | None
        ) = None,
        head: (
            Operation
            | None
        ) = None,
        patch: (
            Operation
            | None
        ) = None,
        trace: (
            Operation
            | None
        ) = None,
        servers: (
            typing.Sequence[
                Server
            ]
            | None
        ) = None,
        parameters: (
            typing.Sequence[
                Reference
            | Parameter
            ]
            | None
        ) = None
    ) -> None:
        self.summary: (
            str
            | None
        ) = summary
        self.description: (
            str
            | None
        ) = description
        self.get: (
            Operation
            | None
        ) = get
        self.put: (
            Operation
            | None
        ) = put
        self.post: (
            Operation
            | None
        ) = post
        self.delete: (
            Operation
            | None
        ) = delete
        self.options: (
            Operation
            | None
        ) = options
        self.head: (
            Operation
            | None
        ) = head
        self.patch: (
            Operation
            | None
        ) = patch
        self.trace: (
            Operation
            | None
        ) = trace
        self.servers: (
            typing.Sequence[
                Server
            ]
            | None
        ) = servers
        self.parameters: (
            typing.Sequence[
                Reference
            | Parameter
            ]
            | None
        ) = parameters
        super().__init__(_data)


class Paths(sob.Dictionary):

    def __init__(
        self,
        items: (
            sob.abc.Dictionary
            | typing.Mapping[
                str,
                PathItem
            ]
            | typing.Iterable[
                tuple[
                    str,
                    PathItem
                ]
            ]
            | sob.abc.Readable
            | str
            | bytes
            | None
        ) = None,
    ) -> None:
        super().__init__(items)


class Properties(sob.Dictionary):

    def __init__(
        self,
        items: (
            sob.abc.Dictionary
            | typing.Mapping[
                str,
                Reference
                | Schema
            ]
            | typing.Iterable[
                tuple[
                    str,
                    Reference
                    | Schema
                ]
            ]
            | sob.abc.Readable
            | str
            | bytes
            | None
        ) = None,
    ) -> None:
        super().__init__(items)


class Reference(sob.Object):
    """
    [OpenAPI 3 Reference Object
    ](https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.1.1.md#
    reference-object)

    Attributes:
        ref:
        summary:
        description:
    """

    __slots__: tuple[str, ...] = (
        "ref",
        "summary",
        "description",
    )

    def __init__(
        self,
        _data: (
            sob.abc.Dictionary
            | typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ]
            | typing.Iterable[
                tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ]
            | sob.abc.Readable
            | typing.IO
            | str
            | bytes
            | None
        ) = None,
        ref: (
            str
            | None
        ) = None,
        summary: (
            str
            | None
        ) = None,
        description: (
            str
            | None
        ) = None
    ) -> None:
        self.ref: (
            str
            | None
        ) = ref
        self.summary: (
            str
            | None
        ) = summary
        self.description: (
            str
            | None
        ) = description
        super().__init__(_data)


class RequestBodies(sob.Dictionary):

    def __init__(
        self,
        items: (
            sob.abc.Dictionary
            | typing.Mapping[
                str,
                Reference
                | RequestBody
            ]
            | typing.Iterable[
                tuple[
                    str,
                    Reference
                    | RequestBody
                ]
            ]
            | sob.abc.Readable
            | str
            | bytes
            | None
        ) = None,
    ) -> None:
        super().__init__(items)


class RequestBody(sob.Object):
    """
    [OpenAPI 3 Request Body Object
    ](https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.1.1.md#
    request-body-object)

    Attributes:
        description:
        content:
        required:
    """

    __slots__: tuple[str, ...] = (
        "description",
        "content",
        "required",
    )

    def __init__(
        self,
        _data: (
            sob.abc.Dictionary
            | typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ]
            | typing.Iterable[
                tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ]
            | sob.abc.Readable
            | typing.IO
            | str
            | bytes
            | None
        ) = None,
        description: (
            str
            | None
        ) = None,
        content: (
            typing.Mapping[
                str,
                MediaType
            ]
            | None
        ) = None,
        required: (
            bool
            | None
        ) = None
    ) -> None:
        self.description: (
            str
            | None
        ) = description
        self.content: (
            typing.Mapping[
                str,
                MediaType
            ]
            | None
        ) = content
        self.required: (
            bool
            | None
        ) = required
        super().__init__(_data)


class Response(sob.Object):
    """
    [OpenAPI 3 Response Object
    ](https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.1.1.md#
    response-object)

    Attributes:
        description: A short description of the response. [CommonMark
            syntax](http://spec.commonmark.org/) may be used for rich text
            representation.
        headers: Maps a header name to its
            definition (mappings are case-insensitive).
        content: A mapping of media value_types to
            `MediaType` instances describing potential payloads.
        links: A map of operations links that can be
            followed from the response.
        examples: Examples responses
        schema: (OpenAPI 2x only)
    """

    __slots__: tuple[str, ...] = (
        "description",
        "schema",
        "headers",
        "examples",
        "content",
        "links",
    )

    def __init__(
        self,
        _data: (
            sob.abc.Dictionary
            | typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ]
            | typing.Iterable[
                tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ]
            | sob.abc.Readable
            | typing.IO
            | str
            | bytes
            | None
        ) = None,
        description: (
            str
            | None
        ) = None,
        schema: (
            Reference
            | Schema
            | None
        ) = None,
        headers: (
            typing.Mapping[
                str,
                Reference
                | Header
            ]
            | None
        ) = None,
        examples: (
            typing.Mapping[
                str,
                sob.abc.MarshallableTypes | None
            ]
            | None
        ) = None,
        content: (
            typing.Mapping[
                str,
                Reference
                | MediaType
            ]
            | None
        ) = None,
        links: (
            typing.Mapping[
                str,
                Reference
                | LinkObject
            ]
            | None
        ) = None
    ) -> None:
        self.description: (
            str
            | None
        ) = description
        self.schema: (
            Reference
            | Schema
            | None
        ) = schema
        self.headers: (
            typing.Mapping[
                str,
                Reference
                | Header
            ]
            | None
        ) = headers
        self.examples: (
            typing.Mapping[
                str,
                sob.abc.MarshallableTypes | None
            ]
            | None
        ) = examples
        self.content: (
            typing.Mapping[
                str,
                Reference
                | MediaType
            ]
            | None
        ) = content
        self.links: (
            typing.Mapping[
                str,
                Reference
                | LinkObject
            ]
            | None
        ) = links
        super().__init__(_data)


class Responses(sob.Dictionary):

    def __init__(
        self,
        items: (
            sob.abc.Dictionary
            | typing.Mapping[
                str,
                Reference
                | Response
                | Response
            ]
            | typing.Iterable[
                tuple[
                    str,
                    Reference
                    | Response
                    | Response
                ]
            ]
            | sob.abc.Readable
            | str
            | bytes
            | None
        ) = None,
    ) -> None:
        super().__init__(items)


class Schema(sob.Object):
    """
    [Open API 3 Schema Object
    ](https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.1.1.md#
    schema-object)
    | [JSON Schema](http://json-schema.org)

    Attributes:
        title:
        description:
        multiple_of: The numeric value this schema describes
            should be divisible by this number.
        maximum: The number this schema describes should be less
            than or equal to this value, or less than
            this value, depending on the value of `exclusive_maximum`.
        exclusive_maximum: If `True`, the numeric instance described
            by this schema must be *less than*
            `maximum`. If `False`, the numeric instance described by this
            schema can be less than or *equal to* `maximum`.
        minimum: The number this schema describes should be
            greater than or equal to this value, or greater
            than this value, depending on the value of `exclusive_minimum`.
        exclusive_minimum: If `True`, the numeric instance described
            by this schema must be *greater than* `minimum`. If `False`, the
            numeric instance described by this schema can be greater than or
            *equal to* `minimum`.
        max_length: The number of characters in the string instance
            described by this schema must be less than,
            or equal to, the value of this property.
        min_length: The number of characters in the string instance
            described by this schema must be greater
            than, or equal to, the value of this property.
        pattern: The string instance described by this schema should
            match this regular expression (ECMA 262).
        items:
            -   If `items` is a sub-schema--each item in the array instance
                described by this schema should be valid as described by this
                sub-schema.
            -   If `items` is a sequence of sub-schemas, the array instance
                described by this schema should be equal in length to this
                sequence, and each value should be valid as described by the
                sub-schema at the corresponding index within this sequence of
                sub-schemas.
        max_items: The array instance described by this schema should
            contain no more than this number of items.
        min_items: The array instance described by this schema should
            contain at least this number of items.
        unique_items: The array instance described by this schema
            should contain only unique items.
        max_properties:
        min_properties:
        properties: Any properties of the object
            instance described by this schema which correspond to a name in
            this mapping should be valid as described by the sub-schema
            corresponding to that name.
        additional_properties:
            -   If `additional_properties` is `True`—properties may be
                present in the object described by this schema with names which
                do not match those in `properties`.
            -   If `additional_properties` is `False`—all properties
                present in the object described by this schema must correspond
                to a property matched in `properties`.
            -   If `additional_properties` is a schema object,
                all properties not described in `properties` must have
                values matching the `additional_properties` schema.
        enum: The value/instance described by this schema should be
            among those in this sequence.
        type_: See [OpenAPI 3 Data Types
            (https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.
            1.1.md#data-types)],
            [Swagger - OpenAPI 3 Data Types
            ](https://swagger.io/docs/specification/v3_0/data-models/data-
            types/)
            and [OpenAPI 2 Data Types
            ](https://github.com/OAI/OpenAPI-Specification/blob/main/versions/
            2.0.md#data-types)

            - "boolean"
            - "object"
            - "array"
            - "number"
            - "string"
            - "integer"
            - "file"

        format_: See [Open API 3 Data Type Format
            ](https://github.com/OAI/OpenAPI-Specification/blob/main/versions/
            3.1.1.md#data-type-format)

            - "date-time":
                A date and time in the format YYYY-MM-DDThh:mm:ss.sTZD
                (eg 1997-07-16T19:20:30.45+01:00),
                YYYY-MM-DDThh:mm:ssTZD (eg 1997-07-16T19:20:30+01:00), or
                YYYY-MM-DDThh:mmTZD (eg 1997-07-16T19:20+01:00).
            - "email"
            - "hostname"
            - "ipv4"
            - "ipv6"
            - "uri"
            - "uriref": A URI or a relative reference.

        all_of: The value/instance described by the schema should
            *also* be valid as
            described by all sub-schemas in this sequence.
        any_of: The value/instance described by the schema should
            *also* be valid as
            described in at least one of the sub-schemas in this sequence.
        one_of: The value/instance described by the schema should
            *also* be valid as
            described in one (but *only* one) of the sub-schemas in this
            sequence.
        is_not: The value/instance described by this schema should *
            not* be valid as described by this
            sub-schema.
        definitions:Schema}): A dictionary of sub-schemas, stored for
            the purpose of referencing these sub-schemas elsewhere in the
            schema.
        required: A list of attributes which must be present on the
            object instance described by this schema.
        default: The value presumed if the value/instance described by
            this schema is absent.
        content_media_type:
        content_encoding:
        examples: A list of valid examples of this object
        nullable: If `True`, the value/instance described by this
            schema may be a null value (`None`). (Specific to OpenAPI, not part
            of the [JSON Schema](http://json-schema.org))
        discriminator: Adds support for polymorphism. (Specific to OpenAPI,
            not part of the [JSON Schema](http://json-schema.org))
        read_only: If `True`, the property described may be returned
            as part of a response, but should not be part of a request
            (Specific to OpenAPI, not part of the
            [JSON Schema](http://json-schema.org)).
        write_only: If `True`, the property described may be sent as
            part of a request, but should not be returned as part of a response
            (Specific to OpenAPI, not part of the
            [JSON Schema](http://json-schema.org)).
        xml: Provides additional information describing XML
            representation of the property described by this schema
            (Specific to OpenAPI, not part of the
            [JSON Schema](http://json-schema.org)).
        external_docs: (Specific to OpenAPI, not part of the
            [JSON Schema](http://json-schema.org))
        example: (Specific to OpenAPI, not part of the
            [JSON Schema](http://json-schema.org))
        definitions: (Specific to OpenAPI, not part of the
            [JSON Schema](http://json-schema.org))
        depracated: If `True`, the property or instance described by
            this schema should be phased out, as if will no longer be supported
            in future versions (Specific to OpenAPI, not part of the
            [JSON Schema](http://json-schema.org)).
    """

    __slots__: tuple[str, ...] = (
        "title",
        "description",
        "multiple_of",
        "maximum",
        "exclusive_maximum",
        "minimum",
        "exclusive_minimum",
        "max_length",
        "min_length",
        "pattern",
        "max_items",
        "min_items",
        "unique_items",
        "items",
        "max_properties",
        "min_properties",
        "properties",
        "additional_properties",
        "enum",
        "type_",
        "format_",
        "required",
        "all_of",
        "any_of",
        "one_of",
        "is_not",
        "definitions",
        "default",
        "discriminator",
        "read_only",
        "write_only",
        "xml",
        "external_docs",
        "example",
        "deprecated",
        "links",
        "nullable",
        "content_encoding",
        "content_media_type",
        "examples",
    )

    def __init__(
        self,
        _data: (
            sob.abc.Dictionary
            | typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ]
            | typing.Iterable[
                tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ]
            | sob.abc.Readable
            | typing.IO
            | str
            | bytes
            | None
        ) = None,
        title: (
            str
            | None
        ) = None,
        description: (
            str
            | None
        ) = None,
        multiple_of: (
            float
            | int
            | decimal.Decimal
            | None
        ) = None,
        maximum: (
            float
            | int
            | decimal.Decimal
            | None
        ) = None,
        exclusive_maximum: (
            bool
            | None
        ) = None,
        minimum: (
            float
            | int
            | decimal.Decimal
            | None
        ) = None,
        exclusive_minimum: (
            bool
            | None
        ) = None,
        max_length: (
            int
            | None
        ) = None,
        min_length: (
            int
            | None
        ) = None,
        pattern: (
            str
            | None
        ) = None,
        max_items: (
            int
            | None
        ) = None,
        min_items: (
            int
            | None
        ) = None,
        unique_items: (
            bool
            | None
        ) = None,
        items: (
            Reference
            | Schema
            | typing.Sequence[
                Reference
            | Schema
            ]
            | None
        ) = None,
        max_properties: (
            int
            | None
        ) = None,
        min_properties: (
            int
            | None
        ) = None,
        properties: (
            Properties
            | None
        ) = None,
        additional_properties: (
            Reference
            | Schema
            | bool
            | None
        ) = None,
        enum: (
            typing.Sequence[
                sob.abc.MarshallableTypes | None
            ]
            | None
        ) = None,
        type_: (
            str
            | None
        ) = None,
        format_: (
            str
            | None
        ) = None,
        required: (
            typing.Sequence[
                str
            ]
            | None
        ) = None,
        all_of: (
            typing.Sequence[
                Reference
            | Schema
            ]
            | None
        ) = None,
        any_of: (
            typing.Sequence[
                Reference
            | Schema
            ]
            | None
        ) = None,
        one_of: (
            typing.Sequence[
                Reference
            | Schema
            ]
            | None
        ) = None,
        is_not: (
            Reference
            | Schema
            | None
        ) = None,
        definitions: (
            typing.Any
            | None
        ) = None,
        default: (
            typing.Any
            | None
        ) = None,
        discriminator: (
            Discriminator
            | str
            | None
        ) = None,
        read_only: (
            bool
            | None
        ) = None,
        write_only: (
            bool
            | None
        ) = None,
        xml: (
            XML
            | None
        ) = None,
        external_docs: (
            ExternalDocumentation
            | None
        ) = None,
        example: (
            typing.Any
            | None
        ) = None,
        deprecated: (
            bool
            | None
        ) = None,
        links: (
            typing.Sequence[
                Link
            ]
            | None
        ) = None,
        nullable: (
            bool
            | None
        ) = None,
        content_encoding: (
            str
            | None
        ) = None,
        content_media_type: (
            str
            | None
        ) = None,
        examples: (
            typing.Sequence[
                sob.abc.MarshallableTypes | None
            ]
            | None
        ) = None
    ) -> None:
        self.title: (
            str
            | None
        ) = title
        self.description: (
            str
            | None
        ) = description
        self.multiple_of: (
            float
            | int
            | decimal.Decimal
            | None
        ) = multiple_of
        self.maximum: (
            float
            | int
            | decimal.Decimal
            | None
        ) = maximum
        self.exclusive_maximum: (
            bool
            | None
        ) = exclusive_maximum
        self.minimum: (
            float
            | int
            | decimal.Decimal
            | None
        ) = minimum
        self.exclusive_minimum: (
            bool
            | None
        ) = exclusive_minimum
        self.max_length: (
            int
            | None
        ) = max_length
        self.min_length: (
            int
            | None
        ) = min_length
        self.pattern: (
            str
            | None
        ) = pattern
        self.max_items: (
            int
            | None
        ) = max_items
        self.min_items: (
            int
            | None
        ) = min_items
        self.unique_items: (
            bool
            | None
        ) = unique_items
        self.items: (
            Reference
            | Schema
            | typing.Sequence[
                Reference
            | Schema
            ]
            | None
        ) = items
        self.max_properties: (
            int
            | None
        ) = max_properties
        self.min_properties: (
            int
            | None
        ) = min_properties
        self.properties: (
            Properties
            | None
        ) = properties
        self.additional_properties: (
            Reference
            | Schema
            | bool
            | None
        ) = additional_properties
        self.enum: (
            typing.Sequence[
                sob.abc.MarshallableTypes | None
            ]
            | None
        ) = enum
        self.type_: (
            str
            | None
        ) = type_
        self.format_: (
            str
            | None
        ) = format_
        self.required: (
            typing.Sequence[
                str
            ]
            | None
        ) = required
        self.all_of: (
            typing.Sequence[
                Reference
            | Schema
            ]
            | None
        ) = all_of
        self.any_of: (
            typing.Sequence[
                Reference
            | Schema
            ]
            | None
        ) = any_of
        self.one_of: (
            typing.Sequence[
                Reference
            | Schema
            ]
            | None
        ) = one_of
        self.is_not: (
            Reference
            | Schema
            | None
        ) = is_not
        self.definitions: (
            typing.Any
            | None
        ) = definitions
        self.default: (
            typing.Any
            | None
        ) = default
        self.discriminator: (
            Discriminator
            | str
            | None
        ) = discriminator
        self.read_only: (
            bool
            | None
        ) = read_only
        self.write_only: (
            bool
            | None
        ) = write_only
        self.xml: (
            XML
            | None
        ) = xml
        self.external_docs: (
            ExternalDocumentation
            | None
        ) = external_docs
        self.example: (
            typing.Any
            | None
        ) = example
        self.deprecated: (
            bool
            | None
        ) = deprecated
        self.links: (
            typing.Sequence[
                Link
            ]
            | None
        ) = links
        self.nullable: (
            bool
            | None
        ) = nullable
        self.content_encoding: (
            str
            | None
        ) = content_encoding
        self.content_media_type: (
            str
            | None
        ) = content_media_type
        self.examples: (
            typing.Sequence[
                sob.abc.MarshallableTypes | None
            ]
            | None
        ) = examples
        super().__init__(_data)


class Schemas(sob.Dictionary):

    def __init__(
        self,
        items: (
            sob.abc.Dictionary
            | typing.Mapping[
                str,
                Reference
                | Schema
            ]
            | typing.Iterable[
                tuple[
                    str,
                    Reference
                    | Schema
                ]
            ]
            | sob.abc.Readable
            | str
            | bytes
            | None
        ) = None,
    ) -> None:
        super().__init__(items)


class SecurityRequirement(sob.Dictionary):

    def __init__(
        self,
        items: (
            sob.abc.Dictionary
            | typing.Mapping[
                str,
                typing.Sequence[
                    str
                ]
            ]
            | typing.Iterable[
                tuple[
                    str,
                    typing.Sequence[
                        str
                    ]
                ]
            ]
            | sob.abc.Readable
            | str
            | bytes
            | None
        ) = None,
    ) -> None:
        super().__init__(items)


class SecurityScheme(sob.Object):
    """
    [OpenAPI 3 Security Scheme Object]
    ](https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.1.1.md#
    security-scheme-object)
    | [OpenAPI 2 Security Scheme Object
    ](https://github.com/OAI/OpenAPI-Specification/blob/main/versions/2.0.md#
    security-scheme-object)

    Attributes:
        type_: OpenAPI 3x: "apiKey", "http", "mutualTLS", "oauth2",
            or "openIdConnect". OpenAPI 2x: "basic", "apiKey" or "oauth2".
        description:
        name:
        in_:
        scheme:
        bearer_format:
        flows:
        open_id_connect_url:
        scopes:
        flow: "implicit", "password", "application" or "accessCode"
        authorization_url:
        token_url:
    """

    __slots__: tuple[str, ...] = (
        "type_",
        "description",
        "name",
        "in_",
        "scheme",
        "bearer_format",
        "flows",
        "open_id_connect_url",
        "flow",
        "authorization_url",
        "token_url",
        "scopes",
    )

    def __init__(
        self,
        _data: (
            sob.abc.Dictionary
            | typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ]
            | typing.Iterable[
                tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ]
            | sob.abc.Readable
            | typing.IO
            | str
            | bytes
            | None
        ) = None,
        type_: (
            str
            | None
        ) = None,
        description: (
            str
            | None
        ) = None,
        name: (
            str
            | None
        ) = None,
        in_: (
            str
            | None
        ) = None,
        scheme: (
            str
            | None
        ) = None,
        bearer_format: (
            str
            | None
        ) = None,
        flows: (
            OAuthFlows
            | None
        ) = None,
        open_id_connect_url: (
            str
            | None
        ) = None,
        flow: (
            str
            | None
        ) = None,
        authorization_url: (
            str
            | None
        ) = None,
        token_url: (
            str
            | None
        ) = None,
        scopes: (
            typing.Mapping[
                str,
                str
            ]
            | None
        ) = None
    ) -> None:
        self.type_: (
            str
            | None
        ) = type_
        self.description: (
            str
            | None
        ) = description
        self.name: (
            str
            | None
        ) = name
        self.in_: (
            str
            | None
        ) = in_
        self.scheme: (
            str
            | None
        ) = scheme
        self.bearer_format: (
            str
            | None
        ) = bearer_format
        self.flows: (
            OAuthFlows
            | None
        ) = flows
        self.open_id_connect_url: (
            str
            | None
        ) = open_id_connect_url
        self.flow: (
            str
            | None
        ) = flow
        self.authorization_url: (
            str
            | None
        ) = authorization_url
        self.token_url: (
            str
            | None
        ) = token_url
        self.scopes: (
            typing.Mapping[
                str,
                str
            ]
            | None
        ) = scopes
        super().__init__(_data)


class SecuritySchemes(sob.Dictionary):

    def __init__(
        self,
        items: (
            sob.abc.Dictionary
            | typing.Mapping[
                str,
                Reference
                | SecurityScheme
            ]
            | typing.Iterable[
                tuple[
                    str,
                    Reference
                    | SecurityScheme
                ]
            ]
            | sob.abc.Readable
            | str
            | bytes
            | None
        ) = None,
    ) -> None:
        super().__init__(items)


class Server(sob.Object):
    """
    [OpenAPI 3 Server Object
    ](https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.1.1.md#
    server-object)

    Attributes:
        url:
        description:
        variables:
    """

    __slots__: tuple[str, ...] = (
        "url",
        "description",
        "variables",
    )

    def __init__(
        self,
        _data: (
            sob.abc.Dictionary
            | typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ]
            | typing.Iterable[
                tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ]
            | sob.abc.Readable
            | typing.IO
            | str
            | bytes
            | None
        ) = None,
        url: (
            str
            | None
        ) = None,
        description: (
            str
            | None
        ) = None,
        variables: (
            typing.Mapping[
                str,
                ServerVariable
            ]
            | None
        ) = None
    ) -> None:
        self.url: (
            str
            | None
        ) = url
        self.description: (
            str
            | None
        ) = description
        self.variables: (
            typing.Mapping[
                str,
                ServerVariable
            ]
            | None
        ) = variables
        super().__init__(_data)


class ServerVariable(sob.Object):
    """
    [OpenAPI 3 Server Variable Object
    ](https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.1.1.md#
    server-variable-object)

    Attributes:
        enum:
        default:
        description:
    """

    __slots__: tuple[str, ...] = (
        "enum",
        "default",
        "description",
    )

    def __init__(
        self,
        _data: (
            sob.abc.Dictionary
            | typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ]
            | typing.Iterable[
                tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ]
            | sob.abc.Readable
            | typing.IO
            | str
            | bytes
            | None
        ) = None,
        enum: (
            typing.Sequence[
                str
            ]
            | None
        ) = None,
        default: (
            str
            | None
        ) = None,
        description: (
            str
            | None
        ) = None
    ) -> None:
        self.enum: (
            typing.Sequence[
                str
            ]
            | None
        ) = enum
        self.default: (
            str
            | None
        ) = default
        self.description: (
            str
            | None
        ) = description
        super().__init__(_data)


class Tag(sob.Object):
    """
    [OpenAPI 3 Tag Object
    ](https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.1.1.md#
    tag-object)

    Attributes:
        name:
        description:
        external_docs:
    """

    __slots__: tuple[str, ...] = (
        "name",
        "description",
        "external_docs",
    )

    def __init__(
        self,
        _data: (
            sob.abc.Dictionary
            | typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ]
            | typing.Iterable[
                tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ]
            | sob.abc.Readable
            | typing.IO
            | str
            | bytes
            | None
        ) = None,
        name: (
            str
            | None
        ) = None,
        description: (
            str
            | None
        ) = None,
        external_docs: (
            ExternalDocumentation
            | None
        ) = None
    ) -> None:
        self.name: (
            str
            | None
        ) = name
        self.description: (
            str
            | None
        ) = description
        self.external_docs: (
            ExternalDocumentation
            | None
        ) = external_docs
        super().__init__(_data)


class XML(sob.Object):
    """
    [OpenAPI 3 XML Object
    ](https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.1.1.md#
    xml-object)

    Attributes:
        name: The element name.
        name_space: The *absolute* URI of a namespace.
        prefix: The prefix to be used with the name to reference the
            name-space.
        attribute: If `True`, the property described is an attribute
            rather than a sub-element.
        wrapped: If `True`, an array instance described by the schema
            will be wrapped by a tag (named according to the parent element's
            property, while `name` refers to the child element name).
    """

    __slots__: tuple[str, ...] = (
        "name",
        "name_space",
        "prefix",
        "attribute",
        "wrapped",
    )

    def __init__(
        self,
        _data: (
            sob.abc.Dictionary
            | typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ]
            | typing.Iterable[
                tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ]
            | sob.abc.Readable
            | typing.IO
            | str
            | bytes
            | None
        ) = None,
        name: (
            str
            | None
        ) = None,
        name_space: (
            str
            | None
        ) = None,
        prefix: (
            str
            | None
        ) = None,
        attribute: (
            bool
            | None
        ) = None,
        wrapped: (
            bool
            | None
        ) = None
    ) -> None:
        self.name: (
            str
            | None
        ) = name
        self.name_space: (
            str
            | None
        ) = name_space
        self.prefix: (
            str
            | None
        ) = prefix
        self.attribute: (
            bool
            | None
        ) = attribute
        self.wrapped: (
            bool
            | None
        ) = wrapped
        super().__init__(_data)


sob.get_writable_dictionary_meta(  # type: ignore
    Callback
).value_types = sob.MutableTypes([
    PathItem
])
sob.get_writable_dictionary_meta(  # type: ignore
    Callbacks
).value_types = sob.MutableTypes([
    Reference,
    Callback
])
sob.get_writable_object_meta(  # type: ignore
    Components
).properties = sob.Properties([
    (
        'schemas',
        sob.Property(
            types=sob.MutableTypes([
                Schemas
            ])
        )
    ),
    (
        'responses',
        sob.Property(
            types=sob.MutableTypes([
                Responses
            ])
        )
    ),
    (
        'parameters',
        sob.Property(
            types=sob.MutableTypes([
                Parameters
            ])
        )
    ),
    (
        'examples',
        sob.Property(
            types=sob.MutableTypes([
                Examples
            ])
        )
    ),
    (
        'request_bodies',
        sob.Property(
            name="requestBodies",
            types=sob.MutableTypes([
                RequestBodies
            ])
        )
    ),
    (
        'headers',
        sob.Property(
            types=sob.MutableTypes([
                Headers
            ])
        )
    ),
    (
        'security_schemes',
        sob.Property(
            name="securitySchemes",
            types=sob.MutableTypes([
                SecuritySchemes
            ])
        )
    ),
    (
        'links',
        sob.Property(
            types=sob.MutableTypes([
                Links
            ])
        )
    ),
    (
        'callbacks',
        sob.Property(
            types=sob.MutableTypes([
                Callbacks
            ])
        )
    )
])
sob.get_writable_object_meta(  # type: ignore
    Contact
).properties = sob.Properties([
    ('name', sob.StringProperty()),
    ('url', sob.StringProperty()),
    ('email', sob.StringProperty())
])
sob.get_writable_dictionary_meta(  # type: ignore
    Definitions
).value_types = sob.MutableTypes([
    Schema
])
sob.get_writable_object_meta(  # type: ignore
    Discriminator
).properties = sob.Properties([
    (
        'property_name',
        sob.StringProperty(
            name="propertyName",
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'mapping',
        sob.DictionaryProperty(
            value_types=sob.MutableTypes([
                str
            ]),
            versions=(
                'openapi>=3.0',
            )
        )
    )
])
sob.get_writable_object_meta(  # type: ignore
    Encoding
).properties = sob.Properties([
    (
        'content_type',
        sob.StringProperty(
            name="contentType"
        )
    ),
    (
        'headers',
        sob.DictionaryProperty(
            value_types=sob.MutableTypes([
                Reference,
                Header
            ])
        )
    ),
    ('style', sob.StringProperty()),
    ('explode', sob.BooleanProperty()),
    (
        'allow_reserved',
        sob.BooleanProperty(
            name="allowReserved"
        )
    )
])
sob.get_writable_object_meta(  # type: ignore
    Example
).properties = sob.Properties([
    (
        'summary',
        sob.StringProperty(
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'description',
        sob.StringProperty(
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'value',
        sob.Property(
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'external_value',
        sob.StringProperty(
            name="externalValue",
            versions=(
                'openapi>=3.0',
            )
        )
    )
])
sob.get_writable_dictionary_meta(  # type: ignore
    Examples
).value_types = sob.MutableTypes([
    Reference,
    Example
])
sob.get_writable_object_meta(  # type: ignore
    ExternalDocumentation
).properties = sob.Properties([
    ('description', sob.StringProperty()),
    (
        'url',
        sob.StringProperty(
            required=True
        )
    )
])
sob.get_writable_object_meta(  # type: ignore
    Header
).properties = sob.Properties([
    ('description', sob.StringProperty()),
    (
        'required',
        sob.BooleanProperty(
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'deprecated',
        sob.BooleanProperty(
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'allow_empty_value',
        sob.BooleanProperty(
            name="allowEmptyValue",
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'style',
        sob.StringProperty(
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'explode',
        sob.BooleanProperty(
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'allow_reserved',
        sob.BooleanProperty(
            name="allowReserved",
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'schema',
        sob.Property(
            types=sob.MutableTypes([
                Reference,
                Schema
            ]),
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'example',
        sob.Property(
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'examples',
        sob.DictionaryProperty(
            value_types=sob.MutableTypes([
                Reference,
                Example
            ]),
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'content',
        sob.DictionaryProperty(
            value_types=sob.MutableTypes([
                MediaType
            ]),
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'type_',
        sob.EnumeratedProperty(
            name="type",
            types=sob.Types([
                str
            ]),
            values={
                "array",
                "boolean",
                "integer",
                "number",
                "string"
            },
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'default',
        sob.Property(
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'maximum',
        sob.NumberProperty(
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'exclusive_maximum',
        sob.BooleanProperty(
            name="exclusiveMaximum",
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'minimum',
        sob.NumberProperty(
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'exclusive_minimum',
        sob.BooleanProperty(
            name="exclusiveMinimum",
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'max_length',
        sob.IntegerProperty(
            name="maxLength",
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'min_length',
        sob.IntegerProperty(
            name="minLength",
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'pattern',
        sob.StringProperty(
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'max_items',
        sob.IntegerProperty(
            name="maxItems",
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'min_items',
        sob.IntegerProperty(
            name="minItems",
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'unique_items',
        sob.BooleanProperty(
            name="uniqueItems",
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'enum',
        sob.ArrayProperty(
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'format_',
        sob.StringProperty(
            name="format",
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'collection_format',
        sob.EnumeratedProperty(
            name="collectionFormat",
            types=sob.Types([
                str
            ]),
            values={
                "csv",
                "multi",
                "pipes",
                "ssv",
                "tsv"
            },
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'items',
        sob.Property(
            types=sob.MutableTypes([
                Items
            ]),
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'multiple_of',
        sob.NumberProperty(
            name="multipleOf",
            versions=(
                'openapi<3.0',
            )
        )
    )
])
sob.get_writable_dictionary_meta(  # type: ignore
    Headers
).value_types = sob.MutableTypes([
    Reference,
    Header
])
sob.get_writable_object_meta(  # type: ignore
    Info
).properties = sob.Properties([
    (
        'title',
        sob.StringProperty(
            required=True
        )
    ),
    ('description', sob.StringProperty()),
    (
        'terms_of_service',
        sob.StringProperty(
            name="termsOfService"
        )
    ),
    (
        'contact',
        sob.Property(
            types=sob.MutableTypes([
                Contact
            ])
        )
    ),
    (
        'license_',
        sob.Property(
            name="license",
            types=sob.MutableTypes([
                License
            ])
        )
    ),
    (
        'version',
        sob.StringProperty(
            required=True
        )
    )
])
sob.get_writable_object_meta(  # type: ignore
    Items
).properties = sob.Properties([
    (
        'type_',
        sob.EnumeratedProperty(
            name="type",
            types=sob.Types([
                str
            ]),
            values={
                "array",
                "boolean",
                "file",
                "integer",
                "number",
                "object",
                "string"
            },
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'format_',
        sob.StringProperty(
            name="format",
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'items',
        sob.Property(
            types=sob.MutableTypes([
                Items
            ]),
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'collection_format',
        sob.EnumeratedProperty(
            name="collectionFormat",
            types=sob.Types([
                str
            ]),
            values={
                "csv",
                "pipes",
                "ssv",
                "tsv"
            },
            versions=(
                'openapi<3.0',
            )
        )
    ),
    ('default', sob.Property()),
    (
        'maximum',
        sob.NumberProperty(
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'exclusive_maximum',
        sob.BooleanProperty(
            name="exclusiveMaximum",
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'minimum',
        sob.NumberProperty(
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'exclusive_minimum',
        sob.BooleanProperty(
            name="exclusiveMinimum",
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'max_length',
        sob.IntegerProperty(
            name="maxLength",
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'min_length',
        sob.IntegerProperty(
            name="minLength",
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'pattern',
        sob.StringProperty(
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'max_items',
        sob.IntegerProperty(
            name="maxItems",
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'min_items',
        sob.IntegerProperty(
            name="minItems",
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'unique_items',
        sob.BooleanProperty(
            name="uniqueItems",
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'enum',
        sob.ArrayProperty(
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'multiple_of',
        sob.NumberProperty(
            name="multipleOf",
            versions=(
                'openapi<3.0',
            )
        )
    )
])
sob.get_writable_object_meta(  # type: ignore
    License
).properties = sob.Properties([
    (
        'name',
        sob.StringProperty(
            required=True
        )
    ),
    ('url', sob.StringProperty())
])
sob.get_writable_object_meta(  # type: ignore
    Link
).properties = sob.Properties([
    ('rel', sob.StringProperty()),
    ('href', sob.StringProperty())
])
sob.get_writable_object_meta(  # type: ignore
    LinkObject
).properties = sob.Properties([
    (
        'operation_ref',
        sob.StringProperty(
            name="operationRef",
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'operation_id',
        sob.StringProperty(
            name="operationId",
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'parameters',
        sob.DictionaryProperty(
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'request_body',
        sob.Property(
            name="requestBody",
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'description',
        sob.StringProperty(
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'server',
        sob.Property(
            types=sob.MutableTypes([
                Server
            ]),
            versions=(
                'openapi>=3.0',
            )
        )
    )
])
sob.get_writable_dictionary_meta(  # type: ignore
    Links
).value_types = sob.MutableTypes([
    Reference,
    LinkObject
])
sob.get_writable_object_meta(  # type: ignore
    MediaType
).properties = sob.Properties([
    (
        'schema',
        sob.Property(
            types=sob.MutableTypes([
                Reference,
                Schema
            ]),
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'example',
        sob.Property(
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'examples',
        sob.DictionaryProperty(
            value_types=sob.MutableTypes([
                Reference,
                Example
            ]),
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'encoding',
        sob.DictionaryProperty(
            value_types=sob.MutableTypes([
                Reference,
                Encoding
            ]),
            versions=(
                'openapi>=3.0',
            )
        )
    )
])
sob.get_writable_object_meta(  # type: ignore
    OAuthFlow
).properties = sob.Properties([
    (
        'authorization_url',
        sob.StringProperty(
            name="authorizationUrl"
        )
    ),
    (
        'token_url',
        sob.StringProperty(
            name="tokenUrl"
        )
    ),
    (
        'refresh_url',
        sob.StringProperty(
            name="refreshUrl"
        )
    ),
    (
        'scopes',
        sob.DictionaryProperty(
            value_types=sob.MutableTypes([
                str
            ])
        )
    )
])
sob.get_writable_object_meta(  # type: ignore
    OAuthFlows
).properties = sob.Properties([
    (
        'implicit',
        sob.Property(
            types=sob.MutableTypes([
                OAuthFlow
            ]),
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'password',
        sob.Property(
            types=sob.MutableTypes([
                OAuthFlow
            ]),
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'client_credentials',
        sob.Property(
            name="clientCredentials",
            types=sob.MutableTypes([
                OAuthFlow
            ]),
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'authorization_code',
        sob.Property(
            name="authorizationCode",
            types=sob.MutableTypes([
                OAuthFlow
            ]),
            versions=(
                'openapi>=3.0',
            )
        )
    )
])
sob.get_writable_object_meta(  # type: ignore
    OpenAPI
).properties = sob.Properties([
    (
        'openapi',
        sob.StringProperty(
            required=True,
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'info',
        sob.Property(
            required=True,
            types=sob.MutableTypes([
                Info
            ])
        )
    ),
    (
        'json_schema_dialect',
        sob.StringProperty(
            name="jsonSchemaDialect",
            versions=(
                'openapi>=3.1',
            )
        )
    ),
    (
        'host',
        sob.StringProperty(
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'servers',
        sob.ArrayProperty(
            item_types=sob.MutableTypes([
                Server
            ]),
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'base_path',
        sob.StringProperty(
            name="basePath",
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'schemes',
        sob.ArrayProperty(
            item_types=sob.MutableTypes([
                str
            ]),
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'tags',
        sob.ArrayProperty(
            item_types=sob.MutableTypes([
                Tag
            ])
        )
    ),
    (
        'paths',
        sob.Property(
            required=True,
            types=sob.MutableTypes([
                Paths
            ])
        )
    ),
    (
        'components',
        sob.Property(
            types=sob.MutableTypes([
                Components
            ]),
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'consumes',
        sob.ArrayProperty(
            item_types=sob.MutableTypes([
                str
            ]),
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'swagger',
        sob.StringProperty(
            required=True,
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'definitions',
        sob.Property(
            types=sob.MutableTypes([
                Definitions
            ]),
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'security_definitions',
        sob.Property(
            name="securityDefinitions",
            types=sob.MutableTypes([
                SecuritySchemes
            ]),
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'produces',
        sob.ArrayProperty(
            item_types=sob.MutableTypes([
                str
            ]),
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'external_docs',
        sob.Property(
            name="externalDocs",
            types=sob.MutableTypes([
                ExternalDocumentation
            ])
        )
    ),
    (
        'parameters',
        sob.DictionaryProperty(
            value_types=sob.MutableTypes([
                Parameter
            ]),
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'responses',
        sob.DictionaryProperty(
            value_types=sob.MutableTypes([
                Response
            ]),
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'security',
        sob.ArrayProperty(
            item_types=sob.MutableTypes([
                SecurityRequirement
            ])
        )
    )
])
sob.get_writable_object_meta(  # type: ignore
    Operation
).properties = sob.Properties([
    (
        'tags',
        sob.ArrayProperty(
            item_types=sob.MutableTypes([
                str
            ])
        )
    ),
    ('summary', sob.StringProperty()),
    ('description', sob.StringProperty()),
    (
        'external_docs',
        sob.Property(
            name="externalDocs",
            types=sob.MutableTypes([
                ExternalDocumentation
            ])
        )
    ),
    (
        'operation_id',
        sob.StringProperty(
            name="operationId"
        )
    ),
    (
        'consumes',
        sob.ArrayProperty(
            item_types=sob.MutableTypes([
                str
            ]),
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'produces',
        sob.ArrayProperty(
            item_types=sob.MutableTypes([
                str
            ]),
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'parameters',
        sob.ArrayProperty(
            item_types=sob.MutableTypes([
                Reference,
                Parameter
            ])
        )
    ),
    (
        'request_body',
        sob.Property(
            name="requestBody",
            types=sob.MutableTypes([
                Reference,
                RequestBody
            ]),
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'responses',
        sob.Property(
            required=True,
            types=sob.MutableTypes([
                Responses
            ])
        )
    ),
    (
        'callbacks',
        sob.Property(
            types=sob.MutableTypes([
                Callbacks
            ]),
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'schemes',
        sob.ArrayProperty(
            item_types=sob.MutableTypes([
                str
            ]),
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    ('deprecated', sob.BooleanProperty()),
    (
        'security',
        sob.ArrayProperty(
            item_types=sob.MutableTypes([
                SecurityRequirement
            ])
        )
    ),
    (
        'servers',
        sob.ArrayProperty(
            item_types=sob.MutableTypes([
                Server
            ]),
            versions=(
                'openapi>=3.0',
            )
        )
    )
])
sob.get_writable_object_meta(  # type: ignore
    Parameter
).properties = sob.Properties([
    (
        'name',
        sob.StringProperty(
            required=True
        )
    ),
    (
        'in_',
        sob.Property(
            name="in",
            required=True,
            types=sob.Types([
                sob.EnumeratedProperty(
                    types=sob.Types([
                        str
                    ]),
                    values={
                        "cookie",
                        "header",
                        "path",
                        "query"
                    },
                    versions=(
                        'openapi>=3.0',
                    )
                ),
                sob.EnumeratedProperty(
                    types=sob.Types([
                        str
                    ]),
                    values={
                        "body",
                        "formData",
                        "header",
                        "path",
                        "query"
                    },
                    versions=(
                        'openapi<3.0',
                    )
                )
            ])
        )
    ),
    ('description', sob.StringProperty()),
    ('required', sob.BooleanProperty()),
    ('deprecated', sob.BooleanProperty()),
    (
        'allow_empty_value',
        sob.BooleanProperty(
            name="allowEmptyValue"
        )
    ),
    (
        'style',
        sob.StringProperty(
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'explode',
        sob.BooleanProperty(
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'allow_reserved',
        sob.BooleanProperty(
            name="allowReserved",
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'schema',
        sob.Property(
            types=sob.MutableTypes([
                Reference,
                Schema
            ])
        )
    ),
    (
        'example',
        sob.Property(
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'examples',
        sob.DictionaryProperty(
            value_types=sob.MutableTypes([
                Reference,
                Example
            ]),
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'content',
        sob.DictionaryProperty(
            value_types=sob.MutableTypes([
                MediaType
            ]),
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'type_',
        sob.EnumeratedProperty(
            name="type",
            types=sob.Types([
                str
            ]),
            values={
                "array",
                "boolean",
                "file",
                "integer",
                "number",
                "object",
                "string"
            },
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'default',
        sob.Property(
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'maximum',
        sob.NumberProperty(
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'exclusive_maximum',
        sob.BooleanProperty(
            name="exclusiveMaximum",
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'minimum',
        sob.NumberProperty(
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'exclusive_minimum',
        sob.BooleanProperty(
            name="exclusiveMinimum",
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'max_length',
        sob.IntegerProperty(
            name="maxLength",
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'min_length',
        sob.IntegerProperty(
            name="minLength",
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'pattern',
        sob.StringProperty(
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'max_items',
        sob.IntegerProperty(
            name="maxItems",
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'min_items',
        sob.IntegerProperty(
            name="minItems",
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'unique_items',
        sob.BooleanProperty(
            name="uniqueItems",
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'enum',
        sob.ArrayProperty(
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'format_',
        sob.StringProperty(
            name="format",
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'collection_format',
        sob.EnumeratedProperty(
            name="collectionFormat",
            types=sob.Types([
                str
            ]),
            values={
                "csv",
                "multi",
                "pipes",
                "ssv",
                "tsv"
            },
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'items',
        sob.Property(
            types=sob.MutableTypes([
                Items
            ]),
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'multiple_of',
        sob.NumberProperty(
            name="multipleOf",
            versions=(
                'openapi<3.0',
            )
        )
    )
])
sob.get_writable_dictionary_meta(  # type: ignore
    Parameters
).value_types = sob.MutableTypes([
    Reference,
    Parameter
])
sob.get_writable_object_meta(  # type: ignore
    PathItem
).properties = sob.Properties([
    (
        'summary',
        sob.StringProperty(
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'description',
        sob.StringProperty(
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'get',
        sob.Property(
            types=sob.MutableTypes([
                Operation
            ])
        )
    ),
    (
        'put',
        sob.Property(
            types=sob.MutableTypes([
                Operation
            ])
        )
    ),
    (
        'post',
        sob.Property(
            types=sob.MutableTypes([
                Operation
            ])
        )
    ),
    (
        'delete',
        sob.Property(
            types=sob.MutableTypes([
                Operation
            ])
        )
    ),
    (
        'options',
        sob.Property(
            types=sob.MutableTypes([
                Operation
            ])
        )
    ),
    (
        'head',
        sob.Property(
            types=sob.MutableTypes([
                Operation
            ])
        )
    ),
    (
        'patch',
        sob.Property(
            types=sob.MutableTypes([
                Operation
            ])
        )
    ),
    (
        'trace',
        sob.Property(
            types=sob.MutableTypes([
                Operation
            ]),
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'servers',
        sob.ArrayProperty(
            item_types=sob.MutableTypes([
                Server
            ]),
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'parameters',
        sob.ArrayProperty(
            item_types=sob.MutableTypes([
                Reference,
                Parameter
            ])
        )
    )
])
sob.get_writable_dictionary_meta(  # type: ignore
    Paths
).value_types = sob.MutableTypes([
    PathItem
])
sob.get_writable_dictionary_meta(  # type: ignore
    Properties
).value_types = sob.MutableTypes([
    Reference,
    Schema
])
sob.get_writable_object_meta(  # type: ignore
    Reference
).properties = sob.Properties([
    (
        'ref',
        sob.StringProperty(
            name="$ref",
            required=True
        )
    ),
    ('summary', sob.StringProperty()),
    ('description', sob.StringProperty())
])
sob.get_writable_dictionary_meta(  # type: ignore
    RequestBodies
).value_types = sob.MutableTypes([
    Reference,
    RequestBody
])
sob.get_writable_object_meta(  # type: ignore
    RequestBody
).properties = sob.Properties([
    (
        'description',
        sob.StringProperty(
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'content',
        sob.DictionaryProperty(
            value_types=sob.MutableTypes([
                MediaType
            ]),
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'required',
        sob.BooleanProperty(
            versions=(
                'openapi>=3.0',
            )
        )
    )
])
sob.get_writable_object_meta(  # type: ignore
    Response
).properties = sob.Properties([
    (
        'description',
        sob.StringProperty(
            required=True
        )
    ),
    (
        'schema',
        sob.Property(
            types=sob.MutableTypes([
                Reference,
                Schema
            ]),
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'headers',
        sob.DictionaryProperty(
            value_types=sob.MutableTypes([
                Reference,
                Header
            ])
        )
    ),
    (
        'examples',
        sob.DictionaryProperty(
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'content',
        sob.DictionaryProperty(
            value_types=sob.MutableTypes([
                Reference,
                MediaType
            ]),
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'links',
        sob.DictionaryProperty(
            value_types=sob.MutableTypes([
                Reference,
                LinkObject
            ]),
            versions=(
                'openapi>=3.0',
            )
        )
    )
])
sob.get_writable_dictionary_meta(  # type: ignore
    Responses
).value_types = sob.MutableTypes([
    sob.Property(
        types=sob.MutableTypes([
            Reference,
            Response
        ]),
        versions=(
            'openapi>=3.0',
        )
    ),
    sob.Property(
        types=sob.MutableTypes([
            Response
        ]),
        versions=(
            'openapi<3.0',
        )
    )
])
sob.get_writable_object_meta(  # type: ignore
    Schema
).properties = sob.Properties([
    ('title', sob.StringProperty()),
    ('description', sob.StringProperty()),
    (
        'multiple_of',
        sob.NumberProperty(
            name="multipleOf"
        )
    ),
    ('maximum', sob.NumberProperty()),
    (
        'exclusive_maximum',
        sob.BooleanProperty(
            name="exclusiveMaximum"
        )
    ),
    ('minimum', sob.NumberProperty()),
    (
        'exclusive_minimum',
        sob.BooleanProperty(
            name="exclusiveMinimum"
        )
    ),
    (
        'max_length',
        sob.IntegerProperty(
            name="maxLength"
        )
    ),
    (
        'min_length',
        sob.IntegerProperty(
            name="minLength"
        )
    ),
    ('pattern', sob.StringProperty()),
    (
        'max_items',
        sob.IntegerProperty(
            name="maxItems"
        )
    ),
    (
        'min_items',
        sob.IntegerProperty(
            name="minItems"
        )
    ),
    (
        'unique_items',
        sob.BooleanProperty(
            name="uniqueItems"
        )
    ),
    (
        'items',
        sob.Property(
            types=sob.MutableTypes([
                Reference,
                Schema,
                sob.ArrayProperty(
                    item_types=sob.MutableTypes([
                        Reference,
                        Schema
                    ])
                )
            ])
        )
    ),
    (
        'max_properties',
        sob.IntegerProperty(
            name="maxProperties"
        )
    ),
    (
        'min_properties',
        sob.IntegerProperty(
            name="minProperties"
        )
    ),
    (
        'properties',
        sob.Property(
            types=sob.MutableTypes([
                Properties
            ])
        )
    ),
    (
        'additional_properties',
        sob.Property(
            name="additionalProperties",
            types=sob.MutableTypes([
                Reference,
                Schema,
                bool
            ])
        )
    ),
    ('enum', sob.ArrayProperty()),
    (
        'type_',
        sob.Property(
            name="type",
            types=sob.MutableTypes([
                sob.EnumeratedProperty(
                    types=sob.Types([
                        str
                    ]),
                    values={
                        "array",
                        "boolean",
                        "file",
                        "integer",
                        "number",
                        "object",
                        "string"
                    }
                )
            ])
        )
    ),
    (
        'format_',
        sob.StringProperty(
            name="format"
        )
    ),
    (
        'required',
        sob.ArrayProperty(
            item_types=sob.MutableTypes([
                str
            ])
        )
    ),
    (
        'all_of',
        sob.ArrayProperty(
            item_types=sob.MutableTypes([
                Reference,
                Schema
            ]),
            name="allOf"
        )
    ),
    (
        'any_of',
        sob.ArrayProperty(
            item_types=sob.MutableTypes([
                Reference,
                Schema
            ]),
            name="anyOf"
        )
    ),
    (
        'one_of',
        sob.ArrayProperty(
            item_types=sob.MutableTypes([
                Reference,
                Schema
            ]),
            name="oneOf"
        )
    ),
    (
        'is_not',
        sob.Property(
            name="isNot",
            types=sob.MutableTypes([
                Reference,
                Schema
            ])
        )
    ),
    ('definitions', sob.Property()),
    ('default', sob.Property()),
    (
        'discriminator',
        sob.Property(
            types=sob.MutableTypes([
                sob.Property(
                    types=sob.MutableTypes([
                        Discriminator
                    ]),
                    versions=(
                        'openapi>=3.0',
                    )
                ),
                sob.Property(
                    types=sob.MutableTypes([
                        str
                    ]),
                    versions=(
                        'openapi<3.0',
                    )
                )
            ])
        )
    ),
    (
        'read_only',
        sob.BooleanProperty(
            name="readOnly"
        )
    ),
    (
        'write_only',
        sob.BooleanProperty(
            name="writeOnly",
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'xml',
        sob.Property(
            types=sob.MutableTypes([
                XML
            ])
        )
    ),
    (
        'external_docs',
        sob.Property(
            name="externalDocs",
            types=sob.MutableTypes([
                ExternalDocumentation
            ])
        )
    ),
    ('example', sob.Property()),
    (
        'deprecated',
        sob.BooleanProperty(
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'links',
        sob.ArrayProperty(
            item_types=sob.MutableTypes([
                Link
            ])
        )
    ),
    (
        'nullable',
        sob.BooleanProperty(
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'content_encoding',
        sob.StringProperty(
            name="contentEncoding",
            versions=(
                'openapi>=3.1',
            )
        )
    ),
    (
        'content_media_type',
        sob.StringProperty(
            name="contentMediaType",
            versions=(
                'openapi>=3.1',
            )
        )
    ),
    (
        'examples',
        sob.ArrayProperty(
            name="examples",
            versions=(
                'openapi>=3.1',
            )
        )
    )
])
sob.get_writable_dictionary_meta(  # type: ignore
    Schemas
).value_types = sob.MutableTypes([
    Reference,
    Schema
])
sob.get_writable_dictionary_meta(  # type: ignore
    SecurityRequirement
).value_types = sob.MutableTypes([
    sob.ArrayProperty(
        item_types=sob.MutableTypes([
            str
        ])
    )
])
sob.get_writable_object_meta(  # type: ignore
    SecurityScheme
).properties = sob.Properties([
    (
        'type_',
        sob.EnumeratedProperty(
            name="type",
            required=True,
            types=sob.Types([
                str
            ]),
            values={
                "apiKey",
                "http",
                "oauth2",
                "openIdConnect"
            }
        )
    ),
    ('description', sob.StringProperty()),
    ('name', sob.StringProperty()),
    (
        'in_',
        sob.Property(
            name="in",
            types=sob.MutableTypes([
                sob.EnumeratedProperty(
                    types=sob.Types([
                        str
                    ]),
                    values={
                        "cookie",
                        "header",
                        "query"
                    },
                    versions=(
                        'openapi>=3.0',
                    )
                ),
                sob.EnumeratedProperty(
                    types=sob.Types([
                        str
                    ]),
                    values={
                        "header",
                        "query"
                    },
                    versions=(
                        'openapi<3.0',
                    )
                )
            ])
        )
    ),
    (
        'scheme',
        sob.StringProperty(
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'bearer_format',
        sob.StringProperty(
            name="bearerFormat"
        )
    ),
    (
        'flows',
        sob.Property(
            types=sob.MutableTypes([
                OAuthFlows
            ]),
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'open_id_connect_url',
        sob.StringProperty(
            name="openIdConnectUrl"
        )
    ),
    (
        'flow',
        sob.StringProperty(
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'authorization_url',
        sob.StringProperty(
            name="authorizationUrl",
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'token_url',
        sob.StringProperty(
            name="tokenUrl",
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'scopes',
        sob.DictionaryProperty(
            value_types=sob.MutableTypes([
                str
            ]),
            versions=(
                'openapi<3.0',
            )
        )
    )
])
sob.get_writable_dictionary_meta(  # type: ignore
    SecuritySchemes
).value_types = sob.MutableTypes([
    Reference,
    SecurityScheme
])
sob.get_writable_object_meta(  # type: ignore
    Server
).properties = sob.Properties([
    (
        'url',
        sob.StringProperty(
            required=True
        )
    ),
    ('description', sob.StringProperty()),
    (
        'variables',
        sob.DictionaryProperty(
            value_types=sob.MutableTypes([
                ServerVariable
            ])
        )
    )
])
sob.get_writable_object_meta(  # type: ignore
    ServerVariable
).properties = sob.Properties([
    (
        'enum',
        sob.ArrayProperty(
            item_types=sob.MutableTypes([
                str
            ])
        )
    ),
    (
        'default',
        sob.StringProperty(
            required=True
        )
    ),
    ('description', sob.StringProperty())
])
sob.get_writable_object_meta(  # type: ignore
    Tag
).properties = sob.Properties([
    (
        'name',
        sob.StringProperty(
            required=True
        )
    ),
    ('description', sob.StringProperty()),
    (
        'external_docs',
        sob.Property(
            types=sob.MutableTypes([
                ExternalDocumentation
            ])
        )
    )
])
sob.get_writable_object_meta(  # type: ignore
    XML
).properties = sob.Properties([
    ('name', sob.StringProperty()),
    (
        'name_space',
        sob.StringProperty(
            name="nameSpace"
        )
    ),
    ('prefix', sob.StringProperty()),
    ('attribute', sob.BooleanProperty()),
    ('wrapped', sob.BooleanProperty())
])

# region Aliases

Link_ = _deprecated(
    "`oapi.oas.model.Link_` is deprecated and will be removed in oapi 3. "
    "Please use `oapi.oas.model.LinkObject` instead."
)(LinkObject)

# endregion

# region Hooks


def _add_object_property(object_: sob.abc.Object, key: str) -> None:
    """
    Look for a matching property, and if none exists--create one
    """
    object_meta: sob.abc.ObjectMeta | None = sob.read_object_meta(object_)
    if object_meta and object_meta.properties:
        properties: sob.abc.Properties = object_meta.properties
        key_property: tuple[str, sob.abc.Property]
        if key in (
            key_property[1].name or key_property[0]
            for key_property in properties.items()
        ):
            # There is no need to add the property, it already exists
            return
    object_meta = sob.get_writable_object_meta(object_)
    if object_meta.properties is None:
        object_meta.properties = sob.Properties()  # type: ignore
    property_name = sob.utilities.get_property_name(key)
    object_meta.properties[property_name] = sob.Property(name=key)


def _reference_before_setitem(
    reference_: sob.abc.Object, key: str, value: sob.abc.MarshallableTypes
) -> tuple[str, typing.Any]:
    """
    This hook allows for the use of any arbitrary attribute, as specified in
    the `patternProperties` for this object in the OpenAPI spec.
    """
    if key != "$ref":
        _add_object_property(reference_, key)
    return key, value


def _reference_after_unmarshal(data: sob.abc.Model) -> typing.Any:
    """
    This ensures all reference objects have a `$ref` attribute
    """
    if not isinstance(data, Reference):
        raise TypeError(data)
    message: str
    ref: str | None
    try:
        ref = typing.cast(str, data["$ref"])
    except KeyError:
        ref = None
    if ref is None:
        message = (
            "All instances of "
            f"`{sob.utilities.get_qualified_name(Reference)}` must have a "
            "`$ref` attribute"
        )
        raise ValueError(message)
    return data


def _parameter_after_validate(parameter: sob.abc.Model) -> None:
    message: str
    if not isinstance(parameter, Parameter):
        raise TypeError(parameter)
    if (parameter.content is not None) and len(
        tuple(parameter.content.keys())
    ) > 1:
        message = (
            f"`{sob.utilities.get_qualified_name(type(parameter))}."
            "content` may have only one mapped value.:\n"
            f"{sob.utilities.represent(parameter)}"
        )
        raise sob.errors.ValidationError(message)
    if (parameter.content is not None) and (parameter.schema is not None):
        message = (
            "An instance of "
            f"`{sob.utilities.get_qualified_name(type(parameter))}` may have "
            "a `schema` property or a `content` property, but not *both*:\n"
            f"{sob.utilities.represent(parameter)}"
        )
        raise sob.errors.ValidationError(message)
    _schema_after_validate(parameter)


def _schema_after_validate(schema: sob.abc.Model) -> None:
    message: str
    if not isinstance(schema, (Schema, Parameter)):
        raise TypeError(schema)
    if schema.format_ in (
        "int32",
        "int64",  # type_ == 'integer'
        "float",
        "double",  # type_ == 'number'
        "byte",
        "base64",
        "binary",
        "date",
        "date-time",
        "password",  # type_ == 'string'
    ):
        if schema.type_ == "integer" and (
            schema.format_ not in ("int32", "int64", None)
        ):
            qualified_class_name = sob.utilities.get_qualified_name(
                type(schema)
            )
            message = (
                f'"{schema.format_}" is not a valid value for '
                f"`{qualified_class_name}.format_` in this circumstance. "
                f'`{qualified_class_name}.format_` may be "int32" or "int64" '
                f'when `{qualified_class_name}.type_` is "integer".'
            )
            raise sob.errors.ValidationError(message)
        if schema.type_ == "number" and (
            schema.format_ not in ("float", "double", None)
        ):
            qualified_class_name = sob.utilities.get_qualified_name(
                type(schema)
            )
            message = (
                f'"{schema.format_}" in not a valid value for '
                f"`{qualified_class_name}.format_` in this circumstance. "
                f'`{qualified_class_name}.format_` may be "float" or "double" '
                f'when `{qualified_class_name}.type_` is "number".'
            )
            raise sob.errors.ValidationError(message)
        if schema.type_ == "string" and (
            schema.format_
            not in (
                "base64",
                "byte",
                "binary",
                "date",
                "date-time",
                "password",
                None,
            )
        ):
            qualified_class_name = sob.utilities.get_qualified_name(
                type(schema)
            )
            message = (
                f'"{schema.format_}" in not a valid value for '
                f"`{qualified_class_name}.format_` in this circumstance. "
                f'`{qualified_class_name}.format_` may be "byte", "binary", '
                '"date", "date-time", "base64" or "password" when '
                f'`{qualified_class_name}.type_` is "string".'
            )
            raise sob.errors.ValidationError(message)


_reference_hooks: sob.abc.ObjectHooks = sob.get_writable_object_hooks(
    Reference
)
_reference_hooks.before_setitem = _reference_before_setitem
_reference_hooks.after_unmarshal = _reference_after_unmarshal
_parameter_hooks: sob.abc.ObjectHooks = sob.get_writable_object_hooks(
    Parameter
)
_parameter_hooks.after_validate = _parameter_after_validate
_schema_hooks: sob.abc.ObjectHooks = sob.get_writable_object_hooks(Schema)
_schema_hooks.after_validate = _schema_after_validate
if _schema_hooks.before_setitem != (
    typing.cast(
        sob.abc.ObjectHooks, sob.read_object_hooks(Schema())
    ).before_setitem
):
    raise ValueError(_schema_hooks.before_setitem)

# endregion
