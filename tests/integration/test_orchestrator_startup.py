# tests/integration/test_orchestrator_startup.py

from fastapi.testclient import TestClient

from orchestrator.main import create_app


def test_orchestrator_starts_services_and_reports_health():
    """
    Tests that the orchestrator can be initialized, start the registered
    services, and report a healthy status via the /v1/health endpoint.
    This test uses the real services registered in create_app.
    """
    app = create_app()
    client = TestClient(app)

    # The first request will trigger the lifespan startup event
    response = client.get("/v1/health")

    assert response.status_code == 200
    data = response.json()

    assert data["healthy"] is True
    assert "services" in data

    # Check for the real services
    assert "gateway" in data["services"]
    assert "memory" in data["services"]
