# region Backwards Compatibility

from __future__ import nested_scopes, generators, division, absolute_import, with_statement, \
   print_function, unicode_literals

from sob.utilities.compatibility import backport

backport()  # noqa

# endregion

from warnings import warn
import re
from collections import OrderedDict
from copy import copy
from urllib.parse import urljoin

from io import IOBase

from sob.utilities import class_name, get_source, camel_split, property_name, properties_values, qualified_name
import sob

from .oas import model, references


_POINTER_RE = re.compile(r'{(?:[^{}]+)}')


class Model(object):
    """
    This class parses an OpenAPI schema and produces a data model based on the `sob` library.
    """

    def __init__(self, root, rename=None):

        # type: (Union[IOBase, str], str, Callable) -> None
        if not isinstance(root, model.OpenAPI):
            root = model.OpenAPI(root)

        # This ensures all elements have URLs and JSON pointers
        sob.meta.url(root, sob.meta.url(root))
        sob.meta.pointer(root, sob.meta.pointer(root))

        self.resolver = references.Resolver(root)

        self._major_version = int((root.swagger or root.openapi).split('.')[0].strip())
        self._root = root
        self._rename = rename
        self._references = OrderedDict()
        self._pointers_schemas = OrderedDict()
        self._names_models = OrderedDict()
        self._names_schemas = {}
        self._pointers_models = OrderedDict()
        self._pointers_meta = OrderedDict()
        self._get_models()

    def __getattr__(self, name):
        # type: (str) -> type
        return self._names_models[name]

    @property
    def __all__(self):
        return tuple(self._names_models.keys())

    def __dir__(self):
        return self.__all__

    def _get_property(self, schema, name=None, required=None):

        # type: (Union[model.Schema, model.Reference], Optional[str], Optional[bool]) -> sob.properties.Property
        if not isinstance(schema, (model.Schema, model.Reference)):
            raise TypeError(
                'The parameter `schema` must be of type `%s` or `%s`, not %s.' % (
                    qualified_name(model.Schema),
                    qualified_name(model.Reference),
                    repr(schema)
                )
            )

        pointer = sob.meta.url(schema) + sob.meta.pointer(schema)

        if isinstance(schema, model.Reference):
            pointer = urljoin(pointer, schema.ref)
            schema = self._references[pointer]

        if (schema.any_of is not None) or (schema.one_of is not None):
            property = sob.properties.Property()
            types = []
            if schema.any_of is not None:
                i = 0
                for s in schema.any_of:
                    p = self._get_property(s)
                    types.append(p)
                    i += 1
            if schema.one_of is not None:
                i = 0
                for s in schema.one_of:
                    p = self._get_property(s)
                    types.append(p)
                    i += 1
            property.types = tuple(types)
        elif schema.all_of is not None:
            property = sob.properties.Dictionary()
            # TODO: schema.all_of
            # i = 0
            # for s in schema.all_of:
            #     p = self._get_property(s)
            #     i += 1
        elif schema.type_ == 'object' or schema.properties or schema.additional_properties:
            if schema.additional_properties:
                additional_properties = schema.additional_properties
                property = sob.properties.Dictionary()
                if not isinstance(additional_properties, bool):
                    property_value_types = []
                    property_value_types.append(self._get_property(additional_properties))
                    if schema.properties:
                        for schema_property in schema.properties.values():
                            property_value_types.append(self._get_property(schema_property))
                    property.value_types = property_value_types
            elif schema.properties:
                property = sob.properties.Property()
                if pointer in self._pointers_models:
                    property.types = (self._pointers_models[pointer],)
            else:
                property = sob.properties.Dictionary()
        elif schema.type_ == 'array' or schema.items:
            property = sob.properties.Array()
            items = schema.items
            if items:
                item_types = []
                if isinstance(items, (model.Schema, model.Reference)):
                    item_type_property = self._get_property(items)
                    if (
                        item_type_property.types and
                        len(item_type_property.types) == 1 and
                        not isinstance(
                            item_type_property,
                            (
                                sob.properties.Date,
                                sob.properties.DateTime,
                                sob.properties.Array,
                                sob.properties.Dictionary
                            )
                        )
                    ):
                        item_types = item_type_property.types
                    elif item_type_property.types:
                        item_types = (item_type_property,)
                else:
                    for item in items:
                        item_type_property = self._get_property(item)
                        if (
                            item_type_property.types and
                            len(item_type_property.types) == 1 and
                            not isinstance(
                                item_type_property,
                                (
                                    sob.meta.Date,
                                    sob.meta.DateTime,
                                    sob.meta.Array,
                                    sob.meta.Dictionary
                                )
                            )
                        ):
                            item_types.append(item_type_property.types[0])
                        elif item_type_property.types:
                            item_types.append(item_type_property)
                if item_types:
                    property.item_types = item_types
        elif schema.type_ == 'number':
            property = sob.properties.Number()
        elif schema.type_ == 'integer':
            property = sob.properties.Integer()
        elif schema.type_ == 'string':
            if schema.format_ == 'date-time':
                property = sob.properties.DateTime()
            elif schema.format_ == 'date':
                property = sob.properties.Date()
            elif schema.format_ == 'byte':
                property = sob.properties.Bytes()
            else:
                property = sob.properties.String()
        elif schema.type_ == 'boolean':
            property = sob.properties.Boolean()
        elif schema.type_ == 'file':
            property = sob.properties.Bytes()
        else:
            raise ValueError(schema.type_)
        if schema.enum:
            property = sob.properties.Enumerated(
                values=tuple(schema.enum),
                types=(property,)
            )
        if name is not None:
            property.name = name
        if (
            schema.nullable or
            # Swagger/OpenAPI versions prior to 3.0 do not support `nullable`, so it must be assumed that
            # null values are acceptable for required attributes
            ((self._major_version < 3) and (required is True))
        ):
            if schema.nullable is not False:
                name, required, versions = property.name, property.required, property.versions
                property.name = property.required = property.versions = None
                property = sob.properties.Property(
                    types=(property, sob.properties.Null),
                    name=name,
                    required=required,
                    versions=versions
                )
        if required is not None:
            property.required = required
        return property

    def _get_models(self):
        # type: (int) -> None
        for i in range(2):
            for pointer, name_schema in self._get_schemas(
                self._root,
                root=self._root
            ).items():
                name, schema = name_schema  # type: typing.Tuple[str, model.Schema, sob.model.Object]
                self._names_models[name] = self._get_model(pointer, name, schema)

    def _get_model(self, pointer, name, schema):
        # type: (str, model.Schema, sob.model.Object) -> None
        if (not schema.properties) or schema.additional_properties:
            return
        m = sob.meta.Object()
        for n, p in schema.properties.items():
            pn = property_name(n)
            if pn == 'sob':
                pn = 'serial_'
            m.properties[pn] = self._get_property(
                p,
                name=None if pn == n else n,
                required=True if (schema.required and (n in schema.required)) else False
            )
        self._pointers_meta[pointer] = m
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
        self._pointers_models[pointer] = sob.model.from_meta(
            name,
            m,
            docstring='\n\n'.join(ds),
            module='__main__'
        )
        return self._pointers_models[pointer]

    def _resolve_schema_reference(
        self,
        url,  # type: str
        pointer,  # type: str
        reference,  # type: model.Reference
        root,  # type: sob.model.Model
        types=None  # Optional[Union[type, sob.properties.Property]]
    ):
        # type: (...) -> typing.Dict[str, typing.Tuple[str, oapi.model.Schema]]
        path_phrase = []
        path_operation_phrase = []
        operation_phrase = []
        reference_parts = _POINTER_RE.split(reference.ref.split('/')[-1])
        before_arguments = '/'.join(reference_parts[:-1])
        after_arguments = reference_parts[-1]

        if before_arguments:
            for property_pointer in re.split(r'[/\-]', before_arguments):
                for w in camel_split(property_pointer):
                    path_phrase.append(w)
                    path_operation_phrase.append(w)

        for property_pointer in re.split(r'[/\-]', after_arguments):
            for w in camel_split(property_pointer):
                path_phrase.append(w)
                path_operation_phrase.append(w)

        reference = self.resolver.resolve(reference.ref, types=types)
        reference_url = sob.meta.url(reference)

        if reference_url != url:
            root = reference
            pointer = reference_url + '#'

        if types:
            reference = sob.model.unmarshal(reference, types=types)

        return pointer, reference, root, path_phrase, path_operation_phrase, operation_phrase

    def _is_duplicate_schema_name(self, name, schema, root):
        # type: (str, model.Schema, sob.model.Model) -> bool
        """
        This method determines if another schema is already using the given `name`.
        """
        duplicate_exists = False  # type: bool

        if name in self._names_schemas:

            # Lookup the existing schema of the same name
            existing_schema = self._names_schemas[name]

            # Resolve references, where needed
            if isinstance(schema, model.Reference):
                schema = self.resolver.resolve(
                    schema.ref
                )
            if isinstance(existing_schema, model.Reference):
                existing_schema = self.resolver.resolve(
                    existing_schema.ref
                )

            # We only consider these to be duplicates if one is not a reference to the other
            if schema == existing_schema:

                # Make sure the name -> schema dictionary now holds the de-referenced schema
                self._names_schemas[name] = existing_schema

            else:

                duplicate_exists = True

                # If one of these is just an array of the other, that array won't comprise a model of it's own which
                # would have a conflicting name--so we don't consider it a duplicate
                if (
                    existing_schema.type_ == 'array' and
                    isinstance(existing_schema.items, model.Reference)
                ):
                    existing_schema_items = self.resolver.resolve(existing_schema.items.ref)
                    if sob.model.marshal(schema) == sob.model.marshal(existing_schema_items):
                        # The name will reference the item's schema
                        self._names_schemas[name] = schema
                        duplicate_exists = False

                elif (
                    schema.type_ == 'array' and
                    isinstance(schema.items, model.Reference)
                ):
                    schema_items = self.resolver.resolve(schema.items.ref)
                    if sob.model.marshal(schema_items) == sob.model.marshal(existing_schema):
                        duplicate_exists = False

                if duplicate_exists:
                    warn(
                        'The name "%s" is already being used:\n%s\n%s' % (
                            name,
                            repr(schema),
                            repr(existing_schema)
                        )
                    )

        return duplicate_exists

    def _get_schemas(
        self,
        o,  # type: sob.model.Model
        root,  # type: sob.model.Model
        path_phrase=None,  # type: Optional[typing.Sequence[str]]
        path_operation_phrase=None,  # type: Optional[typing.Sequence[str]]
        operation_phrase=None,  # type: Optional[typing.Sequence[str]]
        types=None  # Optional[Union[type, sob.properties.Property]]
    ):
        # type: (...) -> typing.Dict[str, typing.Tuple[str, oapi.model.Schema]]
        if not isinstance(o, sob.abc.model.Model):
            raise TypeError(
                'The parameter `o` must be an instance of `%s`, not %s.' % (
                    qualified_name(sob.abc.model.Model),
                    repr(o)
                )
            )

        if not isinstance(root, sob.abc.model.Model):
            raise TypeError(
                'The parameter `root` must be an instance of `%s`, not %s.' % (
                    qualified_name(sob.abc.model.Model),
                    repr(root)
                )
            )

        url = sob.meta.url(o)
        pointer = url + sob.meta.pointer(o)
        if pointer in self._references:
            return self._pointers_schemas
        path_phrase = path_phrase or []
        path_operation_phrase = path_operation_phrase or []
        operation_phrase = operation_phrase or []

        if isinstance(o, model.Reference):
            pointer = urljoin(pointer, o.ref)
            if pointer in self._references:
                return self._pointers_schemas[pointer]
            pointer, o, root, path_phrase, path_operation_phrase, operation_phrase = self._resolve_schema_reference(
                url, pointer, o, root, types
            )

        self._references[pointer] = o
        if hasattr(o, 'operation_id') and (o.operation_id is not None):
            operation_phrase = []
            path_operation_phrase = []
            for w in camel_split(o.operation_id):
                operation_phrase.append(w)
                path_operation_phrase.append(w)

        if isinstance(o, model.Schema):

            if pointer in self._pointers_schemas:
                return self._pointers_schemas

            if o.type_ == 'object' or o.properties or o.type_ == 'array' or o.items:

                if path_phrase:

                    name = None
                    phrases = []

                    if path_phrase:
                        phrases.append(path_phrase)
                    if operation_phrase:
                        phrases.append(operation_phrase)
                    if path_operation_phrase:
                        phrases.append(path_operation_phrase)

                    name_is_unique = False  # type: bool

                    for redundant_placement in (1, 2, 3):

                        for phrase in phrases:
                            title = []
                            for word in phrase:
                                if len(word) == 1 or word.upper() != word:
                                    word = word.lower()
                                if redundant_placement == 3:
                                    title.append(word)
                                else:
                                    sk = word
                                    ks = None
                                    if word in title:
                                        if redundant_placement == 2:
                                            title.remove(word)
                                            title.append(word)
                                    elif (word not in title) and (sk not in title):
                                        title.append(word)
                                    elif (ks is not None) and ks == word and (ks not in title) and (sk in title):
                                        if redundant_placement == 1:
                                            title[title.index(sk)] = ks
                                        else:
                                            title.remove(sk)
                                            title.append(ks)

                            name = class_name('/'.join(title))

                            if self._rename is not None:
                                name = self._rename(name, set(self._names_schemas.keys()))

                            if name and not self._is_duplicate_schema_name(name, o, root):
                                name_is_unique = True
                                break

                        if name_is_unique:
                            break

                    if not name_is_unique:
                        unique_name = name
                        i = 1
                        while unique_name in self._names_schemas:
                            unique_name = name + str(i)
                            i += 1
                            name = unique_name

                    self._names_schemas[name] = o
                else:
                    name = None
                self._pointers_schemas[pointer] = (name, o)
            else:
               return self._pointers_schemas

        if not isinstance(o, sob.abc.model.Model):
            return self._pointers_schemas

        m = sob.meta.read(o)
        if isinstance(o, sob.model.Dictionary):
            items = o.items()
            if isinstance(o, model.Paths):
                items = sorted(items, key=lambda kv: len(kv[0]))
            for k, property_value in items:
                if isinstance(property_value, sob.abc.model.Model):
                    property_pointer = sob.meta.url(property_value) + sob.meta.pointer(property_value)
                    if property_pointer in self._references:
                        continue
                    if isinstance(property_value, model.Reference):
                        self._get_schemas(
                            property_value,
                            root=root,
                            types=m.value_types,
                            path_phrase=copy(path_phrase),
                            path_operation_phrase=copy(path_operation_phrase),
                            operation_phrase=copy(operation_phrase),
                        )
                    else:
                        item_path_operation_phrase = copy(path_operation_phrase)
                        item_path_phrase = copy(path_phrase)
                        item_operation_phrase = copy(operation_phrase)
                        if isinstance(o, model.Paths) or (not isinstance(o, model.Responses)):
                            epilogue = []
                            phrase = k
                            phrase_parts = _POINTER_RE.split(phrase)
                            before_arguments = '/'.join(phrase_parts[:-1])
                            after_arguments = phrase_parts[-1]
                            if before_arguments:
                                for phrase_part in re.split(r'[/\-]', before_arguments):
                                    for word in camel_split(phrase_part):
                                        epilogue.append(word)
                            for phrase_part in re.split(r'[/\-]', after_arguments):
                                for word in camel_split(phrase_part):
                                    epilogue.append(word)
                            if isinstance(o, model.Paths):
                                item_path_phrase = epilogue
                                item_path_operation_phrase = copy(epilogue)
                                item_operation_phrase = []
                            elif not isinstance(o, model.Responses):
                                item_path_phrase += epilogue
                                item_path_operation_phrase += epilogue
                        self._get_schemas(
                            property_value,
                            root=root,
                            types=m.value_types,
                            path_phrase=item_path_phrase,
                            path_operation_phrase=item_path_operation_phrase,
                            operation_phrase=item_operation_phrase,
                        )
        elif isinstance(o, sob.model.Array):
            for i in range(len(o)):
                property_value = o[i]
                if isinstance(property_value, sob.abc.model.Model):
                    property_pointer = sob.meta.url(property_value) + sob.meta.pointer(property_value)
                    if property_pointer in self._references:
                        return self._pointers_schemas
                    self._get_schemas(
                        property_value,
                        root=root,
                        types=m.item_types,
                        path_phrase=copy(path_phrase),
                        path_operation_phrase=copy(path_operation_phrase),
                        operation_phrase=copy(operation_phrase),
                    )
        elif isinstance(o, sob.model.Object):
            object_properties = tuple(m.properties.items())
            if isinstance(o, model.OpenAPI):
                object_properties = sorted(
                    object_properties,
                    key=lambda kv: 0 if kv[0] in ('components', 'definitions') else 0
                )
            for name, property in object_properties:
                property_value = getattr(o, name)
                if property_value is not None:
                    if isinstance(property_value, sob.abc.model.Model):
                        property_pointer = sob.meta.url(property_value) + sob.meta.pointer(property_value)
                        if property_pointer in self._references:
                            return self._pointers_schemas
                        self._get_schemas(
                            property_value,
                            root=root,
                            types=(property,),
                            path_phrase=(
                                [name]
                                if isinstance(property_value, model.Operation) and isinstance(o, model.PathItem) else
                                []
                            ) + copy(path_phrase),
                            path_operation_phrase=copy(path_operation_phrase),
                            operation_phrase=copy(operation_phrase),
                        )
        else:
            raise TypeError(o)
        return self._pointers_schemas

    def __str__(self):
        lines = []
        for p, m in self._pointers_models.items():
            imports, source = get_source(m).split('\n\n\n')
            if not lines:
                lines.append(imports + '\n\n')
            lines.append(source)
        for pointer, metadata in self._pointers_meta.items():
            cn = self._pointers_schemas[pointer][0]
            if len(pointer) > 118:
                pointer_split = pointer.split('#')
                lines.append('# ' + pointer_split[0])
                lines.append('# #' + '#'.join(pointer_split[1:]))
            else:
                lines.append('# ' + pointer)
            for p, v in properties_values(metadata):
                if v is not None:
                    v = repr(v)
                    if v[:19] == 'sob.meta.Properties(':
                        v = v[19:-1]
                    lines.append(
                        'sob.meta.writable(%s).%s = %s' % (
                            cn, p, v
                        )
                    )
            lines.append('')
        return '\n'.join(lines)
