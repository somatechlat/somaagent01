"""Chat endpoints extracted from the gateway monolith (incremental)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from services.common.admin_settings import ADMIN_SETTINGS
from services.common.session_repository import (
    ensure_schema as ensure_session_schema,
    PostgresSessionStore,
    RedisSessionCache,
)

router = APIRouter(prefix="/v1/chat", tags=["chat"])


def _session_store() -> PostgresSessionStore:
    store = PostgresSessionStore(ADMIN_SETTINGS.postgres_dsn)
    return store


def _session_cache() -> RedisSessionCache:
    cache = RedisSessionCache(ADMIN_SETTINGS.redis_url)
    return cache


@router.get("/session/{session_id}")
async def get_chat_session(
    session_id: str,
    store: PostgresSessionStore = Depends(_session_store),
    cache: RedisSessionCache = Depends(_session_cache),
):
    """Fetch chat session metadata (minimal example to start decomposition)."""
    try:
        await ensure_session_schema(store)
        session = await store.get(session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="session_not_found")
        return {
            "session_id": session_id,
            "persona_id": session.persona_id,
            "tenant": session.tenant,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"session_error: {type(exc).__name__}")
