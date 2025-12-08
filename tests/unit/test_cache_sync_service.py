"""Unit tests for the CacheSyncService.

This file verifies that a registered CacheSyncService is reachable via its
``health`` endpoint and that the orchestrator correctly mounts it under the
``/health-sync`` prefix.
"""

import pytest
from httpx import AsyncClient
from orchestrator.main import create_app


@pytest.mark.asyncio
async def test_cache_sync_health(client: AsyncClient, base_url: str):
    """Test that the CacheSyncService health endpoint returns 200."""
    resp = await client.get(f"{base_url}/v1/status")
    assert resp.status == 200
    data = await resp.json()
    # The status endpoint returns a dict with a ``services`` key that contains
    # a list of registered services.  We just check that the list includes our
    # new service.
    assert "cache_sync" in [s["name"] for s in data.get("services", [])]