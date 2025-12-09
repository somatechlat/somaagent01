import pytest
from httpx import AsyncClient

from orchestrator.main import create_app


@pytest.mark.asyncio
async def test_health_endpoint():
    """Smoke test the orchestrator health endpoint."""
    app = create_app()
    async with AsyncClient(app) as client:
        resp = await client.get(f"{os.getenv('HOST','127.0.0.0')}:{os.getenv('GATEWAY_PORT','8000')}/v1/health")
        assert resp.status == 200
        data = await resp.json()
        assert data["healthy"] is True

@pytest.mark.asyncio
async def test_status_endpoint():
    """Smoke test the orchestrator status endpoint."""
    app = create_app()
    async with AsyncClient(app) as client:
        resp = await client.get(f"{os.getenv('HOST','127.0.0.0')}:{os.getenv('GATEWAY_PORT','8000')}/v1/status")
        assert resp.status == 200
        data = await resp.json()
        assert "services" in data

@pytest.mark.asyncio
async def test_shutdown_endpoint():
    """Smoke test the orchestrator shutdown endpoint."""
    app = create_app()
    async with AsyncClient(app) as client:
        resp = await client.post(f"{os.getenv('HOST','127.0.0.0')}:{os.getenv('GATEWAY_PORT','8000')}/v1/shutdown")
        assert resp.status == 200
        data = await resp.json()
        assert data["status"] == "shutting_down"