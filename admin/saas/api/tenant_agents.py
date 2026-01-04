"""Tenant Agent Management API.

Pure Django ORM + Django Ninja implementation.

"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional
from uuid import uuid4

from django.conf import settings
from ninja import Query, Router
from pydantic import BaseModel

from admin.common.auth import AuthBearer
from admin.common.exceptions import NotFoundError, ValidationError
from admin.common.responses import api_response, paginated_response
from admin.saas.models import Agent, AgentStatus, Tenant, TenantUser

router = Router(tags=["tenant-agents"])
logger = logging.getLogger(__name__)


# =============================================================================
# SCHEMAS
# =============================================================================


class AgentSchema(BaseModel):
    """Agent schema."""

    id: str
    name: str
    slug: str
    status: str
    tenant_id: str
    chat_model: str
    memory_enabled: bool
    voice_enabled: bool
    created_at: datetime
    conversations: int = 0
    tokens_used: int = 0


class AgentCreateRequest(BaseModel):
    """Create agent request."""

    name: str
    slug: Optional[str] = None
    chat_model: str = None  # Uses settings.SAAS_DEFAULT_CHAT_MODEL if not provided
    memory_enabled: bool = True
    voice_enabled: bool = False


class AgentUpdateRequest(BaseModel):
    """Update agent request."""

    name: Optional[str] = None
    chat_model: Optional[str] = None
    memory_enabled: Optional[bool] = None
    voice_enabled: Optional[bool] = None


class QuotaStatus(BaseModel):
    """Quota status for tenant."""

    agents_used: int
    agents_limit: int
    users_used: int
    users_limit: int
    tokens_used: int
    tokens_limit: int
    storage_used_gb: float
    storage_limit_gb: float
    can_create_agent: bool
    can_invite_user: bool


def _agent_to_schema(agent: Agent) -> AgentSchema:
    """Convert Agent model to schema."""
    config = agent.config or {}
    return AgentSchema(
        id=str(agent.id),
        name=agent.name,
        slug=agent.slug or agent.name.lower().replace(" ", "-"),
        status=agent.status,
        tenant_id=str(agent.tenant_id),
        chat_model=config.get("chat_model", settings.SAAS_DEFAULT_CHAT_MODEL),
        memory_enabled=config.get("memory_enabled", True),
        voice_enabled=config.get("voice_enabled", False),
        created_at=agent.created_at,
        conversations=0,
        tokens_used=0,
    )


def get_tenant_quota(tenant_id: str) -> QuotaStatus:
    """Get quota status for tenant from database."""
    agents_used = Agent.objects.filter(tenant_id=tenant_id).count()
    users_used = TenantUser.objects.filter(tenant_id=tenant_id).count()

    # Get tenant limits from subscription tier
    try:
        tenant = Tenant.objects.select_related("tier").get(id=tenant_id)
        tier = tenant.tier
        if tier and tier.limits:
            agents_limit = tier.limits.get("max_agents", settings.SAAS_DEFAULT_MAX_AGENTS)
            users_limit = tier.limits.get("max_users", settings.SAAS_DEFAULT_MAX_USERS)
            tokens_limit = tier.limits.get(
                "max_tokens_monthly", settings.SAAS_DEFAULT_MAX_TOKENS_MONTHLY
            )
            storage_limit = tier.limits.get("storage_gb", settings.SAAS_DEFAULT_STORAGE_GB)
        else:
            agents_limit = settings.SAAS_DEFAULT_MAX_AGENTS
            users_limit = settings.SAAS_DEFAULT_MAX_USERS
            tokens_limit = settings.SAAS_DEFAULT_MAX_TOKENS_MONTHLY
            storage_limit = settings.SAAS_DEFAULT_STORAGE_GB
    except Tenant.DoesNotExist:
        agents_limit = settings.SAAS_DEFAULT_MAX_AGENTS
        users_limit = settings.SAAS_DEFAULT_MAX_USERS
        tokens_limit = settings.SAAS_DEFAULT_MAX_TOKENS_MONTHLY
        storage_limit = settings.SAAS_DEFAULT_STORAGE_GB

    return QuotaStatus(
        agents_used=agents_used,
        agents_limit=agents_limit,
        users_used=users_used,
        users_limit=users_limit,
        tokens_used=0,
        tokens_limit=tokens_limit,
        storage_used_gb=0.0,
        storage_limit_gb=storage_limit,
        can_create_agent=agents_used < agents_limit,
        can_invite_user=users_used < users_limit,
    )


# =============================================================================
# AGENT MANAGEMENT ENDPOINTS
# =============================================================================


@router.get(
    "/agents",
    summary="List tenant agents",
    auth=AuthBearer(),
)
def list_agents(
    request,
    status: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
) -> dict:
    """List all agents in the tenant."""
    tenant_id = getattr(request.auth, "tenant_id", None) or settings.SAAS_DEFAULT_TENANT_ID

    qs = Agent.objects.filter(tenant_id=tenant_id)

    if status:
        qs = qs.filter(status=status)
    if search:
        qs = qs.filter(name__icontains=search)

    total = qs.count()
    offset = (page - 1) * per_page
    agents = qs.order_by("-created_at")[offset : offset + per_page]

    quota = get_tenant_quota(tenant_id)

    response = paginated_response(
        items=[_agent_to_schema(a).model_dump() for a in agents],
        total=total,
        page=page,
        page_size=per_page,
    )
    response["quota"] = quota.model_dump()
    return response


@router.post(
    "/agents",
    summary="Create new agent",
    auth=AuthBearer(),
)
def create_agent(
    request,
    payload: AgentCreateRequest,
) -> dict:
    """Create a new agent in the tenant."""
    tenant_id = getattr(request.auth, "tenant_id", None) or settings.SAAS_DEFAULT_TENANT_ID

    # Check quota
    quota = get_tenant_quota(tenant_id)
    if not quota.can_create_agent:
        raise ValidationError("Agent limit reached. Upgrade to create more agents.")

    slug = payload.slug or payload.name.lower().replace(" ", "-").replace(".", "")

    # Get tenant for FK
    try:
        tenant = Tenant.objects.get(id=tenant_id)
    except Tenant.DoesNotExist:
        raise NotFoundError("tenant", tenant_id)

    agent = Agent.objects.create(
        id=uuid4(),
        tenant=tenant,
        name=payload.name,
        slug=slug,
        status=AgentStatus.ACTIVE,
        config={
            "chat_model": payload.chat_model or settings.SAAS_DEFAULT_CHAT_MODEL,
            "memory_enabled": payload.memory_enabled,
            "voice_enabled": payload.voice_enabled,
        },
    )

    logger.info(f"Agent created: {payload.name} ({agent.id})")

    return api_response(_agent_to_schema(agent).model_dump(), message="Agent created")


@router.get(
    "/agents/{agent_id}",
    summary="Get agent details",
    auth=AuthBearer(),
)
def get_agent(
    request,
    agent_id: str,
) -> dict:
    """Get a single agent's details."""
    try:
        agent = Agent.objects.get(id=agent_id)
    except Agent.DoesNotExist:
        raise NotFoundError("agent", agent_id)

    return api_response(_agent_to_schema(agent).model_dump())


