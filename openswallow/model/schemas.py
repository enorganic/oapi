import collections
from copy import copy
from typing import Any

from marshmallow import Schema, fields, post_load, post_dump, pre_load, pre_dump, missing
from openswallow.model import Service, JSONObject


def get_model(schema):
    # type: (type) -> JSONObject
    return schema.__model__


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
        if get_model(self) is None:
            return None
        try:
            return get_model(self)(**data)
        except KeyError:
            raise TypeError(
                'JSON object type ``%s`` is not recognized'
            )

    @post_dump
    def post_dump(
        self,
        data  # type: JSONObject
    ):
        return data


class ResponseSchematicSchema(JSONObjectSchema):

    type = fields.String()
    items = fields.Dict()


class Headers(JSONObjectSchema):

    pass


class ResponseSchema(JSONObjectSchema):

    description = fields.String()
    headers = fields.Function(
        serialize=lambda data: serialize_mapping(data, Headers)
    )
    schema = fields.Nested(ResponseSchematicSchema)


class ResponsesSchema(JSONObjectSchema):

    success = fields.Nested(ResponseSchema, load_from='200', dump_to='200')
    unauthorized = fields.Nested(ResponseSchema, load_from='401', dump_to='401')
    default = fields.Nested(ResponseSchema)


class ParameterSchema(JSONObjectSchema):

    name = fields.String()
    parameter_in = fields.String(load_from='in', dump_to='in')
    parameter_type = fields.String(load_from='type', dump_to='type')
    required = fields.Boolean()


class ServiceMethodSchema(JSONObjectSchema):

    tags = fields.List(fields.String)
    description = fields.String
    operation_id = fields.String(load_from='operationId', dump_to='operationId')
    parameters = fields.Nested(ParameterSchema, many=True)
    responses = fields.Nested(ResponsesSchema)


class ServiceSchema(JSONObjectSchema):

    get = fields.Nested(ServiceMethodSchema)
    put = fields.Nested(ServiceMethodSchema)
    post = fields.Nested(ServiceMethodSchema)
    patch = fields.Nested(ServiceMethodSchema)
    delete = fields.Nested(ServiceMethodSchema)


class TagSchema(JSONObjectSchema):

    name = fields.String()
    description = fields.String()


class InfoSchema(JSONObjectSchema):

    version = fields.String()
    title = fields.String()


class ServerVariableSchema(JSONObjectSchema):

    enum = fields.List(fields.String())
    default = fields.String()
    description = fields.String()


class ServerSchema(JSONObjectSchema):

    url = fields.String()
    description = fields.String()
    variables = fields.Dict()

    @post_load
    def post_load(
        self,
        data
    ):
        """
        This overrides the behavior of ``JSONObjectSchema.post_load`` in order to loads each value in Swagger.paths as an
        instance of the ``Service`` class.
        """
        ss = super().post_load(data=data)
        if ss.variables is not missing:
            for vn, v in copy(ss.paths).items():
                if not isinstance(v, dict):
                    raise TypeError(v)
                ss.variables[vn] = get_model(ServerVariableSchema)(**v)
        return ss

    @post_dump
    def post_dump(
        self,
        data
    ):
        """
        This ensures each value in Swagger.paths is rendered serializable, since ``SwaggerSchema.post_load`` causes
        this dictionary to hold (non-serializable) instances of the ``Service`` class.
        """
        if ('variables' in data) and (data['variables'] is not None):
            for vn, v in copy(data['variables']).items():
                if not isinstance(v, get_model(ServerVariableSchema)):
                    raise TypeError(v)
                data['variables'][vn] = ServerVariableSchema(strict=True, many=False).dump(v).data
                if not isinstance(data['variables'][vn], dict):
                    raise TypeError(data['variables'][vn])
        return data


class DiscriminatorSchema(JSONObjectSchema):

    property_name = fields.String(load_from='propertyName', dump_to='propertyName')
    mapping = fields.Dict()


class XMLMetadataSchema(JSONObjectSchema):

    name = fields.String()
    name_space = fields.String(load_from='namespace', dump_to='namespace')
    prefix = fields.String()
    attribute = fields.Boolean()
    wrapped = fields.Boolean()


