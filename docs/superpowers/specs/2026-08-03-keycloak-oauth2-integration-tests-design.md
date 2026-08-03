# Keycloak OAuth2/OIDC Integration Tests: Design

## Goal

Add real, protocol-compliant integration tests for every OpenAPI
authentication method `oapi.client.Client` actually implements
client-side behavior for, using a real Keycloak instance (via `docker
compose`) rather than a fake/hand-rolled token endpoint -- catching
real protocol-compliance gaps a lenient fake server can't.

## Scope: which auth methods need Keycloak, and which don't

OpenAPI defines four security scheme types: `apiKey`, `http` (basic/
bearer), `oauth2` (four flows: `authorizationCode`, `implicit`,
`password`, `clientCredentials`), and `openIdConnect`. Of these:

- **`apiKey` (header/query/cookie) and `http` (basic/bearer) need no
  real server.** `Client`'s handling of these is pure value placement
  (a header, a query parameter, a cookie, an `Authorization: Basic
  .../Bearer ...` header) -- there is no protocol exchange to get
  wrong. These are already fully covered by the existing
  `http_test_server`-backed tests in `tests/test_client.py` (real HTTP
  requests, real header/query/cookie inspection).
- **`oauth2`'s `authorizationCode` and `implicit` flows are not
  implemented client-side at all.** `Client._oauth2_authenticate_request`
  only ever emits a `warnings.warn(...)` for these two ("not currently
  implemented" / "requires the client be initialized with..."). There
  is no request-building code to integration-test -- this is already
  covered by `tests/test_client.py`'s
  `test_oauth2_authenticate_request_warns_for_unconfigured_flows`.
- **`oauth2`'s `password` and `clientCredentials` grants, and
  `openIdConnect` discovery, are exactly where a real server adds
  value.** `Client` builds and sends real token-request bodies for
  these; the existing tests (`tests/test_client.py`'s oauth2-flow
  section) already validate this against a fake token endpoint
  (`http_test_server` returning a canned JSON response) -- which
  proves `Client`'s *own* logic (caching, retry-on-redirect, `scope`
  handling, the real `timeout=0` bug already documented) but cannot
  prove the *wire format* `Client` sends is something a real,
  spec-compliant OAuth2/OIDC server will actually accept.

This plan therefore targets exactly three flows against a real
Keycloak: **password grant, client-credentials grant, and OIDC
discovery** (which itself just derives the token URL, then delegates
to whichever grant is configured).

## What was found by hand-validating this before writing a plan

Every claim below was verified live against a real, running Keycloak
26.0 instance (`quay.io/keycloak/keycloak:26.0`, `docker compose up -d
--wait`), not assumed:

1. **`oapi`'s wire format is protocol-compliant for both grants** --
   this is a real, valuable negative result, not a bug report. Neither
   grant needed any workaround on `Client`'s side.
   - Password grant (`_request_oauth2_password_authorization`) never
     sends a `client_secret` -- only `client_id`, `username`,
     `password`, `grant_type=password`. Per RFC 6749, this only works
     against a *public* client (or one that otherwise doesn't require
     client authentication). Verified: succeeds against a real
     Keycloak public client; a confidential client would need a
     `client_secret` `Client` never sends (not tested here, since
     `Client` genuinely can't do it -- worth knowing, not a bug to fix
     in this test-only effort).
   - Client-credentials grant sends `client_id`/`client_secret` as
     form-body parameters, not an HTTP Basic `Authorization` header.
     RFC 6749 §2.3.1 permits this for confidential clients, and
     Keycloak's default client authenticator (`client-secret`) accepts
     it. Verified: succeeds against a real Keycloak confidential
     client with a service account.
2. **A real Keycloak realm-configuration gotcha, not an `oapi` bug**:
   Keycloak 26's default "User Profile" feature requires `email`,
   `firstName`, and `lastName` on a user for the direct-grant (password)
   flow to consider the account "fully set up" -- a user with only a
   username/password credential (no profile fields) gets a real `400
   invalid_grant: "Account is not fully set up"` from Keycloak itself,
   confirmed by reproducing with raw `curl`, independent of `oapi`.
   The realm fixture (below) includes a complete profile for exactly
   this reason.
3. **Negative paths produce real, informative errors**: wrong password
   -> real `401` `invalid_grant: "Invalid user credentials"`; wrong
   client secret -> real `401` `unauthorized_client: "Invalid client or
   Invalid client credentials"`.
4. **Token caching works against a real `expires_in`**: a second
   `Client.request()` call reuses the cached `Authorization` header
   (verified via `Client.headers["Authorization"]` equality across two
   real requests), matching the existing fake-server-backed test but
   now against a real token lifetime.
5. **A full end-to-end path works**: a `Client` configured for the
   client-credentials flow, given `oauth2_scope="openid"`, correctly
   authenticates a real request against Keycloak's own `/userinfo`
   endpoint (used as a stand-in protected resource) -- proving the
   token isn't just successfully parsed, but genuinely accepted by a
   real resource server.
6. **Keycloak startstart-up is fast**: `start-dev --import-realm` with
   the default in-memory H2 store becomes healthy in ~9-12 seconds,
   confirmed repeatedly across multiple fresh container starts --
   acceptable for CI.
