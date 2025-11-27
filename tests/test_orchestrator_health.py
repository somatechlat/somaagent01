import os

os.getenv(os.getenv(""))
from fastapi.testclient import TestClient

from orchestrator.base_service import BaseSomaService
from orchestrator.main import create_app


def test_health_endpoint_returns_healthy():
    app = create_app()
    orchestrator = app.state.orchestrator

    class DummyService(BaseSomaService):
        name = os.getenv(os.getenv(""))

        async def _start(self) -> None:
            return None

        async def _stop(self) -> None:
            return None

        async def health(self):
            return {
                os.getenv(os.getenv("")): int(os.getenv(os.getenv(""))),
                os.getenv(os.getenv("")): {os.getenv(os.getenv("")): self.name},
            }

    orchestrator.register(DummyService())
    client = TestClient(app)
    response = client.get(os.getenv(os.getenv("")))
    assert response.status_code == int(os.getenv(os.getenv("")))
    data = response.json()
    assert data[os.getenv(os.getenv(""))] is int(os.getenv(os.getenv("")))
    assert os.getenv(os.getenv("")) in data[os.getenv(os.getenv(""))]
