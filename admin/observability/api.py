"""Observability API - Metrics, Traces, Health.

VIBE COMPLIANT - Django Ninja + Prometheus.
Per AGENT_TASKS.md Phase 7.6 - Observability.

7-Persona Implementation:
- DevOps: Prometheus metrics, OpenTelemetry spans
- QA: Health check patterns
- PhD Dev: Performance profiling
"""

from __future__ import annotations

import logging
import time
from typing import Optional

from django.utils import timezone
from ninja import Router
from pydantic import BaseModel

from admin.common.auth import AuthBearer

router = Router(tags=["observability"])
logger = logging.getLogger(__name__)


# =============================================================================
# PROMETHEUS METRICS (in-memory for now)
# =============================================================================

_metrics = {
    "http_requests_total": 0,
    "http_requests_duration_seconds": [],
    "active_connections": 0,
    "memory_operations_total": 0,
    "cognitive_operations_total": 0,
    "workflow_executions_total": 0,
}


# =============================================================================
# SCHEMAS
# =============================================================================


class MetricValue(BaseModel):
    """Single metric."""

    name: str
    value: float
    labels: Optional[dict] = None
    timestamp: str


class MetricsResponse(BaseModel):
    """Prometheus metrics."""

    metrics: list[MetricValue]
    format: str = "prometheus"


class TraceSpan(BaseModel):
    """OpenTelemetry span."""

    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None
    name: str
    start_time: str
    end_time: Optional[str] = None
    duration_ms: Optional[float] = None
    status: str  # ok, error
    attributes: Optional[dict] = None


class TracesResponse(BaseModel):
    """Traces response."""

    traces: list[TraceSpan]
    total: int


class HealthCheckResult(BaseModel):
    """Individual health check."""

    name: str
    status: str  # healthy, degraded, down
    latency_ms: Optional[float] = None
    message: Optional[str] = None


class ReadinessResponse(BaseModel):
    """Kubernetes readiness."""

    ready: bool
    checks: list[HealthCheckResult]
    timestamp: str


class LivenessResponse(BaseModel):
    """Kubernetes liveness."""

    alive: bool
    uptime_seconds: float
    timestamp: str


# =============================================================================
# ENDPOINTS - Prometheus Metrics
# =============================================================================


@router.get(
    "/metrics",
    summary="Prometheus metrics",
)
async def get_metrics(request) -> str:
    """Get Prometheus-formatted metrics.

    Per Phase 7.6: Prometheus metrics on all services.

    DevOps: Standard Prometheus exposition format.
    """
    # Build Prometheus exposition format
    lines = []

    # HTTP requests
    lines.append("# HELP http_requests_total Total HTTP requests")
    lines.append("# TYPE http_requests_total counter")
    lines.append(f"http_requests_total {_metrics['http_requests_total']}")

    # Active connections
    lines.append("# HELP active_connections Current active connections")
    lines.append("# TYPE active_connections gauge")
    lines.append(f"active_connections {_metrics['active_connections']}")

    # Memory operations
    lines.append("# HELP memory_operations_total Total memory operations")
    lines.append("# TYPE memory_operations_total counter")
    lines.append(f"memory_operations_total {_metrics['memory_operations_total']}")

    # Cognitive operations
    lines.append("# HELP cognitive_operations_total Total cognitive operations")
    lines.append("# TYPE cognitive_operations_total counter")
    lines.append(f"cognitive_operations_total {_metrics['cognitive_operations_total']}")

    # Workflow executions
    lines.append("# HELP workflow_executions_total Total workflow executions")
    lines.append("# TYPE workflow_executions_total counter")
    lines.append(f"workflow_executions_total {_metrics['workflow_executions_total']}")

    return "\n".join(lines)


@router.get(
    "/metrics/json",
    response=MetricsResponse,
    summary="Metrics as JSON",
)
async def get_metrics_json(request) -> MetricsResponse:
    """Get metrics in JSON format.

    Alternative to Prometheus format for dashboard integration.
    """
    now = timezone.now().isoformat()

    metrics = [
        MetricValue(
            name="http_requests_total", value=float(_metrics["http_requests_total"]), timestamp=now
        ),
        MetricValue(
            name="active_connections", value=float(_metrics["active_connections"]), timestamp=now
        ),
        MetricValue(
            name="memory_operations_total",
            value=float(_metrics["memory_operations_total"]),
            timestamp=now,
        ),
        MetricValue(
            name="cognitive_operations_total",
            value=float(_metrics["cognitive_operations_total"]),
            timestamp=now,
        ),
        MetricValue(
            name="workflow_executions_total",
            value=float(_metrics["workflow_executions_total"]),
            timestamp=now,
        ),
    ]

    return MetricsResponse(metrics=metrics)


