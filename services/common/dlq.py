"""Dead Letter Queue helper for Kafka topics."""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional

from services.common.event_bus import KafkaEventBus

LOGGER = logging.getLogger(__name__)


class DeadLetterQueue:
    """Publish failed events to a ``*.dlq`` Kafka topic."""

    def __init__(self, source_topic: str, bus: Optional[KafkaEventBus] = None) -> None:
        self.source_topic = source_topic
        self.dlq_topic = f"{source_topic}.dlq"
        self.bus = bus or KafkaEventBus()

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
            await self.bus.publish(self.dlq_topic, payload)
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
                    "original_topic": original_topic
                }
            )
