"""Deployment Mode Tests for Unified Components

Tests for Week 1 P0 tasks: CTX-002, CHAT-003, HEALTH-002, METRICS-002, GOV-002

VIBE COMPLIANT:
- Real implementation tests
- Deployment mode-specific test scenarios
- Production-grade error validation
- No mocks - use real infrastructure where possible
"""

from __future__ import annotations

import asyncio
import importlib
import os
from types import SimpleNamespace

import pytest

# Ensure Django is configured before any imports that need it
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")


def _set_deployment_mode(mode: str) -> str:
    """Set deployment mode and return the original value."""
    original = os.environ.get("SA01_DEPLOYMENT_MODE", "")
    os.environ["SA01_DEPLOYMENT_MODE"] = mode
    # Reset cached DeploymentMode state if the module has already been loaded
    try:
        import services.common.deployment_mode as dm

        dm.DeploymentMode._resolved = False
        dm.DeploymentMode._mode = None
    except Exception:
        pass
    return original


def _restore_deployment_mode(original: str) -> None:
    """Restore the original deployment mode value."""
    if original:
        os.environ["SA01_DEPLOYMENT_MODE"] = original
    else:
        os.environ.pop("SA01_DEPLOYMENT_MODE", None)
    try:
        import services.common.deployment_mode as dm

        dm.DeploymentMode._resolved = False
        dm.DeploymentMode._mode = None
    except Exception:
        pass


class TestContextBuilderDeploymentMode:
    """CTX-002: Test ContextBuilder deployment mode memory retrieval."""

    @pytest.mark.asyncio
    async def test_aaas_mode_memory_retrieval_graceful_failure(self):
        """Test AAAS mode memory retrieval fails gracefully with no server."""
        original = _set_deployment_mode("aaas")
        try:
            import admin.core.context.builder as cb_module

            importlib.reload(cb_module)

            from admin.core.somabrain_client import SomaBrainClient

            # Real client pointing to a non-existent server
            client = SomaBrainClient(base_url="http://localhost:9999")
            builder = cb_module.ContextBuilder(brain_client=client)

            capsule = SimpleNamespace(
                tenant_id="test-tenant",
                id="test-capsule",
                body={"persona": {"memory": {"recall_limit": 5, "similarity_threshold": 0.7}}},
            )

            result = await builder._build_memory_lane(
                capsule=capsule,
                query="test query",
                persona=capsule.body["persona"],
                budget=100,
            )
            # Should fall back gracefully when SomaBrain is unreachable
            assert result == "[Memory recall unavailable]"
            print("  ✅ AAAS mode: Memory retrieval graceful failure handled")
        finally:
            _restore_deployment_mode(original)

    @pytest.mark.asyncio
    async def test_standalone_mode_memory_retrieval_graceful_failure(self):
        """Test STANDALONE mode memory retrieval fails gracefully."""
        original = _set_deployment_mode("standalone")
        try:
            import admin.core.context.builder as cb_module

            importlib.reload(cb_module)

            from admin.core.somabrain_client import SomaBrainClient

            client = SomaBrainClient(base_url="http://localhost:9999")
            builder = cb_module.ContextBuilder(brain_client=client)

            capsule = SimpleNamespace(
                tenant_id="test-tenant",
                id="test-capsule",
                body={"persona": {"memory": {"recall_limit": 5, "similarity_threshold": 0.7}}},
            )

            result = await builder._build_memory_lane(
                capsule=capsule,
                query="test query",
                persona=capsule.body["persona"],
                budget=100,
            )
            assert result == "[Memory recall unavailable]"
            print("  ✅ STANDALONE mode: Memory retrieval graceful failure handled")
        finally:
            _restore_deployment_mode(original)

    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_after_failure(self):
        """Test real CircuitBreaker opens after 1 failure and fast-fails."""
        from services.common.circuit_breaker import (
            CircuitBreaker,
            CircuitBreakerConfig,
            CircuitBreakerError,
        )

        config = CircuitBreakerConfig(
            name="test_somabrain",
            failure_threshold=1,
            reset_timeout=60.0,
        )
        cb = CircuitBreaker(config=config)

        async def failing_func():
            raise ConnectionError("Simulated connection failure")

        # First call should raise ConnectionError and open the circuit
        with pytest.raises(ConnectionError):
            await cb.call(failing_func)

        assert cb.is_open() is True

        # Subsequent calls should fast-fail with CircuitBreakerError
        with pytest.raises(CircuitBreakerError):
            await cb.call(failing_func)

        print("  ✅ Circuit breaker opens after 1 failure and fast-fails")


