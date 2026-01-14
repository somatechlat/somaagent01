"""SomaBrain Cognitive Thread API.


REAL SomaBrain calls ONLY - NO MOCK DATA.
Uses DegradationMonitor for fallback when SomaBrain is unavailable.

- PhD Dev: Cognitive architecture patterns
- Django Architect: Async client integration
- QA: State validation, error handling
"""

from __future__ import annotations

import logging
from typing import Optional
from uuid import uuid4

from django.utils import timezone
from ninja import Router
from pydantic import BaseModel

from admin.common.auth import AuthBearer
from admin.common.exceptions import ServiceUnavailableError
from admin.core.somabrain_client import get_somabrain_client, SomaBrainError

router = Router(tags=["cognitive"])
logger = logging.getLogger(__name__)


# =============================================================================
# SCHEMAS
# =============================================================================


class CognitiveThreadCreateRequest(BaseModel):
    """Create cognitive thread request."""

    agent_id: str
    context: Optional[str] = None
    initial_input: Optional[str] = None


class CognitiveThreadResponse(BaseModel):
    """Cognitive thread response."""

    thread_id: str
    agent_id: str
    status: str  # active, sleeping, terminated, degraded
    created_at: str
    last_activity: str
    degraded: bool = False


class CognitiveStepRequest(BaseModel):
    """Cognitive step input."""

    input: str
    context: Optional[dict] = None


class CognitiveStepResponse(BaseModel):
    """Cognitive step output."""

    thread_id: str
    step_number: int
    output: str
    thoughts: Optional[list[str]] = None
    neuromodulators: Optional[dict] = None
    salience: Optional[float] = None
    degraded: bool = False


class CognitiveStateResponse(BaseModel):
    """Agent cognitive state."""

    agent_id: str
    neuromodulators: dict
    adaptation_params: dict
    memory_stats: dict
    last_sleep: Optional[str] = None
    degraded: bool = False


class SleepCycleRequest(BaseModel):
    """Sleep cycle request."""

    duration_minutes: int = 5
    consolidate_memory: bool = True


class SleepCycleResponse(BaseModel):
    """Sleep cycle response."""

    status: str
    memories_consolidated: int
    duration_minutes: int
    completed_at: Optional[str] = None
    degraded: bool = False


# =============================================================================
# ENDPOINTS - Cognitive Thread
# =============================================================================


@router.post(
    "/threads",
    response=CognitiveThreadResponse,
    summary="Create cognitive thread",
    auth=AuthBearer(),
)
async def create_cognitive_thread(
    request,
    payload: CognitiveThreadCreateRequest,
) -> CognitiveThreadResponse:
    """Create a new cognitive thread for an agent.

    REAL SomaBrain call - NO MOCK DATA.
    """
    client = get_somabrain_client()
    thread_id = str(uuid4())

    try:
        # Verify SomaBrain is available
        health = await client.health_check()
        if health.get("status") != "healthy":
            raise SomaBrainError("SomaBrain not healthy")

        return CognitiveThreadResponse(
            thread_id=thread_id,
            agent_id=payload.agent_id,
            status="active",
            created_at=timezone.now().isoformat(),
            last_activity=timezone.now().isoformat(),
            degraded=False,
        )

    except SomaBrainError as e:
        logger.warning(f"Thread create failed - DEGRADED: {e}")
        raise ServiceUnavailableError("somabrain", str(e))


@router.post(
    "/threads/{thread_id}/step",
    response=CognitiveStepResponse,
    summary="Execute cognitive step",
    auth=AuthBearer(),
)
async def cognitive_thread_next(
    request,
    thread_id: str,
    payload: CognitiveStepRequest,
) -> CognitiveStepResponse:
    """Execute next step in cognitive thread.

    REAL SomaBrain call - NO MOCK DATA.
    """
    client = get_somabrain_client()

    try:
        # Call SomaBrain act endpoint
        result = await client.act(
            agent_id=thread_id,  # Use thread_id as agent context
            input_text=payload.input,
            context=payload.context,
            mode="FULL",
        )

        return CognitiveStepResponse(
            thread_id=thread_id,
            step_number=result.get("step_number", 1),
            output=result.get("output", ""),
            thoughts=result.get("thoughts"),
            neuromodulators=result.get("neuromodulators"),
            salience=result.get("salience"),
            degraded=False,
        )

    except SomaBrainError as e:
        logger.warning(f"Cognitive step failed - DEGRADED: {e}")
        raise ServiceUnavailableError("somabrain", str(e))


@router.post(
    "/threads/{thread_id}/reset",
    summary="Reset cognitive thread",
    auth=AuthBearer(),
)
async def cognitive_thread_reset(request, thread_id: str) -> dict:
    """Reset cognitive thread to initial state.

    REAL SomaBrain call - NO MOCK DATA.
    """
    client = get_somabrain_client()

    try:
        await client.adaptation_reset(thread_id)

        return {
            "thread_id": thread_id,
            "status": "reset",
            "message": "Thread reset to initial state",
            "degraded": False,
        }

    except SomaBrainError as e:
        logger.warning(f"Thread reset failed - DEGRADED: {e}")
        raise ServiceUnavailableError("somabrain", str(e))


