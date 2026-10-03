"""Infrastructure health checks.

One inventory, and it is not this file. What this deployment runs is declared
in ``config.settings_registry`` as ``service_health_endpoints`` per mode
(VIBE Rule 100). This module probes that map and nothing else.

The previous version of this file checked ten services by name and resolved
each one's URL with ``getattr(settings, "X", "http://localhost:PORT")`` — a
silent default on every line. Concretely, that meant:

* ``REDIS_URL`` is not a Django setting in this project (the value lives at
  ``SA01_REDIS_URL`` and in the registry), so the Redis check raised
  "REDIS_URL is required" on every call. Permanently broken.
* ``SOMABRAIN_URL`` *is* a setting, but it has no default and is ``None``
  unless the environment sets it — so ``getattr(..., "http://localhost:9696")``
  returned ``None`` (the attribute exists) and the check probed ``"None/health"``.
* Flink, Qdrant, Whisper and Kokoro are not containers in any compose file
  under ``infra/``, so those checks always fell through to probing localhost
  and always reported "degraded" — a fabricated signal that made the dashboard
  look monitored.

VIBE Rule 91, Zero-Fallback: a missing configuration value fails the call. It
does not silently become localhost. A service the map does not name is not
deployed here, and the result says exactly that.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Dict

from django.conf import settings
from django.db import connection
from django.utils import timezone

logger = logging.getLogger(__name__)


class HealthCheckResult:
    """Result of a health check."""

    def __init__(
        self,
        name: str,
        status: str,
        latency_ms: float | None = None,
        details: dict | None = None,
        error: str | None = None,
    ):
        """Initialize the instance."""

        self.name = name
        # healthy | degraded | down | not_deployed
        self.status = status
        self.latency_ms = latency_ms
        self.details = details or {}
        self.error = error

    def to_dict(self) -> dict:
        """Execute to dict."""

        return {
            "name": self.name,
            "status": self.status,
            "latency_ms": self.latency_ms,
            "details": self.details,
            "error": self.error if self.status != "healthy" else None,
        }


def _registry():
    """The declared topology for this deployment (Rule 100).

    Returns ``config.settings_registry.BaseSettings``.

    Raised, not defaulted: if the registry cannot load, the health check is
    not the place to paper over it.
    """
    from config.settings_registry import get_settings

    return get_settings()


def _http_endpoints() -> Dict[str, str]:
    """Declared HTTP health endpoints, name -> full probe URL."""
    cfg = _registry()
    endpoints = getattr(cfg, "service_health_endpoints", None)
    if not isinstance(endpoints, dict):
        raise RuntimeError(
            "VIBE Rule 91 VIOLATION: service_health_endpoints is missing from "
            "the settings registry. A health check must not invent an inventory."
        )
    return {str(k): str(v) for k, v in endpoints.items() if v}


class InfrastructureHealthChecker:
    """Probes the declared deployment inventory. No mocks, no fake data."""

    def __init__(self):
        """Initialize the instance."""

        self.check_timeout = 5.0  # seconds

    # ------------------------------------------------------------------
    # Connection-based checks — topology comes from the registry.
    # ------------------------------------------------------------------

    async def check_postgresql(self) -> HealthCheckResult:
        """Check PostgreSQL database connectivity."""
        from asgiref.sync import sync_to_async

        start = time.time()
        try:
            @sync_to_async
            def _check_db():
                """Execute check db."""

                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    cursor.fetchone()
                with connection.cursor() as cursor:
                    cursor.execute("SELECT version()")
                    return cursor.fetchone()[0]

            version = await _check_db()
            latency = (time.time() - start) * 1000

            return HealthCheckResult(
                name="postgresql",
                status="healthy",
                latency_ms=latency,
                details={
                    "version": version.split(",")[0] if version else "unknown",
                    "database": settings.DATABASES["default"]["NAME"],
                },
            )
        except Exception as e:
            logger.error("PostgreSQL health check failed: %s", e)
            return HealthCheckResult(
                name="postgresql",
                status="down",
                latency_ms=(time.time() - start) * 1000,
                error=str(e),
            )

    async def check_redis(self) -> HealthCheckResult:
        """Check Redis connectivity against the registry's redis topology.

        The URL is built from ``redis_host`` / ``redis_port`` / ``redis_db``,
        which is where that topology actually lives. The previous
        ``getattr(settings, "REDIS_URL", None)`` named an attribute this
        project does not define, so this check failed on every call.
        """
        start = time.time()
        try:
            import redis.asyncio as redis

            cfg = _registry()
            redis_url = cfg.redis_url
            client = redis.from_url(redis_url, socket_timeout=self.check_timeout)

            await client.ping()
            info = await client.info("server")
            await client.aclose()

            latency = (time.time() - start) * 1000

            return HealthCheckResult(
                name="redis",
                status="healthy",
                latency_ms=latency,
                details={
                    "version": info.get("redis_version", "unknown"),
                    "mode": info.get("redis_mode", "standalone"),
                },
            )
        except ImportError:
            return HealthCheckResult(
                name="redis",
                status="degraded",
                error="redis package not installed",
            )
        except Exception as e:
            logger.warning("Redis health check failed: %s", e)
            return HealthCheckResult(
                name="redis",
                status="degraded",
                latency_ms=(time.time() - start) * 1000,
                error=str(e),
            )

    async def check_kafka(self) -> HealthCheckResult:
        """Check Kafka connectivity.

        An empty ``kafka_bootstrap_servers`` is a real topology state — this
        deployment runs no broker (Standalone is declared that way). It is not
        a reason to guess ``localhost:9092``.
        """
        start = time.time()
        try:
            from services.common.event_bus import KafkaEventBus, KafkaSettings

            cfg = _registry()
            bootstrap_servers = (cfg.kafka_bootstrap_servers or "").strip()
            if not bootstrap_servers:
                return HealthCheckResult(
                    name="kafka",
                    status="not_deployed",
                    error="kafka_bootstrap_servers is empty in this deployment's topology",
                )

            kafka_settings = KafkaSettings(bootstrap_servers=bootstrap_servers)
            bus = KafkaEventBus(kafka_settings)

            await bus.healthcheck()
            await bus.close()

            latency = (time.time() - start) * 1000

            return HealthCheckResult(
                name="kafka",
                status="healthy",
                latency_ms=latency,
                details={"bootstrap_servers": bootstrap_servers},
            )
        except ImportError as e:
            return HealthCheckResult(
                name="kafka",
                status="degraded",
                error=f"Kafka module not available: {e}",
            )
        except Exception as e:
            logger.warning("Kafka health check failed: %s", e)
            return HealthCheckResult(
                name="kafka",
                status="degraded",
                latency_ms=(time.time() - start) * 1000,
                error=str(e),
            )

    # ------------------------------------------------------------------
    # HTTP-probed checks — one generic prober, driven by the registry.
    # ------------------------------------------------------------------

    async def _check_http(self, name: str) -> HealthCheckResult:
        """Probe one declared HTTP endpoint.

        An undeclared name is reported as ``not_deployed`` and never probed.
        There is no fallback URL anywhere in this method — that is the point.
        """
        start = time.time()
        endpoints = _http_endpoints()
        url = endpoints.get(name)
        if not url:
            return HealthCheckResult(
                name=name,
                status="not_deployed",
                error=(
                    f"'{name}' is not in service_health_endpoints for this "
                    f"deployment. Declared: {sorted(endpoints)}"
                ),
            )

        try:
            import httpx

            async with httpx.AsyncClient(timeout=self.check_timeout) as client:
                response = await client.get(url)

            latency = (time.time() - start) * 1000

            if response.status_code == 200:
                return HealthCheckResult(
                    name=name,
                    status="healthy",
                    latency_ms=latency,
                    details={"url": url},
                )
            return HealthCheckResult(
                name=name,
                status="degraded",
                latency_ms=latency,
                details={"url": url},
                error=f"HTTP {response.status_code}",
            )
        except Exception as e:
            logger.warning("Health check failed for %s: %s", name, e)
            return HealthCheckResult(
                name=name,
                status="degraded",
                latency_ms=(time.time() - start) * 1000,
                details={"url": url},
                error=str(e),
            )

    def __getattr__(self, item: str):
        """Expose ``check_<name>`` for every declared HTTP service.

        ``admin.observability.api`` dispatches on the service name
        dynamically, so the method has to exist. Undeclared names still get a
        method — one that answers "not deployed" rather than inventing a probe.
        """
        if not item.startswith("check_"):
            raise AttributeError(item)
        name = item[len("check_") :]

        async def _bound() -> HealthCheckResult:
            if name == "postgresql":
                return await self.check_postgresql()
            if name == "redis":
                return await self.check_redis()
            if name == "kafka":
                return await self.check_kafka()
            return await self._check_http(name)

        _bound.__name__ = item
        return _bound

    # ------------------------------------------------------------------
    # Inventory
    # ------------------------------------------------------------------

    async def check_all(self) -> dict:
        """Check the connection-based services and every declared HTTP endpoint."""
        start_time = time.time()

        declared = sorted(_http_endpoints())
        checks = await asyncio.gather(
            self.check_postgresql(),
            self.check_redis(),
            self.check_kafka(),
            *(self._check_http(name) for name in declared),
            return_exceptions=True,
        )

        results = []
        all_healthy = True
        critical_down = False

        for check in checks:
            if isinstance(check, BaseException):
                results.append(
                    HealthCheckResult(
                        name="unknown",
                        status="down",
                        error=str(check),
                    )
                )
                critical_down = True
            else:
                results.append(check)
                if check.status == "down":
                    critical_down = True
                    all_healthy = False
                elif check.status in ("degraded", "not_deployed"):
                    all_healthy = False

        if critical_down:
            overall_status = "degraded"
        elif all_healthy:
            overall_status = "healthy"
        else:
            overall_status = "degraded"

        return {
            "overall_status": overall_status,
            "timestamp": timezone.now().isoformat(),
            "duration_ms": (time.time() - start_time) * 1000,
            "services": [r.to_dict() for r in results if isinstance(r, HealthCheckResult)],
        }


# Singleton instance
health_checker = InfrastructureHealthChecker()
