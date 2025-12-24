"""Dead Letter Queue helper for Kafka topics."""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional

from services.common.event_bus import KafkaEventBus
from services.common.publisher import DurablePublisher
from services.common.outbox import OutboxPublisher
import os
from prometheus_client import Counter, Histogram

LOGGER = logging.getLogger(__name__)

DLQ_EVENTS = Counter(
    "dlq_events_total",
    "DLQ forwarding results",
    labelnames=("result",),
)
COMPENSATIONS_TOTAL = Counter(
    "compensations_total",
    "Compensating actions executed",
    labelnames=("source", "status"),
)
ROLLBACK_LATENCY = Histogram(
    "rollback_latency_seconds",
    "Latency of rollback/compensation paths",
    buckets=[0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10],
)


class DeadLetterQueue:
    """Publish failed events to a ``*.dlq`` Kafka topic."""

    def __init__(
        self,
        source_topic: str,
        bus: Optional[KafkaEventBus] = None,
        publisher: Optional[DurablePublisher] = None,
    ) -> None:
        self.source_topic = source_topic
        self.dlq_topic = f"{source_topic}.dlq"
        self._use_outbox = os.environ.get("SA01_USE_OUTBOX", "false").lower() == "true"
        self._outbox = OutboxPublisher(bus=bus or KafkaEventBus()) if self._use_outbox else None
        self.publisher = publisher or DurablePublisher(bus=bus or KafkaEventBus())

    async def send_to_dlq(
        self,
        event: Dict[str, Any],
        error: Exception,
        *,
        retry_count: int = 0,
    ) -> None:
        payload = {
            "original_event": event,
            "source_topic": self.source_topic,
            "error_message": str(error),
            "error_type": type(error).__name__,
            "retry_count": retry_count,
            "timestamp": time.time(),
        }

        try:
            start = time.time()
            if self._use_outbox and self._outbox:
                outbox_id = await self._outbox.enqueue(
                    topic=self.dlq_topic,
                    payload=payload,
                    tenant=(event.get("metadata") or {}).get("tenant"),
                    session_id=str(event.get("session_id") or ""),
                    correlation=str(event.get("event_id") or event.get("task_id") or ""),
                )
                try:
                    await self._outbox.publish_once(outbox_id)
                    DLQ_EVENTS.labels("published").inc()
                    COMPENSATIONS_TOTAL.labels(self.dlq_topic, "published").inc()
                    ROLLBACK_LATENCY.observe(time.time() - start)
                except Exception:
                    LOG = logging.getLogger(__name__)
                    LOG.warning("DLQ outbox publish pending retry", extra={"outbox_id": outbox_id})
                    DLQ_EVENTS.labels("pending_retry").inc()
                    COMPENSATIONS_TOTAL.labels(self.dlq_topic, "pending_retry").inc()
            else:
                await self.publisher.publish(
                    self.dlq_topic,
                    payload,
                    dedupe_key=str(event.get("event_id") or event.get("task_id") or ""),
                    session_id=str(event.get("session_id") or ""),
                    tenant=(event.get("metadata") or {}).get("tenant"),
                )
                DLQ_EVENTS.labels("published").inc()
                COMPENSATIONS_TOTAL.labels(self.dlq_topic, "published").inc()
                ROLLBACK_LATENCY.observe(time.time() - start)
            LOGGER.warning(
                "Event forwarded to DLQ",
                extra={
                    "source_topic": self.source_topic,
                    "dlq_topic": self.dlq_topic,
                    "error": str(error),
                },
            )
        except Exception as dlq_error:
            LOGGER.error(
                "DLQ publish failed",
                extra={
                    "error": str(dlq_error),
                    "error_type": type(dlq_error).__name__,
                    "original_topic": self.source_topic,
                },
            )
            DLQ_EVENTS.labels("failed").inc()
            COMPENSATIONS_TOTAL.labels(self.dlq_topic, "failed").inc()
