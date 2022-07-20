"""
https://github.com/OAI/OpenAPI-Specification
"""
import decimal
import sob
import typing

# region Base Classes


class ExtensibleObject(sob.model.Object):
    pass


# endregion


class Callback(sob.model.Dictionary):

    def __init__(
        self,
        items: typing.Union[
            sob.abc.Dictionary,
            typing.Mapping[
                str,
                "PathItem"
            ],
            typing.Iterable[
                typing.Tuple[
                    str,
                    "PathItem"
                ]
            ],
            sob.abc.Readable,
            str,
            bytes,
            None,
        ] = None,
    ) -> None:
        super().__init__(items)


class Callbacks(sob.model.Dictionary):

    def __init__(
        self,
        items: typing.Union[
            sob.abc.Dictionary,
            typing.Mapping[
                str,
                typing.Union[
                    "Reference",
                    "Callback"
                ]
            ],
            typing.Iterable[
                typing.Tuple[
                    str,
                    typing.Union[
                        "Reference",
                        "Callback"
                    ]
                ]
            ],
            sob.abc.Readable,
            str,
            bytes,
            None,
        ] = None,
    ) -> None:
        super().__init__(items)


class Components(ExtensibleObject):

    def __init__(
        self,
        _data: typing.Union[
            sob.abc.Dictionary,
            typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ],
            typing.Iterable[
                typing.Tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ],
            sob.abc.Readable,
            str,
            bytes,
            None,
        ] = None,
        schemas: typing.Optional[
            "Schemas"
        ] = None,
        responses: typing.Optional[
            "Responses"
        ] = None,
        parameters: typing.Optional[
            "Parameters"
        ] = None,
        examples: typing.Optional[
            "Examples"
        ] = None,
        request_bodies: typing.Optional[
            "RequestBodies"
        ] = None,
        headers: typing.Optional[
            "Headers"
        ] = None,
        security_schemes: typing.Optional[
            "SecuritySchemes"
        ] = None,
        links: typing.Optional[
            "Links"
        ] = None,
        callbacks: typing.Optional[
            "Callbacks"
        ] = None
    ) -> None:
        self.schemas = schemas
        self.responses = responses
        self.parameters = parameters
        self.examples = examples
        self.request_bodies = request_bodies
        self.headers = headers
        self.security_schemes = security_schemes
        self.links = links
        self.callbacks = callbacks
        super().__init__(_data)


class Contact(ExtensibleObject):
    """
    https://bit.ly/3uLJCHF
    """

    def __init__(
        self,
        _data: typing.Union[
            sob.abc.Dictionary,
            typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ],
            typing.Iterable[
                typing.Tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ],
            sob.abc.Readable,
            str,
            bytes,
            None,
        ] = None,
        name: typing.Optional[
            str
        ] = None,
        url: typing.Optional[
            str
        ] = None,
        email: typing.Optional[
            str
        ] = None
    ) -> None:
        self.name = name
        self.url = url
        self.email = email
        super().__init__(_data)


class Definitions(sob.model.Dictionary):

    def __init__(
        self,
        items: typing.Union[
            sob.abc.Dictionary,
            typing.Mapping[
                str,
                "Schema"
            ],
            typing.Iterable[
                typing.Tuple[
                    str,
                    "Schema"
                ]
            ],
            sob.abc.Readable,
            str,
            bytes,
            None,
        ] = None,
    ) -> None:
        super().__init__(items)


class Discriminator(ExtensibleObject):
    """
    https://bit.ly/3uFJ9Hi

    Properties:

    - property_name (str): The name of the property which will hold the
      discriminating value.
    - mapping ({str:str}): An mappings of payload values to schema names or
      references.
    """

    def __init__(
        self,
        _data: typing.Union[
            sob.abc.Dictionary,
            typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ],
            typing.Iterable[
                typing.Tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ],
            sob.abc.Readable,
            str,
            bytes,
            None,
        ] = None,
        property_name: typing.Optional[
            str
        ] = None,
        mapping: typing.Optional[
            typing.Mapping[
                str,
                str
            ]
        ] = None
    ) -> None:
        self.property_name = property_name
        self.mapping = mapping
        super().__init__(_data)


class Encoding(ExtensibleObject):
    """
    https://bit.ly/3qSyFTA
    """

    def __init__(
        self,
        _data: typing.Union[
            sob.abc.Dictionary,
            typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ],
            typing.Iterable[
                typing.Tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ],
            sob.abc.Readable,
            str,
            bytes,
            None,
        ] = None,
        content_type: typing.Optional[
            str
        ] = None,
        headers: typing.Optional[
            typing.Mapping[
                str,
                typing.Union[
                    "Reference",
                    "Header"
                ]
            ]
        ] = None,
        style: typing.Optional[
            str
        ] = None,
        explode: typing.Optional[
            bool
        ] = None,
        allow_reserved: typing.Optional[
            bool
        ] = None
    ) -> None:
        self.content_type = content_type
        self.headers = headers
        self.style = style
        self.explode = explode
        self.allow_reserved = allow_reserved
        super().__init__(_data)


class Example(ExtensibleObject):
    """
    https://bit.ly/3LyvV62
    """

    def __init__(
        self,
        _data: typing.Union[
            sob.abc.Dictionary,
            typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ],
            typing.Iterable[
                typing.Tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ],
            sob.abc.Readable,
            str,
            bytes,
            None,
        ] = None,
        summary: typing.Optional[
            str
        ] = None,
        description: typing.Optional[
            str
        ] = None,
        value: typing.Optional[
            typing.Any
        ] = None,
        external_value: typing.Optional[
            str
        ] = None
    ) -> None:
        self.summary = summary
        self.description = description
        self.value = value
        self.external_value = external_value
        super().__init__(_data)


class Examples(sob.model.Dictionary):

    def __init__(
        self,
        items: typing.Union[
            sob.abc.Dictionary,
            typing.Mapping[
                str,
                typing.Union[
                    "Reference",
                    "Example"
                ]
            ],
            typing.Iterable[
                typing.Tuple[
                    str,
                    typing.Union[
                        "Reference",
                        "Example"
                    ]
                ]
            ],
            sob.abc.Readable,
            str,
            bytes,
            None,
        ] = None,
    ) -> None:
        super().__init__(items)


class ExternalDocumentation(ExtensibleObject):
    """
    Properties:

        - description (str)
        - url (str)
    """

    def __init__(
        self,
        _data: typing.Union[
            sob.abc.Dictionary,
            typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ],
            typing.Iterable[
                typing.Tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ],
            sob.abc.Readable,
            str,
            bytes,
            None,
        ] = None,
        description: typing.Optional[
            str
        ] = None,
        url: typing.Optional[
            str
        ] = None
    ) -> None:
        self.description = description
        self.url = url
        super().__init__(_data)


class Header(ExtensibleObject):

    def __init__(
        self,
        _data: typing.Union[
            sob.abc.Dictionary,
            typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ],
            typing.Iterable[
                typing.Tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ],
            sob.abc.Readable,
            str,
            bytes,
            None,
        ] = None,
        description: typing.Optional[
            str
        ] = None,
        required: typing.Optional[
            bool
        ] = None,
        deprecated: typing.Optional[
            bool
        ] = None,
        allow_empty_value: typing.Optional[
            bool
        ] = None,
        style: typing.Optional[
            str
        ] = None,
        explode: typing.Optional[
            bool
        ] = None,
        allow_reserved: typing.Optional[
            bool
        ] = None,
        schema: typing.Optional[
            typing.Union[
                "Reference",
                "Schema"
            ]
        ] = None,
        example: typing.Optional[
            typing.Any
        ] = None,
        examples: typing.Optional[
            typing.Mapping[
                str,
                typing.Union[
                    "Reference",
                    "Example"
                ]
            ]
        ] = None,
        content: typing.Optional[
            typing.Mapping[
                str,
                "MediaType"
            ]
        ] = None,
        type_: typing.Optional[
            str
        ] = None,
        default: typing.Optional[
            typing.Any
        ] = None,
        maximum: typing.Optional[
            typing.Union[
                float,
                int,
                decimal.Decimal
            ]
        ] = None,
        exclusive_maximum: typing.Optional[
            bool
        ] = None,
        minimum: typing.Optional[
            typing.Union[
                float,
                int,
                decimal.Decimal
            ]
        ] = None,
        exclusive_minimum: typing.Optional[
            bool
        ] = None,
        max_length: typing.Optional[
            int
        ] = None,
        min_length: typing.Optional[
            int
        ] = None,
        pattern: typing.Optional[
            str
        ] = None,
        max_items: typing.Optional[
            int
        ] = None,
        min_items: typing.Optional[
            int
        ] = None,
        unique_items: typing.Optional[
            bool
        ] = None,
        enum: typing.Optional[
            typing.Sequence[
                typing.Optional[sob.abc.MarshallableTypes]
            ]
        ] = None,
        format_: typing.Optional[
            str
        ] = None,
        collection_format: typing.Optional[
            str
        ] = None,
        items: typing.Optional[
            "Items"
        ] = None,
        multiple_of: typing.Optional[
            typing.Union[
                float,
                int,
                decimal.Decimal
            ]
        ] = None
    ) -> None:
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
        self.format_ = format_
        self.collection_format = collection_format
        self.items = items
        self.multiple_of = multiple_of
        super().__init__(_data)


class Headers(sob.model.Dictionary):

    def __init__(
        self,
        items: typing.Union[
            sob.abc.Dictionary,
            typing.Mapping[
                str,
                typing.Union[
                    "Reference",
                    "Header"
                ]
            ],
            typing.Iterable[
                typing.Tuple[
                    str,
                    typing.Union[
                        "Reference",
                        "Header"
                    ]
                ]
            ],
            sob.abc.Readable,
            str,
            bytes,
            None,
        ] = None,
    ) -> None:
        super().__init__(items)


class Info(ExtensibleObject):
    """
    https://bit.ly/3iUcY1k
    """

    def __init__(
        self,
        _data: typing.Union[
            sob.abc.Dictionary,
            typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ],
            typing.Iterable[
                typing.Tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ],
            sob.abc.Readable,
            str,
            bytes,
            None,
        ] = None,
        title: typing.Optional[
            str
        ] = None,
        description: typing.Optional[
            str
        ] = None,
        terms_of_service: typing.Optional[
            str
        ] = None,
        contact: typing.Optional[
            "Contact"
        ] = None,
        license_: typing.Optional[
            "License"
        ] = None,
        version: typing.Optional[
            str
        ] = None
    ) -> None:
        self.title = title
        self.description = description
        self.terms_of_service = terms_of_service
        self.contact = contact
        self.license_ = license_
        self.version = version
        super().__init__(_data)


