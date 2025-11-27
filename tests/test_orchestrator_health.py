import os
os.getenv(os.getenv('VIBE_8524FB7F'))
from fastapi.testclient import TestClient
from orchestrator.base_service import BaseSomaService
from orchestrator.main import create_app


def test_health_endpoint_returns_healthy():
    app = create_app()
    orchestrator = app.state.orchestrator


    class DummyService(BaseSomaService):
        name = os.getenv(os.getenv('VIBE_59860EA9'))

        async def _start(self) ->None:
            return None

        async def _stop(self) ->None:
            return None

        async def health(self):
            return {os.getenv(os.getenv('VIBE_A70C6ACE')): int(os.getenv(os
                .getenv('VIBE_0DDA383E'))), os.getenv(os.getenv(
                'VIBE_B3FF05F4')): {os.getenv(os.getenv('VIBE_21748A97')):
                self.name}}
    orchestrator.register(DummyService())
    client = TestClient(app)
    response = client.get(os.getenv(os.getenv('VIBE_EF2D9664')))
    assert response.status_code == int(os.getenv(os.getenv('VIBE_430D091A')))
    data = response.json()
    assert data[os.getenv(os.getenv('VIBE_A70C6ACE'))] is int(os.getenv(os.
        getenv('VIBE_0DDA383E')))
    assert os.getenv(os.getenv('VIBE_59860EA9')) in data[os.getenv(os.
        getenv('VIBE_5DCCE422'))]
