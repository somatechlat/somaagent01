"""Health-aware publisher with durable outbox fallback.

Usage:
        publisher = DurablePublisher(bus=KafkaEventBus(...), outbox=OutboxStore(...))
        await publisher.publish("topic", payload, dedupe_key=event_id, session_id=..., tenant=...)

Notes:
- In unstable broker scenarios AIOKafka's producer.start()/send can hang awaiting
    metadata. To avoid blocking HTTP request handlers, we enforce a short, configurable
    timeout on the Kafka publish attempt and fall back to the Postgres outbox when it
    elapses. Control via env PUBLISH_KAFKA_TIMEOUT_SECONDS (default: 2.0 seconds).
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, Optional

from aiokafka.errors import KafkaError
from prometheus_client import Counter

from services.common.event_bus import KafkaEventBus
from services.common.outbox_repository import OutboxStore

LOGGER = logging.getLogger(__name__)

PUBLISH_EVENTS = Counter(
    "durable_publish_total",
    "Durable publisher events",
    labelnames=("result",),
)


class DurablePublisher:
    def __init__(self, *, bus: KafkaEventBus, outbox: OutboxStore) -> None:
        self.bus = bus
        self.outbox = outbox

    def _build_headers(
        self,
        *,
        payload: dict[str, Any],
        session_id: Optional[str],
        tenant: Optional[str],
        provided: Optional[dict[str, Any]],
    ) -> dict[str, Any]:
        hdr: dict[str, Any] = dict(provided or {})
        # Prefer explicit args, fall back to payload metadata
        meta = payload.get("metadata") if isinstance(payload, dict) else None
        eff_tenant = tenant or (meta.get("tenant") if isinstance(meta, dict) else None)
        eff_session = session_id or payload.get("session_id")
        eff_persona = payload.get("persona_id")
        schema = payload.get("version") or "sa01-v1"
        event_type = payload.get("type")
        event_id = payload.get("event_id")
        if eff_tenant:
            hdr.setdefault("tenant_id", str(eff_tenant))
        if eff_session:
            hdr.setdefault("session_id", str(eff_session))
        if eff_persona:
            hdr.setdefault("persona_id", str(eff_persona))
        if schema:
            hdr.setdefault("schema", str(schema))
        if event_type:
            hdr.setdefault("event_type", str(event_type))
        if event_id:
            hdr.setdefault("event_id", str(event_id))
        return hdr

    async def publish(
        self,
        topic: str,
        payload: dict[str, Any],
        *,
        partition_key: Optional[str] = None,
        headers: Optional[dict[str, Any]] = None,
        dedupe_key: Optional[str] = None,
        session_id: Optional[str] = None,
        tenant: Optional[str] = None,
        fallback: bool = True,
    ) -> dict[str, Any]:
        """Try Kafka first, then fallback to Outbox if enabled.

        Returns a dict with {"published": bool, "enqueued": bool, "id": Optional[int]}.
        """
        # Apply a bounded timeout to avoid hanging request paths on metadata waits
        timeout_s: float
        try:
            timeout_s = float(os.getenv("PUBLISH_KAFKA_TIMEOUT_SECONDS", "2.0"))
        except Exception:
            timeout_s = 2.0
        # Compute unified headers for Kafka and (if needed) for outbox persistence
        hdrs = self._build_headers(
            payload=payload, session_id=session_id, tenant=tenant, provided=headers
        )
        try:
            await asyncio.wait_for(self.bus.publish(topic, payload, headers=hdrs), timeout=timeout_s)
            PUBLISH_EVENTS.labels("published").inc()
            return {"published": True, "enqueued": False, "id": None}
        except (asyncio.TimeoutError, KafkaError, Exception) as exc:
            if not fallback:
                PUBLISH_EVENTS.labels("failed").inc()
                raise
            # Fallback to outbox
            msg_id = await self.outbox.enqueue(
                topic=topic,
                payload=payload,
                partition_key=partition_key,
                headers=hdrs,
                dedupe_key=dedupe_key,
                session_id=session_id,
                tenant=tenant,
            )
            PUBLISH_EVENTS.labels("enqueued").inc()
            LOGGER.warning(
                "Kafka publish failed or timed out; enqueued to outbox",
                extra={
                    "error": str(exc),
                    "topic": topic,
                    "dedupe_key": dedupe_key,
                    "session_id": session_id,
                    "tenant": tenant,
                    "timeout_seconds": timeout_s,
                },
            )
            return {"published": False, "enqueued": True, "id": msg_id}
