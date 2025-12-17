"""Unit tests for MultimodalExecutor Rework Loop.

Verifies that the executor correctly handles feedback loops when AssetCritic
rejects generated assets, including prompt injection and retry limits.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, ANY
from uuid import uuid4

from services.tool_executor.multimodal_executor import MultimodalExecutor
from services.common.asset_store import AssetStore, AssetRecord, AssetType, AssetFormat
from services.common.job_planner import JobPlanner, JobPlan, TaskStep, JobStatus, StepType
from services.common.execution_tracker import ExecutionTracker, ExecutionStatus, ExecutionRecord
from services.common.asset_critic import AssetCritic, AssetEvaluation, evaluation_status, AssetRubric
from services.common.soma_brain_client import SomaBrainClient
from services.multimodal.base_provider import (
    MultimodalProvider,
    GenerationResult,
    ProviderCapability,
)


@pytest.fixture
def mock_asset_store():
    store = MagicMock(spec=AssetStore)
    store.create = AsyncMock(return_value=AssetRecord(
        id=uuid4(),
        tenant_id="t",
        asset_type=AssetType.IMAGE,
        format=AssetFormat.PNG,
        checksum_sha256="hash",
        mime_type="image/png",
        content_size_bytes=100,
        metadata={},
    ))
    return store

@pytest.fixture
def mock_job_planner():
    planner = MagicMock(spec=JobPlanner)
    planner.update_status = AsyncMock()
    return planner

@pytest.fixture
def mock_execution_tracker():
    tracker = MagicMock(spec=ExecutionTracker)
    tracker.start = AsyncMock(return_value=MagicMock(id=uuid4()))
    tracker.complete = AsyncMock()
    tracker.get_latest_for_step = AsyncMock(return_value=None)
    return tracker

@pytest.fixture
def mock_soma_brain():
    client = MagicMock(spec=SomaBrainClient)
    client.record_outcome = AsyncMock()
    return client

@pytest.fixture
def mock_asset_critic():
    critic = MagicMock(spec=AssetCritic)
    return critic

@pytest.fixture
def mock_provider():
    provider = MagicMock(spec=MultimodalProvider)
    provider.name = "dalle3_image_gen"
    provider.provider_id = "test"
    provider.capabilities = [ProviderCapability.IMAGE]
    provider.generate = AsyncMock(return_value=GenerationResult(
        success=True,
        content=b"image",
        content_type="image/png",
        format="png",
        latency_ms=100,
        cost_cents=10,
    ))
    return provider


class TestExecutorRework:
    
    @pytest.mark.asyncio
    async def test_rework_success_on_second_attempt(
        self,
        mock_asset_store,
        mock_job_planner,
        mock_execution_tracker,
        mock_soma_brain,
        mock_asset_critic,
        mock_provider,
    ):
        """Verify that executor retries with feedback when first attempt fails quality gate."""
        executor = None  # Moved inside patch
        
        # await executor.register_provider(mock_provider) # Moved inside patch
        
        # Setup Plan
        task = TaskStep(
            "t1", 
            StepType.GENERATE_IMAGE, 
            "image_gen", 
            params={"prompt": "draw a cat"},
            quality_gate={"enabled": True, "max_reworks": 1}
        )
        plan = JobPlan(
            id=uuid4(),
            tenant_id="test",
            session_id="s1",
            tasks=[task],
            status=JobStatus.PENDING,
        )
        mock_job_planner.get = AsyncMock(return_value=plan)
        
        # Setup Critic: Fail 1st time, Pass 2nd time
        fail_eval = AssetEvaluation(
            asset_id=uuid4(),
            status=evaluation_status.FAILED,
            score=0.4,
            feedback=["Too blurry"],
            failed_criteria=["sharpness"]
        )
        pass_eval = AssetEvaluation(
            asset_id=uuid4(),
            status=evaluation_status.PASSED,
            score=0.9,
            feedback=[],
            failed_criteria=[]
        )
        mock_asset_critic.evaluate.side_effect = [fail_eval, pass_eval]
        
        # Patch config to allow LLMAdapter init or just ignore it implies we need it for critic?
        # Critic is passed in, so LLMAdapter init in executor might be redundant strictly for this test,
        # but the code runs it.
        with patch("services.tool_executor.multimodal_executor.cfg") as mock_cfg:
            mock_cfg.settings.return_value.llm.openai_api_key = "test-key"
            
            # Re-init executor inside patch context
            executor = MultimodalExecutor(
                dsn="postgresql://test",
                asset_store=mock_asset_store,
                job_planner=mock_job_planner,
                execution_tracker=mock_execution_tracker,
                asset_critic=mock_asset_critic,
                soma_brain_client=mock_soma_brain,
            )
            await executor.register_provider(mock_provider)
            
            # Execute
            success = await executor.execute_plan(plan.id)
        
        assert success is True
        
        # Verify Provider calls
        assert mock_provider.generate.call_count == 2
        
        # Check prompts
        # 1st call should be original prompt
        call1 = mock_provider.generate.call_args_list[0]
        assert call1[0][0].prompt == "draw a cat"
        
        # 2nd call should have feedback
        call2 = mock_provider.generate.call_args_list[1]
        assert "draw a cat" in call2[0][0].prompt
        assert "IMPORTANT: The previous attempt failed quality checks" in call2[0][0].prompt
        assert "Too blurry" in call2[0][0].prompt
        
        # Verify SomaBrain recording (1 fail, 1 success)
        assert mock_soma_brain.record_outcome.call_count == 2
        
        # Verify Execution Tracker
        # Should start twice
        assert mock_execution_tracker.start.call_count == 2
        # Should fail first, succeed second
        assert mock_execution_tracker.complete.call_count == 2
        
        calls = mock_execution_tracker.complete.call_args_list
        # First completion: FAILED
        assert calls[0][0][1] == ExecutionStatus.FAILED
        assert "Quality check failed" in calls[0][1]["error_message"]
        # Second completion: SUCCESS
        assert calls[1][0][1] == ExecutionStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_rework_failure_max_attempts(
        self,
        mock_asset_store,
        mock_job_planner,
        mock_execution_tracker,
        mock_soma_brain,
        mock_asset_critic,
        mock_provider,
    ):
        """Verify that executor fails after max reworks are exhausted."""
        executor = None # Moved inside patch
        # await executor.register_provider(mock_provider) # Moved inside patch
        
        # Setup Plan with 1 rework (total 2 attempts)
        task = TaskStep(
            "t1", 
            StepType.GENERATE_IMAGE, 
            "image_gen", 
            params={"prompt": "draw a cat"},
            quality_gate={"enabled": True, "max_reworks": 1}
        )
        plan = JobPlan(
            id=uuid4(),
            tenant_id="test",
            session_id="s1",
            tasks=[task],
            status=JobStatus.PENDING,
        )
        mock_job_planner.get = AsyncMock(return_value=plan)
        
        # Setup Critic: Always fail
        fail_eval = AssetEvaluation(
            asset_id=uuid4(),
            status=evaluation_status.FAILED,
            score=0.4,
            feedback=["Bad"],
            failed_criteria=["bad"]
        )
        mock_asset_critic.evaluate.return_value = fail_eval
        
        with patch("services.tool_executor.multimodal_executor.cfg") as mock_cfg:
            mock_cfg.settings.return_value.llm.openai_api_key = "test-key"
            
            executor = MultimodalExecutor(
                dsn="postgresql://test",
                asset_store=mock_asset_store,
                job_planner=mock_job_planner,
                execution_tracker=mock_execution_tracker,
                asset_critic=mock_asset_critic,
                soma_brain_client=mock_soma_brain,
            )
            await executor.register_provider(mock_provider)
            
            # Execute
            success = await executor.execute_plan(plan.id)
        
        assert success is False
        
        # Verify calls limited to max_reworks + 1 (initial) = 2
        assert mock_provider.generate.call_count == 2
        assert mock_asset_critic.evaluate.call_count == 2
        assert mock_soma_brain.record_outcome.call_count == 2
        
        # Job Status should be FAILED
        mock_job_planner.update_status.assert_called_with(
            plan.id, JobStatus.FAILED, error_message=ANY
        )
