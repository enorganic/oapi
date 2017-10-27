from __future__ import nested_scopes, generators, division, absolute_import, with_statement, print_function,\
    unicode_literals

import re
from collections import namedtuple, OrderedDict
from copy import copy
from urllib.parse import urljoin
from urllib.request import urlopen

from future import standard_library

import serial
from oapi.model import resolve_references
from serial import meta
from serial.model import from_meta
from serial.utilities import class_name, get_source

standard_library.install_aliases()
from builtins import *
#

from io import IOBase

from oapi import model, errors


class Model(object):


    def __init__(self, openapi, url=None):
        # type: (Union[IOBase, str], str) -> None
        if not isinstance(openapi, model.OpenAPI):
            openapi = model.OpenAPI(openapi)
        m = meta.read(openapi)
        if url is not None:
            m.url = url
        self._root = openapi
        self._references = OrderedDict()
        self._schemas = OrderedDict()
        self._names = set()
        self._get_schemas(self._root, (m.url or '') + '#')

    def _get_schemas(
        self,
        o,  # type: Union[serial.model.Model]
        pointer,  # type: str
        operation_id=None,  # type: Optional[str]
        keys=None,  # type: Optional[str]
        types=None  # Optional[Union[type, serial.properties.Property]]
    ):
        # type: (...) -> dict
        if pointer in self._references:
            return self._schemas
        if keys is None:
            keys = []
        if isinstance(o, model.Reference):
            operation_id = None
            keys = [o.ref.split('/')[-1]]
            pointer = urljoin(pointer, o.ref)
            if pointer in self._references:
                return self._schemas
            o = model.resolve_references(o, root=self._root, recursive=False)
            if types:
                o = serial.model.unmarshal(o, types=types)
            self._references[pointer] = o
        if hasattr(o, 'operation_id') and (o.operation_id is not None):
            operation_id = o.operation_id
        if isinstance(o, model.Schema):
            if pointer in self._schemas:
                return self._schemas
            if o.type_ == 'object':
                if keys:
                    key = '/'.join(keys)
                    pre = re.compile(r'{([^{}]+)}')
                    if pre.search(key):
                        key = pre.sub('', key)
                        if key[-3:].lower() == 'ies':
                            key = key[:-3] + 'y'
                        elif key[-1].lower() == 's':
                            key = key[:-1]
                    cn = class_name(key)
                    if cn in self._names:
                        oid_cn = class_name(operation_id)
                        if oid_cn in self._names:
                            ucn = cn
                            i = 1
                            while ucn in self._names:
                                ucn = cn + str(i)
                                i += 1
                            cn = ucn
                        else:
                            cn = class_name(oid_cn)
                    self._names.add(cn)
                else:
                    cn = None
                self._schemas[pointer] = (cn, o)
            # else:
            #    return self._schemas
        if not isinstance(o, serial.model.Model):
            return self._schemas
        m = meta.read(o)
        if isinstance(o, serial.model.Dictionary):
            for k, v in o.items():
                p = '%s/%s' % (pointer, k.replace('~', '~0').replace('/', '~1'))
                if p in self._references:
                    continue
                if isinstance(v, model.Reference):
                    self._get_schemas(
                        v,
                        p,
                        types=m.value_types,
                        operation_id=operation_id,
                        keys=copy(keys)
                    )
                elif isinstance(v, (serial.model.Dictionary, serial.model.Array, serial.model.Object)):
                    value_keys = copy(keys)
                    if isinstance(o, model.Paths):
                        value_keys = [k]
                    elif not isinstance(o, model.Responses):
                        value_keys.append(k)
                    self._get_schemas(
                        v,
                        p,
                        types=m.value_types,
                        operation_id=operation_id,
                        keys=value_keys
                    )
        elif isinstance(o, serial.model.Array):
            for i in range(len(o)):
                v = o[i]
                p = '%s[%s]' % (pointer, str(i))
                if p in self._references:
                    return self._schemas
                if isinstance(v, (serial.model.Dictionary, serial.model.Array, serial.model.Object)):
                    self._get_schemas(
                        v,
                        p,
                        types=m.item_types,
                        operation_id=operation_id,
                        keys=copy(keys)
                    )
        elif isinstance(o, serial.model.Object):
            object_properties = tuple(m.properties.items())
            if isinstance(o, model.OpenAPI):
                object_properties = sorted(
                    object_properties,
                    key=lambda kv: 1 if kv[0] in ('components', 'definitions') else 0
                )
            for name, property in object_properties:
                v = getattr(o, name)
                if v is not None:
                    n = property.name or name
                    p = '%s/%s' % (pointer, n.replace('~', '~0').replace('/', '~1'))
                    if p in self._references:
                        return self._schemas
                    property_keys = copy(keys)
                    # if isinstance(v, model.Operation):
                    #     property_keys.append(n)
                    if isinstance(v, (serial.model.Dictionary, serial.model.Array, serial.model.Object)):
                        self._get_schemas(
                            v,
                            p,
                            types=(property,),
                            operation_id=operation_id,
                            keys=property_keys
                        )
        return self._schemas

    def __str__(self):
        lines = [
            'from __future__ import nested_scopes, generators, division, absolute_import, with_statement,\\',
            'print_function, unicode_literals',
            'from urllib.request import urlopen',
            'from future import standard_library',
            '',
            'standard_library.install_aliases()',
            '',
            'from builtins import *',
            '#',
            'from serial import model, meta, properties'
            '',
            ''
        ]
        return ''.join(lines)


if __name__ == '__main__':
    # print(urljoin('http://www.google.com/tacos#/so/bad', '#/so/good'))
    # print(get_source(from_meta('OpenAPI2', meta.read(model.OpenAPI))))
    with urlopen('http://devdocs.magento.com/swagger/schemas/latest-2.2.schema.json') as response:
        m = Model(response)
        for k, v in m._schemas.items():
            print(repr(k))
            print(repr(v[0]))
            print()
