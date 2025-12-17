"""Unit tests for AssetCritic Vision LLM Integration.

Verifies that:
1. AssetCritic constructs correct multimodal payloads (base64).
2. Uses LLMAdapter correctly.
3. Parses JSON responses from the Vision model.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
import json
import base64

from services.common.asset_critic import AssetCritic, AssetRubric, evaluation_status
from services.common.asset_store import AssetRecord, AssetType, AssetFormat
from services.common.llm_adapter import LLMAdapter

def make_asset_with_content(content: bytes) -> AssetRecord:
    return AssetRecord(
        id=uuid4(),
        tenant_id="t",
        asset_type=AssetType.IMAGE,
        format=AssetFormat.PNG,
        checksum_sha256="hash",
        mime_type="image/png",
        content_size_bytes=len(content),
        dimensions={"width": 1024, "height": 1024},
        metadata={},
        created_at=None,
        content=content
    )

@pytest.mark.asyncio
async def test_vision_payload_construction():
    """Verify correct construction of base64 payload for Vision API."""
    adapter = MagicMock(spec=LLMAdapter)
    adapter.chat = AsyncMock(return_value=('{"pass": true, "score": 1.0, "feedback": "Perfect"}', {}))
    
    critic = AssetCritic(llm_adapter=adapter)
    
    # Create asset with specific bytes
    fake_content = b"fake_pixel_data"
    asset = make_asset_with_content(fake_content)
    rubric = AssetRubric(min_quality_score=0.8)
    
    # Execute
    await critic.evaluate(asset, rubric)
    
    # Inspect arguments passed to adapter.chat
    assert adapter.chat.called
    call_args = adapter.chat.call_args
    messages = call_args[0][0] # First arg matches validation
    
    # 2 messages: System + User
    assert len(messages) == 2
    user_msg = messages[1]
    assert user_msg.role == "user"
    
    # Content should be list
    assert isinstance(user_msg.content, list)
    
    # Check for image_url type
    image_block = next((b for b in user_msg.content if b["type"] == "image_url"), None)
    assert image_block is not None
    
    # Validate Base64
    url = image_block["image_url"]["url"]
    assert url.startswith("data:image/png;base64,")
    
    expected_b64 = base64.b64encode(fake_content).decode('utf-8')
    assert expected_b64 in url

@pytest.mark.asyncio
async def test_vision_response_parsing_failure():
    """Verify handling of negative Vision feedback."""
    adapter = MagicMock(spec=LLMAdapter)
    adapter.chat = AsyncMock(return_value=('{"pass": false, "score": 0.3, "feedback": "Too cluttery"}', {}))
    
    critic = AssetCritic(llm_adapter=adapter)
    
    asset = make_asset_with_content(b"bad_image")
    rubric = AssetRubric(min_quality_score=0.8)
    
    result = await critic.evaluate(asset, rubric)
    
    assert result.status == evaluation_status.FAILED
    assert result.score == 0.3
    assert "LLM quality check failed (score 0.30)" in result.failed_criteria
    assert "Aesthetice/Semantic issue: Too cluttery" in result.feedback

@pytest.mark.asyncio
async def test_vision_exception_handling():
    """Verify gracefull fallback if Vision check explodes."""
    adapter = MagicMock(spec=LLMAdapter)
    adapter.chat = AsyncMock(side_effect=Exception("API Error"))
    
    critic = AssetCritic(llm_adapter=adapter)
    
    asset = make_asset_with_content(b"retry_image")
    rubric = AssetRubric(min_quality_score=0.8)
    
    # Should default to 0.5 score/PASS (Fail-Open logic in current impl)
    # See AssetCritic code: return 0.5, "Vision check error (defaulted pass)", True
    result = await critic.evaluate(asset, rubric)
    
    # 0.5 is < 0.8, so it will likely be WARNING status
    assert result.status == evaluation_status.WARNING
    assert "Vision check error" in str(result.feedback)
