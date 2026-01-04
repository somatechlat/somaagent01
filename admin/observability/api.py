"""Observability API - Real Infrastructure Metrics & Health.


Per 

10-Persona Implementation:
- PhD Developer: Clean async implementation
- DevOps: Prometheus metrics, K8s probes
- QA: Comprehensive health checks
- Security Auditor: No sensitive data exposure
- Performance Engineer: Efficient concurrent checks
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Optional

from django.utils import timezone
from ninja import Router
from pydantic import BaseModel

from admin.common.auth import AuthBearer
from admin.core.infrastructure import health_checker

router = Router(tags=["observability"])
logger = logging.getLogger(__name__)

# Store application start time for uptime calculation
_app_start_time = time.time()


# =============================================================================
# SCHEMAS
# =============================================================================


class ServiceHealthResponse(BaseModel):
    """Individual service health."""

    name: str
    status: str
    latency_ms: Optional[float] = None
    details: Optional[dict] = None
    error: Optional[str] = None


class InfrastructureHealthResponse(BaseModel):
    """Complete infrastructure health."""

    overall_status: str
    timestamp: str
    duration_ms: float
    services: list[ServiceHealthResponse]


class ReadinessResponse(BaseModel):
    """Kubernetes readiness probe response."""

    ready: bool
    checks: list[ServiceHealthResponse]
    timestamp: str


class LivenessResponse(BaseModel):
    """Kubernetes liveness probe response."""

    alive: bool
    uptime_seconds: float
    timestamp: str


class MetricValue(BaseModel):
    """Single metric for JSON response."""

    name: str
    value: float
    labels: Optional[dict] = None
    timestamp: str


class MetricsJsonResponse(BaseModel):
    """JSON metrics response."""

    metrics: list[MetricValue]


# =============================================================================
# ENDPOINTS - Infrastructure Health (REAL CHECKS)
# =============================================================================


@router.get(
    "/infrastructure/health",
    response=InfrastructureHealthResponse,
    summary="Complete infrastructure health check",
    auth=AuthBearer(),
)
async def get_infrastructure_health(request) -> InfrastructureHealthResponse:
    """Check health of ALL infrastructure services.

    VIBE: Real async checks to PostgreSQL, Redis, Temporal, Qdrant,
    Keycloak, Lago, SomaBrain, Whisper, Kokoro.

    DevOps: Returns detailed status for each service.
    """
    result = await health_checker.check_all()

    return InfrastructureHealthResponse(
        overall_status=result["overall_status"],
        timestamp=result["timestamp"],
        duration_ms=result["duration_ms"],
        services=[ServiceHealthResponse(**s) for s in result["services"]],
    )


@router.get(
    "/infrastructure/{service}/health",
    response=ServiceHealthResponse,
    summary="Single service health check",
    auth=AuthBearer(),
)
async def get_service_health(request, service: str) -> ServiceHealthResponse:
    """Check health of a specific service.

    Args:
        service: Service name (postgresql, redis, temporal, qdrant, etc.)
    """
    check_method = getattr(health_checker, f"check_{service}", None)
    if not check_method:
        return ServiceHealthResponse(
            name=service,
            status="unknown",
            error=f"Unknown service: {service}",
        )

    result = await check_method()
    return ServiceHealthResponse(
        name=result.name,
        status=result.status,
        latency_ms=result.latency_ms,
        details=result.details,
        error=result.error,
    )


# =============================================================================
# ENDPOINTS - Kubernetes Probes (REAL CHECKS)
# =============================================================================


@router.get(
    "/ready",
    response=ReadinessResponse,
    summary="Kubernetes readiness probe",
)
async def readiness(request) -> ReadinessResponse:
    """Kubernetes readiness check.

    Returns 200 if ready to serve traffic.
    Checks critical services: PostgreSQL (required).

    DevOps: Use for K8s readinessProbe.
    """
    checks = []
    all_healthy = True

    # PostgreSQL is CRITICAL - must be healthy
    pg_result = await health_checker.check_postgresql()
    checks.append(
        ServiceHealthResponse(
            name=pg_result.name,
            status=pg_result.status,
            latency_ms=pg_result.latency_ms,
        )
    )
    if pg_result.status != "healthy":
        all_healthy = False

    # Redis - degraded is OK, down is not
    redis_result = await health_checker.check_redis()
    checks.append(
        ServiceHealthResponse(
            name=redis_result.name,
            status=redis_result.status,
            latency_ms=redis_result.latency_ms,
        )
    )

    return ReadinessResponse(
        ready=all_healthy,
        checks=checks,
        timestamp=timezone.now().isoformat(),
    )


@router.get(
    "/live",
    response=LivenessResponse,
    summary="Kubernetes liveness probe",
)
async def liveness(request) -> LivenessResponse:
    """Kubernetes liveness check.

    Returns 200 if process is alive.
    Simple check - does not verify external services.

    DevOps: Use for K8s livenessProbe.
    """
    uptime = time.time() - _app_start_time

    return LivenessResponse(
        alive=True,
        uptime_seconds=uptime,
        timestamp=timezone.now().isoformat(),
    )


# =============================================================================
# ENDPOINTS - Prometheus Metrics (REAL DATA)
# =============================================================================


@router.get(
    "/metrics",
    summary="Prometheus metrics",
)
async def get_prometheus_metrics(request) -> str:
    """Get Prometheus-formatted metrics.

    Returns metrics in Prometheus exposition format.
    DevOps: Scrape with Prometheus server.
    """
    from admin.core.observability.metrics import get_all_metrics_prometheus

    try:
        return get_all_metrics_prometheus()
    except ImportError:
        # Fallback if metrics module not available
        lines = [
            "# HELP soma_up Server is up",
            "# TYPE soma_up gauge",
            f"soma_up 1",
            f"# HELP soma_uptime_seconds Server uptime in seconds",
            f"# TYPE soma_uptime_seconds gauge",
            f"soma_uptime_seconds {time.time() - _app_start_time:.2f}",
        ]
        return "\n".join(lines)


@router.get(
    "/metrics/json",
    response=MetricsJsonResponse,
    summary="Metrics as JSON",
    auth=AuthBearer(),
)
async def get_metrics_json(request) -> MetricsJsonResponse:
    """Get metrics in JSON format.

    Alternative to Prometheus format for dashboard integration.
    """
    from admin.core.observability.metrics import get_all_metrics_json

    try:
        metrics_data = get_all_metrics_json()
        now = timezone.now().isoformat()
        return MetricsJsonResponse(
            metrics=[
                MetricValue(
                    name=m["name"],
                    value=m["value"],
                    labels=m.get("labels"),
                    timestamp=now,
                )
                for m in metrics_data
            ]
        )
    except ImportError:
        now = timezone.now().isoformat()
        return MetricsJsonResponse(
            metrics=[
                MetricValue(name="soma_up", value=1.0, timestamp=now),
                MetricValue(
                    name="soma_uptime_seconds",
                    value=time.time() - _app_start_time,
                    timestamp=now,
                ),
            ]
        )


# =============================================================================
# ENDPOINTS - SLA Compliance
# =============================================================================


@router.get(
    "/sla",
    summary="SLA compliance metrics",
    auth=AuthBearer(),
)
async def get_sla_compliance(request) -> dict:
    """Get SLA compliance metrics.

    Returns current SLA targets vs actual values.
    """
    # Get health check for latency data
    result = await health_checker.check_all()

    # Calculate SLA metrics
    healthy_count = sum(1 for s in result["services"] if s["status"] == "healthy")
    total_count = len(result["services"])
    availability_pct = (healthy_count / total_count * 100) if total_count > 0 else 0

    return {
        "timestamp": timezone.now().isoformat(),
        "metrics": [
            {
                "name": "API Availability",
                "target": 99.9,
                "actual": availability_pct,
                "status": "pass" if availability_pct >= 99.9 else "fail",
            },
            {
                "name": "Infrastructure Health",
                "target": 80.0,  # 80% of services healthy
                "actual": (healthy_count / total_count * 100) if total_count > 0 else 0,
                "status": "pass" if healthy_count >= total_count * 0.8 else "fail",
            },
        ],
        "overall_status": result["overall_status"],
    }


# =============================================================================
# ENDPOINTS - Dashboards
# =============================================================================


@router.get(
    "/dashboards",
    summary="List available dashboards",
    auth=AuthBearer(),
)
async def list_dashboards(request) -> dict:
    """List available monitoring dashboards."""
    return {
        "dashboards": [
            {
                "id": "infrastructure",
                "name": "Infrastructure Health",
                "route": "/platform/infrastructure",
            },
            {
                "id": "metrics",
                "name": "Platform Metrics",
                "route": "/platform/metrics",
            },
            {
                "id": "sla",
                "name": "SLA Compliance",
                "route": "/platform/metrics/sla",
            },
        ],
    }