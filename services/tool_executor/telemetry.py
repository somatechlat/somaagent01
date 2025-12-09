"""Telemetry emission for tool executor service.

This module handles telemetry publishing for tool execution events,
wrapping the common TelemetryPublisher with tool-specific logic.
"""

from __future__ import annotations

import logging
from typing import Any

from services.common.publisher import DurablePublisher
from services.common.telemetry import TelemetryPublisher
from services.common.telemetry_store import TelemetryStore

LOGGER = logging.getLogger(__name__)


class ToolTelemetryEmitter:
    """Emits telemetry events for tool executions."""

    def __init__(self, publisher: DurablePublisher, settings: Any) -> None:
        """Initialize the telemetry emitter.

        Args:
            publisher: DurablePublisher for event publishing.
            settings: Service settings containing telemetry configuration.
        """
        telemetry_store = TelemetryStore.from_settings(settings)
        self._telemetry = TelemetryPublisher(publisher=publisher, store=telemetry_store)

    async def emit_tool_execution(
        self,
        result_event: dict[str, Any],
        status: str,
        execution_time: float,
    ) -> None:
        """Emit telemetry for a tool execution result.

        Args:
            result_event: The tool result event containing session/persona info.
            status: The execution status (success, error, etc.).
            execution_time: Execution time in seconds.
        """
        tenant_meta = result_event.get("metadata", {})
        tenant = tenant_meta.get("tenant", "default")

        await self._telemetry.emit_tool(
            session_id=result_event["session_id"],
            persona_id=result_event.get("persona_id"),
            tenant=tenant,
            tool_name=result_event.get("tool_name", ""),
            status=status,
            latency_seconds=execution_time,
            metadata=tenant_meta,
        )
