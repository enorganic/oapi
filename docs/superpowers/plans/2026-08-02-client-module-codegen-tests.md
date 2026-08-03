# ClientModule Code Generation Tests Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task-by-task. Steps
> use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bring `src/oapi/client.py`'s `ClientModule` class (lines
2284-3963, ~1680 lines -- the OpenAPI-to-Python-client code generator,
the largest remaining chunk of this module) and the free functions
immediately above it (lines 1929-2281 -- naming/import/parameter-
representation helpers `ClientModule` itself calls) from 56% to a
substantially higher whole-file coverage on `client.py`, per
`docs/superpowers/specs/2026-08-01-test-coverage-design.md`'s step 6
("`client.py` `ClientModule` code generation").

**Architecture:** This plan uses a fundamentally different testing
strategy than the three prior `client.py` plans. `ClientModule` has
~50 private methods, almost all of which assemble fragments of
generated Python *source text* -- unit-testing each one in isolation
would mean asserting exact generated-source-string output, which is
brittle and largely tautological (the same "testing that generated
code says what the generator says" problem already excluded for
`ModelModule`-generated constructor boilerplate in an earlier plan).
Instead, this plan tests `ClientModule` **black-box, through its real
output**: for each of the four purpose-built OpenAPI fixtures already
sitting unused in `tests/input-data/` since the infrastructure plan
(`parameter-styles.json`, `security-schemes.json`,
`multipart-request-body.json`, `polymorphic-schemas.json` -- each
fixture's own `description` field already states it exists "for
testing `oapi.client`... code-generation and runtime behavior
end-to-end"), this plan generates a **real model module and a real
client module**, loads them as a real importable Python package,
instantiates the generated `Client` subclass, and calls its generated
methods against the real `http_test_server` -- verifying the actual
HTTP request that reaches the server (path, query, headers, cookies,
body) and the actual deserialized response. This single black-box
pass, across the four fixtures, transitively exercises the overwhelming
majority of `ClientModule`'s ~50 private methods (parameter-style
representation, security-scheme-derived `__init__` defaults, OAuth2
flow handling, multipart form-data assembly, polymorphic response type
resolution, method naming) at once -- confirmed by the coverage delta
in Task 8 below (56% → 83%, file-wide). A small number of the
free functions above `ClientModule` (Task 3) are additionally isolable
enough to unit-test directly.

Five new test files:

- `tests/test_client_module_helpers.py` -- direct unit tests for the
  isolable free functions: `_get_relative_module_path`, `_get_relative_
  module_import`, `_schema_defines_model`, `_iter_path_item_operations`,
  `get_default_method_name_from_path_method_operation`, `_strip_def_
  decorators`.
- `tests/test_client_module_parameter_styles.py` -- generates a real
  client from `parameter-styles.json` and executes every one of its 9
  operations (path `simple`/`label`/`matrix` styles, query `form`/
  `spaceDelimited`/`pipeDelimited`/`deepObject` styles, header `simple`
  style, cookie `form` style) against `http_test_server`, asserting the
  real path/query/header/cookie that reaches the server.
- `tests/test_client_module_security_schemes.py` -- generates a real
  client from `security-schemes.json`, asserts the generated `__init__`
  bakes in the right defaults for API-key location/name and OAuth2/OIDC
  URLs, and executes the API-key (header/query/cookie) and Bearer
  operations end-to-end.
- `tests/test_client_module_multipart.py` -- generates a real client
  from `multipart-request-body.json` and documents a real bug (see
  Global Constraints).
- `tests/test_client_module_polymorphic_responses.py` -- generates a
  real client from `polymorphic-schemas.json` and executes its four
  operations, asserting `allOf`-merged, `oneOf`-resolved,
  `anyOf`-resolved, and `additionalProperties`-dictionary responses all
  deserialize to the correct real model type.

Plus two small supporting changes:

- `tests/conftest.py` gains a new `generated_client_package` fixture
  (Task 2) -- `generated_module_loader` (from the infrastructure plan)
  loads a *single* generated file, but a generated client module always
  contains a package-relative `from . import model` import, so it must
  be loaded as part of a real package. This fixture generates a real
  model + client module pair into a real temporary package directory,
  imports both, and cleans up `sys.modules`/`sys.path` afterward.
- `tests/input-data/security-schemes.json` gains one real schema (Task
  1) -- as originally authored (infrastructure plan), every response in
  this fixture was a bare `{"type": "object"}` with no named
  `components/schemas` entry, which triggers a real, separate
  `ModelModule` bug (an empty-schema OpenAPI document generates a
  `model.py` missing a needed `sob` import, raising `NameError` on
  import -- out of `client.py`'s scope, noted for a future `model.py`
  plan). Adding one minimal named schema (`ProtectedResource`) and
  referencing it from one response unblocks generating a genuinely
  loadable/runnable package from this fixture without touching
  `model.py`.

**Tech Stack:** Python 3.10, `pytest`, stdlib (`importlib`, `inspect`),
`oapi.model.ModelModule`, `oapi.client.ClientModule` (the systems under
test, used as real code generators, not mocked), `tests/servers.py`'s
`http_test_server`.

## Global Constraints

- Line length 79 (ruff + black), enforced via `hatch fmt --check`.
- mypy strict on `tests/`: explicit type annotations on every local
  variable, per this project's standing preference. All code verified
  against a real `hatch run mypy --strict --ignore-missing-imports`
  run. Generated-module attribute access (`client_module.Client`,
  `model_module.Pet`, etc.) is necessarily untyped -- the modules are
  loaded dynamically via `importlib`, so mypy sees `ModuleType` and
  treats attribute access as `Any` -- this is not a new exception to
  the annotation rule, it's the same dynamic-loading pattern already
  used (and already accepted by `mypy --strict`) for `generated_module_
  loader` in prior plans.