class Items(ExtensibleObject):
    """
    https://bit.ly/3K0BklW (OpenAPI/Swagger Version 2.0 Only)
    """

    def __init__(
        self,
        _data: typing.Union[
            sob.abc.Dictionary,
            typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ],
            typing.Iterable[
                typing.Tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ],
            sob.abc.Readable,
            str,
            bytes,
            None,
        ] = None,
        type_: typing.Optional[
            str
        ] = None,
        format_: typing.Optional[
            str
        ] = None,
        items: typing.Optional[
            "Items"
        ] = None,
        collection_format: typing.Optional[
            str
        ] = None,
        default: typing.Optional[
            typing.Any
        ] = None,
        maximum: typing.Optional[
            typing.Union[
                float,
                int,
                decimal.Decimal
            ]
        ] = None,
        exclusive_maximum: typing.Optional[
            bool
        ] = None,
        minimum: typing.Optional[
            typing.Union[
                float,
                int,
                decimal.Decimal
            ]
        ] = None,
        exclusive_minimum: typing.Optional[
            bool
        ] = None,
        max_length: typing.Optional[
            int
        ] = None,
        min_length: typing.Optional[
            int
        ] = None,
        pattern: typing.Optional[
            str
        ] = None,
        max_items: typing.Optional[
            int
        ] = None,
        min_items: typing.Optional[
            int
        ] = None,
        unique_items: typing.Optional[
            bool
        ] = None,
        enum: typing.Optional[
            typing.Sequence[
                typing.Optional[sob.abc.MarshallableTypes]
            ]
        ] = None,
        multiple_of: typing.Optional[
            typing.Union[
                float,
                int,
                decimal.Decimal
            ]
        ] = None
    ) -> None:
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
        super().__init__(_data)


class License(ExtensibleObject):
    """
    https://bit.ly/3NzSlFt
    """

    def __init__(
        self,
        _data: typing.Union[
            sob.abc.Dictionary,
            typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ],
            typing.Iterable[
                typing.Tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ],
            sob.abc.Readable,
            str,
            bytes,
            None,
        ] = None,
        name: typing.Optional[
            str
        ] = None,
        url: typing.Optional[
            str
        ] = None
    ) -> None:
        self.name = name
        self.url = url
        super().__init__(_data)


class Link(ExtensibleObject):

    def __init__(
        self,
        _data: typing.Union[
            sob.abc.Dictionary,
            typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ],
            typing.Iterable[
                typing.Tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ],
            sob.abc.Readable,
            str,
            bytes,
            None,
        ] = None,
        rel: typing.Optional[
            str
        ] = None,
        href: typing.Optional[
            str
        ] = None
    ) -> None:
        self.rel = rel
        self.href = href
        super().__init__(_data)


class Link_(ExtensibleObject):
    """
    https://bit.ly/3JWqWM3
    """

    def __init__(
        self,
        _data: typing.Union[
            sob.abc.Dictionary,
            typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ],
            typing.Iterable[
                typing.Tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ],
            sob.abc.Readable,
            str,
            bytes,
            None,
        ] = None,
        operation_ref: typing.Optional[
            str
        ] = None,
        operation_id: typing.Optional[
            str
        ] = None,
        parameters: typing.Optional[
            typing.Mapping[
                str,
                typing.Optional[sob.abc.MarshallableTypes]
            ]
        ] = None,
        request_body: typing.Optional[
            typing.Any
        ] = None,
        description: typing.Optional[
            str
        ] = None,
        server: typing.Optional[
            "Server"
        ] = None
    ) -> None:
        self.operation_ref = operation_ref
        self.operation_id = operation_id
        self.parameters = parameters
        self.request_body = request_body
        self.description = description
        self.server = server
        super().__init__(_data)


class Links(sob.model.Dictionary):

    def __init__(
        self,
        items: typing.Union[
            sob.abc.Dictionary,
            typing.Mapping[
                str,
                typing.Union[
                    "Reference",
                    "Link_"
                ]
            ],
            typing.Iterable[
                typing.Tuple[
                    str,
                    typing.Union[
                        "Reference",
                        "Link_"
                    ]
                ]
            ],
            sob.abc.Readable,
            str,
            bytes,
            None,
        ] = None,
    ) -> None:
        super().__init__(items)


class MediaType(ExtensibleObject):
    """
    https://bit.ly/3tU0FYU
    """

    def __init__(
        self,
        _data: typing.Union[
            sob.abc.Dictionary,
            typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ],
            typing.Iterable[
                typing.Tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ],
            sob.abc.Readable,
            str,
            bytes,
            None,
        ] = None,
        schema: typing.Optional[
            typing.Union[
                "Reference",
                "Schema"
            ]
        ] = None,
        example: typing.Optional[
            typing.Any
        ] = None,
        examples: typing.Optional[
            typing.Mapping[
                str,
                typing.Union[
                    "Reference",
                    "Example"
                ]
            ]
        ] = None,
        encoding: typing.Optional[
            typing.Mapping[
                str,
                typing.Union[
                    "Reference",
                    "Encoding"
                ]
            ]
        ] = None
    ) -> None:
        self.schema = schema
        self.example = example
        self.examples = examples
        self.encoding = encoding
        super().__init__(_data)


class OAuthFlow(ExtensibleObject):
    """
    https://bit.ly/3iUiXD4
    """

    def __init__(
        self,
        _data: typing.Union[
            sob.abc.Dictionary,
            typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ],
            typing.Iterable[
                typing.Tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ],
            sob.abc.Readable,
            str,
            bytes,
            None,
        ] = None,
        authorization_url: typing.Optional[
            str
        ] = None,
        token_url: typing.Optional[
            str
        ] = None,
        refresh_url: typing.Optional[
            str
        ] = None,
        scopes: typing.Optional[
            typing.Mapping[
                str,
                str
            ]
        ] = None
    ) -> None:
        self.authorization_url = authorization_url
        self.token_url = token_url
        self.refresh_url = refresh_url
        self.scopes = scopes
        super().__init__(_data)


class OAuthFlows(ExtensibleObject):
    """
    https://bit.ly/36Ywwie
    """

    def __init__(
        self,
        _data: typing.Union[
            sob.abc.Dictionary,
            typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ],
            typing.Iterable[
                typing.Tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ],
            sob.abc.Readable,
            str,
            bytes,
            None,
        ] = None,
        implicit: typing.Optional[
            "OAuthFlow"
        ] = None,
        password: typing.Optional[
            "OAuthFlow"
        ] = None,
        client_credentials: typing.Optional[
            "OAuthFlow"
        ] = None,
        authorization_code: typing.Optional[
            "OAuthFlow"
        ] = None
    ) -> None:
        self.implicit = implicit
        self.password = password
        self.client_credentials = client_credentials
        self.authorization_code = authorization_code
        super().__init__(_data)


class OpenAPI(ExtensibleObject):
    """
    https://bit.ly/3Lu2zp9
    """

    def __init__(
        self,
        _data: typing.Union[
            sob.abc.Dictionary,
            typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ],
            typing.Iterable[
                typing.Tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ],
            sob.abc.Readable,
            str,
            bytes,
            None,
        ] = None,
        openapi: typing.Optional[
            str
        ] = None,
        info: typing.Optional[
            "Info"
        ] = None,
        json_schema_dialect: typing.Optional[
            str
        ] = None,
        host: typing.Optional[
            str
        ] = None,
        servers: typing.Optional[
            typing.Sequence[
                "Server"
            ]
        ] = None,
        base_path: typing.Optional[
            str
        ] = None,
        schemes: typing.Optional[
            typing.Sequence[
                str
            ]
        ] = None,
        tags: typing.Optional[
            typing.Sequence[
                "Tag"
            ]
        ] = None,
        paths: typing.Optional[
            "Paths"
        ] = None,
        components: typing.Optional[
            "Components"
        ] = None,
        consumes: typing.Optional[
            typing.Sequence[
                str
            ]
        ] = None,
        swagger: typing.Optional[
            str
        ] = None,
        definitions: typing.Optional[
            "Definitions"
        ] = None,
        security_definitions: typing.Optional[
            "SecuritySchemes"
        ] = None,
        produces: typing.Optional[
            typing.Sequence[
                str
            ]
        ] = None,
        external_docs: typing.Optional[
            "ExternalDocumentation"
        ] = None,
        parameters: typing.Optional[
            typing.Mapping[
                str,
                "Parameter"
            ]
        ] = None,
        responses: typing.Optional[
            typing.Mapping[
                str,
                "Response"
            ]
        ] = None,
        security: typing.Optional[
            typing.Sequence[
                "SecurityRequirement"
            ]
        ] = None
    ) -> None:
        self.openapi = openapi
        self.info = info
        self.json_schema_dialect = json_schema_dialect
        self.host = host
        self.servers = servers
        self.base_path = base_path
        self.schemes = schemes
        self.tags = tags
        self.paths = paths
        self.components = components
        self.consumes = consumes
        self.swagger = swagger
        self.definitions = definitions
        self.security_definitions = security_definitions
        self.produces = produces
        self.external_docs = external_docs
        self.parameters = parameters
        self.responses = responses
        self.security = security
        super().__init__(_data)
        version: str = self.openapi or self.swagger or ""
        if version:
            sob.meta.version(self, "openapi", version)


