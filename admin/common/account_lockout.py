"""Account Lockout Service for brute-force protection.

VIBE COMPLIANT - Real Redis backend, no mocks.
Per login-to-chat-journey design.md Section 2.5: Account Lockout

Implements:
- Track failed login attempts in Redis
- Lock account after 5 failures within 15 minutes
- Return 403 with retry_after when locked
- Auto-expire lockout after 15 minutes

Personas:
- Security Auditor: Brute-force protection, timing-safe operations
- Django Architect: Async Redis integration
- Performance Engineer: Efficient Redis operations
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from typing import Optional

import redis.asyncio as redis
from prometheus_client import Counter, Gauge

logger = logging.getLogger(__name__)

# =============================================================================
# PROMETHEUS METRICS
# =============================================================================

LOGIN_ATTEMPTS = Counter(
    "login_attempts_total",
    "Total login attempts",
    labelnames=("result",),
)
ACCOUNT_LOCKOUTS = Counter(
    "account_lockouts_total",
    "Total account lockouts triggered",
)
LOCKED_ACCOUNTS = Gauge(
    "locked_accounts_current",
    "Current number of locked accounts (estimate)",
)


# =============================================================================
# CONFIGURATION
# =============================================================================

# Per design.md Section 2.5
DEFAULT_MAX_ATTEMPTS = 5
DEFAULT_LOCKOUT_DURATION = 900  # 15 minutes
DEFAULT_ATTEMPT_WINDOW = 900  # 15 minutes


@dataclass
class LockoutConfig:
    """Account lockout configuration."""

    max_attempts: int = DEFAULT_MAX_ATTEMPTS
    lockout_duration: int = DEFAULT_LOCKOUT_DURATION
    attempt_window: int = DEFAULT_ATTEMPT_WINDOW

    @classmethod
    def from_env(cls) -> "LockoutConfig":
        """Load configuration from environment."""
        return cls(
            max_attempts=int(os.getenv("AUTH_MAX_ATTEMPTS", DEFAULT_MAX_ATTEMPTS)),
            lockout_duration=int(os.getenv("AUTH_LOCKOUT_DURATION", DEFAULT_LOCKOUT_DURATION)),
            attempt_window=int(os.getenv("AUTH_ATTEMPT_WINDOW", DEFAULT_ATTEMPT_WINDOW)),
        )


# =============================================================================
# DATA CLASSES
# =============================================================================


@dataclass
class LockoutStatus:
    """Account lockout status."""

    is_locked: bool
    attempts: int
    remaining_attempts: int
    retry_after: Optional[int] = None  # Seconds until lockout expires
    locked_at: Optional[float] = None  # Unix timestamp when locked


# =============================================================================
# ACCOUNT LOCKOUT SERVICE
# =============================================================================


class AccountLockoutService:
    """Redis-backed account lockout service.

    Per design.md Section 2.5:
    - Track failed attempts: key `login_attempts:{email}`, TTL 15 min
    - Lock after 5 failures: key `lockout:{email}`, TTL 15 min
    - Return 403 with retry_after when locked

    Key formats:
    - login_attempts:{email} = count (int)
    - lockout:{email} = timestamp (float)
    """

    ATTEMPTS_PREFIX = "login_attempts:"
    LOCKOUT_PREFIX = "lockout:"

    def __init__(
        self,
        redis_url: Optional[str] = None,
        config: Optional[LockoutConfig] = None,
    ):
        """Initialize AccountLockoutService.

        Args:
            redis_url: Redis connection URL. Defaults to REDIS_URL env var.
            config: Lockout configuration. Defaults to env-based config.
        """
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.config = config or LockoutConfig.from_env()
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
            logger.info(f"AccountLockoutService connected to Redis")

    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            self._connected = False

    async def _ensure_connected(self) -> None:
        """Ensure Redis connection is established."""
        if not self._connected:
            await self.connect()

    def _attempts_key(self, email: str) -> str:
        """Build Redis key for login attempts."""
        return f"{self.ATTEMPTS_PREFIX}{email.lower()}"

    def _lockout_key(self, email: str) -> str:
        """Build Redis key for lockout status."""
        return f"{self.LOCKOUT_PREFIX}{email.lower()}"

    async def check_lockout(self, email: str) -> LockoutStatus:
        """Check if account is locked.

        Args:
            email: User email address

        Returns:
            LockoutStatus with current state
        """
        await self._ensure_connected()

        lockout_key = self._lockout_key(email)
        attempts_key = self._attempts_key(email)

        # Check lockout
        locked_at = await self._redis.get(lockout_key)

        if locked_at:
            locked_timestamp = float(locked_at)
            ttl = await self._redis.ttl(lockout_key)
            retry_after = max(0, ttl) if ttl > 0 else 0

            return LockoutStatus(
                is_locked=True,
                attempts=self.config.max_attempts,
                remaining_attempts=0,
                retry_after=retry_after,
                locked_at=locked_timestamp,
            )

        # Get current attempts
        attempts = await self._redis.get(attempts_key)
        attempts_count = int(attempts) if attempts else 0
        remaining = max(0, self.config.max_attempts - attempts_count)

        return LockoutStatus(
            is_locked=False,
            attempts=attempts_count,
            remaining_attempts=remaining,
        )

    async def record_failed_attempt(self, email: str) -> LockoutStatus:
        """Record a failed login attempt.

        Increments attempt counter and locks account if threshold reached.

        Args:
            email: User email address

        Returns:
            Updated LockoutStatus
        """
        await self._ensure_connected()

        attempts_key = self._attempts_key(email)
        lockout_key = self._lockout_key(email)

        # Increment attempts with TTL
        pipe = self._redis.pipeline()
        pipe.incr(attempts_key)
        pipe.expire(attempts_key, self.config.attempt_window)
        results = await pipe.execute()

        attempts_count = results[0]
        LOGIN_ATTEMPTS.labels("failure").inc()

        logger.info(f"Failed login attempt: email={email}, attempts={attempts_count}")

        # Check if should lock
        if attempts_count >= self.config.max_attempts:
            # Lock the account
            now = time.time()
            await self._redis.setex(
                lockout_key,
                self.config.lockout_duration,
                str(now),
            )

            ACCOUNT_LOCKOUTS.inc()
            logger.warning(
                f"Account locked: email={email}, attempts={attempts_count}, "
                f"duration={self.config.lockout_duration}s"
            )

            return LockoutStatus(
                is_locked=True,
                attempts=attempts_count,
                remaining_attempts=0,
                retry_after=self.config.lockout_duration,
                locked_at=now,
            )

        remaining = self.config.max_attempts - attempts_count

        return LockoutStatus(
            is_locked=False,
            attempts=attempts_count,
            remaining_attempts=remaining,
        )

    async def record_successful_login(self, email: str) -> None:
        """Record a successful login (clears attempts).

        Args:
            email: User email address
        """
        await self._ensure_connected()

        attempts_key = self._attempts_key(email)

        # Clear attempts on successful login
        await self._redis.delete(attempts_key)

        LOGIN_ATTEMPTS.labels("success").inc()
        logger.debug(f"Successful login, cleared attempts: email={email}")

    async def clear_lockout(self, email: str) -> bool:
        """Manually clear lockout (admin action).

        Args:
            email: User email address

        Returns:
            True if lockout was cleared, False if not locked
        """
        await self._ensure_connected()

        lockout_key = self._lockout_key(email)
        attempts_key = self._attempts_key(email)

        # Clear both lockout and attempts
        pipe = self._redis.pipeline()
        pipe.delete(lockout_key)
        pipe.delete(attempts_key)
        results = await pipe.execute()

        cleared = results[0] > 0

        if cleared:
            logger.info(f"Lockout cleared by admin: email={email}")

        return cleared

    async def get_lockout_info(self, email: str) -> dict:
        """Get detailed lockout information (for admin).

        Args:
            email: User email address

        Returns:
            Dict with lockout details
        """
        status = await self.check_lockout(email)

        return {
            "email": email,
            "is_locked": status.is_locked,
            "attempts": status.attempts,
            "remaining_attempts": status.remaining_attempts,
            "retry_after": status.retry_after,
            "locked_at": status.locked_at,
            "config": {
                "max_attempts": self.config.max_attempts,
                "lockout_duration": self.config.lockout_duration,
                "attempt_window": self.config.attempt_window,
            },
        }


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_lockout_service_instance: Optional[AccountLockoutService] = None


async def get_lockout_service() -> AccountLockoutService:
    """Get or create the singleton AccountLockoutService.

    Usage:
        lockout_service = await get_lockout_service()
        status = await lockout_service.check_lockout(email)
    """
    global _lockout_service_instance
    if _lockout_service_instance is None:
        _lockout_service_instance = AccountLockoutService()
        await _lockout_service_instance.connect()
    return _lockout_service_instance


__all__ = [
    "AccountLockoutService",
    "LockoutConfig",
    "LockoutStatus",
    "get_lockout_service",
]
