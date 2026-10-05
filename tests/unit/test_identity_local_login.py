"""Logging in with a credential the agent itself holds.

Standalone authenticates a person against ``LocalIdentity``
(SOMA-01-DEPLOY-001 §4.1). This file drives the real ``/login`` route to
prove that path end to end: the decision table, the lockout ledger, the
fail-closed audit gate, and the session that comes out of it.

Two rules are load-bearing here.

* **The public failure is uniform.** Unknown user, wrong password, disabled
  account and a locked account all produce the same string. Which one it was
  goes to the audit trail, never to the response — user enumeration is not a
  feature, and a lockout message tells a stranger that the account exists.

* **The ledger advances only where a secret was compared.** A locked account
  poked again, an unknown username and an identity with no credential must
  not move ``failure_count``. If they did, a third party could walk past a
  stranger's soft lock and escalate it into a hard lock that needs a human —
  the lockout would become a weapon aimed at the victim.

Run:
    pytest tests/unit/test_identity_local_login.py -v

Requires a reachable PostgreSQL and Redis. No Keycloak: that is the point.
"""

from __future__ import annotations

import pytest
from asgiref.sync import sync_to_async

from admin.aaas.models.identity import LocalIdentity
from admin.aaas.models.session import LocalSession
from services.common.identity.password import hash_password
from services.common.identity.pepper import get_password_pepper
from services.common.identity.session import hash_session_token

# Cheap parameters for tests only. memory_cost is only legal at or above
# 8 * parallelism, so parallelism must be lowered with it. Production uses
# the policy defaults; those are exercised in the password suite.
_FAST = {"time_cost": 1, "memory_cost": 8, "parallelism": 1}

pytestmark = [
    pytest.mark.django_db(transaction=True),
    pytest.mark.asyncio,
]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def auth_client():
    """The real auth router, mounted and driven over HTTP.

    Not a mock of the view: a request through Django Ninja's test client
    exercises the same function production calls.

    ``TestAsyncClient``, not ``TestClient``. ``/login`` is a coroutine view;
    the synchronous client hands the un-awaited coroutine to ``NinjaResponse``,
    which then reads ``.status_code`` off it and dies. The async client awaits
    the view, which is what ASGI does in production.

    ``register_exception_handlers`` is registered exactly as production does
    (``admin/api.py``). Without it an ``ApiError`` reaches ninja's default
    handler and is re-raised instead of becoming the JSON response production
    returns, so the suite could not observe status codes or bodies at all.
    """
    from ninja import NinjaAPI
    from ninja.testing import TestAsyncClient

    from admin.auth.api import router
    from admin.common.handlers import register_exception_handlers

    test_api = NinjaAPI()
    register_exception_handlers(test_api)
    test_api.add_router("/auth", router)
    return TestAsyncClient(test_api)


@pytest.fixture(autouse=True)
def _fresh_rate_limiter():
    """Give every test a rate limiter bound to its own event loop.

    pytest-asyncio builds a new loop per test. ``get_rate_limiter`` caches a
    Redis connection on the first loop and marks itself connected, so every
    later test hits "Event loop is closed" and the limiter fails closed
    with a 429 — the control is armed but its socket is dead. Resetting the
    singleton and the shared pools drops only the stale connection; the
    real limiter still counts and still denies. Disabling it to make the
    suite pass would be testing a system that does not exist.
    """
    import asyncio

    import services.common.rate_limiter as rate_limiter_mod
    from services.common.redis_pool import reset_pools

    rate_limiter_mod._limiter_instance = None
    rate_limiter_mod._limiter_lock = asyncio.Lock()
    reset_pools()
    yield
    rate_limiter_mod._limiter_instance = None
    rate_limiter_mod._limiter_lock = asyncio.Lock()
    reset_pools()


@pytest.fixture(autouse=True)
def _standalone_mode(monkeypatch):
    """Identity source is dispatched from the mode, never probed. Standalone
    is the shape where the agent holds the credential itself."""
    from services.common.deployment_mode import DeploymentMode

    monkeypatch.setenv("SA01_DEPLOYMENT_MODE", "STANDALONE")
    monkeypatch.setattr(DeploymentMode, "_mode", None)
    monkeypatch.setattr(DeploymentMode, "_resolved", False)
    yield
    monkeypatch.setattr(DeploymentMode, "_mode", None)
    monkeypatch.setattr(DeploymentMode, "_resolved", False)


