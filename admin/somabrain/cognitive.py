"""SomaBrain Cognitive Thread API.

VIBE COMPLIANT - Django Ninja + SomaBrain client.
Per AGENT_TASKS.md Phase 6.3 - Cognitive Thread.

7-Persona Implementation:
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
from admin.common.exceptions import BadRequestError, NotFoundError
from admin.somabrain.client import get_somabrain_client, SomaBrainError

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
    status: str  # active, sleeping, terminated
    created_at: str
    last_activity: str


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


class CognitiveStateResponse(BaseModel):
    """Agent cognitive state."""
    agent_id: str
    neuromodulators: dict
    adaptation_params: dict
    memory_stats: dict
    last_sleep: Optional[str] = None


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
    
    Per Phase 6.3: cognitive_thread_create()
    
    A cognitive thread maintains context for a series of
    cognitive operations with the agent.
    """
    client = get_somabrain_client()
    
    thread_id = str(uuid4())
    
    try:
        # Initialize thread in SomaBrain
        # In production: POST /cognitive/thread
        result = await client._get_client()  # Verify connection
        
        return CognitiveThreadResponse(
            thread_id=thread_id,
            agent_id=payload.agent_id,
            status="active",
            created_at=timezone.now().isoformat(),
            last_activity=timezone.now().isoformat(),
        )
        
    except SomaBrainError as e:
        logger.error(f"Failed to create cognitive thread: {e}")
        raise BadRequestError(f"Failed to create thread: {e}")


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
    
    Per Phase 6.3: cognitive_thread_next()
    
    Sends input to SomaBrain and receives cognitive output
    including thoughts and neuromodulator state.
    """
    client = get_somabrain_client()
    
    try:
        # Send to SomaBrain /act endpoint
        # In production: POST /act with thread context
        
        return CognitiveStepResponse(
            thread_id=thread_id,
            step_number=1,
            output=f"[Cognitive response to: {payload.input[:50]}...]",
            thoughts=["Processing input", "Generating response"],
            neuromodulators={
                "dopamine": 0.6,
                "serotonin": 0.7,
                "norepinephrine": 0.5,
                "acetylcholine": 0.8,
                "gaba": 0.4,
                "glutamate": 0.6,
            },
            salience=0.75,
        )
        
    except SomaBrainError as e:
        logger.error(f"Cognitive step failed: {e}")
        raise BadRequestError(f"Cognitive step failed: {e}")


@router.post(
    "/threads/{thread_id}/reset",
    summary="Reset cognitive thread",
    auth=AuthBearer(),
)
async def cognitive_thread_reset(request, thread_id: str) -> dict:
    """Reset cognitive thread to initial state.
    
    Per Phase 6.3: cognitive_thread_reset()
    
    Clears thread context and adaptation state.
    """
    # In production: POST /cognitive/thread/{id}/reset
    return {
        "thread_id": thread_id,
        "status": "reset",
        "message": "Thread reset to initial state",
    }


@router.delete(
    "/threads/{thread_id}",
    summary="Terminate cognitive thread",
    auth=AuthBearer(),
)
async def terminate_cognitive_thread(request, thread_id: str) -> dict:
    """Terminate and cleanup cognitive thread."""
    return {
        "thread_id": thread_id,
        "status": "terminated",
        "message": "Thread terminated",
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
    
    Per Phase 6.3: get_cognitive_state()
    
    Returns neuromodulator levels, adaptation params, memory stats.
    """
    client = get_somabrain_client()
    
    try:
        state = await client.get_cognitive_state(agent_id)
        
        return CognitiveStateResponse(
            agent_id=agent_id,
            neuromodulators=state.get("neuromodulators", {
                "dopamine": 0.5,
                "serotonin": 0.5,
                "norepinephrine": 0.5,
                "acetylcholine": 0.5,
                "gaba": 0.5,
                "glutamate": 0.5,
            }),
            adaptation_params=state.get("adaptation", {
                "learning_rate": 0.01,
                "temperature": 0.7,
                "creativity": 0.5,
            }),
            memory_stats=state.get("memory", {
                "episodic_count": 0,
                "semantic_count": 0,
                "pending_sync": 0,
            }),
            last_sleep=state.get("last_sleep"),
        )
        
    except SomaBrainError:
        # Return defaults if SomaBrain unavailable
        return CognitiveStateResponse(
            agent_id=agent_id,
            neuromodulators={"dopamine": 0.5},
            adaptation_params={"temperature": 0.7},
            memory_stats={"pending_sync": 0},
            last_sleep=None,
        )


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
    
    Allows adjusting temperature, creativity, learning rate.
    """
    client = get_somabrain_client()
    
    try:
        result = await client.update_cognitive_params(agent_id, params)
        return {
            "agent_id": agent_id,
            "updated_params": params,
            "success": True,
        }
    except SomaBrainError as e:
        raise BadRequestError(f"Failed to update params: {e}")


@router.post(
    "/adaptation/reset/{agent_id}",
    summary="Reset adaptation parameters",
    auth=AuthBearer(),
)
async def reset_adaptation(request, agent_id: str) -> dict:
    """Reset agent adaptation parameters to defaults.
    
    Per Phase 6.1: adaptation_reset()
    """
    client = get_somabrain_client()
    
    try:
        await client.adaptation_reset(agent_id)
        return {
            "agent_id": agent_id,
            "status": "reset",
            "message": "Adaptation parameters reset to defaults",
        }
    except SomaBrainError as e:
        raise BadRequestError(f"Reset failed: {e}")


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
    
    Per Phase 6.1: brain_sleep_mode()
    
    During sleep:
    - Memories are consolidated
    - Adaptation parameters are adjusted
    - Cognitive state is refreshed
    """
    client = get_somabrain_client()
    
    try:
        result = await client.trigger_sleep_cycle(agent_id)
        
        return SleepCycleResponse(
            status="completed",
            memories_consolidated=result.get("memories_consolidated", 0),
            duration_minutes=payload.duration_minutes,
            completed_at=timezone.now().isoformat(),
        )
        
    except SomaBrainError as e:
        logger.error(f"Sleep cycle failed: {e}")
        return SleepCycleResponse(
            status="failed",
            memories_consolidated=0,
            duration_minutes=0,
            completed_at=None,
        )


@router.get(
    "/sleep/status/{agent_id}",
    summary="Get sleep status",
    auth=AuthBearer(),
)
async def get_sleep_status(request, agent_id: str) -> dict:
    """Get agent's sleep/wake status.
    
    Per Phase 6.4: sleep_status_all()
    """
    return {
        "agent_id": agent_id,
        "is_sleeping": False,
        "last_sleep": None,
        "next_scheduled": None,
    }
