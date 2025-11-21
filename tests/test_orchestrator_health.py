"""Integration test for the orchestrator /v1/health endpoint.

Validates the single-entry orchestrator wiring:
* ``create_app`` attaches the orchestrator to ``app.state.orchestrator``.
* Services registered on that orchestrator are surfaced by ``/v1/health``.
"""

from fastapi.testclient import TestClient

from orchestrator.base_service import BaseSomaService
from orchestrator.main import create_app


def test_health_endpoint_returns_healthy():
    # Create the orchestrator app and fetch the instance attached to app.state.
    app = create_app()
    orchestrator = app.state.orchestrator

    class DummyService(BaseSomaService):
        name = "dummy"

        async def _start(self) -> None:  # pragma: no cover – trivial
            return None

        async def _stop(self) -> None:  # pragma: no cover – trivial
            return None

        async def health(self):  # pragma: no cover – exercised via endpoint
            return {"healthy": True, "details": {"name": self.name}}

    orchestrator.register(DummyService())

    client = TestClient(app)
    response = client.get("/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["healthy"] is True
    assert "dummy" in data["services"]
