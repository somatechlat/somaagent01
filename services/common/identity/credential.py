"""Routing a credential to the stack that answers for it.

``decode_token`` receives a bearer and has to decide which validation stack
is responsible for it: an issued API key, a local session, or a federated
JWT. Getting that wrong is not cosmetic — a session token handed to the JWT
decoder, or a JWT handed to the session store, is a credential validated by
rules that were never written to cover it.

This is the pure part of that decision: given the shape of the string, which
stack answers. The lookups around it are glue and must not contain a second
opinion.

**The prefixes are the contract.** ``sk_`` and ``ses_`` are reserved and
unambiguous; neither is a prefix of the other. A prefixed credential is
never reinterpreted as a JWT.

**A prefix is not a partial match.** It is four (or three) characters at the
start. A string that merely contains them, or that carries an unknown
reserved-looking prefix, is not routed to that stack.

**Unknown is a rejection, not a fallback.** A bearer that is neither a known
prefix nor JWT-shaped raises. Rule 91: never default. Handing it to the JWT
decoder would be a guess about which authority minted it.
"""

from __future__ import annotations

from enum import Enum

from services.common.identity.session import SESSION_TOKEN_PREFIX

__all__ = [
    "API_KEY_PREFIX",
    "SESSION_TOKEN_PREFIX",
    "CredentialKind",
    "classify_credential",
]

#: Issued API key. Carries explicit scopes and never its issuer's roles.
API_KEY_PREFIX = "sk_"

#: Re-exported: the session token format owns its own prefix (see
#: ``services.common.identity.session``), and this module routes on it.
#: One definition, so the router and the mint cannot drift apart.


class CredentialKind(str, Enum):
    """Which validation stack answers for a bearer."""

    API_KEY = "api_key"
    LOCAL_SESSION = "local_session"
    JWT = "jwt"


def classify_credential(token: str) -> CredentialKind:
    """Name the stack responsible for validating ``token``.

    Args:
        token: the bearer exactly as it was presented. Not trimmed: a
            leading space means this is not the credential that was issued,
            and silently accepting it would accept a bearer no authority
            ever minted.

    Returns:
        The stack that must validate it.

    Raises:
        ValueError: if the token is empty, padded with whitespace, is a bare
            reserved prefix, or is neither a known prefix nor JWT-shaped.
            Never falls through to a guess.
    """
    if not isinstance(token, str) or not token:
        raise ValueError("credential is empty")

    if token != token.strip():
        raise ValueError("credential has leading or trailing whitespace")

    for prefix, kind in (
        (SESSION_TOKEN_PREFIX, CredentialKind.LOCAL_SESSION),
        (API_KEY_PREFIX, CredentialKind.API_KEY),
    ):
        if token.startswith(prefix):
            # The prefix alone is not a credential: it carries no key
            # material, so routing it would look up a hash of almost nothing.
            if len(token) == len(prefix):
                raise ValueError(f"credential is the bare {prefix!r} prefix")
            return kind

    # Three non-empty dot-separated segments is a JWT. Anything else that
    # did not match a known prefix is not something we can identify, and
    # "not identifiable" must not become "treat as federated".
    if _looks_like_jwt(token):
        return CredentialKind.JWT

    raise ValueError("credential matches no known form")


def _looks_like_jwt(token: str) -> bool:
    """Whether ``token`` has the three-segment JWS compact shape."""
    parts = token.split(".")
    return len(parts) == 3 and all(part for part in parts)
