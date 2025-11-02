import pytest

from services.common.dlq_store import DLQStore, ensure_schema


@pytest.mark.asyncio
@pytest.mark.integration
async def test_dlq_add_list_purge_and_delete_by_id():
    store = DLQStore()
    await ensure_schema(store)

    topic = "memory.wal.dlq"
    event = {"type": "memory.write", "session_id": "s-1", "payload": {"id": "x"}}

    # Add two entries
    id1 = await store.add(topic=topic, event=event, error="boom")
    id2 = await store.add(topic=topic, event=event, error="boom2")
    assert id1 != id2

    # List recent should include the items
    items = await store.list_recent(topic=topic, limit=10)
    ids = {i.id for i in items}
    assert id1 in ids and id2 in ids

    # Get by id
    one = await store.get_by_id(id=id1)
    assert one and one.id == id1 and one.topic == topic

    # Delete single by id
    deleted_one = await store.delete_by_id(id=id1)
    assert deleted_one == 1

    # Purge the rest
    remaining = await store.purge(topic=topic)
    assert remaining >= 1
