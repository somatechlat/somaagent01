"""Resolving a local session token into a principal.

``decode_token`` receives a bearer and has to decide which validation stack
is responsible for it. This file covers the session stack: the glue between
the pure routing decision (``services.common.identity.credential``) and the
row that answers for it (``admin.aaas.models.session.LocalSession``).

Three rules are load-bearing here.

* **A session token is never decoded as a JWT.** ``ses_`` is four characters
  at the start of an opaque lookup key. It has no ``kid``, no signature and
  no claims. The proof that routing is correct is not a message string — it
  is that a live session *resolves*: a JWT decoder cannot return a payload
  carrying the session row's id and the identity's current roles.

* **Authority is resolved at request time, never frozen at issuance.** The
  session row holds no roles and no permissions. They are read from the
  identity on every request, so a role change takes effect on the next call
  and a revoked grant cannot survive inside a live session.

* **Offboarding is permanent.** A session whose identity has been disabled
  or removed is killed, not merely refused. Refusing alone would leave a
  live credential sitting in the table waiting for the identity to come
  back.

Run:
    pytest tests/unit/test_identity_decode_session.py -v
"""

from __future__ import annotations

from datetime import timedelta

import pytest
from asgiref.sync import sync_to_async

from admin.common.auth import TokenPayload, decode_token
from admin.common.exceptions import UnauthorizedError
from admin.aaas.models.identity import LocalIdentity
from admin.aaas.models.session import LocalSession
from admin.core.authz import permissions_for_principal
from services.common.identity.session import (
    ABSOLUTE_TIMEOUT,
    SESSION_TOKEN_PREFIX,
    generate_session_token,
    hash_session_token,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


async def _seed_identity(roles: list[str]) -> LocalIdentity:
    """An identity that can hold a session. No password: this file tests
    resolution of a session, not the login that mints one."""
    create = sync_to_async(LocalIdentity.objects.create)
    return await create(
        username="resolvable",
        email="resolvable@example.test",
        display_name="Resolvable Person",
        roles=roles,
        is_active=True,
        password_hash="argon2id-not-used-by-this-path",
    )


async def _mint_session(identity: LocalIdentity, **kwargs) -> tuple[str, LocalSession]:
    """Mint and persist one session for ``identity``."""
    raw, session = LocalSession.build(str(identity.id), **kwargs)
    await sync_to_async(session.save)()
    return raw, session


# ---------------------------------------------------------------------------
# The session token is resolved as a session
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_a_live_session_resolves_to_the_person_who_holds_it():
    """The decisive routing proof.

    A JWT decoder cannot produce this payload: the ``ses_`` token is not
    three dot-separated segments, so ``jwt.get_unverified_header`` would
    refuse it outright. Success here means the session store answered.
    """
    identity = await _seed_identity(["member"])
    raw, _session = await _mint_session(identity)

    payload = await decode_token(raw)

    assert payload.sub == str(identity.id)


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_the_session_row_is_addressable_from_the_payload():
    """``session_id`` names the row, so a kill can be aimed at the exact
    session rather than at every session the principal holds."""
    identity = await _seed_identity(["member"])
    raw, session = await _mint_session(identity)

    payload = await decode_token(raw)

    assert payload.session_id == str(session.id)


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_the_payload_names_the_local_session_store_as_issuer():
    """``iss`` says which authority vouched for the principal. A local
    session is not a Keycloak token and must not claim to be one."""
    identity = await _seed_identity(["member"])
    raw, _session = await _mint_session(identity)

    payload = await decode_token(raw)

    assert payload.iss == "local-session"


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_a_session_carries_the_identitys_display_fields():
    identity = await _seed_identity(["member"])
    raw, _session = await _mint_session(identity)

    payload = await decode_token(raw)

    assert payload.preferred_username == "resolvable"
    assert payload.email == "resolvable@example.test"
    assert payload.name == "Resolvable Person"


# ---------------------------------------------------------------------------
# Authority is resolved at request time
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_a_session_carries_the_roles_the_identity_holds_now():
    """Roles are read on every request, not captured when the session was
    minted. A grant taken away must not survive inside a live session."""
    identity = await _seed_identity(["member"])
    raw, _session = await _mint_session(identity)

    # The person is promoted after the session was issued.
    identity.roles = ["developer"]
    await sync_to_async(identity.save)(update_fields=["roles"])

    payload = await decode_token(raw)

    assert payload.roles == ["developer"]


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_a_session_is_a_person_and_not_an_api_key():
    """A session is the person themselves. A key is a delegation that holds
    scopes and never its issuer's roles — the two must not be confused, so a
    session must not carry ``delegated_scopes``."""
    identity = await _seed_identity(["developer"])
    raw, _session = await _mint_session(identity)

    payload = await decode_token(raw)

    assert payload.is_api_key is False
    assert payload.delegated_scopes is None


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_permissions_are_derived_from_roles_and_never_scopes():
    identity = await _seed_identity(["developer", "trainer"])
    raw, _session = await _mint_session(identity)

    payload = await decode_token(raw)

    assert payload.permissions == sorted(
        permissions_for_principal(roles=["developer", "trainer"])
    )


# ---------------------------------------------------------------------------
# Offboarding is permanent
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_disabling_an_identity_kills_its_session_permanently():
    """Offboarding. Refusing the request would leave a live credential in
    the table waiting for the identity to be re-enabled. The session is
    revoked, so the kill survives the identity coming back."""
    identity = await _seed_identity(["member"])
    raw, session = await _mint_session(identity)

    identity.is_active = False
    await sync_to_async(identity.save)(update_fields=["is_active"])

    with pytest.raises(UnauthorizedError):
        await decode_token(raw)

    refreshed = await sync_to_async(LocalSession.objects.get)(pk=session.id)
    assert refreshed.revoked is True
    assert refreshed.revoked_at is not None


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_removing_an_identity_kills_its_session():
    """A session whose principal no longer exists is orphaned. It must not
    outlive the person it belonged to."""
    identity = await _seed_identity(["member"])
    raw, session = await _mint_session(identity)

    await sync_to_async(identity.delete)()

    with pytest.raises(UnauthorizedError):
        await decode_token(raw)

    refreshed = await sync_to_async(LocalSession.objects.get)(pk=session.id)
    assert refreshed.revoked is True


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_a_killed_session_stays_dead_after_the_identity_returns():
    """Revocation is checked first and wins. Re-enabling the identity must
    not resurrect a session that was killed while they were gone."""
    identity = await _seed_identity(["member"])
    raw, session = await _mint_session(identity)

    identity.is_active = False
    await sync_to_async(identity.save)(update_fields=["is_active"])
    with pytest.raises(UnauthorizedError):
        await decode_token(raw)

    identity.is_active = True
    await sync_to_async(identity.save)(update_fields=["is_active"])

    with pytest.raises(UnauthorizedError):
        await decode_token(raw)

    assert (await sync_to_async(LocalSession.objects.get)(pk=session.id)).revoked is True


# ---------------------------------------------------------------------------
# The session's own lifecycle still applies
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_a_revoked_session_is_refused():
    identity = await _seed_identity(["member"])
    raw, session = await _mint_session(identity)
    session.mark_revoked()
    await sync_to_async(session.save)(update_fields=["revoked", "revoked_at"])

    with pytest.raises(UnauthorizedError):
        await decode_token(raw)


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_an_idle_expired_session_is_refused():
    identity = await _seed_identity(["member"])
    raw, session = await _mint_session(identity)

    stale = session.last_seen_at - timedelta(hours=2)
    await sync_to_async(LocalSession.objects.filter(pk=session.id).update)(
        last_seen_at=stale
    )

    with pytest.raises(UnauthorizedError):
        await decode_token(raw)


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_an_absolute_expired_session_is_refused():
    """Active or not, an old session dies. This is the window an attacker
    holding the cookie cannot talk past by keeping it warm."""
    identity = await _seed_identity(["member"])
    raw, session = await _mint_session(identity)

    long_ago = session.created_at - ABSOLUTE_TIMEOUT - timedelta(minutes=1)
    await sync_to_async(LocalSession.objects.filter(pk=session.id).update)(
        created_at=long_ago, last_seen_at=long_ago
    )

    with pytest.raises(UnauthorizedError):
        await decode_token(raw)


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_using_a_session_advances_the_idle_clock():
    """The idle window slides on use. Without this a person working
    steadily would be logged out mid-task."""
    identity = await _seed_identity(["member"])
    raw, session = await _mint_session(identity)

    stale = session.last_seen_at - timedelta(minutes=20)
    await sync_to_async(LocalSession.objects.filter(pk=session.id).update)(
        last_seen_at=stale
    )

    await decode_token(raw)

    refreshed = await sync_to_async(LocalSession.objects.get)(pk=session.id)
    assert refreshed.last_seen_at > stale


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_the_raw_token_is_never_stored():
    """The table holds a digest. A dump of it must not yield cookies."""
    identity = await _seed_identity(["member"])
    raw, session = await _mint_session(identity)

    assert session.token_hash == hash_session_token(raw)
    assert session.token_hash != raw

    stored = await sync_to_async(
        lambda: list(LocalSession.objects.values_list("token_hash", flat=True))
    )()
    assert raw not in stored


# ---------------------------------------------------------------------------
# Fail-closed on everything that is not a resolvable session
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_an_unknown_session_token_is_refused():
    raw, _hash = generate_session_token()

    with pytest.raises(UnauthorizedError):
        await decode_token(raw)


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_a_bare_session_prefix_is_refused():
    with pytest.raises(UnauthorizedError):
        await decode_token(SESSION_TOKEN_PREFIX)


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_an_empty_bearer_is_refused():
    with pytest.raises(UnauthorizedError):
        await decode_token("")


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_an_unclassifiable_bearer_is_refused_not_guessed():
    """Rule 91. A string that is neither a known prefix nor JWT-shaped must
    not fall through to the federated decoder as a default."""
    with pytest.raises(UnauthorizedError):
        await decode_token("not-a-credential-and-not-a-jwt")


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_a_whitespace_padded_credential_is_refused():
    """A padded bearer is not the credential that was issued. Silently
    trimming it would accept something no authority ever minted."""
    identity = await _seed_identity(["member"])
    raw, _session = await _mint_session(identity)

    with pytest.raises(UnauthorizedError):
        await decode_token(" " + raw)


# ---------------------------------------------------------------------------
# The contract stays closed
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_the_session_principal_carries_no_delegated_scopes():
    """Regression against the API-key path. A session must never grow
    ``delegated_scopes``, because that flag is what switches authority from
    roles to scopes."""
    identity = await _seed_identity(["sysadmin"])
    raw, _session = await _mint_session(identity)

    payload: TokenPayload = await decode_token(raw)

    assert payload.delegated_scopes is None
    assert payload.is_api_key is False
    assert "sysadmin" in payload.roles
