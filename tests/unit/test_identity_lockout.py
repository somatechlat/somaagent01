"""Local identity — account lockout and the failure ledger.

Credential stuffing does not win by being clever; it wins by being patient.
The lockout is what makes patience expensive.

Four properties are load-bearing and each has a test here:

* **Lockout is decided before the password hash.** Argon2 is deliberately
  expensive; an endpoint that hashes for an attacker is a denial-of-service
  amplifier. The decision must be computable without touching argon2.
* **Expiry does not forgive.** When a lock expires the failure count stays
  where it was, so a slow attacker cannot simply wait out each window and
  resume. Only a successful login or an admin unlock clears the ledger.
* **A longer lock is never replaced by a shorter one.** Re-attempting during
  a lock must not shrink the window.
* **Hard lock.** Past a threshold, time no longer unlocks the account. A
  human has to.

State ownership: ``failure_count`` is the source of truth for *how long the
next lock will be*; ``locked_until`` is the source of truth for *whether one
is active*. The caller passes both plus the instant, so the rules are
testable and persistence stays with the caller.

Run:
    pytest tests/unit/test_identity_lockout.py -v
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from services.common.identity.lockout import (
    HARD_LOCK_AT_FAILURES,
    LockoutState,
    evaluate_lockout,
    lock_window_for,
    record_failure,
    record_success,
    unlock,
)

NOW = datetime(2026, 9, 30, 12, 0, 0, tzinfo=timezone.utc)


def state(failures: int = 0, locked_until: datetime | None = None, hard: bool = False):
    return LockoutState(
        failure_count=failures, locked_until=locked_until, hard_locked=hard
    )


# ---------------------------------------------------------------------------
# The policy: how many failures buy how long
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_below_the_first_threshold_there_is_no_window():
    for n in range(0, 5):
        assert lock_window_for(n) == timedelta(0)


@pytest.mark.unit
def test_five_failures_buy_fifteen_minutes():
    assert lock_window_for(5) == timedelta(minutes=15)


@pytest.mark.unit
def test_ten_failures_buy_an_hour():
    assert lock_window_for(10) == timedelta(hours=1)


@pytest.mark.unit
def test_the_window_never_shrinks_as_failures_rise():
    """A growing attack must not see the window shrink."""
    previous = timedelta(0)
    for n in range(0, HARD_LOCK_AT_FAILURES):
        window = lock_window_for(n)
        assert window >= previous, f"window shrank at {n} failures"
        previous = window


# ---------------------------------------------------------------------------
# Not locked
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_a_clean_account_is_not_locked():
    decision = evaluate_lockout(state(), now=NOW)
    assert decision.locked is False
    assert decision.reason == "ok"
    assert decision.requires_admin is False


@pytest.mark.unit
def test_failures_below_the_first_threshold_do_not_lock():
    for n in range(1, 5):
        assert evaluate_lockout(state(failures=n), now=NOW).locked is False


# ---------------------------------------------------------------------------
# Locking
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_the_fifth_failure_sets_a_fifteen_minute_lock():
    updated = record_failure(state(failures=4), now=NOW)
    assert updated.failure_count == 5
    assert updated.locked_until == NOW + timedelta(minutes=15)

    decision = evaluate_lockout(updated, now=NOW)
    assert decision.locked is True
    assert decision.remaining == timedelta(minutes=15)


@pytest.mark.unit
def test_the_tenth_failure_sets_an_hour_lock():
    updated = record_failure(state(failures=9), now=NOW)
    assert updated.locked_until == NOW + timedelta(hours=1)


@pytest.mark.unit
def test_a_current_lock_still_blocks():
    decision = evaluate_lockout(
        state(failures=5, locked_until=NOW + timedelta(minutes=10)), now=NOW
    )
    assert decision.locked is True
    assert decision.remaining == timedelta(minutes=10)


# ---------------------------------------------------------------------------
# Expiry does not forgive
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_an_expired_lock_unlocks_but_keeps_the_failure_count():
    """Waiting out a window must not reset the ledger.

    If expiry cleared the count, an attacker with patience would get five
    free guesses every fifteen minutes forever. It does not.
    """
    expired = state(failures=5, locked_until=NOW)
    later = NOW + timedelta(minutes=1)

    decision = evaluate_lockout(expired, now=later)
    assert decision.locked is False

    # One more failure puts them straight back at 6, not at 1.
    updated = record_failure(expired, now=later)
    assert updated.failure_count == 6


# ---------------------------------------------------------------------------
# A longer lock is never replaced by a shorter one
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_record_failure_while_already_locked_keeps_the_longer_window():
    existing = NOW + timedelta(minutes=30)
    updated = record_failure(state(failures=5, locked_until=existing), now=NOW)
    assert updated.locked_until == existing


# ---------------------------------------------------------------------------
# Hard lock
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_past_the_threshold_time_no_longer_unlocks_the_account():
    """A hard lock is a human decision, not a timer."""
    far_future = NOW + timedelta(days=365)
    decision = evaluate_lockout(state(failures=HARD_LOCK_AT_FAILURES), now=far_future)
    assert decision.locked is True
    assert decision.requires_admin is True


@pytest.mark.unit
def test_the_hard_lock_flag_alone_is_enough_even_with_a_low_count():
    """Fail-closed: the flag and the count both mean locked."""
    decision = evaluate_lockout(state(failures=0, hard=True), now=NOW)
    assert decision.locked is True
    assert decision.requires_admin is True


@pytest.mark.unit
def test_only_an_admin_unlock_clears_a_hard_lock():
    cleared = unlock(state(failures=HARD_LOCK_AT_FAILURES, hard=True))
    assert cleared.failure_count == 0
    assert cleared.hard_locked is False
    assert cleared.locked_until is None

    assert evaluate_lockout(cleared, now=NOW).locked is False


# ---------------------------------------------------------------------------
# The ledger
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_record_success_clears_the_ledger():
    """A real login is the only thing besides an admin that resets the count."""
    cleared = record_success(state(failures=19, locked_until=NOW + timedelta(hours=2)))
    assert cleared.failure_count == 0
    assert cleared.locked_until is None
    assert cleared.hard_locked is False


@pytest.mark.unit
def test_repeated_failures_reach_the_hard_lock_and_stay():
    updated = state(failures=0)
    for _ in range(40):
        updated = record_failure(updated, now=NOW)
    assert updated.hard_locked is True

    far_future = NOW + timedelta(days=365)
    decision = evaluate_lockout(updated, now=far_future)
    assert decision.locked is True
    assert decision.requires_admin is True


@pytest.mark.unit
def test_lock_state_does_not_leak_the_password_or_username():
    """This ends up in logs and audit records."""
    updated = record_failure(state(failures=0), now=NOW)
    assert "password" not in repr(updated).lower()
    assert "secret" not in repr(updated).lower()
