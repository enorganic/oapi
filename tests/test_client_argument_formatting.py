from __future__ import annotations

import decimal
from datetime import date, datetime

import pytest
import sob

from oapi.client import (
    URLENCODE_SAFE,
    _censor_long_json_strings,
    _format_deep_object_argument_value,
    _format_dot_object_argument_value,
    _format_form_argument_value,
    _format_label_argument_value,
    _format_matrix_argument_value,
    _format_pipe_delimited_argument_value,
    _format_primitive_value,
    _format_simple_argument_value,
    _format_space_delimited_argument_value,
    _item_is_not_empty,
    _iter_items,
    format_argument_value,
    urlencode,
)
from oapi.oas.model import Reference


def test_iter_items_yields_mapping_items() -> None:
    result: list[tuple[str, object]] = list(_iter_items({"a": 1, "b": 2}))
    assert result == [("a", 1), ("b", 2)]


def test_iter_items_yields_sob_dictionary_items() -> None:
    dictionary: sob.abc.Dictionary = sob.model.Dictionary({"x": 1, "y": 2})
    result: list[tuple[str, object]] = list(_iter_items(dictionary))
    assert result == [("x", 1), ("y", 2)]


def test_iter_items_yields_sob_object_property_values() -> None:
    """
    A `sob.abc.Object` iterates by *property name* (not by JSON key) --
    `Reference`'s `$ref` property is named `ref` internally (since `$ref`
    is not a valid Python identifier), and unset properties (`description`
    here) are yielded too, with a value of `None`.
    """
    reference: Reference = Reference(
        {"$ref": "#/components/schemas/Foo", "summary": "hi"}
    )
    result: list[tuple[str, object]] = list(_iter_items(reference))
    assert result == [
        ("description", None),
        ("ref", "#/components/schemas/Foo"),
        ("summary", "hi"),
    ]


def test_iter_items_yields_from_a_sequence_of_tuples() -> None:
    result: list[tuple[str, object]] = list(_iter_items([("a", 1), ("b", 2)]))
    assert result == [("a", 1), ("b", 2)]


def test_urlencode_bumps_nested_dictionary_values_to_the_top_level() -> None:
    """
    When a query value is itself a dictionary/mapping, `urlencode` merges
    that mapping's items into the top-level query instead of nesting it.
    """
    encoded: str = urlencode({"a": 1, "nested": {"b": 2, "c": 3}})
    assert encoded == "a=1&b=2&c=3"


def test_urlencode_repeats_a_key_for_sequence_values_by_default() -> None:
    encoded: str = urlencode({"a": [1, 2, 3]})
    assert encoded == "a=1&a=2&a=3"


def test_urlencode_default_safe_characters_are_not_percent_encoded() -> None:
    encoded: str = urlencode({"a": "|;,/=+[]."})
    assert encoded == f"a={URLENCODE_SAFE}"


@pytest.mark.parametrize(
    ("item", "expected"),
    [
        (("k", "v"), True),
        (("k", None), False),
        (("k", ""), False),
        (("", "v"), False),
    ],
)
def test_item_is_not_empty(item: tuple[str, object], expected: bool) -> None:
    assert _item_is_not_empty(item) is expected


def test_censor_long_json_strings_replaces_strings_over_the_limit() -> None:
    text: str = '{"short": "ok", "long": "' + ("x" * 3000) + '"}'
    censored: str = _censor_long_json_strings(text)
    assert censored == '{"short": "ok", "long": "..."}'


def test_censor_long_json_strings_leaves_short_strings_untouched() -> None:
    text: str = '{"short": "ok"}'
    assert _censor_long_json_strings(text) == text


def test_censor_long_json_strings_respects_a_custom_limit() -> None:
    text: str = '{"value": "abcdef"}'
    censored: str = _censor_long_json_strings(text, limit=6)
    assert censored == '{"value": "..."}'


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, None),
        ("abc", "abc"),
        (True, "true"),
        (False, "false"),
        (42, "42"),
        (3.14, "3.14"),
        (decimal.Decimal("1.5"), "1.5"),
        (b"hello", "aGVsbG8="),
        (date(2024, 1, 1), "2024-01-01"),
        (datetime(2024, 1, 1, 12, 0, 0), "2024-01-01T12:00:00"),
    ],
)
def test_format_primitive_value(value: object, expected: str | None) -> None:
    assert _format_primitive_value(value) == expected  # type: ignore[arg-type]


