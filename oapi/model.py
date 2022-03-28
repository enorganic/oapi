import sob
import os
import re
from itertools import chain
from more_itertools import unique_everseen
from typing import (
    IO,
    Any,
    Dict,
    Iterable,
    Iterator,
    Match,
    Optional,
    Sequence,
    Set,
    Tuple,
    Type,
    Union,
    List,
)
from collections import OrderedDict, deque
from io import IOBase
from urllib.parse import urlparse, urljoin
from urllib.request import urlopen
from sob.thesaurus import get_class_meta_attribute_assignment_source
from sob.utilities.inspect import (
    get_source,
    properties_values,
    calling_function_qualified_name,
)
from sob.utilities.string import (
    property_name,
    class_name,
    split_long_docstring_lines,
)
from sob.utilities.string import split_long_comment_line
from sob.utilities import qualified_name, url_relative_to
from sob.utilities.types import Null

from oapi.errors import DuplicateClassNameError
from .oas.references import Resolver
from .oas.model import (
    OpenAPI,
    Properties,
    Schema,
    Reference,
    Parameter,
    Operation,
)

_META_PROPERTIES_QAULIFIED_NAME = qualified_name(sob.meta.Properties)
_META_PROPERTIES_QAULIFIED_NAME_LENGTH = len(_META_PROPERTIES_QAULIFIED_NAME)
_DOC_POINTER_RE = re.compile(
    (
        # Pointer
        r"^(.*?)"
        # Pointer stops at a double-return or end-of-string
        r"(?:\r?\n\s*\r?\n|$)"
    ),
    re.DOTALL,
)
_SPACES_RE = re.compile(r"[\s\n]")
_MODEL_DEFINITION_TYPES: Tuple[Type[sob.abc.Model], ...] = (
    Schema,
    Operation,
    Parameter,
)

# region Functions


def schema_defines_array(schema: Schema) -> bool:
    """
    Schemas of the type `array` translate to an `Array`. Incorrectly
    implemented schemas may also neglect this, however use of the attribute
    `items` is only valid in the context of an array--and therefore indicate
    the schema also defines an instance of `Array`.
    """
    return bool(schema.type_ == "array" or schema.items)


def schema_defines_object(schema: Schema) -> bool:
    """
    If properties are defined for a schema, it will translate to an instance of
    `Object`.
    """
    return (
        (schema.properties and schema.type_ is None)
        or schema.type_ == "object"
    ) and (not schema.additional_properties)


def schema_defines_dictionary(schema: Schema) -> bool:
    """
    If properties are not defined for a schema, or unspecified attributes are
    allowed--the schema will translate to an instance of `sob.abc.Dictionary`.
    """
    return bool(
        schema.type_ == "object"
        and (schema.additional_properties or (not schema.properties))
    )


def schema_defines_model(schema: Schema) -> bool:
    return (
        schema_defines_array(schema)
        or schema_defines_object(schema)
        or schema_defines_dictionary(schema)
    )


# endregion


# region Private Classes


def _get_model_import_class_source(
    model: Type[sob.abc.Model],
) -> Tuple[str, str]:
    model_source: str = get_source(model)
    partitions: Tuple[str, str, str] = model_source.partition("\n\n\n")
    return partitions[0], partitions[2]


def _get_string_property(
    format_: Optional[str], required: bool
) -> sob.abc.Property:
    if format_ == "date-time":
        return sob.properties.DateTime(required=required)
    elif format_ == "date":
        return sob.properties.Date(required=required)
    elif format_ == "byte":
        return sob.properties.Bytes(required=required)
    else:
        return sob.properties.String(required=required)


def _get_type_property(
    type_: Optional[str], format_: Optional[str], required: bool
) -> sob.abc.Property:
    if type_ == "number":
        return sob.properties.Number(required=required)
    elif type_ == "integer":
        return sob.properties.Integer(required=required)
    elif type_ == "string":
        return _get_string_property(format_, required)
    elif type_ == "boolean":
        return sob.properties.Boolean(required=required)
    elif type_ == "file":
        return sob.properties.Bytes(required=required)
    elif type_ == "array":
        return sob.properties.Array(required=required)
    else:
        if type_ and type_ != "object":
            raise ValueError(f"Unknown schema type: {type_}")
        return sob.properties.Property(required=required)


def _types_from_enum_values(
    values: Iterable[sob.abc.MarshallableTypes],
) -> sob.abc.Types:
    types: sob.abc.MutableTypes = sob.types.MutableTypes()

    def add_value_type(value: sob.abc.MarshallableTypes) -> None:
        type_: type = type(value)
        if type_ not in types:
            types.append(type_)

    deque(map(add_value_type, values), maxlen=0)
    return types


def _append_property_type(
    property_: sob.abc.Property, type_: Union[type, sob.abc.Property]
) -> sob.abc.Property:
    if type_ not in (property_.types or ()):
        if not isinstance(property_.types, sob.abc.MutableTypes):
            property_ = sob.properties.Property(
                name=property_.name,
                types=sob.types.MutableTypes(property_.types or ()),
                required=property_.required,
                versions=property_.versions,
            )
        assert isinstance(property_.types, sob.abc.MutableTypes)
        property_.types.append(type_)
    return property_


