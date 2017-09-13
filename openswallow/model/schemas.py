import collections
import json
from collections import OrderedDict
from copy import copy, deepcopy
from itertools import chain

from marshmallow import Schema, fields, post_load, post_dump, pre_load, pre_dump, missing, ValidationError
from openswallow.model import JSONObject, JSONDict, JSONList, get_data, get_properties_values


def get_model(schema):
    # type: (type) -> JSONObject
    return schema.__model__


def serialize_polymorph(
    data,  # type: Sequence[JSONObjectSchema]
    schemas=None,  # type: Optional[Sequence[JSONObjectSchema]]
    types=None,  # type: Optional[Sequence[type]]
    many=None  # type: bool
):
    # type: (...) -> Any
    if (data is None) or (data is missing):
        return data
    data = copy(data)
    # print(
    #     'Data to be serialized: ' +
    #     repr({k:v for k, v in get_properties_values(data)})
    # )
    if (
        (many is not False) and
        (schemas is not None) and
        (ReferenceSchema in schemas) and
        isinstance(data, get_model(ReferenceSchema))
    ):
        many = False
    elif many is None:
        many = isinstance(data, collections.Sequence) and (not isinstance(data, (str, bytes)))
    if many:
        if (not isinstance(data, collections.Sequence)) or isinstance(data, (str, bytes)):
            raise TypeError(
                'Error encountered while parsing:\n%s\n...this is not a sequence' % (
                    repr(data)
                )
            )
        data = [
            serialize_polymorph(copy(d), schemas=schemas, types=types, many=False)
            for d in data
        ]
    else:
        if schemas:
            models = tuple(get_model(s) for s in schemas)
        else:
            models = None
        if models and isinstance(data, models):
            data = get_data(data)
        elif not (types and isinstance(data, tuple(types))):
            raise TypeError(
                repr({k: v for k, v in get_properties_values(data)}) +
                '\n`%s` is not an instance of ' % type(data).__name__ +
                '|'.join(
                    chain(
                        (m.__name__ for m in (models or [])),
                        (t.__name__ for t in (types or []))
                    )
                )
            )
    return data


def deserialize_polymorph(
    data,  # type: Union[dict, Sequence[dict]]
    schemas=None,  # type: Optional[Sequence[JSONObjectSchema]]
    types=None,  # type: Optional[Sequence[type]]
    many=None  # type: bool
):
    # type: (...) -> JSONObjectSchema
    # print('Data to be de-serialized: ' + repr(data))
    data = copy(data)
    if isinstance(schemas, JSONObjectSchema):
        schemas = (schemas,)
    if isinstance(types, type):
        types = (types,)
    if (
        (many is not False) and
        (schemas is not None) and
        (ReferenceSchema in schemas) and
        isinstance(data, dict) and
        len(data.keys()) == 1 and
        ('$ref' in data.keys())
    ):
        many = False
    elif many is None:
        many = isinstance(data, collections.Sequence) and (not isinstance(data, (str, bytes)))
    if many:
        if (not isinstance(data, collections.Sequence)) or isinstance(data, (str, bytes)):
            raise TypeError(data)
        data = JSONList([
            deserialize_polymorph(d, schemas=schemas, types=types, many=False)
            for d in data
        ])
    else:
        schema = None
        smallest_unconsumed = None
        if isinstance(data, collections.Mapping):
            data = JSONDict(data)
            properties = set(data.keys())
            for s in schemas:
                sp = set()
                si = s(strict=True, many=False)
                for n, p in si.fields.items():
                    if isinstance(p, fields.Field):
                        pn = p.load_from or n
                        sp.add(pn)
                unconsumed = properties - sp
                if unconsumed:
                    if (smallest_unconsumed is None) or len(smallest_unconsumed[-1] > len(unconsumed)):
                        smallest_unconsumed = (s, unconsumed)
                else:
                    schema = s
                    break
        type_match = False
        if schema is None:
            type_match = bool(types and isinstance(data, tuple(types)))
            if not type_match:
                raise TypeError(
                    'Could not identify a schema%s or type%s for: %s%s' % (
                        ' (%s)' % '|'.join(s.__name__ for s in schemas) if schemas else '',
                        ' (%s)' % '|'.join(t.__name__ for t in types) if types else '',
                        json.dumps(data),
                        (
                            '' if smallest_unconsumed is None else
                            '\n(closest match: %s does not consume: %s)' % (
                                smallest_unconsumed[0].__name__,
                                ', '.join(smallest_unconsumed[1])
                            )
                        )
                    )
                )
        if not type_match:
            if isinstance(data, JSONObject):
                # data = OrderedDict(get_properties_values(data))
                data = schema(
                    strict=True,
                    many=False
                ).dump(data).data
            elif isinstance(data, collections.Mapping):
                data = JSONDict(data)
            elif isinstance(data, collections.Sequence) and not isinstance(data, (str, bytes)):
                data = JSONList(data)
    return data