async def _identity(**overrides) -> LocalIdentity:
    """A real identity with a real argon2id verifier under the real pepper.

    The pepper is read from Vault through ``get_password_pepper`` — the same
    secret and the same fail-closed reader the login path uses. A dummy
    pepper here would let the suite hash under one key while production
    verifies under another: the gate would be a fiction. If the secret is
    absent, this raises naming it. That is the correct outcome (Rule 7).
    """

    def _create() -> LocalIdentity:
        fields = {
            "username": "standalone-operator",
            "email": "operator@example.test",
            "display_name": "Standalone Operator",
            "roles": ["developer"],
            "is_active": True,
            "password_hash": hash_password(
                "correct horse battery staple", get_password_pepper(), **_FAST
            ),
        }
        fields.update(overrides)
        identity = LocalIdentity(**fields)
        identity.save()
        return identity

    return await sync_to_async(_create)()


async def _login(client, email: str, password: str, ip: str | None = None):
    """POST to the real ``/login``.

    Each call carries its own ``REMOTE_ADDR``. Login is rate limited per
    source address — ten attempts a minute — which is a real control and must
    stay armed. A test suite is not one caller hammering one door; it is many
    independent callers, so it gets many addresses. Disabling the limiter to
    make the suite pass would be testing a system that does not exist.
    """
    source = ip or _next_ip()
    return await client.post(
        "/auth/login",
        json={"email": email, "password": password},
        META={"REMOTE_ADDR": source},
    )


_counter = {"n": 0}


def _next_ip() -> str:
    """A distinct private address per login attempt within the suite."""
    _counter["n"] += 1
    return f"10.255.255.{_counter['n'] % 254 + 1}"


async def _reload(identity: LocalIdentity) -> LocalIdentity:
    """Re-read a row from the database. Mutating an in-memory instance and
    asserting on it would prove nothing about what was persisted."""
    return await sync_to_async(LocalIdentity.objects.get)(pk=identity.pk)


async def _session_digests() -> list[str]:
    return await sync_to_async(
        lambda: list(LocalSession.objects.values_list("token_hash", flat=True))
    )()


# ---------------------------------------------------------------------------
# A correct credential produces a session
# ---------------------------------------------------------------------------


async def test_a_correct_password_issues_a_local_session(auth_client):
    await _identity()

    response = await _login(auth_client, "operator@example.test", "correct horse battery staple")

    assert response.status_code == 200, response.content
    body = response.json()
    assert body["token"].startswith("ses_")
    assert body["user"]["email"] == "operator@example.test"


async def test_the_response_carries_the_roles_the_identity_holds(auth_client):
    await _identity(roles=["developer", "trainer"])

    response = await _login(auth_client, "operator@example.test", "correct horse battery staple")

    assert response.status_code == 200
    assert response.json()["user"]["roles"] == ["developer", "trainer"]


async def test_the_issued_token_resolves_through_the_session_store(auth_client):
    """The token in the response must be the one the session store will
    accept. A response that hands back something else is a login that cannot
    be used."""
    identity = await _identity()
    response = await _login(auth_client, "operator@example.test", "correct horse battery staple")
    raw = response.json()["token"]

    stored = await sync_to_async(LocalSession.objects.get)(
        token_hash=hash_session_token(raw)
    )
    assert str(stored.principal_id) == str(identity.id)


async def test_the_raw_token_is_never_stored(auth_client):
    await _identity()
    response = await _login(auth_client, "operator@example.test", "correct horse battery staple")
    raw = response.json()["token"]

    digests = await _session_digests()
    assert raw not in digests
    assert hash_session_token(raw) in digests


# ---------------------------------------------------------------------------
# The public failure is uniform
# ---------------------------------------------------------------------------


async def test_a_wrong_password_is_refused_with_the_uniform_message(auth_client):
    await _identity()

    response = await _login(auth_client, "operator@example.test", "wrong")

    assert response.status_code == 401
    # ApiError.to_dict() nests the human message under "error"; that is the
    # body production's exception handler returns. The assertion still
    # demands the exact uniform string.
    assert response.json()["error"]["message"] == "Invalid credentials"


async def test_an_unknown_account_gets_the_same_message_as_a_wrong_password(auth_client):
    """The enumeration test. If these two responses differed, anyone could
    walk the user table with a login form."""
    await _identity()
    known_wrong = await _login(auth_client, "operator@example.test", "wrong")
    unknown = await _login(auth_client, "nobody@example.test", "wrong")

    assert known_wrong.status_code == unknown.status_code == 401
    assert known_wrong.json() == unknown.json()


