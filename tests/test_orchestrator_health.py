"""Basic integration test for the orchestrator health endpoint.

The test spins up a minimal FastAPI app using the ``SomaOrchestrator`` and a
dummy ``BaseSomaService`` implementation that always reports healthy. It then
issues a GET request to ``/v1/health`` and asserts that the response indicates
overall health ``true`` and contains the dummy service entry.
"""

from fastapi.testclient import TestClient

from orchestrator.base_service import BaseSomaService
from orchestrator.main import create_app


class DummyService(BaseSomaService):
    name = "dummy"

    async def _start(self) -> None:  # pragma: no cover – trivial
        pass

    async def _stop(self) -> None:  # pragma: no cover – trivial
        pass

    async def health(self):  # pragma: no cover – exercised via endpoint
        return {"healthy": True, "details": {"name": self.name}}


def test_health_endpoint_returns_healthy():
    # Create the orchestrator app and register the dummy service.
    app = create_app()
    # The orchestrator registers services during create_app; we manually add our dummy.
    # Retrieve the orchestrator instance from the app's state (registered in create_app).
    # The orchestrator is attached via ``orchestrator.attach()`` which mounts the health router.
    # We can directly register the dummy service using the orchestrator's register method.
    from orchestrator.orchestrator import SomaOrchestrator

    # Access the orchestrator instance that was created inside ``create_app``.
    # ``create_app`` does not expose it, so we instantiate a new orchestrator for the test.
    orchestrator = SomaOrchestrator(app)
    orchestrator.register(DummyService())
    orchestrator.attach()

    client = TestClient(app)
    response = client.get("/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["healthy"] is True
    assert "dummy" in data["services"]