@router.put(
    "/agents/{agent_id}",
    summary="Update agent",
    auth=AuthBearer(),
)
def update_agent(
    request,
    agent_id: str,
    payload: AgentUpdateRequest,
) -> dict:
    """Update an agent's configuration."""
    try:
        agent = Agent.objects.get(id=agent_id)
    except Agent.DoesNotExist:
        raise NotFoundError("agent", agent_id)

    if payload.name:
        agent.name = payload.name

    config = agent.config or {}
    if payload.chat_model:
        config["chat_model"] = payload.chat_model
    if payload.memory_enabled is not None:
        config["memory_enabled"] = payload.memory_enabled
    if payload.voice_enabled is not None:
        config["voice_enabled"] = payload.voice_enabled
    agent.config = config
    agent.save()

    logger.info(f"Agent updated: {agent_id}")

    return api_response(_agent_to_schema(agent).model_dump(), message="Agent updated")


@router.delete(
    "/agents/{agent_id}",
    summary="Delete agent",
    auth=AuthBearer(),
)
def delete_agent(
    request,
    agent_id: str,
) -> dict:
    """Delete an agent."""
    try:
        agent = Agent.objects.get(id=agent_id)
    except Agent.DoesNotExist:
        raise NotFoundError("agent", agent_id)

    agent.delete()
    logger.info(f"Agent deleted: {agent_id}")

    return api_response({"agent_id": agent_id}, message="Agent deleted")


@router.post(
    "/agents/{agent_id}/start",
    summary="Start agent",
    auth=AuthBearer(),
)
def start_agent(
    request,
    agent_id: str,
) -> dict:
    """Start an agent."""
    try:
        agent = Agent.objects.get(id=agent_id)
    except Agent.DoesNotExist:
        raise NotFoundError("agent", agent_id)

    agent.status = AgentStatus.ACTIVE
    agent.save()
    logger.info(f"Agent started: {agent_id}")

    return api_response({"agent_id": agent_id, "status": "active"}, message="Agent started")


@router.post(
    "/agents/{agent_id}/stop",
    summary="Stop agent",
    auth=AuthBearer(),
)
def stop_agent(
    request,
    agent_id: str,
) -> dict:
    """Stop an agent."""
    try:
        agent = Agent.objects.get(id=agent_id)
    except Agent.DoesNotExist:
        raise NotFoundError("agent", agent_id)

    agent.status = AgentStatus.PAUSED
    agent.save()
    logger.info(f"Agent stopped: {agent_id}")

    return api_response({"agent_id": agent_id, "status": "paused"}, message="Agent stopped")


@router.get(
    "/quota",
    summary="Get tenant quota status",
    auth=AuthBearer(),
)
def get_quota(request) -> dict:
    """Get the current quota status for the tenant."""
    tenant_id = getattr(request.auth, "tenant_id", None) or settings.SAAS_DEFAULT_TENANT_ID
    quota = get_tenant_quota(tenant_id)
    return api_response(quota.model_dump())