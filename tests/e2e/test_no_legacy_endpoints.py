import os
import pytest
import httpx

BASE = os.environ.get("GATEWAY_BASE_URL") or f"http://127.0.0.1:{os.getenv('GATEWAY_PORT', '21016')}"

@pytest.mark.asyncio
async def test_legacy_endpoints_return_404():
    async with httpx.AsyncClient(timeout=5.0) as client:
        # /v1/ui/poll must not exist
        r1 = await client.post(BASE + "/v1/ui/poll")
        assert r1.status_code == 404, f"/v1/ui/poll returned {r1.status_code}"
        # /v1/csrf must not exist
        r2 = await client.get(BASE + "/v1/csrf")
        assert r2.status_code == 404, f"/v1/csrf returned {r2.status_code}"
