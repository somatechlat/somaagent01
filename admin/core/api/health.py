"""Full Health Check API Router.

Migrated from: services/gateway/routers/health.py
Pure Django Ninja implementation with async infrastructure checks.


"""

from __future__ import annotations

import logging
from typing import Optional

import httpx
from django.conf import settings
from ninja import Router
from pydantic import BaseModel

router = Router(tags=["health"])
logger = logging.getLogger(__name__)


class ComponentHealth(BaseModel):
    """Individual component health status."""

    status: str  # "ok", "degraded", "down"
    detail: Optional[str] = None


class HealthResponse(BaseModel):
    """Full health check response."""

    status: str  # "ok", "degraded", "down"
    components: dict[str, ComponentHealth]


async def _check_postgres() -> tuple[str, Optional[str]]:
    """Check PostgreSQL connectivity."""
    try:
        from django.db import connection

        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return "ok", None
    except Exception as exc:
        logger.warning("Postgres health check failed", extra={"error": str(exc)})
        return "down", f"{type(exc).__name__}: {exc}"


async def _check_redis() -> tuple[str, Optional[str]]:
    """Check Redis connectivity using Django cache."""
    try:
        from django.core.cache import cache

        # Test cache set/get
        cache.set("health_check", "ok", timeout=5)
        result = cache.get("health_check")
        if result == "ok":
            return "ok", None
        return "degraded", "Cache value mismatch"
    except Exception as exc:
        logger.warning("Redis health check failed", extra={"error": str(exc)})
        return "down", f"{type(exc).__name__}: {exc}"


async def _check_kafka() -> tuple[str, Optional[str]]:
    """Check Kafka connectivity."""
    try:
        from services.common.event_bus import KafkaEventBus, KafkaSettings

        kafka_bus = KafkaEventBus(KafkaSettings.from_env())
        try:
            await kafka_bus.healthcheck()
            return "ok", None
        finally:
            await kafka_bus.close()
    except Exception as exc:
        logger.warning("Kafka health check failed", extra={"error": str(exc)})
        return "down", f"{type(exc).__name__}: {exc}"


async def _check_http_target(name: str, url: Optional[str]) -> tuple[str, Optional[str]]:
    """Check HTTP target health."""
    if not url:
        return "unknown", "URL not configured"
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(url)
        if response.status_code < 500:
            return "ok", None
        return "degraded", f"Status {response.status_code}"
    except Exception as exc:
        return "down", f"{type(exc).__name__}: {exc}"


async def _check_temporal() -> tuple[str, Optional[str]]:
    """Check Temporal connectivity."""
    try:
        from temporalio.api.workflowservice.v1 import GetSystemInfoRequest

        from services.gateway.providers import get_temporal_client

        temporal_client = await get_temporal_client()
        await temporal_client.workflow_service.get_system_info(GetSystemInfoRequest())
        return "ok", None
    except Exception as exc:
        return "down", f"{type(exc).__name__}: {exc}"


@router.get("/health", response=HealthResponse, summary="Full infrastructure health check")
async def health_check() -> dict:
    """
    Comprehensive health check for all infrastructure components.

    Checks: PostgreSQL, Redis, Kafka, SomaBrain, OPA, Temporal, Degradation Monitor.

    Returns:
        HealthResponse with overall status and per-component details.
    """
    from services.common import degradation_monitor

    components: dict[str, dict] = {}
    overall_status = "ok"

    def record_status(name: str, status: str, detail: Optional[str] = None) -> None:
        """Execute record status.

        Args:
            name: The name.
            status: The status.
            detail: The detail.
        """

        nonlocal overall_status
        components[name] = {"status": status}
        if detail:
            components[name]["detail"] = detail
        if status == "down":
            overall_status = "down"
        elif status == "degraded" and overall_status == "ok":
            overall_status = "degraded"

    # Check infrastructure components
    pg_status, pg_detail = await _check_postgres()
    record_status("postgres", pg_status, pg_detail)

    redis_status, redis_detail = await _check_redis()
    record_status("redis", redis_status, redis_detail)

    kafka_status, kafka_detail = await _check_kafka()
    record_status("kafka", kafka_status, kafka_detail)

    # Check external services
    somabrain_status, somabrain_detail = await _check_http_target(
        "somabrain", getattr(settings, "SOMABRAIN_URL", "http://localhost:9696")
    )
    record_status("somabrain", somabrain_status, somabrain_detail)

    opa_status, opa_detail = await _check_http_target(
        "opa", getattr(settings, "OPA_URL", "http://localhost:8181")
    )
    record_status("opa", opa_status, opa_detail)

    temporal_status, temporal_detail = await _check_temporal()
    record_status("temporal", temporal_status, temporal_detail)

    # Degradation monitor
    if degradation_monitor.is_monitoring():
        record_status("degradation_monitor", "ok")

    # Static services (assume running via Docker)
    static_services = [
        "conversation-worker",
        "tool-executor",
        "memory-replicator",
        "fasta2a-gateway",
    ]
    for svc in static_services:
        record_status(svc, "ok")

    return {"status": overall_status, "components": components}


@router.get("/health/quick", summary="Quick liveness check")
async def quick_health() -> dict:
    """
    Quick liveness check - just returns ok if the service is running.
    Use this for Kubernetes liveness probes.
    """
    return {"status": "ok"}


@router.get("/health/ready", summary="Readiness check")
async def readiness_check() -> dict:
    """
    Readiness check - verifies critical dependencies are available.
    Use this for Kubernetes readiness probes.
    """
    try:
        # Just check postgres and redis
        pg_status, _ = await _check_postgres()
        redis_status, _ = await _check_redis()

        if pg_status == "ok" and redis_status == "ok":
            return {"status": "ready", "postgres": "ok", "redis": "ok"}

        return {
            "status": "not_ready",
            "postgres": pg_status,
            "redis": redis_status,
        }
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}
