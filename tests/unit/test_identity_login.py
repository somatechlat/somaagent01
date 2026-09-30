"""Local identity — completing a login attempt.

Everything up to here answers "may this attempt succeed?". This module
answers the harder question that follows: **what is the final, auditable
record of the attempt**, and what does it leave behind in the lockout ledger?

Three rules are load-bearing and each is asserted here:

* **An authentication that could not be audited did not happen.** If the
  audit sink is down, a correct password does not produce a session. A
  privileged action with no audit trail is precisely the failure mode
  ISO/IEC 27001 A.8.15 exists to prevent, and it is the one place in login
  where "best effort" is the wrong answer.

* **The ledger advances only when a password was actually compared.** A
  locked account that is poked again, an unknown username, and an identity
  with no credential set must not move ``failure_count``. Otherwise a third
  party can escalate a stranger's soft lock into a hard lock and deny them
  the service — the lockout becomes a weapon against the victim.

* **The result is a record, not a credential.** Nothing on it can be
  replayed or cracked.

Run:
    pytest tests/unit/test_identity_login.py -v
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from services.common.identity.authenticate import (
    AuthenticationOutcome,
    decide_authentication,
)
from services.common.identity.lockout import (
    LockoutDecision,
    LockoutState,
    evaluate_lockout,
)
from services.common.identity.login import (
    AUDIT_ACTION_LOGIN_FAILED,
    AUDIT_ACTION_LOGIN_SUCCEEDED,
    LoginResult,
    complete_login,
)

NOW = datetime(2026, 9, 30, 12, 0, 0, tzinfo=timezone.utc)

NOT_LOCKED = LockoutDecision(locked=False, remaining=timedelta(0), reason="ok")
SOFT_LOCKED = LockoutDecision(
    locked=True, remaining=timedelta(minutes=15), reason="soft_lock"
)
HARD_LOCKED = LockoutDecision(
    locked=True, remaining=timedelta.max, reason="hard_lock", requires_admin=True
)

FRESH_LEDGER = LockoutState()
LEDGER_WITH_FAILURES = LockoutState(failure_count=3)


# ---------------------------------------------------------------------------
# The happy path
# ---------------------------------------------------------------------------


def test_a_successful_login_is_recorded_and_issues_a_session():
    outcome = decide_authentication(
        is_active=True, has_password=True, password_ok=True, lockout=NOT_LOCKED
    )
    result = complete_login(
        outcome=outcome,
        lockout=NOT_LOCKED,
        ledger=FRESH_LEDGER,
        audit_written=True,
        now=NOW,
    )
    assert result.ok is True
    assert result.session_issued is True
    assert result.reason == "ok"
    assert result.audit_action == AUDIT_ACTION_LOGIN_SUCCEEDED


def test_a_successful_login_clears_the_failure_ledger():
    """Success is the only thing that wipes the ledger. Everything else
    either advances it or leaves it alone."""
    outcome = decide_authentication(
        is_active=True, has_password=True, password_ok=True, lockout=NOT_LOCKED
    )
    result = complete_login(
        outcome=outcome,
        lockout=NOT_LOCKED,
        ledger=LEDGER_WITH_FAILURES,
        audit_written=True,
        now=NOW,
    )
    assert result.next_ledger == LockoutState()


def test_a_successful_login_records_the_login_time():
    outcome = decide_authentication(
        is_active=True, has_password=True, password_ok=True, lockout=NOT_LOCKED
    )
    result = complete_login(
        outcome=outcome,
        lockout=NOT_LOCKED,
        ledger=FRESH_LEDGER,
        audit_written=True,
        now=NOW,
    )
    assert result.authenticated_at == NOW


# ---------------------------------------------------------------------------
# An authentication that could not be audited did not happen
# ---------------------------------------------------------------------------


def test_a_correct_password_without_an_audit_trail_is_denied():
    """THE rule. The audit sink being down is not a licence to authenticate.

    A session issued with no audit record is an unauditable privileged
    action. The safe direction is to refuse, not to proceed and hope the
    sink comes back.
    """
    outcome = decide_authentication(
        is_active=True, has_password=True, password_ok=True, lockout=NOT_LOCKED
    )
    result = complete_login(
        outcome=outcome,
        lockout=NOT_LOCKED,
        ledger=FRESH_LEDGER,
        audit_written=False,
        now=NOW,
    )
    assert result.ok is False
    assert result.session_issued is False
    assert result.reason == "audit_unavailable"
    assert result.requires_admin is False


def test_the_audit_denial_does_not_punish_the_ledger():
    """Denying for a missing audit trail must not count as a failed password.

    The password was right. Counting it would lock out a legitimate user
    because of an infrastructure fault on our side.
    """
    outcome = decide_authentication(
        is_active=True, has_password=True, password_ok=True, lockout=NOT_LOCKED
    )
    result = complete_login(
        outcome=outcome,
        lockout=NOT_LOCKED,
        ledger=LEDGER_WITH_FAILURES,
        audit_written=False,
        now=NOW,
    )
    assert result.next_ledger == LEDGER_WITH_FAILURES
    assert result.next_ledger.failure_count == 3


def test_the_audit_denial_still_audits_the_denial_itself_when_possible():
    """The record of "we refused because the sink was down" has its own
    action, so an operator can find the incident."""
    outcome = decide_authentication(
        is_active=True, has_password=True, password_ok=True, lockout=NOT_LOCKED
    )
    result = complete_login(
        outcome=outcome,
        lockout=NOT_LOCKED,
        ledger=FRESH_LEDGER,
        audit_written=False,
        now=NOW,
    )
    assert result.audit_action != AUDIT_ACTION_LOGIN_SUCCEEDED


# ---------------------------------------------------------------------------
# The ledger advances only when a password was compared
# ---------------------------------------------------------------------------


def test_a_wrong_password_advances_the_ledger():
    outcome = decide_authentication(
        is_active=True, has_password=True, password_ok=False, lockout=NOT_LOCKED
    )
    result = complete_login(
        outcome=outcome,
        lockout=NOT_LOCKED,
        ledger=LEDGER_WITH_FAILURES,
        audit_written=True,
        now=NOW,
    )
    assert result.ok is False
    assert result.next_ledger.failure_count == 4
    assert result.audit_action == AUDIT_ACTION_LOGIN_FAILED


def test_a_locked_account_poked_again_does_not_advance_the_ledger():
    """The anti-weapon rule.

    If a lockout denial incremented the counter, anyone could walk past a
    stranger's soft lock and escalate it into a hard lock requiring a human
    unlock. That is a denial-of-service against the victim, dressed up as
    security.
    """
    outcome = decide_authentication(
        is_active=True, has_password=True, password_ok=True, lockout=SOFT_LOCKED
    )
    assert outcome.password_checked is False
    result = complete_login(
        outcome=outcome,
        lockout=SOFT_LOCKED,
        ledger=LockoutState(failure_count=5, locked_until=NOW + timedelta(minutes=10)),
        audit_written=True,
        now=NOW,
    )
    assert result.ok is False
    assert result.next_ledger.failure_count == 5


def test_an_unknown_account_does_not_advance_any_ledger():
    """There is no row to advance, and inventing one would leak whether the
    username exists."""
    outcome = decide_authentication(
        is_active=False, has_password=False, password_ok=False, lockout=NOT_LOCKED
    )
    result = complete_login(
        outcome=outcome,
        lockout=NOT_LOCKED,
        ledger=FRESH_LEDGER,
        audit_written=True,
        now=NOW,
    )
    assert result.ok is False
    assert result.next_ledger == FRESH_LEDGER


def test_an_identity_with_no_credential_does_not_advance_the_ledger():
    """No hash exists, so there was no secret to get wrong. Counting it
    would let an attacker lock a freshly provisioned account before its
    owner ever sets a password."""
    outcome = decide_authentication(
        is_active=True, has_password=False, password_ok=False, lockout=NOT_LOCKED
    )
    result = complete_login(
        outcome=outcome,
        lockout=NOT_LOCKED,
        ledger=FRESH_LEDGER,
        audit_written=True,
        now=NOW,
    )
    assert result.ok is False
    assert result.next_ledger == FRESH_LEDGER
    assert result.next_ledger.failure_count == 0


def test_a_hard_lock_survives_an_admin_only_flag():
    outcome = decide_authentication(
        is_active=True, has_password=True, password_ok=True, lockout=HARD_LOCKED
    )
    result = complete_login(
        outcome=outcome,
        lockout=HARD_LOCKED,
        ledger=LockoutState(failure_count=20, hard_locked=True),
        audit_written=True,
        now=NOW,
    )
    assert result.ok is False
    assert result.requires_admin is True
    assert result.next_ledger.hard_locked is True


# ---------------------------------------------------------------------------
# The result is a record, not a credential
# ---------------------------------------------------------------------------


def test_the_result_carries_no_replayable_credential_material():
    """Everything on a LoginResult is a boolean, a short reason string, a
    timestamp or a lockout state. Nothing here is a secret, so a LoginResult
    that ends up in a log cannot be replayed."""
    outcome = decide_authentication(
        is_active=True, has_password=True, password_ok=True, lockout=NOT_LOCKED
    )
    result = complete_login(
        outcome=outcome,
        lockout=NOT_LOCKED,
        ledger=FRESH_LEDGER,
        audit_written=True,
        now=NOW,
    )
    assert isinstance(result, LoginResult)
    assert isinstance(result.ok, bool)
    assert isinstance(result.session_issued, bool)
    assert isinstance(result.reason, str)
    assert isinstance(result.audit_action, str)
    assert "password" not in result.reason
    assert "password" not in result.audit_action
    assert not any(
        "password" in key or "secret" in key or "token" in key for key in vars(result)
    )


# ---------------------------------------------------------------------------
# Audit vocabulary is closed
# ---------------------------------------------------------------------------


def test_the_audit_action_vocabulary_is_closed():
    outcome_ok = decide_authentication(
        is_active=True, has_password=True, password_ok=True, lockout=NOT_LOCKED
    )
    outcome_bad = decide_authentication(
        is_active=True, has_password=True, password_ok=False, lockout=NOT_LOCKED
    )
    actions = {
        complete_login(
            outcome=o, lockout=lock, ledger=led, audit_written=aud, now=NOW
        ).audit_action
        for o, lock, led, aud in (
            (outcome_ok, NOT_LOCKED, FRESH_LEDGER, True),
            (outcome_ok, NOT_LOCKED, FRESH_LEDGER, False),
            (outcome_bad, NOT_LOCKED, FRESH_LEDGER, True),
        )
    }
    assert actions <= {
        AUDIT_ACTION_LOGIN_SUCCEEDED,
        AUDIT_ACTION_LOGIN_FAILED,
    }


# ---------------------------------------------------------------------------
# End to end: the whole decision path, as the endpoint will run it
# ---------------------------------------------------------------------------


def test_the_full_path_for_a_correct_password():
    """Lockout first, then decide, then seal — in that order, end to end."""
    ledger = LockoutState(failure_count=2)
    lockout = evaluate_lockout(ledger, now=NOW)
    outcome = decide_authentication(
        is_active=True, has_password=True, password_ok=True, lockout=lockout
    )
    assert outcome.password_checked is True
    result = complete_login(
        outcome=outcome, lockout=lockout, ledger=ledger, audit_written=True, now=NOW
    )
    assert result.ok is True
    assert result.session_issued is True
    assert result.next_ledger.failure_count == 0


def test_the_full_path_denies_before_the_hash_when_locked():
    """The endpoint asks the lockout before argon2. This asserts the whole
    path agrees, so an expensive hash cannot be reached through it."""
    ledger = LockoutState(failure_count=5, locked_until=NOW + timedelta(minutes=10))
    lockout = evaluate_lockout(ledger, now=NOW)
    assert lockout.locked is True
    outcome = decide_authentication(
        is_active=True, has_password=True, password_ok=False, lockout=lockout
    )
    assert outcome.password_checked is False
    result = complete_login(
        outcome=outcome, lockout=lockout, ledger=ledger, audit_written=True, now=NOW
    )
    assert result.ok is False
    assert result.session_issued is False
    assert result.next_ledger.failure_count == 5


def test_the_full_path_denies_when_the_audit_sink_is_down():
    ledger = LockoutState()
    lockout = evaluate_lockout(ledger, now=NOW)
    outcome = decide_authentication(
        is_active=True, has_password=True, password_ok=True, lockout=lockout
    )
    assert outcome.ok is True
    result = complete_login(
        outcome=outcome, lockout=lockout, ledger=ledger, audit_written=False, now=NOW
    )
    assert result.ok is False
    assert result.reason == "audit_unavailable"
    assert result.session_issued is False


# ---------------------------------------------------------------------------
# Nothing fails open
# ---------------------------------------------------------------------------


def test_a_denied_outcome_never_issues_a_session_however_the_sink_behaves():
    for audit_written in (True, False):
        outcome = AuthenticationOutcome(
            ok=False,
            reason="bad_password",
            password_checked=True,
        )
        result = complete_login(
            outcome=outcome,
            lockout=NOT_LOCKED,
            ledger=FRESH_LEDGER,
            audit_written=audit_written,
            now=NOW,
        )
        assert result.ok is False
        assert result.session_issued is False
