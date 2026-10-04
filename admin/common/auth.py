"""Authentication utilities for Django Ninja endpoints.

Provides Keycloak-based authentication and authorization.
"""

from __future__ import annotations

import logging
import time
import uuid
from functools import lru_cache
from typing import Any, Optional

import httpx
from django.http import HttpRequest
from jose import jwt, JWTError
from ninja.security import HttpBearer
from pydantic import BaseModel

from admin.common.exceptions import ForbiddenError, UnauthorizedError
from services.common.identity.credential import (
    API_KEY_PREFIX,
    CredentialKind,
    classify_credential,
)

# ``API_KEY_PREFIX`` is defined in ``services.common.identity.credential`` and
# imported here, not redeclared. A second definition of a routing prefix is a
# second opinion about which stack owns a bearer, and the two can drift while
# both keep passing their own tests.


def as_uuid(value: Any) -> Optional["uuid.UUID"]:
    """Coerce an identity claim to a UUID, or None.

    ``AuditLog.actor_id`` is a UUIDField. A claim that is not a UUID must not
    be stringified into it: that write raises, and the audit call around it
    swallows the exception, so the event is lost silently. ``None`` means
    "no identifiable actor", which is the truth in that case.

    An audit trail that stores a fabricated identity for an unidentified
    caller is worse than one that records the gap.
    """
    if value is None:
        return None
    try:
        return uuid.UUID(str(value))
    except (ValueError, AttributeError, TypeError):
        return None

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================


class KeycloakConfig(BaseModel):
    """Keycloak configuration."""

    server_url: str
    realm: str
    client_id: str
    # Optional by design: a public OIDC client has no secret. The settings layer
    # normalises a stored empty string to None rather than sending "" to the
    # provider — an empty string is not a credential.
    client_secret: str | None = None

    @property
    def issuer(self) -> str:
        """Get the token issuer URL."""
        return f"{self.server_url}/realms/{self.realm}"

    @property
    def jwks_url(self) -> str:
        """Get the JWKS URL for public keys."""
        return f"{self.issuer}/protocol/openid-connect/certs"

    @property
    def userinfo_url(self) -> str:
        """Get the userinfo endpoint URL."""
        return f"{self.issuer}/protocol/openid-connect/userinfo"


@lru_cache(maxsize=1)
def get_keycloak_config() -> KeycloakConfig:
    """Get cached Keycloak configuration from Django settings."""
    from django.conf import settings

    return KeycloakConfig(
        server_url=settings.KEYCLOAK_URL,
        realm=settings.KEYCLOAK_REALM,
        client_id=settings.KEYCLOAK_CLIENT_ID,
        client_secret=settings.KEYCLOAK_CLIENT_SECRET,
    )


# =============================================================================
# JWT TOKEN HANDLING
# =============================================================================


