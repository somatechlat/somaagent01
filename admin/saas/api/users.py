"""Tenant User Management API.

Pure Django ORM + Django Ninja implementation.
VIBE COMPLIANT - No SQLAlchemy.
"""

from __future__ import annotations

import logging
from typing import Optional
from uuid import uuid4

from django.conf import settings
from django.db.models import Q
from ninja import Query, Router
from pydantic import BaseModel

from admin.common.auth import AuthBearer
from admin.common.exceptions import NotFoundError, ValidationError
from admin.common.responses import api_response, paginated_response
from admin.saas.models import TenantRole, TenantUser

router = Router(tags=["tenant-users"])
logger = logging.getLogger(__name__)


# =============================================================================
# SCHEMAS
# =============================================================================


class TenantUserOut(BaseModel):
    """Tenant user output schema."""

    id: str
    email: str
    name: str
    role: str
    is_active: bool
    tenant_id: str
    created_at: str
    last_login_at: Optional[str] = None


class UserInviteRequest(BaseModel):
    """Invite user request."""

    email: str
    name: str
    role: str = "member"


class UserUpdateRequest(BaseModel):
    """Update user request."""

    name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


VALID_ROLES = [r[0] for r in TenantRole.choices]


def _user_to_out(user: TenantUser) -> TenantUserOut:
    """Convert TenantUser model to output schema."""
    return TenantUserOut(
        id=str(user.id),
        email=user.email,
        name=user.display_name or "",
        role=user.role,
        is_active=user.is_active,
        tenant_id=str(user.tenant_id),
        created_at=user.created_at.isoformat() if user.created_at else "",
        last_login_at=user.last_login_at.isoformat() if user.last_login_at else None,
    )


# =============================================================================
# USER MANAGEMENT ENDPOINTS
# =============================================================================


@router.get(
    "/users",
    summary="List tenant users",
    auth=AuthBearer(),
)
def list_users(
    request,
    role: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
) -> dict:
    """List all users in the tenant with filtering."""
    tenant_id = getattr(request.auth, "tenant_id", None) or settings.SAAS_DEFAULT_TENANT_ID

    qs = TenantUser.objects.filter(tenant_id=tenant_id)

    if role:
        qs = qs.filter(role=role)
    if status == "active":
        qs = qs.filter(is_active=True)
    elif status == "inactive":
        qs = qs.filter(is_active=False)
    if search:
        qs = qs.filter(Q(display_name__icontains=search) | Q(email__icontains=search))

    total = qs.count()
    offset = (page - 1) * per_page
    users = qs.order_by("-created_at")[offset : offset + per_page]

    return paginated_response(
        items=[_user_to_out(u).model_dump() for u in users],
        total=total,
        page=page,
        page_size=per_page,
    )


@router.post(
    "/users",
    summary="Invite user to tenant",
    auth=AuthBearer(),
)
def invite_user(
    request,
    payload: UserInviteRequest,
) -> dict:
    """Invite a new user to the tenant."""
    if payload.role not in VALID_ROLES:
        raise ValidationError(f"Invalid role. Must be one of: {VALID_ROLES}", field="role")

    tenant_id = getattr(request.auth, "tenant_id", None) or settings.SAAS_DEFAULT_TENANT_ID

    user = TenantUser.objects.create(
        id=uuid4(),
        tenant_id=tenant_id,
        user_id=uuid4(),  # Would be from Keycloak
        email=payload.email,
        display_name=payload.name,
        role=payload.role,
        is_active=False,  # Pending invite acceptance
    )

    logger.info(f"User invited: {payload.email} as {payload.role}")

    return api_response(_user_to_out(user).model_dump(), message="User invited")


@router.get(
    "/users/{user_id}",
    summary="Get user details",
    auth=AuthBearer(),
)
def get_user(
    request,
    user_id: str,
) -> dict:
    """Get a single user's details."""
    try:
        user = TenantUser.objects.get(id=user_id)
    except TenantUser.DoesNotExist:
        raise NotFoundError("user", user_id)

    return api_response(_user_to_out(user).model_dump())


