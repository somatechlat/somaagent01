"""AgentIQ Governor Tests.

Tests token budgeting, AIQ scoring, and path determination.

VIBE COMPLIANT:
- Real infrastructure for degradation checks
- No mocks for core logic
"""

from __future__ import annotations

import os
from uuid import uuid4

import pytest

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.environ.get("SA01_INFRA_AVAILABLE") != "1",
        reason="Requires SA01_INFRA_AVAILABLE=1",
    ),
]


class TestLaneAllocator:
    """Test lane allocation logic."""

    def test_default_lane_allocation(self):
        """Test default lane ratios for healthy system."""
        from admin.agents.services.agentiq_schemas import LanesConfig
        from admin.agents.services.agentiq_governor import LaneAllocator
        from services.common.degradation_schemas import DegradationLevel
        
        config = LanesConfig()
        allocator = LaneAllocator(config)
        
        lane_plan = allocator.allocate(
            total_budget=10000,
            degradation_level=DegradationLevel.NONE,
        )
        
        # Check all lanes are allocated
        assert lane_plan.system_policy > 0
        assert lane_plan.history > 0
        assert lane_plan.memory > 0
        assert lane_plan.tools > 0
        assert lane_plan.tool_results > 0
        assert lane_plan.buffer >= 200  # Minimum buffer
        
        # Total should not exceed budget
        total = (lane_plan.system_policy + lane_plan.history + lane_plan.memory +
                 lane_plan.tools + lane_plan.tool_results + lane_plan.buffer)
        assert total <= 10000

    def test_degraded_allocation_reduces_tools(self):
        """Test that degradation reduces tool allocation."""
        from admin.agents.services.agentiq_schemas import LanesConfig
        from admin.agents.services.agentiq_governor import LaneAllocator
        from services.common.degradation_schemas import DegradationLevel
        
        config = LanesConfig()
        allocator = LaneAllocator(config)
        
        normal_plan = allocator.allocate(
            total_budget=10000,
            degradation_level=DegradationLevel.NONE,
        )
        
        degraded_plan = allocator.allocate(
            total_budget=10000,
            degradation_level=DegradationLevel.MODERATE,
        )
        
        # Degraded should have fewer tools
        assert degraded_plan.tools < normal_plan.tools
        # But more buffer
        assert degraded_plan.buffer >= normal_plan.buffer

    def test_critical_allocation_minimal(self):
        """Test that critical degradation gives minimal allocation."""
        from admin.agents.services.agentiq_schemas import LanesConfig
        from admin.agents.services.agentiq_governor import LaneAllocator
        from services.common.degradation_schemas import DegradationLevel
        
        config = LanesConfig()
        allocator = LaneAllocator(config)
        
        critical_plan = allocator.allocate(
            total_budget=10000,
            degradation_level=DegradationLevel.CRITICAL,
        )
        
        # Critical should have zero tools
        assert critical_plan.tools == 0
        assert critical_plan.history == 0
        # But system_policy should be high
        assert critical_plan.system_policy > 0


class TestAIQCalculator:
    """Test AIQ scoring logic."""

    def test_aiq_score_range(self):
        """Test that AIQ score is in valid range."""
        from admin.agents.services.agentiq_schemas import AIQWeights, TurnContext, LanePlan
        from admin.agents.services.agentiq_governor import AIQCalculator
        from services.common.degradation_schemas import DegradationLevel
        
        weights = AIQWeights()
        calculator = AIQCalculator(weights)
        
        turn = TurnContext(
            turn_id=str(uuid4()),
            session_id=str(uuid4()),
            tenant_id=str(uuid4()),
            user_message="Test message",
            history=[{"role": "user", "content": "Previous message"}],
            system_prompt="You are a helpful assistant.",
        )
        
        lane_plan = LanePlan(
            system_policy=500,
            history=1000,
            memory=800,
            tools=600,
            tool_results=400,
            buffer=300,
        )
        
        aiq = calculator.compute_predicted(turn, lane_plan, DegradationLevel.NONE)
        
        assert aiq.predicted >= 0
        assert aiq.predicted <= 100
        assert "context_quality" in aiq.components
        assert "tool_relevance" in aiq.components
        assert "budget_efficiency" in aiq.components

    def test_aiq_higher_with_memory(self):
        """Test that memory snippets increase AIQ score."""
        from admin.agents.services.agentiq_schemas import AIQWeights, TurnContext, LanePlan
        from admin.agents.services.agentiq_governor import AIQCalculator
        from services.common.degradation_schemas import DegradationLevel
        
        weights = AIQWeights()
        calculator = AIQCalculator(weights)
        
        lane_plan = LanePlan(
            system_policy=500, history=1000, memory=800,
            tools=600, tool_results=400, buffer=300,
        )
        
        turn_no_memory = TurnContext(
            turn_id=str(uuid4()), session_id=str(uuid4()), tenant_id=str(uuid4()),
            user_message="Test", history=[], system_prompt="",
        )
        
        turn_with_memory = TurnContext(
            turn_id=str(uuid4()), session_id=str(uuid4()), tenant_id=str(uuid4()),
            user_message="Test", history=[],
            system_prompt="",
            memory_snippets=[{"score": 0.9, "content": "Relevant memory"}],
        )
        
        aiq_no_mem = calculator.compute_predicted(turn_no_memory, lane_plan, DegradationLevel.NONE)
        aiq_with_mem = calculator.compute_predicted(turn_with_memory, lane_plan, DegradationLevel.NONE)
        
        assert aiq_with_mem.predicted >= aiq_no_mem.predicted


class TestGovernorDecision:
    """Test full Governor decision flow."""

    @pytest.mark.asyncio
    async def test_govern_returns_decision(self, governor, test_tenant_id):
        """Test that govern returns a complete decision."""
        from admin.agents.services.agentiq_schemas import TurnContext, GovernorDecision
        
        turn = TurnContext(
            turn_id=str(uuid4()),
            session_id=str(uuid4()),
            tenant_id=test_tenant_id,
            user_message="Hello, world!",
            history=[],
            system_prompt="You are a helpful assistant.",
        )
        
        decision = await governor.govern(turn, max_tokens=8000)
        
        assert isinstance(decision, GovernorDecision)
        assert decision.lane_plan is not None
        assert decision.aiq_score is not None
        assert decision.degradation_level is not None
        assert decision.path_mode is not None
        assert decision.tool_k >= 0
        assert decision.latency_ms > 0

    @pytest.mark.asyncio
    async def test_govern_with_fallback(self, governor, test_tenant_id):
        """Test govern_with_fallback handles errors gracefully."""
        from admin.agents.services.agentiq_schemas import TurnContext, PathMode
        
        turn = TurnContext(
            turn_id=str(uuid4()),
            session_id=str(uuid4()),
            tenant_id=test_tenant_id,
            user_message="Test",
            history=[],
            system_prompt="",
        )
        
        decision = await governor.govern_with_fallback(turn, max_tokens=8000)
        
        # Should always return a decision (never raise)
        assert decision is not None
        # In case of error, should be rescue path
        assert decision.path_mode in [PathMode.FAST, PathMode.RESCUE]
