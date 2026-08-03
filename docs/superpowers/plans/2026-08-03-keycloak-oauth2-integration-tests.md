# Keycloak OAuth2/OIDC Integration Tests: Plan

See the design rationale in
`docs/superpowers/specs/2026-08-03-keycloak-oauth2-integration-tests-design.md`
before executing this plan -- it explains *why* each file below looks
the way it does (scope analysis, protocol-compliance findings, the
realm-configuration gotcha, the auto-provisioning fixture design).

Every file below has already been validated end-to-end, live, against
a real Keycloak 26.0 instance (not just written and assumed correct):

- `hatch run mypy --strict --ignore-missing-imports` is clean on
  `tests/conftest.py` and `tests/test_client_keycloak_integration.py`.
- `hatch fmt --check` is clean on both.
- A cold run (no containers running beforehand) auto-provisions
  Keycloak via the `keycloak_url` fixture, all 7 tests pass in ~10s
  total, and the container is confirmed removed afterward.
- A warm run (Keycloak already running) reuses it in under a second
  and leaves it running afterward (the fixture only tears down what it
  started).
- `hatch test tests/test_client_keycloak_integration.py -c -vv` was run
  directly, cold, and passed.
- The full suite (`hatch run hatch-test.py3.10:pytest tests/ -q`) was
  re-run after these changes: 406 passed, 0 skipped (Docker is
  available on the machine these changes were validated on, so the
  Keycloak tests ran for real as part of the full suite too, not just
  in isolation).

Execution is therefore mechanical: create/edit each file with the
exact content below, then re-run the verification commands in
"Verification" to confirm nothing has drifted.

## Files

### 1. `tests/docker-compose.yml` (new)

```yaml
services:
  keycloak:
    image: quay.io/keycloak/keycloak:26.0
    command: start-dev --import-realm
    environment:
      KC_BOOTSTRAP_ADMIN_USERNAME: admin
      KC_BOOTSTRAP_ADMIN_PASSWORD: admin
      KC_HEALTH_ENABLED: "true"
    ports:
      - "127.0.0.1:8080:8080"
      - "127.0.0.1:9000:9000"
    volumes:
      - ./keycloak/realm.json:/opt/keycloak/data/import/realm.json:ro
    healthcheck:
      test:
        - CMD-SHELL
        - >-
          exec 3<>/dev/tcp/localhost/9000;
          printf 'GET /health/ready HTTP/1.1\r\nhost: localhost\r\nConnection: close\r\n\r\n' >&3;
          grep -q '"UP"' <&3
      interval: 3s
      timeout: 3s
      retries: 20
      start_period: 5s
```

Notes for whoever executes this: the healthcheck avoids `curl`
(absent from the Keycloak image) via a `/dev/tcp` bash trick against
the management port's `/health/ready` endpoint. `Connection: close` is
required in the crafted request -- without it, keep-alive means the
socket never closes and the healthcheck hangs.

The ports are bound explicitly to `127.0.0.1`, not just `8080:8080`/
`9000:9000` -- Docker's default (no host IP given) binds `0.0.0.0`,
exposing this admin/admin-credentialed, ephemeral Keycloak instance to
the entire local network for the ~10 seconds it's up on a
contributor's machine. Loopback-only binding is the correct default
for a test fixture with no legitimate need for LAN access.

### 2. `tests/keycloak/realm.json` (new)

```json
{
  "realm": "oapi-test",
  "enabled": true,
  "sslRequired": "none",
  "clients": [
    {
      "clientId": "password-grant-client",
      "publicClient": true,
      "directAccessGrantsEnabled": true,
      "standardFlowEnabled": false,
      "serviceAccountsEnabled": false,
      "enabled": true
    },
    {
      "clientId": "client-credentials-client",
      "publicClient": false,
      "secret": "test-secret",
      "clientAuthenticatorType": "client-secret",
      "directAccessGrantsEnabled": false,
      "standardFlowEnabled": false,
      "serviceAccountsEnabled": true,
      "enabled": true
    }
  ],
  "users": [
    {
      "username": "testuser",
      "enabled": true,
      "email": "testuser@example.com",
      "emailVerified": true,
      "firstName": "Test",
      "lastName": "User",
      "requiredActions": [],
      "credentials": [
        {
          "type": "password",
          "value": "testpassword",
          "temporary": false
        }
      ]
    }
  ]
}
```