def test_format_primitive_value_rejects_unsupported_types() -> None:
    with pytest.raises(TypeError):
        _format_primitive_value(object())  # type: ignore[arg-type]


def test_format_simple_argument_value_with_a_primitive() -> None:
    assert _format_simple_argument_value(5) == "5"


def test_format_simple_argument_value_with_a_sequence() -> None:
    assert _format_simple_argument_value([1, 2, 3]) == "1,2,3"


def test_format_simple_argument_value_with_a_dictionary_not_exploded() -> None:
    assert _format_simple_argument_value({"a": 1, "b": 2}) == "a,1,b,2"


def test_format_simple_argument_value_dict_explode_iterates_dict_keys() -> (
    None
):
    """
    `_format_simple_argument_value`'s exploded-dictionary branch iterates
    `value` directly (`for item in value`), which -- for a plain `dict` --
    yields its *keys*, not `(key, value)` pairs. `item[0]`/`item[1]` then
    index into that key string rather than a tuple. This only avoids
    crashing when every key is at least 2 characters long, and the
    "value" half of the output is actually the second character of the
    key, not the dictionary's mapped value. This is real, current
    behavior of the function -- documented here, not corrected.
    """
    result: str = _format_simple_argument_value(
        {"ab": 1, "cd": 2}, explode=True
    )
    assert result == "a=b,c=d"


def test_format_simple_argument_value_dict_explode_crashes_on_short_keys() -> (
    None
):
    with pytest.raises(IndexError):
        _format_simple_argument_value({"a": 1, "b": 2}, explode=True)


def test_format_simple_argument_value_rejects_unsupported_types() -> None:
    with pytest.raises(ValueError, match=".*"):
        _format_simple_argument_value(object())  # type: ignore[arg-type]


def test_format_label_argument_value_with_a_primitive() -> None:
    assert _format_label_argument_value(5) == ".5"


def test_format_label_argument_value_with_a_sequence_not_exploded() -> None:
    assert _format_label_argument_value([1, 2, 3]) == ".1,2,3"


def test_format_label_argument_value_with_a_sequence_exploded() -> None:
    assert _format_label_argument_value([1, 2, 3], explode=True) == ".1.2.3"


def test_format_label_argument_value_dict_explode_shares_the_dict_quirk() -> (
    None
):
    with pytest.raises(IndexError):
        _format_label_argument_value({"a": 1, "b": 2}, explode=True)


def test_format_label_argument_value_rejects_unsupported_exploded_types() -> (
    None
):
    with pytest.raises(ValueError, match=".*"):
        _format_label_argument_value(object(), explode=True)  # type: ignore[arg-type]


def test_format_matrix_argument_value_with_none() -> None:
    assert _format_matrix_argument_value("id", None) is None


def test_format_matrix_argument_value_with_a_primitive() -> None:
    assert _format_matrix_argument_value("id", 5) == ";id=5"


def test_format_matrix_argument_value_with_a_sequence_exploded() -> None:
    result = _format_matrix_argument_value("id", [3, 4, 5], explode=True)
    assert result == ";id=3;id=4;id=5"


def test_format_matrix_argument_value_with_a_sequence_not_exploded() -> None:
    result = _format_matrix_argument_value("id", [3, 4, 5], explode=False)
    assert result == ";id=3,4,5"


def test_format_matrix_argument_value_dict_explode_shares_the_dict_quirk() -> (
    None
):
    """
    Like `_format_simple_argument_value`, the exploded-dictionary branch
    here also does `for item in value` over a plain `dict`, hitting the
    same "iterates keys, not pairs" issue when a key is a single
    character.
    """
    with pytest.raises(IndexError):
        _format_matrix_argument_value("id", {"a": 1, "b": 2}, explode=True)


def test_format_matrix_argument_value_rejects_unsupported_exploded_types() -> (
    None
):
    with pytest.raises(TypeError):
        _format_matrix_argument_value("id", object(), explode=True)  # type: ignore[arg-type]


def test_format_space_delimited_argument_value_with_a_primitive() -> None:
    assert _format_space_delimited_argument_value(5) == "5"


def test_format_space_delimited_argument_value_with_a_sequence() -> None:
    assert _format_space_delimited_argument_value([1, 2, 3]) == "1 2 3"


