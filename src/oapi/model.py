from __future__ import annotations

import os
import re
from collections import deque
from copy import copy
from datetime import date, datetime
from functools import partial
from itertools import chain, starmap
from logging import Logger
from pathlib import Path
from re import Match, Pattern
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
)
from urllib.request import urlopen

import sob
from sob.thesaurus import get_class_meta_attribute_assignment_source
from sob.utilities import (
    get_calling_function_qualified_name,
    get_qualified_name,
    get_source,
    iter_properties_values,
)

from oapi._utilities import deprecated, get_type_format_property, iter_distinct
from oapi.errors import OAPIDuplicateClassNameError
from oapi.oas.model import (
    Items,
    OpenAPI,
    Parameter,
    Properties,
    Reference,
    Schema,
)
from oapi.oas.references import Resolver

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, Sequence

_META_PROPERTIES_QAULIFIED_NAME = get_qualified_name(sob.Properties)
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


def _get_schema_type(schema: Schema | Items) -> str | None:
    schema_type: str | None = schema.type_
    if schema_type is None:
        if isinstance(schema, Schema) and (
            schema.properties or schema.additional_properties
        ):
            schema_type = "object"
        elif schema.items:
            schema_type = "array"
    return schema_type


def get_default_class_name_from_pointer(
    pointer: str,
    name: str = "",
    log: Logger | Callable[[str], None] | None = None,
) -> str:
    """
    This function infers a class name from a JSON pointer (or from a
    relative URL concatenated with a JSON pointer) + parameter name (or
    empty string when a parameter name is not applicable). This function is
    the default naming function used by `oapi.model.Module`.

    Parameters:
        pointer: A JSON pointer referencing a schema within an OpenAPI
            document, or a concatenation of a relative URL + "#" + a JSON
            pointer.
        name: The parameter name, or "" if the element is not a
            parameter.
        log: A logger, or a callback function for log messages

    Examples:

    >>> print(
    ...     get_default_class_name_from_pointer(
    ...         "#/paths/~1directory~1sub-directory~1name/get/parameters/1",
    ...         name="argument-name",
    ...     )
    ... )
    DirectorySubDirectoryNameGetArgumentName

    >>> print(
    ...     get_default_class_name_from_pointer(
    ...         "#/paths/~1directory~1sub-directory~1name/get/parameters/1"  #
    ...         "/item",
    ...         name="argument-name",
    ...     )
    ... )
    DirectorySubDirectoryNameGetArgumentNameItem
    """
    relative_url: str = ""
    if "#" in pointer:
        relative_url, pointer = pointer.split("#", 1)
    class_name_: str = pointer.lstrip("/")
    pattern: str
    repl: str
    for pattern, repl in (
        (
            r"/([^\/]+)/responses/200/(content/[^\/]+/)?schema\b",
            r"/\1/response",
        ),
        (
            r"/([^\/]+)/responses/(\d+)/(content/[^\/]+/)?schema\b",
            r"/\1/response/\2",
        ),
        (
            r"/(anyOf|allOf|oneOf)/\d+/",
            "/",
        ),
        (
            r"(?:^components)?(/|^)parameters/([^/]+)/schema(/|$)",
            r"\1\2\3",
        ),
        (
            r"^(components/[^/]+/|definitions/|paths/)",
            "/",
        ),
        (
            r"/properties/",
            "/",
        ),
        (
            r"/items(/|$)",
            r"/item\1",
        ),
        (
            r"~1",
            "/",
        ),
        (
            r"~0",
            "~",
        ),
    ):
        class_name_ = re.sub(pattern, repl, class_name_)
    # For parameters, include the parameter name in the class name *if* the
    # parameter is defined inline (if it's not defined inline, the path to
    # the parameter definition will usually be sufficiently descriptive),
    # and don't include "/parameters/" or the parameter # in the class
    # name.
    if name and not (
        pointer.startswith(("/components/parameters/", "/definitions/"))
    ):
        parameters_pattern: Pattern = re.compile(r"/parameters/\d+((?:/.+)?)$")
        if parameters_pattern.search(class_name_):
            class_name_ = parameters_pattern.sub(f"/{name}/\\1", class_name_)
        else:
            class_name_ = f"{class_name_}/{name}"
    if relative_url:
        class_name_ = f"{relative_url}/{class_name_}"
    if log is not None:  # pragma: no cover
        message: str = (
            f"{pointer} -> {class_name_} (JSON Pointer -> Class Name)"
        )
        if isinstance(log, Logger):
            log.info(message)
        elif callable(log):
            log(message)
    return sob.utilities.get_class_name(class_name_)


def _get_model_import_class_source(
    model: type[sob.abc.Model],
) -> tuple[str, str]:
    model_source: str = get_source(model)
    partitions: tuple[str, str, str] = model_source.partition("\n\n\n")
    return partitions[0], partitions[2]


def _types_from_enum_values(
    values: Iterable[sob.abc.MarshallableTypes],
) -> sob.abc.Types:
    types: sob.abc.MutableTypes = sob.types.MutableTypes()

    def add_value_type(value: sob.abc.MarshallableTypes) -> None:
        type_: type | sob.abc.Property = type(value)
        if isinstance(value, datetime):
            type_ = sob.DateTimeProperty()
        elif isinstance(value, date):
            type_ = sob.DateProperty()
        if type_ not in types:
            types.append(type_)

    deque(map(add_value_type, values), maxlen=0)
    return types


