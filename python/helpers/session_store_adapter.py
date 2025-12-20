"""
Session persistence helpers replacing legacy file-based persist_chat module.

Provides thin, real implementations backed by PostgresSessionStore and, where
needed, AttachmentsStore. All functions are async and production-safe.
"""

from __future__ import annotations

import asyncio
import hashlib
import os
import tempfile
import uuid
from pathlib import Path
from typing import Any, Iterable, Optional

from agent import AgentContext
# Use central configuration via cfg instead of legacy ADMIN_SETTINGS.
from src.core.config import cfg
from services.common.attachments_store import AttachmentsStore
from services.common.session_repository import PostgresSessionStore

# Lazily created singletons
_SESSION_STORE: Optional[PostgresSessionStore] = None
_ATTACHMENT_STORE: Optional[AttachmentsStore] = None
_LOCK = asyncio.Lock()


async def _get_session_store() -> PostgresSessionStore:
    global _SESSION_STORE
    if _SESSION_STORE is None:
        async with _LOCK:
            if _SESSION_STORE is None:
                # Use the central Postgres DSN from cfg.
                _SESSION_STORE = PostgresSessionStore(dsn=cfg.settings().database.dsn)
    return _SESSION_STORE


async def _get_attachment_store() -> AttachmentsStore:
    global _ATTACHMENT_STORE
    if _ATTACHMENT_STORE is None:
        async with _LOCK:
            if _ATTACHMENT_STORE is None:
                # Use the central Postgres DSN from cfg for attachments store.
                _ATTACHMENT_STORE = AttachmentsStore(dsn=cfg.settings().database.dsn)
                await _ATTACHMENT_STORE.ensure_schema()
    return _ATTACHMENT_STORE


def _serialize_logs(log_items: Iterable[Any]) -> list[dict[str, Any]]:
    serialized: list[dict[str, Any]] = []
    for item in log_items:
        try:
            payload = item.output()
            if payload.get("kvps") and not isinstance(payload["kvps"], dict):
                payload["kvps"] = dict(payload["kvps"])
            serialized.append(payload)
        except Exception:
            # Best-effort capture; skip malformed entries
            continue
    return serialized


def _context_snapshot(context: AgentContext, *, reason: str | None = None) -> dict[str, Any]:
    base = context.serialize()
    snapshot = {
        "type": "context_snapshot",
        "event_id": str(uuid.uuid4()),
        "session_id": context.id,
        "metadata": {
            "reason": reason or "checkpoint",
            "context_type": context.type.value if hasattr(context, "type") else None,
        },
        "payload": {
            "context": base,
            "log": _serialize_logs(getattr(context.log, "logs", [])),
        },
    }
    return snapshot


async def save_context(context: AgentContext, *, reason: str | None = None) -> None:
    """Persist a full context snapshot as a session event."""
    store = await _get_session_store()
    snapshot = _context_snapshot(context, reason=reason)
    await store.append_event(context.id, snapshot)


async def delete_context(context_id: str) -> None:
    """Delete all events/envelope for a session."""
    store = await _get_session_store()
    await store.delete_session(context_id)


def get_context_folder(context_id: str) -> str:
    """
    Return a temporary directory path for transitional file-based consumers.
    Directory is created under system temp; caller may write transient data.
    """
    base = Path(tempfile.gettempdir()) / "somaagent_sessions" / context_id
    os.makedirs(base, exist_ok=True)
    return str(base)


async def record_tool_result(
    session_id: str,
    *,
    tool_name: str,
    result: Any,
    persona_id: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None,
) -> str:
    """Persist a tool result as a session event; returns event_id."""
    store = await _get_session_store()
    event_id = str(uuid.uuid4())
    payload = {
        "type": "tool_result",
        "event_id": event_id,
        "session_id": session_id,
        "persona_id": persona_id,
        "tool_name": tool_name,
        "result": result,
        "metadata": metadata or {},
    }
    await store.append_event(session_id, payload)
    return event_id


async def save_screenshot_attachment(
    session_id: str,
    *,
    persona_id: Optional[str],
    content: bytes,
    filename: str,
    tenant: Optional[str] = None,
) -> str:
    """Store screenshot bytes in attachments store and return attachment id as str."""
    store = await _get_attachment_store()
    sha = hashlib.sha256(content).hexdigest()
    att_id = await store.insert(
        tenant=tenant,
        session_id=session_id,
        persona_id=persona_id,
        filename=filename,
        mime="image/png",
        size=len(content),
        sha256=sha,
        status="clean",
        quarantine_reason=None,
        content=content,
    )
    return str(att_id)
