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
from ninja import Router
from ninja.errors import HttpError

from admin.agents.api.schemas import (
    Agent,
    AgentStats,
    AgentToolsOut,
    AgentToolsUpdate,
    AgentUpdatePayload,
    CapsuleConfigOut,
    CapsuleConfigUpdate,
    CapsuleConfigUpdateResult,
    MultimodalConfig,
)
from admin.agents.services.agent_service import (
    _available_tools,
    _create_agent_and_capsule,
    _get_agent_by_id,
    _get_agent_capsule,
    _get_tenant,
    _list_agents,
    _map_agent_to_schema,
    _resolve_tenant_id,
    _update_agent,
    _update_capsule,
)
from admin.aaas.models.choices import AgentStatus
from admin.common.auth import AuthBearer

router = Router(tags=["agents"])
logger = logging.getLogger(__name__)


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

    logger.info("Agent created: %s (%s)", name, agent.id)

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
    payload: AgentUpdatePayload,
) -> dict:
    """Update agent settings."""
    effective_tenant_id = _resolve_tenant_id(request, None)
    agent = await _get_agent_by_id(agent_id, effective_tenant_id)
    if agent is None:
        raise HttpError(404, f"Agent {agent_id} not found")

    await _update_agent(agent, payload)

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
    """Archive an agent.

    There is no hard delete: AgentStatus has no DELETED state and the row is
    referenced by conversations and audit records. Archived agents drop out
    of every listing, which filters on status.
    """
    tenant_id = _resolve_tenant_id(request, None)
    agent = await _get_agent_by_id(agent_id, tenant_id)
    if not agent:
        raise HttpError(404, "Agent not found")

    @sync_to_async
    def _archive() -> None:
        agent.status = AgentStatus.ARCHIVED
        agent.save(update_fields=["status", "updated_at"])

    await _archive()
    logger.info("Agent archived: %s", agent_id)
    return {"agent_id": agent_id, "deleted": True, "status": AgentStatus.ARCHIVED}


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

    Stored on ``Agent.config["personality"]`` — the same place
    ``admin.agents.services.agent_service`` already reads it from.
    """
    tenant_id = _resolve_tenant_id(request, None)
    agent = await _get_agent_by_id(agent_id, tenant_id)
    if not agent:
        raise HttpError(404, "Agent not found")

    return {
        "agent_id": agent_id,
        "personality": (agent.config or {}).get("personality", {}),
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
    """Update agent personality on ``Agent.config["personality"]``."""
    tenant_id = _resolve_tenant_id(request, None)
    agent = await _get_agent_by_id(agent_id, tenant_id)
    if not agent:
        raise HttpError(404, "Agent not found")

    @sync_to_async
    def _persist() -> None:
        config = agent.config or {}
        config["personality"] = personality
        agent.config = config
        agent.save(update_fields=["config", "updated_at"])

    await _persist()
    return {"agent_id": agent_id, "updated": True, "personality": personality}


@router.get(
    "/{agent_id}/tools",
    response=AgentToolsOut,
    summary="Get tools",
    auth=AuthBearer(),
)
async def get_agent_tools(request, agent_id: str) -> AgentToolsOut:
    """Get agent's enabled tools and the full catalog of available tools.

    PhD Dev: Tool configuration.
    """
    tenant_id = _resolve_tenant_id(request, None)
    agent = await _get_agent_by_id(agent_id, tenant_id)
    if not agent:
        raise HttpError(404, "Agent not found")

    config = agent.config or {}
    enabled = config.get("tools", []) or []
    if isinstance(enabled, str):
        enabled = [enabled]

    return AgentToolsOut(
        agent_id=agent_id,
        available_tools=_available_tools(),
        enabled_tools=list(enabled),
    )


@router.patch(
    "/{agent_id}/tools",
    response=AgentToolsOut,
    summary="Update tools",
    auth=AuthBearer(),
)
async def update_agent_tools(
    request,
    agent_id: str,
    payload: AgentToolsUpdate,
) -> AgentToolsOut:
    """Update agent's enabled tools."""
    from services.tool_executor.tools import AVAILABLE_TOOLS

    tenant_id = _resolve_tenant_id(request, None)
    agent = await _get_agent_by_id(agent_id, tenant_id)
    if not agent:
        raise HttpError(404, "Agent not found")

    valid_tools = set(AVAILABLE_TOOLS.keys())
    enabled = [t for t in payload.tools if t in valid_tools]

    @sync_to_async
    def _persist() -> None:
        config = agent.config or {}
        config["tools"] = enabled
        agent.config = config
        agent.save(update_fields=["config", "updated_at"])

    await _persist()

    return AgentToolsOut(
        agent_id=agent_id,
        available_tools=_available_tools(),
        enabled_tools=enabled,
    )


@router.get(
    "/{agent_id}/memory",
    summary="Get memory config",
    auth=AuthBearer(),
)
async def get_memory_config(request, agent_id: str) -> dict:
    """Get agent memory configuration.

    Stored on ``Agent.config["memory"]``, which ``admin.core.chat_orchestrator``
    and ``admin.core.context.builder`` already read (``recall_limit`` and
    friends). There is no separate memory-config store.
    """
    tenant_id = _resolve_tenant_id(request, None)
    agent = await _get_agent_by_id(agent_id, tenant_id)
    if not agent:
        raise HttpError(404, "Agent not found")

    return {
        "agent_id": agent_id,
        "memory_config": (agent.config or {}).get("memory", {}),
    }


