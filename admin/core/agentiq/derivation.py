"""
derive_all_settings - Core derivation function.

This is the SINGLE entry point for deriving all agent settings
from the 3 knobs in capsule.body.persona.knobs.

Performance Engineer: Pure Python, 0ms latency, no external calls.
Security Auditor: Bounded inputs, no injection possible.
PhD Developer: Clean functional design.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict

from admin.core.agentiq.settings import DerivedSettings
from admin.core.agentiq.tables import (
    lookup_autonomy,
    lookup_intelligence,
    lookup_resource,
)

if TYPE_CHECKING:
    from admin.core.models import Capsule


def derive_all_settings(capsule: "Capsule") -> DerivedSettings:
    """
    Derive ALL settings from capsule.body.persona.knobs.

    This is PURE PYTHON with 0ms latency. No database calls,
    no external services. Just table lookups.

    Args:
        capsule: The Capsule model with body containing knobs

    Returns:
        DerivedSettings: Frozen Pydantic model with all derived values

    Raises:
        ValueError: If capsule.body is malformed
    """
    # Extract knobs from capsule.body
    body: Dict[str, Any] = capsule.body or {}
    persona = body.get("persona", {})
    knobs = persona.get("knobs", {})

    # Get the 3 control knobs with safe defaults
    intelligence_level: int = knobs.get("intelligence_level", 5)
    autonomy_level: int = knobs.get("autonomy_level", 5)
    resource_budget: float = knobs.get("resource_budget", 0.10)

    # Lookup derivations from tables
    intel = lookup_intelligence(intelligence_level)
    auto = lookup_autonomy(autonomy_level)
    resource = lookup_resource(resource_budget)

    # Build and return immutable settings
    return DerivedSettings(
        # From INTELLIGENCE
        temperature=intel.temperature,
        max_tokens=intel.max_tokens,
        rlm_iterations=intel.rlm_iterations,
        recall_limit=intel.recall_limit,
        model_tier=intel.model_tier,
        brain_query_enabled=intel.brain_query_enabled,
        # From AUTONOMY
        require_hitl=auto.require_hitl,
        tool_approval=auto.tool_approval,
        egress_allowed=auto.egress_allowed,
        # From RESOURCE
        token_limit=resource.token_limit,
        cost_tier=resource.cost_tier,
        thinking_budget=resource.thinking_budget,
    )


def derive_from_knobs(
    intelligence_level: int = 5,
    autonomy_level: int = 5,
    resource_budget: float = 0.10,
) -> DerivedSettings:
    """
    Derive settings from raw knob values (for testing).

    Args:
        intelligence_level: 1-10
        autonomy_level: 1-10
        resource_budget: $/turn

    Returns:
        DerivedSettings
    """
    intel = lookup_intelligence(intelligence_level)
    auto = lookup_autonomy(autonomy_level)
    resource = lookup_resource(resource_budget)

    return DerivedSettings(
        temperature=intel.temperature,
        max_tokens=intel.max_tokens,
        rlm_iterations=intel.rlm_iterations,
        recall_limit=intel.recall_limit,
        model_tier=intel.model_tier,
        brain_query_enabled=intel.brain_query_enabled,
        require_hitl=auto.require_hitl,
        tool_approval=auto.tool_approval,
        egress_allowed=auto.egress_allowed,
        token_limit=resource.token_limit,
        cost_tier=resource.cost_tier,
        thinking_budget=resource.thinking_budget,
    )
