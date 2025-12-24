"""Auth API Router for Django Ninja.

VIBE COMPLIANT - 100% Django Ninja, Keycloak integration.
Provides token-based authentication endpoints:
- POST /token - Get access token
- POST /refresh - Refresh token
- GET /me - Get current user info
- POST /logout - Revoke tokens
"""

from __future__ import annotations

import logging
from typing import Optional
from uuid import UUID

import httpx
from django.conf import settings
from django.utils import timezone
from ninja import Router, Schema
from pydantic import EmailStr
from jose import jwt, JWTError

from admin.common.auth import get_keycloak_config, decode_token, TokenPayload
from admin.common.exceptions import UnauthorizedError, BadRequestError
from admin.saas.models import Tenant, TenantUser


logger = logging.getLogger(__name__)

router = Router(tags=["Authentication"])


# =============================================================================
# SCHEMAS
# =============================================================================


class TokenRequest(Schema):
    """Login request with username/password or OAuth code."""
    username: Optional[str] = None
    password: Optional[str] = None
    code: Optional[str] = None  # OAuth authorization code
    redirect_uri: Optional[str] = None
    grant_type: str = "password"


class TokenResponse(Schema):
    """Token response."""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "Bearer"
    expires_in: int
    redirect_path: str = "/chat"


class RefreshRequest(Schema):
    """Refresh token request."""
    refresh_token: Optional[str] = None


class UserResponse(Schema):
    """Current user info response."""
    id: str
    tenant_id: Optional[str] = None
    username: str
    email: Optional[str] = None
    name: Optional[str] = None
    role: str
    roles: list[str] = []
    permissions: list[str] = []


# =============================================================================
# ENDPOINTS
# =============================================================================


@router.post("/token", response=TokenResponse)
async def get_token(request, payload: TokenRequest):
    """Get access token via password grant or OAuth code exchange.
    
    VIBE COMPLIANT - Real Keycloak token exchange, no mocks.
    """
    config = get_keycloak_config()
    token_url = f"{config.server_url}/realms/{config.realm}/protocol/openid-connect/token"
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            if payload.grant_type == "authorization_code" and payload.code:
                # OAuth code exchange
                response = await client.post(
                    token_url,
                    data={
                        "grant_type": "authorization_code",
                        "client_id": config.client_id,
                        "code": payload.code,
                        "redirect_uri": payload.redirect_uri or f"{request.build_absolute_uri('/')[:-1]}/auth/callback",
                    }
                )
            else:
                # Password grant (for dev/testing)
                if not payload.username or not payload.password:
                    raise BadRequestError(
                        message="Username and password required",
                        details={"field": "username"}
                    )
                    
                response = await client.post(
                    token_url,
                    data={
                        "grant_type": "password",
                        "client_id": config.client_id,
                        "username": payload.username,
                        "password": payload.password,
                        "scope": "openid profile email",
                    }
                )
            
            if response.status_code != 200:
                logger.warning(f"Token request failed: {response.status_code}")
                raise UnauthorizedError(message="Invalid credentials")
            
            token_data = response.json()
            
            # Decode token to determine redirect path based on role
            token_payload = await decode_token(token_data["access_token"])
            redirect_path = _determine_redirect_path(token_payload)
            
            # Update last login timestamp if user exists
            await _update_last_login(token_payload)
            
            return TokenResponse(
                access_token=token_data["access_token"],
                refresh_token=token_data.get("refresh_token"),
                token_type="Bearer",
                expires_in=token_data.get("expires_in", 900),
                redirect_path=redirect_path,
            )
            
    except httpx.HTTPError as e:
        logger.error(f"Keycloak communication error: {e}")
        raise UnauthorizedError(message="Authentication service unavailable")


@router.post("/refresh", response=TokenResponse)
async def refresh_token(request, payload: RefreshRequest):
    """Refresh access token using refresh token.
    
    VIBE COMPLIANT - Real Keycloak token refresh.
    """
    config = get_keycloak_config()
    
    # Get refresh token from request body or Authorization header
    refresh_token = payload.refresh_token
    if not refresh_token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            # Try to get stored refresh token (would need session store)
            raise BadRequestError(message="Refresh token required")
    
    token_url = f"{config.server_url}/realms/{config.realm}/protocol/openid-connect/token"
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                token_url,
                data={
                    "grant_type": "refresh_token",
                    "client_id": config.client_id,
                    "refresh_token": refresh_token,
                }
            )
            
            if response.status_code != 200:
                raise UnauthorizedError(message="Invalid or expired refresh token")
            
            token_data = response.json()
            
            return TokenResponse(
                access_token=token_data["access_token"],
                refresh_token=token_data.get("refresh_token"),
                token_type="Bearer",
                expires_in=token_data.get("expires_in", 900),
                redirect_path="/chat",
            )
            
    except httpx.HTTPError as e:
        logger.error(f"Token refresh error: {e}")
        raise UnauthorizedError(message="Token refresh failed")


