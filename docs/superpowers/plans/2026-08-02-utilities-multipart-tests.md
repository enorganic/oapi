# Utilities & Multipart Request Tests Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task-by-task. Steps
> use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bring `src/oapi/_utilities.py` (59% → ~100%) and
`src/oapi/_multipart_request.py` (31% → ~90%+) to real, integration-first
test coverage, per
`docs/superpowers/specs/2026-08-01-test-coverage-design.md`'s step 2
("self-contained, fast, cheap wins toward 100%").

**Architecture:** Two new test files, `tests/test_utilities.py` and
`tests/test_multipart_request.py`. `_utilities.py`'s pure functions are
tested directly (nothing to fake — they have no I/O), plus its
`deprecated` decorator is tested through the three *real* public aliases
that already use it (`oapi.oas.model.Link_`, `oapi.model.Module`,
`oapi.client.Module`) rather than a throwaway decorated function, so the
test also proves the library's actual deprecated-alias surface works.
`_multipart_request.py`'s wire-format correctness is verified against
the stdlib `email.parser` as an independent oracle, and its `Request`/
`MultipartRequest` classes are exercised end-to-end over a real socket
using the `http_test_server` infrastructure built in
`docs/superpowers/plans/2026-08-01-test-infrastructure.md` (already
merged into this branch as `tests/servers.py`). Three small module-level
helpers (`_headers`, `_data_bytes`, `_parts`) narrow `Data.headers`/
`Data.data`/`Part.parts` from their real `X | None` return types down
to `X` via `assert ... is not None` — these properties are only ever
`None` before the corresponding setter normalizes them (verified: after
`__init__`, `Data.headers` and `Part.parts` are never `None` at
runtime), so the assertion documents a real invariant rather than
papering over one; it's also what satisfies this project's mypy-strict
`disallow_untyped_defs` gate without loosening any type. Every local
variable in both files carries an explicit type annotation (not just
function signatures) — see Global Constraints.

**Tech Stack:** Python 3.10, `pytest`, stdlib `email`/`random`/`warnings`
(no new dependencies), `sob` (already a dependency), the existing
`tests/input-data/multipart-request-body.json` fixture (from the prior
plan — reused here, not recreated) and `tests/servers.py`'s
`http_test_server`.

## Global Constraints

