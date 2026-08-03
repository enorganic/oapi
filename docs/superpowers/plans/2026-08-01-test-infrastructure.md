# Test Infrastructure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task-by-task. Steps
> use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the shared test infrastructure — a real local HTTP test
server, a generated-module loader, and four new OpenAPI fixture
documents — that every subsequent test-coverage plan
(`_utilities.py`, `_multipart_request.py`, `oas/references.py`,
`oas/model.py`, `client.py` runtime, `client.py` codegen, `model.py`)
depends on.

**Architecture:** A stdlib-only `ThreadingHTTPServer` subclass
(`tests/servers.py`) records every request it receives and answers from
one of three sources — a static per-`(method, path)` response, a
consumable response *sequence* (for simulating transient failures), or a
dynamic callback — so one primitive covers plain request assertions,
retry/flaky-server tests, and computed responses (e.g. a future OAuth2
token endpoint) without new classes per scenario. A `tests/conftest.py`
fixture wraps `importlib` to load generated source strings as real,
importable modules from a `tmp_path`. Four new minimal OpenAPI 3.0 JSON
fixtures under `tests/input-data/` cover parameter styles, security
schemes, multipart bodies, and polymorphic schemas that no existing
fixture exercises.

**Tech Stack:** Python 3.10, stdlib `http.server`/`urllib`/`importlib`
only (no new dependencies), `pytest`, `sob` (already a dependency, used
to validate the new fixtures are real OpenAPI documents).

## Global Constraints

- Line length 79 (ruff + black), enforced via `hatch fmt --check`.
- mypy strict on `tests/`: `disallow_untyped_defs`,
  `disallow_incomplete_defs` — every function/method signature in new
  test files must be fully annotated.
- No new runtime or test dependencies — `tests/servers.py` and
  `tests/conftest.py` must use only the Python standard library.
- Python `~=3.10` — avoid syntax newer than 3.10 supports (this project
  already uses `from __future__ import annotations`, so `X | Y` union
  syntax in annotations is fine).
- Tests run with `--doctest-modules` (see `pyproject.toml`
  `[tool.hatch.envs.hatch-test]`) — do not put `>>>` sequences in
  docstrings in `tests/servers.py`/`tests/conftest.py` unless they are
  meant to be executed as doctests.
- New OpenAPI fixtures go in `tests/input-data/`, authored as **JSON**,
  not YAML: `oapi.oas.model.OpenAPI(readable)` parses JSON directly from
  a plain file object; YAML input only works when routed through
  `oapi.oas.references._urlopen`, which pre-converts YAML to JSON before
  handing it to `OpenAPI(...)`. All new fixtures here are loaded via
  plain `open()`, matching the existing
  `tests/input-data/languagetool-swagger.json` pattern in
  `tests/test_model.py`.
