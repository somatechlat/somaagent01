"""MemoryGateway — one write path, one read path. SomaBrain is the ONLY bridge.

Agent → SomaBrain → somafractalmemory (store). The agent never talks to SFM.
Remember / recall / forget all go through SomaBrainAdapter (T-1).
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Callable

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
    """Brain-backed MemoryGateway. SomaBrain is the sole store bridge.

    Historical name: there is no fan-out. Hot path is SomaBrain only.
    """

    def __init__(
        self,
        brain: SomaBrainAdapter,
        *,
        embed_fn: EmbedFn | None = None,
    ) -> None:
        """Initialize with the SomaBrain adapter and optional embedder override."""
        self._brain = brain
        self._embed_fn: EmbedFn = embed_fn or embed_text

    def _embed(self, text: str) -> list[float]:
        """Compute the shared embedding once for one memory."""
        return self._embed_fn(text, get_mem_embed_dim())

    async def remember(self, w: MemoryWrite) -> list[MemoryAck]:
        """Store one memory in SomaBrain only; one ack, never raises on store failure."""
        if w.embedding is None:
            w.embedding = self._embed(w.text)
        try:
            ack = await self._brain.remember(w)
        except Exception as exc:
            LOGGER.warning("Memory write to somabrain failed: %s", exc)
            ack = MemoryAck(coord=w.coord, store="somabrain", ok=False, error=str(exc))
        return [ack]

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
        """Write through SomaBrain with seam coordinate convergence (T-1)."""
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
        try:
            ack = await self._brain.remember(w, key_material=material)
        except Exception as exc:
            LOGGER.warning("Memory write to somabrain failed: %s", exc)
            ack = MemoryAck(coord=w.coord, store="somabrain", ok=False, error=str(exc))
        return [ack]

    async def recall(self, query: str, k: int, tenant_id: str) -> list[MemoryHit]:
        """Recall from SomaBrain only. Raises MemoryRecallUnavailable on outage (no empty lie)."""
        hits = await self._brain.recall(query, k, tenant_id)
        ranked = sorted(hits, key=lambda h: h.score, reverse=True)
        return ranked[: max(1, int(k))]

    async def forget(self, coord: str, tenant_id: str) -> bool:
        """Forget via SomaBrain only (T-1). True when deleted."""
        return await self._brain.forget(coord, tenant_id)

    async def close(self) -> None:
        """Close SomaBrain client."""
        await self._brain.close()


def build_memory_gateway(
    *,
    somabrain_url: str | None = None,
    timeout: float | None = None,
    embed_fn: EmbedFn | None = None,
    somabrain_token: str | None = None,
) -> FanoutMemoryGateway:
    """Build a SomaBrain-only gateway. Raises MemoryConfigurationError if URL unset."""
    return FanoutMemoryGateway(
        SomaBrainAdapter(somabrain_url, token=somabrain_token, timeout=timeout),
        embed_fn=embed_fn,
    )


_memory_gateway_instance: FanoutMemoryGateway | None = None


def get_memory_gateway() -> FanoutMemoryGateway:
    """Get or create the singleton FanoutMemoryGateway (SomaBrain only)."""
    global _memory_gateway_instance
    if _memory_gateway_instance is None:
        _memory_gateway_instance = build_memory_gateway()
    return _memory_gateway_instance


__all__ = [
    "FanoutMemoryGateway",
    "build_memory_gateway",
    "get_memory_gateway",
]
