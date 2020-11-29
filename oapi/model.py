import os
import re
import collections

from collections import OrderedDict
from io import IOBase
from urllib.parse import urlparse, urljoin
from urllib.request import urlopen

from sob import __name__ as _sob_module_name
from sob import meta
from sob import properties
from sob.thesaurus import get_class_meta_attribute_assignment_source
from sob.types import MutableTypes
from sob.utilities.inspect import (
    get_source, properties_values, calling_function_qualified_name
)
from sob.utilities.string import property_name, class_name
from sob.utilities.string import split_long_comment_line
from sob.model import (
    Model as ModelBase, Object, Dictionary, Array,
    from_meta as model_from_meta
)
from sob.utilities import qualified_name, url_relative_to
from sob.properties import Property
from sob.utilities.types import NoneType, Null
from .oas.references import Resolver
from .oas.model import OpenAPI, Schema, Reference, Parameter, Operation
from typing import Iterable, Sequence, Optional, Tuple, Union, List

_META_MODULE_QUALIFIED_NAME = qualified_name(meta)
_META_PROPERTIES_QAULIFIED_NAME = qualified_name(meta.Properties)
_META_PROPERTIES_QAULIFIED_NAME_LENGTH = len(_META_PROPERTIES_QAULIFIED_NAME)
_DOC_POINTER_RE = re.compile(
    (
        # Pointer
        r'^(.*?)'
        # Pointer stops at a double-return or end-of-string
        r'(?:\r?\n\s*\r?\n|$)'
    ),
    re.DOTALL
)
_SPACES_RE = re.compile(r'[\s\n]')
_LINE_LENGTH = 79  # type: int

# region Functions


def schema_defines_array(schema):
    # type: (Schema) -> bool
    """
    Schemas of the type `array` translate to an `Array`. Incorrectly
    implemented schemas may also neglect this, however use of the attribute
    `items` is only valid in the context of an array--and therefore indicate
    the schema also defines an instance of `Array`.
    """
    return schema.type_ == 'array' or schema.items


def schema_defines_object(schema):
    # type: (Schema) -> bool
    """
    If properties are defined for a schema, it will translate to an instance of
    `Object`.
    """
    return (
        schema.properties and
        schema.type_ in ('object', None) and
        (not schema.additional_properties)
    )


def schema_defines_dictionary(schema):
    # type: (Schema) -> bool
    """
    If properties are not defined for a schema, or unspecified attributes are
    allowed--the schema will translate to an instance of `Dictionary`.
    """
    return schema.type_ == 'object' and (
        schema.additional_properties or (not schema.properties)
    )


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


# endregion


# region Private Classes


class _RecursiveReferencePlaceholder:

    def __init__(self, relative_url_pointer):
        # type: (str) -> None
        self.relative_url_pointer = relative_url_pointer

    def __eq__(self, other):
        # type: (_RecursiveReferencePlaceholder) -> bool
        return (
            self.relative_url_pointer == other.relative_url_pointer
        )


