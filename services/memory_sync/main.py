"""Memory Sync Worker

Retries failed SomaBrain remember() writes from the memory_write_outbox and
publishes memory.wal on success to keep the replica in sync.
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from typing import Optional

import httpx
from prometheus_client import Counter, Gauge, Histogram, start_http_server

from services.common.event_bus import KafkaEventBus, KafkaSettings
from services.common.publisher import DurablePublisher
from services.common.outbox_repository import OutboxStore, ensure_schema as ensure_outbox_schema
from services.common.memory_write_outbox import (
    MemoryWriteOutbox,
    ensure_schema as ensure_mw_schema,
)
from services.common.tracing import setup_tracing
from python.integrations.soma_client import SomaClient, SomaClientError


LOGGER = logging.getLogger(__name__)


JOBS = Counter("memory_sync_jobs_total", "Memory sync job outcomes", labelnames=("result",))
JOB_SECONDS = Histogram("memory_sync_seconds", "Latency of memory sync processing")
BACKLOG = Gauge("memory_sync_backlog", "Pending memory write outbox items")


def _kafka_settings() -> KafkaSettings:
    return KafkaSettings.from_env()


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


class MemorySyncWorker:
    def __init__(self) -> None:
        self.store = MemoryWriteOutbox(dsn=os.getenv("POSTGRES_DSN"))
        self.bus = KafkaEventBus(_kafka_settings())
        # Durable publisher requires an OutboxStore for reliability
        self.outbox = OutboxStore(dsn=os.getenv("POSTGRES_DSN"))
        self.publisher = DurablePublisher(bus=self.bus, outbox=self.outbox)
        self.soma = SomaClient.get()
        self.batch_size = _env_int("MEMORY_SYNC_BATCH_SIZE", 100)
        self.interval = _env_float("MEMORY_SYNC_INTERVAL_SECONDS", 1.0)
        self.max_retries = _env_int("MEMORY_SYNC_MAX_RETRIES", 6)
        self.backoff_base = _env_float("MEMORY_SYNC_BACKOFF_BASE_SECONDS", 1.0)
        self.backoff_max = _env_float("MEMORY_SYNC_BACKOFF_MAX_SECONDS", 60.0)
        self._stopping = asyncio.Event()

    async def start(self) -> None:
        await ensure_mw_schema(self.store)
        try:
            await ensure_outbox_schema(self.outbox)
        except Exception:
            LOGGER.debug("Outbox schema ensure failed in memory_sync", exc_info=True)
        metrics_port = int(os.getenv("MEMORY_SYNC_METRICS_PORT", "9471"))
        start_http_server(metrics_port)
        LOGGER.info("memory_sync started", extra={"batch": self.batch_size, "interval": self.interval})
        while not self._stopping.is_set():
            pending = await self.store.count_pending()
            BACKLOG.set(pending)
            items = await self.store.claim_batch(limit=self.batch_size)
            if not items:
                await asyncio.sleep(self.interval)
                continue
            for item in items:
                with JOB_SECONDS.time():
                    await self._process(item)

    async def stop(self) -> None:
        self._stopping.set()
        await self.bus.close()
        try:
            await self.outbox.close()
        except Exception:
            pass
        await self.store.close()

    async def _process(self, item) -> None:  # item: MemoryWriteItem
        payload = dict(item.payload)
        # Ensure idempotency key is populated
        if "idempotency_key" not in payload and payload.get("id"):
            payload["idempotency_key"] = payload.get("id")

        try:
            result = await self.soma.remember(payload)
        except SomaClientError as exc:
            # Retry with exponential backoff
            retry = item.retry_count + 1
            if retry > self.max_retries:
                await self.store.mark_failed(item.id, error=str(exc))
                JOBS.labels("failed").inc()
                return
            backoff = min(self.backoff_base * (2 ** (retry - 1)), self.backoff_max)
            await self.store.mark_retry(item.id, backoff_seconds=backoff, error=str(exc))
            JOBS.labels("retry").inc()
            return
        except Exception as exc:
            retry = item.retry_count + 1
            if retry > self.max_retries:
                await self.store.mark_failed(item.id, error=str(exc))
                JOBS.labels("failed").inc()
                return
            backoff = min(self.backoff_base * (2 ** (retry - 1)), self.backoff_max)
            await self.store.mark_retry(item.id, backoff_seconds=backoff, error=str(exc))
            JOBS.labels("retry").inc()
            return

        # Success: publish WAL and mark sent
        try:
            wal_topic = os.getenv("MEMORY_WAL_TOPIC", "memory.wal")
            wal_event = {
                "type": "memory.write",
                "role": payload.get("role"),
                "session_id": payload.get("session_id"),
                "persona_id": payload.get("persona_id"),
                "tenant": (payload.get("metadata") or {}).get("tenant"),
                "payload": payload,
                "result": {
                    "coord": (result or {}).get("coordinate") or (result or {}).get("coord"),
                    "trace_id": (result or {}).get("trace_id"),
                    "request_id": (result or {}).get("request_id"),
                },
                "timestamp": time.time(),
            }
            await self.publisher.publish(
                wal_topic,
                wal_event,
                dedupe_key=str(payload.get("id")) if payload.get("id") else None,
                session_id=str(payload.get("session_id")) if payload.get("session_id") else None,
                tenant=(payload.get("metadata") or {}).get("tenant"),
            )
        except Exception:
            LOGGER.debug("memory_sync: WAL publish failed", exc_info=True)
        await self.store.mark_sent(item.id)
        JOBS.labels("ok").inc()


async def main() -> None:
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    setup_tracing("memory-sync", endpoint=os.getenv("OTLP_ENDPOINT"))
    worker = MemorySyncWorker()
    try:
        await worker.start()
    finally:
        await worker.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        LOGGER.info("memory_sync stopped")

