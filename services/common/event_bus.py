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
from opentelemetry.trace import SpanKind

from services.common.trace_context import inject_trace_context, with_trace_context

LOGGER = logging.getLogger(__name__)
TRACER = trace.get_tracer(__name__)


def _build_trace_headers(span_ctx) -> list[tuple[str, bytes]]:
    """Build Kafka message headers for the current span context.

    Includes stable trace_id/span_id plus W3C traceparent (version 00) header.
    Returns a list of (key, value_bytes) pairs suitable for aiokafka send.
    Defensive: returns empty list if context missing identifiers.
    """
    try:
        if not span_ctx or not span_ctx.trace_id or not span_ctx.span_id:
            return []
        trace_id_hex = f"{span_ctx.trace_id:032x}"
        span_id_hex = f"{span_ctx.span_id:016x}"
        # TraceFlags sampled bit reflected by low bit (0x01) when enabled
        sampled_flag = (
            0x01
            if getattr(span_ctx, "trace_flags", None) and int(span_ctx.trace_flags) & 0x01
            else 0x00
        )
        traceparent = f"00-{trace_id_hex}-{span_id_hex}-{sampled_flag:02x}"  # version 00
        headers = [
            ("trace_id", trace_id_hex.encode("utf-8")),
            ("span_id", span_id_hex.encode("utf-8")),
            ("traceparent", traceparent.encode("utf-8")),
        ]
        return headers
    except Exception:  # pragma: no cover
        return []


@dataclass
class KafkaSettings:
    bootstrap_servers: str
    security_protocol: str = "PLAINTEXT"
    sasl_mechanism: Optional[str] = None
    sasl_username: Optional[str] = None
    sasl_password: Optional[str] = None

    @classmethod
    def from_env(cls) -> "KafkaSettings":
        from services.common import runtime_config as cfg

        return cls(
            bootstrap_servers=cfg.settings().kafka_bootstrap_servers or "kafka:9092",
            security_protocol=cfg.env("KAFKA_SECURITY_PROTOCOL", "PLAINTEXT") or "PLAINTEXT",
            sasl_mechanism=cfg.env("KAFKA_SASL_MECHANISM"),
            sasl_username=cfg.env("KAFKA_SASL_USERNAME"),
            sasl_password=cfg.env("KAFKA_SASL_PASSWORD"),
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

    async def close(self) -> None:
        """Close underlying producer if started.

        Safe to call multiple times. Intended for tests and graceful shutdowns.
        """
        if self._producer is not None:
            try:
                await self._producer.stop()
            finally:
                self._producer = None

    async def publish(
        self, topic: str, payload: Any, headers: Optional[dict[str, Any]] = None
    ) -> None:
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
            # Capture current span context for lightweight logging / troubleshooting.
            try:
                span_ctx = trace.get_current_span().get_span_context()
                trace_hdrs = _build_trace_headers(span_ctx)
                # Merge provided headers (if any) with trace headers; convert to list[tuple[str, bytes]]
                hdr_list: list[tuple[str, bytes]] = []
                if isinstance(headers, dict):
                    for k, v in headers.items():
                        try:
                            b = (str(v)).encode("utf-8")
                        except Exception:
                            b = b""
                        hdr_list.append((str(k), b))
                # Ensure trace headers are present and take precedence for trace keys
                seen = {k for k, _ in hdr_list}
                for k, v in trace_hdrs:
                    if k not in seen:
                        hdr_list.append((k, v))
                # Mirror identifiers into payload for downstream processors lacking header access
                if trace_hdrs:
                    payload.setdefault("trace", {})
                    for k, v in trace_hdrs:
                        if k in {"trace_id", "span_id"}:
                            payload["trace"].setdefault(k, v.decode("utf-8", errors="ignore"))
                    tp = next(
                        (
                            v.decode("utf-8", errors="ignore")
                            for k, v in trace_hdrs
                            if k == "traceparent"
                        ),
                        None,
                    )
                    if tp:
                        payload["trace"].setdefault("traceparent", tp)
            except Exception:  # pragma: no cover - never fail publish on logging concerns
                hdr_list = []
            message = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            await producer.send_and_wait(topic, message, headers=hdr_list)
        try:
            # Log minimal trace identifiers (do not log full payload in production to reduce PII risk)
            tinfo = payload.get("trace") or {}
            LOGGER.debug(
                "Published event",
                extra={
                    "topic": topic,
                    "trace_id": tinfo.get("trace_id"),
                    "span_id": tinfo.get("span_id"),
                    # Retain small payload preview for debugging; truncate if very large
                    "payload_preview": str(payload)[:500],
                },
            )
        except Exception:  # pragma: no cover
            LOGGER.debug("Published event (trace logging failed)", extra={"topic": topic})

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
            from services.common import runtime_config as cfg

            fetch_wait_ms = int(cfg.env("KAFKA_FETCH_MAX_WAIT_MS", "20") or "20")
            fetch_min_bytes = int(cfg.env("KAFKA_FETCH_MIN_BYTES", "1") or "1")
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
                # Surface trace headers into payload if not already present (header preference over body).
                try:
                    if isinstance(message.headers, list):
                        hdr_map = {
                            k: v.decode("utf-8", errors="ignore") for k, v in message.headers
                        }
                        if hdr_map.get("trace_id") and hdr_map.get("span_id"):
                            data.setdefault("trace", {})
                            data["trace"].setdefault("trace_id", hdr_map["trace_id"])
                            data["trace"].setdefault("span_id", hdr_map["span_id"])
                        # Surface W3C traceparent header if present
                        if hdr_map.get("traceparent"):
                            data.setdefault("trace", {})
                            data["trace"].setdefault("traceparent", hdr_map["traceparent"])
                except Exception:  # pragma: no cover
                    pass
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
                try:
                    span_ctx = trace.get_current_span().get_span_context()
                    LOGGER.debug(
                        "Consumed event",
                        extra={
                            "topic": topic,
                            "group_id": group_id,
                            "trace_id": f"{span_ctx.trace_id:032x}" if span_ctx.trace_id else None,
                            "span_id": f"{span_ctx.span_id:016x}" if span_ctx.span_id else None,
                        },
                    )
                except Exception:  # pragma: no cover
                    pass
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
