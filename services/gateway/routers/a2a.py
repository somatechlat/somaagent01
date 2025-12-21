"""A2A/Delegation workflow ingress for Temporal."""

from __future__ import annotations

import uuid

from fastapi import APIRouter
from pydantic import BaseModel

from services.gateway.providers import get_temporal_client
from services.delegation_gateway.temporal_worker import A2AWorkflow
from src.core.config import cfg

router = APIRouter(prefix="/v1/a2a", tags=["a2a"])


class A2ARequest(BaseModel):
    event: dict


@router.post("/execute")
async def execute_a2a(req: A2ARequest) -> dict:
    event = dict(req.event)
    workflow_id = f"a2a-{event.get('session_id') or 'n/a'}-{uuid.uuid4()}"
    client = await get_temporal_client()
    task_queue = cfg.env("SA01_TEMPORAL_A2A_QUEUE", "a2a")
    event["workflow_id"] = workflow_id
    await client.start_workflow(
        A2AWorkflow.run,
        event,
        id=workflow_id,
        task_queue=task_queue,
    )
    return {"status": "started", "workflow_id": workflow_id}


@router.post("/terminate/{workflow_id}")
async def terminate_a2a(workflow_id: str) -> dict:
    client = await get_temporal_client()
    try:
        handle = client.get_workflow_handle(workflow_id=workflow_id)
        await handle.cancel()
        return {"status": "canceled", "workflow_id": workflow_id}
    except Exception as exc:
        return {"status": "error", "workflow_id": workflow_id, "error": str(exc)}
