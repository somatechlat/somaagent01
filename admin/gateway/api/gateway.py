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

from admin.common.auth import AuthBearer
from admin.common.exceptions import NotFoundError, ServiceError
from admin.common.messages import ErrorCode, get_message
from services.common.authorization import authorize

router = Router(tags=["gateway"])
logger = logging.getLogger(__name__)


# === A2A/Delegation Workflow ===


class A2ARequest(BaseModel):
    """Agent-to-Agent delegation request."""

    event: dict


@router.post("/a2a/execute", summary="Execute A2A workflow", auth=AuthBearer())
async def execute_a2a(request: HttpRequest, req: A2ARequest) -> dict:
    """Start an A2A delegation workflow via Temporal.

    🔒 Security: Workflow ID includes session for audit
    ⚡ Perf: Async Temporal client
    """
    # Starting a delegation workflow is starting an agent's work. Gate before
    # the event body is read: an unauthenticated caller must not learn which
    # event shapes the gateway accepts.
    await authorize(request, action="agent:start", resource="gateway")
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


class A2aTerminationResponse(BaseModel):
    """A2A workflow termination response."""

    status: str
    workflow_id: str


@router.post(
    "/a2a/terminate/{workflow_id}",
    response=A2aTerminationResponse,
    summary="Terminate A2A workflow",
    auth=AuthBearer(),
)
async def terminate_a2a(request: HttpRequest, workflow_id: str) -> A2aTerminationResponse:
    """Cancel a running A2A workflow.

    🔒 Security: Stopping agent work is a privileged act.
    """
    await authorize(request, action="agent:stop", resource="a2a_workflow")

    from services.gateway.providers import get_temporal_client

    client = await get_temporal_client()
    try:
        handle = client.get_workflow_handle(workflow_id=workflow_id)
        await handle.cancel()
        return A2aTerminationResponse(status="canceled", workflow_id=workflow_id)
    except Exception as exc:
        raise ServiceError(
            get_message(ErrorCode.INTERNAL_ERROR),
            details={"workflow_id": workflow_id, "detail": str(exc)},
        )


# === Workflow Describe ===


@router.get("/describe/{workflow_id}", summary="Describe workflow", auth=AuthBearer())
async def describe_workflow(request: HttpRequest, workflow_id: str) -> dict:
    """Get workflow description and status.

    🔒 Security: Workflow metadata reveals what the agent was asked to do.
    📚 ISO Doc: Returns workflow metadata for audit
    """
    await authorize(request, action="agent:view_logs", resource="a2a_workflow")

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
# Canonical source: admin.aaas.models.profiles.ApiKey (Django ORM)


class KeyCreateRequest(BaseModel):
    """API key creation request.

    Scopes are mandatory, must name permissions from the catalog, and may
    never exceed the issuing principal's authority. The previous ``scope``
    field defaulted to ``"default"``, which is not a permission.
    """

    name: str
    scopes: list[str]


@router.get("/keys", summary="List API keys", auth=AuthBearer())
async def list_keys(request: HttpRequest) -> dict:
    """List all API keys for the tenant.

    🔒 Security: Tenant-scoped access
    """
    await authorize(request, action="org:apikey_read", resource="keys")
    from asgiref.sync import sync_to_async

    from admin.aaas.models.profiles import ApiKey

    tenant_id = request.headers.get("X-Tenant-Id", "")
    keys = await sync_to_async(list)(
        ApiKey.objects.filter(tenant_id=tenant_id, is_active=True).values(
            "id", "name", "key_prefix", "scopes", "created_at", "last_used_at"
        )
    )
    return {"keys": keys}


