from __future__ import annotations

import collections.abc
import gzip
import io
import typing
from urllib.request import Request, urlopen

import pytest
from servers import Response, http_test_server

from oapi._multipart_request import MultipartRequest, Part
from oapi.client import (
    _assemble_request,
    _format_request_data,
    _get_file_name,
    _get_first,
    _remove_none,
    _represent_http_response,
    _set_response_callback,
    get_request_curl,
    urlencode,
)
from oapi.oas.model import Reference


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
