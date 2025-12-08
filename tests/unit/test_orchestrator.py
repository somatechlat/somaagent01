"""Unit tests for the orchestrator lifecycle.

This file contains a small smoke test that verifies the three public endpoints
(`/v1/health`, `/v1/status`, `/v1/shutdown`) are reachable and return the expected
status codes.  It uses the fixture defined in ``tests/conftest.py`` so the URLs are
configurable.
"""

import pytest
from httpx import AsyncClient
from orchestrator.main import create_app


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient, base_url: str):
    """Test the health endpoint returns 200 and a JSON key."""
    resp = await client.get(f"{base_url}/v1/health")
    assert resp.status == 200
    data = await resp.json()
    assert data["healthy"] is True

@pytest.mark.asyncio
async def test_status_endpoint(client: AsyncClient, base_url: str):
    """Test the status endpoint returns 200 and a JSON key."""
    resp = await client.get(f"{base_url}/v1/status")
    assert resp.status == 200
    data = await resp.json()
    assert "services" in data

@pytest.mark.asyncio
async def test_shutdown_endpoint(client: AsyncClient, base_url: str):
    """Test the shutdown endpoint returns 200 and a JSON key."""
    resp = await client.post(f"{base_url}/v1/shutdown")
    assert resp.status == 200
    data = await resp.json()
    assert data["status"] == "shutting_down"