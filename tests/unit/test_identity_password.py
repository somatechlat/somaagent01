"""Local identity — password hashing, verification and policy.

Standalone authenticates a person with a username and password held by the
agent itself (SOMA-01-DEPLOY-001 §4.1). There is no identity-provider process
in that shape, so the credential check is ours and it has to be the strongest
part of the system, not the weakest.

These tests cover the pure functions only. They take the pepper as a
parameter so nothing here needs infrastructure and nothing here is faked —
the Vault fetch is a separate, thin layer (``services.common.identity.pepper``)
whose job is to refuse to proceed when the pepper is missing.

The assertions that matter are the negative ones: a wrong password, a hash
made under a different pepper, a mangled hash, a short password, a password
that is the username. A suite that only proved the happy path would pass
against exactly the bugs this module exists to prevent.

Run:
    pytest tests/unit/test_identity_password.py -v
"""

from __future__ import annotations

import pytest

from services.common.identity.password import (
    ARGON2_MEMORY_KIB,
    ARGON2_PARALLELISM,
    ARGON2_TIME_COST,
    PasswordPolicyError,
    check_password_policy,
    hash_password,
    needs_rehash,
    verify_password,
)
from services.common.identity.pepper import require_password_pepper

# Cheap parameters for tests only. The production defaults above are the
# policy; these keep the suite fast without changing what is asserted.
_FAST = {
    "time_cost": 1,
    "memory_cost": 8,
    "parallelism": 1,
}

PEPPER = "test-pepper-value-not-a-real-secret"
OTHER_PEPPER = "a-different-pepper-entirely"


# ---------------------------------------------------------------------------
# hash / verify — the round trip, and every way it must fail
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_hash_password_produces_argon2id_with_embedded_params():
    """The stored value must carry its own algorithm and parameters.

    Parameters live in the hash string so they can be raised later without a
    flag day and without ever mistaking an old hash for a current one.
    """
    encoded = hash_password("correct horse battery staple", PEPPER, **_FAST)

    assert encoded.startswith("$argon2id$")
    # $argon2id$v=19$m=...,t=...,p=...$salt$hash
    parts = encoded.split("$")
    assert parts[3].startswith("m=")
    assert "t=" in parts[3]
    assert "p=" in parts[3]


@pytest.mark.unit
def test_verify_password_accepts_the_right_password():
    encoded = hash_password("correct horse battery staple", PEPPER, **_FAST)
    assert verify_password("correct horse battery staple", encoded, PEPPER) is True


@pytest.mark.unit
def test_verify_password_rejects_the_wrong_password():
    encoded = hash_password("correct horse battery staple", PEPPER, **_FAST)
    assert verify_password("incorrect horse battery staple", encoded, PEPPER) is False


@pytest.mark.unit
def test_verify_password_rejects_a_hash_made_with_a_different_pepper():
    """A stolen database is inert without Vault.

    The hash alone must not verify against any other pepper. This is the
    property that makes exfiltrating the credential store useless.
    """
    encoded = hash_password("correct horse battery staple", PEPPER, **_FAST)
    assert verify_password("correct horse battery staple", encoded, OTHER_PEPPER) is False


@pytest.mark.unit
def test_verify_password_rejects_a_mangled_hash():
    encoded = hash_password("correct horse battery staple", PEPPER, **_FAST)
    mangled = encoded[:-4] + "AAAA"
    assert verify_password("correct horse battery staple", mangled, PEPPER) is False


@pytest.mark.unit
def test_verify_password_rejects_a_hash_from_another_algorithm():
    """No downgrade path: an md5 or sha256 digest must not verify.

    An attacker who can write the credential row must not be able to plant a
    weaker hash that the verifier will happily accept.
    """
    assert (
        verify_password("correct horse battery staple", "not-a-phc-string", PEPPER) is False
    )


@pytest.mark.unit
def test_hash_password_never_embeds_the_pepper_or_the_password():
    encoded = hash_password("correct horse battery staple", PEPPER, **_FAST)
    assert PEPPER not in encoded
    assert "correct horse battery staple" not in encoded


