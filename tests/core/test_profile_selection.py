"""Tests for profile selection logic in ConversationWorker."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from services.conversation_worker.main import ConversationWorker
from services.common.profile_repository import PersonaProfile

@pytest.fixture
def mock_worker():
    worker = MagicMock(spec=ConversationWorker)
    worker.profile_store = AsyncMock()
    worker._select_profile = ConversationWorker._select_profile.__get__(worker, ConversationWorker)
    return worker

@pytest.mark.asyncio
async def test_select_profile_keyword_match(mock_worker):
    # Setup profiles
    p1 = MagicMock(spec=PersonaProfile)
    p1.name = "work_mode"
    p1.activation_triggers = {"keywords": ["work", "code"]}
    
    p2 = MagicMock(spec=PersonaProfile)
    p2.name = "teaching_mode"
    p2.activation_triggers = {"keywords": ["teach", "explain"]}
    
    mock_worker.profile_store.list_active_profiles.return_value = [p1, p2]
    
    # Test match
    result = await mock_worker._select_profile("I need to work on code", {})
    assert result == p1
    
    result = await mock_worker._select_profile("Please explain this", {})
    assert result == p2

@pytest.mark.asyncio
async def test_select_profile_tag_match(mock_worker):
    # Setup profiles
    p1 = MagicMock(spec=PersonaProfile)
    p1.name = "emergency_mode"
    p1.activation_triggers = {"tags": ["critical"]}
    
    mock_worker.profile_store.list_active_profiles.return_value = [p1]
    
    # Test match
    result = await mock_worker._select_profile("System is down", {"tags": ["critical"]})
    assert result == p1

@pytest.mark.asyncio
async def test_select_profile_no_match(mock_worker):
    p1 = MagicMock(spec=PersonaProfile)
    p1.name = "work_mode"
    p1.activation_triggers = {"keywords": ["work"]}
    
    mock_worker.profile_store.list_active_profiles.return_value = [p1]
    
    result = await mock_worker._select_profile("Hello there", {})
    assert result is None
