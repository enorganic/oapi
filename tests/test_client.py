from __future__ import annotations

import collections.abc
import contextlib
import decimal
import gzip
import inspect
import io
import json as json_module
import logging
import pickle
import tempfile
import threading
import time
import typing
import warnings
import zlib
from collections.abc import Callable
from datetime import date, datetime
from email.message import Message
from http.cookiejar import CookieJar
from logging import Logger, getLogger
from pathlib import Path
from types import ModuleType
from urllib.error import HTTPError
from urllib.request import OpenerDirector, Request, urlopen

import pytest
import sob
from servers import Response, http_test_server

from oapi._multipart_request import MultipartRequest, Part
from oapi.client import (
    URLENCODE_SAFE,
    Client,
    SSLContext,
    _assemble_request,
    _censor_long_json_strings,
    _decode_content,
    _encode_content,
    _format_deep_object_argument_value,
    _format_dot_object_argument_value,
    _format_form_argument_value,
    _format_label_argument_value,
    _format_matrix_argument_value,
    _format_pipe_delimited_argument_value,
    _format_primitive_value,
    _format_request_data,
    _format_simple_argument_value,
    _format_space_delimited_argument_value,
    _get_file_name,
    _get_first,
    _get_relative_module_import,
    _get_relative_module_path,
    _item_is_not_empty,
    _iter_items,
    _iter_path_item_operations,
    _make_http_errors_pickleable,
    _make_loggers_pickleable,
    _make_thread_locks_pickleable,
    _remove_none,
    _represent_http_response,
    _schema_defines_model,
    _set_response_callback,
    _strip_def_decorators,
    default_retry_hook,
    format_argument_value,
    get_default_method_name_from_path_method_operation,
    get_request_curl,
    retry,
    urlencode,
)
from oapi.oas.model import (
    OpenAPI,
    Operation,
    Parameter,
    PathItem,
    Reference,
    Schema,
)

# region Argument-value formatting


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


# endregion

# region Request/response assembly


def test_get_request_curl_basic_get_has_no_data_flag() -> None:
    request: Request = Request("http://example.com/foo", method="GET")
    assert get_request_curl(request) == "curl -X GET -i http://example.com/foo"


def test_get_request_curl_censors_a_matching_header_by_default() -> None:
    request: Request = Request(
        "http://example.com/foo",
        data=b'{"a": 1}',
        method="POST",
        headers={
            "Content-type": "application/json",
            "Authorization": "Bearer secret",
        },
    )
    assert get_request_curl(request) == (
        "curl -X POST -i -H 'Authorization: ***' "
        "-H 'Content-type: application/json' "
        "-d '{\"a\": 1}' http://example.com/foo"
    )


def test_get_request_curl_censors_a_matching_form_parameter() -> None:
    form_data: bytes = urlencode(
        {"client_secret": "topsecret", "grant_type": "client_credentials"}
    ).encode()
    request: Request = Request(
        "http://example.com/token",
        data=form_data,
        method="POST",
        headers={"Content-type": "application/x-www-form-urlencoded"},
    )
    assert get_request_curl(request) == (
        "curl -X POST -i -H 'Content-type: application/x-www-form-urlencoded' "
        "-d 'client_secret=***&grant_type=client_credentials' "
        "http://example.com/token"
    )


def test_get_request_curl_non_utf8_body_becomes_a_placeholder() -> None:
    request: Request = Request(
        "http://example.com/bin", data=b"\xff\xfe\x00", method="POST"
    )
    assert get_request_curl(request) == (
        "curl -X POST -i -d *** http://example.com/bin"
    )


def test_get_request_curl_decodes_gzip_content_before_rendering() -> None:
    request: Request = Request(
        "http://example.com/foo",
        data=gzip.compress(b'{"a": 1}'),
        method="POST",
        headers={
            "Content-type": "application/json",
            "Content-encoding": "gzip",
        },
    )
    assert get_request_curl(request) == (
        "curl -X POST -i -H 'Content-encoding: gzip' "
        "-H 'Content-type: application/json' "
        "-d '{\"a\": 1}' http://example.com/foo"
    )


def test_get_request_curl_reads_a_readable_data_object() -> None:
    request: Request = Request(
        "http://example.com/foo",
        data=io.BytesIO(b'{"a":1}'),
        method="POST",
        headers={"Content-type": "application/json"},
    )
    assert get_request_curl(request) == (
        "curl -X POST -i -H 'Content-type: application/json' "
        "-d '{\"a\":1}' http://example.com/foo"
    )


def test_get_request_curl_joins_an_iterable_of_byte_chunks() -> None:
    encoded: bytes = urlencode({"a": "1", "b": "2"}).encode()
    request: Request = Request(
        "http://example.com/foo",
        method="POST",
        headers={"Content-type": "application/x-www-form-urlencoded"},
    )
    request.data = [encoded[:5], encoded[5:]]
    assert get_request_curl(request) == (
        "curl -X POST -i -H 'Content-type: application/x-www-form-urlencoded' "
        "-d 'a=1&b=2' http://example.com/foo"
    )


def test_get_request_curl_without_censored_headers_or_parameters() -> None:
    request: Request = Request(
        "http://example.com/foo",
        data=b"client_secret=topsecret",
        method="POST",
        headers={
            "Content-type": "application/x-www-form-urlencoded",
            "Authorization": "Bearer secret",
        },
    )
    assert get_request_curl(
        request, censored_headers=(), censored_parameters=()
    ) == (
        "curl -X POST -i -H 'Authorization: Bearer secret' "
        "-H 'Content-type: application/x-www-form-urlencoded' "
        "-d client_secret=topsecret http://example.com/foo"
    )


def test_represent_http_response_includes_status_headers_and_body() -> None:
    with http_test_server(
        responses={
            ("GET", "/foo"): Response(
                status=200,
                headers={"X-Custom": "abc", "Authorization": "secret"},
                body=b"hello world",
            )
        }
    ) as server:
        request: Request = Request(server.url + "/foo")
        with urlopen(request) as response:  # noqa: S310
            text: str = _represent_http_response(
                response, censored_headers=("authorization",)
            )
    assert "200" in text
    assert "X-Custom: abc" in text
    assert "Authorization: ***" in text
    assert text.endswith("hello world")


def test_set_response_callback_invokes_the_callback_on_read() -> None:
    with http_test_server(
        responses={("GET", "/foo"): Response(status=200, body=b"hello")}
    ) as server:
        request: Request = Request(server.url + "/foo")
        captured: list[str] = []
        with urlopen(request) as response:  # noqa: S310
            _set_response_callback(response, callback=captured.append)
            data: bytes = response.read()
    assert data == b"hello"
    assert len(captured) == 1
    assert captured[0].endswith("hello")


def test_set_response_callback_decodes_encoded_content_before_callback() -> (
    None
):
    with http_test_server(
        responses={
            ("GET", "/foo"): Response(
                status=200,
                headers={"Content-encoding": "gzip"},
                body=gzip.compress(b"hello gzip"),
            )
        }
    ) as server:
        request: Request = Request(server.url + "/foo")
        captured: list[str] = []
        with urlopen(request) as response:  # noqa: S310
            _set_response_callback(response, callback=captured.append)
            data: bytes = response.read()
    assert data == b"hello gzip"
    assert captured[0].endswith("hello gzip")


def test_remove_none_filters_a_mapping() -> None:
    result: collections.abc.Sequence[tuple[str, object]] = _remove_none(
        {"a": 1, "b": None, "c": "x"}
    )
    assert result == (("a", 1), ("c", "x"))


def test_remove_none_filters_a_sequence_of_pairs() -> None:
    result: collections.abc.Sequence[tuple[str, object]] = _remove_none(
        [("a", 1), ("b", None)]
    )
    assert result == (("a", 1),)


def test_get_first_returns_the_first_item() -> None:
    assert _get_first([10, 20, 30]) == 10
    assert _get_first(iter(["a", "b"])) == "a"


def test_get_first_raises_on_an_empty_iterable() -> None:
    with pytest.raises(StopIteration):
        _get_first([])


def test_format_request_data_with_a_json_string() -> None:
    assert _format_request_data('{"a": 1}', {}) == b'{"a": 1}'


def test_format_request_data_with_json_bytes() -> None:
    assert _format_request_data(b'{"a": 1}', {}) == b'{"a": 1}'


def test_format_request_data_rejects_json_and_data_together() -> None:
    with pytest.raises(
        ValueError, match="only contain form data or JSON data"
    ):
        _format_request_data('{"a": 1}', {"x": 1})


def test_format_request_data_serializes_a_sob_model_to_json() -> None:
    reference: Reference = Reference({"$ref": "#/x"})
    assert _format_request_data(reference, {}) == b'{"$ref": "#/x"}'


