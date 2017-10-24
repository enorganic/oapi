from __future__ import nested_scopes, generators, division, absolute_import, with_statement, print_function,\
    unicode_literals
from future import standard_library
standard_library.install_aliases()
from builtins import *


class ReferenceError(RuntimeError):

    pass


class ReferenceLoopError(ReferenceError):

    pass


class ReferencePointerError(ReferenceError):

    pass