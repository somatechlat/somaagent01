import logging

logger = logging.getLogger(__name__)
"""Quick Test: SimpleGovernor Budget Allocation (GOV-002)

Minimal standalone test without Django dependencies.

VIBE COMPLIANT:
- Real implementation tests
- Production-grade validation
- No mocks
"""

from admin.core.context.lanes import LANE_KEYS as BUILDER_LANE_KEYS

# Must be the same spelling as admin.core.context.lanes.LANE_KEYS (AP-06).
GOVERNOR_LANE_KEYS = ("system", "history", "memory", "tools", "buffer")


def test_lane_vocabulary_matches_builder():
    """One vocabulary: governor lanes are exactly ContextBuilder LANE_KEYS."""
    from services.common.simple_governor import LANE_KEYS as GOV_KEYS

    assert GOV_KEYS == BUILDER_LANE_KEYS
    assert GOVERNOR_LANE_KEYS == BUILDER_LANE_KEYS


def test_five_lane_keys_sum_to_full_budget():
    """The five keys carry the whole turn budget — no silent 10% loss."""
    from services.common.simple_governor import SimpleGovernor

    governor = SimpleGovernor()
    max_tokens = 4096

    for is_degraded in (False, True):
        decision = governor.allocate_budget(
            max_tokens=max_tokens,
            is_degraded=is_degraded,
        )
        budget = decision.lane_budget
        keys = budget.to_dict()

        assert set(keys) == set(BUILDER_LANE_KEYS)
        assert "tool_results" not in keys
        assert "system_policy" not in keys
        assert budget.total_allocated == max_tokens
        assert sum(keys.values()) == max_tokens
        assert sum(SimpleGovernor.NORMAL_RATIOS.values()) == 1.0
        assert sum(SimpleGovernor.DEGRADED_RATIOS.values()) == 1.0

    print("  five LANE_KEYS sum to the full budget in normal and degraded mode")


def test_normal_mode_budget_allocation():
    """Test NORMAL mode budget allocation."""
    from services.common.simple_governor import (
        HealthStatus,
        SimpleGovernor,
    )

    governor = SimpleGovernor()

    # Test NORMAL mode allocation
    decision = governor.allocate_budget(
        max_tokens=4096,
        is_degraded=False,
    )

    assert decision.health_status == HealthStatus.HEALTHY
    assert decision.mode == "normal"
    assert decision.tools_enabled is True

    # NORMAL: 15% system, 35% history, 25% memory, 20% tools, 5% buffer
    budget = decision.lane_budget
    assert budget.system == 614, f"Expected 614, got {budget.system}"
    assert budget.history == 1434, f"Expected 1434, got {budget.history}"
    assert budget.memory == 1024, f"Expected 1024, got {budget.memory}"
    assert budget.tools == 819, f"Expected 819, got {budget.tools}"
    assert budget.buffer == 205, f"Expected 205, got {budget.buffer}"
    assert budget.total_allocated == 4096

    print("✅ NORMAL mode: Budget allocation verified (15%/35%/25%/20%/5%)")
    print(f"   System: {budget.system}")
    print(f"   History: {budget.history}")
    print(f"   Memory: {budget.memory}")
    print(f"   Tools: {budget.tools}")
    print(f"   Buffer: {budget.buffer}")
    print(f"   Total: {budget.total_allocated}")


def test_degraded_mode_budget_allocation():
    """Test DEGRADED mode budget allocation."""
    from services.common.simple_governor import (
        HealthStatus,
        SimpleGovernor,
    )

    governor = SimpleGovernor()

    # Test DEGRADED mode allocation
    decision = governor.allocate_budget(
        max_tokens=4096,
        is_degraded=True,
    )

    assert decision.health_status == HealthStatus.DEGRADED
    assert decision.mode == "degraded"
    assert decision.tools_enabled is False, "Tools should be disabled in degraded mode"

    # DEGRADED: 40% system, 10% history, 15% memory, 0% tools, 35% buffer
    budget = decision.lane_budget
    assert budget.system == 1638, f"Expected 1638, got {budget.system}"
    assert budget.history == 410, f"Expected 410, got {budget.history}"
    assert budget.memory == 614, f"Expected 614, got {budget.memory}"
    assert budget.tools == 0, f"Expected 0, got {budget.tools}"
    assert budget.buffer == 1434, f"Expected 1434, got {budget.buffer}"
    assert budget.total_allocated == 4096

    print("✅ DEGRADED mode: Budget allocation verified (40%/10%/15%/0%/35%)")
    print(f"   System: {budget.system}")
    print(f"   History: {budget.history}")
    print(f"   Memory: {budget.memory}")
    print(f"   Tools: {budget.tools} (DISABLED)")
    print(f"   Buffer: {budget.buffer}")
    print(f"   Total: {budget.total_allocated}")


def test_rescue_mode_budget_allocation():
    """Test RESCUE mode budget allocation."""
    from services.common.simple_governor import GovernorDecision, HealthStatus

    # Test rescue path
    decision = GovernorDecision.rescue_path(reason="Emergency fallback")

    assert decision.health_status == HealthStatus.DEGRADED
    assert decision.mode == "degraded"
    assert decision.tools_enabled is False

    # Verify rescue path allocation
    budget = decision.lane_budget
    assert budget.system == 400, f"Expected 400, got {budget.system}"
    assert budget.history == 0, f"Expected 0, got {budget.history}"
    assert budget.memory == 100, f"Expected 100, got {budget.memory}"
    assert budget.tools == 0, f"Expected 0, got {budget.tools}"
    assert budget.buffer == 500, f"Expected 500, got {budget.buffer}"

    print("✅ RESCUE mode: Budget allocation verified (emergency fallback)")
    print(f"   System: {budget.system}")
    print(f"   History: {budget.history}")
    print(f"   Memory: {budget.memory}")
    print(f"   Tools: {budget.tools} (DISABLED)")
    print(f"   Buffer: {budget.buffer} (LARGE)")
    print(f"   Total: {budget.total_allocated}")


if __name__ == "__main__":
    logger.info("=" * 70)
    logger.info("Running SimpleGovernor Budget Allocation Tests (GOV-002)")
    logger.info("=" * 70)

    logger.info("\n0. Testing lane vocabulary...")
    test_lane_vocabulary_matches_builder()

    logger.info("\n0b. Testing five-key sum-to-budget...")
    test_five_lane_keys_sum_to_full_budget()

    logger.info("\n1. Testing NORMAL mode allocation...")
    test_normal_mode_budget_allocation()

    logger.info("\n2. Testing DEGRADED mode allocation...")
    test_degraded_mode_budget_allocation()

    logger.info("\n3. Testing RESCUE mode allocation...")
    test_rescue_mode_budget_allocation()

    logger.info("\n" + "=" * 70)
    logger.info("✅ All SimpleGovernor tests passed!")
    logger.info("=" * 70)
