"""PostgreSQL-backed outbox with Kafka publish + tombstone support.

Provides:
- Schema management (`ensure_schema`)
- Atomic enqueue of events with headers
- Publish + delete in one call; if publish fails, rows remain for retry
- Tombstone publishing for compensations
- Optional bulk flush for pending rows
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict, Optional

import asyncpg
from prometheus_client import Counter, Histogram

from services.common.event_bus import KafkaEventBus
from services.common.messaging_utils import build_headers
from src.core.config import cfg

LOG = logging.getLogger(__name__)

OUTBOX_EVENTS = Counter("outbox_events_total", "Outbox events", ["result"])
OUTBOX_LATENCY = Histogram(
    "outbox_publish_latency_seconds",
    "Latency from enqueue to publish",
    buckets=[0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10],
)


class OutboxPublisher:
    def __init__(self, dsn: Optional[str] = None, bus: Optional[KafkaEventBus] = None) -> None:
        self._dsn = dsn or cfg.settings().database.dsn
        self._bus = bus or KafkaEventBus()

    async def _conn(self) -> asyncpg.Connection:
        return await asyncpg.connect(self._dsn)

    async def ensure_schema(self) -> None:
        conn = await self._conn()
        try:
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS outbox (
                    id SERIAL PRIMARY KEY,
                    topic TEXT NOT NULL,
                    payload JSONB NOT NULL,
                    headers JSONB NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                CREATE INDEX IF NOT EXISTS outbox_created_at_idx ON outbox (created_at);
                """
            )
        finally:
            await conn.close()

    async def enqueue(
        self,
        *,
        topic: str,
        payload: Dict[str, Any],
        tenant: Optional[str] = None,
        session_id: Optional[str] = None,
        persona_id: Optional[str] = None,
        correlation: Optional[str] = None,
        event_id: Optional[str] = None,
    ) -> int:
        await self.ensure_schema()
        headers = build_headers(
            tenant=tenant or (payload.get("metadata") or {}).get("tenant"),
            session_id=session_id or payload.get("session_id"),
            persona_id=persona_id or payload.get("persona_id"),
            event_type=payload.get("type"),
            event_id=event_id or payload.get("event_id"),
            schema=payload.get("version") or payload.get("schema"),
            correlation=correlation or payload.get("correlation_id"),
        )
        conn = await self._conn()
        try:
            row_id = await conn.fetchval(
                "INSERT INTO outbox (topic, payload, headers) VALUES ($1, $2, $3) RETURNING id",
                topic,
                json.dumps(payload),
                json.dumps(headers),
            )
            return int(row_id)
        finally:
            await conn.close()

    async def publish_once(self, outbox_id: int) -> bool:
        """Publish a single outbox row; delete on success."""
        conn = await self._conn()
        try:
            row = await conn.fetchrow("SELECT * FROM outbox WHERE id = $1", outbox_id)
            if not row:
                return False
            payload = json.loads(row["payload"])
            headers = json.loads(row["headers"])
            start = asyncio.get_event_loop().time()
            await self._bus.publish(row["topic"], payload, headers=headers)
            await conn.execute("DELETE FROM outbox WHERE id = $1", outbox_id)
            OUTBOX_EVENTS.labels("published").inc()
            OUTBOX_LATENCY.observe(asyncio.get_event_loop().time() - start)
            return True
        finally:
            await conn.close()

    async def publish_pending(self, limit: int = 100) -> int:
        """Publish up to `limit` pending rows."""
        conn = await self._conn()
        published = 0
        try:
            rows = await conn.fetch(
                "SELECT * FROM outbox ORDER BY created_at ASC LIMIT $1",
                limit,
            )
            for row in rows:
                payload = json.loads(row["payload"])
                headers = json.loads(row["headers"])
                start = asyncio.get_event_loop().time()
                try:
                    await self._bus.publish(row["topic"], payload, headers=headers)
                    await conn.execute("DELETE FROM outbox WHERE id = $1", row["id"])
                    OUTBOX_EVENTS.labels("published").inc()
                    OUTBOX_LATENCY.observe(asyncio.get_event_loop().time() - start)
                    published += 1
                except Exception as exc:
                    OUTBOX_EVENTS.labels("failed").inc()
                    LOG.warning("Outbox publish failed", extra={"id": row["id"], "error": str(exc)})
            return published
        finally:
            await conn.close()

    async def tombstone(
        self,
        *,
        topic: str,
        key: str,
        reason: Optional[str] = None,
        tenant: Optional[str] = None,
        session_id: Optional[str] = None,
        persona_id: Optional[str] = None,
        correlation: Optional[str] = None,
    ) -> None:
        headers = build_headers(
            tenant=tenant,
            session_id=session_id,
            persona_id=persona_id,
            event_type="tombstone",
            event_id=None,
            schema=None,
            correlation=correlation,
        )
        if reason:
            headers["tombstone_reason"] = reason
        start = asyncio.get_event_loop().time()
        await self._bus.publish(topic, None, headers=headers, key=key)
        OUTBOX_EVENTS.labels("tombstone").inc()
        OUTBOX_LATENCY.observe(asyncio.get_event_loop().time() - start)
