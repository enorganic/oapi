from __future__ import annotations

import threading
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit


@dataclass
class RecordedRequest:
    method: str
    path: str
    query: str
    headers: dict[str, str]
    body: bytes


@dataclass
class Response:
    status: int = 200
    headers: dict[str, str] = field(default_factory=dict)
    body: bytes = b"{}"


ResponseKey = tuple[str, str]
ResponseHandler = Callable[[RecordedRequest], Response]


class HTTPTestServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(
        self,
        responses: Mapping[ResponseKey, Response] | None = None,
        sequences: Mapping[ResponseKey, list[Response]] | None = None,
        handlers: Mapping[ResponseKey, ResponseHandler] | None = None,
        default_response: Response | None = None,
    ) -> None:
        self.requests: list[RecordedRequest] = []
        self._lock = threading.Lock()
        self.responses: dict[ResponseKey, Response] = dict(responses or {})
        self.sequences: dict[ResponseKey, list[Response]] = {
            key: list(value) for key, value in (sequences or {}).items()
        }
        self.handlers: dict[ResponseKey, ResponseHandler] = dict(
            handlers or {}
        )
        self.default_response: Response = default_response or Response()
        super().__init__(("127.0.0.1", 0), _RequestHandler)

    @property
    def url(self) -> str:
        host, port = self.server_address[:2]
        host_str: str = host if isinstance(host, str) else host.decode()
        return f"http://{host_str}:{port}"

    def record(self, request: RecordedRequest) -> None:
        with self._lock:
            self.requests.append(request)

    def response_for(self, request: RecordedRequest) -> Response:
        key: ResponseKey = (request.method, request.path)
        handler = self.handlers.get(key)
        if handler is not None:
            return handler(request)
        with self._lock:
            sequence = self.sequences.get(key)
            if sequence:
                if len(sequence) > 1:
                    return sequence.pop(0)
                return sequence[0]
        return self.responses.get(key, self.default_response)


class _RequestHandler(BaseHTTPRequestHandler):
    server: HTTPTestServer

    def _handle(self) -> None:
        parsed = urlsplit(self.path)
        length = int(self.headers.get("Content-length") or 0)
        body = self.rfile.read(length) if length else b""
        request = RecordedRequest(
            method=self.command,
            path=parsed.path,
            query=parsed.query,
            headers=dict(self.headers.items()),
            body=body,
        )
        self.server.record(request)
        response = self.server.response_for(request)
        self.send_response(response.status)
        for key, value in response.headers.items():
            self.send_header(key, value)
        if "Content-length" not in response.headers:
            self.send_header("Content-length", str(len(response.body)))
        self.end_headers()
        if response.body:
            self.wfile.write(response.body)

    def do_GET(self) -> None:  # noqa: N802
        self._handle()

    def do_POST(self) -> None:  # noqa: N802
        self._handle()

    def do_PUT(self) -> None:  # noqa: N802
        self._handle()

    def do_PATCH(self) -> None:  # noqa: N802
        self._handle()

    def do_DELETE(self) -> None:  # noqa: N802
        self._handle()

    def log_message(self, format_: str, *args: object) -> None:
        return


@contextmanager
def http_test_server(
    responses: Mapping[ResponseKey, Response] | None = None,
    sequences: Mapping[ResponseKey, list[Response]] | None = None,
    handlers: Mapping[ResponseKey, ResponseHandler] | None = None,
    default_response: Response | None = None,
) -> Iterator[HTTPTestServer]:
    server = HTTPTestServer(
        responses=responses,
        sequences=sequences,
        handlers=handlers,
        default_response=default_response,
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
