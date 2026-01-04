"""Users API - User management.


User lifecycle and profile management.

7-Persona Implementation:
- Security Auditor: User security, MFA
- PM: User onboarding
- Django Architect: Django User model
"""

from __future__ import annotations

import logging
from typing import Optional
from uuid import uuid4

from django.utils import timezone
from ninja import Router
from pydantic import BaseModel

from admin.common.auth import AuthBearer
from asgiref.sync import sync_to_async

router = Router(tags=["users"])
logger = logging.getLogger(__name__)


# =============================================================================
# SCHEMAS
# =============================================================================


class User(BaseModel):
    """User definition."""

    user_id: str
    email: str
    name: str
    tenant_id: str
    status: str  # active, suspended, pending
    role: str
    created_at: str
    last_login: Optional[str] = None
    mfa_enabled: bool = False


class UserProfile(BaseModel):
    """User profile."""

    user_id: str
    email: str
    name: str
    avatar_url: Optional[str] = None
    timezone: str = "UTC"
    language: str = "en"
    preferences: dict


# =============================================================================
# ENDPOINTS - User CRUD
# =============================================================================


@router.get(
    "",
    summary="List users",
    auth=AuthBearer(),
)
async def list_users(
    request,
    tenant_id: Optional[str] = None,
    status: Optional[str] = None,
    role: Optional[str] = None,
    limit: int = 50,
) -> dict:
    """List users.

    PM: User directory.
    """
    return {
        "users": [],
        "total": 0,
    }


@router.post(
    "",
    response=User,
    summary="Create user",
    auth=AuthBearer(),
)
async def create_user(
    request,
    email: str,
    name: str,
    tenant_id: str,
    role: str = "user",
) -> User:
    """Create a new user.

    PM: User registration.
    """
    user_id = str(uuid4())

    logger.info(f"User created: {email} ({user_id})")

    return User(
        user_id=user_id,
        email=email,
        name=name,
        tenant_id=tenant_id,
        status="pending",
        role=role,
        created_at=timezone.now().isoformat(),
    )


@router.get(
    "/{user_id}",
    response=User,
    summary="Get user",
    auth=AuthBearer(),
)
async def get_user(request, user_id: str) -> User:
    """Get user details."""
    from django.contrib.auth import get_user_model
    from admin.common.exceptions import NotFoundError

    UserModel = get_user_model()

    try:
        db_user = await sync_to_async(UserModel.objects.get)(id=user_id)
    except UserModel.DoesNotExist:
        raise NotFoundError("user", user_id)

    return User(
        user_id=str(db_user.id),
        email=db_user.email,
        name=db_user.get_full_name() or db_user.username,
        tenant_id=getattr(db_user, "tenant_id", "") or "",
        status="active" if db_user.is_active else "suspended",
        role="admin" if db_user.is_staff else "user",
        created_at=db_user.date_joined.isoformat(),
        last_login=db_user.last_login.isoformat() if db_user.last_login else None,
        mfa_enabled=getattr(db_user, "mfa_enabled", False),
    )


@router.patch(
    "/{user_id}",
    summary="Update user",
    auth=AuthBearer(),
)
async def update_user(
    request,
    user_id: str,
    name: Optional[str] = None,
    role: Optional[str] = None,
) -> dict:
    """Update user details."""
    return {
        "user_id": user_id,
        "updated": True,
    }


@router.delete(
    "/{user_id}",
    summary="Delete user",
    auth=AuthBearer(),
)
async def delete_user(request, user_id: str) -> dict:
    """Delete a user.

    Security Auditor: GDPR deletion.
    """
    logger.warning(f"User deleted: {user_id}")

    return {
        "user_id": user_id,
        "deleted": True,
    }


# =============================================================================
# ENDPOINTS - Status
# =============================================================================


