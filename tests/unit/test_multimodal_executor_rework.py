"""Unit tests for MultimodalExecutor Rework Logic.

Tests retry loops, feedback injection, and quality gating failure.

Pattern Reference: test_multimodal_executor.py
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, ANY, call
from uuid import uuid4

from services.tool_executor.multimodal_executor import MultimodalExecutor
from services.common.asset_store import AssetStore, AssetRecord, AssetType
from services.common.asset_critic import AssetCritic, AssetEvaluation, evaluation_status, AssetRubric
from services.common.job_planner import JobPlanner, JobPlan, TaskStep, JobStatus, StepType
from services.common.execution_tracker import ExecutionTracker, ExecutionStatus
from services.multimodal.base_provider import MultimodalProvider, GenerationResult, ProviderCapability


@pytest.fixture
def base_mocks():
    return {
        "store": MagicMock(spec=AssetStore),
        "planner": MagicMock(spec=JobPlanner),
        "tracker": MagicMock(spec=ExecutionTracker),
        "critic": MagicMock(spec=AssetCritic),
        "provider": MagicMock(spec=MultimodalProvider),
    }

@pytest.fixture
def executor(base_mocks):
    ex = MultimodalExecutor(
        dsn="postgresql://test",
        asset_store=base_mocks["store"],
        job_planner=base_mocks["planner"],
        execution_tracker=base_mocks["tracker"],
        asset_critic=base_mocks["critic"],
    )
    
    # Configure common mock behaviors
    base_mocks["store"].create = AsyncMock(return_value=MagicMock(id=uuid4(), asset_type=AssetType.IMAGE))
    base_mocks["store"].get = AsyncMock(return_value=MagicMock(content=b"test"))
    base_mocks["planner"].update_status = AsyncMock()
    base_mocks["tracker"].start = AsyncMock(return_value=MagicMock(id=uuid4()))
    base_mocks["tracker"].complete = AsyncMock()
    base_mocks["tracker"].get_latest_for_step = AsyncMock(return_value=None)
    
    # Provider setup
    base_mocks["provider"].name = "dalle3_image_gen"  # Matches logic
    base_mocks["provider"].provider_id = "test"
    base_mocks["provider"].capabilities = [ProviderCapability.IMAGE]
    
    return ex

@pytest.mark.asyncio
async def test_rework_success_on_second_attempt(executor, base_mocks):
    # Setup
    plan_id = uuid4()
    plan = JobPlan(
        id=plan_id,
        tenant_id="test",
        session_id="s1",
        tasks=[
            TaskStep(
                "t1", 
                StepType.GENERATE_IMAGE, 
                "image_photo", 
                params={"prompt": "draw a cat"},
                quality_gate={"enabled": True, "max_reworks": 1}
            )
        ],
    )
    base_mocks["planner"].get = AsyncMock(return_value=plan)
    
    # Register provider
    await executor.register_provider(base_mocks["provider"])
    
    # Mock Provider responses (always success generation)
    base_mocks["provider"].generate = AsyncMock(return_value=GenerationResult(
        success=True, content=b"img", format="png", latency_ms=100, cost_cents=10
    ))

    # Mock Critic: Fail first, Pass second
    base_mocks["critic"].evaluate.side_effect = [
        AssetEvaluation(uuid4(), evaluation_status.FAILED, 0.5, feedback=["Too blurry"], failed_criteria=["blurry"]),
        AssetEvaluation(uuid4(), evaluation_status.PASSED, 0.95),
    ]

    # Execute
    success = await executor.execute_plan(plan_id)

    # Verify
    assert success is True
    assert base_mocks["provider"].generate.call_count == 2
    assert base_mocks["critic"].evaluate.call_count == 2
    
    # Check feedback injection in 2nd call
    call_args = base_mocks["provider"].generate.call_args_list
    first_prompt = call_args[0][0][0].prompt
    second_prompt = call_args[1][0][0].prompt
    
    assert "draw a cat" in first_prompt
    assert "Too blurry" not in first_prompt
    assert "draw a cat" in second_prompt
    assert "Too blurry" in second_prompt  # Feedback injected

@pytest.mark.asyncio
async def test_rework_failed_max_attempts(executor, base_mocks):
    # Setup
    plan_id = uuid4()
    plan = JobPlan(
        id=plan_id,
        tenant_id="test",
        session_id="s1",
        tasks=[
            TaskStep(
                "t1", 
                StepType.GENERATE_IMAGE, 
                "image_photo", 
                quality_gate={"enabled": True, "max_reworks": 1} # Max 2 attempts total
            )
        ],
    )
    base_mocks["planner"].get = AsyncMock(return_value=plan)
    await executor.register_provider(base_mocks["provider"])
    
    # Always succeed generation
    base_mocks["provider"].generate = AsyncMock(return_value=GenerationResult(
        success=True, content=b"img", format="png", latency_ms=100, cost_cents=10
    ))
    
    # Always fail critique
    base_mocks["critic"].evaluate.return_value = AssetEvaluation(
        uuid4(), evaluation_status.FAILED, 0.2, feedback=["Bad"], failed_criteria=["Bad"]
    )

    # Execute
    success = await executor.execute_plan(plan_id)

    # Verify
    assert success is False
    assert base_mocks["provider"].generate.call_count == 2 # 1 initial + 1 rework
    assert base_mocks["critic"].evaluate.call_count == 2
    
    # Execution tracker should show failure on final attempt
    # Note: Intermediate failures are also tracked, but final one matters most for step result
    assert base_mocks["tracker"].complete.call_count == 2 # 2 completions (both failed)
    
    # Check final status update
    base_mocks["planner"].update_status.assert_called_with(
        plan_id, JobStatus.FAILED, error_message=ANY
    )
    
    # Check error message contains "max attempts"
    args, kwargs = base_mocks["planner"].update_status.call_args
    assert "failed after max attempts" in kwargs["error_message"]

@pytest.mark.asyncio
async def test_provider_error_counts_as_attempt(executor, base_mocks):
    # Test that provider failures (timeouts etc) consume attempts
    plan_id = uuid4()
    plan = JobPlan(
        id=plan_id,
        tenant_id="test",
        session_id="s1",
        tasks=[TaskStep("t1", StepType.GENERATE_IMAGE, "image_photo", quality_gate={"max_reworks": 1})],
    )
    base_mocks["planner"].get = AsyncMock(return_value=plan)
    await executor.register_provider(base_mocks["provider"])
    
    # Provider fails first time, succeeds second
    base_mocks["provider"].generate.side_effect = [
        GenerationResult(success=False, error_message="Timeout"),
        GenerationResult(success=True, content=b"img", format="png", latency_ms=100, cost_cents=10)
    ]
    
    # Critic passes (only called once for successful gen)
    base_mocks["critic"].evaluate.return_value = AssetEvaluation(uuid4(), evaluation_status.PASSED, 1.0)
    
    success = await executor.execute_plan(plan_id)
    
    assert success is True
    assert base_mocks["provider"].generate.call_count == 2
    assert base_mocks["critic"].evaluate.call_count == 1 # Only called on successful generation
