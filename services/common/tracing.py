"""Lightweight OpenTelemetry tracing setup used across services.

If no endpoint is provided, tracing is left unconfigured. When an OTLP gRPC
endpoint is provided, a BatchSpanProcessor + OTLPSpanExporter is installed.
"""

from __future__ import annotations

from typing import Optional

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


def setup_tracing(service_name: str, *, endpoint: Optional[str] = None) -> Optional[TracerProvider]:
	"""Configure OpenTelemetry tracing for a service.

	Parameters:
		service_name: Logical name reported in traces.
		endpoint: OTLP gRPC endpoint (e.g., http://localhost:4317). If empty/None, skip.

	Returns the configured TracerProvider, or None if disabled.
	"""
	if not endpoint:
		return None

	# Accept http(s)://host:port or host:port; exporter handles both
	resource = Resource.create({"service.name": service_name})
	provider = TracerProvider(resource=resource)
	exporter = OTLPSpanExporter(endpoint=endpoint)
	processor = BatchSpanProcessor(exporter)
	provider.add_span_processor(processor)
	trace.set_tracer_provider(provider)
	return provider

