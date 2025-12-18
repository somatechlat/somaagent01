"""Simplified integration test for Multimodal API routes.

VIBE COMPLIANCE: Tests multimodal router logic directly without full Gateway app import.
Avoids faiss/transformers import conflicts on macOS.
"""

import os
import pytest
from uuid import uuid4

# Direct router testing without full app import
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture
def multimodal_app():
    """Create minimal FastAPI app with just multimodal router."""
    app = FastAPI()
    
    # Import and register multimodal router
    from services.gateway.routers.multimodal import router
    app.include_router(router)
    
    return app


def test_multimodal_get_plan_404_direct(multimodal_app):
    """Test GET /multimodal/plans/{id} returns 404 for non-existent plan.
    
    VIBE: Tests against real JobPlanner (via dependency injection).
    """
    client = TestClient(multimodal_app)
    
    fake_id = str(uuid4())
    response = client.get(f"/multimodal/plans/{fake_id}")

    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_multimodal_get_asset_404_direct(multimodal_app):
    """Test GET /multimodal/assets/{id} returns 404 for non-existent asset.
    
    VIBE: Tests against real AssetStore.
    """
    client = TestClient(multimodal_app)
    
    fake_id = str(uuid4())
    response = client.get(f"/multimodal/assets/{fake_id}")
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_multimodal_generate_invalid_plan(multimodal_app):
    """Test POST /multimodal/generate rejects invalid plan.
    
    VIBE: Tests error handling.
    """
    client = TestClient(multimodal_app)
    
    # Invalid plan (missing required fields)
    response = client.post(
        "/multimodal/generate",
        json={
            "plan": {},  # Empty plan
            "tenant_id": str(uuid4()),
            "session_id": str(uuid4())
        }
    )
    
    # Should fail with 400 or 500
    assert response.status_code in [400, 500], f"Expected 400 or 500, got {response.status_code}"