class _Modeler:
    """
    This class parses an OpenAPI schema and produces a data model based on the
    `sob` library.
    """

    def __init__(self, root):
        # type: (Union[IOBase, str], str, Callable) -> None
        if not isinstance(root, OpenAPI):
            root = OpenAPI(root)
        # This ensures all elements have URLs and JSON pointers
        meta.url(root, meta.url(root))
        meta.pointer(root, meta.pointer(root))
        # Private Properties
        self._traversed_relative_urls_pointers = set()
        self._relative_urls_pointers_class_names = {}
        self._class_names_relative_urls_pointers = {}
        self._relative_urls_pointers_meta = {}
        self._class_names_meta = {}
        self._relative_urls_pointers_models = {}
        self._class_names_models = {}
        # Public properties
        self.root = root
        self.resolver = Resolver(self.root)
        self.major_version = int(
            (self.root.swagger or self.root.openapi).split('.')[0].strip()
        )
        self.references = OrderedDict()
        self.pointers_schemas = OrderedDict()
        self.names_models = OrderedDict()
        self.names_schemas = {}
        self.pointers_models = OrderedDict()

    def get_relative_url_pointer_model(self, relative_url_pointer):
        # type: (str) -> Module
        return self._relative_urls_pointers_models[relative_url_pointer]

    def set_relative_url_pointer_class_name(
        self, relative_url_pointer, class_name_
    ):
        # type: (str, str) -> str
        # Check to see if this pointer already has a class name, and use that
        # if it does
        if relative_url_pointer in self._relative_urls_pointers_class_names:
            class_name_ = self._relative_urls_pointers_class_names[
                relative_url_pointer
            ]
        else:
            self._relative_urls_pointers_class_names[
                relative_url_pointer
            ] = class_name_
        self._class_names_relative_urls_pointers[
            class_name_
        ] = relative_url_pointer
        return class_name_

    def relative_url_pointer_class_name_exists(self, relative_url_pointer):
        # type: (str) -> bool
        return relative_url_pointer in self._relative_urls_pointers_class_names

    def relative_url_pointer_model_exists(self, relative_url_pointer):
        # type: (str) -> bool
        return relative_url_pointer in self._relative_urls_pointers_models

    def class_name_relative_urls_pointer_exists(self, class_name_):
        # type: (str) -> bool
        return class_name_ in self._class_names_relative_urls_pointers

    def get_relative_url_pointer_class_name(self, relative_url_pointer):
        # type: (str) -> str
        return self._relative_urls_pointers_class_names[relative_url_pointer]

    def get_class_name_relative_url_pointer(self, class_name_):
        # type: (str) -> str
        return self._class_names_relative_urls_pointers[class_name_]

    def property_any_of(self, property_, schemas):
        # type: (Property, Iterable[Schema]) -> None
        if schemas:
            if property_.types is None:
                property_.types = []
            for schema in schemas:
                child_property_ = self.get_property(schema)
                if child_property_ is not None:
                    property_.types.append(child_property_)

    def property_all_of(self, property_, schemas):
        # type: (Iterable[Schema]) -> None
        """
        TODO
        """
        if schemas:
            if property_.types is None:
                property_.types = []
            for schema in schemas:
                child_property_ = self.get_property(schema)
                if child_property_ is not None:
                    property_.types.append(child_property_)

    def get_property(
        self,
        schema,  # type: Union[Schema, Reference]
        name=None,  # type: Optional[str]
        required=None  # type: Optional[bool]
    ):
        # type: (...) -> properties.Property
        is_referenced = isinstance(schema, Reference)
        schema = self._resolve(schema)
        if (
            (schema.any_of is not None) or
            (schema.one_of is not None) or
            (schema.all_of is not None)
        ):
            property_ = properties.Property(required=required)
            self.property_any_of(property_, schema.any_of)
            self.property_any_of(property_, schema.one_of)
            self.property_all_of(property_, schema.all_of)
        elif schema_defines_model(schema):
            property_ = properties.Property(required=required)
            property_types = self.get_model(
                schema,
                is_property=(not is_referenced)
            )
            if property_types is not None:
                property_.types = (property_types,)
        elif schema.type_ == 'number':
            property_ = properties.Number(required=required)
        elif schema.type_ == 'integer':
            property_ = properties.Integer(required=required)
        elif schema.type_ == 'string':
            if schema.format_ == 'date-time':
                property_ = properties.DateTime(required=required)
            elif schema.format_ == 'date':
                property_ = properties.Date(required=required)
            elif schema.format_ == 'byte':
                property_ = properties.Bytes(required=required)
            else:
                property_ = properties.String(required=required)
        elif schema.type_ == 'boolean':
            property_ = properties.Boolean(required=required)
        elif schema.type_ == 'file':
            property_ = properties.Bytes(required=required)
        else:
            raise ValueError(
                'No schema "type" found:\n' + repr(schema)
            )
        if schema.enum:
            property_ = properties.Enumerated(
                values=tuple(schema.enum),
                types=(property_,),
                required=required
            )
        if name is not None:
            property_.name = name
        if (
            schema.nullable or
            # Swagger/OpenAPI versions prior to 3.0 do not support `nullable`,
            # so it must be assumed that null values are acceptable for
            # required attributes
            ((self.major_version < 3) and (required is True))
        ):
            if schema.nullable is not False:
                name, required, versions = (
                    property_.name, property_.required, property_.versions
                )
                property_.name = (
                    property_.required
                ) = property_.versions = None
                property_ = Property(
                    types=(property_, Null),
                    name=name,
                    required=required,
                    versions=versions
                )
        if required is not None:
            property_.required = required
        return property_

    def get_relative_url(self, url: str) -> str:
        relative_url: str = ''
        if url:
            parse_result = urlparse(url)
            # Determine if the URL is absolute or relative
            if parse_result.netloc or parse_result.scheme == 'file':
                # Only include the relative URL if it is not the root document
                if url == self.resolver.url:
                    relative_url = ''
                else:
                    relative_url = url_relative_to(url, self.resolver.url)
            else:
                relative_url = url
        return relative_url

    def get_definition_relative_url_and_pointer(
        self,
        definition: Union[Schema, Operation, Parameter]
    ) -> Tuple[str, str]:
        """
        Given a schema/operation/parameter definition, return a relative path
        in relation to the root document and the pointer
        """
        url: Optional[str] = meta.url(definition) or ''
        assert isinstance(url, str)
        pointer = meta.pointer(definition)
        return self.get_relative_url(url), pointer

    def get_definition_relative_url_pointer(self, definition):
        # type: (Union[Schema, Operation, Parameter]) -> str
        """
        Given a schema/operation/parameter definition, return a relative path +
        pointer in relation to the root document
        """
        relative_url, pointer = self.get_definition_relative_url_and_pointer(
            definition
        )
        return relative_url + pointer

    def set_relative_url_pointer_model(self, relative_url_pointer, model):
        # type: (str, Optional[sob.model.Model]) -> None
        self._relative_urls_pointers_models[relative_url_pointer] = model

    def set_model_class_name(self, model, class_name_=None):
        # type: (Optional[sob.model.Model], Optional[str]) -> None
        if class_name_ is None:
            class_name_ = model.__name__
        self._class_names_models[class_name_] = model

    def get_model(self, definition, is_property=False, required=False):
        # type: (Union[Schema, Operation, Parameter], bool, bool) -> ModelBase
        relative_url_pointer = self.get_definition_relative_url_pointer(
            definition
        )
        # If this model has already been generated--use the cached model
        if not self.relative_url_pointer_model_exists(relative_url_pointer):
            # Setting this to prevents recursion errors
            self.set_relative_url_pointer_model(
                relative_url_pointer,
                None
            )
            if isinstance(definition, Schema):
                model = self.get_schema_model(
                    definition,
                    relative_url_pointer=relative_url_pointer,
                    is_property=is_property
                )
            elif isinstance(definition, Operation):
                model = self.get_operation_model(
                    definition,
                    relative_url_pointer=relative_url_pointer,
                    is_property=is_property
                )
            elif isinstance(definition, Parameter):
                model = self.get_parameter_model(
                    definition,
                    relative_url_pointer=relative_url_pointer,
                    is_property=is_property,
                    required=required
                )
            else:
                raise TypeError(
                    'The model definition must be a `%s`, `%s` or `%s`, '
                    'not:\n%s'
                    % (
                        qualified_name(Schema),
                        qualified_name(Operation),
                        qualified_name(Parameter),
                        repr(definition)
                    )
                )
            self.set_relative_url_pointer_model(
                relative_url_pointer,
                model
            )
            self.set_model_class_name(model)
        return self.get_relative_url_pointer_model(relative_url_pointer)

    @property
    def models(self):
        # type: (...) -> typing.Iterator[Union[Schema, Operation, Parameter]]
        models_names = {}
        for definition in self.model_definitions:
            model = self.get_model(definition)
            if model.__name__ in models_names:
                existing_model_meta = meta.read(models_names[model.__name__])
                new_model_meta = meta.read(model)
                # Ensure this is just a repeat use of the same model, and not
                # a different model of the same name
                if existing_model_meta != new_model_meta:
                    raise RuntimeError(
                        'An attempt was made to define a model using an '
                        'existing model name (`%s`)"\n\n'
                        'Existing Module Metadata:\n\n%s\n\n'
                        'New Module Metadata:\n\n%s' % (
                            model.__name__,
                            repr(existing_model_meta),
                            repr(new_model_meta)
                        )
                    )
            elif model not in (Array, Dictionary):
                models_names[model.__name__] = model
                yield model

    def get_operation_model(self, operation):
        # type: (Operation) -> type
        name = self.get_operation_class_name(operation)
        # TODO

    def get_parameter_model(self, parameter, required: bool=False):
        # type: (Parameter) -> type
        return self.get_schema_model(
            parameter.schema,
            name=self.get_parameter_class_name(parameter),
            required=required
        )

    def get_schema_model(
        self, schema, name=None, relative_url_pointer=None, is_property=False
    ):
        # type: (Schema, Optional[str], Optional[str], bool) -> type
        if name is None:
            name = self.get_schema_class_name(
                schema,
                is_property=is_property
            )
        if relative_url_pointer is None:
            relative_url_pointer = self.get_definition_relative_url_pointer(
                schema
            )
        if schema_defines_array(schema):
            return self.get_schema_array(
                schema,
                name=name,
                relative_url_pointer=relative_url_pointer
            )
        elif schema_defines_object(schema):
            return self.get_schema_object(
                schema,
                name=name,
                relative_url_pointer=relative_url_pointer
            )
        elif schema_defines_dictionary(schema):
            return self.get_schema_dictionary(
                schema,
                name=name,
                relative_url_pointer=relative_url_pointer
            )
        else:
            return None

    def get_schema_array(
        self, schema, name=None, relative_url_pointer=None,
        required: bool = False
    ):
        # type: (Schema, Optional[str], Optional[str]) -> type
        # Get all applicable items schemas
        items_schemas = self._resolve(schema.items)
        if isinstance(items_schemas, (collections.Sequence, collections.Set)):
            items_schemas = tuple(
                self._resolve(items_schema) for items_schema in items_schemas
            )
        elif items_schemas is not None:
            items_schemas = (items_schemas,)
        item_types = None
        # If item types are defined--create a class, otherwise--use the base
        # class
        if items_schemas:
            item_types = []
            for items_schema in items_schemas:
                if schema_defines_model(items_schema):
                    items_model = self.get_model(
                        items_schema,
                        required=required
                    )
                else:
                    items_model = self.get_property(items_schema)
                # Checking to make sure the model is not `None` is
                # necessary because is some fringe cases (involving cyclic
                # references) a model cannot be retrieved at this point
                if items_model is not None:
                    item_types.append(items_model)
        if item_types:
            array_meta = meta.Array(item_types=item_types)
            # If the array allows a single type--base the array name on that
            # type in order to allow re-use
            if (
                len(item_types) == 1 and isinstance(item_types[0], type) and
                issubclass(item_types[0], ModelBase)
            ):
                name = item_types[0].__name__
            elif name is None:
                name = self.get_schema_class_name(schema)
            name += 'Array'
            if name in self._class_names_models:
                return self._class_names_models[name]
            else:
                if relative_url_pointer is None:
                    relative_url_pointer = (
                        self.get_definition_relative_url_pointer(schema)
                    )
                name = self.set_relative_url_pointer_class_name(
                    relative_url_pointer, name
                )
                self._class_names_meta[name] = array_meta
                array_class = model_from_meta(
                    name,
                    array_meta,
                    docstring=self.get_docstring(schema, relative_url_pointer),
                    module='__main__'
                )
        else:
            array_class = Array
        return array_class

    def get_schema_dictionary(
        self, schema, name=None, relative_url_pointer=None,
        required: bool = False
    ):
        # type: (Schema, Optional[str], Optional[str], bool) -> type
        # Get the value type schema, if applicable
        if isinstance(schema.additional_properties, (Schema, Reference)):
            if name is None:
                name = self.get_schema_class_name(schema)
            if relative_url_pointer is None:
                relative_url_pointer = (
                    self.get_definition_relative_url_pointer(schema)
                )
            name += 'Dictionary'
            dictionary_meta = meta.Dictionary()
            value_type = self.get_model(
                self._resolve(
                    schema.additional_properties
                ),
                required=required
            )
            dictionary_meta.value_types = (value_type,)
            name = self.set_relative_url_pointer_class_name(
                relative_url_pointer, name
            )
            self._class_names_meta[name] = dictionary_meta
            dictionary_class = model_from_meta(
                name,
                dictionary_meta,
                docstring=self.get_docstring(schema, relative_url_pointer),
                module='__main__'
            )
        else:
            dictionary_class = Dictionary
        return dictionary_class

    def get_docstring(self, schema, relative_url_pointer):
        # type: (Schema, str) -> type
        if relative_url_pointer is None:
            relative_url_pointer = self.get_definition_relative_url_pointer(
                schema
            )

        if len(relative_url_pointer) > 116 and relative_url_pointer[0] != '#':
            pointer_split = relative_url_pointer.split('#')
            docstring_lines = [
                pointer_split[0] + '\n' +
                '#' + '#'.join(pointer_split[1:])
            ]
        else:
            docstring_lines = [relative_url_pointer]
        if schema and schema.description:
            docstring_lines.append(schema.description)
        return '\n\n'.join(docstring_lines)

    def get_schema_object(self, schema, name=None, relative_url_pointer=None):
        # type: (Schema, Optional[str], Optional[str]) -> type
        if name is None:
            name = self.get_schema_class_name(schema)
        if relative_url_pointer is None:
            relative_url_pointer = self.get_definition_relative_url_pointer(
                schema
            )
        object_meta = meta.Object()
        for name_, property_ in schema.properties.items():
            property_name_ = property_name(name_)
            # Prevent property names from conflicting with the dependency
            # module namespace
            if property_name_ == _sob_module_name:
                property_name_ = _sob_module_name + '_'
            object_meta.properties[property_name_] = self.get_property(
                property_,
                name=None if property_name_ == name_ else name_,
                required=(
                    True if (
                        schema.required and (
                            name_ in schema.required
                        )
                    ) else False
                )
            )
        name = self.set_relative_url_pointer_class_name(
            relative_url_pointer, name
        )
        self._class_names_meta[name] = object_meta
        return model_from_meta(
            name,
            object_meta,
            docstring=self.get_docstring(schema, relative_url_pointer),
            module='__main__'
        )

    def get_operation_class_name(self, operation):
        # type: (Operation) -> str
        """
        Derive a model's class name from an `Operation` object. This only
        applies when one or more parameters are
        "in": "form".
        """
        relative_url, pointer = self.get_definition_relative_url_and_pointer(
            operation
        )
        return self.get_relative_url_and_pointer_class_name(
            relative_url, pointer, is_property=True
        )

    def get_parameter_class_name(self, parameter):
        # type: (Parameter) -> str
        """
        Derive a model's class name from a `Parameter` object
        """
        relative_url, pointer = self.get_definition_relative_url_and_pointer(
            parameter
        )
        return self.get_relative_url_and_pointer_class_name(
            relative_url, pointer, is_property=True
        )

    def get_schema_class_name(self, schema, is_property=False):
        # type: (Schema, bool) -> str
        """
        Derive a model's class name from a `Schema` object
        """
        relative_url, pointer = self.get_definition_relative_url_and_pointer(
            schema
        )
        return self.get_relative_url_and_pointer_class_name(
            relative_url, pointer, is_property=is_property
        )

    def get_relative_url_and_pointer_class_name(
        self, relative_url, pointer, is_property=False
    ):
        # type: (str, str, Optional[bool]) -> str
        relative_url_pointer = relative_url + pointer
        if not self.relative_url_pointer_class_name_exists(relative_url_pointer):
            parts = [
                part.replace('~1', '/') for part in
                pointer.lstrip('#/').split('/')
            ]
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

            def get_class_name(pointer_start_index):
                # type: (int) -> str
                relevant_parts = list(parts[pointer_start_index:])
                if relative_url:
                    relevant_parts.insert(0, relative_url)
                if is_property and len(relevant_parts) > 1:
                    relevant_parts.pop(-2)
                return class_name(
                    '/'.join(relevant_parts)
                )

            relative_url_pointer_class_name = get_class_name(start_index)
            while start_index and (
                    self.class_name_relative_urls_pointer_exists(relative_url_pointer_class_name) and
                    self.get_class_name_relative_url_pointer(
                    relative_url_pointer_class_name
                ) != relative_url_pointer
            ):
                start_index -= 1
                relative_url_pointer_class_name = get_class_name(start_index)
            # Cache the result
            self.set_relative_url_pointer_class_name(
                relative_url_pointer, relative_url_pointer_class_name
            )
        return self.get_relative_url_pointer_class_name(relative_url_pointer)

    @property
    def model_definitions(self):
        # type: (...) -> Tuple[str, str, ModelBase]
        """
        This property returns all objects defining a model, namely instances of
        `Schema`, `Parameter`, and `Operation`
        """
        self._traversed_relative_urls_pointers = set()
        for definition in tuple(
            self._traverse_model_definitions(
                self.root,
                (OpenAPI,)
            )
        ):
            yield self._resolve(definition)

    def _resolve(self, model_instance, types=None):
        # type: (ModelBase, Optional[Sequence[type, Property]]) -> ModelBase
        """
        If `model_instance` is a reference, get the referenced object
        """
        if isinstance(model_instance, Reference):
            if types is None:
                types = (Schema,)
            url = meta.url(model_instance) or ''
            pointer = urljoin(
                meta.pointer(model_instance),
                model_instance.ref
            )
            while isinstance(model_instance, Reference):
                resolved_model_instance = self.resolver.get_document(
                    url
                ).resolve(
                    pointer,
                    types
                )
                if resolved_model_instance is model_instance:
                    raise RuntimeError(
                        '`Reference` instance is self-referential: ' +
                        pointer
                    )
                else:
                    model_instance = resolved_model_instance
            if isinstance(model_instance, Reference):
                raise RuntimeError(pointer)
        return model_instance

    def _add_traversed_definition(
        self,
        definition  # type: ModelBase
    ):
        # type: (...) -> None
        self._traversed_relative_urls_pointers.add(
            self.get_definition_relative_url_pointer(definition)
        )

    def _is_traversed_definition(
        self,
        definition  # type: ModelBase
    ):
        # type: (...) -> bool
        relative_url_pointer = self.get_definition_relative_url_pointer(
            definition
        )
        return relative_url_pointer in self._traversed_relative_urls_pointers

    def _traverse_model_definitions(
        self,
        model_instance,  # type: ModelBase
        types=None  # type: Optional[Union[type, properties.Property]]
    ):
        # type: (...) -> typing.Iterator[Union[Schema, Operation, Parameter]]
        assert isinstance(model_instance, ModelBase)
        model_instance = self._resolve(model_instance, types)
        if not self._is_traversed_definition(model_instance):
            self._add_traversed_definition(model_instance)
            # If this is a schema/parameter/operation defining a model--include
            # it in the returned results
            if (
                isinstance(model_instance, Schema) and
                schema_defines_model(model_instance)
            ):
                yield model_instance
            elif isinstance(model_instance, Parameter):
                if model_instance.schema is not None:
                    schema = self._resolve(model_instance.schema)
                    if schema_defines_model(schema) and not (
                        self._is_traversed_definition(schema)
                    ):
                        yield schema
            elif isinstance(
                model_instance, Operation
            ) and operation_defines_model(model_instance):
                yield model_instance
            meta_ = meta.read(model_instance)
            # Recursively find other definitions
            if isinstance(model_instance, Dictionary):
                for key, value in model_instance.items():
                    if isinstance(value, ModelBase):
                        for definition in self._traverse_model_definitions(
                            value, meta_.value_types
                        ):
                            yield definition
            elif isinstance(model_instance, Array):
                for item in model_instance:
                    if isinstance(item, ModelBase):
                        for definition in self._traverse_model_definitions(
                            item, meta_.item_types
                        ):
                            yield definition
            elif isinstance(model_instance, Object):
                for name, property_ in meta_.properties.items():
                    value = getattr(model_instance, name)
                    if isinstance(value, ModelBase):
                        for definition in self._traverse_model_definitions(
                            value, (property_,)
                        ):
                            yield definition
            else:
                raise TypeError(model_instance)

    def represent_model_meta(self, class_name_: str) -> str:
        meta_ = self._class_names_meta[class_name_]
        relative_url_pointer = self.get_class_name_relative_url_pointer(
            class_name_
        )
        lines = list()
        lines.append(
            split_long_comment_line(
                '# ' + relative_url_pointer
            )
        )
        for property_name_, value in properties_values(meta_):
            if value is not None:
                value = repr(value)
                if value[:_META_PROPERTIES_QAULIFIED_NAME_LENGTH + 1] == (
                    _META_PROPERTIES_QAULIFIED_NAME + '('
                ):
                    value = value[
                        _META_PROPERTIES_QAULIFIED_NAME_LENGTH + 1:
                        -1
                    ]
                lines.append(
                    get_class_meta_attribute_assignment_source(
                        class_name_,
                        property_name_,
                        meta_
                    )
                    # 'setattr(\n'
                    # '    {}.writable(\n'
                    # '        {}{}\n'
                    # '    ),\n'
                    # '    "{}",\n'
                    # '    {}\n'
                    # ')'.format(
                    #     _META_MODULE_QUALIFIED_NAME,
                    #     class_name_,
                    #     (
                    #         '  # noqa'
                    #         if len(class_name_) + 8 > _LINE_LENGTH else
                    #         ''
                    #     ),
                    #     property_name_,
                    #     '\n'.join(
                    #         '    {}{}'.format(
                    #             line,
                    #             (
                    #                 '  # noqa'
                    #                 if len(line) + 4 > _LINE_LENGTH else
                    #                 ''
                    #             )
                    #         )
                    #         for line in value.split('\n')
                    #     )
                    # )
                )
        return '\n'.join(lines) + '\n'

    @staticmethod
    def represent_model(model):
        # type: (ModelBase) -> Tuple[str, str]
        model_source: str = get_source(model)
        sections: Sequence[str] = model_source.split('\n\n\n')
        if len(sections) != 2:
            raise ValueError(
                'Model source contains unexpected content:\n' +
                model_source
            )
        return sections

    @property
    def module_definition(self) -> str:
        class_names_sources = OrderedDict()
        classes: List[str] = []
        imports: List[str] = []
        for model_class in self.models:
            class_name_ = model_class.__name__
            imports_str, source = self.represent_model(model_class)
            if class_name_ in class_names_sources:
                raise RuntimeError(
                    'The class name `%s` occured twice:\n\n%s\n\n%s' % (
                        class_name_,
                        class_names_sources[class_name_],
                        source
                    )
                )
            class_names_sources[class_name_] = source
            # Only include each import once
            line: str
            for line in imports_str.split('\n'):
                if line not in imports:
                    imports.append(line)
            classes.append(source)
        return '\n'.join(
            sorted(
                imports,
                key=lambda sort_line: 1 if sort_line == 'import sob' else 0
            ) + ['\n'] +
            classes + [
                self.represent_model_meta(class_name_)
                for class_name_ in class_names_sources.keys()
            ]
        )


