"""MemoryGateway — one write path, one read path across both stores.

Implements the PLAN-TRIAD-SEAMLESS.md §1 gateway: embedding computed once in
the gateway and sent precomputed to both stores; ``remember`` fans out and
returns one ``MemoryAck`` per store (a single-store failure is a failed ack,
never an exception); ``recall`` merges both stores, dedupes by coordinate and
ranks by score.

Store dialects are isolated in the adapters:
    SomaBrainAdapter  → POST /memory/remember|recall
    SFMAdapter        → POST /memories|/memories/search, DELETE /memories/{coord}
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from typing import Callable

from services.common.adapters.sfm_adapter import SFMAdapter
from services.common.adapters.somabrain_adapter import SomaBrainAdapter
from services.common.memory_contract import (
    MemoryAck,
    MemoryHit,
    MemoryWrite,
    coord_key_material,
    embed_text,
    get_mem_embed_dim,
    make_coord,
)

LOGGER = logging.getLogger(__name__)

EmbedFn = Callable[[str, int], list[float]]


class FanoutMemoryGateway:
    """Fan-out implementation of the MemoryGateway protocol."""

    def __init__(
        self,
        brain: SomaBrainAdapter,
        sfm: SFMAdapter,
        *,
        embed_fn: EmbedFn | None = None,
    ) -> None:
        """Initialize with both store adapters and an optional embedder override."""

        self._brain = brain
        self._sfm = sfm
        self._embed_fn: EmbedFn = embed_fn or embed_text

    def _embed(self, text: str) -> list[float]:
        """Compute the shared embedding once for one memory."""

        return self._embed_fn(text, get_mem_embed_dim())

    async def remember(self, w: MemoryWrite) -> list[MemoryAck]:
        """Store one memory in both stores; one ack per store, never raises on store failure."""

        if w.embedding is None:
            w.embedding = self._embed(w.text)
        results = await asyncio.gather(
            self._brain.remember(w),
            self._sfm.remember(w),
            return_exceptions=True,
        )
        acks: list[MemoryAck] = []
        for store_name, result in zip(("somabrain", "somafractalmemory"), results):
            if isinstance(result, MemoryAck):
                acks.append(result)
            else:
                LOGGER.warning("Memory write to %s failed: %s", store_name, result)
                acks.append(
                    MemoryAck(
                        coord=w.coord,
                        store=store_name,
                        ok=False,
                        error=str(result),
                    )
                )
        return acks

    async def remember_text(
        self,
        text: str,
        *,
        tenant_id: str,
        kind: str = "episodic",
        ts: str | datetime | None = None,
        session_id: str | None = None,
        salience: float = 0.5,
        source: str = "agent-chat",
    ) -> list[MemoryAck]:
        """Convenience writer that also converges SomaBrain onto the seam coordinate.

        Computes ``make_coord`` once and passes the same key material to the
        brain, so its ``/memory/remember`` placement matches the SFM row key.
        """

        stamp = ts if ts is not None else datetime.now(UTC)
        material = coord_key_material(tenant_id, kind, stamp, text)
        w = MemoryWrite(
            text=text,
            kind=kind,
            tenant_id=tenant_id,
            session_id=session_id,
            coord=make_coord(tenant_id, kind, stamp, text),
            embedding=self._embed(text),
            salience=salience,
            source=source,
        )
        results = await asyncio.gather(
            self._brain.remember(w, key_material=material),
            self._sfm.remember(w),
            return_exceptions=True,
        )
        acks: list[MemoryAck] = []
        for store_name, result in zip(("somabrain", "somafractalmemory"), results):
            if isinstance(result, MemoryAck):
                acks.append(result)
            else:
                LOGGER.warning("Memory write to %s failed: %s", store_name, result)
                acks.append(
                    MemoryAck(coord=w.coord, store=store_name, ok=False, error=str(result))
                )
        return acks

    async def recall(self, query: str, k: int, tenant_id: str) -> list[MemoryHit]:
        """Merge hits from both stores, dedupe by coord, sort by score descending."""

        results = await asyncio.gather(
            self._brain.recall(query, k, tenant_id),
            self._sfm.recall(query, k, tenant_id),
            return_exceptions=True,
        )
        merged: dict[str, MemoryHit] = {}
        for result in results:
            if isinstance(result, BaseException):
                LOGGER.warning("Memory recall leg failed: %s", result)
                continue
            for hit in result:
                current = merged.get(hit.coord)
                if current is None or hit.score > current.score:
                    merged[hit.coord] = hit
        ranked = sorted(merged.values(), key=lambda h: h.score, reverse=True)
        return ranked[: max(1, int(k))]

    async def forget(self, coord: str, tenant_id: str) -> bool:
        """Forget a memory in both stores. True when at least one store deleted it."""

        results = await asyncio.gather(
            self._brain.forget(coord, tenant_id),
            self._sfm.forget(coord, tenant_id),
            return_exceptions=True,
        )
        deleted = False
        for store_name, result in zip(("somabrain", "somafractalmemory"), results):
            if isinstance(result, BaseException):
                LOGGER.warning("Memory forget on %s failed: %s", store_name, result)
                continue
            deleted = deleted or bool(result)
        return deleted

    async def close(self) -> None:
        """Close both store clients."""

        await asyncio.gather(self._brain.close(), self._sfm.close())


# =============================================================================
# FACTORY
# =============================================================================


def build_memory_gateway(
    *,
    somabrain_url: str | None = None,
    sfm_url: str | None = None,
    timeout: float | None = None,
    embed_fn: EmbedFn | None = None,
    somabrain_token: str | None = None,
    sfm_token: str | None = None,
) -> FanoutMemoryGateway:
    """Build a gateway with both adapters. Raises MemoryConfigurationError if a URL is unset.

    ``timeout=None`` means "use settings.MEM_HTTP_TIMEOUT" — the adapters
    resolve it, so no default is duplicated here (VIBE §4).
    """

    return FanoutMemoryGateway(
        SomaBrainAdapter(somabrain_url, token=somabrain_token, timeout=timeout),
        SFMAdapter(sfm_url, token=sfm_token, timeout=timeout),
        embed_fn=embed_fn,
    )


_memory_gateway_instance: FanoutMemoryGateway | None = None


def get_memory_gateway() -> FanoutMemoryGateway:
    """Get or create the singleton FanoutMemoryGateway."""

    global _memory_gateway_instance
    if _memory_gateway_instance is None:
        _memory_gateway_instance = build_memory_gateway()
    return _memory_gateway_instance


__all__ = [
    "FanoutMemoryGateway",
    "build_memory_gateway",
    "get_memory_gateway",
]