def test_format_request_data_urlencodes_form_data_and_drops_none() -> None:
    result: bytes | None = _format_request_data(
        None, {"a": 1, "b": None, "c": b"xyz"}
    )
    assert result == b"a=1&c=eHl6"


def test_format_request_data_base64_encodes_a_readable_value() -> None:
    result: bytes | None = _format_request_data(
        None, {"file": io.BytesIO(b"content")}
    )
    assert result == b"file=Y29udGVudA=="


def test_format_request_data_rejects_a_readable_returning_non_bytes() -> None:
    class BadReadable:
        def read(self) -> str:
            return "not bytes"

    with pytest.raises(TypeError):
        _format_request_data(None, {"file": BadReadable()})


def test_format_request_data_applies_content_encoding() -> None:
    result: bytes | None = _format_request_data(
        '{"a": 1}', {}, content_encoding="gzip"
    )
    assert result is not None
    assert result[:2] == b"\x1f\x8b"
    assert gzip.decompress(result) == b'{"a": 1}'


def test_format_request_data_with_neither_json_nor_data_returns_none() -> None:
    assert _format_request_data(None, {}) is None


def test_get_file_name_prefers_a_url_attribute() -> None:
    class WithUrl:
        url: str = "http://example.com/path/to/file.json"

    assert _get_file_name(WithUrl()) == "file.json"  # type: ignore[arg-type]


def test_get_file_name_falls_back_to_a_name_attribute() -> None:
    class WithName:
        name: str = "/local/path/data.csv"

    assert _get_file_name(WithName()) == "data.csv"  # type: ignore[arg-type]


def test_get_file_name_uses_the_default_when_neither_is_present() -> None:
    class Neither:
        pass

    assert _get_file_name(Neither(), default="fallback.bin") == "fallback.bin"  # type: ignore[arg-type]


def test_assemble_request_builds_a_plain_json_request() -> None:
    request: Request = _assemble_request(
        "http://example.com/foo",
        "post",
        '{"a": 1}',
        {},
        {"Content-type": "application/json"},
        multipart=False,
        multipart_data_headers={},
    )
    assert type(request) is Request
    assert request.method == "POST"
    assert request.full_url == "http://example.com/foo"


def test_assemble_request_builds_a_urlencoded_form_request() -> None:
    request: Request = _assemble_request(
        "http://example.com/foo",
        "post",
        None,
        {"a": 1, "b": 2},
        {},
        multipart=False,
        multipart_data_headers={},
    )
    assert request.data == b"a=1&b=2"


def test_assemble_request_rejects_a_non_http_scheme() -> None:
    with pytest.raises(ValueError, match="ftp://example.com/foo"):
        _assemble_request(
            "ftp://example.com/foo",
            "get",
            None,
            {},
            {},
            multipart=False,
            multipart_data_headers={},
        )


def test_assemble_request_url_guard_does_not_guarantee_a_valid_request() -> (
    None
):
    """
    `_assemble_request`'s own scheme guard treats a scheme-less relative
    URL like `/relative/path` as acceptable (no `:` appears before the
    first `/`), but `urllib.request.Request` itself then rejects it when
    actually constructed, since it isn't a fully qualified URL. This is
    real, current behavior of the two layers together, not something
    `_assemble_request` catches on its own.
    """
    with pytest.raises(ValueError, match="."):
        _assemble_request(
            "/relative/path",
            "get",
            None,
            {},
            {},
            multipart=False,
            multipart_data_headers={},
        )


def test_assemble_request_multipart_rejects_json() -> None:
    with pytest.raises(
        ValueError, match="only contain form data, not JSON data"
    ):
        _assemble_request(
            "http://x",
            "post",
            '{"a":1}',
            {"f": b"x"},
            {},
            multipart=True,
            multipart_data_headers={},
        )


def test_assemble_request_multipart_rejects_empty_data() -> None:
    with pytest.raises(
        ValueError, match="only contain form data, not JSON data"
    ):
        _assemble_request(
            "http://x",
            "post",
            None,
            {},
            {},
            multipart=True,
            multipart_data_headers={},
        )


def test_assemble_request_multipart_wraps_a_scalar_value_as_text() -> None:
    request: MultipartRequest = typing.cast(
        "MultipartRequest",
        _assemble_request(
            "http://x",
            "post",
            None,
            {"name": "value"},
            {},
            multipart=True,
            multipart_data_headers={},
        ),
    )
    assert request.parts is not None
    assert len(request.parts) == 1
    part: Part = list(request.parts)[0]
    assert part.headers is not None
    assert dict(part.headers) == {
        "Content-disposition": 'form-data; name="name"',
        "Content-type": "text/plain",
    }
    assert part.data == b"value"


def test_assemble_request_multipart_respects_preset_headers() -> None:
    request: MultipartRequest = typing.cast(
        "MultipartRequest",
        _assemble_request(
            "http://x",
            "post",
            None,
            {"file": b"binarydata"},
            {},
            multipart=True,
            multipart_data_headers={
                "file": {"Content-disposition": "custom; already=set"}
            },
        ),
    )
    assert request.parts is not None
    part: Part = list(request.parts)[0]
    assert part.headers is not None
    assert dict(part.headers) == {
        "Content-disposition": "custom; already=set",
        "Content-type": "application/octet-stream",
    }


def test_assemble_request_multipart_derives_a_filename_from_a_readable() -> (
    None
):
    file: io.BytesIO = io.BytesIO(b"filecontent")
    file.name = "upload.bin"
    request: MultipartRequest = typing.cast(
        "MultipartRequest",
        _assemble_request(
            "http://x",
            "post",
            None,
            {"file": file},
            {},
            multipart=True,
            multipart_data_headers={},
        ),
    )
    assert request.parts is not None
    part: Part = list(request.parts)[0]
    assert part.headers is not None
    assert dict(part.headers) == {
        "Content-disposition": (
            'form-data; name="file"; filename="upload.bin"'
        ),
        "Content-type": "application/octet-stream",
    }
    assert part.data == b"filecontent"


def test_assemble_request_multipart_creates_one_part_per_sequence_item() -> (
    None
):
    request: MultipartRequest = typing.cast(
        "MultipartRequest",
        _assemble_request(
            "http://x",
            "post",
            None,
            {"tags": [b"one", b"two"]},
            {},
            multipart=True,
            multipart_data_headers={},
        ),
    )
    assert request.parts is not None
    assert len(request.parts) == 2
    assert [part.data for part in request.parts] == [b"one", b"two"]


def test_assemble_request_multipart_json_encodes_a_mapping_value() -> None:
    request: MultipartRequest = typing.cast(
        "MultipartRequest",
        _assemble_request(
            "http://x",
            "post",
            None,
            {"meta": {"a": 1}},
            {},
            multipart=True,
            multipart_data_headers={},
        ),
    )
    assert request.parts is not None
    part: Part = list(request.parts)[0]
    assert part.headers is not None
    assert part.headers["Content-type"] == "application/json"
    assert part.data == b'{"a": 1}'


# endregion

# region Retry decorator and content encoding


@pytest.mark.parametrize(
    ("code", "expected"),
    [
        (404, False),
        (401, False),
        (409, False),
        (410, False),
        (500, True),
        (503, True),
    ],
)
def test_default_retry_hook_by_status_code(code: int, expected: bool) -> None:
    error: HTTPError = HTTPError("http://x", code, "message", None, None)  # type: ignore[arg-type]
    assert default_retry_hook(error) is expected


def test_default_retry_hook_retries_non_http_errors() -> None:
    assert default_retry_hook(ValueError("not an http error")) is True


def test_retry_returns_on_success_without_retrying() -> None:
    calls: list[int] = []

    @retry(number_of_attempts=3, errors=ValueError)
    def succeeds() -> str:
        calls.append(1)
        return "ok"

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        assert succeeds() == "ok"
    assert len(calls) == 1


def test_retry_retries_warns_and_backs_off_until_success() -> None:
    """
    One assertion covers three behaviors of a single retry: the call is
    re-attempted until it succeeds, a `UserWarning` is emitted for the
    failed attempt, and the retry sleeps for `2 ** attempt_number`
    seconds beforehand -- checked together so the ~2 second real sleep
    is only paid once.
    """
    calls: list[int] = []

    @retry(number_of_attempts=2, errors=ValueError)
    def flaky() -> str:
        calls.append(1)
        if len(calls) < 2:
            message: str = "fail once"
            raise ValueError(message)
        return "ok"

    start: float = time.monotonic()
    with pytest.warns(UserWarning, match="Attempt # 1"):
        assert flaky() == "ok"
    elapsed: float = time.monotonic() - start
    assert len(calls) == 2
    assert elapsed >= 1.9


