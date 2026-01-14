"""Degradation Monitor - Compatibility shim.

This module was replaced by health_monitor.py which provides a simpler
binary health model. This shim provides backwards compatibility for
existing imports.

DEPRECATED: Use health_monitor.py for new code.
"""

from __future__ import annotations

import logging
from enum import Enum
from typing import Optional

from services.common.health_monitor import (
    HealthMonitor,
    ServiceHealth,
    ServiceStatus,
    OverallHealth,
    get_health_monitor,
)

logger = logging.getLogger(__name__)


class DegradationLevel(Enum):
    """Legacy degradation levels - mapped to binary health model."""

    NORMAL = "normal"
    MINOR = "minor"
    MODERATE = "moderate"
    SEVERE = "severe"
    CRITICAL = "critical"


class DegradationMonitor:
    """Compatibility wrapper around HealthMonitor.

    Maps the old multi-level degradation model to binary healthy/unhealthy.
    """

    def __init__(self):
        """Initialize with underlying HealthMonitor."""
        self._monitor = get_health_monitor()

    @property
    def current_level(self) -> DegradationLevel:
        """Get current degradation level (mapped from binary health)."""
        health = self._monitor.get_overall_health()
        if health.critical_failure:
            return DegradationLevel.CRITICAL
        elif health.degraded:
            return DegradationLevel.MODERATE
        else:
            return DegradationLevel.NORMAL

    def get_health_report(self) -> dict:
        """Get health report in legacy format."""
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


# Singleton for backwards compatibility
_degradation_monitor: Optional[DegradationMonitor] = None


def get_degradation_monitor() -> DegradationMonitor:
    """Get degradation monitor singleton (deprecated, use get_health_monitor)."""
    global _degradation_monitor
    if _degradation_monitor is None:
        _degradation_monitor = DegradationMonitor()
    return _degradation_monitor


# Provide singleton instance for legacy imports
degradation_monitor = None  # Lazy initialization


def _init_singleton():
    """Initialize singleton on first access."""
    global degradation_monitor
    if degradation_monitor is None:
        degradation_monitor = get_degradation_monitor()


__all__ = [
    "DegradationLevel",
    "DegradationMonitor",
    "degradation_monitor",
    "get_degradation_monitor",
]