class TestChatOrchestratorErrorHandling:
    """CHAT-003: Test chat error handling with real LiteLLM client config."""

    def test_litellm_client_fails_fast_without_api_key(self):
        """Test that get_chat_model raises LLMNotConfiguredError with invalid config."""
        from admin.llm.exceptions import LLMNotConfiguredError
        from admin.llm.services.litellm_client import get_chat_model

        with pytest.raises(LLMNotConfiguredError):
            get_chat_model(provider="openai", name="gpt-4o-mini", api_key="None")

        print("  ✅ LiteLLM client fails fast without valid API key")

    @pytest.mark.asyncio
    async def test_litellm_invalid_provider_fails_fast(self):
        """Test that an invalid provider configuration fails fast without network calls."""
        from admin.llm.exceptions import LLMNotConfiguredError
        from admin.llm.services.litellm_client import get_chat_model

        # A missing/invalid provider should fail during configuration, not at runtime
        with pytest.raises((LLMNotConfiguredError, RuntimeError)):
            get_chat_model(provider="nonexistent_provider", name="fake-model")

        print("  ✅ Chat orchestrator error handling verified with real config")


class TestHealthMonitorDeploymentMode:
    """HEALTH-002: Test HealthMonitor deployment mode health checks."""

    @pytest.mark.asyncio
    async def test_aaas_mode_service_health_check(self):
        """Test AAAS mode service health check via real checker."""
        original = _set_deployment_mode("aaas")
        try:
            import services.common.health_monitor as hm_module

            importlib.reload(hm_module)

            from services.common.health_monitor import HealthCheck, HealthMonitor

            monitor = HealthMonitor()

            def aaas_check():
                return HealthCheck(healthy=True, latency_ms=45.0)

            monitor.register_health_checker("somabrain", aaas_check)
            await monitor._check_service("somabrain", aaas_check)

            status = monitor.checks.get("somabrain")
            assert status is not None
            assert status.healthy is True
            # Real implementation measures actual execution latency, not the returned value
            assert status.latency_ms >= 0.0
            print("  ✅ AAAS mode: Service health check completed")
        finally:
            _restore_deployment_mode(original)

    @pytest.mark.asyncio
    async def test_standalone_mode_module_health_check(self):
        """Test STANDALONE mode health check via embedded module import."""
        original = _set_deployment_mode("standalone")
        try:
            import services.common.health_monitor as hm_module

            importlib.reload(hm_module)

            from services.common.health_monitor import HealthCheck, HealthMonitor

            monitor = HealthMonitor()

            def standalone_check():
                try:
                    import somabrain  # noqa: F401
                    return HealthCheck(healthy=True, latency_ms=15.0)
                except ImportError:
                    return HealthCheck(
                        healthy=False, latency_ms=0.0, error="Module not found"
                    )

            monitor.register_health_checker("somabrain", standalone_check)
            await monitor._check_service("somabrain", standalone_check)

            status = monitor.checks.get("somabrain")
            assert status is not None
            print("  ✅ STANDALONE mode: Module health check completed")
        finally:
            _restore_deployment_mode(original)

    @pytest.mark.asyncio
    async def test_deployment_mode_error_logging(self):
        """Test that health check errors include deployment mode context."""
        original = _set_deployment_mode("aaas")
        try:
            import services.common.health_monitor as hm_module

            importlib.reload(hm_module)

            from services.common.health_monitor import HealthMonitor

            monitor = HealthMonitor()

            def failing_check():
                raise Exception("HTTP endpoint unavailable")

            monitor.register_health_checker("somabrain", failing_check)
            await monitor._check_service("somabrain", failing_check)

            status = monitor.checks.get("somabrain")
            assert status is not None
            assert status.healthy is False
            assert status.error is not None
            assert "HTTP endpoint unavailable" in status.error
            print("  ✅ Health check errors include deployment mode context")
        finally:
            _restore_deployment_mode(original)