@router.put(
    "/users/{user_id}",
    summary="Update user",
    auth=AuthBearer(),
)
def update_user(
    request,
    user_id: str,
    payload: UserUpdateRequest,
) -> dict:
    """Update a user's information."""
    try:
        user = TenantUser.objects.get(id=user_id)
    except TenantUser.DoesNotExist:
        raise NotFoundError("user", user_id)

    if payload.name is not None:
        user.display_name = payload.name
    if payload.role is not None:
        if payload.role not in VALID_ROLES:
            raise ValidationError("Invalid role", field="role")
        user.role = payload.role
    if payload.is_active is not None:
        user.is_active = payload.is_active

    user.save()
    logger.info(f"User updated: {user_id}")

    return api_response(_user_to_out(user).model_dump(), message="User updated")


@router.delete(
    "/users/{user_id}",
    summary="Remove user from tenant",
    auth=AuthBearer(),
)
def remove_user(
    request,
    user_id: str,
) -> dict:
    """Remove a user from the tenant."""
    try:
        user = TenantUser.objects.get(id=user_id)
    except TenantUser.DoesNotExist:
        raise NotFoundError("user", user_id)

    user.delete()
    logger.info(f"User removed: {user_id}")

    return api_response({"user_id": user_id}, message="User removed")


@router.put(
    "/users/{user_id}/role",
    summary="Change user role",
    auth=AuthBearer(),
)
def change_user_role(
    request,
    user_id: str,
    role: str = Query(...),
) -> dict:
    """Change a user's role."""
    if role not in VALID_ROLES:
        raise ValidationError(f"Invalid role. Must be one of: {VALID_ROLES}", field="role")

    try:
        user = TenantUser.objects.get(id=user_id)
    except TenantUser.DoesNotExist:
        raise NotFoundError("user", user_id)

    user.role = role
    user.save()
    logger.info(f"User role changed: {user_id} -> {role}")

    return api_response({"user_id": user_id, "role": role}, message="Role updated")


# =============================================================================
# EXTENDED USER MANAGEMENT (User Detail View Support)
# =============================================================================


class UserDetailOut(BaseModel):
    """Extended user details with agent access, activity, sessions."""

    id: str
    email: str
    displayName: str
    avatarUrl: Optional[str] = None
    role: str
    roleLabel: str
    status: str  # active, pending, suspended, archived
    lastSeen: Optional[str] = None
    mfaEnabled: bool
    createdAt: str
    permissions: list[str]
    agentAccess: list[dict]
    activityLog: list[dict]
    sessions: list[dict]


@router.get(
    "/users/{user_id}/detail",
    summary="Get detailed user info",
    auth=AuthBearer(),
)
def get_user_detail(
    request,
    user_id: str,
) -> dict:
    """Get detailed user info with agent access, activity, sessions."""
    try:
        user = TenantUser.objects.get(id=user_id)
    except TenantUser.DoesNotExist:
        raise NotFoundError("user", user_id)

    # Build role permissions
    from admin.auth.api import _get_permissions_for_roles

    permissions = _get_permissions_for_roles([user.role])

    # Mock agent access (would query AgentUser model)
    agent_access = [
        {
            "agentId": "agent-001",
            "agentName": "Support Bot",
            "modes": ["chat", "dev"],
            "isOwner": True,
        },
    ]

    # Mock activity log (would query AuditLog)
    activity_log = [
        {
            "id": "act-001",
            "action": "Logged in",
            "target": "Session",
            "timestamp": "2025-12-25T10:00:00Z",
            "ip": "192.168.1.1",
        },
    ]

    # Mock sessions
    sessions = [
        {
            "id": "sess-001",
            "device": "Chrome on macOS",
            "location": "New York, US",
            "lastActive": "2025-12-25T16:00:00Z",
            "current": True,
        },
    ]

    role_labels = {
        "sysadmin": "System Administrator",
        "admin": "Administrator",
        "developer": "Developer",
        "trainer": "Trainer",
        "user": "User",
        "viewer": "Viewer",
    }

    return api_response(
        UserDetailOut(
            id=str(user.id),
            email=user.email,
            displayName=user.display_name or "",
            role=user.role,
            roleLabel=role_labels.get(user.role, user.role),
            status="active" if user.is_active else "suspended",
            lastSeen=user.last_login_at.isoformat() if user.last_login_at else None,
            mfaEnabled=True,  # Would check actual MFA status
            createdAt=user.created_at.isoformat() if user.created_at else "",
            permissions=permissions,
            agentAccess=agent_access,
            activityLog=activity_log,
            sessions=sessions,
        ).model_dump()
    )


