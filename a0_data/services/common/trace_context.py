"""Utilities for propagating OpenTelemetry trace context through Kafka events."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Dict

from opentelemetry import trace
from opentelemetry.context import attach, detach
from opentelemetry.propagate import extract, inject

TRACE_CONTEXT_KEY = "trace_context"


def inject_trace_context(event: Dict[str, Any]) -> Dict[str, Any]:
    """Inject the current OpenTelemetry context into *event*.

    The caller receives the same dictionary instance to allow inline usage:

    >>> event = inject_trace_context({"payload": 1})
    >>> event["trace_context"]  # doctest: +SKIP
    {...}
    """

    carrier: Dict[str, str] = {}
    inject(carrier)
    trace_map = event.setdefault(TRACE_CONTEXT_KEY, {})
    trace_map.update(carrier)
    return event


def extract_trace_context(event: Dict[str, Any]):
    """Extract an OpenTelemetry context from *event* if present."""

    carrier = event.get(TRACE_CONTEXT_KEY, {})
    if not isinstance(carrier, dict):
        return trace.set_span_in_context(trace.get_current_span())
    return extract(carrier)


@contextmanager
def with_trace_context(event: Dict[str, Any]):
    """Context manager to run work inside the event's trace context."""

    ctx = extract_trace_context(event)
    token = attach(ctx)
    try:
        yield
    finally:
        detach(token)
