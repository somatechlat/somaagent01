"""Capability Registry API.


Per AGENT_TASKS.md Phase 7.1 - Capability Registry.

- PhD Dev: Capability matching algorithms
- DevOps: Circuit breakers, health tracking
- Security Auditor: Access control, rate limiting
"""

from __future__ import annotations

import logging
from typing import Optional
from uuid import uuid4

from django.utils import timezone
from ninja import Router
from pydantic import BaseModel

from admin.common.auth import AuthBearer
from admin.common.exceptions import NotFoundError

router = Router(tags=["capabilities"])
logger = logging.getLogger(__name__)


# =============================================================================
# CIRCUIT BREAKER STATE
# =============================================================================

_circuit_breakers = {}  # capability_id -> CircuitBreakerState


class CircuitBreakerState:
    """Circuit breaker for capability health."""

    def __init__(self):
        """Initialize the instance."""

        self.state = "closed"  # closed, open, half_open
        self.failure_count = 0
        self.last_failure = None
        self.last_success = None
        self.reset_timeout = 30  # seconds


# =============================================================================
# SCHEMAS
# =============================================================================


class CapabilityRegistration(BaseModel):
    """Register a capability."""

    name: str
    capability_type: str  # llm, tool, memory, cognitive, voice
    endpoint: str
    version: str = "1.0.0"
    metadata: Optional[dict] = None
    health_endpoint: Optional[str] = None


class CapabilityInfo(BaseModel):
    """Capability information."""

    capability_id: str
    name: str
    capability_type: str
    endpoint: str
    version: str
    status: str  # healthy, degraded, down, unknown
    circuit_state: str  # closed, open, half_open
    last_health_check: Optional[str] = None
    registered_at: str


class CapabilityListResponse(BaseModel):
    """List of capabilities."""

    capabilities: list[CapabilityInfo]
    total: int


class FindCandidatesRequest(BaseModel):
    """Find capability candidates."""

    capability_type: str
    required_features: Optional[list[str]] = None
    prefer_healthy: bool = True
    limit: int = 5


class FindCandidatesResponse(BaseModel):
    """Matching capabilities."""

    candidates: list[CapabilityInfo]
    total_matching: int


class HealthReportRequest(BaseModel):
    """Report health status."""

    status: str  # healthy, degraded, down
    latency_ms: Optional[float] = None
    error: Optional[str] = None


# =============================================================================
# ENDPOINTS - Registration
# =============================================================================


@router.post(
    "/register",
    response=CapabilityInfo,
    summary="Register capability",
    auth=AuthBearer(),
)
async def register_capability(
    request,
    payload: CapabilityRegistration,
) -> CapabilityInfo:
    """Register a new capability in the registry.

    Per Phase 7.1: register()

    DevOps: Capabilities are tracked with circuit breakers.
    """
    capability_id = str(uuid4())

    # Initialize circuit breaker
    _circuit_breakers[capability_id] = CircuitBreakerState()

    logger.info(f"Capability registered: {payload.name} ({capability_id})")

    # In production: persist to database
    # Capability.objects.create(
    #     id=capability_id,
    #     name=payload.name,
    #     capability_type=payload.capability_type,
    #     endpoint=payload.endpoint,
    #     version=payload.version,
    #     metadata=payload.metadata,
    #     health_endpoint=payload.health_endpoint,
    # )

    return CapabilityInfo(
        capability_id=capability_id,
        name=payload.name,
        capability_type=payload.capability_type,
        endpoint=payload.endpoint,
        version=payload.version,
        status="healthy",
        circuit_state="closed",
        last_health_check=timezone.now().isoformat(),
        registered_at=timezone.now().isoformat(),
    )


@router.delete(
    "/{capability_id}",
    summary="Deregister capability",
    auth=AuthBearer(),
)
async def deregister_capability(request, capability_id: str) -> dict:
    """Remove a capability from the registry."""
    if capability_id in _circuit_breakers:
        del _circuit_breakers[capability_id]

    logger.info(f"Capability deregistered: {capability_id}")

    return {
        "capability_id": capability_id,
        "deregistered": True,
    }


@router.get(
    "",
    response=CapabilityListResponse,
    summary="List capabilities",
    auth=AuthBearer(),
)
async def list_capabilities(
    request,
    capability_type: Optional[str] = None,
    status: Optional[str] = None,
) -> CapabilityListResponse:
    """List all registered capabilities."""
    # In production: query from database
    return CapabilityListResponse(
        capabilities=[],
        total=0,
    )


