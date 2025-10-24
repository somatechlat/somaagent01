"""Outbox sync worker: publishes pending outbox rows to Kafka.

Environment variables:
- OUTBOX_SYNC_BATCH_SIZE (default: 100)
- OUTBOX_SYNC_INTERVAL_SECONDS (default: 0.5)
- OUTBOX_SYNC_MAX_RETRIES (default: 8)
- OUTBOX_SYNC_BACKOFF_BASE_SECONDS (default: 1.0)
- OUTBOX_SYNC_BACKOFF_MAX_SECONDS (default: 60.0)
"""

from __future__ import annotations

import asyncio
import logging
import math
import os
from contextlib import suppress
from typing import Optional

from aiokafka.errors import KafkaError
from prometheus_client import Counter, start_http_server

from services.common.event_bus import KafkaEventBus, KafkaSettings
from services.common.outbox_repository import (
    OutboxMessage,
    OutboxStore,
    ensure_schema,
    OUTBOX_PUBLISH_LATENCY,
)
from services.common.telemetry import setup_tracing

LOGGER = logging.getLogger(__name__)


PUBLISH_OK = Counter(
    "outbox_sync_publish_total",
    "Messages published by sync worker",
    labelnames=("result",),
)


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except ValueError:
        return default


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


class OutboxSyncWorker:
    def __init__(self, *, store: Optional[OutboxStore] = None, bus: Optional[KafkaEventBus] = None) -> None:
        self.store = store or OutboxStore()
        self.bus = bus or KafkaEventBus(KafkaSettings.from_env())
        self.batch_size = _env_int("OUTBOX_SYNC_BATCH_SIZE", 100)
        self.interval = _env_float("OUTBOX_SYNC_INTERVAL_SECONDS", 0.5)
        self.max_retries = _env_int("OUTBOX_SYNC_MAX_RETRIES", 8)
        self.backoff_base = _env_float("OUTBOX_SYNC_BACKOFF_BASE_SECONDS", 1.0)
        self.backoff_max = _env_float("OUTBOX_SYNC_BACKOFF_MAX_SECONDS", 60.0)
        self._stopping = asyncio.Event()

    async def start(self) -> None:
        await ensure_schema(self.store)
        LOGGER.info("Outbox sync worker started",
                    extra={"batch_size": self.batch_size, "interval": self.interval})
        while not self._stopping.is_set():
            msgs = await self.store.claim_batch(limit=self.batch_size)
            if not msgs:
                await asyncio.sleep(self.interval)
                continue
            await self._publish_batch(msgs)

    async def stop(self) -> None:
        self._stopping.set()
        with suppress(Exception):
            await self.bus.close()
        with suppress(Exception):
            await self.store.close()
        LOGGER.info("Outbox sync worker stopped")

    def _compute_backoff(self, retry_count: int) -> float:
        exp = min(retry_count, self.max_retries)
        delay = self.backoff_base * math.pow(2, exp)
        return min(delay, self.backoff_max)

    async def _publish_batch(self, messages: list[OutboxMessage]) -> None:
        for msg in messages:
            try:
                with OUTBOX_PUBLISH_LATENCY.time():
                    await self.bus.publish(msg.topic, msg.payload)
            except KafkaError as kerr:
                await self._handle_failure(msg, kerr)
            except Exception as exc:  # safety net
                await self._handle_failure(msg, exc)
            else:
                await self.store.mark_sent(msg.id)
                PUBLISH_OK.labels("success").inc()

    async def _handle_failure(self, msg: OutboxMessage, exc: Exception) -> None:
        retry = msg.retry_count + 1
        if retry > self.max_retries:
            await self.store.mark_failed(msg.id, error=str(exc))
            PUBLISH_OK.labels("failed").inc()
            LOGGER.warning("Outbox message failed permanently", extra={"id": msg.id, "topic": msg.topic})
            return
        backoff = self._compute_backoff(retry)
        await self.store.mark_retry(msg.id, backoff_seconds=backoff, error=str(exc))
        PUBLISH_OK.labels("retry").inc()
        LOGGER.debug(
            "Outbox message scheduled for retry",
            extra={"id": msg.id, "retry": retry, "backoff": backoff, "topic": msg.topic},
        )


async def main() -> None:
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    setup_tracing("outbox-sync", endpoint=os.getenv("OTLP_ENDPOINT"))
    # Optional metrics server
    metrics_port = int(os.getenv("OUTBOX_SYNC_METRICS_PORT", "9469"))
    start_http_server(metrics_port)
    worker = OutboxSyncWorker()
    try:
        await worker.start()
    finally:
        await worker.stop()


if __name__ == "__main__":
    asyncio.run(main())
