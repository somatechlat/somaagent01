"""Memory batch/delete endpoints extracted from gateway monolith."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.core.domain.memory.replica_store import MemoryReplicaStore

router = APIRouter(prefix="/v1/memory", tags=["memory"])


class MemoryBatchRequest(BaseModel):
    items: list[dict]


@router.post("/batch")
async def memory_batch(req: MemoryBatchRequest):
    store = MemoryReplicaStore()
    ids = []
    for item in req.items:
        res = await store.insert_memory(item)
        ids.append(res)
    return {"inserted": len(ids), "ids": ids}


@router.delete("/{mem_id}")
async def memory_delete(mem_id: str):
    store = MemoryReplicaStore()
    deleted = await store.delete_memory(mem_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="memory_not_found")
    return {"deleted": mem_id}
