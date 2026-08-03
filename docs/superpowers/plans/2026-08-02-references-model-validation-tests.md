# References & Model Validation Tests Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task-by-task. Steps
> use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bring `src/oapi/oas/references.py` (79% → ~98%) and the
hand-written validation hooks in `src/oapi/oas/model.py` (92% → ~95%,
file-wide) to real, integration-first test coverage, per
`docs/superpowers/specs/2026-08-01-test-coverage-design.md`'s step 3
("self-contained, no server needed except the one HTTP-`$ref` test").

**Architecture:** Two new test files, `tests/test_references.py` and
`tests/test_oas_model_hooks.py`. `references.py`'s happy-path reference
resolution is already exercised indirectly by `tests/test_model.py`'s
`test_openapi_examples` (which calls `Resolver(...).dereference()` on
real-world OpenAPI documents) — this plan targets the *error* and
*edge-case* paths that well-formed real-world specs never trigger:
malformed/self-referencing/empty-ref documents built directly with
`oapi.oas.model` classes, real multi-document HTTP resolution (via the
`http_test_server` infrastructure from
`docs/superpowers/plans/2026-08-01-test-infrastructure.md`, already
merged into this branch), and `resolve_reference()` — which had *zero*
prior coverage. `oas/model.py`'s targets are its hand-written
`after_validate`/`after_unmarshal`/`before_setitem` hooks near the end
of the file (`_schema_after_validate`, `_parameter_after_validate`,
`_reference_after_unmarshal`, `_add_object_property`) — real validation
logic, not the surrounding generated constructor boilerplate (which
this plan deliberately does not chase; see Global Constraints).

**Tech Stack:** Python 3.10, `pytest`, stdlib (no new dependencies),
`sob` (already a dependency), `tests/servers.py`'s `http_test_server`
(one task only).

## Global Constraints

