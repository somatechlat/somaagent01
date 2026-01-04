"""
DLQ consumer and alerting helper.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict

from prometheus_client import Counter

from services.common.event_bus import KafkaEventBus, KafkaSettings

DLQ_CONSUMED_TOTAL = Counter(
    "sa01_dlq_events_total",
    "Count of DLQ events consumed",
    ["topic", "result"],
)

LOGGER = logging.getLogger(__name__)


class DLQConsumer:
    """Dlqconsumer class implementation."""

    def __init__(self, topic: str, group: str = "dlq-consumer") -> None:
        """Initialize the instance."""

        self.topic = topic
        self.group = group
        kafka_cfg = os.environ.kafka
        self.bus = KafkaEventBus(
            KafkaSettings(
                bootstrap_servers=kafka_cfg.bootstrap_servers,
                security_protocol=kafka_cfg.security_protocol,
                sasl_mechanism=kafka_cfg.sasl_mechanism,
                sasl_username=kafka_cfg.sasl_username,
                sasl_password=kafka_cfg.sasl_password,
            )
        )

    async def start(self) -> None:
        """Execute start."""

        await self.bus.consume(self.topic, self.group, self._handle_event)

    async def _handle_event(self, event: Dict[str, Any]) -> None:
        """Execute handle event.

        Args:
            event: The event.
        """

        try:
            LOGGER.error("DLQ event", extra={"topic": self.topic, "event": event})
            DLQ_CONSUMED_TOTAL.labels(self.topic, "seen").inc()
        except Exception as exc:
            LOGGER.exception("DLQ consumer failed", extra={"error": str(exc)})
            DLQ_CONSUMED_TOTAL.labels(self.topic, "error").inc()
