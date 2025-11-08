"""Asynchronous Kafka event bus helpers for SomaAgent 01.

The implementation relies on aiokafka, but keeps the interface minimal so
we can plug in alternative transports during tests or in constrained
environments.  The default configuration is driven by environment
variables so LOCAL mode can point to the docker-compose cluster while
production reads from Vault/ConfigMaps.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from dataclasses import dataclass
from typing import Any, AsyncIterator, Callable, Optional

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from opentelemetry import trace
from opentelemetry.trace import SpanKind

from services.common.trace_context import inject_trace_context, with_trace_context

LOGGER = logging.getLogger(__name__)
TRACER = trace.get_tracer(__name__)


@dataclass
class KafkaSettings:
    bootstrap_servers: str
    security_protocol: str = "PLAINTEXT"
    sasl_mechanism: Optional[str] = None
    sasl_username: Optional[str] = None
    sasl_password: Optional[str] = None

    @classmethod
    def from_env(cls) -> "KafkaSettings":
        return cls(
            bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"),
            security_protocol=os.getenv("KAFKA_SECURITY_PROTOCOL", "PLAINTEXT"),
            sasl_mechanism=os.getenv("KAFKA_SASL_MECHANISM"),
            sasl_username=os.getenv("KAFKA_SASL_USERNAME"),
            sasl_password=os.getenv("KAFKA_SASL_PASSWORD"),
        )


class KafkaEventBus:
    """Thin wrapper around aiokafka producer/consumer."""

    def __init__(self, settings: Optional[KafkaSettings] = None) -> None:
        self.settings = settings or KafkaSettings.from_env()
        self._producer: Optional[AIOKafkaProducer] = None

    async def _ensure_producer(self) -> AIOKafkaProducer:
        if self._producer is None:
            kwargs: dict[str, Any] = {
                "bootstrap_servers": self.settings.bootstrap_servers,
                "security_protocol": self.settings.security_protocol,
            }
            if self.settings.sasl_mechanism:
                kwargs.update(
                    {
                        "sasl_mechanism": self.settings.sasl_mechanism,
                        "sasl_plain_username": self.settings.sasl_username,
                        "sasl_plain_password": self.settings.sasl_password,
                    }
                )
            self._producer = AIOKafkaProducer(**kwargs)
            await self._producer.start()
        return self._producer

    async def healthcheck(self) -> None:
        producer = await self._ensure_producer()
        await producer.client.force_metadata_update()

    async def publish(self, topic: str, payload: Any) -> None:
        producer = await self._ensure_producer()
        with TRACER.start_as_current_span(
            "kafka.publish",
            kind=SpanKind.PRODUCER,
            attributes={
                "messaging.system": "kafka",
                "messaging.destination": topic,
            },
        ):
            # Normalize payload to a dict for trace context injection
            if not isinstance(payload, dict):
                try:
                    if isinstance(payload, (bytes, bytearray)):
                        payload = json.loads(payload.decode("utf-8"))
                    elif isinstance(payload, str):
                        payload = json.loads(payload)
                    else:
                        # Best-effort conversion via JSON round-trip
                        payload = json.loads(json.dumps(payload, ensure_ascii=False, default=str))
                except Exception:
                    payload = {"payload": str(payload)}
            inject_trace_context(payload)
            message = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            await producer.send_and_wait(topic, message)
        LOGGER.debug("Published event", extra={"topic": topic, "payload": payload})

    async def consume(
        self,
        topic: str,
        group_id: str,
        handler: Callable[[dict[str, Any]], asyncio.Future | Any],
        stop_event: Optional[asyncio.Event] = None,
    ) -> None:
        """Consume events and forward to *handler* until stop_event is set."""
        settings = self.settings
        kwargs: dict[str, Any] = {
            "bootstrap_servers": settings.bootstrap_servers,
            "group_id": group_id,
            "enable_auto_commit": False,
            "security_protocol": settings.security_protocol,
        }
        # Low-latency fetch settings for near‑real‑time UI streaming. Defaults are conservative;
        # allow tuning via environment variables without code changes.
        try:
            fetch_wait_ms = int(os.getenv("KAFKA_FETCH_MAX_WAIT_MS", "20"))  # default 20ms
            fetch_min_bytes = int(os.getenv("KAFKA_FETCH_MIN_BYTES", "1"))  # default 1 byte
            kwargs.update(
                {
                    "fetch_max_wait_ms": max(1, fetch_wait_ms),
                    "fetch_min_bytes": max(1, fetch_min_bytes),
                }
            )
        except Exception:
            # Fall back silently if envs are invalid
            pass
        if settings.sasl_mechanism:
            kwargs.update(
                {
                    "sasl_mechanism": settings.sasl_mechanism,
                    "sasl_plain_username": settings.sasl_username,
                    "sasl_plain_password": settings.sasl_password,
                }
            )
        consumer = AIOKafkaConsumer(topic, **kwargs)
        await consumer.start()
        LOGGER.info("Started consumer", extra={"topic": topic, "group_id": group_id})
        try:
            async for message in consumer:
                data = json.loads(message.value.decode("utf-8"))
                with with_trace_context(data):
                    with TRACER.start_as_current_span(
                        "kafka.consume",
                        kind=SpanKind.CONSUMER,
                        attributes={
                            "messaging.system": "kafka",
                            "messaging.destination": topic,
                            "messaging.consumer.group": group_id,
                        },
                    ):
                        await handler(data)
                await consumer.commit()
                if stop_event and stop_event.is_set():
                    break
        finally:
            await consumer.stop()
            LOGGER.info("Stopped consumer", extra={"topic": topic, "group_id": group_id})

    async def close(self) -> None:
        if self._producer is not None:
            await self._producer.stop()
            self._producer = None


async def iterate_topic(
    topic: str,
    group_id: str,
    settings: Optional[KafkaSettings] = None,
) -> AsyncIterator[dict[str, Any]]:
    """Async iterator helper for streaming topics (used by WebSockets)."""
    bus = KafkaEventBus(settings)
    queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
    stop_event = asyncio.Event()

    async def _handler(payload: dict[str, Any]) -> None:
        await queue.put(payload)

    consumer_task = asyncio.create_task(bus.consume(topic, group_id, _handler, stop_event))
    try:
        while True:
            payload = await queue.get()
            yield payload
    finally:
        stop_event.set()
        await consumer_task
        await bus.close()
