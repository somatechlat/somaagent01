"""MemoryGateway — one write path, one read path. SomaBrain is the ONLY bridge.

Agent → SomaBrain → somafractalmemory (store). The agent never talks to SFM.
Remember / recall / forget all go through SomaBrainAdapter (T-1).
"""

from __future__ import annotations

import logging
from datetime import datetime, UTC
from typing import Any, Callable

from services.common.adapters.somabrain_adapter import SomaBrainAdapter
from services.common.circuit_breaker import CircuitBreakerError, get_circuit_breaker
from services.common.memory_contract import (
    coord_key_material,
    embed_text,
    get_mem_embed_dim,
    make_coord,
    MemoryAck,
    MemoryHit,
    MemoryWrite,
)

LOGGER = logging.getLogger(__name__)

EmbedFn = Callable[[str, int], list[float]]

# The one memory replay topic. Memory WAL is the single replay authority for
# unacked writes (memory-replicator replays it into SomaBrain). PendingMemory
# is NOT a second writer — see SOMA degradation doctrine (T-6 / one authority).
MEMORY_WAL_TOPIC_DEFAULT = "memory.wal"


async def _durable_accept(
    *,
    topic: str,
    payload: dict[str, Any],
    idempotency_key: str,
    partition_key: str | None,
) -> Any:
    """T-6: record the write durably BEFORE the network hop.

    Lands in the local outbox (Postgres). A successful ``MemoryAck`` marks the
    row published without a second send; a failed hop leaves it pending so the
    outbox drain / memory-replicator can replay until acked.
    """
    from asgiref.sync import sync_to_async

    from admin.core.models.zdl import OutboxMessage

    def _create() -> Any:
        row, _ = OutboxMessage.objects.get_or_create(
            idempotency_key=idempotency_key,
            defaults={
                "topic": topic,
                "payload": payload,
                "partition_key": partition_key,
                "headers": {"source": "memory-gateway", "t6": "durable-before-hop"},
            },
        )
        return row

    return await sync_to_async(_create)()


async def _durable_complete(row: Any) -> None:
    """Mark a durable-accept row complete (ack.ok — never replayed)."""
    from asgiref.sync import sync_to_async

    await sync_to_async(row.mark_published)()


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
        # Hottest path in the agent: remember_text / recall must fail fast
        # when SomaBrain is down, not pile up timeouts (R-SCL-03).
        self._cb = get_circuit_breaker("memory_gateway", failure_threshold=5, reset_timeout=30.0)

    def _embed(self, text: str) -> list[float]:
        """Compute the shared embedding once for one memory."""
        return self._embed_fn(text, get_mem_embed_dim())

    async def remember(self, w: MemoryWrite) -> list[MemoryAck]:
        """Store one memory in SomaBrain only; one ack, never raises on store failure."""
        if w.embedding is None:
            w.embedding = self._embed(w.text)
        try:
            ack = await self._cb.call(self._brain.remember, w)
        except CircuitBreakerError as exc:
            LOGGER.warning("Memory write fast-failed (breaker open): %s", exc)
            ack = MemoryAck(coord=w.coord, store="somabrain", ok=False, error=str(exc))
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
        role: str | None = None,
    ) -> list[MemoryAck]:
        """Write through SomaBrain with seam coordinate convergence (T-1).

        T-6: the write is accepted into the local durable outbox **before** the
        network hop. ``MemoryAck.ok`` completes that record (never replayed).
        A failed hop leaves it pending — the one replay authority (memory WAL
        via outbox drain / memory-replicator) re-delivers until acked.
        """
        from services.common.memory_contract import get_memory_setting

        stamp = ts if ts is not None else datetime.now(UTC)
        material = coord_key_material(tenant_id, kind, stamp, text)
        coord = make_coord(tenant_id, kind, stamp, text)
        w = MemoryWrite(
            text=text,
            kind=kind,  # type: ignore[arg-type]
            tenant_id=tenant_id,
            session_id=session_id,
            coord=coord,
            embedding=self._embed(text),
            salience=salience,
            source=source,
        )
        wal_topic = str(get_memory_setting("MEMORY_WAL_TOPIC", MEMORY_WAL_TOPIC_DEFAULT))
        durable = await _durable_accept(
            topic=wal_topic,
            payload={
                "id": coord,
                "type": "memory.degraded",
                "role": "memory",
                "session_id": session_id,
                "tenant": tenant_id,
                "payload": {
                    "text": text,
                    "content": text,
                    "kind": kind,
                    "salience": salience,
                    "source": source,
                    "coord": coord,
                    "role": role,
                    "ts": stamp.isoformat() if hasattr(stamp, "isoformat") else str(stamp),
                },
            },
            idempotency_key=f"mem:{coord}",
            partition_key=tenant_id,
        )
        try:
            ack = await self._cb.call(
                self._brain.remember, w, key_material=material, role=role
            )
        except CircuitBreakerError as exc:
            LOGGER.warning("Memory write fast-failed (breaker open): %s", exc)
            ack = MemoryAck(coord=coord, store="somabrain", ok=False, error=str(exc))
        except Exception as exc:
            LOGGER.warning("Memory write to somabrain failed: %s", exc)
            ack = MemoryAck(coord=coord, store="somabrain", ok=False, error=str(exc))
        if ack.ok:
            try:
                await _durable_complete(durable)
            except Exception as dexc:
                LOGGER.warning("Durable-accept complete failed for coord=%s: %s", coord, dexc)
        return [ack]

    async def recall(self, query: str, k: int, tenant_id: str) -> list[MemoryHit]:
        """Recall from SomaBrain only. Raises MemoryRecallUnavailable on outage (no empty lie)."""
        try:
            hits = await self._cb.call(self._brain.recall, query, k, tenant_id)
        except CircuitBreakerError as exc:
            raise MemoryRecallUnavailable(str(exc)) from exc
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
