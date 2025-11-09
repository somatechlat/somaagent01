import pytest
from opentelemetry.trace import SpanContext, TraceFlags, TraceState

from services.common.event_bus import _build_trace_headers


def _make_span_context(trace_id: int, span_id: int) -> SpanContext:
    # Construct a local (non-remote) span context with sampled flag set
    return SpanContext(
        trace_id=trace_id,
        span_id=span_id,
        is_remote=False,
        trace_flags=TraceFlags(0x01),
        trace_state=TraceState(),
    )


def test_build_trace_headers_includes_traceparent():
    sc = _make_span_context(0x1234567890ABCDEF1234567890ABCDEF, 0xCAFEBABE12345678)
    headers = _build_trace_headers(sc)
    # Convert list of tuples to dict for assertions
    hmap = {k: v.decode("utf-8") for k, v in headers}
    assert "trace_id" in hmap
    assert "span_id" in hmap
    assert "traceparent" in hmap
    assert hmap["trace_id"].startswith("12345678")  # sanity prefix check
    assert hmap["span_id"].startswith("cafebabe")
    # traceparent format: 00-<32hex trace>-<16hex span>-<flags>
    parts = hmap["traceparent"].split("-")
    assert parts[0] == "00"
    assert len(parts[1]) == 32
    assert len(parts[2]) == 16
    assert parts[3] in {"01", "00"}


def test_build_trace_headers_empty_on_missing_ids():
    sc = _make_span_context(0, 0)
    headers = _build_trace_headers(sc)
    assert headers == []
