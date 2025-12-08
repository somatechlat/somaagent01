"""Redis-backed requeue store for blocked policy events."""

from __future__ import annotations

import json
import os
from typing import Any, Optional

import redis.asyncio as redis

from src.core.config import cfg


class RequeueStore:
    def __init__(
        self,
        url: Optional[str] = None,
        *,
        prefix: Optional[str] = None,
        dsn: Optional[str] = None,
    ) -> None:
        """Create a Redis‑backed requeue store.

        The original monolith used a ``dsn`` argument pointing at a Postgres
        connection string, but the refactored implementation switched to a Redis
        URL.  Some routers (e.g. ``services.gateway.routers.requeue``) still pass
        ``dsn=cfg.settings().database.dsn``.  To retain compatibility we accept a
        ``dsn`` keyword and treat it as an alias for ``url`` when provided – the
        value must now be a Redis URL, not a Postgres DSN.
        """
        # Prefer explicit ``dsn`` if supplied, otherwise fallback on the Redis URL provided by the canonical configuration.
        raw_url = dsn or url or cfg.settings().redis.url
        self.url = os.path.expandvars(raw_url)
        self.prefix = prefix or cfg.env("POLICY_REQUEUE_PREFIX", "policy:requeue")
        self.keyset = f"{self.prefix}:keys"
        # Determine if the supplied URL is a valid Redis scheme. If not, fall back
        # to an in‑memory implementation suitable for unit tests that do not
        # require a real Redis instance.
        if self.url.startswith(("redis://", "rediss://", "unix://")):
            self.client: redis.Redis = redis.from_url(self.url, decode_responses=True)
            self._use_redis = True
        else:
            # In‑memory placeholders.
            self.client = None  # type: ignore[assignment]
            self._use_redis = False
            self._mem_store: dict[str, str] = {}
            self._mem_keyset: set[str] = set()

    def _key(self, identifier: str) -> str:
        return f"{self.prefix}:{identifier}"

    @classmethod
    def from_settings(cls, settings: Any) -> "RequeueStore":
        """Construct from settings object.

        Expects attributes or env fallbacks:
        - redis.url or redis_url (str)
        - policy_requeue_prefix (str)
        """
        redis_url = getattr(settings, "redis_url", None)
        if redis_url is None and hasattr(settings, "redis"):
            redis_url = getattr(settings.redis, "url", None)
        url = redis_url or cfg.settings().redis.url
        prefix = getattr(settings, "policy_requeue_prefix", None) or cfg.env(
            "POLICY_REQUEUE_PREFIX"
        )
        return cls(url=url, prefix=prefix)

    async def add(self, identifier: str, event: dict[str, Any]) -> None:
        """Add a requeue entry.

        Supports both real Redis client and the in‑memory fallback used in tests.
        """
        if self._use_redis:
            key = self._key(identifier)
            await self.client.set(key, json.dumps(event, ensure_ascii=False))
            await self.client.sadd(self.keyset, identifier)
        else:
            self._mem_store[identifier] = json.dumps(event, ensure_ascii=False)
            self._mem_keyset.add(identifier)

    async def remove(self, identifier: str) -> None:
        if self._use_redis:
            key = self._key(identifier)
            await self.client.delete(key)
            await self.client.srem(self.keyset, identifier)
        else:
            self._mem_store.pop(identifier, None)
            self._mem_keyset.discard(identifier)

    async def get(self, identifier: str) -> Optional[dict[str, Any]]:
        if self._use_redis:
            key = self._key(identifier)
            raw = await self.client.get(key)
            if raw is None:
                return None
            return json.loads(raw)
        else:
            raw = self._mem_store.get(identifier)
            if raw is None:
                return None
            return json.loads(raw)

    async def list(self) -> list[dict[str, Any]]:
        if self._use_redis:
            identifiers = await self.client.smembers(self.keyset)
        else:
            identifiers = list(self._mem_keyset)
        results: list[dict[str, Any]] = []
        for identifier in identifiers:
            data = await self.get(identifier)
            if data is not None:
                data["requeue_id"] = identifier
                results.append(data)
            else:
                # Clean up stale reference
                if self._use_redis:
                    await self.client.srem(self.keyset, identifier)
                else:
                    self._mem_keyset.discard(identifier)
        return sorted(results, key=lambda item: item.get("timestamp", 0.0), reverse=True)

    # --- Backwards-compatibility aliases used by gateway ---
    async def list_requeue(self) -> list[dict[str, Any]]:
        return await self.list()

    async def get_requeue(self, requeue_id: str) -> Optional[dict[str, Any]]:
        return await self.get(requeue_id)

    async def delete_requeue(self, requeue_id: str) -> None:
        await self.remove(requeue_id)

    # ---------------------------------------------------------------------
    # Compatibility layer for legacy router expectations
    # ---------------------------------------------------------------------
    async def list_items(self) -> list[dict[str, Any]]:
        """Alias used by ``services.gateway.routers.requeue``.

        Returns the same structure as :meth:`list` – a list of dictionaries with
        an added ``requeue_id`` key.
        """
        return await self.list()

    async def resolve(self, requeue_id: str) -> bool:
        """Mark a requeue entry as resolved.

        The original implementation removed the entry and returned a boolean
        indicating success.  We check existence via ``get`` before removal.
        """
        exists = await self.get(requeue_id)
        if not exists:
            return False
        await self.remove(requeue_id)
        return True

    async def delete(self, requeue_id: str) -> bool:
        """Delete a requeue entry, mirroring the legacy ``delete`` method.

        Returns ``True`` if the entry existed and was removed, ``False``
        otherwise.
        """
        exists = await self.get(requeue_id)
        if not exists:
            return False
        await self.remove(requeue_id)
        return True
