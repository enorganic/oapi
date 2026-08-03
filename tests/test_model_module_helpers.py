from __future__ import annotations

from datetime import date, datetime

import sob

from oapi.model import (
    _append_property_type,
    _get_schema_type,
    _types_from_enum_values,
    get_default_class_name_from_pointer,
)
from oapi.oas.model import Items, Schema


def test_get_schema_type_returns_the_explicit_type() -> None:
    assert _get_schema_type(Schema({"type": "string"})) == "string"


def test_get_schema_type_infers_object_from_properties() -> None:
    schema: Schema = Schema({"properties": {"a": {"type": "string"}}})
    assert _get_schema_type(schema) == "object"


def test_get_schema_type_infers_object_from_additional_properties() -> None:
    schema: Schema = Schema({"additionalProperties": {"type": "string"}})
    assert _get_schema_type(schema) == "object"


def test_get_schema_type_infers_array_from_items() -> None:
    schema: Schema = Schema({"items": {"type": "string"}})
    assert _get_schema_type(schema) == "array"


def test_get_schema_type_returns_none_when_nothing_is_inferable() -> None:
    assert _get_schema_type(Schema({})) is None


def test_get_schema_type_accepts_an_items_instance() -> None:
    items: Items = Items({"items": {"type": "string"}})
    assert _get_schema_type(items) == "array"


def test_types_from_enum_values_maps_python_types() -> None:
    types: sob.abc.Types = _types_from_enum_values(["a", "b", 1])
    assert list(types) == [str, int]


def test_types_from_enum_values_maps_date_and_datetime_specially() -> None:
    types: sob.abc.Types = _types_from_enum_values(
        [date(2024, 1, 1), datetime(2024, 1, 1)]
    )
    represented: list[str] = [
        sob.utilities.represent(type_) for type_ in types
    ]
    assert represented == [
        sob.utilities.represent(sob.DateProperty()),
        sob.utilities.represent(sob.DateTimeProperty()),
    ]


def test_types_from_enum_values_deduplicates_by_type() -> None:
    types: sob.abc.Types = _types_from_enum_values(["a", "b", "c"])
    assert list(types) == [str]


def test_append_property_type_adds_a_new_type() -> None:
    property_: sob.abc.Property = sob.Property()
    result: sob.abc.Property = _append_property_type(property_, str)
    assert list(result.types or ()) == [str]


def test_append_property_type_accumulates_distinct_types() -> None:
    property_: sob.abc.Property = _append_property_type(sob.Property(), str)
    property_ = _append_property_type(property_, int)
    assert list(property_.types or ()) == [str, int]


def test_append_property_type_is_idempotent_for_the_same_type() -> None:
    property_: sob.abc.Property = _append_property_type(sob.Property(), str)
    property_ = _append_property_type(property_, str)
    assert list(property_.types or ()) == [str]


def test_append_property_type_maps_date_and_datetime_specially() -> None:
    property_: sob.abc.Property = _append_property_type(
        sob.Property(), datetime
    )
    types: list[str] = [
        sob.utilities.represent(type_) for type_ in (property_.types or ())
    ]
    assert types == [sob.utilities.represent(sob.DateTimeProperty())]


def test_get_default_class_name_from_pointer_for_a_named_schema() -> None:
    result: str = get_default_class_name_from_pointer(
        "#/components/schemas/Foo"
    )
    assert result == "Foo"


def test_get_default_class_name_from_pointer_for_a_200_response() -> None:
    result: str = get_default_class_name_from_pointer(
        "#/paths/~1foo/get/responses/200/content/application~1json/schema"
    )
    assert result == "FooGetResponse"


def test_get_default_class_name_from_pointer_for_a_non_200_response() -> None:
    result: str = get_default_class_name_from_pointer(
        "#/paths/~1foo/get/responses/404/schema"
    )
    assert result == "FooGetResponse404"
