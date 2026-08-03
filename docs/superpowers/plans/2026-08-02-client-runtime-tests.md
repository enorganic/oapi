# Client Runtime Tests Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task-by-task. Steps
> use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bring `src/oapi/client.py`'s `Client` class (lines 1067-1929 --
the base class for generated OpenAPI clients: construction/validation,
pickling, authentication, and the real request/response cycle) from 40%
to essentially full coverage, per
`docs/superpowers/specs/2026-08-01-test-coverage-design.md`'s step 5
("`client.py` `Client` runtime"). This plan follows
`docs/superpowers/plans/2026-08-02-client-argument-formatting-tests.md`
(the pure-function layer below the class, now at 38%) and precedes the
`ClientModule` code-generation plan (the largest remaining chunk,
covering lines 2284-3963).

**Architecture:** Four new test files:

- `tests/test_client_init_and_pickling.py` -- `__init__` validation
  (`api_key_in`, `oauth2_flows` translation/validation, URL scheme
  checks), default property values, the lazily-built/cached `_opener`
  property, `__getstate__`/`__setstate__`, a real `pickle` round-trip,
  and the deprecated `_resurrect_client` classmethod.
- `tests/test_client_authentication.py` -- `_authenticate_request`
  (Basic, Bearer), `_api_key_authenticate_request` (header/query/cookie
  variants and their error paths), and `_oauth2_authenticate_request`'s
  warning-emitting branches for unconfigured/unimplemented flows. All
  of these are tested as pure header/URL mutations on a real
  `urllib.request.Request`, no network needed.
- `tests/test_client_request_runtime.py` -- the real, network-backed
  `Client.request()`/`Client._request()` cycle against
  `tests/servers.py`'s `http_test_server`: plain GET/POST, query-string
  building, header merging, absolute-URL passthrough, the
  backward-compatible `data`-as-`json` calling convention, retry
  integration, `HTTPError` handling, `echo`/`logger` callbacks, and a
  direct unit test of `_get_request_response_callback`'s error path
  (real code, but never actually invoked with a real error anywhere in
  `Client` itself -- see Global Constraints).
- `tests/test_client_oauth2_flows.py` -- the real, network-backed
  OAuth2 password and client-credentials flows (token fetch, caching,
  `scope`, redirect-on-error, and each flow's own `RuntimeError`
  validation), OIDC token-URL discovery, and two tests that document a
  real, verified, unfixed bug (see Global Constraints).

As with the prior plan in this initiative, every test below was already
written and independently verified against the real library, `pytest`,
`mypy --strict`, and `hatch fmt --check` before this document was
drafted -- so each task is a single "create this already-correct file"
step, not an incremental build-up.

**Tech Stack:** Python 3.10, `pytest`, stdlib (`pickle`, `warnings`,
`contextlib`, `io`, `logging`, `json`), `tests/servers.py`'s
`http_test_server` (from the infrastructure plan).

## Global Constraints

- Line length 79 (ruff + black), enforced via `hatch fmt --check`.
- mypy strict on `tests/`: explicit type annotations on every local
  variable, per this project's standing preference. All code verified
  against a real `hatch run mypy --strict --ignore-missing-imports`
  run. One new, narrowly-scoped exception beyond the two already
  established (`with ... as name:` targets; a hand-written annotation
  that would be a real mypy error against a complex inferred type):
  `Client.oauth2_flows`'s own declared type in the real source is `(
  typing.Literal["authorizationCode", ...] | None)` -- a single
  `Literal`, not a `tuple` of them, even though `__init__` always
  assigns it a tuple (the source itself marks this assignment
  `# type: ignore`). Comparing it to a tuple is therefore a real,
  pre-existing mypy `comparison-overlap` error, silenced the same way
  the source silences its own assignment.
- Prefer real integration over mocks: no `unittest.mock`/`pytest-mock`
  anywhere in any of the four new files. Every authentication test
  builds a real `urllib.request.Request` and inspects its real,
  mutated headers/URL. Every network-backed test uses the real
  `http_test_server`, never a fake transport.
