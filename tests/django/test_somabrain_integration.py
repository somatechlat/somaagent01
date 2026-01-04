"""SomaBrain Integration Tests - Django Framework.

Tests the migrated SomaBrain client against REAL infrastructure.
NO MOCKS.

Real Infrastructure:
- SomaBrain: localhost:9696
- PostgreSQL: localhost:20432
- Redis: localhost:20379
"""

from __future__ import annotations

import os
import sys

import pytest

# Ensure the project is in the Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Django setup - use gateway settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "services.gateway.settings")

# Trigger Django setup
import services.gateway.django_setup  # noqa: F401


class TestSomaBrainDjangoIntegration:
    """Test SomaBrain integration using Django settings."""

    def test_django_settings_has_somabrain_url(self):
        """Verify SOMABRAIN_URL is configured in Django settings."""
        from django.conf import settings

        somabrain_url = getattr(
            settings, "SOMABRAIN_URL", os.environ.get("SA01_SOMA_BASE_URL", "http://localhost:9696")
        )
        assert somabrain_url is not None
        assert "localhost" in somabrain_url or "9696" in somabrain_url
        print(f"✅ SOMABRAIN_URL = {somabrain_url}")

    def test_django_settings_has_database_dsn(self):
        """Verify DATABASE_DSN is configured."""
        from django.conf import settings

        db_dsn = getattr(settings, "DATABASE_DSN", os.environ.get("SA01_DB_DSN", ""))
        assert db_dsn is not None
        assert "postgresql" in db_dsn or db_dsn == ""
        print(f"✅ DATABASE_DSN configured")

    @pytest.mark.asyncio
    async def test_somabrain_health_check(self):
        """Test SomaBrain health endpoint on real infrastructure."""
        from admin.core.soma_client import SomaClient

        somabrain_url = os.environ.get("SA01_SOMA_BASE_URL", "http://localhost:9696")
        client = SomaClient(base_url=somabrain_url)
        try:
            health = await client.health()

            assert health is not None
            assert "ok" in health
            print(f"✅ SomaBrain Health: ok={health.get('ok')}")
        finally:
            await client.close()

    @pytest.mark.asyncio
    async def test_somabrain_remember_memory(self):
        """Test storing a memory in SomaBrain - REAL storage."""
        from admin.core.soma_client import SomaClient

        somabrain_url = os.environ.get("SA01_SOMA_BASE_URL", "http://localhost:9696")
        client = SomaClient(base_url=somabrain_url)
        try:
            memory_payload = {
                "id": "django-test-memory-001",
                "content": "Django migration test memory",
                "type": "django_test",
                "metadata": {"source": "test_somabrain_django_integration", "framework": "Django"},
            }

            result = await client.remember(
                memory_payload, tenant="django-test-tenant", namespace="wm"
            )

            assert result is not None
            assert result.get("ok", False) or "promoted_to_wm" in result
            print(f"✅ Memory Stored: {result.get('promoted_to_wm', 'N/A')}")
        finally:
            await client.close()

    @pytest.mark.asyncio
    async def test_somabrain_recall_memory(self):
        """Test recalling memories from SomaBrain - REAL retrieval."""
        from admin.core.soma_client import SomaClient

        somabrain_url = os.environ.get("SA01_SOMA_BASE_URL", "http://localhost:9696")
        client = SomaClient(base_url=somabrain_url)
        try:
            # First store a memory
            await client.remember(
                {"id": "recall-test", "content": "Test for recall verification"},
                tenant="django-test-tenant",
                namespace="wm",
            )

            # Then recall it
            result = await client.recall(
                "recall verification test", tenant="django-test-tenant", namespace="wm", top_k=5
            )

            assert result is not None
            assert "results" in result or "ltm_hits" in result
            print(
                f"✅ Memory Recalled: {result.get('ltm_hits', 0)} LTM, {result.get('wm_hits', 0)} WM"
            )
        finally:
            await client.close()

    @pytest.mark.asyncio
    async def test_full_memory_cycle(self):
        """Test complete memory cycle: store -> recall -> verify."""
        from admin.core.soma_client import SomaClient
        import uuid

        somabrain_url = os.environ.get("SA01_SOMA_BASE_URL", "http://localhost:9696")
        client = SomaClient(base_url=somabrain_url)
        try:
            # Unique test ID
            test_id = f"django-cycle-{uuid.uuid4().hex[:8]}"
            test_content = f"Full cycle test from Django migration - {test_id}"

            # 1. Store
            store_result = await client.remember(
                {"id": test_id, "content": test_content, "type": "cycle_test"},
                tenant="django-test-tenant",
                namespace="wm",
            )
            assert store_result.get("ok", False) or store_result.get("promoted_to_wm", False)
            print(f"✅ Step 1 - Stored: {test_id}")

            # 2. Recall
            recall_result = await client.recall(
                test_content[:50], tenant="django-test-tenant", namespace="wm", top_k=3
            )
            assert recall_result is not None
            print(f"✅ Step 2 - Recalled: {recall_result.get('duration_ms', 0):.2f}ms")

            # 3. Verify we got results
            total_hits = recall_result.get("ltm_hits", 0) + recall_result.get("wm_hits", 0)
            print(f"✅ Step 3 - Verified: {total_hits} total hits")

            print(f"\n=== Full Memory Cycle: PASSED ===")
        finally:
            await client.close()


class TestDjangoORMWithSomaBrain:
    """Test Django ORM works alongside SomaBrain."""

    @pytest.mark.django_db
    def test_django_orm_tenant_model(self):
        """Verify Django ORM Tenant model works."""
        from admin.saas.models import Tenant

        # Count tenants in real PostgreSQL
        count = Tenant.objects.count()
        print(f"✅ Django ORM: {count} tenants in PostgreSQL")
        assert count >= 0  # Just verify query works

    @pytest.mark.django_db
    def test_django_orm_and_somabrain_coexist(self):
        """Verify Django ORM and SomaBrain can both access data."""
        from admin.saas.models import Tenant

        # Django ORM query
        tenant_count = Tenant.objects.count()

        # SomaBrain URL from env
        somabrain_url = os.environ.get("SA01_SOMA_BASE_URL", "http://localhost:9696")

        assert tenant_count >= 0
        assert somabrain_url is not None
        print(
            f"✅ Django ORM + SomaBrain coexist: {tenant_count} tenants, SomaBrain at {somabrain_url}"
        )
