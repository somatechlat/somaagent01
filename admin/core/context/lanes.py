"""
Lane Allocation - Token budget distribution across 5 context lanes.

From SRS-CONTEXT-BUILDING:
- Uses capsule.body.learned.lane_preferences if available
- Falls back to intelligence-based defaults

PhD Analyst: Mathematical allocation with normalization.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict

if TYPE_CHECKING:
    from admin.core.models import Capsule


@dataclass(frozen=True)
class LaneAllocation:
    """
    Token allocation percentages for 5 context lanes.

    Must sum to 1.0 (normalized).
    """

    system: float  # Base prompt
    history: float  # Conversation history
    memory: float  # SomaBrain recall
    tools: float  # Tool descriptions
    buffer: float  # User message

    def __post_init__(self) -> None:
        """Validate sum is ~1.0."""
        total = self.system + self.history + self.memory + self.tools + self.buffer
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Lane allocation must sum to 1.0, got {total}")

    def allocate(self, max_tokens: int) -> Dict[str, int]:
        """
        Allocate token budget per lane.

        Args:
            max_tokens: Total available tokens

        Returns:
            Dict mapping lane name to token count
        """
        return {
            "system": int(max_tokens * self.system),
            "history": int(max_tokens * self.history),
            "memory": int(max_tokens * self.memory),
            "tools": int(max_tokens * self.tools),
            "buffer": int(max_tokens * self.buffer),
        }


# Default allocations by intelligence level
DEFAULT_LANES_LOW = LaneAllocation(
    system=0.20, history=0.20, memory=0.20, tools=0.20, buffer=0.20
)

DEFAULT_LANES_MID = LaneAllocation(
    system=0.15, history=0.30, memory=0.25, tools=0.20, buffer=0.10
)

DEFAULT_LANES_HIGH = LaneAllocation(
    system=0.10, history=0.35, memory=0.30, tools=0.15, buffer=0.10
)


def get_lane_allocation(capsule: "Capsule") -> LaneAllocation:
    """
    Get lane allocation from capsule.body.learned or defaults.

    Priority:
    1. capsule.body.learned.lane_preferences (brain-learned)
    2. Default based on intelligence_level

    Args:
        capsule: Capsule model with body

    Returns:
        LaneAllocation with normalized percentages
    """
    body: Dict[str, Any] = capsule.body or {}

    # Try brain-learned preferences first
    learned = body.get("learned", {})
    lane_prefs = learned.get("lane_preferences")

    if lane_prefs and isinstance(lane_prefs, dict):
        try:
            return LaneAllocation(
                system=float(lane_prefs.get("system", 0.15)),
                history=float(lane_prefs.get("history", 0.30)),
                memory=float(lane_prefs.get("memory", 0.25)),
                tools=float(lane_prefs.get("tools", 0.20)),
                buffer=float(lane_prefs.get("buffer", 0.10)),
            )
        except (ValueError, TypeError):
            pass  # Fall through to defaults

    # Fall back to intelligence-based defaults
    persona = body.get("persona", {})
    knobs = persona.get("knobs", {})
    intelligence = knobs.get("intelligence_level", 5)

    if intelligence <= 3:
        return DEFAULT_LANES_LOW
    elif intelligence <= 6:
        return DEFAULT_LANES_MID
    else:
        return DEFAULT_LANES_HIGH