- Verify commands throughout this plan with:
  `hatch run hatch-test.py3.10:python ...` (the `hatch-test` env is the
  one with `pytest`, `pyyaml`, and this project installed; the bare
  `default` env in this checkout currently fails to sync — don't use it).

---

## Task 1: `HTTPTestServer` — recording + static responses

**Files:**
- Create: `tests/servers.py`
- Test: `tests/test_servers.py`

**Interfaces:**
- Produces: `tests.servers.RecordedRequest` (dataclass: `method: str`,
  `path: str`, `query: str`, `headers: dict[str, str]`, `body: bytes`),
  `tests.servers.Response` (dataclass: `status: int = 200`,
  `headers: dict[str, str] = field(default_factory=dict)`,
  `body: bytes = b"{}"`), `tests.servers.HTTPTestServer` (with `.url:
  str` property and `.requests: list[RecordedRequest]`),
  `tests.servers.http_test_server(...)` (a `@contextmanager` function
  yielding a running `HTTPTestServer` on an OS-assigned free port,
  shutting it down cleanly on exit). Every later task/plan that needs a
  real local HTTP endpoint imports `http_test_server` from this module.

- [ ] **Step 1: Write the failing test**

Create `tests/test_servers.py`:

```python
from __future__ import annotations

from urllib.request import urlopen

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
            assert (
                response.headers["Content-type"] == "application/json"
            )
        assert len(server.requests) == 1
        recorded = server.requests[0]
        assert recorded.method == "GET"
        assert recorded.path == "/hello"
        assert recorded.query == "x=1"


if __name__ == "__main__":
    test_records_request_and_returns_static_response()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `hatch run hatch-test.py3.10:pytest tests/test_servers.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'servers'`

- [ ] **Step 3: Write the implementation**

Create `tests/servers.py`:

```python
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
        default_response: Response | None = None,
    ) -> None:
        self.requests: list[RecordedRequest] = []
        self._lock = threading.Lock()
        self.responses: dict[ResponseKey, Response] = dict(
            responses or {}
        )
        self.default_response: Response = default_response or Response()
        super().__init__(("127.0.0.1", 0), _RequestHandler)

    @property
    def url(self) -> str:
        host, port = self.server_address[:2]
        return f"http://{host}:{port}"

    def record(self, request: RecordedRequest) -> None:
        with self._lock:
            self.requests.append(request)

    def response_for(self, request: RecordedRequest) -> Response:
        key: ResponseKey = (request.method, request.path)
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
            self.send_header(
                "Content-length", str(len(response.body))
            )
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
    default_response: Response | None = None,
) -> Iterator[HTTPTestServer]:
    server = HTTPTestServer(
        responses=responses,
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `hatch run hatch-test.py3.10:pytest tests/test_servers.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/servers.py tests/test_servers.py
git commit -m "test: add local HTTP test server with static responses"
```

## Task 2: Response sequences (for flaky-server / retry tests)

**Files:**
- Modify: `tests/servers.py`
- Test: `tests/test_servers.py`

**Interfaces:**
- Consumes: `HTTPTestServer.__init__`, `HTTPTestServer.response_for`
  from Task 1.
- Produces: `HTTPTestServer(sequences=...)` constructor parameter —
  `Mapping[ResponseKey, list[Response]]`. For a given `(method, path)`
  key, each request pops the next `Response` off the list until only
  one remains, which then repeats for all subsequent requests. This is
  what a later retry-logic test uses to simulate "fails twice, then
  succeeds" against a real socket.

- [ ] **Step 1: Write the failing test**

Add to `tests/test_servers.py`:

```python
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
```

Add `from urllib.error import HTTPError` to the imports at the top of
`tests/test_servers.py`.

- [ ] **Step 2: Run test to verify it fails**

Run: `hatch run hatch-test.py3.10:pytest tests/test_servers.py -v`
Expected: FAIL with
`TypeError: HTTPTestServer.__init__() got an unexpected keyword argument 'sequences'`

- [ ] **Step 3: Write the implementation**

In `tests/servers.py`, update `HTTPTestServer.__init__` and
`response_for`:

```python
    def __init__(
        self,
        responses: Mapping[ResponseKey, Response] | None = None,
        sequences: Mapping[ResponseKey, list[Response]] | None = None,
        default_response: Response | None = None,
    ) -> None:
        self.requests: list[RecordedRequest] = []
        self._lock = threading.Lock()
        self.responses: dict[ResponseKey, Response] = dict(
            responses or {}
        )
        self.sequences: dict[ResponseKey, list[Response]] = {
            key: list(value) for key, value in (sequences or {}).items()
        }
        self.default_response: Response = default_response or Response()
        super().__init__(("127.0.0.1", 0), _RequestHandler)
```

```python
    def response_for(self, request: RecordedRequest) -> Response:
        key: ResponseKey = (request.method, request.path)
        with self._lock:
            sequence = self.sequences.get(key)
            if sequence:
                if len(sequence) > 1:
                    return sequence.pop(0)
                return sequence[0]
        return self.responses.get(key, self.default_response)
```

Update `http_test_server(...)` to accept and forward `sequences`:

```python
@contextmanager
def http_test_server(
    responses: Mapping[ResponseKey, Response] | None = None,
    sequences: Mapping[ResponseKey, list[Response]] | None = None,
    default_response: Response | None = None,
) -> Iterator[HTTPTestServer]:
    server = HTTPTestServer(
        responses=responses,
        sequences=sequences,
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `hatch run hatch-test.py3.10:pytest tests/test_servers.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add tests/servers.py tests/test_servers.py
git commit -m "test: add sequence responses to the test HTTP server"
```

## Task 3: Dynamic handler callbacks (for computed responses)

**Files:**
- Modify: `tests/servers.py`
- Test: `tests/test_servers.py`

**Interfaces:**
- Consumes: `HTTPTestServer.__init__`, `HTTPTestServer.response_for`,
  `RecordedRequest` from Tasks 1–2.
- Produces: `HTTPTestServer(handlers=...)` constructor parameter —
  `Mapping[ResponseKey, Callable[[RecordedRequest], Response]]`, checked
  before static `responses`/`sequences`. This is what a later OAuth2
  test uses to build a fake token endpoint that reads the real posted
  `grant_type`/`Authorization` header and computes a real token
  response, without hand-rolling a second server class.

- [ ] **Step 1: Write the failing test**

Add to `tests/test_servers.py`:

```python
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
```

Add `from urllib.request import Request, urlopen` — replace the earlier
bare `from urllib.request import urlopen` import with this combined
one.

- [ ] **Step 2: Run test to verify it fails**

Run: `hatch run hatch-test.py3.10:pytest tests/test_servers.py -v`
Expected: FAIL with
`TypeError: HTTPTestServer.__init__() got an unexpected keyword argument 'handlers'`

- [ ] **Step 3: Write the implementation**

In `tests/servers.py`, add the `ResponseHandler` type alias usage to
`__init__`, `response_for`, and `http_test_server`:

```python
    def __init__(
        self,
        responses: Mapping[ResponseKey, Response] | None = None,
        sequences: Mapping[ResponseKey, list[Response]] | None = None,
        handlers: Mapping[ResponseKey, ResponseHandler] | None = None,
        default_response: Response | None = None,
    ) -> None:
        self.requests: list[RecordedRequest] = []
        self._lock = threading.Lock()
        self.responses: dict[ResponseKey, Response] = dict(
            responses or {}
        )
        self.sequences: dict[ResponseKey, list[Response]] = {
            key: list(value) for key, value in (sequences or {}).items()
        }
        self.handlers: dict[ResponseKey, ResponseHandler] = dict(
            handlers or {}
        )
        self.default_response: Response = default_response or Response()
        super().__init__(("127.0.0.1", 0), _RequestHandler)
```

```python
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
```

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `hatch run hatch-test.py3.10:pytest tests/test_servers.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add tests/servers.py tests/test_servers.py
git commit -m "test: add dynamic handler callbacks to the test HTTP server"
```

## Task 4: Clean shutdown verification

**Files:**
- Test: `tests/test_servers.py` (no changes to `tests/servers.py` — this
  task verifies existing teardown behavior from Task 1's
  `http_test_server` implementation)

**Interfaces:**
- Consumes: `http_test_server` from Task 1 (unchanged).
- Produces: nothing new — this is a regression guard so later plans can
  rely on `http_test_server` never leaking a thread or a bound port
  across tests (important once dozens of tests each open their own
  server).

- [ ] **Step 1: Write the failing-if-broken test**

Add to `tests/test_servers.py`:

```python
def test_server_thread_is_joined_on_exit() -> None:
    threads_before = threading.active_count()
    with http_test_server() as server:
        assert threading.active_count() == threads_before + 1
        port = server.server_address[1]
    assert threading.active_count() == threads_before
    with pytest.raises(URLError):
        urlopen(f"http://127.0.0.1:{port}/", timeout=1)
```

Add `import threading`, `import pytest`, and
`from urllib.error import URLError` to `tests/test_servers.py`'s
imports.

- [ ] **Step 2: Run test to verify it currently passes**

Run: `hatch run hatch-test.py3.10:pytest tests/test_servers.py -v`
Expected: PASS (4 tests) — this test documents behavior Task 1 already
implemented (the `finally` block joins the thread and closes the
socket), so there is no red step here; it exists to catch a future
regression, not to drive new code.

- [ ] **Step 3: Commit**

```bash
git add tests/test_servers.py
git commit -m "test: verify the test HTTP server shuts down cleanly"
```

## Task 5: Generated-module loader fixture

**Files:**
- Create: `tests/conftest.py`
- Test: `tests/test_conftest.py`

**Interfaces:**
- Produces: `generated_module_loader` pytest fixture — a
  `Callable[[str, str], ModuleType]` (`source, module_name="generated_module"`)
  that writes `source` to a `tmp_path`-backed `.py` file, imports it as
  a real module via `importlib`, and returns it. Later plans (`client.py`
  codegen, `model.py` codegen) use this to `exec` the source strings
  produced by `ClientModule.get_source(...)`/`ModelModule.__str__()` and
  then exercise the resulting classes/functions for real.

- [ ] **Step 1: Write the failing test**

Create `tests/test_conftest.py`:

```python
from __future__ import annotations

from collections.abc import Callable
from types import ModuleType


def test_generated_module_loader_imports_real_module(
    generated_module_loader: Callable[..., ModuleType],
) -> None:
    module = generated_module_loader(
        "VALUE = 42\n\n\ndef greet(name: str) -> str:\n"
        "    return f'hi {name}'\n"
    )
    assert module.VALUE == 42
    assert module.greet("x") == "hi x"


if __name__ == "__main__":
    pass
```

- [ ] **Step 2: Run test to verify it fails**

Run: `hatch run hatch-test.py3.10:pytest tests/test_conftest.py -v`
Expected: FAIL with
`fixture 'generated_module_loader' not found`

- [ ] **Step 3: Write the implementation**

Create `tests/conftest.py`:

```python
from __future__ import annotations

import importlib.util
import sys
from collections.abc import Callable, Iterator
from pathlib import Path
from types import ModuleType

import pytest


@pytest.fixture
def generated_module_loader(
    tmp_path: Path,
) -> Iterator[Callable[..., ModuleType]]:
    loaded_module_names: list[str] = []

    def load(
        source: str, module_name: str = "generated_module"
    ) -> ModuleType:
        module_path = tmp_path / f"{module_name}.py"
        module_path.write_text(source)
        spec = importlib.util.spec_from_file_location(
            module_name, module_path
        )
        if spec is None or spec.loader is None:
            message = f"Unable to load a module from {module_path}"
            raise ImportError(message)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        loaded_module_names.append(module_name)
        spec.loader.exec_module(module)
        return module

    yield load
    for module_name in loaded_module_names:
        sys.modules.pop(module_name, None)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `hatch run hatch-test.py3.10:pytest tests/test_conftest.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/conftest.py tests/test_conftest.py
git commit -m "test: add generated-module loader fixture"
```

## Task 6: `parameter-styles.json` fixture

**Files:**
- Create: `tests/input-data/parameter-styles.json`
- Test: `tests/test_input_data.py`

**Interfaces:**
- Produces: a real, `sob.validate`-passing `OpenAPI` document with nine
  operations, one per OpenAPI 3 parameter `style`/location combination
  (`simple`/path, `label`/path, `matrix`/path, `form`/query,
  `spaceDelimited`/query, `pipeDelimited`/query, `deepObject`/query,
  `simple`/header, `form`/cookie) — `operationId`s
  `getPathSimple`, `getPathLabel`, `getPathMatrix`, `getQueryForm`,
  `getQuerySpaceDelimited`, `getQueryPipeDelimited`,
  `getQueryDeepObject`, `getHeaderSimple`, `getCookieForm`. A later
  `client.py` plan generates a client from this fixture and asserts
  against what a real local server actually received for each style.

- [ ] **Step 1: Write the failing test**

Create `tests/test_input_data.py`:

```python
from __future__ import annotations

from pathlib import Path

import sob

from oapi.oas.model import OpenAPI

INPUT_DATA_PATH: Path = Path(__file__).absolute().parent / "input-data"


def test_parameter_styles_fixture_is_valid_openapi() -> None:
    with open(INPUT_DATA_PATH / "parameter-styles.json") as io_:
        open_api = OpenAPI(io_)
    sob.validate(open_api)
    assert open_api.paths is not None
    operation_ids = {
        operation.operation_id
        for path_item in open_api.paths.values()
        for operation in (
            path_item.get,
            path_item.post,
            path_item.put,
            path_item.patch,
            path_item.delete,
        )
        if operation is not None
    }
    assert operation_ids == {
        "getPathSimple",
        "getPathLabel",
        "getPathMatrix",
        "getQueryForm",
        "getQuerySpaceDelimited",
        "getQueryPipeDelimited",
        "getQueryDeepObject",
        "getHeaderSimple",
        "getCookieForm",
    }
```

- [ ] **Step 2: Run test to verify it fails**

Run: `hatch run hatch-test.py3.10:pytest tests/test_input_data.py -v`
Expected: FAIL with `FileNotFoundError`

- [ ] **Step 3: Create the fixture**

Create `tests/input-data/parameter-styles.json`:

```json
{
  "openapi": "3.0.3",
  "info": {
    "title": "Parameter Styles",
    "description": "Minimal fixture exercising every OpenAPI 3 parameter `style`, for testing `oapi.client`'s argument-formatting functions end-to-end.",
    "version": "1.0.0"
  },
  "paths": {
    "/path/simple/{id}": {
      "get": {
        "operationId": "getPathSimple",
        "parameters": [
          {
            "name": "id",
            "in": "path",
            "required": true,
            "style": "simple",
            "schema": {"type": "array", "items": {"type": "integer"}}
          }
        ],
        "responses": {
          "200": {
            "description": "OK",
            "content": {"application/json": {"schema": {"type": "object"}}}
          }
        }
      }
    },
    "/path/label/{id}": {
      "get": {
        "operationId": "getPathLabel",
        "parameters": [
          {
            "name": "id",
            "in": "path",
            "required": true,
            "style": "label",
            "explode": true,
            "schema": {"type": "array", "items": {"type": "integer"}}
          }
        ],
        "responses": {
          "200": {
            "description": "OK",
            "content": {"application/json": {"schema": {"type": "object"}}}
          }
        }
      }
    },
    "/path/matrix/{id}": {
      "get": {
        "operationId": "getPathMatrix",
        "parameters": [
          {
            "name": "id",
            "in": "path",
            "required": true,
            "style": "matrix",
            "explode": true,
            "schema": {
              "type": "object",
              "additionalProperties": {"type": "integer"}
            }
          }
        ],
        "responses": {
          "200": {
            "description": "OK",
            "content": {"application/json": {"schema": {"type": "object"}}}
          }
        }
      }
    },
    "/query/form": {
      "get": {
        "operationId": "getQueryForm",
        "parameters": [
          {
            "name": "ids",
            "in": "query",
            "style": "form",
            "explode": false,
            "schema": {"type": "array", "items": {"type": "integer"}}
          }
        ],
        "responses": {
          "200": {
            "description": "OK",
            "content": {"application/json": {"schema": {"type": "object"}}}
          }
        }
      }
    },
    "/query/space-delimited": {
      "get": {
        "operationId": "getQuerySpaceDelimited",
        "parameters": [
          {
            "name": "ids",
            "in": "query",
            "style": "spaceDelimited",
            "schema": {"type": "array", "items": {"type": "integer"}}
          }
        ],
        "responses": {
          "200": {
            "description": "OK",
            "content": {"application/json": {"schema": {"type": "object"}}}
          }
        }
      }
    },
    "/query/pipe-delimited": {
      "get": {
        "operationId": "getQueryPipeDelimited",
        "parameters": [
          {
            "name": "ids",
            "in": "query",
            "style": "pipeDelimited",
            "schema": {"type": "array", "items": {"type": "integer"}}
          }
        ],
        "responses": {
          "200": {
            "description": "OK",
            "content": {"application/json": {"schema": {"type": "object"}}}
          }
        }
      }
    },
    "/query/deep-object": {
      "get": {
        "operationId": "getQueryDeepObject",
        "parameters": [
          {
            "name": "filter",
            "in": "query",
            "style": "deepObject",
            "explode": true,
            "schema": {
              "type": "object",
              "additionalProperties": {"type": "string"}
            }
          }
        ],
        "responses": {
          "200": {
            "description": "OK",
            "content": {"application/json": {"schema": {"type": "object"}}}
          }
        }
      }
    },
    "/header/simple": {
      "get": {
        "operationId": "getHeaderSimple",
        "parameters": [
          {
            "name": "X-Ids",
            "in": "header",
            "style": "simple",
            "schema": {"type": "array", "items": {"type": "integer"}}
          }
        ],
        "responses": {
          "200": {
            "description": "OK",
            "content": {"application/json": {"schema": {"type": "object"}}}
          }
        }
      }
    },
    "/cookie/form": {
      "get": {
        "operationId": "getCookieForm",
        "parameters": [
          {
            "name": "ids",
            "in": "cookie",
            "style": "form",
            "explode": false,
            "schema": {"type": "array", "items": {"type": "integer"}}
          }
        ],
        "responses": {
          "200": {
            "description": "OK",
            "content": {"application/json": {"schema": {"type": "object"}}}
          }
        }
      }
    }
  }
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `hatch run hatch-test.py3.10:pytest tests/test_input_data.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/input-data/parameter-styles.json tests/test_input_data.py
git commit -m "test: add parameter-styles OpenAPI fixture"
```

## Task 7: `security-schemes.json` fixture

**Files:**
- Create: `tests/input-data/security-schemes.json`
- Modify: `tests/test_input_data.py`

**Interfaces:**
- Produces: a real, `sob.validate`-passing `OpenAPI` document with
  `components.securitySchemes` covering `apiKey` (header/query/cookie),
  `http` (`bearer`), `oauth2` (`password`, `clientCredentials`,
  `authorizationCode`, `implicit` flows), and `openIdConnect` — one GET
  operation per scheme (`operationId`s `getApiKeyHeader`,
  `getApiKeyQuery`, `getApiKeyCookie`, `getBearer`,
  `getOauth2Password`, `getOauth2ClientCredentials`,
  `getOauth2AuthorizationCode`, `getOauth2Implicit`,
  `getOpenIdConnect`). A later `client.py` plan generates a client from
  this fixture to cover the auth-related source-generation branches and
  (for `apiKey`/`oauth2Password`/`oauth2ClientCredentials`, which are
  runtime-exercisable without a browser redirect) runtime auth behavior
  against a real local server.

- [ ] **Step 1: Write the failing test**

Add to `tests/test_input_data.py`:

```python
def test_security_schemes_fixture_is_valid_openapi() -> None:
    with open(INPUT_DATA_PATH / "security-schemes.json") as io_:
        open_api = OpenAPI(io_)
    sob.validate(open_api)
    assert open_api.components is not None
    assert open_api.components.security_schemes is not None
    assert set(open_api.components.security_schemes.keys()) == {
        "apiKeyHeader",
        "apiKeyQuery",
        "apiKeyCookie",
        "httpBearer",
        "oauth2Password",
        "oauth2ClientCredentials",
        "oauth2AuthorizationCode",
        "oauth2Implicit",
        "openIdConnect",
    }
```

- [ ] **Step 2: Run test to verify it fails**

Run: `hatch run hatch-test.py3.10:pytest tests/test_input_data.py -v`
Expected: FAIL with `FileNotFoundError`

- [ ] **Step 3: Create the fixture**

Create `tests/input-data/security-schemes.json`:

```json
{
  "openapi": "3.0.3",
  "info": {
    "title": "Security Schemes",
    "description": "Minimal fixture covering apiKey, http, oauth2 (all four flows), and openIdConnect security schemes, for testing `oapi.client` auth code-generation and runtime behavior end-to-end.",
    "version": "1.0.0"
  },
  "paths": {
    "/protected/api-key-header": {
      "get": {
        "operationId": "getApiKeyHeader",
        "security": [{"apiKeyHeader": []}],
        "responses": {
          "200": {
            "description": "OK",
            "content": {"application/json": {"schema": {"type": "object"}}}
          }
        }
      }
    },
    "/protected/api-key-query": {
      "get": {
        "operationId": "getApiKeyQuery",
        "security": [{"apiKeyQuery": []}],
        "responses": {
          "200": {
            "description": "OK",
            "content": {"application/json": {"schema": {"type": "object"}}}
          }
        }
      }
    },
    "/protected/api-key-cookie": {
      "get": {
        "operationId": "getApiKeyCookie",
        "security": [{"apiKeyCookie": []}],
        "responses": {
          "200": {
            "description": "OK",
            "content": {"application/json": {"schema": {"type": "object"}}}
          }
        }
      }
    },
    "/protected/bearer": {
      "get": {
        "operationId": "getBearer",
        "security": [{"httpBearer": []}],
        "responses": {
          "200": {
            "description": "OK",
            "content": {"application/json": {"schema": {"type": "object"}}}
          }
        }
      }
    },
    "/protected/oauth2-password": {
      "get": {
        "operationId": "getOauth2Password",
        "security": [{"oauth2Password": ["read"]}],
        "responses": {
          "200": {
            "description": "OK",
            "content": {"application/json": {"schema": {"type": "object"}}}
          }
        }
      }
    },
    "/protected/oauth2-client-credentials": {
      "get": {
        "operationId": "getOauth2ClientCredentials",
        "security": [{"oauth2ClientCredentials": ["read"]}],
        "responses": {
          "200": {
            "description": "OK",
            "content": {"application/json": {"schema": {"type": "object"}}}
          }
        }
      }
    },
    "/protected/oauth2-authorization-code": {
      "get": {
        "operationId": "getOauth2AuthorizationCode",
        "security": [{"oauth2AuthorizationCode": ["read"]}],
        "responses": {
          "200": {
            "description": "OK",
            "content": {"application/json": {"schema": {"type": "object"}}}
          }
        }
      }
    },
    "/protected/oauth2-implicit": {
      "get": {
        "operationId": "getOauth2Implicit",
        "security": [{"oauth2Implicit": ["read"]}],
        "responses": {
          "200": {
            "description": "OK",
            "content": {"application/json": {"schema": {"type": "object"}}}
          }
        }
      }
    },
    "/protected/open-id-connect": {
      "get": {
        "operationId": "getOpenIdConnect",
        "security": [{"openIdConnect": []}],
        "responses": {
          "200": {
            "description": "OK",
            "content": {"application/json": {"schema": {"type": "object"}}}
          }
        }
      }
    }
  },
  "components": {
    "securitySchemes": {
      "apiKeyHeader": {
        "type": "apiKey",
        "in": "header",
        "name": "X-Api-Key"
      },
      "apiKeyQuery": {
        "type": "apiKey",
        "in": "query",
        "name": "api_key"
      },
      "apiKeyCookie": {
        "type": "apiKey",
        "in": "cookie",
        "name": "api_key"
      },
      "httpBearer": {
        "type": "http",
        "scheme": "bearer"
      },
      "oauth2Password": {
        "type": "oauth2",
        "flows": {
          "password": {
            "tokenUrl": "https://example.com/oauth2/token",
            "scopes": {"read": "Read access"}
          }
        }
      },
      "oauth2ClientCredentials": {
        "type": "oauth2",
        "flows": {
          "clientCredentials": {
            "tokenUrl": "https://example.com/oauth2/token",
            "scopes": {"read": "Read access"}
          }
        }
      },
      "oauth2AuthorizationCode": {
        "type": "oauth2",
        "flows": {
          "authorizationCode": {
            "authorizationUrl": "https://example.com/oauth2/authorize",
            "tokenUrl": "https://example.com/oauth2/token",
            "scopes": {"read": "Read access"}
          }
        }
      },
      "oauth2Implicit": {
        "type": "oauth2",
        "flows": {
          "implicit": {
            "authorizationUrl": "https://example.com/oauth2/authorize",
            "scopes": {"read": "Read access"}
          }
        }
      },
      "openIdConnect": {
        "type": "openIdConnect",
        "openIdConnectUrl": "https://example.com/.well-known/openid-configuration"
      }
    }
  }
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `hatch run hatch-test.py3.10:pytest tests/test_input_data.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add tests/input-data/security-schemes.json tests/test_input_data.py
git commit -m "test: add security-schemes OpenAPI fixture"
```

## Task 8: `multipart-request-body.json` fixture

**Files:**
- Create: `tests/input-data/multipart-request-body.json`
- Modify: `tests/test_input_data.py`

**Interfaces:**
- Produces: a real, `sob.validate`-passing `OpenAPI` document with one
  `POST /upload` operation (`operationId` `postUpload`) whose request
  body is `multipart/form-data` with a required `file` field
  (`type: string, format: binary`), an optional `description` string
  field, and an optional `tags` array-of-strings field. A later plan
  drives both `_multipart_request.py` and `client.py`'s
  `_iter_request_body_form_parameters_source` branches with this
  fixture.

- [ ] **Step 1: Write the failing test**

Add to `tests/test_input_data.py`:

```python
def test_multipart_request_body_fixture_is_valid_openapi() -> None:
    with open(INPUT_DATA_PATH / "multipart-request-body.json") as io_:
        open_api = OpenAPI(io_)
    sob.validate(open_api)
    assert open_api.paths is not None
    upload = open_api.paths["/upload"]
    assert upload.post is not None
    assert upload.post.operation_id == "postUpload"
    assert upload.post.request_body is not None
    assert "multipart/form-data" in upload.post.request_body.content
```

- [ ] **Step 2: Run test to verify it fails**

Run: `hatch run hatch-test.py3.10:pytest tests/test_input_data.py -v`
Expected: FAIL with `FileNotFoundError`

- [ ] **Step 3: Create the fixture**

Create `tests/input-data/multipart-request-body.json`:

```json
{
  "openapi": "3.0.3",
  "info": {
    "title": "Multipart Request Body",
    "description": "Minimal fixture with a `multipart/form-data` request body (one file field, one string field, one array field), for testing `oapi._multipart_request` and `oapi.client` form-data code-generation and runtime behavior end-to-end.",
    "version": "1.0.0"
  },
  "paths": {
    "/upload": {
      "post": {
        "operationId": "postUpload",
        "requestBody": {
          "required": true,
          "content": {
            "multipart/form-data": {
              "schema": {
                "type": "object",
                "required": ["file"],
                "properties": {
                  "file": {"type": "string", "format": "binary"},
                  "description": {"type": "string"},
                  "tags": {
                    "type": "array",
                    "items": {"type": "string"}
                  }
                }
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "OK",
            "content": {"application/json": {"schema": {"type": "object"}}}
          }
        }
      }
    }
  }
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `hatch run hatch-test.py3.10:pytest tests/test_input_data.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add tests/input-data/multipart-request-body.json tests/test_input_data.py
git commit -m "test: add multipart-request-body OpenAPI fixture"
```

## Task 9: `polymorphic-schemas.json` fixture

**Files:**
- Create: `tests/input-data/polymorphic-schemas.json`
- Modify: `tests/test_input_data.py`

**Interfaces:**
- Produces: a real, `sob.validate`-passing `OpenAPI` document with
  `components.schemas`: `Status` (string enum), `NamedEntity` (base
  object), `Pet` (`allOf` merging `NamedEntity` + inline properties),
  `Circle`/`Square`/`Shape` (`oneOf`), `EmailContact`/`PhoneContact`/
  `Contact` (`anyOf`), plus a `GET /tags` operation returning a
  dictionary schema (`additionalProperties`). A later `model.py` plan
  drives `_Modeler.merge_schemas_properties`,
  `merge_array_schemas`/`merge_dictionary_schemas`,
  `get_merged_schemas_object_class`, and `polymorph_property` with this
  fixture.

- [ ] **Step 1: Write the failing test**

Add to `tests/test_input_data.py`:

```python
def test_polymorphic_schemas_fixture_is_valid_openapi() -> None:
    with open(INPUT_DATA_PATH / "polymorphic-schemas.json") as io_:
        open_api = OpenAPI(io_)
    sob.validate(open_api)
    assert open_api.components is not None
    assert open_api.components.schemas is not None
    assert set(open_api.components.schemas.keys()) == {
        "Status",
        "NamedEntity",
        "Pet",
        "Circle",
        "Square",
        "Shape",
        "EmailContact",
        "PhoneContact",
        "Contact",
    }
```

- [ ] **Step 2: Run test to verify it fails**

Run: `hatch run hatch-test.py3.10:pytest tests/test_input_data.py -v`
Expected: FAIL with `FileNotFoundError`

- [ ] **Step 3: Create the fixture**

Create `tests/input-data/polymorphic-schemas.json`:

```json
{
  "openapi": "3.0.3",
  "info": {
    "title": "Polymorphic Schemas",
    "description": "Minimal fixture covering `allOf` merging, `oneOf`/`anyOf` polymorphism, array schemas, dictionary (`additionalProperties`) schemas, and enums, for testing `oapi.model`'s `_Modeler` merge/polymorph code paths.",
    "version": "1.0.0"
  },
  "paths": {
    "/pets": {
      "get": {
        "operationId": "getPets",
        "responses": {
          "200": {
            "description": "OK",
            "content": {
              "application/json": {
                "schema": {
                  "type": "array",
                  "items": {"$ref": "#/components/schemas/Pet"}
                }
              }
            }
          }
        }
      }
    },
    "/shapes": {
      "get": {
        "operationId": "getShapes",
        "responses": {
          "200": {
            "description": "OK",
            "content": {
              "application/json": {
                "schema": {"$ref": "#/components/schemas/Shape"}
              }
            }
          }
        }
      }
    },
    "/contacts": {
      "get": {
        "operationId": "getContacts",
        "responses": {
          "200": {
            "description": "OK",
            "content": {
              "application/json": {
                "schema": {"$ref": "#/components/schemas/Contact"}
              }
            }
          }
        }
      }
    },
    "/tags": {
      "get": {
        "operationId": "getTags",
        "responses": {
          "200": {
            "description": "OK",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "additionalProperties": {"type": "string"}
                }
              }
            }
          }
        }
      }
    }
  },
  "components": {
    "schemas": {
      "Status": {
        "type": "string",
        "enum": ["available", "pending", "sold"]
      },
      "NamedEntity": {
        "type": "object",
        "required": ["name"],
        "properties": {"name": {"type": "string"}}
      },
      "Pet": {
        "allOf": [
          {"$ref": "#/components/schemas/NamedEntity"},
          {
            "type": "object",
            "properties": {
              "species": {"type": "string"},
              "status": {"$ref": "#/components/schemas/Status"}
            }
          }
        ]
      },
      "Circle": {
        "type": "object",
        "required": ["radius"],
        "properties": {"radius": {"type": "number"}}
      },
      "Square": {
        "type": "object",
        "required": ["side"],
        "properties": {"side": {"type": "number"}}
      },
      "Shape": {
        "oneOf": [
          {"$ref": "#/components/schemas/Circle"},
          {"$ref": "#/components/schemas/Square"}
        ]
      },
      "EmailContact": {
        "type": "object",
        "required": ["email"],
        "properties": {"email": {"type": "string"}}
      },
      "PhoneContact": {
        "type": "object",
        "required": ["phone"],
        "properties": {"phone": {"type": "string"}}
      },
      "Contact": {
        "anyOf": [
          {"$ref": "#/components/schemas/EmailContact"},
          {"$ref": "#/components/schemas/PhoneContact"}
        ]
      }
    }
  }
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `hatch run hatch-test.py3.10:pytest tests/test_input_data.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add tests/input-data/polymorphic-schemas.json tests/test_input_data.py
git commit -m "test: add polymorphic-schemas OpenAPI fixture"
```

