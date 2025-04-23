from __future__ import annotations


class OAPIError(Exception):
    pass


class OAPIReferenceError(OAPIError, ValueError):
    pass


class OAPIReferenceLoopError(OAPIReferenceError):
    pass


class OAPIReferencePointerError(OAPIReferenceError):
    pass


class OAPIDuplicateClassNameError(OAPIError):
    pass
