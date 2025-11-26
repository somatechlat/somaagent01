"""Tests for ProfileStore."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from uuid import uuid4

from services.common.profile_repository import ProfileStore, PersonaProfile

@pytest.fixture
def mock_pool():
    pool = AsyncMock()
    conn = AsyncMock()
    pool.acquire.return_value.__aenter__.return_value = conn
    return pool, conn

@pytest.mark.asyncio
async def test_ensure_schema(mock_pool):
    pool, conn = mock_pool
    store = ProfileStore(dsn="postgres://localhost:5432/test")
    store._pool = pool
    
    # Mock empty table to trigger seeding
    conn.fetchval.return_value = 0
    
    await store.ensure_schema()
    
    # Check migration execution
    conn.execute.assert_any_call(pytest.any_str())
    
    # Check seeding (3 default profiles)
    assert conn.execute.call_count >= 4  # Migration + 3 inserts

@pytest.mark.asyncio
async def test_get_profile_by_name(mock_pool):
    pool, conn = mock_pool
    store = ProfileStore(dsn="postgres://localhost:5432/test")
    store._pool = pool
    
    mock_row = {
        "id": uuid4(),
        "name": "work_mode",
        "description": "Work mode",
        "activation_triggers": '{"keywords": ["work"]}',
        "cognitive_params": '{"urgency": 0.8}',
        "tool_weights": '{"code": 1.5}',
        "system_prompt_modifier": "Be professional.",
        "is_active": True,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }
    conn.fetchrow.return_value = mock_row
    
    profile = await store.get_profile_by_name("work_mode")
    
    assert profile is not None
    assert profile.name == "work_mode"
    assert profile.activation_triggers == {"keywords": ["work"]}
    assert profile.cognitive_params == {"urgency": 0.8}

@pytest.mark.asyncio
async def test_list_active_profiles(mock_pool):
    pool, conn = mock_pool
    store = ProfileStore(dsn="postgres://localhost:5432/test")
    store._pool = pool
    
    mock_rows = [
        {
            "id": uuid4(),
            "name": "p1",
            "description": "d1",
            "activation_triggers": "{}",
            "cognitive_params": "{}",
            "tool_weights": "{}",
            "system_prompt_modifier": "m1",
            "is_active": True,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        },
        {
            "id": uuid4(),
            "name": "p2",
            "description": "d2",
            "activation_triggers": "{}",
            "cognitive_params": "{}",
            "tool_weights": "{}",
            "system_prompt_modifier": "m2",
            "is_active": True,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }
    ]
    conn.fetch.return_value = mock_rows
    
    profiles = await store.list_active_profiles()
    
    assert len(profiles) == 2
    assert profiles[0].name == "p1"
    assert profiles[1].name == "p2"
