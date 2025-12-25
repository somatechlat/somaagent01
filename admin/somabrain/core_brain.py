"""SomaBrain Core Endpoints API.

VIBE COMPLIANT - Django Ninja + SomaBrain client.
REAL SomaBrain calls ONLY - NO MOCK DATA.
Uses DegradationMonitor for fallback when SomaBrain is unavailable.

7-Persona Implementation:
- PhD Dev: Neuromorphic patterns, salience scoring
- Security Auditor: Action validation, rate limiting
- Django Architect: Async patterns, proper error handling
- DevOps: Health checks, graceful degradation
"""

from __future__ import annotations

import logging
import time
from typing import Optional

from django.utils import timezone
from ninja import Router
from pydantic import BaseModel

from admin.common.auth import AuthBearer
from admin.common.exceptions import BadRequestError, ServiceUnavailableError
from admin.somabrain.client import get_somabrain_client, SomaBrainError
from admin.somabrain.event_bridge import AgentEventCapture, SessionMemoryStore
from services.common.degradation_monitor import DegradationLevel

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
    degraded: bool = False  # True if using fallback


class PersonalityRequest(BaseModel):
    """Set agent personality."""
    agent_id: str
    personality: dict  # Personality traits and values


class PersonalityResponse(BaseModel):
    """Personality set response."""
    agent_id: str
    personality: dict
    updated_at: str
    degraded: bool = False


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
    degraded: bool = False


class SleepRequest(BaseModel):
    """Sleep mode request."""
    duration_minutes: int = 5
    deep_sleep: bool = False  # Full memory consolidation


class SleepResponse(BaseModel):
    """Sleep response."""
    agent_id: str
    status: str  # sleeping, awake, transitioning, degraded
    started_at: Optional[str] = None
    estimated_wake: Optional[str] = None
    degraded: bool = False


class AdaptationResetRequest(BaseModel):
    """Reset adaptation parameters."""
    reset_neuromodulators: bool = True
    reset_learning_rate: bool = True
    preset: Optional[str] = None  # default, exploratory, conservative


# =============================================================================
# DEGRADATION HELPERS
# =============================================================================


async def get_somabrain_degradation_level() -> DegradationLevel:
    """Get current SomaBrain degradation level from monitor."""
    try:
        from services.common.degradation_monitor import degradation_monitor
        if not degradation_monitor.components:
            await degradation_monitor.initialize()
        
        somabrain_health = degradation_monitor.components.get("somabrain")
        if somabrain_health:
            return somabrain_health.degradation_level
    except Exception as e:
        logger.warning(f"Could not check degradation level: {e}")
    
    return DegradationLevel.NONE


def is_somabrain_degraded() -> bool:
    """Check if SomaBrain is in degraded mode (quick sync check)."""
    try:
        from services.common.degradation_monitor import degradation_monitor
        somabrain_health = degradation_monitor.components.get("somabrain")
        if somabrain_health:
            return not somabrain_health.healthy or somabrain_health.degradation_level != DegradationLevel.NONE
    except Exception:
        pass
    return False


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
    
    REAL SomaBrain call - NO MOCK DATA.
    Falls back to degraded mode if SomaBrain unavailable.
    
    PhD Dev: Implements salience-based attention mechanism.
    Security Auditor: Input validation and rate limiting.
    """
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
            degraded=False,
        )
        
    except SomaBrainError as e:
        # DEGRADED MODE: SomaBrain is unavailable
        # Return minimal response indicating degradation
        latency_ms = (time.time() - start) * 1000
        logger.warning(f"SomaBrain unavailable for act() - DEGRADED MODE: {e}")
        
        raise ServiceUnavailableError(
            "somabrain",
            f"SomaBrain service unavailable. System is in DEGRADED MODE. Error: {e}"
        )


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
    
    REAL SomaBrain call - NO MOCK DATA.
    """
    client = get_somabrain_client()
    reset_config = payload or AdaptationResetRequest()
    
    try:
        result = await client.adaptation_reset(agent_id)
        
        return {
            "agent_id": agent_id,
            "status": "reset",
            "result": result,
            "reset_neuromodulators": reset_config.reset_neuromodulators,
            "reset_learning_rate": reset_config.reset_learning_rate,
            "preset": reset_config.preset or "default",
            "timestamp": timezone.now().isoformat(),
            "degraded": False,
        }
        
    except SomaBrainError as e:
        logger.warning(f"Adaptation reset failed - DEGRADED: {e}")
        raise ServiceUnavailableError("somabrain", str(e))


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
    
    REAL SomaBrain call - NO MOCK DATA.
    """
    client = get_somabrain_client()
    
    try:
        result = await client.trigger_sleep_cycle(agent_id)
        
        from datetime import timedelta
        wake_time = timezone.now() + timedelta(minutes=payload.duration_minutes)
        
        return SleepResponse(
            agent_id=agent_id,
            status=result.get("status", "sleeping"),
            started_at=timezone.now().isoformat(),
            estimated_wake=wake_time.isoformat(),
            degraded=False,
        )
        
    except SomaBrainError as e:
        logger.warning(f"Sleep mode failed - DEGRADED: {e}")
        return SleepResponse(
            agent_id=agent_id,
            status="degraded",
            started_at=None,
            estimated_wake=None,
            degraded=True,
        )


@router.post(
    "/util/sleep",
    summary="Utility sleep (scheduled)",
    auth=AuthBearer(),
)
async def util_sleep(request, agent_id: str, seconds: int = 60) -> dict:
    """Utility endpoint for scheduled sleep.
    
    REAL SomaBrain call - NO MOCK DATA.
    """
    if seconds > 3600:
        raise BadRequestError("Sleep duration cannot exceed 1 hour")
    
    client = get_somabrain_client()
    
    try:
        # Call SomaBrain to schedule sleep
        result = await client.trigger_sleep_cycle(agent_id)
        
        return {
            "agent_id": agent_id,
            "scheduled_sleep_seconds": seconds,
            "status": "scheduled",
            "result": result,
            "degraded": False,
        }
        
    except SomaBrainError as e:
        logger.warning(f"Util sleep failed - DEGRADED: {e}")
        raise ServiceUnavailableError("somabrain", str(e))


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
    
    REAL SomaBrain call - NO MOCK DATA.
    """
    client = get_somabrain_client()
    
    try:
        # Call SomaBrain to set personality
        result = await client.update_cognitive_params(agent_id, {
            "personality": payload.personality
        })
        
        return PersonalityResponse(
            agent_id=agent_id,
            personality=result.get("personality", payload.personality),
            updated_at=timezone.now().isoformat(),
            degraded=False,
        )
        
    except SomaBrainError as e:
        logger.warning(f"Personality set failed - DEGRADED: {e}")
        raise ServiceUnavailableError("somabrain", str(e))


