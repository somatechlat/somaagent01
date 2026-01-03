"""Tool execution tracking for SomaBrain learning.

VIBE COMPLIANT: Real implementation that sends feedback to SomaBrain.
Queues events when SomaBrain is unavailable for later retry.
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

from admin.core.observability.metrics import Counter, Histogram

LOGGER = logging.getLogger(__name__)

# Prometheus metrics for tool execution tracking
TOOL_EXEC_TOTAL = Counter(
    "tool_execution_total",
    "Total tool executions",
    labelnames=("tool_name", "status"),
)
TOOL_EXEC_DURATION = Histogram(
    "tool_execution_duration_seconds",
    "Tool execution duration in seconds",
    labelnames=("tool_name",),
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0),
)
TOOL_TRACKING_QUEUED = Counter(
    "tool_tracking_queued_total",
    "Tool tracking events queued for retry",
    labelnames=("tool_name",),
)


@dataclass
class ToolExecutionEvent:
    """Event representing a tool execution for learning."""

    tool_name: str
    tool_args: Dict[str, Any]
    response: str
    success: bool
    duration_seconds: float
    session_id: Optional[str] = None
    tenant_id: Optional[str] = None
    persona_id: Optional[str] = None
    timestamp: float = 0.0

    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()


# In-memory queue for events when SomaBrain is unavailable
_pending_events: list[ToolExecutionEvent] = []
_queue_lock = asyncio.Lock()
MAX_QUEUE_SIZE = 1000


async def _track_tool_execution_for_learning(
    tool_name: str,
    tool_args: Dict[str, Any],
    response: str,
    success: bool,
    duration_seconds: float,
    session_id: Optional[str] = None,
    tenant_id: Optional[str] = None,
    persona_id: Optional[str] = None,
) -> None:
    """Track tool execution and send to SomaBrain for learning.

    VIBE: Real implementation that sends feedback to SomaBrain /context/feedback.
    If SomaBrain is unavailable, events are queued for later retry.

    Args:
        tool_name: Name of the executed tool
        tool_args: Arguments passed to the tool
        response: Tool response (truncated if too long)
        success: Whether the tool execution succeeded
        duration_seconds: Execution duration in seconds
        session_id: Optional session ID for context
        tenant_id: Optional tenant ID for multi-tenancy
        persona_id: Optional persona ID for personalization
    """
    # Record Prometheus metrics
    status = "success" if success else "failure"
    TOOL_EXEC_TOTAL.labels(tool_name=tool_name, status=status).inc()
    TOOL_EXEC_DURATION.labels(tool_name=tool_name).observe(duration_seconds)

    # Create event
    event = ToolExecutionEvent(
        tool_name=tool_name,
        tool_args=_sanitize_args(tool_args),
        response=_truncate_response(response),
        success=success,
        duration_seconds=duration_seconds,
        session_id=session_id,
        tenant_id=tenant_id,
        persona_id=persona_id,
    )

    # Try to send to SomaBrain
    try:
        await _send_to_somabrain(event)
    except Exception as e:
        LOGGER.warning(f"Failed to send tool tracking to SomaBrain: {e}")
        await _queue_event(event)


async def _send_to_somabrain(event: ToolExecutionEvent) -> None:
    """Send tool execution feedback to SomaBrain.

    Uses the /context/feedback endpoint for learning.
    """
    # Check if SomaBrain is enabled
    if not os.environ.get("SOMABRAIN_ENABLED"):
        LOGGER.debug("SomaBrain disabled, skipping tool tracking")
        return

    try:
        from admin.core.soma_client import SomaClient

        client = SomaClient.get()

        # Build feedback payload
        feedback = {
            "session_id": event.session_id or "unknown",
            "query": f"tool:{event.tool_name}",
            "prompt": str(event.tool_args),
            "response_text": event.response,
            "utility": 1.0 if event.success else 0.0,
            "reward": 1.0 if event.success else -0.5,
            "tenant_id": event.tenant_id,
            "metadata": {
                "tool_name": event.tool_name,
                "duration_seconds": event.duration_seconds,
                "success": event.success,
                "persona_id": event.persona_id,
                "timestamp": event.timestamp,
            },
        }

        await client.context_feedback(**feedback)
        LOGGER.debug(f"Tool tracking sent to SomaBrain: {event.tool_name}")

    except Exception as e:
        # Re-raise to trigger queueing
        raise RuntimeError(f"SomaBrain feedback failed: {e}") from e


async def _queue_event(event: ToolExecutionEvent) -> None:
    """Queue event for later retry when SomaBrain is unavailable."""
    async with _queue_lock:
        if len(_pending_events) >= MAX_QUEUE_SIZE:
            # Drop oldest events if queue is full
            _pending_events.pop(0)
            LOGGER.warning("Tool tracking queue full, dropping oldest event")

        _pending_events.append(event)
        TOOL_TRACKING_QUEUED.labels(tool_name=event.tool_name).inc()
        LOGGER.debug(f"Queued tool tracking event: {event.tool_name}")


async def flush_pending_events() -> int:
    """Flush pending events to SomaBrain.

    Called by periodic task.
    Returns number of events successfully sent.
    """
    async with _queue_lock:
        events = _pending_events.copy()
        _pending_events.clear()

    sent = 0
    for event in events:
        try:
            await _send_to_somabrain(event)
            sent += 1
        except Exception as e:
            LOGGER.warning(f"Failed to flush tool tracking event: {e}")
            # Re-queue failed events
            async with _queue_lock:
                if len(_pending_events) < MAX_QUEUE_SIZE:
                    _pending_events.append(event)

    return sent


def _sanitize_args(args: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitize tool arguments for storage.

    Removes sensitive data and truncates large values.
    """
    sanitized = {}
    sensitive_keys = {"password", "secret", "token", "api_key", "key", "credential"}

    for key, value in args.items():
        if any(s in key.lower() for s in sensitive_keys):
            sanitized[key] = "[REDACTED]"
        elif isinstance(value, str) and len(value) > 1000:
            sanitized[key] = value[:1000] + "...[truncated]"
        elif isinstance(value, (dict, list)):
            # Convert to string and truncate
            str_val = str(value)
            if len(str_val) > 1000:
                sanitized[key] = str_val[:1000] + "...[truncated]"
            else:
                sanitized[key] = value
        else:
            sanitized[key] = value

    return sanitized


def _truncate_response(response: str, max_length: int = 5000) -> str:
    """Truncate response to reasonable length for storage."""
    if len(response) <= max_length:
        return response
    return response[:max_length] + "...[truncated]"


# Export the main tracking function
track_tool_execution = _track_tool_execution_for_learning
