"""Password hashing, verification and policy.

Design decisions, each of which is a security property:

**argon2id.** Memory-hard, the OWASP first choice, resistant to both GPU and
ASIC attack in a way bcrypt and PBKDF2 are not.

**The pepper is an HMAC key, not a concatenation.** ``HMAC-SHA256(pepper,
password)`` is what argon2 sees. The password never enters the hash in the
clear, and a stolen hash is worthless without the pepper, which lives in
Vault (VIBE Rule 164).

**Parameters travel with the hash.** The PHC string records m/t/p, so they
can be raised later and ``needs_rehash`` can tell an old hash from a current
one. There is no flag day and no silent weakening.

**Policy is length-first (NIST SP 800-63B).** No composition rules: they
produce ``P@ssw0rd1``, not security. No forced periodic rotation: it
produces ``Password1``, ``Password2``. Screen for the obvious — too short,
too long, a repeated character, the user's own name.

Every failure raises or returns False. There is no path that treats a
missing pepper, an unparseable hash or a policy violation as success.
"""

from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
from argon2.low_level import Type

__all__ = [
    "ARGON2_HASH_LEN",
    "ARGON2_MEMORY_KIB",
    "ARGON2_PARALLELISM",
    "ARGON2_SALT_LEN",
    "ARGON2_TIME_COST",
    "MAX_PASSWORD_LENGTH",
    "MIN_PASSWORD_LENGTH",
    "PRIVILEGED_MIN_PASSWORD_LENGTH",
    "PasswordPolicyError",
    "check_password_policy",
    "hash_password",
    "needs_rehash",
    "verify_password",
]

# --- Parameters (OWASP 2024 minimum is m=19456 KiB, t=2, p=1; this is
# deliberately above it. Raise, never lower — needs_rehash upgrades old
# hashes on the next successful login.)
ARGON2_TIME_COST = 3
ARGON2_MEMORY_KIB = 65536  # 64 MiB
ARGON2_PARALLELISM = 4
ARGON2_HASH_LEN = 32
ARGON2_SALT_LEN = 16

# --- Policy (NIST SP 800-63B: 8 is a floor for memorised secrets and is not
# enough for an enterprise agent that administers itself. 12 for members,
# 14 for anyone who can change who holds what.)
MIN_PASSWORD_LENGTH = 12
PRIVILEGED_MIN_PASSWORD_LENGTH = 14
MAX_PASSWORD_LENGTH = 128


class PasswordPolicyError(ValueError):
    """A candidate password failed policy.

    The message never contains the candidate. This exception is routinely
    logged and written to the audit trail.
    """


@dataclass(frozen=True)
class Argon2Params:
    """The cost parameters recorded in a hash string."""

    time_cost: int
    memory_cost: int
    parallelism: int


#: What the product requires today. Anything weaker triggers a rehash.
POLICY_PARAMS = Argon2Params(
    time_cost=ARGON2_TIME_COST,
    memory_cost=ARGON2_MEMORY_KIB,
    parallelism=ARGON2_PARALLELISM,
)


def _hasher(params: Argon2Params) -> PasswordHasher:
    return PasswordHasher(
        time_cost=params.time_cost,
        memory_cost=params.memory_cost,
        parallelism=params.parallelism,
        hash_len=ARGON2_HASH_LEN,
        salt_len=ARGON2_SALT_LEN,
        type=Type.ID,
    )


def _mix(password: str, pepper: str) -> bytes:
    """Fold the pepper into the password with an HMAC.

    The pepper is the HMAC key. A hash computed under one pepper cannot be
    verified under another, which is what makes an exfiltrated credential
    store inert without Vault.
    """
    return hmac.new(
        pepper.encode("utf-8"),
        password.encode("utf-8"),
        hashlib.sha256,
    ).digest()


def hash_password(
    password: str,
    pepper: str,
    *,
    time_cost: int = ARGON2_TIME_COST,
    memory_cost: int = ARGON2_MEMORY_KIB,
    parallelism: int = ARGON2_PARALLELISM,
) -> str:
    """Hash a password under ``pepper``.

    Returns the PHC string, which carries the algorithm and its parameters.
    Neither the password nor the pepper appears in the result.

    Raises:
        PasswordPolicyError: if the password fails policy. Hashing a password
            the product would refuse to accept is how weak credentials get
            written to the store.
    """
    check_password_policy(password)
    params = Argon2Params(
        time_cost=time_cost, memory_cost=memory_cost, parallelism=parallelism
    )
    return _hasher(params).hash(_mix(password, pepper))