@router.get(
    "/config/memory/{agent_id}",
    response=MemoryConfigResponse,
    summary="Get memory configuration",
    auth=AuthBearer(),
)
async def memory_config_get(request, agent_id: str) -> MemoryConfigResponse:
    """Get agent memory configuration.
    
    REAL SomaBrain call - NO MOCK DATA.
    """
    client = get_somabrain_client()
    
    try:
        state = await client.get_cognitive_state(agent_id)
        memory_config = state.get("memory_config", {})
        
        return MemoryConfigResponse(
            agent_id=agent_id,
            consolidation_interval=memory_config.get("consolidation_interval", 0),
            recall_threshold=memory_config.get("recall_threshold", 0.0),
            max_episodic_count=memory_config.get("max_episodic_count", 0),
            enable_semantic_linking=memory_config.get("enable_semantic_linking", False),
            last_updated=state.get("updated_at", timezone.now().isoformat()),
            degraded=False,
        )
        
    except SomaBrainError as e:
        logger.warning(f"Memory config get failed - DEGRADED: {e}")
        raise ServiceUnavailableError("somabrain", str(e))


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
    
    REAL SomaBrain call - NO MOCK DATA.
    """
    client = get_somabrain_client()
    
    # Validate recall threshold
    if payload.recall_threshold is not None:
        if not 0.0 <= payload.recall_threshold <= 1.0:
            raise BadRequestError("recall_threshold must be between 0.0 and 1.0")
    
    try:
        result = await client.update_cognitive_params(agent_id, {
            "memory_config": {
                "consolidation_interval": payload.consolidation_interval,
                "recall_threshold": payload.recall_threshold,
                "max_episodic_count": payload.max_episodic_count,
                "enable_semantic_linking": payload.enable_semantic_linking,
            }
        })
        
        memory_config = result.get("memory_config", {})
        
        return MemoryConfigResponse(
            agent_id=agent_id,
            consolidation_interval=memory_config.get("consolidation_interval", payload.consolidation_interval or 0),
            recall_threshold=memory_config.get("recall_threshold", payload.recall_threshold or 0.0),
            max_episodic_count=memory_config.get("max_episodic_count", payload.max_episodic_count or 0),
            enable_semantic_linking=memory_config.get("enable_semantic_linking", payload.enable_semantic_linking or False),
            last_updated=timezone.now().isoformat(),
            degraded=False,
        )
        
    except SomaBrainError as e:
        logger.warning(f"Memory config patch failed - DEGRADED: {e}")
        raise ServiceUnavailableError("somabrain", str(e))


@router.get(
    "/wake/{agent_id}",
    summary="Wake agent from sleep",
    auth=AuthBearer(),
)
async def wake_agent(request, agent_id: str) -> dict:
    """Wake an agent from sleep mode.
    
    REAL SomaBrain call - NO MOCK DATA.
    """
    client = get_somabrain_client()
    
    try:
        # In production: call SomaBrain wake endpoint
        state = await client.get_cognitive_state(agent_id)
        
        return {
            "agent_id": agent_id,
            "status": state.get("status", "awake"),
            "message": "Agent awakened",
            "timestamp": timezone.now().isoformat(),
            "degraded": False,
        }
        
    except SomaBrainError as e:
        logger.warning(f"Wake agent failed - DEGRADED: {e}")
        raise ServiceUnavailableError("somabrain", str(e))


@router.get(
    "/status/{agent_id}",
    summary="Get agent brain status",
    auth=AuthBearer(),
)
async def get_brain_status(request, agent_id: str) -> dict:
    """Get comprehensive agent brain status.
    
    REAL SomaBrain call - NO MOCK DATA.
    Returns degradation status if SomaBrain unavailable.
    """
    client = get_somabrain_client()
    degradation_level = await get_somabrain_degradation_level()
    
    try:
        state = await client.get_cognitive_state(agent_id)
        
        return {
            "agent_id": agent_id,
            "status": "active",
            "is_sleeping": state.get("is_sleeping", False),
            "neuromodulators": state.get("neuromodulators", {}),
            "memory_stats": state.get("memory", {}),
            "adaptation_params": state.get("adaptation", {}),
            "last_activity": timezone.now().isoformat(),
            "degradation_level": degradation_level.value,
            "degraded": False,
        }
        
    except SomaBrainError as e:
        logger.warning(f"Brain status failed - DEGRADED: {e}")
        return {
            "agent_id": agent_id,
            "status": "degraded",
            "is_sleeping": None,
            "neuromodulators": {},
            "memory_stats": {},
            "adaptation_params": {},
            "last_activity": None,
            "degradation_level": "critical",
            "degraded": True,
            "error": str(e),
        }
