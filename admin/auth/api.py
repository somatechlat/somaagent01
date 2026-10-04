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
from ninja.responses import Response as NinjaResponse

from admin.aaas.models import Tenant
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
    UserResponse,
)
from admin.common.auth import AuthBearer, as_uuid, decode_token, get_keycloak_config
from admin.common.exceptions import BadRequestError, ServiceUnavailableError, UnauthorizedError
from services.common.authorization import authorize
from admin.common.messages import get_message, SuccessCode
from services.common.http_timeouts import httpx_timeout  # noqa: E402

logger = logging.getLogger(__name__)
router = Router(tags=["Authentication"])


async def _emit_auth_audit(
    request,
    action: str,
    details: dict | None = None,
    actor_id: str = "",
    actor_email: str = "",
) -> None:
    """Emit audit event for auth failure. Best-effort: never blocks response."""
    from uuid import uuid4

    from asgiref.sync import sync_to_async

    try:
        from admin.aaas.models import AuditLog

        await sync_to_async(AuditLog.objects.create, thread_sensitive=False)(
            # NULL = no authenticated actor. A sentinel string cannot be
            # stored in a UUIDField; the write would raise and be swallowed.
            actor_id=actor_id or None,
            actor_email=actor_email or "",
            action=action,
            resource_type="auth",
            resource_id=None,
            new_value=details or {},
            ip_address=request.META.get("REMOTE_ADDR"),
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:500],
            request_id=str(uuid4()),
        )
    except Exception as exc:
        logger.warning("Auth audit logging failed: %s", exc)


# =============================================================================
# CORE ENDPOINTS
# =============================================================================


@router.post("/token")
async def get_token(request, payload: TokenRequest):
    """Get access token via password grant or OAuth code exchange."""
    config = get_keycloak_config()
    token_url = f"{config.server_url}/realms/{config.realm}/protocol/openid-connect/token"

    try:
        async with httpx.AsyncClient(timeout=httpx_timeout()) as client:
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

            cookie_secure = bool(
                request.is_secure()
                or request.META.get("HTTP_X_FORWARDED_PROTO", "").lower() == "https"
            )
            data = {
                "access_token": token_data["access_token"],
                "refresh_token": token_data.get("refresh_token"),
                "token_type": "Bearer",
                "expires_in": token_data.get("expires_in", 900),
                "redirect_path": redirect_path,
            }
            resp_obj = NinjaResponse(data, status=200)
            _set_auth_cookies(resp_obj, token_data, session.session_id, cookie_secure)
            return resp_obj
    except httpx.HTTPError as e:
        logger.error("Keycloak communication error: %s", e)
        await _emit_auth_audit(
            request,
            action="auth.token_failed",
            details={
                "error": "Authentication service unavailable",
                "grant_type": payload.grant_type,
            },
        )
        raise UnauthorizedError(message="Authentication service unavailable")


@router.post("/refresh")
async def refresh_token(request, payload: RefreshRequest):
    """Refresh access token using refresh token."""
    config = get_keycloak_config()
    refresh_token_val = payload.refresh_token or request.COOKIES.get("refresh_token")
    if not refresh_token_val:
        await _emit_auth_audit(
            request,
            action="auth.refresh_failed",
            details={"error": "Refresh token required"},
        )
        raise BadRequestError(message="Refresh token required")

    token_url = f"{config.server_url}/realms/{config.realm}/protocol/openid-connect/token"
    try:
        async with httpx.AsyncClient(timeout=httpx_timeout()) as client:
            resp = await client.post(
                token_url,
                data={
                    "grant_type": "refresh_token",
                    "client_id": config.client_id,
                    "refresh_token": refresh_token_val,
                },
            )
            if resp.status_code != 200:
                await _emit_auth_audit(
                    request,
                    action="auth.refresh_failed",
                    details={
                        "error": "Invalid or expired refresh token",
                        "status_code": resp.status_code,
                    },
                )
                raise UnauthorizedError(message="Invalid or expired refresh token")
            token_data = resp.json()
            token_payload = await decode_token(token_data["access_token"])

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

            cookie_secure = bool(
                request.is_secure()
                or request.META.get("HTTP_X_FORWARDED_PROTO", "").lower() == "https"
            )
            data = {
                "access_token": token_data["access_token"],
                "refresh_token": token_data.get("refresh_token"),
                "token_type": "Bearer",
                "expires_in": token_data.get("expires_in", 900),
                "redirect_path": "/chat",
            }
            resp_obj = NinjaResponse(data, status=200)
            _set_auth_cookies(resp_obj, token_data, session_id, cookie_secure)
            return resp_obj
    except httpx.HTTPError as e:
        logger.error("Token refresh error: %s", e)
        await _emit_auth_audit(
            request,
            action="auth.refresh_failed",
            details={"error": "Token refresh failed"},
        )
        raise UnauthorizedError(message="Token refresh failed")


