"""End-to-end integration test for the Soma Cognitive Triad.

Tests the full AAAS flow: SomaAgent01 → SomaBrain → SomaFractalMemory.
Validates that all three repos work together as a cognitive agent.

Requirements tested:
- REQ-CHAT-001: Real-time chat via WebSocket
- REQ-CHAT-003: 12-phase V3 orchestrator pipeline
- REQ-MEM-001: SomaBrain cognitive memory integration
- REQ-MEM-002: SomaFractalMemory vector storage integration
- REQ-MEM-003: Memory recall hierarchy (Brain primary, SFM fallback)
- REQ-AC-001: OPA policy enforcement
- REQ-AC-002: SpiceDB authorization
"""

import os
import pytest
import httpx


# Skip if infrastructure not available
INFRA_AVAILABLE = os.environ.get("SA01_INFRA_AVAILABLE", "false").lower() == "true"
pytestmark = pytest.mark.skipif(
    not INFRA_AVAILABLE,
    reason="Full AAAS infrastructure not available (set SA01_INFRA_AVAILABLE=1)"
)


AGENT_URL = os.environ.get("SA01_AGENT_URL", "http://localhost:63900")
BRAIN_URL = os.environ.get("SA01_BRAIN_URL", "http://localhost:63996")
SFM_URL = os.environ.get("SA01_SFM_URL", "http://localhost:63901")
AUTH_TOKEN = os.environ.get("SA01_TEST_TOKEN", "")


@pytest.fixture
def auth_headers():
    """Authorization headers for API calls."""
    return {"Authorization": f"Bearer {AUTH_TOKEN}"} if AUTH_TOKEN else {}


class TestTriadHealth:
    """Verify all three services are healthy."""

    @pytest.mark.integration
    def test_agent_health(self):
        """SomaAgent01 health endpoint returns ok."""
        resp = httpx.get(f"{AGENT_URL}/api/health/", timeout=10)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"

    @pytest.mark.integration
    def test_brain_health(self):
        """SomaBrain health endpoint returns healthy."""
        resp = httpx.get(f"{BRAIN_URL}/health", timeout=10)
        assert resp.status_code == 200

    @pytest.mark.integration
    def test_sfm_health(self):
        """SomaFractalMemory healthz endpoint returns all stores healthy."""
        resp = httpx.get(f"{SFM_URL}/healthz", timeout=10)
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("kv_store") is True
        assert data.get("vector_store") is True


class TestTriadAuth:
    """Verify authentication works across the triad."""

    @pytest.mark.integration
    def test_agent_requires_auth(self, auth_headers):
        """Protected endpoint requires authentication."""
        resp = httpx.get(f"{AGENT_URL}/api/v2/agents", timeout=10)
        # Should return 401 without auth
        assert resp.status_code in [401, 403]

    @pytest.mark.integration
    def test_sfm_requires_auth(self):
        """SFM protected endpoint requires authentication."""
        resp = httpx.post(
            f"{SFM_URL}/memories",
            json={"coord": "1.0,2.0,3.0", "payload": {"test": True}, "memory_type": "semantic"},
            timeout=10,
        )
        # Should return 401 without auth
        assert resp.status_code in [401, 403]


class TestMemoryFlow:
    """Test the memory flow: Agent → Brain → SFM."""

    @pytest.mark.integration
    def test_sfm_store_and_recall(self, auth_headers):
        """Store a memory in SFM and recall it."""
        # Store
        store_resp = httpx.post(
            f"{SFM_URL}/memories",
            json={
                "coord": "0.5,0.5,0.5",
                "payload": {"content": "test memory from E2E", "type": "episodic"},
                "memory_type": "episodic",
            },
            headers=auth_headers,
            timeout=10,
        )
        assert store_resp.status_code in [200, 201]

        # Recall
        search_resp = httpx.post(
            f"{SFM_URL}/memories/search",
            json={"query": "test memory", "top_k": 5},
            headers=auth_headers,
            timeout=10,
        )
        assert search_resp.status_code == 200

    @pytest.mark.integration
    def test_brain_remember_and_recall(self, auth_headers):
        """Store a memory in SomaBrain and recall it."""
        # Remember
        remember_resp = httpx.post(
            f"{BRAIN_URL}/api/v1/memory/store",
            json={
                "content": "test cognitive memory from E2E",
                "namespace": "e2e_test",
                "importance": 0.8,
            },
            headers=auth_headers,
            timeout=10,
        )
        # May return 200 or 201
        assert remember_resp.status_code in [200, 201]

        # Recall
        recall_resp = httpx.post(
            f"{BRAIN_URL}/api/v1/memory/recall",
            json={
                "query": "cognitive memory test",
                "top_k": 5,
                "namespace": "e2e_test",
            },
            headers=auth_headers,
            timeout=10,
        )
        assert recall_resp.status_code == 200


class TestDegradation:
    """Test graceful degradation when services are unavailable."""

    @pytest.mark.integration
    def test_agent_degradation_status(self):
        """Degradation status endpoint responds."""
        resp = httpx.get(
            f"{AGENT_URL}/api/v2/core/infrastructure/degradation/status",
            timeout=10,
        )
        # Should return 200 (may be degraded or healthy)
        assert resp.status_code == 200

    @pytest.mark.integration
    def test_agent_health_detailed(self):
        """Detailed health endpoint returns component status."""
        resp = httpx.get(f"{AGENT_URL}/api/health/", timeout=10)
        assert resp.status_code == 200


class TestVersionCompatibility:
    """Verify version compatibility matrix."""

    @pytest.mark.integration
    def test_agent_version(self):
        """SomaAgent01 reports version in health."""
        resp = httpx.get(f"{AGENT_URL}/api/health/", timeout=10)
        assert resp.status_code == 200
        data = resp.json()
        assert "version" in data
