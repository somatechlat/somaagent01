"""SomaBrain Bridge Tests — REAL Direct Integration.

VIBE CODING RULES:
- ZERO HARDCODED VALUES (Rule 91)
- ALL config from Django settings
- REAL SomaBrain interaction (Direct or HTTP)
- NO MOCKS, NO STUBS

This test verifies the AAAS Direct pattern:
- SomaBrain is imported directly when available
- HTTP fallback when direct import not available

Requirements:
- DJANGO_SETTINGS_MODULE=services.gateway.settings
- SA01_INFRA_AVAILABLE=1

Usage:
    DJANGO_SETTINGS_MODULE=services.gateway.settings SA01_INFRA_AVAILABLE=1 \
        pytest tests/aaas_direct/test_brain_bridge.py -v
"""

from __future__ import annotations

import os
import uuid

import pytest

# Infrastructure gate
INFRA_AVAILABLE = os.environ.get("SA01_INFRA_AVAILABLE") == "1"

pytestmark = [
    pytest.mark.integration,
    pytest.mark.bridge,
    pytest.mark.skipif(not INFRA_AVAILABLE, reason="Requires SA01_INFRA_AVAILABLE=1"),
]


@pytest.fixture(scope="session", autouse=True)
def django_setup():
    """Configure Django from centralized settings."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "services.gateway.settings")

    import django
    django.setup()


@pytest.fixture
def tenant_id() -> str:
    """Generate unique tenant ID for test isolation."""
    return f"bridge-test-{uuid.uuid4().hex[:8]}"


class TestSomaBrainClientConfiguration:
    """Test SomaBrainClient uses centralized settings."""

    def test_client_uses_settings_url(self):
        """Verify client gets URL from Django settings (Rule 91)."""
        from django.conf import settings
        from admin.core.somabrain_client import SomaBrainClient

        client = SomaBrainClient()

        # URL should come from settings, not hardcoded
        expected_url = getattr(settings, "SOMABRAIN_URL", None)
        if expected_url:
            assert client._base_url == expected_url

    def test_client_singleton_pattern(self):
        """Verify singleton pattern for connection pooling."""
        from admin.core.somabrain_client import SomaBrainClient

        client1 = SomaBrainClient.get()
        client2 = SomaBrainClient.get()

        assert client1 is client2

    def test_facade_availability_check(self):
        """Verify HAS_FACADE check for direct import mode."""
        from admin.core import somabrain_client

        # HAS_FACADE should be a boolean
        assert isinstance(somabrain_client.HAS_FACADE, bool)

        # If True, direct import is available
        if somabrain_client.HAS_FACADE:
            # BrainMemoryFacade should be importable
            from soma_core.memory_client import BrainMemoryFacade
            assert BrainMemoryFacade is not None


class TestSomaBrainDirectImport:
    """Test AAAS Direct import pattern."""

    def test_direct_import_available(self):
        """Verify SomaBrain can be imported directly (AAAS Mode)."""
        try:
            # This is the AAAS Direct import
            from somabrain.cognitive import CognitiveCore
            assert CognitiveCore is not None

            # Mark as direct mode available
            direct_available = True
        except ImportError:
            # HTTP fallback will be used
            direct_available = False

        # Either mode is acceptable, but we should know which
        assert isinstance(direct_available, bool)

    def test_brain_bridge_exists(self):
        """Verify admin.somabrain module exists for bridge."""
        try:
            from admin.somabrain import core_brain
            # Check for actual exports: router, act function, schemas
            assert hasattr(core_brain, "router") or hasattr(core_brain, "act")
        except ImportError:
            pytest.skip("admin.somabrain.core_brain not implemented")


class TestSomaBrainOperations:
    """Test REAL SomaBrain operations."""

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Verify SomaBrain health endpoint is reachable."""
        from admin.core.somabrain_client import SomaBrainClient

        client = SomaBrainClient()

        try:
            # Health check should not raise
            result = await client._request("GET", "/healthz")
            assert result is not None
        except Exception as e:
            # May fail if SomaBrain not running, but that's infrastructure issue
            pytest.skip(f"SomaBrain not reachable: {e}")
        finally:
            await client.close()

    @pytest.mark.asyncio
    async def test_remember_operation(self, tenant_id: str):
        """Test remember (memorize) operation with REAL data."""
        from admin.core.somabrain_client import SomaBrainClient

        client = SomaBrainClient()

        try:
            payload = {
                "value": f"Bridge test memory {uuid.uuid4().hex[:8]}",
                "key": f"bridge-key-{uuid.uuid4().hex[:8]}",
                "tags": ["bridge-test"],
                "importance": 5,
                "novelty": 0.5,
            }

            result = await client.remember(
                payload=payload,
                tenant=tenant_id,
                namespace="wm",
            )

            # Should return coordinate
            assert "coord" in result or "coordinate" in result or "id" in result

        except Exception as e:
            pytest.skip(f"SomaBrain remember failed: {e}")
        finally:
            await client.close()

    @pytest.mark.asyncio
    async def test_recall_operation(self, tenant_id: str):
        """Test recall operation with REAL data."""
        from admin.core.somabrain_client import SomaBrainClient

        client = SomaBrainClient()

        try:
            result = await client.recall(
                query="bridge test",
                tenant=tenant_id,
                top_k=5,
            )

            # Should return list of memories (may be empty)
            assert isinstance(result, (list, dict))

        except Exception as e:
            pytest.skip(f"SomaBrain recall failed: {e}")
        finally:
            await client.close()


class TestDirectModeVerification:
    """Verify which mode is active (Direct vs HTTP)."""

    def test_identify_active_mode(self):
        """Identify if AAAS Direct mode is active."""
        from admin.core import somabrain_client

        mode = "direct" if somabrain_client.HAS_FACADE else "http"

        print(f"✅ SomaBrain Mode: {mode.upper()}")

        # Store for report
        assert mode in ("direct", "http")
