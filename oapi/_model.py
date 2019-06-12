# region Backwards Compatibility

from __future__ import nested_scopes, generators, division, absolute_import, with_statement, \
   print_function, unicode_literals

import collections

from sob.properties import Property, Null
from sob.utilities.compatibility import backport

backport()  # noqa

# endregion

import re
from collections import OrderedDict
from urllib.parse import urljoin, urlparse

from io import IOBase

from sob.utilities import class_name, get_source, camel_split, property_name, properties_values, qualified_name,\
    class_name

import urlesque

from sob.model import Model, Object, Dictionary, Array, unmarshal, marshal, from_meta
from sob import meta
from sob import properties
from sob.utilities import qualified_name, url_relative_to

from .oas.references import Resolver
from .oas.model import OpenAPI, Schema, Reference, Parameter, Operation


DEPENDENCY_NAMESPACE = 'sob'

_POINTER_RE = re.compile(r'{(?:[^{}]+)}')

_META_PROPERTIES_QAULIFIED_NAME = qualified_name(meta.Properties)
_META_PROPERTIES_QAULIFIED_NAME_LENGTH = len(_META_PROPERTIES_QAULIFIED_NAME)


def schema_defines_array(schema):
    # type: (Schema) -> bool
    """
    Schemas of the type `array` translate to an `Array`. Incorrectly implemented schemas may also neglect this, however
    use of the attribute `items` is only valid in the context of an array--and therefore indicate the schema also
    defines an instance of `Array`.
    """
    return schema.type_ == 'array' or schema.items


def schema_defines_object(schema):
    # type: (Schema) -> bool
    """
    If properties are defined for a schema, it will translate to an instance of `Object`.
    """
    return (
        schema.type_ == 'object' and
        schema.properties and
        (not schema.additional_properties)
    )


def schema_defines_dictionary(schema):
    # type: (Schema) -> bool
    """
    If properties are not defined for a schema, or unspecified attributes are allowed--the schema will translate to an
    instance of `Dictionary`.
    """
    return schema.type_ == 'object' and (schema.additional_properties or (not schema.properties))


def schema_defines_model(schema):
    # type: (Schema) -> bool
    return (
        schema_defines_array(schema) or
        schema_defines_object(schema) or
        schema_defines_dictionary(schema)
    )


def operation_defines_model(operation):
    # type: (Operation) -> bool
    """
    Determine if an operation requires a model (if it describes a form)
    """
    if operation.parameters:
        for parameter in operation.parameters:
            if parameter.in_ == 'form':
                return True
    return False


