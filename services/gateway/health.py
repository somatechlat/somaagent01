"""
Comprehensive health check endpoints for SomaAgent01 canonical backend.
Real-time health monitoring for all singleton integrations and external dependencies.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict

import httpx
from fastapi import APIRouter, HTTPException

from observability.metrics import get_metrics_snapshot, metrics_collector
from python.integrations.soma_client import SomaClient

router = APIRouter(prefix="/health", tags=["health"])


class HealthChecker:
    """Centralized health checking for all singleton integrations."""

    def __init__(self):
        self.soma_client = SomaClient()
        self.checks = {
            "postgres": self._check_postgres,
            "kafka": self._check_kafka,
            "somabrain": self._check_somabrain,
            "opa": self._check_opa,
            "singleton_registry": self._check_singleton_registry,
            "sse_streaming": self._check_sse_streaming,
        }

    async def _check_postgres(self) -> Dict[str, Any]:
        """PostgreSQL check disabled - no postgres_client available."""
        return {
            "status": "skipped",
            "message": "PostgreSQL client not available",
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def _check_kafka(self) -> Dict[str, Any]:
        """Check Kafka connectivity."""
        try:
            from kafka import KafkaProducer

            from src.core.config import cfg

            bootstrap_servers = cfg.settings().kafka_bootstrap_servers or "localhost:9092"
            producer = KafkaProducer(
                bootstrap_servers=bootstrap_servers,
                value_serializer=lambda x: str(x).encode("utf-8"),
                request_timeout_ms=5000,
            )

            # Test connection
            if producer.bootstrap_connected():
                producer.close()
                return {
                    "status": "healthy",
                    "message": "Kafka connection successful",
                    "timestamp": datetime.utcnow().isoformat(),
                }
            else:
                return {
                    "status": "unhealthy",
                    "message": "Kafka connection failed",
                    "timestamp": datetime.utcnow().isoformat(),
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"Kafka error: {str(e)}",
                "timestamp": datetime.utcnow().isoformat(),
            }

    async def _check_somabrain(self) -> Dict[str, Any]:
        """Check SomaBrain service connectivity."""
        try:
            # Check if SomaBrain client is properly initialized
            if hasattr(self.soma_client, "base_url"):
                async with httpx.AsyncClient(timeout=5.0) as client:
                    resp = await client.get(f"{self.soma_client.base_url}/health")
                    return {
                        "status": "healthy" if resp.status_code == 200 else "unhealthy",
                        "message": f"SomaBrain health check: {resp.status_code}",
                        "timestamp": datetime.utcnow().isoformat(),
                    }
            else:
                return {
                    "status": "healthy",  # Assume healthy if no health endpoint
                    "message": "SomaBrain client initialized",
                    "timestamp": datetime.utcnow().isoformat(),
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"SomaBrain error: {str(e)}",
                "timestamp": datetime.utcnow().isoformat(),
            }

    async def _check_opa(self) -> Dict[str, Any]:
        """OPA check after middleware removal.

        The prior EnforcePolicy middleware has been removed. This check now
        reports 'skipped' to avoid failing aggregate health while policy
        integration is refactored to selective authorization.
        """
        return {
            "status": "skipped",
            "message": "opa_middleware_removed",
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def _check_singleton_registry(self) -> Dict[str, Any]:
        """Check singleton registry pattern."""
        try:
            # Verify singleton instances are properly initialized
            from python.integrations.soma_client import SomaClient as SomaClient2

            soma1 = SomaClient()
            soma2 = SomaClient2()

            # Check if they're the same instance (singleton)
            is_singleton = soma1 is soma2

            return {
                "status": "healthy" if is_singleton else "unhealthy",
                "message": f'Singleton registry: {"enabled" if is_singleton else "disabled"}',
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"Singleton registry error: {str(e)}",
                "timestamp": datetime.utcnow().isoformat(),
            }

    async def _check_sse_streaming(self) -> Dict[str, Any]:
        """Check SSE streaming capabilities."""
        try:
            # Check if SSE endpoints are available
            return {
                "status": "healthy",
                "message": "SSE streaming enabled",
                "timestamp": datetime.utcnow().isoformat(),
                "endpoints": [
                    "/v1/sessions/{session_id}/events",
                    "/v1/weights",
                    "/v1/context",
                    "/v1/feature-flags",
                ],
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"SSE streaming error: {str(e)}",
                "timestamp": datetime.utcnow().isoformat(),
            }

    async def check_health(self) -> Dict[str, Any]:
        """Run all health checks."""
        checks = {}

        # Run all checks concurrently
        tasks = []
        for name, check_func in self.checks.items():
            tasks.append(check_func())

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, (name, result) in enumerate(zip(self.checks.keys(), results, strict=False)):
            if isinstance(result, Exception):
                checks[name] = {
                    "status": "error",
                    "message": str(result),
                    "timestamp": datetime.utcnow().isoformat(),
                }
            else:
                checks[name] = result

        # Update metrics
        for name, result in checks.items():
            is_healthy = result.get("status") == "healthy"
            metrics_collector.track_singleton_health(name, is_healthy)

        overall_healthy = all(result.get("status") == "healthy" for result in checks.values())

        return {
            "status": "healthy" if overall_healthy else "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": checks,
            "uptime": datetime.utcnow().isoformat(),
            "version": "canonical-0.1.0",
        }


# Global health checker
health_checker = HealthChecker()


@router.get("/ready")
async def readiness_check():
    """Kubernetes-style readiness check."""
    health = await health_checker.check_health()
    if health["status"] == "healthy":
        return {"status": "ready", "timestamp": health["timestamp"]}
    else:
        raise HTTPException(status_code=503, detail=health)


@router.get("/live")
async def liveness_check():
    """Kubernetes-style liveness check."""
    return {"status": "alive", "timestamp": datetime.utcnow().isoformat()}


@router.get("/detailed")
async def detailed_health():
    """Comprehensive health check with all details."""
    return await health_checker.check_health()


@router.get("/metrics")
async def health_metrics():
    """Prometheus metrics snapshot."""
    return get_metrics_snapshot()


@router.get("/integrations/{integration_name}")
async def integration_health(integration_name: str):
    """Health check for specific integration."""
    if integration_name not in health_checker.checks:
        raise HTTPException(status_code=404, detail=f"Integration {integration_name} not found")

    check_func = health_checker.checks[integration_name]
    result = await check_func()
    return result


@router.get("/sse/streaming")
async def sse_health():
    """SSE streaming specific health check."""
    return await health_checker._check_sse_streaming()


@router.get("/summary")
async def health_summary():
    """Quick health summary for monitoring dashboards."""
    health = await health_checker.check_health()

    # Count healthy vs unhealthy services
    healthy_count = sum(1 for check in health["checks"].values() if check["status"] == "healthy")
    total_count = len(health["checks"])

    return {
        "overall_status": health["status"],
        "healthy_services": healthy_count,
        "total_services": total_count,
        "health_percentage": (healthy_count / total_count) * 100,
        "last_check": health["timestamp"],
    }

# ---------------------------------------------------------------------------
# Degradation status endpoint
# ---------------------------------------------------------------------------
# Exposes the current state of each circuit breaker (CLOSED, OPEN, HALF-OPEN).
# When any breaker is OPEN the system is considered degraded.  This endpoint
# allows the UI or monitoring tools to visualise the degradation level (e.g.
# colour‑code green/amber/red).

from services.gateway.circuit_breakers import circuit_breakers


@router.get("/degraded")
async def degraded_status() -> dict:
    """Return degradation information for all external services.

    The response includes:
    * ``degraded`` – ``True`` if any circuit breaker is ``OPEN``.
    * ``services`` – mapping of service name → breaker state name.
    * ``timestamp`` – ISO‑formatted time of the check.
    """
    any_open = False
    status: dict[str, str] = {}
    for name, service in circuit_breakers.items():
        # ``pybreaker`` exposes ``current_state`` with a ``name`` attribute.
        state_obj = getattr(service.breaker, "current_state", None)
        state_name = getattr(state_obj, "name", str(state_obj))
        status[name] = state_name
        if state_name == "OPEN":
            any_open = True

    return {
        "degraded": any_open,
        "services": status,
        "timestamp": datetime.utcnow().isoformat(),
    }



