# Test Coverage Plan

Spec for closing coverage gaps in `oapi`. Baseline measured via
`hatch test -c` on 2026-08-01:

| Module | Stmts | Miss | Cover |
|---|---:|---:|---:|
| `src/oapi/__init__.py` | 5 | 0 | 100% |
| `src/oapi/errors.py` | 6 | 0 | 100% |
| `src/oapi/oas/__init__.py` | 3 | 0 | 100% |
| `src/oapi/oas/model.py` | 518 | 52 | 90% |
| `src/oapi/oas/references.py` | 202 | 42 | 79% |
| `src/oapi/model.py` | 637 | 229 | 64% |
| `src/oapi/_utilities.py` | 54 | 22 | 59% |
| `src/oapi/_multipart_request.py` | 238 | 164 | 31% |
| `src/oapi/client.py` | 1447 | 1212 | **16%** |
| **TOTAL** | 3110 | 1721 | **45%** |

`client.py` is the priority: it's the largest file (4039 lines) and the
least covered, and it holds both the runtime HTTP client and the client
*code generator* (`ClientModule`). `tests/test_client.py` is currently a
stub (`TODO`, no assertions) — every real client test is new work.

Rerun the baseline any time with:

```shell
hatch test -c && hatch run hatch-test.py3.10:coverage report -m
```

## Philosophy: real integration over mocks

This library's job is to talk real HTTP and generate real, runnable Python
source. Mocking `urlopen` or stubbing the code generator would only prove
the mocks were configured correctly, not that generated clients work
against real servers or that formatting matches the OpenAPI spec byte for
byte. Concretely:

- **Runtime HTTP behavior** (`Client`, retries, auth, encoding,
  multipart) is tested against a **real local HTTP server** in the test
  process — not `unittest.mock.patch`/`responses`/`requests-mock`. The
  server is stdlib-only (`http.server.ThreadingHTTPServer` +
  `BaseHTTPRequestHandler`) so no new dependency is needed; it runs on an
  ephemeral port in a background thread, per-test, and is torn down in a
  `finally`/fixture teardown.
- **Code generation** (`ClientModule`, `ModelModule`) is tested by
  generating real `.py` source from real OpenAPI fixture documents,
  `exec`/importing the result as an actual module, and — for the client —
  instantiating the generated `Client` subclass and firing real requests
  at the local test server. This is the only way to exercise the
  hundreds of `_iter_*`/`_get_*` source-fragment branches: generate many
  small, deliberately varied specs and assert on the *behavior* of the
  generated code, with golden-file source comparison (existing
  `tests/regression-data` pattern) as a secondary regression check, not
  the primary assertion.
- **Pure functions with no I/O** (arg-formatting helpers, content
  encode/decode, `_utilities.py`) are exercised directly with real inputs
  and real codecs (`gzip`, `zlib`, `brotli`, `zstandard` — all already
  optional deps of this project) — no mocking needed since there's
  nothing to isolate from.
- The only place a double is arguably justified is simulating *transient
  network failure* for retry tests (killing/delaying a real socket is
  fiddly). Prefer a real flaky server (fails N times by real HTTP 5xx /
  real connection-reset, then succeeds) over mocking `retry()`'s
  internals — this is still achievable for real with a small stateful
  request handler, so plan A is "real flaky server," not a mock.

## New test infrastructure (build once, reuse everywhere)

1. **`tests/servers.py`** — a small stdlib-only local HTTP test server:
   - `class HTTPTestServer(ThreadingHTTPServer)` started on `("127.0.0.1", 0)`
     (OS-assigned free port) in a `threading.Thread(daemon=True)`.
   - A pluggable handler: either (a) a `RequestHandler` that records each
     received request (method, path, query string, headers, body) into a
     thread-safe list the test can assert against and returns a
     configurable canned response, or (b) a routing handler keyed by
     `(method, path)` for tests that need distinct responses per
     generated-client operation.
   - A context manager / pytest fixture `def http_server() -> Iterator[HTTPTestServer]` yielding the server with `.url` and `.requests` (recorded requests), used by every `Client`/`ClientModule` integration test.
   - A `FlakyRequestHandler` variant for retry tests: returns real
     `503`/connection-drop for the first *N* requests to a given path,
     then a real `200`.
   - A minimal real OAuth2 token-endpoint handler (`POST /token` reading
     real `grant_type=password|client_credentials` form bodies, real
     `Authorization: Basic` header, returning a real JSON access-token
     payload) for the OAuth2 auth tests — this is a fake *authorization
     server*, not a mock of `oapi`'s own auth code, so the client's HTTP
     and parsing logic still runs for real.
