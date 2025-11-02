import uuid

import pytest
from testcontainers.postgres import PostgresContainer

from services.common.session_repository import (
    ensure_schema,
    PostgresSessionStore,
)


@pytest.mark.asyncio
async def test_session_repository_lists_sessions_and_events() -> None:
    """Verify session repository exposes chronological events and session summaries."""

    with PostgresContainer("postgres:16-alpine") as postgres:
        dsn = postgres.get_connection_url()
        # asyncpg expects a plain postgresql DSN
        if "+" in dsn:
            driver, rest = dsn.split("+", 1)
            dsn = driver + "://" + rest.split("://", 1)[1]

        store = PostgresSessionStore(dsn=dsn)
        try:
            await ensure_schema(store)

            session_id = str(uuid.uuid4())
            tenant = "default"

            user_event = {
                "event_id": str(uuid.uuid4()),
                "session_id": session_id,
                "persona_id": None,
                "role": "user",
                "message": "Hello there",
                "metadata": {"tenant": tenant, "source": "ui"},
            }
            assistant_event = {
                "event_id": str(uuid.uuid4()),
                "session_id": session_id,
                "persona_id": None,
                "role": "assistant",
                "message": "Hi!",
                "metadata": {"tenant": tenant, "source": "slm", "status": "completed"},
            }

            await store.append_event(session_id, {"type": "user", **user_event})
            await store.append_event(session_id, {"type": "assistant", **assistant_event})

            events = await store.list_events_after(session_id)
            assert len(events) == 2
            assert events[0]["payload"]["message"] == "Hello there"
            assert events[1]["payload"]["message"] == "Hi!"

            first_id = events[0]["id"]
            newer_events = await store.list_events_after(session_id, after_id=first_id)
            assert len(newer_events) == 1
            assert newer_events[0]["payload"]["message"] == "Hi!"

            summaries = await store.list_sessions(limit=10)
            assert len(summaries) == 1
            summary = summaries[0]
            assert str(summary.session_id) == session_id
            assert summary.metadata.get("tenant") == tenant
        finally:
            await store.close()