def test_retry_exhausts_attempts_and_reraises() -> None:
    calls: list[int] = []

    @retry(number_of_attempts=2, errors=ValueError, retry_hook=lambda e: True)
    def always_fails() -> None:
        calls.append(1)
        message: str = "always fails"
        raise ValueError(message)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        with pytest.raises(ValueError, match="always fails"):
            always_fails()
    assert len(calls) == 2


def test_retry_hook_returning_false_skips_retry() -> None:
    calls: list[int] = []

    @retry(number_of_attempts=5, errors=ValueError, retry_hook=lambda e: False)
    def never_retry() -> None:
        calls.append(1)
        message: str = "no retry"
        raise ValueError(message)

    with pytest.raises(ValueError, match="no retry"):
        never_retry()
    assert len(calls) == 1


def test_retry_default_number_of_attempts_does_nothing() -> None:
    calls: list[int] = []

    @retry(errors=ValueError)
    def always_fails() -> None:
        calls.append(1)
        message: str = "boom"
        raise ValueError(message)

    with pytest.raises(ValueError, match="boom"):
        always_fails()
    assert len(calls) == 1


def test_retry_logs_a_warning_when_a_logger_is_provided() -> None:
    logger: logging.Logger = logging.getLogger(
        "test-client-retry-and-encoding"
    )
    records: list[str] = []

    class RecordingHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            records.append(record.getMessage())

    handler: RecordingHandler = RecordingHandler()
    logger.addHandler(handler)
    logger.setLevel(logging.WARNING)
    try:
        calls: list[int] = []

        @retry(number_of_attempts=2, errors=ValueError, logger=logger)
        def flaky() -> str:
            calls.append(1)
            if len(calls) < 2:
                message: str = "fail"
                raise ValueError(message)
            return "ok"

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            assert flaky() == "ok"
        assert len(records) == 1
    finally:
        logger.removeHandler(handler)


@pytest.mark.parametrize("encoding", ["gzip", "deflate", "zstd", "br"])
def test_encode_and_decode_content_round_trip(encoding: str) -> None:
    data: bytes = b'{"hello": "world"}' * 50
    encoded: bytes = _encode_content(data, encoding)
    assert len(encoded) < len(data)
    assert _decode_content(encoded, encoding) == data


@pytest.mark.parametrize("encoding", ["dcb", "dcz"])
def test_encode_and_decode_content_brotli_aliases(encoding: str) -> None:
    data: bytes = b'{"hello": "world"}' * 50
    encoded: bytes = _encode_content(data, encoding)
    assert _decode_content(encoded, encoding) == data


def test_encode_content_is_a_no_op_for_empty_data() -> None:
    assert _encode_content(b"", "gzip") == b""


def test_decode_content_is_a_no_op_for_empty_data() -> None:
    assert _decode_content(b"", "gzip") == b""


def test_encode_and_decode_content_are_case_and_whitespace_insensitive() -> (
    None
):
    data: bytes = b'{"hello": "world"}' * 50
    encoded: bytes = _encode_content(data, " GZIP ")
    assert _decode_content(encoded, " GZIP ") == data


def test_encode_content_comma_branch_only_applies_the_first_encoding() -> None:
    """
    A comma-separated `content_encoding` is meant to apply each encoding
    in the order listed. `_encode_content`'s comma branch instead
    recursively *decodes* the still-plain data using the remaining
    tokens before applying the first one -- a genuine bug in the current
    source, documented here rather than corrected. It happens not to
    raise when the remaining token (`"identity"`) is unrecognized, since
    `_decode_content` silently returns unrecognized-encoding data
    unchanged; the practical effect is that only the first-listed
    encoding (`gzip`) is actually applied.
    """
    data: bytes = b'{"hello": "world"}' * 50
    encoded: bytes = _encode_content(data, "gzip,identity")
    assert gzip.decompress(encoded) == data


def test_decode_content_comma_branch_reverses_a_real_encoding_chain() -> None:
    """
    `_decode_content`'s comma branch is correct: for
    `Content-Encoding: gzip, deflate` (gzip applied first, then
    deflate), decoding must undo deflate first, then gzip -- which is
    exactly what the recursive call (decode the remaining tokens first,
    then apply the first token's decoder) does.
    """
    data: bytes = b'{"hello": "world"}' * 50
    double_encoded: bytes = zlib.compress(gzip.compress(data))
    assert _decode_content(double_encoded, "gzip,deflate") == data


# endregion

# region Pickling helpers and SSLContext


def test_make_thread_locks_pickleable_is_idempotent_and_pickles_a_lock() -> (
    None
):
    _make_thread_locks_pickleable()
    lock: threading.Lock = threading.Lock()
    unpickled: threading.Lock = pickle.loads(pickle.dumps(lock))
    assert type(unpickled) is type(lock)


def test_make_thread_locks_pickleable_pickles_an_rlock() -> None:
    rlock: threading.RLock = threading.RLock()
    unpickled: threading.RLock = pickle.loads(pickle.dumps(rlock))
    assert type(unpickled) is type(rlock)


def test_make_http_errors_pickleable_is_idempotent_and_pickles_an_error() -> (
    None
):
    _make_http_errors_pickleable()
    headers: Message[str, str] = Message()
    headers["X"] = "1"
    error: HTTPError = HTTPError("http://x", 404, "not found", headers, None)
    unpickled: HTTPError = pickle.loads(pickle.dumps(error))
    assert unpickled.code == 404
    assert unpickled.msg == "not found"


def test_make_loggers_pickleable_is_idempotent_and_pickles_a_logger() -> None:
    _make_loggers_pickleable()
    logger: Logger = getLogger("test-client-pickling")
    unpickled: Logger = pickle.loads(pickle.dumps(logger))
    assert unpickled.name == "test-client-pickling"
    assert unpickled is logger


def test_ssl_context_default_verifies_the_hostname() -> None:
    import ssl

    context: SSLContext = SSLContext()
    assert context.check_hostname is True
    assert context.verify_mode == ssl.CERT_REQUIRED


def test_ssl_context_can_disable_hostname_verification() -> None:
    import ssl

    context: SSLContext = SSLContext(check_hostname=False)
    assert context.check_hostname is False
    assert context.verify_mode == ssl.CERT_NONE


def test_ssl_context_pickles_as_a_fresh_instance() -> None:
    context: SSLContext = SSLContext(check_hostname=False)
    unpickled: SSLContext = pickle.loads(pickle.dumps(context))
    assert unpickled.check_hostname is False
    assert unpickled is not context


# endregion

# region Client construction, validation, and pickling


def test_init_rejects_an_invalid_api_key_in() -> None:
    with pytest.raises(ValueError, match="api_key_in"):
        Client(api_key_in="bogus")  # type: ignore[arg-type]


def test_init_rejects_invalid_oauth2_flows() -> None:
    with pytest.raises(ValueError, match="oauth2_flows"):
        Client(oauth2_flows=("bogus",))  # type: ignore[arg-type]


def test_init_translates_openapi_2x_flow_names() -> None:
    client: Client = Client(oauth2_flows=("accessCode", "application"))
    # `Client.oauth2_flows` is annotated (in the real source, with a
    # `# type: ignore`) as a single `Literal[...] | None`, but the
    # actual runtime value assigned by `__init__` is always a tuple.
    assert client.oauth2_flows == (  # type: ignore[comparison-overlap]
        "authorizationCode",
        "clientCredentials",
    )


@pytest.mark.parametrize(
    "url_kwarg",
    [
        "url",
        "oauth2_authorization_url",
        "oauth2_token_url",
        "oauth2_refresh_url",
    ],
)
def test_init_rejects_a_non_http_scheme_url(url_kwarg: str) -> None:
    with pytest.raises(ValueError, match="ftp://bad"):
        Client(**{url_kwarg: "ftp://bad"})  # type: ignore[arg-type]


def test_init_allows_a_relative_url() -> None:
    client: Client = Client(url="/relative")
    assert client.url == "/relative"


def test_init_default_headers() -> None:
    client: Client = Client()
    assert client.headers == {
        "Accept": "application/json",
        "Content-type": "application/json",
    }


def test_opener_is_lazily_built_and_cached() -> None:
    client: Client = Client()
    opener_first: OpenerDirector = client._opener
    opener_second: OpenerDirector = client._opener
    assert opener_first is opener_second


def test_getstate_excludes_the_private_opener() -> None:
    client: Client = Client(url="http://example.com", user="u", password="p")
    state: dict[str, object] = client.__getstate__()
    assert "__opener" not in state
    assert state["url"] == "http://example.com"
    assert state["user"] == "u"


def test_setstate_reconstructs_a_client_via_init_kwargs() -> None:
    client: Client = Client(url="http://example.com", user="u", password="p")
    state: dict[str, object] = client.__getstate__()
    new_client: Client = Client.__new__(Client)
    new_client.__setstate__(dict(state))
    assert new_client.url == "http://example.com"
    assert new_client.user == "u"
    assert new_client.password == "p"
    assert isinstance(new_client._cookie_jar, CookieJar)


