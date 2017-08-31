from copy import copy
from marshmallow import Schema, fields, post_load, post_dump, pre_load, pre_dump
from openswallow.model import SCHEMAS_OBJECTS, Service
from openswallow.utilities import bases

OBJECTS_SCHEMAS = {}


class JSONSchema(Schema):

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
            An python object (an instance of ``JSONDict``).
        """
        if data is None:
           return None
        try:
            return SCHEMAS_OBJECTS[self.__class__.__name__](**data)
        except KeyError:
            raise TypeError(
                'JSON object type ``%s`` is not recognized'
            )


# Swagger ("Open API") 2.0


class ResponseSchematicSchema(JSONSchema):

    type = fields.String()
    items = fields.Dict()


class ResponseSchema(JSONSchema):

    description = fields.String()
    schema = fields.Nested(ResponseSchematicSchema)


class ResponsesSchema(JSONSchema):

    success = fields.Nested(ResponseSchema, load_from='200', dump_to='200')
    unauthorized = fields.Nested(ResponseSchema, load_from='401', dump_to='401')
    default = fields.Nested(ResponseSchema)


class ParameterSchema(JSONSchema):

    name = fields.String()
    parameter_in = fields.String(load_from='in', dump_to='in')
    parameter_type = fields.String(load_from='type', dump_to='type')
    required = fields.Boolean()


class ServiceMethodSchema(JSONSchema):

    tags = fields.List(fields.String)
    description = fields.String
    operation_id = fields.String(load_from='operationId', dump_to='operationId')
    parameters = fields.Nested(ParameterSchema, many=True)
    responses = fields.Nested(ResponsesSchema)


class ServiceSchema(JSONSchema):

    get = fields.Dict()
    put = fields.Dict()
    post = fields.Dict()
    patch = fields.Dict()
    delete = fields.Dict()


class TagSchema(JSONSchema):

    name = fields.String()
    description = fields.String()


class InfoSchema(JSONSchema):

    version = fields.String()
    title = fields.String()


class OpenAPISchema(JSONSchema):

    # For Swagger 2.0 Compatibility
    open_api = fields.String(dump_to='openapi', load_from='openapi')

    # OpenAPI 3.0
    swagger = fields.String(dump_to='swagger', load_from='swagger')
    info = fields.Nested(InfoSchema)
    host = fields.String()
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
        This overrides the behavior of ``JSONSchema.post_load`` in order to loads each value in Swagger.paths as an
        instance of the ``Service`` class.
        """
        o = super().post_load(data=data)
        if o.paths is not None:
            for path, service in copy(o.paths).items():
                if not isinstance(service, dict):
                    raise TypeError(service)
                o.paths[path] = SCHEMAS_OBJECTS['ServiceSchema'](**service)
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


for k, v in copy(locals()).items():
    if isinstance(v, type) and (Schema  in bases(v)):
        n = v.__name__
        if n != 'Schema' and n[-6:] == 'Schema':
            OBJECTS_SCHEMAS[n[:-6]] = v



