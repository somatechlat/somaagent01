"""Requeue/DLQ endpoints extracted from gateway monolith."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.common.requeue_store import RequeueStore

router = APIRouter(prefix="/v1/requeue", tags=["requeue"])
STORE = RequeueStore()


class RequeueItem(BaseModel):
    requeue_id: str
    payload: dict
    status: str


@router.get("")
async def list_requeue():
    return await STORE.list()


@router.post("/{requeue_id}/resolve")
async def resolve_requeue(requeue_id: str):
    item = await STORE.get(requeue_id)
    if item is None:
        raise HTTPException(status_code=404, detail="requeue_not_found")
    await STORE.remove(requeue_id)
    return {"resolved": requeue_id}


@router.delete("/{requeue_id}")
async def delete_requeue(requeue_id: str):
    await STORE.remove(requeue_id)
    return {"deleted": requeue_id}
