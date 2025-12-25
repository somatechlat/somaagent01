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
