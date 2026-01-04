"""Memory replication worker: consumes memory WAL and persists replica rows.

On failure, publishes to Kafka DLQ and records to Postgres DLQ store for
admin inspection. Exposes Prometheus metrics for throughput and lag.
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from typing import Any

# Django setup for logging and ORM
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "services.gateway.settings")
import django

django.setup()

from prometheus_client import Counter, Gauge, Histogram, start_http_server
from services.common.dlq_store import DLQStore, ensure_schema as ensure_dlq_schema

from services.common.dlq import DeadLetterQueue
from services.common.event_bus import KafkaEventBus, KafkaSettings
from services.common.tracing import setup_tracing
from services.memory_replicator.service import (
    ensure_schema as ensure_replica_schema,
    MemoryReplicaStore,
)

LOGGER = logging.getLogger(__name__)

# Retrieve unified settings from central configuration.
# Django settings used instead
# OTLP endpoint is now under the external configuration section.
setup_tracing("memory-replicator", endpoint=SERVICE_SETTINGS.external.otlp_endpoint)

_METRICS_STARTED = False


REPL_EVENTS = Counter(
    "memory_replicator_events_total",
    "Replication outcomes by result",
    labelnames=("result",),
)
REPL_LATENCY = Histogram(
    "memory_replicator_replication_seconds",
    "Time to handle a WAL event",
)
REPL_LAG = Gauge(
    "memory_replicator_lag_seconds",
    "Replication lag computed from wal_timestamp",
)


def ensure_metrics_server(settings: object) -> None:
    global _METRICS_STARTED
    if _METRICS_STARTED:
        return
    # Prefer admin-wide metrics configuration; fall back to provided defaults.
    default_port = int(getattr(os.environ.service, "metrics_port", 9403))
    default_host = str(getattr(os.environ.service, "metrics_host", "0.0.0.0"))
    port = int(os.environ.get("REPLICATOR_METRICS_PORT", str(default_port)))
    if port > 0:
        start_http_server(port, addr=os.environ.get("REPLICATOR_METRICS_HOST", default_host))
        LOGGER.info("Memory replicator metrics server started", extra={"port": port})
    else:
        LOGGER.warning("Memory replicator metrics disabled", extra={"port": port})
    _METRICS_STARTED = True


def _kafka_settings() -> KafkaSettings:
    # Centralise Kafka bootstrap configuration via ADMIN_SETTINGS.
    return KafkaSettings(
        bootstrap_servers=os.environ.get("SA01_KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
        security_protocol=os.environ.get("KAFKA_SECURITY_PROTOCOL", "PLAINTEXT"),
        sasl_mechanism=os.environ.get("KAFKA_SASL_MECHANISM"),
        sasl_username=os.environ.get("KAFKA_SASL_USERNAME"),
        sasl_password=os.environ.get("KAFKA_SASL_PASSWORD"),
    )


class MemoryReplicator:
    def __init__(self) -> None:
        ensure_metrics_server(SERVICE_SETTINGS)
        self.kafka_settings = _kafka_settings()
        self.bus = KafkaEventBus(self.kafka_settings)
        self.wal_topic = os.environ.get("MEMORY_WAL_TOPIC", "memory.wal")
        self.group_id = os.environ.get("MEMORY_REPLICATOR_GROUP", "memory-replicator")
        # Use centralized admin settings for Postgres DSN.
        self.replica = MemoryReplicaStore(dsn=os.environ.get("SA01_DB_DSN", ""))
        self.dlq_store = DLQStore(dsn=os.environ.get("SA01_DB_DSN", ""))
        self.dlq = DeadLetterQueue(source_topic=self.wal_topic)

    async def start(self) -> None:
        try:
            await ensure_replica_schema(self.replica)
        except Exception:
            LOGGER.debug("Replica schema ensure failed", exc_info=True)
        try:
            await ensure_dlq_schema(self.dlq_store)
        except Exception:
            LOGGER.debug("DLQ schema ensure failed", exc_info=True)
        await self.bus.consume(self.wal_topic, self.group_id, self._handle_wal)

    async def _handle_wal(self, event: dict[str, Any]) -> None:
        start = time.time()
        try:
            await self.replica.insert_from_wal(event)
        except Exception as exc:
            REPL_EVENTS.labels("error").inc()
            LOGGER.error(
                "Failed to replicate WAL",
                extra={"error": str(exc), "error_type": type(exc).__name__},
            )
            # Publish to Kafka DLQ and persist to Postgres DLQ table
            try:
                await self.dlq.send_to_dlq(event, exc)
            except Exception:
                LOGGER.debug("DLQ publish failed (kafka)", exc_info=True)
            try:
                await self.dlq_store.add(topic=f"{self.wal_topic}.dlq", event=event, error=str(exc))
            except Exception:
                LOGGER.debug("DLQ store persist failed", exc_info=True)
        else:
            REPL_EVENTS.labels("ok").inc()
        finally:
            elapsed = max(0.0, time.time() - start)
            REPL_LATENCY.observe(elapsed)
            try:
                wal_ts = float(event.get("timestamp") or 0.0)
                if wal_ts > 0:
                    REPL_LAG.set(max(0.0, time.time() - wal_ts))
            except Exception:
                # Ignore malformed timestamps
                pass


async def main() -> None:
    worker = MemoryReplicator()
    await worker.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        LOGGER.info("Memory replicator stopped")
