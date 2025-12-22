"""Unit tests for RunReceipt.

VIBE COMPLIANT:
- Real implementations only (no mocks)
- Tests use actual dataclasses
- No placeholder assertions

Tests cover:
- RunReceipt immutability
- Serialization to audit event
- Builder pattern validation
- No PII in receipts
"""

import pytest
import time
from typing import Dict

from python.somaagent.run_receipt import (
    RunReceipt,
    RunReceiptBuilder,
    create_receipt_from_decision,
)
from python.somaagent.agentiq_governor import (
    GovernorDecision,
    LanePlan,
    AIQScore,
    TurnContext,
    PathMode,
)
from services.common.degradation_monitor import DegradationLevel


# -----------------------------------------------------------------------------
# RunReceipt Tests
# -----------------------------------------------------------------------------

class TestRunReceipt:
    """Test RunReceipt dataclass."""

    @pytest.fixture
    def sample_receipt(self) -> RunReceipt:
        """Create a sample receipt for testing."""
        return RunReceipt(
            turn_id="turn-123",
            session_id="session-456",
            tenant_id="tenant-789",
            capsule_id="capsule-001",
            aiq_pred=75.0,
            aiq_obs=80.0,
            confidence=0.85,
            lane_budgets={
                "system_policy": 500,
                "history": 1000,
                "memory": 800,
                "tools": 400,
                "tool_results": 200,
                "buffer": 200,
            },
            lane_actual={
                "system_policy": 450,
                "history": 950,
                "memory": 750,
                "tools": 350,
                "tool_results": 150,
                "buffer": 200,
            },
            degradation_level="L0",
            path_mode="fast",
            tool_k=5,
            latency_ms=8.5,
            timestamp=time.time(),
        )

    def test_run_receipt_immutable(self, sample_receipt):
        """RunReceipt should be immutable (frozen)."""
        with pytest.raises(AttributeError):
            sample_receipt.aiq_pred = 90.0  # type: ignore

    def test_run_receipt_to_audit_event(self, sample_receipt):
        """to_audit_event should return serializable dict."""
        event = sample_receipt.to_audit_event()
        
        assert event["turn_id"] == "turn-123"
        assert event["session_id"] == "session-456"
        assert event["tenant_id"] == "tenant-789"
        assert event["aiq_pred"] == 75.0
        assert event["aiq_obs"] == 80.0
        assert event["confidence"] == 0.85
        assert event["degradation_level"] == "L0"
        assert event["path_mode"] == "fast"
        assert event["tool_k"] == 5
        assert "lane_budgets" in event
        assert "lane_actual" in event

    def test_run_receipt_to_dict(self, sample_receipt):
        """to_dict should return all fields."""
        d = sample_receipt.to_dict()
        assert d["turn_id"] == "turn-123"
        assert d["latency_ms"] == 8.5
        assert "timestamp" in d

    def test_run_receipt_from_dict(self, sample_receipt):
        """from_dict should reconstruct receipt."""
        d = sample_receipt.to_dict()
        restored = RunReceipt.from_dict(d)
        
        assert restored.turn_id == sample_receipt.turn_id
        assert restored.aiq_pred == sample_receipt.aiq_pred
        assert restored.confidence == sample_receipt.confidence

    def test_run_receipt_no_pii(self, sample_receipt):
        """Receipt should not contain PII."""
        event = sample_receipt.to_audit_event()
        event_str = str(event).lower()
        
        # Should not contain common PII field names
        assert "email" not in event_str
        assert "password" not in event_str
        assert "phone" not in event_str
        assert "ssn" not in event_str
        assert "credit_card" not in event_str

    def test_run_receipt_nullable_confidence(self):
        """Confidence can be None."""
        receipt = RunReceipt(
            turn_id="turn-123",
            session_id="session-456",
            tenant_id="tenant-789",
            capsule_id=None,
            aiq_pred=75.0,
            aiq_obs=80.0,
            confidence=None,  # No confidence
            lane_budgets={},
            lane_actual={},
            degradation_level="L0",
            path_mode="fast",
            tool_k=5,
            latency_ms=8.5,
            timestamp=time.time(),
        )
        assert receipt.confidence is None
        event = receipt.to_audit_event()
        assert event["confidence"] is None


