"""
Derivation Tables - Lookup tables for 3-knob system.

From V3 Theory:
- INTELLIGENCE: temperature, max_tokens, rlm_iter, recall_limit, model_tier
- AUTONOMY: require_hitl, tool_approval, egress_allowed
- RESOURCE: token_limit, cost_tier, thinking_budget

PhD Analyst: Mathematical derivation tables from SRS-AGENTIQ.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

from admin.core.agentiq.settings import (
    EgressAllowed,
    ModelTier,
    ToolApproval,
)


@dataclass(frozen=True)
class IntelligenceRow:
    """Derivation from intelligence_level."""

    temperature: float
    max_tokens: int
    rlm_iterations: int
    recall_limit: int
    model_tier: ModelTier
    brain_query_enabled: bool


@dataclass(frozen=True)
class AutonomyRow:
    """Derivation from autonomy_level."""

    require_hitl: bool
    tool_approval: ToolApproval
    egress_allowed: EgressAllowed


@dataclass(frozen=True)
class ResourceRow:
    """Derivation from resource_budget."""

    token_limit: int
    cost_tier: str
    thinking_budget: int


# === INTELLIGENCE TABLE ===
# Level ranges: 1-3, 4-6, 7-8, 9-10
INTELLIGENCE_TABLE: Dict[Tuple[int, int], IntelligenceRow] = {
    (1, 3): IntelligenceRow(
        temperature=0.3,
        max_tokens=512,
        rlm_iterations=1,
        recall_limit=5,
        model_tier=ModelTier.BUDGET,
        brain_query_enabled=False,
    ),
    (4, 6): IntelligenceRow(
        temperature=0.7,
        max_tokens=2048,
        rlm_iterations=2,
        recall_limit=15,
        model_tier=ModelTier.STANDARD,
        brain_query_enabled=True,
    ),
    (7, 8): IntelligenceRow(
        temperature=0.8,
        max_tokens=4096,
        rlm_iterations=3,
        recall_limit=25,
        model_tier=ModelTier.PREMIUM,
        brain_query_enabled=True,
    ),
    (9, 10): IntelligenceRow(
        temperature=0.9,
        max_tokens=8192,
        rlm_iterations=5,
        recall_limit=50,
        model_tier=ModelTier.FLAGSHIP,
        brain_query_enabled=True,
    ),
}


# === AUTONOMY TABLE ===
# Level ranges: 1-3, 4-6, 7-8, 9-10
AUTONOMY_TABLE: Dict[Tuple[int, int], AutonomyRow] = {
    (1, 3): AutonomyRow(
        require_hitl=True,
        tool_approval=ToolApproval.ALL,
        egress_allowed=EgressAllowed.NONE,
    ),
    (4, 6): AutonomyRow(
        require_hitl=False,  # Only for dangerous
        tool_approval=ToolApproval.DANGEROUS,
        egress_allowed=EgressAllowed.WHITELIST,
    ),
    (7, 8): AutonomyRow(
        require_hitl=False,
        tool_approval=ToolApproval.NONE,
        egress_allowed=EgressAllowed.EXPANDED,
    ),
    (9, 10): AutonomyRow(
        require_hitl=False,
        tool_approval=ToolApproval.NONE,
        egress_allowed=EgressAllowed.UNRESTRICTED,
    ),
}


# === RESOURCE TABLE ===
# Budget ranges: 0.01-0.10, 0.10-0.50, 0.50-2.00, 2.00+
RESOURCE_TABLE: Dict[Tuple[float, float], ResourceRow] = {
    (0.0, 0.10): ResourceRow(
        token_limit=1000,
        cost_tier="budget",
        thinking_budget=256,
    ),
    (0.10, 0.50): ResourceRow(
        token_limit=10000,
        cost_tier="standard",
        thinking_budget=1024,
    ),
    (0.50, 2.00): ResourceRow(
        token_limit=50000,
        cost_tier="premium",
        thinking_budget=2048,
    ),
    (2.00, float("inf")): ResourceRow(
        token_limit=100000,
        cost_tier="flagship",
        thinking_budget=4096,
    ),
}


def lookup_intelligence(level: int) -> IntelligenceRow:
    """Look up intelligence derivation by level (1-10)."""
    level = max(1, min(10, level))  # Clamp to bounds
    for (low, high), row in INTELLIGENCE_TABLE.items():
        if low <= level <= high:
            return row
    # Fallback (should never reach due to clamping)
    return INTELLIGENCE_TABLE[(1, 3)]


def lookup_autonomy(level: int) -> AutonomyRow:
    """Look up autonomy derivation by level (1-10)."""
    level = max(1, min(10, level))  # Clamp to bounds
    for (low, high), row in AUTONOMY_TABLE.items():
        if low <= level <= high:
            return row
    return AUTONOMY_TABLE[(1, 3)]


def lookup_resource(budget: float) -> ResourceRow:
    """Look up resource derivation by budget ($/turn)."""
    budget = max(0.0, budget)  # No negative budgets
    for (low, high), row in RESOURCE_TABLE.items():
        if low <= budget < high:
            return row
    return RESOURCE_TABLE[(2.00, float("inf"))]
