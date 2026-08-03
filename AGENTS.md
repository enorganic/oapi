# AGENTS.md

`oapi`: generates type-safe Python API client/model modules from OpenAPI
2.0/3.x documents. Data models are built on `sob` (schema-enforcing
serialization) and reject/validate data not matching the spec.

## Layout

- `src/oapi/oas/model.py` — data model for OpenAPI/Swagger documents
  themselves (`OpenAPI`, `Info`, `Paths`, `Schema`, ...). Excluded from
  ruff/lint — treat as generated, do not hand-format.
- `src/oapi/oas/references.py` — `$ref` resolution for OAS documents.
- `src/oapi/model.py` — `write_model_module` / `ModelModule`: generates a
  data-model `.py` file from an OpenAPI doc.
- `src/oapi/client.py` — `write_client_module` / `ClientModule` /
  `Client`: generates a client `.py` file; also request formatting,
  encoding, retry logic used by generated clients at runtime.
- `src/oapi/errors.py` — exception types.
- `scripts/remodel.py` — regenerates `src/oapi/oas/model.py` itself (run
  via `make remodel` after changes affecting that generation).
- `template/` — cookiecutter template for scaffolding new `oapi`-based
  client projects (own `pyproject.toml`, own `scripts/remodel.py`
  pattern). Excluded from ruff/mypy/tests.
- `tests/test_model.py`, `tests/test_client.py` — unit + doctest tests.
- `tests/input-data/*.{yaml,json}` — sample OpenAPI specs used as fixtures.
- `tests/regression-data/` — generated golden model/client modules,
  **tracked in git**; compared against on each test run.
- `docs/` — mkdocs-material source (published to oapi.enorganic.org).

## Environment & commands

Uses `hatch` (not bare pip/venv). Python `~=3.10`, tested on 3.10–3.13.

- `make install` — create all hatch envs (first-time setup).
- `make test` — `hatch fmt --check && hatch run mypy && hatch test -c -vv`
  (lint check, type check, full test matrix). Run this before considering
  work done.
- `make format` — `hatch fmt --formatter && hatch fmt --linter && hatch run mypy`
  (auto-fixes formatting/lint, then type-checks).
- `make refresh-test-data` — deletes `tests/regression-data` and reruns
  tests to regenerate golden files. Use when a change intentionally
  alters generated model/client output; review the diff before committing.
- `make remodel` — regenerate `src/oapi/oas/model.py` via
  `scripts/remodel.py`.
- `make docs` — build and serve mkdocs locally.
- Single test: `hatch test -c -vv tests/test_model.py::test_name`.

CI (`.github/workflows/test.yml`) runs `hatch fmt --check && hatch run mypy`
plus `hatch test -c` across OS × Python-version matrix — mirror this
locally before pushing.

## Conventions

- Line length 79 (ruff + black). Ruff is the formatter/linter of record
  (`hatch fmt`); black config exists for the `docs` env only.
- mypy strict on new code: `disallow_untyped_defs`,
  `disallow_incomplete_defs` — annotate all defs in `src/` and `tests/`.
- Tests run with `--doctest-modules`, so docstring code examples in
  `src/` are executed — keep them correct and runnable.
- Don't hand-edit `src/oapi/oas/model.py`; change `scripts/remodel.py` and
  run `make remodel` instead.
- Follow existing patterns in `docs/contributing.md` for branch naming
  (`feature/...`, `bugfix/...`).
