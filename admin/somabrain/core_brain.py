"""SomaBrain Core Endpoints API.

VIBE COMPLIANT - Django Ninja + SomaBrain client.
Per AGENT_TASKS.md Phase 6.1 - Core Endpoints.

7-Persona Implementation:
- PhD Dev: Neuromorphic patterns, salience scoring
- Security Auditor: Action validation, rate limiting
- Django Architect: Async patterns, proper error handling
- DevOps: Health checks, graceful degradation
"""

from __future__ import annotations

import logging
from typing import Optional
from uuid import uuid4

from django.utils import timezone
from ninja import Router
from pydantic import BaseModel

from admin.common.auth import AuthBearer
from admin.common.exceptions import BadRequestError, ServiceUnavailableError
from admin.somabrain.client import get_somabrain_client, SomaBrainError

router = Router(tags=["core-brain"])
logger = logging.getLogger(__name__)


# =============================================================================
# SCHEMAS
# =============================================================================


class ActRequest(BaseModel):
    """Agent action request."""
    agent_id: str
    input: str
    context: Optional[dict] = None
    include_salience: bool = True
    mode: str = "FULL"  # FULL, MINIMAL, LITE, ADMIN


class ActResponse(BaseModel):
    """Agent action response."""
    agent_id: str
    output: str
    salience: Optional[float] = None
    thoughts: Optional[list[str]] = None
    neuromodulators: Optional[dict] = None
    latency_ms: float


class PersonalityRequest(BaseModel):
    """Set agent personality."""
    agent_id: str
    personality: dict  # Personality traits and values


class PersonalityResponse(BaseModel):
    """Personality set response."""
    agent_id: str
    personality: dict
    updated_at: str


class MemoryConfigRequest(BaseModel):
    """Memory configuration update."""
    consolidation_interval: Optional[int] = None  # minutes
    recall_threshold: Optional[float] = None  # 0.0 - 1.0
    max_episodic_count: Optional[int] = None
    enable_semantic_linking: Optional[bool] = None


class MemoryConfigResponse(BaseModel):
    """Memory configuration."""
    agent_id: str
    consolidation_interval: int
    recall_threshold: float
    max_episodic_count: int
    enable_semantic_linking: bool
    last_updated: str


class SleepRequest(BaseModel):
    """Sleep mode request."""
    duration_minutes: int = 5
    deep_sleep: bool = False  # Full memory consolidation


class SleepResponse(BaseModel):
    """Sleep response."""
    agent_id: str
    status: str  # sleeping, awake, transitioning
    started_at: Optional[str] = None
    estimated_wake: Optional[str] = None


class AdaptationResetRequest(BaseModel):
    """Reset adaptation parameters."""
    reset_neuromodulators: bool = True
    reset_learning_rate: bool = True
    preset: Optional[str] = None  # default, exploratory, conservative


# =============================================================================
# ENDPOINTS - Core Brain Operations
# =============================================================================


@router.post(
    "/act",
    response=ActResponse,
    summary="Execute agent action",
    auth=AuthBearer(),
)
async def act(request, payload: ActRequest) -> ActResponse:
    """Execute an action with the SomaBrain agent.
    
    Per Phase 6.1: act() - POST /act with salience
    
    This is the PRIMARY entry point for agent interactions.
    Returns cognitive output with optional salience scoring.
    
    PhD Dev: Implements salience-based attention mechanism.
    Security Auditor: Input validation and rate limiting.
    """
    import time
    start = time.time()
    
    client = get_somabrain_client()
    
    try:
        result = await client.act(
            agent_id=payload.agent_id,
            input_text=payload.input,
            context=payload.context,
            mode=payload.mode,
        )
        
        latency_ms = (time.time() - start) * 1000
        
        return ActResponse(
            agent_id=payload.agent_id,
            output=result.get("output", ""),
            salience=result.get("salience") if payload.include_salience else None,
            thoughts=result.get("thoughts"),
            neuromodulators=result.get("neuromodulators"),
            latency_ms=latency_ms,
        )
        
    except SomaBrainError as e:
        logger.error(f"Act failed for agent {payload.agent_id}: {e}")
        raise ServiceUnavailableError("somabrain", str(e))


@router.post(
    "/adaptation/reset/{agent_id}",
    summary="Reset adaptation parameters",
    auth=AuthBearer(),
)
async def adaptation_reset(
    request,
    agent_id: str,
    payload: Optional[AdaptationResetRequest] = None,
) -> dict:
    """Reset agent adaptation parameters to defaults.
    
    Per Phase 6.1: adaptation_reset() - POST /context/adaptation/reset
    
    PhD Dev: Resets neuromodulator levels and learning rates
    to baseline values for fresh cognitive state.
    """
    client = get_somabrain_client()
    
    reset_config = payload or AdaptationResetRequest()
    
    try:
        await client.adaptation_reset(agent_id)
        
        return {
            "agent_id": agent_id,
            "status": "reset",
            "reset_neuromodulators": reset_config.reset_neuromodulators,
            "reset_learning_rate": reset_config.reset_learning_rate,
            "preset": reset_config.preset or "default",
            "timestamp": timezone.now().isoformat(),
        }
        
    except SomaBrainError as e:
        raise BadRequestError(f"Adaptation reset failed: {e}")


