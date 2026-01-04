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
from dataclasses import dataclass
from typing import Any, AsyncIterator, Callable, Optional

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from opentelemetry import trace
from opentelemetry.trace import SpanContext, SpanKind

from services.common.trace_context import inject_trace_context, with_trace_context
import os

LOGGER = logging.getLogger(__name__)
TRACER = trace.get_tracer(__name__)


@dataclass
class KafkaSettings:
    """Kafkasettings class implementation."""

    bootstrap_servers: str
    security_protocol: str = "PLAINTEXT"
    sasl_mechanism: Optional[str] = None
    sasl_username: Optional[str] = None
    sasl_password: Optional[str] = None

    @classmethod
    def from_env(cls) -> "KafkaSettings":
        """Execute from env.
            """

        return cls(
            bootstrap_servers=os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"),
            security_protocol=os.environ.get("KAFKA_SECURITY_PROTOCOL", "PLAINTEXT"),
            sasl_mechanism=os.environ.get("KAFKA_SASL_MECHANISM"),
            sasl_username=os.environ.get("KAFKA_SASL_USERNAME"),
            sasl_password=os.environ.get("KAFKA_SASL_PASSWORD"),
        )


class KafkaEventBus:
    """Thin wrapper around aiokafka producer/consumer."""

    def __init__(self, settings: Optional[KafkaSettings] = None) -> None:
        """Initialize the instance."""

        self.settings = settings or KafkaSettings.from_env()
        self._producer: Optional[AIOKafkaProducer] = None

    async def _ensure_producer(self) -> AIOKafkaProducer:
        """Execute ensure producer.
            """

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
        """Execute healthcheck.
            """

        producer = await self._ensure_producer()
        await producer.client.force_metadata_update()

    async def publish(
        self, topic: str, payload: Any, headers: dict[str, Any] | None = None
    ) -> None:
        """Publish a payload to a Kafka topic.

        ``headers`` is a mapping of header name → value that will be converted
        to the ``list[tuple[bytes, bytes]]`` format expected by ``aiokafka``.
        Header values are encoded as UTF‑8 bytes; keys remain ``str`` for easy
        lookup in tests (see ``test_publisher_headers``).
        """
        producer = await self._ensure_producer()
        with TRACER.start_as_current_span(
            "kafka.publish",
            kind=SpanKind.PRODUCER,
            attributes={
                "messaging.system": "kafka",
                "messaging.destination": topic,
            },
        ):
            # Normalise payload for trace injection
            if not isinstance(payload, dict):
                try:
                    if isinstance(payload, (bytes, bytearray)):
                        payload = json.loads(payload.decode("utf-8"))
                    elif isinstance(payload, str):
                        payload = json.loads(payload)
                    else:
                        payload = json.loads(json.dumps(payload, ensure_ascii=False, default=str))
                except Exception:
                    payload = {"payload": str(payload)}
            inject_trace_context(payload)
            message = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            # Convert header dict to list of (key, bytes) tuples expected by aiokafka
            kafka_headers: list[tuple[str, bytes]] | None = None
            if headers:
                kafka_headers = [(k, str(v).encode()) for k, v in headers.items()]
            await producer.send_and_wait(topic, message, headers=kafka_headers)
        LOGGER.debug(
            "Published event",
            extra={"topic": topic, "payload": payload, "headers": headers},
        )

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
        """Execute close.
            """

        if self._producer is not None:
            await self._producer.stop()
            self._producer = None


# ---------------------------------------------------------------------------
# Helper – build W3C trace headers for Kafka messages (module level)
# ---------------------------------------------------------------------------
def _build_trace_headers(sc: SpanContext) -> list[tuple[str, bytes]]:
    """Return trace‑related headers for a given ``SpanContext``.

    The test suite expects the *keys* to be plain ``str`` objects while the
    *values* remain ``bytes``. Previously the function returned ``bytes`` keys,
    causing look‑ups like ``"trace_id" in hmap`` to fail. This patch switches the
    key type to ``str`` while preserving the original byte‑encoded values.
    """
    if not sc.trace_id or not sc.span_id:
        return []
    trace_id_hex = f"{sc.trace_id:032x}".lower()
    span_id_hex = f"{sc.span_id:016x}".lower()
    flags_hex = f"{int(sc.trace_flags):02x}"
    traceparent = f"00-{trace_id_hex}-{span_id_hex}-{flags_hex}"
    return [
        ("trace_id", trace_id_hex.encode()),
        ("span_id", span_id_hex.encode()),
        ("traceparent", traceparent.encode()),
    ]


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
        """Execute handler.

            Args:
                payload: The payload.
            """

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