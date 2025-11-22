"""Background worker that syncs events buffered in Redis to Somabrain.

The regular ``MemorySyncWorker`` processes items from the ``memory_write_outbox``
table.  When Somabrain is unavailable the gateway stores raw events in the
Redis transient buffer via ``services.common.degraded_persist``.  This worker
periodically reads those buffered events, attempts enrichment through Somabrain,
publishes the enriched assistant event to the outbound Kafka topic, and removes
the entry from Redis on success.

All configuration values are read from the central ``cfg`` object – no hard‑
coded URLs or thresholds.  The Somabrain call is wrapped with the existing
``circuit_breakers['somabrain']`` so failures respect the circuit‑breaker
state and back‑off is applied automatically.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Dict

from src.core.config import cfg
from services.common.admin_settings import ADMIN_SETTINGS
from services.common.event_bus import KafkaEventBus, KafkaSettings
from services.common.publisher import DurablePublisher
from services.common.outbox_repository import OutboxStore
from services.gateway.circuit_breakers import circuit_breakers
from services.common.redis_client import get_all_events, delete_event
from python.integrations.soma_client import SomaClient, SomaClientError
from observability.metrics import (
    degraded_sync_success_total,
    degraded_sync_failure_total,
    degraded_sync_backlog,
)

LOGGER = logging.getLogger(__name__)


class DegradedSyncWorker:
    """Consume the Redis ``degraded:*`` buffer and push enriched events.

    The worker runs an infinite loop (until stopped) with a configurable sleep
    interval.  Errors are logged but the event remains in Redis so it will be
    retried on the next iteration.
    """

    def __init__(self) -> None:
        self.soma = SomaClient.get()
        self.publisher = DurablePublisher(
            bus=KafkaEventBus(KafkaSettings.from_env()),
            outbox=OutboxStore(dsn=ADMIN_SETTINGS.postgres_dsn),
        )
        self.interval = float(cfg.env("DEGRADED_SYNC_INTERVAL_SECONDS", "2"))
        self._stop = asyncio.Event()

    async def start(self) -> None:
        while not self._stop.is_set():
            events: Dict[str, dict] = await get_all_events()
            # Update backlog gauge before processing.
            degraded_sync_backlog.labels(service="memory_sync").set(len(events))
            if not events:
                await asyncio.sleep(self.interval)
                continue
            for event_id, payload in events.items():
                await self._process(event_id, payload)
            await asyncio.sleep(self.interval)

    async def stop(self) -> None:
        self._stop.set()

    async def _process(self, event_id: str, payload: dict) -> None:
        """Enrich a single buffered event via Somabrain.

        On success the enriched assistant event is published to the outbound
        topic and the Redis entry is deleted.  On any exception the event is
        left in Redis for a later retry.
        """
        try:
            # Use the circuit‑breaker to avoid hammering a down Somabrain.
            result = await circuit_breakers["somabrain"].call_async(self.soma.remember, payload)
        except Exception as exc:  # pragma: no cover – exercised in integration tests
            LOGGER.debug("Degraded sync failed for %s: %s", event_id, exc)
            degraded_sync_failure_total.labels(service="memory_sync", error_type=type(exc).__name__).inc()
            return

        outbound_topic = cfg.env("CONVERSATION_OUTBOUND", "conversation.outbound")
        enriched_event = {
            "event_id": str(uuid.uuid4()),
            "session_id": payload.get("session_id"),
            "persona_id": payload.get("persona_id"),
            "role": "assistant",
            "message": result.get("message", ""),
            "attachments": [],
            "metadata": payload.get("metadata", {}),
            "version": "sa01-v1",
            "trace_context": payload.get("trace_context", {}),
        }
        try:
            await self.publisher.publish(
                outbound_topic,
                enriched_event,
                dedupe_key=enriched_event["event_id"],
                session_id=payload.get("session_id"),
                tenant=payload.get("metadata", {}).get("tenant"),
            )
        except Exception:
            LOGGER.debug("Failed to publish enriched event for %s", event_id, exc_info=True)
            degraded_sync_failure_total.labels(service="memory_sync", error_type="publish_error").inc()
            return

        # Success – remove from Redis so it is not retried.
        await delete_event(event_id)
        degraded_sync_success_total.labels(service="memory_sync").inc()