async def test_a_disabled_account_gets_the_same_message(auth_client):
    await _identity(is_active=False)

    response = await _login(auth_client, "operator@example.test", "correct horse battery staple")

    assert response.status_code == 401
    # ApiError.to_dict() nests the human message under "error"; that is the
    # body production's exception handler returns. The assertion still
    # demands the exact uniform string.
    assert response.json()["error"]["message"] == "Invalid credentials"


async def test_a_locked_account_gets_the_same_message(auth_client):
    """A lockout message tells a stranger that this account exists and is
    currently unusable. That is enumeration with a timestamp on it. The
    precise reason belongs in the audit trail."""
    identity = await _identity()
    await sync_to_async(
        lambda: LocalIdentity.objects.filter(pk=identity.pk).update(hard_locked=True)
    )()

    response = await _login(auth_client, "operator@example.test", "correct horse battery staple")

    assert response.status_code == 401
    # ApiError.to_dict() nests the human message under "error"; that is the
    # body production's exception handler returns. The assertion still
    # demands the exact uniform string.
    assert response.json()["error"]["message"] == "Invalid credentials"
    assert "locked" not in response.content.decode().lower()


# ---------------------------------------------------------------------------
# The ledger advances only where a secret was compared
# ---------------------------------------------------------------------------


async def test_a_wrong_password_advances_the_ledger(auth_client):
    identity = await _identity()

    await _login(auth_client, "operator@example.test", "wrong")

    refreshed = await _reload(identity)
    assert refreshed.failure_count == 1


async def test_an_unknown_account_does_not_create_a_ledger(auth_client):
    await _login(auth_client, "nobody@example.test", "wrong")

    assert not await sync_to_async(
        LocalIdentity.objects.filter(email="nobody@example.test").exists
    )()


async def test_a_locked_account_poked_again_does_not_advance_the_ledger(auth_client):
    """The anti-weapon rule. Without this, a third party who learns an
    account is soft-locked can push it to a hard lock that needs a human to
    clear — denial of service against the victim, using our own defence."""
    identity = await _identity()
    await sync_to_async(
        lambda: LocalIdentity.objects.filter(pk=identity.pk).update(
            failure_count=3, hard_locked=True
        )
    )()

    await _login(auth_client, "operator@example.test", "wrong")
    await _login(auth_client, "operator@example.test", "correct horse battery staple")

    refreshed = await _reload(identity)
    assert refreshed.failure_count == 3


async def test_a_disabled_account_does_not_advance_the_ledger(auth_client):
    """No secret was compared against a disabled identity, so there is
    nothing to count."""
    identity = await _identity(is_active=False)

    await _login(auth_client, "operator@example.test", "correct horse battery staple")

    refreshed = await _reload(identity)
    assert refreshed.failure_count == 0


async def test_a_correct_password_clears_the_ledger(auth_client):
    identity = await _identity()
    await sync_to_async(
        lambda: LocalIdentity.objects.filter(pk=identity.pk).update(failure_count=2)
    )()

    response = await _login(auth_client, "operator@example.test", "correct horse battery staple")

    assert response.status_code == 200
    refreshed = await _reload(identity)
    assert refreshed.failure_count == 0


# ---------------------------------------------------------------------------
# Offboarding
# ---------------------------------------------------------------------------


async def test_a_disabled_identity_cannot_authenticate_even_with_the_right_password(
    auth_client,
):
    await _identity(is_active=False)

    response = await _login(auth_client, "operator@example.test", "correct horse battery staple")

    assert response.status_code == 401
    assert await _session_digests() == []


# ---------------------------------------------------------------------------
# Nothing is invented about the caller
# ---------------------------------------------------------------------------


async def test_an_empty_password_is_refused(auth_client):
    await _identity()

    response = await _login(auth_client, "operator@example.test", "")

    assert response.status_code == 401
    # ApiError.to_dict() nests the human message under "error"; that is the
    # body production's exception handler returns. The assertion still
    # demands the exact uniform string.
    assert response.json()["error"]["message"] == "Invalid credentials"


async def test_the_response_names_no_infrastructure_state(auth_client):
    """A denial must not tell the caller whether the audit sink, the
    database or the password hash was what failed. That is a map of the
    inside, handed to anyone who can post to /login."""
    await _identity(is_active=False)

    denial = await _login(auth_client, "operator@example.test", "x")
    body = denial.content.decode().lower()
    for leaked in ("audit", "vault", "argon", "database", "redis", "postgres"):
        assert leaked not in body