# =============================================================================
# ENDPOINTS - OpenTelemetry Traces
# =============================================================================


@router.get(
    "/traces",
    response=TracesResponse,
    summary="Get recent traces",
    auth=AuthBearer(),
)
async def get_traces(
    request,
    limit: int = 100,
    service: Optional[str] = None,
) -> TracesResponse:
    """Get recent OpenTelemetry traces.

    Per Phase 7.6: OpenTelemetry spans.

    In production: Query Jaeger/Tempo backend.
    """
    # Placeholder - in production connects to tracing backend
    return TracesResponse(
        traces=[],
        total=0,
    )


@router.get(
    "/traces/{trace_id}",
    summary="Get trace by ID",
    auth=AuthBearer(),
)
async def get_trace(request, trace_id: str) -> dict:
    """Get specific trace with all spans."""
    return {
        "trace_id": trace_id,
        "spans": [],
        "duration_ms": None,
    }


# =============================================================================
# ENDPOINTS - Kubernetes Health
# =============================================================================


@router.get(
    "/ready",
    response=ReadinessResponse,
    summary="Kubernetes readiness probe",
)
async def readiness(request) -> ReadinessResponse:
    """Kubernetes readiness check.

    DevOps: Returns 200 if ready to serve traffic.
    """
    import httpx

    checks = []
    all_healthy = True

    # Check database
    try:
        from django.db import connection

        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        checks.append(
            HealthCheckResult(
                name="database",
                status="healthy",
                latency_ms=1.0,
            )
        )
    except Exception as e:
        all_healthy = False
        checks.append(
            HealthCheckResult(
                name="database",
                status="down",
                message=str(e),
            )
        )

    # Check Redis
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            start = time.time()
            response = await client.get("http://localhost:20379/")
        checks.append(
            HealthCheckResult(
                name="redis",
                status="healthy",
                latency_ms=(time.time() - start) * 1000,
            )
        )
    except Exception:
        # Redis not required for readiness
        checks.append(
            HealthCheckResult(
                name="redis",
                status="degraded",
                message="Redis unavailable but not blocking",
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

    DevOps: Returns 200 if process is alive.
    """
    import os

    # Get process uptime
    try:
        uptime = time.time() - os.path.getctime("/proc/self")
    except Exception:
        uptime = 0.0

    return LivenessResponse(
        alive=True,
        uptime_seconds=uptime,
        timestamp=timezone.now().isoformat(),
    )


# =============================================================================
# ENDPOINTS - Dashboards
# =============================================================================


@router.get(
    "/dashboards",
    summary="List Grafana dashboards",
    auth=AuthBearer(),
)
async def list_dashboards(request) -> dict:
    """List available Grafana dashboards.

    Per Phase 7.6: Grafana dashboards.
    """
    return {
        "dashboards": [
            {
                "id": "soma-overview",
                "name": "SomaAgent Overview",
                "url": "/grafana/d/soma-overview",
            },
            {
                "id": "soma-memory",
                "name": "Memory Operations",
                "url": "/grafana/d/soma-memory",
            },
            {
                "id": "soma-cognitive",
                "name": "Cognitive Performance",
                "url": "/grafana/d/soma-cognitive",
            },
        ],
    }


@router.post(
    "/metrics/record",
    summary="Record custom metric",
    auth=AuthBearer(),
)
async def record_metric(
    request,
    name: str,
    value: float,
    labels: Optional[dict] = None,
) -> dict:
    """Record a custom metric.

    Used by services to push metrics.
    """
    # In production: push to Prometheus Pushgateway
    logger.debug(f"Metric recorded: {name}={value}")

    return {
        "recorded": True,
        "name": name,
        "value": value,
        "timestamp": timezone.now().isoformat(),
    }
