"""Budget System Unit Tests — Pure Python (No Django Required).

VIBE CODING RULES:
- NO mocks, NO stubs, NO fakes
- Pure Python logic tests only
- No Django cache or database

Applied Personas:
- QA Engineer: Comprehensive test coverage
- Security Auditor: Fail-closed testing
"""

from __future__ import annotations

from unittest import TestCase

import pytest

from admin.core.budget.registry import (
    METRIC_REGISTRY,
    BudgetedMetric,
    get_metric,
    list_critical_metrics,
    list_metrics,
)
from admin.core.budget.limits import PLAN_LIMITS


class TestMetricRegistry(TestCase):
    """Test metric registry completeness and correctness."""

    def test_all_metrics_defined(self) -> None:
        """Verify all 10 metrics are in registry."""
        expected = {
            "tokens",
            "tool_calls",
            "images",
            "voice_minutes",
            "api_calls",
            "memory_tokens",
            "vector_ops",
            "learning",
            "storage_gb",
            "sessions",
        }
        actual = set(METRIC_REGISTRY.keys())
        assert actual == expected, f"Missing metrics: {expected - actual}"

    def test_metric_immutability(self) -> None:
        """Verify metrics are frozen (immutable)."""
        metric = get_metric("tokens")
        with pytest.raises(AttributeError):
            metric.code = "hacked"  # type: ignore

    def test_get_metric_returns_correct_type(self) -> None:
        """Verify get_metric returns BudgetedMetric."""
        metric = get_metric("tokens")
        assert isinstance(metric, BudgetedMetric)
        assert metric.code == "tokens"

    def test_get_metric_unknown_raises(self) -> None:
        """Verify unknown metric raises KeyError."""
        with pytest.raises(KeyError):
            get_metric("unknown_metric")

    def test_list_metrics_returns_all(self) -> None:
        """Verify list_metrics returns all registry entries."""
        metrics = list_metrics()
        assert len(metrics) == 10

    def test_critical_metrics_are_locked(self) -> None:
        """Verify critical metrics cannot be disabled."""
        for code in ["tokens", "tool_calls", "images", "voice_minutes"]:
            metric = get_metric(code)
            assert metric.tier == "critical", f"{code} should be critical"
            assert not metric.lockable, f"{code} should not be lockable"

    def test_critical_metrics_enforce_pre(self) -> None:
        """Verify critical metrics enforce before action."""
        critical = list_critical_metrics()
        assert len(critical) >= 4
        for metric in critical:
            assert metric.enforce_pre, f"{metric.code} should enforce_pre"


class TestPlanLimits(TestCase):
    """Test plan limit matrix."""

    def test_all_plans_defined(self) -> None:
        """Verify all 4 plans are in PLAN_LIMITS."""
        expected = {"free", "starter", "team", "enterprise"}
        actual = set(PLAN_LIMITS.keys())
        assert actual == expected

    def test_enterprise_has_unlimited(self) -> None:
        """Verify enterprise has unlimited (-1) for some metrics."""
        ent = PLAN_LIMITS["enterprise"]
        unlimited_metrics = [k for k, v in ent.items() if v == -1]
        assert len(unlimited_metrics) >= 5, "Enterprise should have unlimited metrics"

    def test_limits_increase_with_tier(self) -> None:
        """Verify limits increase from free to enterprise."""
        for metric in ["tokens", "images", "tool_calls"]:
            free = PLAN_LIMITS["free"][metric]
            starter = PLAN_LIMITS["starter"][metric]
            team = PLAN_LIMITS["team"][metric]
            # Enterprise may be unlimited (-1)
            assert starter > free, f"{metric}: starter > free"
            assert team > starter, f"{metric}: team > starter"
