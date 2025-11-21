"""Requeue/DLQ endpoints extracted from gateway monolith."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.common.requeue_store import RequeueStore
from services.common.admin_settings import ADMIN_SETTINGS

router = APIRouter(prefix="/v1/requeue", tags=["requeue"])
STORE = RequeueStore(dsn=ADMIN_SETTINGS.postgres_dsn)


class RequeueItem(BaseModel):
    requeue_id: str
    payload: dict
    status: str


@router.get("")
async def list_requeue():
    return await STORE.list_items()


@router.post("/{requeue_id}/resolve")
async def resolve_requeue(requeue_id: str):
    ok = await STORE.resolve(requeue_id)
    if not ok:
        raise HTTPException(status_code=404, detail="requeue_not_found")
    return {"resolved": requeue_id}


@router.delete("/{requeue_id}")
async def delete_requeue(requeue_id: str):
    ok = await STORE.delete(requeue_id)
    if not ok:
        raise HTTPException(status_code=404, detail="requeue_not_found")
    return {"deleted": requeue_id}