async def _set_agent_status(request, agent_id: str, status: str) -> dict:
    """Set an agent's status on the real Agent row."""
    tenant_id = _resolve_tenant_id(request, None)
    agent = await _get_agent_by_id(agent_id, tenant_id)
    if not agent:
        raise HttpError(404, "Agent not found")

    @sync_to_async
    def _persist() -> None:
        agent.status = status
        agent.save(update_fields=["status", "updated_at"])

    await _persist()
    logger.info("Agent %s -> %s", agent_id, status)
    return {"agent_id": agent_id, "status": status}


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
    return await _set_agent_status(request, agent_id, AgentStatus.ACTIVE)


@router.post(
    "/{agent_id}/pause",
    summary="Pause agent",
    auth=AuthBearer(),
)
async def pause_agent(request, agent_id: str) -> dict:
    """Pause an agent."""
    return await _set_agent_status(request, agent_id, AgentStatus.PAUSED)


@router.post(
    "/{agent_id}/archive",
    summary="Archive agent",
    auth=AuthBearer(),
)
async def archive_agent(request, agent_id: str) -> dict:
    """Archive an agent."""
    return await _set_agent_status(request, agent_id, AgentStatus.ARCHIVED)


# =============================================================================
# ENDPOINTS - Stats
# =============================================================================


@router.get(
    "/{agent_id}/stats",
    response=AgentStats,
    summary="Get agent stats",
    auth=AuthBearer(),
)
async def get_agent_stats(request, agent_id: str) -> AgentStats:
    """Get agent statistics.

    Counted from the real conversation and message rows. Latency is omitted
    rather than reported as 0.0 — nothing in this system records per-message
    timing, so a number here would be invented.
    """
    from admin.chat.models import Conversation, Message

    @sync_to_async
    def _count() -> tuple[int, int]:
        # Message.conversation_id is a plain UUIDField, not a ForeignKey, so
        # there is no reverse relation to aggregate across.
        convs = Conversation.objects.filter(agent_id=agent_id)
        return convs.count(), Message.objects.filter(
            conversation_id__in=concs.values("id")
        ).count()

    conversations, messages = await _count()
    return AgentStats(
        total_conversations=conversations,
        total_messages=messages,
    )


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

    Copies the Agent row and its config/feature_settings. Capsule links are
    ManyToMany and are copied too; the capsule rows themselves are shared,
    not duplicated.
    """
    from django.utils.text import slugify

    from admin.aaas.models import Agent as AgentModel
    from admin.aaas.models import Tenant as TenantModel

    tenant_id = _resolve_tenant_id(request, None)
    source = await _get_agent_by_id(agent_id, tenant_id)
    if not source:
        raise HttpError(404, "Agent not found")

    @sync_to_async
    def _clone():
        target_tenant_id_val = target_tenant_id or str(source.tenant_id)
        if not TenantModel.objects.filter(id=target_tenant_id_val).exists():
            raise HttpError(404, f"Target tenant {target_tenant_id_val} not found")

        clone = AgentModel.objects.create(
            tenant_id=target_tenant_id_val,
            name=new_name,
            slug=slugify(new_name),
            description=source.description,
            status=AgentStatus.PAUSED,
            config=source.config or {},
            feature_settings=source.feature_settings or {},
            primary_capsule=source.primary_capsule,
        )
        clone.capsules.set(source.capsules.all())
        return clone

    clone = await _clone()
    logger.info("Agent cloned: %s -> %s", agent_id, clone.id)

    return {
        "original_agent_id": agent_id,
        "new_agent_id": str(clone.id),
        "name": clone.name,
        "cloned": True,
    }


# =============================================================================
# ENDPOINTS - Multimodal Configuration (SRS 4.1)
# =============================================================================


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


# =============================================================================
# ENDPOINTS - Capsule Configuration
# =============================================================================


@router.get(
    "/{agent_id}/capsule",
    response=CapsuleConfigOut,
    summary="Get agent capsule config",
    auth=AuthBearer(),
)
async def get_agent_capsule_config(request, agent_id: str) -> CapsuleConfigOut:
    """Get the agent's primary capsule configuration."""
    effective_tenant_id = _resolve_tenant_id(request, None)
    capsule = await _get_agent_capsule(agent_id, effective_tenant_id)
    if capsule is None:
        raise HttpError(404, f"Capsule for agent {agent_id} not found")

    return CapsuleConfigOut(
        agent_id=agent_id,
        capsule_id=str(capsule.id),
        name=capsule.name,
        description=capsule.description,
        status=capsule.status,
        system_prompt=capsule.system_prompt,
        personality_traits=capsule.personality_traits,
        neuromodulator_baseline=capsule.neuromodulator_baseline,
        learning_config=capsule.learning_config,
    )


@router.patch(
    "/{agent_id}/capsule",
    response=CapsuleConfigUpdateResult,
    summary="Update agent capsule config",
    auth=AuthBearer(),
)
async def update_agent_capsule_config(
    request,
    agent_id: str,
    payload: CapsuleConfigUpdate,
) -> CapsuleConfigUpdateResult:
    """Update the agent's primary capsule configuration."""
    effective_tenant_id = _resolve_tenant_id(request, None)
    capsule = await _get_agent_capsule(agent_id, effective_tenant_id)
    if capsule is None:
        raise HttpError(404, f"Capsule for agent {agent_id} not found")

    await _update_capsule(capsule, payload)

    return CapsuleConfigUpdateResult(
        agent_id=agent_id,
        capsule_id=str(capsule.id),
        updated=True,
    )