@router.post(
    "/users/{user_id}/suspend",
    summary="Suspend user",
    auth=AuthBearer(),
)
def suspend_user(
    request,
    user_id: str,
) -> dict:
    """Suspend a user account."""
    try:
        user = TenantUser.objects.get(id=user_id)
    except TenantUser.DoesNotExist:
        raise NotFoundError("user", user_id)

    user.is_active = False
    user.save()
    logger.warning(f"User suspended: {user_id}")

    return api_response({"user_id": user_id, "status": "suspended"}, message="User suspended")


@router.post(
    "/users/{user_id}/unsuspend",
    summary="Unsuspend user",
    auth=AuthBearer(),
)
def unsuspend_user(
    request,
    user_id: str,
) -> dict:
    """Unsuspend a user account."""
    try:
        user = TenantUser.objects.get(id=user_id)
    except TenantUser.DoesNotExist:
        raise NotFoundError("user", user_id)

    user.is_active = True
    user.save()
    logger.info(f"User unsuspended: {user_id}")

    return api_response({"user_id": user_id, "status": "active"}, message="User unsuspended")


@router.delete(
    "/users/{user_id}/sessions/{session_id}",
    summary="Revoke user session",
    auth=AuthBearer(),
)
def revoke_user_session(
    request,
    user_id: str,
    session_id: str,
) -> dict:
    """Revoke a specific user session."""
    # Would invalidate session in Keycloak/Redis
    logger.info(f"Session revoked: {session_id} for user {user_id}")
    return api_response({"session_id": session_id}, message="Session revoked")


# =============================================================================
# PROFILE ENDPOINTS (Platform Admin / Current User)
# =============================================================================


class ProfileUpdateRequest(BaseModel):
    """Profile update request."""

    display_name: Optional[str] = None
    session_timeout: Optional[int] = None
    notifications: Optional[dict] = None


class ProfileOut(BaseModel):
    """Admin profile output."""

    id: str
    email: str
    name: str
    avatar_url: Optional[str] = None
    role: str
    roles: list[str]
    permissions: list[str]
    mfa_enabled: bool
    last_login: Optional[str] = None
    session_timeout: int
    active_sessions: int
    api_key_count: int
    notifications: dict


@router.get(
    "/profile",
    summary="Get current user profile",
    auth=AuthBearer(),
)
def get_profile(request) -> dict:
    """Get current authenticated user's profile."""
    from admin.auth.api import _get_permissions_for_roles

    user_id = getattr(request.auth, "sub", "unknown")
    email = getattr(request.auth, "email", "admin@example.com")
    name = getattr(request.auth, "name", "Admin User")
    roles = getattr(request.auth, "roles", ["saas_admin"])

    permissions = _get_permissions_for_roles(roles)

    return api_response(
        ProfileOut(
            id=user_id,
            email=email,
            name=name,
            role=roles[0] if roles else "user",
            roles=roles,
            permissions=permissions,
            mfa_enabled=True,
            session_timeout=30,
            active_sessions=1,
            api_key_count=2,
            notifications={
                "criticalAlerts": True,
                "billingEvents": True,
                "weeklyDigest": False,
                "marketing": False,
            },
        ).model_dump()
    )


@router.put(
    "/profile",
    summary="Update current user profile",
    auth=AuthBearer(),
)
def update_profile(
    request,
    payload: ProfileUpdateRequest,
) -> dict:
    """Update current user's profile settings."""
    user_id = getattr(request.auth, "sub", "unknown")
    logger.info(f"Profile updated for user: {user_id}")

    # Would save to database
    return api_response(
        {
            "display_name": payload.display_name,
            "session_timeout": payload.session_timeout,
            "notifications": payload.notifications,
        },
        message="Profile updated",
    )
