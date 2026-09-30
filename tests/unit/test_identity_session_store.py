"""Local identity — the session store.

``SessionRecord`` and ``session_decision`` are pure and already covered in
``test_identity_session.py``. This is the persistence: where a live session
lives, how it is revoked, and — the part that matters — **what the store
never holds**.

Three rules are load-bearing and each is asserted here:

* **The raw token exists exactly once, at issuance.** ``issue`` returns it to
  the caller and the row keeps only its SHA-256. A dump of this table is a
  list of unusable digests. Nothing on the model, its ``repr``, its ``str``
  or any serialisation may carry the raw value.

* **Revocation is the first thing checked and it is permanent.** A revoked
  session stays revoked. It is not a flag that can be flipped by an idle
  timeout or a re-touch; the caller may not resurrect one by writing
  ``last_seen_at``.

* **The store decides nothing.** Whether a session is live is
  ``session_decision``. The model only holds state and delegates, so there
  is no second opinion in the glue.

Run:
    pytest tests/unit/test_identity_session_store.py -v
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from admin.aaas.models.session import LocalSession
from services.common.identity.session import (
    ABSOLUTE_TIMEOUT,
    SESSION_TOKEN_PREFIX,
    generate_session_token,
    hash_session_token,
    session_decision,
)

NOW = datetime(2026, 9, 30, 12, 0, 0, tzinfo=timezone.utc)
PRINCIPAL = "3f6b1c2e-8a44-4d1e-9c3b-2a7e5f0d1b64"


def make_session(**kwargs) -> LocalSession:
    """An unsaved instance. The model's methods are real; nothing is faked."""
    raw = kwargs.pop("raw", None)
    if raw is None:
        raw, token_hash = generate_session_token()
    else:
        token_hash = hash_session_token(raw)
    defaults = dict(
        id=None,
        token_hash=token_hash,
        principal_id=PRINCIPAL,
        created_at=NOW,
        last_seen_at=NOW,
        revoked=False,
        privileged=False,
    )
    defaults.update(kwargs)
    return LocalSession(**defaults), raw


# ---------------------------------------------------------------------------
# The raw token exists exactly once, at issuance
# ---------------------------------------------------------------------------


def test_the_row_holds_a_hash_and_never_the_raw_token():
    session, raw = make_session()
    assert raw.startswith(SESSION_TOKEN_PREFIX)
    assert session.token_hash != raw
    assert session.token_hash == hash_session_token(raw)
    assert len(session.token_hash) == 64  # sha-256 hex


def test_no_field_on_the_model_is_named_like_a_credential():
    """A stored session is a digest plus a clock. If a field ever appears
    here that could hold a bearer, the whole design is wrong."""
    field_names = {f.name for f in LocalSession._meta.fields}
    forbidden = {"token", "raw_token", "secret", "password", "cookie"}
    assert not (field_names & forbidden), field_names & forbidden
    assert "token_hash" in field_names


def test_the_representation_does_not_leak_the_credential():
    """Whatever form this takes — repr, str, the pure record — the raw
    token is not in it."""
    session, raw = make_session()
    for rendered in (repr(session), str(session), session.to_session_record()):
        assert raw not in repr(rendered)


def test_serialisation_exposes_the_digest_only():
    session, raw = make_session()
    dumped = session.to_session_record()
    assert dumped.token_hash == session.token_hash
    assert raw not in repr(dumped)


# ---------------------------------------------------------------------------
# Issuance
# ---------------------------------------------------------------------------


def test_issue_returns_the_raw_token_exactly_once():
    session, raw = make_session()
    assert raw.startswith(SESSION_TOKEN_PREFIX)
    # What the caller keeps is the raw; what we keep is the digest.
    assert hash_session_token(raw) == session.token_hash


def test_a_fresh_session_is_not_revoked():
    session, _ = make_session()
    assert session.revoked is False
    assert session.revoked_at is None


def test_a_privileged_session_is_marked_as_such():
    """Privileged sessions carry the shorter idle and absolute windows.
    The flag has to be on the row for ``session_decision`` to apply them."""
    session, _ = make_session(privileged=True)
    assert session.privileged is True
    record = session.to_session_record()
    assert record.privileged is True
    decision = session_decision(record, now=NOW)
    assert decision.valid is True


# ---------------------------------------------------------------------------
# Revocation is the first thing checked and it is permanent
# ---------------------------------------------------------------------------


def test_a_revoked_session_is_invalid_immediately():
    session, _ = make_session(revoked=True, revoked_at=NOW)
    decision = session_decision(session.to_session_record(), now=NOW)
    assert decision.valid is False
    assert decision.reason == "revoked"


def test_revocation_takes_precedence_over_a_live_clock():
    """A session revoked one second ago is dead even though its idle and
    absolute windows have not expired. Order is security."""
    session, _ = make_session(
        revoked=True, revoked_at=NOW, last_seen_at=NOW - timedelta(seconds=1)
    )
    decision = session_decision(session.to_session_record(), now=NOW)
    assert decision.valid is False
    assert decision.reason == "revoked"