def serialize_mapping(
    data, # type: dict
    schemas=None,  # type: Optional[Sequence[JSONObjectSchema]]
    types=None,  # type: Optional[Sequence[type]]
    many=None,  # type: Optional[bool]
    depth=1
):
    # type: (dict, type, Optional[bool]) -> dict
    if (data is missing) or (data is None):
        return data
    if isinstance(data, (collections.MutableSequence, collections.MutableMapping, collections.MutableSet)):
        data = copy(data)
    for k, v in copy(data).items():
        if isinstance(v, (collections.MutableSequence, collections.MutableMapping, collections.MutableSet)):
            v = copy(v)
        if depth > 1 and (
            # This allows references to occur at every depth
            (ReferenceSchema not in schemas) or
            (not isinstance(data, dict)) or
            ('$ref' not in data) or
            len(data.keys()) > 1
        ):
            data[k] = serialize_mapping(v, schemas=schemas, types=types, many=many, depth=depth - 1)
        else:
            data[k] = serialize_polymorph(v, schemas=schemas, types=types, many=many)
    return data


def deserialize_mapping(
    data,  # type: dict
    schemas=None,  # type: Optional[Sequence[JSONObjectSchema]]
    types=None,  # type: Optional[Sequence[type]]
    many=None,  # type: Optional[bool]
    depth=1
):
    # type: (dict, type, Optional[bool]) -> JSONObject
    if (data is missing) or (data is None):
        return data
    # if isinstance(data, (collections.MutableSequence, collections.MutableMapping, collections.MutableSet)):
    if isinstance(data, collections.Mapping):
        data = JSONDict(data)
    else:
        raise TypeError(data)
    if ReferenceSchema in schemas:
        reference_model = get_model(ReferenceSchema)
    else:
        reference_model = None
    for k, v in data.items():
        if depth > 1 and (
            (reference_model is None) or
            isinstance(data, reference_model)
        ):
            data[k] = deserialize_mapping(v, schemas=schemas, types=types, many=many, depth=depth - 1)
        else:
            data[k] = deserialize_polymorph(v, schemas=schemas, types=types, many=many)
    return data


def polymorph(
    schemas=None,  # type: Optional[Union[Sequence[JSONObjectSchema], str]]
    types=None,  # type: Optional[Sequence[type]]
    many=None,  # type: bool
    load_from=None,  # type: Optional[str]
    dump_to=None,  # type: Optional[str]
    attribute=None,  # type: Optional[str]
):
    # type: (...) -> fields.Function
    if isinstance(schemas, type):
        schemas = (schemas,)
    if isinstance(types, type):
        types = (types,)
    kwargs = dict(
        load_from=load_from,
        dump_to=dump_to,
        attribute=attribute
    )
    for k in tuple(kwargs.keys()):
        if kwargs[k] is None:
            del kwargs[k]
    return fields.Function(
        serialize=lambda data: serialize_polymorph(
            data,
            schemas=schemas,
            types=types,
            many=many
        ),
        deserialize=lambda data: deserialize_polymorph(
            data,
            schemas=schemas,
            types=types,
            many=many
        ),
        **kwargs
    )


