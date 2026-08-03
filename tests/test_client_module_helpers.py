from __future__ import annotations

from oapi.client import (
    _get_relative_module_import,
    _get_relative_module_path,
    _iter_path_item_operations,
    _schema_defines_model,
    _strip_def_decorators,
    get_default_method_name_from_path_method_operation,
)
from oapi.oas.model import Operation, Parameter, PathItem, Schema


def test_get_relative_module_path_across_directories() -> None:
    assert _get_relative_module_path("a/b/c.py", "d/e/f.py") == "...a.b.c"


def test_get_relative_module_path_within_the_same_directory() -> None:
    assert _get_relative_module_path("a/b/c.py", "a/b/f.py") == ".c"


def test_get_relative_module_import_across_directories() -> None:
    result: str = _get_relative_module_import("a/b/c.py", "d/e/f.py")
    assert result == "from ...a.b import c"


def test_get_relative_module_import_within_the_same_directory() -> None:
    result: str = _get_relative_module_import("a/b/c.py", "a/b/f.py")
    assert result == "from . import c"


def test_schema_defines_model_for_object_and_array_types() -> None:
    assert _schema_defines_model(Schema({"type": "object"})) is True
    assert _schema_defines_model(Schema({"type": "array"})) is True


def test_schema_defines_model_for_primitive_types() -> None:
    assert _schema_defines_model(Schema({"type": "string"})) is False


def test_schema_defines_model_accepts_a_parameter() -> None:
    parameter: Parameter = Parameter(
        {"name": "x", "in": "query", "type": "object"}
    )
    assert _schema_defines_model(parameter) is True


def test_iter_path_item_operations_yields_name_and_operation_pairs() -> None:
    path_item: PathItem = PathItem(
        {
            "get": {"operationId": "getX"},
            "post": {"operationId": "postX"},
        }
    )
    name: str
    operation: Operation
    result: list[tuple[str, str | None]] = [
        (name, operation.operation_id)
        for name, operation in _iter_path_item_operations(path_item)
    ]
    assert result == [("get", "getX"), ("post", "postX")]


def test_iter_path_item_operations_skips_unset_methods() -> None:
    path_item: PathItem = PathItem({"get": {"operationId": "getX"}})
    result: list[str] = [
        name for name, _operation in _iter_path_item_operations(path_item)
    ]
    assert result == ["get"]


def test_get_default_method_name_derives_from_path_when_no_operation_id() -> (
    None
):
    result: str = get_default_method_name_from_path_method_operation(
        "/foo/{id}/bar", "get", None
    )
    assert result == "get_foo_id_bar"


def test_get_default_method_name_prefers_the_operation_id() -> None:
    result: str = get_default_method_name_from_path_method_operation(
        "/foo/{id}/bar", "get", "myOperationId"
    )
    assert result == "my_operation_id"


def test_strip_def_decorators_removes_a_leading_decorator() -> None:
    source: str = "@decorator\ndef foo():\n    pass\n"
    assert _strip_def_decorators(source) == "def foo():\n    pass\n"


def test_strip_def_decorators_is_a_no_op_without_a_decorator() -> None:
    source: str = "def foo():\n    pass\n"
    assert _strip_def_decorators(source) == source