def _append_property_type(
    property_: sob.abc.Property, type_: type | sob.abc.Property
) -> sob.abc.Property:
    if type_ is datetime:
        type_ = sob.DateTimeProperty()
    elif type_ is date:
        type_ = sob.DateProperty()
    # Representations are used in lieu of comparing classes directly
    # because in the course of type generation it is possible to create
    # an identical class more than once
    type_representations: set[str] = set(
        filter(
            None,
            map(sob.utilities.represent, property_.types or ()),
        )
    ) | {sob.utilities.represent(property_)}
    if sob.utilities.represent(type_) not in type_representations:
        if not isinstance(property_.types, sob.abc.MutableTypes):
            types: sob.abc.MutableTypes
            # If the existing property type is a base class of the
            # type to be appended, the appended class supercedes
            # the original
            if (
                property_.types
                and len(property_.types) == 1
                and isinstance(type_, type)
                and isinstance(property_.types[0], type)
                and issubclass(type_, property_.types[0])
            ):
                types = sob.types.MutableTypes()
            elif type(property_) is sob.Property:
                types = sob.types.MutableTypes(property_.types or ())
            else:
                new_property: sob.abc.Property = copy(property_)
                new_property.name = None
                new_property.required = False
                new_property.versions = None  # type: ignore
                types = sob.types.MutableTypes((new_property,))
            property_ = sob.Property(
                name=property_.name,
                types=types,
                required=property_.required,
                versions=property_.versions,
            )
        if not isinstance(property_.types, sob.abc.MutableTypes):
            raise TypeError(property_.types)
        property_.types.append(type_)
    return property_