def test_pickle_round_trip_preserves_configuration() -> None:
    client: Client = Client(
        url="http://example.com", api_key="key123", api_key_name="X-KEY"
    )
    unpickled: Client = pickle.loads(pickle.dumps(client))
    assert type(unpickled) is Client
    assert unpickled.url == "http://example.com"
    assert unpickled.api_key == "key123"
    assert unpickled.api_key_name == "X-KEY"


def test_resurrect_client_warns_and_reconstructs_from_minimal_args() -> None:
    """
    `_resurrect_client` is a deprecated `__reduce__`-era un-pickling path
    (superseded by `__getstate__`/`__setstate__`). It calls
    `cls(*init_parameters)` positionally after popping the trailing
    `cookie_jar`/`oauth2_authorization_expires` values, but `Client.
    __init__` only accepts `url` positionally (every other parameter is
    keyword-only) -- so this method only actually works for the minimal
    pickled-state shape of `(url_or_nothing, cookie_jar, expires)`. It
    is exercised here with that minimal shape, matching what old
    pickled data (from before `__getstate__`/`__setstate__` existed)
    would have looked like for a client with only a `url` set.
    """
    with pytest.warns(DeprecationWarning, match="out of date"):
        client: Client = Client._resurrect_client(
            "http://example.com", CookieJar(), 0
        )
    assert client.url == "http://example.com"


def test_resurrect_client_with_no_positional_args() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        client: Client = Client._resurrect_client(CookieJar(), 0)
    assert client.url is None


# endregion

# region Client authentication


def test_authenticate_request_adds_basic_authentication() -> None:
    client: Client = Client(user="alice", password="secret")
    request: Request = Request("http://example.com/foo")
    client._authenticate_request(request)
    assert request.get_header("Authorization") == "Basic YWxpY2U6c2VjcmV0"


def test_authenticate_request_adds_bearer_token() -> None:
    client: Client = Client(bearer_token="tok123")
    request: Request = Request("http://example.com/foo")
    client._authenticate_request(request)
    assert request.get_header("Authorization") == "Bearer tok123"


def test_authenticate_request_prefers_bearer_over_basic_when_both_set() -> (
    None
):
    """
    `_authenticate_request` applies Basic auth first, then Bearer --
    since both call `add_header("Authorization", ...)`, the second call
    (Bearer) wins for the real, final header value if both `user`/
    `password` and `bearer_token` are configured together.
    """
    client: Client = Client(
        user="alice", password="secret", bearer_token="tok123"
    )
    request: Request = Request("http://example.com/foo")
    client._authenticate_request(request)
    assert request.get_header("Authorization") == "Bearer tok123"


def test_api_key_authenticate_request_in_header() -> None:
    client: Client = Client(
        api_key="key123", api_key_name="X-API-KEY", api_key_in="header"
    )
    request: Request = Request("http://example.com/foo")
    client._authenticate_request(request)
    assert request.get_header("X-api-key") == "key123"


def test_api_key_authenticate_request_in_query_appends_to_existing() -> None:
    client: Client = Client(
        api_key="key123", api_key_name="apikey", api_key_in="query"
    )
    request: Request = Request("http://example.com/foo?a=1")
    client._authenticate_request(request)
    assert request.full_url == "http://example.com/foo?a=1&apikey=key123"


def test_api_key_authenticate_request_in_query_without_existing_query() -> (
    None
):
    client: Client = Client(
        api_key="key123", api_key_name="apikey", api_key_in="query"
    )
    request: Request = Request("http://example.com/foo")
    client._authenticate_request(request)
    assert request.full_url == "http://example.com/foo?apikey=key123"


def test_api_key_authenticate_request_in_cookie_without_existing_cookie() -> (
    None
):
    client: Client = Client(
        api_key="key123", api_key_name="session", api_key_in="cookie"
    )
    request: Request = Request("http://example.com/foo")
    client._authenticate_request(request)
    assert request.get_header("Cookie") == "session=key123"


def test_api_key_authenticate_request_in_cookie_appends_to_existing() -> None:
    client: Client = Client(
        api_key="key123", api_key_name="session", api_key_in="cookie"
    )
    request: Request = Request(
        "http://example.com/foo", headers={"Cookie": "existing=1"}
    )
    client._authenticate_request(request)
    assert request.get_header("Cookie") == "existing=1; session=key123"


def test_api_key_authenticate_request_in_query_requires_a_key() -> None:
    client: Client = Client(api_key_in="query")
    with pytest.raises(RuntimeError, match="No API key"):
        client._api_key_authenticate_request(Request("http://example.com/foo"))


def test_api_key_authenticate_request_in_header_requires_a_key() -> None:
    client: Client = Client(api_key_in="header")
    with pytest.raises(RuntimeError, match="No API key"):
        client._api_key_authenticate_request(Request("http://example.com/foo"))


def test_api_key_authenticate_request_rejects_an_invalid_api_key_in() -> None:
    """
    `Client.__init__` validates `api_key_in` up front, but
    `_api_key_authenticate_request` re-validates it independently (its
    `else` branch double-checks `self.api_key_in == "header"`) --
    reachable by mutating the attribute directly after construction,
    bypassing `__init__`'s guard.
    """
    client: Client = Client(api_key="x")
    client.api_key_in = "bogus"  # type: ignore[assignment]
    with pytest.raises(ValueError, match="bogus"):
        client._api_key_authenticate_request(Request("http://example.com/foo"))


def test_oauth2_authenticate_request_warns_for_unconfigured_flows() -> None:
    client: Client = Client(
        oauth2_flows=(
            "implicit",
            "password",
            "clientCredentials",
            "authorizationCode",
        )
    )
    request: Request = Request("http://example.com/foo")
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        client._oauth2_authenticate_request(request)
    messages: list[str] = [str(warning.message) for warning in caught]
    assert len(messages) == 4
    assert any("implicit" in message for message in messages)
    assert any(
        '"password" OAuth2 flow requires' in message for message in messages
    )
    assert any(
        '"clientCredentials" OAuth2 flow requires' in message
        for message in messages
    )
    assert any("authorizationCode" in message for message in messages)
    assert request.get_header("Authorization") is None


def test_oauth2_authenticate_request_does_nothing_when_unconfigured() -> None:
    client: Client = Client()
    request: Request = Request("http://example.com/foo")
    client._oauth2_authenticate_request(request)
    assert request.get_header("Authorization") is None


# endregion

# region Client.request's real request/response cycle


def test_request_basic_get_returns_a_readable_response() -> None:
    with http_test_server(
        responses={("GET", "/foo"): Response(status=200, body=b'{"ok": true}')}
    ) as server:
        client: Client = Client(url=server.url)
        with client.request("/foo", "GET") as response:
            data: bytes | str = response.read()
        assert data == b'{"ok": true}'
        assert server.requests[0].method == "GET"
        assert server.requests[0].path == "/foo"


def test_request_data_kwarg_treated_as_json_for_backward_compat() -> None:
    """
    For backward compatibility, passing a `str`/`bytes`/`sob.abc.Model`
    (or `None`) as `data` is silently treated as the `json` argument
    instead (the pre-`json`-argument calling convention).
    """
    with http_test_server(
        responses={("POST", "/foo"): Response(status=200, body=b"{}")}
    ) as server:
        client: Client = Client(url=server.url)
        with client.request(
            "/foo",
            "POST",
            data='{"a": 1}',  # type: ignore[arg-type]
        ) as response:
            response.read()
        assert server.requests[0].body == b'{"a": 1}'


def test_request_accepts_an_explicit_none_data_argument() -> None:
    with http_test_server(
        responses={("GET", "/foo"): Response(status=200, body=b"{}")}
    ) as server:
        client: Client = Client(url=server.url)
        with client.request("/foo", "GET", data=None) as response:  # type: ignore[arg-type]
            response.read()
        assert server.requests[0].body == b""


def test_request_accepts_an_explicit_per_request_timeout() -> None:
    with http_test_server(
        responses={("GET", "/foo"): Response(status=200, body=b"{}")}
    ) as server:
        client: Client = Client(url=server.url)
        with client.request("/foo", "GET", timeout=5) as response:
            response.read()
        assert server.requests[0].path == "/foo"


def test_request_callback_adds_curl_flags_for_compression_and_no_verify() -> (
    None
):
    with http_test_server(
        responses={("POST", "/foo"): Response(status=200, body=b"{}")}
    ) as server:
        client: Client = Client(
            url=server.url, verify_ssl_certificate=False, echo=True
        )
        buffer: io.StringIO = io.StringIO()
        with (
            contextlib.redirect_stdout(buffer),
            client.request(
                "/foo",
                "POST",
                json='{"a": 1}',
                headers={"Content-encoding": "gzip"},
            ) as response,
        ):
            response.read()
        output: str = buffer.getvalue()
        assert "--compressed" in output
        assert "-k" in output


