"""Real Infrastructure Health Checker.


Per

10-Persona Implementation:
- PhD Developer: Async health checks with proper error handling
- DevOps: Real infrastructure verification
- Performance Engineer: Latency measurement
- Security Auditor: Connection timeout limits
- QA Engineer: Comprehensive status reporting
"""

from __future__ import annotations

import asyncio
import logging
import time

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
        latency_ms: float = None,
        details: dict = None,
        error: str = None,
    ):
        """Initialize the instance."""

        self.name = name
        self.status = status  # healthy, degraded, down
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


class InfrastructureHealthChecker:
    """Real infrastructure health checker.

    Connects to actual services and verifies they are operational.
    No mocks, no fake data -
    """

    def __init__(self):
        """Initialize the instance."""

        self.check_timeout = 5.0  # seconds

    async def check_all(self) -> dict:
        """Check all infrastructure services."""
        start_time = time.time()

        # Run all checks concurrently - INCLUDING Kafka and Flink
        checks = await asyncio.gather(
            self.check_postgresql(),
            self.check_redis(),
            self.check_kafka(),
            self.check_flink(),
            self.check_temporal(),
            self.check_qdrant(),
            self.check_keycloak(),
            self.check_lago(),
            self.check_somabrain(),
            self.check_whisper(),
            self.check_kokoro(),
            return_exceptions=True,
        )

        # Process results
        results = []
        all_healthy = True
        critical_down = False

        for check in checks:
            if isinstance(check, Exception):
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
                elif check.status == "degraded":
                    all_healthy = False

        # Overall status
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

    async def check_postgresql(self) -> HealthCheckResult:
        """Check PostgreSQL database connectivity."""
        from asgiref.sync import sync_to_async

        start = time.time()
        try:
            # Use sync_to_async wrapper for Django ORM in async context
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
            logger.error(f"PostgreSQL health check failed: {e}")
            return HealthCheckResult(
                name="postgresql",
                status="down",
                latency_ms=(time.time() - start) * 1000,
                error=str(e),
            )

    async def check_redis(self) -> HealthCheckResult:
        """Check Redis connectivity."""
        start = time.time()
        try:
            import redis.asyncio as redis

            redis_url = getattr(settings, "REDIS_URL", "redis://localhost:6379")
            client = redis.from_url(redis_url, socket_timeout=self.check_timeout)

            # Ping Redis
            await client.ping()

            # Get info
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
            logger.warning(f"Redis health check failed: {e}")
            return HealthCheckResult(
                name="redis",
                status="degraded",
                latency_ms=(time.time() - start) * 1000,
                error=str(e),
            )

    async def check_kafka(self) -> HealthCheckResult:
        """Check Kafka connectivity using existing KafkaEventBus adapter.

        DevOps: Uses production KafkaEventBus.healthcheck() method.
        """
        start = time.time()
        try:
            from services.common.event_bus import KafkaEventBus, KafkaSettings

            bootstrap_servers = getattr(settings, "KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
            settings = KafkaSettings(bootstrap_servers=bootstrap_servers)
            bus = KafkaEventBus(settings)

            # Use the existing healthcheck method from KafkaEventBus
            await bus.healthcheck()
            await bus.close()

            latency = (time.time() - start) * 1000

            return HealthCheckResult(
                name="kafka",
                status="healthy",
                latency_ms=latency,
                details={
                    "bootstrap_servers": bootstrap_servers,
                },
            )
        except ImportError as e:
            return HealthCheckResult(
                name="kafka",
                status="degraded",
                error=f"Kafka module not available: {e}",
            )
        except Exception as e:
            logger.warning(f"Kafka health check failed: {e}")
            return HealthCheckResult(
                name="kafka",
                status="degraded",
                latency_ms=(time.time() - start) * 1000,
                error=str(e),
            )

    async def check_flink(self) -> HealthCheckResult:
        """Check Flink cluster via REST API.

        DevOps: Queries Flink JobManager REST endpoint.
        Performance Engineer: Monitors streaming job status.
        """
        start = time.time()
        try:
            import httpx

            flink_rest_url = getattr(settings, "FLINK_REST_URL", "http://localhost:8081")
            url = f"{flink_rest_url}/overview"

            async with httpx.AsyncClient(timeout=self.check_timeout) as client:
                response = await client.get(url)

            latency = (time.time() - start) * 1000

            if response.status_code == 200:
                data = response.json() if response.text else {}
                return HealthCheckResult(
                    name="flink",
                    status="healthy",
                    latency_ms=latency,
                    details={
                        "flink_version": data.get("flink-version", "unknown"),
                        "jobs_running": data.get("jobs-running", 0),
                        "jobs_finished": data.get("jobs-finished", 0),
                        "taskmanagers": data.get("taskmanagers", 0),
                        "slots_total": data.get("slots-total", 0),
                        "slots_available": data.get("slots-available", 0),
                    },
                )
            else:
                return HealthCheckResult(
                    name="flink",
                    status="degraded",
                    latency_ms=latency,
                    error=f"HTTP {response.status_code}",
                )
        except Exception as e:
            logger.warning(f"Flink health check failed: {e}")
            return HealthCheckResult(
                name="flink",
                status="degraded",
                latency_ms=(time.time() - start) * 1000,
                error=str(e),
            )

    async def check_temporal(self) -> HealthCheckResult:
        """Check Temporal server connectivity."""
        start = time.time()
        try:
            import httpx

            temporal_host = getattr(settings, "TEMPORAL_HOST", "localhost:7233")
            # Temporal health check endpoint
            url = f"http://{temporal_host}/health"

            async with httpx.AsyncClient(timeout=self.check_timeout) as client:
                response = await client.get(url)

            latency = (time.time() - start) * 1000

            if response.status_code == 200:
                return HealthCheckResult(
                    name="temporal",
                    status="healthy",
                    latency_ms=latency,
                    details={"host": temporal_host},
                )
            else:
                return HealthCheckResult(
                    name="temporal",
                    status="degraded",
                    latency_ms=latency,
                    error=f"HTTP {response.status_code}",
                )
        except Exception as e:
            logger.warning(f"Temporal health check failed: {e}")
            return HealthCheckResult(
                name="temporal",
                status="degraded",
                latency_ms=(time.time() - start) * 1000,
                error=str(e),
            )

    async def check_qdrant(self) -> HealthCheckResult:
        """Check Qdrant vector database connectivity."""
        start = time.time()
        try:
            import httpx

            qdrant_host = getattr(settings, "QDRANT_HOST", "localhost:6333")
            url = f"http://{qdrant_host}/health"

            async with httpx.AsyncClient(timeout=self.check_timeout) as client:
                response = await client.get(url)

            latency = (time.time() - start) * 1000

            if response.status_code == 200:
                data = response.json() if response.text else {}
                return HealthCheckResult(
                    name="qdrant",
                    status="healthy",
                    latency_ms=latency,
                    details={
                        "host": qdrant_host,
                        "version": data.get("version", "unknown"),
                    },
                )
            else:
                return HealthCheckResult(
                    name="qdrant",
                    status="degraded",
                    latency_ms=latency,
                    error=f"HTTP {response.status_code}",
                )
        except Exception as e:
            logger.warning(f"Qdrant health check failed: {e}")
            return HealthCheckResult(
                name="qdrant",
                status="degraded",
                latency_ms=(time.time() - start) * 1000,
                error=str(e),
            )

    async def check_keycloak(self) -> HealthCheckResult:
        """Check Keycloak authentication server."""
        start = time.time()
        try:
            import httpx

            keycloak_url = getattr(settings, "KEYCLOAK_URL", "http://localhost:8080")
            url = f"{keycloak_url}/health/ready"

            async with httpx.AsyncClient(timeout=self.check_timeout) as client:
                response = await client.get(url)

            latency = (time.time() - start) * 1000

            if response.status_code == 200:
                return HealthCheckResult(
                    name="keycloak",
                    status="healthy",
                    latency_ms=latency,
                    details={"url": keycloak_url},
                )
            else:
                return HealthCheckResult(
                    name="keycloak",
                    status="degraded",
                    latency_ms=latency,
                    error=f"HTTP {response.status_code}",
                )
        except Exception as e:
            logger.warning(f"Keycloak health check failed: {e}")
            return HealthCheckResult(
                name="keycloak",
                status="degraded",
                latency_ms=(time.time() - start) * 1000,
                error=str(e),
            )

    async def check_lago(self) -> HealthCheckResult:
        """Check Lago billing server."""
        start = time.time()
        try:
            import httpx

            lago_url = getattr(settings, "LAGO_API_URL", "http://localhost:63690/api/v1")
            url = f"{lago_url}/health"

            async with httpx.AsyncClient(timeout=self.check_timeout) as client:
                response = await client.get(url)

            latency = (time.time() - start) * 1000

            if response.status_code == 200:
                return HealthCheckResult(
                    name="lago",
                    status="healthy",
                    latency_ms=latency,
                    details={"url": lago_url},
                )
            else:
                return HealthCheckResult(
                    name="lago",
                    status="degraded",
                    latency_ms=latency,
                    error=f"HTTP {response.status_code}",
                )
        except Exception as e:
            logger.warning(f"Lago health check failed: {e}")
            return HealthCheckResult(
                name="lago",
                status="degraded",
                latency_ms=(time.time() - start) * 1000,
                error=str(e),
            )

    async def check_somabrain(self) -> HealthCheckResult:
        """Check SomaBrain memory service."""
        start = time.time()
        try:
            import httpx

            somabrain_url = getattr(settings, "SOMABRAIN_URL", "http://localhost:9696")
            url = f"{somabrain_url}/health"

            async with httpx.AsyncClient(timeout=self.check_timeout) as client:
                response = await client.get(url)

            latency = (time.time() - start) * 1000

            if response.status_code == 200:
                data = response.json() if response.text else {}
                return HealthCheckResult(
                    name="somabrain",
                    status="healthy",
                    latency_ms=latency,
                    details={
                        "url": somabrain_url,
                        "status": data.get("status", "unknown"),
                    },
                )
            else:
                return HealthCheckResult(
                    name="somabrain",
                    status="degraded",
                    latency_ms=latency,
                    error=f"HTTP {response.status_code}",
                )
        except Exception as e:
            logger.warning(f"SomaBrain health check failed: {e}")
            return HealthCheckResult(
                name="somabrain",
                status="degraded",
                latency_ms=(time.time() - start) * 1000,
                error=str(e),
            )

    async def check_whisper(self) -> HealthCheckResult:
        """Check Whisper STT service."""
        start = time.time()
        try:
            import httpx

            whisper_url = getattr(settings, "WHISPER_URL", "http://localhost:9100")
            url = f"{whisper_url}/health"

            async with httpx.AsyncClient(timeout=self.check_timeout) as client:
                response = await client.get(url)

            latency = (time.time() - start) * 1000

            if response.status_code == 200:
                return HealthCheckResult(
                    name="whisper",
                    status="healthy",
                    latency_ms=latency,
                )
            else:
                return HealthCheckResult(
                    name="whisper",
                    status="degraded",
                    latency_ms=latency,
                    error=f"HTTP {response.status_code}",
                )
        except Exception as e:
            # Voice services are optional
            return HealthCheckResult(
                name="whisper",
                status="degraded",
                latency_ms=(time.time() - start) * 1000,
                error=str(e),
            )

    async def check_kokoro(self) -> HealthCheckResult:
        """Check Kokoro TTS service."""
        start = time.time()
        try:
            import httpx

            kokoro_url = getattr(settings, "KOKORO_URL", "http://localhost:9200")
            url = f"{kokoro_url}/health"

            async with httpx.AsyncClient(timeout=self.check_timeout) as client:
                response = await client.get(url)

            latency = (time.time() - start) * 1000

            if response.status_code == 200:
                return HealthCheckResult(
                    name="kokoro",
                    status="healthy",
                    latency_ms=latency,
                )
            else:
                return HealthCheckResult(
                    name="kokoro",
                    status="degraded",
                    latency_ms=latency,
                    error=f"HTTP {response.status_code}",
                )
        except Exception as e:
            # Voice services are optional
            return HealthCheckResult(
                name="kokoro",
                status="degraded",
                latency_ms=(time.time() - start) * 1000,
                error=str(e),
            )


# Singleton instance
health_checker = InfrastructureHealthChecker()
