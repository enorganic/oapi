from copy import copy
from marshmallow import Schema, fields, post_load, post_dump, pre_load, pre_dump, missing
from openswallow.model import Service
from openswallow.utilities import bases

# OBJECTS_SCHEMAS = {}


class JSONObjectSchema(Schema):

    __model__ = None

    @pre_load
    def pre_load(
        self,
        data  # type: str
    ):
        return copy(data)

    @pre_dump
    def pre_dump(
        self,
        data  # type: str
    ):
        return copy(data)

    @post_load
    def post_load(
        self,
        data  # type: str
    ):
        """
        :param data:
            A dictionary relating end-point relative paths to JSON representations of the service called at each
            end-point.

        :return:
            An python object (an instance of ``JSONObject``).
        """
        if data is missing:
           return missing
        elif data is None:
           return None
        if self.__model__ is None:
            return None
        try:
            return self.__model__(**data)
        except KeyError:
            raise TypeError(
                'JSON object type ``%s`` is not recognized'
            )


class ResponseSchematicSchema(JSONObjectSchema):

    type = fields.String()
    items = fields.Dict()


class ResponseSchema(JSONObjectSchema):

    description = fields.String()
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
                ss.variables[vn] = ServerVariableSchema.__model__(**v)
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
                if not isinstance(v, ServerVariable):
                    raise TypeError(v)
                data['variables'][vn] = ServerVariableSchema(strict=True, many=False).dump(v).data
                if not isinstance(data['variables'][vn], dict):
                    raise TypeError(data['variables'][vn])
        return data


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
        o = super().post_load(data=data)
        if o.paths is not missing:
            for path, service in copy(o.paths).items():
                if not isinstance(service, dict):
                    raise TypeError(service)
                o.paths[path] = ServiceSchema.__model__(**service)
        return o

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


# for k, v in copy(locals()).items():
#     if isinstance(v, type) and (Schema  in bases(v)):
#         n = v.__name__
#         if n != 'Schema' and n[-6:] == 'Schema':
#             OBJECTS_SCHEMAS[n[:-6]] = v



