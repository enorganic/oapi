# Client Argument-Formatting & Content-Encoding Tests Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task-by-task. Steps
> use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bring `src/oapi/client.py`'s pure-function layer (lines
109-1064: `_iter_items` through `_get_first`, i.e. everything above the
`Client` class) from 18% to essentially full coverage, per
`docs/superpowers/specs/2026-08-01-test-coverage-design.md`'s step 4
("`client.py` argument-formatting + content-encoding"). This is the
half of `client.py` that has zero dependency on network I/O or a real
`Client` instance — pure functions and two small helper classes
(`SSLContext`, the pickling registrars) — so it is tackled before the
`Client` runtime (a later plan) and the `ClientModule` code generator
(the largest remaining chunk, also later).

**Architecture:** Four new test files, each independently runnable and
each targeting a cohesive group of functions:

- `tests/test_client_argument_formatting.py` — `_iter_items`,
  `urlencode`, `_item_is_not_empty`, `_censor_long_json_strings`,
  `_format_primitive_value`, all seven `_format_*_argument_value` style
  formatters, `_format_dot_object_argument_value`, and the
  `format_argument_value` dispatcher.
- `tests/test_client_request_assembly.py` — `get_request_curl`,
  `_represent_http_response`, `_set_response_callback` (both of the
  latter two use the real `http_test_server` from
  `docs/superpowers/plans/2026-08-01-test-infrastructure.md`),
  `_remove_none`, `_format_request_data`, `_get_file_name`, `_get_first`,
  and `_assemble_request` (both the plain and multipart branches).
- `tests/test_client_retry_and_encoding.py` — `default_retry_hook`,
  `retry`, `_encode_content`, `_decode_content`.
- `tests/test_client_pickling.py` — `_make_thread_locks_pickleable`,
  `_make_http_errors_pickleable`, `_make_loggers_pickleable`,
  `SSLContext`.

Unlike the prior two plans in this initiative, every test in all four
files below was already written and independently verified against the
real library, `pytest`, `mypy --strict`, and `hatch fmt --check` *before*
this plan document was drafted (each function's real behavior was
explored live via `hatch run hatch-test.py3.10:python -` scratch
scripts, several genuine test-writing mistakes were caught and fixed
that way — see Global Constraints — and several genuine *source* bugs
were discovered and are documented as real behavior rather than
"fixed"). Because of that, each task below is a single "create/verify
this already-correct file" step rather than the incremental
per-function-group build-up used in earlier plans: there is exactly one
task per file, plus one small task to add two optional test
dependencies. This does not reduce implementer rigor — Step 2 in every
task still requires an independent `pytest`/`mypy --strict`/`hatch fmt
--check` run before committing, not a rubber-stamp.

**Tech Stack:** Python 3.10, `pytest`, stdlib (`gzip`, `zlib`, `pickle`,
`ssl`, `logging`, `threading`, `email.message`), `sob` (already a
dependency), `zstandard`/`brotli` (newly added as `hatch-test`-env-only
test dependencies — see Task 1), `tests/servers.py`'s `http_test_server`
(Task 3 only).

## Global Constraints

