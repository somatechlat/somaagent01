"""DLQ endpoints extracted from gateway monolith."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from services.common.admin_settings import ADMIN_SETTINGS
from services.common.dlq_store import DLQItem, DLQStore

router = APIRouter(prefix="/v1/admin/dlq", tags=["admin"])
STORE = DLQStore(dsn=ADMIN_SETTINGS.postgres_dsn)


@router.get("/{topic}", response_model=list[DLQItem])
async def list_dlq(topic: str):
    return await STORE.list(topic)


@router.delete("/{topic}")
async def clear_dlq(topic: str):
    await STORE.clear(topic)
    return {"cleared": topic}


@router.post("/{topic}/{item_id}/reprocess")
async def reprocess_dlq(topic: str, item_id: str):
    ok = await STORE.reprocess(topic, item_id)
    if not ok:
        raise HTTPException(status_code=404, detail="item_not_found")
    return {"reprocessed": item_id, "topic": topic}
