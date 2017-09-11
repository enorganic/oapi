import collections
import json
from copy import copy
from time import sleep
from typing import Any

from marshmallow import Schema, fields, post_load, post_dump, pre_load, pre_dump, missing
from openswallow.model import PathItem, JSONObject, JSONDict, JSONList
from openswallow.utilities import bases


def get_model(schema):
    # type: (type) -> JSONObject
    return schema.__model__


def serialize_polymorph(
    data,  # type: Union[JSONObject, Sequence[JSONObject]]
    schemas=None,  # type: Optional[Sequence[JSONObjectSchema]]
    types=None,  # type: Optional[Sequence[type]]
    many=None  # type: bool
):
    data = copy(data)
    if isinstance(schemas, JSONObjectSchema):
        schemas = (schemas,)
    if isinstance(types, type):
        types = (types,)
    # print(data)
    # print('many = ' + repr(many))
    if many is None:
        many = isinstance(data, collections.Sequence) and (not isinstance(data, (str, bytes)))
    # print('many = ' + repr(many))
    if many:
        if (not isinstance(data, collections.Sequence)) or isinstance(data, (str, bytes)):
            raise TypeError(
                'Error encountered while parsing %s:\n%s\n...is not a sequence' % (
                    '|'.join(s.__name__ for s in schemas),
                    repr(data)
                )
            )
        data = JSONList([
            serialize_polymorph(d, schemas=schemas, types=types, many=False)
            for d in data
        ])
    elif not (types and isinstance(data, tuple(types))):
        models = tuple(get_model(s) for s in schemas)
        if not isinstance(data, models):
            # return data
            raise TypeError(repr(data) + '\n...is not an instance of ' + '|'.join(m.__name__ for m in models))
        schema = None
        for i in range(len(schemas)):
            if isinstance(data, models[i]):
                schema = schemas[i]
                break
        if schema is None:
            raise TypeError(
                'Could not identify a schema (%s) for:%s' % (
                    '|'.join(s.__name__ for s in schemas),
                    repr(data)
                )
            )
        else:
            data = get_model(schema)(**data)
    return data


def deserialize_polymorph(
    data,  # type: Union[dict, Sequence[dict]]
    schemas=None,  # type: Optional[Sequence[JSONObjectSchema]]
    types=None,  # type: Optional[Sequence[type]]
    many=None  # type: bool
):
    # type: (...) -> JSONObjectSchema
    if isinstance(schemas, JSONObjectSchema):
        schemas = (schemas,)
    if isinstance(types, type):
        types = (types,)
    if many is None:
        many = isinstance(data, collections.Sequence) and (not isinstance(data, (dict, str, bytes)))
    if many:
        if (not isinstance(data, collections.Sequence)) or isinstance(data, (dict, str, bytes)):
            raise TypeError(data)
        data = [
            deserialize_polymorph(d, schemas=schemas, types=types, many=False)
            for d in data
        ]
    elif not (types and isinstance(data, tuple(types))):
        if not isinstance(data, dict):
            raise TypeError(data)
        data = copy(data)
        properties = set(data.keys())
        schema = None
        smallest_unconsumed = None
        for s in schemas:
            sp = set()
            si = s(strict=True)
            for n, p in si.fields.items():
                if isinstance(p, fields.FieldABC):
                    pn = p.load_from or n
                    # print('Field: ' + pn)
                    sp.add(pn)
            unconsumed = properties - sp
            if unconsumed:
                if (smallest_unconsumed is None) or len(smallest_unconsumed[-1] > len(unconsumed)):
                    smallest_unconsumed = (s, unconsumed)
            else:
                schema = s
                break
        # print('schema = ' + repr(schema))
        if schema is None:
            raise TypeError(
                'Could not identify a schema (%s) for:%s%s' % (
                    '|'.join(s.__name__ for s in schemas),
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
        else:
            # print(repr(schema))
            # print('data = ' + repr(data))
            if isinstance(data, JSONObject):
                data = schema(strict=True, many=False).dump(data).data
    return data


def serialize_mapping(
    data, # type: dict
    schemas,  # type: Optional[Sequence[JSONObjectSchema]]
    types=None,  # type: Optional[Sequence[type]]
    many=None,  # type: Optional[bool]
    depth=1
):
    # type: (dict, type, Optional[bool]) -> dict
    if (data is missing) or (data is None):
        return data
    data = copy(data)
    for k, v in copy(data).items():
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
    schemas,  # type: Optional[Sequence[JSONObjectSchema]]
    types=None,  # type: Optional[Sequence[type]]
    many=None,  # type: Optional[bool]
    depth=1
):
    # type: (dict, type, Optional[bool]) -> JSONObject
    if (data is missing) or (data is None):
        return data
    data = JSONDict(copy(data))
    if ReferenceSchema in schemas:
        reference_model = get_model(ReferenceSchema)
    else:
        reference_model = None
    for k, v in copy(data).items():
        # print('"%s": %s' % (k, json.dumps(v)))
        if depth > 1 and (
            (reference_model is None) or
            isinstance(data, reference_model)
        ):
            data[k] = deserialize_mapping(data[k], schemas=schemas, types=types, many=many, depth=depth - 1)
        else:
            data[k] = deserialize_polymorph(data[k], schemas=schemas, types=types, many=many)
    return data


def polymorph(
    schemas,  # type: Optional[Sequence[JSONObjectSchema]]
    types=None,  # type: Optional[Sequence[type]]
    many=None,  # type: bool
    load_from=None,  # type: Optional[str]
    dump_to=None,  # type: Optional[str]
):
    # type: (...) -> fields.Function
    if isinstance(schemas, type):
        schemas = (schemas,)
    if isinstance(types, type):
        types = (types,)
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
        load_from=load_from,
        dump_to=dump_to
    )


