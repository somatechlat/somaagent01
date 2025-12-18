
import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from uuid import uuid4

from services.tool_executor.multimodal_executor import MultimodalExecutor
from services.common.job_planner import JobPlan, TaskStep, JobStatus, StepType
from services.common.policy_graph_router import PolicyGraphRouter, RoutingDecision, FallbackReason
from services.multimodal.base_provider import MultimodalProvider, GenerationResult, GenerationRequest, ProviderCapability
from services.common.execution_tracker import ExecutionTracker
from services.common.asset_store import AssetStore

# Mock Providers
class MockFailureProvider(MultimodalProvider):
    @property
    def name(self) -> str:
        return "mock_fail"

    @property
    def provider_id(self) -> str:
        return "fail_corp"

    @property
    def capabilities(self) -> list[ProviderCapability]:
        return [ProviderCapability.IMAGE]

    def __init__(self):
        self.attempts = 0

    async def generate(self, request: GenerationRequest) -> GenerationResult:
        self.attempts += 1
        return GenerationResult(
            success=False,
            error_code="SERVICE_UNAVAILABLE",
            error_message="Mock service is down"
        )

    def validate(self, request: GenerationRequest) -> list[str]:
        return []

    def estimate_cost(self, request: GenerationRequest) -> int:
        return 10


class MockSuccessProvider(MultimodalProvider):
    @property
    def name(self) -> str:
        return "mock_success"

    @property
    def provider_id(self) -> str:
        return "success_corp"

    @property
    def capabilities(self) -> list[ProviderCapability]:
        return [ProviderCapability.IMAGE]

    def __init__(self):
        self.attempts = 0

    async def generate(self, request: GenerationRequest) -> GenerationResult:
        self.attempts += 1
        return GenerationResult(
            success=True,
            content=b"mock_image_data",
            format="png",
            latency_ms=100,
            cost_cents=5
        )

    def validate(self, request: GenerationRequest) -> list[str]:
        return []

    def estimate_cost(self, request: GenerationRequest) -> int:
        return 10

@pytest.mark.asyncio
async def test_executor_fallback_chain_integration():
    """
    Test that MultimodalExecutor correctly falls back to secondary provider
    when primary provider fails.
    
    Scenario:
    1. Plan with 1 IMAGE_GENERATION step.
    2. Primary provider (FailCorp) always fails.
    3. Secondary provider (SuccessCorp) succeeds.
    4. Router is mocked to return FailCorp then SuccessCorp.
    5. Verify execution succeeds and both providers were attempted.
    """
    # Setup Mocks
    mock_store = AsyncMock(spec=AssetStore)
    mock_store.create.return_value = MagicMock(id=uuid4())
    mock_store.get.return_value = None # No cache
    
    mock_tracker = AsyncMock(spec=ExecutionTracker)
    mock_tracker.start.return_value = MagicMock(id=uuid4())
    mock_tracker.get_latest_for_step.return_value = None
    
    mock_planner = AsyncMock()
    mock_planner.update_status = AsyncMock()
    
    # Setup Router to simulate fallback ladder
    mock_router = AsyncMock(spec=PolicyGraphRouter)
    
    # Logic for router.route():
    # If excluded_options is empty -> return FailCorp
    # If excluded_options has FailCorp -> return SuccessCorp
    async def route_side_effect(**kwargs):
        excluded = kwargs.get("excluded_options", [])
        print(f"DEBUG: route called with excluded={excluded}")
        
        # Check if FailCorp is excluded
        fail_excluded = any(p == "fail_corp" for _, p in excluded)
        
        if not fail_excluded:
            print("DEBUG: Returning FailCorp")
            return RoutingDecision(
                success=True,
                tool_id="mock_fail",
                provider="fail_corp",
                fallback_reason=FallbackReason.NONE
            )
        else:
             print("DEBUG: Returning SuccessCorp")
             return RoutingDecision(
                success=True,
                tool_id="mock_success",
                provider="success_corp",
                fallback_reason=FallbackReason.NOT_AVAILABLE
            )
            
    mock_router.route.side_effect = route_side_effect

    # Initialize Executor
    executor = MultimodalExecutor(
        asset_store=mock_store,
        job_planner=mock_planner,
        execution_tracker=mock_tracker,
        policy_router=mock_router,
        # Mock other deps as None/Mock
        asset_critic=AsyncMock(), 
        soma_brain_client=AsyncMock()
    )
    
    # Register Mock Providers
    fail_provider = MockFailureProvider()
    success_provider = MockSuccessProvider()
    
    await executor.register_provider(fail_provider)
    await executor.register_provider(success_provider)
    
    # Create Plan
    plan = JobPlan(
        id=uuid4(),
        tenant_id="test_tenant",
        session_id="test_session",
        tasks=[
            TaskStep(
                task_id="step1",
                step_type=StepType.GENERATE_IMAGE,
                modality="image",
                params={"prompt": "cat"},
                quality_gate={"enabled": False} # Disable critic for this test
            )
        ],
        status=JobStatus.PENDING
    )
    mock_planner.get.return_value = plan
    
    # Execute
    result = await executor.execute_plan(plan.id)
    
    # Assertions
    assert result is True, "Plan execution should succeed via fallback"
    assert fail_provider.attempts >= 1, "Primary provider should have been attempted"
    assert success_provider.attempts == 1, "Secondary provider should have been attempted exactly once"
    
    # Verify planner updates
    # Should have updated to RUNNING then COMPLETED
    assert mock_planner.update_status.call_count >= 2
    args, _ = mock_planner.update_status.call_args
    assert args[1] == JobStatus.COMPLETED

if __name__ == "__main__":
    asyncio.run(test_executor_fallback_chain_integration())
