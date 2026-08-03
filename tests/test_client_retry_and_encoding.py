from __future__ import annotations

import gzip
import logging
import time
import warnings
import zlib
from urllib.error import HTTPError

import pytest

from oapi.client import (
    _decode_content,
    _encode_content,
    default_retry_hook,
    retry,
)


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