- Prefer real integration over mocks: no `unittest.mock`/`pytest-mock`
  anywhere in any of the five new files. Every test in this plan
  generates real source code with the real `ModelModule`/`ClientModule`
  generators, executes it as a real imported Python package, and (for
  four of the five files) makes real HTTP calls against the real
  `http_test_server`. This is the most "real integration" plan in the
  initiative so far -- no OpenAPI construct is faked; every fixture is
  a real, validated `OpenAPI` document.
- **Four verified, real, currently-unfixed bugs found while validating
  this plan's tests (do not deviate from the specified test code trying
  to "fix" them -- document, don't correct)**:
  1. **`matrix`-style path parameters are completely broken in every
     generated client.** `_represent_dictionary_parameter` (client.py)
     prepends the matrix delimiter to the *dictionary key* used for
     string formatting (`";id"`, since `_format_matrix_argument_value`'s
     own output already includes the full `;id=value` fragment), but
     the generated path template's `str.format(**{...})` placeholder
     is still the bare `{id}` from the OpenAPI path --
     `"{id}".format(**{";id": ...})` cannot find an `"id"` key in
     the kwargs dict it was given and raises `KeyError`. Verified live:
     `client.get_path_matrix_id(id_=[1, 2, 3])` against a real
     generated client raises `KeyError: \'id\'` every time. Documented
     in `tests/test_client_module_parameter_styles.py`'s
     `test_path_matrix_style_raises_key_error`.
  2. **A generated client cannot be instantiated with its own defaults
     whenever its OpenAPI document names a multi-word OAuth2 flow**
     (`authorizationCode`/`clientCredentials` -- i.e. most real-world
     OAuth2 specs). `_iter_oauth2_flows` reads flow-type names via
     `sob.utilities.iter_properties_values(security_scheme.flows)`,
     which yields the Python-side snake_case *property* names of the
     generated `OAuthFlows` model (`"authorization_code"`) rather than
     the OpenAPI spec's own camelCase flow-type identifiers
     (`"authorizationCode"`) that `Client.__init__`'s own validation
     requires. The baked-in default `oauth2_flows` tuple therefore
     fails that validation immediately on construction. Verified live:
     `Client(url="http://example.com")` (no override) against a real
     generated client raises `ValueError` every time; the identical
     construction with an explicit, valid `oauth2_flows=(...)` succeeds.
     Documented in `tests/test_client_module_security_schemes.py`'s
     `test_default_oauth2_flows_value_is_invalid`; every other test in
     that file works around it with an explicit override, exactly as a
     real caller currently must.
  3. **Every generated multipart operation is unusable**, for the same
     reason documented in the prior plan
     (`docs/superpowers/plans/2026-08-02-client-runtime-tests.md`'s
     Global Constraints): `_request_callback` calls `request.headers.
     get("Content-encoding")` expecting ordinary `dict.get` semantics,
     but a `MultipartRequest`'s custom `Headers` object re-raises
     `KeyError` when the key is missing (as it always is for an
     ordinary multipart request) and no `default` is passed. Verified
     live against a real *generated* multipart method (not just
     `Client.request()` directly, as the prior plan tested) --
     `client.post_upload(file=b"...", description="...", tags=[...])`
     raises `KeyError: \'Content-encoding\'` every time. Documented in
     `tests/test_client_module_multipart.py`.
  4. **A narrower, separate `ModelModule` bug** (not `ClientModule`'s;
     noted here because it was discovered while building this plan's
     test fixtures, and blocks generating a runnable package from an
     OpenAPI document with no named `components/schemas`): the
     generated `model.py`'s trailing `_POINTERS_CLASSES: dict[str,
     type[sob.abc.Model]] = {}` line references `sob.abc.Model` in a
     variable annotation, but when a document defines no real model
     classes, `ModelModule` omits both `from __future__ import
     annotations` and `import sob` from the generated file (since
     nothing *else* in the file needs them) -- so that one remaining
     reference raises `NameError: name \'sob\' is not defined` on
     import. Worked around here (Task 1) by giving `security-
     schemes.json` one real named schema rather than by fixing
     `ModelModule` (out of `client.py`'s scope) -- noted for whoever
     picks up the `model.py`/`ModelModule` plan next.
  All four are real, reproducible defects in `oapi`, flagged directly
  to the user in conversation, not just recorded here.
- **Codegen naming default worth knowing, not a bug**: `ClientModule`'s
  `use_operation_id` parameter defaults to `False`, so even when an
  OpenAPI operation has an explicit `operationId`, generated method
  names default to being derived from the path and HTTP method instead
  (`get_protected_api_key_header`, not `get_api_key_header`) --
  `get_default_method_name_from_path_method_operation` (tested directly
  in Task 3) is the function responsible, and it's exercised in its
  default (`use_operation_id=False`) configuration by every integration
  test in this plan, matching how `ClientModule`/`write_client_module`
  actually behave without an explicit override.
- **Deliberately out of scope for this plan** (diminishing returns,
  chased and found not worth it): `ClientModule`'s many optional
  customization parameters not exercised by a default `ClientModule(open_api,
  model_path=...)` call -- `imports`, `init_decorator`,
  `include_init_parameters`, `add_init_parameters`, `add_init_parameter_
  docs`, `init_parameter_defaults`/`init_parameter_defaults_source`,
  `use_operation_id`, `module_docstring`, `class_docstring` -- and the
  deprecated `Module`/`write_client_module` aliases. Each is a
  real, independent feature, but covering all of them would mean many
  more generate-and-load round trips for configuration options with no
  fixture built to specifically exercise them; the coverage delta
  already achieved (Task 8) demonstrates the four existing fixtures
  already exercise the overwhelming majority of `ClientModule`'s real
  logic. Not chased further in this plan.
- Verify commands: `hatch run hatch-test.py3.10:pytest
  tests/test_client_module_helpers.py
  tests/test_client_module_parameter_styles.py
  tests/test_client_module_security_schemes.py
  tests/test_client_module_multipart.py
  tests/test_client_module_polymorphic_responses.py -v` (34 tests
  total: 13 + 9 + 7 + 1 + 4). `hatch run mypy --strict
  --ignore-missing-imports <file>` per file -- expect exactly one
  pre-existing, unrelated finding on `tests/servers.py:56`
  (`[str-bytes-safe]`) whenever `servers.py` is imported transitively;
  nothing else.
- Commit scope: this working tree has unrelated pre-existing staged
  files (`.claude/settings.json`, `.claude/skills/fableplan/SKILL.md`,
  `AGENTS.md`, `.gitignore`) belonging to other work-in-progress --
  **never** include them in a commit. Never a bare `git commit -m
  "..."` -- always `git commit <exact-path(s)> -m "..."` (paths before
  `-m`). Never `git add -A`/`.`/`-u`, never `git reset` in any form to
  self-fix a mistake -- if a commit's scope looks wrong, stop and
  report it. Never touch `tests/servers.py`, `src/oapi/client.py`, or
  `src/oapi/model.py` -- this is a test-only (plus one fixture-data)
  initiative.
- Known, out-of-scope, pre-existing issue: running the full suite
  (`hatch test -c` or `hatch run hatch-test.py3.10:pytest tests/`) has
  the unrelated, pre-existing side effect of `test_languagetool`
  re-downloading and overwriting `tests/input-data/languagetool-
  swagger.json`; run `git checkout -- tests/input-data/languagetool-
  swagger.json` afterward if you ran the full suite, before checking
  `git status --porcelain`.

---

## Task 1: Add a real schema to `security-schemes.json`

**Files:**
- Modify: `tests/input-data/security-schemes.json`

**Interfaces:**
- Consumes: nothing new.
- Produces: a `security-schemes.json` that `ModelModule` can turn into
  a genuinely importable `model.py` (see Global Constraints, bug 4).

- [ ] **Step 1: Replace the file**

Replace the full contents of `tests/input-data/security-schemes.json`
with:

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
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/ProtectedResource"
                }
              }
            }
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
    "schemas": {
      "ProtectedResource": {
        "type": "object",
        "properties": {
          "name": {"type": "string"}
        }
      }
    },
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

