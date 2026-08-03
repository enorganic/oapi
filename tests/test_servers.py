from __future__ import annotations

import threading
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import pytest
from servers import Response, http_test_server


def test_records_request_and_returns_static_response() -> None:
    with http_test_server(
        responses={
            ("GET", "/hello"): Response(
                status=201,
                body=b'{"ok":true}',
                headers={"Content-type": "application/json"},
            )
        }
    ) as server:
        with urlopen(f"{server.url}/hello?x=1") as response:
            assert response.status == 201
            assert response.read() == b'{"ok":true}'
            assert response.headers["Content-type"] == "application/json"
        assert len(server.requests) == 1
        recorded = server.requests[0]
        assert recorded.method == "GET"
        assert recorded.path == "/hello"
        assert recorded.query == "x=1"


def test_sequence_responses_are_consumed_then_repeat_last() -> None:
    with http_test_server(
        sequences={
            ("GET", "/flaky"): [
                Response(status=503),
                Response(status=503),
                Response(status=200, body=b'{"ok":true}'),
            ]
        }
    ) as server:
        statuses = []
        for _ in range(4):
            try:
                with urlopen(f"{server.url}/flaky") as response:
                    statuses.append(response.status)
            except HTTPError as error:
                statuses.append(error.code)
        assert statuses == [503, 503, 200, 200]


def test_dynamic_handler_computes_response_from_request() -> None:
    with http_test_server(
        handlers={
            ("POST", "/echo"): lambda request: Response(
                status=200, body=request.body
            )
        }
    ) as server:
        data = b'{"a":1}'
        request = Request(f"{server.url}/echo", data=data, method="POST")
        with urlopen(request) as response:
            assert response.read() == data


def test_server_thread_is_joined_on_exit() -> None:
    threads_before = threading.active_count()
    with http_test_server() as server:
        assert threading.active_count() == threads_before + 1
        port = server.server_address[1]
    assert threading.active_count() == threads_before
    with pytest.raises(URLError):
        urlopen(f"http://127.0.0.1:{port}/", timeout=1)


if __name__ == "__main__":
    test_records_request_and_returns_static_response()
