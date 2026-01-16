"""Redis-backed requeue store for blocked policy events."""

from __future__ import annotations

import json
import os
from typing import Any, Optional

import redis.asyncio as redis


class RequeueStore:
    """Requeuestore class implementation."""

    def __init__(
        self,
        url: Optional[str] = None,
        *,
        prefix: Optional[str] = None,
    ) -> None:
        """Create a Redis‑backed requeue store."""
        raw_url = url or os.environ.get("SA01_REDIS_URL", "")
        if not raw_url:
            raise ValueError("Redis URL is required for the requeue store.")
        self.url = os.path.expandvars(raw_url)
        self.prefix = prefix or os.environ.get("POLICY_REQUEUE_PREFIX", "policy:requeue")
        self.keyset = f"{self.prefix}:keys"
        if not self.url.startswith(("redis://", "rediss://", "unix://")):
            raise ValueError(f"Invalid Redis URL scheme for requeue store: {self.url!r}")
        self.client: redis.Redis = redis.from_url(self.url, decode_responses=True)

    def _key(self, identifier: str) -> str:
        """Execute key.

        Args:
            identifier: The identifier.
        """

        return f"{self.prefix}:{identifier}"

    @classmethod
    def from_settings(cls, settings: Any) -> "RequeueStore":
        """Construct from settings object.

        Expects attributes or env sources:
        - redis.url or redis_url (str)
        - policy_requeue_prefix (str)
        """
        redis_url = getattr(settings, "redis_url", None)
        if redis_url is None and hasattr(settings, "redis"):
            redis_url = getattr(settings.redis, "url", None)
        url = redis_url or os.environ.get("SA01_REDIS_URL", "")
        if not url:
            raise ValueError("Redis URL is required for the requeue store.")
        prefix = getattr(settings, "policy_requeue_prefix", None) or os.environ.get(
            "POLICY_REQUEUE_PREFIX"
        )
        return cls(url=url, prefix=prefix)

    async def add(self, identifier: str, event: dict[str, Any]) -> None:
        """Add a requeue entry."""
        key = self._key(identifier)
        await self.client.set(key, json.dumps(event, ensure_ascii=False))
        await self.client.sadd(self.keyset, identifier)

    async def remove(self, identifier: str) -> None:
        """Execute remove.

        Args:
            identifier: The identifier.
        """

        key = self._key(identifier)
        await self.client.delete(key)
        await self.client.srem(self.keyset, identifier)

    async def get(self, identifier: str) -> Optional[dict[str, Any]]:
        """Execute get.

        Args:
            identifier: The identifier.
        """

        key = self._key(identifier)
        raw = await self.client.get(key)
        if raw is None:
            return None
        return json.loads(raw)

    async def list(self) -> list[dict[str, Any]]:
        """Execute list."""

        identifiers = await self.client.smembers(self.keyset)
        results: list[dict[str, Any]] = []
        for identifier in identifiers:
            data = await self.get(identifier)
            if data is not None:
                data["requeue_id"] = identifier
                results.append(data)
            else:
                # Clean up stale reference
                await self.client.srem(self.keyset, identifier)
        return sorted(results, key=lambda item: item.get("timestamp", 0.0), reverse=True)

    async def resolve(self, requeue_id: str) -> bool:
        """Mark a requeue entry as resolved."""
        exists = await self.get(requeue_id)
        if not exists:
            return False
        await self.remove(requeue_id)
        return True

    async def delete(self, requeue_id: str) -> bool:
        """Delete a requeue entry."""
        exists = await self.get(requeue_id)
        if not exists:
            return False
        await self.remove(requeue_id)
        return True
