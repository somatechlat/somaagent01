"""Audit logging utilities for tool executor."""

import logging
from typing import Any

LOGGER = logging.getLogger(__name__)


async def log_tool_event(
    audit_store,
    action: str,
    tool_name: str,
    session_id: str,
    tenant: str,
    persona_id: str | None,
    event_id: str | None,
    trace_id: str | None,
    details: dict[str, Any],
) -> None:
    """Log a tool execution audit event (best-effort)."""
    try:
        await audit_store.log(
            request_id=None,
            trace_id=trace_id,
            session_id=session_id,
            tenant=tenant,
            subject=str(persona_id) if persona_id else None,
            action=action,
            resource=str(tool_name),
            target_id=event_id,
            details=details,
            diff=None,
            ip=None,
            user_agent=None,
        )
    except Exception:
        LOGGER.debug(f"Failed to write audit log for {action}", exc_info=True)


def get_trace_id() -> str | None:
    """Extract current OpenTelemetry trace ID if available."""
    try:
        from opentelemetry import trace as _trace

        ctx = _trace.get_current_span().get_span_context()
        return f"{ctx.trace_id:032x}" if getattr(ctx, "trace_id", 0) else None
    except Exception:
        return None