def mapping(
    schemas,  # Union[JSONObjectSchema, Sequence[JSONObjectSchema]]
    types=None,  # Union[type, Sequence[types]]
    many=None,  # type: Optional[bool]
    depth=1,  # type: int
    load_from=None,  # type: Optional[str]
    dump_to=None  # type: Optional[str]
):
    # type: (...) -> fields.Function
    if isinstance(schemas, type):
        schemas = (schemas,)
    if isinstance(types, type):
        types = (types,)
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
        load_from=load_from,
        dump_to=dump_to
    )


class JSONObjectSchema(Schema):

    __model__ = None

    @pre_load
    def pre_load(
        self,
        data  # type: dict
    ):
        return copy(data)

    @pre_dump
    def pre_dump(
        self,
        data  # type: dict
    ):
        return copy(data)

    @post_load
    def post_load(
        self,
        data  # type: dict
    ):
        if data is missing:
           return missing
        elif data is None:
           return None
        m = get_model(self)
        if m is None:
            return None
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
        return data


class ReferenceSchema(JSONObjectSchema):

    ref = fields.String(load_from='$ref', dump_to='$ref')


class ResponseSchematicSchema(JSONObjectSchema):

    type = fields.String()
    items = fields.Dict()


class SchematicSchema(JSONObjectSchema):

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
    items = None
    additional_items = None
    max_items = fields.Integer(load_from='maxItems', dump_to='maxItems')
    min_items = fields.Integer(load_from='minItems', dump_to='minItems')
    unique_items = fields.String(load_from='uniqueItems', dump_to='uniqueItems')
    max_properties = fields.Integer(load_from='maxProperties', dump_to='maxProperties')
    min_properties = fields.Integer(load_from='minProperties', dump_to='minProperties')
    properties = None
    pattern_properties = fields.Dict()
    additional_properties = fields.Dict()
    dependencies = None
    enum = fields.List(fields.String())
    data_type = fields.String(load_from='type', dump_to='type')
    format = fields.String()
    all_of = fields.Nested('self', load_from='allOf', dump_to='allOf', many=True)
    any_of = fields.Nested('self', load_from='anyOf', dump_to='anyOf', many=True)
    one_of = fields.Nested('self', load_from='oneOf', dump_to='oneOf', many=True)
    is_not = fields.Nested('self', load_from='isNot', dump_to='isNot', many=False)
    definitions = fields.Dict()
    required = fields.List(fields.String())
    default = fields.Raw()

    # @pre_load
    # def pre_load(self, data):
    #     data = super().pre_load(data)
    #     if 'items' in data:
    #         if isinstance(data['items'], dict):
    #             self.items = fields.Nested(self.__class__)
    #         elif isinstance(data['items'], collections.Sequence):
    #             self.items = fields.Nested('self', many=True)
    #     if 'additionalItems' in data:
    #         if isinstance(data['additionalItems'], dict):
    #             self.additional_items = fields.Nested('self')
    #         elif isinstance(data['additionalItems'], collections.Sequence):
    #             self.additional_items = fields.Nested('self', many=True)
    #     return data
    #
    # @pre_dump
    # def pre_dump(self, data):
    #     data = super().pre_dump(data)
    #     # type: (JSONSchematic) -> Any
    #     if isinstance(data.items, get_model(self)):
    #         self.items = fields.Nested('self')
    #     elif isinstance(data.items, collections.Sequence):
    #         self.items = fields.Nested('self', many=True)
    #     if isinstance(data.additional_items, self.__class__):
    #         self.additional_items = fields.Nested(
    #             'self',
    #             load_from='additionalItems',
    #             dump_to='additionalItems'
    #         )
    #     elif isinstance(data.additional_items, bool):
    #         self.additional_items = fields.Boolean(
    #             'self',
    #             load_from='additionalItems',
    #             dump_to='additionalItems'
    #         )
    #     return data


SchematicSchema.items = polymorph(
    schemas=(SchematicSchema,),
)


SchematicSchema.additional_items = polymorph(
    schemas=(SchematicSchema,),
    types=(bool,),
    load_from='additionalItems',
    dump_to='additionalItems'
)


SchematicSchema.properties = mapping(SchematicSchema)
SchematicSchema.dependencies = mapping(SchematicSchema, depth=2)


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


class LinkSchema(JSONObjectSchema):

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
    links = mapping((LinkSchema, ReferenceSchema))
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
    data_type = fields.String(load_from='type', dump_to='type')
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
    # responses = fields.Nested(ResponsesSchema)
    callbacks = None
    deprecated = fields.Boolean()
    security = fields.Raw()
    servers = fields.Nested(
        ServerSchema,
        many=True
    )
    # Version 2x Compatibility
    produces = fields.String(many=True)


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


OperationSchema.callbacks = mapping(
    schemas=(PathItemSchema, ReferenceSchema),
    depth=2
)

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
    links = mapping((LinkSchema, ReferenceSchema))
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
    paths = mapping((PathItemSchema,))
    # version 2x compatibility
    swagger = fields.String(dump_to='swagger', load_from='swagger')
    host = fields.String()