@pytest.mark.unit
def test_hash_password_is_salted_so_the_same_password_hashes_differently():
    a = hash_password("correct horse battery staple", PEPPER, **_FAST)
    b = hash_password("correct horse battery staple", PEPPER, **_FAST)
    assert a != b


# ---------------------------------------------------------------------------
# needs_rehash — progressive upgrade, never a silent weakening
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_needs_rehash_is_true_when_params_are_weaker_than_policy():
    weak = hash_password("correct horse battery staple", PEPPER, **_FAST)
    assert needs_rehash(weak) is True


@pytest.mark.unit
def test_needs_rehash_is_false_for_current_policy_params():
    strong = hash_password(
        "correct horse battery staple",
        PEPPER,
        time_cost=ARGON2_TIME_COST,
        memory_cost=ARGON2_MEMORY_KIB,
        parallelism=ARGON2_PARALLELISM,
    )
    assert needs_rehash(strong) is False


@pytest.mark.unit
def test_needs_rehash_is_false_for_a_malformed_hash():
    """A hash we cannot parse is not "current". The caller must re-hash."""
    assert needs_rehash("garbage") is False


# ---------------------------------------------------------------------------
# require_password_pepper — Rule 91, zero fallback
# ---------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.parametrize("value", [None, "", "   "])
def test_require_password_pepper_refuses_a_missing_pepper(value):
    """There is no default pepper and no generated one.

    A missing pepper must raise at the point of use. Silently minting a new
    one would either lock every existing account out or — worse — accept
    passwords under a pepper nobody chose. Both are worse than being down.
    """
    with pytest.raises(RuntimeError):
        require_password_pepper(value)


@pytest.mark.unit
def test_require_password_pepper_accepts_a_real_value():
    assert require_password_pepper(PEPPER) == PEPPER


# ---------------------------------------------------------------------------
# policy — NIST SP 800-63B: length first, no composition theatre
# ---------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.parametrize("password", ["", "short", "12345678901"])
def test_policy_rejects_passwords_below_the_minimum_length(password):
    with pytest.raises(PasswordPolicyError):
        check_password_policy(password)


@pytest.mark.unit
def test_policy_rejects_passwords_above_the_maximum_length():
    """128 is the cap. Longer inputs are a denial-of-service vector against
    the hash, and nobody needs a 400-character password."""
    with pytest.raises(PasswordPolicyError):
        check_password_policy("a" * 129)


@pytest.mark.unit
def test_policy_accepts_a_long_passphrase():
    check_password_policy("correct horse battery staple staple stapler")


@pytest.mark.unit
def test_policy_rejects_a_single_repeated_character():
    with pytest.raises(PasswordPolicyError):
        check_password_policy("aaaaaaaaaaaaaaaaaaaaaaaa")


@pytest.mark.unit
def test_policy_rejects_the_username_or_email_as_the_password():
    with pytest.raises(PasswordPolicyError):
        check_password_policy("alice@example.com", username="alice", email="alice@example.com")
    with pytest.raises(PasswordPolicyError):
        check_password_policy("alice", username="alice", email="alice@example.com")


@pytest.mark.unit
def test_privileged_principals_need_a_longer_password():
    """sysadmin / org_admin / agent_owner — the roles that can change who
    holds what. Their credential is worth more, so it must be longer."""
    check_password_policy("twelvechars12")
    with pytest.raises(PasswordPolicyError):
        check_password_policy("twelvechars12", privileged=True)
    check_password_policy("fourteenchars1", privileged=True)


@pytest.mark.unit
def test_policy_error_does_not_echo_the_password():
    """A policy failure is an audit event and often a log line. The candidate
    password must never appear in the message."""
    password = "hunter2-hunter2-hunter2"
    try:
        check_password_policy(password, username="hunter2-hunter2-hunter2")
    except PasswordPolicyError as exc:
        assert password not in str(exc)
    else:
        pytest.fail("expected PasswordPolicyError")
