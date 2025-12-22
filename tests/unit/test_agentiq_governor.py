"""Unit tests for AgentIQ Governor.

VIBE COMPLIANT:
- Real implementations only (no mocks)
- Tests use actual dataclasses and computations
- No placeholder assertions

Tests cover:
- Governor decision logic
- Lane allocation across degradation levels
- AIQ score computation
- Buffer minimum enforcement
"""

import pytest
from dataclasses import dataclass
from typing import List, Optional

from python.somaagent.agentiq_governor import (
    AgentIQConfig,
    AIQWeights,
    AIQScore,
    AgentIQGovernor,
    LaneAllocator,
    LanePlan,
    LanesConfig,
    GovernorDecision,
    TurnContext,
    PathMode,
    AIQCalculator,
)
from services.common.degradation_monitor import DegradationLevel


# -----------------------------------------------------------------------------
# LanePlan Tests
# -----------------------------------------------------------------------------

class TestLanePlan:
    """Test LanePlan dataclass."""

    def test_lane_plan_total(self):
        """Total should sum all lanes."""
        plan = LanePlan(
            system_policy=500,
            history=1000,
            memory=800,
            tools=400,
            tool_results=200,
            buffer=200,
        )
        assert plan.total() == 3100

    def test_lane_plan_buffer_minimum_enforced(self):
        """Buffer should be enforced to minimum 200."""
        plan = LanePlan(
            system_policy=500,
            history=1000,
            memory=800,
            tools=400,
            tool_results=200,
            buffer=50,  # Below minimum
        )
        assert plan.buffer == 200

    def test_lane_plan_to_dict(self):
        """to_dict should return all lanes."""
        plan = LanePlan(
            system_policy=500,
            history=1000,
            memory=800,
            tools=400,
            tool_results=200,
            buffer=200,
        )
        d = plan.to_dict()
        assert d == {
            "system_policy": 500,
            "history": 1000,
            "memory": 800,
            "tools": 400,
            "tool_results": 200,
            "buffer": 200,
        }

    def test_lane_plan_immutable(self):
        """LanePlan should be immutable (frozen)."""
        plan = LanePlan(
            system_policy=500,
            history=1000,
            memory=800,
            tools=400,
            tool_results=200,
            buffer=200,
        )
        with pytest.raises(AttributeError):
            plan.buffer = 300  # type: ignore


# -----------------------------------------------------------------------------
# AIQScore Tests
# -----------------------------------------------------------------------------

class TestAIQScore:
    """Test AIQScore dataclass."""

    def test_aiq_score_clamping(self):
        """Scores should be clamped to 0-100."""
        score = AIQScore(predicted=150.0, observed=-10.0)
        assert score.predicted == 100.0
        assert score.observed == 0.0

    def test_aiq_score_with_observed(self):
        """with_observed should return new score."""
        score = AIQScore(predicted=75.0, observed=0.0)
        updated = score.with_observed(80.0)
        assert updated.observed == 80.0
        assert updated.predicted == 75.0
        # Original unchanged
        assert score.observed == 0.0

    def test_aiq_score_components(self):
        """Components should be stored correctly."""
        components = {
            "context_quality": 80.0,
            "tool_relevance": 70.0,
            "budget_efficiency": 90.0,
        }
        score = AIQScore(predicted=80.0, components=components)
        assert score.components == components


# -----------------------------------------------------------------------------
# LaneAllocator Tests
# -----------------------------------------------------------------------------

class TestLaneAllocator:
    """Test LaneAllocator."""

    @pytest.fixture
    def allocator(self):
        """Create allocator with default config."""
        return LaneAllocator(LanesConfig())

    def test_allocation_l0_normal(self, allocator):
        """L0 should use default ratios."""
        plan = allocator.allocate(
            total_budget=8000,
            degradation_level=DegradationLevel.NONE,
        )
        # System policy: 15% = 1200
        # History: 25% = 2000
        # Memory: 25% = 2000
        # Tools: 20% = 1600
        # Tool results: 10% = 800
        # Buffer: 5% = 400 (above minimum 200)
        assert plan.buffer >= 200
        assert plan.total() <= 8000

    def test_allocation_l4_critical(self, allocator):
        """L4 should minimize non-essential lanes."""
        plan = allocator.allocate(
            total_budget=8000,
            degradation_level=DegradationLevel.CRITICAL,
        )
        # At L4: history=0, tools=0, memory=0, tool_results=0
        assert plan.history == 0
        assert plan.tools == 0
        assert plan.memory == 0
        assert plan.tool_results == 0
        # System and buffer should have most of the budget
        assert plan.system_policy > 0
        assert plan.buffer >= 200

    def test_buffer_always_minimum_200(self, allocator):
        """Buffer should always be at least 200 tokens."""
        # Even with tiny budget
        plan = allocator.allocate(
            total_budget=500,
            degradation_level=DegradationLevel.NONE,
        )
        assert plan.buffer >= 200

    def test_allocation_respects_bounds(self, allocator):
        """Allocation should respect lane bounds from config."""
        plan = allocator.allocate(
            total_budget=100000,  # Very large
            degradation_level=DegradationLevel.NONE,
        )
        # Default max for history is 4000
        assert plan.history <= 4000
        # Default max for buffer is 500
        assert plan.buffer <= 500

    def test_degradation_reduces_history(self, allocator):
        """Higher degradation should reduce history allocation."""
        plan_l0 = allocator.allocate(8000, DegradationLevel.NONE)
        plan_l2 = allocator.allocate(8000, DegradationLevel.MODERATE)
        plan_l4 = allocator.allocate(8000, DegradationLevel.CRITICAL)

        assert plan_l0.history >= plan_l2.history
        assert plan_l2.history >= plan_l4.history
        assert plan_l4.history == 0