- Line length 79 (ruff + black), enforced via `hatch fmt --check`.
- mypy strict on `tests/`: `disallow_untyped_defs`,
  `disallow_incomplete_defs`, and — per this project's standing
  preference — **explicit type annotations on every local variable**,
  not only function signatures. All code in this plan was verified
  against a real `mypy --strict` run (not the project's own `hatch run
  mypy`, which fails to *sync* in this checkout on a pre-existing,
  unrelated `dependence~=1.4` issue).
- No new dependencies — stdlib + `pytest` + `sob` only.
- Python `~=3.10`.
- Prefer real integration over mocks: no `unittest.mock`/`pytest-mock`
  anywhere in either new test file. Malformed/edge-case OpenAPI
  documents are built as real `oapi.oas.model` object graphs (or real
  JSON dicts passed through the real `OpenAPI(...)` constructor), never
  faked. The one test needing genuine network I/O uses the real
  `http_test_server` from the prior infrastructure plan.
- **Imports go at the top of the file** (this project's ruff config
  enforces `I001` import sorting). Add new import lines to the existing
  top-of-file block in each task, then run `hatch fmt --formatter`
  (auto-sorts) followed by `hatch fmt --check` before every commit —
  not optional.
- Private members are imported and called directly where that's the
  only way to reach real, reachable-but-not-currently-publicly-wired
  code (e.g. `_Document`, `_reference_after_unmarshal`,
  `_schema_after_validate`). This mirrors the pattern already used for
  `tests/test_model.py` (which imports `_urlopen` from
  `oapi.oas.references`) and is not a project-specific new convention.
- **Two verified, real, non-obvious behaviors this plan's tests
  document rather than "fix" (do not treat as bugs, do not deviate from
  the specified test code trying to make them "more correct")**:
  1. `_Document.dereference(model, recursive=True)` — the setting every
     current public caller uses — silently **swallows**
     `OAPIReferenceLoopError` rather than raising it (see
     `dereference`'s `except OAPIReferenceLoopError: if not recursive:
     raise`). The error only propagates when `recursive=False`, which
     no public method currently passes. Task 3 tests both: the real,
     reachable raise (calling `_Document.dereference` directly with
     `recursive=False`) and the real, current swallow-and-continue
     behavior (via the public `Resolver.dereference()`).
  2. `Reference.summary` and `Reference.description` are **already
     pre-declared properties** on the generated `Reference` class
     (confirmed via `sob.read_object_meta(Reference).properties` —
     `['ref', 'summary', 'description']`), so they do *not* exercise
     `_add_object_property`'s "this is a genuinely new property"
     branch. Task 10 uses an `x-`-prefixed key (OpenAPI's own
     convention for arbitrary extensions) instead.
- **`src/oapi/oas/model.py:6748-6749` (the `except KeyError: ref = None`
  lines inside `_reference_after_unmarshal`) is dead code for
  `Reference`, not a coverage-tool bug** — an earlier draft of this
  plan wrongly attributed the "missing" report for these two lines to a
  `coverage.py` measurement quirk. That was wrong: verified directly
  (`Reference()["$ref"]` returns `None`, it does not raise `KeyError`,
  because `sob` returns `None` for a declared-but-unset property rather
  than raising), the `try` block's `ref = typing.cast(str,
  data["$ref"])` simply assigns `None` and succeeds — the `except
  KeyError:` handler never runs for this or any other `Reference`
  input, since `$ref` is always a declared property on the class.
  `coverage.py`'s "missing" report for 6748-6749 was accurate the whole
  time. Task 10's test (`test_reference_after_unmarshal_requires_a_ref_attribute`)
  still correctly asserts the real, resulting `ValueError` — only the
  *mechanism* described in its docstring was wrong, and has been
  corrected to match this explanation. This branch is in the same
  category as the acknowledged-dead `6721` branch below: real code,
  genuinely unreachable under the current `sob` behavior, not worth
  chasing further.
- **Deliberately out of scope for this plan** — the *other* remaining
  gaps in `oas/model.py` (`325-336, 406-430, 533, 964, 1377-1385, 2698,
  3009, 4385-4405`) are generated constructor-body boilerplate
  (`self.x: ... = x` assignments for classes like `Discriminator`/
  `Encoding` that no current test happens to instantiate with those
  specific kwargs) — real code, but low-value, tautological coverage
  (testing that a generated `__init__` assigns its own parameters).
  `references.py:79-80` (the `except ImportError: pass` branch requiring
  `pyyaml` to be genuinely absent) and `references.py:202-203`/`313`
  (a `None`-metadata branch requiring a schema-less `sob.Object`, and an
  effectively-unreachable defensive `RuntimeError`) are similarly
  excluded — each was investigated and found to require either
  destabilizing the shared test environment (uninstalling a real
  dependency) or fabricating a scenario with no real-world trigger.
  `oas/model.py:6721` (`_add_object_property`'s `if object_meta.properties
  is None:` branch) is dead code specifically for `Reference` (its
  properties are never `None` — see the second bullet above); note it
  if asked, don't chase it.
- Verify commands: `hatch run hatch-test.py3.10:pytest tests/test_references.py tests/test_oas_model_hooks.py -v`
  (the `hatch-test` env has `pytest` and this project installed; the
  bare `default` env fails to sync — don't use it for `hatch run mypy`,
  and don't treat that sync failure as a real type error).
- Commit scope: this working tree has unrelated pre-existing staged
  files (`.claude/settings.json`, `.claude/skills/fableplan/SKILL.md`,
  `AGENTS.md`, `.gitignore`) belonging to other work-in-progress —
  **never** include them in a commit. Never a bare `git commit -m
  "..."` — always `git commit <exact-path(s)> -m "..."` (paths before
  `-m`). Never `git add -A`/`.`/`-u`, never `git reset` in any form to
  self-fix a mistake — if a commit's scope looks wrong, stop and report
  it.
- Known, out-of-scope, pre-existing issue: a real `mypy --strict` run
  also flags `tests/servers.py:56` (`[str-bytes-safe]`, from the
  infrastructure plan) — unrelated to this plan's files, don't touch
  `tests/servers.py`.

---

## Task 1: `Resolver`/`_Document` construction validation

**Files:**
- Create: `tests/test_references.py`

**Interfaces:**
- Consumes: `oapi.oas.references.Resolver`, `_Document` (existing),
  `oapi.oas.model.OpenAPI` (existing).
- Produces: `tests/test_references.py` as a new file — later tasks in
  this plan append to it. Produces the `_openapi(data: dict[str,
  typing.Any]) -> OpenAPI` module-level helper, used by every later
  task to build a real `OpenAPI` document from a plain dict literal.

- [ ] **Step 1: Write the test**

Create `tests/test_references.py`:

```python
from __future__ import annotations

import typing
from pathlib import Path

import pytest
import sob

from oapi.oas.model import OpenAPI
from oapi.oas.references import Resolver, _Document


def _openapi(data: dict[str, typing.Any]) -> OpenAPI:
    open_api: OpenAPI = OpenAPI(data)
    return open_api


def test_resolver_rejects_non_openapi_root() -> None:
    with pytest.raises(TypeError):
        Resolver(root="not-an-openapi")  # type: ignore[arg-type]


def test_resolver_rejects_non_callable_urlopen() -> None:
    open_api: OpenAPI = _openapi(
        {"openapi": "3.0.3", "info": {"title": "t", "version": "1"}}
    )
    with pytest.raises(TypeError):
        Resolver(open_api, urlopen="not-callable")  # type: ignore[arg-type]


def test_resolver_rejects_non_string_url() -> None:
    open_api: OpenAPI = _openapi(
        {"openapi": "3.0.3", "info": {"title": "t", "version": "1"}}
    )
    with pytest.raises(TypeError):
        Resolver(open_api, url=123)  # type: ignore[arg-type]


def test_document_requires_an_inferable_url() -> None:
    open_api: OpenAPI = _openapi(
        {"openapi": "3.0.3", "info": {"title": "t", "version": "1"}}
    )
    resolver: Resolver = Resolver(
        open_api, url="http://example.com/openapi.json"
    )
    with pytest.raises(ValueError, match="You must provide a URL"):
        _Document(resolver, root=open_api, url=None)


def test_document_rejects_non_resolver_argument() -> None:
    open_api: OpenAPI = _openapi(
        {"openapi": "3.0.3", "info": {"title": "t", "version": "1"}}
    )
    with pytest.raises(TypeError):
        _Document(
            "not-a-resolver",  # type: ignore[arg-type]
            root=open_api,
            url="http://example.com/openapi.json",
        )


def test_document_normalizes_a_path_url_to_str() -> None:
    open_api: OpenAPI = _openapi(
        {"openapi": "3.0.3", "info": {"title": "t", "version": "1"}}
    )
    resolver: Resolver = Resolver(
        open_api, url="http://example.com/openapi.json"
    )
    document: _Document = _Document(
        resolver, open_api, url=Path("/tmp/openapi.json")
    )
    assert document.url == "/tmp/openapi.json"
    assert isinstance(document.url, str)


def test_document_infers_url_from_roots_model_url() -> None:
    open_api: OpenAPI = _openapi(
        {"openapi": "3.0.3", "info": {"title": "t", "version": "1"}}
    )
    sob.set_model_url(open_api, "http://example.com/inferred.json")
    resolver: Resolver = Resolver(
        open_api, url="http://example.com/openapi.json"
    )
    document: _Document = _Document(resolver, open_api)
    assert document.url == "http://example.com/inferred.json"


def test_get_absolute_url_and_get_url_pointer() -> None:
    open_api: OpenAPI = _openapi(
        {"openapi": "3.0.3", "info": {"title": "t", "version": "1"}}
    )
    resolver: Resolver = Resolver(
        open_api, url="http://example.com/dir/openapi.json"
    )
    document: _Document = _Document(
        resolver, open_api, url="http://example.com/dir/openapi.json"
    )
    assert document.get_absolute_url("other.json") == (
        "http://example.com/dir/other.json"
    )
    url: str
    pointer: str
    url, pointer = document.get_url_pointer("other.json#/foo/bar")
    assert url == "http://example.com/dir/other.json"
    assert pointer == "#/foo/bar"
```

- [ ] **Step 2: Run test to verify it passes**

Run: `hatch run hatch-test.py3.10:pytest tests/test_references.py -v`
Expected: PASS (8 tests). Verified against the real library: each
constructor-validation branch (`TypeError`/`ValueError`) was traced
directly against `Resolver.__init__`/`_Document.__init__`'s actual
guard clauses; `Path("/tmp/openapi.json")` really normalizes to the str
`"/tmp/openapi.json"`; a root with a real `sob.set_model_url` really
gets inferred when no explicit `url` is passed to `_Document`.

- [ ] **Step 3: Format and commit**

```bash
hatch fmt --formatter
hatch fmt --check
git add tests/test_references.py
git commit tests/test_references.py -m "test: add Resolver/_Document construction validation coverage"
```

## Task 2: `dereference()` error branches and empty-ref rejection

**Files:**
- Modify: `tests/test_references.py`

**Interfaces:**
- Consumes: `oapi.oas.model.Reference`, `Schema`, `Properties`
  (existing).

- [ ] **Step 1: Add imports and append the test**

Add these lines to the top import block:

```python
from oapi.oas.model import Properties, Reference, Schema
```

Append to `tests/test_references.py`:

```python
def test_dereference_rejects_a_non_model_argument() -> None:
    open_api: OpenAPI = _openapi(
        {"openapi": "3.0.3", "info": {"title": "t", "version": "1"}}
    )
    sob.set_model_url(open_api, "http://example.com/openapi.json")
    resolver: Resolver = Resolver(open_api)
    document: _Document = resolver.documents[""]
    with pytest.raises(TypeError):
        document.dereference("just a string")  # type: ignore[arg-type]


def test_dereference_object_properties_rejects_an_empty_ref() -> None:
    open_api: OpenAPI = _openapi(
        {"openapi": "3.0.3", "info": {"title": "t", "version": "1"}}
    )
    sob.set_model_url(open_api, "http://example.com/openapi.json")
    resolver: Resolver = Resolver(open_api)
    document: _Document = resolver.documents[""]
    schema: Schema = Schema()
    schema.items = Reference({"$ref": ""})
    with pytest.raises(ValueError, match=r'\{"\$ref": ""\}'):
        document.dereference_object_properties(schema)


def test_dereference_array_items_rejects_an_empty_ref() -> None:
    open_api: OpenAPI = _openapi(
        {"openapi": "3.0.3", "info": {"title": "t", "version": "1"}}
    )
    sob.set_model_url(open_api, "http://example.com/openapi.json")
    resolver: Resolver = Resolver(open_api)
    document: _Document = resolver.documents[""]
    schema: Schema = Schema()
    schema.all_of = [Reference({"$ref": ""})]
    all_of: typing.Sequence[Reference | Schema] | None = schema.all_of
    assert isinstance(all_of, sob.abc.Array)
    with pytest.raises(ValueError, match=r'\{"\$ref": ""\}'):
        document.dereference_array_items(all_of)


def test_dereference_dictionary_values_rejects_an_empty_ref() -> None:
    open_api: OpenAPI = _openapi(
        {"openapi": "3.0.3", "info": {"title": "t", "version": "1"}}
    )
    sob.set_model_url(open_api, "http://example.com/openapi.json")
    resolver: Resolver = Resolver(open_api)
    document: _Document = resolver.documents[""]
    schema: Schema = Schema()
    schema.properties = Properties({"x": Reference({"$ref": ""})})
    properties: Properties | None = schema.properties
    assert isinstance(properties, sob.abc.Dictionary)
    with pytest.raises(ValueError, match=r'\{"\$ref": ""\}'):
        document.dereference_dictionary_values(properties)
```

Note on `all_of`/`properties`: `Schema.all_of` is statically typed
`Sequence[Reference | Schema] | None` and `Schema.properties` is typed
`Properties | None` — neither is `sob.abc.Array`/`sob.abc.Dictionary`
per the type checker, even though the real runtime value is (confirmed:
`type(schema.all_of)` is `sob.Array`, a `list` subclass). Rather than a
blind `cast(...)`, both use a real `isinstance` check to narrow — the
same honest-narrowing idiom as elsewhere in this codebase, not a
type-checker workaround.

- [ ] **Step 2: Run test to verify it passes**

Run: `hatch run hatch-test.py3.10:pytest tests/test_references.py -v`
Expected: PASS (12 tests). Verified against the real library: `Schema.items`
directly holding an empty-`$ref` `Reference`, `Schema.all_of`/`Schema.properties`
each containing one, and a plain string passed to `dereference()` — all
four raise their real, exact exceptions.

- [ ] **Step 3: Format and commit**

```bash
hatch fmt --formatter
hatch fmt --check
git add tests/test_references.py
git commit tests/test_references.py -m "test: add dereference() error-branch coverage"
```

## Task 3: Real reference-loop detection

**Files:**
- Modify: `tests/test_references.py`

**Interfaces:**
- Consumes: `oapi.errors.OAPIReferenceLoopError` (existing).

- [ ] **Step 1: Add import and append the test**

Add to the top import block:

```python
from oapi.errors import OAPIReferenceLoopError
```

Append to `tests/test_references.py`:

```python
def test_dereference_raises_loop_error_for_self_referencing_array() -> None:
    """
    `Schema.items` is a direct `Reference | Schema` attribute (not nested
    inside a dict/list container), so a schema whose `items` refers back
    to itself is visited directly by `dereference_object_properties` --
    unlike a self-reference nested inside `properties`, which would only
    be reached with `recursive=True`, and `recursive=True` is exactly
    the setting under which `dereference()` catches and suppresses
    `OAPIReferenceLoopError` (see the module docstring/`dereference`
    implementation: `except OAPIReferenceLoopError: if not recursive:
    raise`). Calling `_Document.dereference` directly with
    `recursive=False` is therefore the only way to observe this real,
    reachable error -- no public caller currently passes
    `recursive=False`, but the code path is real production code, not
    dead code invented for this test.
    """
    open_api: OpenAPI = _openapi(
        {
            "openapi": "3.0.3",
            "info": {"title": "t", "version": "1"},
            "paths": {},
            "components": {
                "schemas": {
                    "Node": {
                        "type": "array",
                        "items": {"$ref": "#/components/schemas/Node"},
                    }
                }
            },
        }
    )
    sob.set_model_url(open_api, "http://example.com/openapi.json")
    resolver: Resolver = Resolver(open_api)
    document: _Document = resolver.documents[""]
    assert open_api.components is not None
    assert open_api.components.schemas is not None
    node: Schema = open_api.components.schemas["Node"]
    with pytest.raises(OAPIReferenceLoopError):
        document.dereference(node, recursive=False)


def test_dereference_with_recursive_true_silently_absorbs_the_loop() -> None:
    """
    Contrasts with the test above: the real, public-facing behavior for
    `recursive=True` (what every public caller actually uses) is to
    swallow the loop error rather than raise it, leaving the
    self-referencing structure as-is. This is current, real behavior,
    not something this test judges as correct or incorrect.
    """
    open_api: OpenAPI = _openapi(
        {
            "openapi": "3.0.3",
            "info": {"title": "t", "version": "1"},
            "paths": {},
            "components": {
                "schemas": {
                    "Node": {
                        "type": "array",
                        "items": {"$ref": "#/components/schemas/Node"},
                    }
                }
            },
        }
    )
    sob.set_model_url(open_api, "http://example.com/openapi.json")
    resolver: Resolver = Resolver(open_api)
    resolver.dereference()
```

- [ ] **Step 2: Run test to verify it passes**

Run: `hatch run hatch-test.py3.10:pytest tests/test_references.py -v`
Expected: PASS (14 tests). Verified against the real library: this
exact scenario (a self-referencing array schema's `items`) was traced
by hand against `dereference_object_properties`'s real
`prevent_infinite_recursion`/`resolve` interaction — with
`recursive=False`, `_Document.dereference` genuinely raises
`OAPIReferenceLoopError`; with `recursive=True` (via the public
`Resolver.dereference()`), it genuinely does not.

- [ ] **Step 3: Format and commit**

```bash
hatch fmt --formatter
hatch fmt --check
git add tests/test_references.py
git commit tests/test_references.py -m "test: add real reference-loop detection coverage"
```

## Task 4: `resolve()` pointer-error and type-error edge cases

**Files:**
- Modify: `tests/test_references.py`

**Interfaces:**
- Consumes: `oapi.errors.OAPIReferencePointerError` (existing).

- [ ] **Step 1: Add import and append the test**

Add to the top import block:

```python
from oapi.errors import OAPIReferenceLoopError, OAPIReferencePointerError
```

(replacing the single-name `OAPIReferenceLoopError` import from Task 3
with this combined one).

Append to `tests/test_references.py`:

```python
def test_resolve_raises_pointer_error_for_a_falsy_but_existing_target() -> (
    None
):
    """
    `resolve_pointer` (the `jsonpointer` library) raises its own
    `JsonPointerException` for a pointer path that doesn't exist at
    all -- that is a different, real failure mode, not this one.
    `OAPIReferencePointerError` is specifically for a pointer that
    *does* resolve, but to a falsy value (e.g. a real, empty
    `sob.Array`), which the `if not model:` check at the end of
    `resolve()` treats as "not found."
    """
    open_api: OpenAPI = _openapi(
        {
            "openapi": "3.0.3",
            "info": {"title": "t", "version": "1"},
            "paths": {},
            "components": {
                "schemas": {"Color": {"type": "string", "enum": []}}
            },
        }
    )
    sob.set_model_url(open_api, "http://example.com/openapi.json")
    resolver: Resolver = Resolver(open_api)
    with pytest.raises(OAPIReferencePointerError):
        resolver.resolve("#/components/schemas/Color/enum")


def test_resolve_raises_type_error_for_a_null_valued_target() -> None:
    """
    Resolving a pointer to a location whose real, unmarshalled value is
    `None` hits `_unmarshal_resolved_reference`'s own `TypeError` guard
    (it only accepts already-`sob.abc.Model` results, or something
    `sob.unmarshal` can turn into one) before `resolve()`'s own
    falsy-value check is ever reached.
    """
    open_api: OpenAPI = _openapi(
        {
            "openapi": "3.0.3",
            "info": {"title": "t", "version": "1", "description": None},
            "paths": {},
        }
    )
    sob.set_model_url(open_api, "http://example.com/openapi.json")
    resolver: Resolver = Resolver(open_api)
    with pytest.raises(TypeError):
        resolver.resolve("#/info/description")
```

- [ ] **Step 2: Run test to verify it passes**

Run: `hatch run hatch-test.py3.10:pytest tests/test_references.py -v`
Expected: PASS (16 tests). Verified against the real library: resolving
`#/components/schemas/Color/enum` where `enum: []` (a real, empty
`sob.Array`, confirmed falsy via `bool([]) is False`) raises
`OAPIReferencePointerError`; resolving `#/info/description` where
`description: null` raises a real `TypeError` from
`_unmarshal_resolved_reference`.

