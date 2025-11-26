"""Tests for ContextBuilder behavior rule injection."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from python.somaagent.context_builder import ContextBuilder, SomabrainHealthState, BuiltContext

@pytest.fixture
def mock_somabrain():
    return AsyncMock()

@pytest.fixture
def mock_metrics():
    metrics = MagicMock()
    metrics.time_total.return_value.__enter__.return_value = None
    metrics.time_tokenisation.return_value.__enter__.return_value = None
    metrics.time_prompt.return_value.__enter__.return_value = None
    metrics.time_retrieval.return_value.__enter__.return_value = None
    metrics.time_ranking.return_value.__enter__.return_value = None
    metrics.time_salience.return_value.__enter__.return_value = None
    metrics.time_redaction.return_value.__enter__.return_value = None
    return metrics

@pytest.fixture
def context_builder(mock_somabrain, mock_metrics):
    return ContextBuilder(
        somabrain=mock_somabrain,
        metrics=mock_metrics,
        token_counter=lambda s: len(s.split()),  # Simple whitespace tokenizer
        health_provider=lambda: SomabrainHealthState.NORMAL
    )

@pytest.mark.asyncio
async def test_behavior_rule_injection(context_builder, mock_somabrain):
    # Setup behavior rules (Pass 1)
    mock_somabrain.recall.return_value = {
        "candidates": [
            {"text": "Be concise", "score": 0.9},
            {"text": "Prefer Python", "score": 0.8}
        ]
    }
    
    # Setup context memories (Pass 2)
    mock_somabrain.context_evaluate.return_value = {
        "results": [
            {"text": "User likes Flask", "score": 0.7, "id": "mem-1"}
        ],
        "constitution_checksum": "sha256:123"
    }
    
    turn = {
        "session_id": "sess-1",
        "user_message": "Hello",
        "system_prompt": "You are Agent Zero."
    }
    
    result = await context_builder.build_for_turn(turn, max_prompt_tokens=1000)
    
    # Verify behavior rules are in system messages
    system_msgs = [m for m in result.messages if m["role"] == "system"]
    behavior_msg = next((m for m in system_msgs if m.get("name") == "behavior"), None)
    
    assert behavior_msg is not None
    assert "## Session Behavioral Rules" in behavior_msg["content"]
    assert "- Be concise" in behavior_msg["content"]
    assert "- Prefer Python" in behavior_msg["content"]
    
    # Verify memory block is also present
    memory_msg = next((m for m in system_msgs if m.get("name") == "memory"), None)
    assert memory_msg is not None
    assert "User likes Flask" in memory_msg["content"]
    
    # Verify debug data
    assert result.debug["behavior_rule_count"] == 2
    assert result.debug["constitution_checksum"] == "sha256:123"

@pytest.mark.asyncio
async def test_behavior_rule_retrieval_failure_graceful(context_builder, mock_somabrain):
    # Pass 1 fails
    mock_somabrain.recall.side_effect = Exception("Recall failed")
    
    # Pass 2 succeeds
    mock_somabrain.context_evaluate.return_value = {"results": []}
    
    turn = {"session_id": "sess-2", "user_message": "Hi"}
    result = await context_builder.build_for_turn(turn, max_prompt_tokens=1000)
    
    # Should succeed without behavior rules
    assert result.debug["behavior_rule_count"] == 0
    system_msgs = [m for m in result.messages if m["role"] == "system"]
    assert not any(m.get("name") == "behavior" for m in system_msgs)

@pytest.mark.asyncio
async def test_intelligent_history_trimming(context_builder, mock_somabrain):
    # Setup no memories to focus on history
    mock_somabrain.recall.return_value = {}
    mock_somabrain.context_evaluate.return_value = {}
    
    # Create long history: 2 anchor + 10 filler + 2 recent
    history = [
        {"role": "user", "content": "Anchor 1"},
        {"role": "assistant", "content": "Anchor 2"},
        *[{"role": "user", "content": f"Filler {i}"} for i in range(10)],
        {"role": "user", "content": "Recent 1"},
        {"role": "assistant", "content": "Recent 2"}
    ]
    
    turn = {
        "session_id": "sess-3",
        "history": history,
        "user_message": "New"
    }
    
    # Budget allows Anchor (4 tokens) + Recent (4 tokens) + System (4) + User (1) = 13 tokens
    # Filler is ~20 tokens. Total needed ~33.
    # We set max tokens to force trimming of filler but keep anchor/recent.
    # Assuming "Anchor 1" = 2 tokens, etc.
    
    result = await context_builder.build_for_turn(turn, max_prompt_tokens=20)
    
    messages = result.messages
    contents = [m["content"] for m in messages]
    
    # Check Anchor preservation
    assert "Anchor 1" in contents
    assert "Anchor 2" in contents
    
    # Check Recency preservation
    assert "Recent 1" in contents
    assert "Recent 2" in contents
    
    # Check Filler removal
    assert "Filler 0" not in contents
    assert "Filler 5" not in contents
