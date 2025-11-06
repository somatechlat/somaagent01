"""Telemetry publisher for SomaAgent 01.

Now supports durable publishing via the outbox by accepting a
DurablePublisher. If not provided, will construct one with a default
KafkaEventBus and OutboxStore using environment configuration.
"""

from __future__ import annotations

import time
import uuid
from typing import Any, Optional

from services.common.event_bus import KafkaEventBus
from services.common.outbox_repository import OutboxStore
from services.common.publisher import DurablePublisher
from services.common.telemetry_store import TelemetryStore


class TelemetryPublisher:
    def __init__(
        self,
        publisher: Optional[DurablePublisher] = None,
        store: Optional[TelemetryStore] = None,
        bus: Optional[KafkaEventBus] = None,
    ) -> None:
        # prefer provided durable publisher; else wrap provided bus; else create both
        if publisher is not None:
            self.publisher = publisher
        else:
            event_bus = bus or KafkaEventBus()
            outbox = OutboxStore()  # DSN from env
            self.publisher = DurablePublisher(bus=event_bus, outbox=outbox)
        self.store = store or TelemetryStore()
        self.topics = {
            "slm": "slm.metrics",
            "tool": "tool.metrics",
            "audio": "audio.metrics",
            "budget": "budget.events",
            "escalation": "llm.escalation.metrics",
            "generic": "metrics.generic",
        }

    async def _publish(self, topic: str, event: dict[str, Any]) -> None:
        await self.publisher.publish(
            topic,
            event,
            dedupe_key=event.get("event_id"),
            session_id=event.get("session_id"),
            tenant=(event.get("metadata") or {}).get("tenant") or event.get("tenant"),
        )

    async def emit_slm(
        self,
        *,
        session_id: str,
        persona_id: str | None,
        tenant: str,
        model: str,
        latency_seconds: float,
        input_tokens: int,
        output_tokens: int,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        event = {
            "event_id": str(uuid.uuid4()),
            "session_id": session_id,
            "persona_id": persona_id,
            "tenant": tenant,
            "model": model,
            "latency_seconds": latency_seconds,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "timestamp": time.time(),
            "metadata": metadata or {},
        }
        await self._publish(self.topics["slm"], event)
        await self.store.insert_slm(event)

    async def emit_tool(
        self,
        *,
        session_id: str,
        persona_id: str | None,
        tenant: str,
        tool_name: str,
        status: str,
        latency_seconds: float,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        event = {
            "event_id": str(uuid.uuid4()),
            "session_id": session_id,
            "persona_id": persona_id,
            "tenant": tenant,
            "tool_name": tool_name,
            "status": status,
            "latency_seconds": latency_seconds,
            "timestamp": time.time(),
            "metadata": metadata or {},
        }
        await self._publish(self.topics["tool"], event)
        await self.store.insert_tool(event)

    async def emit_budget(
        self,
        *,
        tenant: str,
        persona_id: str | None,
        delta_tokens: int,
        total_tokens: int,
        limit_tokens: Optional[int],
        status: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        event = {
            "event_id": str(uuid.uuid4()),
            "tenant": tenant,
            "persona_id": persona_id,
            "delta_tokens": delta_tokens,
            "total_tokens": total_tokens,
            "limit_tokens": limit_tokens,
            "status": status,
            "timestamp": time.time(),
            "metadata": metadata or {},
        }
        await self._publish(self.topics["budget"], event)
        await self.store.insert_budget(event)

    async def emit_escalation_llm(
        self,
        *,
        session_id: str,
        persona_id: str | None,
        tenant: str,
        model: str,
        latency_seconds: float,
        input_tokens: int,
        output_tokens: int,
        decision_reason: str,
        status: str = "success",
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        event = {
            "event_id": str(uuid.uuid4()),
            "session_id": session_id,
            "persona_id": persona_id,
            "tenant": tenant,
            "model": model,
            "latency_seconds": latency_seconds,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "decision_reason": decision_reason,
            "status": status,
            "timestamp": time.time(),
            "metadata": metadata or {},
        }
        await self._publish(self.topics["escalation"], event)
        await self.store.insert_escalation(event)

    async def emit_generic_metric(
        self,
        *,
        metric_name: str,
        labels: dict[str, Any] | None = None,
        value: float | int | None = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        event = {
            "event_id": str(uuid.uuid4()),
            "metric_name": metric_name,
            "labels": labels or {},
            "value": value,
            "timestamp": time.time(),
            "metadata": metadata or {},
        }
        # Publish lightweight; session/tenant may be absent for global metrics
        await self._publish(self.topics["generic"], event)
        await self.store.insert_generic_metric(
            metric_name=metric_name,
            labels=labels or {},
            value=value,
            metadata=metadata or {},
        )
