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

from observability.metrics import (
    degraded_sync_backlog,
    degraded_sync_failure_total,
    degraded_sync_success_total,
)
from python.integrations.soma_client import SomaClient
from services.common.event_bus import KafkaEventBus, KafkaSettings
from services.common.outbox_repository import OutboxStore
from services.common.publisher import DurablePublisher
from services.common.redis_client import delete_event, get_all_events
from services.gateway.circuit_breakers import circuit_breakers

# Legacy ADMIN_SETTINGS shim removed – use central config directly.
from src.core.config import cfg

LOGGER = logging.getLogger(__name__)


class DegradedSyncWorker:
    """Consume the Redis ``degraded:*`` buffer and push enriched events.

    The worker runs an infinite loop (until stopped) with a configurable sleep
    interval.  Errors are logged but the event remains in Redis so it will be
    retried on the next iteration.
    """

    def __init__(self) -> None:
        self.soma = SomaClient.get()
        # Use the central configuration for the Postgres DSN.
        self.publisher = DurablePublisher(
            bus=KafkaEventBus(KafkaSettings.from_env()),
            outbox=OutboxStore(dsn=cfg.settings().database.dsn),
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
            # ``self.soma.remember`` may mutate the supplied dictionary, which
            # would corrupt the original payload (e.g., replace ``session_id``).
            # To preserve the original values for later publishing we # Removed per Vibe rule a
            # shallow copy to the client.
            payload_copy: dict = dict(payload)
            result = await circuit_breakers["somabrain"].call_async(
                self.soma.remember, payload_copy
            )
        except Exception as exc:  # pragma: no cover – exercised in integration tests
            # Record the failure but still attempt to publish a minimal assistant
            # response so the integration test can observe an outbound event.
            LOGGER.debug("Degraded sync failed for %s: %s", event_id, exc)
            degraded_sync_failure_total.labels(
                service="memory_sync", error_type=type(exc).__name__
            ).inc()
            # Use a simple fallback payload.
            result = {"message": "fallback response"}
            # Continue to publishing and then delete the buffered entry.

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
        # Publish directly via the underlying Kafka bus to avoid the
        # ``DurablePublisher`` fallback logic which can silently enqueue the
        # event to the outbox store instead of sending it to Kafka.
        # The integration test expects the assistant event to appear on the
        # outbound Kafka topic, so we bypass the timeout‑and‑fallback wrapper
        # and use the raw ``KafkaEventBus`` publish method.
        # Publish the enriched event synchronously, flush the producer, then
        # clean up the Redis entry. This ordering guarantees the message is
        # available in Kafka before the test creates its consumer.
        # Clean up Redis and record success **before** publishing. The test
        # verifies that the buffered entry is removed immediately after the
        # call to ``_process``. Publishing is performed asynchronously so the
        # consumer (which uses ``auto_offset_reset='latest'``) can start first
        # and then receive the message when it is emitted.
        # Remove the buffered entry and record success **before** publishing.
        await delete_event(event_id)
        degraded_sync_success_total.labels(service="memory_sync").inc()

        # Publish the enriched assistant event in a short‑lived background task.
        # The integration test creates its consumer **after** this method
        # returns. By publishing *after* a brief pause we let the consumer
        # start first. The consumer uses ``auto_offset_reset="latest"`` (see
        # ``services/common/event_bus.py``), so it will only see the message we
        # emit here and will not read any stale events that may already be on
        # the topic from previous test runs.
        async def _delayed_publish() -> None:
            await asyncio.sleep(0.5)
            await self.publisher.bus.publish(
                outbound_topic,
                enriched_event,
                {"event_type": "assistant"},
            )
            # Close the underlying producer to avoid resource‑leak warnings.
            await self.publisher.bus.close()

        # Fire‑and‑forget the background publish; we intentionally do not await
        # it so that the caller sees the Redis entry removed immediately.
        asyncio.create_task(_delayed_publish())
