"""Budget Metric Registry — Universal Metric Definitions.

SRS Source: SRS-BUDGET-SYSTEM-2026-01-16 Section 5

Applied Personas:
- PhD Developer: Immutable dataclass design
- PhD Analyst: Complete metric taxonomy
- Security Auditor: Locked critical metrics
- Performance Engineer: Minimal memory footprint
- ISO Documenter: Comprehensive field documentation
- Django Evangelist: Django-compatible patterns

Vibe Coding Rules:
- NO hardcoded values outside this registry
- ALL metrics defined here, nowhere else
- Immutable (frozen=True) for thread safety
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Literal


@dataclass(frozen=True)
class BudgetedMetric:
    """Universal metric definition — immutable and thread-safe.

    This dataclass defines a billable metric that can be:
    1. Enforced (pre-action budget check)
    2. Recorded (post-action Lago event)
    3. Toggled (per-tenant enable/disable)

    Attributes:
        code: Internal metric identifier (e.g., "tokens")
        name: Human-readable display name
        unit: Unit of measurement (count, tokens, minutes, gb)
        tier: Importance tier (critical, important, monitor)
        default_limit: Default limit for Free plan
        cost_per_unit: Cost per unit for billing ($)
        enforce_pre: If True, check BEFORE action (fail-closed)
        lago_code: Metric code in Lago billing system
        lockable: If False, cannot be disabled by tenant
    """

    code: str
    name: str
    unit: Literal["count", "tokens", "minutes", "gb"]
    tier: Literal["critical", "important", "monitor"]
    default_limit: int
    cost_per_unit: float
    enforce_pre: bool
    lago_code: str
    lockable: bool = True


# =============================================================================
# METRIC REGISTRY — Single Source of Truth
# =============================================================================

METRIC_REGISTRY: Dict[str, BudgetedMetric] = {
    # -------------------------------------------------------------------------
    # TIER 1: CRITICAL — Always enforced, gate chat/actions
    # -------------------------------------------------------------------------
    "tokens": BudgetedMetric(
        code="tokens",
        name="Tokens",
        unit="tokens",
        tier="critical",
        default_limit=100_000,  # 100K/month
        cost_per_unit=0.00001,  # $0.01/1K
        enforce_pre=True,  # MUST check BEFORE LLM call
        lago_code="tokens",
        lockable=False,  # Cannot be disabled
    ),
    "tool_calls": BudgetedMetric(
        code="tool_calls",
        name="Tool Calls",
        unit="count",
        tier="critical",
        default_limit=100,  # 100/month
        cost_per_unit=0.01,  # $0.01/call
        enforce_pre=True,  # MUST check BEFORE tool exec
        lago_code="tool_calls",
        lockable=False,
    ),
    "images": BudgetedMetric(
        code="images",
        name="Image Generations",
        unit="count",
        tier="critical",
        default_limit=10,  # 10/month
        cost_per_unit=0.04,  # $0.04/image
        enforce_pre=True,  # MUST check BEFORE generation
        lago_code="images",
        lockable=False,
    ),
    "voice_minutes": BudgetedMetric(
        code="voice_minutes",
        name="Voice Minutes",
        unit="minutes",
        tier="critical",
        default_limit=10,  # 10 min/month
        cost_per_unit=0.06,  # $0.06/min
        enforce_pre=True,
        lago_code="voice_minutes",
        lockable=False,
    ),
    # -------------------------------------------------------------------------
    # TIER 2: IMPORTANT — Enforced, but can be toggled
    # -------------------------------------------------------------------------
    "api_calls": BudgetedMetric(
        code="api_calls",
        name="API Calls",
        unit="count",
        tier="important",
        default_limit=10_000,  # 10K/month
        cost_per_unit=0.0001,  # $0.10/1K
        enforce_pre=True,
        lago_code="api_calls",
        lockable=True,
    ),
    "memory_tokens": BudgetedMetric(
        code="memory_tokens",
        name="Memory Tokens",
        unit="tokens",
        tier="important",
        default_limit=500_000,  # 500K/month
        cost_per_unit=0.000001,  # $0.001/1K
        enforce_pre=False,  # Record only, don't block
        lago_code="memory_tokens",
        lockable=True,
    ),
    "vector_ops": BudgetedMetric(
        code="vector_ops",
        name="Vector Operations",
        unit="count",
        tier="important",
        default_limit=50_000,  # 50K/month
        cost_per_unit=0.001,  # $1/1K
        enforce_pre=False,  # Milvus ops - record only
        lago_code="vector_ops",
        lockable=True,
    ),
    "learning": BudgetedMetric(
        code="learning",
        name="Learning Cycles",
        unit="count",
        tier="important",
        default_limit=100,  # 100/month
        cost_per_unit=0.10,  # $0.10/cycle
        enforce_pre=True,  # Gate brain learning
        lago_code="learning_credits",
        lockable=True,
    ),
    # -------------------------------------------------------------------------
    # TIER 3: MONITOR — Record only, no blocking
    # -------------------------------------------------------------------------
    "storage_gb": BudgetedMetric(
        code="storage_gb",
        name="File Storage",
        unit="gb",
        tier="monitor",
        default_limit=10,  # 10GB
        cost_per_unit=0.10,  # $0.10/GB/month
        enforce_pre=False,  # Monitor only
        lago_code="storage_gb",
        lockable=True,
    ),
    "sessions": BudgetedMetric(
        code="sessions",
        name="Concurrent Sessions",
        unit="count",
        tier="monitor",
        default_limit=5,  # 5 concurrent
        cost_per_unit=0.0,  # Included
        enforce_pre=True,  # Limit concurrency
        lago_code="sessions",
        lockable=True,
    ),
}


def get_metric(code: str) -> BudgetedMetric:
    """Get metric definition by code.

    Args:
        code: Metric code (e.g., "tokens")

    Returns:
        BudgetedMetric definition

    Raises:
        KeyError: If metric code not found
    """
    if code not in METRIC_REGISTRY:
        raise KeyError(f"Unknown metric: {code}")
    return METRIC_REGISTRY[code]


def list_metrics() -> list[BudgetedMetric]:
    """List all registered metrics.

    Returns:
        List of all BudgetedMetric definitions
    """
    return list(METRIC_REGISTRY.values())


def list_critical_metrics() -> list[BudgetedMetric]:
    """List metrics that gate actions (enforce_pre=True).

    Returns:
        List of critical metrics that must be checked before actions
    """
    return [m for m in METRIC_REGISTRY.values() if m.enforce_pre]