def mapping(
    schemas,  # Union[JSONObjectSchema, Sequence[JSONObjectSchema]]
    types=None,  # Union[type, Sequence[types]]
    many=None,  # type: Optional[bool]
    depth=1,  # type: int
    load_from=None,  # type: Optional[str]
    dump_to=None,  # type: Optional[str]
    attribute=None,  # type: Optional[str]
):
    # type: (...) -> fields.Function
    if isinstance(schemas, type):
        schemas = (schemas,)
    if isinstance(types, (type, str)):
        types = (types,)
    kwargs = dict(
        load_from=load_from,
        dump_to=dump_to,
        attribute=attribute
    )
    for k in tuple(kwargs.keys()):
        if kwargs[k] is None:
            del kwargs[k]
    return fields.Function(
        serialize=lambda data: serialize_mapping(
            data,
            schemas=schemas,
            types=types,
            many=many,
            depth=depth
        ),
        deserialize=lambda data: deserialize_mapping(
            data,
            schemas=schemas,
            types=types,
            many=many,
            depth=depth
        ),
        **kwargs
    )


class JSONObjectSchema(Schema):

    __model__ = None

    # @pre_load
    # def pre_load(
    #     self,
    #     data  # type: dict
    # ):
    #     # print(
    #     #     self.__class__.__name__ +
    #     #     ' - data to be loaded: ' +
    #     #     str(tuple(sorted((k for k in data.keys()), key=lambda k: k.replace('$', ''))))
    #     # )
    #     # print('Data to be loaded: ' + str(data))
    #     if isinstance(data, (collections.MutableMapping, collections.MutableSequence, collections.MutableSet)):
    #         data = copy(data)
    #     if isinstance(data, collections.Mapping):
    #         data = JSONDict(data)
    #     return data
    #
    # @pre_dump
    # def pre_dump(
    #     self,
    #     data  # type: dict
    # ):
    #     # print(
    #     #     self.__class__.__name__ +
    #     #     ' - data to be dumped: ' +
    #     #     str(tuple(sorted((k for k, v in get_properties_values(data)), key=lambda k: k.replace('$', ''))))
    #     # )
    #     print('Data to be dumped: ' + str(
    #         OrderedDict(
    #             list(get_properties_values(data))
    #             if isinstance(data, JSONObject)
    #             else data
    #         )
    #     ))
    #     #if not isinstance(data, get_model(JSONObjectSchema)):
    #     #    data = get_data(data)
    #     # if isinstance(data, (collections.MutableMapping, collections.MutableSequence, collections.MutableSet)):
    #     #     data = copy(data)
    #     # if isinstance(data, collections.Mapping):
    #     #     data = JSONDict(data)
    #     return data

    @post_load
    def post_load(
        self,
        data  # type: dict
    ):
        m = get_model(self)
        # if isinstance(data, (collections.MutableMapping, collections.MutableSequence, collections.MutableSet)):
        #     data = copy(data)
        # if isinstance(data, collections.Mapping):
        #     data = JSONDict(data)
        try:
            return m(**data)
        except (KeyError, TypeError) as e:
            raise TypeError(
                'JSON object type ``%s`` could not be parsed:\n%s' % (m.__name__, '\n'.join(e.args))
            )

    @post_dump
    def post_dump(
        self,
        data  # type: JSONObject
    ):
        # if isinstance(data, (collections.MutableMapping, collections.MutableSequence, collections.MutableSet)):
        #     data = copy(data)
        if isinstance(data, collections.Mapping):
            data = JSONDict(data)
        return data

    class Meta:

        strict = True


class ReferenceSchema(JSONObjectSchema):

    ref = fields.String(load_from='$ref', dump_to='$ref')


class LinkSchema(JSONObjectSchema):

    rel = fields.String()
    href = fields.String()