@router.get("/me", response=UserResponse, auth=AuthBearer())
async def get_current_user(request):
    """Get current authenticated user info."""
    # Self-service: acts on the caller's own principal. Identity, not elevated authority.
    await authorize(request, action="identity:self", resource="identity")
    # Check Authorization header first, then httpOnly cookie fallback
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
    else:
        token = request.COOKIES.get("access_token", "")
    if not token:
        await _emit_auth_audit(
            request,
            action="auth.me_failed",
            details={"error": "No token in header or cookie"},
        )
        raise UnauthorizedError()
    try:
        payload = await decode_token(token)
        config = get_keycloak_config()
        async with httpx.AsyncClient(timeout=httpx_timeout()) as client:
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
        await _emit_auth_audit(
            request,
            action="auth.me_failed",
            details={"error": "Invalid token"},
        )
        raise UnauthorizedError(message="Invalid token")


@router.post("/logout", auth=AuthBearer())
async def logout(request):
    """Logout and revoke tokens."""
    # Self-service: acts on the caller's own principal. Identity, not elevated authority.
    await authorize(request, action="identity:self", resource="identity")
    refresh_token = request.POST.get("refresh_token") or request.COOKIES.get("refresh_token")
    config = get_keycloak_config()
    logout_url = f"{config.server_url}/realms/{config.realm}/protocol/openid-connect/logout"
    try:
        async with httpx.AsyncClient(timeout=httpx_timeout()) as client:
            if refresh_token:
                await client.post(
                    logout_url, data={"client_id": config.client_id, "refresh_token": refresh_token}
                )
    except httpx.HTTPError:
        pass

    # Clear auth cookies
    from django.http import JsonResponse

    response = JsonResponse({"success": True})
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    response.delete_cookie("session_id")

    return response


# =============================================================================
# LOGIN ENDPOINT
# =============================================================================


