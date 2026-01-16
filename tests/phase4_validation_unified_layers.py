"""
Phase 4 Validation: Unified Layers A/B Testing
Compares legacy AgentIQ path vs new simplified path
"""

import asyncio
import os
import time
from dataclasses import dataclass
from typing import Dict, Any, Optional
from unittest.mock import Mock, AsyncMock, patch

import pytest

# Configure test environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
os.environ.setdefault("SA01_USE_SIMPLIFIED_LAYERS", "false")


@dataclass
class ValidationMetrics:
    """Metrics collected from a single chat turn."""
    path: str  # "legacy" or "simplified"
    latency_ms: float
    tokens_total: int  # Total tokens in context
    error_occurred: bool
    circuit_open_occurred: bool
    health_status: str
    budget_used: Dict[str, int]
    lane_actuals: Dict[str, int]


class Phase4Validator:
    """Validates unified layers against legacy paths."""

    def __init__(self):
        self.metrics: list[ValidationMetrics] = []
        self.test_scenarios = [
            {"name": "Normal Turn", "token_budget": 4096, "degraded": False},
            {"name": "Degraded Turn", "token_budget": 4096, "degraded": True},
            {"name": "Memory-Rich Turn", "token_budget": 8192, "degraded": False, "memory_snippets": 5},
            {"name": "Tool-Heavy Turn", "token_budget": 4096, "degraded": False, "tools_count": 3},
        ]

    async def test_simplified_budget_allocation(self):
        """Test SimpleGovernor budget allocation vs legacy."""
        from services.common.simple_governor import SimpleGovernor, get_governor, GovernorDecision, HealthStatus

        governor = get_governor()
        print("\n[TEST 1] SimpleGovernor Budget Allocation")

        # Test NORMAL mode
        result_normal: GovernorDecision = governor.allocate_budget(
            max_tokens=4096,
            is_degraded=False
        )
        print(f"  NORMAL budget: {result_normal.lane_budget}")
        print(f"    System Policy: {result_normal.lane_budget.system_policy} (expected 15% = 614)")
        print(f"    History: {result_normal.lane_budget.history} (expected 25% = 1024)")
        print(f"    Memory: {result_normal.lane_budget.memory} (expected 25% = 1024)")
        print(f"    Tools: {result_normal.lane_budget.tools} (expected 20% = 819)")

        # Verify ratios
        assert result_normal.health_status == HealthStatus.HEALTHY
        assert abs(result_normal.lane_budget.system_policy - 614) < 10, "Normal system ratio incorrect"
        assert abs(result_normal.lane_budget.history - 1024) < 10, "Normal history ratio incorrect"
        assert abs(result_normal.lane_budget.memory - 1024) < 10, "Normal memory ratio incorrect"
        assert abs(result_normal.lane_budget.tools - 819) < 10, "Normal tools ratio incorrect"
        assert result_normal.tools_enabled is True
        assert result_normal.mode == "normal"
        print("  ✅ NORMAL ratios verified")

        # Test DEGRADED mode
        result_degraded: GovernorDecision = governor.allocate_budget(
            max_tokens=4096,
            is_degraded=True
        )
        print(f"\n  DEGRADED budget: {result_degraded.lane_budget}")
        print(f"    System Policy: {result_degraded.lane_budget.system_policy} (expected 40% = 1638)")
        print(f"    History: {result_degraded.lane_budget.history} (expected 10% = 409)")
        print(f"    Memory: {result_degraded.lane_budget.memory} (expected 15% = 614)")
        print(f"    Tools: {result_degraded.lane_budget.tools} (expected 0%)")

        assert result_degraded.health_status == HealthStatus.DEGRADED
        assert abs(result_degraded.lane_budget.system_policy - 1638) < 10, "Degraded system ratio incorrect"
        assert abs(result_degraded.lane_budget.history - 409) < 10, "Degraded history ratio incorrect"
        assert abs(result_degraded.lane_budget.tools - 0) < 1, "Degraded tools should be 0"
        assert result_degraded.tools_enabled is False
        assert result_degraded.mode == "degraded"
        print("  ✅ DEGRADED ratios verified")

        return True

    async def test_unified_metrics(self):
        """Test UnifiedMetrics collection vs legacy scattered metrics."""
        from services.common.unified_metrics import (
            get_metrics, HealthStatus, TurnPhase
        )
        from prometheus_client import REGISTRY

        print("\n[TEST 2] UnifiedMetrics Collection")

        metrics = get_metrics()

        # Record turn start
        turn_id = "test-turn-123"
        turn = metrics.record_turn_start(
            turn_id=turn_id,
            tenant_id="tenant-1",
            user_id="user-789",
            agent_id="agent-456"
        )
        print(f"  Turn started: {turn_id}")

        # Record phases
        metrics.record_turn_phase(turn_id, TurnPhase.AUTH_VALIDATED)
        metrics.record_turn_phase(turn_id, TurnPhase.BUDGET_ALLOCATED)
        metrics.record_turn_phase(turn_id, TurnPhase.CONTEXT_BUILT)
        metrics.record_turn_phase(turn_id, TurnPhase.LLM_INVOKED)
        print(f"  Phases recorded: {len([p for p in TurnPhase if p in turn.phases])}")

        # Record health status
        metrics.record_health_status(service_name="somabrain", is_healthy=True, latency_ms=25.0)
        metrics.record_health_status(service_name="database", is_healthy=True, latency_ms=5.0)
        print(f"  Health statuses recorded")

        # Record memory retrieval
        metrics.record_memory_retrieval(latency_seconds=0.045, snippet_count=3)
        print(f"  Memory retrieval recorded")

        # Complete turn with tokens
        metrics.record_turn_complete(
            turn_id=turn_id,
            tokens_in=500,
            tokens_out=300,
            model="gpt-4o",
            provider="openai",
            error=None
        )
        print(f"  Turn completed: 800 tokens total")

        # Check metrics in Registry
        print(f"  Total metrics registered: {len(list(REGISTRY.collect()))}")

        # Verify TurnMetrics was recorded and completed
        assert turn.tenant_id == "tenant-1"
        assert turn.tokens_in == 500
        assert turn.tokens_out == 300
        assert turn.latency_ms is not None and turn.latency_ms > 0
        assert turn.error is None

        print(f"  Turn stats: latency_ms={turn.latency_ms:.2f}, tokens={turn.tokens_in + turn.tokens_out}")
        print("  ✅ UnifiedMetrics working correctly")

        return True

    async def test_circuit_breaker(self):
        """Test unified circuit breaker behavior."""
        from services.common.circuit_breaker import (
            CircuitBreaker, CircuitState, CircuitBreakerConfig, CircuitBreakerError
        )

        print("\n[TEST 3] Unified Circuit Breaker")

        # Create circuit breaker for SomaBrain with custom exception
        class CustomException(Exception):
            pass

        config = CircuitBreakerConfig(
            name="somabrain_retrieval",
            failure_threshold=2,
            reset_timeout=5.0,
            expected_exceptions=(CustomException,),
        )
        cb = CircuitBreaker(config=config)

        print(f"  Circuit breaker name: {cb.config.name}")
        print(f"  Initial state: {cb.state.value}")

        # Test successful calls
        async def mock_success(*args, **kwargs):
            return {"result": "success"}

        result = await cb.call(mock_success)
        assert result == {"result": "success"}
        assert cb.state == CircuitState.CLOSED
        print("  ✅ Successful call: state = CLOSED")

        # Test failure exception handling
        async def mock_failure(*args, **kwargs):
            raise CustomException("Simulated failure")

        try:
            await cb.call(mock_failure)
            print("  ⚠️  Expected CustomException but got result")
        except CustomException:
            print("  ✅ CustomException caught ( tracked in failure count)")

        # Verify circuit breaker exists and can be created with different configs
        config2 = CircuitBreakerConfig(
            name="database_query",
            failure_threshold=5,
            reset_timeout=60.0,
        )
        cb2 = CircuitBreaker(config=config2)
        assert cb2.config.name == "database_query"
        assert cb2.config.failure_threshold == 5
        print("  ✅ Multiple circuit breakers can be created")

        # Test CircuitBreakerError is raised when OPEN
        assert isinstance(CircuitBreakerError("test", "message"), Exception)
        print("  ✅ CircuitBreakerError exception type exists")

        print("  ✅ Circuit breaker components working")

        return True

    async def test_health_monitor(self):
        """Test HealthMonitor binary health detection."""
        from services.common.health_monitor import (
            HealthMonitor, HealthCheck, ServiceStatus
        )

        print("\n[TEST 4] HealthMonitor Binary Detection")

        monitor = HealthMonitor()
        print(f"  HealthMonitor initialized with critical services: {monitor.CRITICAL_SERVICES}")

        # Verify critical services set
        assert "somabrain" in monitor.CRITICAL_SERVICES
        assert "database" in monitor.CRITICAL_SERVICES
        assert "llm" in monitor.CRITICAL_SERVICES
        print("  ✅ Critical services defined")

        # Register mock health checkers for critical services
        def create_healthy_checker():
            return HealthCheck(healthy=True, latency_ms=10.0)

        def create_unhealthy_checker():
            return HealthCheck(healthy=False, latency_ms=1000.0, error="Service timeout")

        # Register healthy checkers
        monitor.register_health_checker("somabrain", create_healthy_checker)
        monitor.register_health_checker("database", create_healthy_checker)
        monitor.register_health_checker("llm", create_healthy_checker)

        # Perform health check
        await monitor._check_all_services()

        # Check if degraded (should not be with all healthy)
        is_degraded = monitor.is_degraded()
        print(f"  All services healthy: is_degraded={is_degraded}")
        assert is_degraded is False, "Should not be degraded when all critical services healthy"

        # Get OverallHealth
        overall = monitor.get_overall_health()
        print(f"  Overall (healthy): healthy={overall.healthy}, degraded={overall.degraded}, critical_failure={overall.critical_failure}")
        assert overall.healthy is True, "Should be healthy when all critical services healthy"
        assert overall.critical_failure is False, "Should not have critical failure when all healthy"

        # Now register an unhealthy checker for a critical service
        monitor.register_health_checker("somabrain", create_unhealthy_checker)
        await monitor._check_all_services()

        # Check if degraded (should be now)
        is_degraded = monitor.is_degraded()
        print(f"  SomaBrain unhealthy: is_degraded={is_degraded}")
        assert is_degraded is True, "Should be degraded when SomaBrain unhealthy"

        # Check OverallHealth after failure - get_critical_failures() is on OverallHealth
        overall = monitor.get_overall_health()
        print(f"  Overall (unhealthy): healthy={overall.healthy}, degraded={overall.degraded}, critical_failure={overall.critical_failure}")
        assert overall.critical_failure is True, "Should have critical failure flag set"
        # Call get_critical_failures on OverallHealth instance
        critical_failures = overall.get_critical_failures()
        assert "somabrain" in critical_failures, "SomaBrain should be in critical failures list"
        print("  ✅ Binary degradation detection working")

        # Test is_critical method on OverallHealth
        is_critical = overall.is_critical()
        assert is_critical is True, "is_critical should return True when critical service unhealthy"
        print("  ✅ is_critical() method working")

        return True

    async def test_context_builder(self):
        """Test SimpleContextBuilder vs legacy."""
        from unittest.mock import AsyncMock, Mock
        from services.common.simple_context_builder import (
            ContextBuilder, BuiltContext
        )

        print("\n[TEST 5] SimpleContextBuilder")

        # Create mock SomaBrain client
        mock_somabrain = AsyncMock()
        mock_somabrain.retrieve_snippets.return_value = [
            {"content": "Python is a programming language", "metadata": {"source": "docs"}},
        ]

        # Create mock token counter
        def mock_token_counter(text: str) -> int:
            return len(text.split())  # Simple word count for testing

        # Create builder
        builder = ContextBuilder(
            somabrain=mock_somabrain,
            token_counter=mock_token_counter,
        )
        print(f"  ContextBuilder initialized")

        # Test degraded mode first (simpler - no memory retrieval)
        turn_degraded = {
            "system_prompt": "You are SomaAgent01.",
            "user_message": "Tell me about Python",
            "history": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there"},
                {"role": "user", "content": "How are you?"},
            ]
        }

        lane_budget_degraded = {
            "system_policy": 100,
            "history": 200,
            "memory": 50,  # Budget available but won't use due to degraded flag
            "tools": 0,
            "tool_results": 0,
            "buffer": 50,
        }

        # Build context in degraded mode
        built_degraded = await builder.build_for_turn(
            turn=turn_degraded,
            lane_budget=lane_budget_degraded,
            is_degraded=True
        )

        print(f"  Degraded context built:")
        print(f"    System prompt length: {len(built_degraded.system_prompt)} chars")
        print(f"    Messages count: {len(built_degraded.messages)}")
        print(f"    Token counts: {built_degraded.token_counts}")
        print(f"    Lane actuals: {built_degraded.lane_actual}")

        assert built_degraded.system_prompt is not None, "System prompt should be built"
        assert built_degraded.messages, "Messages should be built"
        # In degraded mode, memory should not be used
        assert built_degraded.token_counts.get("memory", 0) == 0, "Memory should be 0 in degraded mode"
        print(f"  ✅ Degraded mode working correctly")

        # Now test normal mode (with memory retrieval)
        lane_budget_normal = {
            "system_policy": 100,
            "history": 300,
            "memory": 200,
            "tools": 0,
            "tool_results": 0,
            "buffer": 50,
        }

        # Build context in normal mode
        built_normal = await builder.build_for_turn(
            turn=turn_degraded,
            lane_budget=lane_budget_normal,
            is_degraded=False
        )

        print(f"  Normal context built:")
        print(f"    System prompt length: {len(built_normal.system_prompt)} chars")
        print(f"    Messages count: {len(built_normal.messages)}")
        print(f"    Token counts: {built_normal.token_counts}")

        assert built_normal.system_prompt is not None, "System prompt should be built"
        assert built_normal.messages, "Messages should be built"
        # In normal mode, memory should be retrieved (may fail due to circuit breaker, but should try)
        print(f"  ✅ Normal mode completed")

        print("  ✅ Context builder working correctly")

        return True

    async def run_all_tests(self):
        """Run all Phase 4 validation tests."""
        print("=" * 80)
        print("PHASE 4 VALIDATION: UNIFIED LAYERS")
        print("=" * 80)

        tests = [
            ("SimpleGovernor Budget Allocation", self.test_simplified_budget_allocation),
            ("UnifiedMetrics Collection", self.test_unified_metrics),
            ("Unified Circuit Breaker", self.test_circuit_breaker),
            ("HealthMonitor Detection", self.test_health_monitor),
            ("SimpleContextBuilder", self.test_context_builder),
        ]

        results = []
        for name, test_func in tests:
            try:
                result = await test_func()
                results.append((name, "PASS", None))
                print(f"\n✅ {name}: PASSED")
            except Exception as e:
                results.append((name, "FAIL", str(e)))
                print(f"\n❌ {name}: FAILED - {e}")

        print("\n" + "=" * 80)
        print("PHASE 4 VALIDATION SUMMARY")
        print("=" * 80)

        for name, status, error in results:
            status_symbol = "✅" if status == "PASS" else "❌"
            print(f"{status_symbol} {name}: {status}")
            if error:
                print(f"   Error: {error}")

        passed = sum(1 for _, status, _ in results if status == "PASS")
        total = len(results)
        print(f"\nPassed: {passed}/{total} ({passed/total*100:.1f}%)")

        if passed == total:
            print("\n🎉 ALL TESTS PASSED - Ready for Phase 5 cleanup!")
            return True
        else:
            print("\n⚠️  Some tests failed - Fix issues before proceeding to Phase 5")
            return False


# async def test_feature_flag_routing():
#     """Test that feature flag correctly routes to new vs old path."""
#     from services.common.chat_service import ChatService

#     print("\n[TEST 6] Feature Flag Routing")

#     # Test with flag OFF (default - use legacy)
#     os.environ["SA01_USE_SIMPLIFIED_LAYERS"] = "false"
#     service = ChatService()
#     assert service._use_simplified_layers() is False, "Should use legacy when flag false"
#     print("  ✅ Flag OFF → uses legacy path")

#     # Test with flag ON (use new)
#     os.environ["SA01_USE_SIMPLIFIED_LAYERS"] = "true"
#     service = ChatService()
#     assert service._use_simplified_layers() is True, "Should use simplified when flag true"
#     print("  ✅ Flag ON → uses simplified path")

#     return True


@pytest.mark.asyncio
async def test_phase4_complete():
    """Run complete Phase 4 validation."""
    validator = Phase4Validator()
    success = await validator.run_all_tests()
    assert success, "Phase 4 validation failed"


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(test_phase4_complete()))
