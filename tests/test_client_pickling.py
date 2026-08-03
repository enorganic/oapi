from __future__ import annotations

import pickle
import threading
from email.message import Message
from logging import Logger, getLogger
from urllib.error import HTTPError

from oapi.client import (
    SSLContext,
    _make_http_errors_pickleable,
    _make_loggers_pickleable,
    _make_thread_locks_pickleable,
)


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
