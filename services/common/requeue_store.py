"""Redis-backed requeue store for blocked policy events."""

from __future__ import annotations

import json
import os
from typing import Any, Optional

from services.common.admin_settings import ADMIN_SETTINGS
from services.common import runtime_config as cfg

import redis.asyncio as redis


class RequeueStore:
    def __init__(
        self,
        url: Optional[str] = None,
        *,
        prefix: Optional[str] = None,
    ) -> None:
        # Resolve Redis URL with environment variable expansion to support values like
        # REDIS_URL=redis://localhost:${REDIS_PORT}/0 in local .env files.
        # Resolve Redis URL using ADMIN_SETTINGS unless an explicit URL is provided.
        raw_url = url or ADMIN_SETTINGS.redis_url
        self.url = os.path.expandvars(raw_url)
        self.prefix = prefix or cfg.env("POLICY_REQUEUE_PREFIX", "policy:requeue")
        self.keyset = f"{self.prefix}:keys"
        self.client: redis.Redis = redis.from_url(self.url, decode_responses=True)

    def _key(self, identifier: str) -> str:
        return f"{self.prefix}:{identifier}"

    @classmethod
    def from_settings(cls, settings: Any) -> "RequeueStore":
        """Construct from settings object.

        Expects attributes or env fallbacks:
        - redis_url (str)
        - policy_requeue_prefix (str)
        """
        url = getattr(settings, "redis_url", None) or ADMIN_SETTINGS.redis_url
        prefix = getattr(settings, "policy_requeue_prefix", None) or cfg.env("POLICY_REQUEUE_PREFIX")
        return cls(url=url, prefix=prefix)

    async def add(self, identifier: str, event: dict[str, Any]) -> None:
        key = self._key(identifier)
        await self.client.set(key, json.dumps(event, ensure_ascii=False))
        await self.client.sadd(self.keyset, identifier)

    async def remove(self, identifier: str) -> None:
        key = self._key(identifier)
        await self.client.delete(key)
        await self.client.srem(self.keyset, identifier)

    async def get(self, identifier: str) -> Optional[dict[str, Any]]:
        key = self._key(identifier)
        raw = await self.client.get(key)
        if raw is None:
            return None
        return json.loads(raw)

    async def list(self) -> list[dict[str, Any]]:
        identifiers = await self.client.smembers(self.keyset)
        results: list[dict[str, Any]] = []
        for identifier in identifiers:
            data = await self.get(identifier)
            if data is not None:
                data["requeue_id"] = identifier
                results.append(data)
            else:
                await self.client.srem(self.keyset, identifier)
        return sorted(results, key=lambda item: item.get("timestamp", 0.0), reverse=True)

    # --- Backwards-compatibility aliases used by gateway ---
    async def list_requeue(self) -> list[dict[str, Any]]:
        return await self.list()

    async def get_requeue(self, requeue_id: str) -> Optional[dict[str, Any]]:
        return await self.get(requeue_id)

    async def delete_requeue(self, requeue_id: str) -> None:
        await self.remove(requeue_id)
