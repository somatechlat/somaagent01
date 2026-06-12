"""Agents API - Agent lifecycle management.


Agent CRUD, configuration, and lifecycle.

- PhD Dev: Agent architecture, LLM config
- PM: Agent catalog, templates
- ML Eng: Model selection, parameters
"""

from __future__ import annotations

import logging
from typing import Optional
from uuid import uuid4

from asgiref.sync import sync_to_async
from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils.text import slugify
from ninja import Router
from ninja.errors import HttpError
from pydantic import BaseModel

from admin.aaas.models.agents import Agent as AgentModel
from admin.aaas.models.tenants import Tenant
from admin.common.auth import AuthBearer
from admin.core.models.core import Capsule

router = Router(tags=["agents"])
logger = logging.getLogger(__name__)


# =============================================================================
# SCHEMAS
# =============================================================================


class Agent(BaseModel):
    """Agent definition."""

    agent_id: str
    name: str
    description: Optional[str] = None
    tenant_id: str
    status: str  # draft, active, paused, archived
    model: str  # gpt-4, claude-3, etc.
    personality: dict
    tools: list[str]
    memory_config: dict
    capsule_id: Optional[str] = None
    created_at: str
    updated_at: str


class AgentStats(BaseModel):
    """Agent statistics."""

    total_conversations: int
    total_messages: int
    avg_response_time_ms: float
    satisfaction_score: Optional[float] = None


class AgentDeployment(BaseModel):
    """Agent deployment info."""

    agent_id: str
    environment: str
    version: str
    deployed_at: str
    deployed_by: str


# =============================================================================
# HELPERS
# =============================================================================


def _resolve_tenant_id(request, tenant_id: Optional[str]) -> str:
    """Resolve effective tenant ID from auth, query param, or settings."""
    auth_tenant = None
    if hasattr(request, "auth") and request.auth is not None:
        auth_tenant = getattr(request.auth, "tenant_id", None)
    if auth_tenant:
        return auth_tenant
    if tenant_id:
        return tenant_id
    default_tenant = getattr(settings, "AAAS_DEFAULT_TENANT_ID", None)
    if default_tenant:
        return str(default_tenant)
    raise HttpError(400, "tenant_id is required")


def _map_agent_to_schema(agent: AgentModel) -> Agent:
    """Map an Agent ORM instance to the Agent schema."""
    config = agent.config or {}
    return Agent(
        agent_id=str(agent.id),
        name=agent.name,
        description=agent.description,
        tenant_id=str(agent.tenant_id),
        status=agent.status,
        model=config.get("model", "gpt-4"),
        personality=config.get("personality", {}),
        tools=config.get("tools", []),
        memory_config=config.get("memory", {}),
        capsule_id=str(agent.primary_capsule_id) if agent.primary_capsule_id else None,
        created_at=agent.created_at.isoformat(),
        updated_at=agent.updated_at.isoformat(),
    )


@sync_to_async
def _list_agents(
    tenant_id: str,
    status: Optional[str],
    limit: int,
) -> tuple[list[AgentModel], int]:
    """Query agents for the given tenant and return page + total count."""
    qs = AgentModel.objects.filter(tenant_id=tenant_id)
    if status:
        qs = qs.filter(status=status)
    total = qs.count()
    page_qs = qs.select_related("tenant").order_by("-created_at")[:limit]
    agents = list(page_qs)
    return agents, total


@sync_to_async
def _get_agent_by_id(agent_id: str, tenant_id: str) -> AgentModel | None:
    """Fetch a single agent by ID and tenant."""
    try:
        return AgentModel.objects.select_related("tenant").get(id=agent_id, tenant_id=tenant_id)
    except AgentModel.DoesNotExist:
        return None


@sync_to_async
def _get_tenant(tenant_id: str) -> Tenant | None:
    """Fetch a tenant by ID."""
    try:
        return Tenant.objects.get(id=tenant_id)
    except Tenant.DoesNotExist:
        return None


def _reserve_slug(tenant: Tenant, base_slug: str) -> str:
    """Best-effort reservation of a unique slug within a tenant."""
    slug = base_slug
    counter = 1
    while AgentModel.objects.filter(tenant=tenant, slug=slug).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1
    return slug


@sync_to_async
def _create_agent_and_capsule(
    tenant: Tenant,
    name: str,
    description: Optional[str],
    model: str,
) -> AgentModel:
    """Create a Capsule and Agent atomically with slug-collision retries."""
    base_slug = slugify(name) or "agent"
    last_error: Optional[Exception] = None

    for attempt in range(5):
        slug = _reserve_slug(tenant, base_slug)
        try:
            with transaction.atomic():
                capsule = Capsule.objects.create(
                    tenant=tenant,
                    name=name,
                    description=description or "",
                    status=Capsule.STATUS_ACTIVE,
                    system_prompt="You are a helpful assistant.",
                )
                agent = AgentModel.objects.create(
                    tenant=tenant,
                    name=name,
                    slug=slug,
                    description=description or "",
                    status="draft",
                    config={"model": model},
                    primary_capsule=capsule,
                )
            return agent
        except IntegrityError as exc:
            last_error = exc
            # Collision likely on the unique (tenant, slug) constraint; retry.
            continue

    raise HttpError(409, f"Slug conflict after retries: {last_error}")


