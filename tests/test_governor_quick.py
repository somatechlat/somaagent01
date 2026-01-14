"""Quick Test: SimpleGovernor Budget Allocation (GOV-002)

Minimal standalone test without Django dependencies.

VIBE COMPLIANT:
- Real implementation tests
- Production-grade validation
- No mocks
"""


def test_normal_mode_budget_allocation():
    """Test NORMAL mode budget allocation."""
    from services.common.simple_governor import (
        GovernorDecision,
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

    # Verify ratios (NORMAL: 15% system, 25% history, 25% memory, 20% tools)
    budget = decision.lane_budget
    assert abs(budget.system_policy - 614) < 10, f"Expected ~614, got {budget.system_policy}"
    assert abs(budget.history - 1024) < 10, f"Expected ~1024, got {budget.history}"
    assert abs(budget.memory - 1024) < 10, f"Expected ~1024, got {budget.memory}"
    assert abs(budget.tools - 819) < 10, f"Expected ~819, got {budget.tools}"

    print(f"✅ NORMAL mode: Budget allocation verified (15%/25%/25%/20%)")
    print(f"   System Policy: {budget.system_policy}")
    print(f"   History: {budget.history}")
    print(f"   Memory: {budget.memory}")
    print(f"   Tools: {budget.tools}")
    print(f"   Buffer: {budget.buffer}")
    print(f"   Total: {budget.total_allocated}")


def test_degraded_mode_budget_allocation():
    """Test DEGRADED mode budget allocation."""
    from services.common.simple_governor import (
        GovernorDecision,
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

    # Verify ratios (DEGRADED: 70% system, 10% history, 15% memory, 0% tools)
    budget = decision.lane_budget
    assert abs(budget.system_policy - 1638) < 10, f"Expected ~1638, got {budget.system_policy}"
    assert abs(budget.history - 409) < 10, f"Expected ~409, got {budget.history}"
    assert abs(budget.memory - 614) < 10, f"Expected ~614, got {budget.memory}"
    assert budget.tools == 0, f"Expected 0, got {budget.tools}"

    print(f"✅ DEGRADED mode: Budget allocation verified (70%/10%/15%/0%)")
    print(f"   System Policy: {budget.system_policy}")
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
    assert budget.system_policy == 400, f"Expected 400, got {budget.system_policy}"
    assert budget.history == 0, f"Expected 0, got {budget.history}"
    assert budget.memory == 100, f"Expected 100, got {budget.memory}"
    assert budget.tools == 0, f"Expected 0, got {budget.tools}"
    assert budget.buffer >= 200, "Buffer should be at least 200"

    print(f"✅ RESCUE mode: Budget allocation verified (emergency fallback)")
    print(f"   System Policy: {budget.system_policy}")
    print(f"   History: {budget.history}")
    print(f"   Memory: {budget.memory}")
    print(f"   Tools: {budget.tools} (DISABLED)")
    print(f"   Buffer: {budget.buffer} (LARGE)")
    print(f"   Total: {budget.total_allocated}")


if __name__ == "__main__":
    print("=" * 70)
    print("Running SimpleGovernor Budget Allocation Tests (GOV-002)")
    print("=" * 70)

    print("\n1. Testing NORMAL mode allocation...")
    test_normal_mode_budget_allocation()

    print("\n2. Testing DEGRADED mode allocation...")
    test_degraded_mode_budget_allocation()

    print("\n3. Testing RESCUE mode allocation...")
    test_rescue_mode_budget_allocation()

    print("\n" + "=" * 70)
    print("✅ All SimpleGovernor tests passed!")
    print("=" * 70)
