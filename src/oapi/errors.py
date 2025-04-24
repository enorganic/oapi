from __future__ import annotations


class OAPIError(Exception):
    """
    This is base class for `oapi` errors.
    """


class OAPIReferenceError(OAPIError, ValueError):
    """
    This is base class for errors encountered while attempting to resolve
    references in an OpenAPI document.
    """


class OAPIReferenceLoopError(OAPIReferenceError):
    """
    This is an error raised when a referential loop is encountered. This
    error will only be encountered if attempting to recursively dereference
    a document using `oapi.oas.references.Resolver.dereference`. Typical
    usage of `oapi` does not require dereferencing a document.
    """


class OAPIReferencePointerError(OAPIReferenceError):
    """
    This is an error raised when a reference has a pointer which
    cannot be resolved (no entity exists at the indicated position).
    """


class OAPIDuplicateClassNameError(OAPIError):
    """
    This is an error raised if/when an instance of `oapi.ModelModule`
    produces two model classes having the same name. This is not possible using
    the default naming algorithm, however a custom class naming
    callback function can be provided, so this scenario is possible in that
    case.
    """
