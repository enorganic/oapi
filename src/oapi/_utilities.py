from __future__ import annotations

import functools
from typing import TYPE_CHECKING, Any, Callable
from warnings import warn

import sob

if TYPE_CHECKING:
    from collections.abc import Hashable, Iterable


def rename_parameters(
    **old_new_parameter_names: str,
) -> Callable[..., Callable[..., Any]]:
    """
    This decorator maps legacy parameter names to new parameter names, for
    backwards compatibility.
    """

    def decorating_function(
        function: Callable[..., Any],
    ) -> Callable[..., Any]:
        @functools.wraps(function)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """
            This function wraps the original and translates old parameter
            names to new parameter names
            """
            old_parameter_name: str
            new_parameter_name: str
            for old_parameter_name in set(kwargs.keys()) & set(
                old_new_parameter_names.keys()
            ):
                new_parameter_name = old_new_parameter_names[
                    old_parameter_name
                ]
                kwargs[new_parameter_name] = kwargs.pop(old_parameter_name)
            # Execute the wrapped function
            return function(*args, **kwargs)

        return wrapper

    return decorating_function


def get_string_format_property(
    format_: str | None,
    content_encoding: str | None,
    *,
    required: bool = False,
) -> sob.abc.Property:
    if format_ == "date-time":
        return sob.DateTimeProperty(required=required)
    if format_ == "date":
        return sob.DateProperty(required=required)
    if (format_ in ("byte", "binary", "base64")) or content_encoding:
        return sob.BytesProperty(required=required)
    return sob.StringProperty(required=required)


def get_type_format_property(
    type_: str | None,
    format_: str | None = None,
    content_media_type: str | None = None,
    content_encoding: str | None = None,
    default_type: type[sob.abc.Property] = sob.Property,
    *,
    required: bool = False,
) -> sob.abc.Property:
    if type_ == "number":
        return sob.NumberProperty(required=required)
    if type_ == "integer":
        return sob.IntegerProperty(required=required)
    if type_ == "string":
        return get_string_format_property(
            format_, content_encoding, required=required
        )
    if type_ == "boolean":
        return sob.BooleanProperty(required=required)
    if type_ == "file":
        return sob.BytesProperty(required=required)
    if type_ == "array":
        return sob.ArrayProperty(required=required)
    if type_ == "object":
        return sob.Property(required=required)
    if type_ is None:
        if content_media_type or content_encoding:
            return sob.BytesProperty(required=required)
        return default_type(required=required)
    message: str = f"Unknown schema type: {type_}"
    raise ValueError(message)


def iter_distinct(items: Iterable[Hashable]) -> Iterable:
    """
    Yield distinct elements, preserving order
    """
    yield from dict.fromkeys(items).keys()


def deprecated(
    message: str,
    category: type[Warning] = DeprecationWarning,
    stacklevel: int = 2,
) -> Callable[..., Callable[..., Any]]:
    """
    This decorator marks a function as deprecated, and issues a
    deprecation warning when the function is called.
    """

    def decorating_function(
        function_or_class: type | Callable[..., Any],
    ) -> Callable[..., Any]:
        @functools.wraps(function_or_class)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            warn(
                message,
                category,
                stacklevel=stacklevel,
            )
            return function_or_class(*args, **kwargs)

        return wrapper

    return decorating_function