class Operation(ExtensibleObject):
    """
    https://bit.ly/3DpKi9I

    Describes a single API operation on a path.

    Properties:

    - tags ([str]):  A list of tags for API documentation control. Tags can
      be used for logical grouping of operations by resources or any other
      qualifier.
    - summary (str):  A short summary of what the operation does.
    - description (str): A verbose explanation of the operation behavior. `
      CommonMark <http://spec.commonmark.org>` syntax may be used for rich
      text representation.
    - external_docs (ExternalDocumentation):  Additional external
      documentation for this operation.
    - operation_id (str):  Unique string used to identify the operation.
      The ID must be unique among all operations described in the API. Tools
      and libraries may use the `operation_id` to uniquely identify an
      operation, therefore, it is recommended to follow common programming
      naming conventions.
    - parameters ([Parameter|Reference]):  A list of parameters that are
      applicable for this operation. If a parameter is already defined at the
      `PathItem`, the new definition will override it, but can never remove it.
    - request_body (RequestBody|Reference):  The request body applicable
      for this operation. The requestBody is only
      supported in HTTP methods where the HTTP 1.1 specification
      `RFC7231 <https://tools.ietf.org/html/rfc7231#section-4.3.1>` has
      explicitly defined semantics for request
      bodies.
    - responses (Responses): A mapping of HTTP
      response codes to `Response` objects.
    - callbacks ({str:{str:PathItem}|Reference})
    - deprecated (bool)
    - security ([SecurityRequirement])
    - servers ([Server])

    Version 2x Compatibility:

    - produces ([str])
    """

    def __init__(
        self,
        _data: typing.Union[
            sob.abc.Dictionary,
            typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ],
            typing.Iterable[
                typing.Tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ],
            sob.abc.Readable,
            str,
            bytes,
            None,
        ] = None,
        tags: typing.Optional[
            typing.Sequence[
                str
            ]
        ] = None,
        summary: typing.Optional[
            str
        ] = None,
        description: typing.Optional[
            str
        ] = None,
        external_docs: typing.Optional[
            "ExternalDocumentation"
        ] = None,
        operation_id: typing.Optional[
            str
        ] = None,
        consumes: typing.Optional[
            typing.Sequence[
                str
            ]
        ] = None,
        produces: typing.Optional[
            typing.Sequence[
                str
            ]
        ] = None,
        parameters: typing.Optional[
            typing.Sequence[
                typing.Union[
                    "Reference",
                    "Parameter"
                ]
            ]
        ] = None,
        request_body: typing.Optional[
            typing.Union[
                "Reference",
                "RequestBody"
            ]
        ] = None,
        responses: typing.Optional[
            "Responses"
        ] = None,
        callbacks: typing.Optional[
            "Callbacks"
        ] = None,
        schemes: typing.Optional[
            typing.Sequence[
                str
            ]
        ] = None,
        deprecated: typing.Optional[
            bool
        ] = None,
        security: typing.Optional[
            typing.Sequence[
                "SecurityRequirement"
            ]
        ] = None,
        servers: typing.Optional[
            typing.Sequence[
                "Server"
            ]
        ] = None
    ) -> None:
        self.tags = tags
        self.summary = summary
        self.description = description
        self.external_docs = external_docs
        self.operation_id = operation_id
        self.consumes = consumes
        self.produces = produces
        self.parameters = parameters
        self.request_body = request_body
        self.responses = responses
        self.callbacks = callbacks
        self.schemes = schemes
        self.deprecated = deprecated
        self.security = security
        self.servers = servers
        super().__init__(_data)


class Parameter(ExtensibleObject):
    """
    https://bit.ly/3wTpiXR

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
    - allow_empty_value (bool): Sets the ability to pass empty-valued
      parameters. This is valid only for query parameters and allows sending a
      parameter with an empty value. The
      default value is `False`. If `style`
      is used, and if `behavior` is inapplicable (cannot be serialized),
      the value of `allow_empty_value` will be ignored.
    - style (str): Describes how the parameter value will be serialized,
      depending on the type of the parameter value (see:
      https://swagger.io/docs/specification/serialization).
      - "matrix"
      - "label"
      - "form"
      - "simple"
      - "spaceDelimited"
      - "pipeDelimited"
      - "deepObject"

      Default values:
      - query: "form"
      - path: "simple"
      - header: "simple"
      - cookie: "form"

    - explode (bool): When this is `True`, array or object parameter values
      generate separate parameters for each value of the array or name-value
      pair of the map. For other value_types of parameters this property has no
      effect. When `style` is "form", the default value is `True`. For all
      other styles, the default value is `False`.
    - allow_reserved (bool): Determines whether the parameter value SHOULD
      allow reserved characters :/?#[]@!$&'()*+,;= (as defined by
      `RFC3986 <https://tools.ietf.org/ html/rfc3986#section-2.2>`) to be
      included without percent-encoding. This property only applies to
      "query" parameters. The default value is `False`.
    - schema (Schema): The schema defining the type used for the parameter.
    - example (Any): Example of the media type. The example should match
      the specified schema and encoding properties if present. The `example`
      parameter should not be present if `examples` is present. If
      referencing a `schema` which contains an example--*this* example
      overrides the example provided by the `schema`. To represent
      examples of media value_types that cannot naturally be represented in
      JSON or YAML, a string value can contain the example with escaping where
      necessary.
    - examples ({str:Example}): Examples of the media type. Each example
      should contain a value in the correct format, as specified in the
      parameter encoding. The `examples` parameter should not be present if
      `example` is present. If referencing a `schema` which contains an
      example--*these* example override the
      example provided by the `schema`. To represent examples of media
      value_types that cannot naturally be represented
      in JSON or YAML, a string value can contain the example with escaping
      where necessary. https://bit.ly/3LMUeNJ
    - content ({str:MediaType}): A map containing the representations for
      the parameter. The name is the media type and the value describing it.
      The map must only contain one entry.

    ...for version 2x compatibility:

    - type_ (str)
    - enum ([Any])
    """

    def __init__(
        self,
        _data: typing.Union[
            sob.abc.Dictionary,
            typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ],
            typing.Iterable[
                typing.Tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ],
            sob.abc.Readable,
            str,
            bytes,
            None,
        ] = None,
        name: typing.Optional[
            str
        ] = None,
        in_: typing.Optional[
            typing.Union[
                str,
                str
            ]
        ] = None,
        description: typing.Optional[
            str
        ] = None,
        required: typing.Optional[
            bool
        ] = None,
        deprecated: typing.Optional[
            bool
        ] = None,
        allow_empty_value: typing.Optional[
            bool
        ] = None,
        style: typing.Optional[
            str
        ] = None,
        explode: typing.Optional[
            bool
        ] = None,
        allow_reserved: typing.Optional[
            bool
        ] = None,
        schema: typing.Optional[
            typing.Union[
                "Reference",
                "Schema"
            ]
        ] = None,
        example: typing.Optional[
            typing.Any
        ] = None,
        examples: typing.Optional[
            typing.Mapping[
                str,
                typing.Union[
                    "Reference",
                    "Example"
                ]
            ]
        ] = None,
        content: typing.Optional[
            typing.Mapping[
                str,
                "MediaType"
            ]
        ] = None,
        type_: typing.Optional[
            str
        ] = None,
        default: typing.Optional[
            typing.Any
        ] = None,
        maximum: typing.Optional[
            typing.Union[
                float,
                int,
                decimal.Decimal
            ]
        ] = None,
        exclusive_maximum: typing.Optional[
            bool
        ] = None,
        minimum: typing.Optional[
            typing.Union[
                float,
                int,
                decimal.Decimal
            ]
        ] = None,
        exclusive_minimum: typing.Optional[
            bool
        ] = None,
        max_length: typing.Optional[
            int
        ] = None,
        min_length: typing.Optional[
            int
        ] = None,
        pattern: typing.Optional[
            str
        ] = None,
        max_items: typing.Optional[
            int
        ] = None,
        min_items: typing.Optional[
            int
        ] = None,
        unique_items: typing.Optional[
            bool
        ] = None,
        enum: typing.Optional[
            typing.Sequence[
                typing.Optional[sob.abc.MarshallableTypes]
            ]
        ] = None,
        format_: typing.Optional[
            str
        ] = None,
        collection_format: typing.Optional[
            str
        ] = None,
        items: typing.Optional[
            "Items"
        ] = None,
        multiple_of: typing.Optional[
            typing.Union[
                float,
                int,
                decimal.Decimal
            ]
        ] = None
    ) -> None:
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
        self.format_ = format_
        self.collection_format = collection_format
        self.items = items
        self.multiple_of = multiple_of
        super().__init__(_data)


class Parameters(sob.model.Dictionary):

    def __init__(
        self,
        items: typing.Union[
            sob.abc.Dictionary,
            typing.Mapping[
                str,
                typing.Union[
                    "Reference",
                    "Parameter"
                ]
            ],
            typing.Iterable[
                typing.Tuple[
                    str,
                    typing.Union[
                        "Reference",
                        "Parameter"
                    ]
                ]
            ],
            sob.abc.Readable,
            str,
            bytes,
            None,
        ] = None,
    ) -> None:
        super().__init__(items)


class PathItem(ExtensibleObject):
    """
    https://bit.ly/3Lt8wCO
    """

    def __init__(
        self,
        _data: typing.Union[
            sob.abc.Dictionary,
            typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ],
            typing.Iterable[
                typing.Tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ],
            sob.abc.Readable,
            str,
            bytes,
            None,
        ] = None,
        summary: typing.Optional[
            str
        ] = None,
        description: typing.Optional[
            str
        ] = None,
        get: typing.Optional[
            "Operation"
        ] = None,
        put: typing.Optional[
            "Operation"
        ] = None,
        post: typing.Optional[
            "Operation"
        ] = None,
        delete: typing.Optional[
            "Operation"
        ] = None,
        options: typing.Optional[
            "Operation"
        ] = None,
        head: typing.Optional[
            "Operation"
        ] = None,
        patch: typing.Optional[
            "Operation"
        ] = None,
        trace: typing.Optional[
            "Operation"
        ] = None,
        servers: typing.Optional[
            typing.Sequence[
                "Server"
            ]
        ] = None,
        parameters: typing.Optional[
            typing.Sequence[
                typing.Union[
                    "Reference",
                    "Parameter"
                ]
            ]
        ] = None
    ) -> None:
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
        super().__init__(_data)


class Paths(sob.model.Dictionary):

    def __init__(
        self,
        items: typing.Union[
            sob.abc.Dictionary,
            typing.Mapping[
                str,
                "PathItem"
            ],
            typing.Iterable[
                typing.Tuple[
                    str,
                    "PathItem"
                ]
            ],
            sob.abc.Readable,
            str,
            bytes,
            None,
        ] = None,
    ) -> None:
        super().__init__(items)


class Properties(sob.model.Dictionary):

    def __init__(
        self,
        items: typing.Union[
            sob.abc.Dictionary,
            typing.Mapping[
                str,
                typing.Union[
                    "Reference",
                    "Schema"
                ]
            ],
            typing.Iterable[
                typing.Tuple[
                    str,
                    typing.Union[
                        "Reference",
                        "Schema"
                    ]
                ]
            ],
            sob.abc.Readable,
            str,
            bytes,
            None,
        ] = None,
    ) -> None:
        super().__init__(items)