async def _login_local(request, payload: "LoginRequest", lockout_service):
    """Standalone login: LocalIdentity is the authority.

    The session token is the session id - `_decode_session` resolves it and
    re-reads roles and permissions from the identity on every request, so a
    stale row cannot carry a stale grant.
    """
    from admin.auth.identity import authenticate_local
    from admin.common.session_manager import get_session_manager

    identity = await authenticate_local(payload.email, payload.password)
    logger.warning('LOCAL_LOGIN email=%s ok=%s reason=%s', payload.email, identity.ok, identity.reason)
    if not identity.ok:
        new_status = await lockout_service.record_failed_attempt(payload.email)
        await _emit_auth_audit(
            request,
            action="auth.login_failed",
            details={"error": identity.reason},
            actor_email=payload.email,
        )
        if new_status.is_locked:
            raise ForbiddenError(
                action="login",
                resource="account",
                message=f"Account locked. Try again in {(new_status.retry_after or 0) // 60} minutes.",
                details={"retry_after": new_status.retry_after},
            )
        raise UnauthorizedError(message="Invalid email or password")

    await lockout_service.record_successful_login(payload.email)

    # Mint a real local session. `generate_session_token` returns the raw
    # bearer (shown to the client once) and its hash (the only thing stored).
    # decode_token classifies on shape - `ses_` is what routes a bearer to the
    # local-session stack instead of the JWT stack.
    from asgiref.sync import sync_to_async

    from admin.aaas.models.session import LocalSession
    from services.common.identity.session import generate_session_token

    raw_token, token_hash = generate_session_token()

    @sync_to_async
    def _open_session() -> str:
        from django.utils import timezone

        now = timezone.now()
        # LocalSession has no expires_at column: is_valid() derives the
        # absolute window from created_at and the idle window from
        # last_seen_at. Both are required and NOT NULL.
        LocalSession.objects.create(
            token_hash=token_hash,
            principal_id=identity.principal_id,
            created_at=now,
            last_seen_at=now,
            revoked=False,
            privileged=False,
        )
        return identity.principal_id

    principal = await _open_session()
    await _emit_auth_audit(
        request,
        action="auth.login_succeeded",
        details={"provider": "local"},
        actor_email=identity.email,
    )

    from django.http import JsonResponse

    fwd_proto = request.META.get("HTTP_X_FORWARDED_PROTO", "")
    cookie_secure = bool(request.is_secure() or fwd_proto.lower() == "https")
    resp_obj = JsonResponse(
        status=200,
        data={
            "token": raw_token,
            "refresh_token": None,
            "session_id": principal,
            "redirect_path": "/chat",
            "user": {
                "id": identity.email,
                "email": identity.email,
                "name": identity.display_name,
                "role": "member",
                "roles": [],
            },
        },
    )
    # path="/" is load-bearing: without it Django scopes the cookie to the
    # request path (/api/v2/auth/) and /chat never sees it, so checkAuth()
    # bounces straight back to the login screen.
    resp_obj.set_cookie(
        "access_token",
        raw_token,
        max_age=3600,
        path="/",
        httponly=True,
        secure=cookie_secure,
        samesite="Lax",
    )
    return resp_obj