2. **New minimal OpenAPI fixtures under `tests/input-data/`** — the
   existing fixtures (petstore, uspto, languagetool, etc.) don't exercise
   several client-generation branches at all (checked via grep):
   no `matrix`/`label`/`spaceDelimited`/`pipeDelimited`/`deepObject`
   parameter styles anywhere, no `multipart/form-data` request bodies,
   no OAuth2 security schemes. Add small, purpose-built specs (a few
   paths each, not full pet-store-sized documents) rather than editing
   the existing golden-file fixtures (would perturb existing
   regression-data):
   - `tests/input-data/parameter-styles.yaml` — one path per style
     (`simple`, `label`, `matrix`, `form`, `spaceDelimited`,
     `pipeDelimited`, `deepObject`) across path/query/header/cookie
     locations, `explode` true/false variants.
   - `tests/input-data/security-schemes.yaml` — `apiKey` in
     header/query/cookie, `oauth2` with `password` and
     `clientCredentials` flows (and `authorizationCode`/`implicit` for
     source-generation coverage even if not runtime-exercised),
     `openIdConnect`, `http bearer`.
   - `tests/input-data/multipart-request-body.yaml` — a path whose
     request body is `multipart/form-data` with file (`format: binary`)
     and non-file fields, to drive both `_multipart_request.py` and the
     `_iter_request_body_form_parameters_source` / form-parameter
     branches in `client.py`.
   - `tests/input-data/polymorphic-schemas.yaml` (for `ModelModule`) —
     `allOf`/`oneOf`/`anyOf`, schema merging, array/dictionary schemas,
     enums, to hit `model.py`'s merge/polymorph branches.
   These become new golden entries in `tests/regression-data/` the same
   way `languagetool.py` is today (generate once, commit, compare on
   every run).
3. **`tests/conftest.py`** — if not already implied by the above, house
   shared fixtures (`http_server`, `tmp_path`-based generated-module
   loader helper: write generated source to a temp `.py` file, import it
   via `importlib`, return the module).

## Per-module plan

### `src/oapi/client.py` (16% → target ~85%+)

Split by concern; each bullet is a test group, not necessarily one test
function.

**Argument formatting (lines ~109–479, currently almost entirely
uncovered: `urlencode`, `_format_simple_argument_value`,
`_format_label_argument_value`, `_format_matrix_argument_value`,
`_format_space_delimited_argument_value`,
`_format_pipe_delimited_argument_value`, `_format_form_argument_value`,
`_format_deep_object_argument_value`, `_format_dot_object_argument_value`,
`format_argument_value`)**
- Call these functions directly with real primitive/array/object values
  (they're pure — no need to route through HTTP for the *unit* of
  formatting logic), covering: primitives, arrays, objects, `explode`
  true/false, `None`/empty values (`_item_is_not_empty`), non-ASCII/
  reserved characters (percent-encoding correctness).
- Then close the loop end-to-end: generate a client from
  `parameter-styles.yaml`, call each generated operation method against
  `http_server`, and assert the **actual request line / query string /
  headers the server received** match the OpenAPI-spec-defined
  serialization for that style — this is what proves the formatter is
  wired correctly into request assembly, not just correct in isolation.

**`get_request_curl` / `_represent_http_response`**
- Build a real `urllib.request.Request` (and a real multipart `Request`
  from `_multipart_request.py`), call `get_request_curl`, assert the
  produced curl command's structure (method, `-H` headers, `--data`)
  round-trips the request's real content — e.g., shell-split the string
  and check the pieces, rather than exact string matching, to avoid
  over-fitting to formatting.
- `_represent_http_response`: perform a real request against
  `http_server`, pass the real `http.client.HTTPResponse` in.

**`retry` / `default_retry_hook`**
- Real flaky server (`FlakyRequestHandler`): assert a decorated function
  making real requests succeeds after N real failures and that the
  number of attempts matches configuration (max retries, backoff).
