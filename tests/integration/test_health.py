"""Integration test for the FastAPI health endpoint.

The gateway exposes the production health router under ``/v1/health``. This test
spins up the FastAPI app with a ``TestClient`` and verifies that the endpoint
returns a 200 status and the expected JSON payload shape.
"""

import pytest
from fastapi.testclient import TestClient

# Import the FastAPI app defined in the gateway service.
from services.gateway.main import app


@pytest.mark.integration
def test_health_endpoint() -> None:
    """Ensure the health endpoint returns a successful payload."""
    client = TestClient(app)
    response = client.get("/v1/health")
    assert response.status_code == 200, "Health endpoint should be reachable"
    data = response.json()
    # Basic sanity checks – the payload must contain the keys exposed by the router.
    assert data.get("status") in {"ok", "degraded", "down"}
    assert isinstance(data.get("components"), dict)
