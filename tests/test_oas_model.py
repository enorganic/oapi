from __future__ import annotations

import pytest
import sob

from oapi.oas.model import (
    Parameter,
    Reference,
    Schema,
    _parameter_after_validate,
    _reference_after_unmarshal,
    _schema_after_validate,
)


@pytest.mark.parametrize(
    ("type_", "format_"),
    [
        ("integer", "int32"),
        ("integer", "int64"),
        ("number", "float"),
        ("number", "double"),
        ("string", "byte"),
        ("string", "binary"),
        ("string", "date"),
        ("string", "date-time"),
        ("string", "password"),
    ],
)
def test_schema_validate_accepts_matching_type_and_format(
    type_: str, format_: str
) -> None:
    schema: Schema = Schema({"type": type_, "format": format_})
    sob.validate(schema)


def test_schema_validate_rejects_integer_with_a_string_format() -> None:
    schema: Schema = Schema({"type": "integer", "format": "date"})
    with pytest.raises(sob.errors.ValidationError, match="int32.*int64"):
        sob.validate(schema)


def test_schema_validate_rejects_number_with_an_integer_format() -> None:
    schema: Schema = Schema({"type": "number", "format": "int32"})
    with pytest.raises(sob.errors.ValidationError, match="float.*double"):
        sob.validate(schema)


def test_schema_validate_rejects_string_with_a_numeric_format() -> None:
    schema: Schema = Schema({"type": "string", "format": "int32"})
    with pytest.raises(sob.errors.ValidationError, match="byte.*binary"):
        sob.validate(schema)


def test_schema_after_validate_rejects_a_non_schema_argument() -> None:
    with pytest.raises(TypeError):
        _schema_after_validate("not a schema")  # type: ignore[arg-type]


def test_parameter_validate_rejects_more_than_one_content_entry() -> None:
    parameter: Parameter = Parameter(
        {
            "name": "x",
            "in": "query",
            "content": {
                "application/json": {"schema": {"type": "string"}},
                "application/xml": {"schema": {"type": "string"}},
            },
        }
    )
    with pytest.raises(
        sob.errors.ValidationError, match="only one mapped value"
    ):
        sob.validate(parameter)


def test_parameter_validate_rejects_both_content_and_schema() -> None:
    parameter: Parameter = Parameter(
        {
            "name": "x",
            "in": "query",
            "schema": {"type": "string"},
            "content": {"application/json": {"schema": {"type": "string"}}},
        }
    )
    with pytest.raises(sob.errors.ValidationError, match="not \\*both\\*"):
        sob.validate(parameter)


def test_parameter_validate_delegates_to_schema_validation() -> None:
    """
    `_parameter_after_validate` calls `_schema_after_validate(parameter)`
    as its last step (a `Parameter` shares the `type_`/`format_` fields a
    `Schema` has), so an invalid format/type combination on a
    `Parameter` itself -- not on a nested `schema` -- is also rejected.
    """
    parameter: Parameter = Parameter(
        {"name": "x", "in": "query", "type": "integer", "format": "date"}
    )
    with pytest.raises(sob.errors.ValidationError, match="int32.*int64"):
        sob.validate(parameter)


def test_parameter_after_validate_rejects_a_non_parameter_argument() -> None:
    with pytest.raises(TypeError):
        _parameter_after_validate("not a parameter")  # type: ignore[arg-type]


def test_reference_after_unmarshal_rejects_a_non_reference_argument() -> None:
    with pytest.raises(TypeError):
        _reference_after_unmarshal("not a reference")  # type: ignore[arg-type]


def test_reference_after_unmarshal_requires_a_ref_attribute() -> None:
    """
    `Reference()` (no data) has no `$ref` set. `data["$ref"]` does NOT
    raise `KeyError` here -- `$ref` is a declared property on
    `Reference`, and `sob` returns `None` for a declared-but-unset
    property rather than raising. So `ref = typing.cast(str,
    data["$ref"])` in the real `try` block simply succeeds with `ref =
    None`, and the `except KeyError:` handler never runs for this (or
    any) `Reference` -- it's dead code under current `sob` behavior.
    The real, asserted `ValueError` comes from the `if ref is None:`
    check that follows.
    """
    with pytest.raises(ValueError, match="must have a"):
        _reference_after_unmarshal(Reference())


def test_unmarshal_also_rejects_a_reference_missing_ref() -> None:
    """
    The same real validation is reachable through the public
    `sob.unmarshal` entry point (not just by calling the private hook
    directly): `sob.unmarshal` wraps the underlying `ValueError` in its
    own composite "does not match any of the expected types" error, but
    that wrapper's message embeds the original text.
    """
    with pytest.raises(ValueError, match="must have a"):
        sob.unmarshal({}, types=(Reference,))


def test_reference_accepts_a_genuinely_arbitrary_extra_property() -> None:
    """
    Exercises `_add_object_property`'s "this is a genuinely new
    property" branch: OpenAPI 3.1 allows arbitrary extra attributes on a
    `Reference` object (its `patternProperties`), and
    `_reference_before_setitem` dynamically adds a property definition
    for any key it hasn't seen before. `summary` and `description` are
    already pre-declared properties on `Reference` (confirmed via
    `sob.read_object_meta(Reference).properties`), so a genuinely novel
    key is needed to exercise this -- OpenAPI's own convention for
    arbitrary extensions (`x-`-prefixed keys) is used here.
    """
    reference: Reference = Reference(
        {"$ref": "#/components/schemas/Foo", "x-custom": "a value"}
    )
    assert reference["x-custom"] == "a value"