class SchematicSchema(JSONObjectSchema):

    schema = fields.String(load_from='$schema', dump_to='$schema')
    schema_id = fields.String(load_from='$id', dump_to='$id')
    title = fields.String()
    description = fields.String()
    multiple_of = fields.Number(dump_to='multipleOf', load_from='multipleOf')
    maximum = fields.Number()
    exclusive_maximum = fields.Boolean(dump_to='exclusiveMaximum', load_from='exclusiveMaximum')
    minimum = fields.Number()
    exclusive_minimum = fields.Boolean(dump_to='exclusiveMinimum', load_from='exclusiveMinimum')
    max_length = fields.Integer(dump_to='maxLength', load_from='maxLength')
    min_length = fields.Integer(dump_to='minLength', load_from='minLength')
    pattern = fields.String()
    max_items = fields.Integer(load_from='maxItems', dump_to='maxItems')
    min_items = fields.Integer(load_from='minItems', dump_to='minItems')
    unique_items = fields.String(load_from='uniqueItems', dump_to='uniqueItems')
    max_properties = fields.Integer(load_from='maxProperties', dump_to='maxProperties')
    min_properties = fields.Integer(load_from='minProperties', dump_to='minProperties')
    pattern_properties = fields.Dict()
    additional_properties = fields.Dict()
    enum = fields.List(fields.String())
    # data_type = polymorph(types=(str, collections.Sequence), load_from='type', dump_to='type', many=None)
    data_type = fields.Raw(load_from='type', dump_to='type')
    format = fields.String()
    required = fields.String(many=True)
    default = fields.Raw()
    links = fields.Nested(LinkSchema, many=True)

    @property
    @staticmethod
    def items():
        return polymorph(schemas=(SchematicSchema,))

    @property
    @staticmethod
    def additional_items():
        return polymorph(
            schemas=(SchematicSchema,),
            types=(bool,),
            load_from='additionalItems',
            dump_to='additionalItems',
        )

    @property
    @staticmethod
    def properties():
        return mapping((SchematicSchema,))

    @property
    @staticmethod
    def dependencies():
        return mapping((SchematicSchema,), depth=2)

    @property
    @staticmethod
    def all_of():
        return polymorph(
            (SchematicSchema, ReferenceSchema),
            load_from='allOf', dump_to='allOf',
            many=True,
        )

    @property
    @staticmethod
    def any_of():
        return polymorph(
            (SchematicSchema, ReferenceSchema),
            load_from='anyOf', dump_to='anyOf',
            many=True,
        )

    @property
    @staticmethod
    def one_of():
        return polymorph(
            (SchematicSchema, ReferenceSchema),
            load_from='oneOf', dump_to='oneOf',
            many=True,
        )

    @property
    @staticmethod
    def is_not():
        return polymorph(
            (SchematicSchema, ReferenceSchema),
            load_from='isNot', dump_to='isNot',
            many=False,
        )

    @property
    @staticmethod
    def definitions():
        return mapping((SchematicSchema, ReferenceSchema), many=False)

    class Meta:

        additional = (
            'items', 'additional_items', 'properties', 'dependencies', 'all_of', 'any_of', 'one_of', 'is_not',
            'definitions',
        )
        ordered = True
        strict = True


class ExampleSchema(JSONObjectSchema):

    summary = fields.String()
    description = fields.String()
    value = fields.Raw()
    external_value = fields.String(load_from='externalValue', dump_to='externalValue')


class MediaTypeSchema(JSONObjectSchema):

    schema = mapping((SchematicSchema, ReferenceSchema))
    example = fields.Raw()
    examples = mapping(schemas=(ExampleSchema, ReferenceSchema), types=(str,), many=True)


class HeaderSchema(JSONObjectSchema):

    description = fields.String()
    required = fields.Boolean()
    deprecated = fields.Boolean()
    allow_empty_value = fields.Boolean()
    style = fields.String()
    explode = fields.Boolean()
    allow_reserved = fields.Boolean()
    schema = polymorph((SchematicSchema, ReferenceSchema))
    example = fields.Raw()
    examples = mapping((SchematicSchema, ReferenceSchema))
    content = mapping(MediaTypeSchema)


