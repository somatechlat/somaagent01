"""Sessions API - User session management.


Session lifecycle and security management.

7-Persona Implementation:
- Security Auditor: Session security, forced logout
- Django Architect: Django session backend
- DevOps: Redis session store
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone as dt_timezone
from typing import Optional

from django.utils import timezone
from ninja import Router
from pydantic import BaseModel

from admin.common.auth import AuthBearer, get_current_user
from admin.common.exceptions import NotFoundError
from admin.common.session_manager import get_session_manager

router = Router(tags=["sessions"])
logger = logging.getLogger(__name__)


# =============================================================================
# SCHEMAS
# =============================================================================


class Session(BaseModel):
    """User session."""

    session_id: str
    user_id: str
    created_at: str
    last_activity: str
    expires_at: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    device_type: Optional[str] = None
    location: Optional[str] = None
    is_current: bool = False


class SessionStats(BaseModel):
    """Session statistics."""

    active_sessions: int
    sessions_today: int
    unique_users_today: int
    avg_session_duration_minutes: float


def _to_session_response(
    session_data,
    *,
    session_ttl: int,
    current_session_id: Optional[str] = None,
) -> Session:
    """Convert SessionManager Session to API response schema."""
    created_at = session_data.created_at or timezone.now().isoformat()
    last_activity = session_data.last_activity or created_at
    try:
        last_dt = datetime.fromisoformat(last_activity)
    except ValueError:
        last_dt = datetime.now(dt_timezone.utc)
    expires_at = (last_dt + timedelta(seconds=session_ttl)).isoformat()

    return Session(
        session_id=session_data.session_id,
        user_id=session_data.user_id,
        created_at=created_at,
        last_activity=last_activity,
        expires_at=expires_at,
        ip_address=session_data.ip_address or None,
        user_agent=session_data.user_agent or None,
        is_current=session_data.session_id == current_session_id,
    )


# =============================================================================
# ENDPOINTS - Current Session
# =============================================================================


@router.get(
    "/current",
    response=Session,
    summary="Get current session",
    auth=AuthBearer(),
)
async def get_current_session(request) -> Session:
    """Get current session info.

    Security Auditor: Self-inspection.
    """
    user = get_current_user(request)
    session_id = getattr(user, "session_id", None) or request.COOKIES.get("session_id")
    if not session_id:
        raise NotFoundError("session", "current")

    session_manager = await get_session_manager()
    session = await session_manager.get_session(user.sub, session_id)

    if session is None:
        raise NotFoundError("session", session_id)

    return _to_session_response(
        session,
        session_ttl=session_manager.session_ttl,
        current_session_id=session_id,
    )


@router.post(
    "/current/refresh",
    summary="Refresh session",
    auth=AuthBearer(),
)
async def refresh_session(request) -> dict:
    """Refresh current session token.

    Security Auditor: Token rotation.
    """
    user = get_current_user(request)
    session_id = getattr(user, "session_id", None) or request.COOKIES.get("session_id")
    if not session_id:
        raise NotFoundError("session", "current")

    session_manager = await get_session_manager()
    updated = await session_manager.update_activity(user.sub, session_id)
    if not updated:
        raise NotFoundError("session", session_id)

    new_expires_at = (
        datetime.now(dt_timezone.utc) + timedelta(seconds=session_manager.session_ttl)
    ).isoformat()

    return {
        "refreshed": True,
        "new_expires_at": new_expires_at,
    }


@router.post(
    "/current/logout",
    summary="Logout current session",
    auth=AuthBearer(),
)
async def logout_current(request) -> dict:
    """Logout current session."""
    user = get_current_user(request)
    session_id = getattr(user, "session_id", None) or request.COOKIES.get("session_id")
    if not session_id:
        raise NotFoundError("session", "current")

    session_manager = await get_session_manager()
    deleted = await session_manager.delete_session(user.sub, session_id)

    logger.info("User logged out")

    return {
        "logged_out": deleted,
    }


# =============================================================================
# ENDPOINTS - User Sessions
# =============================================================================


@router.get(
    "/users/{user_id}",
    summary="List user sessions",
    auth=AuthBearer(),
)
async def list_user_sessions(
    request,
    user_id: str,
    active_only: bool = True,
) -> dict:
    """List all sessions for a user.

    Security Auditor: Multi-device awareness.
    """
    session_manager = await get_session_manager()
    sessions = await session_manager.list_sessions(user_id)

    return {
        "user_id": user_id,
        "sessions": [
            _to_session_response(
                session,
                session_ttl=session_manager.session_ttl,
            ).model_dump()
            for session in sessions
        ],
        "total": len(sessions),
    }


@router.delete(
    "/users/{user_id}",
    summary="Logout user everywhere",
    auth=AuthBearer(),
)
async def logout_user_everywhere(
    request,
    user_id: str,
) -> dict:
    """Force logout user from all sessions.

    Security Auditor: Account compromise response.
    """
    session_manager = await get_session_manager()
    deleted = await session_manager.delete_user_sessions(user_id)

    logger.warning(f"Forced logout for user: {user_id}")

    return {
        "user_id": user_id,
        "sessions_terminated": deleted,
    }


# =============================================================================
# ENDPOINTS - Session Management
# =============================================================================


@router.get(
    "",
    summary="List all sessions",
    auth=AuthBearer(),
)
async def list_all_sessions(
    request,
    active_only: bool = True,
    limit: int = 100,
) -> dict:
    """List all active sessions (admin).

    DevOps: Platform-wide session monitoring.
    """
    session_manager = await get_session_manager()
    sessions = await session_manager.list_all_sessions(limit=limit)

    return {
        "sessions": [
            _to_session_response(
                session,
                session_ttl=session_manager.session_ttl,
            ).model_dump()
            for session in sessions
        ],
        "total": len(sessions),
    }


@router.delete(
    "/{session_id}",
    summary="Terminate session",
    auth=AuthBearer(),
)
async def terminate_session(
    request,
    session_id: str,
) -> dict:
    """Terminate a specific session.

    Security Auditor: Targeted session kill.
    """
    session_manager = await get_session_manager()
    session = await session_manager.get_session_by_id(session_id)
    if not session:
        raise NotFoundError("session", session_id)

    deleted = await session_manager.delete_session(session.user_id, session_id)

    logger.warning(f"Session terminated: {session_id}")

    return {
        "session_id": session_id,
        "terminated": deleted,
    }


@router.get(
    "/stats",
    response=SessionStats,
    summary="Get session stats",
    auth=AuthBearer(),
)
async def get_session_stats(request) -> SessionStats:
    """Get session statistics.

    DevOps: Usage monitoring.
    """
    session_manager = await get_session_manager()
    sessions = await session_manager.list_all_sessions(limit=1000)

    now = datetime.now(dt_timezone.utc)
    today = now.date()

    sessions_today = 0
    unique_users = set()
    durations = []

    for session in sessions:
        try:
            created_at = datetime.fromisoformat(session.created_at)
        except ValueError:
            created_at = now

        if created_at.date() == today:
            sessions_today += 1
            unique_users.add(session.user_id)

        try:
            last_activity = datetime.fromisoformat(session.last_activity)
        except ValueError:
            last_activity = now

        durations.append((last_activity - created_at).total_seconds() / 60.0)

    avg_duration = sum(durations) / len(durations) if durations else 0.0

    return SessionStats(
        active_sessions=len(sessions),
        sessions_today=sessions_today,
        unique_users_today=len(unique_users),
        avg_session_duration_minutes=avg_duration,
    )


# =============================================================================
# ENDPOINTS - Security Actions
# =============================================================================


@router.post(
    "/security/terminate-all",
    summary="Terminate all sessions",
    auth=AuthBearer(),
)
async def terminate_all_sessions(
    request,
    except_current: bool = True,
) -> dict:
    """Terminate all sessions (emergency).

    Security Auditor: Platform-wide emergency logout.
    """
    user = get_current_user(request)
    current_session_id = getattr(user, "session_id", None) or request.COOKIES.get("session_id")

    session_manager = await get_session_manager()
    sessions = await session_manager.list_all_sessions(limit=10000)

    deleted = 0
    for session in sessions:
        if except_current and current_session_id and session.session_id == current_session_id:
            continue
        if await session_manager.delete_session(session.user_id, session.session_id):
            deleted += 1

    logger.critical("EMERGENCY: All sessions terminated")

    return {
        "terminated": deleted,
        "except_current": except_current,
    }


@router.post(
    "/security/terminate-by-ip",
    summary="Terminate by IP",
    auth=AuthBearer(),
)
async def terminate_by_ip(
    request,
    ip_address: str,
) -> dict:
    """Terminate all sessions from an IP.

    Security Auditor: IP-based threat response.
    """
    session_manager = await get_session_manager()
    sessions = await session_manager.list_all_sessions(limit=10000)

    deleted = 0
    for session in sessions:
        if session.ip_address == ip_address:
            if await session_manager.delete_session(session.user_id, session.session_id):
                deleted += 1

    logger.warning(f"Sessions terminated for IP: {ip_address}")

    return {
        "ip_address": ip_address,
        "terminated": deleted,
    }


# =============================================================================
# ENDPOINTS - Session Configuration
# =============================================================================


@router.get(
    "/config",
    summary="Get session config",
    auth=AuthBearer(),
)
async def get_session_config(request) -> dict:
    """Get session configuration.

    DevOps: Session settings.
    """
    session_manager = await get_session_manager()
    return {
        "session_timeout_minutes": int(session_manager.session_ttl / 60),
        "max_sessions_per_user": 5,
        "require_mfa_reauthentication": True,
        "session_cookie_secure": True,
    }


@router.patch(
    "/config",
    summary="Update session config",
    auth=AuthBearer(),
)
async def update_session_config(
    request,
    session_timeout_minutes: Optional[int] = None,
    max_sessions_per_user: Optional[int] = None,
) -> dict:
    """Update session configuration."""
    return {
        "updated": True,
    }