from __future__ import annotations

import contextlib
import io
import logging
import tempfile
import typing
import warnings
from pathlib import Path
from urllib.error import HTTPError

import pytest
from servers import Response, http_test_server

from oapi.client import Client


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
        temp_path: str = temp_file.name
    try:
        client: Client = Client(url="http://example.com")
        with pytest.raises(TypeError):
            client.request(
                f"file://{temp_path}",
                "POST",
                data={"field": b"x"},
                multipart=True,
                headers={"Content-encoding": "identity"},
            )
    finally:
        Path(temp_path).unlink()


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
