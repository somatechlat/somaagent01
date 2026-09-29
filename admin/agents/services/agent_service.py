"""Agents API - business logic and data access helpers."""

from __future__ import annotations

from typing import Optional

from asgiref.sync import sync_to_async
from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils.text import slugify
from ninja.errors import HttpError

from admin.aaas.models.agents import Agent as AgentModel
from admin.aaas.models.tenants import Tenant
from admin.agents.api.schemas import (
    Agent,
    AgentUpdatePayload,
    CapsuleConfigUpdate,
    ToolInfo,
)
from admin.core.models.core import Capsule


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
        tenant_id=str(agent.tenant.id),
        status=agent.status,
        model=config.get("model", "gpt-4"),
        personality=config.get("personality", {}),
        tools=config.get("tools", []),
        memory_config=config.get("memory", {}),
        capsule_id=str(agent.primary_capsule.id) if agent.primary_capsule else None,
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
    page_qs = qs.select_related("tenant", "primary_capsule").order_by("-created_at")[:limit]
    agents = list(page_qs)
    return agents, total


@sync_to_async
def _get_agent_by_id(agent_id: str, tenant_id: str) -> AgentModel | None:
    """Fetch a single agent by ID and tenant."""
    try:
        return AgentModel.objects.select_related("tenant", "primary_capsule").get(
            id=agent_id, tenant_id=tenant_id
        )
    except AgentModel.DoesNotExist:
        return None


@sync_to_async
def _get_tenant(tenant_id: str) -> Tenant | None:
    """Fetch a tenant by ID."""
    try:
        return Tenant.objects.get(id=tenant_id)
    except Tenant.DoesNotExist:
        return None


@sync_to_async
def _get_agent_capsule(agent_id: str, tenant_id: str) -> Capsule | None:
    """Fetch an agent's primary capsule by agent ID and tenant."""
    try:
        agent = AgentModel.objects.select_related("primary_capsule").get(
            id=agent_id, tenant_id=tenant_id
        )
    except AgentModel.DoesNotExist:
        return None

    return agent.primary_capsule


@sync_to_async
def _update_capsule(
    capsule: Capsule,
    payload: CapsuleConfigUpdate,
) -> None:
    """Persist capsule field updates."""
    if payload.name is not None:
        capsule.name = payload.name
    if payload.description is not None:
        capsule.description = payload.description
    if payload.system_prompt is not None:
        capsule.system_prompt = payload.system_prompt
    if payload.personality_traits is not None:
        capsule.personality_traits = payload.personality_traits
    if payload.neuromodulator_baseline is not None:
        capsule.neuromodulator_baseline = payload.neuromodulator_baseline
    if payload.learning_config is not None:
        capsule.learning_config = payload.learning_config
    capsule.save()


@sync_to_async
def _update_agent(
    agent: AgentModel,
    payload: AgentUpdatePayload,
) -> None:
    """Persist agent field updates."""
    if payload.name is not None:
        agent.name = payload.name
    if payload.description is not None:
        agent.description = payload.description
    if payload.model is not None:
        config = agent.config or {}
        config["model"] = payload.model
        agent.config = config
    agent.save()


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


def _available_tools() -> list[ToolInfo]:
    """Return metadata for all registered tools."""
    from services.tool_executor.tools import AVAILABLE_TOOLS

    return [
        ToolInfo(
            name=tool.name,
            description=tool.__doc__ or tool.name,
            input_schema=tool.input_schema(),
        )
        for tool in AVAILABLE_TOOLS.values()
    ]
