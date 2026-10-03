"""SomaBrain Admin API - host diagnostics and service visibility.

What this module is, and what it deliberately is not:

It is a read-only window onto things that are actually measured — host
resources from ``psutil``, and the live infrastructure probes in
``admin.core.infrastructure.health_checker``. Nothing here asserts a status
it did not observe.

It is not a service lifecycle console. The previous version shipped seven
routes: five of them raised ``HttpError(501)`` forever (per-service status,
start/stop/restart, sleep status, read and write of feature flags), one
returned invented numbers (``{"somabrain": "running"}``, ``connections: 5``,
``kafka_lag: 0``) as if they were diagnostics, and one held a hardcoded
Python dict of ``http://localhost:PORT/health`` URLs as its service
inventory. That dict named Whisper, Kokoro TTS and a "SomaBrain Core"
service; none of them is a container in either compose file under
``infra/``. The routes are gone. A surface that cannot work must not exist,
and a diagnostics response must never contain a constant dressed as a
reading.

There is one infrastructure inventory in this codebase and it is
``InfrastructureHealthChecker``. This module reads it; it does not keep a
second list.
"""

from __future__ import annotations

import logging

from django.utils import timezone
from ninja import Router
from pydantic import BaseModel

from admin.common.auth import AuthBearer
from services.common.authorization import authorize

router = Router(tags=["admin"])
logger = logging.getLogger(__name__)


# =============================================================================
# SCHEMAS — shapes for measured data only.
# =============================================================================


class DiagnosticsResponse(BaseModel):
    """System diagnostics.

    Every field is observed at request time. There are no status literals:
    if a subsystem is not measured here, it is not in the response.
    """

    timestamp: str
    system: dict
    memory: dict
    services: list[dict]


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
    """Host resources and live service probes, measured at request time.

    ``system`` and ``memory`` come from psutil. ``services`` is the result of
    the infrastructure health checks — same probes, same one inventory as
    everything else. Nothing is assumed; a probe that cannot run reports its
    own error rather than a status.
    """
    await authorize(request, action="system:read_metrics", resource="system")

    import platform

    import psutil

    from admin.core.infrastructure import health_checker

    health = await health_checker.check_all()

    return DiagnosticsResponse(
        timestamp=timezone.now().isoformat(),
        system={
            "platform": platform.platform(),
            "python": platform.python_version(),
            "cpu_count": psutil.cpu_count() if hasattr(psutil, "cpu_count") else 0,
            "cpu_percent": psutil.cpu_percent() if hasattr(psutil, "cpu_percent") else 0,
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
        services=list(health.get("services", [])),
    )


@router.get(
    "/services",
    summary="List probed services",
    auth=AuthBearer(),
)
async def list_services(request) -> dict:
    """The infrastructure inventory, as it probes out right now.

    Delegates to ``InfrastructureHealthChecker`` — the one place that knows
    what services exist. The former version of this route kept its own
    hardcoded map of localhost URLs, which is how the stack came to advertise
    services it does not run.
    """
    await authorize(request, action="system:view", resource="system")

    from admin.core.infrastructure import health_checker

    health = await health_checker.check_all()
    return {
        "overall_status": health.get("overall_status"),
        "timestamp": health.get("timestamp"),
        "duration_ms": health.get("duration_ms"),
        "services": health.get("services", []),
        "total": len(health.get("services", [])),
    }
