"""Unit tests for SomaBrain Integration in Executor.

Verifies that execution outcomes are correctly recorded via SomaBrainClient.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from services.tool_executor.multimodal_executor import MultimodalExecutor
from services.common.soma_brain_client import SomaBrainClient, MultimodalOutcome
from services.common.job_planner import JobPlan, TaskStep, StepType
from services.multimodal.base_provider import GenerationResult

@pytest.fixture
def executor_with_brain(base_mocks):
    # base_mocks comes from conftest or we redefine here if needed.
    # Since we are creating a new test file, let's redefine minimal mocks.
    pass

# We'll use the existing test_multimodal_executor_rework.py pattern
# but strictly focus on the interaction with SomaBrainClient

@pytest.mark.asyncio
async def test_execution_records_outcome():
    # Setup Mocks
    planner = MagicMock()
    tracker = MagicMock()
    store = MagicMock()
    critic = MagicMock()
    brain = MagicMock(spec=SomaBrainClient)
    brain.record_outcome = AsyncMock()
    
    executor = MultimodalExecutor(
        dsn="pg://",
        job_planner=planner,
        execution_tracker=tracker,
        asset_store=store,
        asset_critic=critic,
        soma_brain_client=brain
    )
    
    # Configure Execution
    plan = JobPlan(
        id=uuid4(), tenant_id="t", session_id="s",
        tasks=[TaskStep("t1", StepType.GENERATE_IMAGE, "img")]
    )
    planner.get = AsyncMock(return_value=plan)
    planner.update_status = AsyncMock()
    
    store.create = AsyncMock(return_value=MagicMock(id=uuid4()))
    tracker.start = AsyncMock()
    tracker.complete = AsyncMock()
    tracker.get_latest_for_step = AsyncMock(return_value=None)
    
    # Provider
    provider = MagicMock()
    provider.name = "dalle3"
    provider.generate = AsyncMock(return_value=GenerationResult(
        success=True, content=b"x", format="png", latency_ms=100, cost_cents=5
    ))
    provider.capabilities = []
    
    await executor.register_provider(provider)
    executor._select_provider = MagicMock(return_value=provider) # Skip logic
    
    # Execute
    await executor.execute_plan(plan.id)
    
    # Verify
    assert brain.record_outcome.called
    call_args = brain.record_outcome.call_args[0][0]
    assert isinstance(call_args, MultimodalOutcome)
    assert call_args.success is True
    assert call_args.provider == "dalle3"
    assert call_args.latency_ms == 100
    assert call_args.cost_cents == 5