- Assert exhausting retries re-raises the real underlying exception.
- `default_retry_hook`: exercise with real exception instances raised by
  a real failing connection (e.g., connect to a closed port) rather than
  constructing exceptions by hand, where practical.

**Content encoding (`_encode_content`, `_decode_content`,
`_format_request_data`)**
- Round-trip real payloads through `gzip`, `deflate`, `br` (brotli),
  `zstd` — all are already installed via the `all` extra used by the
  `hatch-test` env. Assert decode(encode(x)) == x for each, and that
  `_decode_content` correctly rejects/handles an unsupported encoding.
- End-to-end: local server that echoes back whatever `Content-Encoding`
  it received and the raw bytes, generated/raw client sends compressed
  body, test asserts the server saw genuinely compressed bytes.

**`_assemble_request` (largest single uncovered function, ~965–1063)**
- Exercise via real generated-client operation calls (not by calling the
  private function directly) covering: path parameters, query
  parameters, header parameters, cookie parameters, JSON body, form
  body, multipart body, combinations of several parameter locations on
  one operation. Assert against what `http_server` actually received.

**Pickling (`SSLContext`, `_make_thread_locks_pickleable`,
`_make_http_errors_pickleable`, `_make_loggers_pickleable`,
`Client.__getstate__`/`__setstate__`/`_resurrect_client`)**
- Real `pickle.dumps`/`pickle.loads` round-trip of a live `Client`
  instance (with a real `SSLContext`, real retry hook, real logger
  attached), then use the unpickled client to make a real request
  against `http_server` — proves the round-trip produces a *working*
  client, not just a structurally-equal one.
- If feasible in CI, a real `multiprocessing.Pool` sending the client to
  a worker process and making a request there is the most faithful test
  of why this pickling support exists at all; fall back to plain
  `pickle` round-trip if multiprocessing proves flaky in CI sandboxes.

**`Client` class runtime (`__init__`, `request`, `_request`,
`_request_callback`, auth methods)**
- `request()`/`_request()` against `http_server` for GET/POST/PUT/PATCH/
  DELETE, real non-2xx responses (assert real `errors.py`/`urllib`
  exceptions surface correctly), real timeouts (server that sleeps past
  a short client timeout), real redirects if supported.
- API key auth: generate a client from `security-schemes.yaml`, real
  request against `http_server`, assert the server actually received the
  key in the configured location (header/query/cookie).
