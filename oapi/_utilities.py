import functools
from typing import Any, Callable, Optional, Type

import sob


def rename_parameters(
    **old_new_parameter_names: str,
) -> Callable[..., Callable[..., Any]]:
    """
    This decorator maps legacy parameter names to new parameter names, for
    backwards compatibility.
    """

    def decorating_function(
        function: Callable[..., Any]
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
    format_: Optional[str],
    content_encoding: Optional[str],
    required: bool = False,
) -> sob.abc.Property:
    if format_ == "date-time":
        return sob.properties.DateTime(required=required)
    elif format_ == "date":
        return sob.properties.Date(required=required)
    elif (format_ in ("byte", "binary", "base64")) or content_encoding:
        return sob.properties.Bytes(required=required)
    else:
        return sob.properties.String(required=required)


def get_type_format_property(
    type_: Optional[str],
    format_: Optional[str] = None,
    content_media_type: Optional[str] = None,
    content_encoding: Optional[str] = None,
    required: bool = False,
    default_type: Type[sob.abc.Property] = sob.properties.Property,
) -> sob.abc.Property:
    if type_ == "number":
        return sob.properties.Number(required=required)
    elif type_ == "integer":
        return sob.properties.Integer(required=required)
    elif type_ == "string":
        return get_string_format_property(format_, content_encoding, required)
    elif type_ == "boolean":
        return sob.properties.Boolean(required=required)
    elif type_ == "file":
        return sob.properties.Bytes(required=required)
    elif type_ == "array":
        return sob.properties.Array(required=required)
    elif type_ == "object":
        return sob.properties.Property(required=required)
    elif type_ is None:
        if content_media_type or content_encoding:
            return sob.properties.Bytes(required=required)
        return default_type(required=required)
    else:
        raise ValueError(f"Unknown schema type: {type_}")