def test_request_builds_a_query_string_from_a_dict_and_drops_none() -> None:
    with http_test_server(
        responses={("GET", "/foo"): Response(status=200, body=b"{}")}
    ) as server:
        client: Client = Client(url=server.url)
        with client.request(
            "/foo", "GET", query={"a": 1, "b": None}
        ) as response:
            response.read()
        assert server.requests[0].query == "a=1"


def test_request_accepts_a_pre_built_query_string() -> None:
    with http_test_server(
        responses={("GET", "/foo"): Response(status=200, body=b"{}")}
    ) as server:
        client: Client = Client(url=server.url)
        with client.request("/foo", "GET", query="x=1&y=2") as response:
            response.read()
        assert server.requests[0].query == "x=1&y=2"


def test_request_sends_a_json_body() -> None:
    with http_test_server(
        responses={("POST", "/foo"): Response(status=200, body=b"{}")}
    ) as server:
        client: Client = Client(url=server.url)
        with client.request("/foo", "POST", json='{"a": 1}') as response:
            response.read()
        assert server.requests[0].body == b'{"a": 1}'


def test_request_merges_custom_headers_with_defaults() -> None:
    with http_test_server(
        responses={("GET", "/foo"): Response(status=200, body=b"{}")}
    ) as server:
        client: Client = Client(url=server.url)
        with client.request(
            "/foo", "GET", headers={"X-Custom": "abc"}
        ) as response:
            response.read()
        recorded_headers: dict[str, str] = server.requests[0].headers
        assert recorded_headers["X-Custom"] == "abc"
        assert recorded_headers["Accept"] == "application/json"


def test_request_with_an_absolute_url_ignores_the_client_base_url() -> None:
    with http_test_server(
        responses={("GET", "/bar"): Response(status=200, body=b"{}")}
    ) as server:
        client: Client = Client(url="http://unused.invalid")
        with client.request(server.url + "/bar", "GET") as response:
            response.read()
        assert server.requests[0].path == "/bar"


def test_request_rejects_a_relative_path_missing_a_leading_slash() -> None:
    client: Client = Client(url="http://example.com")
    with pytest.raises(ValueError, match="relative"):
        client.request("relative", "GET")


def test_request_raises_http_error_and_appends_response_body_to_it() -> None:
    with http_test_server(
        responses={
            ("GET", "/bad"): Response(status=500, body=b'{"error": "boom"}')
        }
    ) as server:
        client: Client = Client(url=server.url)
        with pytest.raises(HTTPError) as excinfo:
            client.request("/bad", "GET")
        assert excinfo.value.code == 500
        assert "boom" in str(excinfo.value)


def test_request_retries_a_failing_request_until_it_succeeds() -> None:
    with http_test_server(
        sequences={
            ("GET", "/flaky"): [
                Response(status=500, body=b"err"),
                Response(status=200, body=b'{"ok": true}'),
            ]
        }
    ) as server:
        client: Client = Client(
            url=server.url,
            retry_number_of_attempts=2,
            retry_hook=lambda error: True,
        )
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            with client.request("/flaky", "GET") as response:
                data: bytes | str = response.read()
        assert data == b'{"ok": true}'
        assert len(server.requests) == 2


def test_request_does_not_retry_by_default() -> None:
    with http_test_server(
        sequences={
            ("GET", "/flaky"): [
                Response(status=500, body=b"err"),
                Response(status=200, body=b'{"ok": true}'),
            ]
        }
    ) as server:
        client: Client = Client(url=server.url)
        with pytest.raises(HTTPError):
            client.request("/flaky", "GET")
        assert len(server.requests) == 1


def test_request_echo_prints_the_curl_representation() -> None:
    with http_test_server(
        responses={("GET", "/foo"): Response(status=200, body=b'{"ok": true}')}
    ) as server:
        client: Client = Client(url=server.url, echo=True)
        buffer: io.StringIO = io.StringIO()
        with (
            contextlib.redirect_stdout(buffer),
            client.request("/foo", "GET") as response,
        ):
            response.read()
        output: str = buffer.getvalue()
        assert "curl" in output
        assert "200" in output


def test_request_multipart_crashes_missing_content_encoding_header() -> None:
    """
    Documents a real, verified, currently-unfixed bug: every multipart
    `Client.request()` call crashes with `KeyError: 'Content-encoding'`.
    `_request_callback` (client.py:1514) calls `request.headers.get(
    "Content-encoding")` expecting normal `dict.get` semantics (`None`
    when absent), but a `MultipartRequest`'s `.headers` is a custom
    `Headers` object (`_multipart_request.py`) whose `.get()` defaults
    to `sob.UNDEFINED` and *re-raises* `KeyError` when no explicit
    `default` is passed and the key is missing. Since ordinary
    multipart requests don't set a `Content-encoding` header, this
    fires on essentially every real multipart upload. Not fixed here
    (out of this test-only initiative's scope) -- flagged to the user
    directly as well as documented here.
    """
    with http_test_server(
        responses={("POST", "/foo"): Response(status=200, body=b"{}")}
    ) as server:
        client: Client = Client(url=server.url)
        with pytest.raises(KeyError, match="Content-encoding"):
            client.request(
                "/foo", "POST", data={"field": b"x"}, multipart=True
            )


def test_request_rejects_a_non_readable_response() -> None:
    """
    `Client._request`'s final `if not isinstance(response, sob.abc.
    Readable): raise TypeError(response)` (client.py:1919) is real,
    reachable code -- not dead, despite an earlier draft of this plan
    claiming otherwise (corrected during final review). `_assemble_
    request`'s URL-scheme guard only applies to its non-multipart
    branch, so a `multipart=True` request with a `file://` URL bypasses
    it entirely and reaches a real `FileHandler`, which returns a real
    `urllib.response.addinfourl` -- an object `sob.abc.Readable` does
    *not* recognize (its structural check requires a class-level `read`
    method; `addinfourl` only proxies one through `__getattr__`). A
    `Content-encoding` header is set explicitly here to route around
    the separate multipart `KeyError` bug documented above and actually
    reach this line.
    """
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(b"hello")
        temp_path: Path = Path(temp_file.name)
    try:
        client: Client = Client(url="http://example.com")
        with pytest.raises(TypeError):
            client.request(
                temp_path.as_uri(),
                "POST",
                data={"field": b"x"},
                multipart=True,
                headers={"Content-encoding": "identity"},
            )
    finally:
        # `urllib`'s `FileHandler.open_local_file` opens the temp file
        # and never gets a chance to close it (the response is
        # discarded as soon as the expected `TypeError` is raised) --
        # on Windows, an open file cannot be unlinked, unlike POSIX,
        # where an unlinked-but-open file is simply removed once
        # closed. Best-effort cleanup only; a leftover temp file is
        # harmless.
        with contextlib.suppress(PermissionError):
            temp_path.unlink()


def test_request_logs_at_info_level_on_success() -> None:
    logger: logging.Logger = logging.getLogger(
        "test-client-request-runtime-success"
    )
    records: list[str] = []

    class RecordingHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            records.append(record.levelname)

    handler: RecordingHandler = RecordingHandler()
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    try:
        with http_test_server(
            responses={
                ("GET", "/foo"): Response(status=200, body=b'{"ok": true}')
            }
        ) as server:
            client: Client = Client(url=server.url, logger=logger)
            with client.request("/foo", "GET") as response:
                response.read()
        assert records == ["INFO", "INFO"]
    finally:
        logger.removeHandler(handler)


def test_get_request_response_callback_error_path_logs_and_appends_text() -> (
    None
):
    """
    `_get_request_response_callback(error=...)` -- the ERROR-level
    logging and exception-text-appending branch -- is real, callable
    code, but `Client._request` never actually invokes it with a real
    `error` argument anywhere in the class (its one call site inside the
    `except HTTPError` block only calls `sob.errors.append_exception_text`
    directly, not through this callback). It's exercised here as a
    direct unit test of the method itself, not through `Client.request`.
    """
    logger: logging.Logger = logging.getLogger(
        "test-client-request-runtime-error-path"
    )
    records: list[str] = []

    class RecordingHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            records.append(record.levelname)

    handler: RecordingHandler = RecordingHandler()
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    try:
        client: Client = Client(logger=logger, echo=True)
        error: HTTPError = HTTPError("http://x", 500, "boom", None, None)  # type: ignore[arg-type]
        callback: typing.Callable[[str], None] = (
            client._get_request_response_callback(error=error)
        )
        buffer: io.StringIO = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            callback("some appended text")
        assert records == ["ERROR"]
        # echo is suppressed when an error is present (only the
        # ERROR-level log fires, nothing is printed to stdout)
        assert buffer.getvalue() == ""
        assert "some appended text" in str(error)
    finally:
        logger.removeHandler(handler)


