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
from contextlib import suppress
from typing import Optional
import time

from aiokafka.errors import KafkaError
from prometheus_client import Counter, Gauge, start_http_server

import httpx

from services.common.event_bus import KafkaEventBus, KafkaSettings
from services.common.outbox_repository import (
    ensure_schema,
    OUTBOX_PUBLISH_LATENCY,
    OutboxMessage,
    OutboxStore,
)
from services.common.tracing import setup_tracing
from src.core.config import cfg

LOGGER = logging.getLogger(__name__)


PUBLISH_OK = Counter(
    "outbox_sync_publish_total",
    "Messages published by sync worker",
    labelnames=("result",),
)

HEALTH_STATE = Gauge(
    "somabrain_health_state",
    "Health state of SomaBrain as observed by outbox sync worker",
    labelnames=("state",),  # states: normal|degraded|down
)

EFFECTIVE_BATCH = Gauge(
    "outbox_sync_effective_batch_size",
    "Effective batch size used by outbox sync based on health state",
)


def _env_float(name: str, default: float) -> float:
    raw = cfg.env(name, str(default))
    try:
        return float(raw)
    except (TypeError, ValueError):
        return default


def _env_int(name: str, default: int) -> int:
    raw = cfg.env(name, str(default))
    try:
        return int(raw)
    except (TypeError, ValueError):
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
        # Health-aware controls
        self._health_state: str = "normal"  # normal|degraded|down
        self._health_checked_at: float = 0.0
        self._health_interval: float = _env_float("OUTBOX_SYNC_HEALTH_INTERVAL_SECONDS", 1.5)
        # Initial metrics
        for state in ("normal", "degraded", "down"):
            HEALTH_STATE.labels(state).set(1.0 if state == self._health_state else 0.0)
        EFFECTIVE_BATCH.set(self.batch_size)

    async def start(self) -> None:
        await ensure_schema(self.store)
        LOGGER.info("Outbox sync worker started",
                    extra={"batch_size": self.batch_size, "interval": self.interval})
        while not self._stopping.is_set():
            await self._maybe_probe_health()
            effective_batch, effective_interval = self._compute_effective_limits()
            EFFECTIVE_BATCH.set(effective_batch)
            # Note: Even if SomaBrain is down, continue publishing Kafka outbox messages.
            # Health only adjusts batch/interval; do not pause publishes entirely.
            msgs = await self.store.claim_batch(limit=effective_batch)
            if not msgs:
                await asyncio.sleep(effective_interval)
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

    def _compute_effective_limits(self) -> tuple[int, float]:
        """Return (batch_size, interval) adjusted for health state.

        - normal: configured batch/interval
        - degraded: cap batch<=25, widen interval>=1.0s
        - down: use tiny batch (unused) and longer sleep to reduce churn
        """
        if self._health_state == "normal":
            return self.batch_size, self.interval
        if self._health_state == "degraded":
            return min(self.batch_size, 25), max(self.interval, 1.0)
        # down
        return 1, max(self.interval * 2.0, 3.0)

    async def _maybe_probe_health(self) -> None:
        now = time.time()
        if (now - self._health_checked_at) < self._health_interval:
            return
        self._health_checked_at = now
        new_state = await self._probe_somabrain_health()
        if new_state != self._health_state:
            LOGGER.info("Outbox sync health state changed", extra={"from": self._health_state, "to": new_state})
            self._health_state = new_state
            for state in ("normal", "degraded", "down"):
                HEALTH_STATE.labels(state).set(1.0 if state == self._health_state else 0.0)

    async def _probe_somabrain_health(self) -> str:
        """Probe SOMA_BASE_URL/health quickly and classify state.

        - normal: HTTP 200 and body ok=true or status==ok within ~1.5s
        - degraded: HTTP 200 but body not clearly ok
        - down: request error/timeout/non-200
        """
        base = cfg.env("SOMA_BASE_URL", "http://localhost:9696").rstrip("/")
        url = f"{base}/health"
        timeout = _env_float("OUTBOX_SYNC_HEALTH_INTERVAL_SECONDS", 1.5)
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.get(url)
                if resp.status_code != 200:
                    return "down"
                try:
                    body = resp.json()
                except Exception:
                    body = None
                if isinstance(body, dict) and (body.get("ok") is True or body.get("status") == "ok"):
                    return "normal"
                return "degraded"
        except Exception:
            return "down"

    async def _publish_batch(self, messages: list[OutboxMessage]) -> None:
        for msg in messages:
            try:
                with OUTBOX_PUBLISH_LATENCY.time():
                    payload = msg.payload
                    # Ensure payload is a dict; some drivers may return JSONB as text
                    if isinstance(payload, str):
                        try:
                            import json as _json
                            payload = _json.loads(payload)
                        except Exception:
                            # Fall back to wrapping string payload
                            payload = {"payload": str(msg.payload)}
                    await self.bus.publish(msg.topic, payload)
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
    logging.basicConfig(level=cfg.env("LOG_LEVEL", "INFO"))
    setup_tracing("outbox-sync", endpoint=cfg.env("OTLP_ENDPOINT"))
    # Optional metrics server
    metrics_port = int(cfg.env("OUTBOX_SYNC_METRICS_PORT", "9469"))
    start_http_server(metrics_port)
    worker = OutboxSyncWorker()
    try:
        await worker.start()
    finally:
        await worker.stop()


if __name__ == "__main__":
    asyncio.run(main())
