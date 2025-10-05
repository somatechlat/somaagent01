"""Telemetry publisher for SomaAgent 01."""
from __future__ import annotations

import time
import uuid
from typing import Any, Optional

from services.common.event_bus import KafkaEventBus
from services.common.telemetry_store import TelemetryStore


class TelemetryPublisher:
    def __init__(
        self,
        bus: Optional[KafkaEventBus] = None,
        store: Optional[TelemetryStore] = None,
    ) -> None:
        self.bus = bus or KafkaEventBus()
        self.store = store or TelemetryStore()
        self.topics = {
            "slm": "slm.metrics",
            "tool": "tool.metrics",
            "audio": "audio.metrics",
            "budget": "budget.events",
            "escalation": "llm.escalation.metrics",
        }

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
        await self.bus.publish(self.topics["slm"], event)
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
        await self.bus.publish(self.topics["tool"], event)
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
        await self.bus.publish(self.topics["budget"], event)
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
        await self.bus.publish(self.topics["escalation"], event)
        await self.store.insert_escalation(event)
