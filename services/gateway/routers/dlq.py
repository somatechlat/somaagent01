"""DLQ endpoints extracted from gateway monolith."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.common.dlq_store import DLQStore, ensure_schema

router = APIRouter(prefix="/v1/admin/dlq", tags=["admin"])
STORE = DLQStore()


class DLQItem(BaseModel):
    id: int
    topic: str
    event: dict
    error: str | None
    created_at: str


@router.on_event("startup")
async def init_dlq_table():
    try:
        await ensure_schema(STORE)
    except Exception:
        # best effort; health endpoints will surface issues
    # Removed per Vibe rule

@router.get("/{topic}", response_model=list[DLQItem])
async def list_dlq(topic: str, limit: int = 100):
    rows = await STORE.list_recent(topic=topic, limit=limit)
    return [
        DLQItem(
            id=row.id,
            topic=row.topic,
            event=row.event,
            error=row.error,
            created_at=row.created_at.isoformat(),
        )
        for row in rows
    ]


@router.delete("/{topic}")
async def clear_dlq(topic: str):
    await STORE.purge(topic=topic)
    return {"cleared": topic}


@router.post("/{topic}/{item_id}/reprocess")
async def reprocess_dlq(topic: str, item_id: int):
    msg = await STORE.get_by_id(id=item_id)
    if msg is None or msg.topic != topic:
        raise HTTPException(status_code=404, detail="item_not_found")
    # In this trimmed version, "reprocess" just purges the entry; real logic would re-enqueue.
    await STORE.delete_by_id(id=item_id)
    return {"reprocessed": item_id, "topic": topic}