- [ ] **Step 3: Format and commit**

```bash
hatch fmt --formatter
hatch fmt --check
git add tests/test_references.py
git commit tests/test_references.py -m "test: add resolve() pointer-error and type-error coverage"
```

## Task 5: `resolve_reference()` — previously zero coverage

**Files:**
- Modify: `tests/test_references.py`

**Interfaces:** none new — reuses `_openapi`, `Resolver`,
`OAPIReferenceLoopError` from earlier tasks.

- [ ] **Step 1: Append the test**

`resolve_reference()` had no test coverage at all before this plan.
Append to `tests/test_references.py`:

```python
def test_resolve_reference_follows_a_chain_to_the_real_target() -> None:
    open_api: OpenAPI = _openapi(
        {
            "openapi": "3.0.3",
            "info": {"title": "t", "version": "1"},
            "paths": {},
            "components": {
                "schemas": {
                    "A": {"type": "string"},
                    "B": {"$ref": "#/components/schemas/A"},
                }
            },
        }
    )
    sob.set_model_url(open_api, "http://example.com/openapi.json")
    resolver: Resolver = Resolver(open_api)
    assert open_api.components is not None
    assert open_api.components.schemas is not None
    b_reference: Reference = open_api.components.schemas["B"]
    resolved: sob.abc.Model = resolver.resolve_reference(b_reference)
    assert isinstance(resolved, Schema)
    assert resolved.type_ == "string"


def test_resolve_reference_recurses_through_a_two_level_chain() -> None:
    """
    `B` above resolves to a real `Schema` in one hop, so it never
    exercises `resolve_reference`'s own recursive
    `self.resolve_reference(resolved_model, types=types)` call (that
    branch only fires when the *result* of resolving one reference is
    itself still a `Reference`). This test adds one more hop
    (`C -> B -> A`) specifically to reach that recursive call for real.
    """
    open_api: OpenAPI = _openapi(
        {
            "openapi": "3.0.3",
            "info": {"title": "t", "version": "1"},
            "paths": {},
            "components": {
                "schemas": {
                    "A": {"type": "string"},
                    "B": {"$ref": "#/components/schemas/A"},
                    "C": {"$ref": "#/components/schemas/B"},
                }
            },
        }
    )
    sob.set_model_url(open_api, "http://example.com/openapi.json")
    resolver: Resolver = Resolver(open_api)
    assert open_api.components is not None
    assert open_api.components.schemas is not None
    c_reference: Reference = open_api.components.schemas["C"]
    resolved: sob.abc.Model = resolver.resolve_reference(c_reference)
    assert isinstance(resolved, Schema)
    assert resolved.type_ == "string"


def test_resolve_reference_rejects_an_empty_ref() -> None:
    open_api: OpenAPI = _openapi(
        {"openapi": "3.0.3", "info": {"title": "t", "version": "1"}}
    )
    sob.set_model_url(open_api, "http://example.com/openapi.json")
    resolver: Resolver = Resolver(open_api)
    empty_reference: Reference = Reference({"$ref": ""})
    with pytest.raises(ValueError, match=r'\{"\$ref": ""\}'):
        resolver.resolve_reference(empty_reference)


def test_resolve_reference_raises_a_real_loop_error_for_self_reference() -> (
    None
):
    open_api: OpenAPI = _openapi(
        {
            "openapi": "3.0.3",
            "info": {"title": "t", "version": "1"},
            "paths": {},
            "components": {
                "schemas": {
                    "SelfRef": {"$ref": "#/components/schemas/SelfRef"}
                }
            },
        }
    )
    sob.set_model_url(open_api, "http://example.com/openapi.json")
    resolver: Resolver = Resolver(open_api)
    assert open_api.components is not None
    assert open_api.components.schemas is not None
    self_reference: Reference = open_api.components.schemas["SelfRef"]
    with pytest.raises(OAPIReferenceLoopError):
        resolver.resolve_reference(self_reference)
```