- **Two verified, real, non-obvious behaviors documented rather than
  "fixed" (do not deviate from the specified test code trying to make
  them "more correct")**:
  1. **A real, reproducible bug**: `_request_oauth2_client_credentials_
     authorization` (client.py:1640-1643) and `_get_oauth2_token_url`'s
     OIDC-discovery branch (client.py:1590) both pass `timeout=self.
     timeout` straight through to the opener with **no fallback** for
     `self.timeout == 0` (the `Client` default -- contrast with
     `_request_oauth2_password_authorization`, which correctly falls
     back via `self.timeout or inspect.signature(...).default`).
     Python's `socket` module treats `settimeout(0)` as "set the
     socket to non-blocking mode", not "no timeout", so `socket.
     connect()` returns immediately without completing --
     `_request_oauth2_client_credentials_authorization()` and
     `_get_oauth2_token_url()`'s discovery call both raise `OSError`
     (`BlockingIOError: [Errno 36] Operation now in progress` on this
     machine) for **every real network call**, unless the `Client` was
     constructed with an explicit, non-zero `timeout`. Verified
     directly and repeatedly against a real local server (not a
     network flake -- the identical configuration with `timeout=30`
     succeeds every time). This means the OAuth2 client-credentials
     flow and OIDC discovery are both broken by default for any
     `Client` that doesn't explicitly set `timeout`. `tests/
     test_client_oauth2_flows.py` documents this with two dedicated
     tests (`test_oauth2_client_credentials_flow_with_default_timeout_
     fails`, `test_get_oauth2_token_url_with_default_timeout_fails`)
     asserting the real `OSError`, and uses an explicit `timeout=30` in
     every other test of these two flows to get real, working coverage
     of the surrounding logic (token caching, `scope`, redirect
     handling) despite the bug. **This is a real functional defect in
     `oapi`, flagged to the user directly -- not something this
     test-only initiative fixes.**
  2. `_get_request_response_callback(error=...)`'s ERROR-level-logging
     and exception-text-appending branch is real, callable code, but
     grepping the whole `Client` class shows it is **never** invoked
     with a real `error` argument anywhere -- `_request`'s only
     `except HTTPError` handler calls `sob.errors.append_exception_
     text` directly, not through this callback. `tests/
     test_client_request_runtime.py`'s
     `test_get_request_response_callback_error_path_logs_and_appends_text`
     exercises it as a direct unit test of the method itself.
- **A third real bug, found during final review, and a correction to
  this plan's own earlier "dead code" claim.** An earlier draft of this
  plan claimed `Client._request`'s `if not isinstance(response, sob.
  abc.Readable): raise TypeError(response)` (line 1919) was genuinely
  dead, reasoning that `self._opener.open(...)` always returns a real
  `http.client.HTTPResponse` (which always has `.read()`). **That
  reasoning missed a real, reachable path**: `_assemble_request`'s
  URL-scheme guard (the `http`/`https`-only check) lives *only* in its
  non-multipart branch -- the multipart branch returns early via
  `MultipartRequest(...)` before that guard ever runs. So a
  `multipart=True` request with a non-HTTP URL (e.g. `file://...`)
  reaches a real `FileHandler`, which returns a real
  `urllib.response.addinfourl` -- an object `sob.abc.Readable` does
  *not* recognize (its structural check requires a class-level `read`
  method; `addinfourl` only proxies one through `__getattr__`). This
  was caught by the opus final-branch review, independently
  re-confirmed live by the controller (`Client(url="http://x").request
  ("file://<real temp file>", "POST", data={"field": b"x"},
  multipart=True, headers={"Content-encoding": "identity"})` really
  does raise `TypeError` at line 1919), and is now covered by
  `test_request_rejects_a_non_readable_response` in `tests/
  test_client_request_runtime.py` (added post-review) rather than left
  as a wrong "dead code" claim. This is the **third** time in this
  initiative a "must be dead/unreachable" claim was wrong -- see the
  same warning already recorded for the references/model-validation
  plan and the client-argument-formatting plan (its line 465). Treat
  this as a hard-learned, standing pattern: trace *every* branch that
  could reach a given line, including branches (like `multipart=True`)
  that bypass an earlier guard, before asserting something is dead.