class _Modeler:
    """
    This class parses an OpenAPI schema and produces a data model based on the
    `sob` library.
    """

    def __init__(
        self,
        root: OpenAPI,
    ) -> None:
        # This ensures all elements have URLs and JSON pointers
        sob.meta.set_url(root, sob.meta.get_url(root))
        sob.meta.set_pointer(root, sob.meta.get_pointer(root) or "")
        # Private Properties
        self._traversed_relative_urls_pointers: Set[str] = set()
        self._relative_urls_pointers_class_names: Dict[str, str] = {}
        self._class_names_relative_urls_pointers: Dict[str, str] = {}
        self._class_names_meta: Dict[str, sob.abc.Meta] = {}
        self._relative_urls_pointers_models: Dict[
            str, Optional[Type[sob.abc.Model]]
        ] = {}
        self._class_names_models: Dict[str, Optional[Type[sob.abc.Model]]] = {}
        # Public properties
        self.root: OpenAPI = root
        self.resolver: Resolver = Resolver(self.root)
        assert self.root and (self.root.swagger or self.root.openapi)
        self.major_version: int = int(
            (self.root.swagger or self.root.openapi or "0")
            .split(".")[0]
            .strip()
        )

    def get_relative_url_pointer_model(
        self, relative_url_pointer: str
    ) -> Optional[Type[sob.abc.Model]]:
        return self._relative_urls_pointers_models[relative_url_pointer]

    def set_relative_url_pointer_class_name(
        self, relative_url_pointer: str, class_name_: str
    ) -> str:
        """
        Check to see if this pointer already has a class name, and use that
        if it does
        """
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

    def relative_url_pointer_class_name_exists(
        self, relative_url_pointer: str
    ) -> bool:
        return relative_url_pointer in self._relative_urls_pointers_class_names

    def relative_url_pointer_model_exists(
        self, relative_url_pointer: str
    ) -> bool:
        return relative_url_pointer in self._relative_urls_pointers_models

    def class_name_relative_urls_pointer_exists(
        self, class_name_: str
    ) -> bool:
        return class_name_ in self._class_names_relative_urls_pointers

    def get_relative_url_pointer_class_name(
        self, relative_url_pointer: str
    ) -> str:
        return self._relative_urls_pointers_class_names[relative_url_pointer]

    def get_class_name_relative_url_pointer(self, class_name_: str) -> str:
        return self._class_names_relative_urls_pointers[class_name_]

    def extend_property_schemas(
        self,
        property_: sob.abc.Property,
        schemas: Iterable[Union[Schema, Reference]],
    ) -> sob.abc.Property:
        schemas = iter(schemas)
        next_schema: Optional[Schema] = self.next_schema(schemas)
        if next_schema is None:
            return property_
        if property_.types is None:
            property_.types = sob.types.MutableTypes()  # type: ignore
        elif not isinstance(property_.types, sob.abc.MutableTypes):
            property_ = sob.properties.Property(
                types=sob.types.MutableTypes(property_.types)  # type: ignore
            )
        child_property_ = self.get_property(next_schema)
        # Representations are used in lieu of comparing classes directly
        # because in the course of type generation it is possible to create
        # an identical class more than once
        type_representations: Set[str] = set(
            filter(
                None,
                map(sob.utilities.inspect.represent, property_.types or ()),
            )
        ) | {sob.utilities.inspect.represent(property_)}
        if child_property_ and child_property_.types:
            for type_ in child_property_.types:
                if (
                    sob.utilities.inspect.represent(property_)
                    not in type_representations
                ):
                    property_.types.append(type_)  # type: ignore
        return self.extend_property_schemas(property_, schemas)

    def next_schema(
        self, schemas: Iterator[Union[Schema, Reference]]
    ) -> Optional[Schema]:
        next_schema: Union[Schema, Reference]
        try:
            next_schema = next(schemas)
        except StopIteration:
            return None
        if isinstance(next_schema, Reference):
            next_schema = self.resolve_reference(next_schema)  # type: ignore
            assert isinstance(next_schema, Schema)
        return next_schema

    def merge_schemas_properties(
        self,
        meta_properties: sob.abc.Properties,
        schemas: Iterable[Union[Schema, Reference]],
    ) -> None:
        """
        Add property definitions to a properties object based on multiple
        schemas, merging property definitions when defined more than once.

        Parameters:

        - meta_properties (sob.model.Properties)
        - schemas ([Schema|Reference])
        """
        schemas = iter(schemas)
        next_schema: Optional[Schema] = self.next_schema(schemas)
        if next_schema is None:
            return None
        schema_properties: Optional[Properties] = next_schema.properties
        if schema_properties:
            name_: str
            schema: Union[Schema, Reference]
            for name_, schema in schema_properties.items():
                property_name_ = property_name(name_)
                # Prevent property names from conflicting with the dependency
                # module namespace
                if property_name_ == sob.__name__:
                    property_name_ = f"{sob.__name__}_"
                property_: sob.abc.Property
                if property_name_ in meta_properties:
                    if next_schema.required and (
                        name_ in next_schema.required
                    ):
                        meta_properties[property_name_].required = True
                    meta_properties[
                        property_name_
                    ] = self.extend_property_schemas(
                        meta_properties[property_name_], (schema,)
                    )
                else:
                    property_ = self.get_property(
                        schema,
                        name=None if property_name_ == name_ else name_,
                        required=(
                            True
                            if (
                                next_schema.required
                                and (name_ in next_schema.required)
                            )
                            else False
                        ),
                    )
                    meta_properties[property_name_] = property_
        if next_schema.all_of:
            schemas = chain(schemas, next_schema.all_of)
        if next_schema.any_of:
            schemas = chain(schemas, next_schema.any_of)
        if next_schema.one_of:
            schemas = chain(schemas, next_schema.one_of)
        self.merge_schemas_properties(meta_properties, schemas)

    def get_merged_schemas_object_class(
        self,
        schemas: Iterable[Union[Schema, Reference]],
        name: Optional[str] = None,
        relative_url_pointer: Optional[str] = None,
    ) -> Optional[Type[sob.abc.Object]]:
        """
        Obtain a sub-class of `sob.model.Model` from multiple instance of
        `oapi.oas.model.Schema`.

        Parameters:

        - schema (oapi.oas.model.Schema)
        - name (str|None) = None
        - relative_url_pointer (str|None)
        """
        schemas = iter(schemas)
        next_schema: Optional[Schema] = self.next_schema(schemas)
        assert next_schema is not None
        schemas = chain((next_schema,), schemas)
        if name is None:
            name = self.get_schema_class_name(next_schema)
        if relative_url_pointer is None:
            relative_url_pointer = self.get_model_relative_url_pointer(
                next_schema
            )
        meta_properties: sob.abc.Properties = sob.meta.Properties()
        self.merge_schemas_properties(meta_properties, schemas)
        object_meta: sob.abc.ObjectMeta = sob.meta.Object(
            properties=meta_properties
        )
        name = self.set_relative_url_pointer_class_name(
            relative_url_pointer, name
        )
        self._class_names_meta[name] = object_meta
        object_class: Type[
            sob.abc.Object
        ] = sob.model.from_meta(  # type: ignore
            name,
            object_meta,
            docstring=self.get_docstring(next_schema, relative_url_pointer),
            module="__main__",
        )
        return object_class

    def polymorph_property(
        self, property_: sob.abc.Property, schema: Schema
    ) -> sob.abc.Property:
        if schema.any_of:
            property_ = self.extend_property_schemas(property_, schema.any_of)
        if schema.one_of:
            property_ = self.extend_property_schemas(property_, schema.one_of)
        if schema.all_of:
            property_ = self.extend_property_schemas(property_, schema.all_of)
        return property_

    def get_property(
        self,
        schema: Union[Schema, Reference],
        name: Optional[str] = None,
        required: bool = False,
    ) -> sob.abc.Property:
        is_referenced: bool = isinstance(schema, Reference)
        if is_referenced:
            schema = self.resolve_reference(schema)  # type: ignore
        assert isinstance(schema, Schema)
        property_: sob.abc.Property = _get_type_property(
            schema.type_, format_=schema.format_, required=required
        )
        if schema_defines_model(schema):
            model_class: Optional[Type[sob.abc.Model]] = self.get_model_class(
                schema, is_property=(not is_referenced)
            )
            if model_class:
                property_ = _append_property_type(property_, model_class)
        if (
            (schema.any_of is not None)
            or (schema.one_of is not None)
            or (schema.all_of is not None)
        ):
            property_ = self.polymorph_property(property_, schema)
        if schema.enum:
            property_ = sob.properties.Enumerated(
                values=tuple(schema.enum),
                types=(
                    property_.types
                    or _types_from_enum_values(schema.enum)
                    or None
                ),
                required=required,
            )
        if name is not None:
            property_.name = name
        if (
            schema.nullable
            or
            # Swagger/OpenAPI versions prior to 3.0 do not support `nullable`,
            # so it must be assumed that null values are acceptable for
            # required attributes
            (
                (self.major_version < 3)
                and (required is True)
                and (schema.nullable is not False)
            )
        ):
            property_ = _append_property_type(property_, Null)
        if required is not None:
            property_.required = required
        return property_

    def get_relative_url(self, url: str) -> str:
        relative_url: str = ""
        if url:
            parse_result = urlparse(url)
            # Determine if the URL is absolute or relative
            if parse_result.netloc or parse_result.scheme == "file":
                # Only include the relative URL if it is not the root document
                if url == self.resolver.url:
                    relative_url = ""
                else:
                    relative_url = url_relative_to(url, self.resolver.url)
            else:
                relative_url = url
        return relative_url

    def get_model_relative_url_and_pointer(
        self, model: sob.abc.Model
    ) -> Tuple[str, str]:
        """
        Return a relative path in relation to the root document and the pointer
        """
        url: str = sob.meta.url(model) or ""
        pointer: Optional[str] = sob.meta.pointer(model)
        assert pointer
        return self.get_relative_url(url), pointer

    def get_model_relative_url_pointer(self, model: sob.abc.Model) -> str:
        """
        Given a schema/operation/parameter definition, return a relative path +
        pointer in relation to the root document
        """
        relative_url, pointer = self.get_model_relative_url_and_pointer(model)
        return f"{relative_url}{pointer}"

    def set_relative_url_pointer_model(
        self, relative_url_pointer: str, model: Optional[Type[sob.abc.Model]]
    ) -> None:
        self._relative_urls_pointers_models[relative_url_pointer] = model

    def set_model_class_name(
        self,
        model: Optional[Type[sob.abc.Model]],
        class_name_: Optional[str] = None,
    ) -> None:
        if model and not class_name_:
            class_name_ = model.__name__
        assert class_name_
        self._class_names_models[class_name_] = model

    def get_model_class(
        self,
        definition: Union[Schema, Operation, Parameter],
        is_property: bool = False,
    ) -> Optional[Type[sob.abc.Model]]:
        """
        Get a model class from a schema/operation/parameter. This method
        may also return `None` in the case of a referential loop.
        """
        relative_url_pointer = self.get_model_relative_url_pointer(definition)
        cls: Optional[Type[sob.abc.Model]]
        # If this model has already been generated--use the cached model
        if not self.relative_url_pointer_model_exists(relative_url_pointer):
            # Setting this to prevents recursion errors
            self.set_relative_url_pointer_model(relative_url_pointer, None)
            if isinstance(definition, Schema):
                cls = self.get_schema_model_class(
                    definition,
                    relative_url_pointer=relative_url_pointer,
                    is_property=is_property,
                )
            elif isinstance(definition, Operation):
                cls = self.get_operation_model_class(
                    definition,
                    relative_url_pointer=relative_url_pointer,
                    is_property=is_property,
                )
            elif isinstance(definition, Parameter):
                cls = self.get_parameter_model_class(
                    definition,
                    relative_url_pointer=relative_url_pointer,
                    is_property=is_property,
                )
            else:
                raise TypeError(
                    "The model definition must be a "
                    f"`{qualified_name(Schema)}`, "
                    f"`{qualified_name(Operation)}` or "
                    f"`{qualified_name(Parameter)}`, "
                    f"not:\n{repr(definition)}"
                )
            self.set_relative_url_pointer_model(relative_url_pointer, cls)
            self.set_model_class_name(cls)
        return self.get_relative_url_pointer_model(relative_url_pointer)

    @property  # type: ignore
    def model_classes(self) -> Iterable[Type[sob.abc.Model]]:
        models_names: Dict[str, Type[sob.abc.Model]] = {}
        for definition in self.model_definitions:
            model: Optional[Type[sob.abc.Model]] = self.get_model_class(
                definition
            )
            if model:
                if model.__name__ in models_names:
                    existing_model_meta = sob.meta.read(
                        models_names[model.__name__]
                    )
                    new_model_meta = sob.meta.read(model)
                    # Ensure this is just a repeat use of the same model, and
                    # not a different model of the same name
                    if existing_model_meta != new_model_meta:
                        raise RuntimeError(
                            "An attempt was made to define a model using an "
                            'existing model name (`%s`)"\n\n'
                            "Existing Module Metadata:\n\n%s\n\n"
                            "New Module Metadata:\n\n%s"
                            % (
                                model.__name__,
                                repr(existing_model_meta),
                                repr(new_model_meta),
                            )
                        )
                elif model not in (sob.model.Array, sob.model.Dictionary):
                    models_names[model.__name__] = model
                    yield model

    def get_operation_model_class(
        self,
        operation: Operation,
        relative_url_pointer: Optional[str] = None,
        is_property: bool = False,
        required: bool = False,
    ) -> Type[sob.abc.Model]:
        name: str = self.get_operation_class_name(operation)  # noqa
        raise NotImplementedError()  # TODO

    def get_parameter_model_class(
        self,
        parameter: Parameter,
        relative_url_pointer: Optional[str] = None,
        is_property: bool = False,
        required: bool = False,
    ) -> Optional[Type[sob.abc.Model]]:
        return self.get_schema_model_class(
            parameter.schema,  # type: ignore
            name=self.get_parameter_class_name(parameter),
            relative_url_pointer=relative_url_pointer,
            is_property=is_property,
            required=required,
        )

    def get_schema_model_class(
        self,
        schema: Schema,
        name: Optional[str] = None,
        relative_url_pointer: Optional[str] = None,
        is_property: bool = False,
        required: bool = False,
    ) -> Optional[Type[sob.abc.Model]]:
        if name is None:
            name = self.get_schema_class_name(schema, is_property=is_property)
        if relative_url_pointer is None:
            relative_url_pointer = self.get_model_relative_url_pointer(schema)
        if schema_defines_array(schema):
            return self.get_schema_array_class(
                schema,
                name=name,
                relative_url_pointer=relative_url_pointer,
                required=required,
            )
        elif schema_defines_object(schema):
            return self.get_schema_object_class(
                schema, name=name, relative_url_pointer=relative_url_pointer
            )
        elif schema_defines_dictionary(schema):
            return self.get_schema_dictionary_class(
                schema,
                name=name,
                relative_url_pointer=relative_url_pointer,
                required=required,
            )
        else:
            return None

    def merge_array_schemas(
        self, cls: Type[sob.abc.Array], schemas: Iterable[Schema]
    ) -> None:
        """
        Incorporate additional schemas into a the allowed item types
        for a sub-class of `sob.model.Array`.

        Parameters:

        - cls (typing.Type[sob.abc.Array])
        - schemas (oapi.oas.model.Schema)
        """
        meta: sob.abc.ArrayMeta = sob.meta.array_writable(cls)
        meta.item_types = sob.types.MutableTypes(  # type: ignore
            () if meta.item_types is None else meta.item_types
        )
        deque(
            map(
                meta.item_types.append,
                filter(None, map(self.get_property, schemas)),
            ),
            maxlen=0,
        )

    def merge_dictionary_schemas(
        self, cls: Type[sob.abc.Dictionary], schemas: Iterable[Schema]
    ) -> None:
        """
        Incorporate additional schemas into a the allowed value types
        for a sub-class of `sob.model.Dictionary`.

        Parameters:

        - cls (typing.Type[sob.abc.Dictionary])
        - schemas (oapi.oas.model.Schema)
        """
        meta: sob.abc.DictionaryMeta = sob.meta.dictionary_writable(cls)
        meta.value_types = sob.types.MutableTypes(  # type: ignore
            () if meta.value_types is None else meta.value_types
        )
        deque(
            map(
                meta.value_types.append,
                filter(None, map(self.get_property, schemas)),
            ),
            maxlen=0,
        )

    def iter_dereferenced_schemas(
        self,
        schemas: Union[Schema, Reference, Iterable[Union[Schema, Reference]]],
    ) -> Iterable[Schema]:
        """
        Iterate over schemas after having resolving references and
        flattened anyOf/allOf/oneOf.

        Parameters:

        - schemas (oapi.oas.model.Schema|oapi.oas.model.Reference|
          [oapi.oas.model.Schema])
        """
        if schemas:
            dereferenced_schemas: Iterable[Schema]
            if isinstance(schemas, Schema):
                dereferenced_schemas = (schemas,)
            elif isinstance(schemas, Reference):
                dereferenced_schemas = (
                    self.resolve_reference(schemas),  # type: ignore
                )
            else:
                dereferenced_schemas = filter(
                    None, map(self.resolve_reference, schemas)  # type: ignore
                )
            for dereferenced_schema in dereferenced_schemas:
                yield dereferenced_schema
                if dereferenced_schema.any_of:
                    yield from self.iter_dereferenced_schemas(
                        dereferenced_schema.any_of
                    )
                if dereferenced_schema.all_of:
                    yield from self.iter_dereferenced_schemas(
                        dereferenced_schema.all_of
                    )
                if dereferenced_schema.one_of:
                    yield from self.iter_dereferenced_schemas(
                        dereferenced_schema.one_of
                    )

    def get_required_schema_model_or_property(
        self, schema: Schema
    ) -> Union[sob.abc.Property, Type[sob.abc.Model], None]:
        return self.get_schema_model_or_property(schema, required=True)

    def get_schema_model_or_property(
        self,
        schema: Schema,
        required: bool = False,
    ) -> Union[sob.abc.Property, Type[sob.abc.Model], None]:
        type_: Union[Type[sob.abc.Model], sob.abc.Property, None]
        if schema_defines_model(schema):
            type_ = self.get_model_class(schema)
        else:
            type_ = self.get_property(schema, required=required)
        return type_

    def get_schema_array_class(
        self,
        schema: Schema,
        name: Optional[str] = None,
        relative_url_pointer: Optional[str] = None,
        required: bool = False,
    ) -> Type[sob.abc.Array]:
        """
        Get all applicable items schemas
        """
        array_class: Type[sob.abc.Array]
        item_types: Tuple[
            Union[Type[sob.abc.Model], sob.abc.Property], ...
        ] = tuple(
            filter(
                None,
                map(  # type: ignore
                    (
                        self.get_required_schema_model_or_property
                        if required
                        else self.get_schema_model_or_property
                    ),
                    unique_everseen(
                        self.iter_dereferenced_schemas(
                            schema.items  # type: ignore
                        )
                    ),
                ),
            )
        )
        # If item types are defined--create a class, otherwise--use the base
        # class
        if item_types:
            array_meta = sob.meta.Array(item_types=item_types)
            if not name:
                # If the array allows a single type--base the array name on
                # that type in order to allow re-use
                if (
                    len(item_types) == 1
                    and isinstance(item_types[0], type)
                    and issubclass(item_types[0], sob.abc.Model)
                ):
                    name = item_types[0].__name__
                else:
                    name = self.get_schema_class_name(schema)
            name = f"{name}Array"
            if name in self._class_names_models:
                return self._class_names_models[name]  # type: ignore
            else:
                if relative_url_pointer is None:
                    relative_url_pointer = self.get_model_relative_url_pointer(
                        schema
                    )
                name = self.set_relative_url_pointer_class_name(
                    relative_url_pointer, name
                )
                self._class_names_meta[name] = array_meta
                array_class = sob.model.from_meta(  # type: ignore
                    name,
                    array_meta,
                    docstring=self.get_docstring(schema, relative_url_pointer),
                    module="__main__",
                )
        else:
            # If types are not defined, use a generic array class
            array_class = sob.model.Array
        return array_class

    def get_schema_dictionary_class(
        self,
        schema: Schema,
        name: Optional[str] = None,
        relative_url_pointer: Optional[str] = None,
        required: bool = False,
    ) -> Type[sob.abc.Dictionary]:
        """
        If a schema is open-ended (could have "additional", un-named,
        properties), is must be interpreted as a dictionary.

        Parameters:

        - schema (oapi.oas.model.Schema)
        - name (str|None) = None
        - relative_url_pointer (str|None) = None
        - required (bool) = False
        """
        if (
            schema.properties or schema.additional_properties
        ) and not isinstance(schema.additional_properties, bool):
            value_types: Tuple[
                Union[sob.abc.Property, Type[sob.abc.Model]], ...
            ] = tuple(  # type: ignore
                filter(
                    None,
                    map(  # type: ignore
                        (
                            self.get_required_schema_model_or_property
                            if required
                            else self.get_schema_model_or_property
                        ),
                        unique_everseen(
                            chain(
                                (
                                    self.iter_dereferenced_schemas(
                                        schema.properties.values()
                                    )
                                    if schema.properties
                                    else ()
                                ),
                                (
                                    self.iter_dereferenced_schemas(
                                        schema.additional_properties
                                    )
                                    if schema.additional_properties
                                    else ()
                                ),
                            )
                        ),
                    ),
                )
            )
            # Create a new class if value types are specified,
            # otherwise return a generic dictionary model class
            if value_types:
                if not name:
                    # If the array allows a single type--base the array name
                    # on that type in order to allow re-use
                    if (
                        len(value_types) == 1
                        and isinstance(value_types[0], type)
                        and issubclass(value_types[0], sob.abc.Model)
                    ):
                        name = f"{value_types[0].__name__}Dictionary"
                    elif name is None:
                        name = self.get_schema_class_name(schema)
                if relative_url_pointer is None:
                    relative_url_pointer = self.get_model_relative_url_pointer(
                        schema
                    )
                dictionary_meta = sob.meta.Dictionary(value_types=value_types)
                name = self.set_relative_url_pointer_class_name(
                    relative_url_pointer, name
                )
                self._class_names_meta[name] = dictionary_meta
                return sob.model.from_meta(  # type: ignore
                    name,
                    dictionary_meta,
                    docstring=self.get_docstring(schema, relative_url_pointer),
                    module="__main__",
                )
        return sob.model.Dictionary

    def get_docstring(self, schema: Schema, relative_url_pointer: str) -> str:
        if relative_url_pointer is None:
            relative_url_pointer = self.get_model_relative_url_pointer(schema)
        if len(relative_url_pointer) > 116 and relative_url_pointer[0] != "#":
            pointer_split = relative_url_pointer.split("#")
            docstring_lines = [
                f"{pointer_split[0]}\n#{'#'.join(pointer_split[1:])}"
            ]
        else:
            docstring_lines = [relative_url_pointer]
        if schema and schema.description:
            docstring_lines.append(schema.description)
        return split_long_docstring_lines("\n\n".join(docstring_lines))

    def get_schema_object_class(
        self,
        schema: Schema,
        name: Optional[str] = None,
        relative_url_pointer: Optional[str] = None,
    ) -> Type[sob.abc.Object]:
        """
        Obtain a sub-class of `sob.model.Model` from an instance of
        `oapi.oas.model.Schema`.

        Parameters:

        - schema (oapi.oas.model.Schema)
        - name (str|None) = None
        - relative_url_pointer (str|None)
        """
        cls: Optional[
            Type[sob.abc.Object]
        ] = self.get_merged_schemas_object_class(
            chain(
                (schema,),
                (schema.any_of or ()),
                (schema.all_of or ()),
                (schema.one_of or ()),
            ),
            name=name,
            relative_url_pointer=relative_url_pointer,
        )
        assert cls
        return cls

    def get_operation_class_name(self, operation: Operation) -> str:
        """
        Derive a model's class name from an `Operation` object. This only
        applies when one or more parameters are
        "in": "form".
        """
        relative_url, pointer = self.get_model_relative_url_and_pointer(
            operation
        )
        return self.get_relative_url_and_pointer_class_name(
            relative_url, pointer, is_property=True
        )

    def get_parameter_class_name(self, parameter: Parameter) -> str:
        """
        Derive a model's class name from a `Parameter` object
        """
        relative_url, pointer = self.get_model_relative_url_and_pointer(
            parameter
        )
        return self.get_relative_url_and_pointer_class_name(
            relative_url, pointer, is_property=True
        )

    def get_schema_class_name(
        self, schema: Schema, is_property: bool = False
    ) -> str:
        """
        Derive a model's class name from a `Schema` object
        """
        relative_url, pointer = self.get_model_relative_url_and_pointer(schema)
        return self.get_relative_url_and_pointer_class_name(
            relative_url, pointer, is_property=is_property
        )

    def get_relative_url_and_pointer_class_name(
        self, relative_url: str, pointer: str, is_property: bool = False
    ) -> str:
        relative_url_pointer = relative_url + pointer
        if not self.relative_url_pointer_class_name_exists(
            relative_url_pointer
        ):
            parts = [
                part.replace("~1", "/")
                for part in re.sub(
                    r"/(anyOf|allOf|oneOf)/\d+/", "/", pointer.lstrip("#/")
                ).split("/")
            ]
            length = len(parts)
            start_index = 0
            first_part = parts[0].lower()
            if length > 1:
                if first_part in ("definitions", "paths"):
                    start_index += 1
                elif first_part == "components":
                    start_index += 1
                    if length > 2 and parts[1] == "schemas":
                        start_index += 1

            def get_class_name(pointer_start_index: int) -> str:
                relevant_parts = list(parts[pointer_start_index:])
                if relative_url:
                    relevant_parts.insert(0, relative_url)
                if is_property and len(relevant_parts) > 1:
                    relevant_parts.pop(-2)
                return class_name("/".join(relevant_parts))

            relative_url_pointer_class_name = get_class_name(start_index)
            while start_index and (
                self.class_name_relative_urls_pointer_exists(
                    relative_url_pointer_class_name
                )
                and self.get_class_name_relative_url_pointer(
                    relative_url_pointer_class_name
                )
                != relative_url_pointer
            ):
                start_index -= 1
                relative_url_pointer_class_name = get_class_name(start_index)
            # Cache the result
            self.set_relative_url_pointer_class_name(
                relative_url_pointer, relative_url_pointer_class_name
            )
        return self.get_relative_url_pointer_class_name(relative_url_pointer)

    @property  # type: ignore
    def model_definitions(
        self,
    ) -> Iterable[Union[Schema, Parameter, Operation]]:
        """
        This property returns all objects defining a model, namely instances of
        `Schema`, `Parameter`, and `Operation`
        """
        self._traversed_relative_urls_pointers = set()
        for definition in self.iter_model_definitions(self.root, (OpenAPI,)):
            if isinstance(definition, Reference):
                definition = self.resolve_reference(
                    definition, types=_MODEL_DEFINITION_TYPES
                )
            assert isinstance(definition, _MODEL_DEFINITION_TYPES)
            yield definition

    def resolve_reference(
        self,
        reference: Reference,
        types: Union[
            sob.abc.Types, Sequence[Union[type, sob.abc.Property]]
        ] = (),
    ) -> sob.abc.Model:
        """
        If `model_instance` is a reference, get the referenced object.

        Parameters:

        - reference (oapi.oas.model.Reference)
        - types ([Union[type, sob.abc.Property]]) = ()
        """
        url: str = sob.meta.get_url(reference) or ""
        assert reference.ref
        pointer: str = urljoin(
            sob.meta.get_pointer(reference) or "",
            reference.ref,
        )
        resolved_model: sob.abc.Model = self.resolver.get_document(
            url
        ).resolve(pointer, types)
        if resolved_model is reference or (
            isinstance(resolved_model, Reference)
            and resolved_model.ref == reference.ref
        ):
            raise RuntimeError(
                f"`Reference` instance is self-referential: {pointer}"
            )
        if isinstance(resolved_model, Reference):
            resolved_model = self.resolve_reference(
                resolved_model, types=types
            )
        return resolved_model

    def add_traversed(self, model: sob.abc.Model) -> None:
        self._traversed_relative_urls_pointers.add(
            self.get_model_relative_url_pointer(model)
        )

    def is_traversed(self, model: sob.abc.Model) -> bool:
        relative_url_pointer = self.get_model_relative_url_pointer(model)
        return relative_url_pointer in self._traversed_relative_urls_pointers

    def operation_defines_model(self, operation: Operation) -> bool:
        """
        Determine if an operation requires a model (if it describes a form)
        """
        if operation.parameters:
            parameter_or_reference: Union[Parameter, Reference]
            parameter: Parameter
            for parameter in filter(  # type: ignore
                None,
                map(
                    lambda parameter_or_reference: (
                        self.resolve_reference(
                            parameter_or_reference, (Parameter,)
                        )
                        if isinstance(parameter_or_reference, Reference)
                        else parameter_or_reference
                    ),
                    operation.parameters,
                ),
            ):
                if parameter.in_ == "form":  # type: ignore
                    return True
        return False

    def iter_parameter_definitions(
        self,
        parameter: Parameter,
    ) -> Iterable[Union[Schema, Operation, Parameter]]:
        if parameter.schema is not None:
            schema = parameter.schema
            if isinstance(schema, Reference):
                schema = self.resolve_reference(  # type: ignore
                    schema, (Schema,)
                )
            assert isinstance(schema, Schema)
            if schema_defines_model(schema) and not (
                self.is_traversed(schema)
            ):
                yield schema

    def iter_array_definitions(
        self,
        array: sob.abc.Array,
        skip: int = 0,
    ) -> Iterable[Union[Schema, Operation, Parameter]]:
        meta_: Optional[sob.abc.ArrayMeta] = sob.meta.array_read(array)
        for item in array:
            if isinstance(item, sob.abc.Model):
                yield from self.iter_model_definitions(
                    item,
                    (meta_.item_types or () if meta_ else ()),
                    skip=skip,
                )

    def iter_dictionary_definitions(
        self,
        dictionary: sob.abc.Dictionary,
    ) -> Iterable[Union[Schema, Operation, Parameter]]:
        meta_: Optional[sob.abc.DictionaryMeta] = sob.meta.dictionary_read(
            dictionary
        )
        for value in dictionary.values():
            if isinstance(value, sob.abc.Model):
                yield from self.iter_model_definitions(
                    value, (meta_.value_types or () if meta_ else ())
                )

    def iter_object_definitions(
        self,
        object_: sob.abc.Object,
    ) -> Iterable[Union[Schema, Operation, Parameter]]:
        meta_: Optional[sob.abc.ObjectMeta] = sob.meta.object_read(object_)
        if meta_ and meta_.properties:
            name: str
            property_: sob.abc.Property
            for name, property_ in meta_.properties.items():
                value: Any = getattr(object_, name)
                if isinstance(value, sob.abc.Model):
                    yield from self.iter_model_definitions(
                        value,
                        property_.types or (),
                        skip=(
                            2
                            if isinstance(object_, Schema)
                            and (name in ("any_of", "all_of", "one_of"))
                            else 0
                        ),
                    )

    def iter_model_definitions(
        self,
        model: sob.abc.Model,
        types: Union[Sequence[type], sob.abc.Types] = (),
        skip: int = 0,
    ) -> Iterable[Union[Schema, Operation, Parameter]]:
        if isinstance(model, Reference):
            model = self.resolve_reference(model, types)
            skip = 0
        if not self.is_traversed(model):
            self.add_traversed(model)
            # If this is a schema/parameter/operation defining a model--include
            # it in the returned results
            if (
                (not skip)
                and isinstance(model, Schema)
                and schema_defines_model(model)
            ):
                yield model
            elif isinstance(model, Parameter):
                yield from self.iter_parameter_definitions(model)
            elif isinstance(model, Operation):
                if self.operation_defines_model(model):
                    yield model
            # Recursively find other definitions
            if isinstance(model, sob.abc.Dictionary):
                yield from self.iter_dictionary_definitions(model)
            elif isinstance(model, sob.abc.Array):
                yield from self.iter_array_definitions(model, skip=skip - 1)
            elif isinstance(model, sob.abc.Object):
                yield from self.iter_object_definitions(model)
            else:
                raise TypeError(model)

    def represent_model_meta(self, class_name_: str) -> str:
        meta_ = self._class_names_meta[class_name_]
        relative_url_pointer = self.get_class_name_relative_url_pointer(
            class_name_
        )
        lines = list()
        lines.append(split_long_comment_line("# " + relative_url_pointer))
        for property_name_, value in properties_values(meta_):
            if value is not None:
                value = repr(value)
                if value[: _META_PROPERTIES_QAULIFIED_NAME_LENGTH + 1] == (
                    f"{_META_PROPERTIES_QAULIFIED_NAME}("
                ):
                    start: int = _META_PROPERTIES_QAULIFIED_NAME_LENGTH + 1
                    value = value[start:-1]
                lines.append(
                    get_class_meta_attribute_assignment_source(
                        class_name_, property_name_, meta_
                    )
                )
        return "\n".join(lines) + "\n"

    def get_module_source(self) -> str:
        class_names_sources: Dict[str, str] = OrderedDict()
        classes: List[str] = []
        imports: Set[str] = set()
        for model_class in self.model_classes:
            class_name_ = model_class.__name__
            class_imports, class_source = _get_model_import_class_source(
                model_class
            )
            if class_name_ in class_names_sources:
                raise DuplicateClassNameError(
                    f"The class name `{class_name_}` occured twice:\n\n"
                    f"{class_names_sources[class_name_]}\n\n"
                    f"{class_source}"
                )
            class_names_sources[class_name_] = class_source
            deque(
                map(imports.add, filter(None, class_imports.split("\n"))),
                maxlen=0,
            )
            classes.append(class_source)
        return "\n".join(
            chain(
                sorted(
                    imports,
                    key=lambda sort_line: 1
                    if sort_line == "import sob"
                    else 0,
                ),
                ("\n",),
                classes,
                map(self.represent_model_meta, class_names_sources.keys()),
            )
        )