class TokenPayload(BaseModel):
    """Decoded JWT token payload."""

    sub: str  # Subject (user ID)
    exp: int  # Expiration timestamp
    iat: int  # Issued at timestamp
    iss: str  # Issuer
    aud: str | list[str] | None = None  # Audience
    email: str | None = None
    email_verified: bool = False
    preferred_username: str | None = None
    name: str | None = None
    given_name: str | None = None
    family_name: str | None = None
    realm_access: dict[str, list[str]] | None = None
    resource_access: dict[str, dict[str, list[str]]] | None = None
    scope: str | None = None
    tenant: str | None = None  # JWT claim from Keycloak (e.g., "default")
    tenant_id: str | None = None  # Custom claim for multi-tenancy (UUID)
    session_id: str | None = None  # Custom claim for session tracking

    # Set only when the principal is an API key rather than a person. A key is
    # a delegation: it holds exactly these permissions and no roles at all.
    delegated_scopes: list[str] | None = None

    @property
    def is_api_key(self) -> bool:
        """True when this principal is a delegated API key."""
        return self.delegated_scopes is not None

    @property
    def permissions(self) -> list[str]:
        """Catalog permissions this principal holds.

        A key holds its scopes and nothing else. A person holds what their
        roles grant. The two are never unioned — see
        ``admin.core.authz.permissions_for_principal``.
        """
        from admin.core.authz import permissions_for_principal

        if self.delegated_scopes is not None:
            return sorted(permissions_for_principal(scopes=self.delegated_scopes))
        return sorted(permissions_for_principal(roles=self.roles))

    @property
    def effective_tenant_id(self) -> str | None:
        """Get tenant ID with fallback chain: tenant_id → tenant → settings default.

        This handles the case where Keycloak uses 'tenant' claim but we need UUID.
        """
        from django.conf import settings

        # 1. Direct tenant_id claim (if present)
        if self.tenant_id:
            return self.tenant_id

        # 2. Map 'tenant' claim to UUID
        if self.tenant:
            # If tenant is "default", return the settings default UUID
            if self.tenant == "default":
                return getattr(settings, "AAAS_DEFAULT_TENANT_ID", None)
            # Otherwise use the tenant value directly (might be a UUID)
            return self.tenant

        return None

    @property
    def roles(self) -> list[str]:
        """Get all realm roles."""
        if self.realm_access:
            return self.realm_access.get("roles", [])
        return []

    def has_role(self, role: str) -> bool:
        """Check if token has a specific realm role."""
        return role in self.roles

    def get_client_roles(self, client_id: str) -> list[str]:
        """Get roles for a specific client."""
        if self.resource_access:
            client_access = self.resource_access.get(client_id, {})
            return client_access.get("roles", [])
        return []


class JWKSCache:
    """Cache for JWKS public keys."""

    def __init__(self, ttl_seconds: int = 3600):
        """Initialize the instance."""

        self._cache: dict[str, Any] = {}
        self._expires_at: float = 0
        self._ttl = ttl_seconds

    async def get_keys(self, jwks_url: str) -> dict[str, Any]:
        """Get JWKS keys, fetching if cache expired."""
        if time.time() > self._expires_at:
            async with httpx.AsyncClient() as client:
                try:
                    response = await client.get(jwks_url, timeout=10.0)
                    response.raise_for_status()
                    self._cache = response.json()
                    self._expires_at = time.time() + self._ttl
                except httpx.HTTPError as e:
                    logger.error("Failed to fetch JWKS: %s", e)
                    if not self._cache:
                        raise UnauthorizedError("Unable to verify token")
        return self._cache


_jwks_cache = JWKSCache()


async def decode_token(token: str) -> TokenPayload:
    """Decode and validate a credential.

    Three stacks answer for three kinds of bearer, and the kind is decided
    from the shape of the string before any of them is consulted:

    * an issued API key (``sk_``) is verified against its stored hash and
      carries only the scopes it was issued with;
    * a local session (``ses_``) is resolved against the session store and
      carries the roles its principal holds *now*;
    * a federated JWT is verified against the identity provider's JWKS.

    A bearer is never handed to a stack that did not mint it. A session
    token decoded as a JWT would be checked against rules that cannot cover
    it, and a JWT resolved as a session would be looked up by a hash of
    something that was never a session.

    Args:
        token: The credential string, exactly as presented.

    Returns:
        Decoded token payload

    Raises:
        UnauthorizedError: If the credential is invalid, expired, revoked or
            unknown. All failures are the same failure.
    """
    from django.conf import settings as django_settings

    try:
        kind = classify_credential(token)
    except ValueError:
        # Rule 91: an unrecognised bearer is not a default. Nothing is
        # guessed about who minted it, so it never reaches a decoder.
        raise UnauthorizedError("Invalid or expired token") from None

    if kind is CredentialKind.API_KEY:
        return await _decode_api_key(token)

    if kind is CredentialKind.LOCAL_SESSION:
        return await _decode_session(token)

    config = get_keycloak_config()

    try:
        # Get JWKS for signature verification
        jwks = await _jwks_cache.get_keys(config.jwks_url)

        # Get the signing key
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")

        rsa_key = None
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                rsa_key = key
                break

        if not rsa_key:
            raise UnauthorizedError("Unable to find signing key")

        # Check if strict issuer validation is enabled
        strict_issuer = getattr(django_settings, "JWT_ISSUER_STRICT", True)
        expected_issuer = config.issuer if strict_issuer else None

        # Decode and verify
        # VIBE SECURITY: verify_aud is enabled when JWT_ISSUER_STRICT=true (default)
        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=["RS256"],
            audience=config.client_id if strict_issuer else None,
            issuer=expected_issuer,
            options={
                "verify_aud": strict_issuer,
                "verify_iss": strict_issuer,
            },
        )

        return TokenPayload(**payload)

    except JWTError as e:
        logger.warning("JWT decode error: %s", e)
        raise UnauthorizedError("Invalid or expired token")