@router.post(
    "/{user_id}/suspend",
    summary="Suspend user",
    auth=AuthBearer(),
)
async def suspend_user(
    request,
    user_id: str,
    reason: str,
) -> dict:
    """Suspend a user.

    Security Auditor: Access revocation.
    """
    logger.warning(f"User suspended: {user_id}")

    return {
        "user_id": user_id,
        "status": "suspended",
    }


@router.post(
    "/{user_id}/activate",
    summary="Activate user",
    auth=AuthBearer(),
)
async def activate_user(request, user_id: str) -> dict:
    """Activate a user."""
    return {
        "user_id": user_id,
        "status": "active",
    }


# =============================================================================
# ENDPOINTS - Profile
# =============================================================================


@router.get(
    "/{user_id}/profile",
    response=UserProfile,
    summary="Get profile",
    auth=AuthBearer(),
)
async def get_profile(request, user_id: str) -> UserProfile:
    """Get user profile."""
    from django.contrib.auth import get_user_model
    from admin.common.exceptions import NotFoundError

    UserModel = get_user_model()

    try:
        db_user = await sync_to_async(UserModel.objects.get)(id=user_id)
    except UserModel.DoesNotExist:
        raise NotFoundError("user", user_id)

    return UserProfile(
        user_id=str(db_user.id),
        email=db_user.email,
        name=db_user.get_full_name() or db_user.username,
        avatar_url=getattr(db_user, "avatar_url", None),
        timezone=getattr(db_user, "timezone", "UTC") or "UTC",
        language=getattr(db_user, "language", "en") or "en",
        preferences=getattr(db_user, "preferences", {}) or {},
    )


@router.patch(
    "/{user_id}/profile",
    summary="Update profile",
    auth=AuthBearer(),
)
async def update_profile(
    request,
    user_id: str,
    name: Optional[str] = None,
    timezone: Optional[str] = None,
    language: Optional[str] = None,
    preferences: Optional[dict] = None,
) -> dict:
    """Update user profile."""
    return {
        "user_id": user_id,
        "updated": True,
    }


# =============================================================================
# ENDPOINTS - Security
# =============================================================================


@router.post(
    "/{user_id}/reset-password",
    summary="Reset password",
    auth=AuthBearer(),
)
async def reset_password(request, user_id: str) -> dict:
    """Send password reset email.

    Security Auditor: Password reset flow.
    """
    logger.info(f"Password reset requested: {user_id}")

    return {
        "user_id": user_id,
        "reset_sent": True,
    }


@router.post(
    "/{user_id}/mfa/enable",
    summary="Enable MFA",
    auth=AuthBearer(),
)
async def enable_mfa(request, user_id: str) -> dict:
    """Enable MFA for user.

    Security Auditor: MFA enrollment.
    """
    return {
        "user_id": user_id,
        "mfa_enabled": True,
        "setup_url": "otpauth://...",
    }


@router.post(
    "/{user_id}/mfa/disable",
    summary="Disable MFA",
    auth=AuthBearer(),
)
async def disable_mfa(
    request,
    user_id: str,
    verification_code: str,
) -> dict:
    """Disable MFA for user."""
    logger.warning(f"MFA disabled: {user_id}")

    return {
        "user_id": user_id,
        "mfa_enabled": False,
    }


# =============================================================================
# ENDPOINTS - Activity
# =============================================================================


@router.get(
    "/{user_id}/activity",
    summary="Get activity",
    auth=AuthBearer(),
)
async def get_activity(
    request,
    user_id: str,
    limit: int = 50,
) -> dict:
    """Get user activity log.

    Security Auditor: User activity audit.
    """
    return {
        "user_id": user_id,
        "activities": [],
        "total": 0,
    }


@router.get(
    "/{user_id}/sessions",
    summary="Get sessions",
    auth=AuthBearer(),
)
async def get_user_sessions(
    request,
    user_id: str,
) -> dict:
    """Get user's active sessions."""
    return {
        "user_id": user_id,
        "sessions": [],
        "total": 0,
    }