class _Modeler(object):
    """
    This class parses an OpenAPI schema and produces a data model based on the `sob` library.
    """

    def __init__(self, root):

        # type: (Union[IOBase, str], str, Callable) -> None
        if not isinstance(root, OpenAPI):
            root = OpenAPI(root)

        # This ensures all elements have URLs and JSON pointers
        meta.url(root, meta.url(root))
        meta.pointer(root, meta.pointer(root))

        self._pointers_class_names = {}
        self._class_names_pointers = {}
        self._pointers_class_names_meta = {}
        self._pointers_models = {}

        self.resolver = Resolver(root)
        self.major_version = int((root.swagger or root.openapi).split('.')[0].strip())
        self.root = root
        self.references = OrderedDict()
        self.pointers_schemas = OrderedDict()
        self.names_models = OrderedDict()
        self.names_schemas = {}
        self.pointers_models = OrderedDict()

    def get_property(self, schema, name=None, required=None):
        # type: (Union[Schema, Reference], Optional[str], Optional[bool]) -> properties.Property

        assert isinstance(schema, Schema)

        pointer = meta.url(schema) + meta.pointer(schema)

        if (schema.any_of is not None) or (schema.one_of is not None):
            property = properties.Property()
            types = []
            if schema.any_of is not None:
                i = 0
                for s in schema.any_of:
                    p = self.get_property(s)
                    types.append(p)
                    i += 1
            if schema.one_of is not None:
                i = 0
                for s in schema.one_of:
                    p = self.get_property(s)
                    types.append(p)
                    i += 1
            property.types = tuple(types)
        elif schema.all_of is not None:
            property = properties.Dictionary()
            # TODO: schema.all_of
            # i = 0
            # for s in schema.all_of:
            #     p = self.get_property(s)
            #     i += 1
        elif schema.type_ == 'object' or schema.properties or schema.additional_properties:
            if schema.additional_properties:
                additional_properties = schema.additional_properties
                property = properties.Dictionary()
                if not isinstance(additional_properties, bool):
                    property_value_types = []
                    property_value_types.append(self.get_property(additional_properties))
                    if schema.properties:
                        for schema_property in schema.properties.values():
                            property_value_types.append(self.get_property(schema_property))
                    property.value_types = property_value_types
            elif schema.properties:
                property = properties.Property()
                if pointer in self.pointers_models:
                    property.types = (self.pointers_models[pointer],)
            else:
                property = properties.Dictionary()
        elif schema.type_ == 'array' or schema.items:
            property = properties.Array()
            items = schema.items
            if items:
                item_types = []
                if isinstance(items, (Schema, Reference)):
                    items = self._resolve(items)
                    item_type_property = self.get_property(items)
                    if (
                        item_type_property.types and
                        len(item_type_property.types) == 1 and
                        not isinstance(
                            item_type_property,
                            (
                                properties.Date,
                                properties.DateTime,
                                properties.Array,
                                properties.Dictionary
                            )
                        )
                    ):
                        item_types = item_type_property.types
                    elif item_type_property.types:
                        item_types = (item_type_property,)
                else:
                    for item in items:
                        item_type_property = self.get_property(item)
                        if (
                            item_type_property.types and
                            len(item_type_property.types) == 1 and
                            not isinstance(
                                item_type_property,
                                (
                                    meta.Date,
                                    meta.DateTime,
                                    meta.Array,
                                    meta.Dictionary
                                )
                            )
                        ):
                            item_types.append(item_type_property.types[0])
                        elif item_type_property.types:
                            item_types.append(item_type_property)
                if item_types:
                    property.item_types = item_types
        elif schema.type_ == 'number':
            property = properties.Number()
        elif schema.type_ == 'integer':
            property = properties.Integer()
        elif schema.type_ == 'string':
            if schema.format_ == 'date-time':
                property = properties.DateTime()
            elif schema.format_ == 'date':
                property = properties.Date()
            elif schema.format_ == 'byte':
                property = properties.Bytes()
            else:
                property = properties.String()
        elif schema.type_ == 'boolean':
            property = properties.Boolean()
        elif schema.type_ == 'file':
            property = properties.Bytes()
        else:
            raise ValueError(schema.type_)
        if schema.enum:
            property = properties.Enumerated(
                values=tuple(schema.enum),
                types=(property,)
            )
        if name is not None:
            property.name = name
        if (
            schema.nullable or
            # Swagger/OpenAPI versions prior to 3.0 do not support `nullable`, so it must be assumed that
            # null values are acceptable for required attributes
            ((self.major_version < 3) and (required is True))
        ):
            if schema.nullable is not False:
                name, required, versions = property.name, property.required, property.versions
                property.name = property.required = property.versions = None
                property = Property(
                    types=(property, Null),
                    name=name,
                    required=required,
                    versions=versions
                )
        if required is not None:
            property.required = required
        return property

    def get_relative_url_pointer(self, definition):
        # type: (Union[Schema, Operation, Parameter]) -> str
        """
        Given a schema/operation/parameter definition, return a relative path + pointer in relation to the root document
        """

        url = meta.url(definition)
        pointer = meta.pointer(definition)

        # Determine if the URL is absolute or relative
        if urlparse(url).netloc:

            if url == self.resolver.url:
                relative_url = ''
            else:
                relative_url = url_relative_to(url, self.resolver.url)

        else:

            relative_url = url

    def get_model(self, definition):
        # type: (Union[Schema, Operation, Parameter]) -> Model

        relative_url_pointer = self.get_relative_url_pointer(definition)

        if isinstance(definition, Schema):
            model = self.get_schema_model(definition)
        elif isinstance(definition, Operation):
            model = self.get_operation_model(definition)
        elif isinstance(definition, Parameter):
            model = self.get_parameter_model(definition)

    @property
    def models(self):
        # type: (...) -> typing.Iterator[Union[Schema, Operation, Parameter]]
        for definition in self.model_definitions:
            yield self.get_model(definition)

    def get_operation_model(self, operation):
        # type: (Operation) -> type
        name = self.get_operation_class_name(operation)
        # TODO

    def get_parameter_model(self, parameter):
        # type: (Parameter) -> type
        return self.get_schema_model(
            parameter.schema,
            name=self.get_parameter_class_name(parameter)
        )

    def get_schema_model(self, schema, name=None):
        # type: (Schema, Optional[str]) -> type

        if name is None:
            name = self.get_schema_class_name(schema)

        if schema_defines_array(schema):
            return self.get_schema_array(schema, name)
        elif schema_defines_object(schema):
            return self.get_schema_object(schema, name)
        elif schema_defines_dictionary(schema):
            return self.get_schema_dictionary(schema, name)
        else:
            raise ValueError(
                'The schema does not define an object or array: \n' +
                repr(schema)
            )

    def get_schema_array(self, schema, name=None):
        # type: (Schema, Optional[str]) -> type

        name += 'Array'

        # Get all applicable items schemas
        items_schemas = self._resolve(schema.items)
        if isinstance(items_schemas, (collections.Sequence, collections.Set)):
            items_schemas = tuple(self._resolve(items_schema) for items_schema in items_schemas)
        elif items_schemas is not None:
            items_schemas = (items_schemas,)

        pointer = meta.pointer(schema)
        array_meta = meta.Array()
        array_meta.item_types = None

    def get_schema_object(self, schema, name=None):
        # type: (Schema, Optional[str]) -> type

        pointer = meta.pointer(schema)

        object_meta = meta.Object()

        for name_, property_ in schema.properties.items():

            property_name_ = property_name(name_)

            # Prevent property names from conflicting with the dependency module namespace
            if property_name_ == DEPENDENCY_NAMESPACE:
                property_name_ = DEPENDENCY_NAMESPACE + '_'

            object_meta.properties[property_name_] = self.get_property(
                property_,
                name=None if property_name_ == name_ else name_,
                required=True if (schema.required and (name_ in schema.required)) else False
            )

        self._pointers_class_names_meta[pointer] = (name, object_meta)

        if len(pointer) > 116:
            pointer_split = pointer.split('#')
            ds = [
                pointer_split[0] +
                '\n#' + '#'.join(pointer_split[1:])
            ]
        else:
            ds = [pointer]

        if schema.description:
            ds.append(schema.description)

        return from_meta(
            name,
            object_meta,
            docstring='\n\n'.join(ds),
            module='__main__'
        )

    def get_operation_class_name(self, operation):
        # type: (Operation) -> str
        """
        Derive a model's class name from an `Operation` object. This only applies when one or more parameters are
        "in": "form".

        """
        # TODO
        pointer = meta.pointer(operation)

        if pointer not in self._pointers_class_names:

            pass

        return self._pointers_class_names[pointer]

    def get_parameter_class_name(self, parameter):
        # type: (Parameter) -> str
        """
        Derive a model's class name from a `Parameter` object
        """
        # TODO
        pointer = meta.pointer(parameter)

        if pointer not in self._pointers_class_names:

            pass

        return self._pointers_class_names[pointer]

    def get_schema_class_name(self, schema):
        # type: (Schema) -> str
        """
        Derive a model's class name from a `Schema` object
        """
        pointer = meta.pointer(schema)

        if pointer not in self._pointers_class_names:

            parts = pointer.lstrip('#/').split('/')
            length = len(parts)

            start_index = 0

            first_part = parts[0].lower()

            if length > 1:
                if first_part in ('definitions', 'paths'):
                    start_index += 1
                elif first_part == 'components':
                    start_index += 1
                    if length > 2 and parts[1] == 'schemas':
                        start_index += 1

            pointer_class_name = class_name('/'.join(parts[start_index:]))

            while start_index and (
                pointer_class_name in self._class_names_pointers and
                self._class_names_pointers[pointer_class_name] != pointer
            ):
                start_index -= 1
                pointer_class_name = class_name('/'.join(parts[start_index:]))

            # Cache the result
            self._class_names_pointers[pointer_class_name] = pointer
            self._pointers_class_names[pointer] = pointer_class_name
            print(pointer)
            print(pointer_class_name)

        return self._pointers_class_names[pointer]

    @property
    def model_definitions(self):
        # type: (...) -> Tuple[str, str, Model]
        """
        This property returns all objects defining a model, namely instances of `Schema`, `Parameter`, and `Operation`
        """
        for definition in self._traverse_model_definitions(self.root, (OpenAPI,)):
            yield definition

    def _resolve(self, model_instance, types=None):
        # type: (Model, Optional[Sequence[type, Property]]) -> Model
        """
        If `model_instance` is a reference, get the referenced object
        """
        
        if isinstance(model_instance, Reference):

            if types is None:
                types = (Schema,)

            url = meta.url(model_instance)

            model_instance = self.resolver.get_document(url).resolve(
                urljoin(meta.pointer(model_instance), model_instance.ref),
                types
            )

        return model_instance

    def _traverse_model_definitions(
        self,
        model_instance,  # type: Model
        types=None  # type: Optional[Union[type, properties.Property]]
    ):
        # type: (...) -> typing.Iterator[Union[Schema, Operation, Parameter]]

        assert isinstance(model_instance, Model)

        model_instance = self._resolve(model_instance, types)

        # If this is a schema/parameter/operation defining a model--include it in the returned results
        if (
            isinstance(model_instance, Schema) and
            schema_defines_model(model_instance)
        ):
            yield model_instance
        elif isinstance(model_instance, Parameter):
            if model_instance.schema is not None:
                schema = self._resolve(model_instance.schema)
                if schema_defines_model(schema):
                    yield schema
        elif isinstance(model_instance, Operation) and operation_defines_model(model_instance):
            yield model_instance

        if model_instance is not None:

            meta_ = meta.read(model_instance)

            # Recursively find other definitions
            if isinstance(model_instance, Dictionary):
                for key, value in model_instance.items():
                    if isinstance(value, Model):
                        for definition in self._traverse_model_definitions(value, meta_.value_types):
                            yield definition
            elif isinstance(model_instance, Array):
                for item in model_instance:
                    if isinstance(item, Model):
                        for definition in self._traverse_model_definitions(item, meta_.item_types):
                            yield definition
            elif isinstance(model_instance, Object):
                for name, property_ in meta_.properties.items():
                    value = getattr(model_instance, name)
                    if isinstance(value, Model):
                        for definition in self._traverse_model_definitions(value, (property_,)):
                            yield definition
            else:
                raise TypeError(model_instance)

    @property
    def module_definition(self):
        # type: (...) -> str

        lines = []

        for model_class in self.models:

            imports, source = get_source(model_class).split('\n\n\n')

            # Only include the imports once
            if not lines:
                lines.append(imports + '\n\n')

            lines.append(source)

        for pointer, class_name_meta in self.pointers_class_names_meta.items():

            class_name_, meta_ = class_name_meta

            if len(pointer) > 118:
                pointer_split = pointer.split('#')
                lines.append('# ' + pointer_split[0])
                lines.append('# #' + '#'.join(pointer_split[1:]))
            else:
                lines.append('# ' + pointer)

            for property_name_, value in properties_values(meta_):
                if value is not None:
                    value = repr(value)
                    if value[:_META_PROPERTIES_QAULIFIED_NAME_LENGTH + 1] == (
                        _META_PROPERTIES_QAULIFIED_NAME + '('
                    ):
                        value = value[_META_PROPERTIES_QAULIFIED_NAME_LENGTH + 1:-1]
                    lines.append(
                        'sob.meta.writable(%s).%s = %s' % (
                            class_name_, property_name_, value
                        )
                    )

            lines.append('')

        return '\n'.join(lines)