Note: unlike `_Document.dereference`, `resolve_reference`'s own
self-referential check (`resolved_model is reference or
(isinstance(resolved_model, Reference) and resolved_model.ref ==
reference.ref)`) does not have the same recursive/swallow behavior as
Task 3 — it's a direct equality/identity check against the resolved
result, and raises for real through the normal public call path (no
`recursive=False` workaround needed here).

- [ ] **Step 2: Run test to verify it passes**

Run: `hatch run hatch-test.py3.10:pytest tests/test_references.py -v`
Expected: PASS (20 tests). Verified against the real library: a
one-hop chain (`B -> A`) resolves to the real `A` schema; a two-hop
chain (`C -> B -> A`) genuinely exercises the method's own recursive
call and still resolves to `A`; an empty-ref `Reference` raises
`ValueError`; a schema that refers to itself
(`SelfRef -> SelfRef`) raises a real `OAPIReferenceLoopError` with
message `` `Reference` instance is self-referential: ... ``.

- [ ] **Step 3: Format and commit**

```bash
hatch fmt --formatter
hatch fmt --check
git add tests/test_references.py
git commit tests/test_references.py -m "test: add resolve_reference() coverage (previously untested)"
```

## Task 6: `get_relative_url()`

**Files:**
- Modify: `tests/test_references.py`

