"""Local identity — the credential record.

``LocalIdentity`` is who a person is when the agent holds the credential
itself (Standalone, SOMA-01-DEPLOY-001 §4.1). It is an authentication
record, not an authority record: it says which **roles** a person holds and
never what those roles mean. Every permission is still resolved through
``admin.core.authz``, identically in every deployment mode.

These tests construct unsaved instances. Nothing here needs a database and
nothing here is faked — the model's methods are real and the pure logic they
delegate to is already covered in ``test_identity_password.py`` and
``test_identity_lockout.py``.

The assertions that matter are the negative ones: a disabled account must
not verify, a wrong password must not verify, and no plaintext credential
may ever sit on the object.

Run:
    pytest tests/unit/test_identity_model.py -v
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from admin.aaas.models.identity import LocalIdentity
from services.common.identity.lockout import LockoutState
from services.common.identity.password import (
    PasswordPolicyError,
)

NOW = datetime(2026, 9, 30, 12, 0, 0, tzinfo=timezone.utc)
PEPPER = "test-pepper-value-not-a-real-secret"
_FAST = {"time_cost": 1, "memory_cost": 8, "parallelism": 1}


def identity(**kwargs) -> LocalIdentity:
    defaults = dict(
        username="alice",
        email="alice@example.com",
        display_name="Alice",
    )
    defaults.update(kwargs)
    return LocalIdentity(**defaults)


# ---------------------------------------------------------------------------
# Setting a password
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_set_password_stores_a_verifier_and_not_the_password():
    obj = identity()
    obj.set_password("correct horse battery staple", PEPPER, **_FAST)

    assert obj.password_hash.startswith("$argon2id$")
    assert "correct horse battery staple" not in obj.password_hash
    assert PEPPER not in obj.password_hash
    # And there is no attribute that ever held it.
    assert not hasattr(obj, "password")
    assert "password" not in vars(obj)


@pytest.mark.unit
def test_set_password_refuses_a_password_that_fails_policy():
    obj = identity()
    with pytest.raises(PasswordPolicyError):
        obj.set_password("short", PEPPER, **_FAST)
    assert not obj.password_hash


@pytest.mark.unit
def test_set_password_refuses_the_own_username():
    obj = identity(username="alice", email="alice@example.com")
    with pytest.raises(PasswordPolicyError):
        obj.set_password("alice", PEPPER, **_FAST)


@pytest.mark.unit
def test_set_password_records_when_it_changed():
    obj = identity()
    obj.set_password("correct horse battery staple", PEPPER, now=NOW, **_FAST)
    assert obj.password_changed_at == NOW


# ---------------------------------------------------------------------------
# Verifying a password
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_verify_password_accepts_the_right_password():
    obj = identity()
    obj.set_password("correct horse battery staple", PEPPER, **_FAST)
    assert obj.verify_password("correct horse battery staple", PEPPER) is True


@pytest.mark.unit
def test_verify_password_rejects_the_wrong_password():
    obj = identity()
    obj.set_password("correct horse battery staple", PEPPER, **_FAST)
    assert obj.verify_password("nope nope nope nope", PEPPER) is False


@pytest.mark.unit
def test_verify_password_rejects_a_password_set_under_another_pepper():
    obj = identity()
    obj.set_password("correct horse battery staple", PEPPER, **_FAST)
    assert obj.verify_password("correct horse battery staple", "other-pepper") is False


@pytest.mark.unit
def test_a_disabled_identity_cannot_verify_any_password():
    """Offboarding and lockout-by-admin must take effect immediately.

    A disabled account that can still authenticate is an account that was
    never really disabled.
    """
    obj = identity(is_active=False)
    obj.set_password("correct horse battery staple", PEPPER, **_FAST)
    assert obj.verify_password("correct horse battery staple", PEPPER) is False


@pytest.mark.unit
def test_an_identity_with_no_password_set_verifies_nothing():
    """Fail-closed: an unset credential is not a free pass."""
    obj = identity()
    assert obj.password_hash == ""
    assert obj.verify_password("anything at all here", PEPPER) is False


# ---------------------------------------------------------------------------
# The lockout ledger, round-tripped through the pure rules
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_lockout_state_round_trips_through_the_model():
    obj = identity(
        failure_count=7,
        locked_until=NOW + timedelta(minutes=10),
        hard_locked=False,
    )
    state = obj.to_lockout_state()
    assert state == LockoutState(
        failure_count=7, locked_until=NOW + timedelta(minutes=10), hard_locked=False
    )

    obj.apply_lockout_state(LockoutState(failure_count=0, locked_until=None, hard_locked=True))
    assert obj.failure_count == 0
    assert obj.locked_until is None
    assert obj.hard_locked is True


@pytest.mark.unit
def test_the_model_never_stores_a_password_in_the_lockout_ledger():
    obj = identity(failure_count=3)
    assert "password" not in repr(obj.to_lockout_state()).lower()


# ---------------------------------------------------------------------------
# Roles are declarative; authority is always the catalog's
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_roles_are_stored_but_never_invented():
    """The identity says which roles a person holds. It does not decide what
    those roles mean — that is ``admin.core.authz`` and it is the same in
    every deployment mode."""
    obj = identity(roles=["developer", "trainer"])
    assert obj.roles == ["developer", "trainer"]


@pytest.mark.unit
def test_an_unknown_role_name_is_not_authority():
    from admin.core.authz import permissions_for_principal

    obj = identity(roles=["developer", "not_a_real_role"])
    perms = permissions_for_principal(roles=obj.roles)
    # Whatever "not_a_real_role" means, it grants nothing.
    assert perms == permissions_for_principal(roles=["developer"])
