"""Integration test for Portfolio Ranker and Outcome Recording."""

import pytest
import os
import json
import asyncio
from datetime import datetime
from services.common.portfolio_ranker import PortfolioRanker
from services.common.soma_brain_client import SomaBrainClient, MultimodalOutcome

@pytest.mark.asyncio
async def test_portfolio_ranker_logic():
    """Test that ranker sorts candidates based on score."""
    client = SomaBrainClient(output_dir="/tmp")
    ranker = PortfolioRanker(client)
    
    # Mock aggregation method to avoid needing a complex history file setup for unit logic
    # We patch the instance method directly for this test
    original_aggregate = ranker._aggregate_stats
    
    def mock_aggregate(history, provider):
        if provider == "fast_provider":
            return {"success_rate": 0.99, "avg_quality": 0.9, "avg_latency": 100.0, "avg_cost": 1.0}
        elif provider == "slow_provider":
            return {"success_rate": 0.99, "avg_quality": 0.9, "avg_latency": 5000.0, "avg_cost": 1.0}
        return {"success_rate": 0.5, "avg_quality": 0.5, "avg_latency": 1000.0, "avg_cost": 5.0}
        
    ranker._aggregate_stats = mock_aggregate
    
    candidates = [
        ("slow_provider", "modelA"),
        ("fast_provider", "modelB"),
        ("bad_provider", "modelC")
    ]
    
    ranked = ranker.rank(candidates, "generate_image")
    
    # Fast provider should be first due to latency weighting
    assert ranked[0] == ("fast_provider", "modelB")
    assert ranked[1] == ("slow_provider", "modelA")
    assert ranked[2] == ("bad_provider", "modelC")

@pytest.mark.asyncio
async def test_outcome_recording_real_file():
    """Test that outcomes are actually written to the file (Real Implementation)."""
    # Use a temp dir for this test run
    test_dir = "./tests/temp_data"
    os.makedirs(test_dir, exist_ok=True)
    
    client = SomaBrainClient(output_dir=test_dir)
    
    # Create an outcome
    outcome = MultimodalOutcome(
        plan_id="plan-123",
        task_id="task-456",
        step_type="generate_image",
        provider="test_provider",
        model="v1",
        success=True,
        latency_ms=150.0,
        cost_cents=0.5,
        quality_score=0.95,
        feedback="Good job"
    )
    
    # Record it
    await client.record_outcome(outcome)
    
    # Verify file content
    expected_file = os.path.join(test_dir, "soma_brain_outcomes.jsonl")
    assert os.path.exists(expected_file)
    
    with open(expected_file, "r") as f:
        lines = f.readlines()
        last_line = lines[-1]
        data = json.loads(last_line)
        
    assert data["plan_id"] == "plan-123"
    assert data["provider"] == "test_provider"
    assert data["success"] is True
    
    # Verify fetch works
    history = client.fetch_outcomes(limit=10)
    assert len(history) >= 1
    assert history[0].plan_id == "plan-123"

