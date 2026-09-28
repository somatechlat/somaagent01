"""Session Manager for Redis-backed user sessions.

This module exposes a high-level facade over session storage
(:mod:`admin.common.session_store`) and session security
(:mod:`admin.common.session_security`).
"""

from __future__ import annotations

import logging
import os
from typing import Optional

from admin.common.session_security import PermissionResolver
from admin.common.session_store import (
    ACTIVE_SESSIONS,
    RedisSessionStore,
    Session,
    SESSION_CREATED,
    SESSION_DELETED,
    SESSION_OPERATION_DURATION,
    SESSION_RETRIEVED,
)

logger = logging.getLogger(__name__)


# =============================================================================
# SESSION MANAGER
# =============================================================================


class SessionManager:
    """Redis-backed session manager.

    Implements session lifecycle per design.md:
    - create_session(): Create new session with Redis storage
    - get_session(): Retrieve session by ID
    - update_activity(): Extend TTL on activity
    - delete_session(): Remove single session
    - delete_user_sessions(): Remove all sessions for user

    Key format: session:{user_id}:{session_id}
    TTL: 900 seconds (15 minutes) by default, extended on activity
    """

    SESSION_TTL = 900  # 15 minutes per design.md
    SESSION_PREFIX = RedisSessionStore.SESSION_PREFIX
    CONFIG_KEY = RedisSessionStore.CONFIG_KEY
    DEFAULT_CONFIG = RedisSessionStore.DEFAULT_CONFIG

    def __init__(
        self,
        redis_url: Optional[str] = None,
        session_ttl: int = SESSION_TTL,
    ):
        """Initialize SessionManager.

        Args:
            redis_url: Redis connection URL. Defaults to REDIS_URL env var.
            session_ttl: Session TTL in seconds. Defaults to 900 (15 min).
        """
        try:
            from config.settings_registry import SettingsRegistry

            settings = SettingsRegistry.get()
            resolved_redis_url = redis_url or settings.redis_url
        except Exception:
            resolved_redis_url = redis_url or os.getenv("REDIS_URL")

            if not resolved_redis_url:
                raise ValueError("REDIS_URL is required")

        self.redis_url = resolved_redis_url
        self.session_ttl = session_ttl
        self._store = RedisSessionStore(
            redis_url=resolved_redis_url,
            session_ttl=session_ttl,
        )
        self._security = PermissionResolver()

    async def connect(self) -> None:
        """Connect to Redis."""
        await self._store.connect()

    async def close(self) -> None:
        """Close Redis connection."""
        await self._store.close()

    def _make_key(self, user_id: str, session_id: str) -> str:
        """Build Redis key for session.

        Format: session:{user_id}:{session_id}
        """
        return self._store._make_key(user_id, session_id)

    def _make_user_pattern(self, user_id: str) -> str:
        """Build Redis key pattern for all user sessions.

        Format: session:{user_id}:*
        """
        return self._store._make_user_pattern(user_id)

    async def create_session(
        self,
        user_id: str,
        tenant_id: str,
        email: str,
        roles: list[str],
        permissions: list[str],
        ip_address: str,
        user_agent: str,
    ) -> Session:
        """Create new session in Redis.

        Per design.md Section 5.1:
        - Generate UUID4 session_id
        - Store with TTL matching access_token expiry (15 min)
        - Include all required session data

        Args:
            user_id: User UUID from Keycloak
            tenant_id: Tenant UUID
            email: User email
            roles: List of realm roles
            permissions: List of resolved permissions (from SpiceDB)
            ip_address: Client IP address
            user_agent: Client user agent string

        Returns:
            Created Session object
        """
        import uuid

        session_id = str(uuid.uuid4())
        session = Session(
            session_id=session_id,
            user_id=user_id,
            tenant_id=tenant_id,
            email=email,
            roles=roles,
            permissions=permissions,
            ip_address=ip_address,
            user_agent=user_agent[:500] if user_agent else "",  # Truncate long user agents
        )

        await self._store.create(session)
        return session

    async def get_session(self, user_id: str, session_id: str) -> Optional[Session]:
        """Retrieve session from Redis.

        Args:
            user_id: User UUID
            session_id: Session UUID

        Returns:
            Session if found and valid, None otherwise
        """
        return await self._store.get(user_id, session_id)

    async def get_session_by_id(self, session_id: str) -> Optional[Session]:
        """Retrieve session by session_id only (scans for user_id).

        Less efficient than get_session() - use when user_id unknown.

        Args:
            session_id: Session UUID

        Returns:
            Session if found, None otherwise
        """
        return await self._store.get_by_id(session_id)

    async def update_activity(self, user_id: str, session_id: str) -> bool:
        """Update last_activity and extend TTL.

        Per design.md Section 5.5:
        - Update last_activity timestamp
        - Extend TTL on each authenticated request

        Args:
            user_id: User UUID
            session_id: Session UUID

        Returns:
            True if session was updated, False if not found
        """
        return await self._store.update_activity(user_id, session_id)

    async def delete_session(self, user_id: str, session_id: str) -> bool:
        """Delete session from Redis.

        Args:
            user_id: User UUID
            session_id: Session UUID

        Returns:
            True if session was deleted, False if not found
        """
        return await self._store.delete(user_id, session_id)

    async def delete_user_sessions(self, user_id: str) -> int:
        """Delete all sessions for a user.

        Used for:
        - Logout from all devices
        - Account security actions
        - User deletion

        Args:
            user_id: User UUID

        Returns:
            Number of sessions deleted
        """
        return await self._store.delete_user_sessions(user_id)

    async def count_user_sessions(self, user_id: str) -> int:
        """Count active sessions for a user.

        Args:
            user_id: User UUID

        Returns:
            Number of active sessions
        """
        return await self._store.count_user_sessions(user_id)

    async def list_sessions(self, user_id: str) -> list[Session]:
        """List all active sessions for a user."""
        return await self._store.list_sessions(user_id)

    async def list_all_sessions(self, limit: int = 100) -> list[Session]:
        """List active sessions across all users (admin use)."""
        return await self._store.list_all_sessions(limit)

    async def get_config(self) -> dict:
        """Read session configuration from Redis.

        Returns:
            Dict with session configuration. Falls back to DEFAULT_CONFIG.
        """
        return await self._store.get_config()

    async def update_config(self, updates: dict) -> dict:
        """Update session configuration in Redis.

        Applies valid updates and persists to Redis.
        Also updates live session_ttl if timeout changes.

        Args:
            updates: Dict of configuration changes.

        Returns:
            Updated configuration dict.
        """
        current = await self._store.get_config()

        # Only allow known keys
        allowed = set(self.DEFAULT_CONFIG.keys())
        for key, value in updates.items():
            if key in allowed:
                current[key] = value
            else:
                logger.warning("Ignoring unknown session config key: %s", key)

        # Apply live session_ttl change immediately
        if "session_timeout_minutes" in updates:
            new_ttl = int(updates["session_timeout_minutes"]) * 60
            self.session_ttl = new_ttl
            self._store.session_ttl = new_ttl
            logger.info("Session TTL updated to %s seconds", new_ttl)

        await self._store.update_config(current)
        logger.info("Session config updated: %s", current)
        return current

    async def resolve_permissions(
        self,
        user_id: str,
        tenant_id: str,
        roles: list[str],
    ) -> list[str]:
        """Resolve permissions from SpiceDB and roles.

        Per design.md Section 5.3:
        - Query SpiceDB for fine-grained permissions
        - Fall back to role-based permissions if SpiceDB unavailable
        - Cache permissions in session

        Args:
            user_id: User ID
            tenant_id: Tenant ID
            roles: User roles from token

        Returns:
            List of permission strings
        """
        return await self._security.resolve_permissions(user_id, tenant_id, roles)

    def _get_permissions_for_roles(self, roles: list[str]) -> list[str]:
        """Get permissions based on roles.

        Per design.md Section 5.3:
        - Role hierarchy: admin > developer > trainer > user
        - Each role inherits lower role permissions
        """
        return self._security._get_permissions_for_roles(roles)

    async def get_accessible_agents(
        self,
        user_id: str,
    ) -> list[str]:
        """Get list of agent IDs user can access.

        Per design.md Section 5.3:
        - Query SpiceDB for agents with 'view' permission
        - Used for agent list filtering

        Args:
            user_id: User ID

        Returns:
            List of agent IDs
        """
        return await self._security.get_accessible_agents(user_id)


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_session_manager_instance: Optional[SessionManager] = None


async def get_session_manager() -> SessionManager:
    """Get or create the singleton SessionManager.

    Usage:
        session_manager = await get_session_manager()
        session = await session_manager.create_session(...)
    """
    global _session_manager_instance
    if _session_manager_instance is None:
        _session_manager_instance = SessionManager()
        await _session_manager_instance.connect()
    return _session_manager_instance


__all__ = [
    "ACTIVE_SESSIONS",
    "SESSION_CREATED",
    "SESSION_DELETED",
    "SESSION_OPERATION_DURATION",
    "SESSION_RETRIEVED",
    "Session",
    "SessionManager",
    "get_session_manager",
]