7. **A real Docker bind-mount gotcha, worth documenting for whoever
   executes this plan**: if `docker compose up` ever runs before the
   realm file exists at the expected host path, Docker silently creates
   an empty *directory* at that path (both on the host and in the
   container) instead of erroring -- silently breaking the realm
   import with no obvious error (Keycloak just starts with an empty
   realm, no import log line, no crash). The fix, if this happens, is
   to `rm -rf` the wrongly-created directory and recreate the real
   file. The plan's task order (create the real file, *then* first run
   `docker compose up`) avoids ever hitting this, but it's worth
   knowing about if a future contributor changes the file first without
   realizing it might already be a stale directory.

## Design decisions

- **The `keycloak_url` fixture manages its own Docker Compose lifecycle
  -- no manual `docker compose up` step required, by contributors or by
  CI.** The session-scoped fixture first does a real reachability check
  (`urllib.request.urlopen` against the realm's discovery URL, 2 second
  timeout). If already reachable (someone else started it), it's used
  as-is and left running. Otherwise, if `docker` is on `PATH`, the
  fixture runs `docker compose up -d --wait` itself, re-checks
  reachability, and tears the service back down (`docker compose
  down`) at the end of the session -- but only if *this fixture* was
  the one that started it, so it never stops an instance a developer
  is deliberately running for their own use. If `docker` isn't
  installed, or Keycloak never becomes reachable, every test depending
  on the fixture is skipped rather than failed. This mirrors the
  existing `test_languagetool` network-dependent-test pattern already
  in this codebase (skip via a live check, don't fail), while going one
  step further and self-provisioning the dependency instead of just
  detecting it. The fixture makes no platform assumption -- it works
  anywhere a working `docker compose` is on `PATH`, including a
  contributor's local macOS or Windows machine, not just Linux.
  Verified live, on macOS: a cold run (no containers running) auto
  -starts Keycloak, all 7 tests pass in ~10s total, and the container is
  confirmed gone afterward; a warm run (already running) reuses it in
  under a second and leaves it running afterward.
- **No CI workflow changes at all (superseding an earlier version of
  this design that added a dedicated `ubuntu-latest`-only job).**
  `.github/workflows/test.yml`'s existing cross-platform `test` job
  already runs the entire `tests/` suite across its matrix, so the new
  Keycloak test file runs there automatically with no extra job, no
  platform gate, and no explicit `docker compose` step: it
  auto-provisions and passes on `ubuntu-latest` legs (Docker is
  present), and cleanly skips wherever Docker isn't available or
  compatible (`macos-latest`, and `windows-latest` unless it happens to
  have a working Linux-container Docker setup). This was the simpler
  design once the fixture became fully self-provisioning -- a separate
  job would only have duplicated coverage the matrix already provides.
- **A new `tests/docker-compose.yml`** (not repo root, superseding an
  earlier version of this design that put it at the top level) -- it
  exists solely to support this test suite and isn't part of the
  package's runtime or distribution, so it's scoped under `tests/`
  alongside everything else that exists only for testing. The
  `keycloak_url` fixture invokes it explicitly via `docker compose -f
  tests/docker-compose.yml ...`, so `docker compose`'s default
  discovery behavior (looking for a compose file in the current
  directory) doesn't matter for automated use; a contributor invoking
  it manually needs `-f tests/docker-compose.yml` too (or `cd tests`
  first).
- **A new `tests/keycloak/realm.json`** (not `tests/input-data/`) --
  the existing `tests/input-data/` directory holds OpenAPI documents
  (a specific, consistent fixture type consumed by `OpenAPI(...)`); a
  Keycloak realm export is a different kind of fixture entirely, so it
  gets its own directory rather than being mixed in.
- **A new, separate test file, `tests/test_client_keycloak_integration.py`
  -- a deliberate, explained exception to the "one test file per source
  module" consolidation already done for the rest of this suite.**
  Every test in this file exercises `Client` (so by that rule alone it
  would belong in `tests/test_client.py`), but it has a fundamentally
  different operational profile than everything else in that file: it
  requires an external service, is expected to skip in most
  environments, and is the one place in the whole suite where `docker
  compose` involvement matters. Keeping it separate makes the
  distinction obvious at a glance (file name, `git diff`, CI job
  mapping) without requiring anyone to know import-time skip logic
  exists inside a 2900-line file to understand why some tests "don't
  run."
- **No changes to any `src/oapi/*.py` file.** Every finding above is
  either a confirmation of correct, spec-compliant behavior, or a
  realm-configuration nuance -- there is nothing to fix in `oapi`
  itself as a result of this investigation.

## Files this plan will add/change

- `tests/docker-compose.yml` (new)
- `tests/keycloak/realm.json` (new)
- `tests/conftest.py` (add one new fixture, `keycloak_url`)
- `tests/test_client_keycloak_integration.py` (new, 7 tests)
- `Makefile` -- no changes; `make test` already runs the full suite,
  which now includes the Keycloak tests (see design decisions above).
  A contributor who wants just these tests locally can run `hatch test
  tests/test_client_keycloak_integration.py -c -vv` directly.
- `.github/workflows/test.yml` -- no changes; the existing `test`
  matrix job already covers this (see design decisions above)
