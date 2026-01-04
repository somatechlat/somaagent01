"""Result publishing logic for tool executor service.

This module handles publishing tool execution results, sending feedback
to SomaBrain, and capturing memory for successful executions.
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from typing import Any, TYPE_CHECKING

from admin.core.soma_client import SomaClientError
from services.common.idempotency import generate_for_memory_payload
from services.common.policy_client import PolicyRequest
from services.tool_executor.metrics import TOOL_FEEDBACK_TOTAL
from services.tool_executor.validation import validate_tool_result
import os

if TYPE_CHECKING:
    from services.tool_executor.main import ToolExecutor

LOGGER = logging.getLogger(__name__)


class ResultPublisher:
    """Publishes tool execution results and handles feedback/memory."""

    def __init__(self, executor: "ToolExecutor") -> None:
        """Initialize the instance."""

        self._executor = executor

    async def publish(
        self,
        event: dict[str, Any],
        status: str,
        payload: dict[str, Any],
        *,
        execution_time: float,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Publish a tool execution result."""
        result_event = {
            "event_id": str(uuid.uuid4()),
            "session_id": event.get("session_id"),
            "persona_id": event.get("persona_id"),
            "tool_name": event.get("tool_name"),
            "status": status,
            "payload": payload,
            "metadata": metadata if metadata is not None else event.get("metadata", {}),
            "execution_time": execution_time,
        }

        if not validate_tool_result(result_event):
            return

        await self._executor.store.append_event(
            event.get("session_id", "unknown"), {"type": "tool", **result_event}
        )
        await self._executor.publisher.publish(
            self._executor.streams["results"],
            result_event,
            dedupe_key=result_event.get("event_id"),
            session_id=result_event.get("session_id"),
            tenant=(result_event.get("metadata") or {}).get("tenant"),
        )

        # Publish UI-friendly outbound event
        await self._publish_ui_event(result_event, status, execution_time, payload)

        # Emit telemetry
        await self._executor.telemetry.emit_tool_execution(result_event, status, execution_time)

        # Send feedback and capture memory
        await self._send_feedback(result_event)

    async def _publish_ui_event(
        self,
        result_event: dict[str, Any],
        status: str,
        execution_time: float,
        payload: dict[str, Any],
    ) -> None:
        """Publish UI-friendly event to conversation.outbound."""
        try:
            if isinstance(payload, str):
                tool_text = payload
            else:
                try:
                    tool_text = json.dumps(payload, ensure_ascii=False)
                except Exception:
                    tool_text = str(payload)

            ui_meta = dict(result_event.get("metadata") or {})
            ui_meta.update(
                {
                    "status": status,
                    "source": "tool_executor",
                    "tool_name": result_event.get("tool_name"),
                    "execution_time": execution_time,
                }
            )
            outbound_event = {
                "event_id": str(uuid.uuid4()),
                "session_id": result_event.get("session_id"),
                "persona_id": result_event.get("persona_id"),
                "role": "tool",
                "message": tool_text,
                "metadata": ui_meta,
                "version": "sa01-v1",
                "type": "tool.result",
            }
            await self._executor.publisher.publish(
                os.environ.get("CONVERSATION_OUTBOUND", "conversation.outbound"),
                outbound_event,
                dedupe_key=outbound_event.get("event_id"),
                session_id=str(result_event.get("session_id")),
                tenant=(ui_meta or {}).get("tenant"),
            )
        except Exception:
            LOGGER.debug("Failed to publish tool result to conversation.outbound", exc_info=True)

    async def _send_feedback(self, result_event: dict[str, Any]) -> None:
        """Send tool execution feedback to SomaBrain."""
        feedback = {
            "task_name": result_event.get("tool_name"),
            "tenant_id": (result_event.get("metadata") or {}).get("tenant"),
            "persona_id": result_event.get("persona_id"),
            "session_id": result_event.get("session_id"),
            "success": result_event.get("status") == "success",
            "latency_ms": int((result_event.get("execution_time") or 0) * 1000),
            "error_type": (
                None if result_event.get("status") == "success" else result_event.get("status")
            ),
            "tags": ["tool_executor"],
        }
        try:
            await self._executor.soma.context_feedback(feedback)
            TOOL_FEEDBACK_TOTAL.labels("delivered").inc()
        except Exception as exc:
            try:
                await self._executor.publisher.publish(
                    os.environ.get("TASK_FEEDBACK_TOPIC", "task.feedback.dlq"),
                    {"payload": feedback, "error": str(exc)},
                    dedupe_key=str(result_event.get("event_id")),
                    session_id=str(result_event.get("session_id")),
                    tenant=feedback.get("tenant_id"),
                )
                TOOL_FEEDBACK_TOTAL.labels("queued_dlq").inc()
            except Exception:
                LOGGER.debug("Failed to enqueue tool feedback DLQ", exc_info=True)
                TOOL_FEEDBACK_TOTAL.labels("failed").inc()

        # Capture memory for successful executions
        result_status = result_event.get("status")
        result_payload = result_event.get("payload", {})
        result_tenant = (result_event.get("metadata") or {}).get("tenant", "default")
        if result_status == "success":
            await self._capture_memory(result_event, result_payload, result_tenant)

    async def _capture_memory(
        self,
        result_event: dict[str, Any],
        payload: dict[str, Any],
        tenant: str,
    ) -> None:
        """Capture tool result as memory in SomaBrain."""
        persona_id = result_event.get("persona_id")
        if isinstance(payload, str):
            content = payload
        else:
            try:
                content = json.dumps(payload, ensure_ascii=False)
            except Exception:
                content = str(payload)

        metadata = result_event.get("metadata") or {}
        str_metadata = {str(key): str(value) for key, value in metadata.items()}
        if result_event.get("tool_name"):
            str_metadata.setdefault("tool_name", str(result_event.get("tool_name")))
        if result_event.get("session_id"):
            str_metadata.setdefault("session_id", str(result_event.get("session_id")))
        if isinstance(payload, dict) and payload.get("model"):
            str_metadata.setdefault("tool_model", str(payload.get("model")))

        memory_payload = {
            "id": result_event.get("event_id"),
            "type": "tool_result",
            "tool_name": result_event.get("tool_name"),
            "content": content,
            "session_id": result_event.get("session_id"),
            "persona_id": persona_id,
            "metadata": {
                **str_metadata,
                "agent_profile_id": (result_event.get("metadata") or {}).get("agent_profile_id"),
                "universe_id": (result_event.get("metadata") or {}).get("universe_id")
                or os.environ.get("SA01_NAMESPACE"),
            },
            "status": result_event.get("status"),
        }
        memory_payload["idempotency_key"] = generate_for_memory_payload(memory_payload)

        try:
            allow_memory = False
            try:
                allow_memory = await self._executor.policy.evaluate(
                    PolicyRequest(
                        tenant=tenant,
                        persona_id=persona_id,
                        action="memory.write",
                        resource="somabrain",
                        context={
                            "payload_type": memory_payload.get("type"),
                            "tool_name": memory_payload.get("tool_name"),
                            "session_id": memory_payload.get("session_id"),
                            "metadata": memory_payload.get("metadata", {}),
                        },
                    )
                )
            except Exception:
                LOGGER.warning(
                    "OPA memory.write check failed; denying by fail-closed policy", exc_info=True
                )

            if allow_memory:
                wal_topic = os.environ.get("MEMORY_WAL_TOPIC", "memory.wal")
                result = await self._executor.soma.remember(memory_payload)
                try:
                    wal_event = {
                        "type": "memory.write",
                        "role": "tool",
                        "session_id": result_event.get("session_id"),
                        "persona_id": persona_id,
                        "tenant": tenant,
                        "payload": memory_payload,
                        "result": {
                            "coord": (result or {}).get("coordinate")
                            or (result or {}).get("coord"),
                            "trace_id": (result or {}).get("trace_id"),
                            "request_id": (result or {}).get("request_id"),
                        },
                        "timestamp": time.time(),
                    }
                    await self._executor.publisher.publish(
                        wal_topic,
                        wal_event,
                        dedupe_key=str(memory_payload.get("id")),
                        session_id=str(result_event.get("session_id")),
                        tenant=tenant,
                    )
                except Exception:
                    LOGGER.debug("Failed to publish memory WAL (tool result)", exc_info=True)
            else:
                LOGGER.info(
                    "memory.write denied by policy",
                    extra={
                        "session_id": result_event.get("session_id"),
                        "tool": result_event.get("tool_name"),
                        "event_id": result_event.get("event_id"),
                    },
                )
        except SomaClientError as exc:
            LOGGER.warning(
                "SomaBrain remember failed for tool result",
                extra={
                    "session_id": result_event.get("session_id"),
                    "tool": result_event.get("tool_name"),
                    "error": str(exc),
                },
            )
        except Exception:
            LOGGER.debug("SomaBrain remember (tool result) unexpected error", exc_info=True)