(The only changes from the infrastructure-plan version: a new
`components.schemas.ProtectedResource` object schema, and the
`/protected/api-key-header` operation's `200` response now references
it via `$ref` instead of an inline bare `{"type": "object"}`.)

- [ ] **Step 2: Verify**

Run:
```bash
python3 -m json.tool tests/input-data/security-schemes.json > /dev/null && echo "valid JSON"
```
Expected: `valid JSON`. Full end-to-end verification (that this
actually produces a loadable package) happens in Task 5.

- [ ] **Step 3: Commit**

```bash
git add tests/input-data/security-schemes.json
git commit tests/input-data/security-schemes.json -m "test: add a named schema to the security-schemes fixture so it generates a loadable model module"
```

## Task 2: Add the `generated_client_package` fixture

**Files:**
- Modify: `tests/conftest.py`

**Interfaces:**
- Consumes: `oapi.client.ClientModule`, `oapi.model.ModelModule`,
  `oapi.oas.model.OpenAPI` (existing).
- Produces: a new `generated_client_package` pytest fixture, consumed
  by every other task in this plan.

- [ ] **Step 1: Replace the file**

Replace the full contents of `tests/conftest.py` with:

```python
from __future__ import annotations

import importlib
import importlib.util
import sys
from collections.abc import Callable, Iterator
from pathlib import Path
from types import ModuleType

import pytest

from oapi.client import ClientModule
from oapi.model import ModelModule
from oapi.oas.model import OpenAPI


@pytest.fixture
def generated_module_loader(
    tmp_path: Path,
) -> Iterator[Callable[..., ModuleType]]:
    loaded_module_names: list[str] = []

    def load(source: str, module_name: str = "generated_module") -> ModuleType:
        module_path = tmp_path / f"{module_name}.py"
        module_path.write_text(source)
        spec = importlib.util.spec_from_file_location(module_name, module_path)
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


@pytest.fixture
def generated_client_package(
    tmp_path: Path,
) -> Iterator[Callable[[OpenAPI], tuple[ModuleType, ModuleType]]]:
    """
    Generates a real `oapi.model`/`oapi.client` module pair from a real
    `OpenAPI` document, writes them into a real, importable package (the
    generated client module uses a package-relative `from . import
    model` import, so it cannot be loaded as a standalone file the way
    `generated_module_loader` loads single files), and returns
    `(model_module, client_module)`.
    """
    loaded_module_names: list[str] = []
    inserted_sys_path: str | None = None

    def load(
        open_api: OpenAPI, package_name: str = "generated_client_pkg"
    ) -> tuple[ModuleType, ModuleType]:
        nonlocal inserted_sys_path
        package_dir: Path = tmp_path / package_name
        package_dir.mkdir()
        (package_dir / "__init__.py").write_text("")
        model_path: Path = package_dir / "model.py"
        model_path.write_text(str(ModelModule(open_api)))
        client_path: Path = package_dir / "client.py"
        ClientModule(open_api, model_path=str(model_path)).save(
            str(client_path)
        )
        if inserted_sys_path is None:
            sys.path.insert(0, str(tmp_path))
            inserted_sys_path = str(tmp_path)
        model_module: ModuleType = importlib.import_module(
            f"{package_name}.model"
        )
        client_module: ModuleType = importlib.import_module(
            f"{package_name}.client"
        )
        loaded_module_names.extend(
            (package_name, f"{package_name}.model", f"{package_name}.client")
        )
        return model_module, client_module

    yield load
    for module_name in loaded_module_names:
        sys.modules.pop(module_name, None)
    if inserted_sys_path is not None and inserted_sys_path in sys.path:
        sys.path.remove(inserted_sys_path)
```

