"""Simple Governor - Token budget allocation for healthy/degraded states.

Replaces 327-line AgentIQ Governor with production-proven simplicity.

Lane vocabulary is ``admin.core.context.lanes.LANE_KEYS`` — exactly five keys:
system, history, memory, tools, buffer. One vocabulary for one concept (AP-06).

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

# Same spelling as admin.core.context.lanes.LANE_KEYS. Duplicated as literals
# only because importing the admin package would drag the context stack into
# this standalone module; the governor tests assert the two spellings match.
LANE_KEYS = ("system", "history", "memory", "tools", "buffer")


class HealthStatus(str, Enum):
    """Binary health status for production reality."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"


@dataclass
class LaneBudget:
    """Token budget allocation per context lane (LANE_KEYS)."""

    system: int
    history: int
    memory: int
    tools: int
    buffer: int

    def to_dict(self) -> dict[str, int]:
        """Token counts keyed by LANE_KEYS — the only spelling."""
        return {
            "system": self.system,
            "history": self.history,
            "memory": self.memory,
            "tools": self.tools,
            "buffer": self.buffer,
        }

    @property
    def total_allocated(self) -> int:
        """Sum of all allocated tokens."""
        return (
            self.system
            + self.history
            + self.memory
            + self.tools
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
            system=400,
            history=0,
            memory=100,
            tools=0,
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

    # Production ratios - Field-tested and proven.
    # The five keys are LANE_KEYS. They sum to 1.0 and every token of the
    # turn budget is allocated to a lane that actually reads it.
    NORMAL_RATIOS = {
        "system": 0.15,  # 15% system prompt
        "history": 0.35,  # 35% chat history (incl. tool output turns)
        "memory": 0.25,  # 25% SomaBrain snippets
        "tools": 0.20,  # 20% tool definitions
        "buffer": 0.05,  # 5% current user message
    }

    DEGRADED_RATIOS = {
        "system": 0.40,  # Prioritize system prompt
        "history": 0.10,  # Minimize history
        "memory": 0.15,  # Limited memory
        "tools": 0.00,  # Disable tools
        "buffer": 0.35,  # Large safety margin
    }

    MINIMUM_TOKENS = {
        "system": 200,
        "history": 0,
        "memory": 50,
        "tools": 0,
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

        The five lanes are LANE_KEYS. Allocations sum to exactly ``max_tokens``
        — a budget that is allocated and then dropped is the D-06 defect.

        Args:
            max_tokens: Maximum context window size
            is_degraded: Whether system is in degraded state

        Returns:
            GovernorDecision with lane allocations
        """
        ratios = self.DEGRADED_RATIOS if is_degraded else self.NORMAL_RATIOS

        # Cumulative rounding: the five ints sum to exactly max_tokens, so no
        # token is allocated to a lane and then thrown away on the floor.
        allocations: dict[str, int] = {}
        running = 0.0
        given = 0
        for lane, ratio in ratios.items():
            running += max_tokens * ratio
            allocations[lane] = int(running) - given
            given = int(running)

        # Raise any lane below its minimum by transferring from a donor lane.
        # Transfers only — the total stays max_tokens (never invent tokens).
        for lane, minimum in self.MINIMUM_TOKENS.items():
            if allocations[lane] >= minimum:
                continue
            deficit = minimum - allocations[lane]
            donors = (
                ("history", "memory") if is_degraded else ("buffer", "history", "memory")
            )
            for donor in donors:
                if donor == lane:
                    continue
                spare = allocations[donor] - self.MINIMUM_TOKENS[donor]
                if spare <= 0:
                    continue
                take = min(deficit, spare)
                allocations[donor] -= take
                deficit -= take
                if deficit == 0:
                    break
            allocations[lane] = minimum - deficit

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
                    "Service %s is unhealthy - entering degraded mode",
                    service,
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


__all__ = [
    "SimpleGovernor",
    "HealthStatus",
    "LaneBudget",
    "GovernorDecision",
    "get_governor",
    "LANE_KEYS",
]
