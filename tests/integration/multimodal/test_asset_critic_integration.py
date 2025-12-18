"""Integration tests for AssetCritic service.

Verifies REAL connection to Vision/LLM providers.
Requires valid API keys in environment.
"""

import pytest
import os
import pytest_asyncio
from uuid import uuid4

from services.common.asset_critic import AssetCritic, AssetRubric, evaluation_status
from services.common.asset_store import AssetRecord, AssetType, AssetFormat
from services.common.llm_adapter import LLMAdapter

# Skip if no API key present
pytestmark = pytest.mark.skipif(
    not os.getenv("SA01_OPENAI_API_KEY"),
    reason="Missing SA01_OPENAI_API_KEY"
)

@pytest.fixture
def real_critic():
    # This assumes LLMAdapter can auto-configure from env
    # Integration tests should rely on actual service wiring where possible
    adapter = LLMAdapter()
    return AssetCritic(llm_adapter=adapter)

def create_real_dummy_image() -> AssetRecord:
    # A tiny 1x1 transparent PNG
    import base64
    content = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=")
    
    return AssetRecord(
        id=uuid4(),
        tenant_id="integration-test",
        asset_type=AssetType.IMAGE,
        format=AssetFormat.PNG,
        checksum_sha256="dummy",
        mime_type="image/png",
        content_size_bytes=len(content),
        dimensions={"width": 1, "height": 1},
        metadata={},
        created_at=None,
        content=content
    )

@pytest.mark.asyncio
async def test_real_asset_evaluation_flow(real_critic):
    """Test end-to-end evaluation with real OpenAI call."""
    asset = create_real_dummy_image()
    
    # Rubric that requires high quality
    # Our dummy image is 1x1, so heuristic MIGHT fail depending on configuration
    # asset_critic default heuristic checks min_width only if specified in rubric.
    # Let's set a rubric that passes heuristics but asks for semantic check.
    
    rubric = AssetRubric(
        min_width=1, 
        min_height=1,
        min_quality_score=0.1 # Low score to likely pass "valid image" check
    )
    
    # This will trigger LLM call because heuristics pass
    result = await real_critic.evaluate(asset, rubric)
    
    # We expect a result. 
    # GPT-4o might say "It's just a dot" or fail it for quality, 
    # but the point is we get a valid LLM response, not an error.
    
    assert result.status in [evaluation_status.PASSED, evaluation_status.WARNING, evaluation_status.FAILED]
    assert result.score >= 0.0
    # It should have attempted vision check
    # Check logs or ensure no "Vision check error" in feedback
    error_feedback = [f for f in result.feedback if "Vision check error" in f]
    assert not error_feedback, f"Expected clean run, got errors: {error_feedback}"
