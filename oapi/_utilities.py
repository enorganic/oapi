import functools
from typing import (
    Any,
    Callable,
)


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
