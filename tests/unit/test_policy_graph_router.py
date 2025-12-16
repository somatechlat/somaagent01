"""Unit tests for PolicyGraphRouter (no DB required).

Tests verify fallback ladder logic, budget enforcement, and routing decisions
using mocked capability registry and policy client.

Pattern Reference: test_capsule_enforcer.py, test_capability_registry.py
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from services.common.policy_graph_router import (
    PolicyGraphRouter,
    RoutingDecision,
    FallbackReason,
    FALLBACK_LADDERS,
)
from services.common.capability_registry import (
    CapabilityRecord,
    CapabilityHealth,
    CostTier,
)


def make_capability(**kwargs) -> CapabilityRecord:
    """Create a test CapabilityRecord with sensible defaults."""
    defaults = {
        "tool_id": "test_tool",
        "provider": "test_provider",
        "modalities": ["image"],
        "input_schema": {},
        "output_schema": {},
        "constraints": {},
        "cost_tier": CostTier.MEDIUM,
        "health_status": CapabilityHealth.HEALTHY,
        "latency_p95_ms": 5000,
        "failure_count": 0,
        "enabled": True,
        "tenant_id": None,
        "display_name": "Test Tool",
        "description": "A test capability",
    }
    defaults.update(kwargs)
    return CapabilityRecord(**defaults)


class TestFallbackLadders:
    """Tests for fallback ladder configuration."""

    def test_image_diagram_ladder_exists(self):
        """Verify image_diagram ladder has mermaid as primary."""
        ladder = FALLBACK_LADDERS.get("image_diagram", [])
        assert len(ladder) > 0
        assert ladder[0] == ("mermaid_diagram", "local")

    def test_image_photo_ladder_exists(self):
        """Verify image_photo ladder has dalle3 as primary."""
        ladder = FALLBACK_LADDERS.get("image_photo", [])
        assert len(ladder) > 0
        assert ladder[0] == ("dalle3_image_gen", "openai")

    def test_screenshot_ladder_exists(self):
        """Verify screenshot ladder has playwright as primary."""
        ladder = FALLBACK_LADDERS.get("screenshot", [])
        assert len(ladder) > 0
        assert ladder[0] == ("playwright_screenshot", "local")

    def test_all_ladders_have_valid_format(self):
        """Verify all ladder entries are (tool_id, provider) tuples."""
        for modality, ladder in FALLBACK_LADDERS.items():
            for entry in ladder:
                assert isinstance(entry, tuple), f"Entry in {modality} not a tuple"
                assert len(entry) == 2, f"Entry in {modality} not length 2"
                tool_id, provider = entry
                assert isinstance(tool_id, str), f"tool_id in {modality} not string"
                assert isinstance(provider, str), f"provider in {modality} not string"


class TestRoutingDecision:
    """Tests for RoutingDecision dataclass."""

    def test_create_success_decision(self):
        capability = make_capability(tool_id="dalle3", provider="openai")
        decision = RoutingDecision(
            capability=capability,
            tool_id="dalle3",
            provider="openai",
            success=True,
            fallback_reason=FallbackReason.NONE,
            fallback_position=0,
        )
        assert decision.success is True
        assert decision.is_primary is True
        assert decision.tool_id == "dalle3"

    def test_create_fallback_decision(self):
        capability = make_capability(tool_id="stability", provider="stability")
        decision = RoutingDecision(
            capability=capability,
            tool_id="stability",
            provider="stability",
            success=True,
            fallback_reason=FallbackReason.UNHEALTHY,
            fallback_position=1,
        )
        assert decision.success is True
        assert decision.is_primary is False
        assert decision.fallback_position == 1

    def test_create_failure_decision(self):
        decision = RoutingDecision(
            success=False,
            fallback_reason=FallbackReason.NOT_AVAILABLE,
            denied_options=[("dalle3", "openai", "unavailable")],
        )
        assert decision.success is False
        assert decision.capability is None
        assert len(decision.denied_options) == 1


class TestFallbackReason:
    """Tests for FallbackReason enum."""

    def test_reason_values(self):
        assert FallbackReason.NONE.value == "none"
        assert FallbackReason.POLICY_DENIED.value == "policy_denied"
        assert FallbackReason.OVER_BUDGET.value == "over_budget"
        assert FallbackReason.UNHEALTHY.value == "unhealthy"
        assert FallbackReason.NOT_AVAILABLE.value == "not_available"
        assert FallbackReason.USER_OVERRIDE.value == "user_override"


class TestPolicyGraphRouterLadderLookup:
    """Tests for ladder lookup logic."""

    def test_get_ladder_exact_match(self):
        router = PolicyGraphRouter(registry=MagicMock())
        ladder = router.get_ladder("image_diagram")
        assert ladder == FALLBACK_LADDERS["image_diagram"]

    def test_get_ladder_category_fallback(self):
        router = PolicyGraphRouter(registry=MagicMock())
        # 'image_custom' should fall back to 'image' category
        ladder = router.get_ladder("image_custom")
        assert ladder == FALLBACK_LADDERS.get("image", [])

    def test_get_ladder_nonexistent(self):
        router = PolicyGraphRouter(registry=MagicMock())
        ladder = router.get_ladder("nonexistent_modality")
        assert ladder == []


class TestBudgetEnforcement:
    """Tests for budget checking logic."""

    def test_budget_within_limit(self):
        router = PolicyGraphRouter(registry=MagicMock())
        capability = make_capability(cost_tier=CostTier.MEDIUM)
        
        ok, reason = router._check_budget(
            capability=capability,
            budget_limit_cents=100,
            budget_used_cents=0,
        )
        assert ok is True
        assert reason == ""

    def test_budget_unlimited(self):
        router = PolicyGraphRouter(registry=MagicMock())
        capability = make_capability(cost_tier=CostTier.PREMIUM)
        
        ok, reason = router._check_budget(
            capability=capability,
            budget_limit_cents=None,  # Unlimited
            budget_used_cents=0,
        )
        assert ok is True

    def test_budget_exceeded(self):
        router = PolicyGraphRouter(registry=MagicMock())
        capability = make_capability(cost_tier=CostTier.PREMIUM)  # Costs ~100 cents
        
        ok, reason = router._check_budget(
            capability=capability,
            budget_limit_cents=50,  # Only 50 cents allowed
            budget_used_cents=0,
        )
        assert ok is False
        assert "exceeds" in reason

    def test_budget_already_used(self):
        router = PolicyGraphRouter(registry=MagicMock())
        capability = make_capability(cost_tier=CostTier.MEDIUM)  # Costs ~20 cents
        
        ok, reason = router._check_budget(
            capability=capability,
            budget_limit_cents=50,
            budget_used_cents=40,  # Only 10 cents remaining
        )
        assert ok is False


class TestCostEstimation:
    """Tests for cost estimation by tier."""

    def test_estimate_free_tier(self):
        router = PolicyGraphRouter(registry=MagicMock())
        capability = make_capability(cost_tier=CostTier.FREE)
        cost = router._estimate_cost(capability)
        assert cost == 0

    def test_estimate_low_tier(self):
        router = PolicyGraphRouter(registry=MagicMock())
        capability = make_capability(cost_tier=CostTier.LOW)
        cost = router._estimate_cost(capability)
        assert cost == 5

    def test_estimate_medium_tier(self):
        router = PolicyGraphRouter(registry=MagicMock())
        capability = make_capability(cost_tier=CostTier.MEDIUM)
        cost = router._estimate_cost(capability)
        assert cost == 20

    def test_estimate_high_tier(self):
        router = PolicyGraphRouter(registry=MagicMock())
        capability = make_capability(cost_tier=CostTier.HIGH)
        cost = router._estimate_cost(capability)
        assert cost == 50

    def test_estimate_premium_tier(self):
        router = PolicyGraphRouter(registry=MagicMock())
        capability = make_capability(cost_tier=CostTier.PREMIUM)
        cost = router._estimate_cost(capability)
        assert cost == 100


class TestFallbackReasonInference:
    """Tests for inferring fallback reasons from denied options."""

    def test_infer_policy_denied(self):
        router = PolicyGraphRouter(registry=MagicMock())
        denied = [("dalle3", "openai", "opa_policy_denied")]
        reason = router._infer_fallback_reason(denied)
        assert reason == FallbackReason.POLICY_DENIED

    def test_infer_over_budget(self):
        router = PolicyGraphRouter(registry=MagicMock())
        denied = [("dalle3", "openai", "estimated_cost_100_exceeds_remaining_50")]
        reason = router._infer_fallback_reason(denied)
        assert reason == FallbackReason.OVER_BUDGET

    def test_infer_unhealthy(self):
        router = PolicyGraphRouter(registry=MagicMock())
        denied = [("dalle3", "openai", "unavailable")]
        reason = router._infer_fallback_reason(denied)
        assert reason == FallbackReason.UNHEALTHY

    def test_infer_not_available(self):
        router = PolicyGraphRouter(registry=MagicMock())
        denied = [("dalle3", "openai", "not_registered")]
        reason = router._infer_fallback_reason(denied)
        assert reason == FallbackReason.NOT_AVAILABLE

    def test_infer_empty_list(self):
        router = PolicyGraphRouter(registry=MagicMock())
        reason = router._infer_fallback_reason([])
        assert reason == FallbackReason.NONE


class TestRouterIntegration:
    """Integration tests using mocked registry and policy client."""

    @pytest.mark.asyncio
    async def test_route_primary_success(self):
        """Test routing when primary option is available."""
        # Mock registry
        mock_registry = AsyncMock()
        mock_capability = make_capability(
            tool_id="mermaid_diagram",
            provider="local",
            cost_tier=CostTier.FREE,
            health_status=CapabilityHealth.HEALTHY,
        )
        mock_registry.get = AsyncMock(return_value=mock_capability)
        
        # Mock policy client
        mock_policy = AsyncMock()
        mock_policy.evaluate = AsyncMock(return_value=True)
        
        router = PolicyGraphRouter(
            registry=mock_registry,
            policy_client=mock_policy,
        )
        
        decision = await router.route(
            modality="image_diagram",
            tenant_id="test-tenant",
        )
        
        assert decision.success is True
        assert decision.tool_id == "mermaid_diagram"
        assert decision.provider == "local"
        assert decision.is_primary is True

    @pytest.mark.asyncio
    async def test_route_fallback_on_unhealthy(self):
        """Test fallback when primary is unhealthy."""
        # Mock registry - first call returns unhealthy, second returns healthy
        mock_registry = AsyncMock()
        unhealthy_cap = make_capability(
            tool_id="mermaid_diagram",
            provider="local",
            health_status=CapabilityHealth.UNAVAILABLE,
        )
        healthy_cap = make_capability(
            tool_id="plantuml_diagram",
            provider="local",
            health_status=CapabilityHealth.HEALTHY,
            cost_tier=CostTier.FREE,
        )
        mock_registry.get = AsyncMock(side_effect=[unhealthy_cap, healthy_cap])
        
        # Mock policy client
        mock_policy = AsyncMock()
        mock_policy.evaluate = AsyncMock(return_value=True)
        
        router = PolicyGraphRouter(
            registry=mock_registry,
            policy_client=mock_policy,
        )
        
        decision = await router.route(
            modality="image_diagram",
            tenant_id="test-tenant",
        )
        
        assert decision.success is True
        assert decision.tool_id == "plantuml_diagram"
        assert decision.fallback_position == 1
        assert decision.fallback_reason == FallbackReason.UNHEALTHY

    @pytest.mark.asyncio
    async def test_route_all_exhausted(self):
        """Test failure when all options exhausted."""
        mock_registry = AsyncMock()
        mock_registry.get = AsyncMock(return_value=None)  # Nothing registered
        
        router = PolicyGraphRouter(registry=mock_registry)
        
        decision = await router.route(
            modality="image_diagram",
            tenant_id="test-tenant",
        )
        
        assert decision.success is False
        assert len(decision.denied_options) > 0

    @pytest.mark.asyncio
    async def test_route_nonexistent_modality(self):
        """Test routing for unknown modality."""
        mock_registry = AsyncMock()
        router = PolicyGraphRouter(registry=mock_registry)
        
        decision = await router.route(
            modality="unknown_modality",
            tenant_id="test-tenant",
        )
        
        assert decision.success is False
        assert decision.fallback_reason == FallbackReason.NOT_AVAILABLE


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