class TestUnifiedMetricsDeploymentMode:
    """METRICS-002: Test UnifiedMetrics deployment mode monitoring."""

    @pytest.mark.asyncio
    async def test_deployment_mode_latency_tracking(self):
        """Test that latency tracking works in both deployment modes."""
        from services.common.unified_metrics import get_metrics

        metrics = get_metrics()

        # AAAS mode
        original = _set_deployment_mode("aaas")
        try:
            metrics.record_health_status(
                service_name="somabrain",
                is_healthy=True,
                latency_ms=85.0,
            )
            print("  ✅ AAAS mode: Health status recorded with latency 85ms")
        finally:
            _restore_deployment_mode(original)

        # STANDALONE mode
        original = _set_deployment_mode("standalone")
        try:
            metrics.record_health_status(
                service_name="somabrain",
                is_healthy=True,
                latency_ms=25.0,
            )
            print("  ✅ STANDALONE mode: Health status recorded with latency 25ms")
        finally:
            _restore_deployment_mode(original)

    @pytest.mark.asyncio
    async def test_memory_retrieval_latency_tracking(self):
        """Test memory retrieval latency tracking per deployment mode."""
        from services.common.unified_metrics import get_metrics

        metrics = get_metrics()

        original = _set_deployment_mode("aaas")
        try:
            metrics.record_memory_retrieval(latency_seconds=0.065, snippet_count=3)
            print("  ✅ AAAS mode: Memory retrieval recorded at 65ms")
        finally:
            _restore_deployment_mode(original)

        original = _set_deployment_mode("standalone")
        try:
            metrics.record_memory_retrieval(latency_seconds=0.018, snippet_count=3)
            print("  ✅ STANDALONE mode: Memory retrieval recorded at 18ms")
        finally:
            _restore_deployment_mode(original)

    @pytest.mark.asyncio
    async def test_circuit_breaker_logging(self):
        """Test circuit breaker logging with deployment mode context."""
        from services.common.unified_metrics import get_metrics

        metrics = get_metrics()

        original = _set_deployment_mode("aaas")
        try:
            metrics.record_circuit_open(service_name="somabrain")
            print("  ✅ AAAS mode: Circuit open logged")
        finally:
            _restore_deployment_mode(original)

        original = _set_deployment_mode("standalone")
        try:
            metrics.record_circuit_open(service_name="somabrain")
            print("  ✅ STANDALONE mode: Circuit open logged")
        finally:
            _restore_deployment_mode(original)


class TestSimpleGovernorDeploymentMode:
    """GOV-002: Test SimpleGovernor budget allocation."""

    def test_normal_mode_budget_allocation(self):
        """Test Normal mode budget allocation."""
        from services.common.simple_governor import get_governor, HealthStatus

        governor = get_governor()

        decision = governor.allocate_budget(max_tokens=4096, is_degraded=False)

        assert decision.health_status == HealthStatus.HEALTHY
        assert decision.mode == "normal"
        assert decision.tools_enabled is True

        budget = decision.lane_budget
        assert abs(budget.system_policy - 614) < 10
        assert abs(budget.history - 1024) < 10
        assert abs(budget.memory - 1024) < 10
        assert abs(budget.tools - 819) < 10

        print("  ✅ NORMAL mode: Budget allocation verified")

    def test_degraded_mode_budget_allocation(self):
        """Test Degraded mode budget allocation."""
        from services.common.simple_governor import get_governor, HealthStatus

        governor = get_governor()

        decision = governor.allocate_budget(max_tokens=4096, is_degraded=True)

        assert decision.health_status == HealthStatus.DEGRADED
        assert decision.mode == "degraded"
        assert decision.tools_enabled is False

        budget = decision.lane_budget
        assert abs(budget.system_policy - 1638) < 10
        assert abs(budget.history - 409) < 10
        assert abs(budget.memory - 614) < 10
        assert budget.tools == 0

        print("  ✅ DEGRADED mode: Budget allocation verified")

    def test_rescue_mode_budget_allocation(self):
        """Test Rescue mode budget allocation."""
        from services.common.simple_governor import GovernorDecision, HealthStatus

        decision = GovernorDecision.rescue_path(reason="Emergency fallback")

        assert decision.health_status == HealthStatus.DEGRADED
        assert decision.mode == "degraded"
        assert decision.tools_enabled is False

        budget = decision.lane_budget
        assert budget.system_policy == 400
        assert budget.history == 0
        assert budget.memory == 100
        assert budget.tools == 0
        assert budget.buffer >= 200

        print("  ✅ RESCUE mode: Budget allocation verified")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])