- [ ] **Step 2: Verify**

Run:
```bash
hatch run hatch-test.py3.10:pytest tests/test_conftest.py -v
hatch run mypy --strict --ignore-missing-imports tests/conftest.py
hatch fmt --formatter
hatch fmt --check
```
Expected: the existing `test_conftest.py` (from the infrastructure
plan, exercising `generated_module_loader`) still passes unmodified --
confirming this change is additive; mypy `Success: no issues found in
1 source file`; `hatch fmt --check` clean.

- [ ] **Step 3: Commit**

```bash
git add tests/conftest.py
git commit tests/conftest.py -m "test: add generated_client_package fixture for loading real generated model+client packages"
```

## Task 3: `tests/test_client_module_helpers.py`

**Files:**
- Create: `tests/test_client_module_helpers.py`

**Interfaces:**
- Consumes: `oapi.client._get_relative_module_path`, `_get_relative_
  module_import`, `_schema_defines_model`, `_iter_path_item_operations`,
  `get_default_method_name_from_path_method_operation`, `_strip_def_
  decorators` (existing). `oapi.oas.model.Operation`, `Parameter`,
  `PathItem`, `Schema` (existing).
- Produces: `tests/test_client_module_helpers.py`, 13 tests.

- [ ] **Step 1: Write the test file**

Create `tests/test_client_module_helpers.py`:

```python
from __future__ import annotations

from oapi.client import (
    _get_relative_module_import,
    _get_relative_module_path,
    _iter_path_item_operations,
    _schema_defines_model,
    _strip_def_decorators,
    get_default_method_name_from_path_method_operation,
)
from oapi.oas.model import Operation, Parameter, PathItem, Schema


def test_get_relative_module_path_across_directories() -> None:
    assert _get_relative_module_path("a/b/c.py", "d/e/f.py") == "...a.b.c"


def test_get_relative_module_path_within_the_same_directory() -> None:
    assert _get_relative_module_path("a/b/c.py", "a/b/f.py") == ".c"


def test_get_relative_module_import_across_directories() -> None:
    result: str = _get_relative_module_import("a/b/c.py", "d/e/f.py")
    assert result == "from ...a.b import c"


def test_get_relative_module_import_within_the_same_directory() -> None:
    result: str = _get_relative_module_import("a/b/c.py", "a/b/f.py")
    assert result == "from . import c"


def test_schema_defines_model_for_object_and_array_types() -> None:
    assert _schema_defines_model(Schema({"type": "object"})) is True
    assert _schema_defines_model(Schema({"type": "array"})) is True


def test_schema_defines_model_for_primitive_types() -> None:
    assert _schema_defines_model(Schema({"type": "string"})) is False


def test_schema_defines_model_accepts_a_parameter() -> None:
    parameter: Parameter = Parameter(
        {"name": "x", "in": "query", "type": "object"}
    )
    assert _schema_defines_model(parameter) is True


def test_iter_path_item_operations_yields_name_and_operation_pairs() -> None:
    path_item: PathItem = PathItem(
        {
            "get": {"operationId": "getX"},
            "post": {"operationId": "postX"},
        }
    )
    name: str
    operation: Operation
    result: list[tuple[str, str | None]] = [
        (name, operation.operation_id)
        for name, operation in _iter_path_item_operations(path_item)
    ]
    assert result == [("get", "getX"), ("post", "postX")]


def test_iter_path_item_operations_skips_unset_methods() -> None:
    path_item: PathItem = PathItem({"get": {"operationId": "getX"}})
    result: list[str] = [
        name for name, _operation in _iter_path_item_operations(path_item)
    ]
    assert result == ["get"]


def test_get_default_method_name_derives_from_path_when_no_operation_id() -> (
    None
):
    result: str = get_default_method_name_from_path_method_operation(
        "/foo/{id}/bar", "get", None
    )
    assert result == "get_foo_id_bar"


def test_get_default_method_name_prefers_the_operation_id() -> None:
    result: str = get_default_method_name_from_path_method_operation(
        "/foo/{id}/bar", "get", "myOperationId"
    )
    assert result == "my_operation_id"


def test_strip_def_decorators_removes_a_leading_decorator() -> None:
    source: str = "@decorator\ndef foo():\n    pass\n"
    assert _strip_def_decorators(source) == "def foo():\n    pass\n"


def test_strip_def_decorators_is_a_no_op_without_a_decorator() -> None:
    source: str = "def foo():\n    pass\n"
    assert _strip_def_decorators(source) == source
```

- [ ] **Step 2: Verify**

Run:
```bash
hatch run hatch-test.py3.10:pytest tests/test_client_module_helpers.py -v
hatch run mypy --strict --ignore-missing-imports tests/test_client_module_helpers.py
hatch fmt --formatter
hatch fmt --check
```
Expected: 13 passed; mypy `Success: no issues found in 1 source file`;
`hatch fmt --check` clean. Every assertion's expected value was
produced by actually calling the real function (including the two
docstring examples already present on `_get_relative_module_path`/
`_get_relative_module_import`, re-verified live rather than trusted).

- [ ] **Step 3: Commit**

```bash
git add tests/test_client_module_helpers.py
git commit tests/test_client_module_helpers.py -m "test: add coverage for ClientModule's isolable naming/import helper functions"
```

## Task 4: `tests/test_client_module_parameter_styles.py`

**Files:**
- Create: `tests/test_client_module_parameter_styles.py`

**Interfaces:**
- Consumes: the `generated_client_package` fixture (Task 2).
  `tests/input-data/parameter-styles.json` (existing, from the
  infrastructure plan). `tests/servers.py`'s `Response`,
  `http_test_server` (existing).
- Produces: `tests/test_client_module_parameter_styles.py`, 9 tests.
- Requires: Task 2.

