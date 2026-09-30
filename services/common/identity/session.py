"""Opaque session tokens and session lifetime.

Browser sessions here are **opaque**, not JWT.

A JWT is a bearer credential that is good until it expires and cannot be
taken back. An opaque token is a lookup key into a server-side record that
can be killed in one write. For an agent that administers itself — one that
can issue API keys, export the audit trail and impersonate — "revoke now"
is worth more than "no round trip".

What the token is:

* **256 bits from the CSPRNG**, prefixed so a presented credential can be
  routed to this verifier without trying to parse it as a JWT.
* **Only its SHA-256 is stored.** A dump of the session table must not yield
  working cookies. The hash is deterministic so it can be a lookup key.
* **No structure to forge.** There is no signature, no `alg` field, no
  audience claim to get wrong. Guessing is the only attack and 256 bits is
  not guessable.

How long it lives:

* **Idle timeout** — unused, it dies.
* **Absolute timeout** — active or not, it dies. This is the one that cannot
  be talked past: without it a stolen session is permanent, because an
  attacker who has the cookie can keep it warm forever.
* **Privileged sessions get less rope** in both dimensions. The roles that
  can change who holds what do not sit on a twelve-hour session.

Revocation is checked first and wins over every timing rule. A revoked
session is dead on the next request, not at expiry.

The clock is passed in. Persistence is the caller's.
"""

from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta

__all__ = [
    "ABSOLUTE_TIMEOUT",
    "IDLE_TIMEOUT",
    "PRIVILEGED_ABSOLUTE_TIMEOUT",
    "PRIVILEGED_IDLE_TIMEOUT",
    "SESSION_TOKEN_PREFIX",
    "SessionDecision",
    "SessionRecord",
    "generate_session_token",
    "hash_session_token",
    "session_decision",
]

#: Routing prefix. A credential starting with this is a session token and
#: must be resolved here, never decoded as a JWT (and never confused with an
#: API key, which is ``sk_``).
SESSION_TOKEN_PREFIX = "ses_"

#: 32 bytes = 256 bits from the CSPRNG. A UUID is 122 bits and half of it is
#: predictable; that is not a credential.
SESSION_TOKEN_ENTROPY_BYTES = 32

IDLE_TIMEOUT = timedelta(minutes=30)
ABSOLUTE_TIMEOUT = timedelta(hours=12)
PRIVILEGED_IDLE_TIMEOUT = timedelta(minutes=15)
PRIVILEGED_ABSOLUTE_TIMEOUT = timedelta(hours=8)


@dataclass(frozen=True)
class SessionRecord:
    """Server-side session state.

    Holds the token **hash**, never the token. Carries no password, no role
    and no permission — authority is resolved from the principal through the
    permission catalog at request time, so a stale session cannot carry a
    stale grant.
    """

    token_hash: str
    principal_id: str
    created_at: datetime
    last_seen_at: datetime
    revoked: bool = False
    privileged: bool = False


@dataclass(frozen=True)
class SessionDecision:
    """Whether a session may be used for this request."""

    valid: bool
    reason: str  # "ok" | "revoked" | "idle_expired" | "absolute_expired"


def generate_session_token() -> tuple[str, str]:
    """Mint a session token.

    Returns:
        ``(raw_token, token_hash)``. The raw token is shown to the client
        once and never stored; the hash is what goes in the session record.
    """
    raw = SESSION_TOKEN_PREFIX + secrets.token_urlsafe(SESSION_TOKEN_ENTROPY_BYTES)
    return raw, hash_session_token(raw)


def hash_session_token(raw: str) -> str:
    """SHA-256 of the raw token, hex.

    Deterministic, so it works as a lookup key. One-way, so the stored form
    cannot be turned back into a cookie. SHA-256 is the right choice here
    and not argon2: this is a lookup key over 256 bits of CSPRNG output, not
    a low-entropy secret a human chose. Making lookup expensive would only
    make every authenticated request slower without raising the bar.
    """
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def session_decision(record: SessionRecord, *, now: datetime) -> SessionDecision:
    """Decide whether ``record`` may be used at ``now``.

    Order matters and is deliberate:

    1. revocation — a kill switch, not a timer
    2. idle expiry — unused means dead
    3. absolute expiry — old means dead, however active

    Absolute is checked after idle so the reason reflects the more specific
    cause when both have elapsed; either one is a denial.
    """
    if record.revoked:
        return SessionDecision(valid=False, reason="revoked")

    idle = PRIVILEGED_IDLE_TIMEOUT if record.privileged else IDLE_TIMEOUT
    if now - record.last_seen_at > idle:
        return SessionDecision(valid=False, reason="idle_expired")

    absolute = (
        PRIVILEGED_ABSOLUTE_TIMEOUT if record.privileged else ABSOLUTE_TIMEOUT
    )
    if now - record.created_at > absolute:
        return SessionDecision(valid=False, reason="absolute_expired")

    return SessionDecision(valid=True, reason="ok")
