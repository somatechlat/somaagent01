"""Unified TRIAD degradation contract.

ONE vocabulary for somaAgent01 + somabrain + somafractalmemory.

Law (operator-absolute):
  Failures FLAG. They never fabricate empty success.
  Empty results ≠ degraded results. Degraded is always explicit.

This module is the product-wide status shape and the mapper from each
organ's local health model into that shape. No organ may invent a second
spelling of these fields.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable, Sequence


class DegradationStatus(str, Enum):
    """Product-wide status. The only spelling."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class CircuitState(str, Enum):
    """Circuit state. Shared with Brain per-tenant breaker."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class FeatureState(str, Enum):
    """Feature state. Shared with FeatureRegistry."""

    ON = "on"
    DEGRADED = "degraded"
    DISABLED = "disabled"


# Critical services whose failure forces product DEGRADED (agent HealthMonitor).
CRITICAL_SERVICES = ("somabrain", "database", "llm")


@dataclass(frozen=True)
class DegradationReport:
    """Single product-facing degradation record."""

    status: DegradationStatus
    component: str
    reason: str | None = None
    circuit: CircuitState = CircuitState.CLOSED
    feature_state: FeatureState = FeatureState.ON
    mode: str = "normal"  # normal | rescue
    tenant: str | None = None
    details: dict[str, Any] = field(default_factory=dict)

    @property
    def degraded(self) -> bool:
        """True when the component is not fully healthy (API `degraded` flag)."""
        return self.status is not DegradationStatus.HEALTHY

    def to_dict(self) -> dict[str, Any]:
        """Serialize for HTTP/Kafka — one schema everywhere."""
        return {
            "status": self.status.value,
            "degraded": self.degraded,
            "component": self.component,
            "reason": self.reason,
            "circuit": self.circuit.value,
            "feature_state": self.feature_state.value,
            "mode": self.mode,
            "tenant": self.tenant,
            "details": dict(self.details),
        }


def healthy(component: str, **details: Any) -> DegradationReport:
    """Healthy report."""
    return DegradationReport(
        status=DegradationStatus.HEALTHY, component=component, details=details
    )


def degraded(
    component: str, reason: str, *, mode: str = "normal", **details: Any
) -> DegradationReport:
    """Degraded report. Reason is mandatory — never silent."""
    if not reason or not str(reason).strip():
        raise ValueError("degraded() requires a non-empty reason (flag, never silent)")
    return DegradationReport(
        status=DegradationStatus.DEGRADED,
        component=component,
        reason=str(reason),
        mode=mode,
        details=details,
    )


def unhealthy(component: str, reason: str, **details: Any) -> DegradationReport:
    """Unhealthy report. Reason is mandatory."""
    if not reason or not str(reason).strip():
        raise ValueError("unhealthy() requires a non-empty reason")
    return DegradationReport(
        status=DegradationStatus.UNHEALTHY,
        component=component,
        reason=str(reason),
        details=details,
    )


def flag_fields(
    report: DegradationReport,
) -> dict[str, Any]:
    """Merge into API responses: degraded + degraded_reason + status.

    Use on every Brain/SFM/agent response that can be partially wrong.
    """
    return {
        "degraded": report.degraded,
        "degraded_reason": report.reason,
        "degradation_status": report.status.value,
        "degradation_component": report.component,
    }


def aggregate(
    reports: Iterable[DegradationReport],
) -> dict[str, Any]:
    """Product status across organs.

    UNHEALTHY if any unhealthy; DEGRADED if any degraded; else HEALTHY.
    """
    items = list(reports)
    if not items:
        return {
            "status": DegradationStatus.HEALTHY.value,
            "degraded": False,
            "components": [],
        }
    if any(r.status is DegradationStatus.UNHEALTHY for r in items):
        status = DegradationStatus.UNHEALTHY
    elif any(r.status is DegradationStatus.DEGRADED for r in items):
        status = DegradationStatus.DEGRADED
    else:
        status = DegradationStatus.HEALTHY
    return {
        "status": status.value,
        "degraded": status is not DegradationStatus.HEALTHY,
        "components": [r.to_dict() for r in items],
    }


def from_binary_health(
    component: str,
    *,
    healthy_flag: bool,
    reason: str | None = None,
    circuit: str | CircuitState = CircuitState.CLOSED,
    mode: str = "normal",
    **details: Any,
) -> DegradationReport:
    """Map a binary healthy/unhealthy signal (agent HealthMonitor style)."""
    if isinstance(circuit, str):
        circuit = CircuitState(circuit)
    if healthy_flag and circuit is CircuitState.CLOSED:
        return healthy(component, mode=mode, **details)
    if not healthy_flag and circuit is CircuitState.OPEN:
        return unhealthy(
            component,
            reason or f"{component} circuit open",
            mode=mode,
            **details,
        )
    return degraded(
        component,
        reason or f"{component} degraded",
        mode=mode,
        **details,
    )


def assert_reason_when_degraded(payload: dict[str, Any]) -> None:
    """Test helper: a payload that claims degraded must carry a reason."""
    if payload.get("degraded") and not payload.get("degraded_reason"):
        raise AssertionError(
            "degraded=true without degraded_reason — silent failure is forbidden"
        )


__all__ = [
    "CircuitState",
    "CRITICAL_SERVICES",
    "DegradationReport",
    "DegradationStatus",
    "FeatureState",
    "aggregate",
    "assert_reason_when_degraded",
    "degraded",
    "flag_fields",
    "from_binary_health",
    "healthy",
    "unhealthy",
]
