from copy import copy
from marshmallow import Schema, fields, post_load, post_dump

from swallow.model import SCHEMAS_OBJECTS
from swallow.utilities import bases

OBJECTS_SCHEMAS = {}


class JSONSchema(Schema):

    @post_load
    def post_load(
        self,
        data
    ):
        """
        :param data:
            A dictionary relating end-point relative paths to JSON representations of the service called at each
            end-point.

        :return:
            An python object (an instance of ``JSONDict``).
        """
        try:
            return SCHEMAS_OBJECTS[self.__class__.__name__](**data)  # [:-6]
        except KeyError:
            raise TypeError(
                'JSON object type ``%s`` is not recognized'
            )


# Swagger ("Open API") 2.0


class SwaggerResponseSchematicSchema(JSONSchema):

    type = fields.String()
    items = fields.Dict()


class SwaggerResponseSchema(JSONSchema):

    description = fields.String()
    schema = fields.Nested(SwaggerResponseSchematicSchema)


class SwaggerResponsesSchema(JSONSchema):

    success = fields.Nested(SwaggerResponseSchema, load_from='200', dump_to='200')
    unauthorized = fields.Nested(SwaggerResponseSchema, load_from='401', dump_to='401')
    default = fields.Nested(SwaggerResponseSchema)


class SwaggerParameterSchema(JSONSchema):

    name = fields.String()
    parameter_in = fields.String(load_from='in', dump_to='in')
    parameter_type = fields.String(load_from='type', dump_to='type')
    required = fields.Boolean()


class SwaggerServiceMethodSchema(JSONSchema):

    tags = fields.List(fields.String)
    description = fields.String
    operation_id = fields.String(load_from='operationId', dump_to='operationId')
    parameters = fields.Nested(SwaggerParameterSchema, many=True)
    responses = fields.Nested(SwaggerResponsesSchema)


class SwaggerServiceSchema(JSONSchema):

    get = fields.Dict()
    put = fields.Dict()
    post = fields.Dict()
    patch = fields.Dict()
    delete = fields.Dict()


class SwaggerTagSchema(JSONSchema):

    name = fields.String()
    description = fields.String()


class SwaggerInfoSchema(JSONSchema):

    version = fields.String()
    title = fields.String()


class SwaggerSchema(JSONSchema):

    swagger = fields.String()
    info = fields.Nested(SwaggerInfoSchema)
    host = fields.String()
    base_path = fields.String(dump_to='basePath', load_from='basePath')
    schemes = fields.List(fields.String())
    tags = fields.Nested(SwaggerTagSchema, many=True)
    paths = fields.Dict()

    @post_load
    def post_load(
        self,
        data
    ):
        """
        This overrides the behavior of ``JSONSchema.post_load`` in order to loads each value in Swagger.paths as an
        instance of the ``SwaggerService`` class.
        """
        o = super().post_load(data=data)
        if o.paths is not None:
            for path, service in o.paths.items():
                o.paths[path] = SCHEMAS_OBJECTS['SwaggerServiceSchema'](**service)
        return o

    @post_dump
    def post_dump(
        self,
        data
    ):
        """
        This ensures each value in Swagger.paths is rendered serializable, since ``SwaggerSchema.post_load`` causes
        this dictionary to hold (non-serializable) instances of the ``SwaggerService`` class.
        """
        if 'paths' in data:
            for k, v in data['paths'].items():
                data['paths'][k] = SwaggerServiceSchema().dump(v)
        return data


# Magento


class CredentialsSchema(JSONSchema):

    username = fields.String()
    password = fields.String()


class FilterSchema(JSONSchema):

    field = fields.String()
    value = fields.String()
    condition_type = fields.String()


class SortOrderSchema(JSONSchema):

    field = fields.String()
    direction = fields.String()


class SearchCriteriaSchema(JSONSchema):

    filter_groups = fields.List(
        fields.Nested(FilterSchema, many=True),
        dump_to='filterGroups',
        load_from='filterGroups'
    )
    sort_orders = fields.Nested(
        SortOrderSchema,
        dump_to='sortOrders',
        load_from='sortOrders',
        many=True
    )
    current_page = fields.Integer(load_from='currentPage', dump_to='currentPage')
    page_size = fields.Integer(load_from='pageSize', dump_to='pageSize')


for k, v in copy(locals()).items():
    if isinstance(v, type) and (Schema  in bases(v)):
        n = v.__name__
        if n != 'Schema' and n[-6:] == 'Schema':
            OBJECTS_SCHEMAS[n[:-6]] = v



