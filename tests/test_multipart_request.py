from __future__ import annotations

import json
import random
from email.message import Message
from email.parser import BytesParser
from email.policy import compat32
from typing import cast
from urllib.request import urlopen

import pytest
from servers import RecordedRequest, Response, http_test_server

from oapi._multipart_request import (
    Data,
    Headers,
    MultipartRequest,
    Part,
    Parts,
    Request,
)


def _headers(data: Data) -> Headers:
    headers: Headers | None = data.headers
    assert headers is not None
    return headers


def _data_bytes(data: Data) -> bytes:
    value: bytes | None = data.data
    assert value is not None
    return value


def _parts(part: Part) -> Parts:
    parts: Parts | None = part.parts
    assert parts is not None
    return parts


def test_headers_capitalizes_keys() -> None:
    data: Data = Data(data=b"hello", headers={"x-custom": "1"})
    assert list(_headers(data).keys()) == [
        "X-custom",
        "Content-length",
    ]


def test_headers_contains_is_case_insensitive() -> None:
    data: Data = Data(data=b"hello", headers={"X-Custom": "1"})
    assert "x-custom" in _headers(data)


def test_headers_get_returns_default_for_missing_key() -> None:
    data: Data = Data(data=b"hello")
    assert _headers(data).get("missing", "fallback") == "fallback"


def test_headers_get_raises_without_default() -> None:
    data: Data = Data(data=b"hello")
    with pytest.raises(KeyError):
        _headers(data).get("missing")


def test_headers_content_length_is_always_present_for_data() -> None:
    data: Data = Data(data=b"hello")
    assert _headers(data)["Content-length"] == "5"
    assert "Content-length" in dict(_headers(data).items())


def test_headers_setitem_and_getitem() -> None:
    data: Data = Data(data=b"x", headers={})
    _headers(data)["New-Header"] = "val"
    assert _headers(data)["New-header"] == "val"


def test_headers_pop_removes_and_returns_value() -> None:
    data: Data = Data(data=b"x", headers={"New-Header": "val"})
    assert _headers(data).pop("New-Header") == "val"
    assert "New-header" not in _headers(data)


def test_headers_setdefault_adds_missing_key() -> None:
    data: Data = Data(data=b"x", headers={})
    assert _headers(data).setdefault("Another", "def") == "def"
    assert _headers(data)["Another"] == "def"


def test_headers_setdefault_keeps_existing_value() -> None:
    data: Data = Data(data=b"x", headers={"Another": "orig"})
    assert _headers(data).setdefault("Another", "def") == "orig"


def test_headers_update_with_mapping_and_kwargs() -> None:
    data: Data = Data(data=b"x", headers={"X-custom": "1"})
    _headers(data).update({"X-custom": "2"}, extra="3")
    items: dict[str, str] = dict(_headers(data).items())
    assert items["X-custom"] == "2"
    assert items["Extra"] == "3"


def test_headers_delitem_removes_key() -> None:
    data: Data = Data(data=b"x", headers={"Extra": "3"})
    del _headers(data)["Extra"]
    assert "Extra" not in dict(_headers(data).items())


def test_headers_popitem_removes_and_returns_pair() -> None:
    data: Data = Data(data=b"x", headers={"Only": "val"})
    key: str
    value: str
    key, value = _headers(data).popitem()
    assert (key, value) == ("Only", "val")


def test_headers_copy_produces_independent_equal_copy() -> None:
    data: Data = Data(data=b"x", headers={"X-custom": "1"})
    copied: Headers = _headers(data).copy()
    assert dict(copied.items()) == dict(_headers(data).items())
    assert copied is not _headers(data)


def test_headers_content_type_only_present_for_part_with_parts() -> None:
    data: Data = Data(data=b"x")
    assert "Content-type" not in dict(_headers(data).items())


def test_data_bytes_serializes_headers_and_body() -> None:
    data: Data = Data(
        data={"a": 1}, headers={"Content-Type": "application/json"}
    )
    assert bytes(data) == (
        b"Content-type: application/json\r\n"
        b"Content-length: 8\r\n\r\n"
        b'{"a": 1}\r\n'
    )


def test_data_str_matches_bytes_decoded() -> None:
    data: Data = Data(data=b"hello", headers={"X": "1"})
    assert str(data) == bytes(data).decode()


def test_data_deleter_clears_data() -> None:
    data: Data = Data(data=b"hello")
    del data.data
    assert data.data is None


def test_data_serializes_sob_model_via_sob_serialize() -> None:
    data: Data = Data(data=[1, 2, 3])
    assert data.data == b"[1, 2, 3]"