class EncodingSchema(JSONObjectSchema):

    content_type = fields.String(dump_to='contentType', load_from='contentType')
    headers = mapping((HeaderSchema, ReferenceSchema))
    style = fields.String()
    explode = fields.Boolean()
    allow_reserved = fields.Boolean(load_from='allowReserved', dump_to='allowReserved')


class ServerVariableSchema(JSONObjectSchema):

    enum = fields.String(many=True)
    default = fields.String()
    description = fields.String()


class ServerSchema(JSONObjectSchema):

    url = fields.String()
    description = fields.String()  # allow_none=True
    variables = mapping(ServerVariableSchema)


class LinkedOperationSchema(JSONObjectSchema):

    operation_ref = fields.String(load_from='operationRef', dump_to='operationRef')
    operation_id = fields.String(load_from='operationId', dump_to='operationId')
    parameters = fields.Dict()
    request_body = fields.Raw(load_from='requestBody', dump_to='requestBody')
    description = fields.String()
    server = fields.Nested(ServerSchema)


class ResponseSchema(JSONObjectSchema):

    description = fields.String()
    headers = mapping((HeaderSchema, ReferenceSchema))
    content = mapping((MediaTypeSchema, ReferenceSchema))
    links = mapping((LinkedOperationSchema, ReferenceSchema))
    # version 2.0 compatibility
    schema = polymorph((SchematicSchema, ReferenceSchema))


class ResponsesSchema(JSONObjectSchema):

    default = fields.Nested(ResponseSchema)
    please_continue = fields.Nested(ResponseSchema, load_from='100', dump_to='100')
    switching_protocols = fields.Nested(ResponseSchema, load_from='101', dump_to='101')
    ok = fields.Nested(ResponseSchema, load_from='200', dump_to='200')
    created = fields.Nested(ResponseSchema, load_from='201', dump_to='201')
    accepted = fields.Nested(ResponseSchema, load_from='202', dump_to='202')
    non_authoritative_information = fields.Nested(ResponseSchema, load_from='203', dump_to='203')
    no_content = fields.Nested(ResponseSchema, load_from='204', dump_to='204')
    reset_content = fields.Nested(ResponseSchema, load_from='205', dump_to='205')
    partial_content = fields.Nested(ResponseSchema, load_from='206', dump_to='206')
    multiple_choices = fields.Nested(ResponseSchema, load_from='300', dump_to='300')
    moved_permanently = fields.Nested(ResponseSchema, load_from='301', dump_to='301')
    found = fields.Nested(ResponseSchema, load_from='302', dump_to='302')
    see_other = fields.Nested(ResponseSchema, load_from='303', dump_to='303')
    not_modified = fields.Nested(ResponseSchema, load_from='304', dump_to='304')
    use_proxy = fields.Nested(ResponseSchema, load_from='305', dump_to='305')
    temporary_redirect = fields.Nested(ResponseSchema, load_from='307', dump_to='307')
    bad_request = fields.Nested(ResponseSchema, load_from='400', dump_to='400')
    unauthorized = fields.Nested(ResponseSchema, load_from='401', dump_to='401')
    payment_required = fields.Nested(ResponseSchema, load_from='402', dump_to='402')
    forbidden = fields.Nested(ResponseSchema, load_from='403', dump_to='403')
    not_found = fields.Nested(ResponseSchema, load_from='404', dump_to='404')
    method_not_allowed = fields.Nested(ResponseSchema, load_from='405', dump_to='405')
    not_acceptable = fields.Nested(ResponseSchema, load_from='406', dump_to='406')
    proxy_authentication_required = fields.Nested(ResponseSchema, load_from='407', dump_to='407')
    request_timeout = fields.Nested(ResponseSchema, load_from='408', dump_to='408')
    conflict = fields.Nested(ResponseSchema, load_from='409', dump_to='409')
    gone = fields.Nested(ResponseSchema, load_from='410', dump_to='410')
    length_required = fields.Nested(ResponseSchema, load_from='411', dump_to='411')
    precondition_failed = fields.Nested(ResponseSchema, load_from='412', dump_to='412')
    payload_too_large = fields.Nested(ResponseSchema, load_from='413', dump_to='413')
    uri_too_long = fields.Nested(ResponseSchema, load_from='414', dump_to='414')
    unsupported_media_type = fields.Nested(ResponseSchema, load_from='415', dump_to='415')
    range_not_satisfiable = fields.Nested(ResponseSchema, load_from='416', dump_to='416')
    expectation_failed = fields.Nested(ResponseSchema, load_from='417', dump_to='417')
    upgrade_required = fields.Nested(ResponseSchema, load_from='426', dump_to='426')
    internal_server_error = fields.Nested(ResponseSchema, load_from='500', dump_to='500')
    not_implemented = fields.Nested(ResponseSchema, load_from='501', dump_to='501')
    bad_gateway = fields.Nested(ResponseSchema, load_from='502', dump_to='502')
    service_unavailable = fields.Nested(ResponseSchema, load_from='503', dump_to='503')
    gateway_timeout = fields.Nested(ResponseSchema, load_from='504', dump_to='504')
    http_version_not_supported = fields.Nested(ResponseSchema, load_from='505', dump_to='505')


