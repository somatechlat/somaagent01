"""
UiSettingsStore service.

Provides a Redis-backed store for UI settings, used by AgentConfig loader.

"""

import json
import logging
from typing import Any, Dict

from django_redis import get_redis_connection

LOGGER = logging.getLogger(__name__)


class UiSettingsStore:
    """Redis-backed store for UI settings."""

    REDIS_KEY = "ui_settings:v1"

    def __init__(self):
        """Initialize store."""
        self.redis = get_redis_connection("default")

    async def ensure_schema(self) -> None:
        """Ensure default schema exists if not present."""
        if not self.redis.exists(self.REDIS_KEY):
            LOGGER.info("Initializing UI settings with default schema")
            default_settings = {
                "sections": [
                    {
                        "id": "agent_config",
                        "title": "Agent Configuration",
                        "fields": [
                            {
                                "id": "profile",
                                "label": "Agent Profile",
                                "type": "select",
                                "value": "enhanced",
                                "options": ["minimal", "standard", "enhanced", "max"],
                            },
                            {
                                "id": "code_exec_ssh_enabled",
                                "label": "Enable SSH Execution",
                                "type": "boolean",
                                "value": True,
                            },
                        ],
                    }
                ]
            }
            self.redis.set(self.REDIS_KEY, json.dumps(default_settings))

    async def get(self) -> Dict[str, Any]:
        """Get current settings."""
        data = self.redis.get(self.REDIS_KEY)
        if not data:
            await self.ensure_schema()
            data = self.redis.get(self.REDIS_KEY)

        if data:
            try:
                return json.loads(data)
            except json.JSONDecodeError as e:
                LOGGER.error(f"Failed to decode UI settings: {e}")
                return {}
        return {}

    async def update(self, settings: Dict[str, Any]) -> None:
        """Update settings."""
        self.redis.set(self.REDIS_KEY, json.dumps(settings))