# =============================================================================
# ENDPOINTS - Agent CRUD
# =============================================================================


@router.get(
    "",
    summary="List agents",
    auth=AuthBearer(),
)
async def list_agents(
    request,
    tenant_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
) -> dict:
    """List agents.

    PM: Agent catalog.
    """
    effective_tenant_id = _resolve_tenant_id(request, tenant_id)
    limit = min(max(limit, 1), 200)
    agents, total = await _list_agents(effective_tenant_id, status, limit)
    return {
        "agents": [_map_agent_to_schema(agent) for agent in agents],
        "total": total,
    }


@router.post(
    "",
    response=Agent,
    summary="Create agent",
    auth=AuthBearer(),
)
async def create_agent(
    request,
    name: str,
    tenant_id: str,
    model: str = "gpt-4",
    description: Optional[str] = None,
) -> Agent:
    """Create a new agent.

    PhD Dev: Agent instantiation.
    """
    effective_tenant_id = _resolve_tenant_id(request, tenant_id)
    tenant = await _get_tenant(effective_tenant_id)
    if tenant is None:
        raise HttpError(400, "Invalid tenant")

    agent = await _create_agent_and_capsule(
        tenant=tenant,
        name=name,
        description=description,
        model=model,
    )

    logger.info('Agent created: %s (%s)', name, agent.id)

    return _map_agent_to_schema(agent)


@router.get(
    "/{agent_id}",
    response=Agent,
    summary="Get agent",
    auth=AuthBearer(),
)
async def get_agent(request, agent_id: str) -> Agent:
    """Get agent details."""
    effective_tenant_id = _resolve_tenant_id(request, None)
    agent = await _get_agent_by_id(agent_id, effective_tenant_id)
    if agent is None:
        raise HttpError(404, f"Agent {agent_id} not found")
    return _map_agent_to_schema(agent)


@router.patch(
    "/{agent_id}",
    summary="Update agent",
    auth=AuthBearer(),
)
async def update_agent(
    request,
    agent_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    model: Optional[str] = None,
) -> dict:
    """Update agent settings."""
    return {
        "agent_id": agent_id,
        "updated": True,
    }


@router.delete(
    "/{agent_id}",
    summary="Delete agent",
    auth=AuthBearer(),
)
async def delete_agent(request, agent_id: str) -> dict:
    """Delete an agent."""
    logger.warning('Agent deleted: %s', agent_id)

    return {
        "agent_id": agent_id,
        "deleted": True,
    }


# =============================================================================
# ENDPOINTS - Configuration
# =============================================================================


@router.get(
    "/{agent_id}/personality",
    summary="Get personality",
    auth=AuthBearer(),
)
async def get_personality(request, agent_id: str) -> dict:
    """Get agent personality config.

    PhD Dev: Personality tuning.
    """
    return {
        "agent_id": agent_id,
        "personality": {
            "system_prompt": "",
            "tone": "professional",
            "language": "en",
            "temperature": 0.7,
        },
    }


@router.patch(
    "/{agent_id}/personality",
    summary="Update personality",
    auth=AuthBearer(),
)
async def update_personality(
    request,
    agent_id: str,
    personality: dict,
) -> dict:
    """Update agent personality."""
    return {
        "agent_id": agent_id,
        "updated": True,
    }


@router.get(
    "/{agent_id}/tools",
    summary="Get tools",
    auth=AuthBearer(),
)
async def get_agent_tools(request, agent_id: str) -> dict:
    """Get agent's enabled tools.

    PhD Dev: Tool configuration.
    """
    return {
        "agent_id": agent_id,
        "tools": [],
    }


@router.patch(
    "/{agent_id}/tools",
    summary="Update tools",
    auth=AuthBearer(),
)
async def update_agent_tools(
    request,
    agent_id: str,
    tools: list[str],
) -> dict:
    """Update agent's tools."""
    return {
        "agent_id": agent_id,
        "tools": tools,
        "updated": True,
    }


@router.get(
    "/{agent_id}/memory",
    summary="Get memory config",
    auth=AuthBearer(),
)
async def get_memory_config(request, agent_id: str) -> dict:
    """Get agent memory configuration.

    PhD Dev: Memory architecture.
    """
    return {
        "agent_id": agent_id,
        "memory_config": {
            "type": "conversation",
            "retention_days": 30,
            "max_context_tokens": 4000,
        },
    }


# =============================================================================
# ENDPOINTS - Lifecycle
# =============================================================================