- Line length 79 (ruff + black), enforced via `hatch fmt --check`.
- mypy strict on `tests/`: `disallow_untyped_defs`,
  `disallow_incomplete_defs` — every function/method signature fully
  annotated. All code in this plan was verified against a real
  `mypy --strict` run (not just the project's `hatch run mypy`, which
  fails to *sync* in this checkout on a pre-existing, unrelated
  `dependence~=1.4` issue — see the infrastructure plan's ledger).
  `Data.headers`, `Data.data`, and `Part.parts` are typed `X | None` on
  the real class, so every test that uses them goes through the
  `_headers`/`_data_bytes`/`_parts` helpers introduced in Tasks 5, 7,
  and 8 rather than accessing the properties directly.
- **Explicit type annotations on every local variable, not only
  function signatures.** This is a project-wide, user-stated preference
  applying beyond what mypy strict alone requires (mypy strict mandates
  annotated signatures; it does not require annotating a local like
  `data = Data(...)` — this plan does so anyway, throughout). Two narrow
  exceptions, both verified necessary rather than assumed:
  - Python does not support inline annotation on a `with ... as name:`
    context-manager target (e.g. `with warnings.catch_warnings(record=True) as caught:`,
    `with open(path) as io_:`) — there is no syntax for it, so these
    stay unannotated.
  - `email.message.Message.get_payload()` (used in Tasks 9-10) has a
    real, verified return type of
    `Message[str, str] | str | list[Message[str, str] | str] | Any`
    (confirmed via `reveal_type` against a real `mypy --strict` run) —
    narrower than that (e.g. `list[object]`) is a genuine mypy error,
    not a style choice, because `list` is invariant. The pattern used
    here is: leave `payloads = message.get_payload()` unannotated
    (correct inference), `assert isinstance(payloads, list)`, then bind
    the narrowed, explicitly-annotated `typed_payloads: list[Message[str, str]] = cast(...)`
    for everything used afterward.
- No new dependencies — stdlib + `pytest` + `sob` only.
- Python `~=3.10`.
- Tests run with `--doctest-modules` — no ambiguous `>>>` sequences in
  new test docstrings.
- Prefer real integration over mocks: no `unittest.mock`/`pytest-mock`
  anywhere in either new test file. Where true non-determinism must be
  made reproducible (the boundary-collision retry loop in Task 7), use
  `random.seed(N)` — real randomness made deterministic — never patch
  `random.choice` itself.
- **Imports go at the top of the file, grouped stdlib / third-party /
  first-party (this project's ruff config enforces `I001` import
  sorting).** Every task after Task 1/5 (file creation) adds new import
  lines to the existing top-of-file import block. You do not need to
  place them in perfect sorted order by hand — add the line(s) shown,
  anywhere in a sensible existing `import`/`from` group, then run
  `hatch fmt --formatter` (auto-sorts and reformats) followed by
  `hatch fmt --check` (must report `All checks passed!` /
  `N files already formatted`) before every commit in this plan. This
  is not optional — skipping it is what produces `E402`/`I001`
  failures.
- Verify commands: `hatch run hatch-test.py3.10:pytest tests/test_utilities.py tests/test_multipart_request.py -v`
  (the `hatch-test` env has `pytest` and this project installed; the
  bare `default` env in this checkout currently fails to sync — don't
  use it for `hatch run mypy`, and don't treat that sync failure as a
  real type error).
- Commit scope: this working tree has unrelated pre-existing staged
  files (`.claude/settings.json`, `.claude/skills/fableplan/SKILL.md`,
  `AGENTS.md`, `.gitignore`) belonging to other work-in-progress —
  **never** include them in a commit. A bare `git commit -m "..."`
  commits everything currently staged, not just what you just added —
  always commit with an explicit pathspec naming exactly the task's
  files: `git commit <exact-path(s)> -m "..."` (paths before `-m`).
  Never `git add -A`/`.`/`-u`, never `git reset` in any form to
  self-fix a mistake — if a commit's scope looks wrong, stop and report
  it rather than trying to fix it with git surgery.
- Known, out-of-scope, pre-existing issue (do not fix as part of this
  plan): a real `mypy --strict` run also flags
  `tests/servers.py:56: error: If x = b'abc' then f"{x}" ... [str-bytes-safe]`
  in the *prior* plan's `http_test_server` code
  (`f"http://{host}:{port}"` where `port`'s inferred type includes
  `bytes` per some `socket` typeshed overload). This predates this plan
  and is unrelated to `_utilities.py`/`_multipart_request.py` — note it
  if asked, but do not touch `tests/servers.py` in this plan.

---

## Task 1: `rename_parameters` — legacy-kwarg translation

**Files:**
- Create: `tests/test_utilities.py`

**Interfaces:**
- Consumes: `oapi._utilities.rename_parameters` (existing,
  `**old_new_parameter_names: str -> Callable[..., Callable[..., Any]]`).
- Produces: `tests/test_utilities.py` as a new file — later tasks in
  this plan append to it.

- [ ] **Step 1: Write the failing test**

Create `tests/test_utilities.py`:

```python
from __future__ import annotations

from oapi._utilities import rename_parameters


@rename_parameters(old_name="new_name")
def _greet(new_name: str, other: str = "x") -> str:
    return f"{new_name}-{other}"


def test_rename_parameters_translates_old_kwarg_to_new() -> None:
    assert _greet(old_name="a") == "a-x"


def test_rename_parameters_passes_through_new_kwarg_unchanged() -> None:
    assert _greet(new_name="b") == "b-x"


def test_rename_parameters_passes_through_other_kwargs() -> None:
    assert _greet(old_name="a", other="y") == "a-y"


if __name__ == "__main__":
    test_rename_parameters_translates_old_kwarg_to_new()
```

(No local variables in this task's tests to annotate — every value is
consumed directly in an `assert`.)

- [ ] **Step 2: Run test to verify it fails**

Run: `hatch run hatch-test.py3.10:pytest tests/test_utilities.py -v`
Expected: collects and PASSES immediately — `rename_parameters` already
exists and works; this task adds *coverage* of existing behavior, not
new behavior. There is no red step for this particular function; the
"failing" state to confirm is that before this file exists, the test
command errors with "no tests ran" / file-not-found.

- [ ] **Step 3: Run test to verify it passes**

Run: `hatch run hatch-test.py3.10:pytest tests/test_utilities.py -v`
Expected: PASS (3 tests). Verified against the real function:
`_greet(old_name="a")` → `"a-x"`, `_greet(new_name="b")` → `"b-x"`,
`_greet(old_name="a", other="y")` → `"a-y"`.

- [ ] **Step 4: Format and commit**

```bash
hatch fmt --formatter
hatch fmt --check
git add tests/test_utilities.py
git commit tests/test_utilities.py -m "test: add rename_parameters coverage"
```

## Task 2: `get_type_format_property` / `get_string_format_property`

**Files:**
- Modify: `tests/test_utilities.py`

**Interfaces:**
- Consumes: `oapi._utilities.get_type_format_property`,
  `oapi._utilities.get_string_format_property` (existing), `sob`'s
  property classes.

- [ ] **Step 1: Add imports and append the test**

Add these lines to the top import block (anywhere reasonable — `hatch
fmt --formatter` will sort them):

```python
import pytest
import sob

from oapi._utilities import (
    get_string_format_property,
    get_type_format_property,
)
```

(`rename_parameters` is already imported from `oapi._utilities` on its
own line from Task 1 — merge it into one `from oapi._utilities import
(...)` block with the two new names, don't leave two separate `from
oapi._utilities import` statements. `hatch fmt --formatter` will not
merge them for you.)

Append to `tests/test_utilities.py`:

```python
@pytest.mark.parametrize(
    ("type_", "expected_class"),
    [
        ("number", sob.NumberProperty),
        ("integer", sob.IntegerProperty),
        ("boolean", sob.BooleanProperty),
        ("file", sob.BytesProperty),
        ("array", sob.ArrayProperty),
        ("object", sob.Property),
    ],
)
def test_get_type_format_property_maps_simple_types(
    type_: str, expected_class: type[sob.abc.Property]
) -> None:
    property_: sob.abc.Property = get_type_format_property(type_)
    assert type(property_) is expected_class


@pytest.mark.parametrize(
    ("format_", "content_encoding", "expected_class"),
    [
        ("date-time", None, sob.DateTimeProperty),
        ("date", None, sob.DateProperty),
        ("byte", None, sob.BytesProperty),
        ("binary", None, sob.BytesProperty),
        ("base64", None, sob.BytesProperty),
        (None, None, sob.StringProperty),
        (None, "base64", sob.BytesProperty),
    ],
)
def test_get_string_format_property_maps_formats(
    format_: str | None,
    content_encoding: str | None,
    expected_class: type[sob.abc.Property],
) -> None:
    property_: sob.abc.Property = get_string_format_property(
        format_, content_encoding
    )
    assert type(property_) is expected_class


def test_get_type_format_property_string_delegates() -> None:
    property_: sob.abc.Property = get_type_format_property(
        "string", "date-time"
    )
    assert type(property_) is sob.DateTimeProperty


def test_get_type_format_property_none_type_without_media_or_encoding() -> (
    None
):
    property_: sob.abc.Property = get_type_format_property(None)
    assert type(property_) is sob.Property


def test_get_type_format_property_none_type_uses_default_type() -> None:
    property_: sob.abc.Property = get_type_format_property(
        None, default_type=sob.StringProperty
    )
    assert type(property_) is sob.StringProperty


def test_get_type_format_property_none_type_with_content_media_type() -> (
    None
):
    property_: sob.abc.Property = get_type_format_property(
        None, content_media_type="application/json"
    )
    assert type(property_) is sob.BytesProperty


def test_get_type_format_property_none_type_with_content_encoding() -> (
    None
):
    property_: sob.abc.Property = get_type_format_property(
        None, content_encoding="base64"
    )
    assert type(property_) is sob.BytesProperty


def test_get_type_format_property_unknown_type_raises() -> None:
    with pytest.raises(ValueError, match="Unknown schema type: bogus"):
        get_type_format_property("bogus")


def test_get_type_format_property_required_is_propagated() -> None:
    property_: sob.abc.Property = get_type_format_property(
        "string", required=True
    )
    assert property_.required is True
```

- [ ] **Step 2: Run test to verify it passes**

Run: `hatch run hatch-test.py3.10:pytest tests/test_utilities.py -v`
Expected: PASS (all tests so far, 23 total). Verified against the real
functions: every `(type_, expected_class)` and `(format_,
content_encoding, expected_class)` pair above was executed against
`oapi._utilities` directly and produced exactly the stated class; the
unknown-type case raises `ValueError: Unknown schema type: bogus`;
`required=True` propagates to `property_.required`.

- [ ] **Step 3: Format and commit**

```bash
hatch fmt --formatter
hatch fmt --check
git add tests/test_utilities.py
git commit tests/test_utilities.py -m "test: add get_type_format_property/get_string_format_property coverage"
```

## Task 3: `iter_distinct`

**Files:**
- Modify: `tests/test_utilities.py`

**Interfaces:**
- Consumes: `oapi._utilities.iter_distinct` (existing).

- [ ] **Step 1: Add import and append the test**

Add `iter_distinct` into the existing `from oapi._utilities import
(...)` block from Task 2 (now: `get_string_format_property,
get_type_format_property, iter_distinct, rename_parameters` — merge
`rename_parameters` in too if it's still on its own line from Task 1).

Append to `tests/test_utilities.py`:

```python
def test_iter_distinct_deduplicates_preserving_order() -> None:
    assert list(iter_distinct([1, 2, 1, 3, 2, 4])) == [1, 2, 3, 4]


def test_iter_distinct_empty_iterable() -> None:
    assert list(iter_distinct([])) == []
```

(No local variables to annotate — both assertions consume the
generator's result directly.)

- [ ] **Step 2: Run test to verify it passes**

Run: `hatch run hatch-test.py3.10:pytest tests/test_utilities.py -v`
Expected: PASS (25 total). Verified: `list(iter_distinct([1, 2, 1, 3, 2,
4]))` → `[1, 2, 3, 4]`.

- [ ] **Step 3: Format and commit**

```bash
hatch fmt --formatter
hatch fmt --check
git add tests/test_utilities.py
git commit tests/test_utilities.py -m "test: add iter_distinct coverage"
```

## Task 4: `deprecated` — via the three real public aliases

**Files:**
- Modify: `tests/test_utilities.py`

**Interfaces:**
- Consumes: `oapi.oas.model.Link_` / `oapi.oas.model.LinkObject`,
  `oapi.model.Module` / `oapi.model.ModelModule`, `oapi.client.Module` /
  `oapi.client.ClientModule`, `oapi.oas.model.OpenAPI` (all existing) —
  these three aliases are the *only* real usages of the `deprecated`
  decorator in this codebase today (confirmed: `rename_parameters` and
  a bare `@deprecated` are not applied anywhere else). Testing through
  them, rather than a throwaway decorated function, proves the
  library's actual deprecated surface works, not just the decorator in
  isolation.
- Consumes: `tests/input-data/multipart-request-body.json` (already
  exists from the prior plan — reused, not recreated) as the `OpenAPI`
  document `ClientModule`/`ModelModule` need.

- [ ] **Step 1: Add imports and append the test**

Add these lines to the top import block:

```python
import warnings
from pathlib import Path

from oapi.client import ClientModule
from oapi.client import Module as ClientModuleAlias
from oapi.model import ModelModule
from oapi.model import Module as ModelModuleAlias
from oapi.oas.model import Link_, LinkObject, OpenAPI
```

Append to `tests/test_utilities.py` (constants near the top of the
test-function section, then the three tests):

```python
TESTS_PATH: Path = Path(__file__).absolute().parent
MULTIPART_FIXTURE_PATH: Path = (
    TESTS_PATH / "input-data" / "multipart-request-body.json"
)


def test_deprecated_link_alias_warns_and_returns_link_object() -> None:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        link: LinkObject = Link_()
    assert len(caught) == 1
    assert issubclass(caught[0].category, DeprecationWarning)
    assert "oapi.oas.model.Link_" in str(caught[0].message)
    assert "oapi.oas.model.LinkObject" in str(caught[0].message)
    assert isinstance(link, LinkObject)


def test_deprecated_model_module_alias_warns_and_returns_model_module() -> (
    None
):
    with open(MULTIPART_FIXTURE_PATH) as io_:
        open_api: OpenAPI = OpenAPI(io_)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        model_module: ModelModule = ModelModuleAlias(open_api)
    assert len(caught) == 1
    assert issubclass(caught[0].category, DeprecationWarning)
    assert "oapi.model.Module" in str(caught[0].message)
    assert "oapi.ModelModule" in str(caught[0].message)
    assert isinstance(model_module, ModelModule)


def test_deprecated_client_module_alias_warns_and_returns_client_module(
    tmp_path: Path,
) -> None:
    with open(MULTIPART_FIXTURE_PATH) as io_:
        open_api: OpenAPI = OpenAPI(io_)
    model_module: ModelModule = ModelModule(open_api)
    model_path: Path = tmp_path / "model.py"
    model_path.write_text(str(model_module))
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        client_module: ClientModule = ClientModuleAlias(
            open_api, model_path=str(model_path)
        )
    assert len(caught) == 1
    assert issubclass(caught[0].category, DeprecationWarning)
    assert "oapi.client.Module" in str(caught[0].message)
    assert "oapi.ClientModule" in str(caught[0].message)
    assert isinstance(client_module, ClientModule)
```

Note: `with open(...) as io_:` and `with warnings.catch_warnings(...) as
caught:` are the documented exception from Global Constraints — Python
doesn't support annotating a `with ... as name:` target inline, so
those two stay unannotated; every other local (`link`, `open_api`,
`model_module`, `model_path`, `client_module`) is explicitly annotated.

Place the `TESTS_PATH`/`MULTIPART_FIXTURE_PATH` constants after the
imports and before the first test function in the file (i.e., move
them up, don't leave them appended at the very bottom below the
`_greet` helper) — `hatch fmt --formatter` does not reorder statements,
only imports, so put them in a sensible place yourself.

- [ ] **Step 2: Run test to verify it passes**

Run: `hatch run hatch-test.py3.10:pytest tests/test_utilities.py -v`
Expected: PASS (28 total). Verified against the real library: `Link_()`
emits exactly one `DeprecationWarning` with message `` `oapi.oas.model.Link_`
is deprecated and will be removed in oapi 3. Please use
`oapi.oas.model.LinkObject` instead. `` and returns a real
`LinkObject` instance; `ModelModuleAlias(open_api)` (loaded from the
real `multipart-request-body.json` fixture) emits the analogous
`oapi.model.Module`/`oapi.ModelModule` warning and returns a real
`ModelModule`; `ClientModuleAlias(open_api, model_path=...)` (given a
real, freshly-generated `model.py` written to `tmp_path`) emits the
analogous `oapi.client.Module`/`oapi.ClientModule` warning and returns a
real `ClientModule`.

- [ ] **Step 3: Format, verify with mypy if available, and commit**

```bash
hatch fmt --formatter
hatch fmt --check
git add tests/test_utilities.py
git commit tests/test_utilities.py -m "test: add deprecated-alias coverage via real public aliases"
```

The final `tests/test_utilities.py` (all of Tasks 1-4 combined) should
be 187 lines, `hatch fmt --check`-clean, and pass a `mypy --strict`
run with zero errors if you have a way to run it directly (the
project's own `hatch run mypy` is blocked by the known pre-existing
`dependence~=1.4` sync issue — see Global Constraints).

## Task 5: `Headers` — dict-protocol behavior

**Files:**
- Create: `tests/test_multipart_request.py`

**Interfaces:**
- Consumes: `oapi._multipart_request.Data`, `Headers` (existing).
- Produces: `tests/test_multipart_request.py` as a new file — later
  tasks in this plan append to it. Produces the `_headers(data: Data)
  -> Headers` module-level helper (asserts `data.headers is not None`
  and returns it) — every later task in this file that touches
  `.headers` uses this helper instead of the raw property, to satisfy
  mypy strict against the real `Headers | None` return type.

- [ ] **Step 1: Write the test**

Create `tests/test_multipart_request.py`:

```python
from __future__ import annotations

import pytest

from oapi._multipart_request import Data, Headers


def _headers(data: Data) -> Headers:
    headers: Headers | None = data.headers
    assert headers is not None
    return headers


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
```

Note: `test_headers_popitem_removes_and_returns_pair` cannot write
`key: str, value: str = _headers(data).popitem()` — Python doesn't
support annotating a tuple-unpacking assignment inline. Instead,
pre-declare both names on their own lines (`key: str` / `value: str`)
immediately before the unpacking assignment, as shown.

- [ ] **Step 2: Run test to verify it passes**

Run: `hatch run hatch-test.py3.10:pytest tests/test_multipart_request.py -v`
Expected: PASS (14 tests). Verified against the real library: header
keys are `.capitalize()`d (`"x-custom"` → `"X-custom"`), containment
checks are case-insensitive via the same capitalization,
`Headers.get(key)` without a default re-raises the real `KeyError`,
`Content-length` is always present in a `Data`'s (non-`Part`) header
iteration even though never explicitly set (computed from
`len(data or b"")`), and `Content-type` is absent unless the request is
a `Part` with a non-empty `parts` list (covered directly in Task 7 —
this task only asserts its absence on plain `Data`, checked via
`dict(data.headers.items())` since `Data` has no `.parts` attribute at
all).

- [ ] **Step 3: Format and commit**

```bash
hatch fmt --formatter
hatch fmt --check
git add tests/test_multipart_request.py
git commit tests/test_multipart_request.py -m "test: add Headers dict-protocol coverage"
```

## Task 6: `Data` — serialization and cache behavior

**Files:**
- Modify: `tests/test_multipart_request.py`

**Interfaces:**
- Consumes: `oapi._multipart_request.Data`, `Part` (existing).

- [ ] **Step 1: Add import and append the test**

Add `Part` to the existing `from oapi._multipart_request import Data,
Headers` line (now `Data, Headers, Part`).

Append to `tests/test_multipart_request.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it passes**

Run: `hatch run hatch-test.py3.10:pytest tests/test_multipart_request.py -v`
Expected: PASS (20 tests). Verified against the real library, including
the exact byte string for the JSON-serialized `Data` example
(`sob.serialize` renders `{"a": 1}` with a space after the colon, 8
bytes) and the real, confirmed cache-invalidation asymmetry between
`Data` and `Part`.

- [ ] **Step 3: Format and commit**

```bash
hatch fmt --formatter
hatch fmt --check
git add tests/test_multipart_request.py
git commit tests/test_multipart_request.py -m "test: add Data serialization and cache-behavior coverage"
```

## Task 7: `Part` — boundary computation and collision avoidance

**Files:**
- Modify: `tests/test_multipart_request.py`

**Interfaces:**
- Consumes: `oapi._multipart_request.Part` (existing), stdlib `random`.
- Produces: the `_data_bytes(data: Data) -> bytes` module-level helper
  (asserts `data.data is not None` and returns it), for the same
  mypy-strict reason as `_headers`.

- [ ] **Step 1: Add import and helper, then append the test**

Add `import random` to the top import block (stdlib group).

Add this helper next to `_headers` (near the top of the file, after the
imports):

```python
def _data_bytes(data: Data) -> bytes:
    value: bytes | None = data.data
    assert value is not None
    return value
```

Append to `tests/test_multipart_request.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it passes**

Run: `hatch run hatch-test.py3.10:pytest tests/test_multipart_request.py -v`
Expected: PASS (26 tests). Verified against the real library, including
the seeded collision scenario: with `random.seed(12345)`, the first
candidate boundary is `b'qK0QQPjSnXchAran'`; constructing data
containing that exact 16-byte string and re-seeding identically
produces a final boundary of `b'qK0QQPjSnXchAran7'` (17 bytes,
extending the original candidate by one real random character) which
does not appear anywhere in the data — proving the `while boundary in
data:` retry loop actually executed, using real randomness made
reproducible via seeding, not a mock of `random.choice`.

- [ ] **Step 3: Format and commit**

```bash
hatch fmt --formatter
hatch fmt --check
git add tests/test_multipart_request.py
git commit tests/test_multipart_request.py -m "test: add Part boundary computation and collision-avoidance coverage"
```

## Task 8: `Parts` — sequence protocol and cache invalidation

**Files:**
- Modify: `tests/test_multipart_request.py`

**Interfaces:**
- Consumes: `oapi._multipart_request.Part`, `Parts` (existing).
- Produces: the `_parts(part: Part) -> Parts` module-level helper
  (asserts `part.parts is not None` and returns it), for the same
  mypy-strict reason as `_headers`/`_data_bytes`.

- [ ] **Step 1: Add import and helper, then append the test**

Add `Parts` to the `from oapi._multipart_request import Data, Headers,
Part` line (now `Data, Headers, Part, Parts`).

Add this helper next to `_headers`/`_data_bytes`:

```python
def _parts(part: Part) -> Parts:
    parts: Parts | None = part.parts
    assert parts is not None
    return parts
```

Append to `tests/test_multipart_request.py`:

```python
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
```

Note: `test_parts_reverse_reorders_in_place`,
`test_parts_delitem_removes_item`, and `test_parts_setitem_replaces_item`
each split what could be a one-line tuple assignment
(`part_a, part_b = Part(data=b"a"), Part(data=b"b")`) into two
separately-annotated lines, since Python doesn't support annotating a
tuple-unpacking assignment inline (same reasoning as Task 5's
`popitem()` test).

- [ ] **Step 2: Run test to verify it passes**

Run: `hatch run hatch-test.py3.10:pytest tests/test_multipart_request.py -v`
Expected: PASS (33 tests). Verified against the real library: every
mutating `Parts` method (`append`, `clear`, `extend`, `reverse`,
`__delitem__`, `__setitem__`) resets the owning `Part`'s
`_boundary`/`_bytes` cache attributes to `None` as a real, observable
side effect (accessed via the documented private attribute `_boundary`
— hence the `# noqa: SLF001` matching this project's existing
convention for that pattern inside `_multipart_request.py` itself).

- [ ] **Step 3: Format and commit**

```bash
hatch fmt --formatter
hatch fmt --check
git add tests/test_multipart_request.py
git commit tests/test_multipart_request.py -m "test: add Parts sequence-protocol coverage"
```

## Task 9: Real multipart wire-format oracle test

**Files:**
- Modify: `tests/test_multipart_request.py`

**Interfaces:**
- Consumes: `oapi._multipart_request.Part` (existing), stdlib
  `email.message.Message`, `email.parser.BytesParser`,
  `email.policy.compat32`, `typing.cast`.

- [ ] **Step 1: Add imports and append the test**

Add these lines to the top import block:

```python
from email.message import Message
from email.parser import BytesParser
from email.policy import compat32
from typing import cast
```

Append to `tests/test_multipart_request.py`:

```python
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
```

Note on `payloads` being left unannotated: this is the documented
exception from Global Constraints, not an oversight. `message.get_payload()`'s
real return type (confirmed via `reveal_type` against a real
`mypy --strict` run) is
`Message[str, str] | str | list[Message[str, str] | str] | Any` — a
hand-written annotation narrower than that (e.g. `list[object]`) is a
genuine mypy error because `list` is invariant, not just a style
choice. Let mypy infer `payloads`' type correctly, narrow it with
`assert isinstance(payloads, list)`, then bind the explicitly-annotated
`typed_payloads: list[Message[str, str]]` via `cast(...)` for
everything used afterward — every other local in this test (`part_a`,
`part_b`, `top`, `message_bytes`, `message`, `typed_payloads`) is
explicitly annotated.

- [ ] **Step 2: Run test to verify it passes**

Run: `hatch run hatch-test.py3.10:pytest tests/test_multipart_request.py -v`
Expected: PASS (34 tests). Verified against the real library: assembling
a top-level `Part` with two sub-`Part`s and feeding the real
`Content-type` header plus real `.data` bytes to Python's stdlib
`email.BytesParser` produces `message.is_multipart() is True` with
exactly 2 payloads, each with the correct `Content-Disposition` and
decoded body — confirmed by direct execution, not asserted from theory.

- [ ] **Step 3: Format and commit**

```bash
hatch fmt --formatter
hatch fmt --check
git add tests/test_multipart_request.py
git commit tests/test_multipart_request.py -m "test: verify multipart wire format against stdlib email parser"
```

## Task 10: `Request` / `MultipartRequest` — real end-to-end HTTP

**Files:**
- Modify: `tests/test_multipart_request.py`

**Interfaces:**
- Consumes: `oapi._multipart_request.Request`, `MultipartRequest`
  (existing), `tests.servers.http_test_server`, `tests.servers.Response`,
  `tests.servers.RecordedRequest` (from
  `docs/superpowers/plans/2026-08-01-test-infrastructure.md`, already
  merged into this branch as `tests/servers.py`) — this is the one task
  in this plan that needs the local HTTP test server, since it's the
  only place actual network I/O is exercised.

- [ ] **Step 1: Add imports and append the test**

Add these lines to the top import block:

```python
import json
from urllib.request import urlopen

from servers import RecordedRequest, Response, http_test_server
```

Add `MultipartRequest, Request` to the existing `from
oapi._multipart_request import Data, Headers, Part, Parts` line (now:
`Data, Headers, MultipartRequest, Part, Parts, Request`).

Append to `tests/test_multipart_request.py`:

```python
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
```

Note: `Part` is already imported (Task 6); `Message`, `BytesParser`,
`compat32`, `cast` are already imported (Task 9) — do not re-import any
of them. `payloads` is left unannotated for the same documented reason
as Task 9. `recorded.headers["Content-Length"]` — capital `L` — is the
real key `http.server`'s request parser uses (confirmed by direct
execution: lowercase `Content-length` returns `None`/`KeyError` from
the recorded headers dict, which is a plain
`email.message.Message`-backed mapping that preserves the wire-format
casing, unlike this library's own `Headers` class which normalizes via
`.capitalize()`).