class ExternalDocumentationSchema(JSONObjectSchema):

    description = fields.String()
    url = fields.String()


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
    items = fields.Raw()
    additional_items = fields.Raw(load_from='additionalItems', dump_to='additionalItems')
    max_items = fields.Integer(load_from='maxItems', dump_to='maxItems')
    min_items = fields.Integer(load_from='minItems', dump_to='minItems')
    unique_items = fields.String(load_from='uniqueItems', dump_to='uniqueItems')
    max_properties = fields.Integer(load_from='maxProperties', dump_to='maxProperties')
    min_properties = fields.Integer(load_from='minProperties', dump_to='minProperties')
    properties = fields.Dict()
    pattern_properties = fields.Dict()
    additional_properties = fields.Dict()
    dependencies = fields.Dict()
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

    @pre_load
    def pre_load(self, data):
        data = super().pre_load(data)
        if 'items' in data:
            if isinstance(data['items'], dict):
                self.items = fields.Nested(self.__class__)
            elif isinstance(data['items'], collections.Sequence):
                self.items = fields.Nested('self', many=True)
        if 'additionalItems' in data:
            if isinstance(data['additionalItems'], dict):
                self.additional_items = fields.Nested('self')
            elif isinstance(data['additionalItems'], collections.Sequence):
                self.additional_items = fields.Nested('self', many=True)
        return data

    @pre_dump
    def pre_dump(self, data):
        data = super().pre_dump(data)
        # type: (JSONSchematic) -> Any
        if isinstance(data.items, get_model(self)):
            self.items = fields.Nested('self')
        elif isinstance(data.items, collections.Sequence):
            self.items = fields.Nested('self', many=True)
        if isinstance(data.additional_items, self.__class__):
            self.additional_items = fields.Nested(
                'self',
                load_from='additionalItems',
                dump_to='additionalItems'
            )
        elif isinstance(data.additional_items, bool):
            self.additional_items = fields.Boolean(
                'self',
                load_from='additionalItems',
                dump_to='additionalItems'
            )
        return data

    @post_dump
    def post_dump(
        self,
        data
    ):
        data = super().post_dump(data)
        if ('properties' in data) and (data['properties'] is not None):
            for k, v in copy(data['properties']).items():
                if not isinstance(v, get_model(self)):
                    raise TypeError(v)
                data['properties'][k] = self.__class__(strict=True, many=False).dump(v).data
                if not isinstance(data['properties'][k], dict):
                    raise TypeError(data['properties'][k])
        if ('dependencies' in data) and (data['dependencies'] is not None):
            for kk, vv in copy(data['dependencies']).items():
                if not isinstance(vv, dict):
                    raise TypeError(vv)
                for k, v in vv.items():
                    if isinstance(v, get_model(self)):
                        data['dependencies'][kk][k] = self.__class__(strict=True, many=False).dump(v).data
                    elif not isinstance(v, collections.Sequence):
                        raise TypeError(v)
        return data

    @post_load
    def post_load(
        self,
        data  # type: JSONSchematic
    ):
        data = super().post_load(data=data)
        if data.properties is not missing:
            for k, v in copy(data.properties).items():
                if not isinstance(v, dict):
                    raise TypeError(v)
                data.properties[k] = get_model(self)(**v)
        if data.dependencies is not missing:
            for kk, vv in copy(data.dependencies).items():
                for k, v in copy(vv).items():
                    if isinstance(v, dict):
                        data.dependencies[kk][k] = get_model(self)(**v)
                    elif not isinstance(v, collections.Sequence):
                        raise TypeError(v)
        return data


def serialize_mapping(data, schema, many=False):
    # type: (dict, type, Optional[bool]) -> dict
    if (data is missing) or (data is None):
        return data
    data = copy(data)
    for k, v in data.items():
        if many:
            if not isinstance(v, collections.Sequence):
                raise TypeError(v)
            for vv in v:
                if not isinstance(vv, schema):
                    raise TypeError(vv)
        else:
            if not isinstance(v, schema):
                raise TypeError(v)
        data[k] = schema(strict=True, many=many).dump(v).data
        if many:
            if not isinstance(data[k], dict):
                raise TypeError(data[k])
        else:
            if not isinstance(data[k], collections.Sequence):
                raise TypeError(data[k])
            for vv in data[k]:
                if not isinstance(vv, dict):
                    raise TypeError(vv)
    return data