class _ModuleParser:

    def __init__(self, path=None):
        # type: (Optional[str]) -> None
        self._relative_urls_pointers_class_names = None  # type: Optional[dict]
        self.namespace = {}
        if path is not None:
            self.open(path)

    def open(self, path=None):
        # type: (Optional[str]) -> None
        path = os.path.abspath(path)
        current_directory = os.path.abspath(os.curdir)
        os.chdir(os.path.dirname(path))
        self.namespace['__file__'] = path
        with open(path) as module_io:
            exec(module_io.read(), self.namespace)
        os.chdir(current_directory)

    @property
    def models(self):
        # type: (...) -> Iterable[type]
        for name, value in self.namespace.items():
            if (
                name[0] != '_' and isinstance(value, type) and
                issubclass(value, ModelBase)
            ):
                yield value

    @staticmethod
    def _get_model_relative_url_pointer_and_class_name(model):
        # type: (type) -> str
        match = _DOC_POINTER_RE.search(
            model.__doc__
        )
        relative_url_pointer = None
        if match:
            groups = match.groups()
            if groups:
                relative_url_pointer = _SPACES_RE.sub('', groups[0])
        return relative_url_pointer, model.__name__

    @property
    def relative_urls_pointers_class_names(self):
        # type: (...) -> Iterator[str, str]
        for model in self.models:
            relative_url_pointer, name = (
                self._get_model_relative_url_pointer_and_class_name(model)
            )
            if relative_url_pointer is not None:
                yield relative_url_pointer, name


