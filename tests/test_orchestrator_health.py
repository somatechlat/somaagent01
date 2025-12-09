import pytest
from httpx import AsyncClient

from orchestrator.main import create_app


@pytest.mark.asyncio
async def test_health_endpoint():
    """Smoke test the orchestrator health endpoint."""
    # Create a fresh FastAPI application instance.
    app = create_app()
    async with AsyncClient(app) as client:
        resp = await client.get("http://127.0.0.0:8000/v1/health")
        assert resp.status == 200
        data = await resp.json()
        assert "healthy" in data

