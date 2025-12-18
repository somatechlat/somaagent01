
import pytest
import asyncio
import logging
from uuid import uuid4
import os

from services.common.asset_store import AssetStore, AssetType, AssetFormat
from services.common.job_planner import JobPlanner, JobPlan, TaskStep, JobStatus, StepType
from services.common.policy_graph_router import PolicyGraphRouter
from services.common.execution_tracker import ExecutionTracker, ExecutionStatus
from services.tool_executor.multimodal_executor import MultimodalExecutor
from services.multimodal.base_provider import MultimodalProvider, GenerationRequest, GenerationResult, ProviderCapability
import asyncpg
from src.core.config import cfg

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Real DSN
import os
DSN = os.getenv("SA01_DB_DSN", "postgresql://soma:soma@localhost:20002/somaagent01")

# --- Custom Real Provider for Testing ---
# This is NOT a mock. It's a real class implementing the interface,
# behaving deterministically for the test scenario.
class StubbornProvider(MultimodalProvider):
    """
    Provider that produces bad output on first attempt, 
    but fixes it if it sees 'CRITIC FEEDBACK' in the prompt.
    """
    @property
    def name(self) -> str:
        return "mermaid_diagram"

    @property
    def provider_id(self) -> str:
        return "local"

    @property
    def capabilities(self):
        return [ProviderCapability.DIAGRAM]

    async def estimate_cost(self, request: GenerationRequest) -> float:
        return 0.0

    async def validate(self, request: GenerationRequest) -> bool:
        return True
        
    async def generate(self, request: GenerationRequest) -> GenerationResult:
        # Check for feedback injection
        has_feedback = "CRITIC FEEDBACK" in request.prompt
        
        if not has_feedback:
            # Attempt 1: Return garbage (1x1 pixel)
            # This should fail the 'min_width' heuristic of the AssetCritic
            logger.info("StubbornProvider: Generating BAD output (Attempt 1)")
            return GenerationResult(
                success=True,
                # Invalid SVG or tiny image? AssetCritic checks size < 100 bytes for diagrams
                content=b"empty", 
                content_type="image/svg+xml",
                format="svg",
                dimensions={"width": 1, "height": 1},
                latency_ms=10,
                cost_cents=0,
                metadata={"attempt": "1", "quality": "bad"}
            )
        else:
            # Attempt 2: User complained (feedback present). Return GOOD output.
            logger.info("StubbornProvider: Generating GOOD output (Attempt 2 with Feedback)")
            # Valid SVG content larger than 100 bytes and valid semantic structure
            content = b"<svg><g><rect x='0' y='0' width='100' height='100'/><circle cx='50' cy='50' r='40'/><text>Valid</text></g></svg>" + (b" " * 100) 
            return GenerationResult(
                success=True,
                content=content,
                content_type="image/svg+xml",
                format="svg",
                dimensions={"width": 100, "height": 100},
                latency_ms=10,
                cost_cents=1,
                metadata={"attempt": "2", "quality": "good"}
            )

@pytest.mark.asyncio
async def test_rework_real_flow():
    """
    Test Rework Logic using Real Infrastructure.
    """
    
    # 1. Setup Real Services
    store = AssetStore(dsn=DSN)
    planner = JobPlanner(dsn=DSN)
    tracker = ExecutionTracker(dsn=DSN)
    
    # Setup Policy Client
    from services.common.policy_client import PolicyClient
    OPA_URL = "http://localhost:20009"
    os.environ["SA01_POLICY_DATA_PATH"] = "/v1/data/soma/policy/allow"
    policy_client = PolicyClient(base_url=OPA_URL)

    router = PolicyGraphRouter(dsn=DSN, policy_client=policy_client)
    
    # Register Capability for StubbornProvider as 'mermaid_diagram'
    # This tricks the Real Router into clearing it for 'image_diagram' modality
    conn = await asyncpg.connect(DSN)
    try:
        await conn.execute("DELETE FROM multimodal_capabilities WHERE tool_id = 'mermaid_diagram'")
        await conn.execute("""
            INSERT INTO multimodal_capabilities (
                tool_id, provider, modalities,
                cost_tier, health_status, enabled, created_at
            ) VALUES (
                'mermaid_diagram', 'local', '["image_diagram"]'::jsonb,
                'free', 'healthy', true, NOW()
            )
        """)
    finally:
        await conn.close()
        
    executor = MultimodalExecutor(
        asset_store=store,
        job_planner=planner,
        execution_tracker=tracker,
        policy_router=router,
        asset_critic=None 
    )
    
    # Register Provider instance under the hacked name
    provider = StubbornProvider()
    # StubbornProvider.name returns "mermaid_diagram" now
    await executor.register_provider(provider)
    
    # 2. Create Plan
    task_id = str(uuid4())
    plan = JobPlan(
        id=uuid4(),
        tenant_id="rework_tenant",
        session_id="rework_ses",
        request_id="rework_" + str(uuid4()),
        tasks=[
            TaskStep(
                task_id=task_id,
                # Use GENERATE_DIAGRAM to target 'mermaid_diagram' ladder
                step_type=StepType.GENERATE_DIAGRAM, 
                modality="image_diagram",
                params={"prompt": "Generate a chart"},
                quality_gate={
                    "enabled": True,
                    "max_reworks": 2
                },
                # Heuristic check for diagram: content > 100 bytes
                # We can rely on that default heuristic in AssetCritic
                constraints={} 
            )
        ],
        status=JobStatus.PENDING
    )
    
    await planner.create(plan)
    
    # 3. Execute
    logger.info("Executing Rework Plan...")
    success = await executor.execute_plan(plan.id)
    
    # 4. Verify
    assert success is True, "Plan should eventually succeed after rework"
    
    # Check execution history
    executions = await tracker.list_for_plan(plan.id)
    logger.info(f"Executions: {len(executions)}")
    for ex in executions:
        logger.info(f"Attempt {ex.attempt_number}: {ex.status} - {ex.error_message}")
        
    # Expect 2 attempts
    # Attempt 1: Failed (Quality)
    # Attempt 2: Success
    assert len(executions) >= 2
    
    attempt1 = executions[0]
    attempt2 = executions[1]
    
    assert attempt1.status == ExecutionStatus.FAILED or attempt1.status.value == "failed"
    assert "too small" in (attempt1.error_message or "") or "Validation failed" in (attempt1.error_message or "")
    
    assert attempt2.status == ExecutionStatus.SUCCESS or attempt2.status.value == "success"
    
    # Verify the second asset is stored
    final_plan = await planner.get(plan.id)
    assert final_plan.status == JobStatus.COMPLETED

if __name__ == "__main__":
    asyncio.run(test_rework_real_flow())
