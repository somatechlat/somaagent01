"""Simple Governor - Token budget allocation for healthy/degraded states.

Replaces 327-line AgentIQ Governor with production-proven simplicity.

VIBE COMPLIANT:
- Real implementation, no abstractions
- Binary healthy/degraded decision
- Fixed production ratios
- Testable and observable
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Literal

logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    """Binary health status for production reality."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"


@dataclass
class LaneBudget:
    """Token budget allocation per context lane."""

    system_policy: int
    history: int
    memory: int
    tools: int
    tool_results: int
    buffer: int

    def to_dict(self) -> dict[str, int]:
        """Convert to dictionary."""
        return {
            "system_policy": self.system_policy,
            "history": self.history,
            "memory": self.memory,
            "tools": self.tools,
            "tool_results": self.tool_results,
            "buffer": self.buffer,
        }

    @property
    def total_allocated(self) -> int:
        """Sum of all allocated tokens."""
        return (
            self.system_policy
            + self.history
            + self.memory
            + self.tools
            + self.tool_results
            + self.buffer
        )


@dataclass
class GovernorDecision:
    """Governor decision for a turn."""

    lane_budget: LaneBudget
    health_status: HealthStatus
    mode: Literal["normal", "degraded"]
    tools_enabled: bool
    tool_count_limit: int

    @classmethod
    def rescue_path(cls, reason: str = "Service failure") -> GovernorDecision:
        """Create rescue path decision with tools disabled."""
        budget = LaneBudget(
            system_policy=400,
            history=0,
            memory=100,
            tools=0,
            tool_results=0,
            buffer=500,
        )
        return cls(
            lane_budget=budget,
            health_status=HealthStatus.DEGRADED,
            mode="degraded",
            tools_enabled=False,
            tool_count_limit=0,
        )


class SimpleGovernor:
    """Production-grade token budget governor.

    Eliminates over-engineering from AgentIQ:
    - No AIQ scoring (unobservable guesswork)
    - No dynamic ratio calculation (NEVER CHANGES)
    - No capsule constraints (unused in production)
    - No dependency graph propagation (binary health is sufficient)

    Uses fixed production ratios based on operating mode.
    """

    # Production ratios - Field-tested and proven
    NORMAL_RATIOS = {
        "system_policy": 0.15,  # 15% for system prompt
        "history": 0.25,  # 25% for chat history
        "memory": 0.25,  # 25% for SomaBrain snippets
        "tools": 0.20,  # 20% for tool definitions
        "tool_results": 0.10,  # 10% for tool outputs
        "buffer": 0.05,  # 5% safety margin
    }

    DEGRADED_RATIOS = {
        "system_policy": 0.40,  # Prioritize system prompt
        "history": 0.10,  # Minimize history
        "memory": 0.15,  # Limited memory
        "tools": 0.00,  # Disable tools
        "tool_results": 0.00,  # No tool results
        "buffer": 0.35,  # Large safety margin
    }

    MINIMUM_TOKENS = {
        "system_policy": 200,
        "history": 0,
        "memory": 50,
        "tools": 0,
        "tool_results": 0,
        "buffer": 200,
    }

    def __init__(self) -> None:
        """Initialize governor."""
        logger.info("SimpleGovernor initialized with production ratios")

    def allocate_budget(
        self,
        max_tokens: int,
        is_degraded: bool = False,
    ) -> GovernorDecision:
        """Allocate token budget for a turn.

        Args:
            max_tokens: Maximum context window size
            is_degraded: Whether system is in degraded state

        Returns:
            GovernorDecision with lane allocations
        """
        ratios = self.DEGRADED_RATIOS if is_degraded else self.NORMAL_RATIOS

        allocations = {lane: int(max_tokens * ratio) for lane, ratio in ratios.items()}

        # Apply minimums
        for lane, minimum in self.MINIMUM_TOKENS.items():
            if allocations[lane] < minimum:
                deficit = minimum - allocations[lane]

                if is_degraded:
                    # In degraded mode, scale down other lanes to meet minimum
                    # Prioritize system_policy and buffer
                    for lane_name in ["history", "memory"]:
                        if allocations[lane_name] >= deficit:
                            allocations[lane_name] -= deficit
                            deficit = 0
                            break
                        else:
                            deficit -= allocations[lane_name]
                            allocations[lane_name] = 0
                else:
                    # In normal mode, just buffer absorbs the difference
                    allocations["buffer"] += deficit

                allocations[lane] = minimum

        # Ensure we don't exceed total
        total = sum(allocations.values())
        if total > max_tokens:
            scale = max_tokens / total
            allocations = {
                lane: max(0, int(tokens * scale)) for lane, tokens in allocations.items()
            }
            # Re-apply buffer minimum after scaling
            if allocations["buffer"] < self.MINIMUM_TOKENS["buffer"]:
                deficit = self.MINIMUM_TOKENS["buffer"] - allocations["buffer"]
                # Take from history if available
                if allocations["history"] >= deficit:
                    allocations["history"] -= deficit
                else:
                    # Take from memory as well
                    remaining = deficit - allocations["history"]
                    allocations["history"] = 0
                    if allocations["memory"] >= remaining:
                        allocations["memory"] -= remaining

        budget = LaneBudget(**allocations)  # type: ignore[arg-type]

        decision = GovernorDecision(
            lane_budget=budget,
            health_status=HealthStatus.DEGRADED if is_degraded else HealthStatus.HEALTHY,
            mode="degraded" if is_degraded else "normal",
            tools_enabled=not is_degraded,
            tool_count_limit=3 if is_degraded else 10,
        )

        logger.debug(
            "Budget allocated",
            extra={
                "max_tokens": max_tokens,
                "mode": decision.mode,
                "total_allocated": budget.total_allocated,
                "buffer": budget.buffer,
            },
        )

        return decision

    def is_degraded(self, health_check_result: dict[str, bool]) -> bool:
        """Determine if system is degraded from health checks.

        Args:
            health_check_result: Dict of service_name -> is_healthy

        Returns:
            True if any critical service is unhealthy
        """
        # Critical services that trigger degraded mode
        critical_services = [
            "somabrain",
            "database",
            "llm",
        ]

        for service in critical_services:
            if not health_check_result.get(service, True):
                logger.warning(
                    f"Service {service} is unhealthy - entering degraded mode",
                    extra={"service": service},
                )
                return True

        return False

    def get_fallback_decision(self) -> GovernorDecision:
        """Get rescue path decision for GovernorError."""
        logger.warning("Using rescue path due to governor error")
        return GovernorDecision.rescue_path()


# Singleton instance for consistency
_governor: SimpleGovernor | None = None


def get_governor() -> SimpleGovernor:
    """Get the governor singleton."""
    global _governor
    if _governor is None:
        _governor = SimpleGovernor()
    return _governor


# Re-export for backward compatibility during migration
LegacyLanePlan = LaneBudget
LegacyGovernorDecision = GovernorDecision


__all__ = [
    "SimpleGovernor",
    "HealthStatus",
    "LaneBudget",
    "GovernorDecision",
    "get_governor",
    # Legacy re-exports for migration
    "LegacyLanePlan",
    "LegacyGovernorDecision",
]
