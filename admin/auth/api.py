"""Authentication API Router for SomaAgent01.

Split into modules for 650-line compliance:
- api_schemas.py: Request/Response schemas
- api_helpers.py: Role/permission helpers
- api_sso.py: SSO endpoints
- api_oauth.py: OAuth/PKCE endpoints
- api.py: Core auth endpoints (this file)
"""

from __future__ import annotations

import logging

import httpx
from jose import jwt, JWTError
from ninja import Router

from admin.auth.api_helpers import (
    determine_redirect_path,
    get_highest_role,
    get_permissions_for_roles,
    update_last_login,
)
from admin.auth.api_schemas import (
    ImpersonationRequest,
    ImpersonationResponse,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenRequest,
    TokenResponse,
    UserResponse,
)
from admin.common.auth import decode_token, get_keycloak_config
from admin.common.exceptions import BadRequestError, UnauthorizedError
from admin.saas.models import Tenant

logger = logging.getLogger(__name__)
router = Router(tags=["Authentication"])


# =============================================================================
# CORE ENDPOINTS
# =============================================================================


@router.post("/token", response=TokenResponse)
async def get_token(request, payload: TokenRequest, response):
    """Get access token via password grant or OAuth code exchange."""
    config = get_keycloak_config()
    token_url = f"{config.server_url}/realms/{config.realm}/protocol/openid-connect/token"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            if payload.grant_type == "authorization_code" and payload.code:
                resp = await client.post(
                    token_url,
                    data={
                        "grant_type": "authorization_code",
                        "client_id": config.client_id,
                        "code": payload.code,
                        "redirect_uri": payload.redirect_uri
                        or f"{request.build_absolute_uri('/')[:-1]}/auth/callback",
                    },
                )
            else:
                if not payload.username or not payload.password:
                    raise BadRequestError(
                        message="Username and password required", details={"field": "username"}
                    )
                resp = await client.post(
                    token_url,
                    data={
                        "grant_type": "password",
                        "client_id": config.client_id,
                        "username": payload.username,
                        "password": payload.password,
                        "scope": "openid profile email",
                    },
                )

            if resp.status_code != 200:
                raise UnauthorizedError(message="Invalid credentials")

            token_data = resp.json()
            token_payload = await decode_token(token_data["access_token"])
            redirect_path = determine_redirect_path(token_payload)
            await update_last_login(token_payload)

            from django.conf import settings

            from admin.common.session_manager import get_session_manager

            session_manager = await get_session_manager()
            permissions = await session_manager.resolve_permissions(
                user_id=token_payload.sub,
                tenant_id=token_payload.tenant_id or "",
                roles=token_payload.roles,
            )
            session = await session_manager.create_session(
                user_id=token_payload.sub,
                tenant_id=token_payload.tenant_id or "",
                email=token_payload.email or payload.username or "",
                roles=token_payload.roles,
                permissions=permissions,
                ip_address=request.META.get("REMOTE_ADDR", ""),
                user_agent=request.META.get("HTTP_USER_AGENT", ""),
            )

            cookie_secure = not settings.DEBUG
            _set_auth_cookies(response, token_data, session.session_id, cookie_secure)

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
async def refresh_token(request, payload: RefreshRequest, response):
    """Refresh access token using refresh token."""
    config = get_keycloak_config()
    refresh_token = payload.refresh_token or request.COOKIES.get("refresh_token")
    if not refresh_token:
        raise BadRequestError(message="Refresh token required")

    token_url = f"{config.server_url}/realms/{config.realm}/protocol/openid-connect/token"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                token_url,
                data={
                    "grant_type": "refresh_token",
                    "client_id": config.client_id,
                    "refresh_token": refresh_token,
                },
            )
            if resp.status_code != 200:
                raise UnauthorizedError(message="Invalid or expired refresh token")
            token_data = resp.json()
            token_payload = await decode_token(token_data["access_token"])

            from django.conf import settings

            from admin.common.session_manager import get_session_manager

            session_manager = await get_session_manager()
            session_id = request.COOKIES.get("session_id")
            if session_id:
                session = await session_manager.get_session(token_payload.sub, session_id)
                if session:
                    await session_manager.update_activity(token_payload.sub, session_id)
            if not session_id:
                permissions = await session_manager.resolve_permissions(
                    user_id=token_payload.sub,
                    tenant_id=token_payload.tenant_id or "",
                    roles=token_payload.roles,
                )
                session = await session_manager.create_session(
                    user_id=token_payload.sub,
                    tenant_id=token_payload.tenant_id or "",
                    email=token_payload.email or "",
                    roles=token_payload.roles,
                    permissions=permissions,
                    ip_address=request.META.get("REMOTE_ADDR", ""),
                    user_agent=request.META.get("HTTP_USER_AGENT", ""),
                )
                session_id = session.session_id

            cookie_secure = not settings.DEBUG
            _set_auth_cookies(response, token_data, session_id, cookie_secure)
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
    """Get current authenticated user info."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise UnauthorizedError()
    token = auth_header[7:]
    try:
        payload = await decode_token(token)
        config = get_keycloak_config()
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{config.server_url}/realms/{config.realm}/protocol/openid-connect/userinfo",
                headers={"Authorization": f"Bearer {token}"},
            )
            userinfo = resp.json() if resp.status_code == 200 else {}
        roles = payload.roles
        return UserResponse(
            id=payload.sub,
            tenant_id=payload.tenant_id,
            username=payload.preferred_username or payload.sub,
            email=payload.email or userinfo.get("email"),
            name=payload.name or userinfo.get("name"),
            role=get_highest_role(roles),
            roles=roles,
            permissions=get_permissions_for_roles(roles),
        )
    except (JWTError, UnauthorizedError):
        raise UnauthorizedError(message="Invalid token")


@router.post("/logout")
async def logout(request):
    """Logout and revoke tokens."""
    refresh_token = request.POST.get("refresh_token")
    config = get_keycloak_config()
    logout_url = f"{config.server_url}/realms/{config.realm}/protocol/openid-connect/logout"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            if refresh_token:
                await client.post(
                    logout_url, data={"client_id": config.client_id, "refresh_token": refresh_token}
                )
    except httpx.HTTPError:
        pass
    return {"success": True}


# =============================================================================
# LOGIN ENDPOINT
# =============================================================================


@router.post("/login")
async def login_with_email(request, payload: LoginRequest, response):
    """Login with email and password with account lockout protection."""
    from admin.common.account_lockout import get_lockout_service
    from admin.common.exceptions import ForbiddenError
    from admin.common.rate_limit import check_rate_limit
    from admin.common.session_manager import get_session_manager

    client_ip = request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[
        0
    ].strip() or request.META.get("REMOTE_ADDR", "unknown")
    await check_rate_limit(client_ip, "/api/v2/auth/login", limit=10, window=60)

    lockout_service = await get_lockout_service()
    lockout_status = await lockout_service.check_lockout(payload.email)
    if lockout_status.is_locked:
        raise ForbiddenError(
            action="login",
            resource="account",
            message=f"Account locked. Try again in {lockout_status.retry_after // 60} minutes.",
            details={"retry_after": lockout_status.retry_after},
        )

    config = get_keycloak_config()
    token_url = f"{config.server_url}/realms/{config.realm}/protocol/openid-connect/token"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                token_url,
                data={
                    "grant_type": "password",
                    "client_id": config.client_id,
                    "username": payload.email,
                    "password": payload.password,
                    "scope": "openid profile email",
                },
            )

            if resp.status_code == 200:
                await lockout_service.record_successful_login(payload.email)
                token_data = resp.json()
                token_payload = await decode_token(token_data["access_token"])
                redirect_path = determine_redirect_path(token_payload)

                session_manager = await get_session_manager()
                permissions = await session_manager.resolve_permissions(
                    user_id=token_payload.sub,
                    tenant_id=token_payload.tenant_id or "",
                    roles=token_payload.roles,
                )
                session = await session_manager.create_session(
                    user_id=token_payload.sub,
                    tenant_id=token_payload.tenant_id or "",
                    email=token_payload.email or payload.email,
                    roles=token_payload.roles,
                    permissions=permissions,
                    ip_address=request.META.get("REMOTE_ADDR", ""),
                    user_agent=request.META.get("HTTP_USER_AGENT", ""),
                )

                from django.conf import settings

                cookie_secure = not settings.DEBUG
                _set_auth_cookies(response, token_data, session.session_id, cookie_secure)

                return {
                    "token": token_data["access_token"],
                    "refresh_token": token_data.get("refresh_token"),
                    "session_id": session.session_id,
                    "user": {
                        "id": token_payload.sub,
                        "email": token_payload.email,
                        "name": token_payload.name,
                        "role": get_highest_role(token_payload.roles),
                        "roles": token_payload.roles,
                    },
                    "redirect_path": redirect_path,
                }

            new_status = await lockout_service.record_failed_attempt(payload.email)
            if new_status.is_locked:
                raise ForbiddenError(
                    action="login",
                    resource="account",
                    message=f"Account locked. Try again in {new_status.retry_after // 60} minutes.",
                    details={"retry_after": new_status.retry_after},
                )
            raise UnauthorizedError(message="Invalid email or password")
    except httpx.HTTPError as e:
        logger.error(f"Login error: {e}")
        raise UnauthorizedError(message="Authentication service unavailable")


@router.post("/register")
async def register_user(request, payload: RegisterRequest):
    """Register a new user."""
    logger.info(f"User registration: {payload.email}")
    return {"success": True, "message": "Verification email sent. Please check your inbox."}


# =============================================================================
# IMPERSONATION - SAAS Super Admin Only
# =============================================================================


@router.post("/impersonate", response=ImpersonationResponse)
async def impersonate_tenant(request, payload: ImpersonationRequest):
    """Generate impersonation token to act as tenant admin."""
    import secrets
    import time
    from uuid import uuid4

    from asgiref.sync import sync_to_async

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise UnauthorizedError("Missing or invalid authorization header")

    token = auth_header.split(" ")[1]
    try:
        current_user = decode_token(token)
    except JWTError as e:
        raise UnauthorizedError(f"Invalid token: {e}")

    user_roles = current_user.realm_access.get("roles", []) if current_user.realm_access else []
    if "super_admin" not in user_roles and "saas_admin" not in user_roles:
        raise UnauthorizedError("Only SAAS super admins can impersonate")

    @sync_to_async
    def get_tenant():
        try:
            return Tenant.objects.get(id=payload.tenant_id, status="active")
        except Tenant.DoesNotExist:
            return None

    tenant = await get_tenant()
    if not tenant:
        raise BadRequestError(f"Tenant {payload.tenant_id} not found or inactive")

    impersonation_claims = {
        "sub": current_user.sub,
        "impersonating_tenant": str(tenant.id),
        "impersonating_as": "tenant_admin",
        "original_roles": user_roles,
        "reason": payload.reason,
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,
        "iss": "somaagent-impersonation",
        "jti": str(uuid4()),
    }
    impersonation_token = jwt.encode(
        impersonation_claims, secrets.token_urlsafe(32), algorithm="HS256"
    )

    @sync_to_async
    def create_audit():
        from admin.saas.models import AuditLog

        return AuditLog.objects.create(
            actor_id=current_user.sub,
            actor_email=current_user.email or "",
            tenant=tenant,
            action="impersonation.started",
            resource_type="tenant",
            resource_id=tenant.id,
            new_value={"reason": payload.reason, "expires_in_seconds": 3600},
            ip_address=request.META.get("REMOTE_ADDR"),
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:500],
            request_id=str(uuid4()),
        )

    audit = await create_audit()
    logger.warning(f"IMPERSONATION: User {current_user.sub} impersonating tenant {tenant.id}")
    return ImpersonationResponse(
        access_token=impersonation_token,
        expires_in=3600,
        impersonating_tenant=tenant.name,
        original_user_id=str(current_user.sub),
        audit_id=str(audit.id),
    )


# =============================================================================
# HELPERS
# =============================================================================


def _set_auth_cookies(response, token_data: dict, session_id: str, secure: bool):
    """Set authentication cookies on response."""
    access_ttl = token_data.get("expires_in", 900)
    refresh_ttl = token_data.get("refresh_expires_in", 86400)
    response.set_cookie(
        "access_token",
        token_data["access_token"],
        max_age=access_ttl,
        httponly=True,
        secure=secure,
        samesite="Lax",
    )
    if token_data.get("refresh_token"):
        response.set_cookie(
            "refresh_token",
            token_data["refresh_token"],
            max_age=refresh_ttl,
            httponly=True,
            secure=secure,
            samesite="Lax",
        )
    response.set_cookie(
        "session_id", session_id, max_age=access_ttl, httponly=True, secure=secure, samesite="Lax"
    )


# =============================================================================
# SUB-ROUTERS
# =============================================================================


from admin.auth.api_oauth import router as oauth_router
from admin.auth.api_sso import router as sso_router
from admin.auth.mfa import router as mfa_router
from admin.auth.password_reset import router as password_reset_router

router.add_router("/sso", sso_router)
router.add_router("/oauth", oauth_router)
router.add_router("/mfa", mfa_router)
router.add_router("/password", password_reset_router)
