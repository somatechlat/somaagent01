"""Unit tests for SomaBrain Client.

Verifies outcome data structure and local file fallback mechanisms.

Pattern Reference: test_asset_critic.py
"""

import json
import os
import pytest
from uuid import uuid4
from datetime import datetime

from services.common.soma_brain_client import SomaBrainClient, MultimodalOutcome


@pytest.fixture
def temp_output_dir(tmp_path):
    return str(tmp_path)


@pytest.fixture
def client(temp_output_dir):
    return SomaBrainClient(output_dir=temp_output_dir)


class TestSomaBrainClient:

    @pytest.mark.asyncio
    async def test_record_outcome_local_fallback(self, client, temp_output_dir):
        # Setup data
        outcome = MultimodalOutcome(
            plan_id=str(uuid4()),
            task_id="task_1",
            step_type="generate_image",
            provider="dalle3",
            model="dalle-3",
            success=True,
            latency_ms=1500.0,
            cost_cents=4.0,
            quality_score=0.95
        )
        
        # Execute
        await client.record_outcome(outcome)
        
        # Verify
        expected_file = os.path.join(temp_output_dir, "soma_brain_outcomes.jsonl")
        assert os.path.exists(expected_file)
        
        with open(expected_file, "r") as f:
            lines = f.readlines()
            assert len(lines) == 1
            data = json.loads(lines[0])
            
            assert data["plan_id"] == outcome.plan_id
            assert data["provider"] == "dalle3"
            assert data["quality_score"] == 0.95
            assert "timestamp" in data

    @pytest.mark.asyncio
    async def test_record_outcome_handles_io_error(self, client):
        # Setup: Force I/O error by passing invalid directory via internal override
        # or by mocking open. Path injection is easiest if we point to a read-only loc?
        # Easier: Mock the _write_to_local method to raise
        
        # We want to ensure record_outcome catches exceptions (FAIL_OPEN)
        outcome = MultimodalOutcome(
             plan_id="1", task_id="t", step_type="s", provider="p", model="m",
             success=True, latency_ms=1, cost_cents=1
        )
        
        # Since _write_to_local is sync, we can patch it on the instance or class
        # Note: mocking on the instance is safer for isolation
        # However, since methods are bound, we need `pytest-mock` or `unittest.mock`
        from unittest.mock import patch
        
        with patch.object(client, "_write_to_local", side_effect=IOError("Disk full")):
            # Should not raise
            await client.record_outcome(outcome)

    @pytest.mark.asyncio
    async def test_outcome_defaults(self):
        outcome = MultimodalOutcome(
             plan_id="p", task_id="t", step_type="s", provider="pr", model="m",
             success=False, latency_ms=0, cost_cents=0
        )
        assert outcome.timestamp is not None
        assert outcome.quality_score is None