class ParameterSchema(JSONObjectSchema):

    name = fields.String()
    parameter_in = fields.String(load_from='in', dump_to='in')
    description = fields.String()
    required = fields.Boolean()
    deprecated = fields.Boolean()
    allow_empty_value = fields.Boolean()
    style = fields.String()
    explode = fields.Boolean()
    allow_reserved = fields.Boolean()
    schema = polymorph((SchematicSchema, ReferenceSchema))
    example = fields.Raw()
    examples = mapping((SchematicSchema, ReferenceSchema))
    content = mapping(MediaTypeSchema)
    # version 2x compatibility
    data_type = polymorph(types=(str,), load_from='type', dump_to='type', many=None)
    enum = fields.List(fields.Raw())


class ExternalDocumentationSchema(JSONObjectSchema):

    description = fields.String()
    url = fields.String()


class RequestBodySchema(JSONObjectSchema):

    description = fields.String()
    content = mapping(MediaTypeSchema)
    required = fields.Boolean()


class TagSchema(JSONObjectSchema):

    name = fields.String()
    description = fields.String()
    external_docs = fields.Nested(
        ExternalDocumentationSchema,
        load_from='externalDocs',
        dump_to='externalDocs'
    )


class OperationSchema(JSONObjectSchema):

    tags = fields.Nested(TagSchema, many=True)
    summary = fields.String()
    description = fields.String()
    external_docs = fields.Nested(
        ExternalDocumentationSchema,
        load_from='externalDocs',
        dump_to='externalDocs'
    )
    operation_id = fields.String(load_from='operationId', dump_to='operationId')
    parameters = polymorph((ParameterSchema, ReferenceSchema), many=True)
    request_body = polymorph(
        schemas=(RequestBodySchema, ReferenceSchema),
        load_from='requestBody',
        dump_to='requestBody'
    )
    responses = mapping((ResponseSchema,))
    deprecated = fields.Boolean()
    security = fields.Raw()
    servers = fields.Nested(
        ServerSchema,
        many=True
    )
    # Version 2x Compatibility
    produces = fields.String(many=True)

    @property
    @staticmethod
    def callbacks():
        return mapping(
            schemas=(PathItemSchema, ReferenceSchema),
            depth=1,
            load_from='callbacks',
            dump_to='callbacks',
            attribute='callbacks'
        )

    class Meta:

        additional = ('callbacks',)
        ordered = True
        strict = True


class PathItemSchema(JSONObjectSchema):

    ref = fields.String(load_from='$ref', dump_to='$ref')
    description = fields.String()
    get = fields.Nested(OperationSchema)
    put = fields.Nested(OperationSchema)
    post = fields.Nested(OperationSchema)
    delete = fields.Nested(OperationSchema)
    options = fields.Nested(OperationSchema)
    head = fields.Nested(OperationSchema)
    patch = fields.Nested(OperationSchema)
    trace = fields.Nested(OperationSchema)
    servers = fields.Nested(ServerSchema, many=True)
    parameters = polymorph((ParameterSchema, ReferenceSchema), many=True)


