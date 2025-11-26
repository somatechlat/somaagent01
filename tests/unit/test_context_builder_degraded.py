import asyncio

import pytest

from observability.metrics import ContextBuilderMetrics
from python.somaagent.context_builder import ContextBuilder, SomabrainHealthState


class FakeSomabrain:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    async def context_evaluate(self, body):
        self.calls.append(body)
        await asyncio.sleep(0)
        return self.payload


@pytest.mark.asyncio
async def test_context_builder_limits_snippets_when_degraded():
    snippets = [{"id": f"m{i}", "text": f"Memory {i}", "score": float(10 - i)} for i in range(6)]
    fake = FakeSomabrain({"candidates": snippets})
    builder = ContextBuilder(
        somabrain=fake,
        metrics=ContextBuilderMetrics(),
        token_counter=lambda text: len(text.split()),
        health_provider=lambda: SomabrainHealthState.DEGRADED,
    )
    built = await builder.build_for_turn(
        {
            "tenant_id": "t-1",
            "session_id": "s-1",
            "system_prompt": "System",
            "user_message": "Hello",
            "history": [],
        },
        max_prompt_tokens=4000,
    )
    assert fake.calls, "Somabrain was never queried in degraded state"
    assert fake.calls[0]["top_k"] == ContextBuilder.DEGRADED_TOP_K
    assert built.debug["somabrain_state"] == "degraded"
    assert built.debug["snippet_count"] == ContextBuilder.DEGRADED_TOP_K


@pytest.mark.asyncio
async def test_context_builder_skips_retrieval_when_down():
    fake = FakeSomabrain({"candidates": [{"id": "x", "text": "should not use"}]})
    builder = ContextBuilder(
        somabrain=fake,
        metrics=ContextBuilderMetrics(),
        token_counter=lambda text: len(text.split()),
        health_provider=lambda: SomabrainHealthState.DOWN,
    )
    built = await builder.build_for_turn(
        {
            "tenant_id": "t-1",
            "session_id": "s-2",
            "system_prompt": "System",
            "user_message": "Hello",
            "history": [],
        },
        max_prompt_tokens=1024,
    )
    assert fake.calls == [], "Somabrain should not be queried when DOWN"
    assert built.debug["somabrain_state"] == "down"
    assert built.debug["snippet_count"] == 0
    # Only system + user messages expected
    roles = [msg["role"] for msg in built.messages]
    assert roles.count("system") == 1
    assert roles.count("user") == 1


@pytest.mark.asyncio
async def test_context_builder_marks_normal_state_when_available():
    snippets = [{"id": f"m{i}", "text": f"Memory {i}", "score": 1.0} for i in range(2)]
    fake = FakeSomabrain({"candidates": snippets})
    builder = ContextBuilder(
        somabrain=fake,
        metrics=ContextBuilderMetrics(),
        token_counter=lambda text: len(text.split()),
        health_provider=lambda: SomabrainHealthState.NORMAL,
    )
    built = await builder.build_for_turn(
        {
            "tenant_id": "t-1",
            "session_id": "s-3",
            "system_prompt": "System",
            "user_message": "Hello",
            "history": [],
        },
        max_prompt_tokens=512,
    )
    assert built.debug["somabrain_state"] == "normal"
    assert built.debug["snippet_count"] == len(snippets)
