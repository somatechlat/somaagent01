import pytest
from httpx import ASGITransport, AsyncClient

from services.common.api_key_store import InMemoryApiKeyStore
from services.gateway import main as gateway_main


@pytest.fixture(autouse=True)
def reset_overrides(monkeypatch):
    overrides = gateway_main.app.dependency_overrides
    overrides.clear()
    yield
    overrides.clear()
    monkeypatch.setattr(gateway_main, "_API_KEY_STORE", None)


@pytest.mark.asyncio
async def test_api_key_lifecycle(monkeypatch):
    monkeypatch.setattr(gateway_main, "REQUIRE_AUTH", False)

    store = InMemoryApiKeyStore()
    gateway_main.app.dependency_overrides[gateway_main.get_api_key_store] = lambda: store

    transport = ASGITransport(app=gateway_main.app)
    async with AsyncClient(transport=transport, base_url="http://gateway") as client:
        create = await client.post("/v1/keys", json={"label": "Testing"})
    assert create.status_code == 200
    body = create.json()
    assert body["secret"].startswith("sk_")

    key_id = body["key_id"]

    async with AsyncClient(transport=transport, base_url="http://gateway") as client:
        listing = await client.get("/v1/keys")
    assert listing.status_code == 200
    payload = listing.json()
    assert len(payload) == 1
    assert payload[0]["key_id"] == key_id

    async with AsyncClient(transport=transport, base_url="http://gateway") as client:
        revoke = await client.delete(f"/v1/keys/{key_id}")
    assert revoke.status_code == 204

    metadata = await store.list_keys()
    assert metadata[0].revoked is True