- [ ] **Step 2: Run test to verify it passes**

Run: `hatch run hatch-test.py3.10:pytest tests/test_multipart_request.py -v`
Expected: PASS (36 tests). Verified against the real library and a real
local socket: a plain `Request` with a dict `data` payload and
`Content-Type: application/json` is sent via `urlopen` to a real
`http_test_server`, and the server-recorded body round-trips through
`json.loads` to the original dict, with a correct real `Content-Length`
header. A `MultipartRequest` wrapping one file `Part` is sent the same
way; the server-recorded `Content-Type` header carries the real
generated boundary, and feeding the server's actual received body to
the stdlib `email` parser confirms it decodes to exactly the one part
sent, with the correct `Content-Disposition` and file contents.

- [ ] **Step 3: Run the full pair of new test files together**

Run: `hatch run hatch-test.py3.10:pytest tests/test_utilities.py tests/test_multipart_request.py -v`
Expected: all 28 + 36 = 64 tests from Tasks 1-10 pass together (no
cross-task interference — nothing in `tests/test_utilities.py` shares
state with `tests/test_multipart_request.py`).

- [ ] **Step 4: Format and commit**

```bash
hatch fmt --formatter
hatch fmt --check
git add tests/test_multipart_request.py
git commit tests/test_multipart_request.py -m "test: add Request/MultipartRequest end-to-end HTTP coverage"
```