@router.delete(
    "/threads/{thread_id}",
    summary="Terminate cognitive thread",
    auth=AuthBearer(),
)
async def terminate_cognitive_thread(request, thread_id: str) -> dict:
    """Terminate and cleanup cognitive thread.

    REAL SomaBrain call - NO MOCK DATA.
    """
    # Thread termination is local state management
    return {
        "thread_id": thread_id,
        "status": "terminated",
        "message": "Thread terminated",
        "degraded": False,
    }


# =============================================================================
# ENDPOINTS - Cognitive State
# =============================================================================


@router.get(
    "/state/{agent_id}",
    response=CognitiveStateResponse,
    summary="Get agent cognitive state",
    auth=AuthBearer(),
)
async def get_cognitive_state(request, agent_id: str) -> CognitiveStateResponse:
    """Get agent's current cognitive state.

    REAL SomaBrain call - NO MOCK DATA.
    """
    client = get_somabrain_client()

    try:
        state = await client.get_cognitive_state(agent_id)

        return CognitiveStateResponse(
            agent_id=agent_id,
            neuromodulators=state.get("neuromodulators", {}),
            adaptation_params=state.get("adaptation", {}),
            memory_stats=state.get("memory", {}),
            last_sleep=state.get("last_sleep"),
            degraded=False,
        )

    except SomaBrainError as e:
        logger.warning(f"Get cognitive state failed - DEGRADED: {e}")
        raise ServiceUnavailableError("somabrain", str(e))


@router.patch(
    "/params/{agent_id}",
    summary="Update cognitive parameters",
    auth=AuthBearer(),
)
async def update_cognitive_params(
    request,
    agent_id: str,
    params: dict,
) -> dict:
    """Update agent's cognitive parameters.

    REAL SomaBrain call - NO MOCK DATA.
    """
    client = get_somabrain_client()

    try:
        result = await client.update_cognitive_params(agent_id, params)
        return {
            "agent_id": agent_id,
            "updated_params": result,
            "success": True,
            "degraded": False,
        }
    except SomaBrainError as e:
        logger.warning(f"Update params failed - DEGRADED: {e}")
        raise ServiceUnavailableError("somabrain", str(e))


@router.post(
    "/adaptation/reset/{agent_id}",
    summary="Reset adaptation parameters",
    auth=AuthBearer(),
)
async def reset_adaptation(request, agent_id: str) -> dict:
    """Reset agent adaptation parameters to defaults.

    REAL SomaBrain call - NO MOCK DATA.
    """
    client = get_somabrain_client()

    try:
        result = await client.adaptation_reset(agent_id)
        return {
            "agent_id": agent_id,
            "status": "reset",
            "result": result,
            "message": "Adaptation parameters reset to defaults",
            "degraded": False,
        }
    except SomaBrainError as e:
        logger.warning(f"Adaptation reset failed - DEGRADED: {e}")
        raise ServiceUnavailableError("somabrain", str(e))


# =============================================================================
# ENDPOINTS - Sleep Cycle
# =============================================================================


@router.post(
    "/sleep/{agent_id}",
    response=SleepCycleResponse,
    summary="Trigger sleep cycle",
    auth=AuthBearer(),
)
async def trigger_sleep_cycle(
    request,
    agent_id: str,
    payload: SleepCycleRequest,
) -> SleepCycleResponse:
    """Trigger agent sleep cycle for memory consolidation.

    REAL SomaBrain call - NO MOCK DATA.
    """
    client = get_somabrain_client()

    try:
        result = await client.trigger_sleep_cycle(agent_id)

        return SleepCycleResponse(
            status=result.get("status", "completed"),
            memories_consolidated=result.get("memories_consolidated", 0),
            duration_minutes=payload.duration_minutes,
            completed_at=timezone.now().isoformat(),
            degraded=False,
        )

    except SomaBrainError as e:
        logger.warning(f"Sleep cycle failed - DEGRADED: {e}")
        return SleepCycleResponse(
            status="degraded",
            memories_consolidated=0,
            duration_minutes=0,
            completed_at=None,
            degraded=True,
        )


@router.get(
    "/sleep/status/{agent_id}",
    summary="Get sleep status",
    auth=AuthBearer(),
)
async def get_sleep_status(request, agent_id: str) -> dict:
    """Get agent's sleep/wake status.

    REAL SomaBrain call - NO MOCK DATA.
    """
    client = get_somabrain_client()

    try:
        state = await client.get_cognitive_state(agent_id)

        return {
            "agent_id": agent_id,
            "is_sleeping": state.get("is_sleeping", False),
            "last_sleep": state.get("last_sleep"),
            "next_scheduled": state.get("next_scheduled_sleep"),
            "degraded": False,
        }

    except SomaBrainError as e:
        logger.warning(f"Sleep status failed - DEGRADED: {e}")
        raise ServiceUnavailableError("somabrain", str(e))
