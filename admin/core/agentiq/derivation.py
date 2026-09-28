"""
derive_all_settings - Core derivation function.

This is the SINGLE entry point for deriving all agent settings
from the 3 knobs in capsule.body.persona.knobs.

Performance Engineer: Pure Python, 0ms latency, no external calls.
Security Auditor: Bounded inputs, no injection possible.
PhD Developer: Clean functional design.
"""

from __future__ import annotations

from typing import Any, cast, Dict, Literal, TYPE_CHECKING

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
    # Extract knobs from capsule.body (use cached body if available)
    body: Dict[str, Any] = getattr(capsule, "_cached_body", None) or capsule.body or {}
    persona = body.get("persona", {})
    knobs = persona.get("knobs", {})

    # The 3 control knobs — Capsule / Django settings authority (no magic numbers).
    from admin.core.helpers.capsule_settings import resolve_setting

    intelligence_level: int = int(
        knobs.get("intelligence_level")
        if knobs.get("intelligence_level") is not None
        else resolve_setting("AGENTIQ_INTELLIGENCE_LEVEL", capsule=capsule, default=5)
    )
    autonomy_level: int = int(
        knobs.get("autonomy_level")
        if knobs.get("autonomy_level") is not None
        else resolve_setting("AGENTIQ_AUTONOMY_LEVEL", capsule=capsule, default=5)
    )
    resource_budget: float = float(
        knobs.get("resource_budget")
        if knobs.get("resource_budget") is not None
        else resolve_setting("AGENTIQ_RESOURCE_BUDGET", capsule=capsule, default=0.10)
    )

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
        cost_tier=cast(Literal["budget", "standard", "premium", "flagship"], resource.cost_tier),
        thinking_budget=resource.thinking_budget,
    )


def derive_from_knobs(
    intelligence_level: int | None = None,
    autonomy_level: int | None = None,
    resource_budget: float | None = None,
) -> DerivedSettings:
    """
    Derive settings from raw knob values.

    Knob defaults resolve through settings (Capsule -> AgentSetting -> Django
    -> schema default) so they are savable agent behaviour, not magic numbers.

    Args:
        intelligence_level: 1-10 (default from AGENTIQ_INTELLIGENCE_LEVEL)
        autonomy_level: 1-10 (default from AGENTIQ_AUTONOMY_LEVEL)
        resource_budget: $/turn (default from AGENTIQ_RESOURCE_BUDGET)

    Returns:
        DerivedSettings
    """
    from admin.core.helpers.capsule_settings import resolve_setting

    if intelligence_level is None:
        intelligence_level = int(resolve_setting("AGENTIQ_INTELLIGENCE_LEVEL", default=5))
    if autonomy_level is None:
        autonomy_level = int(resolve_setting("AGENTIQ_AUTONOMY_LEVEL", default=5))
    if resource_budget is None:
        resource_budget = float(resolve_setting("AGENTIQ_RESOURCE_BUDGET", default=0.10))

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
        cost_tier=cast(Literal["budget", "standard", "premium", "flagship"], resource.cost_tier),
        thinking_budget=resource.thinking_budget,
    )