@router.post("/login")
async def login_with_email(request, payload: LoginRequest):
    """Login with email and password with account lockout protection."""
    from admin.common.account_lockout import get_lockout_service
    from admin.common.exceptions import ForbiddenError
    from admin.common.rate_limit import check_rate_limit
    from admin.common.session_manager import get_session_manager

    client_ip = request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[
        0
    ].strip() or request.META.get("REMOTE_ADDR", "unknown")
    await check_rate_limit(client_ip, "/api/v2/auth/login")

    lockout_service = await get_lockout_service()
    lockout_status = await lockout_service.check_lockout(payload.email)
    if lockout_status.is_locked:
        await _emit_auth_audit(
            request,
            action="auth.login_failed",
            details={"error": "Account locked", "retry_after": lockout_status.retry_after},
            actor_email=payload.email,
        )
        raise ForbiddenError(
            action="login",
            resource="account",
            message=f"Account locked. Try again in {(lockout_status.retry_after or 0) // 60} minutes.",
            details={"retry_after": lockout_status.retry_after},
        )

    # Exactly one authority answers (see admin.auth.identity).
    #
    #   STANDALONE  -> LocalIdentity. The agent holds the credential; there is
    #                  no identity provider and none is consulted.
    #   ENTERPRISE  -> Keycloak password grant. This process never stores it.
    #
    # Never both, and never a fallback between them: falling through from a
    # federated rejection to a local check would let a disabled cloud account
    # be resurrected by a stale local row.
    from admin.auth.identity import resolve_identity_provider

    if resolve_identity_provider() == "local":
        return await _login_local(request, payload, lockout_service)

    config = get_keycloak_config()
    token_url = f"{config.server_url}/realms/{config.realm}/protocol/openid-connect/token"

    try:
        async with httpx.AsyncClient(timeout=httpx_timeout()) as client:
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

                # Secure cookies only on real HTTPS. Local HTTP (Docker/dev)
                # must use Secure=False or browsers drop the session and /chat
                # bounces to login.
                fwd_proto = request.META.get("HTTP_X_FORWARDED_PROTO", "")
                cookie_secure = bool(request.is_secure() or fwd_proto.lower() == "https")

                data = {
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
                resp_obj = NinjaResponse(data, status=200)
                access_ttl = token_data.get("expires_in", 900)
                refresh_ttl = token_data.get("refresh_expires_in", 86400)
                resp_obj.set_cookie(
                    "access_token",
                    token_data["access_token"],
                    max_age=access_ttl,
                    httponly=True,
                    secure=cookie_secure,
                    samesite="Lax",
                )
                if token_data.get("refresh_token"):
                    resp_obj.set_cookie(
                        "refresh_token",
                        token_data["refresh_token"],
                        max_age=refresh_ttl,
                        httponly=True,
                        secure=cookie_secure,
                        samesite="Lax",
                    )
                resp_obj.set_cookie(
                    "session_id",
                    session.session_id,
                    max_age=access_ttl,
                    httponly=True,
                    secure=cookie_secure,
                    samesite="Lax",
                )
                return resp_obj

            new_status = await lockout_service.record_failed_attempt(payload.email)
            if new_status.is_locked:
                await _emit_auth_audit(
                    request,
                    action="auth.login_failed",
                    details={
                        "error": "Account locked after failed attempt",
                        "retry_after": new_status.retry_after,
                    },
                    actor_email=payload.email,
                )
                raise ForbiddenError(
                    action="login",
                    resource="account",
                    message=f"Account locked. Try again in {(new_status.retry_after or 0) // 60} minutes.",
                    details={"retry_after": new_status.retry_after},
                )
            await _emit_auth_audit(
                request,
                action="auth.login_failed",
                details={"error": "Invalid email or password"},
                actor_email=payload.email,
            )
            raise UnauthorizedError(message="Invalid email or password")
    except httpx.HTTPError as e:
        logger.error("Login error: %s", e)
        await _emit_auth_audit(
            request,
            action="auth.login_failed",
            details={"error": "Authentication service unavailable"},
        )
        raise UnauthorizedError(message="Authentication service unavailable")


@router.post("/register")
async def register_user(request, payload: RegisterRequest):
    """Register a new user via Keycloak."""
    config = get_keycloak_config()
    logger.info("User registration: %s", payload.email)

    # Get admin token from Keycloak
    admin_token_url = f"{config.server_url}/realms/master/protocol/openid-connect/token"
    users_url = f"{config.server_url}/admin/realms/{config.realm}/users"

    try:
        # VIBE Rule 164: the Keycloak admin password is a credential and comes
        # from Vault, never from request.META. META is the CGI environment of
        # the request — reading a password out of it means the password was in
        # the process environment, which is exactly the model Rule 164 forbids.
        # The trailing default of "" was worse still: it authenticated to
        # Keycloak with a blank password rather than reporting a missing secret.
        from services.common.unified_secret_manager import get_secret_manager

        admin_password = get_secret_manager().get_credential("keycloak_admin_password")
        if not admin_password:
            logger.error("Keycloak admin password is not configured in Vault")
            raise ServiceUnavailableError(
                "auth",
                "Identity service is not configured "
                "(secret/agent/credentials/keycloak_admin_password)",
            )

        async with httpx.AsyncClient(timeout=httpx_timeout()) as client:
            # Get admin access token
            admin_resp = await client.post(
                admin_token_url,
                data={
                    "grant_type": "password",
                    "client_id": "admin-cli",
                    "username": "admin",
                    "password": admin_password,
                },
            )
            if admin_resp.status_code != 200:
                logger.error("Keycloak admin auth failed: %s", admin_resp.status_code)
                raise ServiceUnavailableError("auth", "Identity service unavailable")

            admin_token = admin_resp.json()["access_token"]

            # Create user in Keycloak
            create_resp = await client.post(
                users_url,
                json={
                    "username": payload.email,
                    "email": payload.email,
                    "firstName": payload.email.split("@")[0],
                    "enabled": True,
                    "emailVerified": False,
                    "credentials": [
                        {
                            "type": "password",
                            "value": payload.password,
                            "temporary": False,
                        }
                    ],
                },
                headers={"Authorization": f"Bearer {admin_token}"},
            )

            if create_resp.status_code == 201:
                logger.info("User registered in Keycloak: %s", payload.email)
                await _emit_auth_audit(
                    request,
                    action="auth.registered",
                    actor_email=payload.email,
                )
                return {
                    "success": True,
                    "message": get_message(SuccessCode.VERIFICATION_EMAIL_SENT),
                }
            elif create_resp.status_code == 409:
                await _emit_auth_audit(
                    request,
                    action="auth.register_failed",
                    details={"reason": "user_exists"},
                    actor_email=payload.email,
                )
                raise BadRequestError("User already exists")
            else:
                logger.error(
                    "Keycloak user creation failed: %s %s",
                    create_resp.status_code,
                    create_resp.text,
                )
                await _emit_auth_audit(
                    request,
                    action="auth.register_failed",
                    details={"reason": "keycloak_rejected"},
                    actor_email=payload.email,
                )
                raise ServiceUnavailableError("auth", "User registration failed")

    except httpx.HTTPError as e:
        logger.error("Keycloak communication error during registration: %s", e)
        await _emit_auth_audit(
            request,
            action="auth.register_failed",
            details={"reason": "identity_service_unavailable"},
            actor_email=payload.email,
        )
        raise ServiceUnavailableError("auth", "Identity service unavailable")


# =============================================================================
# IMPERSONATION - AAAS Super Admin Only
# =============================================================================


@router.post("/impersonate", response=ImpersonationResponse, auth=AuthBearer())
async def impersonate_tenant(request, payload: ImpersonationRequest):
    """Generate impersonation token to act as tenant admin."""
    import time
    from uuid import uuid4

    from asgiref.sync import sync_to_async

    # The old check here looked for Keycloak realm roles named `super_admin` or
    # `aaas_admin`. Neither is a permission this product defines, so the gate
    # was authority invented outside the catalog — and realm names drift from
    # ours the moment an operator renames a Keycloak role. The catalog decides.
    await authorize(request, action="system:impersonate", resource="tenant")
    current_user = request.auth
    user_roles = list(getattr(current_user, "roles", None) or [])

    @sync_to_async
    def get_tenant():
        try:
            return Tenant.objects.get(id=payload.tenant_id, status="active")
        except Tenant.DoesNotExist:
            return None

    tenant = await get_tenant()
    if not tenant:
        raise BadRequestError(f"Tenant {payload.tenant_id} not found or inactive")

    from django.conf import settings

    # VIBE SECURITY: Impersonation JWT MUST use a dedicated secret.
    # NEVER fall back to Django SECRET_KEY — if impersonation secret is compromised,
    # it must NOT compromise session cookies / CSRF tokens.
    impersonation_secret = getattr(settings, "IMPERSONATION_JWT_SECRET", None)
    if not impersonation_secret:
        raise UnauthorizedError(
            "Impersonation disabled: IMPERSONATION_JWT_SECRET not configured. "
            "Set it in your environment or Vault."
        )

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
    impersonation_token = jwt.encode(impersonation_claims, impersonation_secret, algorithm="HS256")

    @sync_to_async
    def create_audit():
        from admin.aaas.models import AuditLog

        return AuditLog.objects.create(
            actor_id=as_uuid(current_user.sub),
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
    logger.warning("IMPERSONATION: User %s impersonating tenant %s", current_user.sub, tenant.id)
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
    """Set authentication cookies on response.

    ``secure`` must be False on plain HTTP (localhost Docker) or browsers
    drop the session and /chat redirects to login.
    """
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

router.add_router("/sso", sso_router)
router.add_router("/oauth", oauth_router)
router.add_router("/mfa", mfa_router)
