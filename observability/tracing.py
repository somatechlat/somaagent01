"""OpenTelemetry tracing utilities for SomaAgent01.

The project uses a *single* tracer that is shared by all services. If the
environment variable ``SA01_OTLP_ENDPOINT`` is defined, the tracer is
configured to export to that endpoint; otherwise a no‑op tracer is returned
so that the rest of the code can call ``get_tracer()`` unconditionally.

All services import ``get_tracer`` and use ``tracer.start_as_current_span``
to create spans for their lifecycle events. The implementation follows the
official OpenTelemetry Python documentation (see
https://opentelemetry.io/docs/instrumentation/python/).
"""

from __future__ import annotations

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import Tracer

_tracer: Tracer | None = None


def _initialize_tracer() -> Tracer:
    """Create and configure the global tracer.

    If ``SA01_OTLP_ENDPOINT`` is not set or empty, a ``TracerProvider`` with
    a ``BatchSpanProcessor`` that discards spans is used – this results in a
    no‑op tracer that has negligible overhead.
    """
    from src.core.config import cfg

    default_endpoint = cfg.settings().external.otlp_endpoint or ""
    endpoint = cfg.env("SA01_OTLP_ENDPOINT", default_endpoint).strip()
    resource = Resource.create({SERVICE_NAME: "somaagent01"})

    provider = TracerProvider(resource=resource)
    if endpoint:
        exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)
        processor = BatchSpanProcessor(exporter)
        provider.add_span_processor(processor)
    # When no endpoint is configured the provider has no processors – spans are
    # created but never exported, which is effectively a no‑op.
    trace.set_tracer_provider(provider)
    return trace.get_tracer(__name__)


def get_tracer() -> Tracer:
    """Return a singleton tracer instance.

    The function is cheap after the first call because the tracer is cached in
    the module‑level ``_tracer`` variable.
    """
    global _tracer
    if _tracer is None:
        _tracer = _initialize_tracer()
    return _tracer
