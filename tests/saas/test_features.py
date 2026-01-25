"""Feature Flags Integration Tests — REAL Infrastructure.

VIBE CODING RULES:
- ZERO HARDCODED VALUES (Rule 91)
- ALL config from Django settings (services.gateway.settings)
- NO mocks, NO stubs, NO fakes

Requirements:
- DJANGO_SETTINGS_MODULE=services.gateway.settings
- SA01_INFRA_AVAILABLE=1
- Docker services running

Usage:
    DJANGO_SETTINGS_MODULE=services.gateway.settings SA01_INFRA_AVAILABLE=1 \
        pytest tests/aaas_direct/test_features.py -v
"""

from __future__ import annotations

import os
import uuid

import pytest
from django.http import HttpRequest

# Skip if infrastructure not available
INFRA_AVAILABLE = os.environ.get("SA01_INFRA_AVAILABLE") == "1"

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not INFRA_AVAILABLE, reason="Requires SA01_INFRA_AVAILABLE=1"),
]


@pytest.fixture(scope="session", autouse=True)
def django_setup():
    """Configure Django from centralized settings.

    NO HARDCODED VALUES. Uses services.gateway.settings.
    """
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "services.gateway.settings")

    import django
    django.setup()


@pytest.fixture
def tenant_id() -> str:
    """Generate unique tenant ID."""
    return f"test-tenant-{uuid.uuid4().hex[:8]}"


@pytest.fixture
def clean_cache():
    """Clear cache before/after test."""
    from django.core.cache import cache
    cache.clear()
    yield
    cache.clear()


class TestFeatureIntegration:
    """Integration checks for Feature Flags system."""

    def test_core_feature_enabled_by_default(self, tenant_id: str):
        """Verify core features are enabled for any tenant."""
        from admin.core.features.check import is_feature_enabled

        assert is_feature_enabled(tenant_id, "chat")

    def test_high_tier_feature_disabled_for_default_tenant(self, tenant_id: str):
        """Verify team feature is disabled for default (free) tenant."""
        from admin.core.features.check import is_feature_enabled

        assert not is_feature_enabled(tenant_id, "voice_cloning")

    def test_redis_override_enables_feature(self, tenant_id: str, clean_cache):
        """Verify Redis override forces feature ON."""
        from django.core.cache import cache
        from admin.core.features.check import is_feature_enabled

        assert not is_feature_enabled(tenant_id, "web_browsing")

        key = f"feature:override:{tenant_id}:web_browsing"
        cache.set(key, "true")

        assert is_feature_enabled(tenant_id, "web_browsing")

    def test_redis_override_disables_feature(self, tenant_id: str, clean_cache):
        """Verify Redis override forces feature OFF."""
        from django.core.cache import cache
        from admin.core.features.check import is_feature_enabled

        assert is_feature_enabled(tenant_id, "chat")

        key = f"feature:override:{tenant_id}:chat"
        cache.set(key, "false")

        assert not is_feature_enabled(tenant_id, "chat")

    def test_dependency_chain_enforcement(self, tenant_id: str, clean_cache):
        """Verify dependencies are checked."""
        from django.core.cache import cache
        from admin.core.features.check import is_feature_enabled

        cache.set(f"feature:override:{tenant_id}:learning", "true")

        assert not is_feature_enabled(tenant_id, "learning")

        cache.set(f"feature:override:{tenant_id}:memory_long_term", "true")

        assert is_feature_enabled(tenant_id, "learning")


class TestFeatureGateIntegration:
    """Test @require_feature decorator."""

    def test_gate_allows_access(self, tenant_id: str):
        """Verify gate allows access when enabled."""
        from admin.core.features.gate import require_feature

        @require_feature("chat")
        def protected_view(request):
            return "ok"

        req = HttpRequest()
        req.user = type("User", (), {"is_authenticated": True, "active_tenant_id": tenant_id})()

        assert protected_view(req) == "ok"

    def test_gate_denies_access(self, tenant_id: str):
        """Verify gate raises FeatureDisabledError when disabled."""
        from admin.core.features.gate import require_feature
        from admin.core.features.exceptions import FeatureDisabledError

        @require_feature("voice_cloning")
        def protected_view(request):
            return "ok"

        req = HttpRequest()
        req.user = type("User", (), {"is_authenticated": True, "active_tenant_id": tenant_id})()

        with pytest.raises(FeatureDisabledError) as exc:
            protected_view(req)

        assert exc.value.http_status == 403
        assert exc.value.feature_code == "voice_cloning"
