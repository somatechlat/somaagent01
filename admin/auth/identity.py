"""Identity — the single authentication entry point.

There is one question authentication answers and it must be answered by
exactly one authority:

* **Standalone** (``SA01_DEPLOYMENT_MODE=STANDALONE``) — the agent holds the
  credential. ``admin.aaas.models.identity.LocalIdentity`` is the record: an
  argon2id verifier under a pepper held in Vault. No identity provider is
  involved and none may be consulted.
* **Enterprise / AAAS** — the credential belongs to a federated identity
  provider. Keycloak answers the password grant and this process never sees
  the password beyond the POST that hands it over.

The defect this module exists to prevent: ``login_with_email`` used to call
Keycloak unconditionally. In Standalone that authenticates against an
authority that is not the authority, so every login fails with
"Invalid email or password" against a perfectly good local record.

Deployment mode is a **bootstrap** fact (``config.settings_registry`` reads
the one env input, ``SA01_DEPLOYMENT_MODE``). It is not inferred, not probed
and never falls back to the other mode.

``LocalIdentity`` is an authentication record, not an authority record: it
carries role *names* and never permission grants. Authority is
``admin.core.authz``, one catalog, identical in both modes.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class IdentityResult:
    """Outcome of one authentication attempt.

    ``ok`` is True only when a real authority accepted the credential.
    ``provider`` names which one answered, so the audit trail records the
    authority and not just the fact.
    """

    ok: bool
    provider: str
    email: str = ""
    display_name: str = ""
    reason: str = ""
    # The identity's primary key. `_decode_session` resolves a session's
    # principal with `as_uuid(...)`, so the session row must hold this UUID -
    # an email is unresolvable and the session is revoked on first use.
    principal_id: str = ""
    # Role names the principal holds. Authority is `admin.core.authz` - these
    # are names only and grant nothing that catalog does not recognise.
    roles: tuple = ()
    # Data-partition key. Not an attribute of the person - Standalone has one
    # partition and it comes from deployment topology. Authorization refuses
    # a request with no tenant (T-5), so this must be populated.
    tenant_id: str = ""


def resolve_identity_provider() -> str:
    """Return ``"local"`` or ``"federated"`` for this deployment.

    Fail-closed: an unset or unrecognised deployment mode raises rather than
    guessing which authority holds the credential.
    """
    import os

    mode = (os.environ.get("SA01_DEPLOYMENT_MODE") or "").strip().upper()
    if not mode:
        raise RuntimeError(
            "SA01_DEPLOYMENT_MODE is not set. Identity cannot be resolved "
            "without knowing which authority holds the credential."
        )
    if mode in {"STANDALONE", "DEV"}:
        return "local"
    if mode in {"AAAS", "AAASMODE", "PROD"}:
        return "federated"
    raise RuntimeError(
        f"SA01_DEPLOYMENT_MODE={mode!r} is not a recognised mode; "
        f"cannot pick an identity authority."
    )


def _standalone_tenant() -> str:
    """The deployment's data partition.

    Fail-closed: an unconfigured tenant is a refusal. Authorization has no
    fallback tenant (T-5), so an identity with no partition cannot be given
    one by guessing.
    """
    import os

    value = (
        os.environ.get("SA01_TENANT_ID")
        or os.environ.get("AAAS_DEFAULT_TENANT_ID")
        or ""
    ).strip()
    if not value:
        raise RuntimeError(
            "SA01_TENANT_ID is not set. A standalone identity has no tenant "
            "column; the partition comes from deployment topology."
        )
    return value


def _pepper() -> str:
    """The argon2id pepper, from Vault. Never from ENV, never a default."""
    from services.common.unified_secret_manager import get_secret_manager

    value = get_secret_manager().get_credential("identity_password_pepper")
    if not value:
        raise RuntimeError(
            "secret/agent/credentials/identity_password_pepper is not set. "
            "LocalIdentity verifiers are peppered; without the pepper no "
            "password can be checked."
        )
    return value


async def authenticate_local(email: str, password: str) -> IdentityResult:
    """Standalone: verify against LocalIdentity. The agent holds the credential."""
    from asgiref.sync import sync_to_async

    from admin.aaas.models.identity import LocalIdentity

    @sync_to_async
    def _verify() -> IdentityResult:
        row = (
            LocalIdentity.objects.filter(email__iexact=email).first()
            or LocalIdentity.objects.filter(username__iexact=email).first()
        )
        if row is None:
            return IdentityResult(ok=False, provider="local", reason="no_such_identity")
        if not getattr(row, "is_active", True):
            return IdentityResult(ok=False, provider="local", reason="disabled")
        if not row.verify_password(password, _pepper()):
            return IdentityResult(ok=False, provider="local", reason="bad_password")
        return IdentityResult(
            ok=True,
            provider="local",
            email=row.email,
            display_name=row.display_name or row.username,
            principal_id=str(row.id),
            roles=tuple(row.roles or ()),
            tenant_id=_standalone_tenant(),
        )

    return await _verify()


async def authenticate_federated(email: str, password: str) -> IdentityResult:
    """Enterprise: the identity provider answers. This process never stores it."""
    import httpx

    from admin.common.auth import get_keycloak_config
    from admin.llm.services.litellm_helpers import httpx_timeout

    config = get_keycloak_config()
    token_url = (
        f"{config.server_url}/realms/{config.realm}/protocol/openid-connect/token"
    )
    try:
        async with httpx.AsyncClient(timeout=httpx_timeout()) as client:
            resp = await client.post(
                token_url,
                data={
                    "grant_type": "password",
                    "client_id": config.client_id,
                    "username": email,
                    "password": password,
                    "scope": "openid profile email",
                },
            )
    except Exception as exc:
        logger.warning("federated identity provider unreachable: %s", exc)
        return IdentityResult(
            ok=False, provider="federated", reason="provider_unavailable"
        )

    if resp.status_code != 200:
        return IdentityResult(
            ok=False, provider="federated", reason="federated_rejected"
        )
    return IdentityResult(ok=True, provider="federated", email=email)


async def authenticate(email: str, password: str) -> IdentityResult:
    """The one entry point. Exactly one authority answers.

    Never both, never a fallback from one to the other: falling through from
    a federated rejection to a local check would let a disabled cloud account
    be resurrected by a stale local row.
    """
    provider = resolve_identity_provider()
    if provider == "local":
        return await authenticate_local(email, password)
    return await authenticate_federated(email, password)


__all__ = [
    "IdentityResult",
    "resolve_identity_provider",
    "authenticate",
    "authenticate_local",
    "authenticate_federated",
]