# endregion

# region Client OAuth2 flows and OIDC discovery


def test_oauth2_password_flow_authenticates_and_caches_the_token() -> None:
    with http_test_server(
        responses={
            ("POST", "/token"): Response(
                status=200,
                body=json_module.dumps(
                    {
                        "token_type": "Bearer",
                        "access_token": "tok-pw",
                        "expires_in": 3600,
                    }
                ).encode(),
            ),
            ("GET", "/protected"): Response(status=200, body=b'{"ok": true}'),
        }
    ) as server:
        client: Client = Client(
            url=server.url,
            oauth2_client_id="cid",
            oauth2_username="user1",
            oauth2_password="pw1",
            oauth2_token_url=server.url + "/token",
        )
        with client.request("/protected", "GET") as response:
            response.read()
        assert (
            server.requests[-1].headers.get("Authorization") == "Bearer tok-pw"
        )
        token_requests_before: int = len(
            [
                request
                for request in server.requests
                if request.path == "/token"
            ]
        )
        with client.request("/protected", "GET") as response:
            response.read()
        token_requests_after: int = len(
            [
                request
                for request in server.requests
                if request.path == "/token"
            ]
        )
        # A second request reuses the cached token: no second POST /token.
        assert token_requests_after == token_requests_before


def test_oauth2_password_flow_requires_a_username() -> None:
    client: Client = Client(
        oauth2_token_url="http://example.com/token",
        oauth2_password="pw1",
    )
    with pytest.raises(RuntimeError, match="username"):
        client._request_oauth2_password_authorization()


def test_oauth2_password_flow_requires_a_password() -> None:
    client: Client = Client(
        oauth2_token_url="http://example.com/token",
        oauth2_username="user1",
    )
    with pytest.raises(RuntimeError, match="password"):
        client._request_oauth2_password_authorization()


def test_oauth2_password_flow_requires_a_token_url() -> None:
    client: Client = Client(
        open_id_connect_url="",
        oauth2_username="user1",
        oauth2_password="pw1",
    )
    with pytest.raises(RuntimeError, match="token URL"):
        client._request_oauth2_password_authorization()


def test_oauth2_password_flow_includes_the_configured_scope() -> None:
    with http_test_server(
        responses={
            ("POST", "/token"): Response(
                status=200,
                body=json_module.dumps(
                    {
                        "token_type": "Bearer",
                        "access_token": "t",
                        "expires_in": 3600,
                    }
                ).encode(),
            ),
        }
    ) as server:
        client: Client = Client(
            oauth2_client_id="cid",
            oauth2_username="u",
            oauth2_password="p",
            oauth2_token_url=server.url + "/token",
            oauth2_scope="read write",
        )
        with client._request_oauth2_password_authorization() as response:
            response.read()
        assert b"scope=read%20write" in server.requests[0].body


def test_oauth2_password_flow_follows_a_location_header_on_http_error() -> (
    None
):
    """
    On an `HTTPError`, `_request_oauth2_password_authorization` checks
    the error response's `Location` header and, if it differs from the
    current `oauth2_token_url`, updates `oauth2_token_url` and retries
    against the new URL. This uses the raw header value as the next
    request's full URL directly (no relative-URL resolution), so a real
    exercise of this branch needs an *absolute* URL in `Location`.
    """
    with http_test_server(responses={}) as server:
        server.responses[("POST", "/token")] = Response(
            status=401, headers={"Location": server.url + "/token2"}
        )
        server.responses[("POST", "/token2")] = Response(
            status=200,
            body=json_module.dumps(
                {
                    "token_type": "Bearer",
                    "access_token": "moved-token",
                    "expires_in": 3600,
                }
            ).encode(),
        )
        client: Client = Client(
            oauth2_client_id="cid",
            oauth2_username="u",
            oauth2_password="p",
            oauth2_token_url=server.url + "/token",
        )
        with client._request_oauth2_password_authorization() as response:
            data: bytes | str = response.read()
        assert b"moved-token" in (
            data if isinstance(data, bytes) else data.encode()
        )
        assert client.oauth2_token_url == server.url + "/token2"


def test_oauth2_password_flow_reraises_an_http_error_without_a_redirect() -> (
    None
):
    """
    When the token endpoint's error response has no `Location` header
    (or one equal to the current `oauth2_token_url`), there is nothing
    to retry against, and the original `HTTPError` is re-raised as-is.
    """
    with http_test_server(
        responses={("POST", "/token"): Response(status=401, body=b"nope")}
    ) as server:
        client: Client = Client(
            oauth2_client_id="cid",
            oauth2_username="u",
            oauth2_password="p",
            oauth2_token_url=server.url + "/token",
        )
        with pytest.raises(HTTPError) as excinfo:
            client._request_oauth2_password_authorization()
        assert excinfo.value.code == 401


def test_oauth2_client_credentials_flow_with_explicit_timeout() -> None:
    """
    `_request_oauth2_client_credentials_authorization` passes
    `timeout=self.timeout` to the opener unconditionally -- unlike
    `_request_oauth2_password_authorization`, it has no fallback for
    `self.timeout == 0` (the `Client` default). A `timeout=0` value
    means "non-blocking socket" to the stdlib socket layer, not "no
    timeout" -- so this flow only works with a real, non-zero `timeout`.
    See `test_oauth2_client_credentials_flow_with_default_timeout_fails`
    below for the real, current, broken default-timeout behavior.
    """
    with http_test_server(
        responses={
            ("POST", "/token"): Response(
                status=200,
                body=json_module.dumps(
                    {
                        "token_type": "Bearer",
                        "access_token": "tok-cc",
                        "expires_in": 3600,
                    }
                ).encode(),
            ),
            ("GET", "/protected"): Response(status=200, body=b'{"ok": true}'),
        }
    ) as server:
        client: Client = Client(
            url=server.url,
            oauth2_client_id="cid",
            oauth2_client_secret="csecret",
            oauth2_token_url=server.url + "/token",
            timeout=30,
        )
        with client.request("/protected", "GET") as response:
            response.read()
        assert (
            server.requests[-1].headers.get("Authorization") == "Bearer tok-cc"
        )
        assert (
            "grant_type=client_credentials" in server.requests[0].body.decode()
        )


def test_oauth2_client_credentials_flow_with_default_timeout_fails() -> None:
    """
    Documents a real, verified bug: with the `Client` default
    `timeout=0`, `_request_oauth2_client_credentials_authorization`
    passes `timeout=0` straight to `OpenerDirector.open`, which
    ultimately reaches `socket.create_connection` with a `0` timeout --
    Python's socket API treats `settimeout(0)` as "set the socket to
    non-blocking mode", not "no timeout", so the connect step raises
    immediately rather than actually connecting. Confirmed against a
    real local server (not a network flake): the exact same client
    configuration succeeds when constructed with a non-zero `timeout`
    (see the test above). This is real, current, unfixed behavior --
    documented here, not corrected.
    """
    with http_test_server(
        responses={
            ("POST", "/token"): Response(status=200, body=b"{}"),
        }
    ) as server:
        client: Client = Client(
            url=server.url,
            oauth2_client_id="cid",
            oauth2_client_secret="csecret",
            oauth2_token_url=server.url + "/token",
        )
        with pytest.raises(OSError):
            client._request_oauth2_client_credentials_authorization()


def test_oauth2_client_credentials_flow_requires_a_client_id() -> None:
    client: Client = Client(
        oauth2_token_url="http://example.com/token",
        oauth2_client_secret="csecret",
    )
    with pytest.raises(RuntimeError, match="client ID"):
        client._request_oauth2_client_credentials_authorization()


def test_oauth2_client_credentials_flow_requires_a_client_secret() -> None:
    client: Client = Client(
        oauth2_token_url="http://example.com/token",
        oauth2_client_id="cid",
    )
    with pytest.raises(RuntimeError, match="client secret"):
        client._request_oauth2_client_credentials_authorization()


def test_oauth2_client_credentials_flow_requires_a_token_url() -> None:
    client: Client = Client(
        open_id_connect_url="",
        oauth2_client_id="cid",
        oauth2_client_secret="s",
    )
    with pytest.raises(RuntimeError, match="token URL"):
        client._request_oauth2_client_credentials_authorization()


def test_oauth2_client_credentials_flow_includes_the_configured_scope() -> (
    None
):
    with http_test_server(
        responses={
            ("POST", "/token"): Response(
                status=200,
                body=json_module.dumps(
                    {
                        "token_type": "Bearer",
                        "access_token": "t",
                        "expires_in": 3600,
                    }
                ).encode(),
            ),
        }
    ) as server:
        client: Client = Client(
            oauth2_client_id="cid",
            oauth2_client_secret="s",
            oauth2_token_url=server.url + "/token",
            oauth2_scope="read",
            timeout=30,
        )
        with client._request_oauth2_client_credentials_authorization() as (
            response
        ):
            response.read()
        assert b"scope=read" in server.requests[0].body