class Reference(ExtensibleObject):
    """
    https://bit.ly/3IWdLJt
    """

    def __init__(
        self,
        _data: typing.Union[
            sob.abc.Dictionary,
            typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ],
            typing.Iterable[
                typing.Tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ],
            sob.abc.Readable,
            str,
            bytes,
            None,
        ] = None,
        ref: typing.Optional[
            str
        ] = None,
        summary: typing.Optional[
            str
        ] = None,
        description: typing.Optional[
            str
        ] = None
    ) -> None:
        self.ref = ref
        self.summary = summary
        self.description = description
        super().__init__(_data)


class RequestBodies(sob.model.Dictionary):

    def __init__(
        self,
        items: typing.Union[
            sob.abc.Dictionary,
            typing.Mapping[
                str,
                typing.Union[
                    "Reference",
                    "RequestBody"
                ]
            ],
            typing.Iterable[
                typing.Tuple[
                    str,
                    typing.Union[
                        "Reference",
                        "RequestBody"
                    ]
                ]
            ],
            sob.abc.Readable,
            str,
            bytes,
            None,
        ] = None,
    ) -> None:
        super().__init__(items)


class RequestBody(ExtensibleObject):

    def __init__(
        self,
        _data: typing.Union[
            sob.abc.Dictionary,
            typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ],
            typing.Iterable[
                typing.Tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ],
            sob.abc.Readable,
            str,
            bytes,
            None,
        ] = None,
        description: typing.Optional[
            str
        ] = None,
        content: typing.Optional[
            typing.Mapping[
                str,
                "MediaType"
            ]
        ] = None,
        required: typing.Optional[
            bool
        ] = None
    ) -> None:
        self.description = description
        self.content = content
        self.required = required
        super().__init__(_data)


class Response(ExtensibleObject):
    """
    https://bit.ly/3qTo3Ed

    Properties:

    - description (str): A short description of the response. `CommonMark
      syntax<http://spec.commonmark.org/>` may be used for rich text
      representation.
    - headers ({str:Header|Reference}): Maps a header name to its
      definition (mappings are case-insensitive).
    - content ({str:MediaType|Reference}): A mapping of media value_types to
      `MediaType` instances describing potential payloads.
    - links ({str:Link_|Reference}): A map of operations links that can be
      followed from the response.

    ...for 2x compatibility:

    - schema (oapi.oas.mode.Schema)
    """

    def __init__(
        self,
        _data: typing.Union[
            sob.abc.Dictionary,
            typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ],
            typing.Iterable[
                typing.Tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ],
            sob.abc.Readable,
            str,
            bytes,
            None,
        ] = None,
        description: typing.Optional[
            str
        ] = None,
        schema: typing.Optional[
            typing.Union[
                "Reference",
                "Schema"
            ]
        ] = None,
        headers: typing.Optional[
            typing.Mapping[
                str,
                typing.Union[
                    "Reference",
                    "Header"
                ]
            ]
        ] = None,
        examples: typing.Optional[
            typing.Mapping[
                str,
                typing.Optional[sob.abc.MarshallableTypes]
            ]
        ] = None,
        content: typing.Optional[
            typing.Mapping[
                str,
                typing.Union[
                    "Reference",
                    "MediaType"
                ]
            ]
        ] = None,
        links: typing.Optional[
            typing.Mapping[
                str,
                typing.Union[
                    "Reference",
                    "Link_"
                ]
            ]
        ] = None
    ) -> None:
        self.description = description
        self.schema = schema
        self.headers = headers
        self.examples = examples
        self.content = content
        self.links = links
        super().__init__(_data)


class Responses(sob.model.Dictionary):

    def __init__(
        self,
        items: typing.Union[
            sob.abc.Dictionary,
            typing.Mapping[
                str,
                typing.Union[
                    typing.Union[
                        "Reference",
                        "Response"
                    ],
                    "Response"
                ]
            ],
            typing.Iterable[
                typing.Tuple[
                    str,
                    typing.Union[
                        typing.Union[
                            "Reference",
                            "Response"
                        ],
                        "Response"
                    ]
                ]
            ],
            sob.abc.Readable,
            str,
            bytes,
            None,
        ] = None,
    ) -> None:
        super().__init__(items)


class Schema(ExtensibleObject):
    """
    https://bit.ly/3JZJWsP
    http://json-schema.org

    Properties:

    - title (str)
    - description (str)
    - multiple_of (int|float): The numeric value this schema describes
      should be divisible by this number.
    - maximum (int|float): The number this schema describes should be less
      than or equal to this value, or less than
      this value, depending on the value of `exclusive_maximum`.
    - exclusive_maximum (bool): If `True`, the numeric instance described
      by this schema must be *less than*
      `maximum`. If `False`, the numeric instance described by this schema
      can be less than or *equal to*
      `maximum`.
    - minimum (int|float): The number this schema describes should be
      greater than or equal to this value, or greater
      than this value, depending on the value of `exclusive_minimum`.
    - exclusive_minimum (bool): If `True`, the numeric instance described
      by this schema must be *greater than* `minimum`. If `False`, the
      numeric instance described by this schema can be greater than or
      *equal to* `minimum`.
    - max_length (int): The number of characters in the string instance
      described by this schema must be less than,
      or equal to, the value of this property.
    - min_length (int): The number of characters in the string instance
      described by this schema must be greater
      than, or equal to, the value of this property.
    - pattern (str): The string instance described by this schema should
      match this regular expression (ECMA 262).
    - items (Reference|Schema|[Schema]):
      - If `items` is a sub-schema--each item in the array instance
        described by this schema should be valid as described by this
        sub-schema.
      - If `items` is a sequence of sub-schemas, the array instance
        described by this schema should be equal in length to this
        sequence, and each value should be valid as described by the
        sub-schema at the corresponding index within this sequence of
        sub-schemas.
    - max_items (int): The array instance described by this schema should
      contain no more than this number of items.
    - min_items (int): The array instance described by this schema should
      contain at least this number of items.
    - unique_items (bool): The array instance described by this schema
      should contain only unique items.
    - max_properties (int)
    - min_properties (int)
    - properties ({str:Schema}): Any properties of the object
      instance described by this schema which correspond to a name in
      this mapping should be valid as described by the sub-schema
      corresponding to that name.
    - additional_properties (bool|Schema):
      - If `additional_properties` is `True`--sob.properties may be
      present in the object described by this schema with names which
      do not match those in `sob.properties`.
      - If `additional_properties` is `False`--all sob.properties present
      in the object described by this schema must correspond to a
      property matched in either `sob.properties`.
    - enum ([Any]): The value/instance described by this schema should be
      among those in this sequence.
    - type_ (str): See https://bit.ly/35xdE9N, https://bit.ly/3j3iJJP and
      https://bit.ly/3DzLF60
      - "boolean"
      - "object"
      - "array"
      - "number"
      - "string"
      - "integer"
      - "file"
    - format_ (str): See https://bit.ly/35xdE9N, https://bit.ly/3j3iJJP and
      https://bit.ly/3DzLF60
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
    - all_of ([Schema]): The value/instance described by the schema should
      *also* be valid as
      described by all sub-schemas in this sequence.
    - any_of ([Schema]): The value/instance described by the schema should
      *also* be valid as
      described in at least one of the sub-schemas in this sequence.
    - one_of ([Schema]): The value/instance described by the schema should
      *also* be valid as
      described in one (but *only* one) of the sub-schemas in this
      sequence.
    - is_not (Schema): The value/instance described by this schema should *
      not* be valid as described by this
      sub-schema.
    - definitions ({str:Schema}): A dictionary of sub-schemas, stored for
      the purpose of referencing these sub-schemas elsewhere in the schema.
    - required ([str]): A list of attributes which must be present on the
      object instance described by this schema.
    - default (Any): The value presumed if the value/instance described by
      this schema is absent.

    The following sob.properties are specific to OpenAPI (not part of the
    core `JSON Schema <http://json-schema.org>`):

    - nullable (bool): If `True`, the value/instance described by this
      schema may be a null value (`None`).
    - discriminator (Discriminator): Adds support for polymorphism.
    - read_only (bool): If `True`, the property described may be returned
      as part of a response, but should not be part of a request.
    - write_only (bool): If `True`, the property described may be sent as
      part of a request, but should not be returned as part of a response.
    - xml (XML): Provides additional information describing XML
      representation of the property described by this schema.
    - external_docs (ExternalDocumentation)
    - example (Any)
    - definitions (Any)
    - depracated (bool): If `True`, the property or instance described by
      this schema should be phased out, as if will no longer be supported
      in future versions.
    """

    def __init__(
        self,
        _data: typing.Union[
            sob.abc.Dictionary,
            typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ],
            typing.Iterable[
                typing.Tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ],
            sob.abc.Readable,
            str,
            bytes,
            None,
        ] = None,
        title: typing.Optional[
            str
        ] = None,
        description: typing.Optional[
            str
        ] = None,
        multiple_of: typing.Optional[
            typing.Union[
                float,
                int,
                decimal.Decimal
            ]
        ] = None,
        maximum: typing.Optional[
            typing.Union[
                float,
                int,
                decimal.Decimal
            ]
        ] = None,
        exclusive_maximum: typing.Optional[
            bool
        ] = None,
        minimum: typing.Optional[
            typing.Union[
                float,
                int,
                decimal.Decimal
            ]
        ] = None,
        exclusive_minimum: typing.Optional[
            bool
        ] = None,
        max_length: typing.Optional[
            int
        ] = None,
        min_length: typing.Optional[
            int
        ] = None,
        pattern: typing.Optional[
            str
        ] = None,
        max_items: typing.Optional[
            int
        ] = None,
        min_items: typing.Optional[
            int
        ] = None,
        unique_items: typing.Optional[
            bool
        ] = None,
        items: typing.Optional[
            typing.Union[
                "Reference",
                "Schema",
                typing.Sequence[
                    typing.Union[
                        "Reference",
                        "Schema"
                    ]
                ]
            ]
        ] = None,
        max_properties: typing.Optional[
            int
        ] = None,
        min_properties: typing.Optional[
            int
        ] = None,
        properties: typing.Optional[
            "Properties"
        ] = None,
        additional_properties: typing.Optional[
            typing.Union[
                "Reference",
                "Schema",
                bool
            ]
        ] = None,
        enum: typing.Optional[
            typing.Sequence[
                typing.Optional[sob.abc.MarshallableTypes]
            ]
        ] = None,
        type_: typing.Optional[
            str
        ] = None,
        format_: typing.Optional[
            str
        ] = None,
        required: typing.Optional[
            typing.Sequence[
                str
            ]
        ] = None,
        all_of: typing.Optional[
            typing.Sequence[
                typing.Union[
                    "Reference",
                    "Schema"
                ]
            ]
        ] = None,
        any_of: typing.Optional[
            typing.Sequence[
                typing.Union[
                    "Reference",
                    "Schema"
                ]
            ]
        ] = None,
        one_of: typing.Optional[
            typing.Sequence[
                typing.Union[
                    "Reference",
                    "Schema"
                ]
            ]
        ] = None,
        is_not: typing.Optional[
            typing.Union[
                "Reference",
                "Schema"
            ]
        ] = None,
        definitions: typing.Optional[
            typing.Any
        ] = None,
        default: typing.Optional[
            typing.Any
        ] = None,
        discriminator: typing.Optional[
            typing.Union[
                "Discriminator",
                str
            ]
        ] = None,
        read_only: typing.Optional[
            bool
        ] = None,
        write_only: typing.Optional[
            bool
        ] = None,
        xml: typing.Optional[
            "XML"
        ] = None,
        external_docs: typing.Optional[
            "ExternalDocumentation"
        ] = None,
        example: typing.Optional[
            typing.Any
        ] = None,
        deprecated: typing.Optional[
            bool
        ] = None,
        links: typing.Optional[
            typing.Sequence[
                "Link"
            ]
        ] = None,
        nullable: typing.Optional[
            bool
        ] = None
    ) -> None:
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
        self.max_items = max_items
        self.min_items = min_items
        self.unique_items = unique_items
        self.items = items
        self.max_properties = max_properties
        self.min_properties = min_properties
        self.properties = properties
        self.additional_properties = additional_properties
        self.enum = enum
        self.type_ = type_
        self.format_ = format_
        self.required = required
        self.all_of = all_of
        self.any_of = any_of
        self.one_of = one_of
        self.is_not = is_not
        self.definitions = definitions
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
        super().__init__(_data)