## Task 10: Full-suite sanity check

**Files:** none (verification only)

**Interfaces:** none — this task only runs the project's standard gate
to confirm the new files integrate cleanly (formatting, typing, doctest
collection, full test run) before this plan is considered done.

- [ ] **Step 1: Run the project's standard test gate**

Run: `make test`
Expected: `hatch fmt --check && hatch run mypy && hatch test -c -vv` all
pass, ending with `Tests Successful`.

- [ ] **Step 2: Confirm the four new fixtures actually generate real
  model/client source**

Run:

```bash
hatch run hatch-test.py3.10:python - <<'PY'
from oapi.oas.model import OpenAPI
from oapi.model import ModelModule

for name in (
    "parameter-styles",
    "security-schemes",
    "multipart-request-body",
    "polymorphic-schemas",
):
    with open(f"tests/input-data/{name}.json") as io_:
        open_api = OpenAPI(io_)
    model_source = str(ModelModule(open_api))
    assert model_source
    print(name, "ModelModule OK", len(model_source), "chars")
PY
```

Expected: four `... ModelModule OK ...` lines, no exceptions.

- [ ] **Step 3: Commit (if Step 1 required any fixes)**

```bash
git add -A
git commit -m "test: fix formatting/typing issues from full-suite check"
```

(Skip this step if Step 1 passed with no changes needed.)

