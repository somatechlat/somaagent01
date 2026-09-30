"""The password pepper, held in Vault and nowhere else.

The pepper is the HMAC key that is folded into every password hash
(``services.common.identity.password``). A stolen credential store is inert
without it, which is the whole point — so it must never be generated on
demand, never defaulted, and never written to ENV, argv, a file in the image
or a log line (VIBE Rule 164).

Rule 91 applies in full: a missing pepper raises. It does not silently mint
a new one. Minting one on the read path would either lock every existing
account out or — worse — start accepting passwords under a pepper nobody
chose. Both are worse than being down.

Creation is a separate, explicit, audited act: ``bootstrap_password_pepper``,
called once from the bootstrap command, never from a request path.
"""

from __future__ import annotations

import secrets
from typing import Optional

__all__ = [
    "PASSWORD_PEPPER_VAULT_KEY",
    "PEPPER_MIN_ENTROPY_BYTES",
    "bootstrap_password_pepper",
    "get_password_pepper",
    "require_password_pepper",
]

#: Where the pepper lives in Vault, under ``agent/credentials``.
PASSWORD_PEPPER_VAULT_KEY = "identity_password_pepper"

#: 32 bytes = 256 bits, from the CSPRNG. Below this is refused at bootstrap.
PEPPER_MIN_ENTROPY_BYTES = 32


class MissingPasswordPepper(RuntimeError):
    """No pepper is available and none will be invented.

    Raised instead of proceeding. This is the fail-closed path.
    """


def require_password_pepper(value: Optional[str]) -> str:
    """Return the pepper, or raise.

    Args:
        value: whatever the secret store returned. ``None``, empty and
            whitespace-only are all "missing".

    Raises:
        MissingPasswordPepper: when there is no pepper. There is no default
            and no fallback.
    """
    if not isinstance(value, str) or not value.strip():
        raise MissingPasswordPepper(
            "VIBE Rule 164 VIOLATION: the password pepper is not set. Every "
            "password hash is an HMAC under this value, so without it no "
            "credential can be verified and none must be accepted. It lives "
            f"in Vault at secret/agent/credentials/{PASSWORD_PEPPER_VAULT_KEY}. "
            "Run the bootstrap command to create one; this process will not "
            "generate or default it, because a pepper minted on the read path "
            "either invalidates every existing account or silently weakens "
            "verification. Refusing to continue."
        )
    return value


def get_password_pepper(manager=None) -> str:
    """Read the pepper from Vault.

    Args:
        manager: a ``UnifiedSecretManager``. Defaults to the real singleton.
            Passed in only so this stays testable without reaching for a
            global; the value it returns is still whatever Vault holds.

    Raises:
        MissingPasswordPepper: if Vault has no pepper, or the read fails.
            A Vault that cannot be read is the same as a Vault that has none:
            neither may produce a working credential check.
    """
    if manager is None:
        from services.common.unified_secret_manager import get_secret_manager

        manager = get_secret_manager()

    try:
        stored = manager.get_credential(PASSWORD_PEPPER_VAULT_KEY)
    except Exception as exc:  # noqa: BLE001 - any read failure is "missing"
        raise MissingPasswordPepper(
            "the password pepper could not be read from Vault: "
            f"{type(exc).__name__}. Refusing to verify any credential."
        ) from exc

    return require_password_pepper(stored)


def bootstrap_password_pepper(manager=None) -> str:
    """Create the pepper if and only if none exists, and return it.

    Called once, from the bootstrap command, never from a request path.
    Idempotent in the safe direction: if a pepper already exists it is
    returned unchanged and nothing is overwritten. Overwriting would
    invalidate every stored credential.

    Raises:
        MissingPasswordPepper: if the store refuses the write, or if a read
            after the write still shows nothing. A pepper that did not land
            is not a pepper.
    """
    if manager is None:
        from services.common.unified_secret_manager import get_secret_manager

        manager = get_secret_manager()

    existing = None
    try:
        existing = manager.get_credential(PASSWORD_PEPPER_VAULT_KEY)
    except Exception as exc:  # noqa: BLE001 - a failed read is not a license to overwrite
        raise MissingPasswordPepper(
            "refusing to bootstrap the password pepper: the existing value "
            f"could not be read ({type(exc).__name__}). Overwriting a pepper "
            "that may already exist would invalidate every stored credential."
        ) from exc

    if existing and existing.strip():
        return require_password_pepper(existing)

    generated = secrets.token_urlsafe(PEPPER_MIN_ENTROPY_BYTES)
    try:
        written = manager.set_credential(PASSWORD_PEPPER_VAULT_KEY, generated)
    except Exception as exc:  # noqa: BLE001 - any write failure is a failed bootstrap
        raise MissingPasswordPepper(
            f"refusing to continue: the password pepper could not be written "
            f"to Vault ({type(exc).__name__})."
        ) from exc

    if not written:
        raise MissingPasswordPepper(
            "refusing to continue: Vault did not accept the password pepper."
        )

    return require_password_pepper(get_password_pepper(manager))