@router.post("/keys", summary="Create API key", auth=AuthBearer())
async def create_key(request: HttpRequest, body: KeyCreateRequest) -> dict:
    """Create a new API key.

    🔒 Security: Key is hashed before storage. Scopes are explicit, validated
    against the authorization catalog, and never exceed the issuer.
    """
    await authorize(request, action="org:apikey_create", resource="keys")
    import hashlib
    import secrets

    from asgiref.sync import sync_to_async

    from admin.aaas.models.profiles import ApiKey
    from admin.core.authz import permissions_for_roles, validate_scopes

    tenant_id = request.headers.get("X-Tenant-Id", "")

    auth = getattr(request, "auth", None)
    issuer_permissions = permissions_for_roles(list(getattr(auth, "roles", None) or []))
    try:
        scopes = sorted(validate_scopes(body.scopes, issuer_permissions))
    except ValueError as exc:
        from admin.common.exceptions import ValidationError

        raise ValidationError(str(exc), field="scopes")

    # Same shape as admin.aaas.api.settings.create_api_key: one format, one
    # prefix length. The previous version wrote a 12-character prefix into
    # ApiKey.key_prefix, which is a CharField(max_length=8).
    from admin.common.auth import API_KEY_PREFIX

    raw_key = f"{API_KEY_PREFIX}{secrets.token_urlsafe(32)}"
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    key_prefix = raw_key[:8]

    key = await sync_to_async(ApiKey.objects.create)(
        key_type="tenant",
        tenant_id=tenant_id,
        name=body.name,
        key_prefix=key_prefix,
        key_hash=key_hash,
        scopes=scopes,
    )

    return {"key": {"id": str(key.id), "name": key.name, "prefix": key_prefix, "value": raw_key}}


@router.delete("/keys/{key_id}", summary="Revoke API key", auth=AuthBearer())
async def revoke_key(request: HttpRequest, key_id: str) -> dict:
    """Revoke an API key."""
    await authorize(request, action="org:apikey_revoke", resource="keys")
    from asgiref.sync import sync_to_async

    from admin.aaas.models.profiles import ApiKey

    tenant_id = request.headers.get("X-Tenant-Id", "")
    updated = await sync_to_async(ApiKey.objects.filter(id=key_id, tenant_id=tenant_id).update)(
        is_active=False
    )

    if not updated:
        raise NotFoundError("key", key_id)

    return {"revoked": key_id}


# === Constitution/Policy ===


class ConstitutionUpdate(BaseModel):
    """Constitution update request."""

    rules: list[str]


@router.get("/constitution", summary="Get constitution", auth=AuthBearer())
async def get_constitution(request: HttpRequest) -> dict:
    """Get the agent constitution/policy rules.

    📚 ISO Doc: Returns governance rules
    """
    await authorize(request, action="system:view", resource="gateway")
    from services.common.constitution_store import ConstitutionStore

    tenant_id = request.headers.get("X-Tenant-Id", "default")
    store = ConstitutionStore()
    await store.ensure_schema()
    rules = await store.get(tenant_id=tenant_id)

    return {"tenant_id": tenant_id, "rules": rules}


@router.put("/constitution", summary="Update constitution", auth=AuthBearer())
async def update_constitution(request: HttpRequest, body: ConstitutionUpdate) -> dict:
    """Update constitution rules."""
    await authorize(request, action="system:security_policy", resource="gateway")
    from services.common.constitution_store import ConstitutionStore

    tenant_id = request.headers.get("X-Tenant-Id", "default")
    store = ConstitutionStore()
    await store.ensure_schema()
    await store.update(identifier=tenant_id, changes={"rules": body.rules})

    return {"status": "updated", "tenant_id": tenant_id}


# === AV/Status ===


@router.get("/av", summary="Get AV status", auth=AuthBearer())
async def get_av_status(request: HttpRequest) -> dict:
    """Get antivirus/content scan status.

    🔒 Security: Scan capability is system configuration, not public state.
    """
    await authorize(request, action="system:view", resource="gateway")

    av_enabled = getattr(settings, "AV_SCAN_ENABLED", False)
    return {"av_enabled": av_enabled, "status": "operational" if av_enabled else "disabled"}
