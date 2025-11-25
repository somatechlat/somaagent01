"""Sessions and chat control endpoints (real, Postgres/Redis-backed)."""
from __future__ import annotations

import json
import uuid
from typing import Any, List, Optional

from fastapi import APIRouter, HTTPException, Query

from services.common.session_repository import (
    PostgresSessionStore,
    RedisSessionCache,
    ensure_schema as ensure_session_schema,
)
from services.common.publisher import DurablePublisher
from src.core.config import cfg

# Single router with absolute paths so we can expose both /v1/sessions/* and
# legacy chat control endpoints used by the Web UI (e.g., /chat_reset).
router = APIRouter(prefix="", tags=["sessions"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _session_store() -> PostgresSessionStore:
    return PostgresSessionStore(cfg.settings().database.dsn)


def _session_cache() -> RedisSessionCache:
    return RedisSessionCache(cfg.settings().redis.url)


def _publisher() -> DurablePublisher:
    from services.gateway.main import get_publisher

    return get_publisher()


# ---------------------------------------------------------------------------
# Session list/history (consumed by web UI chat list + history loader)
# ---------------------------------------------------------------------------
@router.get("/v1/sessions")
async def list_sessions(limit: int = Query(50, ge=1, le=200)):
    store = _session_store()
    # await ensure_session_schema(store)

    rows = await store.list_sessions(limit=limit)
    return [
        {
            "session_id": str(r.session_id),
            "persona_id": getattr(r, "persona_id", None),
            "tenant": getattr(r, "tenant", None),
            "subject": getattr(r, "subject", None),
            "created_at": getattr(r, "created_at", None),
            "updated_at": getattr(r, "updated_at", None),
        }
        for r in rows
    ]


@router.get("/v1/sessions/{session_id}/history")
async def session_history(
    session_id: str, limit: int = Query(200, ge=1, le=1000)
) -> Any:
    store = _session_store()
    # await ensure_session_schema(store)

    events = await store.list_events(session_id=session_id, limit=limit)
    if events is None:
        raise HTTPException(status_code=404, detail="session_not_found")
    return {"session_id": session_id, "events": events}


# ---------------------------------------------------------------------------
# Chat control endpoints used by the existing web UI buttons
# ---------------------------------------------------------------------------
@router.post("/chat_reset")
async def chat_reset(payload: dict | None = None):
    """Create a new empty session envelope and return its id."""
    store = _session_store()
    cache = _session_cache()
    # await ensure_session_schema(store)

    session_id = str(uuid.uuid4())

    meta = (payload or {}).get("metadata") or {}
    subject = (payload or {}).get("subject")
    persona_id = (payload or {}).get("persona_id")
    tenant = (payload or {}).get("tenant") or meta.get("tenant")

    pool = await store._ensure_pool()  # noqa: SLF001 – intentional reuse
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO session_envelopes (
                session_id,
                persona_id,
                tenant,
                subject,
                metadata,
                analysis
            ) VALUES ($1, $2, $3, $4, $5::jsonb, '{}'::jsonb)
            ON CONFLICT (session_id) DO NOTHING
            """,
            session_id,
            persona_id,
            tenant,
            subject,
            json.dumps(meta, ensure_ascii=False),
        )

    # Clear any stray cache entries for safety
    try:
        await cache.delete(cache.format_key(session_id))
    except Exception:
        pass

    return {"ctxid": session_id, "session_id": session_id}


@router.post("/chat_remove")
async def chat_remove(payload: dict):
    session_id = payload.get("context") or payload.get("session_id")
    if not session_id:
        raise HTTPException(status_code=400, detail="missing session_id")

    store = _session_store()
    cache = _session_cache()
    # await ensure_session_schema(store)

    pool = await store._ensure_pool()  # noqa: SLF001
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                "DELETE FROM session_events WHERE session_id = $1", session_id
            )
            await conn.execute(
                "DELETE FROM session_envelopes WHERE session_id = $1", session_id
            )
    try:
        await cache.delete(cache.format_key(session_id))
    except Exception:
        pass
    return {"status": "deleted", "session_id": session_id}


@router.post("/chat_export")
async def chat_export(payload: dict):
    session_id = payload.get("ctxid") or payload.get("session_id")
    if not session_id:
        raise HTTPException(status_code=400, detail="missing session_id")

    store = _session_store()
    # await ensure_session_schema(store)

    events = await store.list_events(session_id=session_id, limit=2000)
    if events is None:
        raise HTTPException(status_code=404, detail="session_not_found")
    content = json.dumps({"session_id": session_id, "events": events}, ensure_ascii=False)
    return {"ctxid": session_id, "content": content}


@router.post("/chat_load")
async def chat_load(payload: dict):
    chats: List[str] = payload.get("chats") or []
    if not chats:
        raise HTTPException(status_code=400, detail="no chat data provided")

    store = _session_store()
    # await ensure_session_schema(store)

    created_ids: List[str] = []

    pool = await store._ensure_pool()  # noqa: SLF001
    for raw in chats:
        try:
            data = json.loads(raw)
        except Exception:
            continue
        events = data.get("events") or []
        session_id = data.get("session_id") or str(uuid.uuid4())
        created_ids.append(session_id)
        async with pool.acquire() as conn:
            async with conn.transaction():
                for ev in events:
                    await conn.execute(
                        "INSERT INTO session_events (session_id, payload) VALUES ($1, $2)",
                        session_id,
                        json.dumps(ev, ensure_ascii=False),
                    )
                # ensure envelope exists (minimal metadata from first event)
                meta = {}
                if events:
                    meta = (events[0] or {}).get("metadata") or {}
                await conn.execute(
                    """
                    INSERT INTO session_envelopes (session_id, tenant, subject, metadata, analysis)
                    VALUES ($1, $2, $3, $4::jsonb, '{}'::jsonb)
                    ON CONFLICT (session_id) DO NOTHING
                    """,
                    session_id,
                    meta.get("tenant"),
                    meta.get("subject"),
                    json.dumps(meta, ensure_ascii=False),
                )

    return {"ctxids": created_ids}


@router.post("/pause")
async def pause(payload: dict):
    session_id = payload.get("context") or payload.get("session_id")
    paused = bool(payload.get("paused"))
    if not session_id:
        raise HTTPException(status_code=400, detail="missing session_id")
    cache = _session_cache()
    meta = {"paused": paused}
    await cache.write_context(session_id, None, meta, ttl=0)
    return {"session_id": session_id, "paused": paused}


@router.post("/restart")
async def restart(payload: Optional[dict] = None):
    # For now we perform a fast health probe to confirm the backend is up.
    # A real container restart is orchestrated outside the app.
    return {"status": "ok", "message": "restart acknowledged"}


@router.post("/nudge")
async def nudge(payload: dict):
    session_id = payload.get("ctxid") or payload.get("session_id")
    if not session_id:
        raise HTTPException(status_code=400, detail="missing session_id")

    publisher = _publisher()
    wal_topic = cfg.env("MEMORY_WAL_TOPIC", "memory.wal")
    event_id = str(uuid.uuid4())
    event = {
        "event_id": event_id,
        "session_id": session_id,
        "role": "system",
        "message": "nudge",
        "metadata": {"action": "nudge"},
        "version": "sa01-v1",
    }
    await publisher.publish(
        wal_topic,
        event,
        dedupe_key=event_id,
        session_id=session_id,
        tenant=None,
    )
    return {"status": "sent", "session_id": session_id, "event_id": event_id}


__all__ = ["router"]