def test_oauth2_client_credentials_flow_follows_a_location_header() -> None:
    with http_test_server(responses={}) as server:
        server.responses[("POST", "/token")] = Response(
            status=401, headers={"Location": server.url + "/token2"}
        )
        server.responses[("POST", "/token2")] = Response(
            status=200,
            body=json_module.dumps(
                {
                    "token_type": "Bearer",
                    "access_token": "moved-token-cc",
                    "expires_in": 3600,
                }
            ).encode(),
        )
        client: Client = Client(
            oauth2_client_id="cid",
            oauth2_client_secret="s",
            oauth2_token_url=server.url + "/token",
            timeout=30,
        )
        with client._request_oauth2_client_credentials_authorization() as (
            response
        ):
            data: bytes | str = response.read()
        assert b"moved-token-cc" in (
            data if isinstance(data, bytes) else data.encode()
        )
        assert client.oauth2_token_url == server.url + "/token2"


def test_oauth2_client_credentials_flow_reraises_without_a_redirect() -> None:
    with http_test_server(
        responses={("POST", "/token"): Response(status=401, body=b"nope")}
    ) as server:
        client: Client = Client(
            oauth2_client_id="cid",
            oauth2_client_secret="s",
            oauth2_token_url=server.url + "/token",
            timeout=30,
        )
        with pytest.raises(HTTPError) as excinfo:
            client._request_oauth2_client_credentials_authorization()
        assert excinfo.value.code == 401


def test_get_oauth2_token_url_returns_the_explicit_url_unchanged() -> None:
    client: Client = Client(oauth2_token_url="http://example.com/token")
    assert client._get_oauth2_token_url() == "http://example.com/token"


def test_get_oauth2_token_url_discovers_via_oidc_with_timeout() -> None:
    """
    Like the client-credentials flow, OIDC discovery
    (`urlopen(url, timeout=self.timeout)`) passes `self.timeout`
    straight through with no fallback for `0` -- exercised here with an
    explicit non-zero `timeout` to get real, working coverage of the
    discovery logic itself (parsing `token_endpoint` out of the
    real HTTP response and caching it onto `self.oauth2_token_url`).
    """
    with http_test_server(
        responses={
            ("GET", "/.well-known/openid-configuration"): Response(
                status=200,
                body=json_module.dumps(
                    {"token_endpoint": "http://example.com/discovered"}
                ).encode(),
            ),
        }
    ) as server:
        client: Client = Client(url=server.url, timeout=30)
        token_url: str | None = client._get_oauth2_token_url()
        assert token_url == "http://example.com/discovered"
        # Cached onto the client -- a second call does not re-fetch.
        assert len(server.requests) == 1
        client._get_oauth2_token_url()
        assert len(server.requests) == 1


def test_get_oauth2_token_url_with_default_timeout_fails() -> None:
    """
    Documents the same real, verified `timeout=0` bug as
    `test_oauth2_client_credentials_flow_with_default_timeout_fails`,
    for OIDC discovery's own real network call.
    """
    with http_test_server(
        responses={
            ("GET", "/.well-known/openid-configuration"): Response(
                status=200, body=b"{}"
            ),
        }
    ) as server:
        client: Client = Client(url=server.url)
        with pytest.raises(OSError):
            client._get_oauth2_token_url()


# endregion

# region ClientModule: naming/import helper functions


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


# endregion

# region ClientModule: argument-style code generation


@pytest.fixture
def parameter_styles_client(
    generated_client_package: Callable[
        [OpenAPI], tuple[ModuleType, ModuleType]
    ],
) -> ModuleType:
    with open("tests/input-data/parameter-styles.json") as f:
        open_api: OpenAPI = OpenAPI(f)
    _model_module, client_module = generated_client_package(open_api)
    return client_module


def test_path_simple_style(parameter_styles_client: ModuleType) -> None:
    with http_test_server(
        responses={("GET", "/path/simple/1,2,3"): Response(body=b"{}")}
    ) as server:
        client = parameter_styles_client.Client(url=server.url)
        client.get_path_simple_id(id_=[1, 2, 3])
        assert server.requests[0].path == "/path/simple/1,2,3"


def test_path_label_style(parameter_styles_client: ModuleType) -> None:
    with http_test_server(
        responses={("GET", "/path/label/.1.2.3"): Response(body=b"{}")}
    ) as server:
        client = parameter_styles_client.Client(url=server.url)
        client.get_path_label_id(id_=[1, 2, 3])
        assert server.requests[0].path == "/path/label/.1.2.3"


def test_path_matrix_style_raises_key_error(
    parameter_styles_client: ModuleType,
) -> None:
    """
    Documents a real, verified, currently-unfixed codegen bug: every
    generated method for a `matrix`-style path parameter crashes with
    `KeyError: 'id'`. `_represent_dictionary_parameter` (client.py)
    prepends the matrix delimiter to the *dictionary key* used for
    string formatting (`";id"`, since `_format_matrix_argument_value`'s
    own output already includes the full `;id=value` fragment), but the
    generated path template's `str.format(**{...})` placeholder is
    still the bare `{id}` from the OpenAPI path -- `"{id}".format(
    **{";id": ...})` cannot find an `"id"` key in the kwargs dict it was
    given (only `";id"` is present) and raises `KeyError`. This means
    matrix-style path parameters are completely unusable in any
    generated client. Not fixed here (out of this test-only
    initiative's scope) -- flagged to the user directly as well as
    documented here.
    """
    with http_test_server(responses={}) as server:
        client = parameter_styles_client.Client(url=server.url)
        with pytest.raises(KeyError, match="id"):
            client.get_path_matrix_id(id_=[1, 2, 3])


def test_query_form_style(parameter_styles_client: ModuleType) -> None:
    with http_test_server(
        responses={("GET", "/query/form"): Response(body=b"{}")}
    ) as server:
        client = parameter_styles_client.Client(url=server.url)
        client.get_query_form(ids=[1, 2, 3])
        assert server.requests[0].query == "ids=1,2,3"


def test_query_space_delimited_style(
    parameter_styles_client: ModuleType,
) -> None:
    with http_test_server(
        responses={("GET", "/query/space-delimited"): Response(body=b"{}")}
    ) as server:
        client = parameter_styles_client.Client(url=server.url)
        client.get_query_space_delimited(ids=[1, 2, 3])
        assert server.requests[0].query == "ids=1%202%203"


def test_query_pipe_delimited_style(
    parameter_styles_client: ModuleType,
) -> None:
    with http_test_server(
        responses={("GET", "/query/pipe-delimited"): Response(body=b"{}")}
    ) as server:
        client = parameter_styles_client.Client(url=server.url)
        client.get_query_pipe_delimited(ids=[1, 2, 3])
        assert server.requests[0].query == "ids=1|2|3"


def test_query_deep_object_style(parameter_styles_client: ModuleType) -> None:
    with http_test_server(
        responses={("GET", "/query/deep-object"): Response(body=b"{}")}
    ) as server:
        client = parameter_styles_client.Client(url=server.url)
        client.get_query_deep_object(filter_={"a": "1", "b": "2"})
        assert server.requests[0].query == "filter[a]=1&filter[b]=2"


def test_header_simple_style(parameter_styles_client: ModuleType) -> None:
    with http_test_server(
        responses={("GET", "/header/simple"): Response(body=b"{}")}
    ) as server:
        client = parameter_styles_client.Client(url=server.url)
        client.get_header_simple(x_ids=[1, 2])
        assert server.requests[0].headers.get("X-Ids") == "1,2"


def test_cookie_form_style(parameter_styles_client: ModuleType) -> None:
    with http_test_server(
        responses={("GET", "/cookie/form"): Response(body=b"{}")}
    ) as server:
        client = parameter_styles_client.Client(url=server.url)
        client.get_cookie_form(ids=[1, 2])
        assert server.requests[0].headers.get("Cookie") == "ids=1,2"


# endregion

# region ClientModule: security-scheme code generation


@pytest.fixture
def security_schemes_client(
    generated_client_package: Callable[
        [OpenAPI], tuple[ModuleType, ModuleType]
    ],
) -> ModuleType:
    with open("tests/input-data/security-schemes.json") as f:
        open_api: OpenAPI = OpenAPI(f)
    _model_module, client_module = generated_client_package(open_api)
    return client_module


