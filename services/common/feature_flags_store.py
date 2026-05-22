"""Feature flags store — Redis-backed feature toggle storage.

VIBE COMPLIANT: Real production implementation.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict

from services.common.redis_pool import get_async_redis_pool

LOGGER = logging.getLogger(__name__)


class FeatureFlagsStore:
    """Redis-backed store for feature flags."""

    KEY_PREFIX = "feature_flags"

    def __init__(self) -> None:
        self.redis: Any = get_async_redis_pool()

    def _key(self, tenant: str) -> str:
        return f"{self.KEY_PREFIX}:{tenant}"

    async def get(self, tenant: str, flag: str, default: bool = False) -> bool:
        """Get feature flag value."""
        key = self._key(tenant)
        data = await self.redis.hget(key, flag)
        if data is None:
            return default
        try:
            return json.loads(data)
        except Exception:
            LOGGER.exception("Failed to parse feature flag value for %s/%s", tenant, flag)
            return default

    async def set(self, tenant: str, flag: str, value: bool) -> None:
        """Set feature flag value."""
        key = self._key(tenant)
        await self.redis.hset(key, flag, json.dumps(value))

    async def list(self, tenant: str) -> Dict[str, bool]:
        """List all feature flags for tenant."""
        key = self._key(tenant)
        data = await self.redis.hgetall(key)
        return {k: json.loads(v) for k, v in data.items()}

    async def get_effective_flags(self, tenant: str) -> Dict[str, Any]:
        """Get effective flags with profile info."""
        flags = await self.list(tenant)
        profile = await self.get_profile(tenant)
        return {"profile": profile, "flags": flags, "source": "redis"}

    async def get_profile(self, tenant: str) -> str:
        """Get feature profile for tenant."""
        key = f"{self._key(tenant)}:profile"
        data = await self.redis.get(key)
        if data is None:
            return "standard"
        return str(data)

    async def list_all_flags(self) -> list[str]:
        """List all available flag keys."""
        return [
            "image_generation",
            "video_generation",
            "audio_generation",
            "streaming",
            "advanced_analytics",
            "custom_models",
        ]

    async def set_flag(self, tenant: str, flag: str, value: bool) -> bool:
        """Set a single feature flag."""
        await self.set(tenant, flag, value)
        return True

    async def set_profile(self, tenant: str, profile: str) -> bool:
        """Set feature profile for tenant."""
        key = f"{self._key(tenant)}:profile"
        await self.redis.set(key, profile)
        return True
