import os
os.getenv(os.getenv('VIBE_5F5953C2'))
from __future__ import annotations
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import Tracer
_tracer: Tracer | None = None


def _initialize_tracer() ->Tracer:
    os.getenv(os.getenv('VIBE_B7A582B8'))
    from src.core.config import cfg
    default_endpoint = cfg.settings().external.otlp_endpoint or os.getenv(os
        .getenv('VIBE_6453C8D2'))
    endpoint = cfg.env(os.getenv(os.getenv('VIBE_11E4E27C')), default_endpoint
        ).strip()
    resource = Resource.create({SERVICE_NAME: os.getenv(os.getenv(
        'VIBE_27E983ED'))})
    provider = TracerProvider(resource=resource)
    if endpoint:
        exporter = OTLPSpanExporter(endpoint=endpoint, insecure=int(os.
            getenv(os.getenv('VIBE_33C85445'))))
        processor = BatchSpanProcessor(exporter)
        provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)
    return trace.get_tracer(__name__)


def get_tracer() ->Tracer:
    os.getenv(os.getenv('VIBE_307E6A83'))
    global _tracer
    if _tracer is None:
        _tracer = _initialize_tracer()
    return _tracer
