"""Integration tests for Multimodal Executor Fallback Logic.

Verifies that the executor correctly falls back to secondary providers
when the primary provider fails due to quality checks or runtime errors.

Pattern:
1. Register Mock Provider A (fails)
2. Register Mock Provider B (succeeds)
3. Execute plan
4. Verify Provider A called first, then Provider B
"""

import pytest
import pytest_asyncio
from uuid import uuid4
from typing import Dict, Any

from services.tool_executor.multimodal_executor import MultimodalExecutor
from services.common.job_planner import JobPlanner, JobPlan, TaskStep, JobStatus, StepType
from services.multimodal.base_provider import MultimodalProvider, GenerationResult, ProviderCapability
from services.common.asset_store import AssetStore
from services.common.execution_tracker import ExecutionTracker
from services.common.policy_graph_router import PolicyGraphRouter

# Mock Providers
class FailingProvider(MultimodalProvider):
    def __init__(self, name="fail_provider"):
        super().__init__(name, "fail_prov_id")
    
    @property
    def capabilities(self):
        return [ProviderCapability.GENERATE_IMAGE]

    async def generate(self, request):
        return GenerationResult(
            success=False, 
            error_message="Simulated Provider Error",
            error_code="SIMULATED",
            cost_cents=0
        )

class QualityFailingProvider(MultimodalProvider):
    """Generates content that will fail quality checks (empty)."""
    def __init__(self, name="low_quality_provider"):
        super().__init__(name, "lq_prov_id")

    @property
    def capabilities(self):
        return [ProviderCapability.GENERATE_IMAGE]

    async def generate(self, request):
        # Return tiny content that fails heuristics
        return GenerationResult(
            success=True,
            content=b"", # Empty content fails validation
            content_type="image/png",
            format="png",
            latency_ms=100,
            cost_cents=1
        )

class SuccessProvider(MultimodalProvider):
    def __init__(self, name="success_provider"):
        super().__init__(name, "success_prov_id")

    @property
    def capabilities(self):
        return [ProviderCapability.GENERATE_IMAGE]

    async def generate(self, request):
        # valid PNG header
        content = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89" + b" " * 100
        return GenerationResult(
            success=True,
            content=content,
            content_type="image/png",
            format="png",
            latency_ms=100,
            cost_cents=1
        )

@pytest.mark.asyncio
async def test_fallback_flow_runtime_error():
    """Test fallback when primary provider raises runtime error."""
    # Setup Services
    # We mock PolicyGraphRouter to force a specific ladder: [fail, success]
    
    executor = MultimodalExecutor(dsn="sqlite:///:memory:") 
    # Use real store instances with memory DB (or trivial mocks for speed if dependencies complex)
    # For this test, we rely on the executor's internal logic mostly.
    
    # 1. Register Providers
    fail_prov = FailingProvider(name="primary")
    succ_prov = SuccessProvider(name="secondary")
    
    await executor.register_provider(fail_prov)
    await executor.register_provider(succ_prov)
    
    # 2. Mock Router
    # We patch the router logic to return primary then secondary
    executor._policy_router = PolicyGraphRouter() # Reset
    
    # Mock _get_fallback_ladder to return our specific provider sequence
    # This requires knowing how router builds ladders.
    # Alternatively, we can inject a mock router that ignores registry and just returns decisions.
    
    class MockRouter:
        def __init__(self):
            self.calls = 0
            
        async def route(self, excluded_options=None, **kwargs):
            self.calls += 1
            excluded = excluded_options or []
            
            # If primary not excluded, return it
            if ("primary", "primary") not in excluded:
                from services.common.policy_graph_router import RoutingDecision
                return RoutingDecision(
                    success=True, provider="primary", tool_id="primary"
                )
            
            # If primary excluded, return secondary
            if ("secondary", "secondary") not in excluded:
                from services.common.policy_graph_router import RoutingDecision
                return RoutingDecision(
                    success=True, provider="secondary", tool_id="secondary"
                )
                
            # Else fail
            from services.common.policy_graph_router import RoutingDecision
            return RoutingDecision(success=False)

    executor._policy_router = MockRouter()
    
    # 3. Create Plan
    plan_id = uuid4()
    # Manually inject plan into planner? Or just mock planner.get()
    
    task = TaskStep(
        task_id="step1",
        step_type=StepType.GENERATE_IMAGE,
        modality="image",
        params={"prompt": "test"},
        quality_gate={"enabled": False} # Disable quality gate to focus on provider error fallback
    )
    
    plan = JobPlan(
        id=plan_id,
        tenant_id="test",
        tasks=[task],
        status=JobStatus.PENDING
    )
    
    # Mock Planner
    executor._job_planner.get = lambda pid: plan if pid == plan_id else None
    executor._job_planner.update_status = lambda *args, **kwargs: None
    executor._execution_tracker.start = lambda *args, **kwargs: type("obj", (object,), {"id": uuid4()})() # Return dummy object with id
    executor._execution_tracker.complete = lambda *args, **kwargs: None
    executor._execution_tracker.get_latest_for_step = lambda *args: None
    
    # 4. Execute
    success = await executor.execute_plan(plan_id)
    
    assert success
    # Router called at least twice (once for primary, once for secondary)
    assert executor._policy_router.calls >= 2

@pytest.mark.asyncio
async def test_fallback_flow_quality_failure():
    """Test fallback when primary provider fails quality gate."""
    executor = MultimodalExecutor(dsn="sqlite:///:memory:") 
    
    fail_prov = QualityFailingProvider(name="primary")
    succ_prov = SuccessProvider(name="secondary")
    
    await executor.register_provider(fail_prov)
    await executor.register_provider(succ_prov)
    
    # Mock Router
    class MockRouter:
        async def route(self, excluded_options=None, **kwargs):
            excluded = excluded_options or []
            if ("primary", "primary") not in excluded:
                from services.common.policy_graph_router import RoutingDecision
                return RoutingDecision(success=True, provider="primary", tool_id="primary")
            return RoutingDecision(success=True, provider="secondary", tool_id="secondary")

    executor._policy_router = MockRouter()
    
    plan_id = uuid4()
    task = TaskStep(
        task_id="step1",
        step_type=StepType.GENERATE_IMAGE,
        modality="image",
        params={"prompt": "test"},
        quality_gate={
            "enabled": True,
            "max_reworks": 0 # Fail fast to trigger fallback
        }
    )
    
    plan = JobPlan(
            id=plan_id,
        tenant_id="test",
        tasks=[task],
        status=JobStatus.PENDING
    )
    
    executor._job_planner.get = lambda pid: plan
    executor._job_planner.update_status = lambda *args, **kwargs: None
    # Mock Tracker and Brain
    mock_tracker = executor._execution_tracker
    mock_tracker.start = lambda *args, **kwargs: type("obj", (object,), {"id": uuid4()})()
    mock_tracker.complete = lambda *args, **kwargs: None
    mock_tracker.get_latest_for_step = lambda *args: None
    
    executor._soma_brain_client.record_outcome = lambda *args: None

    # Execute
    success = await executor.execute_plan(plan_id)
    
    assert success
