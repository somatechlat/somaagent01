"""Integration test for the orchestrator stack.

This file spins up the orchestrator, registers all three services (gateway,
memory, cache‑sync), asserts that the status endpoint returns a list of
services with length 3 and finally triggers a shutdown.  The test uses the
``client`` and ``base_url`` fixtures from ``tests/conftest.py``.
"""

import pytest
from httpx import AsyncClient
from orchestrator.main import create_app


@pytest.mark.asyncio
async def test_full_stack(client: AsyncClient, base_url: str):
    """Verify that the orchestrator can start all services and report them."""
    # Register services – the orchestrator will automatically pick up the
    # three services because they are already registered in ``create_app``.
    resp = await client.get(f"{base_url}/v1/status")
    assert resp.status == 200
    data = await resp.json()
    assert len(data.get("services", [])) == 3
    # Trigger shutdown to clean up the stack
    resp = await client.post(f"{base_url}/v1/shutdown")
    assert resp.status == 200
    data = await resp.json()
    assert data["status"] == "shutting_down"