def test_data_bytes_cache_is_not_invalidated_by_later_header_mutation() -> (
    None
):
    """
    Documents actual behavior: `Data` (unlike `Part`) does not reset its
    `__bytes__` cache when headers are mutated after the first render,
    because `Headers._reset_part` only acts when `self.request` is a
    `Part`. This is the current, real behavior of the class -- not
    something this test judges as correct or incorrect.
    """
    data: Data = Data(data=b"x", headers={"A": "1"})
    first: bytes = bytes(data)
    _headers(data)["A"] = "2"
    second: bytes = bytes(data)
    assert first == second
    assert b"A: 1" in first


def test_part_bytes_cache_is_invalidated_by_header_mutation() -> None:
    """
    Contrasts with the `Data` case above: `Part` DOES reset its cache
    on header mutation, because `Headers._reset_part` checks
    `isinstance(self.request, Part)`.
    """
    part: Part = Part(data=b"x", headers={"A": "1"})
    first: bytes = bytes(part)
    _headers(part)["A"] = "2"
    second: bytes = bytes(part)
    assert first != second
    assert b"A: 2" in second


def test_part_boundary_does_not_collide_with_field_content() -> None:
    """
    Note: the boundary DOES appear in `top.data` -- it's the delimiter
    (`--{boundary}--`) between parts, by design. The real invariant is
    that the computed boundary isn't a substring of any field's actual
    content (which is what the `while boundary in data:` loop guards
    against; see the collision test below for a direct exercise of
    that loop).
    """
    part_a: Part = Part(
        data=b"field-a-value",
        headers={"Content-Disposition": 'form-data; name="a"'},
    )
    part_b: Part = Part(
        data=b"field-b-value",
        headers={"Content-Disposition": 'form-data; name="b"'},
    )
    top: Part = Part(parts=[part_a, part_b])
    assert top.boundary not in _data_bytes(part_a)
    assert top.boundary not in _data_bytes(part_b)


def test_part_content_type_header_includes_boundary() -> None:
    part_a: Part = Part(data=b"x")
    top: Part = Part(parts=[part_a])
    assert _headers(top)["Content-type"] == (
        f"multipart/form-data; boundary={top.boundary.decode()}"
    )


def test_part_boundary_retries_on_collision() -> None:
    """
    Forces a real collision (not mocked): seed `random`, observe the
    first 16-character candidate it would produce, then construct data
    that literally contains that candidate. The real collision-avoidance
    `while boundary in data` loop must then extend the boundary at least
    one character -- proven by re-seeding identically and checking the
    final boundary is longer than 16 bytes, starts with the original
    candidate, and (still) does not appear in the data.
    """
    random.seed(12345)
    probe: Part = Part(data=b"irrelevant")
    first_candidate: bytes = probe.boundary

    random.seed(12345)
    colliding_data: bytes = (
        b"here is some data containing "
        + first_candidate
        + b" right in the middle"
    )
    part: Part = Part(data=colliding_data)
    boundary: bytes = part.boundary

    assert len(boundary) > 16
    assert boundary.startswith(first_candidate)
    assert boundary not in colliding_data


def test_part_boundary_deleter_forces_recalculation() -> None:
    part_a: Part = Part(data=b"x")
    top: Part = Part(parts=[part_a])
    first: bytes = top.boundary
    del top.boundary
    second: bytes = top.boundary
    assert first != second


def test_part_without_parts_has_no_content_type_header() -> None:
    part: Part = Part(data=b"x")
    assert "Content-type" not in dict(_headers(part).items())


def test_part_data_property_returns_none_when_empty() -> None:
    part: Part = Part()
    assert part.data is None


def test_parts_append_invalidates_boundary_cache() -> None:
    top: Part = Part(parts=[Part(data=b"a")])
    _: bytes = top.boundary  # populate the cache
    assert top._boundary is not None  # noqa: SLF001
    _parts(top).append(Part(data=b"b"))
    assert top._boundary is None  # noqa: SLF001
    assert len(_parts(top)) == 2


def test_parts_clear_invalidates_boundary_cache_and_empties() -> None:
    top: Part = Part(parts=[Part(data=b"a"), Part(data=b"b")])
    _: bytes = top.boundary
    _parts(top).clear()
    assert top._boundary is None  # noqa: SLF001
    assert len(_parts(top)) == 0
    assert bool(_parts(top)) is False


def test_parts_extend_adds_all_items() -> None:
    top: Part = Part(parts=[Part(data=b"a")])
    _parts(top).extend([Part(data=b"b"), Part(data=b"c")])
    assert len(_parts(top)) == 3


