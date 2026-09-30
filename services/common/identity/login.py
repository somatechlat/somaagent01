"""Completing a login attempt.

``decide_authentication`` answers "may this attempt succeed?". This module
answers the question that follows it: **what is the final, auditable record
of the attempt**, and what does it leave behind in the lockout ledger?

It is pure. The endpoint supplies the two facts only the endpoint can know —
whether the audit write landed, and what the clock says — and gets back a
decision plus the ledger state to persist. There is no second opinion in the
glue.

**An authentication that could not be audited did not happen.** If the audit
sink is down, a correct password does not produce a session. This is the one
place in login where "best effort" is the wrong answer: a session issued with
no audit record is an unauditable privileged action, and refusing is the only
safe direction.

**The ledger advances only when a password was actually compared.** A locked
account poked again, an unknown username and an identity with no credential
set must not move ``failure_count``. If they did, a third party could walk
past a stranger's soft lock and escalate it into a hard lock that needs a
human to clear — the lockout would become a weapon against the victim rather
than a defence for them.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from services.common.identity.authenticate import AuthenticationOutcome
from services.common.identity.lockout import (
    LockoutDecision,
    LockoutState,
    record_failure,
    record_success,
)

__all__ = [
    "AUDIT_ACTION_LOGIN_FAILED",
    "AUDIT_ACTION_LOGIN_SUCCEEDED",
    "REASON_AUDIT_UNAVAILABLE",
    "LoginResult",
    "complete_login",
]

#: The audit vocabulary is closed. Two actions, because a login either
#: produced a session or it did not. The precise *why* travels in the
#: outcome's ``reason`` and belongs in the audit entry's detail, not in the
#: action name — an open-ended action vocabulary is how audit trails become
#: unqueryable.
AUDIT_ACTION_LOGIN_SUCCEEDED = "auth.login_succeeded"
AUDIT_ACTION_LOGIN_FAILED = "auth.login_failed"

#: Recorded when the password was right but the audit sink was not. The
#: attempt is refused, and an operator can find out why.
REASON_AUDIT_UNAVAILABLE = "audit_unavailable"


@dataclass(frozen=True)
class LoginResult:
    """The final record of one authentication attempt.

    Everything on it is a boolean, a short reason string, a timestamp or a
    lockout state. Nothing here is a credential: a ``LoginResult`` that ends
    up in a log cannot be replayed or cracked.
    """

    ok: bool
    reason: str
    session_issued: bool
    audit_action: str
    next_ledger: LockoutState
    requires_admin: bool = False
    authenticated_at: Optional[datetime] = None


def complete_login(
    *,
    outcome: AuthenticationOutcome,
    lockout: LockoutDecision,
    ledger: LockoutState,
    audit_written: bool,
    now: datetime,
) -> LoginResult:
    """Seal one authentication attempt into an auditable result.

    Args:
        outcome: the decision from ``decide_authentication``.
        lockout: the lockout decision that was applied to the attempt. Carried
            so a disagreement between it and ``outcome`` fails closed rather
            than open.
        ledger: the failure ledger as it stands before this attempt.
        audit_written: whether the audit entry for this attempt was durably
            written. This is the fail-closed seam: False turns a correct
            password into a denial.
        now: the instant of the attempt. Supplied by the caller so this stays
            deterministic.

    Returns:
        The sealed result: the decision, the audit action to record, the
        ledger state to persist, and the session issuance flag.
    """

    # A decision and a lockout that disagree must never produce a session.
    # Whoever called this got the ordering wrong; deny rather than guess.
    if outcome.ok and lockout.locked:
        return LoginResult(
            ok=False,
            reason="locked" if not lockout.requires_admin else "hard_locked",
            session_issued=False,
            audit_action=AUDIT_ACTION_LOGIN_FAILED,
            next_ledger=ledger,
            requires_admin=lockout.requires_admin,
        )

    # --- Denied by the decision table ---------------------------------
    if not outcome.ok:
        return LoginResult(
            ok=False,
            reason=outcome.reason,
            session_issued=False,
            audit_action=AUDIT_ACTION_LOGIN_FAILED,
            next_ledger=_ledger_after_denial(outcome, ledger, now=now),
            requires_admin=outcome.requires_admin,
        )

    # --- Correct password, but no audit trail -------------------------
    # The rule. Refuse, and leave the ledger alone: the password was right,
    # so counting this would lock out a legitimate user because of our own
    # infrastructure fault.
    if not audit_written:
        return LoginResult(
            ok=False,
            reason=REASON_AUDIT_UNAVAILABLE,
            session_issued=False,
            audit_action=AUDIT_ACTION_LOGIN_FAILED,
            next_ledger=ledger,
            requires_admin=False,
        )

    # --- Authenticated, audited --------------------------------------
    return LoginResult(
        ok=True,
        reason="ok",
        session_issued=True,
        audit_action=AUDIT_ACTION_LOGIN_SUCCEEDED,
        next_ledger=record_success(ledger),
        requires_admin=False,
        authenticated_at=now,
    )


def _ledger_after_denial(
    outcome: AuthenticationOutcome,
    ledger: LockoutState,
    *,
    now: datetime,
) -> LockoutState:
    """Advance the failure ledger only where a secret was actually tried.

    * ``bad_password`` — a hash was run and it did not match. Count it.
    * every other denial — no secret was compared, so there is nothing to
      count. Counting anyway is what turns the lockout into a weapon a third
      party can aim at the victim.
    """
    if outcome.reason == "bad_password":
        return record_failure(ledger, now=now)
    return ledger