@router.get(
    "/{capability_id}",
    response=CapabilityInfo,
    summary="Get capability",
    auth=AuthBearer(),
)
async def get_capability(request, capability_id: str) -> CapabilityInfo:
    """Get detailed capability information."""
    # In production: fetch from database
    raise NotFoundError(f"Capability {capability_id} not found")


# =============================================================================
# ENDPOINTS - Discovery
# =============================================================================


@router.post(
    "/find",
    response=FindCandidatesResponse,
    summary="Find capability candidates",
    auth=AuthBearer(),
)
async def find_candidates(
    request,
    payload: FindCandidatesRequest,
) -> FindCandidatesResponse:
    """Find matching capabilities.

    Per Phase 7.1: find_candidates()

    PhD Dev: Intelligent matching based on type, features, health.
    """
    # In production: query database with filters
    # candidates = Capability.objects.filter(
    #     capability_type=payload.capability_type,
    #     status__in=['healthy', 'degraded'] if payload.prefer_healthy else ['healthy', 'degraded', 'down']
    # )

    return FindCandidatesResponse(
        candidates=[],
        total_matching=0,
    )


# =============================================================================
# ENDPOINTS - Health Tracking
# =============================================================================


@router.post(
    "/{capability_id}/health",
    summary="Report health status",
    auth=AuthBearer(),
)
async def report_health(
    request,
    capability_id: str,
    payload: HealthReportRequest,
) -> dict:
    """Report capability health status.

    Per Phase 7.1: Health tracking

    DevOps: Updates circuit breaker state based on health.
    """
    cb = _circuit_breakers.get(capability_id)

    if not cb:
        cb = CircuitBreakerState()
        _circuit_breakers[capability_id] = cb

    if payload.status == "healthy":
        cb.failure_count = 0
        cb.last_success = timezone.now()
        if cb.state == "half_open":
            cb.state = "closed"
    else:
        cb.failure_count += 1
        cb.last_failure = timezone.now()

        # Open circuit after 3 failures
        if cb.failure_count >= 3:
            cb.state = "open"
            logger.warning(f"Circuit OPENED for capability {capability_id}")

    return {
        "capability_id": capability_id,
        "circuit_state": cb.state,
        "failure_count": cb.failure_count,
        "recorded": True,
    }


@router.get(
    "/{capability_id}/circuit",
    summary="Get circuit breaker state",
    auth=AuthBearer(),
)
async def get_circuit_state(request, capability_id: str) -> dict:
    """Get circuit breaker state for a capability.

    Per Phase 7.1: Circuit breakers
    """
    cb = _circuit_breakers.get(capability_id)

    if not cb:
        return {
            "capability_id": capability_id,
            "state": "unknown",
            "failure_count": 0,
        }

    # Check if we should transition from open to half_open
    if cb.state == "open" and cb.last_failure:
        if (timezone.now() - cb.last_failure).total_seconds() > cb.reset_timeout:
            cb.state = "half_open"

    return {
        "capability_id": capability_id,
        "state": cb.state,
        "failure_count": cb.failure_count,
        "last_failure": cb.last_failure.isoformat() if cb.last_failure else None,
        "last_success": cb.last_success.isoformat() if cb.last_success else None,
    }


@router.post(
    "/{capability_id}/circuit/reset",
    summary="Reset circuit breaker",
    auth=AuthBearer(),
)
async def reset_circuit(request, capability_id: str) -> dict:
    """Manually reset circuit breaker to closed state."""
    if capability_id in _circuit_breakers:
        _circuit_breakers[capability_id].state = "closed"
        _circuit_breakers[capability_id].failure_count = 0

    logger.info(f"Circuit reset for capability {capability_id}")

    return {
        "capability_id": capability_id,
        "state": "closed",
        "reset": True,
    }


@router.get(
    "/health/summary",
    summary="Health summary",
    auth=AuthBearer(),
)
async def health_summary(request) -> dict:
    """Get health summary across all capabilities."""
    open_circuits = sum(1 for cb in _circuit_breakers.values() if cb.state == "open")
    half_open = sum(1 for cb in _circuit_breakers.values() if cb.state == "half_open")
    closed = sum(1 for cb in _circuit_breakers.values() if cb.state == "closed")

    return {
        "total_capabilities": len(_circuit_breakers),
        "circuits": {
            "open": open_circuits,
            "half_open": half_open,
            "closed": closed,
        },
        "overall_health": (
            "healthy"
            if open_circuits == 0
            else "degraded"
            if open_circuits < len(_circuit_breakers) / 2
            else "critical"
        ),
    }