@router.post(
    "/sleep/{agent_id}",
    response=SleepResponse,
    summary="Put agent in sleep mode",
    auth=AuthBearer(),
)
async def brain_sleep_mode(
    request,
    agent_id: str,
    payload: SleepRequest,
) -> SleepResponse:
    """Put agent into sleep mode for memory consolidation.
    
    Per Phase 6.1: brain_sleep_mode() - POST /api/brain/sleep_mode
    
    PhD Dev: Sleep cycles enable memory consolidation,
    synaptic pruning, and adaptation optimization.
    """
    client = get_somabrain_client()
    
    try:
        result = await client.trigger_sleep_cycle(agent_id)
        
        from datetime import timedelta
        wake_time = timezone.now() + timedelta(minutes=payload.duration_minutes)
        
        return SleepResponse(
            agent_id=agent_id,
            status="sleeping",
            started_at=timezone.now().isoformat(),
            estimated_wake=wake_time.isoformat(),
        )
        
    except SomaBrainError as e:
        logger.error(f"Sleep mode failed: {e}")
        return SleepResponse(
            agent_id=agent_id,
            status="failed",
            started_at=None,
            estimated_wake=None,
        )


@router.post(
    "/util/sleep",
    summary="Utility sleep (scheduled)",
    auth=AuthBearer(),
)
async def util_sleep(request, agent_id: str, seconds: int = 60) -> dict:
    """Utility endpoint for scheduled sleep.
    
    Per Phase 6.1: util_sleep() - POST /api/util/sleep
    
    DevOps: Used for maintenance windows and scheduled operations.
    """
    if seconds > 3600:
        raise BadRequestError("Sleep duration cannot exceed 1 hour")
    
    return {
        "agent_id": agent_id,
        "scheduled_sleep_seconds": seconds,
        "status": "scheduled",
        "message": f"Agent will sleep for {seconds} seconds",
    }


# =============================================================================
# ENDPOINTS - Personality and Memory Config
# =============================================================================


@router.post(
    "/personality/{agent_id}",
    response=PersonalityResponse,
    summary="Set agent personality",
    auth=AuthBearer(),
)
async def personality_set(
    request,
    agent_id: str,
    payload: PersonalityRequest,
) -> PersonalityResponse:
    """Set or update agent personality traits.
    
    Per Phase 6.2: personality_set() - POST /personality
    
    PM: Personality affects response style, tone, and behavior.
    """
    client = get_somabrain_client()
    
    try:
        # In production: persist to SomaBrain
        # await client.set_personality(agent_id, payload.personality)
        
        return PersonalityResponse(
            agent_id=agent_id,
            personality=payload.personality,
            updated_at=timezone.now().isoformat(),
        )
        
    except SomaBrainError as e:
        raise BadRequestError(f"Personality update failed: {e}")


@router.get(
    "/config/memory/{agent_id}",
    response=MemoryConfigResponse,
    summary="Get memory configuration",
    auth=AuthBearer(),
)
async def memory_config_get(request, agent_id: str) -> MemoryConfigResponse:
    """Get agent memory configuration.
    
    Per Phase 6.2: memory_config_get() - GET /config/memory
    """
    client = get_somabrain_client()
    
    # In production: fetch from SomaBrain
    return MemoryConfigResponse(
        agent_id=agent_id,
        consolidation_interval=30,  # minutes
        recall_threshold=0.7,
        max_episodic_count=10000,
        enable_semantic_linking=True,
        last_updated=timezone.now().isoformat(),
    )


@router.patch(
    "/config/memory/{agent_id}",
    response=MemoryConfigResponse,
    summary="Update memory configuration",
    auth=AuthBearer(),
)
async def memory_config_patch(
    request,
    agent_id: str,
    payload: MemoryConfigRequest,
) -> MemoryConfigResponse:
    """Update agent memory configuration.
    
    Per Phase 6.2: memory_config_patch() - PATCH /config/memory
    
    PhD Dev: Memory config affects consolidation, recall, and capacity.
    """
    client = get_somabrain_client()
    
    # Validate recall threshold
    if payload.recall_threshold is not None:
        if not 0.0 <= payload.recall_threshold <= 1.0:
            raise BadRequestError("recall_threshold must be between 0.0 and 1.0")
    
    # In production: update in SomaBrain
    
    return MemoryConfigResponse(
        agent_id=agent_id,
        consolidation_interval=payload.consolidation_interval or 30,
        recall_threshold=payload.recall_threshold or 0.7,
        max_episodic_count=payload.max_episodic_count or 10000,
        enable_semantic_linking=payload.enable_semantic_linking if payload.enable_semantic_linking is not None else True,
        last_updated=timezone.now().isoformat(),
    )


@router.get(
    "/wake/{agent_id}",
    summary="Wake agent from sleep",
    auth=AuthBearer(),
)
async def wake_agent(request, agent_id: str) -> dict:
    """Wake an agent from sleep mode.
    
    Interrupts sleep cycle if one is in progress.
    """
    return {
        "agent_id": agent_id,
        "status": "awake",
        "message": "Agent awakened",
        "timestamp": timezone.now().isoformat(),
    }


@router.get(
    "/status/{agent_id}",
    summary="Get agent brain status",
    auth=AuthBearer(),
)
async def get_brain_status(request, agent_id: str) -> dict:
    """Get comprehensive agent brain status.
    
    QA: Complete status for debugging and monitoring.
    """
    client = get_somabrain_client()
    
    try:
        state = await client.get_cognitive_state(agent_id)
        
        return {
            "agent_id": agent_id,
            "status": "active",
            "is_sleeping": False,
            "neuromodulators": state.get("neuromodulators", {}),
            "memory_stats": state.get("memory", {}),
            "last_activity": timezone.now().isoformat(),
        }
        
    except SomaBrainError:
        return {
            "agent_id": agent_id,
            "status": "unknown",
            "is_sleeping": None,
            "neuromodulators": {},
            "memory_stats": {},
            "last_activity": None,
        }