**Interfaces:** none new.

- [ ] **Step 1: Append the test**

Append to `tests/test_references.py`:

```python
def test_get_relative_url_for_the_root_document_itself() -> None:
    open_api: OpenAPI = _openapi(
        {"openapi": "3.0.3", "info": {"title": "t", "version": "1"}}
    )
    resolver: Resolver = Resolver(
        open_api, url="http://example.com/docs/openapi.json"
    )
    assert (
        resolver.get_relative_url("http://example.com/docs/openapi.json")
        == ""
    )


def test_get_relative_url_for_a_different_absolute_url() -> None:
    open_api: OpenAPI = _openapi(
        {"openapi": "3.0.3", "info": {"title": "t", "version": "1"}}
    )
    resolver: Resolver = Resolver(
        open_api, url="http://example.com/docs/openapi.json"
    )
    assert (
        resolver.get_relative_url("http://example.com/docs/other.json")
        == "other.json"
    )


def test_get_relative_url_passes_through_a_relative_looking_url() -> None:
    open_api: OpenAPI = _openapi(
        {"openapi": "3.0.3", "info": {"title": "t", "version": "1"}}
    )
    resolver: Resolver = Resolver(
        open_api, url="http://example.com/docs/openapi.json"
    )
    assert resolver.get_relative_url("other.json") == "other.json"


def test_get_relative_url_for_an_empty_url() -> None:
    open_api: OpenAPI = _openapi(
        {"openapi": "3.0.3", "info": {"title": "t", "version": "1"}}
    )
    resolver: Resolver = Resolver(
        open_api, url="http://example.com/docs/openapi.json"
    )
    assert resolver.get_relative_url("") == ""
```

Note: a `file://` URL variant was investigated and dropped — it hits an
unrelated `ValueError` deep inside `sob.utilities.get_url_relative_to`
(a real bug or edge case in the `sob` dependency itself, not in
`oapi`), which is out of scope for this plan. The "different absolute
url" case above already exercises the same `netloc`-truthy branch in
`get_relative_url` that a `file://` URL would, via the simpler,
uncomplicated `http://` case.

- [ ] **Step 2: Run test to verify it passes**

Run: `hatch run hatch-test.py3.10:pytest tests/test_references.py -v`
Expected: PASS (24 tests). Verified against the real library: all four
branches (same URL, different absolute URL, relative passthrough,
empty) produce exactly the strings asserted.

- [ ] **Step 3: Format and commit**

```bash
hatch fmt --formatter
hatch fmt --check
git add tests/test_references.py
git commit tests/test_references.py -m "test: add get_relative_url() coverage"
```

## Task 7: Real multi-document HTTP resolution + fetch errors

**Files:**
- Modify: `tests/test_references.py`

**Interfaces:**
- Consumes: `tests.servers.http_test_server`, `tests.servers.Response`
  (from the prior infrastructure plan, already merged into this branch
  as `tests/servers.py`) — the one task in this plan that needs the
  local HTTP test server.

- [ ] **Step 1: Add imports and append the test**