The final `tests/test_multipart_request.py` (all of Tasks 5-10
combined) should be 427 lines, `hatch fmt --check`-clean, and pass a
`mypy --strict` run with zero errors (verified directly against this
exact plan's code before it was written down — the only other error a
real `mypy --strict tests/` run reports is the known, out-of-scope,
pre-existing `tests/servers.py:56` issue from the prior plan, listed in
Global Constraints).

## Task 11: Full-suite sanity check

**Files:** none (verification only)

- [ ] **Step 1: Run the project's standard test gate**

Run: `make test`
Expected: `hatch fmt --check && hatch run mypy && hatch test -c -vv` — if
`hatch run mypy` fails specifically at the dependency-*sync* step with a
`dependence~=1.4` resolution error (not an actual type error in code),
that's the same known pre-existing environment issue documented in the
prior plan — report it as such rather than treating it as a new
failure, and separately confirm `hatch fmt --check` and
`hatch test -c -vv` pass cleanly on their own.

- [ ] **Step 2: Confirm the coverage improvement**

Run: `hatch test -c && hatch run hatch-test.py3.10:coverage report -m --include="*/_utilities.py,*/_multipart_request.py"`
Expected: `_utilities.py` at or near 100%, `_multipart_request.py`
materially above its 31% baseline (target ~90%+; some lines may remain
uncovered — if any remaining gap looks reachable and valuable, note it
rather than silently accepting it).

