"""Account lockout and the failure ledger.

Credential stuffing does not win by being clever; it wins by being patient.
This module is what makes patience expensive.

The rules, and why:

* **Expiry does not forgive.** When a lock window elapses the failure count
  stays where it was. If expiry cleared the ledger, an attacker with patience
  would get five free guesses every fifteen minutes forever. Only a real
  login or an admin unlock clears it.
* **A longer lock is never replaced by a shorter one.** Re-attempting during
  a lock must not shrink the window, or a lock would be escapable by
  hammering it.
* **Hard lock.** Past ``HARD_LOCK_AT_FAILURES``, time no longer unlocks the
  account. That is a human decision, because past that point this is either
  an attack or a genuine lockout and both deserve a person.
* **Decided without hashing.** Everything here is arithmetic on integers and
  datetimes. The caller asks this module *before* it reaches argon2, so an
  attacker cannot use the login endpoint as an argon2 denial-of-service
  amplifier.

State ownership: ``failure_count`` says how long the *next* lock will be;
``locked_until`` says whether one is active *now*. Persistence belongs to the
caller. Nothing here reads a clock it was not handed.

Nothing here records a password, a token or a username. This state is logged
and audited.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

__all__ = [
    "HARD_LOCK_AT_FAILURES",
    "LockoutDecision",
    "LockoutState",
    "evaluate_lockout",
    "lock_window_for",
    "record_failure",
    "record_success",
    "unlock",
]

#: Failure count at which only a human unlocks the account.
HARD_LOCK_AT_FAILURES = 20

#: Longest soft window. A soft lock never outlasts this.
MAX_SOFT_WINDOW = timedelta(hours=4)

#: ``failures -> window``. Anything at or above a key gets that window; the
#: window never shrinks as the count climbs. Below the first key there is no
#: lock at all — five is the point at which guessing has clearly started.
_LOCK_WINDOWS: tuple[tuple[int, timedelta], ...] = (
    (5, timedelta(minutes=15)),
    (10, timedelta(hours=1)),
    (15, timedelta(hours=4)),
)


@dataclass(frozen=True)
class LockoutState:
    """What the ledger knows about one principal's failed attempts.

    Carries no credential material and no username. Safe to log.
    """

    failure_count: int = 0
    locked_until: datetime | None = None
    hard_locked: bool = False


@dataclass(frozen=True)
class LockoutDecision:
    """The answer to "may this principal attempt authentication right now?"."""

    locked: bool
    remaining: timedelta
    reason: str  # "ok" | "soft_lock" | "hard_lock"
    requires_admin: bool = False


def lock_window_for(failure_count: int) -> timedelta:
    """How long a lock lasts at this failure count.

    Zero below the first threshold. Never shrinks as the count rises. Capped
    at ``MAX_SOFT_WINDOW`` — beyond that, the hard lock is the answer, not an
    ever-growing timer.
    """
    if failure_count < 0:
        return timedelta(0)

    window = timedelta(0)
    for threshold, candidate in _LOCK_WINDOWS:
        if failure_count >= threshold:
            window = candidate
    return window


def evaluate_lockout(current: LockoutState, *, now: datetime) -> LockoutDecision:
    """Decide whether authentication may be attempted.

    Args:
        current: the ledger as it stands
        now: the instant to evaluate against. Never read from a clock here —
            the caller owns time so this stays deterministic.

    Returns:
        A decision. ``locked`` True means the caller must not run a password
        hash at all.
    """
    if current.hard_locked or current.failure_count >= HARD_LOCK_AT_FAILURES:
        return LockoutDecision(
            locked=True,
            remaining=timedelta.max,
            reason="hard_lock",
            requires_admin=True,
        )

    if current.locked_until is not None and current.locked_until > now:
        remaining = current.locked_until - now
        return LockoutDecision(
            locked=True,
            remaining=remaining,
            reason="soft_lock",
            requires_admin=False,
        )

    return LockoutDecision(locked=False, remaining=timedelta(0), reason="ok")


def record_failure(current: LockoutState, *, now: datetime) -> LockoutState:
    """Add one failure to the ledger and set or extend the lock window.

    The window is the longer of what the new count implies and whatever is
    already running. A shorter implied window never replaces a longer one.
    """
    failures = current.failure_count + 1
    implied = now + lock_window_for(failures)

    locked_until = implied
    if current.locked_until is not None and current.locked_until > locked_until:
        locked_until = current.locked_until

    hard = current.hard_locked or failures >= HARD_LOCK_AT_FAILURES
    if hard:
        # A hard lock is not a timer. Keep a far horizon so callers that only
        # look at ``locked_until`` still see a lock, but ``hard_locked`` is
        # what ``evaluate_lockout`` answers from.
        locked_until = current.locked_until or now + MAX_SOFT_WINDOW

    return LockoutState(
        failure_count=failures,
        locked_until=locked_until,
        hard_locked=hard,
    )


def record_success(current: LockoutState) -> LockoutState:
    """Clear the ledger. A real login is the only event besides an admin."""
    return LockoutState(failure_count=0, locked_until=None, hard_locked=False)


def unlock(current: LockoutState) -> LockoutState:
    """Administrative unlock. Audited by the caller; nothing here is silent."""
    return LockoutState(failure_count=0, locked_until=None, hard_locked=False)