class _ModuleParser:
    def __init__(self, path: str = "") -> None:
        self.namespace: Dict[str, Any] = {}
        if path:
            self.open(path)

    def open(self, path: str) -> None:
        path = os.path.abspath(path)
        current_directory = os.path.abspath(os.curdir)
        os.chdir(os.path.dirname(path))
        try:
            self.namespace["__file__"] = path
            with open(path) as module_io:
                exec(module_io.read(), self.namespace)
        finally:
            os.chdir(current_directory)

    @property
    def models(self) -> Iterable[Type[sob.abc.Model]]:
        for name, value in self.namespace.items():
            if (
                name[0] != "_"
                and isinstance(value, type)
                and issubclass(value, sob.abc.Model)
            ):
                yield value

    @staticmethod
    def _get_class_relative_url_pointer_and_name(
        model: Type[sob.abc.Model],
    ) -> Tuple[str, str]:
        if not model.__doc__:
            return "", ""
        match: Optional[Match[str]] = _DOC_POINTER_RE.search(model.__doc__)
        relative_url_pointer: str = ""
        if match:
            groups = match.groups()
            if groups:
                relative_url_pointer = _SPACES_RE.sub("", groups[0])
        return relative_url_pointer, model.__name__

    @property
    def relative_urls_pointers_class_names(self) -> Iterable[Tuple[str, str]]:
        for model in self.models:
            (
                relative_url_pointer,
                name,
            ) = self._get_class_relative_url_pointer_and_name(model)
            if relative_url_pointer:
                yield relative_url_pointer, name