class Schemas(sob.model.Dictionary):

    def __init__(
        self,
        items: typing.Union[
            sob.abc.Dictionary,
            typing.Mapping[
                str,
                typing.Union[
                    "Reference",
                    "Schema"
                ]
            ],
            typing.Iterable[
                typing.Tuple[
                    str,
                    typing.Union[
                        "Reference",
                        "Schema"
                    ]
                ]
            ],
            sob.abc.Readable,
            str,
            bytes,
            None,
        ] = None,
    ) -> None:
        super().__init__(items)


class SecurityRequirement(sob.model.Dictionary):

    def __init__(
        self,
        items: typing.Union[
            sob.abc.Dictionary,
            typing.Mapping[
                str,
                typing.Sequence[
                    str
                ]
            ],
            typing.Iterable[
                typing.Tuple[
                    str,
                    typing.Sequence[
                        str
                    ]
                ]
            ],
            sob.abc.Readable,
            str,
            bytes,
            None,
        ] = None,
    ) -> None:
        super().__init__(items)


class SecurityScheme(ExtensibleObject):
    """
    Properties (https://bit.ly/3qRtjIm):

    - type_ (str): https://tools.ietf.org/html/rfc7235#section-4
    - description (str)
    - name (str)
    - in_ (str)
    - scheme (str)
    - bearer_format (str)
    - flows (OAuthFlows)
    - open_id_connect_url (str)
    - scopes

    OpenAPI 2x Only Properties (https://bit.ly/3Jpx3aA):

    - flow (str): "implicit", "password", "application" or "accessCode"
    - authorization_url (str)
    - token_url (str)
    """

    def __init__(
        self,
        _data: typing.Union[
            sob.abc.Dictionary,
            typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ],
            typing.Iterable[
                typing.Tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ],
            sob.abc.Readable,
            str,
            bytes,
            None,
        ] = None,
        type_: typing.Optional[
            str
        ] = None,
        description: typing.Optional[
            str
        ] = None,
        name: typing.Optional[
            str
        ] = None,
        in_: typing.Optional[
            typing.Union[
                str,
                str
            ]
        ] = None,
        scheme: typing.Optional[
            str
        ] = None,
        bearer_format: typing.Optional[
            str
        ] = None,
        flows: typing.Optional[
            "OAuthFlows"
        ] = None,
        open_id_connect_url: typing.Optional[
            str
        ] = None,
        flow: typing.Optional[
            str
        ] = None,
        authorization_url: typing.Optional[
            str
        ] = None,
        token_url: typing.Optional[
            str
        ] = None,
        scopes: typing.Optional[
            typing.Mapping[
                str,
                str
            ]
        ] = None
    ) -> None:
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
        self.token_url = token_url
        self.scopes = scopes
        super().__init__(_data)


class SecuritySchemes(sob.model.Dictionary):

    def __init__(
        self,
        items: typing.Union[
            sob.abc.Dictionary,
            typing.Mapping[
                str,
                typing.Union[
                    "Reference",
                    "SecurityScheme"
                ]
            ],
            typing.Iterable[
                typing.Tuple[
                    str,
                    typing.Union[
                        "Reference",
                        "SecurityScheme"
                    ]
                ]
            ],
            sob.abc.Readable,
            str,
            bytes,
            None,
        ] = None,
    ) -> None:
        super().__init__(items)


class Server(ExtensibleObject):
    """
    https://bit.ly/3iTqBxv
    """

    def __init__(
        self,
        _data: typing.Union[
            sob.abc.Dictionary,
            typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ],
            typing.Iterable[
                typing.Tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ],
            sob.abc.Readable,
            str,
            bytes,
            None,
        ] = None,
        url: typing.Optional[
            str
        ] = None,
        description: typing.Optional[
            str
        ] = None,
        variables: typing.Optional[
            typing.Mapping[
                str,
                "ServerVariable"
            ]
        ] = None
    ) -> None:
        self.url = url
        self.description = description
        self.variables = variables
        super().__init__(_data)


class ServerVariable(ExtensibleObject):
    """
    https://bit.ly/3iYikZ7
    """

    def __init__(
        self,
        _data: typing.Union[
            sob.abc.Dictionary,
            typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ],
            typing.Iterable[
                typing.Tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ],
            sob.abc.Readable,
            str,
            bytes,
            None,
        ] = None,
        enum: typing.Optional[
            typing.Sequence[
                str
            ]
        ] = None,
        default: typing.Optional[
            str
        ] = None,
        description: typing.Optional[
            str
        ] = None
    ) -> None:
        self.enum = enum
        self.default = default
        self.description = description
        super().__init__(_data)


class Tag(ExtensibleObject):
    """
    https://bit.ly/36K2JtU
    """

    def __init__(
        self,
        _data: typing.Union[
            sob.abc.Dictionary,
            typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ],
            typing.Iterable[
                typing.Tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ],
            sob.abc.Readable,
            str,
            bytes,
            None,
        ] = None,
        name: typing.Optional[
            str
        ] = None,
        description: typing.Optional[
            str
        ] = None,
        external_docs: typing.Optional[
            "ExternalDocumentation"
        ] = None
    ) -> None:
        self.name = name
        self.description = description
        self.external_docs = external_docs
        super().__init__(_data)


class XML(ExtensibleObject):
    """
    https://bit.ly/35sxt1Y

    Properties:

    - name (str): The element name.
    - name_space (str): The *absolute* URI of a namespace.
    - prefix (str): The prefix to be used with the name to reference the
      name-space.
    - attribute (bool): If `True`, the property described is an attribute
      rather than a sub-element.
    - wrapped (bool): If `True`, an array instance described by the schema
      will be wrapped by a tag (named according to the parent element's
      property, while `name` refers to the child element name).
    """

    def __init__(
        self,
        _data: typing.Union[
            sob.abc.Dictionary,
            typing.Mapping[
                str,
                sob.abc.MarshallableTypes
            ],
            typing.Iterable[
                typing.Tuple[
                    str,
                    sob.abc.MarshallableTypes
                ]
            ],
            sob.abc.Readable,
            str,
            bytes,
            None,
        ] = None,
        name: typing.Optional[
            str
        ] = None,
        name_space: typing.Optional[
            str
        ] = None,
        prefix: typing.Optional[
            str
        ] = None,
        attribute: typing.Optional[
            bool
        ] = None,
        wrapped: typing.Optional[
            bool
        ] = None
    ) -> None:
        self.name = name
        self.name_space = name_space
        self.prefix = prefix
        self.attribute = attribute
        self.wrapped = wrapped
        super().__init__(_data)


