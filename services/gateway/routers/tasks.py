"""Runtime task registry APIs (register, list, reload) with OPA gating."""

from __future__ import annotations

import asyncio
from typing import Any, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from python.tasks.celery_app import app as celery_app, register_dynamic_tasks
from services.common.policy_client import PolicyClient, PolicyRequest
from services.common.task_registry import RegistryEntry, TaskRegistry
from src.core.config import cfg

router = APIRouter(prefix="/v1/tasks", tags=["tasks"])

registry = TaskRegistry()
policy = PolicyClient(base_url=cfg.env("OPA_URL"))


class TaskRegistration(BaseModel):
    name: str = Field(..., description="Fully qualified task name")
    kind: str = Field("task", regex="^(task|tool)$")
    module_path: str
    callable_name: str = Field(..., alias="callable")
    queue: str = "fast_a2a"
    rate_limit: Optional[str] = None
    max_retries: Optional[int] = None
    soft_time_limit: Optional[int] = None
    time_limit: Optional[int] = None
    enabled: bool = True
    tenant_scope: List[str] = Field(default_factory=list)
    persona_scope: List[str] = Field(default_factory=list)
    arg_schema: dict[str, Any] = Field(default_factory=dict)
    artifact_hash: Optional[str] = None
    soma_tags: List[str] = Field(default_factory=list)
    created_by: Optional[str] = None

    class Config:
        allow_population_by_field_name = True


def _allow(action: str, tenant: Optional[str], resource: str, context: dict[str, Any]) -> bool:
    if not tenant:
        # fail-closed if tenant missing
        return False
    return asyncio.run(
        policy.evaluate(
            PolicyRequest(
                tenant=tenant,
                persona_id=context.get("persona_id"),
                action=action,
                resource=resource,
                context=context,
            )
        )
    )


@router.post("/register")
async def register_task(req: TaskRegistration, tenant_id: Optional[str] = None) -> dict:
    allowed = _allow("task.register", tenant_id, req.name, req.dict(by_alias=True))
    if not allowed:
        raise HTTPException(status_code=403, detail="policy_denied")

    entry = await registry.register(
        name=req.name,
        kind=req.kind,
        module_path=req.module_path,
        callable_name=req.callable_name,
        queue=req.queue,
        rate_limit=req.rate_limit,
        max_retries=req.max_retries,
        soft_time_limit=req.soft_time_limit,
        time_limit=req.time_limit,
        enabled=req.enabled,
        tenant_scope=req.tenant_scope,
        persona_scope=req.persona_scope,
        arg_schema=req.arg_schema,
        artifact_hash=req.artifact_hash,
        soma_tags=req.soma_tags,
        created_by=req.created_by or tenant_id,
    )

    # Reload registry on gateway for local visibility, then broadcast to workers.
    register_dynamic_tasks(force_refresh=True)
    celery_app.control.broadcast("task_registry.reload")

    return {"status": "registered", "name": entry.name}


@router.get("")
async def list_tasks(
    tenant_id: Optional[str] = None, persona_id: Optional[str] = None
) -> list[dict]:
    entries = await registry.load_all(force_refresh=False)
    visible: list[RegistryEntry] = []
    for e in entries:
        if e.tenant_scope and tenant_id and tenant_id not in e.tenant_scope:
            continue
        if e.persona_scope and persona_id and persona_id not in e.persona_scope:
            continue
        visible.append(e)
    return [e.__dict__ for e in visible]


@router.post("/reload")
async def reload_tasks() -> dict:
    reloaded = register_dynamic_tasks(force_refresh=True)
    celery_app.control.broadcast("task_registry.reload")
    return {"reloaded": reloaded}