Add these lines to the top import block:

```python
import json
from urllib.error import HTTPError

from servers import Response, http_test_server
```

Append to `tests/test_references.py`:

```python
def test_resolver_resolves_a_reference_in_a_real_external_http_document() -> (
    None
):
    external_document: dict[str, object] = {
        "openapi": "3.0.3",
        "info": {"title": "external", "version": "1"},
        "paths": {},
        "components": {
            "schemas": {
                "Widget": {
                    "type": "object",
                    "properties": {"name": {"type": "string"}},
                }
            }
        },
    }
    with http_test_server(
        responses={
            ("GET", "/external.json"): Response(
                status=200,
                body=json.dumps(external_document).encode(),
                headers={"Content-type": "application/json"},
            )
        }
    ) as server:
        open_api: OpenAPI = _openapi(
            {
                "openapi": "3.0.3",
                "info": {"title": "t", "version": "1"},
                "paths": {},
                "components": {
                    "schemas": {
                        "Local": {
                            "$ref": (
                                f"{server.url}/external.json"
                                "#/components/schemas/Widget"
                            )
                        }
                    }
                },
            }
        )
        sob.set_model_url(open_api, f"{server.url}/openapi.json")
        resolver: Resolver = Resolver(open_api)
        assert open_api.components is not None
        assert open_api.components.schemas is not None
        local_reference: Reference = (
            open_api.components.schemas["Local"]
        )
        resolved: sob.abc.Model = resolver.resolve_reference(
            local_reference
        )
        assert isinstance(resolved, sob.abc.Dictionary)
        assert resolved["type"] == "object"


def test_get_document_raises_a_real_http_error_for_a_404() -> None:
    with http_test_server(
        responses={
            ("GET", "/missing.json"): Response(status=404, body=b"n/a")
        }
    ) as server:
        open_api: OpenAPI = _openapi(
            {"openapi": "3.0.3", "info": {"title": "t", "version": "1"}}
        )
        sob.set_model_url(open_api, f"{server.url}/openapi.json")
        resolver: Resolver = Resolver(open_api)
        with pytest.raises(HTTPError):
            resolver.get_document(f"{server.url}/missing.json")


def test_get_document_raises_a_real_file_not_found_error() -> None:
    open_api: OpenAPI = _openapi(
        {"openapi": "3.0.3", "info": {"title": "t", "version": "1"}}
    )
    sob.set_model_url(open_api, "/tmp/openapi.json")
    resolver: Resolver = Resolver(open_api, urlopen=open)
    with pytest.raises(FileNotFoundError):
        resolver.get_document("/tmp/does-not-exist-oapi-test.json")
```

Note: `Resolver(open_api, urlopen=open)` is the exact pattern documented
in `Resolver`'s own class docstring for resolving local file-path
references (`"use `open` as the value for the `urlopen` parameter in
this case"`) — this test exercises that documented usage for real, not
a synthetic scenario.

- [ ] **Step 2: Run test to verify it passes**