sob.meta.dictionary_writable(  # type: ignore
    Callback
).value_types = sob.types.MutableTypes([
    PathItem
])
sob.meta.dictionary_writable(  # type: ignore
    Callbacks
).value_types = sob.types.MutableTypes([
    Reference,
    Callback
])
sob.meta.object_writable(  # type: ignore
    Components
).properties = sob.meta.Properties([
    (
        'schemas',
        sob.properties.Property(
            types=sob.types.MutableTypes([
                Schemas
            ])
        )
    ),
    (
        'responses',
        sob.properties.Property(
            types=sob.types.MutableTypes([
                Responses
            ])
        )
    ),
    (
        'parameters',
        sob.properties.Property(
            types=sob.types.MutableTypes([
                Parameters
            ])
        )
    ),
    (
        'examples',
        sob.properties.Property(
            types=sob.types.MutableTypes([
                Examples
            ])
        )
    ),
    (
        'request_bodies',
        sob.properties.Property(
            name="requestBodies",
            types=sob.types.MutableTypes([
                RequestBodies
            ])
        )
    ),
    (
        'headers',
        sob.properties.Property(
            types=sob.types.MutableTypes([
                Headers
            ])
        )
    ),
    (
        'security_schemes',
        sob.properties.Property(
            name="securitySchemes",
            types=sob.types.MutableTypes([
                SecuritySchemes
            ])
        )
    ),
    (
        'links',
        sob.properties.Property(
            types=sob.types.MutableTypes([
                Links
            ])
        )
    ),
    (
        'callbacks',
        sob.properties.Property(
            types=sob.types.MutableTypes([
                Callbacks
            ])
        )
    )
])
sob.meta.object_writable(  # type: ignore
    Contact
).properties = sob.meta.Properties([
    ('name', sob.properties.String()),
    ('url', sob.properties.String()),
    ('email', sob.properties.String())
])
sob.meta.dictionary_writable(  # type: ignore
    Definitions
).value_types = sob.types.MutableTypes([
    Schema
])
sob.meta.object_writable(  # type: ignore
    Discriminator
).properties = sob.meta.Properties([
    (
        'property_name',
        sob.properties.String(
            name="propertyName",
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'mapping',
        sob.properties.Dictionary(
            value_types=sob.types.MutableTypes([
                str
            ]),
            versions=(
                'openapi>=3.0',
            )
        )
    )
])
sob.meta.object_writable(  # type: ignore
    Encoding
).properties = sob.meta.Properties([
    (
        'content_type',
        sob.properties.String(
            name="contentType"
        )
    ),
    (
        'headers',
        sob.properties.Dictionary(
            value_types=sob.types.MutableTypes([
                Reference,
                Header
            ])
        )
    ),
    ('style', sob.properties.String()),
    ('explode', sob.properties.Boolean()),
    (
        'allow_reserved',
        sob.properties.Boolean(
            name="allowReserved"
        )
    )
])
sob.meta.object_writable(  # type: ignore
    Example
).properties = sob.meta.Properties([
    (
        'summary',
        sob.properties.String(
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'description',
        sob.properties.String(
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'value',
        sob.properties.Property(
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'external_value',
        sob.properties.String(
            name="externalValue",
            versions=(
                'openapi>=3.0',
            )
        )
    )
])
sob.meta.dictionary_writable(  # type: ignore
    Examples
).value_types = sob.types.MutableTypes([
    Reference,
    Example
])
sob.meta.object_writable(  # type: ignore
    ExternalDocumentation
).properties = sob.meta.Properties([
    ('description', sob.properties.String()),
    (
        'url',
        sob.properties.String(
            required=True
        )
    )
])
sob.meta.object_writable(  # type: ignore
    Header
).properties = sob.meta.Properties([
    ('description', sob.properties.String()),
    (
        'required',
        sob.properties.Boolean(
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'deprecated',
        sob.properties.Boolean(
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'allow_empty_value',
        sob.properties.Boolean(
            name="allowEmptyValue",
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'style',
        sob.properties.String(
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'explode',
        sob.properties.Boolean(
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'allow_reserved',
        sob.properties.Boolean(
            name="allowReserved",
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'schema',
        sob.properties.Property(
            types=sob.types.MutableTypes([
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
        sob.properties.Property(
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'examples',
        sob.properties.Dictionary(
            value_types=sob.types.MutableTypes([
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
        sob.properties.Dictionary(
            value_types=sob.types.MutableTypes([
                MediaType
            ]),
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'type_',
        sob.properties.Enumerated(
            name="type",
            types=sob.types.Types([
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
        sob.properties.Property(
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'maximum',
        sob.properties.Number(
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'exclusive_maximum',
        sob.properties.Boolean(
            name="exclusiveMaximum",
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'minimum',
        sob.properties.Number(
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'exclusive_minimum',
        sob.properties.Boolean(
            name="exclusiveMinimum",
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'max_length',
        sob.properties.Integer(
            name="maxLength",
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'min_length',
        sob.properties.Integer(
            name="minLength",
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'pattern',
        sob.properties.String(
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'max_items',
        sob.properties.Integer(
            name="maxItems",
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'min_items',
        sob.properties.Integer(
            name="minItems",
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'unique_items',
        sob.properties.Boolean(
            name="uniqueItems",
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'enum',
        sob.properties.Array(
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'format_',
        sob.properties.String(
            name="format",
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'collection_format',
        sob.properties.Enumerated(
            name="collectionFormat",
            types=sob.types.Types([
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
        sob.properties.Property(
            types=sob.types.MutableTypes([
                Items
            ]),
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'multiple_of',
        sob.properties.Number(
            name="multipleOf",
            versions=(
                'openapi<3.0',
            )
        )
    )
])
sob.meta.dictionary_writable(  # type: ignore
    Headers
).value_types = sob.types.MutableTypes([
    Reference,
    Header
])
sob.meta.object_writable(  # type: ignore
    Info
).properties = sob.meta.Properties([
    (
        'title',
        sob.properties.String(
            required=True
        )
    ),
    ('description', sob.properties.String()),
    (
        'terms_of_service',
        sob.properties.String(
            name="termsOfService"
        )
    ),
    (
        'contact',
        sob.properties.Property(
            types=sob.types.MutableTypes([
                Contact
            ])
        )
    ),
    (
        'license_',
        sob.properties.Property(
            name="license",
            types=sob.types.MutableTypes([
                License
            ])
        )
    ),
    (
        'version',
        sob.properties.String(
            required=True
        )
    )
])
sob.meta.object_writable(  # type: ignore
    Items
).properties = sob.meta.Properties([
    (
        'type_',
        sob.properties.Enumerated(
            name="type",
            types=sob.types.Types([
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
        sob.properties.String(
            name="format",
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'items',
        sob.properties.Property(
            types=sob.types.MutableTypes([
                Items
            ]),
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'collection_format',
        sob.properties.Enumerated(
            name="collectionFormat",
            types=sob.types.Types([
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
    ('default', sob.properties.Property()),
    (
        'maximum',
        sob.properties.Number(
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'exclusive_maximum',
        sob.properties.Boolean(
            name="exclusiveMaximum",
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'minimum',
        sob.properties.Number(
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'exclusive_minimum',
        sob.properties.Boolean(
            name="exclusiveMinimum",
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'max_length',
        sob.properties.Integer(
            name="maxLength",
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'min_length',
        sob.properties.Integer(
            name="minLength",
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'pattern',
        sob.properties.String(
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'max_items',
        sob.properties.Integer(
            name="maxItems",
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'min_items',
        sob.properties.Integer(
            name="minItems",
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'unique_items',
        sob.properties.Boolean(
            name="uniqueItems",
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'enum',
        sob.properties.Array(
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'multiple_of',
        sob.properties.Number(
            name="multipleOf",
            versions=(
                'openapi<3.0',
            )
        )
    )
])
sob.meta.object_writable(  # type: ignore
    License
).properties = sob.meta.Properties([
    (
        'name',
        sob.properties.String(
            required=True
        )
    ),
    ('url', sob.properties.String())
])
sob.meta.object_writable(  # type: ignore
    Link
).properties = sob.meta.Properties([
    ('rel', sob.properties.String()),
    ('href', sob.properties.String())
])
sob.meta.object_writable(  # type: ignore
    Link_
).properties = sob.meta.Properties([
    (
        'operation_ref',
        sob.properties.String(
            name="operationRef",
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'operation_id',
        sob.properties.String(
            name="operationId",
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'parameters',
        sob.properties.Dictionary(
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'request_body',
        sob.properties.Property(
            name="requestBody",
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'description',
        sob.properties.String(
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'server',
        sob.properties.Property(
            types=sob.types.MutableTypes([
                Server
            ]),
            versions=(
                'openapi>=3.0',
            )
        )
    )
])
sob.meta.dictionary_writable(  # type: ignore
    Links
).value_types = sob.types.MutableTypes([
    Reference,
    Link_
])
sob.meta.object_writable(  # type: ignore
    MediaType
).properties = sob.meta.Properties([
    (
        'schema',
        sob.properties.Property(
            types=sob.types.MutableTypes([
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
        sob.properties.Property(
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'examples',
        sob.properties.Dictionary(
            value_types=sob.types.MutableTypes([
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
        sob.properties.Dictionary(
            value_types=sob.types.MutableTypes([
                Reference,
                Encoding
            ]),
            versions=(
                'openapi>=3.0',
            )
        )
    )
])
sob.meta.object_writable(  # type: ignore
    OAuthFlow
).properties = sob.meta.Properties([
    ('authorization_url', sob.properties.String()),
    (
        'token_url',
        sob.properties.String(
            name="tokenUrl"
        )
    ),
    (
        'refresh_url',
        sob.properties.String(
            name="refreshUrl"
        )
    ),
    (
        'scopes',
        sob.properties.Dictionary(
            value_types=sob.types.MutableTypes([
                str
            ])
        )
    )
])
sob.meta.object_writable(  # type: ignore
    OAuthFlows
).properties = sob.meta.Properties([
    (
        'implicit',
        sob.properties.Property(
            types=sob.types.MutableTypes([
                OAuthFlow
            ]),
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'password',
        sob.properties.Property(
            types=sob.types.MutableTypes([
                OAuthFlow
            ]),
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'client_credentials',
        sob.properties.Property(
            name="clientCredentials",
            types=sob.types.MutableTypes([
                OAuthFlow
            ]),
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'authorization_code',
        sob.properties.Property(
            name="authorizationCode",
            types=sob.types.MutableTypes([
                OAuthFlow
            ]),
            versions=(
                'openapi>=3.0',
            )
        )
    )
])
sob.meta.object_writable(  # type: ignore
    OpenAPI
).properties = sob.meta.Properties([
    (
        'openapi',
        sob.properties.String(
            required=True,
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'info',
        sob.properties.Property(
            required=True,
            types=sob.types.MutableTypes([
                Info
            ])
        )
    ),
    (
        'json_schema_dialect',
        sob.properties.String(
            name="jsonSchemaDialect",
            versions=(
                'openapi>=3.1',
            )
        )
    ),
    (
        'host',
        sob.properties.String(
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'servers',
        sob.properties.Array(
            item_types=sob.types.MutableTypes([
                Server
            ]),
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'base_path',
        sob.properties.String(
            name="basePath",
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'schemes',
        sob.properties.Array(
            item_types=sob.types.MutableTypes([
                str
            ]),
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'tags',
        sob.properties.Array(
            item_types=sob.types.MutableTypes([
                Tag
            ])
        )
    ),
    (
        'paths',
        sob.properties.Property(
            required=True,
            types=sob.types.MutableTypes([
                Paths
            ])
        )
    ),
    (
        'components',
        sob.properties.Property(
            types=sob.types.MutableTypes([
                Components
            ]),
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'consumes',
        sob.properties.Array(
            item_types=sob.types.MutableTypes([
                str
            ]),
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'swagger',
        sob.properties.String(
            required=True,
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'definitions',
        sob.properties.Property(
            types=sob.types.MutableTypes([
                Definitions
            ]),
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'security_definitions',
        sob.properties.Property(
            name="securityDefinitions",
            types=sob.types.MutableTypes([
                SecuritySchemes
            ]),
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'produces',
        sob.properties.Array(
            item_types=sob.types.MutableTypes([
                str
            ]),
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'external_docs',
        sob.properties.Property(
            name="externalDocs",
            types=sob.types.MutableTypes([
                ExternalDocumentation
            ])
        )
    ),
    (
        'parameters',
        sob.properties.Dictionary(
            value_types=sob.types.MutableTypes([
                Parameter
            ]),
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'responses',
        sob.properties.Dictionary(
            value_types=sob.types.MutableTypes([
                Response
            ]),
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'security',
        sob.properties.Array(
            item_types=sob.types.MutableTypes([
                SecurityRequirement
            ])
        )
    )
])
sob.meta.object_writable(  # type: ignore
    Operation
).properties = sob.meta.Properties([
    (
        'tags',
        sob.properties.Array(
            item_types=sob.types.MutableTypes([
                str
            ])
        )
    ),
    ('summary', sob.properties.String()),
    ('description', sob.properties.String()),
    (
        'external_docs',
        sob.properties.Property(
            name="externalDocs",
            types=sob.types.MutableTypes([
                ExternalDocumentation
            ])
        )
    ),
    (
        'operation_id',
        sob.properties.String(
            name="operationId"
        )
    ),
    (
        'consumes',
        sob.properties.Array(
            item_types=sob.types.MutableTypes([
                str
            ]),
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'produces',
        sob.properties.Array(
            item_types=sob.types.MutableTypes([
                str
            ]),
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'parameters',
        sob.properties.Array(
            item_types=sob.types.MutableTypes([
                Reference,
                Parameter
            ])
        )
    ),
    (
        'request_body',
        sob.properties.Property(
            name="requestBody",
            types=sob.types.MutableTypes([
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
        sob.properties.Property(
            required=True,
            types=sob.types.MutableTypes([
                Responses
            ])
        )
    ),
    (
        'callbacks',
        sob.properties.Property(
            types=sob.types.MutableTypes([
                Callbacks
            ]),
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'schemes',
        sob.properties.Array(
            item_types=sob.types.MutableTypes([
                str
            ]),
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    ('deprecated', sob.properties.Boolean()),
    (
        'security',
        sob.properties.Array(
            item_types=sob.types.MutableTypes([
                SecurityRequirement
            ])
        )
    ),
    (
        'servers',
        sob.properties.Array(
            item_types=sob.types.MutableTypes([
                Server
            ]),
            versions=(
                'openapi>=3.0',
            )
        )
    )
])
sob.meta.object_writable(  # type: ignore
    Parameter
).properties = sob.meta.Properties([
    (
        'name',
        sob.properties.String(
            required=True
        )
    ),
    (
        'in_',
        sob.properties.Property(
            name="in",
            required=True,
            types=sob.types.Types([
                sob.properties.Enumerated(
                    types=sob.types.Types([
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
                sob.properties.Enumerated(
                    types=sob.types.Types([
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
    ('description', sob.properties.String()),
    ('required', sob.properties.Boolean()),
    ('deprecated', sob.properties.Boolean()),
    (
        'allow_empty_value',
        sob.properties.Boolean(
            name="allowEmptyValue"
        )
    ),
    (
        'style',
        sob.properties.String(
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'explode',
        sob.properties.Boolean(
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'allow_reserved',
        sob.properties.Boolean(
            name="allowReserved",
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'schema',
        sob.properties.Property(
            types=sob.types.MutableTypes([
                Reference,
                Schema
            ])
        )
    ),
    (
        'example',
        sob.properties.Property(
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'examples',
        sob.properties.Dictionary(
            value_types=sob.types.MutableTypes([
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
        sob.properties.Dictionary(
            value_types=sob.types.MutableTypes([
                MediaType
            ]),
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'type_',
        sob.properties.Enumerated(
            name="type",
            types=sob.types.Types([
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
        sob.properties.Property(
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'maximum',
        sob.properties.Number(
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'exclusive_maximum',
        sob.properties.Boolean(
            name="exclusiveMaximum",
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'minimum',
        sob.properties.Number(
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'exclusive_minimum',
        sob.properties.Boolean(
            name="exclusiveMinimum",
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'max_length',
        sob.properties.Integer(
            name="maxLength",
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'min_length',
        sob.properties.Integer(
            name="minLength",
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'pattern',
        sob.properties.String(
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'max_items',
        sob.properties.Integer(
            name="maxItems",
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'min_items',
        sob.properties.Integer(
            name="minItems",
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'unique_items',
        sob.properties.Boolean(
            name="uniqueItems",
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'enum',
        sob.properties.Array(
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'format_',
        sob.properties.String(
            name="format",
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'collection_format',
        sob.properties.Enumerated(
            name="collectionFormat",
            types=sob.types.Types([
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
        sob.properties.Property(
            types=sob.types.MutableTypes([
                Items
            ]),
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'multiple_of',
        sob.properties.Number(
            name="multipleOf",
            versions=(
                'openapi<3.0',
            )
        )
    )
])
sob.meta.dictionary_writable(  # type: ignore
    Parameters
).value_types = sob.types.MutableTypes([
    Reference,
    Parameter
])
sob.meta.object_writable(  # type: ignore
    PathItem
).properties = sob.meta.Properties([
    (
        'summary',
        sob.properties.String(
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'description',
        sob.properties.String(
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'get',
        sob.properties.Property(
            types=sob.types.MutableTypes([
                Operation
            ])
        )
    ),
    (
        'put',
        sob.properties.Property(
            types=sob.types.MutableTypes([
                Operation
            ])
        )
    ),
    (
        'post',
        sob.properties.Property(
            types=sob.types.MutableTypes([
                Operation
            ])
        )
    ),
    (
        'delete',
        sob.properties.Property(
            types=sob.types.MutableTypes([
                Operation
            ])
        )
    ),
    (
        'options',
        sob.properties.Property(
            types=sob.types.MutableTypes([
                Operation
            ])
        )
    ),
    (
        'head',
        sob.properties.Property(
            types=sob.types.MutableTypes([
                Operation
            ])
        )
    ),
    (
        'patch',
        sob.properties.Property(
            types=sob.types.MutableTypes([
                Operation
            ])
        )
    ),
    (
        'trace',
        sob.properties.Property(
            types=sob.types.MutableTypes([
                Operation
            ]),
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'servers',
        sob.properties.Array(
            item_types=sob.types.MutableTypes([
                Server
            ]),
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'parameters',
        sob.properties.Array(
            item_types=sob.types.MutableTypes([
                Reference,
                Parameter
            ])
        )
    )
])
sob.meta.dictionary_writable(  # type: ignore
    Paths
).value_types = sob.types.MutableTypes([
    PathItem
])
sob.meta.dictionary_writable(  # type: ignore
    Properties
).value_types = sob.types.MutableTypes([
    Reference,
    Schema
])
sob.meta.object_writable(  # type: ignore
    Reference
).properties = sob.meta.Properties([
    (
        'ref',
        sob.properties.String(
            name="$ref"
        )
    ),
    ('summary', sob.properties.String()),
    ('description', sob.properties.String())
])
sob.meta.dictionary_writable(  # type: ignore
    RequestBodies
).value_types = sob.types.MutableTypes([
    Reference,
    RequestBody
])
sob.meta.object_writable(  # type: ignore
    RequestBody
).properties = sob.meta.Properties([
    (
        'description',
        sob.properties.String(
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'content',
        sob.properties.Dictionary(
            value_types=sob.types.MutableTypes([
                MediaType
            ]),
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'required',
        sob.properties.Boolean(
            versions=(
                'openapi>=3.0',
            )
        )
    )
])
sob.meta.object_writable(  # type: ignore
    Response
).properties = sob.meta.Properties([
    ('description', sob.properties.String()),
    (
        'schema',
        sob.properties.Property(
            types=sob.types.MutableTypes([
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
        sob.properties.Dictionary(
            value_types=sob.types.MutableTypes([
                Reference,
                Header
            ])
        )
    ),
    (
        'examples',
        sob.properties.Dictionary(
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'content',
        sob.properties.Dictionary(
            value_types=sob.types.MutableTypes([
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
        sob.properties.Dictionary(
            value_types=sob.types.MutableTypes([
                Reference,
                Link_
            ]),
            versions=(
                'openapi>=3.0',
            )
        )
    )
])
sob.meta.dictionary_writable(  # type: ignore
    Responses
).value_types = sob.types.MutableTypes([
    sob.properties.Property(
        types=sob.types.MutableTypes([
            Reference,
            Response
        ]),
        versions=(
            'openapi>=3.0',
        )
    ),
    sob.properties.Property(
        types=sob.types.MutableTypes([
            Response
        ]),
        versions=(
            'openapi<3.0',
        )
    )
])
sob.meta.object_writable(  # type: ignore
    Schema
).properties = sob.meta.Properties([
    ('title', sob.properties.String()),
    ('description', sob.properties.String()),
    (
        'multiple_of',
        sob.properties.Number(
            name="multipleOf"
        )
    ),
    ('maximum', sob.properties.Number()),
    (
        'exclusive_maximum',
        sob.properties.Boolean(
            name="exclusiveMaximum"
        )
    ),
    ('minimum', sob.properties.Number()),
    (
        'exclusive_minimum',
        sob.properties.Boolean(
            name="exclusiveMinimum"
        )
    ),
    (
        'max_length',
        sob.properties.Integer(
            name="maxLength"
        )
    ),
    (
        'min_length',
        sob.properties.Integer(
            name="minLength"
        )
    ),
    ('pattern', sob.properties.String()),
    (
        'max_items',
        sob.properties.Integer(
            name="maxItems"
        )
    ),
    (
        'min_items',
        sob.properties.Integer(
            name="minItems"
        )
    ),
    (
        'unique_items',
        sob.properties.Boolean(
            name="uniqueItems"
        )
    ),
    (
        'items',
        sob.properties.Property(
            types=sob.types.MutableTypes([
                Reference,
                Schema,
                sob.properties.Array(
                    item_types=sob.types.MutableTypes([
                        Reference,
                        Schema
                    ])
                )
            ])
        )
    ),
    (
        'max_properties',
        sob.properties.Integer(
            name="maxProperties"
        )
    ),
    (
        'min_properties',
        sob.properties.Integer(
            name="minProperties"
        )
    ),
    (
        'properties',
        sob.properties.Property(
            types=sob.types.MutableTypes([
                Properties
            ])
        )
    ),
    (
        'additional_properties',
        sob.properties.Property(
            name="additionalProperties",
            types=sob.types.MutableTypes([
                Reference,
                Schema,
                bool
            ])
        )
    ),
    ('enum', sob.properties.Array()),
    (
        'type_',
        sob.properties.Property(
            name="type",
            types=sob.types.MutableTypes([
                sob.properties.Enumerated(
                    types=sob.types.Types([
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
        sob.properties.String(
            name="format"
        )
    ),
    (
        'required',
        sob.properties.Array(
            item_types=sob.types.MutableTypes([
                str
            ])
        )
    ),
    (
        'all_of',
        sob.properties.Array(
            item_types=sob.types.MutableTypes([
                Reference,
                Schema
            ]),
            name="allOf"
        )
    ),
    (
        'any_of',
        sob.properties.Array(
            item_types=sob.types.MutableTypes([
                Reference,
                Schema
            ]),
            name="anyOf"
        )
    ),
    (
        'one_of',
        sob.properties.Array(
            item_types=sob.types.MutableTypes([
                Reference,
                Schema
            ]),
            name="oneOf"
        )
    ),
    (
        'is_not',
        sob.properties.Property(
            name="isNot",
            types=sob.types.MutableTypes([
                Reference,
                Schema
            ])
        )
    ),
    ('definitions', sob.properties.Property()),
    ('default', sob.properties.Property()),
    (
        'discriminator',
        sob.properties.Property(
            types=sob.types.MutableTypes([
                sob.properties.Property(
                    types=sob.types.MutableTypes([
                        Discriminator
                    ]),
                    versions=(
                        'openapi>=3.0',
                    )
                ),
                sob.properties.Property(
                    types=sob.types.MutableTypes([
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
        sob.properties.Boolean(
            name="readOnly"
        )
    ),
    (
        'write_only',
        sob.properties.Boolean(
            name="writeOnly",
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'xml',
        sob.properties.Property(
            types=sob.types.MutableTypes([
                XML
            ])
        )
    ),
    (
        'external_docs',
        sob.properties.Property(
            types=sob.types.MutableTypes([
                ExternalDocumentation
            ])
        )
    ),
    ('example', sob.properties.Property()),
    (
        'deprecated',
        sob.properties.Boolean(
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'links',
        sob.properties.Array(
            item_types=sob.types.MutableTypes([
                Link
            ])
        )
    ),
    (
        'nullable',
        sob.properties.Boolean(
            versions=(
                'openapi>=3.0',
            )
        )
    )
])
sob.meta.dictionary_writable(  # type: ignore
    Schemas
).value_types = sob.types.MutableTypes([
    Reference,
    Schema
])
sob.meta.dictionary_writable(  # type: ignore
    SecurityRequirement
).value_types = sob.types.MutableTypes([
    sob.properties.Array(
        item_types=sob.types.MutableTypes([
            str
        ])
    )
])
sob.meta.object_writable(  # type: ignore
    SecurityScheme
).properties = sob.meta.Properties([
    (
        'type_',
        sob.properties.Enumerated(
            name="type",
            required=True,
            types=sob.types.Types([
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
    ('description', sob.properties.String()),
    ('name', sob.properties.String()),
    (
        'in_',
        sob.properties.Property(
            name="in",
            types=sob.types.MutableTypes([
                sob.properties.Enumerated(
                    types=sob.types.Types([
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
                sob.properties.Enumerated(
                    types=sob.types.Types([
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
        sob.properties.String(
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'bearer_format',
        sob.properties.String(
            name="bearerFormat"
        )
    ),
    (
        'flows',
        sob.properties.Property(
            types=sob.types.MutableTypes([
                OAuthFlows
            ]),
            versions=(
                'openapi>=3.0',
            )
        )
    ),
    (
        'open_id_connect_url',
        sob.properties.String(
            name="openIdConnectUrl"
        )
    ),
    (
        'flow',
        sob.properties.String(
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'authorization_url',
        sob.properties.String(
            name="authorizationUrl",
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'token_url',
        sob.properties.String(
            name="tokenUrl",
            versions=(
                'openapi<3.0',
            )
        )
    ),
    (
        'scopes',
        sob.properties.Dictionary(
            value_types=sob.types.MutableTypes([
                str
            ]),
            versions=(
                'openapi<3.0',
            )
        )
    )
])
sob.meta.dictionary_writable(  # type: ignore
    SecuritySchemes
).value_types = sob.types.MutableTypes([
    Reference,
    SecurityScheme
])
sob.meta.object_writable(  # type: ignore
    Server
).properties = sob.meta.Properties([
    (
        'url',
        sob.properties.String(
            required=True
        )
    ),
    ('description', sob.properties.String()),
    (
        'variables',
        sob.properties.Dictionary(
            value_types=sob.types.MutableTypes([
                ServerVariable
            ])
        )
    )
])
sob.meta.object_writable(  # type: ignore
    ServerVariable
).properties = sob.meta.Properties([
    (
        'enum',
        sob.properties.Array(
            item_types=sob.types.MutableTypes([
                str
            ])
        )
    ),
    (
        'default',
        sob.properties.String(
            required=True
        )
    ),
    ('description', sob.properties.String())
])
sob.meta.object_writable(  # type: ignore
    Tag
).properties = sob.meta.Properties([
    (
        'name',
        sob.properties.String(
            required=True
        )
    ),
    ('description', sob.properties.String()),
    (
        'external_docs',
        sob.properties.Property(
            types=sob.types.MutableTypes([
                ExternalDocumentation
            ])
        )
    )
])
sob.meta.object_writable(  # type: ignore
    XML
).properties = sob.meta.Properties([
    ('name', sob.properties.String()),
    (
        'name_space',
        sob.properties.String(
            name="nameSpace"
        )
    ),
    ('prefix', sob.properties.String()),
    ('attribute', sob.properties.Boolean()),
    ('wrapped', sob.properties.Boolean())
])

# region Hooks

_object_hooks: sob.abc.ObjectHooks = sob.hooks.object_writable(
    ExtensibleObject
)
_reference_hooks: sob.abc.ObjectHooks = sob.hooks.object_writable(Reference)
_parameter_hooks: sob.abc.ObjectHooks = sob.hooks.object_writable(Parameter)
_schema_hooks: sob.abc.ObjectHooks = sob.hooks.object_writable(Schema)


def _add_object_property(object_: sob.abc.Object, key: str) -> None:
    """
    Look for a matching property, and if none exists--create one
    """
    object_meta: typing.Optional[sob.abc.ObjectMeta] = sob.meta.object_read(
        object_
    )
    if object_meta and object_meta.properties:
        properties: sob.abc.Properties = object_meta.properties
        key_property: typing.Tuple[str, sob.abc.Property]
        if key in map(
            lambda key_property: key_property[1].name or key_property[0],
            properties.items(),
        ):
            # There is no need to add the property, it already exists
            return
    object_meta = sob.meta.object_writable(object_)
    if object_meta.properties is None:
        object_meta.properties = sob.meta.Properties()  # type: ignore
    property_name = sob.utilities.property_name(key)
    object_meta.properties[property_name] = sob.properties.Property(name=key)


def _object_before_setitem(
    object_: sob.abc.Object, key: str, value: typing.Any
) -> typing.Tuple[str, typing.Any]:
    """
    This hook allows for the use of extension attributes.
    """
    if key[:2] == "x-":
        _add_object_property(object_, key)
    return key, value


def _reference_before_setitem(
    reference_: sob.abc.Object, key: str, value: sob.abc.MarshallableTypes
) -> typing.Tuple[str, typing.Any]:
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
    assert isinstance(data, Reference)
    ref: typing.Optional[str]
    try:
        ref = data["$ref"]
    except KeyError:
        ref = None
    if ref is None:
        raise TypeError(
            "All instances of "
            f"`{sob.utilities.qualified_name(Reference)}` must have a `$ref` "
            "attribute"
        )
    return data


def _parameter_after_validate(parameter: sob.abc.Model) -> None:
    assert isinstance(parameter, Parameter)
    if (parameter.content is not None) and len(
        tuple(parameter.content.keys())
    ) > 1:
        raise sob.errors.ValidationError(
            f"`{sob.utilities.qualified_name(type(parameter))}."
            "content` may have only one mapped value.:\n"
            f"{sob.utilities.inspect.represent(parameter)}"
        )
    if (parameter.content is not None) and (parameter.schema is not None):
        raise sob.errors.ValidationError(
            "An instance of "
            f"`{sob.utilities.qualified_name(type(parameter))}` may have a "
            "`schema` property or a `content` property, but not *both*:\n"
            f"{sob.utilities.inspect.represent(parameter)}"
        )
    _schema_after_validate(parameter)


def _schema_after_validate(
    schema: sob.abc.Model
) -> None:
    assert isinstance(schema, (Schema, Parameter))
    if schema.format_ in (
        "int32",
        "int64",  # type_ == 'integer'
        "float",
        "double",  # type_ == 'number'
        "byte",
        "binary",
        "date",
        "date-time",
        "password",  # type_ == 'string'
    ):
        if schema.type_ == "integer" and (
            schema.format_ not in ("int32", "int64", None)
        ):
            qualified_class_name = sob.utilities.qualified_name(type(schema))
            raise sob.errors.ValidationError(
                f'"{schema.format_}" in not a valid value for '
                f"`{qualified_class_name}.format_` in this circumstance. "
                f'`{qualified_class_name}.format_` may be "int32" or "int64" '
                f'when `{qualified_class_name}.type_` is "integer".'
            )
        elif schema.type_ == "number" and (
            schema.format_ not in ("float", "double", None)
        ):
            qualified_class_name = sob.utilities.qualified_name(type(schema))
            raise sob.errors.ValidationError(
                f'"{schema.format_}" in not a valid value for '
                f"`{qualified_class_name}.format_` in this circumstance. "
                f'`{qualified_class_name}.format_` may be "float" or "double" '
                f'when `{qualified_class_name}.type_` is "number".'
            )
        elif schema.type_ == "string" and (
            schema.format_
            not in ("byte", "binary", "date", "date-time", "password", None)
        ):
            qualified_class_name = sob.utilities.qualified_name(type(schema))
            raise sob.errors.ValidationError(
                f'"{schema.format_}" in not a valid value for '
                f"`{qualified_class_name}.format_` in this circumstance. "
                f'`{qualified_class_name}.format_` may be "byte", "binary", '
                '"date", "date-time" or "password" when '
                f'`{qualified_class_name}.type_` is "string".'
            )


_object_hooks.before_setitem = _object_before_setitem
_reference_hooks.before_setitem = _reference_before_setitem
_reference_hooks.after_unmarshal = _reference_after_unmarshal
_parameter_hooks.after_validate = _parameter_after_validate
_schema_hooks.after_validate = _schema_after_validate

# endregion
