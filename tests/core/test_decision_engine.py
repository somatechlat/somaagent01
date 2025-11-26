"""Tests for Decision Engine (Basal Ganglia) logic in ConversationWorker."""

import pytest
from unittest.mock import MagicMock
from services.conversation_worker.main import ConversationWorker
from services.common.profile_repository import PersonaProfile

@pytest.fixture
def mock_worker():
    worker = MagicMock(spec=ConversationWorker)
    worker._basal_ganglia_filter = ConversationWorker._basal_ganglia_filter.__get__(worker, ConversationWorker)
    worker._apply_tool_gating = ConversationWorker._apply_tool_gating.__get__(worker, ConversationWorker)
    return worker

def test_basal_ganglia_go(mock_worker):
    profile = MagicMock(spec=PersonaProfile)
    profile.cognitive_params = {"urgency": 0.9}
    
    result = mock_worker._basal_ganglia_filter(profile, {})
    assert result == "GO"

def test_basal_ganglia_nogo(mock_worker):
    profile = MagicMock(spec=PersonaProfile)
    profile.cognitive_params = {"urgency": 0.1}
    
    result = mock_worker._basal_ganglia_filter(profile, {})
    assert result == "NOGO"

def test_basal_ganglia_default(mock_worker):
    profile = MagicMock(spec=PersonaProfile)
    profile.cognitive_params = {"urgency": 0.5}
    
    result = mock_worker._basal_ganglia_filter(profile, {})
    assert result == "DEFAULT"

def test_tool_gating(mock_worker):
    profile = MagicMock(spec=PersonaProfile)
    profile.name = "test_profile"
    profile.tool_weights = {"allowed_tool": 1.0, "blocked_tool": 0.0}
    
    tools = [
        {"function": {"name": "allowed_tool"}},
        {"function": {"name": "blocked_tool"}},
        {"function": {"name": "unknown_tool"}} # Default weight 1.0
    ]
    
    result = mock_worker._apply_tool_gating(tools, profile)
    
    assert len(result) == 2
    names = [t["function"]["name"] for t in result]
    assert "allowed_tool" in names
    assert "unknown_tool" in names
    assert "blocked_tool" not in names
