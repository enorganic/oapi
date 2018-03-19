# Backwards Compatibility ->
from __future__ import nested_scopes, generators, division, absolute_import, with_statement, print_function,\
    unicode_literals
from future import standard_library
standard_library.install_aliases()
from builtins import *
# <- Backwards Compatibility

import re
from collections import OrderedDict
from copy import copy
from urllib.parse import urljoin

import serial
from oapi.model import resolve_references
from serial import meta
from serial.utilities import class_name, get_source, camel_split, property_name, properties_values

from itertools import chain
from io import IOBase

from oapi import model, errors


class Model(object):


    def __init__(self, root, format_='json', rename=None):
        # type: (Union[IOBase, str], str, Callable) -> None
        if not isinstance(root, model.OpenAPI):
            root = model.OpenAPI(root)
        serial.meta.format_(root, format_)
        self._format = format_
        self._major_version = int((root.swagger or root.openapi).split('.')[0].strip())
        self._root = root
        self._rename = rename
        self._references = OrderedDict()
        self._pointers_schemas = OrderedDict()
        self._names_models = OrderedDict()
        self._names = set()
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

    def _get_property(self, schema, pointer, name=None, required=None):
        # type: (str, model.Schema, serial.model.Object, Optional[bool]) -> serial.properties.Property
        property = None
        if isinstance(schema, model.Reference):
            pointer = urljoin(pointer, schema.ref)
            schema = self._references[pointer]
        if (schema.any_of is not None) or (schema.one_of is not None):
            property = serial.properties.Property()
            types = []
            if schema.any_of is not None:
                i = 0
                for s in schema.any_of:
                    p = self._get_property(
                        s,
                        pointer='%s/anyOf[%s]' % (pointer, str(i))
                    )
                    types.append(p)
                    i += 1
            if schema.one_of is not None:
                i = 0
                for s in schema.one_of:
                    p = self._get_property(
                        s,
                        pointer='%s/oneOf[%s]' % (pointer, str(i))
                    )
                    types.append(p)
                    i += 1
            property.types = tuple(types)
        elif schema.all_of is not None:
            property = serial.properties.Dictionary()
            # TODO: schema.all_of
            # i = 0
            # for s in schema.all_of:
            #     p = self._get_property(
            #         s,
            #         pointer='%s/allOf[%s]' % (pointer, str(i))
            #     )
            #     i += 1
        elif schema.type_ == 'object' or schema.properties or schema.additional_properties:
            if schema.properties:
                property = serial.properties.Property()
                if pointer in self._pointers_models:
                    property.types = (self._pointers_models[pointer],)
            elif schema.additional_properties:
                additional_properties = schema.additional_properties
                if additional_properties:
                    additional_properties = schema.additional_properties
                    additional_properties_pointer = pointer + '/additionalProperties'
                    property = serial.properties.Dictionary()
                    if not isinstance(additional_properties, bool):
                        property.value_types = (
                            self._get_property(
                                additional_properties,
                                pointer=additional_properties_pointer
                            ),
                        )
            else:
                property = serial.properties.Dictionary()
        elif schema.type_ == 'array' or schema.items:
            property = serial.properties.Array()
            items = schema.items
            if items:
                item_types = []
                if isinstance(items, serial.model.Object):
                    item_type_property = self._get_property(
                        items,
                        pointer=pointer + '/items'
                    )
                    if (
                        len(item_type_property.types) == 1 and
                        not isinstance(
                            item_type_property,
                            (
                                serial.properties.Date,
                                serial.properties.DateTime,
                                serial.properties.Array,
                                serial.properties.Dictionary
                            )
                        )
                    ):
                        item_types = item_type_property.types
                    else:
                        item_types = (item_type_property,)
                else:
                    i = 0
                    item_types = []
                    for item in items:
                        item_type_property = self._get_property(
                            item,
                            pointer=pointer + '/items[%s]' % str(i)
                        )
                        if (
                            len(item_type_property.types) == 1 and
                            not isinstance(
                                item_type_property,
                                (
                                    serial.meta.Date,
                                    serial.meta.DateTime,
                                    serial.meta.Array,
                                    serial.meta.Dictionary
                                )
                            )
                        ):
                            item_types.append(item_type_property.types[0])
                        else:
                            item_types.append(item_type_property)
                property.item_types = tuple(item_types)
        elif schema.type_ == 'number':
            property = serial.properties.Number()
        elif schema.type_ == 'integer':
            property = serial.properties.Integer()
        elif schema.type_ == 'string':
            if schema.format_ == 'date-time':
                property = serial.properties.DateTime()
            elif schema.format_ == 'date':
                property = serial.properties.Date()
            elif schema.format_ == 'byte':
                property = serial.properties.Bytes()
            else:
                property = serial.properties.String()
        elif schema.type_ == 'boolean':
            property = serial.properties.Boolean()
        elif schema.type_ == 'file':
            property = serial.properties.Bytes()
        else:
            raise ValueError(schema.type_)
        if schema.enum:
            property = serial.properties.Enum(
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
                property = serial.properties.Property(
                    types=(property, serial.properties.Null),
                    name=name,
                    required=required,
                    versions=versions
                )
            # property.types = tuple(chain(property.types, (serial.properties.Null,)))
        if required is not None:
            property.required = required
        return property

    def _get_models(self):
        # type: (int) -> None
        root_meta = meta.read(self._root)
        url = meta.url(self._root)
        for i in range(2):
            for pointer, name_schema in self._get_schemas(
                self._root,
                pointer=(url or '') + '#',
                root=self._root
            ).items():
                name, schema = name_schema  # type: typing.Tuple[str, model.Schema, serial.model.Object]
                self._names_models[name] = self._get_model(pointer, name, schema)

    def _get_model(self, pointer, name, schema):
        # type: (str, model.Schema, serial.model.Object) -> None
        if (not schema.properties) or schema.additional_properties:
            return
        m = serial.meta.Object()
        for n, p in schema.properties.items():
            pn = property_name(n)
            if pn == 'serial':
                pn = 'serial_'
            property_pointer = '%s/%s' % (pointer, n)
            m.properties[pn] = self._get_property(
                p,
                pointer=property_pointer,
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
        self._pointers_models[pointer] = serial.model.from_meta(
            name,
            m,
            docstring='\n\n'.join(ds),
            module='__main__'
        )
        return self._pointers_models[pointer]

    def _get_schemas(
        self,
        o,  # type: Union[serial.model.Model]
        pointer,  # type: str
        root,  # type: serial.model.Model
        path_phrase=None,  # type: Optional[typing.Sequence[str]]
        path_operation_phrase=None,  # type: Optional[typing.Sequence[str]]
        operation_phrase=None,  # type: Optional[typing.Sequence[str]]
        types=None  # Optional[Union[type, serial.properties.Property]]
    ):
        # type: (...) -> typing.Dict[str, typing.Tuple[str, oapi.model.Schema]]
        pre = re.compile(r'{(?:[^{}]+)}')
        if pointer in self._references:
            return self._pointers_schemas
        path_phrase = path_phrase or []
        path_operation_phrase = path_operation_phrase or []
        operation_phrase = operation_phrase or []
        if isinstance(o, model.Reference):
            path_phrase = []
            path_operation_phrase = []
            operation_phrase = []
            reference_parts = pre.split(o.ref.split('/')[-1])
            before_arguments = '/'.join(reference_parts[:-1])
            after_arguments = reference_parts[-1]
            if before_arguments:
                for p in re.split(r'[/\-]', before_arguments):
                    for w in camel_split(p):
                        path_phrase.append(w)
                        path_operation_phrase.append(w)
            for p in re.split(r'[/\-]', after_arguments):
                for w in camel_split(p):
                    path_phrase.append(w)
                    path_operation_phrase.append(w)
            pointer = urljoin(pointer, o.ref)
            if pointer in self._references:
                return self._pointers_schemas
            o = model.resolve_references(o, root=root, recursive=False)
            u = serial.meta.url(o)
            # m = serial.meta.read(o)
            if u:
                root = o
                pointer = u + '#'
            if types:
                o = serial.model.unmarshal(o, types=types)
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
            if o.type_ == 'object' or o.properties:
                if path_phrase:
                    name = None
                    phrases = []
                    if path_phrase:
                        phrases.append(path_phrase)
                    if operation_phrase:
                        phrases.append(operation_phrase)
                    if path_operation_phrase:
                        phrases.append(path_operation_phrase)
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
                                name = self._rename(name, self._names)
                            if name and (name not in self._names):
                                break
                        if name and (name not in self._names):
                            break
                    unique_name = name
                    i = 1
                    while unique_name in self._names:
                        unique_name = name + str(i)
                        i += 1
                        name = unique_name
                    self._names.add(name)
                else:
                    name = None
                self._pointers_schemas[pointer] = (name, o)
            else:
               return self._pointers_schemas
        if not isinstance(o, serial.model.Model):
            return self._pointers_schemas
        m = meta.read(o)
        if isinstance(o, serial.model.Dictionary):
            items = o.items()
            if isinstance(o, model.Paths):
                items = sorted(items, key=lambda kv: len(kv[0]))
            for k, v in items:
                p = '%s/%s' % (pointer, k.replace('~', '~0').replace('/', '~1'))
                if p in self._references:
                    continue
                if isinstance(v, model.Reference):
                    self._get_schemas(
                        v,
                        p,
                        root=root,
                        types=m.value_types,
                        path_phrase=copy(path_phrase),
                        path_operation_phrase=copy(path_operation_phrase),
                        operation_phrase=copy(operation_phrase),
                    )
                elif isinstance(v, (serial.model.Dictionary, serial.model.Array, serial.model.Object)):
                    item_path_operation_phrase = copy(path_operation_phrase)
                    item_path_phrase = copy(path_phrase)
                    item_operation_phrase = copy(operation_phrase)
                    if isinstance(o, model.Paths) or (not isinstance(o, model.Responses)):
                        epilogue = []
                        phrase = k
                        phrase_parts = pre.split(phrase)
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
                        v,
                        p,
                        root=root,
                        types=m.value_types,
                        path_phrase=item_path_phrase,
                        path_operation_phrase=item_path_operation_phrase,
                        operation_phrase=item_operation_phrase,
                    )
        elif isinstance(o, serial.model.Array):
            for i in range(len(o)):
                v = o[i]
                p = '%s[%s]' % (pointer, str(i))
                if p in self._references:
                    return self._pointers_schemas
                if isinstance(v, (serial.model.Dictionary, serial.model.Array, serial.model.Object)):
                    self._get_schemas(
                        v,
                        p,
                        root=root,
                        types=m.item_types,
                        path_phrase=copy(path_phrase),
                        path_operation_phrase=copy(path_operation_phrase),
                        operation_phrase=copy(operation_phrase),
                    )
        elif isinstance(o, serial.model.Object):
            object_properties = tuple(m.properties.items())
            if isinstance(o, model.OpenAPI):
                object_properties = sorted(
                    object_properties,
                    key=lambda kv: 0 if kv[0] in ('components', 'definitions') else 0
                )
            for name, property in object_properties:
                v = getattr(o, name)
                if v is not None:
                    n = property.name or name
                    p = '%s/%s' % (pointer, n.replace('~', '~0').replace('/', '~1'))
                    if p in self._references:
                        return self._pointers_schemas
                    if isinstance(v, (serial.model.Dictionary, serial.model.Array, serial.model.Object)):
                        self._get_schemas(
                            v,
                            p,
                            root=root,
                            types=(property,),
                            path_phrase=(
                                [name]
                                if isinstance(v, model.Operation) and isinstance(o, model.PathItem) else
                                []
                            ) + copy(path_phrase),
                            path_operation_phrase=copy(path_operation_phrase),
                            operation_phrase=copy(operation_phrase),
                        )
        else:
            raise TypeError(o)
        return self._pointers_schemas

    def __str__(self):
        lines = [
            '# region Backwards Compatibility',
            'from __future__ import nested_scopes, generators, division, absolute_import, with_statement,\\',
            'print_function, unicode_literals',
            'from future import standard_library',
            'standard_library.install_aliases()',
            'from builtins import *',
            '# endregion',
            '',
            'import serial',
            '',
            'try:',
            '    import typing',
            '    from typing import Union, Dict, Any',
            'except ImportError:',
            '    typing = Union = Any = None',
            '',
            ''
        ]
        for p, m in self._pointers_models.items():
            lines.append(get_source(m))
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
                    if v[:23] == 'serial.meta.Properties(':
                        v = v[23:-1]
                    lines.append(
                        'serial.meta.writable(%s).%s = %s' % (
                            cn, p, v
                        )
                    )
            lines.append('')
        return '\n'.join(lines)


if __name__ == '__main__':
    pass