def test_format_space_delimited_argument_value_explode_uses_form() -> None:
    result = _format_space_delimited_argument_value([1, 2, 3], explode=True)
    assert result == ("1", "2", "3")


def test_format_space_delimited_argument_value_rejects_non_sequences() -> None:
    with pytest.raises(ValueError, match=".*"):
        _format_space_delimited_argument_value({"a": 1}, explode=False)


def test_format_pipe_delimited_argument_value_with_a_primitive() -> None:
    assert _format_pipe_delimited_argument_value(None) is None
    assert _format_pipe_delimited_argument_value(5) == "5"


def test_format_pipe_delimited_argument_value_with_a_sequence() -> None:
    assert _format_pipe_delimited_argument_value([1, 2, 3]) == "1|2|3"


def test_format_pipe_delimited_argument_value_exploded_delegates_to_form() -> (
    None
):
    result = _format_pipe_delimited_argument_value([1, 2, 3], explode=True)
    assert result == ("1", "2", "3")


def test_format_pipe_delimited_argument_value_rejects_non_sequences() -> None:
    with pytest.raises(ValueError, match=".*"):
        _format_pipe_delimited_argument_value({"a": 1}, explode=False)


def test_format_form_argument_value_with_a_primitive() -> None:
    assert _format_form_argument_value(5) == "5"


def test_format_form_argument_value_with_a_sequence_not_exploded() -> None:
    assert _format_form_argument_value([1, 2, 3]) == "1,2,3"


def test_format_form_argument_value_with_a_sequence_exploded() -> None:
    result = _format_form_argument_value([1, 2, 3], explode=True)
    assert result == ("1", "2", "3")


def test_format_form_argument_value_with_a_dictionary_exploded() -> None:
    """
    Unlike the "simple"/"label"/"matrix" formatters, `_format_form_
    argument_value` recognizes a plain `dict` as one of `_ITEMIZED_TYPES`
    and uses `_iter_items`, so exploding a dictionary correctly yields
    `(key, value)` pairs rather than iterating its keys.
    """
    result = _format_form_argument_value({"a": 1, "b": 2}, explode=True)
    assert result == {"a": "1", "b": "2"}


def test_format_form_argument_value_exploded_merges_duplicate_keys() -> None:
    result = _format_form_argument_value(
        [("a", 1), ("a", 2), ("b", 3)], explode=True
    )
    assert result == {"a": ["1", "2"], "b": "3"}


def test_format_form_argument_value_exploded_appends_a_third_duplicate() -> (
    None
):
    """
    A third occurrence of the same key exercises the "already collected
    into a list" append branch, distinct from the second occurrence
    (which converts a scalar into a two-item list).
    """
    result = _format_form_argument_value(
        [("a", 1), ("a", 2), ("a", 3)], explode=True
    )
    assert result == {"a": ["1", "2", "3"]}


def test_format_form_argument_value_rejects_unsupported_exploded_types() -> (
    None
):
    with pytest.raises(ValueError, match=".*"):
        _format_form_argument_value(object(), explode=True)  # type: ignore[arg-type]


def test_format_deep_object_argument_value_with_none() -> None:
    assert _format_deep_object_argument_value("id", None) is None


def test_format_deep_object_argument_value_with_a_primitive() -> None:
    assert _format_deep_object_argument_value("id", 5) == "5"


def test_format_deep_object_argument_value_requires_explode() -> None:
    with pytest.raises(ValueError, match="only supports `explode=True`"):
        _format_deep_object_argument_value("id", {"a": 1}, explode=False)


def test_format_deep_object_argument_value_with_a_flat_dictionary() -> None:
    result = _format_deep_object_argument_value(
        "id", {"a": 1, "b": 2}, explode=True
    )
    assert result == {"id[a]": "1", "id[b]": "2"}


def test_format_deep_object_argument_value_with_a_nested_dictionary() -> None:
    result = _format_deep_object_argument_value(
        "id", {"a": {"b": 1}}, explode=True
    )
    assert result == {"id[a][b]": "1"}