- Line length 79 (ruff + black), enforced via `hatch fmt --check`.
- mypy strict on `tests/`: `disallow_untyped_defs`,
  `disallow_incomplete_defs`, and — per this project's standing
  preference — **explicit type annotations on every local variable**,
  not only function signatures. Two established exceptions apply
  in this plan: `with ... as name:` targets (no annotation syntax
  exists there), and `Message[str, str]`-vs-`dict[str, str]` in Task 4
  (a hand-written `dict` annotation is a real mypy error against
  `HTTPError`'s actual `hdrs: email.message.Message[str, str]`
  parameter type — a real `email.message.Message` instance is
  constructed and typed instead). All code in this plan was verified
  against a real `hatch run mypy --strict --ignore-missing-imports`
  run (the `default` env, which has `mypy` installed and, in this
  checkout, syncs successfully — unlike in earlier plans in this
  initiative, `dependence~=1.4` resolved cleanly this time; if it
  doesn't for you, fall back to installing `mypy` into `hatch-test`
  ad hoc and note it, don't skip the check).
- Two new **optional** test dependencies (Task 1): `zstandard` and
  `brotli`/`brotlicffi`. Without them, `_encode_content`/
  `_decode_content`'s `zstd`/`br`/`dcb`/`dcz` branches are completely
  untestable in the `hatch-test` environment (they were, before Task
  1 — confirmed by direct `import zstandard`/`import brotli` both
  raising `ModuleNotFoundError` in a freshly-synced `hatch-test.py3.10`
  env). Both packages are already listed in this project's own `zstd`/
  `brotli`/`all` optional-dependency groups (`pyproject.toml`) and are
  real, supported, already-documented dependencies of `client.py`'s own
  content-encoding code — this is closing a real test-environment gap,
  not adding a new production dependency.
- Prefer real integration over mocks: no `unittest.mock`/`pytest-mock`
  anywhere in any of the four new files. Real `gzip`/`zlib`/`zstandard`/
  `brotli` round-trips, a real `http_test_server` for the two functions
  that touch an `HTTPResponse`, real `urllib.request.Request`/
  `HTTPError`/`Logger` instances throughout. The one place a real
  `time.sleep` is unavoidable (`retry`'s exponential backoff) is used
  as-is rather than faked — the resulting real time cost is bounded
  (~6 seconds total across the whole `retry` test file, one to two
  seconds per test that needs a retry) and multiple assertions were
  consolidated onto a single retry attempt where possible specifically
  to keep that cost down (see Task 3).
- **Imports go at the top of the file** (this project's ruff config
  enforces `I001` import sorting). Run `hatch fmt --formatter` (or
  `hatch fmt` without `--check`, which also auto-fixes some lint rules
  like unused-ignore) followed by `hatch fmt --check` before every
  commit — not optional. `hatch fmt`'s auto-formatter reflows some
  function signatures (e.g. `def some_long_name() -> (\n    None\n):`);
  the exact code blocks in this plan already reflect the
  post-`hatch fmt` output, so a byte-for-byte transcription should not
  need reformatting, but run it anyway as a safety net.
- **Several verified, real, non-obvious behaviors these tests document
  rather than "fix" (do not treat as bugs, do not deviate from the
  specified test code trying to make them "more correct")** — all
  independently traced against the real source, not assumed:
  1. `_iter_items` on a `sob.abc.Object` (e.g. `Reference`) iterates by
     *property name*, not JSON key — `$ref` is exposed as the property
     `ref` (since `$ref` isn't a valid Python identifier) — and yields
     every declared property, including unset ones (as `None`), not
     just the ones actually provided at construction time.
  2. `_format_simple_argument_value`, `_format_label_argument_value`,
     and `_format_matrix_argument_value`'s exploded-dictionary branches
     each do `for item in value` directly over a plain `dict`, which
     yields the dict's *keys*, not `(key, value)` pairs — `item[0]`/
     `item[1]` then index into the key string itself. This silently
     produces wrong output for any key of length ≥ 2 and raises
     `IndexError` for any single-character key. `_format_form_
     argument_value` does not share this bug — it recognizes `dict` as
     one of `_ITEMIZED_TYPES` and correctly uses `_iter_items`.
  3. `_format_deep_object_argument_value`: a dictionary entry whose
     value is itself a sequence *of primitives* (e.g. `{"a": [1, 2]}`)
     raises `TypeError: dict.update() argument after ** must be a
     mapping, not str` — the recursive call for each primitive item
     returns a plain formatted string, and the caller unconditionally
     does `deep_object.update(**that_result)`. A sequence of
     *dictionaries* (`{"a": [{"x": 1}]}`-shaped, or a bare top-level
     sequence of dicts) does not hit this, since the recursive result
     is itself a dict there.
  4. `_encode_content`'s comma-separated (`"gzip,deflate"`-style)
     branch is genuinely broken for real multi-stage encoding: its
     comment says "Encode content in the order provided", but the code
     recursively calls `_decode_content` (not `_encode_content`) on the
     still-plain input data using the *remaining* tokens before
     applying the first one. For most real encoding-pair inputs this
     raises (e.g. `zlib.error` when the plain data isn't actually
     deflate-compressed); Task 3's test exercises the branch without
     triggering the crash by using an unrecognized second token
     (`"identity"`), which `_decode_content` silently no-ops on,
     leaving only the first-listed encoding (`gzip`) actually applied.
     `_decode_content`'s own comma branch is correct (verified via a
     real two-stage `gzip` → `deflate`-compressed payload and the
     matching `"gzip,deflate"` decode call) — only the encode side is
     broken.
  5. `_assemble_request`'s own URL-scheme guard accepts a scheme-less
     relative URL like `/relative/path` (its check only looks for a
     `:` before the first `/`), but the plain, non-multipart branch
     then constructs a real `urllib.request.Request(url, ...)`, which
     itself raises `ValueError: unknown url type: '/relative/path'`
     when the URL isn't fully qualified. Task 2's test for this
     asserts a `ValueError` is raised without asserting which of the
     two layers raised it (real, current, combined behavior).
- **Two lines in the pure-function layer are genuinely dead code, not
  reachable via any real call graph — verified by tracing, not assumed
  from a coverage report** (in the same spirit as a prior plan's
  correction of a wrong "coverage.py bug" claim — see
  `docs/superpowers/plans/2026-08-02-references-model-validation-tests.md`'s
  Global Constraints):
  - `_format_deep_object_argument_value`'s `elif isinstance(formatted_value,
    typing.Iterable) and not isinstance(formatted_value, str):` branch
    (lines 454-460) can only be reached via this function's own
    recursive self-calls, and every such recursive call returns either
    `None`, a `str` (from `_format_primitive_value`), or a `dict` (the
    function's own `deep_object` return value) — never a bare list or
    tuple. `None` and `str` are excluded by the `elif`'s own condition;
    `dict` is caught by the itemized-type branch immediately above it.
    Not covered by this plan's tests; not chased further.
  - `_format_request_data`'s `if not isinstance(data, collections.abc.
    MutableMapping): raise ValueError(data)` (line 842) immediately
    follows `data = dict(data)` on the line above, and `dict(...)`
    always produces a `dict`, which always is a `MutableMapping` — the
    `raise` can never execute. Not covered by this plan's tests; not
    chased further.
- Verify commands: `hatch run hatch-test.py3.10:pytest
  tests/test_client_argument_formatting.py
  tests/test_client_request_assembly.py
  tests/test_client_retry_and_encoding.py tests/test_client_pickling.py
  -v` (150 tests total: 81 + 38 + 24 + 7, after a final-review fix
  added one test — see Task 2). `hatch run mypy --strict
  --ignore-missing-imports <file>` per file — expect exactly one
  pre-existing, unrelated finding on `tests/servers.py:56`
  (`[str-bytes-safe]`, from the infrastructure plan) whenever
  `servers.py` is imported transitively; nothing else.
- Commit scope: this working tree has unrelated pre-existing staged
  files (`.claude/settings.json`, `.claude/skills/fableplan/SKILL.md`,
  `AGENTS.md`, `.gitignore`) belonging to other work-in-progress —
  **never** include them in a commit. Never a bare `git commit -m
  "..."` — always `git commit <exact-path(s)> -m "..."` (paths before
  `-m`). Never `git add -A`/`.`/`-u`, never `git reset` in any form to
  self-fix a mistake — if a commit's scope looks wrong, stop and report
  it.
- Known, out-of-scope, pre-existing issue: a real `mypy --strict` run
  also flags `tests/servers.py:56` (`[str-bytes-safe]`) whenever
  `servers.py` is imported — unrelated to this plan's files, don't
  touch `tests/servers.py`. Running the full suite (`hatch test -c` or
  `hatch run hatch-test.py3.10:pytest tests/`) has the unrelated,
  pre-existing side effect of `test_languagetool` re-downloading and
  overwriting `tests/input-data/languagetool-swagger.json`; run `git
  checkout -- tests/input-data/languagetool-swagger.json` afterward if
  you ran the full suite, before checking `git status --porcelain`.

---

## Task 1: Add `zstandard`/`brotli` as `hatch-test` env test dependencies

**Files:**
- Modify: `pyproject.toml`

**Interfaces:**
- Consumes: nothing new.
- Produces: a synced `hatch-test.py3.10` environment where `import
  zstandard` and `import brotli` both succeed, needed by Task 3's
  `_encode_content`/`_decode_content` round-trip tests.

- [ ] **Step 1: Add the dependencies**

In `pyproject.toml`, under `[tool.hatch.envs.hatch-test]`, change:

```toml
[tool.hatch.envs.hatch-test]
extra-dependencies = [
    "dependence~=1.4",
    "pyyaml>2",
]
```

to:

```toml
[tool.hatch.envs.hatch-test]
extra-dependencies = [
    "dependence~=1.4",
    "pyyaml>2",
    "zstandard~=0.25",
    "brotli~=1.2; platform_python_implementation == 'CPython'",
    "brotlicffi~=1.2; platform_python_implementation != 'CPython'",
]
```

- [ ] **Step 2: Sync and verify**

Run: `hatch env prune && hatch run hatch-test.py3.10:python -c "import
zstandard, brotli; print('ok')"`
Expected: environment recreates cleanly and prints `ok`. Verified
against the real environment: before this change, both imports raised
`ModuleNotFoundError` in a freshly-synced `hatch-test.py3.10`; after
adding these three lines and re-syncing, both succeed
(`zstandard.__version__` reports `0.25.0` in the verified run).

- [ ] **Step 3: Commit**

```bash
git add pyproject.toml
git commit pyproject.toml -m "test: add zstandard/brotli to hatch-test env for content-encoding coverage"
```

## Task 2: `tests/test_client_argument_formatting.py`

**Files:**
- Create: `tests/test_client_argument_formatting.py`

**Interfaces:**
- Consumes: `oapi.client._iter_items`, `urlencode`, `URLENCODE_SAFE`,
  `_item_is_not_empty`, `_censor_long_json_strings`,
  `_format_primitive_value`, `_format_simple_argument_value`,
  `_format_label_argument_value`, `_format_matrix_argument_value`,
  `_format_space_delimited_argument_value`,
  `_format_pipe_delimited_argument_value`,
  `_format_form_argument_value`, `_format_deep_object_argument_value`,
  `_format_dot_object_argument_value`, `format_argument_value`
  (existing). `oapi.oas.model.Reference` (existing).
- Produces: `tests/test_client_argument_formatting.py`, 81 tests (80
  as originally written, plus one added during final review — see the
  Self-Review section).

- [ ] **Step 1: Write the test file**

Create `tests/test_client_argument_formatting.py`:

```python
from __future__ import annotations

import decimal
from datetime import date, datetime

import pytest
import sob

from oapi.client import (
    URLENCODE_SAFE,
    _censor_long_json_strings,
    _format_deep_object_argument_value,
    _format_dot_object_argument_value,
    _format_form_argument_value,
    _format_label_argument_value,
    _format_matrix_argument_value,
    _format_pipe_delimited_argument_value,
    _format_primitive_value,
    _format_simple_argument_value,
    _format_space_delimited_argument_value,
    _item_is_not_empty,
    _iter_items,
    format_argument_value,
    urlencode,
)
from oapi.oas.model import Reference


def test_iter_items_yields_mapping_items() -> None:
    result: list[tuple[str, object]] = list(_iter_items({"a": 1, "b": 2}))
    assert result == [("a", 1), ("b", 2)]


def test_iter_items_yields_sob_dictionary_items() -> None:
    dictionary: sob.abc.Dictionary = sob.model.Dictionary({"x": 1, "y": 2})
    result: list[tuple[str, object]] = list(_iter_items(dictionary))
    assert result == [("x", 1), ("y", 2)]


def test_iter_items_yields_sob_object_property_values() -> None:
    """
    A `sob.abc.Object` iterates by *property name* (not by JSON key) --
    `Reference`'s `$ref` property is named `ref` internally (since `$ref`
    is not a valid Python identifier), and unset properties (`description`
    here) are yielded too, with a value of `None`.
    """
    reference: Reference = Reference(
        {"$ref": "#/components/schemas/Foo", "summary": "hi"}
    )
    result: list[tuple[str, object]] = list(_iter_items(reference))
    assert result == [
        ("description", None),
        ("ref", "#/components/schemas/Foo"),
        ("summary", "hi"),
    ]


def test_iter_items_yields_from_a_sequence_of_tuples() -> None:
    result: list[tuple[str, object]] = list(_iter_items([("a", 1), ("b", 2)]))
    assert result == [("a", 1), ("b", 2)]


def test_urlencode_bumps_nested_dictionary_values_to_the_top_level() -> None:
    """
    When a query value is itself a dictionary/mapping, `urlencode` merges
    that mapping's items into the top-level query instead of nesting it.
    """
    encoded: str = urlencode({"a": 1, "nested": {"b": 2, "c": 3}})
    assert encoded == "a=1&b=2&c=3"


def test_urlencode_repeats_a_key_for_sequence_values_by_default() -> None:
    encoded: str = urlencode({"a": [1, 2, 3]})
    assert encoded == "a=1&a=2&a=3"


def test_urlencode_default_safe_characters_are_not_percent_encoded() -> None:
    encoded: str = urlencode({"a": "|;,/=+[]."})
    assert encoded == f"a={URLENCODE_SAFE}"


@pytest.mark.parametrize(
    ("item", "expected"),
    [
        (("k", "v"), True),
        (("k", None), False),
        (("k", ""), False),
        (("", "v"), False),
    ],
)
def test_item_is_not_empty(item: tuple[str, object], expected: bool) -> None:
    assert _item_is_not_empty(item) is expected


def test_censor_long_json_strings_replaces_strings_over_the_limit() -> None:
    text: str = '{"short": "ok", "long": "' + ("x" * 3000) + '"}'
    censored: str = _censor_long_json_strings(text)
    assert censored == '{"short": "ok", "long": "..."}'


def test_censor_long_json_strings_leaves_short_strings_untouched() -> None:
    text: str = '{"short": "ok"}'
    assert _censor_long_json_strings(text) == text


def test_censor_long_json_strings_respects_a_custom_limit() -> None:
    text: str = '{"value": "abcdef"}'
    censored: str = _censor_long_json_strings(text, limit=6)
    assert censored == '{"value": "..."}'


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, None),
        ("abc", "abc"),
        (True, "true"),
        (False, "false"),
        (42, "42"),
        (3.14, "3.14"),
        (decimal.Decimal("1.5"), "1.5"),
        (b"hello", "aGVsbG8="),
        (date(2024, 1, 1), "2024-01-01"),
        (datetime(2024, 1, 1, 12, 0, 0), "2024-01-01T12:00:00"),
    ],
)
def test_format_primitive_value(value: object, expected: str | None) -> None:
    assert _format_primitive_value(value) == expected  # type: ignore[arg-type]


def test_format_primitive_value_rejects_unsupported_types() -> None:
    with pytest.raises(TypeError):
        _format_primitive_value(object())  # type: ignore[arg-type]


def test_format_simple_argument_value_with_a_primitive() -> None:
    assert _format_simple_argument_value(5) == "5"


def test_format_simple_argument_value_with_a_sequence() -> None:
    assert _format_simple_argument_value([1, 2, 3]) == "1,2,3"


def test_format_simple_argument_value_with_a_dictionary_not_exploded() -> None:
    assert _format_simple_argument_value({"a": 1, "b": 2}) == "a,1,b,2"


def test_format_simple_argument_value_dict_explode_iterates_dict_keys() -> (
    None
):
    """
    `_format_simple_argument_value`'s exploded-dictionary branch iterates
    `value` directly (`for item in value`), which -- for a plain `dict` --
    yields its *keys*, not `(key, value)` pairs. `item[0]`/`item[1]` then
    index into that key string rather than a tuple. This only avoids
    crashing when every key is at least 2 characters long, and the
    "value" half of the output is actually the second character of the
    key, not the dictionary's mapped value. This is real, current
    behavior of the function -- documented here, not corrected.
    """
    result: str = _format_simple_argument_value(
        {"ab": 1, "cd": 2}, explode=True
    )
    assert result == "a=b,c=d"


def test_format_simple_argument_value_dict_explode_crashes_on_short_keys() -> (
    None
):
    with pytest.raises(IndexError):
        _format_simple_argument_value({"a": 1, "b": 2}, explode=True)


def test_format_simple_argument_value_rejects_unsupported_types() -> None:
    with pytest.raises(ValueError, match=".*"):
        _format_simple_argument_value(object())  # type: ignore[arg-type]


def test_format_label_argument_value_with_a_primitive() -> None:
    assert _format_label_argument_value(5) == ".5"


def test_format_label_argument_value_with_a_sequence_not_exploded() -> None:
    assert _format_label_argument_value([1, 2, 3]) == ".1,2,3"


def test_format_label_argument_value_with_a_sequence_exploded() -> None:
    assert _format_label_argument_value([1, 2, 3], explode=True) == ".1.2.3"


def test_format_label_argument_value_dict_explode_shares_the_dict_quirk() -> (
    None
):
    with pytest.raises(IndexError):
        _format_label_argument_value({"a": 1, "b": 2}, explode=True)


def test_format_label_argument_value_rejects_unsupported_exploded_types() -> (
    None
):
    with pytest.raises(ValueError, match=".*"):
        _format_label_argument_value(object(), explode=True)  # type: ignore[arg-type]


def test_format_matrix_argument_value_with_none() -> None:
    assert _format_matrix_argument_value("id", None) is None


def test_format_matrix_argument_value_with_a_primitive() -> None:
    assert _format_matrix_argument_value("id", 5) == ";id=5"


def test_format_matrix_argument_value_with_a_sequence_exploded() -> None:
    result = _format_matrix_argument_value("id", [3, 4, 5], explode=True)
    assert result == ";id=3;id=4;id=5"


def test_format_matrix_argument_value_with_a_sequence_not_exploded() -> None:
    result = _format_matrix_argument_value("id", [3, 4, 5], explode=False)
    assert result == ";id=3,4,5"


def test_format_matrix_argument_value_dict_explode_shares_the_dict_quirk() -> (
    None
):
    """
    Like `_format_simple_argument_value`, the exploded-dictionary branch
    here also does `for item in value` over a plain `dict`, hitting the
    same "iterates keys, not pairs" issue when a key is a single
    character.
    """
    with pytest.raises(IndexError):
        _format_matrix_argument_value("id", {"a": 1, "b": 2}, explode=True)


def test_format_matrix_argument_value_rejects_unsupported_exploded_types() -> (
    None
):
    with pytest.raises(TypeError):
        _format_matrix_argument_value("id", object(), explode=True)  # type: ignore[arg-type]


def test_format_space_delimited_argument_value_with_a_primitive() -> None:
    assert _format_space_delimited_argument_value(5) == "5"


def test_format_space_delimited_argument_value_with_a_sequence() -> None:
    assert _format_space_delimited_argument_value([1, 2, 3]) == "1 2 3"


def test_format_space_delimited_argument_value_explode_uses_form() -> None:
    result = _format_space_delimited_argument_value([1, 2, 3], explode=True)
    assert result == ("1", "2", "3")


def test_format_space_delimited_argument_value_rejects_non_sequences() -> None:
    with pytest.raises(ValueError, match=".*"):
        _format_space_delimited_argument_value({"a": 1}, explode=False)


def test_format_pipe_delimited_argument_value_with_a_primitive() -> None:
    assert _format_pipe_delimited_argument_value(None) is None
    assert _format_pipe_delimited_argument_value(5) == "5"


def test_format_pipe_delimited_argument_value_with_a_sequence() -> None:
    assert _format_pipe_delimited_argument_value([1, 2, 3]) == "1|2|3"


def test_format_pipe_delimited_argument_value_exploded_delegates_to_form() -> (
    None
):
    result = _format_pipe_delimited_argument_value([1, 2, 3], explode=True)
    assert result == ("1", "2", "3")


def test_format_pipe_delimited_argument_value_rejects_non_sequences() -> None:
    with pytest.raises(ValueError, match=".*"):
        _format_pipe_delimited_argument_value({"a": 1}, explode=False)


def test_format_form_argument_value_with_a_primitive() -> None:
    assert _format_form_argument_value(5) == "5"


def test_format_form_argument_value_with_a_sequence_not_exploded() -> None:
    assert _format_form_argument_value([1, 2, 3]) == "1,2,3"


def test_format_form_argument_value_with_a_sequence_exploded() -> None:
    result = _format_form_argument_value([1, 2, 3], explode=True)
    assert result == ("1", "2", "3")


def test_format_form_argument_value_with_a_dictionary_exploded() -> None:
    """
    Unlike the "simple"/"label"/"matrix" formatters, `_format_form_
    argument_value` recognizes a plain `dict` as one of `_ITEMIZED_TYPES`
    and uses `_iter_items`, so exploding a dictionary correctly yields
    `(key, value)` pairs rather than iterating its keys.
    """
    result = _format_form_argument_value({"a": 1, "b": 2}, explode=True)
    assert result == {"a": "1", "b": "2"}


def test_format_form_argument_value_exploded_merges_duplicate_keys() -> None:
    result = _format_form_argument_value(
        [("a", 1), ("a", 2), ("b", 3)], explode=True
    )
    assert result == {"a": ["1", "2"], "b": "3"}


def test_format_form_argument_value_exploded_appends_a_third_duplicate() -> (
    None
):
    """
    A third occurrence of the same key exercises the "already collected
    into a list" append branch, distinct from the second occurrence
    (which converts a scalar into a two-item list).
    """
    result = _format_form_argument_value(
        [("a", 1), ("a", 2), ("a", 3)], explode=True
    )
    assert result == {"a": ["1", "2", "3"]}


def test_format_form_argument_value_rejects_unsupported_exploded_types() -> (
    None
):
    with pytest.raises(ValueError, match=".*"):
        _format_form_argument_value(object(), explode=True)  # type: ignore[arg-type]


def test_format_deep_object_argument_value_with_none() -> None:
    assert _format_deep_object_argument_value("id", None) is None


def test_format_deep_object_argument_value_with_a_primitive() -> None:
    assert _format_deep_object_argument_value("id", 5) == "5"


def test_format_deep_object_argument_value_requires_explode() -> None:
    with pytest.raises(ValueError, match="only supports `explode=True`"):
        _format_deep_object_argument_value("id", {"a": 1}, explode=False)


def test_format_deep_object_argument_value_with_a_flat_dictionary() -> None:
    result = _format_deep_object_argument_value(
        "id", {"a": 1, "b": 2}, explode=True
    )
    assert result == {"id[a]": "1", "id[b]": "2"}


def test_format_deep_object_argument_value_with_a_nested_dictionary() -> None:
    result = _format_deep_object_argument_value(
        "id", {"a": {"b": 1}}, explode=True
    )
    assert result == {"id[a][b]": "1"}


def test_format_deep_object_argument_value_dict_of_sequence_is_broken() -> (
    None
):
    """
    A dictionary value whose entry is itself a sequence of primitives
    (rather than a sequence of dictionaries) hits a genuine bug: the
    recursive call for each primitive item returns a plain formatted
    string (e.g. `"1"`), and the caller then does
    `deep_object.update(**that_string)`, which fails because a `str` is
    not a mapping. This is real, current behavior -- documented here, not
    corrected.
    """
    with pytest.raises(TypeError, match="argument after \\*\\*"):
        _format_deep_object_argument_value("id", {"a": [1, 2]}, explode=True)


def test_format_deep_object_argument_value_dict_rejects_bad_types() -> None:
    with pytest.raises(TypeError):
        _format_deep_object_argument_value("id", {"a": object()}, explode=True)


def test_format_deep_object_argument_value_with_a_sequence_of_primitives() -> (
    None
):
    result = _format_deep_object_argument_value("id", [1, 2, 3], explode=True)
    assert result == {"id[0]": "1", "id[1]": "2", "id[2]": "3"}


def test_format_deep_object_argument_value_with_a_sequence_of_dicts() -> None:
    result = _format_deep_object_argument_value(
        "id", [{"a": 1}, {"b": 2}], explode=True
    )
    assert result == {"id[0][a]": "1", "id[1][b]": "2"}


def test_format_deep_object_argument_value_with_nested_sequences() -> None:
    result = _format_deep_object_argument_value(
        "id", [[1, 2], [3, 4]], explode=True
    )
    assert result == {
        "id[0][0]": "1",
        "id[0][1]": "2",
        "id[1][0]": "3",
        "id[1][1]": "4",
    }


def test_format_deep_object_argument_value_rejects_a_non_sequence() -> None:
    """
    A value that is neither a primitive, an itemized type (dict/Object),
    nor a `collections.abc.Sequence` -- e.g. a `set` -- falls through to
    the function's final `raise ValueError(value)`. This is a real,
    reachable guard (unlike the two lines noted as dead code in Global
    Constraints), just not exercised by any of the styles' other tests,
    since query/path/header argument values are otherwise always a
    primitive, mapping, or sequence.
    """
    with pytest.raises(ValueError, match=".*"):
        _format_deep_object_argument_value("id", {1, 2}, explode=True)


def test_format_dot_object_argument_value_uses_dot_notation() -> None:
    result = _format_dot_object_argument_value(
        "id", {"a": {"b": 1}}, explode=True
    )
    assert result == {"id.a.b": "1"}


@pytest.mark.parametrize(
    ("style", "value", "explode", "expected"),
    [
        ("simple", 5, False, "5"),
        ("label", 5, False, ".5"),
        ("matrix", 5, False, ";id=5"),
        ("form", [1, 2], False, "1,2"),
        ("spaceDelimited", [1, 2], False, "1 2"),
        ("pipeDelimited", [1, 2], False, "1|2"),
    ],
)
def test_format_argument_value_dispatches_by_style(
    style: str, value: object, explode: bool, expected: object
) -> None:
    assert (
        format_argument_value("id", value, style, explode=explode)  # type: ignore[arg-type]
        == expected
    )


def test_format_argument_value_dispatches_deep_object_and_dot_object() -> None:
    assert format_argument_value(
        "id", {"a": 1}, "deepObject", explode=True
    ) == {"id[a]": "1"}
    assert format_argument_value(
        "id", {"a": 1}, "dotObject", explode=True
    ) == {"id.a": "1"}


def test_format_argument_value_rejects_an_unknown_style() -> None:
    with pytest.raises(ValueError, match="bogus"):
        format_argument_value("id", 5, "bogus")


def test_format_argument_value_marshals_a_sob_model_first() -> None:
    reference: Reference = Reference({"$ref": "#/x"})
    assert format_argument_value("id", reference, "simple") == "$ref,#/x"


def test_format_argument_value_multipart_bypasses_formatting_for_bytes() -> (
    None
):
    assert (
        format_argument_value("id", b"raw bytes", "simple", multipart=True)
        == b"raw bytes"
    )


def test_format_argument_value_multipart_bypasses_a_readable() -> None:
    import io

    readable: io.BytesIO = io.BytesIO(b"data")
    assert (
        format_argument_value("id", readable, "simple", multipart=True)
        is readable
    )


def test_format_argument_value_multipart_bypasses_a_sequence_of_bytes() -> (
    None
):
    value: list[bytes] = [b"a", b"b"]
    assert (
        format_argument_value("id", value, "simple", multipart=True) is value
    )
```

- [ ] **Step 2: Verify**

Run:
```bash
hatch run hatch-test.py3.10:pytest tests/test_client_argument_formatting.py -v
hatch run mypy --strict --ignore-missing-imports tests/test_client_argument_formatting.py
hatch fmt --formatter
hatch fmt --check
```
Expected: 81 passed (80 as originally written, plus
`test_format_deep_object_argument_value_rejects_a_non_sequence`, added
during final review — see Self-Review); mypy `Success: no issues found
in 1 source file`; `hatch fmt --check` clean. All were verified against
the real library while this file was authored — every assertion's
expected value was produced by actually calling the real function, not
predicted.

- [ ] **Step 3: Commit**

```bash
git add tests/test_client_argument_formatting.py
git commit tests/test_client_argument_formatting.py -m "test: add coverage for client.py's argument-value formatting functions"
```

## Task 3: `tests/test_client_request_assembly.py`

**Files:**
- Create: `tests/test_client_request_assembly.py`

**Interfaces:**
- Consumes: `oapi.client._assemble_request`, `_format_request_data`,
  `_get_file_name`, `_get_first`, `_remove_none`,
  `_represent_http_response`, `_set_response_callback`,
  `get_request_curl`, `urlencode` (existing). `oapi._multipart_request.
  MultipartRequest`, `Part` (existing). `oapi.oas.model.Reference`
  (existing). `tests/servers.py`'s `Response`, `http_test_server`
  (existing, from the infrastructure plan).
- Produces: `tests/test_client_request_assembly.py`, 38 tests.

- [ ] **Step 1: Write the test file**

Create `tests/test_client_request_assembly.py`:

```python
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
```

- [ ] **Step 2: Verify**

Run:
```bash
hatch run hatch-test.py3.10:pytest tests/test_client_request_assembly.py -v
hatch run mypy --strict --ignore-missing-imports tests/test_client_request_assembly.py
hatch fmt --formatter
hatch fmt --check
```
Expected: 38 passed; mypy `Success: no issues found in 1 source file`
(`_assemble_request`'s declared return type is the base `Request`, so
each multipart assertion `typing.cast`s to the real runtime type,
`MultipartRequest`, before accessing `.parts`/`.headers` — both of
which are themselves `Optional`-typed on the real classes even though
they're never actually `None` for a request built with real `parts`/
`headers` arguments, hence the `assert ... is not None` narrowing
lines); `hatch fmt --check` clean.

- [ ] **Step 3: Commit**

```bash
git add tests/test_client_request_assembly.py
git commit tests/test_client_request_assembly.py -m "test: add coverage for client.py's request/response assembly helpers"
```

## Task 4: `tests/test_client_retry_and_encoding.py`

**Files:**
- Create: `tests/test_client_retry_and_encoding.py`

**Interfaces:**
- Consumes: `oapi.client._decode_content`, `_encode_content`,
  `default_retry_hook`, `retry` (existing).
- Produces: `tests/test_client_retry_and_encoding.py`, 24 tests.
- Requires: Task 1 (`zstandard`/`brotli` in `hatch-test`).

- [ ] **Step 1: Write the test file**

Create `tests/test_client_retry_and_encoding.py`:

```python
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
```

- [ ] **Step 2: Verify**

Run:
```bash
hatch run hatch-test.py3.10:pytest tests/test_client_retry_and_encoding.py -v
hatch run mypy --strict --ignore-missing-imports tests/test_client_retry_and_encoding.py
hatch fmt --formatter
hatch fmt --check
```
Expected: 24 passed in roughly 6 seconds (the real-time cost of five
retry-related tests each sleeping ~2 seconds once); mypy `Success: no
issues found in 1 source file`; `hatch fmt --check` clean. Both `zstd`
and `br`/`dcb`/`dcz` round-trips genuinely exercise real
`zstandard`/`brotli` compression — confirmed by checking `len(encoded)
< len(data)` (a real compression ratio on repetitive input), not merely
that no exception was raised.

- [ ] **Step 3: Commit**

```bash
git add tests/test_client_retry_and_encoding.py
git commit tests/test_client_retry_and_encoding.py -m "test: add coverage for client.py's retry decorator and content encoding"
```

## Task 5: `tests/test_client_pickling.py`

**Files:**
- Create: `tests/test_client_pickling.py`

**Interfaces:**
- Consumes: `oapi.client.SSLContext`, `_make_http_errors_pickleable`,
  `_make_loggers_pickleable`, `_make_thread_locks_pickleable`
  (existing).
- Produces: `tests/test_client_pickling.py`, 7 tests.

- [ ] **Step 1: Write the test file**

Create `tests/test_client_pickling.py`:

```python
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
```

- [ ] **Step 2: Verify**

Run:
```bash
hatch run hatch-test.py3.10:pytest tests/test_client_pickling.py -v
hatch run mypy --strict --ignore-missing-imports tests/test_client_pickling.py
hatch fmt --formatter
hatch fmt --check
```
Expected: 7 passed; mypy `Success: no issues found in 1 source file`
(note `HTTPError`'s fourth positional parameter is typed as
`email.message.Message[str, str]`, not `dict`/`None` — a real `Message`
instance is constructed rather than passing a plain `dict` or `None`,
both of which are real mypy errors against the actual stub); `hatch fmt
--check` clean.

- [ ] **Step 3: Commit**

```bash
git add tests/test_client_pickling.py
git commit tests/test_client_pickling.py -m "test: add coverage for client.py's pickling helpers and SSLContext"
```

## Task 6: Whole-plan verification

**Files:**
- None modified (verification only).

- [ ] **Step 1: Run every new file together, plus the full existing suite**

```bash
hatch run hatch-test.py3.10:pytest tests/test_client_argument_formatting.py tests/test_client_request_assembly.py tests/test_client_retry_and_encoding.py tests/test_client_pickling.py -v
hatch run hatch-test.py3.10:pytest tests/ -q
git checkout -- tests/input-data/languagetool-swagger.json
```
Expected: 149 passed for the four new files together; 273+ passed for
the full suite (273 was the full-suite count immediately before this
plan's tests existed); no interference between the new files and any
pre-existing test (verified together, not just individually, since
`retry`'s real `warnings.warn` calls or the real `http_test_server`
instances could in principle interact with other tests' global state —
they don't, confirmed).

- [ ] **Step 2: Confirm the coverage delta**

```bash
hatch run hatch-test.py3.10:coverage run -m pytest tests/test_client_argument_formatting.py tests/test_client_request_assembly.py tests/test_client_retry_and_encoding.py tests/test_client_pickling.py -q
hatch run hatch-test.py3.10:coverage report -m --include="*/client.py"
```
Expected: `src/oapi/client.py` moves from 18% to roughly 38% (whole-file
percentage — the pure-function layer, lines 109-1064, is the first
quarter of a 4039-line file dominated by the `Client` and `ClientModule`
classes covered in later plans). Remaining "Missing" lines below 1215
should be limited to `457-460, 842` — the two confirmed-dead-code
lines from Global Constraints — everything else in the pure-function
layer should show as covered, including line 465 (a real, reachable
`raise ValueError(value)` for non-primitive/non-itemized/non-sequence
input such as a `set`, initially miscategorized as dead alongside
454-460 and corrected during final review — see Task 2's
`test_format_deep_object_argument_value_rejects_a_non_sequence`).

- [ ] **Step 3: Update project memory**

Update the `project-oapi-test-coverage-initiative` memory file to note
this plan complete and move to the next step (the `Client` runtime
plan), per the standing blanket-execution-approval instruction — no
user confirmation needed for this step.

---

## Self-Review

**1. Spec coverage:** The spec's step 4 ("`client.py` argument-formatting
+ content-encoding") is fully addressed: every function in the
pure-function layer (`_iter_items` at line 109 through `_get_first` at
line 1064) has a test, across the four files. The two small
module-level helper classes/registrars that live in this same region
(`SSLContext`, the three `_make_*_pickleable` functions) are covered in
Task 5. `retry`'s exponential backoff — the one place genuine wall-clock
time is unavoidable without mocking — is tested with real timing
assertions, consolidated to minimize total real time spent. Content
encoding is tested against all four real codecs the source supports
(`gzip`, `deflate`, `zstd`, `br`, plus the `dcb`/`dcz` brotli aliases),
which required closing a real gap in the `hatch-test` environment
(Task 1) rather than skipping those branches.

**2. Placeholder scan:** No "TBD"/"add appropriate handling"/"similar to
Task N" language. Every line of test code in every task was executed
against the real library before being written into this document — not
just once per function, but as the exact final file content, re-run
after every fix. Five genuine test-authoring mistakes were caught this
way before they ever reached this plan (two wrong expected values for
`_format_deep_object_argument_value`/`_censor_long_json_strings` in
Task 2; a `Parts`/`Headers` subscript assumption and an over-quoted
`shlex.quote` expectation in Task 3; an invalid `dict`-typed `HTTPError`
header argument in Task 5) — all fixed by re-running against the real
functions, not by adjusting the functions to match a wrong guess. Five
genuine *source* behaviors (not test bugs) were discovered and are
documented as real, current behavior in Global Constraints rather than
"corrected": three separate dict-iteration quirks shared across
`_format_simple_argument_value`/`_format_label_argument_value`/
`_format_matrix_argument_value`, `_format_deep_object_argument_value`'s
crash on a dict-of-primitive-sequence value, `_encode_content`'s broken
comma-separated multi-encoding branch, and `_assemble_request`'s
URL-scheme guard not guaranteeing a constructible `Request`. Two lines
were traced and confirmed genuinely dead code and are explicitly left
uncovered rather than contorted around. A third line (465, the same
function's final `raise ValueError(value)` fallback) was *initially*
lumped in with those two as dead in an earlier draft — this was wrong,
caught by the opus final-branch review, and independently
re-confirmed by the controller with a live `hatch run
hatch-test.py3.10:python -` probe (`_format_deep_object_argument_value
("id", {1, 2}, explode=True)` really does raise `ValueError` at line
465, since a `set` is neither a primitive, an itemized type, nor a
`Sequence`). Rather than repeating the prior plan's mistake of leaving
a real, reachable line undertested, `test_format_deep_object_
argument_value_rejects_a_non_sequence` was added to Task 2 (bringing
its count to 81) to cover it. This is the second time in this
initiative a "coverage gap must be dead code" claim was wrong; both
times the fix was the same — trace the real call graph (or run the
real function) rather than trust the first plausible explanation, and
when a claim turns out wrong, add the missing test rather than just
correcting the prose.

**3. Type consistency:** Each of the four files declares its own
complete import block (no cross-file imports between the new test
files); `Reference` is imported identically in Tasks 2 and 3 wherever
needed. `MultipartRequest`/`Part` are imported once in Task 3 and used
consistently for every multipart assertion via the same `typing.cast`
pattern. `Message[str, str]` in Task 5 is the one deliberate,
documented exception to "always annotate with the obvious type" (see
Global Constraints) — used nowhere else in this plan.

---

**Plan complete and saved to
`docs/superpowers/plans/2026-08-02-client-argument-formatting-tests.md`.**
Per the standing blanket authorization for this initiative
([[feedback-autonomous-plan-execution]]), proceeding directly to
subagent-driven execution on branch `test-coverage` without further
confirmation.