# endregion


# region Public Classes


class Module:
    """
    This class parses an Open API document and outputs a module defining
    classes to represent each schema defined in the Open API document as a
    subclass of `sob.model.Module`.

    Initialization Parameters:

    - data (str|http.client.HTTPResponse|io.IOBase|oapi.oas.model.OpenAPI):

      The input data can be a URL, file-path, an HTTP response
      (`http.client.HTTPResponse`), a file object, or an
      instance of `oapi.oas.model.OpenAPI`.
    """

    def __init__(self, data):
        # type: (Union[str, IOBase, OpenAPI]) -> None
        self._modeler = None  # type: _Modeler
        self._parser = _ModuleParser()
        if isinstance(data, str):
            if os.path.exists(data):
                self._path_init(data)
            else:
                self._url_init(data)
        elif isinstance(data, IOBase):
            self._io_init(data)
        elif isinstance(data, OpenAPI):
            self._model_init(data)
        else:
            raise TypeError(
                '`%s` requires an instance of `str`, `%s`, or `%s` for the '
                '`data` parameter--not %s' % (
                    calling_function_qualified_name(),
                    qualified_name(IOBase),
                    qualified_name(OpenAPI),
                    repr(data)
                )
            )

    def _path_init(self, path):
        # type: (str) -> None
        with open(path, 'r') as model_io:
            self._io_init(model_io)

    def _url_init(self, url):
        # type: (str) -> None
        with urlopen(url) as model_io:
            self._io_init(model_io)

    def _io_init(self, model_io):
        # type: (IOBase) -> None
        self._model_init(OpenAPI(model_io))

    def _model_init(self, model):
        # type: (OpenAPI) -> None
        self._modeler = _Modeler(model)

    def __str__(self):
        # type: (...) -> str
        return self._modeler.module_definition

    def _parse_existing_module(self, path):
        # type: (str) -> None
        if os.path.exists(path):
            self._parser.open(path)
            for relative_url_pointer, class_name_ in (
                self._parser.relative_urls_pointers_class_names
            ):
                self._modeler.set_relative_url_pointer_class_name(
                    relative_url_pointer, class_name_
                )

    def _get_relative_url_and_pointer(self, url_pointer):
        # type: (str) -> str
        relative_url = ''
        pointer = url_pointer
        if url_pointer[0] != '#':
            if '#' in url_pointer:
                key_split = url_pointer.split('#')
                relative_url = self._modeler.get_relative_url(key_split[0])
                pointer = '#' + '#'.join(key_split[1:])
            else:
                relative_url = url_pointer
                pointer = ''
        return relative_url, pointer

    def model_from_pointer(self, url_pointer):
        # type: (str) -> Module
        """
        Return a model from a pointer
        """
        relative_url, pointer = self._get_relative_url_and_pointer(url_pointer)
        return self._modeler.get_relative_url_pointer_model(
            relative_url + pointer
        )

    def save(self, path):
        # type: (str) -> None

        """
        This method will save the generated module to a given path. If there is
        an existing module at that path--the existing module will be imported
        and the pre-existing class names will be utilized for any schemas
        defined by elements residing at the same location as the documented
        JSON pointer in the pre-existing classes' docstrings.
        """
        # Make sure that any matching, existing classes use the same names
        self._parse_existing_module(path)
        model_source: str = str(self)
        # Save the module
        with open(path, 'w') as model_io:
            model_io.write(model_source)

    def __eq__(self, other):
        # type: (Module) -> bool
        return isinstance(other, self.__class__) and str(self) == str(other)


# For backwards compatibility...
Model = Module

# endregion