- **A fourth real bug, found during final review: multipart requests
  are completely broken.** Every `Client.request(..., multipart=True)`
  call crashes with `KeyError: 'Content-encoding'`. `_request_callback`
  (client.py:1514) calls `request.headers.get("Content-encoding")`
  expecting ordinary `dict.get` semantics (`None` when the key is
  absent), but a `MultipartRequest`'s `.headers` is a custom `Headers`
  object (`src/oapi/_multipart_request.py`) whose `.get()` defaults to
  a `sob.UNDEFINED` sentinel and *re-raises* `KeyError` when no
  explicit `default` argument is passed and the key is missing. Since
  an ordinary multipart request doesn't set a `Content-encoding`
  header, this fires on essentially every real multipart upload made
  through `Client.request()`. Confirmed live against a real
  `http_test_server`. Documented (not fixed, per this test-only
  initiative's scope) in `test_request_multipart_crashes_missing_
  content_encoding_header`, added post-review. **This is a
  significant, currently-unfixed functional defect in `oapi` --
  flagged directly to the user, not just recorded here.**
- A relative `Location` header (e.g. `/token2` rather than an absolute
  URL) breaks both OAuth2 flows' redirect-follow branches -- the code
  uses the header value directly as the next request's full URL with
  no relative-URL resolution, and `urllib.request.Request` requires an
  absolute URL. This plan's redirect tests use the real
  `http_test_server`'s own base URL to build an absolute `Location`
  value, matching how a real server's `Location` header would normally
  be absolute.
- Verify commands: `hatch run hatch-test.py3.10:pytest
  tests/test_client_init_and_pickling.py
  tests/test_client_authentication.py
  tests/test_client_request_runtime.py tests/test_client_oauth2_flows.py
  -v` (65 tests total: 15 + 13 + 19 + 18, after two tests were added to
  `tests/test_client_request_runtime.py` post-final-review -- see the
  Self-Review section). `hatch run mypy --strict
  --ignore-missing-imports <file>` per file -- expect exactly one
  pre-existing, unrelated finding on `tests/servers.py:56`
  (`[str-bytes-safe]`, from the infrastructure plan) whenever
  `servers.py` is imported transitively; nothing else.
- Commit scope: this working tree has unrelated pre-existing staged
  files (`.claude/settings.json`, `.claude/skills/fableplan/SKILL.md`,
  `AGENTS.md`, `.gitignore`) belonging to other work-in-progress --
  **never** include them in a commit. Never a bare `git commit -m
  "..."` -- always `git commit <exact-path(s)> -m "..."` (paths before
  `-m`). Never `git add -A`/`.`/`-u`, never `git reset` in any form to
  self-fix a mistake -- if a commit's scope looks wrong, stop and
  report it. Never touch `tests/servers.py` (a pre-existing, documented,
  out-of-scope `mypy` finding lives there; do not "fix" it).
- Known, out-of-scope, pre-existing issue: running the full suite
  (`hatch test -c` or `hatch run hatch-test.py3.10:pytest tests/`) has
  the unrelated, pre-existing side effect of `test_languagetool`
  re-downloading and overwriting `tests/input-data/languagetool-
  swagger.json`; run `git checkout -- tests/input-data/languagetool-
  swagger.json` afterward if you ran the full suite, before checking
  `git status --porcelain`.

---

## Task 1: `tests/test_client_init_and_pickling.py`

**Files:**
- Create: `tests/test_client_init_and_pickling.py`

**Interfaces:**
- Consumes: `oapi.client.Client` (existing).
- Produces: `tests/test_client_init_and_pickling.py`, 15 tests.

- [ ] **Step 1: Write the test file**

Create `tests/test_client_init_and_pickling.py`:

```python
from __future__ import annotations

import pickle
import warnings
from http.cookiejar import CookieJar
from urllib.request import OpenerDirector

import pytest

from oapi.client import Client


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
```

- [ ] **Step 2: Verify**

Run:
```bash
hatch run hatch-test.py3.10:pytest tests/test_client_init_and_pickling.py -v
hatch run mypy --strict --ignore-missing-imports tests/test_client_init_and_pickling.py
hatch fmt --formatter
hatch fmt --check
```
Expected: 15 passed (12 test functions, one parametrized ×4 for the
URL-scheme-validation cases across `url`/`oauth2_authorization_url`/
`oauth2_token_url`/`oauth2_refresh_url`); mypy `Success: no issues
found in 1 source file`; `hatch fmt --check` clean.

- [ ] **Step 3: Commit**

```bash
git add tests/test_client_init_and_pickling.py
git commit tests/test_client_init_and_pickling.py -m "test: add coverage for Client construction, validation, and pickling"
```

## Task 2: `tests/test_client_authentication.py`

**Files:**
- Create: `tests/test_client_authentication.py`

**Interfaces:**
- Consumes: `oapi.client.Client` (existing).
- Produces: `tests/test_client_authentication.py`, 13 tests.

- [ ] **Step 1: Write the test file**

Create `tests/test_client_authentication.py`:

```python
from __future__ import annotations

import warnings
from urllib.request import Request

import pytest

from oapi.client import Client


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
```

- [ ] **Step 2: Verify**

Run:
```bash
hatch run hatch-test.py3.10:pytest tests/test_client_authentication.py -v
hatch run mypy --strict --ignore-missing-imports tests/test_client_authentication.py
hatch fmt --formatter
hatch fmt --check
```
Expected: 13 passed; mypy `Success: no issues found in 1 source file`;
`hatch fmt --check` clean. Every header/URL assertion was produced by
actually calling the real `_authenticate_request`/
`_api_key_authenticate_request`/`_oauth2_authenticate_request` methods
against a real `Request`, including the "Basic then Bearer, Bearer
wins" precedence (both configured together) and the direct-attribute-
mutation path that bypasses `__init__`'s `api_key_in` validation.

- [ ] **Step 3: Commit**

```bash
git add tests/test_client_authentication.py
git commit tests/test_client_authentication.py -m "test: add coverage for Client authentication (basic, bearer, api key, oauth2 warnings)"
```

## Task 3: `tests/test_client_request_runtime.py`

**Files:**
- Create: `tests/test_client_request_runtime.py`

**Interfaces:**
- Consumes: `oapi.client.Client` (existing). `tests/servers.py`'s
  `Response`, `http_test_server` (existing, from the infrastructure
  plan).
- Produces: `tests/test_client_request_runtime.py`, 19 tests (17 as
  originally written, plus two added post-final-review -- see
  Self-Review).

- [ ] **Step 1: Write the test file**

Create `tests/test_client_request_runtime.py`:

```python
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
```

- [ ] **Step 2: Verify**

Run:
```bash
hatch run hatch-test.py3.10:pytest tests/test_client_request_runtime.py -v
hatch run mypy --strict --ignore-missing-imports tests/test_client_request_runtime.py
hatch fmt --formatter
hatch fmt --check
```
Expected: 17 passed in roughly 10 seconds (the real-time cost of one
retry test sleeping ~2 seconds once, plus ~16 real `http_test_server`
startups); mypy `Success: no issues found in 1 source file`; `hatch fmt
--check` clean.

- [ ] **Step 3: Commit**

```bash
git add tests/test_client_request_runtime.py
git commit tests/test_client_request_runtime.py -m "test: add coverage for Client.request's real request/response cycle"
```

## Task 4: `tests/test_client_oauth2_flows.py`

**Files:**
- Create: `tests/test_client_oauth2_flows.py`

**Interfaces:**
- Consumes: `oapi.client.Client` (existing). `tests/servers.py`'s
  `Response`, `http_test_server` (existing).
- Produces: `tests/test_client_oauth2_flows.py`, 18 tests.

- [ ] **Step 1: Write the test file**

Create `tests/test_client_oauth2_flows.py`:

```python
from __future__ import annotations

import json as json_module
from urllib.error import HTTPError

import pytest
from servers import Response, http_test_server

from oapi.client import Client


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
```

- [ ] **Step 2: Verify**

Run:
```bash
hatch run hatch-test.py3.10:pytest tests/test_client_oauth2_flows.py -v
hatch run mypy --strict --ignore-missing-imports tests/test_client_oauth2_flows.py
hatch fmt --formatter
hatch fmt --check
```
Expected: 18 passed in roughly 5 seconds; mypy `Success: no issues
found in 1 source file`; `hatch fmt --check` clean. This includes the
two bug-documenting tests from Global Constraints -- both assert a real
`OSError` (`pytest.raises(OSError)`), not a mock.

- [ ] **Step 3: Commit**

```bash
git add tests/test_client_oauth2_flows.py
git commit tests/test_client_oauth2_flows.py -m "test: add coverage for Client OAuth2 password/client-credentials flows and OIDC discovery"
```

## Task 5: Whole-plan verification

**Files:**
- None modified (verification only).

- [ ] **Step 1: Run every new file together, plus the full existing suite**

```bash
hatch run hatch-test.py3.10:pytest tests/test_client_init_and_pickling.py tests/test_client_authentication.py tests/test_client_request_runtime.py tests/test_client_oauth2_flows.py -v
hatch run hatch-test.py3.10:pytest tests/ -q
git checkout -- tests/input-data/languagetool-swagger.json
```
Expected: 65 passed for the four new files together (63 as originally
authored, plus two added post-final-review -- see Self-Review); 339
passed for the full suite (274 before this plan's tests existed, plus
65).

- [ ] **Step 2: Confirm the coverage delta**

```bash
hatch run hatch-test.py3.10:coverage run -m pytest tests/test_client_argument_formatting.py tests/test_client_request_assembly.py tests/test_client_retry_and_encoding.py tests/test_client_pickling.py tests/test_client_init_and_pickling.py tests/test_client_authentication.py tests/test_client_request_runtime.py tests/test_client_oauth2_flows.py -q
hatch run hatch-test.py3.10:coverage report -m --include="*/client.py"
```
Expected: `src/oapi/client.py` moves from 40% (this plan's starting
point, itself already up from 38% thanks to `test_model.py` indirectly
exercising some of the `Client` class) to roughly 54%. Within the
`Client` class itself (lines 1067-1929), line 1919 -- initially
believed dead, corrected during final review (see Global Constraints)
-- is now covered too, via the two tests added post-review
(`test_request_multipart_crashes_missing_content_encoding_header`,
`test_request_rejects_a_non_readable_response`); nothing in the class
should remain in "Missing".

- [ ] **Step 3: Update project memory**

Update the `project-oapi-test-coverage-initiative` memory file to note
this plan complete and move to the next step (the `ClientModule`
code-generation plan), per the standing blanket-execution-approval
instruction -- no user confirmation needed for this step. Make sure the
memory update prominently notes the real `timeout=0` bug from Global
Constraints, since it's a genuine defect worth surfacing beyond just
this plan document.

---

## Self-Review

**1. Spec coverage:** The spec's step 5 ("`client.py` `Client` runtime")
is fully addressed: `__init__`'s validation and property assignment,
pickling (`__getstate__`/`__setstate__`, a real `pickle` round-trip,
the deprecated `_resurrect_client`), every authentication scheme
(Basic, Bearer, API key ×3 locations, OAuth2 password, OAuth2
client-credentials, OIDC discovery, and the warning-only stub flows),
the real request/response cycle (`request()`/`_request()`, retry
integration, error handling, echo/logger callbacks), and the `_opener`
property's lazy caching all have tests. The spec's explicit mention of
"API key + OAuth2 auth" and "pickling" are both covered by dedicated
files (Tasks 2 and 4; Task 1 respectively).

**2. Placeholder scan:** No "TBD"/"add appropriate handling"/"similar to
Task N" language. Every line of test code in every task was executed
against the real library before being written into this document,
including several rounds of fixing genuine test-authoring mistakes
(a `dict`-splat pattern that `mypy --strict` rejected against
`Client.__init__`'s keyword-only signature in Task 4's two
`missing_kwarg`-parametrized tests, restructured into explicit
per-case tests instead; a relative `Location` header that broke the
redirect-follow tests until an absolute URL was used, matching Global
Constraints' documented note about that branch). Three genuine
*source* bugs (not test bugs) were discovered and are documented, not
"fixed": the `timeout=0` default breaking both the OAuth2
client-credentials flow and OIDC discovery, and -- found post-review,
after the four tasks below had already landed -- the multipart
`Content-encoding` `KeyError` and the corrected line-1919 finding
(Global Constraints; two new tests were added directly to `tests/
test_client_request_runtime.py` to cover both, outside the normal
per-task flow, since they surfaced during the final whole-branch
review rather than during initial authoring). All three are flagged
directly to the user, not just documented here, since unlike this
initiative's earlier "documented, not fixed" findings (dict-iteration
quirks, a broken multi-encoding branch), these silently break whole
request paths (an auth flow, and all multipart uploads) for realistic
configurations. No line in the `Client` class remains uncovered.

**3. Type consistency:** Each of the four files declares its own
complete import block. `Client` is imported identically wherever
needed. `Response`/`http_test_server` from `tests/servers.py` are
imported the same way Tasks 3-4 of the prior plan already established.
The one new, narrowly-scoped mypy exception (`oauth2_flows`'s
tuple-vs-`Literal` comparison) is documented in Global Constraints and
used nowhere else.

---

**Plan complete and saved to
`docs/superpowers/plans/2026-08-02-client-runtime-tests.md`.**
Per the standing blanket authorization for this initiative
([[feedback-autonomous-plan-execution]]), proceeding directly to
subagent-driven execution on branch `test-coverage` without further
confirmation.
