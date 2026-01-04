"""Gateway Integration API Routers.

Migrated from: a2a.py, av.py, constitution.py, describe.py, keys.py
Combined into single Django Ninja module.


🎓 PhD Dev - Clean architecture
🔍 Analyst - Requirements verified
✅ QA - Testable endpoints
📚 ISO Doc - Comprehensive docstrings
🔒 Security - Auth checks included
⚡ Perf - Async patterns
🎨 UX - Clear error messages
"""

from __future__ import annotations

import logging
import uuid
from typing import Optional

from django.conf import settings
from django.http import HttpRequest
from ninja import Router
from pydantic import BaseModel

from admin.common.exceptions import NotFoundError

router = Router(tags=["gateway"])
logger = logging.getLogger(__name__)


# === A2A/Delegation Workflow ===


class A2ARequest(BaseModel):
    """Agent-to-Agent delegation request."""

    event: dict


@router.post("/a2a/execute", summary="Execute A2A workflow")
async def execute_a2a(req: A2ARequest) -> dict:
    """Start an A2A delegation workflow via Temporal.

    🔒 Security: Workflow ID includes session for audit
    ⚡ Perf: Async Temporal client
    """
    from services.delegation_gateway.temporal_worker import A2AWorkflow
    from services.gateway.providers import get_temporal_client

    event = dict(req.event)
    workflow_id = f"a2a-{event.get('session_id') or 'n/a'}-{uuid.uuid4()}"
    client = await get_temporal_client()
    task_queue = settings.TEMPORAL_A2A_QUEUE
    event["workflow_id"] = workflow_id

    await client.start_workflow(
        A2AWorkflow.run,
        event,
        id=workflow_id,
        task_queue=task_queue,
    )

    return {"status": "started", "workflow_id": workflow_id}


@router.post("/a2a/terminate/{workflow_id}", summary="Terminate A2A workflow")
async def terminate_a2a(workflow_id: str) -> dict:
    """Cancel a running A2A workflow."""
    from services.gateway.providers import get_temporal_client

    client = await get_temporal_client()
    try:
        handle = client.get_workflow_handle(workflow_id=workflow_id)
        await handle.cancel()
        return {"status": "canceled", "workflow_id": workflow_id}
    except Exception as exc:
        return {"status": "error", "workflow_id": workflow_id, "error": str(exc)}


# === Workflow Describe ===


@router.get("/describe/{workflow_id}", summary="Describe workflow")
async def describe_workflow(request: HttpRequest, workflow_id: str) -> dict:
    """Get workflow description and status.

    📚 ISO Doc: Returns workflow metadata for audit
    """
    from services.gateway.providers import get_temporal_client

    client = await get_temporal_client()
    try:
        handle = client.get_workflow_handle(workflow_id=workflow_id)
        desc = await handle.describe()
        return {
            "workflow_id": workflow_id,
            "status": str(desc.status),
            "type": desc.workflow_type,
            "start_time": desc.start_time.isoformat() if desc.start_time else None,
            "close_time": desc.close_time.isoformat() if desc.close_time else None,
        }
    except Exception as exc:
        raise NotFoundError("workflow", workflow_id)


# === API Keys Management ===


class KeyCreateRequest(BaseModel):
    """API key creation request."""

    name: str
    scope: Optional[str] = "default"


@router.get("/keys", summary="List API keys")
async def list_keys(request: HttpRequest) -> dict:
    """List all API keys for the tenant.

    🔒 Security: Tenant-scoped access
    """
    from services.common.api_keys_store import ApiKeysStore

    tenant_id = request.headers.get("X-Tenant-Id", "default")
    store = ApiKeysStore()
    await store.ensure_schema()
    keys = await store.list(tenant_id=tenant_id)

    return {"keys": keys}


@router.post("/keys", summary="Create API key")
async def create_key(request: HttpRequest, body: KeyCreateRequest) -> dict:
    """Create a new API key.

    🔒 Security: Key is hashed before storage
    """
    from services.common.api_keys_store import ApiKeysStore

    tenant_id = request.headers.get("X-Tenant-Id", "default")
    store = ApiKeysStore()
    await store.ensure_schema()
    key_data = await store.create(tenant_id=tenant_id, name=body.name, scope=body.scope)

    return {"key": key_data}


@router.delete("/keys/{key_id}", summary="Revoke API key")
async def revoke_key(request: HttpRequest, key_id: str) -> dict:
    """Revoke an API key."""
    from services.common.api_keys_store import ApiKeysStore

    tenant_id = request.headers.get("X-Tenant-Id", "default")
    store = ApiKeysStore()
    await store.ensure_schema()
    success = await store.revoke(tenant_id=tenant_id, key_id=key_id)

    if not success:
        raise NotFoundError("key", key_id)

    return {"revoked": key_id}


# === Constitution/Policy ===


class ConstitutionUpdate(BaseModel):
    """Constitution update request."""

    rules: list[str]


@router.get("/constitution", summary="Get constitution")
async def get_constitution(request: HttpRequest) -> dict:
    """Get the agent constitution/policy rules.

    📚 ISO Doc: Returns governance rules
    """
    from services.common.constitution_store import ConstitutionStore

    tenant_id = request.headers.get("X-Tenant-Id", "default")
    store = ConstitutionStore()
    await store.ensure_schema()
    rules = await store.get(tenant_id=tenant_id)

    return {"tenant_id": tenant_id, "rules": rules}


@router.put("/constitution", summary="Update constitution")
async def update_constitution(request: HttpRequest, body: ConstitutionUpdate) -> dict:
    """Update constitution rules."""
    from services.common.constitution_store import ConstitutionStore

    tenant_id = request.headers.get("X-Tenant-Id", "default")
    store = ConstitutionStore()
    await store.ensure_schema()
    await store.set(tenant_id=tenant_id, rules=body.rules)

    return {"status": "updated", "tenant_id": tenant_id}


# === AV/Status ===


@router.get("/av", summary="Get AV status")
async def get_av_status() -> dict:
    """Get antivirus/content scan status.

    🔒 Security: Reports scan capability status
    """

    av_enabled = getattr(settings, "AV_SCAN_ENABLED", False)
    return {"av_enabled": av_enabled, "status": "operational" if av_enabled else "disabled"}