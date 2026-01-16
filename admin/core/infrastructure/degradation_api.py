"""
Degradation Mode API for SomaAgent01.


Per SAAS_ADMIN_SRS.md - Infrastructure Administration.

Endpoints:
- GET /status - Current degradation status
- GET /history - Degradation history records
- GET /components - All component health states
- GET /dependencies - Service dependency graph
- POST /start - Start monitoring
- POST /stop - Stop monitoring
"""

from __future__ import annotations

import logging
from typing import List, Optional

from django.utils import timezone
from ninja import Router
from pydantic import BaseModel

from services.common.degradation_monitor import (
    degradation_monitor,
)

router = Router(tags=["degradation"])
logger = logging.getLogger(__name__)


# =============================================================================
# SCHEMAS
# =============================================================================


class ComponentHealthSchema(BaseModel):
    """Health status of a single component."""

    name: str
    healthy: bool
    response_time: float
    error_rate: float
    degradation_level: str
    circuit_state: str
    last_check: float


class DegradationStatusSchema(BaseModel):
    """Overall system degradation status."""

    overall_level: str
    affected_components: List[str]
    healthy_components: List[str]
    total_components: int
    timestamp: float
    recommendations: List[str]
    mitigation_actions: List[str]


class HistoryRecordSchema(BaseModel):
    """A degradation history record."""

    timestamp: float
    component_name: str
    degradation_level: str
    healthy: bool
    response_time: float
    error_rate: float
    event_type: str


class DependencySchema(BaseModel):
    """Service dependency information."""

    service: str
    depends_on: List[str]
    depended_by: List[str]


class MonitoringStatusSchema(BaseModel):
    """Monitoring status response."""

    monitoring_active: bool
    message: str
    timestamp: str


# =============================================================================
# ENDPOINTS
# =============================================================================


@router.get(
    "/status",
    response=DegradationStatusSchema,
    summary="Get current degradation status",
)
async def get_degradation_status(request) -> DegradationStatusSchema:
    """
    Get the current degradation status of the entire system.

    Returns:
    - overall_level: NONE, MINOR, MODERATE, SEVERE, or CRITICAL
    - affected_components: List of degraded component names
    - healthy_components: List of healthy component names
    - recommendations: Suggested actions based on current state
    - mitigation_actions: Automated actions that can be taken
    """
    # Initialize if not already done
    if not degradation_monitor.components:
        await degradation_monitor.initialize()

    status = await degradation_monitor.get_degradation_status()

    return DegradationStatusSchema(
        overall_level=status.overall_level.value,
        affected_components=status.affected_components,
        healthy_components=status.healthy_components,
        total_components=status.total_components,
        timestamp=status.timestamp,
        recommendations=status.recommendations,
        mitigation_actions=status.mitigation_actions,
    )


@router.get(
    "/components",
    response=List[ComponentHealthSchema],
    summary="Get all component health states",
)
async def get_component_health(request) -> List[ComponentHealthSchema]:
    """
    Get health status of all monitored components.

    Returns detailed metrics for each component:
    - response_time: Latest response time in seconds
    - error_rate: Error rate (0.0 to 1.0)
    - degradation_level: Current degradation level
    - circuit_state: CLOSED, OPEN, or HALF_OPEN
    """
    if not degradation_monitor.components:
        await degradation_monitor.initialize()

    components = []
    for comp in degradation_monitor.components.values():
        components.append(
            ComponentHealthSchema(
                name=comp.name,
                healthy=comp.healthy,
                response_time=comp.response_time,
                error_rate=comp.error_rate,
                degradation_level=comp.degradation_level.value,
                circuit_state=comp.circuit_state.value,
                last_check=comp.last_check,
            )
        )

    return components


@router.get(
    "/history",
    response=List[HistoryRecordSchema],
    summary="Get degradation history",
)
async def get_degradation_history(
    request,
    limit: int = 100,
    component: Optional[str] = None,
) -> List[HistoryRecordSchema]:
    """
    Get degradation event history.

    Args:
        limit: Maximum number of records (default 100, max 1000)
        component: Filter by component name (optional)

    Returns history records with event types:
    - check: Regular health check
    - failure: Component failure detected
    - recovery: Component recovered
    - cascading: Cascading failure propagated
    """
    limit = min(limit, 1000)

    history = degradation_monitor.get_history(
        limit=limit,
        component_name=component,
    )

    return [
        HistoryRecordSchema(
            timestamp=r["timestamp"],
            component_name=r["component_name"],
            degradation_level=r["degradation_level"],
            healthy=r["healthy"],
            response_time=r["response_time"],
            error_rate=r["error_rate"],
            event_type=r["event_type"],
        )
        for r in history
    ]


@router.get(
    "/dependencies",
    response=List[DependencySchema],
    summary="Get service dependency graph",
)
async def get_dependencies(request) -> List[DependencySchema]:
    """
    Get the service dependency graph.

    Shows which services depend on which, used for
    cascading failure detection and analysis.
    """
    dependencies = []

    for service, deps in degradation_monitor.SERVICE_DEPENDENCIES.items():
        depended_by = degradation_monitor.get_dependent_services(service)
        dependencies.append(
            DependencySchema(
                service=service,
                depends_on=deps,
                depended_by=depended_by,
            )
        )

    return dependencies


@router.post(
    "/start",
    response=MonitoringStatusSchema,
    summary="Start degradation monitoring",
)
async def start_monitoring(request) -> MonitoringStatusSchema:
    """
    Start the continuous degradation monitoring loop.

    The monitoring loop:
    - Runs every 30 seconds
    - Checks all registered components
    - Propagates cascading failures
    - Records metrics to Prometheus
    """
    if degradation_monitor.is_monitoring():
        return MonitoringStatusSchema(
            monitoring_active=True,
            message="Monitoring already active",
            timestamp=timezone.now().isoformat(),
        )

    await degradation_monitor.start_monitoring()
    logger.info("Degradation monitoring started via API")

    return MonitoringStatusSchema(
        monitoring_active=True,
        message="Monitoring started successfully",
        timestamp=timezone.now().isoformat(),
    )


@router.post(
    "/stop",
    response=MonitoringStatusSchema,
    summary="Stop degradation monitoring",
)
async def stop_monitoring(request) -> MonitoringStatusSchema:
    """
    Stop the continuous degradation monitoring loop.
    """
    if not degradation_monitor.is_monitoring():
        return MonitoringStatusSchema(
            monitoring_active=False,
            message="Monitoring not active",
            timestamp=timezone.now().isoformat(),
        )

    await degradation_monitor.stop_monitoring()
    logger.info("Degradation monitoring stopped via API")

    return MonitoringStatusSchema(
        monitoring_active=False,
        message="Monitoring stopped successfully",
        timestamp=timezone.now().isoformat(),
    )


@router.get(
    "/component/{component_name}",
    response=ComponentHealthSchema,
    summary="Get specific component health",
)
async def get_component(request, component_name: str) -> ComponentHealthSchema:
    """
    Get health status of a specific component.
    """
    if not degradation_monitor.components:
        await degradation_monitor.initialize()

    component = degradation_monitor.components.get(component_name)
    if not component:
        from ninja.errors import HttpError

        raise HttpError(404, f"Component '{component_name}' not found")

    return ComponentHealthSchema(
        name=component.name,
        healthy=component.healthy,
        response_time=component.response_time,
        error_rate=component.error_rate,
        degradation_level=component.degradation_level.value,
        circuit_state=component.circuit_state.value,
        last_check=component.last_check,
    )
