"""PKCE (Proof Key for Code Exchange) utilities for OAuth 2.0.


Per login-to-chat-journey design.md Section 3.1: PKCE

Implements:
- code_verifier generation (43-128 chars, cryptographically random)
- code_challenge computation (base64url(SHA256(code_verifier)))
- State parameter generation and validation

Personas:
- Security Auditor: Cryptographic security, OAuth 2.0 compliance
- Django Architect: Async Redis integration for state storage
- Performance Engineer: Efficient operations
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
import secrets
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Optional

import redis.asyncio as redis

logger = logging.getLogger(__name__)


# =============================================================================
# PKCE GENERATION
# =============================================================================


def generate_code_verifier(length: int = 64) -> str:
    """Generate a cryptographically random code_verifier.

    Per RFC 7636:
    - Length: 43-128 characters
    - Characters: [A-Z] / [a-z] / [0-9] / "-" / "." / "_" / "~"

    Args:
        length: Length of verifier (43-128). Default 64.

    Returns:
        Random code_verifier string
    """
    if length < 43 or length > 128:
        raise ValueError("code_verifier length must be 43-128 characters")

    # Use URL-safe base64 encoding of random bytes
    # Each byte becomes ~1.33 base64 chars, so we need length * 0.75 bytes
    num_bytes = (length * 3) // 4 + 1
    random_bytes = secrets.token_bytes(num_bytes)

    # Base64url encode (no padding)
    verifier = base64.urlsafe_b64encode(random_bytes).decode("ascii").rstrip("=")

    # Truncate to exact length
    return verifier[:length]


def generate_code_challenge(code_verifier: str) -> str:
    """Generate code_challenge from code_verifier using S256 method.

    Per RFC 7636:
    code_challenge = BASE64URL(SHA256(code_verifier))

    Args:
        code_verifier: The code_verifier string

    Returns:
        Base64url-encoded SHA256 hash (no padding)
    """
    # SHA256 hash
    digest = hashlib.sha256(code_verifier.encode("ascii")).digest()

    # Base64url encode (no padding)
    challenge = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")

    return challenge


def generate_state() -> str:
    """Generate a cryptographically random state parameter.

    Per OAuth 2.0 spec:
    - Used to prevent CSRF attacks
    - Should be unpredictable

    Returns:
        32-byte random string (base64url encoded)
    """
    return secrets.token_urlsafe(32)


# =============================================================================
# OAUTH STATE STORAGE
# =============================================================================


@dataclass
class OAuthState:
    """OAuth state data stored in Redis.

    Per design.md Section 3.1:
    - state: Random state parameter
    - code_verifier: PKCE code verifier
    - redirect_uri: Callback URL
    - provider: OAuth provider (google, github)
    - created_at: Timestamp
    """

    state: str
    code_verifier: str
    redirect_uri: str
    provider: str
    created_at: str = ""

    def __post_init__(self):
        """Execute post init  .
            """

        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        """Convert to dictionary for Redis storage."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "OAuthState":
        """Create OAuthState from dictionary."""
        return cls(**data)


class OAuthStateStore:
    """Redis-backed OAuth state storage.

    Per design.md Section 3.1:
    - Key format: oauth_state:{state}
    - TTL: 10 minutes
    """

    STATE_TTL = 600  # 10 minutes
    STATE_PREFIX = "oauth_state:"

    def __init__(self, redis_url: Optional[str] = None):
        """Initialize OAuthStateStore.

        Args:
            redis_url: Redis connection URL. Defaults to REDIS_URL env var.
        """
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
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
            logger.info("OAuthStateStore connected to Redis")

    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            self._connected = False

    async def _ensure_connected(self) -> None:
        """Ensure Redis connection is established."""
        if not self._connected:
            await self.connect()

    def _make_key(self, state: str) -> str:
        """Build Redis key for OAuth state."""
        return f"{self.STATE_PREFIX}{state}"

    async def store_state(
        self,
        provider: str,
        redirect_uri: str,
    ) -> OAuthState:
        """Store OAuth state with PKCE parameters.

        Args:
            provider: OAuth provider (google, github)
            redirect_uri: Callback URL

        Returns:
            OAuthState with generated state and code_verifier
        """
        await self._ensure_connected()

        state = generate_state()
        code_verifier = generate_code_verifier()

        oauth_state = OAuthState(
            state=state,
            code_verifier=code_verifier,
            redirect_uri=redirect_uri,
            provider=provider,
        )

        key = self._make_key(state)

        await self._redis.setex(
            key,
            self.STATE_TTL,
            json.dumps(oauth_state.to_dict()),
        )

        logger.info(f"OAuth state stored: provider={provider}, state={state[:8]}...")

        return oauth_state

    async def get_state(self, state: str) -> Optional[OAuthState]:
        """Retrieve and validate OAuth state.

        Args:
            state: State parameter from callback

        Returns:
            OAuthState if valid, None if not found or expired
        """
        await self._ensure_connected()

        key = self._make_key(state)

        data = await self._redis.get(key)

        if data is None:
            logger.warning(f"OAuth state not found or expired: state={state[:8]}...")
            return None

        try:
            return OAuthState.from_dict(json.loads(data))
        except (json.JSONDecodeError, TypeError, KeyError) as e:
            logger.warning(f"Invalid OAuth state data: {e}")
            return None

    async def consume_state(self, state: str) -> Optional[OAuthState]:
        """Retrieve and delete OAuth state (one-time use).

        Args:
            state: State parameter from callback

        Returns:
            OAuthState if valid, None if not found or expired
        """
        await self._ensure_connected()

        key = self._make_key(state)

        # Get and delete atomically
        pipe = self._redis.pipeline()
        pipe.get(key)
        pipe.delete(key)
        results = await pipe.execute()

        data = results[0]

        if data is None:
            logger.warning(f"OAuth state not found or expired: state={state[:8]}...")
            return None

        try:
            oauth_state = OAuthState.from_dict(json.loads(data))
            logger.info(f"OAuth state consumed: provider={oauth_state.provider}")
            return oauth_state
        except (json.JSONDecodeError, TypeError, KeyError) as e:
            logger.warning(f"Invalid OAuth state data: {e}")
            return None


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_oauth_state_store_instance: Optional[OAuthStateStore] = None


async def get_oauth_state_store() -> OAuthStateStore:
    """Get or create the singleton OAuthStateStore.

    Usage:
        store = await get_oauth_state_store()
        state = await store.store_state("google", redirect_uri)
    """
    global _oauth_state_store_instance
    if _oauth_state_store_instance is None:
        _oauth_state_store_instance = OAuthStateStore()
        await _oauth_state_store_instance.connect()
    return _oauth_state_store_instance


__all__ = [
    "generate_code_verifier",
    "generate_code_challenge",
    "generate_state",
    "OAuthState",
    "OAuthStateStore",
    "get_oauth_state_store",
]