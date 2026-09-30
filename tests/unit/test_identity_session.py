"""Local identity — opaque session tokens and session lifetime.

Browser sessions are **opaque**. Not JWT. A JWT is a bearer credential that
is valid until it expires and cannot be taken back; an opaque token is a
lookup key into a server-side record that can be killed in one write. For an
agent that administers itself, "revoke now" matters more than "no round
trip".

Properties tested here:

* The token is 256 bits from the CSPRNG and carries no structure an attacker
  can forge or a caller can parse.
* Only its **hash** is storable. A dump of the session table must not yield
  working cookies.
* Two lifetimes, not one: idle and absolute. The absolute cap cannot be
  extended by activity — otherwise a stolen session is permanent.
* Revocation is immediate and is checked first.

The clock is passed in. Persistence is the caller's.

Run:
    pytest tests/unit/test_identity_session.py -v
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from services.common.identity.session import (
    ABSOLUTE_TIMEOUT,
    IDLE_TIMEOUT,
    PRIVILEGED_ABSOLUTE_TIMEOUT,
    PRIVILEGED_IDLE_TIMEOUT,
    SESSION_TOKEN_PREFIX,
    SessionRecord,
    generate_session_token,
    hash_session_token,
    session_decision,
)

NOW = datetime(2026, 9, 30, 12, 0, 0, tzinfo=timezone.utc)


def record(
    *,
    revoked: bool = False,
    created: datetime = NOW - timedelta(minutes=1),
    last_seen: datetime = NOW - timedelta(minutes=1),
    privileged: bool = False,
) -> SessionRecord:
    return SessionRecord(
        token_hash="stored-hash",
        principal_id="user-1",
        created_at=created,
        last_seen_at=last_seen,
        revoked=revoked,
        privileged=privileged,
    )


# ---------------------------------------------------------------------------
# Token shape
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_generate_session_token_returns_a_prefixed_raw_token_and_its_hash():
    raw, token_hash = generate_session_token()
    assert raw.startswith(SESSION_TOKEN_PREFIX)
    assert raw != token_hash
    assert len(raw) > len(SESSION_TOKEN_PREFIX) + 40


@pytest.mark.unit
def test_tokens_are_256_bits_of_entropy_not_a_uuid():
    """A UUID is 122 bits and half of it is predictable. Not good enough for
    a credential that unlocks an enterprise agent."""
    raw, _ = generate_session_token()
    body = raw[len(SESSION_TOKEN_PREFIX) :]
    assert len(body) >= 43  # 256 bits of urlsafe base64


@pytest.mark.unit
def test_two_tokens_are_never_the_same():
    tokens = {generate_session_token()[0] for _ in range(50)}
    assert len(tokens) == 50


@pytest.mark.unit
def test_the_hash_is_deterministic_and_one_way():
    raw, token_hash = generate_session_token()
    assert hash_session_token(raw) == token_hash
    assert hash_session_token(raw) != raw
    assert token_hash not in raw
    assert raw not in token_hash


@pytest.mark.unit
def test_a_token_hash_is_stable_across_calls_so_it_can_be_looked_up():
    raw, token_hash = generate_session_token()
    assert [hash_session_token(raw) for _ in range(5)] == [token_hash] * 5


# ---------------------------------------------------------------------------
# Lifetime
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_a_fresh_session_is_valid():
    decision = session_decision(record(), now=NOW)
    assert decision.valid is True
    assert decision.reason == "ok"


@pytest.mark.unit
def test_idle_timeout_expires_a_session_that_has_been_unused():
    stale = record(last_seen=NOW - IDLE_TIMEOUT - timedelta(seconds=1))
    decision = session_decision(stale, now=NOW)
    assert decision.valid is False
    assert decision.reason == "idle_expired"


@pytest.mark.unit
def test_absolute_timeout_expires_a_session_no_matter_how_active_it_is():
    """The absolute cap is the one that cannot be talked past.

    A session opened twelve hours ago is dead even if the client has been
    clicking the whole time. Otherwise a stolen session is permanent.
    """
    ancient = record(
        created=NOW - ABSOLUTE_TIMEOUT - timedelta(minutes=1),
        last_seen=NOW,  # still active
    )
    decision = session_decision(ancient, now=NOW)
    assert decision.valid is False
    assert decision.reason == "absolute_expired"


@pytest.mark.unit
def test_privileged_sessions_time_out_sooner():
    """sysadmin / org_admin / agent_owner hold more, so they get less rope."""
    assert PRIVILEGED_IDLE_TIMEOUT < IDLE_TIMEOUT
    assert PRIVILEGED_ABSOLUTE_TIMEOUT < ABSOLUTE_TIMEOUT

    boundary = NOW - PRIVILEGED_IDLE_TIMEOUT - timedelta(seconds=1)
    assert session_decision(record(privileged=True, last_seen=boundary), now=NOW).valid is False
    assert session_decision(record(privileged=False, last_seen=boundary), now=NOW).valid is True


# ---------------------------------------------------------------------------
# Revocation
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_revocation_beats_everything():
    """A revoked session is dead on the next request, not at expiry."""
    otherwise_fine = record(revoked=True)
    decision = session_decision(otherwise_fine, now=NOW)
    assert decision.valid is False
    assert decision.reason == "revoked"


@pytest.mark.unit
def test_revocation_wins_over_a_live_window_and_recent_activity():
    fresh = record(revoked=True, created=NOW, last_seen=NOW)
    assert session_decision(fresh, now=NOW).valid is False


# ---------------------------------------------------------------------------
# Boundaries — a session is valid right up to the cap, not past it
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_a_session_is_valid_exactly_up_to_the_idle_cap():
    at_cap = record(last_seen=NOW - IDLE_TIMEOUT)
    assert session_decision(at_cap, now=NOW).valid is True

    past_cap = record(last_seen=NOW - IDLE_TIMEOUT - timedelta(seconds=1))
    assert session_decision(past_cap, now=NOW).valid is False


@pytest.mark.unit
def test_a_session_is_valid_exactly_up_to_the_absolute_cap():
    at_cap = record(created=NOW - ABSOLUTE_TIMEOUT, last_seen=NOW)
    assert session_decision(at_cap, now=NOW).valid is True

    past_cap = record(created=NOW - ABSOLUTE_TIMEOUT - timedelta(seconds=1), last_seen=NOW)
    assert session_decision(past_cap, now=NOW).valid is False


# ---------------------------------------------------------------------------
# No credential material in the record
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_the_record_stores_a_hash_and_never_the_token():
    raw, token_hash = generate_session_token()
    stored = SessionRecord(
        token_hash=token_hash,
        principal_id="user-1",
        created_at=NOW,
        last_seen_at=NOW,
        revoked=False,
        privileged=False,
    )
    assert raw not in repr(stored)
    assert stored.token_hash == token_hash
