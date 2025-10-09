import pytest

from services.common.api_key_store import InMemoryApiKeyStore


@pytest.mark.asyncio
async def test_create_and_list_keys():
    store = InMemoryApiKeyStore()
    result = await store.create_key("Primary", created_by="admin@example.com")

    assert result.secret.startswith("sk_")
    assert result.label == "Primary"
    assert result.created_by == "admin@example.com"

    keys = await store.list_keys()
    assert len(keys) == 1
    meta = keys[0]
    assert meta.key_id == result.key_id
    assert meta.prefix == result.prefix
    assert meta.last_used_at is None
    assert not meta.revoked


@pytest.mark.asyncio
async def test_revoke_and_verify():
    store = InMemoryApiKeyStore()
    key = await store.create_key("Ops")

    confirmed = await store.verify_key(key.secret)
    assert confirmed is not None
    assert confirmed.key_id == key.key_id

    await store.revoke_key(key.key_id)

    revoked = await store.verify_key(key.secret)
    assert revoked is None


@pytest.mark.asyncio
async def test_touch_updates_timestamp():
    store = InMemoryApiKeyStore()
    key = await store.create_key("Analytics")

    await store.touch_key(key.key_id)
    keys = await store.list_keys()
    assert keys[0].last_used_at is not None
