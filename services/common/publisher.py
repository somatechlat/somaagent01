
"""Usage:
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
    ) -> dict[str, Any]:
        """Publish to Kafka.

        the system will never fall back to the outbox. If Kafka publishing fails,
        the exception propagates to the caller. Returns a dict with
        {"published": bool, "enqueued": bool, "id": Optional[int]}. ``enqueued``
        will always be ``False`` under the new semantics.
        """
        # Apply a bounded timeout to avoid hanging request paths on metadata waits
        timeout_s: float
        try:
            from services.common import runtime_config as cfg

            timeout_s = float(
                cfg.env("SA01_KAFKA_PUBLISH_TIMEOUT_SECONDS")
                or cfg.env("PUBLISH_KAFKA_TIMEOUT_SECONDS", "2.0")
                or "2.0"
            )
        except Exception:
            timeout_s = 2.0
        # Compute unified headers for Kafka and (if needed) for outbox persistence
        hdrs = self._build_headers(
            payload=payload, session_id=session_id, tenant=tenant, provided=headers
        )
        try:
            await asyncio.wait_for(
                self.bus.publish(topic, payload, headers=hdrs), timeout=timeout_s
            )
            PUBLISH_EVENTS.labels("published").inc()
            return {"published": True, "enqueued": False, "id": None}
        except (asyncio.TimeoutError, KafkaError, Exception) as exc:
            # No outbox fallback – surface the failure directly.
            PUBLISH_EVENTS.labels("failed").inc()
            from python.helpers.errors import MissingDependencyError

            LOGGER.error(
                "Kafka publish failed – no fallback enabled",
                extra={
                    "error": str(exc),
                    "topic": topic,
                    "timeout_seconds": timeout_s,
                },
            )
            raise MissingDependencyError(
                f"Failed to publish to Kafka topic '{topic}': {exc}"
            ) from exc