# -----------------------------------------------------------------------------
# RunReceiptBuilder Tests
# -----------------------------------------------------------------------------

class TestRunReceiptBuilder:
    """Test RunReceiptBuilder."""

    def test_builder_fluent_interface(self):
        """Builder should support fluent interface."""
        receipt = (
            RunReceiptBuilder()
            .turn_id("turn-123")
            .session_id("session-456")
            .tenant_id("tenant-789")
            .aiq_pred(75.0)
            .aiq_obs(80.0)
            .lane_budgets({"system_policy": 500})
            .lane_actual({"system_policy": 450})
            .degradation_level("L0")
            .path_mode("fast")
            .tool_k(5)
            .latency_ms(8.5)
            .build()
        )
        assert receipt.turn_id == "turn-123"
        assert receipt.aiq_pred == 75.0

    def test_builder_required_fields(self):
        """Builder should validate required fields."""
        with pytest.raises(ValueError):
            RunReceiptBuilder().build()  # Missing required fields

    def test_builder_missing_turn_id(self):
        """Builder should require turn_id."""
        with pytest.raises(ValueError) as exc_info:
            (
                RunReceiptBuilder()
                .session_id("session-456")
                .tenant_id("tenant-789")
                .aiq_pred(75.0)
                .aiq_obs(80.0)
                .build()
            )
        assert "turn_id" in str(exc_info.value).lower()

    def test_builder_default_timestamp(self):
        """Builder should set timestamp if not provided."""
        receipt = (
            RunReceiptBuilder()
            .turn_id("turn-123")
            .session_id("session-456")
            .tenant_id("tenant-789")
            .aiq_pred(75.0)
            .aiq_obs(80.0)
            .lane_budgets({})
            .lane_actual({})
            .degradation_level("L0")
            .path_mode("fast")
            .tool_k(5)
            .latency_ms(8.5)
            .build()
        )
        assert receipt.timestamp > 0

    def test_builder_confidence_clamping(self):
        """Builder should clamp confidence to 0-1."""
        receipt = (
            RunReceiptBuilder()
            .turn_id("turn-123")
            .session_id("session-456")
            .tenant_id("tenant-789")
            .aiq_pred(75.0)
            .aiq_obs(80.0)
            .confidence(1.5)  # Above max
            .lane_budgets({})
            .lane_actual({})
            .degradation_level("L0")
            .path_mode("fast")
            .tool_k(5)
            .latency_ms(8.5)
            .build()
        )
        assert receipt.confidence <= 1.0


# -----------------------------------------------------------------------------
# Factory Function Tests
# -----------------------------------------------------------------------------

class TestCreateReceiptFromDecision:
    """Test create_receipt_from_decision factory function."""

    def test_create_from_decision(self):
        """Factory should create receipt from GovernorDecision."""
        decision = GovernorDecision(
            lane_plan=LanePlan(500, 1000, 800, 400, 200, 200),
            aiq_score=AIQScore(predicted=75.0, observed=80.0),
            degradation_level=DegradationLevel.NONE,
            path_mode=PathMode.FAST,
            tool_k=5,
            capsule_id="capsule-001",
            allowed_tools=["echo", "search"],
            latency_ms=8.5,
        )
        turn = TurnContext(
            turn_id="turn-123",
            session_id="session-456",
            tenant_id="tenant-789",
        )
        lane_actual = {
            "system_policy": 450,
            "history": 950,
            "memory": 750,
            "tools": 350,
            "tool_results": 150,
            "buffer": 200,
        }

        receipt = create_receipt_from_decision(
            decision=decision,
            turn_context=turn,
            lane_actual=lane_actual,
            confidence=0.85,
            aiq_obs=80.0,
        )

        assert receipt.turn_id == "turn-123"
        assert receipt.session_id == "session-456"
        assert receipt.tenant_id == "tenant-789"
        assert receipt.aiq_pred == 75.0
        assert receipt.aiq_obs == 80.0
        assert receipt.confidence == 0.85
        assert receipt.path_mode == "fast"
        assert receipt.tool_k == 5