def deserialize_mapping(data, schema, many=False):
    # type: (dict, type, Optional[bool]) -> dict
    if (data is missing) or (data is None):
        return data
    data = copy(data)
    for k, v in data.items():
        if many:
            if not isinstance(v, collections.Sequence):
                raise TypeError(v)
            data[k] = [
                get_model(schema)(**vv)
                for vv in v
            ]
        else:
            if not isinstance(v, dict):
                raise TypeError(v)
            data[k] = get_model(schema)(**v)
    return data


class ComponentsSchema(JSONObjectSchema):

    schemas = fields.Function(
        serialize=lambda data: serialize_mapping(data, SchematicSchema),
        deserialize=lambda data: deserialize_mapping(data, SchematicSchema),
    )
    responses = fields.Function(
        serialize=lambda data: serialize_mapping(data, ResponseSchema),
        deserialize=lambda data: deserialize_mapping(data, ResponseSchema),
    )
    parameters = fields.Function(
        serialize=lambda data: serialize_mapping(data, JSONObjectSchema),
        deserialize=lambda data: deserialize_mapping(data, JSONObjectSchema),
    )
    examples = fields.Function(
        serialize=lambda data: serialize_mapping(data, JSONObjectSchema),
        deserialize=lambda data: deserialize_mapping(data, JSONObjectSchema),
    )
    request_bodies = fields.Function(
        serialize=lambda data: serialize_mapping(data, JSONObjectSchema),
        deserialize=lambda data: deserialize_mapping(data, JSONObjectSchema),
    )
    headers = fields.Function(
        serialize=lambda data: serialize_mapping(data, JSONObjectSchema),
        deserialize=lambda data: deserialize_mapping(data, JSONObjectSchema),
    )
    security_schemes = fields.Function(
        serialize=lambda data: serialize_mapping(data, JSONObjectSchema),
        deserialize=lambda data: deserialize_mapping(data, JSONObjectSchema),
    )
    links = fields.Function(
        serialize=lambda data: serialize_mapping(data, JSONObjectSchema),
        deserialize=lambda data: deserialize_mapping(data, JSONObjectSchema),
    )
    call_backs = fields.Function(
        serialize=lambda data: serialize_mapping(data, JSONObjectSchema),
        deserialize=lambda data: deserialize_mapping(data, JSONObjectSchema),
    )


class OpenAPISchema(JSONObjectSchema):

    # For Swagger 2.0 Compatibility
    swagger = fields.String(dump_to='swagger', load_from='swagger')

    # OpenAPI 3.0
    open_api = fields.String(dump_to='openapi', load_from='openapi')
    info = fields.Nested(InfoSchema)
    host = fields.String()
    servers = fields.Nested(ServerSchema, many=True)
    base_path = fields.String(dump_to='basePath', load_from='basePath')
    schemes = fields.List(fields.String())
    tags = fields.Nested(TagSchema, many=True)
    paths = fields.Dict()

    @post_load
    def post_load(
        self,
        data
    ):
        """
        This overrides the behavior of ``JSONObjectSchema.post_load`` in order to loads each value in Swagger.paths as an
        instance of the ``Service`` class.
        """
        data = super().post_load(data=data)
        if data.paths is not missing:
            for path, service in copy(data.paths).items():
                if not isinstance(service, dict):
                    raise TypeError(service)
                data.paths[path] = get_model(ServiceSchema)(**service)
        return data

    @post_dump
    def post_dump(
        self,
        data
    ):
        """
        This ensures each value in Swagger.paths is rendered serializable, since ``SwaggerSchema.post_load`` causes
        this dictionary to hold (non-serializable) instances of the ``Service`` class.
        """
        if ('paths' in data) and (data['paths'] is not None):
            for path, service in copy(data['paths']).items():
                if not isinstance(service, Service):
                    raise TypeError(type(service))
                data['paths'][path] = ServiceSchema(strict=True, many=False).dump(service).data
                if not isinstance(data['paths'][path], dict):
                    raise TypeError(data['paths'][path])
        return data


