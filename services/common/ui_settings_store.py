"""
UiSettingsStore service.

Provides a Redis-backed store for UI settings, used by AgentConfig loader.

"""

import json
import logging
from typing import Any, Dict

from services.common.redis_pool import get_async_redis_pool

LOGGER = logging.getLogger(__name__)


class UiSettingsStore:
    """Redis-backed store for UI settings."""

    REDIS_KEY = "ui_settings:v1"

    def __init__(self):
        """Initialize store."""
        self.redis = get_async_redis_pool()

    async def ensure_schema(self) -> None:
        """Ensure default schema exists if not present.

        VIBE: No hardcoded UI defaults. If no schema is configured, leave the
        store empty so callers know configuration is required.
        """
        exists = await self.redis.exists(self.REDIS_KEY)
        if not exists:
            LOGGER.info("UI settings schema not configured; skipping default injection")
            await self.redis.set(self.REDIS_KEY, json.dumps({"sections": []}))

    async def get(self) -> Dict[str, Any]:
        """Get current settings."""
        data = await self.redis.get(self.REDIS_KEY)
        if not data:
            await self.ensure_schema()
            data = await self.redis.get(self.REDIS_KEY)

        if data:
            try:
                return json.loads(data)
            except json.JSONDecodeError as e:
                LOGGER.error('Failed to decode UI settings: %s', e)
                return {}
        return {}

    async def update(self, settings: Dict[str, Any]) -> None:
        """Update settings."""
        await self.redis.set(self.REDIS_KEY, json.dumps(settings))
