"""Session storage backend for Redis-backed user sessions."""

from __future__ import annotations

import json
import logging
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
# REDIS SESSION STORE
# =============================================================================


class RedisSessionStore:
    """Redis-backed storage for user sessions.

    Encapsulates all Redis I/O for session lifecycle operations.
    """

    SESSION_PREFIX = "session:"
    CONFIG_KEY = "session:config:global"
    DEFAULT_CONFIG = {
        "session_timeout_minutes": 15,
        "max_sessions_per_user": 5,
        "require_mfa_reauthentication": True,
        "session_cookie_secure": True,
    }

    def __init__(self, redis_url: str, session_ttl: int = 900):
        """Initialize RedisSessionStore.

        Args:
            redis_url: Redis connection URL.
            session_ttl: Session TTL in seconds. Defaults to 900 (15 min).
        """
        self.redis_url = redis_url
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
            logger.info("RedisSessionStore connected to Redis: %s", self.redis_url)

    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            self._connected = False
            logger.info("RedisSessionStore disconnected from Redis")

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

    async def create(self, session: Session) -> None:
        """Persist a new session in Redis with the configured TTL."""
        await self._ensure_connected()
        assert self._redis is not None

        with SESSION_OPERATION_DURATION.labels("create").time():
            key = self._make_key(session.user_id, session.session_id)
            await self._redis.setex(
                key,
                self.session_ttl,
                json.dumps(session.to_dict()),
            )
            SESSION_CREATED.labels(session.tenant_id).inc()
            logger.info(
                "Session created: user=%s, session=%s, tenant=%s, ttl=%ss",
                session.user_id,
                session.session_id,
                session.tenant_id,
                self.session_ttl,
            )

    async def get(self, user_id: str, session_id: str) -> Optional[Session]:
        """Retrieve session from Redis by user_id and session_id."""
        await self._ensure_connected()
        assert self._redis is not None

        with SESSION_OPERATION_DURATION.labels("get").time():
            key = self._make_key(user_id, session_id)
            data = await self._redis.get(key)

            if data is None:
                SESSION_RETRIEVED.labels("not_found").inc()
                logger.debug("Session not found: %s", key)
                return None

            try:
                session = Session.from_dict(json.loads(data))
                SESSION_RETRIEVED.labels("found").inc()
                return session
            except (json.JSONDecodeError, TypeError, KeyError) as e:
                SESSION_RETRIEVED.labels("invalid").inc()
                logger.warning("Invalid session data for %s: %s", key, e)
                return None

    async def get_by_id(self, session_id: str) -> Optional[Session]:
        """Retrieve session by session_id only (scans for user_id).

        Less efficient than get() - use when user_id unknown.
        """
        await self._ensure_connected()
        assert self._redis is not None

        with SESSION_OPERATION_DURATION.labels("get_by_id").time():
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
        """Update last_activity and extend TTL."""
        await self._ensure_connected()
        assert self._redis is not None

        with SESSION_OPERATION_DURATION.labels("update_activity").time():
            key = self._make_key(user_id, session_id)
            data = await self._redis.get(key)
            if data is None:
                return False

            try:
                session = Session.from_dict(json.loads(data))
                session.update_activity()
                await self._redis.setex(
                    key,
                    self.session_ttl,
                    json.dumps(session.to_dict()),
                )
                return True
            except (json.JSONDecodeError, TypeError, KeyError) as e:
                logger.warning("Failed to update session %s: %s", key, e)
                return False

    async def delete(self, user_id: str, session_id: str) -> bool:
        """Delete session from Redis."""
        await self._ensure_connected()
        assert self._redis is not None

        with SESSION_OPERATION_DURATION.labels("delete").time():
            key = self._make_key(user_id, session_id)
            deleted = await self._redis.delete(key)

            if deleted:
                SESSION_DELETED.labels("explicit").inc()
                logger.info("Session deleted: %s", key)
                return True

            return False

    async def delete_user_sessions(self, user_id: str) -> int:
        """Delete all sessions for a user."""
        await self._ensure_connected()
        assert self._redis is not None

        with SESSION_OPERATION_DURATION.labels("delete_all").time():
            pattern = self._make_user_pattern(user_id)
            keys_to_delete = []

            async for key in self._redis.scan_iter(match=pattern, count=100):
                keys_to_delete.append(key)

            deleted_count = 0
            if keys_to_delete:
                deleted_count = await self._redis.delete(*keys_to_delete)
                SESSION_DELETED.labels("bulk").inc(deleted_count)
                logger.info("Deleted %s sessions for user %s", deleted_count, user_id)

            return deleted_count

    async def count_user_sessions(self, user_id: str) -> int:
        """Count active sessions for a user."""
        await self._ensure_connected()
        assert self._redis is not None

        pattern = self._make_user_pattern(user_id)
        count = 0

        async for _ in self._redis.scan_iter(match=pattern, count=100):
            count += 1

        return count

    async def list_sessions(self, user_id: str) -> list[Session]:
        """List all active sessions for a user."""
        await self._ensure_connected()
        assert self._redis is not None

        sessions: list[Session] = []
        pattern = self._make_user_pattern(user_id)

        async for key in self._redis.scan_iter(match=pattern, count=100):
            data = await self._redis.get(key)
            if not data:
                continue
            try:
                sessions.append(Session.from_dict(json.loads(data)))
            except (json.JSONDecodeError, TypeError, KeyError) as e:
                logger.warning("Invalid session data for %s: %s", key, e)
                continue

        return sessions

    async def list_all_sessions(self, limit: int = 100) -> list[Session]:
        """List active sessions across all users (admin use)."""
        await self._ensure_connected()
        assert self._redis is not None

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
                logger.warning("Invalid session data for %s: %s", key, e)
                continue

        return sessions

    async def get_config(self) -> dict:
        """Read session configuration from Redis.

        Returns:
            Dict with session configuration. Falls back to DEFAULT_CONFIG.
        """
        await self._ensure_connected()
        assert self._redis is not None
        data = await self._redis.get(self.CONFIG_KEY)
        if data:
            try:
                stored = json.loads(data)
                config = dict(self.DEFAULT_CONFIG)
                config.update(stored)
                return config
            except json.JSONDecodeError:
                logger.warning("Invalid session config in Redis, using defaults")
        return dict(self.DEFAULT_CONFIG)

    async def update_config(self, current: dict) -> None:
        """Persist session configuration to Redis.

        Args:
            current: The fully merged configuration dict to persist.
        """
        await self._ensure_connected()
        assert self._redis is not None
        await self._redis.set(self.CONFIG_KEY, json.dumps(current))


__all__ = [
    "ACTIVE_SESSIONS",
    "RedisSessionStore",
    "SESSION_CREATED",
    "SESSION_DELETED",
    "SESSION_OPERATION_DURATION",
    "SESSION_RETRIEVED",
    "Session",
]
