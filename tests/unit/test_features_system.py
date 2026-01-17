"""Feature System Unit Tests — Real Logic, In-Memory Cache.

VIBE CODING RULES:
- LocMemCache (Real Django Backend)
- NO mocks
- Pure Logic Validation

Applied Personas:
- QA Engineer: Logic verification
"""

from __future__ import annotations

import pytest
from django.core.cache import cache

from admin.core.features.check import is_feature_enabled
from admin.core.features.registry import FEATURE_REGISTRY

# Configure Django for unit tests if not already done (via conftest?)
# But my conftest in root was removed!
# I need to configure settings here or ensure it runs with minimal settings.
# I'll rely on the fact that I'll run this with a specific configuration if needed,
# or add a minimal setup fixture here.

@pytest.fixture(autouse=True)
def setup_django_settings():
    """Ensure Django is configured with LocMemCache."""
    import django
    from django.conf import settings

    if not settings.configured:
        settings.configure(
            DEBUG=True,
            SECRET_KEY="unit-test",
            CACHES={
                "default": {
                    "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
                    "LOCATION": "unique-snowflake",
                }
            },
            INSTALLED_APPS=[],
        )
        django.setup()
    yield
    cache.clear()

def test_core_feature_enabled_default():
    """Verify chat is enabled."""
    # Chat is core
    assert is_feature_enabled("any-tenant", "chat")

def test_tier_restriction():
    """Verify high tier feature disabled for implicit free tier."""
    # voice_cloning is Team tier. Tenant has no plan in cache -> defaults to free?
    # Wait, check.py uses 'get_tenant_plan' which uses tenant model or cache.
    # checking get_tenant_plan in limits.py:
    # it tries cache, then DB. In LocMem/NoDB env, DB fails?
    # admin/core/budget/limits.py:
    # try: tenant = Tenant.objects.get(...) -> This will fail if no DB access
    # except Tenant.DoesNotExist: return "free"
    # except Exception: return "free"

    # So it should default to "free" safely via exception handling.
    assert not is_feature_enabled("any-tenant", "voice_cloning")

def test_memory_override():
    """Test override mechanism with LocMemCache."""
    tenant = "test_tenant"
    # web_browsing is Starter tier (disabled for free), no dependencies
    assert not is_feature_enabled(tenant, "web_browsing")

    # Apply override
    cache.set(f"feature:override:{tenant}:web_browsing", "true")

    assert is_feature_enabled(tenant, "web_browsing")

def test_dependency_logic():
    """Test dependency resolution."""
    tenant = "test_tenant"
    # learning depends on memory_long_term
    # Override learning=true
    cache.set(f"feature:override:{tenant}:learning", "true")

    # But memory_long_term is disabled (starter tier, tenant is free)
    # So learning should be False
    assert not is_feature_enabled(tenant, "learning")

    # Now enable dependency
    cache.set(f"feature:override:{tenant}:memory_long_term", "true")
    assert is_feature_enabled(tenant, "learning")
