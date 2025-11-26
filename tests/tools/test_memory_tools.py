"""Tests for memory management tools."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from services.tool_executor.memory_tools import MemorySaveTool, UpdateBehaviorTool
from services.tool_executor.tools import ToolExecutionError
from python.integrations.somabrain_client import SomaClientError

@pytest.fixture
def mock_soma_client():
    with patch("services.tool_executor.memory_tools.SomaBrainClient") as mock:
        client_instance = AsyncMock()
        mock.get.return_value = client_instance
        yield client_instance

@pytest.mark.asyncio
async def test_memory_save_success(mock_soma_client):
    tool = MemorySaveTool()
    mock_soma_client.remember.return_value = {"key": "mem-123"}
    
    result = await tool.run({
        "content": "User likes Python",
        "fact_type": "semantic",
        "tags": ["preference"],
        "importance": 0.8
    })
    
    assert result["status"] == "success"
    assert result["memory_id"] == "mem-123"
    assert result["fact_type"] == "semantic"
    
    mock_soma_client.remember.assert_called_once()
    call_kwargs = mock_soma_client.remember.call_args.kwargs
    assert call_kwargs["payload"]["content"] == "User likes Python"
    assert call_kwargs["payload"]["fact"] == "semantic"
    assert call_kwargs["payload"]["tags"] == ["preference"]
    assert call_kwargs["importance"] == 0.8

@pytest.mark.asyncio
async def test_memory_save_default_type(mock_soma_client):
    tool = MemorySaveTool()
    mock_soma_client.remember.return_value = {"key": "mem-456"}
    
    result = await tool.run({"content": "Just a thought"})
    
    assert result["fact_type"] == "episodic"
    mock_soma_client.remember.assert_called_once()
    assert mock_soma_client.remember.call_args.kwargs["payload"]["fact"] == "episodic"

@pytest.mark.asyncio
async def test_memory_save_invalid_type_fallback(mock_soma_client):
    tool = MemorySaveTool()
    mock_soma_client.remember.return_value = {"key": "mem-789"}
    
    result = await tool.run({
        "content": "Invalid type test",
        "fact_type": "random_type"
    })
    
    assert result["fact_type"] == "episodic"
    payload = mock_soma_client.remember.call_args.kwargs["payload"]
    assert payload["fact"] == "episodic"
    assert "type:random_type" in payload["tags"]

@pytest.mark.asyncio
async def test_memory_save_failure(mock_soma_client):
    tool = MemorySaveTool()
    mock_soma_client.remember.side_effect = SomaClientError("API Error")
    
    with pytest.raises(ToolExecutionError, match="Failed to save memory"):
        await tool.run({"content": "Fail"})

@pytest.mark.asyncio
async def test_update_behavior_add(mock_soma_client):
    tool = UpdateBehaviorTool()
    mock_soma_client.remember.return_value = {"key": "rule-1"}
    
    result = await tool.run({
        "behavior_description": "Be concise",
        "action": "add"
    })
    
    assert result["status"] == "success"
    assert result["action"] == "add"
    
    mock_soma_client.remember.assert_called_once()
    payload = mock_soma_client.remember.call_args.kwargs["payload"]
    assert payload["content"] == "Be concise"
    assert payload["fact"] == "behavior_rule"
    assert "behavior_rule" in payload["tags"]
    assert "action:add" in payload["tags"]

@pytest.mark.asyncio
async def test_update_behavior_delete(mock_soma_client):
    tool = UpdateBehaviorTool()
    mock_soma_client.remember.return_value = {"key": "rule-2"}
    
    result = await tool.run({
        "behavior_description": "Be verbose",
        "action": "delete"
    })
    
    payload = mock_soma_client.remember.call_args.kwargs["payload"]
    assert payload["content"] == "IGNORE PREVIOUS RULE: Be verbose"
    assert "action:delete" in payload["tags"]
