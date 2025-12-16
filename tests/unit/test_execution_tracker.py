"""Unit tests for ExecutionTracker (no DB required).

Tests verify dataclass creation, enum values, and row conversion
without database connections.

Pattern Reference: test_capability_registry.py
"""

import pytest
from datetime import datetime
from uuid import uuid4

from services.common.execution_tracker import (
    ExecutionTracker,
    ExecutionRecord,
    ExecutionStatus,
)


def make_execution(**kwargs) -> ExecutionRecord:
    """Create a test ExecutionRecord with sensible defaults."""
    defaults = {
        "id": uuid4(),
        "plan_id": uuid4(),
        "step_index": 0,
        "tenant_id": "test-tenant",
        "tool_id": "dalle3_image_gen",
        "provider": "openai",
        "status": ExecutionStatus.PENDING,
        "attempt_number": 1,
    }
    defaults.update(kwargs)
    return ExecutionRecord(**defaults)


class TestExecutionStatus:
    """Tests for ExecutionStatus enum."""

    def test_status_values(self):
        assert ExecutionStatus.PENDING.value == "pending"
        assert ExecutionStatus.RUNNING.value == "running"
        assert ExecutionStatus.SUCCESS.value == "success"
        assert ExecutionStatus.FAILED.value == "failed"
        assert ExecutionStatus.SKIPPED.value == "skipped"

    def test_status_from_string(self):
        assert ExecutionStatus("pending") == ExecutionStatus.PENDING
        assert ExecutionStatus("success") == ExecutionStatus.SUCCESS


class TestExecutionRecord:
    """Tests for ExecutionRecord dataclass."""

    def test_create_minimal(self):
        exec_id = uuid4()
        plan_id = uuid4()
        record = ExecutionRecord(
            id=exec_id,
            plan_id=plan_id,
            step_index=0,
            tenant_id="test",
            tool_id="mermaid",
            provider="local",
        )
        assert record.id == exec_id
        assert record.plan_id == plan_id
        assert record.status == ExecutionStatus.PENDING
        assert record.attempt_number == 1
        assert record.latency_ms is None

    def test_create_full(self):
        record = make_execution(
            status=ExecutionStatus.SUCCESS,
            asset_id=uuid4(),
            latency_ms=1500,
            cost_estimate_cents=50,
            quality_score=0.85,
        )
        assert record.status == ExecutionStatus.SUCCESS
        assert record.latency_ms == 1500
        assert record.cost_estimate_cents == 50
        assert record.quality_score == 0.85

    def test_failed_record(self):
        record = make_execution(
            status=ExecutionStatus.FAILED,
            error_code="TIMEOUT",
            error_message="Request timed out after 30s",
        )
        assert record.status == ExecutionStatus.FAILED
        assert record.error_code == "TIMEOUT"
        assert "timed out" in record.error_message

    def test_fallback_record(self):
        record = make_execution(
            tool_id="stability_image_gen",
            provider="stability",
            fallback_reason="primary_unavailable",
            original_provider="openai",
        )
        assert record.fallback_reason == "primary_unavailable"
        assert record.original_provider == "openai"


class TestRowConversion:
    """Tests for row-to-record conversion."""

    def test_row_to_record_complete(self):
        tracker = ExecutionTracker(dsn="postgresql://test@localhost/test")
        exec_id = uuid4()
        plan_id = uuid4()
        asset_id = uuid4()
        
        mock_row = {
            "id": exec_id,
            "plan_id": plan_id,
            "step_index": 0,
            "tenant_id": "acme-corp",
            "tool_id": "dalle3_image_gen",
            "provider": "openai",
            "status": "success",
            "attempt_number": 1,
            "asset_id": asset_id,
            "latency_ms": 2500,
            "cost_estimate_cents": 40,
            "quality_score": 0.92,
            "quality_feedback": '{"prompt_adherence": 0.95, "visual_quality": 0.90}',
            "error_code": None,
            "error_message": None,
            "fallback_reason": None,
            "original_provider": None,
            "started_at": datetime(2025, 12, 16, 10, 0, 0),
            "completed_at": datetime(2025, 12, 16, 10, 0, 2),
            "created_at": datetime(2025, 12, 16, 10, 0, 0),
        }
        
        record = tracker._row_to_record(mock_row)
        
        assert record.id == exec_id
        assert record.plan_id == plan_id
        assert record.status == ExecutionStatus.SUCCESS
        assert record.asset_id == asset_id
        assert record.latency_ms == 2500
        assert record.quality_feedback["prompt_adherence"] == 0.95

    def test_row_to_record_nulls(self):
        tracker = ExecutionTracker(dsn="postgresql://test@localhost/test")
        exec_id = uuid4()
        plan_id = uuid4()
        
        mock_row = {
            "id": exec_id,
            "plan_id": plan_id,
            "step_index": 0,
            "tenant_id": "test",
            "tool_id": "mermaid",
            "provider": "local",
            "status": "pending",
            "attempt_number": None,
            "asset_id": None,
            "latency_ms": None,
            "cost_estimate_cents": None,
            "quality_score": None,
            "quality_feedback": None,
            "error_code": None,
            "error_message": None,
            "fallback_reason": None,
            "original_provider": None,
            "started_at": None,
            "completed_at": None,
            "created_at": None,
        }
        
        record = tracker._row_to_record(mock_row)
        
        assert record.status == ExecutionStatus.PENDING
        assert record.attempt_number == 1  # Default
        assert record.quality_feedback is None


class TestMetricsCalculation:
    """Tests for metrics logic."""

    def test_latency_aggregation_concept(self):
        """Test that latency values can be aggregated."""
        records = [
            make_execution(latency_ms=1000),
            make_execution(latency_ms=2000),
            make_execution(latency_ms=1500),
        ]
        total_latency = sum(r.latency_ms or 0 for r in records)
        assert total_latency == 4500

    def test_cost_aggregation_concept(self):
        """Test that cost values can be aggregated."""
        records = [
            make_execution(cost_estimate_cents=50),
            make_execution(cost_estimate_cents=30),
        ]
        total_cost = sum(r.cost_estimate_cents or 0 for r in records)
        assert total_cost == 80

    def test_quality_average_concept(self):
        """Test that quality scores can be averaged."""
        records = [
            make_execution(quality_score=0.8),
            make_execution(quality_score=0.9),
            make_execution(quality_score=0.85),
        ]
        scores = [r.quality_score for r in records if r.quality_score]
        avg_score = sum(scores) / len(scores)
        assert avg_score == 0.85


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