Notes: `email`/`firstName`/`lastName` on `testuser` are required --
Keycloak 26's "User Profile" feature rejects the password grant with a
real `400 invalid_grant: "Account is not fully set up"` for a user
missing these, independent of anything `oapi` does.

Trap to avoid while creating this file: if `docker compose -f
tests/docker-compose.yml up` ever runs *before* this file exists at
this exact path, Docker silently creates an empty directory here
instead of erroring, which then silently breaks the realm import
(Keycloak just starts with an empty realm, no error, no "Full
importing from file..." log line). Create this file first, and only
then run `docker compose up` for the first time. If this happens
anyway, `docker compose -f tests/docker-compose.yml down`, `rm -rf
tests/keycloak`, recreate the real file, and confirm `file
tests/keycloak/realm.json` reports "JSON data" (not "directory")
before retrying.

### 3. `tests/conftest.py` (edit: add imports and one new fixture)

Add to the existing import block:

```python
import contextlib
import shutil
import subprocess
```

(`os`, `urllib.error`, and `urllib.request` are already imported for
other reasons in the current file -- if executing this plan against a
tree where they aren't yet present, add those too.)

Append at the end of the file:

```python
_COMPOSE_FILE: Path = Path(__file__).resolve().parent / "docker-compose.yml"


@pytest.fixture(scope="session")
def keycloak_url() -> Iterator[str]:
    """
    The base URL of a real Keycloak instance configured with this
    repository's `tests/keycloak/realm.json` test realm.

    If Keycloak is already reachable (e.g. a developer or CI step
    already started it), that instance is used as-is. Otherwise, if
    Docker is available, this fixture runs `docker compose up -d
    --wait` itself and tears the service back down at the end of the
    test session -- no manual setup step is required. If Docker isn't
    available, or Keycloak never becomes reachable, every test
    depending on this fixture is skipped rather than failed, since
    these are opt-in integration tests, not required for a normal
    `pytest`/`hatch test` run.
    """
    url: str = os.environ.get("KEYCLOAK_URL", "http://localhost:8080")
    discovery_url: str = (
        f"{url}/realms/oapi-test/.well-known/openid-configuration"
    )

    def reachable() -> bool:
        try:
            with urllib.request.urlopen(discovery_url, timeout=2) as response:
                return bool(response.status == 200)
        except (urllib.error.URLError, OSError):
            return False

    if reachable():
        yield url
        return
    if shutil.which("docker") is None:
        pytest.skip(
            "Keycloak is not reachable at "
            f"{url!r}, and Docker is not installed to start it "
            "automatically -- install Docker to enable these tests."
        )
    try:
        subprocess.run(
            [
                "docker",
                "compose",
                "-f",
                str(_COMPOSE_FILE),
                "up",
                "-d",
                "--wait",
            ],
            check=True,
            timeout=120,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        pytest.skip(
            "Keycloak is not reachable at "
            f"{url!r}, and `docker compose up` failed to start it -- "
            "run `docker compose up -d --wait` manually to debug."
        )
    if not reachable():
        pytest.skip(
            f"Keycloak did not become reachable at {url!r} after "
            "`docker compose up -d --wait`."
        )
    try:
        yield url
    finally:
        with contextlib.suppress(subprocess.TimeoutExpired):
            subprocess.run(
                ["docker", "compose", "-f", str(_COMPOSE_FILE), "down"],
                check=False,
                timeout=60,
            )
```

The teardown `docker compose down` call has its own `timeout=60` (and
a `contextlib.suppress` around the `TimeoutExpired` it can raise),
matching the `timeout=120` already on the `up` call -- without it, a
hung or unresponsive Docker daemon at teardown would hang the entire
pytest session with no clear error, rather than failing loudly or at
least returning control to the test runner.

Design note: the fixture makes no platform assumption. It works
anywhere `docker` is on `PATH` and functional -- a Linux CI runner, or
a contributor's own macOS/Windows machine with Docker Desktop
installed (verified live on macOS during validation). There is
deliberately no `sys.platform` gate; `shutil.which` plus the
`try`/`except` around `subprocess.run` already degrade safely
(`pytest.skip`) anywhere Docker isn't usable, without hard-coding
which platforms that might be true on.

The fixture only tears down the container it itself started (tracked
implicitly: the `finally` block is only reachable via the branch that
ran `docker compose up`). If Keycloak was already running when the
fixture first checked, it's left exactly as it was found.

### 4. `tests/test_client_keycloak_integration.py` (new)

```python
from __future__ import annotations

import json
from urllib.error import HTTPError

import pytest

from oapi.client import Client


def _token_url(keycloak_url: str) -> str:
    return f"{keycloak_url}/realms/oapi-test/protocol/openid-connect/token"


def _oidc_discovery_url(keycloak_url: str) -> str:
    return f"{keycloak_url}/realms/oapi-test/.well-known/openid-configuration"


def test_oauth2_password_grant_against_a_real_keycloak(
    keycloak_url: str,
) -> None:
    """
    `password-grant-client` (a real, *public* Keycloak client, per
    `tests/keycloak/realm.json`) works with `oapi`'s password-grant
    implementation as-is: `_request_oauth2_password_authorization`
    never sends a `client_secret`, so the OAuth2 spec requires the
    client be public (or otherwise not require client authentication)
    for this flow to succeed against a real, spec-compliant server.
    """
    client: Client = Client(
        oauth2_client_id="password-grant-client",
        oauth2_username="testuser",
        oauth2_password="testpassword",
        oauth2_token_url=_token_url(keycloak_url),
        timeout=10,
    )
    with client._request_oauth2_password_authorization() as response:
        token_response: dict[str, object] = json.loads(response.read())
    assert token_response["token_type"] == "Bearer"
    assert isinstance(token_response["access_token"], str)


def test_oauth2_password_grant_rejects_wrong_credentials(
    keycloak_url: str,
) -> None:
    client: Client = Client(
        oauth2_client_id="password-grant-client",
        oauth2_username="testuser",
        oauth2_password="wrong-password",
        oauth2_token_url=_token_url(keycloak_url),
        timeout=10,
    )
    with pytest.raises(HTTPError) as excinfo:
        client._request_oauth2_password_authorization()
    assert excinfo.value.code == 401


def test_oauth2_client_credentials_grant_against_a_real_keycloak(
    keycloak_url: str,
) -> None:
    """
    `client-credentials-client` is a real, *confidential* Keycloak
    client with a service account enabled. `oapi` sends `client_id`/
    `client_secret` as form-body parameters (not HTTP Basic auth) --
    Keycloak's default client authenticator accepts both, so this
    succeeds against a real server without any special configuration.
    """
    client: Client = Client(
        oauth2_client_id="client-credentials-client",
        oauth2_client_secret="test-secret",
        oauth2_token_url=_token_url(keycloak_url),
        timeout=10,
    )
    with client._request_oauth2_client_credentials_authorization() as (
        response
    ):
        token_response: dict[str, object] = json.loads(response.read())
    assert token_response["token_type"] == "Bearer"
    assert isinstance(token_response["access_token"], str)


def test_oauth2_client_credentials_grant_rejects_a_wrong_secret(
    keycloak_url: str,
) -> None:
    client: Client = Client(
        oauth2_client_id="client-credentials-client",
        oauth2_client_secret="wrong-secret",
        oauth2_token_url=_token_url(keycloak_url),
        timeout=10,
    )
    with pytest.raises(HTTPError) as excinfo:
        client._request_oauth2_client_credentials_authorization()
    assert excinfo.value.code == 401


def test_oidc_discovery_derives_the_real_token_url(
    keycloak_url: str,
) -> None:
    client: Client = Client(
        open_id_connect_url=_oidc_discovery_url(keycloak_url),
        timeout=10,
    )
    assert client._get_oauth2_token_url() == _token_url(keycloak_url)


def test_client_credentials_grant_authenticates_a_real_protected_request(
    keycloak_url: str,
) -> None:
    """
    End-to-end: a `Client` configured for the client-credentials flow
    automatically fetches and attaches a real bearer token to a real
    request against Keycloak's own `/userinfo` endpoint (used here as
    a stand-in protected resource) -- confirming the token `oapi`
    obtains is genuinely accepted, not just successfully parsed.
    """
    client: Client = Client(
        url=keycloak_url,
        oauth2_client_id="client-credentials-client",
        oauth2_client_secret="test-secret",
        oauth2_token_url=_token_url(keycloak_url),
        oauth2_scope="openid",
        timeout=10,
    )
    with client.request(
        "/realms/oapi-test/protocol/openid-connect/userinfo", "GET"
    ) as response:
        userinfo: dict[str, object] = json.loads(response.read())
    assert userinfo["preferred_username"] == (
        "service-account-client-credentials-client"
    )


def test_client_credentials_grant_caches_the_token_across_requests(
    keycloak_url: str,
) -> None:
    client: Client = Client(
        url=keycloak_url,
        oauth2_client_id="client-credentials-client",
        oauth2_client_secret="test-secret",
        oauth2_token_url=_token_url(keycloak_url),
        oauth2_scope="openid",
        timeout=10,
    )
    with client.request(
        "/realms/oapi-test/protocol/openid-connect/userinfo", "GET"
    ) as response:
        response.read()
    first_authorization: str | None = client.headers.get("Authorization")
    with client.request(
        "/realms/oapi-test/protocol/openid-connect/userinfo", "GET"
    ) as response:
        response.read()
    second_authorization: str | None = client.headers.get("Authorization")
    assert first_authorization == second_authorization
```

Note: no CI workflow changes are needed. `.github/workflows/test.yml`'s
existing `test` job already runs the full `tests/` suite across its
matrix, so this new file runs there automatically -- auto
-provisioning and passing on `ubuntu-latest` legs (Docker is present),
and cleanly skipping wherever Docker isn't available/compatible
(`macos-latest`, and `windows-latest` unless it has a working Linux
-container Docker setup), with no separate job, no platform gate, and
no explicit `docker compose` step required. This was confirmed live:
`hatch test -c -py '3.10'` run against the whole suite passed with the
Keycloak tests included, and `hatch fmt --check`/`hatch run mypy`
(the `lint` job) remain unaffected since nothing there depends on
Docker.

Note: no `Makefile` changes are needed either, for the same reason --
`make test` already runs `hatch test -c -vv` over the whole suite, so
it auto-provisions and runs the Keycloak tests too when Docker is
available, with no dedicated target required. A contributor who wants
to run just the Keycloak tests locally can do so directly with `hatch
test tests/test_client_keycloak_integration.py -c -vv`.

## Verification

After making the changes above, run:

```sh
hatch run mypy --strict --ignore-missing-imports tests/conftest.py tests/test_client_keycloak_integration.py
hatch fmt --check
docker compose -f tests/docker-compose.yml down 2>/dev/null || true
hatch test tests/test_client_keycloak_integration.py -c -vv
docker compose -f tests/docker-compose.yml ps   # confirm no leftover container
make test
git checkout -- tests/input-data/languagetool-swagger.json
```

All of the above were run during plan validation and passed cleanly.