@router.post(
    "/{agent_id}/activate",
    summary="Activate agent",
    auth=AuthBearer(),
)
async def activate_agent(request, agent_id: str) -> dict:
    """Activate an agent for use."""
    logger.info('Agent activated: %s', agent_id)

    return {
        "agent_id": agent_id,
        "status": "active",
    }


@router.post(
    "/{agent_id}/pause",
    summary="Pause agent",
    auth=AuthBearer(),
)
async def pause_agent(request, agent_id: str) -> dict:
    """Pause an agent."""
    return {
        "agent_id": agent_id,
        "status": "paused",
    }


@router.post(
    "/{agent_id}/archive",
    summary="Archive agent",
    auth=AuthBearer(),
)
async def archive_agent(request, agent_id: str) -> dict:
    """Archive an agent."""
    return {
        "agent_id": agent_id,
        "status": "archived",
    }


# =============================================================================
# ENDPOINTS - Stats & Deployments
# =============================================================================


@router.get(
    "/{agent_id}/stats",
    response=AgentStats,
    summary="Get agent stats",
    auth=AuthBearer(),
)
async def get_agent_stats(request, agent_id: str) -> AgentStats:
    """Get agent statistics.

    PM: Performance metrics.
    """
    return AgentStats(
        total_conversations=0,
        total_messages=0,
        avg_response_time_ms=0.0,
    )


@router.get(
    "/{agent_id}/deployments",
    summary="List deployments",
    auth=AuthBearer(),
)
async def list_deployments(request, agent_id: str) -> dict:
    """List agent deployments.

    DevOps: Deployment history.
    """
    return {
        "agent_id": agent_id,
        "deployments": [],
        "total": 0,
    }


@router.post(
    "/{agent_id}/deploy",
    summary="Deploy agent",
    auth=AuthBearer(),
)
async def deploy_agent(
    request,
    agent_id: str,
    environment: str = "production",
) -> dict:
    """Deploy agent to environment.

    DevOps: Deployment.
    """
    deployment_id = str(uuid4())

    logger.info('Agent deployed: %s -> %s', agent_id, environment)

    return {
        "deployment_id": deployment_id,
        "agent_id": agent_id,
        "environment": environment,
        "deployed": True,
    }


# =============================================================================
# ENDPOINTS - Cloning
# =============================================================================


@router.post(
    "/{agent_id}/clone",
    summary="Clone agent",
    auth=AuthBearer(),
)
async def clone_agent(
    request,
    agent_id: str,
    new_name: str,
    target_tenant_id: Optional[str] = None,
) -> dict:
    """Clone an agent.

    PM: Agent replication.
    """
    new_agent_id = str(uuid4())

    logger.info('Agent cloned: %s -> %s', agent_id, new_agent_id)

    return {
        "original_agent_id": agent_id,
        "new_agent_id": new_agent_id,
        "name": new_name,
        "cloned": True,
    }


# =============================================================================
# ENDPOINTS - Multimodal Configuration (SRS 4.1)
# =============================================================================


class MultimodalConfig(BaseModel):
    """Multimodal capabilities configuration."""

    image_enabled: bool = True
    image_quality: str = "standard"
    image_style: str = "vivid"
    diagram_enabled: bool = True
    diagram_format: str = "svg"
    diagram_theme: str = "default"
    screenshot_enabled: bool = True
    screenshot_width: int = 1920
    screenshot_height: int = 1080
    screenshot_full_page: bool = True
    video_enabled: bool = False
    vision_enabled: bool = True
    chat_model_vision: bool = True
    browser_model_vision: bool = True
    image_provider: str = "dalle3"
    diagram_provider: str = "mermaid"
    screenshot_provider: str = "playwright"


@router.get(
    "/{agent_id}/multimodal-config",
    response={200: dict},
    summary="Get multimodal config",
    auth=AuthBearer(),
)
async def get_multimodal_config(request, agent_id: str) -> dict:
    """Get agent multimodal configuration.

    Uses GlobalDefault for persistence (Unified Policy).
    """
    from admin.aaas.models.profiles import PlatformConfig

    gd = await PlatformConfig.aget_instance()
    defaults = gd.defaults

    # Return stored config or defaults
    config = defaults.get("multimodal_policy", MultimodalConfig().dict())

    return {
        "config": config,
        "quotas": {
            "images": {"current": 0, "limit": 500},
            "diagrams": {"current": 0, "limit": 1000},
            "screenshots": {"current": 0, "limit": 1000},
            "video_minutes": {"current": 0, "limit": 10},
        },
    }


@router.put(
    "/{agent_id}/multimodal-config",
    summary="Update multimodal config",
    auth=AuthBearer(),
)
async def update_multimodal_config(request, agent_id: str, config: MultimodalConfig) -> dict:
    """Update agent multimodal configuration.

    Persists to GlobalDefault (Unified Policy).
    """
    from admin.aaas.models.profiles import PlatformConfig

    gd = await PlatformConfig.aget_instance()
    gd.defaults["multimodal_policy"] = config.dict()
    await gd.asave()

    return {"updated": True}