async def _decode_api_key(raw_key: str) -> TokenPayload:
    """Resolve an issued API key into a principal.

    FAIL-CLOSED: an unknown, revoked or expired key raises, exactly like a bad
    JWT. A key that cannot be resolved is not "anonymous with no permissions";
    it is unauthenticated.

    The principal carries the key's scopes and no roles. Roles are what a
    person holds; a key is a delegation of a fixed subset of its issuer's
    authority and must not grow into the issuer's.
    """
    from asgiref.sync import sync_to_async

    from admin.aaas.models.profiles import ApiKey

    @sync_to_async
    def _verify():
        return ApiKey.verify(raw_key)

    @sync_to_async
    def _touch(key: ApiKey) -> None:
        try:
            key.mark_used()
        except Exception:  # noqa: BLE001 - usage tracking must not break auth
            pass

    key = await _verify()
    if key is None:
        raise UnauthorizedError("Invalid or expired API key")

    await _touch(key)

    return TokenPayload(
        sub=str(key.user_id or key.id),
        exp=0,
        iat=0,
        iss="api-key",
        tenant_id=str(key.tenant_id) if key.tenant_id else None,
        delegated_scopes=list(key.scopes or []),
    )


def _deployment_tenant() -> str:
    """The deployment's data partition, from topology.

    Fail-closed: an unconfigured partition is a refusal, never a guess.
    """
    import os

    value = (
        os.environ.get("SA01_TENANT_ID")
        or os.environ.get("AAAS_DEFAULT_TENANT_ID")
        or ""
    ).strip()
    return value or None