@router.get("/me", response=UserResponse)
async def get_current_user(request):
    """Get current authenticated user info.
    
    VIBE COMPLIANT - Real token validation, tenant lookup.
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise UnauthorizedError()
    
    token = auth_header[7:]
    
    try:
        payload = await decode_token(token)
        
        # Get user info from Keycloak
        config = get_keycloak_config()
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{config.server_url}/realms/{config.realm}/protocol/openid-connect/userinfo",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code == 200:
                userinfo = response.json()
            else:
                userinfo = {}
        
        # Get tenant info if available
        tenant_id = payload.tenant_id
        
        # Determine role from token
        roles = payload.roles
        role = _get_highest_role(roles)
        
        # Build permissions list based on roles
        permissions = _get_permissions_for_roles(roles)
        
        return UserResponse(
            id=payload.sub,
            tenant_id=tenant_id,
            username=payload.preferred_username or payload.sub,
            email=payload.email or userinfo.get("email"),
            name=payload.name or userinfo.get("name"),
            role=role,
            roles=roles,
            permissions=permissions,
        )
        
    except (JWTError, UnauthorizedError):
        raise UnauthorizedError(message="Invalid token")


@router.post("/logout")
async def logout(request):
    """Logout and revoke tokens.
    
    VIBE COMPLIANT - Real Keycloak session termination.
    """
    auth_header = request.headers.get("Authorization", "")
    refresh_token = request.POST.get("refresh_token")
    
    config = get_keycloak_config()
    logout_url = f"{config.server_url}/realms/{config.realm}/protocol/openid-connect/logout"
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            if refresh_token:
                await client.post(
                    logout_url,
                    data={
                        "client_id": config.client_id,
                        "refresh_token": refresh_token,
                    }
                )
    except httpx.HTTPError:
        pass  # Continue even if logout call fails
    
    return {"success": True}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def _determine_redirect_path(payload: TokenPayload) -> str:
    """Determine redirect path based on user roles.
    
    - saas_admin, tenant_sysadmin -> /select-mode (mode selection)
    - tenant_admin, agent_owner -> /dashboard
    - user, viewer -> /chat
    """
    roles = set(payload.roles)
    
    if "saas_admin" in roles:
        return "/select-mode"
    elif "tenant_sysadmin" in roles:
        return "/select-mode"
    elif "tenant_admin" in roles:
        return "/dashboard"
    elif "agent_owner" in roles:
        return "/dashboard"
    else:
        return "/chat"


def _get_highest_role(roles: list[str]) -> str:
    """Get the highest priority role from the roles list."""
    role_priority = [
        "saas_admin",
        "tenant_sysadmin",
        "tenant_admin",
        "agent_owner",
        "developer",
        "trainer",
        "user",
        "viewer",
    ]
    
    for role in role_priority:
        if role in roles:
            return role
    
    return "user"


def _get_permissions_for_roles(roles: list[str]) -> list[str]:
    """Map roles to permissions."""
    permissions = set()
    
    role_permissions = {
        "saas_admin": [
            "platform:manage", "platform:manage_tenants", "platform:manage_tiers",
            "platform:manage_roles", "platform:impersonate",
            "tenant:manage", "agent:configure", "chat:send", "memory:read", "memory:write",
        ],
        "tenant_sysadmin": [
            "tenant:manage", "tenant:assign_roles", "tenant:view_billing",
            "agent:configure", "agent:create", "agent:delete",
            "chat:send", "memory:read", "memory:write",
        ],
        "tenant_admin": [
            "tenant:administrate", "agent:configure",
            "chat:send", "memory:read", "memory:write",
        ],
        "agent_owner": [
            "agent:configure", "agent:manage_users",
            "chat:send", "memory:read", "memory:write",
        ],
        "developer": [
            "agent:activate_dev", "chat:send", "memory:read", "memory:write",
        ],
        "trainer": [
            "agent:activate_trn", "cognitive:view", "cognitive:edit",
            "chat:send", "memory:read", "memory:write",
        ],
        "user": [
            "chat:send", "memory:read",
        ],
        "viewer": [
            "chat:view", "memory:read",
        ],
    }
    
    for role in roles:
        if role in role_permissions:
            permissions.update(role_permissions[role])
    
    return list(permissions)


async def _update_last_login(payload: TokenPayload) -> None:
    """Update user's last login timestamp if they exist in our database."""
    from django.db import connection
    from asgiref.sync import sync_to_async
    
    try:
        @sync_to_async
        def update_login():
            TenantUser.objects.filter(
                user_id=payload.sub
            ).update(last_login_at=timezone.now())
        
        await update_login()
    except Exception as e:
        # Non-critical - log but don't fail
        logger.debug(f"Could not update last_login: {e}")
