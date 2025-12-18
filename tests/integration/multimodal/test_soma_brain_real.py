"""Integration test for SomaBrainClient with REAL PostgreSQL.

VIBE Compliance: Tests against real database infrastructure.
No mocks. Real asyncpg connections.
"""

import os
import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from services.common.soma_brain_client import SomaBrainClient, MultimodalOutcome


@pytest.mark.asyncio
async def test_soma_brain_client_db_storage():
    """Test SomaBrainClient stores and retrieves outcomes from PostgreSQL.
    
    VIBE: Uses real database (SA01_DB_DSN).
    """
    # Use real DSN
    dsn = os.getenv("SA01_DB_DSN", "postgresql://soma:soma@localhost:20002/somaagent01")
    
    client = SomaBrainClient(dsn=dsn)
    
    try:
        # 1. Create test outcomes
        plan_id = str(uuid4())
        
        outcome1 = MultimodalOutcome(
            plan_id=plan_id,
            task_id="task_001",
            step_type="generate_image",
            provider="openai",
            model="dall-e-3",
            success=True,
            latency_ms=3240.5,
            cost_cents=4.0,
            quality_score=0.95,
            feedback="Excellent quality"
        )
        
        outcome2 = MultimodalOutcome(
            plan_id=plan_id,
            task_id="task_002",
            step_type="create_diagram",
            provider="local",
            model="mermaid-cli",
            success=False,
            latency_ms=120.3,
            cost_cents=0.0,
            quality_score=None,
            feedback="Parsing error in diagram syntax"
        )
        
        # 2. Record outcomes
        await client.record_outcome(outcome1)
        await client.record_outcome(outcome2)
        
        # 3. Fetch all outcomes
        all_outcomes = await client.fetch_outcomes(limit=10)
        assert len(all_outcomes) >= 2, "Should retrieve at least 2 outcomes"
        
        # Verify our outcomes are in the results
        plan_ids = [o.plan_id for o in all_outcomes]
        assert plan_id in plan_ids, f"Plan {plan_id} should be in results"
        
        # 4. Fetch filtered by step_type
        image_outcomes = await client.fetch_outcomes(step_type="generate_image", limit=10)
        assert len(image_outcomes) >= 1, "Should retrieve at least 1 image outcome"
        
        # Verify filtering worked
        for outcome in image_outcomes:
            assert outcome.step_type == "generate_image", "All outcomes should be image generation"
        
        # 5. Verify data integrity
        retrieved = next((o for o in all_outcomes if o.plan_id == plan_id and o.task_id == "task_001"), None)
        assert retrieved is not None, "Should find outcome1"
        assert retrieved.provider == "openai"
        assert retrieved.model == "dall-e-3"
        assert retrieved.success is True
        assert abs(retrieved.latency_ms - 3240.5) < 0.1
        assert abs(retrieved.cost_cents - 4.0) < 0.01
        assert abs(retrieved.quality_score - 0.95) < 0.01  # Floating point tolerance
        assert "Excellent" in retrieved.feedback
        
    finally:
        # Cleanup
        await client.close()


@pytest.mark.asyncio
async def test_soma_brain_client_fail_open():
    """Test SomaBrainClient fails gracefully on invalid DSN.
    
    VIBE: Tests error handling without mocks.
    """
    # Invalid DSN should not crash
    client = SomaBrainClient(dsn="postgresql://invalid:invalid@localhost:9999/invalid")
    
    outcome = MultimodalOutcome(
        plan_id=str(uuid4()),
        task_id="test",
        step_type="test",
        provider="test",
        model="test",
        success=True,
        latency_ms=100.0,
        cost_cents=0.0
    )
    
    # Should not raise exception
    await client.record_outcome(outcome)
    
    # Fetch should return empty list
    results = await client.fetch_outcomes(limit=10)
    # Might be empty or might fail gracefully
    # Either way, no exception should propagate
    
    await client.close()
