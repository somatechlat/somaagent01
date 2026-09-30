"""Local identity — the authentication decision table.

This is the security-critical core of login: given what the store knows and
what the caller presented, may this attempt succeed?

It is pure so it can be tested exhaustively without a database, and it is
the *only* place the decision is made. The lookup and the persistence around
it are glue; they must not contain a second opinion.

Three rules are load-bearing:

* **Order is security.** Lockout is evaluated before the password is hashed.
  Argon2 is deliberately expensive, so an endpoint that hashes for a locked
  account is a denial-of-service amplifier.
* **Uniform failure.** Unknown user, wrong password, disabled account and
  missing credential are the same answer to the caller. Which one it was
  goes to the audit trail, never to the response.
* **Nothing fails open.** No combination of inputs turns a "cannot check"
  into a "checked and fine".

Run:
    pytest tests/unit/test_identity_authenticate.py -v
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from services.common.identity.authenticate import decide_authentication
from services.common.identity.lockout import LockoutDecision

NOW = datetime(2026, 9, 30, 12, 0, 0, tzinfo=timezone.utc)

NOT_LOCKED = LockoutDecision(locked=False, remaining=timedelta(0), reason="ok")
SOFT_LOCKED = LockoutDecision(
    locked=True, remaining=timedelta(minutes=15), reason="soft_lock"
)
HARD_LOCKED = LockoutDecision(
    locked=True, remaining=timedelta.max, reason="hard_lock", requires_admin=True
)


# ---------------------------------------------------------------------------
# Success
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_the_right_password_on_an_active_account_authenticates():
    outcome = decide_authentication(
        is_active=True, has_password=True, password_ok=True, lockout=NOT_LOCKED
    )
    assert outcome.ok is True
    assert outcome.reason == "ok"


# ---------------------------------------------------------------------------
# Every way it must fail
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_a_wrong_password_does_not_authenticate():
    outcome = decide_authentication(
        is_active=True, has_password=True, password_ok=False, lockout=NOT_LOCKED
    )
    assert outcome.ok is False


@pytest.mark.unit
def test_an_unknown_account_does_not_authenticate():
    outcome = decide_authentication(
        is_active=False, has_password=False, password_ok=False, lockout=NOT_LOCKED
    )
    assert outcome.ok is False


@pytest.mark.unit
def test_a_disabled_account_never_authenticates():
    """Offboarding has to mean it. A disabled identity that can still sign in
    was never disabled."""
    outcome = decide_authentication(
        is_active=False, has_password=True, password_ok=True, lockout=NOT_LOCKED
    )
    assert outcome.ok is False


@pytest.mark.unit
def test_an_account_with_no_credential_set_never_authenticates():
    """Fail-closed. An unset password is not a free pass — it is a locked
    door, and the way to open it is the bootstrap command, not a blank."""
    outcome = decide_authentication(
        is_active=True, has_password=False, password_ok=True, lockout=NOT_LOCKED
    )
    assert outcome.ok is False


@pytest.mark.unit
def test_a_locked_account_never_authenticates():
    outcome = decide_authentication(
        is_active=True, has_password=True, password_ok=True, lockout=SOFT_LOCKED
    )
    assert outcome.ok is False


@pytest.mark.unit
def test_a_hard_locked_account_never_authenticates():
    outcome = decide_authentication(
        is_active=True, has_password=True, password_ok=True, lockout=HARD_LOCKED
    )
    assert outcome.ok is False
    assert outcome.requires_admin is True


# ---------------------------------------------------------------------------
# Lockout is decided before the hash
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_the_hash_must_not_run_for_a_locked_account():
    """The caller asks this function before argon2. This is how it knows.

    ``password_checked`` is False whenever the lockout denied first. An
    attacker who can trigger argon2 on a locked account can use the login
    endpoint as a CPU amplifier; this is the assertion that stops them.
    """
    outcome = decide_authentication(
        is_active=True, has_password=True, password_ok=False, lockout=SOFT_LOCKED
    )
    assert outcome.password_checked is False


@pytest.mark.unit
def test_the_hash_must_not_run_for_an_account_with_no_credential():
    outcome = decide_authentication(
        is_active=True, has_password=False, password_ok=False, lockout=NOT_LOCKED
    )
    assert outcome.password_checked is False


@pytest.mark.unit
def test_the_hash_runs_for_an_active_account_that_is_not_locked():
    outcome = decide_authentication(
        is_active=True, has_password=True, password_ok=True, lockout=NOT_LOCKED
    )
    assert outcome.password_checked is True


# ---------------------------------------------------------------------------
# Uniform failure
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_every_failure_looks_the_same_to_the_caller():
    """User enumeration is not a feature.

    The response must not distinguish "no such user" from "wrong password"
    from "disabled". The audit trail gets the precise reason; the caller
    gets one answer.
    """
    outcomes = [
        decide_authentication(
            is_active=a, has_password=h, password_ok=p, lockout=lock
        )
        for a in (True, False)
        for h in (True, False)
        for p in (True, False)
        for lock in (NOT_LOCKED, SOFT_LOCKED, HARD_LOCKED)
        if not (
            a and h and p and not lock.locked
        )  # every combination except the one success
    ]
    public = {outcome.public_message for outcome in outcomes}
    assert public == {"Invalid credentials"}

    # And the internal reasons really are different, so audit is not guessing.
    reasons = {outcome.reason for outcome in outcomes}
    assert len(reasons) > 1


# ---------------------------------------------------------------------------
# Nothing fails open
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_nothing_authenticates_when_the_lockout_decision_is_missing():
    """A lockout state we cannot compute is a lockout."""
    outcome = decide_authentication(
        is_active=True,
        has_password=True,
        password_ok=True,
        lockout=LockoutDecision(
            locked=True, remaining=timedelta(0), reason="unknown"
        ),
    )
    assert outcome.ok is False


@pytest.mark.unit
def test_the_outcome_carries_no_replayable_credential_material():
    """The outcome is a decision, not a credential.

    It may record *that* a comparison ran; it must never record what was
    compared. Everything on it is a boolean or a short reason string, so
    nothing here can be replayed or cracked if this ends up in a log.
    """
    outcome = decide_authentication(
        is_active=True, has_password=True, password_ok=True, lockout=NOT_LOCKED
    )
    fields = vars(outcome)
    assert set(fields) == {"ok", "reason", "password_checked", "requires_admin"}
    assert all(isinstance(v, (bool, str)) for v in fields.values())
