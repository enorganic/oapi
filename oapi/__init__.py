from __future__ import nested_scopes, generators, division, absolute_import, with_statement, print_function,\
    unicode_literals

from urllib.request import urlopen

from future import standard_library

from oapi.model import resolve_references
from serial.utilities import class_name

standard_library.install_aliases()
from builtins import *
#

from io import IOBase

from oapi import model, errors


def schema2model(schema):
    # type: (Union[IOBase, str], str) -> str
    openapi = model.OpenAPI(schema)
    out = [
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
    references = {}
    for path, path_item in openapi.paths.items():
        # if ('attributes' in path) or ('categories' not in path):
        #     continue
        if path != '/V1/categories':
            continue
        # out.append('#  ' + path)
        # out.append('#      ' + str(path_item))
        # path_item = resolve_references(path_item, root=openapi)
        # out.append('#      ' + str(path_item))
        for method in ('get', 'put', 'post', 'delete', 'options', 'head', 'patch', 'trace'):
            operation = getattr(path_item, method)
            if operation is not None:
                if '200' in operation.responses:
                    schema = operation.responses['200'].schema  # type: model.Schema
                    if schema:
                        if isinstance(schema, model.Reference):
                            ref = schema.ref
                            if ref in references:
                                continue
                            cn = class_name(ref.split('/')[-1])
                            schema = resolve_references(schema, root=openapi)
                            references[ref] = schema
                        else:
                            cn = class_name(operation.operation_id) + 'Response'
                        out += [
                            'class %s(model.Object):\n' % cn,
                            '    def __init__(',
                        ]
                        for n, p in schema.properties.items():
                            out.append(
                                '        %s=None,  # type: Optional[%s],' % (
                                    n,
                                    (
                                        'int'
                                        if p.type_ == 'integer' else
                                    )
                                )
                            )
                        out.append(
                            '    ):'
                        )
                        out.append('\n')
            #     out.append('      ' + str(operation))
            #     out.append('#  %s -> %s -> %s' % (path, operation.operation_id, method))
            #     out.append(str(operation))
    return '\n'.join(out)


if __name__ == '__main__':
    with urlopen('http://devdocs.magento.com/swagger/schemas/latest-2.2.schema.json') as response:
        print(schema2model(response))