def verify_password(password: str, encoded: str, pepper: str) -> bool:
    """Verify a password against a stored hash.

    FAIL-CLOSED: every failure returns False. A malformed hash, a hash from
    another algorithm, a wrong pepper and a wrong password are the same
    answer to the caller — the comparison does not leak which one it was.

    This function never raises on a bad credential; it raises only on
    programming error (a pepper that is not a string).
    """
    if not isinstance(password, str) or not isinstance(encoded, str):
        return False
    if not password or not encoded:
        return False

    try:
        return _hasher(_params_from_hash(encoded)).verify(
            encoded, _mix(password, pepper)
        )
    except (InvalidHashError, VerificationError, VerifyMismatchError, ValueError):
        return False


def needs_rehash(encoded: str) -> bool:
    """True when a stored hash is weaker than current policy and must be upgraded.

    False for anything we cannot parse — including a hash from another
    algorithm. The caller must not treat an unparseable hash as current;
    ``verify_password`` will refuse it anyway.
    """
    try:
        params = _params_from_hash(encoded)
    except InvalidHashError:
        return False
    except ValueError:
        return False
    return params != POLICY_PARAMS and (
        params.time_cost < POLICY_PARAMS.time_cost
        or params.memory_cost < POLICY_PARAMS.memory_cost
        or params.parallelism < POLICY_PARAMS.parallelism
    )


def _params_from_hash(encoded: str) -> Argon2Params:
    """Read m/t/p out of a PHC string. Raises InvalidHashError if absent."""
    if not encoded.startswith("$argon2id$"):
        raise InvalidHashError("not an argon2id hash")
    try:
        fields = encoded.split("$")[3]
    except IndexError as exc:  # pragma: no cover - malformed PHC
        raise InvalidHashError("missing parameter field") from exc

    found: dict[str, int] = {}
    for item in fields.split(","):
        if "=" not in item:
            continue
        key, _, value = item.partition("=")
        if key in ("m", "t", "p"):
            try:
                found[key] = int(value)
            except ValueError as exc:
                raise InvalidHashError("non-integer parameter") from exc

    if set(found) != {"m", "t", "p"}:
        raise InvalidHashError("incomplete parameters")
    return Argon2Params(
        time_cost=found["t"], memory_cost=found["m"], parallelism=found["p"]
    )


# ---------------------------------------------------------------------------
# Policy
# ---------------------------------------------------------------------------


def check_password_policy(
    password: str,
    *,
    username: str | None = None,
    email: str | None = None,
    privileged: bool = False,
) -> None:
    """Raise ``PasswordPolicyError`` if the candidate is not acceptable.

    Length is the control. Composition rules are not used: they push people
    toward predictable substitutions and do not survive a breach list.

    Args:
        password: the candidate, never retained and never echoed
        username: rejected if used as the password
        email: rejected if used as the password
        privileged: apply the longer minimum — anyone who can change who
            holds what

    Raises:
        PasswordPolicyError: on any violation. The message names the rule,
        never the candidate.
    """
    if not isinstance(password, str) or not password:
        raise PasswordPolicyError("Password is required")

    minimum = PRIVILEGED_MIN_PASSWORD_LENGTH if privileged else MIN_PASSWORD_LENGTH

    # Compare on a normalised form so trailing whitespace does not quietly
    # shorten a passphrase, but reject the raw candidate on length first.
    if len(password) < minimum:
        raise PasswordPolicyError(
            f"Password must be at least {minimum} characters"
        )
    if len(password) > MAX_PASSWORD_LENGTH:
        raise PasswordPolicyError(
            f"Password must be at most {MAX_PASSWORD_LENGTH} characters"
        )

    stripped = password.strip()
    if not stripped:
        raise PasswordPolicyError("Password must not be only whitespace")

    if len(set(stripped)) == 1:
        raise PasswordPolicyError("Password must not be a single repeated character")

    lowered = stripped.casefold()
    for label, value in (("username", username), ("email", email)):
        if not value:
            continue
        candidate = value.strip().casefold()
        if not candidate:
            continue
        if lowered == candidate or lowered == candidate.split("@", 1)[0]:
            raise PasswordPolicyError(f"Password must not be the {label}")
