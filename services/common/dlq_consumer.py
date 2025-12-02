"""
DLQ consumer and alerting helper.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from prometheus_client import Counter

from services.common.event_bus import KafkaEventBus, KafkaSettings
from services.common.admin_settings import ADMIN_SETTINGS

DLQ_CONSUMED_TOTAL = Counter(
    "sa01_dlq_events_total",
    "Count of DLQ events consumed",
    ["topic", "result"],
)

LOGGER = logging.getLogger(__name__)


class DLQConsumer:
    def __init__(self, topic: str, group: str = "dlq-consumer") -> None:
        self.topic = topic
        self.group = group
        self.bus = KafkaEventBus(
            KafkaSettings(
                bootstrap_servers=ADMIN_SETTINGS.kafka_bootstrap_servers,
                security_protocol="PLAINTEXT",
            )
        )

    async def start(self) -> None:
        await self.bus.consume(self.topic, self.group, self._handle_event)

    async def _handle_event(self, event: Dict[str, Any]) -> None:
        try:
            LOGGER.error("DLQ event", extra={"topic": self.topic, "event": event})
            DLQ_CONSUMED_TOTAL.labels(self.topic, "seen").inc()
        except Exception as exc:
            LOGGER.exception("DLQ consumer failed", extra={"error": str(exc)})
            DLQ_CONSUMED_TOTAL.labels(self.topic, "error").inc()
