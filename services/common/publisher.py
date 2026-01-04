"""Health-aware publisher.

Usage:
        publisher = DurablePublisher(bus=KafkaEventBus(...))
        await publisher.publish("topic", payload, dedupe_key=event_id, session_id=..., tenant=...)

Notes:
- In unstable broker scenarios AIOKafka's producer.start()/send can hang awaiting
  metadata. To avoid blocking HTTP request handlers, we enforce a short,
  configurable timeout on the Kafka publish attempt. Control via env
  PUBLISH_KAFKA_TIMEOUT_SECONDS (default: 2.0 seconds).


"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Optional

from aiokafka.errors import KafkaError
from prometheus_client import Counter

from services.common.event_bus import KafkaEventBus
from services.common.messaging_utils import build_headers
import os

LOGGER = logging.getLogger(__name__)

PUBLISH_EVENTS = Counter(
    "durable_publish_total",
    "Durable publisher events",
    labelnames=("result",),
)


class DurablePublisher:
    def __init__(self, *, bus: KafkaEventBus) -> None:
        self.bus = bus

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
        correlation: Optional[str] = None,
    ) -> dict[str, Any]:
        """Publish a Kafka event directly.

        Returns {"published": bool, "enqueued": bool, "id": Optional[int]}.
        """
        timeout_s: float
        raw_timeout = os.environ.get("PUBLISH_KAFKA_TIMEOUT_SECONDS", "2.0")
        try:
            timeout_s = float(raw_timeout)
        except (TypeError, ValueError):
            timeout_s = 2.0
        try:
            hdrs = build_headers(
                tenant=tenant or (payload.get("metadata") or {}).get("tenant"),
                session_id=session_id or payload.get("session_id"),
                persona_id=payload.get("persona_id"),
                event_type=payload.get("type"),
                event_id=payload.get("event_id"),
                schema=payload.get("version") or payload.get("schema"),
                correlation=correlation or payload.get("correlation_id"),
            )

            await asyncio.wait_for(
                self.bus.publish(topic, payload, headers=hdrs), timeout=timeout_s
            )
            PUBLISH_EVENTS.labels("published").inc()
            return {"published": True, "enqueued": False, "id": None}
        except (asyncio.TimeoutError, KafkaError, Exception) as exc:
            PUBLISH_EVENTS.labels("failed").inc()
            LOGGER.warning(
                "Kafka publish failed",
                extra={
                    "error": str(exc),
                    "topic": topic,
                    "dedupe_key": dedupe_key,
                    "session_id": session_id,
                    "tenant": tenant,
                    "timeout_seconds": timeout_s,
                },
            )
            raise