def test_init_bakes_in_the_first_api_key_schemes_location_and_name(
    security_schemes_client: ModuleType,
) -> None:
    """
    The OpenAPI document declares three `apiKey` security schemes
    (header/query/cookie) across different operations, but a generated
    `Client` has one shared `api_key_in`/`api_key_name` default pair --
    codegen picks the first `apiKey` scheme it encounters. Other
    locations remain reachable by passing `api_key_in`/`api_key_name`
    explicitly when constructing the client (see the query/cookie tests
    below), which isn't a bug -- a single client instance can only default
    to one location.
    """
    signature: inspect.Signature = inspect.signature(
        security_schemes_client.Client.__init__
    )
    assert signature.parameters["api_key_in"].default == "header"
    assert signature.parameters["api_key_name"].default == "X-Api-Key"


def test_init_bakes_in_oauth2_and_oidc_urls_from_the_security_schemes(
    security_schemes_client: ModuleType,
) -> None:
    signature: inspect.Signature = inspect.signature(
        security_schemes_client.Client.__init__
    )
    assert (
        signature.parameters["oauth2_token_url"].default
        == "https://example.com/oauth2/token"
    )
    assert (
        signature.parameters["oauth2_authorization_url"].default
        == "https://example.com/oauth2/authorize"
    )
    assert (
        signature.parameters["open_id_connect_url"].default
        == "https://example.com/.well-known/openid-configuration"
    )


def test_default_oauth2_flows_value_is_invalid(
    security_schemes_client: ModuleType,
) -> None:
    """
    Documents a real, verified, currently-unfixed codegen bug: a
    generated `Client` for an OpenAPI document with named OAuth2 flows
    cannot be instantiated with its own defaults. `_iter_oauth2_flows`
    (client.py) reads flow-type names via `sob.utilities.
    iter_properties_values(security_scheme.flows)`, which yields the
    Python-side (snake_case) *property* names of the generated
    `OAuthFlows` model -- e.g. `"authorization_code"` -- rather than the
    OpenAPI spec's own camelCase flow-type identifiers (`"authorization
    Code"`) that `Client.__init__`'s own validation (and its `Literal`
    parameter type) require. The baked-in default `oauth2_flows` tuple
    therefore fails that same validation immediately on construction,
    for *any* generated client whose OpenAPI document has a
    multi-word-named OAuth2 flow (`authorizationCode`/
    `clientCredentials` -- i.e. most real-world OAuth2 specs). The
    workaround (used by every other test in this file) is passing an
    explicit, valid `oauth2_flows` override. Not fixed here (out of
    this test-only initiative's scope) -- flagged to the user directly
    as well as documented here.
    """
    with pytest.raises(ValueError, match="oauth2_flows"):
        security_schemes_client.Client(url="http://example.com")


def test_api_key_header_authentication(
    security_schemes_client: ModuleType,
) -> None:
    with http_test_server(
        responses={
            ("GET", "/protected/api-key-header"): Response(
                body=b'{"name": "x"}'
            )
        }
    ) as server:
        client = security_schemes_client.Client(
            url=server.url, api_key="secret123", oauth2_flows=()
        )
        client.get_protected_api_key_header()
        assert server.requests[0].headers.get("X-Api-Key") == "secret123"


def test_api_key_query_authentication_with_an_explicit_location(
    security_schemes_client: ModuleType,
) -> None:
    with http_test_server(
        responses={
            ("GET", "/protected/api-key-query"): Response(
                body=b'{"name": "x"}'
            )
        }
    ) as server:
        client = security_schemes_client.Client(
            url=server.url,
            api_key="qkey",
            api_key_in="query",
            api_key_name="api_key",
            oauth2_flows=(),
        )
        client.get_protected_api_key_query()
        assert server.requests[0].query == "api_key=qkey"


def test_api_key_cookie_authentication_with_an_explicit_location(
    security_schemes_client: ModuleType,
) -> None:
    with http_test_server(
        responses={
            ("GET", "/protected/api-key-cookie"): Response(
                body=b'{"name": "x"}'
            )
        }
    ) as server:
        client = security_schemes_client.Client(
            url=server.url,
            api_key="ckey",
            api_key_in="cookie",
            api_key_name="api_key",
            oauth2_flows=(),
        )
        client.get_protected_api_key_cookie()
        assert server.requests[0].headers.get("Cookie") == "api_key=ckey"


def test_bearer_authentication(security_schemes_client: ModuleType) -> None:
    with http_test_server(
        responses={
            ("GET", "/protected/bearer"): Response(body=b'{"name": "x"}')
        }
    ) as server:
        client = security_schemes_client.Client(
            url=server.url, bearer_token="tok", oauth2_flows=()
        )
        client.get_protected_bearer()
        assert server.requests[0].headers.get("Authorization") == "Bearer tok"


# endregion

# region ClientModule: multipart code generation


@pytest.fixture
def multipart_client(
    generated_client_package: Callable[
        [OpenAPI], tuple[ModuleType, ModuleType]
    ],
) -> ModuleType:
    with open("tests/input-data/multipart-request-body.json") as f:
        open_api: OpenAPI = OpenAPI(f)
    _model_module, client_module = generated_client_package(open_api)
    return client_module


def test_generated_multipart_method_raises_key_error(
    multipart_client: ModuleType,
) -> None:
    """
    Documents the same real, verified, currently-unfixed bug already
    covered directly against `Client.request()` in
    `tests/test_client_request_runtime.py`'s
    `test_request_multipart_crashes_missing_content_encoding_header`,
    confirmed here to also break *generated* multipart operations (the
    exact scenario `tests/input-data/multipart-request-body.json` was
    built to exercise, per the infrastructure plan): `_request_callback`
    calls `request.headers.get("Content-encoding")` expecting ordinary
    `dict.get` semantics, but a `MultipartRequest`'s custom `Headers`
    object re-raises `KeyError` when no `default` is passed and the key
    is missing -- which it always is for an ordinary multipart request.
    Every generated multipart operation is therefore unusable as-is.
    Not fixed here (out of this test-only initiative's scope) --
    flagged to the user directly as well as documented here.
    """
    with http_test_server(
        responses={("POST", "/upload"): Response(status=200, body=b"{}")}
    ) as server:
        client = multipart_client.Client(url=server.url)
        with pytest.raises(KeyError, match="Content-encoding"):
            client.post_upload(
                file=b"filedata", description="a file", tags=["a", "b"]
            )


# endregion

# region ClientModule: polymorphic response-type resolution


@pytest.fixture
def polymorphic_client(
    generated_client_package: Callable[
        [OpenAPI], tuple[ModuleType, ModuleType]
    ],
) -> tuple[ModuleType, ModuleType]:
    with open("tests/input-data/polymorphic-schemas.json") as f:
        open_api: OpenAPI = OpenAPI(f)
    return generated_client_package(open_api)


def test_array_of_allof_merged_schema_response(
    polymorphic_client: tuple[ModuleType, ModuleType],
) -> None:
    model_module, client_module = polymorphic_client
    with http_test_server(
        responses={
            ("GET", "/pets"): Response(
                status=200,
                body=b'[{"name": "Rex", "species": "dog", "status": "sold"}]',
            )
        }
    ) as server:
        client = client_module.Client(url=server.url)
        pets = client.get_pets()
        assert len(pets) == 1
        pet = pets[0]
        assert isinstance(pet, model_module.Pet)
        assert pet.name == "Rex"
        assert pet.species == "dog"
        assert pet.status == "sold"


def test_oneof_response_infers_the_matching_variant(
    polymorphic_client: tuple[ModuleType, ModuleType],
) -> None:
    model_module, client_module = polymorphic_client
    with http_test_server(
        responses={
            ("GET", "/shapes"): Response(status=200, body=b'{"radius": 5}')
        }
    ) as server:
        client = client_module.Client(url=server.url)
        shape = client.get_shapes()
        assert isinstance(shape, model_module.Circle)
        assert shape.radius == 5


def test_anyof_response_infers_the_matching_variant(
    polymorphic_client: tuple[ModuleType, ModuleType],
) -> None:
    model_module, client_module = polymorphic_client
    with http_test_server(
        responses={
            ("GET", "/contacts"): Response(
                status=200, body=b'{"email": "a@b.com"}'
            )
        }
    ) as server:
        client = client_module.Client(url=server.url)
        contact = client.get_contacts()
        assert isinstance(contact, model_module.EmailContact)
        assert contact.email == "a@b.com"


def test_additional_properties_dictionary_response(
    polymorphic_client: tuple[ModuleType, ModuleType],
) -> None:
    _model_module, client_module = polymorphic_client
    with http_test_server(
        responses={
            ("GET", "/tags"): Response(
                status=200, body=b'{"a": "1", "b": "2"}'
            )
        }
    ) as server:
        client = client_module.Client(url=server.url)
        tags = client.get_tags()
        assert dict(tags) == {"a": "1", "b": "2"}


# endregion
