from __future__ import annotations

from collections.abc import Callable
from types import ModuleType


def test_generated_module_loader_imports_real_module(
    generated_module_loader: Callable[..., ModuleType],
) -> None:
    module = generated_module_loader(
        "VALUE = 42\n\n\ndef greet(name: str) -> str:\n"
        "    return f'hi {name}'\n"
    )
    assert module.VALUE == 42
    assert module.greet("x") == "hi x"


if __name__ == "__main__":
    pass
