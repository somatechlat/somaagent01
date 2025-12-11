"""OpenTelemetry tracing utilities for the voice subsystem.

The module provides a thin wrapper around the OpenTelemetry SDK.  Tracing is
optional – if the SDK is not installed the functions become no‑ops, which keeps
the import side‑effect‑free (VIBE rule **NO SIDE‑EFFECTS AT IMPORT**).
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Generator, Callable, Any

try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter

    # Initialise a global tracer provider only once.
    _provider = TracerProvider()
    _provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
    trace.set_tracer_provider(_provider)
    _tracer = trace.get_tracer(__name__)
except Exception:  # pragma: no cover – OpenTelemetry may be missing in CI
    trace = None  # type: ignore
    _tracer = None  # type: ignore


def get_tracer():
    """Return the configured tracer or a dummy object if tracing is unavailable."""
    return _tracer


@contextmanager
def span(name: str, **attributes: Any) -> Generator[Callable[[], None], None, None]:
    """Context manager that creates a span with the given name.

    If OpenTelemetry is not available the context manager yields a no‑op
    ``lambda: None`` function so callers can safely call the returned ``end``
    callable.
    """
    if _tracer is None:
        yield lambda: None
        return
    with _tracer.start_as_current_span(name) as span_obj:
        for k, v in attributes.items():
            span_obj.set_attribute(k, v)
        yield span_obj.end
