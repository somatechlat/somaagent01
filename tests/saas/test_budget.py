"""Budget System Integration Tests — REAL Infrastructure.

VIBE CODING RULES:
- ZERO HARDCODED VALUES (Rule 91)
- ALL config from Django settings (services.gateway.settings)
- NO mocks, NO stubs, NO fakes

Requirements:
- DJANGO_SETTINGS_MODULE=services.gateway.settings
- SA01_INFRA_AVAILABLE=1 environment variable
- Docker services running

Usage:
    DJANGO_SETTINGS_MODULE=services.gateway.settings SA01_INFRA_AVAILABLE=1 \
        pytest tests/aaas_direct/test_budget.py -v
"""

from __future__ import annotations

import os
import uuid

import pytest

# Skip all tests if infrastructure not available
INFRA_AVAILABLE = os.environ.get("SA01_INFRA_AVAILABLE") == "1"

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not INFRA_AVAILABLE, reason="Requires SA01_INFRA_AVAILABLE=1"),
]


@pytest.fixture(scope="session", autouse=True)
def django_setup():
    """Configure Django from centralized settings.

    NO HARDCODED VALUES. Uses services.gateway.settings which
    loads DB/Redis URLs from environment variables.
    """
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "services.gateway.settings")

    import django
    django.setup()


@pytest.fixture
def tenant_id() -> str:
    """Generate unique tenant ID for test isolation."""
    return f"test-tenant-{uuid.uuid4().hex[:8]}"


class TestBudgetLimitsCacheIntegration:
    """Test budget limits with REAL Redis cache."""

    def test_get_current_usage_starts_at_zero(self, tenant_id: str) -> None:
        """Verify new tenant starts with 0 usage."""
        from admin.core.budget.limits import get_current_usage

        usage = get_current_usage(tenant_id, "tokens")
        assert usage == 0

    def test_increment_usage_increases_count(self, tenant_id: str) -> None:
        """Verify increment_usage increases count correctly."""
        from admin.core.budget.limits import get_current_usage, increment_usage

        increment_usage(tenant_id, "tokens", 100)
        usage = get_current_usage(tenant_id, "tokens")
        assert usage == 100

    def test_increment_usage_is_additive(self, tenant_id: str) -> None:
        """Verify multiple increments are additive."""
        from admin.core.budget.limits import get_current_usage, increment_usage

        increment_usage(tenant_id, "tokens", 100)
        increment_usage(tenant_id, "tokens", 50)
        increment_usage(tenant_id, "tokens", 25)
        usage = get_current_usage(tenant_id, "tokens")
        assert usage == 175

    def test_check_budget_available_true(self, tenant_id: str) -> None:
        """Verify budget is available when under limit."""
        from admin.core.budget.limits import check_budget_available

        assert check_budget_available(tenant_id, "tokens", 1000)

    def test_check_budget_available_false_when_exceeded(self, tenant_id: str) -> None:
        """Verify budget is blocked when exceeded."""
        from django.core.cache import cache

        from admin.core.budget.limits import check_budget_available

        cache.set(f"limit:{tenant_id}:tokens", 100)
        cache.set(f"usage:{tenant_id}:tokens", 100)
        assert not check_budget_available(tenant_id, "tokens", 1)

    def test_get_budget_remaining(self, tenant_id: str) -> None:
        """Verify remaining budget calculation."""
        from django.core.cache import cache

        from admin.core.budget.limits import get_budget_remaining

        cache.set(f"limit:{tenant_id}:tokens", 1000)
        cache.set(f"usage:{tenant_id}:tokens", 300)
        remaining = get_budget_remaining(tenant_id, "tokens")
        assert remaining == 700


class TestBudgetExceptionsIntegration:
    """Test budget exceptions with Django configured."""

    def test_budget_exhausted_has_402_status(self) -> None:
        """Verify BudgetExhaustedError has HTTP 402."""
        from admin.core.budget.exceptions import BudgetExhaustedError

        exc = BudgetExhaustedError(
            tenant_id="test",
            metric="tokens",
            usage=10000,
            limit=10000,
        )
        assert exc.http_status == 402

    def test_budget_exhausted_to_dict(self) -> None:
        """Verify to_dict() returns complete data."""
        from admin.core.budget.exceptions import BudgetExhaustedError

        exc = BudgetExhaustedError(
            tenant_id="test",
            metric="tokens",
            usage=10000,
            limit=10000,
        )
        d = exc.to_dict()
        assert d["error"] == "budget_exhausted"
        assert d["metric"] == "tokens"
        assert d["usage"] == 10000
        assert d["limit"] == 10000
        assert d["http_status"] == 402

    def test_metric_not_found_error(self) -> None:
        """Verify MetricNotFoundError message."""
        from admin.core.budget.exceptions import MetricNotFoundError

        exc = MetricNotFoundError("unknown")
        assert "unknown" in str(exc)

    def test_budget_check_error(self) -> None:
        """Verify BudgetCheckError captures context."""
        from admin.core.budget.exceptions import BudgetCheckError

        exc = BudgetCheckError("tenant-1", "tokens", "Redis down")
        assert "tenant-1" in str(exc)
        assert "tokens" in str(exc)
        assert "Redis down" in str(exc)