def test_format_deep_object_argument_value_dict_of_sequence_is_broken() -> (
    None
):
    """
    A dictionary value whose entry is itself a sequence of primitives
    (rather than a sequence of dictionaries) hits a genuine bug: the
    recursive call for each primitive item returns a plain formatted
    string (e.g. `"1"`), and the caller then does
    `deep_object.update(**that_string)`, which fails because a `str` is
    not a mapping. This is real, current behavior -- documented here, not
    corrected.
    """
    with pytest.raises(TypeError, match="argument after \\*\\*"):
        _format_deep_object_argument_value("id", {"a": [1, 2]}, explode=True)


def test_format_deep_object_argument_value_dict_rejects_bad_types() -> None:
    with pytest.raises(TypeError):
        _format_deep_object_argument_value("id", {"a": object()}, explode=True)


def test_format_deep_object_argument_value_with_a_sequence_of_primitives() -> (
    None
):
    result = _format_deep_object_argument_value("id", [1, 2, 3], explode=True)
    assert result == {"id[0]": "1", "id[1]": "2", "id[2]": "3"}


def test_format_deep_object_argument_value_with_a_sequence_of_dicts() -> None:
    result = _format_deep_object_argument_value(
        "id", [{"a": 1}, {"b": 2}], explode=True
    )
    assert result == {"id[0][a]": "1", "id[1][b]": "2"}


def test_format_deep_object_argument_value_with_nested_sequences() -> None:
    result = _format_deep_object_argument_value(
        "id", [[1, 2], [3, 4]], explode=True
    )
    assert result == {
        "id[0][0]": "1",
        "id[0][1]": "2",
        "id[1][0]": "3",
        "id[1][1]": "4",
    }


def test_format_deep_object_argument_value_rejects_a_non_sequence() -> None:
    """
    A value that is neither a primitive, an itemized type (dict/Object),
    nor a `collections.abc.Sequence` -- e.g. a `set` -- falls through to
    the function's final `raise ValueError(value)`. This is a real,
    reachable guard (unlike the two lines noted as dead code in Global
    Constraints), just not exercised by any of the styles' other tests,
    since query/path/header argument values are otherwise always a
    primitive, mapping, or sequence.
    """
    with pytest.raises(ValueError, match=".*"):
        _format_deep_object_argument_value("id", {1, 2}, explode=True)


def test_format_dot_object_argument_value_uses_dot_notation() -> None:
    result = _format_dot_object_argument_value(
        "id", {"a": {"b": 1}}, explode=True
    )
    assert result == {"id.a.b": "1"}


@pytest.mark.parametrize(
    ("style", "value", "explode", "expected"),
    [
        ("simple", 5, False, "5"),
        ("label", 5, False, ".5"),
        ("matrix", 5, False, ";id=5"),
        ("form", [1, 2], False, "1,2"),
        ("spaceDelimited", [1, 2], False, "1 2"),
        ("pipeDelimited", [1, 2], False, "1|2"),
    ],
)
def test_format_argument_value_dispatches_by_style(
    style: str, value: object, explode: bool, expected: object
) -> None:
    assert (
        format_argument_value("id", value, style, explode=explode)  # type: ignore[arg-type]
        == expected
    )


def test_format_argument_value_dispatches_deep_object_and_dot_object() -> None:
    assert format_argument_value(
        "id", {"a": 1}, "deepObject", explode=True
    ) == {"id[a]": "1"}
    assert format_argument_value(
        "id", {"a": 1}, "dotObject", explode=True
    ) == {"id.a": "1"}


def test_format_argument_value_rejects_an_unknown_style() -> None:
    with pytest.raises(ValueError, match="bogus"):
        format_argument_value("id", 5, "bogus")


def test_format_argument_value_marshals_a_sob_model_first() -> None:
    reference: Reference = Reference({"$ref": "#/x"})
    assert format_argument_value("id", reference, "simple") == "$ref,#/x"


def test_format_argument_value_multipart_bypasses_formatting_for_bytes() -> (
    None
):
    assert (
        format_argument_value("id", b"raw bytes", "simple", multipart=True)
        == b"raw bytes"
    )


def test_format_argument_value_multipart_bypasses_a_readable() -> None:
    import io

    readable: io.BytesIO = io.BytesIO(b"data")
    assert (
        format_argument_value("id", readable, "simple", multipart=True)
        is readable
    )


def test_format_argument_value_multipart_bypasses_a_sequence_of_bytes() -> (
    None
):
    value: list[bytes] = [b"a", b"b"]
    assert (
        format_argument_value("id", value, "simple", multipart=True) is value
    )