Run: `hatch run hatch-test.py3.10:pytest tests/test_references.py -v`
Expected: PASS (27 tests). Verified against the real library and a real
local socket: a `$ref` pointing at a real second document served by
`http_test_server` resolves to that document's real `Widget` schema
data (as a `sob.Dictionary`, since it wasn't given explicit `types=`);
fetching a URL that the server answers with a real 404 raises a real
`urllib.error.HTTPError`; fetching a genuinely nonexistent local file
path via `urlopen=open` raises a real `FileNotFoundError`.

- [ ] **Step 3: Run the full file and check coverage**

Run: `hatch run hatch-test.py3.10:pytest tests/test_references.py -v`
Expected: 27/27 pass — this is the complete `tests/test_references.py`
for this plan (Tasks 1-7 combined, 493 lines).

- [ ] **Step 4: Format and commit**

```bash
hatch fmt --formatter
hatch fmt --check
git add tests/test_references.py
git commit tests/test_references.py -m "test: add multi-document HTTP resolution and fetch-error coverage"
```

## Task 8: `_schema_after_validate` — real format/type validation

**Files:**
- Create: `tests/test_oas_model_hooks.py`

**Interfaces:**
- Consumes: `oapi.oas.model.Schema`, `_schema_after_validate`
  (existing).
- Produces: `tests/test_oas_model_hooks.py` as a new file — later tasks
  in this plan append to it.

- [ ] **Step 1: Write the test**

Create `tests/test_oas_model_hooks.py`:

```python
from __future__ import annotations

import pytest
import sob

from oapi.oas.model import Schema, _schema_after_validate


@pytest.mark.parametrize(
    ("type_", "format_"),
    [
        ("integer", "int32"),
        ("integer", "int64"),
        ("number", "float"),
        ("number", "double"),
        ("string", "byte"),
        ("string", "binary"),
        ("string", "date"),
        ("string", "date-time"),
        ("string", "password"),
    ],
)
def test_schema_validate_accepts_matching_type_and_format(
    type_: str, format_: str
) -> None:
    schema: Schema = Schema({"type": type_, "format": format_})
    sob.validate(schema)


def test_schema_validate_rejects_integer_with_a_string_format() -> None:
    schema: Schema = Schema({"type": "integer", "format": "date"})
    with pytest.raises(sob.errors.ValidationError, match="int32.*int64"):
        sob.validate(schema)


def test_schema_validate_rejects_number_with_an_integer_format() -> None:
    schema: Schema = Schema({"type": "number", "format": "int32"})
    with pytest.raises(sob.errors.ValidationError, match="float.*double"):
        sob.validate(schema)


def test_schema_validate_rejects_string_with_a_numeric_format() -> None:
    schema: Schema = Schema({"type": "string", "format": "int32"})
    with pytest.raises(sob.errors.ValidationError, match="byte.*binary"):
        sob.validate(schema)


def test_schema_after_validate_rejects_a_non_schema_argument() -> None:
    with pytest.raises(TypeError):
        _schema_after_validate("not a schema")  # type: ignore[arg-type]
```

- [ ] **Step 2: Run test to verify it passes**

Run: `hatch run hatch-test.py3.10:pytest tests/test_oas_model_hooks.py -v`
Expected: PASS (13 tests). Verified against the real library: all 9
valid `(type_, format_)` pairs pass `sob.validate` cleanly; the three
mismatched combinations (`integer`/`date`, `number`/`int32`,
`string`/`int32`) each raise the real `sob.errors.ValidationError` with
the expected message content; calling the hook directly with a
non-`Schema` argument raises `TypeError`.

- [ ] **Step 3: Format and commit**

```bash
hatch fmt --formatter
hatch fmt --check
git add tests/test_oas_model_hooks.py
git commit tests/test_oas_model_hooks.py -m "test: add _schema_after_validate coverage"
```

## Task 9: `_parameter_after_validate` — content/schema conflicts

**Files:**
- Modify: `tests/test_oas_model_hooks.py`

**Interfaces:**
- Consumes: `oapi.oas.model.Parameter`, `_parameter_after_validate`
  (existing).

- [ ] **Step 1: Add import and append the test**

Add `Parameter` and `_parameter_after_validate` to the existing `from
oapi.oas.model import (...)` block (now: `Parameter, Schema,
_parameter_after_validate, _schema_after_validate`).

Append to `tests/test_oas_model_hooks.py`:

```python
def test_parameter_validate_rejects_more_than_one_content_entry() -> None:
    parameter: Parameter = Parameter(
        {
            "name": "x",
            "in": "query",
            "content": {
                "application/json": {"schema": {"type": "string"}},
                "application/xml": {"schema": {"type": "string"}},
            },
        }
    )
    with pytest.raises(
        sob.errors.ValidationError, match="only one mapped value"
    ):
        sob.validate(parameter)


def test_parameter_validate_rejects_both_content_and_schema() -> None:
    parameter: Parameter = Parameter(
        {
            "name": "x",
            "in": "query",
            "schema": {"type": "string"},
            "content": {"application/json": {"schema": {"type": "string"}}},
        }
    )
    with pytest.raises(sob.errors.ValidationError, match="not \\*both\\*"):
        sob.validate(parameter)


def test_parameter_validate_delegates_to_schema_validation() -> None:
    """
    `_parameter_after_validate` calls `_schema_after_validate(parameter)`
    as its last step (a `Parameter` shares the `type_`/`format_` fields a
    `Schema` has), so an invalid format/type combination on a
    `Parameter` itself -- not on a nested `schema` -- is also rejected.
    """
    parameter: Parameter = Parameter(
        {"name": "x", "in": "query", "type": "integer", "format": "date"}
    )
    with pytest.raises(sob.errors.ValidationError, match="int32.*int64"):
        sob.validate(parameter)


def test_parameter_after_validate_rejects_a_non_parameter_argument() -> None:
    with pytest.raises(TypeError):
        _parameter_after_validate("not a parameter")  # type: ignore[arg-type]
```

- [ ] **Step 2: Run test to verify it passes**

Run: `hatch run hatch-test.py3.10:pytest tests/test_oas_model_hooks.py -v`
Expected: PASS (17 tests). Verified against the real library: a
`Parameter` with two `content` entries raises `ValidationError` with
"only one mapped value" in the message; one with both `content` and
`schema` set raises with "not *both*"; a `Parameter` with its own
mismatched `type_`/`format_` (not nested in a `schema`) is rejected via
the real delegation to `_schema_after_validate`; calling the hook
directly with a non-`Parameter` argument raises `TypeError`.

- [ ] **Step 3: Format and commit**

```bash
hatch fmt --formatter
hatch fmt --check
git add tests/test_oas_model_hooks.py
git commit tests/test_oas_model_hooks.py -m "test: add _parameter_after_validate coverage"
```

## Task 10: `Reference` unmarshal validation and arbitrary properties

**Files:**
- Modify: `tests/test_oas_model_hooks.py`

**Interfaces:**
- Consumes: `oapi.oas.model.Reference`, `_reference_after_unmarshal`
  (existing).

- [ ] **Step 1: Add import and append the test**

Add `Reference` and `_reference_after_unmarshal` to the existing `from
oapi.oas.model import (...)` block (now: `Parameter, Reference, Schema,
_parameter_after_validate, _reference_after_unmarshal,
_schema_after_validate`).

Append to `tests/test_oas_model_hooks.py`:

```python
def test_reference_after_unmarshal_rejects_a_non_reference_argument() -> None:
    with pytest.raises(TypeError):
        _reference_after_unmarshal("not a reference")  # type: ignore[arg-type]


def test_reference_after_unmarshal_requires_a_ref_attribute() -> None:
    """
    `Reference()` (no data) has no `$ref` set. `data["$ref"]` does NOT
    raise `KeyError` here -- `$ref` is a declared property on
    `Reference`, and `sob` returns `None` for a declared-but-unset
    property rather than raising. So `ref = typing.cast(str,
    data["$ref"])` in the real `try` block simply succeeds with `ref =
    None`, and the `except KeyError:` handler never runs for this (or
    any) `Reference` -- it's dead code under current `sob` behavior.
    The real, asserted `ValueError` comes from the `if ref is None:`
    check that follows.
    """
    with pytest.raises(ValueError, match="must have a"):
        _reference_after_unmarshal(Reference())


def test_unmarshal_also_rejects_a_reference_missing_ref() -> None:
    """
    The same real validation is reachable through the public
    `sob.unmarshal` entry point (not just by calling the private hook
    directly): `sob.unmarshal` wraps the underlying `ValueError` in its
    own composite "does not match any of the expected types" error, but
    that wrapper's message embeds the original text.
    """
    with pytest.raises(ValueError, match="must have a"):
        sob.unmarshal({}, types=(Reference,))


def test_reference_accepts_a_genuinely_arbitrary_extra_property() -> None:
    """
    Exercises `_add_object_property`'s "this is a genuinely new
    property" branch: OpenAPI 3.1 allows arbitrary extra attributes on a
    `Reference` object (its `patternProperties`), and
    `_reference_before_setitem` dynamically adds a property definition
    for any key it hasn't seen before. `summary` and `description` are
    already pre-declared properties on `Reference` (confirmed via
    `sob.read_object_meta(Reference).properties`), so a genuinely novel
    key is needed to exercise this -- OpenAPI's own convention for
    arbitrary extensions (`x-`-prefixed keys) is used here.
    """
    reference: Reference = Reference(
        {"$ref": "#/components/schemas/Foo", "x-custom": "a value"}
    )
    assert reference["x-custom"] == "a value"
```

Note on the `except KeyError: ref = None` lines inside
`_reference_after_unmarshal`: `coverage.py` correctly reports these two
lines as "missing" — they are genuinely dead code for `Reference`
(`$ref` is always a declared property, so `data["$ref"]` returns `None`
rather than raising `KeyError`; see the Global Constraints section's
dedicated bullet). `test_reference_after_unmarshal_requires_a_ref_attribute`
still correctly asserts the real `ValueError` this function raises —
it just doesn't (and can't) go through the `except` handler to get
there. Do not try to restructure this test to hit those two lines; they
aren't reachable through any `Reference` input.

