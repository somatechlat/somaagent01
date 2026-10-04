"""Health-aware publisher with a local durable buffer in front of Kafka.

Usage:
        publisher = DurablePublisher(bus=KafkaEventBus(...))
        await publisher.publish("topic", payload, dedupe_key=event_id, session_id=..., tenant=...)

Notes:
- In unstable broker scenarios AIOKafka's producer.start()/send can hang awaiting
  metadata. To avoid blocking HTTP request handlers, we enforce a short,
  configurable timeout on the Kafka publish attempt. Control via env
  PUBLISH_KAFKA_TIMEOUT_SECONDS (default: 2.0 seconds).
- On broker failure the write lands in ``OutboxMessage`` (local durable buffer)
  and is returned as ``enqueued``; ``publish_outbox`` drains it to Kafka.
  A broker blip cannot lose a write.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Optional

from aiokafka.errors import KafkaError
from prometheus_client import Counter

from config.settings_registry import SettingsRegistry
from services.common.event_bus import KafkaEventBus
from services.common.messaging_utils import build_headers

LOGGER = logging.getLogger(__name__)

PUBLISH_EVENTS = Counter(
    "durable_publish_total",
    "Durable publisher events",
    labelnames=("result",),
)

_durable_publisher_instance: Optional[DurablePublisher] = None


async def get_durable_publisher() -> Optional[DurablePublisher]:
    """Get or create the singleton DurablePublisher.

    Returns None if Kafka is not configured.
    """
    global _durable_publisher_instance
    if _durable_publisher_instance is None:
        from services.common.event_bus import KafkaSettings

        settings = SettingsRegistry.get()
        bootstrap = settings.kafka_bootstrap_servers
        if not bootstrap:
            LOGGER.warning("KAFKA_BOOTSTRAP_SERVERS not set — DurablePublisher unavailable")
            return None

        bus = KafkaEventBus(
            KafkaSettings(
                bootstrap_servers=bootstrap,
                security_protocol=settings.kafka_security_protocol,
                sasl_mechanism=settings.kafka_sasl_mechanism or None,
                sasl_username=settings.kafka_sasl_username or None,
                sasl_password=settings.kafka_sasl_password or None,
            )
        )
        _durable_publisher_instance = DurablePublisher(bus=bus)
    return _durable_publisher_instance


class DurablePublisher:
    """Durablepublisher class implementation."""

    def __init__(self, *, bus: KafkaEventBus) -> None:
        """Initialize the instance."""

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
        settings = SettingsRegistry.get()
        timeout_s: float = settings.publish_kafka_timeout_seconds
        hdrs: Optional[dict[str, Any]] = None
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
                "Kafka publish failed — landing in local durable outbox",
                extra={
                    "error": str(exc),
                    "topic": topic,
                    "dedupe_key": dedupe_key,
                    "session_id": session_id,
                    "tenant": tenant,
                    "timeout_seconds": timeout_s,
                },
            )
            # Local durable buffer in front of Kafka: a broker blip must not
            # lose the write. ``publish_outbox`` drains this row to Kafka.
            row = await self._enqueue_local(
                topic=topic,
                payload=payload,
                dedupe_key=dedupe_key,
                headers=hdrs,
            )
            return {"published": False, "enqueued": True, "id": row.id if row else None}

    async def _enqueue_local(
        self,
        *,
        topic: str,
        payload: dict[str, Any],
        dedupe_key: Optional[str],
        headers: Optional[dict[str, Any]],
    ) -> Any:
        """Write one OutboxMessage so the event survives a Kafka outage."""
        import uuid as _uuid

        from asgiref.sync import sync_to_async

        from admin.core.models.zdl import OutboxMessage

        key = dedupe_key or f"{topic}:{_uuid.uuid4().hex}"

        def _create() -> Any:
            row, _ = OutboxMessage.objects.get_or_create(
                idempotency_key=key,
                defaults={
                    "topic": topic,
                    "payload": payload,
                    "headers": dict(headers or {}),
                },
            )
            return row

        try:
            return await sync_to_async(_create)()
        except Exception as exc:
            LOGGER.error(
                "Local durable buffer write failed — event cannot be retained",
                extra={"topic": topic, "dedupe_key": key, "error": str(exc)},
            )
            raise
