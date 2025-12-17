"""Unit tests for AssetCritic LLM Integration.

Verifies that AssetCritic correctly delegates to LLMAdapter when heuristics pass
and handles LLM responses appropriately.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from services.common.asset_critic import AssetCritic, AssetRubric, evaluation_status
from services.common.asset_store import AssetRecord, AssetType, AssetFormat
from services.common.llm_adapter import LLMAdapter

def make_asset(
    content_size=1024,
    width=1024,
    height=1024,
    asset_type=AssetType.IMAGE
) -> AssetRecord:
    return AssetRecord(
        id=uuid4(),
        tenant_id="t",
        asset_type=asset_type,
        format=AssetFormat.PNG,
        storage_path="path",
        checksum_sha256="hash",
        mime_type="image/png",
        content_size_bytes=content_size,
        dimensions={"width": width, "height": height},
        metadata={},
        created_at=None,
        content=b"fake_image_bytes" # Added content for vision check
    )

@pytest.mark.asyncio
async def test_evaluate_llm_skipped_if_heuristics_fail():
    """Ensure LLM is NOT called if basic heuristics fail."""
    adapter = MagicMock(spec=LLMAdapter)
    adapter.chat = AsyncMock()
    
    critic = AssetCritic(llm_adapter=adapter)
    
    # Asset definition that fails heuristics (too small)
    asset = make_asset(width=100, height=100)
    rubric = AssetRubric(min_width=512, min_quality_score=0.8)
    
    result = await critic.evaluate(asset, rubric)
    
    assert result.status == evaluation_status.FAILED
    assert "Width 100 < 512" in result.failed_criteria[0]
    
    # Verify Adapter was NOT called
    adapter.chat.assert_not_called()

@pytest.mark.asyncio
async def test_evaluate_llm_called_if_heuristics_pass():
    """Ensure LLM IS called if heuristics pass and adapter exists."""
    adapter = MagicMock(spec=LLMAdapter)
    # Mock return value for chat
    # Return valid JSON string + usage dict
    adapter.chat = AsyncMock(return_value=('{"pass": true, "score": 0.95, "feedback": "Good job"}', {}))
    
    critic = AssetCritic(llm_adapter=adapter)
    
    # Asset passes heuristics
    asset = make_asset(width=1024, height=1024)
    rubric = AssetRubric(min_width=512, min_quality_score=0.8)
    
    result = await critic.evaluate(asset, rubric)
    
    assert result.status == evaluation_status.PASSED
    assert result.score >= 0.95
    assert adapter.chat.called

@pytest.mark.asyncio
async def test_evaluate_no_llm_adapter():
    """Ensure graceful fallback if no LLM adapter provided."""
    critic = AssetCritic(llm_adapter=None)
    
    asset = make_asset()
    rubric = AssetRubric(min_width=512, min_quality_score=0.8)
    
    result = await critic.evaluate(asset, rubric)
    
    assert result.status == evaluation_status.PASSED
    # Score should remain 1.0 from heuristics since LLM step skipped
    assert result.score == 1.0
