"""Authentication utilities for Django Ninja endpoints.

Provides Keycloak-based authentication and authorization.
"""

from __future__ import annotations

import os
import time
import logging
from typing import Any
from functools import lru_cache

import httpx
from ninja.security import HttpBearer
from pydantic import BaseModel
from jose import jwt, JWTError

from admin.common.exceptions import UnauthorizedError, ForbiddenError


logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================


class KeycloakConfig(BaseModel):
    """Keycloak configuration."""

    server_url: str
    realm: str
    client_id: str
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
    """Get cached Keycloak configuration from environment."""
    return KeycloakConfig(
        server_url=os.environ.get("KEYCLOAK_URL", "http://localhost:20880"),
        realm=os.environ.get("KEYCLOAK_REALM", "somaagent"),
        client_id=os.environ.get("KEYCLOAK_CLIENT_ID", "eye-of-god"),
        client_secret=os.environ.get("KEYCLOAK_CLIENT_SECRET"),
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
    tenant_id: str | None = None  # Custom claim for multi-tenancy

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
                    logger.error(f"Failed to fetch JWKS: {e}")
                    if not self._cache:
                        raise UnauthorizedError("Unable to verify token")
        return self._cache


_jwks_cache = JWKSCache()


async def decode_token(token: str) -> TokenPayload:
    """Decode and validate a JWT token.

    Args:
        token: The JWT token string

    Returns:
        Decoded token payload

    Raises:
        UnauthorizedError: If token is invalid or expired
    """
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

        # Decode and verify
        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=["RS256"],
            audience=config.client_id,
            issuer=config.issuer,
            options={"verify_aud": False},  # Keycloak may have multiple audiences
        )

        return TokenPayload(**payload)

    except JWTError as e:
        logger.warning(f"JWT decode error: {e}")
        raise UnauthorizedError("Invalid or expired token")


# =============================================================================
# NINJA SECURITY CLASSES
# =============================================================================


class AuthBearer(HttpBearer):
    """Bearer token authentication for Django Ninja.

    Usage:
        @router.get("/protected", auth=AuthBearer())
        async def protected_endpoint(request):
            user = request.auth  # TokenPayload
            ...
    """

    async def authenticate(self, request, token: str) -> TokenPayload | None:
        """Authenticate the bearer token."""
        try:
            return await decode_token(token)
        except UnauthorizedError:
            return None


class RoleRequired(HttpBearer):
    """Bearer token authentication with role requirement.

    Usage:
        @router.get("/admin-only", auth=RoleRequired("admin"))
        async def admin_endpoint(request):
            ...
    """

    def __init__(self, *required_roles: str):
        super().__init__()
        self.required_roles = set(required_roles)

    async def authenticate(self, request, token: str) -> TokenPayload | None:
        """Authenticate and check roles."""
        try:
            payload = await decode_token(token)

            # Check if user has at least one required role
            user_roles = set(payload.roles)
            if not user_roles.intersection(self.required_roles):
                return None

            return payload

        except UnauthorizedError:
            return None


class TenantRequired(HttpBearer):
    """Bearer token authentication with tenant requirement.

    Extracts tenant_id from token and validates access.

    Usage:
        @router.get("/tenant-resource", auth=TenantRequired())
        async def tenant_endpoint(request):
            tenant_id = request.auth.tenant_id
            ...
    """

    async def authenticate(self, request, token: str) -> TokenPayload | None:
        """Authenticate and extract tenant."""
        try:
            payload = await decode_token(token)

            # Tenant ID must be present
            if not payload.tenant_id:
                return None

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


def require_roles(*roles: str):
    """Decorator to require specific roles.

    Usage:
        @router.get("/admin")
        @require_roles("admin", "super_admin")
        async def admin_endpoint(request):
            ...
    """

    def decorator(func):
        async def wrapper(request, *args, **kwargs):
            user = get_current_user(request)
            user_roles = set(user.roles)
            required_roles = set(roles)

            if not user_roles.intersection(required_roles):
                raise ForbiddenError(
                    action="access",
                    resource="endpoint",
                )

            return await func(request, *args, **kwargs)

        return wrapper

    return decorator


def require_permission(permission: str):
    """Decorator to require specific permission.

    For use with SpiceDB integration.

    Usage:
        @router.get("/resource/{id}")
        @require_permission("view")
        async def view_resource(request, id: str):
            ...
    """

    def decorator(func):
        async def wrapper(request, *args, **kwargs):
            # For now, just verify authentication
            user = get_current_user(request)
            return await func(request, *args, **kwargs)

        return wrapper

    return decorator