class ContactSchema(JSONObjectSchema):

    name = fields.String()
    url = fields.String()
    email = fields.String()


class LicenseSchema(JSONObjectSchema):

    name = fields.String()
    url = fields.String()


class InfoSchema(JSONObjectSchema):

    title = fields.String()
    description = fields.String()
    terms_of_service = fields.String(load_from='termsOfService', dump_to='termsOfService')
    contact = fields.Nested(ContactSchema)
    license = fields.Nested(LicenseSchema)
    version = fields.String()


class DiscriminatorSchema(JSONObjectSchema):

    property_name = fields.String(load_from='propertyName', dump_to='propertyName')
    mapping = fields.Dict()


class XMLSchema(JSONObjectSchema):

    name = fields.String()
    name_space = fields.String(load_from='namespace', dump_to='namespace')
    prefix = fields.String()
    attribute = fields.Boolean()
    wrapped = fields.Boolean()


class InconsistentReferences(Exception):

    def __init__(
        self,
        array  # type: Sequence
    ):
        json_model = get_model(JSONObjectSchema)
        super().__init__(
            'An array must consist only of references, or exclude references altogether:\n' +
            json.dumps([
                (
                    json.loads(str(a)) if isinstance(a, json_model) else a
                ) for a in array
            ])
        )


class OAuthFlowSchema(JSONObjectSchema):

    authorization_url = fields.String(load_from='authorizationUrl', dump_to='authorizationUrl')
    token_url = fields.String(load_from='tokenUrl', dump_to='tokenUrl')
    refresh_url = fields.String(load_from='refreshUrl', dump_to='refreshUrl')
    scopes = fields.Dict()


class OAuthFlowsSchema(JSONObjectSchema):

    implicit = fields.Nested(OAuthFlowSchema)
    password = fields.Nested(OAuthFlowSchema)
    client_credentials = fields.Nested(OAuthFlowSchema)
    authorization_code = fields.Nested(OAuthFlowSchema)


class SecuritySchemeSchema(JSONObjectSchema):

    security_scheme_type = fields.String(load_from='type', dump_to='type')
    description = fields.String()
    name = fields.String()
    security_scheme_in = fields.String(load_from='in', dump_to='in')
    scheme = fields.String()
    bearer_format = fields.String(load_from='bearerFormat', dump_to='bearerFormat')
    flows = fields.Nested(OAuthFlowsSchema)
    open_id_connect_url = fields.String(load_from='openIdConnectUrl', dump_to='openIdConnectUrl')


class ComponentsSchema(JSONObjectSchema):

    schemas = mapping((SchematicSchema, ReferenceSchema))
    responses = mapping((ResponseSchema, ReferenceSchema))
    parameters = mapping((ParameterSchema, ReferenceSchema))
    examples = mapping((ExampleSchema, ReferenceSchema))
    request_bodies = mapping((RequestBodySchema, ReferenceSchema))
    headers = mapping((HeaderSchema, ReferenceSchema))
    security_schemes = mapping((SecuritySchemeSchema, ReferenceSchema))
    links = mapping((LinkedOperationSchema, ReferenceSchema))
    callbacks = mapping(
        schemas=(ReferenceSchema,),
        types=(dict,)
    )


class OpenAPISchema(JSONObjectSchema):

    open_api = fields.String(dump_to='openapi', load_from='openapi')
    info = fields.Nested(InfoSchema)
    servers = fields.Nested(ServerSchema, many=True)
    base_path = fields.String(dump_to='basePath', load_from='basePath')
    schemes = fields.List(fields.String())
    tags = fields.Nested(TagSchema, many=True)
    paths = mapping((PathItemSchema, ReferenceSchema))
    # version 2x compatibility
    swagger = fields.String(dump_to='swagger', load_from='swagger')
    host = fields.String()
    consumes = fields.List(fields.String())

    # class Meta:
    #
    #     additional = ('paths',)
    #     strict = True
    #     ordered = True


