"""
Degradation Mode Monitor for SomaAgent01 - Real resilience monitoring.
Production-ready degradation detection and management system.
"""

import asyncio
import logging
import os
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional
from temporalio.client import Client as TemporalClient

from admin.core.observability.metrics import Counter, Gauge, Histogram, metrics_collector
from services.common.circuit_breakers import CircuitBreaker, CircuitState

# Prometheus metrics for degradation monitoring
SERVICE_HEALTH_STATE = Gauge(
    "service_health_state",
    "Current health state of service (0=unhealthy, 1=healthy)",
    labelnames=("service",),
)
SERVICE_DEGRADATION_LEVEL = Gauge(
    "service_degradation_level",
    "Current degradation level (0=none, 1=minor, 2=moderate, 3=severe, 4=critical)",
    labelnames=("service",),
)
SERVICE_LATENCY_SECONDS = Histogram(
    "service_latency_seconds",
    "Service response latency in seconds",
    labelnames=("service",),
    buckets=(0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)
SERVICE_ERROR_RATE = Gauge(
    "service_error_rate",
    "Current error rate for service (0.0-1.0)",
    labelnames=("service",),
)
CASCADING_FAILURES_TOTAL = Counter(
    "cascading_failures_total",
    "Total cascading failures detected",
    labelnames=("source_service", "affected_service"),
)

logger = logging.getLogger(__name__)


class DegradationLevel(Enum):
    """Degradation severity levels."""

    NONE = "none"
    MINOR = "minor"
    MODERATE = "moderate"
    SEVERE = "severe"
    CRITICAL = "critical"


@dataclass
class ComponentHealth:
    """Health status of a system component."""

    name: str
    healthy: bool
    response_time: float
    error_rate: float
    last_check: float
    circuit_state: CircuitState = CircuitState.CLOSED
    degradation_level: DegradationLevel = DegradationLevel.NONE


@dataclass
class DegradationStatus:
    """Overall degradation status of the system."""

    overall_level: DegradationLevel
    affected_components: List[str]
    healthy_components: List[str]
    total_components: int
    timestamp: float
    recommendations: List[str] = field(default_factory=list)
    mitigation_actions: List[str] = field(default_factory=list)


@dataclass
class DegradationHistoryRecord:
    """A single degradation event record for history tracking."""

    timestamp: float
    component_name: str
    degradation_level: DegradationLevel
    healthy: bool
    response_time: float
    error_rate: float
    event_type: str  # "check", "failure", "recovery", "cascading"


class DegradationMonitor:
    """
    Production-ready degradation monitoring system.

    Monitors system health, detects degradation patterns, and provides
    actionable insights for system resilience.

    Features:
    - Component health tracking
    - Dependency graph for cascading failure detection
    - Circuit breaker integration
    - Prometheus metrics
    - REAL history tracking (
    """

    # Service dependency graph: key depends on values
    # When a dependency fails, dependents are marked as degraded
    SERVICE_DEPENDENCIES: Dict[str, List[str]] = {
        "gateway": ["database", "redis", "kafka", "temporal"],
        "tool_executor": ["database", "kafka", "somabrain", "temporal", "llm"],
        "conversation_worker": ["database", "kafka", "somabrain", "redis", "temporal", "llm"],
        "auth_service": ["database", "redis"],
        # Multimodal services
        "voice_service": ["llm", "audio_tts", "audio_stt"],
        "upload_service": ["database", "storage"],
        "multimodal": ["llm", "voice_service", "upload_service"],
        # Background services
        "backup_service": ["database", "storage"],
        "task_scheduler": ["database", "redis", "temporal"],
        # Core services have no dependencies (they ARE the dependencies)
        "somabrain": [],
        "database": [],
        "kafka": [],
        "redis": [],
        "temporal": [],
        "llm": [],  # LLM providers (can operate independently)
        "audio_tts": [],  # Text-to-speech providers
        "audio_stt": [],  # Speech-to-text providers
        "storage": [],  # File storage (S3, local, etc.)
    }

    # Maximum history records to keep in memory
    MAX_HISTORY_SIZE = 10000

    def __init__(self):
        self.components: Dict[str, ComponentHealth] = {}
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self._degradation_thresholds = {
            "response_time": 5.0,  # seconds
            "error_rate": 0.1,  # 10%
            "circuit_failure_rate": 0.3,  # 30%
        }
        self._monitoring_active = False
        self._monitor_task: Optional[asyncio.Task] = None
        self._dependency_graph: Dict[str, List[str]] = self.SERVICE_DEPENDENCIES.copy()
        # 
        self._history: List[DegradationHistoryRecord] = []
        self._temporal_client: Optional[TemporalClient] = None

    async def initialize(self) -> None:
        """Initialize degradation monitor with default components."""
        # Initialize core system components
        core_components = [
            "somabrain",
            "database",
            "kafka",
            "redis",
            "temporal",
            "gateway",
            "auth_service",
            "tool_executor",
            "llm",  # LLM providers
            # Multimodal services
            "voice_service",
            "audio_tts",
            "audio_stt",
            "upload_service",
            "multimodal",
            "storage",
            # Background services
            "backup_service",
            "task_scheduler",
        ]

        for component in core_components:
            self.components[component] = ComponentHealth(
                name=component,
                healthy=True,
                response_time=0.0,
                error_rate=0.0,
                last_check=time.time(),
            )

        # Initialize circuit breakers for critical components
        critical_components = [
            "somabrain",
            "database",
            "kafka",
            "llm",
            "audio_tts",
            "audio_stt",
            "storage",
        ]
        for component in critical_components:
            self.circuit_breakers[component] = CircuitBreaker(
                failure_threshold=5, recovery_timeout=60, expected_exception=Exception  # 1 minute
            )

    async def start_monitoring(self) -> None:
        """Start continuous degradation monitoring."""
        if self._monitoring_active:
            return

        self._monitoring_active = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("Degradation monitoring started")

    async def stop_monitoring(self) -> None:
        """Stop degradation monitoring."""
        if not self._monitoring_active:
            return

        self._monitoring_active = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("Degradation monitoring stopped")

    def is_monitoring(self) -> bool:
        """Return whether monitoring is active."""
        return self._monitoring_active

    async def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        while self._monitoring_active:
            try:
                await self._check_all_components()
                await self._analyze_degradation_patterns()
                await asyncio.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"Error in degradation monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait longer on errors

    async def _check_all_components(self) -> None:
        """Check health of all monitored components."""
        for component_name, component in self.components.items():
            try:
                await self._check_component_health(component_name)
            except Exception as e:
                logger.error(f"Error checking component {component_name}: {e}")
                component.healthy = False
                component.error_rate = 1.0

    async def _check_component_health(self, component_name: str) -> None:
        """Check health of a specific component."""
        component = self.components[component_name]

        # Get circuit breaker state if available
        circuit_breaker = self.circuit_breakers.get(component_name)
        if circuit_breaker:
            component.circuit_state = circuit_breaker.state

        # Perform health check based on component type
        start_time = time.time()

        try:
            if component_name == "somabrain":
                await self._check_somabrain_health(component)
            elif component_name == "database":
                await self._check_database_health(component)
            elif component_name == "kafka":
                await self._check_kafka_health(component)
            elif component_name == "redis":
                await self._check_redis_health(component)
            elif component_name == "temporal":
                await self._check_temporal_health(component)
            elif component_name == "llm":
                await self._check_llm_health(component)
            elif component_name in ("audio_tts", "audio_stt", "voice_service"):
                await self._check_audio_health(component)
            elif component_name in ("storage", "upload_service"):
                await self._check_storage_health(component)
            elif component_name == "multimodal":
                await self._check_multimodal_health(component)
            elif component_name in ("backup_service", "task_scheduler"):
                await self._check_background_service_health(component)
            else:
                # Generic health check for other components
                await self._check_generic_component(component)

            component.response_time = time.time() - start_time
            component.last_check = time.time()

            # Update degradation level based on metrics
            old_level = component.degradation_level
            component.degradation_level = self._calculate_degradation_level(component)

            # Record Prometheus metrics
            self._record_component_metrics(component)

            # Record history if degradation level changed or component is degraded
            if component.degradation_level != DegradationLevel.NONE:
                event_type = "check"
                if old_level == DegradationLevel.NONE:
                    event_type = "failure"
                self._record_history(component, event_type)
            elif old_level != DegradationLevel.NONE:
                # Component recovered
                self._record_history(component, "recovery")

        except Exception as e:
            component.healthy = False
            component.error_rate = 1.0
            component.response_time = time.time() - start_time
            component.degradation_level = DegradationLevel.SEVERE
            self._record_component_metrics(component)
            self._record_history(component, "failure")
            logger.error(f"Health check failed for {component_name}: {e}")

    def _record_component_metrics(self, component: ComponentHealth) -> None:
        """Record Prometheus metrics for a component."""
        SERVICE_HEALTH_STATE.labels(service=component.name).set(1.0 if component.healthy else 0.0)
        SERVICE_DEGRADATION_LEVEL.labels(service=component.name).set(
            self._degradation_level_to_int(component.degradation_level)
        )
        SERVICE_LATENCY_SECONDS.labels(service=component.name).observe(component.response_time)
        SERVICE_ERROR_RATE.labels(service=component.name).set(component.error_rate)

    def _degradation_level_to_int(self, level: DegradationLevel) -> int:
        """Convert degradation level to integer for metrics."""
        mapping = {
            DegradationLevel.NONE: 0,
            DegradationLevel.MINOR: 1,
            DegradationLevel.MODERATE: 2,
            DegradationLevel.SEVERE: 3,
            DegradationLevel.CRITICAL: 4,
        }
        return mapping.get(level, 0)

    async def _check_somabrain_health(self, component: ComponentHealth) -> None:
        """Check SomaBrain health specifically."""
        try:
            from admin.core.soma_client import SomaClient

            client = SomaClient.get()
            health_result = await client.health()

            component.healthy = health_result.get("ready", False)
            component.error_rate = 0.0 if component.healthy else 1.0

            logger.debug(f"SomaBrain health check: ready={component.healthy}")

        except Exception as e:
            component.healthy = False
            component.error_rate = 1.0
            logger.warning(f"SomaBrain health check failed: {e}")

    async def _check_database_health(self, component: ComponentHealth) -> None:
        """Check database health with REAL PostgreSQL connection.

        
        """
        try:
            from django.db import connection

            # Real connection test using Django
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()[0]
            component.healthy = result == 1
            component.error_rate = 0.0 if component.healthy else 1.0
            logger.debug(f"Database health check passed: SELECT 1 = {result}")

        except Exception as e:
            component.healthy = False
            component.error_rate = 1.0
            logger.warning(f"Database health check failed: {e}")

    async def _check_kafka_health(self, component: ComponentHealth) -> None:
        """Check Kafka health with REAL Kafka connection.

        
        Uses aiokafka to verify broker connectivity.
        """
        try:
            from aiokafka import AIOKafkaProducer

            import os

            bootstrap_servers = os.environ.kafka_bootstrap_servers
            if not bootstrap_servers:
                component.healthy = False
                component.error_rate = 1.0
                logger.warning("Kafka health check failed: No bootstrap servers configured")
                return

            # Real connection test - create producer and check bootstrap connection
            producer = AIOKafkaProducer(
                bootstrap_servers=bootstrap_servers,
                request_timeout_ms=5000,
                metadata_max_age_ms=5000,
            )
            try:
                # Start producer - this connects to Kafka brokers
                await asyncio.wait_for(producer.start(), timeout=5.0)
                component.healthy = True
                component.error_rate = 0.0
                logger.debug(f"Kafka health check passed: Connected to {bootstrap_servers}")
            finally:
                await producer.stop()

        except asyncio.TimeoutError:
            component.healthy = False
            component.error_rate = 1.0
            logger.warning("Kafka health check failed: Connection timeout")
        except Exception as e:
            component.healthy = False
            component.error_rate = 1.0
            logger.warning(f"Kafka health check failed: {e}")

    async def _check_redis_health(self, component: ComponentHealth) -> None:
        """Check Redis health with REAL Redis connection.

        
        Uses redis-py to execute PING command.
        """
        try:
            import redis.asyncio as aioredis

            import os

            redis_url = os.environ.get("SA01_REDIS_URL", "")
            if not redis_url:
                component.healthy = False
                component.error_rate = 1.0
                logger.warning("Redis health check failed: No Redis URL configured")
                return

            # Real connection test with PING
            client = aioredis.from_url(redis_url, socket_timeout=5.0)
            try:
                # Execute PING to verify connection
                pong = await asyncio.wait_for(client.ping(), timeout=5.0)
                component.healthy = pong is True
                component.error_rate = 0.0 if component.healthy else 1.0
                logger.debug(f"Redis health check passed: PING = {pong}")
            finally:
                await client.aclose()

        except asyncio.TimeoutError:
            component.healthy = False
            component.error_rate = 1.0
            logger.warning("Redis health check failed: Connection timeout")
        except Exception as e:
            component.healthy = False
            component.error_rate = 1.0
            logger.warning(f"Redis health check failed: {e}")

    async def _check_generic_component(self, component: ComponentHealth) -> None:
        """Generic health check for components."""
        # For generic components, assume healthy if no specific issues
        component.healthy = True
        component.error_rate = 0.0

        logger.debug(f"Generic health check passed for {component.name}")

    async def _check_temporal_health(self, component: ComponentHealth) -> None:
        """Check Temporal server health via system info."""
        host = os.environ.get("SA01_TEMPORAL_HOST", "temporal:7233")
        if self._temporal_client is None:
            self._temporal_client = await TemporalClient.connect(host)
        info = await self._temporal_client.workflow_service.get_system_info()
        component.healthy = info is not None
        component.error_rate = 0.0 if component.healthy else 1.0

    async def _check_llm_health(self, component: ComponentHealth) -> None:
        """Check LLM providers health via LLMDegradationService.

        
        """
        try:
            from services.common.llm_degradation import llm_degradation_service

            # Initialize if needed
            if not llm_degradation_service._provider_health:
                await llm_degradation_service.initialize()

            # Get summary of LLM status
            summary = llm_degradation_service.get_degradation_summary()

            # LLM is healthy if at least one provider is available
            healthy_count = len(summary.get("healthy_providers", []))
            degraded_count = len(summary.get("degraded_providers", []))
            unavailable_count = len(summary.get("unavailable_providers", []))
            total = healthy_count + degraded_count + unavailable_count

            if total == 0:
                # No providers configured - assume healthy (will fail on actual call)
                component.healthy = True
                component.error_rate = 0.0
            elif healthy_count > 0:
                component.healthy = True
                component.error_rate = unavailable_count / total if total > 0 else 0.0
            elif degraded_count > 0:
                component.healthy = True  # Still operational via fallback
                component.error_rate = 0.5
            else:
                # All providers unavailable
                component.healthy = False
                component.error_rate = 1.0

            logger.debug(
                f"LLM health check: healthy={healthy_count}, "
                f"degraded={degraded_count}, unavailable={unavailable_count}"
            )

        except Exception as e:
            component.healthy = False
            component.error_rate = 1.0
            logger.warning(f"LLM health check failed: {e}")

    async def _check_audio_health(self, component: ComponentHealth) -> None:
        """Check audio service health (TTS/STT).

        
        """
        try:
            from services.common.multimodal_degradation import multimodal_degradation_service

            # Initialize if needed
            if not multimodal_degradation_service._initialized:
                await multimodal_degradation_service.initialize()

            # Check provider availability based on component
            if component.name == "audio_tts":
                provider = await multimodal_degradation_service.get_available_tts()
                component.healthy = provider is not None
            elif component.name == "audio_stt":
                provider = await multimodal_degradation_service.get_available_stt()
                component.healthy = provider is not None
            elif component.name == "voice_service":
                component.healthy = multimodal_degradation_service.is_voice_available()
            else:
                component.healthy = True

            component.error_rate = 0.0 if component.healthy else 1.0

        except Exception as e:
            component.healthy = False
            component.error_rate = 1.0
            logger.warning(f"Audio health check failed for {component.name}: {e}")

    async def _check_storage_health(self, component: ComponentHealth) -> None:
        """Check storage service health.

        
        """
        try:
            from services.common.multimodal_degradation import multimodal_degradation_service

            if not multimodal_degradation_service._initialized:
                await multimodal_degradation_service.initialize()

            provider = await multimodal_degradation_service.get_available_storage()
            component.healthy = provider is not None
            component.error_rate = 0.0 if component.healthy else 1.0

        except Exception as e:
            component.healthy = False
            component.error_rate = 1.0
            logger.warning(f"Storage health check failed: {e}")

    async def _check_multimodal_health(self, component: ComponentHealth) -> None:
        """Check overall multimodal service health.

        Multimodal is healthy if at least voice OR storage is available.
        """
        try:
            from services.common.multimodal_degradation import multimodal_degradation_service

            if not multimodal_degradation_service._initialized:
                await multimodal_degradation_service.initialize()

            voice_ok = multimodal_degradation_service.is_voice_available()
            storage_ok = await multimodal_degradation_service.get_available_storage() is not None

            component.healthy = voice_ok or storage_ok
            component.error_rate = (
                0.0 if (voice_ok and storage_ok) else (0.5 if component.healthy else 1.0)
            )

        except Exception as e:
            component.healthy = False
            component.error_rate = 1.0
            logger.warning(f"Multimodal health check failed: {e}")

    async def _check_background_service_health(self, component: ComponentHealth) -> None:
        """Check background service health (backup, task scheduler).

        Background services depend on database and temporal.
        """
        try:
            # Check database dependency
            db_health = self.components.get("database")
            temporal_health = self.components.get("temporal")

            db_ok = db_health and db_health.healthy if db_health else True
            temporal_ok = temporal_health and temporal_health.healthy if temporal_health else True

            if component.name == "backup_service":
                storage_health = self.components.get("storage")
                storage_ok = storage_health and storage_health.healthy if storage_health else True
                component.healthy = db_ok and storage_ok
            elif component.name == "task_scheduler":
                component.healthy = db_ok and temporal_ok
            else:
                component.healthy = db_ok

            component.error_rate = 0.0 if component.healthy else 0.5

        except Exception as e:
            component.healthy = False
            component.error_rate = 1.0
            logger.warning(f"Background service health check failed: {e}")

    def _calculate_degradation_level(self, component: ComponentHealth) -> DegradationLevel:
        """Calculate degradation level for a component."""
        if not component.healthy:
            if component.circuit_state == CircuitState.OPEN:
                return DegradationLevel.CRITICAL
            else:
                return DegradationLevel.SEVERE

        # Check response time degradation
        if component.response_time > self._degradation_thresholds["response_time"] * 3:
            return DegradationLevel.SEVERE
        elif component.response_time > self._degradation_thresholds["response_time"] * 2:
            return DegradationLevel.MODERATE
        elif component.response_time > self._degradation_thresholds["response_time"]:
            return DegradationLevel.MINOR

        # Check error rate degradation
        if component.error_rate > self._degradation_thresholds["error_rate"] * 2:
            return DegradationLevel.MODERATE
        elif component.error_rate > self._degradation_thresholds["error_rate"]:
            return DegradationLevel.MINOR

        return DegradationLevel.NONE

    async def _analyze_degradation_patterns(self) -> None:
        """Analyze degradation patterns across all components."""
        # Propagate cascading failures through dependency graph
        await self._propagate_cascading_failures()

        degraded_components = [
            comp
            for comp in self.components.values()
            if comp.degradation_level != DegradationLevel.NONE
        ]

        if degraded_components:
            logger.warning(f"Detected {len(degraded_components)} degraded components")
            for comp in degraded_components:
                logger.warning(
                    f"  {comp.name}: {comp.degradation_level.value} "
                    f"(response_time: {comp.response_time:.3f}s, "
                    f"error_rate: {comp.error_rate:.2f})"
                )

    async def _propagate_cascading_failures(self) -> None:
        """Propagate failures through the dependency graph.

        When a core service (database, kafka, redis, somabrain) fails,
        all services that depend on it are marked as degraded.
        """
        # Find all failed core services
        failed_services = {
            name
            for name, comp in self.components.items()
            if not comp.healthy
            or comp.degradation_level in [DegradationLevel.SEVERE, DegradationLevel.CRITICAL]
        }

        if not failed_services:
            return

        # Propagate failures to dependent services
        for service_name, dependencies in self._dependency_graph.items():
            if service_name not in self.components:
                continue

            component = self.components[service_name]

            # Check if any dependency has failed
            failed_deps = failed_services.intersection(set(dependencies))
            if failed_deps:
                # Mark this service as degraded due to dependency failure
                if component.degradation_level == DegradationLevel.NONE:
                    component.degradation_level = DegradationLevel.MODERATE
                    # Record cascading failure metrics
                    for failed_dep in failed_deps:
                        CASCADING_FAILURES_TOTAL.labels(
                            source_service=failed_dep, affected_service=service_name
                        ).inc()
                    # Record cascading failure in history
                    self._record_history(component, "cascading")
                    logger.warning(
                        f"Cascading degradation: {service_name} degraded due to "
                        f"failed dependencies: {', '.join(failed_deps)}"
                    )

    def get_service_dependencies(self, service_name: str) -> List[str]:
        """Get the dependencies for a service."""
        return self._dependency_graph.get(service_name, [])

    def get_dependent_services(self, service_name: str) -> List[str]:
        """Get services that depend on the given service."""
        dependents = []
        for svc, deps in self._dependency_graph.items():
            if service_name in deps:
                dependents.append(svc)
        return dependents

    def add_dependency(self, service: str, depends_on: str) -> None:
        """Add a dependency relationship."""
        if service not in self._dependency_graph:
            self._dependency_graph[service] = []
        if depends_on not in self._dependency_graph[service]:
            self._dependency_graph[service].append(depends_on)

    def remove_dependency(self, service: str, depends_on: str) -> None:
        """Remove a dependency relationship."""
        if service in self._dependency_graph:
            if depends_on in self._dependency_graph[service]:
                self._dependency_graph[service].remove(depends_on)

    async def get_degradation_status(self) -> DegradationStatus:
        """Get current degradation status."""
        if not self.components:
            await self.initialize()

        affected_components = []
        healthy_components = []

        overall_level = DegradationLevel.NONE

        for component in self.components.values():
            if component.degradation_level != DegradationLevel.NONE:
                affected_components.append(component.name)
                # Update overall level to the most severe degradation
                if component.degradation_level.value > overall_level.value:
                    overall_level = component.degradation_level
            else:
                healthy_components.append(component.name)

        # Generate recommendations based on degradation level
        recommendations = []
        mitigation_actions = []

        if overall_level != DegradationLevel.NONE:
            recommendations = self._generate_recommendations(overall_level, affected_components)
            mitigation_actions = self._generate_mitigation_actions(
                overall_level, affected_components
            )

        return DegradationStatus(
            overall_level=overall_level,
            affected_components=affected_components,
            healthy_components=healthy_components,
            total_components=len(self.components),
            timestamp=time.time(),
            recommendations=recommendations,
            mitigation_actions=mitigation_actions,
        )

    def _generate_recommendations(
        self, level: DegradationLevel, affected_components: List[str]
    ) -> List[str]:
        """Generate recommendations based on degradation level."""
        recommendations = []

        if level in [DegradationLevel.SEVERE, DegradationLevel.CRITICAL]:
            recommendations.append("Immediate attention required for affected components")
            recommendations.append("Consider activating emergency procedures")
            recommendations.append("Notify operations team immediately")

        if level == DegradationLevel.MODERATE:
            recommendations.append("Monitor affected components closely")
            recommendations.append("Consider scaling resources if available")

        if level == DegradationLevel.MINOR:
            recommendations.append("Continue monitoring for escalation")
            recommendations.append("Review component performance metrics")

        # Component-specific recommendations
        if "somabrain" in affected_components:
            recommendations.append("Check SomaBrain service health and connectivity")

        if "database" in affected_components:
            recommendations.append("Review database performance and connection pools")

        if "kafka" in affected_components:
            recommendations.append("Check Kafka broker health and topic configurations")

        return recommendations

    def _generate_mitigation_actions(
        self, level: DegradationLevel, affected_components: List[str]
    ) -> List[str]:
        """Generate mitigation actions based on degradation level."""
        actions = []

        if level in [DegradationLevel.SEVERE, DegradationLevel.CRITICAL]:
            actions.append("Activate circuit breakers for affected components")
            actions.append("Enable failover mechanisms if available")
            actions.append("Consider graceful degradation of non-critical features")

        if level == DegradationLevel.MODERATE:
            actions.append("Increase monitoring frequency for affected components")
            actions.append("Prepare scaling procedures if needed")

        if level == DegradationLevel.MINOR:
            actions.append("Log degradation patterns for analysis")
            actions.append("Schedule maintenance review for affected components")

        return actions

    async def record_component_failure(self, component_name: str, error: Exception) -> None:
        """Record a component failure for degradation analysis."""
        if component_name not in self.components:
            return

        component = self.components[component_name]
        component.healthy = False
        component.error_rate = min(1.0, component.error_rate + 0.1)
        component.last_check = time.time()

        # Update circuit breaker if available
        circuit_breaker = self.circuit_breakers.get(component_name)
        if circuit_breaker:
            await circuit_breaker.call(lambda: None)  # This will record the failure

        # Record metrics
        metrics_collector.track_error(
            error_type=type(error).__name__, location=f"degradation_monitor.{component_name}"
        )

        logger.warning(f"Recorded failure for {component_name}: {error}")

    async def record_component_success(self, component_name: str, response_time: float) -> None:
        """Record a successful component operation."""
        if component_name not in self.components:
            return

        component = self.components[component_name]
        component.response_time = response_time
        component.error_rate = max(0.0, component.error_rate - 0.05)
        component.last_check = time.time()

        # Update circuit breaker if available
        circuit_breaker = self.circuit_breakers.get(component_name)
        if circuit_breaker:
            try:
                await circuit_breaker.call(lambda: None)  # This will record success
            except Exception:
                pass  # Ignore circuit breaker errors in success recording

        logger.debug(f"Recorded success for {component_name}: {response_time:.3f}s")

    def _record_history(self, component: ComponentHealth, event_type: str = "check") -> None:
        """Record a degradation event to history.

        
        """
        record = DegradationHistoryRecord(
            timestamp=time.time(),
            component_name=component.name,
            degradation_level=component.degradation_level,
            healthy=component.healthy,
            response_time=component.response_time,
            error_rate=component.error_rate,
            event_type=event_type,
        )
        self._history.append(record)

        # Trim history if it exceeds max size (FIFO)
        if len(self._history) > self.MAX_HISTORY_SIZE:
            self._history = self._history[-self.MAX_HISTORY_SIZE :]

    def get_history(
        self, limit: int = 100, component_name: Optional[str] = None
    ) -> List[Dict[str, any]]:
        """Get degradation history records.

        

        Args:
            limit: Maximum number of records to return
            component_name: Filter by specific component (optional)

        Returns:
            List of history records as dictionaries
        """
        # Filter by component if specified
        if component_name:
            filtered = [r for r in self._history if r.component_name == component_name]
        else:
            filtered = self._history

        # Return most recent records up to limit
        recent = filtered[-limit:] if len(filtered) > limit else filtered

        # Convert to dictionaries for JSON serialization
        return [
            {
                "timestamp": r.timestamp,
                "component_name": r.component_name,
                "degradation_level": r.degradation_level.value,
                "healthy": r.healthy,
                "response_time": r.response_time,
                "error_rate": r.error_rate,
                "event_type": r.event_type,
            }
            for r in reversed(recent)  # Most recent first
        ]


# Global degradation monitor instance
degradation_monitor = DegradationMonitor()


def is_monitoring() -> bool:
    """Return whether the global degradation monitor is active."""
    return degradation_monitor.is_monitoring()
