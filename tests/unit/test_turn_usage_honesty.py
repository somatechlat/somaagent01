"""Turn token metrics must come from the LLM response, or be absent.

A metric that always reports zero is a lie. A metric that reports a tiktoken
estimate as if the provider billed it is also a lie. The LLM response carries
usage (``prompt_tokens`` / ``completion_tokens``); when a path genuinely has
no usage, the metric is ``None`` — not a fabricated ``0``.
"""

from __future__ import annotations

import inspect
from types import SimpleNamespace

from admin.core.chat_orchestrator import V3ChatOrchestrator
from admin.llm.services.litellm_helpers import _parse_chunk, prepare_completion_kwargs
from services.common.unified_metrics import TurnMetrics, TurnUsage, UnifiedMetrics


class TestParseChunkCarriesProviderUsage:
    def test_usage_is_extracted_from_the_chunk(self):
        chunk = {
            "choices": [{"delta": {"content": "hi"}, "message": {}}],
            "usage": {"prompt_tokens": 11, "completion_tokens": 3, "total_tokens": 14},
        }
        parsed = _parse_chunk(chunk)
        assert parsed["usage"] == {
            "prompt_tokens": 11,
            "completion_tokens": 3,
            "total_tokens": 14,
        }

    def test_absent_usage_is_not_invented(self):
        chunk = {"choices": [{"delta": {"content": "hi"}, "message": {}}]}
        parsed = _parse_chunk(chunk)
        assert parsed.get("usage") is None

    def test_streaming_requests_provider_usage(self):
        """Without include_usage a stream often never reports tokens."""
        kwargs, is_stream = prepare_completion_kwargs("gpt-4o", {}, stream=True)
        assert is_stream is True
        assert kwargs.get("stream_options") == {"include_usage": True}


class TestTurnUsage:
    def test_starts_unknown_not_zero(self):
        usage = TurnUsage()
        assert usage.prompt_tokens is None
        assert usage.completion_tokens is None

    def test_absorb_adds_reported_usage_across_tool_rounds(self):
        usage = TurnUsage()
        usage.absorb({"prompt_tokens": 10, "completion_tokens": 2})
        usage.absorb({"prompt_tokens": 5, "completion_tokens": 7})
        assert usage.prompt_tokens == 15
        assert usage.completion_tokens == 9

    def test_absorb_ignores_non_usage(self):
        usage = TurnUsage()
        usage.absorb(None)
        usage.absorb({})
        assert usage.prompt_tokens is None
        assert usage.completion_tokens is None

    def test_absorb_skips_missing_fields_without_zeroing(self):
        usage = TurnUsage()
        usage.absorb({"prompt_tokens": 4})
        assert usage.prompt_tokens == 4
        assert usage.completion_tokens is None


class TestRecordTurnCompleteIsHonest:
    def test_tokens_are_optional(self):
        import typing

        hints = typing.get_type_hints(UnifiedMetrics.record_turn_complete)
        assert hints["tokens_in"] == int | None
        assert hints["tokens_out"] == int | None

    def test_turn_metrics_default_is_none_not_zero(self):
        m = TurnMetrics(
            turn_id="t", tenant_id="ten", user_id="u", agent_id="a", start_time=0.0
        )
        assert m.tokens_in is None
        assert m.tokens_out is None

    def test_none_tokens_do_not_increment_the_counter(self):
        class _FakeLabels:
            def __init__(self):
                self.calls = []

            def labels(self, **kw):
                return self

            def inc(self, n=1):
                self.calls.append(n)

        metrics = UnifiedMetrics()
        metrics.TURNS_TOTAL = _FakeLabels()
        metrics.TOKENS_TOTAL = _FakeLabels()
        metrics.ERRORS_TOTAL = _FakeLabels()
        metrics.TURN_LATENCY = SimpleNamespace(labels=lambda **kw: SimpleNamespace(observe=lambda *_: None))
        metrics.ACTIVE_TURNS = SimpleNamespace(labels=lambda **kw: SimpleNamespace(inc=lambda: None, dec=lambda: None))
        metrics._active_turns = {}
        start = metrics.record_turn_start("turn-1", "ten", "u", "a")
        metrics.record_turn_complete(
            turn_id="turn-1",
            tokens_in=None,
            tokens_out=None,
            model="m",
            provider="p",
        )
        assert start.tokens_in is None
        assert metrics.TOKENS_TOTAL.calls == []


class TestChatOrchestratorWiresProviderUsage:
    @staticmethod
    def _stream_src() -> str:
        return inspect.getsource(V3ChatOrchestrator.stream_turn)

    @staticmethod
    def _process_src() -> str:
        return inspect.getsource(V3ChatOrchestrator.process_turn)

    def test_completion_records_provider_usage_not_estimates(self):
        src = self._stream_src()
        assert "usage.prompt_tokens" in src
        assert "usage.completion_tokens" in src
        assert "tokens_in=_token_count" not in src
        assert "tokens_out=_token_count" not in src

    def test_process_turn_also_wires_provider_usage(self):
        src = self._process_src()
        assert "usage.prompt_tokens" in src
        assert "usage.completion_tokens" in src
        assert "tokens_in=_token_count" not in src

    def test_error_paths_pass_none_not_a_fabricated_zero(self):
        for src in (self._stream_src(), self._process_src()):
            assert "tokens_in=0" not in src
            assert "tokens_out=0" not in src

    def test_run_tool_loop_absorbs_usage_into_the_sink(self):
        from admin.core import tool_calling

        src = inspect.getsource(tool_calling.run_tool_loop)
        assert "absorb" in src
