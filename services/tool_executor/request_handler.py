"""Request handling logic for tool executor service.

This module contains the core business logic for processing tool execution
requests, extracted from main.py to keep the entry point thin.
"""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any, TYPE_CHECKING

from services.common.policy_client import PolicyRequest
from services.tool_executor.audit import get_trace_id, log_tool_event
from services.tool_executor.metrics import (
    POLICY_DECISIONS,
    REQUEUE_EVENTS,
    TOOL_EXECUTION_LATENCY,
    TOOL_INFLIGHT,
    TOOL_REQUEST_COUNTER,
)
from services.tool_executor.resource_manager import default_limits
from services.tool_executor.tools import ToolExecutionError
from services.tool_executor.validation import validate_tool_request
from src.core.config import cfg

if TYPE_CHECKING:
    from services.tool_executor.main import ToolExecutor

LOGGER = logging.getLogger(__name__)


class RequestHandler:
    """Handles tool execution requests."""

    def __init__(self, executor: "ToolExecutor") -> None:
        self._executor = executor

    async def handle(self, event: dict[str, Any]) -> None:
        """Process a tool execution request event."""
        validation = validate_tool_request(event)
        tool_label = validation.tool_name or "unknown"

        if not validation.valid:
            LOGGER.error(
                "Invalid tool request", extra={"event": event, "error": validation.error_message}
            )
            TOOL_REQUEST_COUNTER.labels(tool_label, "invalid").inc()
            return

        session_id = validation.session_id
        tool_name = validation.tool_name
        tenant = validation.tenant
        persona_id = validation.persona_id
        trace_id_hex = get_trace_id()

        # Audit start
        arg_keys = sorted(list((event.get("args") or {}).keys())) if event.get("args") else []
        await log_tool_event(
            self._executor.get_audit_store(),
            action="tool.execute.start",
            tool_name=tool_name,
            session_id=session_id,
            tenant=tenant,
            persona_id=persona_id,
            event_id=event.get("event_id"),
            trace_id=trace_id_hex,
            details={"args_keys": arg_keys},
        )

        metadata = dict(event.get("metadata", {}))
        args = dict(event.get("args", {}))
        args.setdefault("session_id", session_id)

        # Policy check
        policy_result = await self._check_policy(
            tenant, persona_id, tool_name, tool_label, event, metadata, session_id, trace_id_hex
        )
        if policy_result is not None:
            return

        # Get tool
        tool = self._executor.tool_registry.get(tool_name)
        if not tool:
            await self._handle_unknown_tool(
                event, tool_name, tool_label, metadata, session_id, tenant, persona_id, trace_id_hex
            )
            return

        # Publish tool.start event for UI
        await self._publish_tool_start(event, session_id, persona_id, tool_name, metadata)

        # Execute tool
        result = await self._execute_tool(
            tool,
            tool_name,
            tool_label,
            args,
            event,
            metadata,
            session_id,
            tenant,
            persona_id,
            trace_id_hex,
        )
        if result is None:
            return

        # Publish result
        result_metadata = dict(metadata)
        if getattr(result, "logs", None):
            result_metadata.setdefault("sandbox_logs", result.logs)

        await self._executor.publish_result(
            event,
            status=result.status,
            payload=result.payload,
            execution_time=result.execution_time,
            metadata=result_metadata,
        )

        # Audit finish success
        await log_tool_event(
            self._executor.get_audit_store(),
            action="tool.execute.finish",
            tool_name=tool_name,
            session_id=session_id,
            tenant=tenant,
            persona_id=persona_id,
            event_id=event.get("event_id"),
            trace_id=trace_id_hex,
            details={"status": result.status, "latency_ms": int(result.execution_time * 1000)},
        )

    async def _check_policy(
        self,
        tenant: str,
        persona_id: str | None,
        tool_name: str,
        tool_label: str,
        event: dict[str, Any],
        metadata: dict[str, Any],
        session_id: str,
        trace_id_hex: str | None,
    ) -> str | None:
        """Check policy and return error status if denied, None if allowed."""
        try:
            request = PolicyRequest(
                tenant=tenant,
                persona_id=persona_id,
                action="tool.execute",
                resource=tool_name,
                context={
                    "args": event.get("args", {}),
                    "metadata": event.get("metadata", {}),
                },
            )
            allow = await self._executor.policy.evaluate(request)
        except Exception:
            LOGGER.exception("Policy evaluation failed")
            POLICY_DECISIONS.labels(tool_label, "error").inc()
            TOOL_REQUEST_COUNTER.labels(tool_label, "policy_error").inc()
            await self._executor.publish_result(
                event,
                status="error",
                payload={"message": "Policy evaluation failed."},
                execution_time=0.0,
                metadata=metadata,
            )
            await log_tool_event(
                self._executor.get_audit_store(),
                action="tool.execute.finish",
                tool_name=tool_name,
                session_id=session_id,
                tenant=tenant,
                persona_id=persona_id,
                event_id=event.get("event_id"),
                trace_id=trace_id_hex,
                details={"status": "error", "reason": "policy_error"},
            )
            return "policy_error"

        decision_label = "allowed" if allow else "denied"
        POLICY_DECISIONS.labels(tool_label, decision_label).inc()

        if not allow:
            identifier = event.get("event_id") or str(uuid.uuid4())
            payload = dict(event)
            payload["timestamp"] = time.time()
            await self._executor.requeue.add(identifier, payload)
            REQUEUE_EVENTS.labels(tool_label, "policy_denied").inc()
            await self._executor.publish_result(
                event,
                status="blocked",
                payload={"message": "Policy denied tool execution."},
                execution_time=0.0,
                metadata=metadata,
            )
            await log_tool_event(
                self._executor.get_audit_store(),
                action="tool.execute.finish",
                tool_name=tool_name,
                session_id=session_id,
                tenant=tenant,
                persona_id=persona_id,
                event_id=event.get("event_id"),
                trace_id=trace_id_hex,
                details={"status": "blocked", "reason": "policy_denied"},
            )
            return "policy_denied"

        return None

    async def _handle_unknown_tool(
        self,
        event: dict[str, Any],
        tool_name: str,
        tool_label: str,
        metadata: dict[str, Any],
        session_id: str,
        tenant: str,
        persona_id: str | None,
        trace_id_hex: str | None,
    ) -> None:
        """Handle request for unknown tool."""
        await self._executor.publish_result(
            event,
            status="error",
            payload={"message": f"Unknown tool '{tool_name}'"},
            execution_time=0.0,
            metadata=metadata,
        )
        TOOL_REQUEST_COUNTER.labels(tool_label, "unknown_tool").inc()
        await log_tool_event(
            self._executor.get_audit_store(),
            action="tool.execute.finish",
            tool_name=tool_name,
            session_id=session_id,
            tenant=tenant,
            persona_id=persona_id,
            event_id=event.get("event_id"),
            trace_id=trace_id_hex,
            details={"status": "error", "reason": "unknown_tool"},
        )

    async def _publish_tool_start(
        self,
        event: dict[str, Any],
        session_id: str,
        persona_id: str | None,
        tool_name: str,
        metadata: dict[str, Any],
    ) -> None:
        """Publish tool.start event for UI."""
        try:
            ui_meta = dict(metadata or {})
            ui_meta.update(
                {
                    "status": "start",
                    "source": "tool_executor",
                    "tool_name": tool_name,
                }
            )
            req_id = (metadata or {}).get("request_id") or event.get("event_id")
            if req_id:
                ui_meta["request_id"] = req_id
            start_event = {
                "event_id": str(uuid.uuid4()),
                "session_id": session_id,
                "persona_id": persona_id,
                "role": "tool",
                "message": "",
                "metadata": ui_meta,
                "version": "sa01-v1",
                "type": "tool.start",
            }
            await self._executor.publisher.publish(
                cfg.env("CONVERSATION_OUTBOUND", "conversation.outbound"),
                start_event,
                dedupe_key=start_event.get("event_id"),
                session_id=str(session_id),
                tenant=(ui_meta or {}).get("tenant"),
            )
        except Exception:
            LOGGER.debug("Failed to publish tool.start to conversation.outbound", exc_info=True)

    async def _execute_tool(
        self,
        tool: Any,
        tool_name: str,
        tool_label: str,
        args: dict[str, Any],
        event: dict[str, Any],
        metadata: dict[str, Any],
        session_id: str,
        tenant: str,
        persona_id: str | None,
        trace_id_hex: str | None,
    ) -> Any | None:
        """Execute tool and return result, or None if error occurred."""
        try:
            TOOL_INFLIGHT.labels(tool_label).inc()
            result = await self._executor.execution_engine.execute(tool, args, default_limits())
        except ToolExecutionError as exc:
            LOGGER.error("Tool execution failed", extra={"tool": tool_name, "error": str(exc)})
            await self._executor.publish_result(
                event,
                status="error",
                payload={"message": str(exc)},
                execution_time=0.0,
                metadata=metadata,
            )
            TOOL_REQUEST_COUNTER.labels(tool_label, "execution_error").inc()
            TOOL_INFLIGHT.labels(tool_label).dec()
            await log_tool_event(
                self._executor.get_audit_store(),
                action="tool.execute.finish",
                tool_name=tool_name,
                session_id=session_id,
                tenant=tenant,
                persona_id=persona_id,
                event_id=event.get("event_id"),
                trace_id=trace_id_hex,
                details={"status": "error", "reason": "execution_error"},
            )
            return None
        except Exception as exc:
            LOGGER.error(
                "Error processing tool request",
                extra={
                    "error": str(exc),
                    "error_type": type(exc).__name__,
                    "tool_name": tool_name,
                },
            )
            await self._executor.publish_result(
                event,
                status="error",
                payload={"message": "Unhandled tool executor error."},
                execution_time=0.0,
                metadata={**metadata, "error": str(exc)},
            )
            TOOL_REQUEST_COUNTER.labels(tool_label, "unexpected_error").inc()
            TOOL_INFLIGHT.labels(tool_label).dec()
            await log_tool_event(
                self._executor.get_audit_store(),
                action="tool.execute.finish",
                tool_name=tool_name,
                session_id=session_id,
                tenant=tenant,
                persona_id=persona_id,
                event_id=event.get("event_id"),
                trace_id=trace_id_hex,
                details={"status": "error", "reason": "unexpected_error"},
            )
            return None
        else:
            TOOL_INFLIGHT.labels(tool_label).dec()
            TOOL_EXECUTION_LATENCY.labels(tool_label).observe(result.execution_time)
            TOOL_REQUEST_COUNTER.labels(tool_label, result.status).inc()
            return result
