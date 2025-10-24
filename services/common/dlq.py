"""Dead Letter Queue helper for Kafka topics."""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional

from services.common.event_bus import KafkaEventBus
from services.common.outbox_repository import OutboxStore
from services.common.publisher import DurablePublisher

LOGGER = logging.getLogger(__name__)


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
        if publisher is not None:
            self.publisher = publisher
        else:
            self.publisher = DurablePublisher(bus=bus or KafkaEventBus(), outbox=OutboxStore())

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
            await self.publisher.publish(
                self.dlq_topic,
                payload,
                dedupe_key=str(event.get("event_id") or event.get("task_id") or ""),
                session_id=str(event.get("session_id") or ""),
                tenant=(event.get("metadata") or {}).get("tenant"),
            )
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