class _Modeler:
    """
    This class parses an OpenAPI schema and produces a data model based on the
    `sob` library.

    Parameters:
        root:
        get_class_name_from_pointer:
    """

    def __init__(
        self,
        root: OpenAPI,
        get_class_name_from_pointer: Callable[[str, str], str] = partial(
            get_default_class_name_from_pointer, log=print
        ),
    ) -> None:
        message: str
        # This ensures all elements have URLs and JSON pointers
        sob.set_model_url(root, sob.get_model_url(root))
        sob.set_model_pointer(root, sob.get_model_pointer(root) or "")
        # Private Properties
        self._traversed_relative_urls_pointers: set[str] = set()
        self._relative_urls_pointers_class_names: dict[str, str] = {}
        self._class_names_relative_urls_pointers: dict[str, str] = {}
        self._class_names_meta: dict[str, sob.abc.Meta] = {}
        self._relative_urls_pointers_models: dict[
            str, type[sob.abc.Model] | None
        ] = {}
        self._class_names_models: dict[str, type[sob.abc.Model] | None] = {}
        # Validate arguments
        if not (isinstance(root, OpenAPI) and root):
            message = f"Invalid root document: {root!r}"
            raise ValueError(message)
        if not (root.swagger or root.openapi):
            message = (
                "The root document must specify an OpenAPI/Swagger version: "
                f"{root!r}"
            )
            raise ValueError(message)
        # Public properties
        self.root: OpenAPI = root
        self.resolver: Resolver = Resolver(self.root)
        self.major_version: int = int(
            (self.root.swagger or self.root.openapi or "0")
            .split(".")[0]
            .strip()
        )
        self.get_class_name_from_pointer: Callable[[str, str], str] = (
            get_class_name_from_pointer
        )

    def schema_defines_object(self, schema: Schema | Reference) -> bool:
        """
        If properties are defined for a schema, it will translate to an
        instance of `Object`.
        """
        if isinstance(schema, Reference):
            schema = self.resolver.resolve_reference(schema)  # type: ignore
            if not isinstance(schema, Schema):
                raise TypeError(schema)
        if not isinstance(schema, Schema):
            # Version 2x parameters can't be objects/dictionaries
            return False
        if (schema.properties and schema.type_ in ("object", None)) and (
            not schema.additional_properties
        ):
            return True
        return any(
            map(
                self.schema_defines_object,
                chain(
                    getattr(schema, "any_of", ()) or (),
                    getattr(schema, "all_of", ()) or (),
                    getattr(schema, "one_of", ()) or (),
                ),
            )
        )

    def schema_defines_array(
        self, schema: Schema | Parameter | Reference | Items
    ) -> bool:
        """
        Schemas of the type `array` translate to an `Array`. Incorrectly
        implemented schemas may also neglect this, however use of the attribute
        `items` is only valid in the context of an array--and therefore
        indicate the schema also defines an instance of `Array`.
        """
        if isinstance(schema, Reference):
            schema = self.resolver.resolve_reference(schema)  # type: ignore
            if not isinstance(schema, Schema):
                raise TypeError(schema)
        if not isinstance(schema, (Schema, Parameter, Items)):
            raise TypeError(schema)
        if schema.type_ == "array" or schema.items:
            return True
        return any(
            map(
                self.schema_defines_array,
                chain(
                    getattr(schema, "any_of", ()) or (),
                    getattr(schema, "all_of", ()) or (),
                    getattr(schema, "one_of", ()) or (),
                ),
            )
        )

    def schema_defines_dictionary(self, schema: Schema | Reference) -> bool:
        """
        If properties are not defined for a schema, or unspecified attributes
        are allowed--the schema will translate to an instance of
        `sob.abc.Dictionary`.
        """
        if isinstance(schema, Reference):
            schema = self.resolver.resolve_reference(schema)  # type: ignore
            if not isinstance(schema, Schema):
                raise TypeError(schema)
        if not isinstance(schema, Schema):
            # Version 2x parameters can't be objects/dictionaries
            return False
        if (
            schema.additional_properties and schema.type_ in ("object", None)
        ) or (schema.type_ == "object" and not schema.properties):
            return True
        return any(
            map(
                self.schema_defines_dictionary,
                chain(
                    getattr(schema, "any_of", ()) or (),
                    getattr(schema, "all_of", ()) or (),
                    getattr(schema, "one_of", ()) or (),
                ),
            )
        )

    def schema_defines_model(self, schema: Schema | Parameter | Items) -> bool:
        if not isinstance(schema, (Schema, Parameter, Items)):
            raise TypeError(schema)
        return self.schema_defines_array(schema) or (
            isinstance(schema, Schema)
            and (
                self.schema_defines_object(schema)
                or self.schema_defines_dictionary(schema)
            )
        )

    def get_relative_url_pointer_model(
        self, relative_url_pointer: str
    ) -> type[sob.abc.Model] | None:
        return self._relative_urls_pointers_models[relative_url_pointer]

    def set_relative_url_pointer_class_name(
        self, relative_url_pointer: str, class_name_: str
    ) -> str:
        """
        Attempt to associate a class name (`class_name_`) with a concatenated
        URL + pointer (`relative_url_pointer`), and return the class name
        which is actually used. If the pointer already had a class name
        associated, the pre-existing class name takes precedent. If
        a class name is not unique, it is suffixed with an underscore "_"
        (repeatedly, if necessary) to make it unique.

        Parameters:
            relative_url_pointer:
            class_name_:
        """
        if relative_url_pointer in self._relative_urls_pointers_class_names:
            # Use the previously mapped class name
            class_name_ = self._relative_urls_pointers_class_names[
                relative_url_pointer
            ]
        else:
            # Ensure the name is unique
            while (
                class_name_ in self._class_names_relative_urls_pointers
            ) and self._class_names_relative_urls_pointers[
                class_name_
            ] != relative_url_pointer:
                class_name_ = f"{class_name_}_"
            # Update the mapping
            self._relative_urls_pointers_class_names[relative_url_pointer] = (
                class_name_
            )
        self._class_names_relative_urls_pointers[class_name_] = (
            relative_url_pointer
        )
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
        schemas: Iterable[Schema | Reference],
    ) -> sob.abc.Property:
        schemas = iter(schemas)
        next_schema: Schema | None = self.next_schema(schemas)
        if next_schema is None:
            return property_
        if property_.types is None:
            property_.types = sob.types.MutableTypes()  # type: ignore
        elif not isinstance(property_.types, sob.abc.MutableTypes):
            property_ = sob.Property(
                types=sob.types.MutableTypes(
                    (property_,)
                    if isinstance(
                        property_,
                        (sob.abc.DateProperty, sob.abc.DateTimeProperty),
                    )
                    else property_.types
                )  # type: ignore
            )
        child_property_ = self.get_property(next_schema)
        if child_property_.types:
            deque(
                starmap(
                    _append_property_type,
                    zip(
                        (property_,) * len(child_property_.types),
                        child_property_.types,
                    ),
                ),
                maxlen=0,
            )
        return self.extend_property_schemas(property_, schemas)

    def next_schema(
        self, schemas: Iterator[Schema | Reference]
    ) -> Schema | None:
        next_schema: Schema | Reference
        try:
            next_schema = next(schemas)
        except StopIteration:
            return None
        if isinstance(next_schema, Reference):
            next_schema = self.resolver.resolve_reference(  # type: ignore
                next_schema
            )
            if not isinstance(next_schema, Schema):
                raise TypeError(next_schema)
        return next_schema

    def merge_schemas_properties(
        self,
        meta_properties: sob.abc.Properties,
        schemas: Iterable[Schema | Reference],
    ) -> None:
        """
        Add property definitions to a properties object based on multiple
        schemas, merging property definitions when defined more than once.

        Parameters:
            meta_properties:
            schemas:
        """
        schemas = iter(schemas)
        next_schema: Schema | None = self.next_schema(schemas)
        if next_schema is None:
            return None
        schema_properties: Properties | None = next_schema.properties
        if schema_properties:
            name_: str
            schema: Schema | Reference
            for name_, schema in schema_properties.items():
                property_name = sob.utilities.get_property_name(name_)
                # Prevent property names from conflicting with the dependency
                # module namespace
                if property_name == sob.__name__:
                    property_name = f"{sob.__name__}_"
                property_: sob.abc.Property
                if property_name in meta_properties:
                    if next_schema.required and (
                        name_ in next_schema.required
                    ):
                        meta_properties[property_name].required = True
                    meta_properties[property_name] = (
                        self.extend_property_schemas(
                            meta_properties[property_name], (schema,)
                        )
                    )
                else:
                    property_ = self.get_property(
                        schema,
                        name=None if property_name == name_ else name_,
                        required=(
                            bool(
                                next_schema.required
                                and name_ in next_schema.required
                            )
                        ),
                    )
                    meta_properties[property_name] = property_
        if next_schema.all_of:
            schemas = chain(schemas, next_schema.all_of)
        self.merge_schemas_properties(meta_properties, schemas)

    def get_merged_schemas_object_class(
        self,
        schemas: Iterable[Schema | Reference],
        name: str | None = None,
        relative_url_pointer: str | None = None,
    ) -> type[sob.abc.Object] | None:
        """
        Obtain a sub-class of `sob.Model` from multiple instances of
        `oapi.oas.model.Schema`.

        Parameters:
            schemas:
            name:
            relative_url_pointer:
        """
        schemas = iter(schemas)
        next_schema: Schema | None = self.next_schema(schemas)
        if next_schema is None:
            raise ValueError((schemas, name, relative_url_pointer))
        schemas = chain((next_schema,), schemas)
        if name is None:
            name = self.get_schema_class_name(next_schema)
        if relative_url_pointer is None:
            relative_url_pointer = self.get_model_relative_url_pointer(
                next_schema
            )
        meta_properties: sob.abc.Properties = sob.Properties()
        self.merge_schemas_properties(meta_properties, schemas)
        object_meta: sob.abc.ObjectMeta = sob.ObjectMeta(
            properties=meta_properties
        )
        name = self.set_relative_url_pointer_class_name(
            relative_url_pointer, name
        )
        self._class_names_meta[name] = object_meta
        object_class: type[sob.abc.Object] = sob.get_model_from_meta(  # type: ignore
            name,
            object_meta,
            docstring=self.get_docstring(next_schema),
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
        if schema.all_of and len(schema.all_of) == 1:
            property_ = self.extend_property_schemas(property_, schema.all_of)
        return property_

    def get_property(
        self,
        schema: Schema | Parameter | Reference | Items,
        *,
        name: str | None = None,
        required: bool = False,
    ) -> sob.abc.Property:
        is_referenced: bool = isinstance(schema, Reference)
        if is_referenced:
            schema = self.resolver.resolve_reference(schema)  # type: ignore
        if not isinstance(schema, (Schema, Items)):
            raise TypeError(schema)
        schema_type: str | None = _get_schema_type(schema)
        property_: sob.abc.Property = get_type_format_property(
            schema_type,
            format_=schema.format_,
            content_media_type=(
                schema.content_media_type
                if isinstance(schema, Schema)
                else None
            ),
            content_encoding=(
                schema.content_encoding if isinstance(schema, Schema) else None
            ),
            required=required,
        )
        if self.schema_defines_model(schema):
            model_class: type[sob.abc.Model] | None = self.get_model_class(
                schema
            )
            if model_class:
                property_ = _append_property_type(property_, model_class)
        if isinstance(schema, Schema) and (
            schema.any_of
            or schema.one_of
            or (schema.all_of and len(schema.all_of) == 1)
        ):
            property_ = self.polymorph_property(property_, schema)
        if schema.enum:
            property_ = sob.EnumeratedProperty(
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
            (isinstance(schema, Schema) and schema.nullable)
            # Swagger/OpenAPI versions prior to 3.0 do not support `nullable`,
            # so it must be assumed that null values are acceptable for
            # all attributes. Some specs use the "x-nullable" extension
            # attribute, so we check for this as well, but in the absence
            # of a `False` value for `Schema.x_nullable`, we assume all fields
            # are nullable.
            or (
                (self.major_version < 3)  # noqa: PLR2004
                and (
                    (not isinstance(schema, Schema))
                    or (
                        (schema.nullable is not False)
                        and (getattr(schema, "x_nullable", None) is not False)
                    )
                )
            )
        ):
            property_ = _append_property_type(property_, sob.Null)
        if required is not None:
            property_.required = required
        return property_

    def get_model_relative_url_and_pointer(
        self, model: sob.abc.Model
    ) -> tuple[str, str]:
        """
        Return a relative path in relation to the root document and the pointer
        """
        url: str = sob.get_model_url(model) or ""
        pointer: str | None = sob.get_model_pointer(model)
        if not pointer:
            raise ValueError(model)
        return self.resolver.get_relative_url(url), pointer

    def get_model_relative_url_pointer(self, model: sob.abc.Model) -> str:
        """
        Given a schema/operation/parameter definition, return a relative path +
        pointer in relation to the root document
        """
        relative_url, pointer = self.get_model_relative_url_and_pointer(model)
        return f"{relative_url}{pointer}"

    def set_relative_url_pointer_model(
        self, relative_url_pointer: str, model: type[sob.abc.Model] | None
    ) -> None:
        self._relative_urls_pointers_models[relative_url_pointer] = model

    def set_model_class_name(
        self,
        model: type[sob.abc.Model] | None,
        class_name_: str | None = None,
    ) -> None:
        if model and not class_name_:
            class_name_ = model.__name__
        if class_name_:
            self._class_names_models[class_name_] = model

    def get_model_class(
        self,
        definition: Schema | Parameter | Items,
    ) -> type[sob.abc.Model] | None:
        """
        Get a model class from a schema. This method may also return `None`
        in the case of a referential loop.
        """
        relative_url_pointer = self.get_model_relative_url_pointer(definition)
        cls: type[sob.abc.Model] | None
        # If this model has already been generated--use the cached model
        if not self.relative_url_pointer_model_exists(relative_url_pointer):
            # Setting this to `None` prevents recursion errors
            self.set_relative_url_pointer_model(relative_url_pointer, None)
            cls = self.get_schema_model_class(
                definition,
                relative_url_pointer=relative_url_pointer,
            )
            self.set_relative_url_pointer_model(relative_url_pointer, cls)
            self.set_model_class_name(cls)
        return self.get_relative_url_pointer_model(relative_url_pointer)

    def iter_pointers_model_classes(
        self,
    ) -> Iterable[tuple[str, type[sob.abc.Model]]]:
        message: str
        models_names: dict[str, type[sob.abc.Model]] = {}
        schema: Schema | Parameter
        for schema in self.iter_schemas():
            relative_url_pointer: str = self.get_model_relative_url_pointer(
                schema
            )
            model: type[sob.abc.Model] | None = self.get_model_class(schema)
            if model:
                if model.__name__ in models_names:
                    existing_model_meta = sob.read_model_meta(
                        models_names[model.__name__]
                    )
                    new_model_meta = sob.read_model_meta(model)
                    # Ensure this is just a repeat use of the same model, and
                    # not a different model of the same name
                    if existing_model_meta != new_model_meta:
                        message = (
                            "An attempt was made to define a model using an "
                            f'existing model name (`{model.__name__}`)"\n\n'
                            "Existing Module Metadata:\n\n"
                            f"{existing_model_meta!r}\n\n"
                            f"New Module Metadata:\n\n{new_model_meta!r}"
                        )
                        raise RuntimeError(message)
                elif model not in (sob.Array, sob.Dictionary):
                    models_names[model.__name__] = model
                    yield relative_url_pointer, model

    def get_schema_model_class(
        self,
        schema: Schema | Parameter | Items,
        *,
        name: str | None = None,
        relative_url_pointer: str | None = None,
        required: bool = False,
    ) -> type[sob.abc.Model] | None:
        if name is None:
            name = self.get_schema_class_name(schema)
        if relative_url_pointer is None:
            relative_url_pointer = self.get_model_relative_url_pointer(schema)
        if self.schema_defines_array(schema):
            return self.get_schema_array_class(
                schema,
                name=name,
                relative_url_pointer=relative_url_pointer,
                required=required,
            )
        if isinstance(schema, Schema):
            if self.schema_defines_object(schema):
                if not isinstance(schema, Schema):
                    raise TypeError(schema)
                # If the schema has no properties, but defines "anyOf",
                # or "oneOf" properties, it is just a container
                # for referencing other schemas
                if (not schema.properties) and (
                    schema.any_of
                    or schema.one_of
                    or (schema.all_of and len(schema.all_of) == 1)
                ):
                    return None
                return self.get_schema_object_class(
                    schema,
                    name=name,
                    relative_url_pointer=relative_url_pointer,
                )
            if self.schema_defines_dictionary(schema):
                if not isinstance(schema, Schema):
                    raise TypeError(schema)
                return self.get_schema_dictionary_class(
                    schema,
                    name=name,
                    relative_url_pointer=relative_url_pointer,
                    required=required,
                )
            return None
        return None

    def merge_array_schemas(
        self, cls: type[sob.abc.Array], schemas: Iterable[Schema]
    ) -> None:
        """
        Incorporate additional schemas into a the allowed item types
        for a sub-class of `sob.Array`.

        Parameters:
            cls:
            schemas:
        """
        meta: sob.abc.ArrayMeta = sob.get_writable_array_meta(cls)
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
        self, cls: type[sob.abc.Dictionary], schemas: Iterable[Schema]
    ) -> None:
        """
        Incorporate additional schemas into a the allowed value types
        for a sub-class of `sob.Dictionary`.

        Parameters:
            cls:
            schemas:
        """
        meta: sob.abc.DictionaryMeta = sob.get_writable_dictionary_meta(cls)
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
        schemas: Schema | Reference | Iterable[Schema | Reference],
        *,
        skip: bool = False,
    ) -> Iterable[Schema]:
        """
        Iterate over schemas after having resolving references and
        flattened anyOf/allOf/oneOf.

        Parameters:
            schemas:
        """
        if schemas:
            dereferenced_schemas: Iterable[Schema]
            if isinstance(schemas, Schema):
                dereferenced_schemas = (schemas,)
            elif isinstance(schemas, Reference):
                dereferenced_schemas = (
                    self.resolver.resolve_reference(schemas),  # type: ignore
                )
            else:
                schema_or_reference: Schema | Reference
                dereferenced_schemas = filter(
                    None,
                    (
                        (
                            self.resolver.resolve_reference(  # type: ignore
                                schema_or_reference
                            )
                            if isinstance(schema_or_reference, Reference)
                            else schema_or_reference
                        )
                        for schema_or_reference in schemas
                    ),
                )
            for dereferenced_schema in dereferenced_schemas:
                if not skip:
                    yield dereferenced_schema
                if dereferenced_schema.any_of:
                    yield from self.iter_dereferenced_schemas(
                        dereferenced_schema.any_of
                    )
                if dereferenced_schema.one_of:
                    yield from self.iter_dereferenced_schemas(
                        dereferenced_schema.one_of
                    )
                if dereferenced_schema.all_of:
                    yield from self.iter_dereferenced_schemas(
                        dereferenced_schema.all_of,
                        # If there is only 1 schema in "allOf",
                        # treat it the same as "anyOf" or "oneOf"...
                        skip=dereferenced_schema.all_of != 1,
                    )

    def get_required_schema_model_or_property(
        self, schema: Schema
    ) -> sob.abc.Property | type[sob.abc.Model] | None:
        return self.get_schema_model_or_property(schema, required=True)

    def get_schema_model_or_property(
        self,
        schema: Schema | Parameter | Items,
        *,
        required: bool = False,
    ) -> sob.abc.Property | type[sob.abc.Model] | None:
        type_: type[sob.abc.Model] | sob.abc.Property | None
        if not isinstance(schema, (Schema, Parameter, Items)):
            raise TypeError(schema)
        if self.schema_defines_model(schema):
            type_ = self.get_model_class(schema)
        else:
            type_ = self.get_property(schema, required=required)
        return type_

    def get_schema_array_class(
        self,
        schema: Schema | Parameter | Items,
        *,
        name: str | None = None,
        relative_url_pointer: str | None = None,
        required: bool = False,
    ) -> type[sob.abc.Array]:
        """
        Get all applicable items schemas
        """
        if not isinstance(schema, (Schema, Parameter, Items)):
            raise TypeError(schema)
        array_class: type[sob.abc.Array]
        item_types: tuple[type[sob.abc.Model] | sob.abc.Property, ...] = tuple(
            filter(
                None,
                map(
                    (
                        (self).get_required_schema_model_or_property  # type: ignore
                        if required
                        else self.get_schema_model_or_property
                    ),
                    (
                        (schema.items,)
                        if isinstance(schema.items, Items)
                        else iter_distinct(
                            self.iter_dereferenced_schemas(
                                schema.items  # type: ignore
                            )
                        )
                    ),
                ),
            )
        )
        # If item types are defined--create a class, otherwise--use the base
        # class
        if item_types:
            array_meta = sob.ArrayMeta(item_types=item_types)
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
            if name in self._class_names_models:
                return self._class_names_models[name]  # type: ignore
            if relative_url_pointer is None:
                relative_url_pointer = self.get_model_relative_url_pointer(
                    schema
                )
            name = self.set_relative_url_pointer_class_name(
                relative_url_pointer, name
            )
            self._class_names_meta[name] = array_meta
            array_class = sob.get_model_from_meta(  # type: ignore
                name,
                array_meta,
                docstring=self.get_docstring(schema),
                module="__main__",
            )
        else:
            # If types are not defined, use a generic array class
            array_class = sob.Array
        return array_class

    def get_schema_dictionary_class(
        self,
        schema: Schema,
        *,
        name: str | None = None,
        relative_url_pointer: str | None = None,
        required: bool = False,
    ) -> type[sob.abc.Dictionary]:
        """
        If a schema is open-ended (could have "additional", un-named,
        properties), is must be interpreted as a dictionary.

        Parameters:
            schema:
            name:
            relative_url_pointer:
            required:
        """
        if (
            schema.properties or schema.additional_properties
        ) and not isinstance(schema.additional_properties, bool):
            value_types: tuple[sob.abc.Property | type[sob.abc.Model], ...] = (
                tuple(  # type: ignore
                    filter(
                        None,
                        map(  # type: ignore
                            (
                                self.get_required_schema_model_or_property
                                if required
                                else self.get_schema_model_or_property
                            ),
                            iter_distinct(
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
                dictionary_meta = sob.DictionaryMeta(value_types=value_types)
                name = self.set_relative_url_pointer_class_name(
                    relative_url_pointer, name
                )
                self._class_names_meta[name] = dictionary_meta
                return sob.get_model_from_meta(  # type: ignore
                    name,
                    dictionary_meta,
                    docstring=self.get_docstring(schema),
                    module="__main__",
                )
        return sob.Dictionary

    def _iter_schema_property_schemas(
        self, schema: Schema
    ) -> Iterable[tuple[str, Schema]]:
        if schema.properties:
            name: str
            property_schema: Schema | Reference
            for name, property_schema in schema.properties.items():
                if isinstance(property_schema, Reference):
                    property_schema = (  # noqa: PLW2901
                        self.resolver.resolve_reference(  # type: ignore
                            property_schema, (Schema,)
                        )
                    )
                if not isinstance(property_schema, Schema):
                    raise TypeError(property_schema)
                yield name, property_schema

    def _iter_sorted_schema_property_schemas(
        self, schema: Schema
    ) -> Iterable[tuple[str, Schema]]:
        yield from sorted(
            self._iter_schema_property_schemas(schema),
            key=lambda item: (0 if item[1].required else 1, item[0]),
        )

    def get_docstring(self, schema: Schema | Parameter | Items) -> str | None:
        docstring: list[str] = []
        schema_description: str = ""
        if isinstance(schema, (Schema, Parameter)):
            schema_description = (schema.description or "").strip()
        if schema_description:
            docstring.append(
                sob.utilities.split_long_docstring_lines(schema_description)
            )
        if isinstance(schema, Schema):
            is_first_property: bool = True
            name: str
            property_schema: Schema
            for name, property_schema in self._iter_schema_property_schemas(
                schema
            ):
                if is_first_property:
                    if schema_description:
                        docstring.append("")
                    docstring.append("    Attributes:")
                    is_first_property = False
                name = sob.utilities.get_property_name(name)  # noqa: PLW2901
                property_docstring: str
                if property_schema.description:
                    description: str = re.sub(
                        r"\n[\s\n]*\n+",
                        "\n",
                        property_schema.description.strip(),
                    )
                    property_docstring = (
                        sob.utilities.split_long_docstring_lines(
                            sob.utilities.indent(
                                f"{name}: {description}", 12, start=0
                            )
                        )[4:]
                    )
                else:
                    property_docstring = f"        {name}:"
                docstring.append(property_docstring)
        return "\n".join(docstring) if docstring else None

    def get_schema_object_class(
        self,
        schema: Schema,
        name: str | None = None,
        relative_url_pointer: str | None = None,
    ) -> type[sob.abc.Object]:
        """
        Obtain a sub-class of `sob.Model` from an instance of
        `oapi.oas.Schema`.

        Parameters:
            schema:
            name:
            relative_url_pointer:
        """
        cls: type[sob.abc.Object] | None = (
            self.get_merged_schemas_object_class(
                (schema,),
                name=name,
                relative_url_pointer=relative_url_pointer,
            )
        )
        if cls is None:
            raise ValueError((schema, name, relative_url_pointer))
        return cls

    def get_schema_class_name(
        self, schema: Schema | Parameter | Items, name: str = ""
    ) -> str:
        """
        Derive a model's class name from a `Schema` object
        """
        relative_url: str
        pointer: str
        relative_url, pointer = self.get_model_relative_url_and_pointer(schema)
        if isinstance(schema, Parameter):
            if name:
                if schema.name:
                    # If a name was provided, but there is also
                    # a parameter name, concatenate the two
                    name = f"{name}/{schema.name}"
            else:
                name = schema.name or ""
        relative_url_pointer: str = f"{relative_url}{pointer}"
        if not self.relative_url_pointer_class_name_exists(
            relative_url_pointer
        ):
            # Cache the result
            self.set_relative_url_pointer_class_name(
                relative_url_pointer,
                self.get_class_name_from_pointer(relative_url_pointer, name),
            )
            # Cache the items as well, if this is a parameter, so that we
            # can pass along the parameter name
            if isinstance(schema, Parameter) and name:
                if schema.items:
                    self.get_schema_class_name(schema.items, name)
                if schema.schema:
                    parameter_schema: sob.abc.Model
                    if isinstance(schema.schema, Reference):
                        parameter_schema = self.resolver.resolve_reference(
                            schema.schema
                        )
                    if not isinstance(parameter_schema, Schema):
                        raise TypeError(parameter_schema)
                    self.get_schema_class_name(parameter_schema, name)
        return self.get_relative_url_pointer_class_name(relative_url_pointer)

    def iter_schemas(
        self,
    ) -> Iterable[Schema | Parameter]:
        self._traversed_relative_urls_pointers = set()
        schema: Schema | Parameter
        yield from self.iter_model_schemas(self.root, (OpenAPI,))

    def add_traversed(self, model: sob.abc.Model) -> None:
        self._traversed_relative_urls_pointers.add(
            self.get_model_relative_url_pointer(model)
        )

    def is_traversed(self, model: sob.abc.Model) -> bool:
        relative_url_pointer = self.get_model_relative_url_pointer(model)
        return relative_url_pointer in self._traversed_relative_urls_pointers

    def iter_array_schemas(
        self,
        array: sob.abc.Array,
        *,
        skip: bool = False,
    ) -> Iterable[Schema | Parameter]:
        meta_: sob.abc.ArrayMeta | None = sob.read_array_meta(array)
        item: sob.abc.MarshallableTypes
        for item in array:
            if isinstance(item, sob.abc.Model):
                yield from self.iter_model_schemas(
                    item,
                    (meta_.item_types or () if meta_ else ()),
                    skip=skip,
                )

    def iter_dictionary_schemas(
        self,
        dictionary: sob.abc.Dictionary,
    ) -> Iterable[Schema]:
        meta_: sob.abc.DictionaryMeta | None = sob.read_dictionary_meta(
            dictionary
        )
        for value in dictionary.values():
            if isinstance(value, sob.abc.Model):
                yield from self.iter_model_schemas(  # type: ignore
                    value, (meta_.value_types or () if meta_ else ())
                )

    def iter_object_schemas(
        self,
        object_: sob.abc.Object,
    ) -> Iterable[Schema | Parameter]:
        meta_: sob.abc.ObjectMeta | None = sob.read_object_meta(object_)
        if meta_ and meta_.properties:
            name: str
            property_: sob.abc.Property
            item: tuple[str, sob.abc.Property]
            for name, property_ in sorted(
                meta_.properties.items(),
                key=lambda item: (
                    f"_{item[0]}"
                    if (
                        isinstance(object_, OpenAPI)
                        and item[0] in ("definitions", "components")
                    )
                    else item[0]
                ),
            ):
                value: Any = getattr(object_, name)
                if isinstance(value, sob.abc.Model):
                    yield from self.iter_model_schemas(
                        value,
                        property_.types or (),
                        # When a schema is under "allOf", it will
                        # be merged, and if under "oneOf" or "anyOf",
                        # it will already have been yielded
                        skip=(
                            isinstance(object_, Schema)
                            and name == "all_of"
                            # If there is only one schema in "allOf",
                            # it is no different from "anyOf" or "oneOf"
                            and len(value) != 1  # type: ignore
                        ),
                    )

    def iter_model_schemas(
        self,
        model: sob.abc.Model,
        types: Sequence[type] | sob.abc.Types = (),
        *,
        skip: bool = False,
    ) -> Iterable[Schema | Parameter]:
        if isinstance(model, Reference):
            model = self.resolver.resolve_reference(model, types)
            # Skipping logic doesn't apply to references objects
            skip = False
        if not self.is_traversed(model):
            self.add_traversed(model)
            # Recursively find other definitions
            if isinstance(model, sob.abc.Object):
                # If this is a schema defining a model,
                # include it in the returned results
                if (
                    isinstance(model, Schema)
                    # Version 2x compatibility
                    or (isinstance(model, Parameter) and model.schema is None)
                ):
                    if skip:
                        skip = False
                    elif self.schema_defines_model(model):
                        yield model
                yield from self.iter_object_schemas(model)
            elif isinstance(model, sob.abc.Dictionary):
                yield from self.iter_dictionary_schemas(model)
            elif isinstance(model, sob.abc.Array):
                yield from self.iter_array_schemas(model, skip=skip)
            else:
                raise TypeError(model)

    def represent_model_meta(self, class_name_: str) -> str:
        meta_ = self._class_names_meta[class_name_]
        lines: list[str] = []
        for property_name_, value in iter_properties_values(meta_):
            if value is not None:
                value = repr(value)  # noqa: PLW2901
                if value[: _META_PROPERTIES_QAULIFIED_NAME_LENGTH + 1] == (
                    f"{_META_PROPERTIES_QAULIFIED_NAME}("
                ):
                    start: int = _META_PROPERTIES_QAULIFIED_NAME_LENGTH + 1
                    value = value[start:-1]  # noqa: PLW2901
                lines.append(
                    get_class_meta_attribute_assignment_source(
                        class_name_, property_name_, meta_
                    )
                )
        return "\n".join(lines)

    def get_module_source(self) -> str:
        """
        Return the source code for a model module.
        """
        relative_url_pointer: str
        class_names_sources: dict[str, str] = {}
        classes: list[str] = []
        imports: set[str] = set()
        pointers_classes: list[str] = [
            "# The following is used to retain class names when "
            "re-generating\n"
            "# this model from an updated OpenAPI document\n"
            "_POINTERS_CLASSES: "
            "typing.Dict[str, typing.Type[sob.abc.Model]] = {"
        ]
        for (
            relative_url_pointer,
            model_class,
        ) in sorted(self.iter_pointers_model_classes()):
            message: str
            class_name_: str = model_class.__name__
            class_imports: str
            class_source: str
            class_imports, class_source = _get_model_import_class_source(
                model_class
            )
            if class_name_ in class_names_sources:
                message = (
                    f"The class name `{class_name_}` occured twice:\n\n"
                    f"{class_names_sources[class_name_]}\n\n"
                    f"{class_source}"
                )
                raise OAPIDuplicateClassNameError(message)
            class_names_sources[class_name_] = class_source
            deque(
                map(imports.add, filter(None, class_imports.split("\n"))),
                maxlen=0,
            )
            # pointer -> class mapping
            classes.append(class_source)
            key_value_separator: str = (
                " "
                if (9 + len(relative_url_pointer) + len(model_class.__name__))
                <= sob.utilities.MAX_LINE_LENGTH
                else (
                    "\n    "
                    if (7 + len(relative_url_pointer))
                    <= sob.utilities.MAX_LINE_LENGTH
                    else "  # noqa\n    "
                )
            )
            pointer_class: str = (
                f'    "{relative_url_pointer}":'
                f"{key_value_separator}{model_class.__name__},"
            )
            if (
                len(pointer_class.split("\n")[-1])
                > sob.utilities.MAX_LINE_LENGTH
            ):
                pointer_class = f"{pointer_class}  # noqa"
            pointers_classes.append(pointer_class)
        pointers_classes.append("}")
        import_statement: str
        return "\n".join(
            chain(
                sorted(
                    imports,
                    key=lambda import_statement: (
                        (0, import_statement)
                        if import_statement.startswith("from __future__")
                        else (3, import_statement)
                        if import_statement.startswith("from ")
                        else (2, import_statement)
                        if import_statement == "import sob"
                        else (1, import_statement)
                    ),
                ),
                ("\n",),
                classes,
                map(self.represent_model_meta, class_names_sources.keys()),
                ("\n".join(pointers_classes), ""),
            )
        )


def _get_class_relative_url_pointer_and_name(
    model: type[sob.abc.Model],
) -> tuple[str, str]:
    if not model.__doc__:
        return "", ""
    match: Match[str] | None = _DOC_POINTER_RE.search(model.__doc__)
    relative_url_pointer: str = ""
    if match:
        groups = match.groups()
        if groups:
            relative_url_pointer = _SPACES_RE.sub("", groups[0])
    return relative_url_pointer, model.__name__


class _ModuleParser:
    def __init__(self, path: str | Path | None = None) -> None:
        self.namespace: dict[str, Any] = {}
        if path:
            self.open(path)

    def open(self, path: str | Path) -> None:
        if isinstance(path, Path):
            path = str(path.absolute())
        else:
            path = os.path.abspath(path)
        current_directory: str = os.path.abspath(os.curdir)
        os.chdir(os.path.dirname(path))
        try:
            self.namespace["__file__"] = path
            with open(path) as module_io:
                exec(module_io.read(), self.namespace)  # noqa: S102
        finally:
            os.chdir(current_directory)

    @property
    def models(self) -> Iterable[type[sob.abc.Model]]:
        for name, value in self.namespace.items():
            if (
                (not name.startswith("_"))
                and isinstance(value, type)
                and issubclass(value, sob.abc.Model)
            ):
                yield value

    def iter_relative_urls_pointers_class_names(
        self,
    ) -> Iterable[tuple[str, str]]:
        pointers_classes: dict[str, type[sob.abc.Model]] = self.namespace.get(
            "_POINTERS_CLASSES", {}
        )
        relative_url_pointer: str
        cls: type[sob.abc.Model]
        for relative_url_pointer, cls in pointers_classes.items():
            yield relative_url_pointer, cls.__name__
        for cls in self.models:
            (
                relative_url_pointer,
                name,
            ) = _get_class_relative_url_pointer_and_name(cls)
            if relative_url_pointer and (
                relative_url_pointer not in pointers_classes
            ):
                yield relative_url_pointer, name


def _get_path_modeler(path: str | Path) -> _Modeler:
    with open(path) as model_io:
        if TYPE_CHECKING:
            assert isinstance(model_io, sob.abc.Readable)
        return _get_io_modeler(model_io)


def _get_url_modeler(url: str) -> _Modeler:
    with urlopen(url) as model_io:  # noqa: S310
        return _get_io_modeler(model_io)


def _get_io_modeler(model_io: sob.abc.Readable) -> _Modeler:
    return _get_open_api_modeler(OpenAPI(model_io))


def _get_open_api_modeler(open_api: OpenAPI) -> _Modeler:
    return _Modeler(open_api)


class ModelModule:
    """
    This class parses an Open API document and generates a module defining
    classes to represent each schema defined in the Open API document as a
    subclass of `sob.Object`, `sob.Array`, or
    `sob.Dictionary`.

    Parameters:
        open_api: An OpenAPI document. This can be a URL, file-path, an
            HTTP response (`http.client.HTTPResponse`), a file object, or an
            instance of `oapi.oas.OpenAPI`.
        get_class_name_from_pointer: This argument defaults to
            `oapi.model.get_default_class_name_from_pointer`. If an alternate
            function is provided, it should accept two arguments, both being
            `str` instances. The first argument is a JSON pointer, or
            concatenated relative URL + JSON pointer, and the second being
            either an empty string or a parameter name, where applicable.
            The function should return a `str` which is a valid, unique,
            class name.
    """

    def __init__(
        self,
        open_api: str | sob.abc.Readable | OpenAPI,
        get_class_name_from_pointer: Callable[
            [str, str], str
        ] = get_default_class_name_from_pointer,
    ) -> None:
        message: str
        self._parser = _ModuleParser()
        self._modeler: _Modeler
        if isinstance(open_api, str):
            if os.path.exists(open_api):
                self._modeler = _get_path_modeler(open_api)
            else:
                self._modeler = _get_url_modeler(open_api)
        elif isinstance(open_api, sob.abc.Readable):
            self._modeler = _get_io_modeler(open_api)
        elif isinstance(open_api, OpenAPI):
            self._modeler = _get_open_api_modeler(open_api)
        else:
            message = (
                f"`{get_calling_function_qualified_name()}` requires an "
                f"instance of `str`, `{get_qualified_name(OpenAPI)}`, or "
                "a file-like object for the `open_api` parameter—not: "
                f"{open_api!r}"
            )
            raise TypeError(message)
        self._modeler.get_class_name_from_pointer = get_class_name_from_pointer

    def __str__(self) -> str:
        return self._modeler.get_module_source()

    def _parse_existing_module(self, path: str | Path) -> None:
        if os.path.exists(path):
            self._parser.open(path)
            for (
                relative_url_pointer,
                class_name_,
            ) in self._parser.iter_relative_urls_pointers_class_names():
                self._modeler.set_relative_url_pointer_class_name(
                    relative_url_pointer, class_name_
                )

    def _get_relative_url_and_pointer(
        self, url_pointer: str
    ) -> tuple[str, str]:
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
            relative_url = self._modeler.resolver.get_relative_url(url)
        return relative_url, pointer

    def save(self, path: str | Path) -> None:
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

    def __eq__(self, other: object) -> bool:
        return isinstance(other, self.__class__) and str(self) == str(other)


Module = deprecated(
    "`oapi.model.Module` is deprecated and will be removed in oapi 3. "
    "Please use `oapi.ModelModule` instead."
)(ModelModule)


def write_model_module(
    model_path: str | Path,
    *,
    open_api: str | sob.abc.Readable | OpenAPI,
    get_class_name_from_pointer: Callable[
        [str, str], str
    ] = get_default_class_name_from_pointer,
) -> None:
    """
    This function creates or updates a module defining classes to represent
    each schema in an Open API document as a subclass of `sob.Object`,
    `sob.Array`, or `sob.Dictionary`.

    Parameters:
        model_path: The file path where the model module will be saved
            (created or updated).
        open_api: An OpenAPI document. This can be a URL, file-path, an
            HTTP response (`http.client.HTTPResponse`), a file object, or an
            instance of `oapi.oas.model.OpenAPI`.
        get_class_name_from_pointer: This argument defaults to
            `oapi.model.get_default_class_name_from_pointer`. If an alternate
            function is provided, it should accept two arguments, both being
            `str` instances. The first argument is a JSON pointer, or
            concatenated relative URL + JSON pointer, and the second being
            either an empty string or a parameter name, where applicable.
            The function should return a `str` which is a valid, unique,
            class name.
    """
    locals_: dict[str, Any] = dict(locals())
    locals_.pop("model_path")
    model_module: ModelModule = ModelModule(**locals_)
    model_module.save(model_path)
