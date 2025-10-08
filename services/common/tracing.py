"""OpenTelemetry tracing setup helpers for SomaAgent services."""

from __future__ import annotations

import os
from typing import Optional

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.resources import SERVICE_NAME as OTEL_SERVICE_NAME
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
    SimpleSpanProcessor,
)
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

_TRACER_INITIALISED = False


def _build_resource(service_name: str) -> Resource:
    base = Resource.create(
        {
            OTEL_SERVICE_NAME: service_name,
            "deployment.environment": os.getenv("SOMA_AGENT_MODE", "LOCAL"),
        }
    )
    if hasattr(Resource, "from_env"):
        return base.merge(Resource.from_env())
    return base


def _should_disable_exporter() -> bool:
    """Check environment flag for disabling OTLP exporter."""

    return os.getenv("OTEL_EXPORTER_OTLP_DISABLED", "false").lower() in {"true", "1", "yes"}


def setup_tracing(
    service_name: str,
    *,
    endpoint: Optional[str] = None,
    disable_exporter: bool | None = None,
) -> trace.Tracer:
    """Initialise OpenTelemetry and return a tracer for *service_name*."""

    global _TRACER_INITIALISED
    if disable_exporter is None:
        disable_exporter = _should_disable_exporter()

    if not _TRACER_INITIALISED:
        resource = _build_resource(service_name)
        provider = TracerProvider(resource=resource)
        if disable_exporter:
            provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
        else:
            otlp_exporter = OTLPSpanExporter(
                endpoint=(
                    endpoint
                    or os.getenv(
                        "OTEL_EXPORTER_OTLP_ENDPOINT",
                        "http://otel-collector:4317",
                    )
                ),
                insecure=True,
            )
            provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
        trace.set_tracer_provider(provider)
        _instrument_libraries()
        _TRACER_INITIALISED = True

    return trace.get_tracer(service_name)


def _instrument_libraries() -> None:
    """Attempt to auto-instrument supported libraries if available."""

    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        FastAPIInstrumentor().instrument()
    except Exception:
        pass

    try:
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

        HTTPXClientInstrumentor().instrument()
    except Exception:
        pass

    try:
        from opentelemetry.instrumentation.asyncpg import AsyncPGInstrumentor

        AsyncPGInstrumentor().instrument()
    except Exception:
        pass

    try:
        from opentelemetry.instrumentation.redis import RedisInstrumentor

        RedisInstrumentor().instrument()
    except Exception:
        pass