- [ ] **Step 2: Run test to verify it passes**

Run: `hatch run hatch-test.py3.10:pytest tests/test_oas_model_hooks.py -v`
Expected: PASS (21 tests). Verified against the real library: calling
`_reference_after_unmarshal` with a non-`Reference` argument raises
`TypeError`; calling it with a real, empty `Reference()` raises the
real `ValueError` (message contains "must have a"); the same failure is
independently reachable through the public `sob.unmarshal({},
types=(Reference,))` entry point (its composite error message embeds
the original text); a `Reference` constructed with a genuinely novel
`x-custom` key round-trips that value through real subscript access.

- [ ] **Step 3: Run the full file and confirm the plan's combined total**

Run: `hatch run hatch-test.py3.10:pytest tests/test_references.py tests/test_oas_model_hooks.py -v`
Expected: all 27 + 21 = 48 tests from Tasks 1-10 pass together (no
cross-task interference).

- [ ] **Step 4: Format and commit**

```bash
hatch fmt --formatter
hatch fmt --check
git add tests/test_oas_model_hooks.py
git commit tests/test_oas_model_hooks.py -m "test: add Reference unmarshal and arbitrary-property coverage"
```

The final `tests/test_oas_model_hooks.py` (Tasks 8-10 combined) should
be 152 lines; the final `tests/test_references.py` (Tasks 1-7 combined)
should be 493 lines. Both are `hatch fmt --check`-clean and pass a real
`mypy --strict` run with zero errors (verified directly against this
exact plan's code before it was written down — the only other error a
real `mypy --strict tests/` run reports is the known, out-of-scope
`tests/servers.py:56` issue from the infrastructure plan).

## Task 11: Full-suite sanity check

**Files:** none (verification only)

- [ ] **Step 1: Run the project's standard test gate**

Run: `make test`
Expected: `hatch fmt --check && hatch run mypy && hatch test -c -vv` — if
`hatch run mypy` fails specifically at the dependency-*sync* step with a
`dependence~=1.4` resolution error (not an actual type error in code),
that's the same known pre-existing environment issue documented in
prior plans — report it as such, and separately confirm `hatch fmt
--check` and `hatch test -c -vv` pass cleanly on their own.

- [ ] **Step 2: Confirm the coverage improvement**

Run: `hatch test -c && hatch run hatch-test.py3.10:coverage report -m --include="*/oas/references.py,*/oas/model.py"`
Expected: `oas/references.py` at or near 98% (baseline 79%; remaining
gaps are the documented, deliberately-out-of-scope ones in Global
Constraints), `oas/model.py` at or near 95% file-wide (baseline 92%;
the hooks-region target lines are covered — except `6748-6749`, which
is genuinely dead code for `Reference` (see Global Constraints) — the
remaining gaps are the deliberately-out-of-scope generated constructor
boilerplate).

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

**1. Spec coverage:** The spec's step 3 ("`oas/references.py` and
`oas/model.py` validation hooks") is fully addressed: every method on
`_Document`/`Resolver` with a previously-uncovered branch has a task
(Tasks 1-7), and all four hand-written validation/unmarshal hooks in
`oas/model.py` (`_schema_after_validate`, `_parameter_after_validate`,
`_reference_after_unmarshal`, `_add_object_property`) have a task
(Tasks 8-10). The spec's explicit call-out that this step needs "no
server needed except the one HTTP-`$ref` test" is followed exactly —
`http_test_server` appears only in Task 7. `resolve_reference()`, which
had zero prior coverage, is now covered in Task 5. Generated
constructor-body boilerplate elsewhere in `oas/model.py` is explicitly
and reasoned-out excluded, matching the spec's own guidance
("likely just needs a couple of targeted small fixtures... not new
infrastructure" — investigated and found not worth chasing for
tautological `self.x = x` coverage).

**2. Placeholder scan:** No "TBD"/"add appropriate handling"/"similar to
Task N" language. Every step has runnable code, executed against the
real `oapi` package before being written here. Two genuinely surprising,
real behaviors were discovered during that verification and are now
documented rather than papered over: (a) loop-error swallowing under
`recursive=True` (Task 3, Global Constraints); (b) two `Reference`
fields (`summary`, `description`) that turned out to already be
pre-declared, not arbitrary (Task 10, Global Constraints). A third
claimed behavior — a supposed `coverage.py` line-attribution quirk for
`model.py:6748-6749` — was written into an earlier draft of this plan
based on a flawed reading of a real `coverage run`: the tool's
"missing" report for those two lines was correct all along; they are
genuinely dead code (`Reference()["$ref"]` returns `None` rather than
raising `KeyError`, so the `except KeyError:` handler never runs). This
was caught and corrected during the final whole-branch review (see the
ledger) rather than left standing — the test itself was always correct
(it asserts the real, resulting `ValueError`), only the plan's and the
test docstring's *mechanism* explanation was wrong, and both have been
fixed to match the traced, real behavior.

**3. Type consistency:** `_openapi()` is defined once (Task 1) and
reused verbatim by every later task. Import names introduced in one
task (e.g. `Properties`, `Reference`, `Schema` in Task 2;
`OAPIReferencePointerError` in Task 4) are added to the same shared
import lines and reused without renaming. `Parameter`/`Reference` and
their corresponding `_..._after_validate`/`_..._after_unmarshal`
private functions in `tests/test_oas_model_hooks.py` are added to one
growing `from oapi.oas.model import (...)` block across Tasks 8-10, not
re-declared per task.

---

**Plan complete and saved to
`docs/superpowers/plans/2026-08-02-references-model-validation-tests.md`.**
Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per
task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using
executing-plans, batch execution with checkpoints

**Which approach?**
