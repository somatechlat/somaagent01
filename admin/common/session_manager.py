"""Session Manager for Redis-backed user sessions.


Per login-to-chat-journey design.md Section: SessionManager

Implements:
- Session creation with Redis storage (key: session:{user_id}:{session_id})
- Session retrieval and validation
- Activity tracking with TTL extension
- Session deletion (single and bulk)

Personas:
- Django Architect: Async Redis integration
- Security Auditor: Session isolation, TTL enforcement
- Performance Engineer: Efficient Redis operations
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Optional

import redis.asyncio as redis
from prometheus_client import Counter, Gauge, Histogram

logger = logging.getLogger(__name__)

# =============================================================================
# PROMETHEUS METRICS
# =============================================================================

SESSION_CREATED = Counter(
    "session_created_total",
    "Total sessions created",
    labelnames=("tenant_id",),
)
SESSION_RETRIEVED = Counter(
    "session_retrieved_total",
    "Total session retrievals",
    labelnames=("result",),
)
SESSION_DELETED = Counter(
    "session_deleted_total",
    "Total sessions deleted",
    labelnames=("reason",),
)
ACTIVE_SESSIONS = Gauge(
    "active_sessions",
    "Current active sessions estimate",
)
SESSION_OPERATION_DURATION = Histogram(
    "session_operation_duration_seconds",
    "Session operation duration",
    labelnames=("operation",),
)


# =============================================================================
# DATA CLASSES
# =============================================================================


@dataclass
class Session:
    """User session data stored in Redis.

    Per design.md Section 5.1 Session Creation.
    """

    session_id: str
    user_id: str
    tenant_id: str
    email: str
    roles: list[str] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)
    created_at: str = ""
    last_activity: str = ""
    ip_address: str = ""
    user_agent: str = ""

    def __post_init__(self):
        """Execute post init  ."""

        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()
        if not self.last_activity:
            self.last_activity = self.created_at

    def to_dict(self) -> dict:
        """Convert to dictionary for Redis storage."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Session":
        """Create Session from dictionary."""
        return cls(**data)

    def update_activity(self) -> None:
        """Update last_activity timestamp."""
        self.last_activity = datetime.now(timezone.utc).isoformat()


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
    SESSION_PREFIX = "session:"

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
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.session_ttl = session_ttl
        self._redis: Optional[redis.Redis] = None
        self._connected = False

    async def connect(self) -> None:
        """Connect to Redis."""
        if not self._connected:
            self._redis = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
            await self._redis.ping()
            self._connected = True
            logger.info(f"SessionManager connected to Redis: {self.redis_url}")

    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            self._connected = False
            logger.info("SessionManager disconnected from Redis")

    async def _ensure_connected(self) -> None:
        """Ensure Redis connection is established."""
        if not self._connected:
            await self.connect()

    def _make_key(self, user_id: str, session_id: str) -> str:
        """Build Redis key for session.

        Format: session:{user_id}:{session_id}
        """
        return f"{self.SESSION_PREFIX}{user_id}:{session_id}"

    def _make_user_pattern(self, user_id: str) -> str:
        """Build Redis key pattern for all user sessions.

        Format: session:{user_id}:*
        """
        return f"{self.SESSION_PREFIX}{user_id}:*"

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
        await self._ensure_connected()

        with SESSION_OPERATION_DURATION.labels("create").time():
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

            key = self._make_key(user_id, session_id)

            await self._redis.setex(
                key,
                self.session_ttl,
                json.dumps(session.to_dict()),
            )

            SESSION_CREATED.labels(tenant_id).inc()
            logger.info(
                f"Session created: user={user_id}, session={session_id}, "
                f"tenant={tenant_id}, ttl={self.session_ttl}s"
            )

            return session

    async def get_session(self, user_id: str, session_id: str) -> Optional[Session]:
        """Retrieve session from Redis.

        Args:
            user_id: User UUID
            session_id: Session UUID

        Returns:
            Session if found and valid, None otherwise
        """
        await self._ensure_connected()

        with SESSION_OPERATION_DURATION.labels("get").time():
            key = self._make_key(user_id, session_id)

            data = await self._redis.get(key)

            if data is None:
                SESSION_RETRIEVED.labels("not_found").inc()
                logger.debug(f"Session not found: {key}")
                return None

            try:
                session = Session.from_dict(json.loads(data))
                SESSION_RETRIEVED.labels("found").inc()
                return session
            except (json.JSONDecodeError, TypeError, KeyError) as e:
                SESSION_RETRIEVED.labels("invalid").inc()
                logger.warning(f"Invalid session data for {key}: {e}")
                return None

    async def get_session_by_id(self, session_id: str) -> Optional[Session]:
        """Retrieve session by session_id only (scans for user_id).

        Less efficient than get_session() - use when user_id unknown.

        Args:
            session_id: Session UUID

        Returns:
            Session if found, None otherwise
        """
        await self._ensure_connected()

        with SESSION_OPERATION_DURATION.labels("get_by_id").time():
            # Scan for matching session
            pattern = f"{self.SESSION_PREFIX}*:{session_id}"

            async for key in self._redis.scan_iter(match=pattern, count=100):
                data = await self._redis.get(key)
                if data:
                    try:
                        session = Session.from_dict(json.loads(data))
                        if session.session_id == session_id:
                            SESSION_RETRIEVED.labels("found").inc()
                            return session
                    except (json.JSONDecodeError, TypeError, KeyError):
                        continue

            SESSION_RETRIEVED.labels("not_found").inc()
            return None

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
        await self._ensure_connected()

        with SESSION_OPERATION_DURATION.labels("update_activity").time():
            key = self._make_key(user_id, session_id)

            data = await self._redis.get(key)
            if data is None:
                return False

            try:
                session = Session.from_dict(json.loads(data))
                session.update_activity()

                # Update with extended TTL
                await self._redis.setex(
                    key,
                    self.session_ttl,
                    json.dumps(session.to_dict()),
                )

                return True
            except (json.JSONDecodeError, TypeError, KeyError) as e:
                logger.warning(f"Failed to update session {key}: {e}")
                return False

    async def delete_session(self, user_id: str, session_id: str) -> bool:
        """Delete session from Redis.

        Args:
            user_id: User UUID
            session_id: Session UUID

        Returns:
            True if session was deleted, False if not found
        """
        await self._ensure_connected()

        with SESSION_OPERATION_DURATION.labels("delete").time():
            key = self._make_key(user_id, session_id)

            deleted = await self._redis.delete(key)

            if deleted:
                SESSION_DELETED.labels("explicit").inc()
                logger.info(f"Session deleted: {key}")
                return True

            return False

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
        await self._ensure_connected()

        with SESSION_OPERATION_DURATION.labels("delete_all").time():
            pattern = self._make_user_pattern(user_id)

            deleted_count = 0
            keys_to_delete = []

            async for key in self._redis.scan_iter(match=pattern, count=100):
                keys_to_delete.append(key)

            if keys_to_delete:
                deleted_count = await self._redis.delete(*keys_to_delete)
                SESSION_DELETED.labels("bulk").inc(deleted_count)
                logger.info(f"Deleted {deleted_count} sessions for user {user_id}")

            return deleted_count

    async def count_user_sessions(self, user_id: str) -> int:
        """Count active sessions for a user.

        Args:
            user_id: User UUID

        Returns:
            Number of active sessions
        """
        await self._ensure_connected()

        pattern = self._make_user_pattern(user_id)
        count = 0

        async for _ in self._redis.scan_iter(match=pattern, count=100):
            count += 1

        return count

    async def list_sessions(self, user_id: str) -> list[Session]:
        """List all active sessions for a user."""
        await self._ensure_connected()

        sessions: list[Session] = []
        pattern = self._make_user_pattern(user_id)

        async for key in self._redis.scan_iter(match=pattern, count=100):
            data = await self._redis.get(key)
            if not data:
                continue
            try:
                sessions.append(Session.from_dict(json.loads(data)))
            except (json.JSONDecodeError, TypeError, KeyError) as e:
                logger.warning(f"Invalid session data for {key}: {e}")
                continue

        return sessions

    async def list_all_sessions(self, limit: int = 100) -> list[Session]:
        """List active sessions across all users (admin use)."""
        await self._ensure_connected()

        sessions: list[Session] = []
        pattern = f"{self.SESSION_PREFIX}*"

        async for key in self._redis.scan_iter(match=pattern, count=100):
            if len(sessions) >= limit:
                break
            data = await self._redis.get(key)
            if not data:
                continue
            try:
                sessions.append(Session.from_dict(json.loads(data)))
            except (json.JSONDecodeError, TypeError, KeyError) as e:
                logger.warning(f"Invalid session data for {key}: {e}")
                continue

        return sessions

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
        permissions = set()

        # Try SpiceDB first
        try:
            from services.common.spicedb_client import get_spicedb_client

            spicedb = await get_spicedb_client()
            spicedb_permissions = await spicedb.get_permissions(user_id, tenant_id)
            permissions.update(spicedb_permissions)
            logger.debug(
                f"SpiceDB permissions resolved: user={user_id}, permissions={spicedb_permissions}"
            )
        except Exception as e:
            # FAIL-OPEN for permissions (use role-based fallback)
            logger.warning(f"SpiceDB unavailable, using role-based permissions: {e}")

        # Add role-based permissions as fallback/supplement
        role_permissions = self._get_permissions_for_roles(roles)
        permissions.update(role_permissions)

        return list(permissions)

    def _get_permissions_for_roles(self, roles: list[str]) -> list[str]:
        """Get permissions based on roles.

        Per design.md Section 5.3:
        - Role hierarchy: admin > developer > trainer > user
        - Each role inherits lower role permissions
        """
        permissions = set()

        role_permission_map = {
            "admin": [
                "view",
                "use",
                "develop",
                "train",
                "administrate",
                "manage",
                "agents:create",
                "agents:delete",
                "agents:configure",
                "users:manage",
                "tenants:manage",
            ],
            "developer": [
                "view",
                "use",
                "develop",
                "train",
                "agents:create",
                "agents:configure",
            ],
            "trainer": [
                "view",
                "use",
                "train",
                "agents:train",
            ],
            "user": [
                "view",
                "use",
                "conversations:create",
                "conversations:view",
            ],
        }

        for role in roles:
            role_lower = role.lower()
            if role_lower in role_permission_map:
                permissions.update(role_permission_map[role_lower])

        return list(permissions)

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
        try:
            from services.common.spicedb_client import get_spicedb_client

            spicedb = await get_spicedb_client()
            agent_ids = await spicedb.lookup_resources(
                user_id=user_id,
                resource_type="agent",
                permission="view",
            )
            logger.debug(f"Accessible agents resolved: user={user_id}, count={len(agent_ids)}")
            return agent_ids
        except Exception as e:
            logger.warning(f"SpiceDB lookup failed, returning empty list: {e}")
            return []


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
    "Session",
    "SessionManager",
    "get_session_manager",
]