---

## Self-Review

**1. Spec coverage:** Every "New test infrastructure" item from
`docs/superpowers/specs/2026-08-01-test-coverage-design.md` is covered:
`tests/servers.py` (Tasks 1–4), `tests/conftest.py`'s generated-module
loader (Task 5), and all four new fixtures (Tasks 6–9). The spec's
`FlakyRequestHandler` and "fake OAuth2 token-endpoint handler" are
deliberately implemented as generic `sequences`/`handlers` primitives
(Tasks 2–3) rather than OAuth2-specific code, since no test in *this*
plan exercises OAuth2 — the later `client.py` runtime plan builds the
actual token-endpoint handler on top of this primitive using
`handlers={("POST", "/token"): my_token_handler}`, which Task 3 already
supports.

**2. Placeholder scan:** No "TBD"/"add appropriate error handling"/
"similar to Task N" language; every step has runnable code. All fixture
JSON, `servers.py`, and the `generated_module_loader` were executed
against the real `oapi` package (`hatch-test.py3.10`) before being
written into this plan — `sob.validate` passes on all four fixtures, and
both `ModelModule` and `ClientModule` generate real source from all
four without exceptions.

**3. Type consistency:** `ResponseKey = tuple[str, str]` and
`ResponseHandler = Callable[[RecordedRequest], Response]` are defined
once in Task 1/3 and reused verbatim in every later task's diff.
`generated_module_loader`'s signature (`Callable[[str, str], ModuleType]`
positionally, `source: str, module_name: str = "generated_module"`
by parameter name) is consistent between Task 5's interface note and its
test in Task 5 and the reference in Task 10.

---

**Plan complete and saved to
`docs/superpowers/plans/2026-08-01-test-infrastructure.md`.** Two
execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per
task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using
executing-plans, batch execution with checkpoints

**Which approach?**
