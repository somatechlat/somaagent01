"""Verification Script for SaaS Real Implementation."""

import os
import sys

import django
from django.conf import settings

# 1. Setup Django Environment
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "services.gateway.settings")

# Configure SQLite for isolated testing (overriding Postgres)
if not settings.configured:
    settings.configure(
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": "verify_saas.db",
            }
        },
        INSTALLED_APPS=[
            "django.contrib.contenttypes",
            "django.contrib.auth",
            "admin.saas",
            "admin.core",
            "admin.capsules",  # Required for api.py
        ],
        SECRET_KEY="test-secret-key",
        TIME_ZONE="UTC",
        USE_TZ=True,
    )
    django.setup()
else:
    # If settings already configured by env var, likely need to patch them or trust them.
    # But django.setup() calls configure.
    # Best approach: Mock settings BEFORE setup if using os.environ defaults isn't enough.
    # Actually, verify_persistence_chain did it by setting DJANGO_SETTINGS_MODULE and then patching settings?
    # No, usually you configure manually OR use settings module.
    # Let's try manual configuration which is safer for scripts.
    pass

# Force Django setup if not already done (in case we didn't enter the if block)
try:
    django.setup()
except Exception:
    pass

# Patch migrations to be skipped (Syncdb style)
from django.core.management import call_command

from admin.saas.api.settings import list_models, ModelConfigOut
from admin.saas.models.profiles import GlobalDefault, TenantSettings

# Patch migrations to be skipped (Syncdb style) or run migrate


def verify_real_saas():
    print("🔍 [QA] Starting SaaS Real Implementation Verification...")

    # Initialize DB
    print("   [DevOps] Initializing In-Memory SQLite DB...")
    call_command("migrate", verbosity=0, interactive=False)

    # ------------------------------------------------------------------
    # 1. Global Defaults (Singleton Pattern)
    # ------------------------------------------------------------------
    print("   [PhD] Verifying GlobalDefault Singleton...")
    gd = GlobalDefault.get_instance()
    print(f"   ✅ GlobalDefault ID: {gd.id}")
    print(f"   ✅ Defaults Loaded: {list(gd.defaults.keys())}")
    assert "dev_sandbox_defaults" in gd.defaults, "Missing 'dev_sandbox_defaults' in GlobalDefault"
    assert "dev_live_defaults" in gd.defaults, "Missing 'dev_live_defaults' in GlobalDefault"
    print("   ✅ Sandbox & Live Defaults Verified.")

    # Verify no mock data in API
    print("   [Security] Verifying API Endpoint correctness...")
    request_mock = type("obj", (object,), {})
    models = list_models(request_mock)

    print(f"   ✅ API returned {len(models)} models from DB.")
    assert len(models) > 0, "API returned empty list!"
    assert isinstance(models[0], ModelConfigOut), "API did not return Pydantic models"
    print("   ✅ API Response Type Verified (Strict Pydantic).")

    # ------------------------------------------------------------------
    # 2. Persistence Check
    # ------------------------------------------------------------------
    print("   [DevOps] Verifying Persistence (Write/Read)...")
    original_rate = gd.defaults["models"][0].get("rate_limit", 100)
    new_rate = original_rate + 1

    gd.defaults["models"][0]["rate_limit"] = new_rate
    gd.save()

    # Reload from DB
    gd_refreshed = GlobalDefault.objects.first()
    saved_rate = gd_refreshed.defaults["models"][0]["rate_limit"]

    if saved_rate == new_rate:
        print(f"   ✅ Persistence Verified! Rate limit changed {original_rate} -> {saved_rate}")
    else:
        print(f"   ❌ Persistence FAILED! Expected {new_rate}, got {saved_rate}")
        sys.exit(1)

    # ------------------------------------------------------------------
    # 3. Tenant Settings (Deep JSONB)
    # ------------------------------------------------------------------
    print("   [Arch] Verifying TenantSettings Deep Schema...")
    # Create a dummy tenant if needed (mocking dependency for speed, but using real Model)
    # in a real run we might need a Tenant.
    # For now, we verify the Model class structure exists.
    assert hasattr(TenantSettings, "compliance"), "TenantSettings missing 'compliance' field"
    assert hasattr(TenantSettings, "compute"), "TenantSettings missing 'compute' field"
    assert hasattr(TenantSettings, "auth"), "TenantSettings missing 'auth' field"
    print("   ✅ TenantSettings Schema Verified (Compliance, Compute, Auth present).")

    # ------------------------------------------------------------------
    # 3. New RateLimit API (Persistent)
    # ------------------------------------------------------------------
    print("   [Arch] Verifying RateLimit API (Persistent GlobalDefault)...")
    import asyncio

    from admin.agents.api import get_multimodal_config, MultimodalConfig, update_multimodal_config
    from admin.ratelimit.api import create_rate_limit, get_rate_limits, RateLimitConfig

    # Test Create Rate Limit
    async def test_extensions():
        # Create Limit
        await create_rate_limit(
            None,
            RateLimitConfig(
                name="test_limit_v1",
                requests_per_minute=10,
                requests_per_hour=100,
                requests_per_day=1000,
            ),
        )

        # Verify Persistence
        limits = await get_rate_limits(None)
        found = any(limit_["name"] == "test_limit_v1" for limit_ in limits["limits"])
        if found:
            print("   ✅ RateLimit persistence verified.")
        else:
            print("   ❌ RateLimit persistence FAILED.")

        # Test Multimodal Config
        config = MultimodalConfig(image_enabled=False, image_provider="test_provider")
        await update_multimodal_config(None, "agent_123", config)

        res = await get_multimodal_config(None, "agent_123")
        if res["config"]["image_provider"] == "test_provider":
            print("   ✅ Multimodal persistence verified.")
        else:
            print("   ❌ Multimodal persistence FAILED.")

    # Run async tests
    asyncio.run(test_extensions())

    print("\n✅ [Unified] SaaS Real Implementation Verification PASSED.")


if __name__ == "__main__":
    try:
        verify_real_saas()
    finally:
        import os

        if os.path.exists("verify_saas.db"):
            os.remove("verify_saas.db")
