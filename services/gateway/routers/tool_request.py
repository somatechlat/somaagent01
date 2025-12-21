"""Tool request enqueue endpoint extracted from gateway monolith (minimal functional)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter
from pydantic import BaseModel

from services.gateway.providers import get_temporal_client
from services.tool_executor.temporal_worker import ToolExecutorWorkflow
from temporalio import workflow
from src.core.config import cfg

router = APIRouter(prefix="/v1/tool", tags=["tools"])


class ToolRequest(BaseModel):
    tool_name: str
    args: dict | None = None
    metadata: dict | None = None
    session_id: str | None = None


@router.post("/request")
async def tool_request(payload: ToolRequest):
    event_id = str(uuid.uuid4())
    event = {
        "event_id": event_id,
        "tool_name": payload.tool_name,
        "args": payload.args or {},
        "metadata": payload.metadata or {},
        "session_id": payload.session_id,
    }
    client = await get_temporal_client()
    task_queue = cfg.env("SA01_TEMPORAL_TOOL_QUEUE", "tool-executor")
    workflow_id = f"tool-{payload.session_id or 'n/a'}-{event_id}"
    event["workflow_id"] = workflow_id
    await client.start_workflow(
        ToolExecutorWorkflow.run,
        event,
        id=workflow_id,
        task_queue=task_queue,
    )
    return {"status": "started", "workflow_id": workflow_id, "event_id": event_id}


@router.post("/terminate/{workflow_id}")
async def terminate_tool_workflow(workflow_id: str) -> dict:
    client = await get_temporal_client()
    try:
        handle = client.get_workflow_handle(workflow_id=workflow_id)
        await handle.cancel()
        return {"status": "canceled", "workflow_id": workflow_id}
    except Exception as exc:
        return {"status": "error", "workflow_id": workflow_id, "error": str(exc)}