# endregion


# region Public Classes


def _get_path_modeler(path: str) -> _Modeler:
    with open(path, "r") as model_io:
        assert isinstance(model_io, sob.abc.Readable)
        return _get_io_modeler(model_io)


def _get_url_modeler(url: str) -> _Modeler:
    with urlopen(url) as model_io:
        return _get_io_modeler(model_io)


def _get_io_modeler(model_io: sob.abc.Readable) -> _Modeler:
    return _get_open_api_modeler(OpenAPI(model_io))


def _get_open_api_modeler(open_api: OpenAPI) -> _Modeler:
    return _Modeler(open_api)


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

    def __init__(self, data: Union[str, IOBase, OpenAPI]) -> None:
        self._parser = _ModuleParser()
        self._modeler: _Modeler
        if isinstance(data, str):
            if os.path.exists(data):
                self._modeler = _get_path_modeler(data)
            else:
                self._modeler = _get_url_modeler(data)
        elif isinstance(data, IO):
            self._modeler = _get_io_modeler(data)
        elif isinstance(data, OpenAPI):
            self._modeler = _get_open_api_modeler(data)
        else:
            raise TypeError(
                f"`{calling_function_qualified_name()}` requires an instance "
                f"of `str`, `{qualified_name(OpenAPI)}`, or a file-like "
                f"object for the `data` parameter--not {repr(data)}"
            )

    def __str__(self) -> str:
        return self._modeler.get_module_source()

    def _parse_existing_module(self, path: str) -> None:
        if os.path.exists(path):
            self._parser.open(path)
            for (
                relative_url_pointer,
                class_name_,
            ) in self._parser.relative_urls_pointers_class_names:
                self._modeler.set_relative_url_pointer_class_name(
                    relative_url_pointer, class_name_
                )

    def _get_relative_url_and_pointer(
        self, url_pointer: str
    ) -> Tuple[str, str]:
        relative_url: str = ""
        pointer: str = url_pointer
        if url_pointer[0] != "#":
            url: str
            if "#" in url_pointer:
                url, _, pointer = url_pointer.partition("#")
                pointer = f"#{pointer}"
            else:
                url = url_pointer
                pointer = ""
            relative_url = self._modeler.get_relative_url(url)
        return relative_url, pointer

    def save(self, path: str) -> None:
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
        with open(path, "w") as model_io:
            model_io.write(model_source)

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, self.__class__) and str(self) == str(other)


# For backwards compatibility...
Model = Module

# endregion