- [ ] **Step 1: Write the test file**

Create `tests/test_client_module_parameter_styles.py`:

```python
from __future__ import annotations

from collections.abc import Callable
from types import ModuleType

import pytest
from servers import Response, http_test_server

from oapi.oas.model import OpenAPI


@pytest.fixture
def parameter_styles_client(
    generated_client_package: Callable[
        [OpenAPI], tuple[ModuleType, ModuleType]
    ],
) -> ModuleType:
    with open("tests/input-data/parameter-styles.json") as f:
        open_api: OpenAPI = OpenAPI(f)
    _model_module, client_module = generated_client_package(open_api)
    return client_module


def test_path_simple_style(parameter_styles_client: ModuleType) -> None:
    with http_test_server(
        responses={("GET", "/path/simple/1,2,3"): Response(body=b"{}")}
    ) as server:
        client = parameter_styles_client.Client(url=server.url)
        client.get_path_simple_id(id_=[1, 2, 3])
        assert server.requests[0].path == "/path/simple/1,2,3"


def test_path_label_style(parameter_styles_client: ModuleType) -> None:
    with http_test_server(
        responses={("GET", "/path/label/.1.2.3"): Response(body=b"{}")}
    ) as server:
        client = parameter_styles_client.Client(url=server.url)
        client.get_path_label_id(id_=[1, 2, 3])
        assert server.requests[0].path == "/path/label/.1.2.3"


def test_path_matrix_style_raises_key_error(
    parameter_styles_client: ModuleType,
) -> None:
    """
    Documents a real, verified, currently-unfixed codegen bug: every
    generated method for a `matrix`-style path parameter crashes with
    `KeyError: 'id'`. `_represent_dictionary_parameter` (client.py)
    prepends the matrix delimiter to the *dictionary key* used for
    string formatting (`";id"`, since `_format_matrix_argument_value`'s
    own output already includes the full `;id=value` fragment), but the
    generated path template's `str.format(**{...})` placeholder is
    still the bare `{id}` from the OpenAPI path -- `"{id}".format(
    **{";id": ...})` cannot find an `"id"` key in the kwargs dict it was
    given (only `";id"` is present) and raises `KeyError`. This means
    matrix-style path parameters are completely unusable in any
    generated client. Not fixed here (out of this test-only
    initiative's scope) -- flagged to the user directly as well as
    documented here.
    """
    with http_test_server(responses={}) as server:
        client = parameter_styles_client.Client(url=server.url)
        with pytest.raises(KeyError, match="id"):
            client.get_path_matrix_id(id_=[1, 2, 3])


def test_query_form_style(parameter_styles_client: ModuleType) -> None:
    with http_test_server(
        responses={("GET", "/query/form"): Response(body=b"{}")}
    ) as server:
        client = parameter_styles_client.Client(url=server.url)
        client.get_query_form(ids=[1, 2, 3])
        assert server.requests[0].query == "ids=1,2,3"


def test_query_space_delimited_style(
    parameter_styles_client: ModuleType,
) -> None:
    with http_test_server(
        responses={("GET", "/query/space-delimited"): Response(body=b"{}")}
    ) as server:
        client = parameter_styles_client.Client(url=server.url)
        client.get_query_space_delimited(ids=[1, 2, 3])
        assert server.requests[0].query == "ids=1%202%203"


def test_query_pipe_delimited_style(
    parameter_styles_client: ModuleType,
) -> None:
    with http_test_server(
        responses={("GET", "/query/pipe-delimited"): Response(body=b"{}")}
    ) as server:
        client = parameter_styles_client.Client(url=server.url)
        client.get_query_pipe_delimited(ids=[1, 2, 3])
        assert server.requests[0].query == "ids=1|2|3"


def test_query_deep_object_style(parameter_styles_client: ModuleType) -> None:
    with http_test_server(
        responses={("GET", "/query/deep-object"): Response(body=b"{}")}
    ) as server:
        client = parameter_styles_client.Client(url=server.url)
        client.get_query_deep_object(filter_={"a": "1", "b": "2"})
        assert server.requests[0].query == "filter[a]=1&filter[b]=2"


def test_header_simple_style(parameter_styles_client: ModuleType) -> None:
    with http_test_server(
        responses={("GET", "/header/simple"): Response(body=b"{}")}
    ) as server:
        client = parameter_styles_client.Client(url=server.url)
        client.get_header_simple(x_ids=[1, 2])
        assert server.requests[0].headers.get("X-Ids") == "1,2"


def test_cookie_form_style(parameter_styles_client: ModuleType) -> None:
    with http_test_server(
        responses={("GET", "/cookie/form"): Response(body=b"{}")}
    ) as server:
        client = parameter_styles_client.Client(url=server.url)
        client.get_cookie_form(ids=[1, 2])
        assert server.requests[0].headers.get("Cookie") == "ids=1,2"
```

- [ ] **Step 2: Verify**

Run:
```bash
hatch run hatch-test.py3.10:pytest tests/test_client_module_parameter_styles.py -v
hatch run mypy --strict --ignore-missing-imports tests/test_client_module_parameter_styles.py
hatch fmt --formatter
hatch fmt --check
```
Expected: 9 passed in a few seconds (each test regenerates and
re-imports a real package -- real, bounded overhead, not a flake);
mypy `Success: no issues found in 1 source file`; `hatch fmt --check`
clean. Every expected path/query/header/cookie value was produced by
actually running the generated method against the real
`http_test_server` and reading `RecordedRequest`'s real fields.

- [ ] **Step 3: Commit**

```bash
git add tests/test_client_module_parameter_styles.py
git commit tests/test_client_module_parameter_styles.py -m "test: add end-to-end coverage for ClientModule's argument-style code generation"
```

## Task 5: `tests/test_client_module_security_schemes.py`

