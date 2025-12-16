"""Unit tests for MultimodalExecutor.

Tests orchestration logic, provider selection, and error handling
using mocks for database and external services.

Pattern Reference: test_job_planner.py
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, ANY
from uuid import uuid4
from datetime import datetime

from services.tool_executor.multimodal_executor import MultimodalExecutor, ExecutorError
from services.common.asset_store import AssetStore
from services.common.job_planner import JobPlanner, JobPlan, TaskStep, JobStatus, StepType
from services.common.execution_tracker import ExecutionTracker, ExecutionStatus, ExecutionRecord
from services.multimodal.base_provider import (
    MultimodalProvider,
    GenerationRequest,
    GenerationResult,
    ProviderCapability,
)


@pytest.fixture
def mock_asset_store():
    store = MagicMock(spec=AssetStore)
    store.create = AsyncMock(return_value=MagicMock(id=uuid4()))
    store.get = AsyncMock(return_value=MagicMock(content=b"test"))
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
def mock_provider():
    provider = MagicMock(spec=MultimodalProvider)
    provider.name = "test_provider"
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


class TestMultimodalExecutor:
    
    @pytest.mark.asyncio
    async def test_initialize(self, mock_job_planner):
        executor = MultimodalExecutor(dsn="postgresql://test", job_planner=mock_job_planner)
        
        # Mock register_provider to avoid actually calling providers
        executor.register_provider = AsyncMock()
        
        with patch("services.tool_executor.multimodal_executor.DalleProvider") as MockDalle:
            instance = MockDalle.return_value
            instance.health_check = AsyncMock(return_value=True)
            
            await executor.initialize()
            
            assert executor.register_provider.call_count >= 2  # Mermaid, Playwright, Dalle

    @pytest.mark.asyncio
    async def test_execute_plan_success(
        self,
        mock_asset_store,
        mock_job_planner,
        mock_execution_tracker,
        mock_provider,
    ):
        executor = MultimodalExecutor(
            dsn="postgresql://test",
            asset_store=mock_asset_store,
            job_planner=mock_job_planner,
            execution_tracker=mock_execution_tracker,
        )
        
        # Register a mock provider for image generation
        mock_provider.name = "dalle3_image_gen"  # Match default logic
        await executor.register_provider(mock_provider)
        
        # Create a plan
        plan_id = uuid4()
        plan = JobPlan(
            id=plan_id,
            tenant_id="test",
            session_id="s1",
            tasks=[
                TaskStep("t1", StepType.GENERATE_IMAGE, "image_photo", params={"prompt": "test"})
            ],
            status=JobStatus.PENDING,
        )
        mock_job_planner.get = AsyncMock(return_value=plan)
        
        # Execute
        success = await executor.execute_plan(plan_id)
        
        # Verify
        assert success is True
        mock_job_planner.update_status.assert_called_with(
            plan_id, JobStatus.COMPLETED, error_message=None
        )
        mock_provider.generate.assert_called_once()
        mock_asset_store.create.assert_called_once()
        mock_execution_tracker.complete.assert_called_with(
            ANY, ExecutionStatus.SUCCESS, 
            asset_id=ANY, latency_ms=100, cost_estimate_cents=10
        )

    @pytest.mark.asyncio
    async def test_execute_plan_step_failure(
        self,
        mock_asset_store,
        mock_job_planner,
        mock_execution_tracker,
        mock_provider,
    ):
        executor = MultimodalExecutor(
            dsn="postgresql://test",
            asset_store=mock_asset_store,
            job_planner=mock_job_planner,
            execution_tracker=mock_execution_tracker,
        )
        
        # Provider fails
        mock_provider.name = "dalle3_image_gen"
        mock_provider.generate = AsyncMock(return_value=GenerationResult(
            success=False,
            error_code="TIMEOUT",
            error_message="Timed out"
        ))
        await executor.register_provider(mock_provider)
        
        plan = JobPlan(
            id=uuid4(),
            tenant_id="test",
            session_id="s1",
            tasks=[TaskStep("t1", StepType.GENERATE_IMAGE, "image_photo")],
        )
        mock_job_planner.get = AsyncMock(return_value=plan)
        
        success = await executor.execute_plan(plan.id)
        
        assert success is False
        # Call count might vary depending on progress updates, check final call
        args, kwargs = mock_job_planner.update_status.call_args
        assert args[1] == JobStatus.FAILED
        assert "Step t1 failed" in kwargs["error_message"]

    @pytest.mark.asyncio
    async def test_execute_plan_no_provider(
        self,
        mock_asset_store,
        mock_job_planner,
        mock_execution_tracker,
    ):
        executor = MultimodalExecutor(
            dsn="postgresql://test",
            asset_store=mock_asset_store,
            job_planner=mock_job_planner,
            execution_tracker=mock_execution_tracker,
        )
        
        # No providers registered
        plan = JobPlan(
            id=uuid4(),
            tenant_id="test",
            session_id="s1",
            tasks=[TaskStep("t1", StepType.GENERATE_IMAGE, "image_photo")],
        )
        mock_job_planner.get = AsyncMock(return_value=plan)
        
        success = await executor.execute_plan(plan.id)
        
        assert success is False
        mock_execution_tracker.start.assert_called_with(
            plan.id, 0, "test", "unknown", "unknown"
        )

    @pytest.mark.asyncio
    async def test_skip_completed_steps(
        self,
        mock_asset_store,
        mock_job_planner,
        mock_execution_tracker,
        mock_provider,
    ):
        executor = MultimodalExecutor(
            dsn="postgresql://test",
            asset_store=mock_asset_store,
            job_planner=mock_job_planner,
            execution_tracker=mock_execution_tracker,
        )
        
        # Register provider
        mock_provider.name = "dalle3_image_gen"
        await executor.register_provider(mock_provider)
        
        plan = JobPlan(
            id=uuid4(),
            tenant_id="test",
            session_id="s1",
            tasks=[
                TaskStep("t1", StepType.GENERATE_IMAGE, "image_photo"),
                TaskStep("t2", StepType.GENERATE_IMAGE, "image_photo"),
            ],
        )
        mock_job_planner.get = AsyncMock(return_value=plan)
        
        # Mock step 0 as already completed
        mock_execution_tracker.get_latest_for_step.side_effect = [
            ExecutionRecord(
                id=uuid4(), plan_id=plan.id, step_index=0, tenant_id="test",
                tool_id="test", provider="test", status=ExecutionStatus.SUCCESS,
                asset_id=uuid4()
            ),
            None  # Step 1 not completed
        ]
        
        success = await executor.execute_plan(plan.id)
        
        assert success is True
        # Provider should only be called once for t2
        assert mock_provider.generate.call_count == 1
