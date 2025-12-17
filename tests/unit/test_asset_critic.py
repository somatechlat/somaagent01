"""Unit tests for Asset Critic service.

Verifies heuristic evaluation logic for images and diagrams.

Pattern Reference: test_asset_store.py
"""

import pytest
from uuid import uuid4
from unittest.mock import MagicMock

from services.common.asset_critic import (
    AssetCritic, 
    AssetRubric, 
    evaluation_status,
)
from services.common.asset_store import AssetRecord, AssetType


@pytest.fixture
def critic():
    return AssetCritic()


def create_asset(
    asset_type=AssetType.IMAGE,
    format="png",
    dimensions=None,
    size=1024,
) -> AssetRecord:
    return AssetRecord(
        id=uuid4(),
        tenant_id="test",
        asset_type=asset_type,
        format=format,
        checksum_sha256="hash",
        mime_type=f"image/{format}",
        content_size_bytes=size,
        dimensions=dimensions or {"width": 1024, "height": 1024},
        metadata={},
    )


class TestAssetCritic:
    
    @pytest.mark.asyncio
    async def test_evaluate_pass(self, critic):
        asset = create_asset(dimensions={"width": 1024, "height": 1024})
        rubric = AssetRubric(min_width=800, min_height=800)
        
        result = await critic.evaluate(asset, rubric)
        
        assert result.passed
        assert result.status == evaluation_status.PASSED
        assert result.score == 1.0
        assert not result.failed_criteria

    @pytest.mark.asyncio
    async def test_evaluate_resolution_fail(self, critic):
        asset = create_asset(dimensions={"width": 500, "height": 500})
        rubric = AssetRubric(min_width=800)
        
        result = await critic.evaluate(asset, rubric)
        
        assert not result.passed
        assert result.status == evaluation_status.FAILED
        assert "Width 500 < 800" in result.failed_criteria[0]

    @pytest.mark.asyncio
    async def test_evaluate_format_fail(self, critic):
        asset = create_asset(format="jpg")
        rubric = AssetRubric(required_formats=["png"])
        
        result = await critic.evaluate(asset, rubric)
        
        assert not result.passed
        assert "Format jpg not in ['png']" in result.failed_criteria[0]

    @pytest.mark.asyncio
    async def test_evaluate_size_fail(self, critic):
        asset = create_asset(size=2000)
        rubric = AssetRubric(max_size_bytes=1000)
        
        result = await critic.evaluate(asset, rubric)
        
        # Size fail deducts score but might not strictly fail unless score drops too low
        # OR if implementation logic treats it as hard fail.
        # Current implementation: max_size_bytes fails if exceeded.
        assert not result.passed
        assert result.status == evaluation_status.FAILED

    @pytest.mark.asyncio
    async def test_evaluate_diagram_empty_fail(self, critic):
        asset = create_asset(
            asset_type=AssetType.DIAGRAM,
            format="svg",
            size=50  # Too small
        )
        rubric = AssetRubric()
        
        result = await critic.evaluate(asset, rubric)
        
        assert not result.passed
        assert "Diagram content too small" in result.failed_criteria[0]

    @pytest.mark.asyncio
    async def test_evaluate_score_warning(self, critic):
        # Setup scenario where strict fail conditions aren't met, but score drops
        # For now, heuristics are mostly pass/fail in current implementation code
        # except score deduction logic which leads to FAIL if failed list populated.
        # Let's verify behavior.
        pass # Placeholder for testing complex scoring if implemented