- [ ] **Step 3: Commit (if Step 1 required any fixes)**

```bash
git add -A
git commit -m "test: fix formatting/typing issues from full-suite check"
```

(Skip if Step 1 passed with no changes needed. If you do need this
step, review `git status` first per the Global Constraints — never
stage the unrelated pre-existing files.)

---

## Self-Review

**1. Spec coverage:** Every function in `_utilities.py`
(`rename_parameters`, `get_string_format_property`,
`get_type_format_property`, `iter_distinct`, `deprecated`) has a task.
Every class in `_multipart_request.py` (`Headers`, `Data`, `Part`,
`Parts`, `Request`, `MultipartRequest`) has a task. The spec's called-out
approach for `_multipart_request.py` -- "real, unmocked, `email.parser`
as an oracle" and "end-to-end via `MultipartRequest` sent through
`urlopen`" -- are both present (Tasks 9-10). The spec's approach for
`deprecated` -- test via real usage rather than a synthetic decorated
function -- is followed in Task 4. The user's mid-plan "always use
explicit type annotation" instruction is reflected as a Global
Constraint and applied throughout every task's code, with the two
narrow, individually-verified exceptions (`with ... as` targets;
`email.message.get_payload()`'s real union return type) called out
inline rather than silently dropped.

**2. Placeholder scan:** No "TBD"/"add appropriate handling"/"similar to
Task N" language. Every step has runnable code. All test code in this
plan was executed against the real `oapi` package (via
`hatch-test.py3.10`) before being written here -- including the exact
byte strings, header values, warning messages, and the seeded
boundary-collision scenario. Beyond that first pass, the fully-assembled
contents of both files (all tasks combined, with explicit local-variable
annotations throughout) were placed at their real destination paths in
this checkout and verified: `hatch fmt --check` clean, a real
`mypy --strict` run clean (aside from the documented, out-of-scope
`tests/servers.py:56` issue), and a live `pytest` run of both files
together passing all 64 tests. Two real bugs were caught and fixed
during this process, not left in the plan: (a) an incorrect test
assertion (`test_part_boundary_does_not_collide_with_field_content`
originally, and incorrectly, assumed the boundary never appears in the
final rendered multipart bytes -- it does, as the delimiter -- corrected
to assert against field content instead); (b) an incorrect hand-written
annotation on `message.get_payload()`'s result (`list[object]` is not
assignable from the real `Message[str, str] | str | list[...] | Any`
union under mypy's invariant-list rules) -- corrected by leaving that
one variable to inference and casting into a separately-named,
explicitly-typed variable, which is now the documented pattern for
Tasks 9-10.

**3. Type consistency:** `_headers`, `_data_bytes`, and `_parts` are
each defined once (Tasks 5, 7, 8 respectively) and reused verbatim by
every later task that needs them, with no re-declaration or signature
drift. Import names introduced in one task (e.g. `Part` in Task 6,
`Parts` in Task 8) are added to the same shared `from
oapi._multipart_request import (...)` line and reused by later tasks
without renaming. Every local variable across both files carries the
same annotation for the same real type every time it recurs (e.g.
`data: Data`, `part: Part`, `top: Part`, `first`/`second: bytes` appear
dozens of times across tasks, always with the same type).

---

**Plan complete and saved to
`docs/superpowers/plans/2026-08-02-utilities-multipart-tests.md`.** Two
execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per
task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using
executing-plans, batch execution with checkpoints

**Which approach?**