**Files:**
- Create: `tests/test_client_module_security_schemes.py`

**Interfaces:**
- Consumes: the `generated_client_package` fixture (Task 2).
  `tests/input-data/security-schemes.json` (Task 1). `tests/servers.py`'s
  `Response`, `http_test_server` (existing).
- Produces: `tests/test_client_module_security_schemes.py`, 7 tests.
- Requires: Tasks 1, 2.

- [ ] **Step 1: Write the test file**

Create `tests/test_client_module_security_schemes.py`:

```python
from __future__ import annotations

import inspect
from collections.abc import Callable
from types import ModuleType

import pytest
from servers import Response, http_test_server

from oapi.oas.model import OpenAPI


@pytest.fixture
def security_schemes_client(
    generated_client_package: Callable[
        [OpenAPI], tuple[ModuleType, ModuleType]
    ],
) -> ModuleType:
    with open("tests/input-data/security-schemes.json") as f:
        open_api: OpenAPI = OpenAPI(f)
    _model_module, client_module = generated_client_package(open_api)
    return client_module


def test_init_bakes_in_the_first_api_key_schemes_location_and_name(
    security_schemes_client: ModuleType,
) -> None:
    """
    The OpenAPI document declares three `apiKey` security schemes
    (header/query/cookie) across different operations, but a generated
    `Client` has one shared `api_key_in`/`api_key_name` default pair --
    codegen picks the first `apiKey` scheme it encounters. Other
    locations remain reachable by passing `api_key_in`/`api_key_name`
    explicitly when constructing the client (see the query/cookie tests
    below), which isn't a bug -- a single client instance can only default
    to one location.
    """
    signature: inspect.Signature = inspect.signature(
        security_schemes_client.Client.__init__
    )
    assert signature.parameters["api_key_in"].default == "header"
    assert signature.parameters["api_key_name"].default == "X-Api-Key"


def test_init_bakes_in_oauth2_and_oidc_urls_from_the_security_schemes(
    security_schemes_client: ModuleType,
) -> None:
    signature: inspect.Signature = inspect.signature(
        security_schemes_client.Client.__init__
    )
    assert (
        signature.parameters["oauth2_token_url"].default
        == "https://example.com/oauth2/token"
    )
    assert (
        signature.parameters["oauth2_authorization_url"].default
        == "https://example.com/oauth2/authorize"
    )
    assert (
        signature.parameters["open_id_connect_url"].default
        == "https://example.com/.well-known/openid-configuration"
    )


def test_default_oauth2_flows_value_is_invalid(
    security_schemes_client: ModuleType,
) -> None:
    """
    Documents a real, verified, currently-unfixed codegen bug: a
    generated `Client` for an OpenAPI document with named OAuth2 flows
    cannot be instantiated with its own defaults. `_iter_oauth2_flows`
    (client.py) reads flow-type names via `sob.utilities.
    iter_properties_values(security_scheme.flows)`, which yields the
    Python-side (snake_case) *property* names of the generated
    `OAuthFlows` model -- e.g. `"authorization_code"` -- rather than the
    OpenAPI spec's own camelCase flow-type identifiers (`"authorization
    Code"`) that `Client.__init__`'s own validation (and its `Literal`
    parameter type) require. The baked-in default `oauth2_flows` tuple
    therefore fails that same validation immediately on construction,
    for *any* generated client whose OpenAPI document has a
    multi-word-named OAuth2 flow (`authorizationCode`/
    `clientCredentials` -- i.e. most real-world OAuth2 specs). The
    workaround (used by every other test in this file) is passing an
    explicit, valid `oauth2_flows` override. Not fixed here (out of
    this test-only initiative's scope) -- flagged to the user directly
    as well as documented here.
    """
    with pytest.raises(ValueError, match="oauth2_flows"):
        security_schemes_client.Client(url="http://example.com")


def test_api_key_header_authentication(
    security_schemes_client: ModuleType,
) -> None:
    with http_test_server(
        responses={
            ("GET", "/protected/api-key-header"): Response(
                body=b'{"name": "x"}'
            )
        }
    ) as server:
        client = security_schemes_client.Client(
            url=server.url, api_key="secret123", oauth2_flows=()
        )
        client.get_protected_api_key_header()
        assert server.requests[0].headers.get("X-Api-Key") == "secret123"


def test_api_key_query_authentication_with_an_explicit_location(
    security_schemes_client: ModuleType,
) -> None:
    with http_test_server(
        responses={
            ("GET", "/protected/api-key-query"): Response(
                body=b'{"name": "x"}'
            )
        }
    ) as server:
        client = security_schemes_client.Client(
            url=server.url,
            api_key="qkey",
            api_key_in="query",
            api_key_name="api_key",
            oauth2_flows=(),
        )
        client.get_protected_api_key_query()
        assert server.requests[0].query == "api_key=qkey"


def test_api_key_cookie_authentication_with_an_explicit_location(
    security_schemes_client: ModuleType,
) -> None:
    with http_test_server(
        responses={
            ("GET", "/protected/api-key-cookie"): Response(
                body=b'{"name": "x"}'
            )
        }
    ) as server:
        client = security_schemes_client.Client(
            url=server.url,
            api_key="ckey",
            api_key_in="cookie",
            api_key_name="api_key",
            oauth2_flows=(),
        )
        client.get_protected_api_key_cookie()
        assert server.requests[0].headers.get("Cookie") == "api_key=ckey"


def test_bearer_authentication(security_schemes_client: ModuleType) -> None:
    with http_test_server(
        responses={
            ("GET", "/protected/bearer"): Response(body=b'{"name": "x"}')
        }
    ) as server:
        client = security_schemes_client.Client(
            url=server.url, bearer_token="tok", oauth2_flows=()
        )
        client.get_protected_bearer()
        assert server.requests[0].headers.get("Authorization") == "Bearer tok"
```

- [ ] **Step 2: Verify**

Run:
```bash
hatch run hatch-test.py3.10:pytest tests/test_client_module_security_schemes.py -v
hatch run mypy --strict --ignore-missing-imports tests/test_client_module_security_schemes.py
hatch fmt --formatter
hatch fmt --check
```
Expected: 7 passed; mypy `Success: no issues found in 1 source file`;
`hatch fmt --check` clean. This is the task that both confirms Task 1's
fixture fix (the package must load at all) and documents the real
`oauth2_flows` codegen bug from Global Constraints.

- [ ] **Step 3: Commit**

```bash
git add tests/test_client_module_security_schemes.py
git commit tests/test_client_module_security_schemes.py -m "test: add end-to-end coverage for ClientModule's security-scheme code generation"
```

## Task 6: `tests/test_client_module_multipart.py`

**Files:**
- Create: `tests/test_client_module_multipart.py`

**Interfaces:**
- Consumes: the `generated_client_package` fixture (Task 2).
  `tests/input-data/multipart-request-body.json` (existing, from the
  infrastructure plan). `tests/servers.py`'s `Response`,
  `http_test_server` (existing).
- Produces: `tests/test_client_module_multipart.py`, 1 test.
- Requires: Task 2.

- [ ] **Step 1: Write the test file**

Create `tests/test_client_module_multipart.py`:

```python
from __future__ import annotations

from collections.abc import Callable
from types import ModuleType

import pytest
from servers import Response, http_test_server

from oapi.oas.model import OpenAPI


@pytest.fixture
def multipart_client(
    generated_client_package: Callable[
        [OpenAPI], tuple[ModuleType, ModuleType]
    ],
) -> ModuleType:
    with open("tests/input-data/multipart-request-body.json") as f:
        open_api: OpenAPI = OpenAPI(f)
    _model_module, client_module = generated_client_package(open_api)
    return client_module


def test_generated_multipart_method_raises_key_error(
    multipart_client: ModuleType,
) -> None:
    """
    Documents the same real, verified, currently-unfixed bug already
    covered directly against `Client.request()` in
    `tests/test_client_request_runtime.py`'s
    `test_request_multipart_crashes_missing_content_encoding_header`,
    confirmed here to also break *generated* multipart operations (the
    exact scenario `tests/input-data/multipart-request-body.json` was
    built to exercise, per the infrastructure plan): `_request_callback`
    calls `request.headers.get("Content-encoding")` expecting ordinary
    `dict.get` semantics, but a `MultipartRequest`'s custom `Headers`
    object re-raises `KeyError` when no `default` is passed and the key
    is missing -- which it always is for an ordinary multipart request.
    Every generated multipart operation is therefore unusable as-is.
    Not fixed here (out of this test-only initiative's scope) --
    flagged to the user directly as well as documented here.
    """
    with http_test_server(
        responses={("POST", "/upload"): Response(status=200, body=b"{}")}
    ) as server:
        client = multipart_client.Client(url=server.url)
        with pytest.raises(KeyError, match="Content-encoding"):
            client.post_upload(
                file=b"filedata", description="a file", tags=["a", "b"]
            )
```

- [ ] **Step 2: Verify**

Run:
```bash
hatch run hatch-test.py3.10:pytest tests/test_client_module_multipart.py -v
hatch run mypy --strict --ignore-missing-imports tests/test_client_module_multipart.py
hatch fmt --formatter
hatch fmt --check
```
Expected: 1 passed; mypy `Success: no issues found in 1 source file`;
`hatch fmt --check` clean.

- [ ] **Step 3: Commit**

```bash
git add tests/test_client_module_multipart.py
git commit tests/test_client_module_multipart.py -m "test: document that generated multipart operations crash (Content-encoding KeyError)"
```

## Task 7: `tests/test_client_module_polymorphic_responses.py`

**Files:**
- Create: `tests/test_client_module_polymorphic_responses.py`

**Interfaces:**
- Consumes: the `generated_client_package` fixture (Task 2).
  `tests/input-data/polymorphic-schemas.json` (existing, from the
  infrastructure plan). `tests/servers.py`'s `Response`,
  `http_test_server` (existing).
- Produces: `tests/test_client_module_polymorphic_responses.py`, 4
  tests.
- Requires: Task 2.

- [ ] **Step 1: Write the test file**

Create `tests/test_client_module_polymorphic_responses.py`:

```python
from __future__ import annotations

from collections.abc import Callable
from types import ModuleType

import pytest
from servers import Response, http_test_server

from oapi.oas.model import OpenAPI


@pytest.fixture
def polymorphic_client(
    generated_client_package: Callable[
        [OpenAPI], tuple[ModuleType, ModuleType]
    ],
) -> tuple[ModuleType, ModuleType]:
    with open("tests/input-data/polymorphic-schemas.json") as f:
        open_api: OpenAPI = OpenAPI(f)
    return generated_client_package(open_api)


def test_array_of_allof_merged_schema_response(
    polymorphic_client: tuple[ModuleType, ModuleType],
) -> None:
    model_module, client_module = polymorphic_client
    with http_test_server(
        responses={
            ("GET", "/pets"): Response(
                status=200,
                body=b'[{"name": "Rex", "species": "dog", "status": "sold"}]',
            )
        }
    ) as server:
        client = client_module.Client(url=server.url)
        pets = client.get_pets()
        assert len(pets) == 1
        pet = pets[0]
        assert isinstance(pet, model_module.Pet)
        assert pet.name == "Rex"
        assert pet.species == "dog"
        assert pet.status == "sold"


def test_oneof_response_infers_the_matching_variant(
    polymorphic_client: tuple[ModuleType, ModuleType],
) -> None:
    model_module, client_module = polymorphic_client
    with http_test_server(
        responses={
            ("GET", "/shapes"): Response(status=200, body=b'{"radius": 5}')
        }
    ) as server:
        client = client_module.Client(url=server.url)
        shape = client.get_shapes()
        assert isinstance(shape, model_module.Circle)
        assert shape.radius == 5


def test_anyof_response_infers_the_matching_variant(
    polymorphic_client: tuple[ModuleType, ModuleType],
) -> None:
    model_module, client_module = polymorphic_client
    with http_test_server(
        responses={
            ("GET", "/contacts"): Response(
                status=200, body=b'{"email": "a@b.com"}'
            )
        }
    ) as server:
        client = client_module.Client(url=server.url)
        contact = client.get_contacts()
        assert isinstance(contact, model_module.EmailContact)
        assert contact.email == "a@b.com"


def test_additional_properties_dictionary_response(
    polymorphic_client: tuple[ModuleType, ModuleType],
) -> None:
    _model_module, client_module = polymorphic_client
    with http_test_server(
        responses={
            ("GET", "/tags"): Response(
                status=200, body=b'{"a": "1", "b": "2"}'
            )
        }
    ) as server:
        client = client_module.Client(url=server.url)
        tags = client.get_tags()
        assert dict(tags) == {"a": "1", "b": "2"}
```

- [ ] **Step 2: Verify**

Run:
```bash
hatch run hatch-test.py3.10:pytest tests/test_client_module_polymorphic_responses.py -v
hatch run mypy --strict --ignore-missing-imports tests/test_client_module_polymorphic_responses.py
hatch fmt --formatter
hatch fmt --check
```
Expected: 4 passed; mypy `Success: no issues found in 1 source file`;
`hatch fmt --check` clean. Confirms real, correct polymorphic-type
resolution end-to-end: `allOf` merging (`Pet`), `oneOf` (`Shape` ->
`Circle`), `anyOf` (`Contact` -> `EmailContact`), and a plain
`additionalProperties` dictionary response.

- [ ] **Step 3: Commit**

```bash
git add tests/test_client_module_polymorphic_responses.py
git commit tests/test_client_module_polymorphic_responses.py -m "test: add end-to-end coverage for ClientModule's polymorphic response-type resolution"
```

## Task 8: Whole-plan verification

**Files:**
- None modified (verification only).

- [ ] **Step 1: Run every new file together, plus the full existing suite**

```bash
hatch run hatch-test.py3.10:pytest tests/test_client_module_helpers.py tests/test_client_module_parameter_styles.py tests/test_client_module_security_schemes.py tests/test_client_module_multipart.py tests/test_client_module_polymorphic_responses.py -v
hatch run hatch-test.py3.10:pytest tests/ -q
git checkout -- tests/input-data/languagetool-swagger.json
```
Expected: 34 passed for the five new files together; 373 passed for
the full suite (339 before this plan's tests existed, plus 34).

- [ ] **Step 2: Confirm the coverage delta**

```bash
hatch run hatch-test.py3.10:coverage run -m pytest tests/ -q
hatch run hatch-test.py3.10:coverage report -m --include="*/client.py"
git checkout -- tests/input-data/languagetool-swagger.json
```
Expected: `src/oapi/client.py` moves from 56% (this plan's starting
point) to roughly 83%, file-wide -- confirming the black-box,
generate-and-execute strategy transitively covers the large majority
of `ClientModule` despite no test directly calling any of its ~50
private methods.

- [ ] **Step 3: Update project memory**

Update the `project-oapi-test-coverage-initiative` memory file to note
this plan complete and move to the final remaining step (the `model.py`
`ModelModule` plan), per the standing blanket-execution-approval
instruction -- no user confirmation needed for this step. Make sure the
memory update prominently notes all four real bugs from Global
Constraints (matrix-style path parameters, the `oauth2_flows` codegen
mismatch, the multipart `KeyError` recurrence, and the `ModelModule`
empty-schema `NameError`), since three of them are genuine defects
worth surfacing beyond just this plan document, and the fourth is a
concrete pointer for the next plan.

---

## Self-Review

**1. Spec coverage:** The spec's step 6 ("`client.py` `ClientModule`
code generation... paired with executing generated clients against
`http_test_server`") is followed precisely -- every one of the four
purpose-built fixtures from the infrastructure plan is finally used for
its stated purpose, each generating a real client, loading it as a real
package, and executing it against the real `http_test_server`. The
free-function helpers immediately above `ClientModule` are covered
directly (Task 3) since they're genuinely isolable pure functions,
matching this initiative's established distinction between "isolable
pure logic gets a direct unit test" and "generated-source-text assembly
gets tested through its real output."

**2. Placeholder scan:** No "TBD"/"add appropriate handling"/"similar to
Task N" language. Every line of test code, and the new `conftest.py`
fixture itself, was executed against the real generators before being
written into this document. Four genuine bugs were discovered this way
(three in `ClientModule`/`client.py`, one in `ModelModule`) and are
documented as real, current behavior rather than "fixed," each verified
by tracing the source and then confirming live against a real generated
package -- not assumed. One genuine test-authoring mistake was caught
during validation (an `isinstance(pets, list)` assertion that was wrong
because a generated array response deserializes to a real `sob.Array`
subclass, not a plain `list` -- fixed to check length/indexing instead)
before it ever reached this document.

**3. Type consistency:** `generated_client_package` (Task 2) is the one
new fixture every other task's file depends on; its return type
(`tuple[ModuleType, ModuleType]`) is used consistently everywhere it's
consumed. `Response`/`http_test_server` continue to be imported the
same way established in every prior plan's test files touching
`tests/servers.py`.

---

**Plan complete and saved to
`docs/superpowers/plans/2026-08-02-client-module-codegen-tests.md`.**
Per the standing blanket authorization for this initiative
([[feedback-autonomous-plan-execution]]), proceeding directly to
subagent-driven execution on branch `test-coverage` without further
confirmation.