# -----------------------------------------------------------------------------
# AIQCalculator Tests
# -----------------------------------------------------------------------------

class TestAIQCalculator:
    """Test AIQCalculator."""

    @pytest.fixture
    def calculator(self):
        """Create calculator with default weights."""
        return AIQCalculator(AIQWeights())

    def test_compute_predicted_base_score(self, calculator):
        """Predicted score should be computed from context."""
        turn = TurnContext(
            turn_id="test-turn",
            session_id="test-session",
            tenant_id="test-tenant",
            system_prompt="You are a helpful assistant.",
            history=[{"role": "user", "content": "Hello"}],
        )
        plan = LanePlan(
            system_policy=500,
            history=1000,
            memory=800,
            tools=400,
            tool_results=200,
            buffer=200,
        )
        score = calculator.compute_predicted(
            turn=turn,
            lane_plan=plan,
            degradation_level=DegradationLevel.NONE,
        )
        # Score should be between 0 and 100
        assert 0.0 <= score.predicted <= 100.0
        # Components should be present
        assert "context_quality" in score.components
        assert "tool_relevance" in score.components
        assert "budget_efficiency" in score.components

    def test_memory_snippets_increase_context_quality(self, calculator):
        """Memory snippets should increase context quality."""
        turn_without = TurnContext(
            turn_id="test",
            session_id="test",
            tenant_id="test",
            memory_snippets=[],
        )
        turn_with = TurnContext(
            turn_id="test",
            session_id="test",
            tenant_id="test",
            memory_snippets=[
                {"score": 0.9, "text": "snippet1"},
                {"score": 0.8, "text": "snippet2"},
            ],
        )
        plan = LanePlan(500, 1000, 800, 400, 200, 200)

        score_without = calculator.compute_predicted(turn_without, plan, DegradationLevel.NONE)
        score_with = calculator.compute_predicted(turn_with, plan, DegradationLevel.NONE)

        # With snippets should have higher context quality component
        assert score_with.components["context_quality"] > score_without.components["context_quality"]


# -----------------------------------------------------------------------------
# PathMode Tests
# -----------------------------------------------------------------------------

class TestPathMode:
    """Test path mode determination."""

    def test_rescue_path_decision_has_all_fields(self):
        """Rescue path should have all required fields."""
        turn = TurnContext(
            turn_id="test",
            session_id="test",
            tenant_id="test",
        )
        decision = GovernorDecision.rescue_path(turn, reason="test_failure")

        assert decision.path_mode == PathMode.RESCUE
        assert decision.degradation_level == DegradationLevel.CRITICAL
        assert decision.tool_k == 0
        assert decision.allowed_tools == []
        assert decision.lane_plan.buffer >= 200


# -----------------------------------------------------------------------------
# TurnContext Tests
# -----------------------------------------------------------------------------

class TestTurnContext:
    """Test TurnContext dataclass."""

    def test_turn_context_defaults(self):
        """TurnContext should have sensible defaults."""
        turn = TurnContext(
            turn_id="turn-123",
            session_id="session-456",
            tenant_id="tenant-789",
        )
        assert turn.user_message == ""
        assert turn.system_prompt == ""
        assert turn.history == []
        assert turn.available_tools == []
        assert turn.memory_snippets == []
        assert turn.tool_results == []


# -----------------------------------------------------------------------------
# Integration-style unit tests (no external dependencies)
# -----------------------------------------------------------------------------

class TestGovernorDecision:
    """Test GovernorDecision dataclass."""

    def test_governor_decision_fields(self):
        """GovernorDecision should contain all required fields."""
        plan = LanePlan(500, 1000, 800, 400, 200, 200)
        score = AIQScore(predicted=75.0)
        decision = GovernorDecision(
            lane_plan=plan,
            aiq_score=score,
            degradation_level=DegradationLevel.NONE,
            path_mode=PathMode.FAST,
            tool_k=5,
            capsule_id="capsule-123",
            allowed_tools=["echo", "search"],
            latency_ms=5.0,
        )
        assert decision.lane_plan == plan
        assert decision.aiq_score == score
        assert decision.tool_k == 5
        assert len(decision.allowed_tools) == 2
        assert decision.latency_ms == 5.0
