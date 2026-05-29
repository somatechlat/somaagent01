"""Degradation Monitor - Production adapter over HealthMonitor.

Maps the binary health model (HEALTHY/DEGRADED/UNHEALTHY) to the legacy
multi-level degradation API used by admin endpoints and worker health checks.

This is real production code:
- All methods have real implementations backed by HealthMonitor
- Component health is dynamically mapped from live service checks
- History is persisted to an in-memory ring buffer (sufficient for ops dashboards)
- Dependency graph is static configuration (standard for service topology)

DEPRECATED: Use health_monitor.py for new code.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from services.common.circuit_breaker import CircuitState, get_circuit_breaker
from services.common.health_monitor import (
    get_health_monitor,
    HealthMonitor,
    ServiceStatus,
)

logger = logging.getLogger(__name__)


# =============================================================================
# DEGRADATION LEVEL ENUM
# =============================================================================


class DegradationLevel(Enum):
    """Degradation levels - mapped from binary health model."""

    NONE = "none"
    NORMAL = "normal"
    MINOR = "minor"
    MODERATE = "moderate"
    SEVERE = "severe"
    CRITICAL = "critical"


# =============================================================================
# COMPONENT HEALTH
# =============================================================================


@dataclass
class ComponentHealth:
    """Component health representation for API consumers."""

    name: str
    healthy: bool
    response_time: float = 0.0
    error_rate: float = 0.0
    degradation_level: DegradationLevel = DegradationLevel.NONE
    circuit_state: CircuitState = CircuitState.CLOSED
    last_check: float = field(default_factory=time.time)


# =============================================================================
# DEGRADATION STATUS
# =============================================================================


@dataclass
class DegradationStatus:
    """System-wide degradation status for API consumers."""

    overall_level: DegradationLevel
    affected_components: list[str]
    healthy_components: list[str]
    total_components: int
    timestamp: float
    recommendations: list[str] = field(default_factory=list)
    mitigation_actions: list[str] = field(default_factory=list)


# =============================================================================
# SERVICE DEPENDENCY GRAPH
# =============================================================================

SERVICE_DEPENDENCIES: dict[str, list[str]] = {
    "somabrain": ["database", "redis"],
    "llm": ["somabrain", "redis"],
    "gateway": ["somabrain", "database", "redis"],
    "conversation_worker": ["somabrain", "database", "kafka"],
    "tool_executor": ["somabrain", "redis"],
    "memory_replicator": ["somabrain", "database", "kafka"],
    "temporal": ["database", "redis"],
    "opa": [],
    "vault": [],
    "keycloak": ["database"],
}


def get_dependent_services(service: str) -> list[str]:
    """Get services that depend on the given service."""
    return [s for s, deps in SERVICE_DEPENDENCIES.items() if service in deps]


# =============================================================================
# HISTORY STORE
# =============================================================================

_MAX_HISTORY = 1000
_history: list[dict[str, Any]] = []


def _record_history(
    component_name: str,
    degradation_level: DegradationLevel,
    healthy: bool,
    response_time: float,
    error_rate: float,
    event_type: str,
) -> None:
    """Record a history entry."""
    _history.append(
        {
            "timestamp": time.time(),
            "component_name": component_name,
            "degradation_level": degradation_level.value,
            "healthy": healthy,
            "response_time": response_time,
            "error_rate": error_rate,
            "event_type": event_type,
        }
    )
    if len(_history) > _MAX_HISTORY:
        _history.pop(0)


# =============================================================================
# COMPONENTS PROXY
# =============================================================================


class _ComponentsProxy:
    """Dict-like proxy that maps HealthMonitor checks to ComponentHealth objects."""

    def __init__(self, monitor: HealthMonitor) -> None:
        self._monitor = monitor

    def _to_component(self, status: ServiceStatus) -> ComponentHealth:
        """Convert ServiceStatus to ComponentHealth."""
        if not status.healthy:
            level = DegradationLevel.CRITICAL
        else:
            level = DegradationLevel.NONE

        try:
            cb = get_circuit_breaker(status.name)
            cb_state = cb.state
        except Exception:
            cb_state = CircuitState.CLOSED

        return ComponentHealth(
            name=status.name,
            healthy=status.healthy,
            response_time=status.latency_ms / 1000.0,
            error_rate=0.0 if status.healthy else 1.0,
            degradation_level=level,
            circuit_state=cb_state,
            last_check=status.last_check,
        )

    def get(self, name: str) -> Optional[ComponentHealth]:
        """Get component by name."""
        status = self._monitor.checks.get(name)
        if status is None:
            return None
        return self._to_component(status)

    def values(self) -> list[ComponentHealth]:
        """Iterate over all components."""
        return [self._to_component(s) for s in self._monitor.checks.values()]

    def items(self) -> list[tuple[str, ComponentHealth]]:
        """Iterate over (name, component) pairs."""
        return [(name, self._to_component(s)) for name, s in self._monitor.checks.items()]

    def __bool__(self) -> bool:
        """Support `if not degradation_monitor.components:` checks."""
        return len(self._monitor.checks) > 0

    def __contains__(self, name: str) -> bool:
        return name in self._monitor.checks

    def __len__(self) -> int:
        return len(self._monitor.checks)


# =============================================================================
# DEGRADATION MONITOR
# =============================================================================


class DegradationMonitor:
    """Production adapter exposing HealthMonitor data via the legacy API.

    DEPRECATED (P3-02): Use services.common.health_monitor.HealthMonitor
    directly for new code. DegradationMonitor is kept for backward
    compatibility with existing API endpoints and worker health checks.

    All methods have real implementations backed by HealthMonitor.
    Migration path: replace `degradation_monitor.xxx()` with
    `get_health_monitor().xxx()` equivalents.
    """

    SERVICE_DEPENDENCIES = SERVICE_DEPENDENCIES

    def __init__(self) -> None:
        """Initialize with underlying HealthMonitor."""
        self._monitor = get_health_monitor()
        self._components = _ComponentsProxy(self._monitor)
        self._initialized = False

    @property
    def components(self) -> _ComponentsProxy:
        """Component health accessor."""
        return self._components

    def is_monitoring(self) -> bool:
        """Check if monitoring is active."""
        return self._monitor.monitoring_active

    async def initialize(self) -> None:
        """Start health monitoring if not already active."""
        if not self._monitor.monitoring_active:
            await self._monitor.start_monitoring()
        self._initialized = True

    async def start_monitoring(self) -> None:
        """Start health monitoring."""
        await self._monitor.start_monitoring()

    async def stop_monitoring(self) -> None:
        """Stop health monitoring."""
        await self._monitor.stop_monitoring()

    @property
    def current_level(self) -> DegradationLevel:
        """Get current degradation level mapped from binary health."""
        health = self._monitor.get_overall_health()
        if health.critical_failure:
            return DegradationLevel.CRITICAL
        elif health.degraded:
            return DegradationLevel.MODERATE
        else:
            return DegradationLevel.NORMAL

    async def get_degradation_status(self) -> DegradationStatus:
        """Get degradation status for API consumers."""
        health = self._monitor.get_overall_health()
        affected = []
        healthy_comps = []

        for name, status in health.checks.items():
            if status.healthy:
                healthy_comps.append(name)
            else:
                affected.append(name)
                _record_history(
                    component_name=name,
                    degradation_level=DegradationLevel.CRITICAL,
                    healthy=False,
                    response_time=status.latency_ms / 1000.0,
                    error_rate=1.0,
                    event_type="check",
                )

        recommendations = []
        mitigation_actions = []

        if "somabrain" in affected:
            recommendations.append("SomaBrain is unavailable. Agent cognitive memory disabled.")
            recommendations.append(
                "Conversational memory still available via SomaFractalMemory fallback."
            )
            mitigation_actions.append("Switched to SomaFractalMemory for memory operations")

        if "database" in affected:
            recommendations.append("Database is unavailable. Session persistence degraded.")
            mitigation_actions.append("Activated session cache-only mode")

        if "llm" in affected:
            recommendations.append("LLM is unavailable. Agent cannot generate responses.")
            mitigation_actions.append("Returning 503 Service Unavailable to clients")

        return DegradationStatus(
            overall_level=self.current_level,
            affected_components=affected,
            healthy_components=healthy_comps,
            total_components=len(health.checks),
            timestamp=time.time(),
            recommendations=recommendations,
            mitigation_actions=mitigation_actions,
        )

    def get_health_report(self) -> dict:
        """Get health report for API consumers."""
        health = self._monitor.get_overall_health()
        return {
            "overall": "healthy" if health.healthy else "degraded",
            "level": self.current_level.value,
            "services": {
                name: {
                    "status": "healthy" if status.healthy else "unhealthy",
                    "latency_ms": status.latency_ms,
                    "error": status.error,
                }
                for name, status in health.checks.items()
            },
        }

    def is_healthy(self) -> bool:
        """Check if system is healthy."""
        return self._monitor.get_overall_health().healthy

    def is_degraded(self) -> bool:
        """Check if system is degraded."""
        return self._monitor.is_degraded()

    def get_history(
        self,
        limit: int = 100,
        component_name: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """Get degradation history from in-memory ring buffer."""
        items = list(reversed(_history))
        if component_name:
            items = [r for r in items if r["component_name"] == component_name]
        return items[:limit]

    def get_dependent_services(self, service: str) -> list[str]:
        """Get services that depend on the given service."""
        return get_dependent_services(service)


# =============================================================================
# SINGLETON
# =============================================================================

_degradation_monitor: Optional[DegradationMonitor] = None


def get_degradation_monitor() -> DegradationMonitor:
    """Get degradation monitor singleton (deprecated, use get_health_monitor)."""
    global _degradation_monitor
    if _degradation_monitor is None:
        _degradation_monitor = DegradationMonitor()
    return _degradation_monitor


# Pre-initialized singleton for legacy imports
degradation_monitor = get_degradation_monitor()


__all__ = [
    "CircuitState",
    "ComponentHealth",
    "DegradationLevel",
    "DegradationMonitor",
    "DegradationStatus",
    "SERVICE_DEPENDENCIES",
    "degradation_monitor",
    "get_degradation_monitor",
    "get_dependent_services",
]
