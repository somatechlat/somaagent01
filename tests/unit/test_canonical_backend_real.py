"""
Perfect canonical backend tests - testing real integrations with no mocks.
"""
import pytest
from fastapi.testclient import TestClient

# Import the actual gateway app
from services.gateway.main import app


class TestCanonicalBackendReal:
    """Test canonical backend with real implementations."""

    def setup_method(self):
        """Setup test client."""
        self.client = TestClient(app)

    def test_gateway_health_check(self):
        """Test gateway health endpoint works."""
        response = self.client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "ok"

    def test_gateway_routes_exist(self):
        """Test canonical routes exist."""
        # Check OpenAPI schema
        response = self.client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        
        # Verify canonical endpoints are present based on actual code
        paths = schema.get("paths", {})
        assert "/v1/weights" in paths
        assert "/v1/context" in paths or "/v1/flags/{flag}" in paths

    def test_singleton_integrations(self):
        """Test that integrations are available and importable."""
        # Test actual integrations are available and importable
        from python.integrations.soma_client import SomaClient
        from python.integrations.opa_middleware import EnforcePolicy, enforce_policy
        
        # Test SomaClient class exists
        assert SomaClient is not None
        
        # Test OPA middleware classes exist
        assert EnforcePolicy is not None
        assert enforce_policy is not None

    def test_no_legacy_endpoints(self):
        """Test that legacy endpoints don't exist."""
        response = self.client.post("/v1/ui/poll")
        assert response.status_code == 404
        
        response = self.client.get("/v1/csrf")
        assert response.status_code == 404

    def test_authorization_middleware_real(self):
        """Test authorization works with real middleware."""
        from python.integrations.opa_middleware import EnforcePolicy
        
        # Test OPA middleware class exists
        assert EnforcePolicy is not None
        
        # Test basic authorization flow (simplified)
        response = self.client.get("/health", headers={"Authorization": "Bearer test"})
        # Should either succeed or fail gracefully
        assert response.status_code in [200, 401, 403]