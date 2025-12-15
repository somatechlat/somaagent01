import asyncio
import pytest
import sys
from unittest.mock import MagicMock, AsyncMock

# MOCK HEAVY DEPENDENCIES BEFORE IMPORTING SUT
sys.modules["python.somaagent.agent_context"] = MagicMock()
sys.modules["python.somaagent.conversation_orchestrator"] = MagicMock()
sys.modules["models"] = MagicMock()
sys.modules["sentence_transformers"] = MagicMock()
sys.modules["browser_use"] = MagicMock()
sys.modules["langchain_core"] = MagicMock()
sys.modules["langchain_core.embeddings"] = MagicMock()
sys.modules["langchain_core.embeddings.embeddings"] = MagicMock()

from observability.metrics import ContextBuilderMetrics
from python.somaagent.context_builder import ContextBuilder, SomabrainHealthState, SOMABRAIN_BREAKER
from python.integrations.somabrain_client import SomaClientError
import pybreaker

class FakeSomabrain:
    def __init__(self, payload=None, side_effect=None):
        self.payload = payload
        self.side_effect = side_effect
        self.calls = []

    async def context_evaluate(self, body):
        self.calls.append(body)
        if self.side_effect:
            if isinstance(self.side_effect, list):
                if not self.side_effect:
                    return self.payload
                effect = self.side_effect.pop(0)
                if isinstance(effect, Exception):
                    raise effect
                return effect
            raise self.side_effect
        return self.payload

@pytest.mark.asyncio
async def test_knapsack_optimal_budgeting():
    # Scenario: 
    # A: Cost 10, Score 5
    # B: Cost 10, Score 5
    # C: Cost 15, Score 9
    # Budget: 20
    #
    # Greedy by score density:
    # A: 5/10 = 0.5
    # B: 5/10 = 0.5
    # C: 9/15 = 0.6
    # Greedy picks C (15 cost), remaining 5. Total score 9.
    # Optimal picks A + B (20 cost). Total score 10.
    
    snippets = [
        {"id": "A", "text": "word " * 10, "score": 5.0}, # 10 tokens
        {"id": "B", "text": "word " * 10, "score": 5.0}, # 10 tokens
        {"id": "C", "text": "word " * 15, "score": 9.0}, # 15 tokens
    ]
    
    # Mock token counter: 1 word = 1 token (simple splitting)
    token_counter = lambda t: len(t.strip().split())
    
    # Test Optimal
    fake = FakeSomabrain({"candidates": snippets})
    builder_optimal = ContextBuilder(
        somabrain=fake,
        metrics=ContextBuilderMetrics(),
        token_counter=token_counter,
        use_optimal_budget=True
    )
    
    # We set system + user tokens to 0 effectively for this test logic by mocking/adjusting
    # Actually build_for_turn calculates system/user tokens. 
    # Let's interact with _trim_snippets_optimal directly to isolate the algo logic first
    # or craft a request where system+user is negligible or accounted for.
    selected, tokens = builder_optimal._trim_snippets_optimal(snippets, 20)
    
    # Optimal should select A and B (or equivalent combo with score 10)
    total_score = sum(s["score"] for s in selected)
    assert total_score == 10.0
    assert tokens == 20
    assert len(selected) == 2
    ids = sorted([s["id"] for s in selected])
    assert ids == ["A", "B"]

    # Test Greedy (Default behavior via _trim_snippets_to_budget which takes in order)
    # The current _trim_snippets_to_budget trims from the input list order.
    # The input list to trim is usually ranked by score.
    # If we have [C, A, B] (sorted by score desc), Greedy takes C (15), then stops (remaining 5).
    # Score = 9.
    
    # Let's simulate the ranking order first
    ranked_snippets = sorted(snippets, key=lambda s: s["score"], reverse=True)
    # C (9), A (5), B (5)
    
    builder_greedy = ContextBuilder(
        somabrain=fake,
        metrics=ContextBuilderMetrics(),
        token_counter=token_counter,
        use_optimal_budget=False
    )
    
    selected_g, tokens_g = builder_greedy._trim_snippets_to_budget(ranked_snippets, 30, 20) # 30 is dummy current total
    # It should take C (15), then check A (10) -> 15+10 > 20, break.
    
    assert len(selected_g) == 1
    assert selected_g[0]["id"] == "C"
    assert tokens_g == 15

@pytest.mark.asyncio
async def test_retry_logic():
    # Fail twice with SomaClientError, then succeed
    fake = FakeSomabrain(
        payload={"candidates": []},
        side_effect=[SomaClientError("Fail 1"), SomaClientError("Fail 2"), {"candidates": []}]
    )
    
    builder = ContextBuilder(
        somabrain=fake,
        metrics=ContextBuilderMetrics(),
        token_counter=lambda t: 0
    )
    
    await builder.build_for_turn(
        {"tenant_id": "t1", "session_id": "s1"},
        max_prompt_tokens=100
    )
    
    # Should have called 3 times (2 fails + 1 success)
    assert len(fake.calls) == 3

@pytest.mark.asyncio
async def test_circuit_breaker():
    # Reset breaker
    # AsyncCircuitBreaker doesn't have a close/reset method yet in my simple implementation?
    # Actually, initializing a new one or manually resetting state is fine.
    # Re-import to patch usage
    
    # Access the breaker instance
    breaker = SOMABRAIN_BREAKER
    
    # Reset state manually for test
    async with breaker._lock:
        breaker._state = "closed"
        breaker._fail_count = 0
    
    # Fail enough times to open breaker (fail_max=5)
    fake = FakeSomabrain(
        side_effect=SomaClientError("Persistent Failure")
    )
    
    builder = ContextBuilder(
        somabrain=fake,
        metrics=ContextBuilderMetrics(),
        token_counter=lambda t: 0,
        on_degraded=MagicMock()
    )
    
    # With 3 retries per call, 2 calls = 6 failures -> should open breaker
    
    # Call 1: 3 failures
    await builder.build_for_turn({"tenant_id": "t1", "session_id": "s1"}, max_prompt_tokens=100)
    
    # Call 2: 3 failures -> breaker opens
    await builder.build_for_turn({"tenant_id": "t1", "session_id": "s1"}, max_prompt_tokens=100)
    
    # Check breaker state
    assert breaker.current_state == "open"
    
    # Expect degraded callback to have been called
    assert builder.on_degraded.called

    # Subsequent call should fail fast with CircuitBreakerError (caught and returns empty)
    # and NOT call the fake somabrain
    fake.calls = [] # Reset calls
    await builder.build_for_turn({"tenant_id": "t1", "session_id": "s1"}, max_prompt_tokens=100)
    assert len(fake.calls) == 0
