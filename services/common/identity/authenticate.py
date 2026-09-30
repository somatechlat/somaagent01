"""The authentication decision table.

Given what the store knows and what the caller presented, may this attempt
succeed?

This is the security-critical core of login, and it is pure on purpose. The
lookup and the persistence around it are glue and must not contain a second
opinion; every rule that decides is here.

**Order is security.** The caller must consult the lockout *before* hashing
the password. Argon2 is deliberately expensive, so an endpoint that hashes
on behalf of a locked account is a CPU denial-of-service amplifier. The
result carries ``password_checked`` so that ordering is assertable rather
than assumed.

**Uniform failure.** Unknown user, wrong password, disabled account and
missing credential all produce the same public message. Which one it was
goes to the audit trail as ``reason``, never to the response. User
enumeration is not a feature.

**Nothing fails open.** There is no combination of inputs that turns
"cannot check" into "checked and fine".
"""

from __future__ import annotations

from dataclasses import dataclass

from services.common.identity.lockout import LockoutDecision

__all__ = [
    "AuthenticationOutcome",
    "PUBLIC_FAILURE_MESSAGE",
    "decide_authentication",
]

#: What every failure looks like to whoever is holding the keyboard.
PUBLIC_FAILURE_MESSAGE = "Invalid credentials"


@dataclass(frozen=True)
class AuthenticationOutcome:
    """The decision, plus what the audit trail is allowed to know."""

    ok: bool
    reason: str
    password_checked: bool
    requires_admin: bool = False

    @property
    def public_message(self) -> str:
        """The only failure message a caller may ever see.

        Successful attempts have no public failure message; the property
        still returns the uniform string so a caller cannot accidentally
        interpolate a precise reason into a response.
        """
        return PUBLIC_FAILURE_MESSAGE


def decide_authentication(
    *,
    is_active: bool,
    has_password: bool,
    password_ok: bool,
    lockout: LockoutDecision,
) -> AuthenticationOutcome:
    """Decide one authentication attempt.

    Args:
        is_active: whether the identity exists and is enabled. An unknown
            account is passed as ``is_active=False``.
        has_password: whether a credential has ever been set for this
            identity. An identity with none must never authenticate.
        password_ok: the result of the constant-time password comparison.
            Ignored entirely when the lockout denies first — that is the
            point of calling the lockout first.
        lockout: the lockout decision for this principal right now.

    Returns:
        The decision. ``password_checked`` is False whenever the hash was
        never run, which is the assertion that keeps argon2 off the
        attack path.
    """
    # 1. Lockout first. Cheapest, and it protects the expensive step.
    if lockout.locked:
        return AuthenticationOutcome(
            ok=False,
            reason="locked" if not lockout.requires_admin else "hard_locked",
            password_checked=False,
            requires_admin=lockout.requires_admin,
        )

    # 2. An account that is missing or disabled is not a target to verify.
    if not is_active:
        return AuthenticationOutcome(
            ok=False,
            reason="unknown_or_disabled",
            password_checked=False,
        )

    # 3. No credential set is a locked door, not an open one.
    if not has_password:
        return AuthenticationOutcome(
            ok=False,
            reason="no_credential",
            password_checked=False,
        )

    # 4. Only now was the password actually compared.
    if not password_ok:
        return AuthenticationOutcome(
            ok=False,
            reason="bad_password",
            password_checked=True,
        )

    return AuthenticationOutcome(
        ok=True, reason="ok", password_checked=True
    )