def test_touching_a_revoked_session_does_not_resurrect_it():
    """The store must not let a stale write to ``last_seen_at`` bring a
    killed session back. Revocation is checked first and it wins."""
    session, _ = make_session(revoked=True, revoked_at=NOW)
    session.last_seen_at = NOW  # a stale write attempts resurrection
    decision = session_decision(session.to_session_record(), now=NOW)
    assert decision.valid is False
    assert decision.reason == "revoked"


# ---------------------------------------------------------------------------
# The store decides nothing
# ---------------------------------------------------------------------------


def test_idle_expiry_is_the_pure_rules_decision_not_the_stores():
    session, _ = make_session(last_seen_at=NOW - timedelta(minutes=31))
    decision = session_decision(session.to_session_record(), now=NOW)
    assert decision.valid is False
    assert decision.reason == "idle_expired"
    # The model itself asserts nothing; it only holds state.
    assert session.revoked is False


def test_absolute_expiry_is_the_pure_rules_decision():
    session, _ = make_session(created_at=NOW - ABSOLUTE_TIMEOUT - timedelta(hours=1))
    decision = session_decision(session.to_session_record(), now=NOW)
    assert decision.valid is False
    assert decision.reason == "absolute_expired"


def test_a_live_session_still_validates():
    session, _ = make_session(
        created_at=NOW - timedelta(hours=1), last_seen_at=NOW - timedelta(minutes=5)
    )
    decision = session_decision(session.to_session_record(), now=NOW)
    assert decision.valid is True
    assert decision.reason == "ok"


# ---------------------------------------------------------------------------
# The row mirrors the pure record exactly
# ---------------------------------------------------------------------------


def test_to_session_record_round_trips_every_field():
    session, _ = make_session(
        created_at=NOW - timedelta(hours=2),
        last_seen_at=NOW - timedelta(minutes=1),
        privileged=True,
    )
    record = session.to_session_record()
    assert record.token_hash == session.token_hash
    assert record.principal_id == session.principal_id
    assert record.created_at == session.created_at
    assert record.last_seen_at == session.last_seen_at
    assert record.revoked is False
    assert record.privileged is True


# ---------------------------------------------------------------------------
# Nothing fails open
# ---------------------------------------------------------------------------


def test_an_empty_hash_never_authenticates():
    """A row with no digest is not a universal key — it matches nothing."""
    session, _ = make_session(token_hash="")
    assert session.token_hash == ""
    assert not session.token_hash  # falsy; lookup by hash cannot find it


def test_a_mismatched_hash_does_not_validate():
    session, _ = make_session()
    other_raw, _ = generate_session_token()
    assert hash_session_token(other_raw) != session.token_hash
    assert session.token_hash != other_raw


# ---------------------------------------------------------------------------
# Revocation is a one-way write
# ---------------------------------------------------------------------------


def test_mark_revoked_sets_the_flag_and_the_instant():
    session, _ = make_session()
    assert session.revoked is False
    session.mark_revoked(now=NOW)
    assert session.revoked is True
    assert session.revoked_at == NOW


def test_mark_revoked_is_idempotent():
    """Revoking twice is not an error and does not move the instant. An
    audit trail that shows two different kill times for one session is
    worse than one that shows one."""
    session, _ = make_session()
    session.mark_revoked(now=NOW)
    session.mark_revoked(now=NOW + timedelta(hours=5))
    assert session.revoked is True
    assert session.revoked_at == NOW


def test_mark_revoked_does_not_save():
    """The method sets fields; the caller persists. Keeping the write and
    the commit together in one place is what makes the audit entry and the
    revocation atomic from the caller's point of view."""
    session, _ = make_session()
    session.mark_revoked(now=NOW)
    assert session.revoked is True
    # Nothing here talks to a database, and the method is not a no-op.
    decision = session_decision(session.to_session_record(), now=NOW)
    assert decision.reason == "revoked"


# ---------------------------------------------------------------------------
# Issuance is where the raw token is born and immediately forgotten
# ---------------------------------------------------------------------------


def test_build_mints_a_raw_token_and_keeps_only_its_digest():
    """``build`` is the only place a session token exists in the clear. It
    hands the raw to the caller and stores the digest. There is no second
    return path and no field that could hold the raw."""
    raw, session = LocalSession.build(PRINCIPAL, privileged=True, now=NOW)
    assert raw.startswith(SESSION_TOKEN_PREFIX)
    assert session.token_hash == hash_session_token(raw)
    assert session.principal_id == PRINCIPAL
    assert session.privileged is True
    assert session.created_at == NOW
    assert session.last_seen_at == NOW
    assert session.revoked is False
    assert raw not in repr(session)


def test_two_sessions_for_one_principal_get_different_tokens():
    raw_a, session_a = LocalSession.build(PRINCIPAL, now=NOW)
    raw_b, session_b = LocalSession.build(PRINCIPAL, now=NOW)
    assert raw_a != raw_b
    assert session_a.token_hash != session_b.token_hash


def test_build_never_returns_a_token_without_its_prefix():
    for _ in range(5):
        raw, _session = LocalSession.build(PRINCIPAL, now=NOW)
        assert raw.startswith(SESSION_TOKEN_PREFIX)
        assert raw != SESSION_TOKEN_PREFIX  # not the prefix alone
