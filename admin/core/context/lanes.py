"""
Lane Allocation - Token budget distribution across 5 context lanes.

From SRS-CONTEXT-BUILDING:
- Uses body.persona.learned.lane_preferences if available (the body view of
  ``Capsule.persona_config["learned"]``, see
  ``admin.core.models.core.Capsule._build_body_dict``)
- Falls back to ``SimpleGovernor`` ratios — the one ratio authority.

PhD Analyst: Mathematical allocation with normalization.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from admin.core.models import Capsule


# One vocabulary for the context lanes: the keys ContextBuilder reads and the
# AgentIQ surface reports. A second spelling is a second concept (AP-06).
LANE_KEYS = ("system", "history", "memory", "tools", "buffer")


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

    def to_dict(self) -> Dict[str, float]:
        """Shares keyed by ``LANE_KEYS`` — the only spelling of the vocabulary."""
        return {
            "system": self.system,
            "history": self.history,
            "memory": self.memory,
            "tools": self.tools,
            "buffer": self.buffer,
        }


# Default allocations are GONE as a second authority. Ratio defaults come
# from SimpleGovernor.ratios_for() — see get_lane_allocation.
def _gov_default_shares() -> LaneAllocation:
    from services.common.simple_governor import get_governor

    ratios = get_governor().ratios_for(is_degraded=False)
    return LaneAllocation(
        system=ratios["system"],
        history=ratios["history"],
        memory=ratios["memory"],
        tools=ratios["tools"],
        buffer=ratios["buffer"],
    )


async def get_lane_allocation(
    capsule: "Capsule", *, body: Dict[str, Any] | None = None
) -> LaneAllocation:
    """
    Get lane allocation from body.persona.learned or governor defaults.

    Priority:
    1. body.persona.learned.lane_preferences (brain-learned)
    2. SimpleGovernor healthy ratios — the single ratio authority. A second
       table of defaults here would be a second authority and could disagree
       with the governor (AP-06 / one-authority law).

    Args:
        capsule: Capsule model with body
        body: Pre-fetched ``capsule.body``. When given, no ORM runs here.

    Returns:
        LaneAllocation with normalized percentages

    Raises:
        ValueError: If ``lane_preferences`` is present but malformed. A
            present-but-broken setting is refused, never silently ignored.
    """

    if body is None:
        body = getattr(capsule, "_cached_body", None) or (
            await capsule.async_body() if hasattr(capsule, "async_body") else capsule.body or {}
        )

    persona = body.get("persona", {}) or {}
    learned = persona.get("learned", {}) or {}
    lane_prefs = learned.get("lane_preferences")

    # Brain-learned preferences win when present. Present and malformed is a
    # refusal (Rule 2/91) — not a silent fall-through to defaults.
    if lane_prefs is not None:
        if not isinstance(lane_prefs, dict):
            raise ValueError(
                "persona.learned.lane_preferences must be a mapping of "
                f"{', '.join(LANE_KEYS)}"
            )
        missing = [k for k in LANE_KEYS if lane_prefs.get(k) is None]
        if missing:
            raise ValueError(
                "persona.learned.lane_preferences is missing lane shares: "
                + ", ".join(missing)
            )
        try:
            return LaneAllocation(
                system=float(lane_prefs["system"]),
                history=float(lane_prefs["history"]),
                memory=float(lane_prefs["memory"]),
                tools=float(lane_prefs["tools"]),
                buffer=float(lane_prefs["buffer"]),
            )
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "persona.learned.lane_preferences must be numeric shares summing to 1.0"
            ) from exc

    # Governor is the one ratio authority. Intelligence level no longer picks
    # a second table of defaults — that was two authorities for one concept.
    return _gov_default_shares()