async def _decode_session(raw_token: str) -> TokenPayload:
    """Resolve a local session token into the principal who holds it.

    FAIL-CLOSED on every path: unknown, revoked, expired, orphaned and
    offboarded sessions all raise, exactly like a bad JWT. There is no branch
    that treats "could not tell" as allowed.

    **Offboarding is permanent.** A session whose identity has been disabled
    or removed is revoked, not merely refused. Refusing alone would leave a
    live credential sitting in the table waiting for the identity to come
    back, and the kill would have to be remembered by something outside this
    path.

    **Authority is resolved at request time.** The session row holds no roles
    and no permissions; they are read from the identity on every request. A
    grant taken away therefore cannot survive inside a live session, and a
    session can never carry ``delegated_scopes`` — that flag is what switches
    authority from roles to scopes, and a session is the person themselves,
    not a delegation.
    """
    from asgiref.sync import sync_to_async

    from admin.aaas.models.identity import LocalIdentity
    from admin.aaas.models.session import LocalSession

    @sync_to_async
    def _resolve():
        """One synchronous block: look up, decide, and make any kill stick.

        Returns the row and its identity, or ``None`` after whatever state
        change the denial required. The caller turns ``None`` into one
        uniform failure.
        """
        from django.utils import timezone

        from services.common.identity.session import hash_session_token

        try:
            session = LocalSession.objects.get(
                token_hash=hash_session_token(raw_token)
            )
        except LocalSession.DoesNotExist:
            # Unknown is the same work as known, so the shape of the
            # failure cannot be used to probe for live sessions.
            return None

        now = timezone.now()
        if not session.is_valid(now=now):
            # A dead session is not revived by being presented. Expiry is a
            # timer rather than a kill, so the row is left to age out; only
            # an unusable principal is revoked below.
            return None

        principal = as_uuid(session.principal_id)
        if principal is None:
            # A session whose holder cannot be named is orphaned. It must
            # not outlive whatever it used to point at.
            session.mark_revoked(now=now)
            session.save(update_fields=["revoked", "revoked_at"])
            return None

        try:
            identity = LocalIdentity.objects.get(pk=principal)
        except LocalIdentity.DoesNotExist:
            session.mark_revoked(now=now)
            session.save(update_fields=["revoked", "revoked_at"])
            return None

        if not identity.is_active:
            # Offboarding. The credential is killed so that re-enabling the
            # identity does not silently hand back an old session.
            session.mark_revoked(now=now)
            session.save(update_fields=["revoked", "revoked_at"])
            return None

        # Slide the idle window. If this write fails the session idles out
        # sooner rather than later, which is the safe direction, so it must
        # not turn a good credential into a denial.
        session.last_seen_at = now
        session.save(update_fields=["last_seen_at"])

        return session, identity

    resolved = await _resolve()
    if resolved is None:
        raise UnauthorizedError("Invalid or expired session")

    session, identity = resolved

    return TokenPayload(
        sub=str(identity.id),
        # Opaque credential: the store decides whether it is live, not a
        # claim. These are not consulted for a session and must not become a
        # second expiry policy beside ``session_decision``.
        exp=0,
        iat=0,
        iss="local-session",
        email=identity.email or None,
        preferred_username=identity.username,
        name=identity.display_name or None,
        # A person is authorized by roles. Never by scopes.
        realm_access={"roles": list(identity.roles or [])},
        # Standalone has one data partition and it is deployment topology -
        # LocalIdentity is an authentication record and carries no tenant.
        # Authorization refuses a request with no tenant (T-5).
        tenant_id=_deployment_tenant(),
        session_id=str(session.id),
    )


# =============================================================================
# NINJA SECURITY CLASSES
# =============================================================================


class AuthBearer(HttpBearer):
    """Bearer token authentication for Django Ninja.

    Supports both Bearer header and httpOnly cookie fallback.
    Overrides __call__ because Django Ninja's HttpBearer returns None
    when no Authorization header is present — our cookie fallback never
    fires without this override.

    Usage:
        @router.get("/protected", auth=AuthBearer())
        async def protected_endpoint(request):
            user = request.auth  # TokenPayload
            ...
    """

    def __call__(self, request: HttpRequest) -> Optional[Any]:
        """Check Authorization header first, then fall back to httpOnly cookie."""
        auth_value = request.headers.get("Authorization", "")
        if auth_value.startswith("Bearer "):
            token = auth_value[7:]
            return self.authenticate(request, token)
        # No Bearer header — try cookie fallback
        return self.authenticate(request, "")

    async def authenticate(self, request, token: str) -> TokenPayload | None:
        """Authenticate the bearer token or cookie."""
        try:
            effective_token = token or request.COOKIES.get("access_token", "")
            if not effective_token:
                return None
            payload = await decode_token(effective_token)
            _apply_session_cookie(payload, request)
            return payload
        except UnauthorizedError:
            return None


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def get_current_user(request) -> TokenPayload:
    """Get the authenticated user from request.

    Args:
        request: Django request with auth

    Returns:
        TokenPayload for authenticated user

    Raises:
        UnauthorizedError: If not authenticated
    """
    if not hasattr(request, "auth") or request.auth is None:
        raise UnauthorizedError()
    return request.auth


def _apply_session_cookie(payload: TokenPayload, request) -> None:
    """Attach session_id from cookie to token payload when missing."""
    if payload.session_id:
        return
    session_id = request.COOKIES.get("session_id")
    if session_id:
        payload.session_id = session_id