- OAuth2 password & client_credentials flows: point the generated client
  at the fake token endpoint (`http_server`'s OAuth2 handler) plus a
  protected resource endpoint on the same server; assert the client
  performs a real token request, then a real resource request with the
  real returned bearer token attached. Cover token refresh
  (`_get_oauth2_token_url`, cached-token reuse) by asserting the token
  endpoint is hit once for two resource calls, and hit again after
  forcing expiry.
- `_request_callback`/response-callback (`_set_response_callback`): real
  request, assert callback receives the real, readable response.

**`ClientModule` (code generation, lines ~2284–3965 — the other half of
the gap)**
- For each fixture (`petstore.yaml`, `uspto.yaml` (OAS2), one of the
  OAS3 examples, plus the three new purpose-built fixtures above):
  generate source via `get_source()`/`write_client_module`, compare
  against a committed golden file in `tests/regression-data/` (mirrors
  the existing `test_model.py` pattern) as a change-detector.
  This assertion is available immediately, not
  worth deferring.
- Then, for the fixtures that matter most for behavior coverage
  (parameter-styles, security-schemes, multipart), actually `exec`/
  import the generated module and run it against `http_server` as
  described above — this simultaneously covers the *generation* branches
  (`_iter_parameter_method_source`, `_iter_operation_method_source`,
  `_resolve_*`, security-scheme source helpers, docstring generation)
  and the *generated code's* runtime correctness in one test.
- OAS2-vs-OAS3 branching (`_get_open_api_major_version`,
  `_get_api_key_in`/`_get_api_key_name` differences,
  `_iter_oauth2_flows`): covered by using both an OAS2 fixture (uspto)
  and OAS3 fixtures with security schemes.
- Error paths: malformed/inconsistent operation definitions that should
  raise — check `errors.py` usages in `client.py` for what's reachable
  (e.g. duplicate method names, unresolvable `$ref` in a security
  scheme) and add one fixture per raise site actually reachable through
  the public API.
- `save()` / round-trip: write to a real temp file (`tmp_path`), re-read
  it, assert content matches; parser re-load if `ClientModule` supports
  reading back an existing module (mirrors `ModelModule._parse_existing_module`).

### `src/oapi/model.py` (64% → target ~90%+)

- Use the existing OAS example fixtures (petstore, uspto,
  callback-example, link-example, api-with-examples, petstore-expanded)
  through `ModelModule` the same way `languagetool.py` already is —
  today only `languagetool-swagger.json` is run through `ModelModule` in
  `test_model.py`; the other six fixtures are only used for
  parse/dereference testing (`test_openapi_examples`), not for model
  generation. Wiring them through `ModelModule` with golden-file
  comparison is close to free and should immediately raise coverage.
- Add `polymorphic-schemas.yaml` (above) to specifically hit:
  `_Modeler.merge_schemas_properties`, `merge_array_schemas`,
  `merge_dictionary_schemas`, `get_merged_schemas_object_class`,
  `polymorph_property`, `extend_property_schemas`,
  `iter_dereferenced_schemas`.
- `OAPIDuplicateClassNameError`: construct a fixture (or a custom
  `class_name_from_pointer` callback passed to `ModelModule`) that
  deliberately produces a collision; assert the real error is raised.
- `write_model_module` + `save()`: real temp-file round trip
  (`tmp_path`), including the "module already exists, parse and diff"
  path (`_parse_existing_module`, `_ModuleParser`) by writing once,
  mutating the source spec slightly, and regenerating.
- `get_default_class_name_from_pointer` already has direct unit tests;
  extend with edge cases already implied by nearby uncovered lines
  (nested pointers, `/item` suffixes at deeper nesting, non-ASCII
  names) rather than adding a new mechanism.

### `src/oapi/_multipart_request.py` (31% → target ~90%+)

- Direct, real (no-mock) exercise of `Headers`/`Data`/`Part`/`Parts`/
  `Request`/`MultipartRequest`: dict-protocol methods (`pop`,
  `popitem`, `setdefault`, `update`, `__delitem__`, `copy`), computed
  headers (`Content-length`, `Content-type`/boundary), nested parts,
  boundary collision-avoidance (construct data that contains a
  first-choice boundary substring and assert the real boundary
  regenerates until collision-free — this is real randomness, not
  mocked `random.choice`).
- `__bytes__`/`__str__` round-trip: assert real multipart byte output
  parses correctly using stdlib `email.parser` (a real, independent
  multipart parser) as an oracle, rather than hand-checking substrings.
- End-to-end: real `MultipartRequest` sent via `urllib.request.urlopen`
  (or through `Client`) to `http_server`; server-side, parse the
  real received body with `email.parser`/`cgi`-equivalent and assert
  the parts match what was sent. This is the real integration test that
  proves the format is actually valid multipart, not just internally
  self-consistent.

### `src/oapi/_utilities.py` (59% → target 100%)

Pure, dependency-free — direct unit tests are already "real" (no I/O to
fake):
- `rename_parameters`: decorate a real function, call with old and new
  kwarg names, assert correct mapping and pass-through of unmapped args.
- `get_type_format_property`/`get_string_format_property`: table-driven
  test over every `(type_, format_, content_media_type,
  content_encoding)` combination referenced in the OpenAPI spec, asserting
  the correct real `sob.*Property` type; assert the `ValueError` for an
  unknown `type_`.
- `iter_distinct`: real iterable with duplicates, assert order-preserving
  dedup.
- `deprecated`: assert a real `warnings.catch_warnings()` capture shows
  the expected category/message when the wrapped function is called, and
  that the function's return value still passes through.

### `src/oapi/oas/references.py` (79% → target ~95%+)

- `Resolver`/`_Document`: real dereferencing of local, purpose-built
  fixture documents (small, inline — not necessarily the big OAI
  examples) covering: relative and absolute `$ref` (`get_absolute_url`,
  `get_relative_url`), refs into arrays/dictionaries/object properties
  (`dereference_array_items`, `dereference_dictionary_values`,
  `dereference_object_properties`), refs that recurse
  (`prevent_infinite_recursion`/`reset_recursion_placeholder`) and
  should raise `OAPIReferenceLoopError` for real cycles, refs to a
  pointer that doesn't exist → real `OAPIReferencePointerError`.
- `_urlopen`/`get_document`: fetch across a **real local HTTP server**
  (`http_server` serving a raw YAML/JSON document) in addition to local
  file paths already covered — multi-document dereferencing where one
  document `$ref`s another over HTTP is a realistic scenario for this
  library and currently untested.
- `resolve_reference`/`resolve`: assert resolving the same pointer twice
  returns consistent results (caching behavior implied by `_Document`
  structure) and that `dereference_all` actually mutates in place vs.
  `dereference` (non-mutating) if that distinction exists — check
  current behavior first rather than assuming.

### `src/oapi/oas/model.py` (90% → target ~97%+)

This file is generated (`make remodel`) but not pure boilerplate — the
uncovered ranges include real hand-written validation hooks near the end
of the file (`_reference_before_setitem`, `_reference_after_unmarshal`,
`_parameter_after_validate`, `_schema_after_validate`) plus assorted
version-specific model branches. Don't hand-edit the generated sections;
test them like any other public behavior:
- `_schema_after_validate`: real `Schema`/`Parameter` instances with
  invalid `type_`/`format_` combinations (e.g. `type_="integer",
  format_="date"`), assert real `sob.errors.ValidationError` on
  `sob.validate(...)`.
- `_parameter_after_validate`: a `Parameter` with both `content` (>1
  entry) and `schema` set, and one with both `content` and `schema`
  simultaneously; assert the real `ValidationError`.
- `_reference_after_unmarshal`/`_reference_before_setitem`: unmarshal a
  `Reference` missing `$ref` → real `ValueError`; set an arbitrary
  extra attribute on a `Reference` and confirm it's accepted per
  `patternProperties` semantics.
- For the remaining scattered uncovered line ranges (`325-336`,
  `1377-1385`, `1671-1690`, `1750-1766`, `4385-4405`), identify which
  OAS2-vs-OAS3 model classes/branches they belong to
  (`hatch run hatch-test.py3.10:coverage report -m` gives exact ranges)
  and cover via the OAS2 (uspto) and OAS3 example fixtures already
  exercised in `test_openapi_examples`/`ModelModule` tests above —
  likely just needs a couple of targeted small fixtures rather than new
  infrastructure.

## Sequencing

1. Land `tests/servers.py` + `tests/conftest.py` infrastructure and the
   three/four new minimal fixtures — nothing else can proceed without
   these.
2. `_utilities.py` and `_multipart_request.py` (self-contained, fast,
   unblock nothing else but cheap wins toward 100%).
3. `oas/references.py` and `oas/model.py` validation hooks (self-
   contained, no server needed except the one HTTP-`$ref` test).
4. `client.py` argument-formatting + content-encoding (pure-function
   layer) — needed before the end-to-end request tests so failures
   localize correctly.
5. `client.py` `Client` runtime (`http_server`-backed): plain requests →
   retries → auth (API key, then OAuth2) → pickling.
6. `client.py` `ClientModule` generation, paired with the `http_server`-
   backed execution of generated clients — largest chunk, do last since
   it depends on everything above being solid (a bug in the runtime
   `Client` would otherwise be masked by/confused with a codegen bug).
7. `model.py` `ModelModule` gaps (independent of the client work; can be
   parallelized with step 6 by a second contributor if needed).

## Definition of done

- `hatch test -c` coverage total materially above the 45% baseline; no
  individual `src/oapi/*.py` module below ~85% except where a line range
  is genuinely unreachable (document any such exclusion with a `# pragma:
  no cover` and a one-line reason, don't silently skip).
- `tests/test_client.py` has real assertions and the `TODO`/stub is gone.
- Every new integration test tears down its `http_server` (fixture/
  context-manager, not manual `try`/`finally` per test) and does not leak
  threads or bound ports across the run.
- `make test` (`hatch fmt --check && hatch run mypy && hatch test -c -vv`)
  stays green — new tests fully typed (`disallow_untyped_defs`), new
  fixtures/golden files reviewed like code, not just accepted from
  `make refresh-test-data` output.
