from opentelemetry import trace

from services.common.trace_context import extract_trace_context, inject_trace_context
from services.common.tracing import setup_tracing

setup_tracing("test-harness", disable_exporter=True)


def test_inject_adds_trace_context_keys():
    tracer = trace.get_tracer("test-harness")
    event = {"foo": "bar"}

    with tracer.start_as_current_span("inject"):
        inject_trace_context(event)

    assert "trace_context" in event
    assert isinstance(event["trace_context"], dict)
    assert event["trace_context"]


def test_extract_restores_span_context():
    tracer = trace.get_tracer("test-harness")
    event = {}

    with tracer.start_as_current_span("parent") as span:
        inject_trace_context(event)
        parent_ctx = span.get_span_context()

    ctx = extract_trace_context(event)
    tracer = trace.get_tracer(__name__)

    with tracer.start_as_current_span("child", context=ctx) as child_span:
        child_ctx = child_span.get_span_context()
        assert child_ctx.trace_id == parent_ctx.trace_id
        assert child_ctx.span_id != 0
