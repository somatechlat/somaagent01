"""Requeue management service for SomaAgent 01."""
from __future__ import annotations

import logging
import os

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel

from services.common.requeue_store import RequeueStore
from services.common.event_bus import KafkaEventBus

LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))

app = FastAPI(title="SomaAgent 01 Requeue Service")


def get_store() -> RequeueStore:
    return RequeueStore()


def get_bus() -> KafkaEventBus:
    return KafkaEventBus()


class RequeueOverride(BaseModel):
    allow: bool = True


@app.get("/v1/requeue")
async def list_requeue(store: RequeueStore = Depends(get_store)) -> list[dict]:
    return await store.list()


@app.post("/v1/requeue/{requeue_id}/resolve")
async def resolve_requeue(
    requeue_id: str,
    payload: RequeueOverride,
    store: RequeueStore = Depends(get_store),
    bus: KafkaEventBus = Depends(get_bus),
) -> dict[str, str]:
    entry = await store.get(requeue_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Requeue entry not found")

    await store.remove(requeue_id)
    if payload.allow:
        entry.setdefault("metadata", {})
        entry["metadata"]["requeue_override"] = True
        await bus.publish(os.getenv("TOOL_REQUESTS_TOPIC", "tool.requests"), entry)
        status = "requeued"
    else:
        status = "discarded"

    return {"status": status}


@app.delete("/v1/requeue/{requeue_id}")
async def delete_requeue(requeue_id: str, store: RequeueStore = Depends(get_store)) -> dict[str, str]:
    await store.remove(requeue_id)
    return {"status": "deleted"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8012")))
