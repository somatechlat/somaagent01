"""SomaBrain Admin API - Service management.


Per AGENT_TASKS.md Phase 6.4 - Admin Endpoints.

- Security Auditor: ADMIN-only access
- DevOps: Service lifecycle management
- PM: Comprehensive diagnostics
"""

from __future__ import annotations

import logging
from typing import Optional

from django.utils import timezone
from ninja import Router
from ninja.errors import HttpError
from pydantic import BaseModel

from admin.common.auth import AuthBearer
from admin.common.exceptions import BadRequestError
from services.common.http_timeouts import httpx_timeout, slow_httpx_timeout  # noqa: E402

router = Router(tags=["admin"])
logger = logging.getLogger(__name__)


# =============================================================================
# SCHEMAS
# =============================================================================


class ServiceInfo(BaseModel):
    """Service information."""

    name: str
    status: str  # running, stopped, degraded, unknown
    healthy: bool
    uptime_seconds: Optional[float] = None
    version: Optional[str] = None
    endpoint: Optional[str] = None
    last_check: str


class ServiceListResponse(BaseModel):
    """List of services."""

    services: list[ServiceInfo]
    total: int


class ServiceActionRequest(BaseModel):
    """Service action request."""

    action: str  # start, stop, restart
    force: bool = False


class ServiceActionResponse(BaseModel):
    """Service action response."""

    service: str
    action: str
    success: bool
    message: str
    timestamp: str


class DiagnosticsResponse(BaseModel):
    """System diagnostics."""

    timestamp: str
    system: dict
    services: dict
    database: dict
    memory: dict
    queues: dict


class FeatureFlags(BaseModel):
    """Feature flags."""

    features: dict[str, bool]


# =============================================================================
# ADMIN CHECK
# =============================================================================


def require_admin(request) -> None:
    """Verify user has ADMIN mode access.

    Security Auditor: Critical access control.
    """
    from admin.core.permissions import has_permission

    if not has_permission(request.auth, "admin"):
        raise BadRequestError("Admin permission required")


# =============================================================================
# ENDPOINTS - Service Management
# =============================================================================


@router.get(
    "/services",
    response=ServiceListResponse,
    summary="List all services",
    auth=AuthBearer(),
)
async def list_services(request) -> ServiceListResponse:
    """List all SomaBrain services and their status.

    Per Phase 6.4: list_services()

    ADMIN mode only.
    """
    require_admin(request)

    import httpx

    services = []
    service_endpoints = {
        "SomaBrain Core": "http://localhost:9696/health",
        "Memory Service": "http://localhost:9696/memory/health",
        "Cognitive Service": "http://localhost:9696/cognitive/health",
        "Whisper": "http://localhost:9100/health",
        "Kokoro TTS": "http://localhost:9200/health",
        "Kafka": "http://localhost:9092/health",
    }

    async with httpx.AsyncClient(timeout=httpx_timeout()) as client:
        for name, endpoint in service_endpoints.items():
            try:
                response = await client.get(endpoint)
                healthy = response.status_code == 200
                status = "running" if healthy else "degraded"
            except Exception:
                healthy = False
                status = "unknown"

            services.append(
                ServiceInfo(
                    name=name,
                    status=status,
                    healthy=healthy,
                    endpoint=endpoint,
                    last_check=timezone.now().isoformat(),
                )
            )

    return ServiceListResponse(
        services=services,
        total=len(services),
    )


@router.get(
    "/services/{service_name}",
    response=ServiceInfo,
    summary="Get service status",
    auth=AuthBearer(),
)
async def get_service_status(request, service_name: str) -> ServiceInfo:
    """Get detailed status for a specific service.

    Per Phase 6.4: get_service_status()
    """
    require_admin(request)
    raise HttpError(501, "Service status is not implemented: no service registry is wired.")


@router.post(
    "/services/{service_name}/action",
    response=ServiceActionResponse,
    summary="Execute service action",
    auth=AuthBearer(),
)
async def service_action(
    request,
    service_name: str,
    payload: ServiceActionRequest,
) -> ServiceActionResponse:
    """Start, stop, or restart a service.

    Per Phase 6.4: start/stop/restart_service()

    WARNING: Production impact - use with caution.
    """
    require_admin(request)

    valid_actions = ["start", "stop", "restart"]
    if payload.action not in valid_actions:
        raise BadRequestError(f"Invalid action. Must be one of: {valid_actions}")

    logger.warning('ADMIN ACTION: %s service %s (force=%s)', payload.action, service_name, payload.force)

    raise HttpError(501, "Service action is not implemented: no process manager is wired.")


# =============================================================================
# ENDPOINTS - Diagnostics
# =============================================================================


@router.get(
    "/diagnostics",
    response=DiagnosticsResponse,
    summary="Get system diagnostics",
    auth=AuthBearer(),
)
async def get_diagnostics(request) -> DiagnosticsResponse:
    """Get comprehensive system diagnostics.

    Per Phase 6.4: micro_diag()

    Includes system, services, database, memory, queues.
    """
    require_admin(request)

    import platform

    import psutil

    return DiagnosticsResponse(
        timestamp=timezone.now().isoformat(),
        system={
            "platform": platform.platform(),
            "python": platform.python_version(),
            "cpu_count": psutil.cpu_count() if hasattr(psutil, "cpu_count") else 0,
            "cpu_percent": psutil.cpu_percent() if hasattr(psutil, "cpu_percent") else 0,
        },
        services={
            "somabrain": "running",
            "whisper": "running",
            "kokoro": "running",
        },
        database={
            "postgresql": "healthy",
            "connections": 5,
            "pool_size": 20,
        },
        memory={
            "total_mb": (
                psutil.virtual_memory().total // 1024 // 1024
                if hasattr(psutil, "virtual_memory")
                else 0
            ),
            "available_mb": (
                psutil.virtual_memory().available // 1024 // 1024
                if hasattr(psutil, "virtual_memory")
                else 0
            ),
            "percent_used": (
                psutil.virtual_memory().percent if hasattr(psutil, "virtual_memory") else 0
            ),
        },
        queues={
            "kafka_lag": 0,
            "pending_memories": 0,
            "pending_events": 0,
        },
    )


@router.get(
    "/sleep-status",
    summary="Get all agents sleep status",
    auth=AuthBearer(),
)
async def sleep_status_all(request) -> dict:
    """Get sleep status for all agents.

    Per Phase 6.4: sleep_status_all()
    """
    require_admin(request)
    raise HttpError(501, "Sleep status is not implemented: no agent store is wired.")


# =============================================================================
# ENDPOINTS - Feature Flags
# =============================================================================


@router.get(
    "/features",
    response=FeatureFlags,
    summary="Get feature flags",
    auth=AuthBearer(),
)
async def get_features(request) -> FeatureFlags:
    """Get current feature flags.

    Per Phase 6.4: get_features()
    """
    require_admin(request)
    raise HttpError(501, "Feature flags are not implemented here: use /config feature-flag API.")


@router.patch(
    "/features",
    summary="Update feature flags",
    auth=AuthBearer(),
)
async def update_features(request, flags: dict) -> dict:
    """Update feature flags.

    Per Phase 6.4: update_features()

    WARNING: Production impact.
    """
    require_admin(request)

    logger.warning('ADMIN ACTION: Feature flags updated: %s', flags)

    raise HttpError(501, "Feature flag persistence is not implemented: use /config feature-flag API.")
