"""Integration test for the FastAPI health endpoint.

The gateway registers a tiny ``/v1/health`` route via the ``src.gateway.routers.health``
router. This test spins up the FastAPI app with a ``TestClient`` and verifies that the
endpoint returns a 200 status and the expected JSON payload.
"""

import os

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
    # Basic sanity checks – the payload must contain the keys we set.
    assert data.get("status") == "ok"
    assert data.get("service") == "gateway"
    # The deployment mode should reflect the env var or default to "development".
    expected_mode = os.getenv("DEPLOYMENT_MODE", "development")
    assert data.get("deployment_mode") == expected_mode
