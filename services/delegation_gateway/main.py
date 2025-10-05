"""Delegation gateway service for SomaAgent 01."""
from __future__ import annotations

import logging
import os
import uuid
from typing import Any

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel

from services.common.event_bus import KafkaEventBus
from services.common.delegation_store import DelegationStore

LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))

app = FastAPI(title="SomaAgent 01 Delegation Gateway")


def get_bus() -> KafkaEventBus:
    return KafkaEventBus()


def get_store() -> DelegationStore:
    return DelegationStore()


class DelegationRequest(BaseModel):
    task_id: str | None = None
    payload: dict[str, Any]
    callback_url: str | None = None
    metadata: dict[str, Any] | None = None


class DelegationCallback(BaseModel):
    status: str
    result: dict[str, Any] | None = None


@app.on_event("startup")
async def startup_event() -> None:
    store = DelegationStore()
    await store.ensure_schema()


@app.post("/v1/delegation/task")
async def create_delegation_task(
    request: DelegationRequest,
    bus: KafkaEventBus = Depends(get_bus),
    store: DelegationStore = Depends(get_store),
) -> dict[str, str]:
    task_id = request.task_id or str(uuid.uuid4())
    await store.create_task(
        task_id=task_id,
        payload=request.payload,
        status="queued",
        callback_url=request.callback_url,
        metadata=request.metadata,
    )
    event = {
        "task_id": task_id,
        "payload": request.payload,
        "callback_url": request.callback_url,
        "metadata": request.metadata or {},
    }
    topic = os.getenv("DELEGATION_TOPIC", "somastack.delegation")
    await bus.publish(topic, event)
    return {"task_id": task_id, "status": "queued"}


@app.get("/v1/delegation/task/{task_id}")
async def get_delegation_task(
    task_id: str,
    store: DelegationStore = Depends(get_store),
) -> dict[str, Any]:
    record = await store.get_task(task_id)
    if not record:
        raise HTTPException(status_code=404, detail="Task not found")
    return record


@app.post("/v1/delegation/task/{task_id}/callback")
async def delegation_callback(
    task_id: str,
    payload: DelegationCallback,
    store: DelegationStore = Depends(get_store),
) -> dict[str, Any]:
    record = await store.get_task(task_id)
    if not record:
        raise HTTPException(status_code=404, detail="Task not found")
    await store.update_task(task_id, status=payload.status, result=payload.result)
    return {"task_id": task_id, "status": payload.status}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8015")))