def test_parts_reverse_reorders_in_place() -> None:
    part_a: Part = Part(data=b"a")
    part_b: Part = Part(data=b"b")
    top: Part = Part(parts=[part_a, part_b])
    _parts(top).reverse()
    assert list(_parts(top)) == [part_b, part_a]


def test_parts_delitem_removes_item() -> None:
    part_a: Part = Part(data=b"a")
    part_b: Part = Part(data=b"b")
    top: Part = Part(parts=[part_a, part_b])
    del _parts(top)[0]
    assert list(_parts(top)) == [part_b]


def test_parts_setitem_replaces_item() -> None:
    part_a: Part = Part(data=b"a")
    part_b: Part = Part(data=b"b")
    top: Part = Part(parts=[part_a])
    _parts(top)[0] = part_b
    assert list(_parts(top)) == [part_b]


def test_parts_bool_reflects_emptiness() -> None:
    empty_top: Part = Part()
    assert bool(_parts(empty_top)) is False
    non_empty_top: Part = Part(parts=[Part(data=b"a")])
    assert bool(_parts(non_empty_top)) is True


def test_assembled_multipart_data_parses_with_stdlib_email_parser() -> None:
    """
    Independent verification that this module's hand-rolled multipart
    encoding is genuinely valid RFC 1341 multipart/form-data -- parsed
    by Python's own `email` package, not by any code in this library.
    """
    part_a: Part = Part(
        data=b"field-a-value",
        headers={"Content-Disposition": 'form-data; name="a"'},
    )
    part_b: Part = Part(
        data=b"field-b-value",
        headers={"Content-Disposition": 'form-data; name="b"'},
    )
    top: Part = Part(parts=[part_a, part_b])

    message_bytes: bytes = (
        b"Content-type: "
        + _headers(top)["Content-type"].encode()
        + b"\r\n\r\n"
        + _data_bytes(top)
    )
    message: Message[str, str] = BytesParser(policy=compat32).parsebytes(
        message_bytes
    )

    assert message.is_multipart()
    payloads = message.get_payload()
    assert isinstance(payloads, list)
    typed_payloads: list[Message[str, str]] = cast(
        "list[Message[str, str]]", payloads
    )
    assert len(typed_payloads) == 2
    assert typed_payloads[0].get("Content-Disposition") == (
        'form-data; name="a"'
    )
    assert typed_payloads[0].get_payload(decode=True) == b"field-a-value"
    assert typed_payloads[1].get("Content-Disposition") == (
        'form-data; name="b"'
    )
    assert typed_payloads[1].get_payload(decode=True) == b"field-b-value"


def test_request_sends_real_json_body_over_http() -> None:
    with http_test_server(
        responses={("POST", "/echo"): Response(status=200)}
    ) as server:
        request: Request = Request(
            f"{server.url}/echo",
            data={"name": "widget", "count": 3},
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request) as response:
            assert response.status == 200
        recorded: RecordedRequest = server.requests[0]
        assert json.loads(recorded.body) == {
            "name": "widget",
            "count": 3,
        }
        assert recorded.headers["Content-Length"] == str(len(recorded.body))


def test_multipart_request_sends_real_multipart_body_over_http() -> None:
    with http_test_server(
        responses={("POST", "/upload"): Response(status=200)}
    ) as server:
        part: Part = Part(
            data=b"file-contents-here",
            headers={
                "Content-Disposition": (
                    'form-data; name="file"; filename="a.txt"'
                ),
                "Content-Type": "text/plain",
            },
        )
        request: MultipartRequest = MultipartRequest(
            f"{server.url}/upload", parts=[part], method="POST"
        )
        with urlopen(request) as response:
            assert response.status == 200

        recorded: RecordedRequest = server.requests[0]
        content_type: str = recorded.headers["Content-Type"]
        assert content_type.startswith("multipart/form-data; boundary=")

        message_bytes: bytes = (
            b"Content-type: "
            + content_type.encode()
            + b"\r\n\r\n"
            + recorded.body
        )
        message: Message[str, str] = BytesParser(policy=compat32).parsebytes(
            message_bytes
        )
        assert message.is_multipart()
        payloads = message.get_payload()
        assert isinstance(payloads, list)
        typed_payloads: list[Message[str, str]] = cast(
            "list[Message[str, str]]", payloads
        )
        assert len(typed_payloads) == 1
        assert typed_payloads[0].get("Content-Disposition") == (
            'form-data; name="file"; filename="a.txt"'
        )
        assert typed_payloads[0].get_payload(decode=True) == (
            b"file-contents-here"
        )
