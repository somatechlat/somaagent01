"""Tool request enqueue endpoint extracted from gateway monolith (minimal functional)."""

from __future__ import annotations

import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.common.publisher import DurablePublisher
from services.common.event_bus import KafkaEventBus, KafkaSettings
from services.common.memory_write_outbox import MemoryWriteOutbox

router = APIRouter(prefix="/v1/tool", tags=["tools"])


class ToolRequest(BaseModel):
    tool_name: str
    args: dict | None = None
    metadata: dict | None = None
    session_id: str | None = None


def _publisher() -> DurablePublisher:
    bus = KafkaEventBus(KafkaSettings.from_env())
    outbox = MemoryWriteOutbox()
    return DurablePublisher(bus=bus, outbox=outbox)


@router.post("/request")
async def tool_request(payload: ToolRequest):
    pub = _publisher()
    event_id = str(uuid.uuid4())
    await pub.publish(
        "tool.requests",
        {
            "event_id": event_id,
            "tool_name": payload.tool_name,
            "args": payload.args or {},
            "metadata": payload.metadata or {},
            "session_id": payload.session_id,
        },
        dedupe_key=event_id,
        session_id=payload.session_id,
    )
    return {"status": "enqueued", "event_id": event_id}
