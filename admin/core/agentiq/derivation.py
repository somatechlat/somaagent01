"""
derive_all_settings - Core derivation function.

This is the SINGLE entry point for deriving all agent settings
from the 3 knobs in capsule.body.persona.knobs.

Performance Engineer: Pure Python, 0ms latency, no external calls.
Security Auditor: Bounded inputs, no injection possible.
PhD Developer: Clean functional design.
"""

from __future__ import annotations

from typing import Any, Dict, TYPE_CHECKING

from admin.core.agentiq.settings import DerivedSettings
from admin.core.agentiq.tables import (
    DEFAULT_AUTONOMY_LEVEL,
    DEFAULT_INTELLIGENCE_LEVEL,
    DEFAULT_RESOURCE_BUDGET,
    DEFAULT_RESPONSE_STYLE,
    lookup_autonomy,
    lookup_intelligence,
    lookup_resource,
    lookup_style,
)

if TYPE_CHECKING:
    from admin.core.models import Capsule


def resolve_knobs(capsule: "Capsule") -> Dict[str, Any]:
    """Effective control knobs for a capsule: stored, else chain-resolved.

    One place that decides what the knobs *are*. ``derive_all_settings`` and
    the AgentIQ HTTP surface both read through here, so a reported knob is
    exactly the knob that drove derivation — never a second guess.
    """
    from admin.core.helpers.capsule_settings import resolve_setting

    body: Dict[str, Any] = getattr(capsule, "_cached_body", None) or capsule.body or {}
    persona = body.get("persona", {})
    knobs = persona.get("knobs", {}) or {}

    def _one(name: str, resolved_default: Any) -> Any:
        if knobs.get(name) is not None:
            return knobs.get(name)
        return resolve_setting(
            f"AGENTIQ_{name.upper()}", capsule=capsule, default=resolved_default
        )

    return {
        "intelligence_level": _one("intelligence_level", DEFAULT_INTELLIGENCE_LEVEL),
        "autonomy_level": _one("autonomy_level", DEFAULT_AUTONOMY_LEVEL),
        "resource_budget": _one("resource_budget", DEFAULT_RESOURCE_BUDGET),
        "response_style": _one("response_style", DEFAULT_RESPONSE_STYLE),
    }


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
    knobs = resolve_knobs(capsule)
    intelligence_level: int = int(knobs["intelligence_level"])
    autonomy_level: int = int(knobs["autonomy_level"])
    resource_budget: float = float(knobs["resource_budget"])
    response_style: str = str(knobs["response_style"])

    # Lookup derivations from tables
    intel = lookup_intelligence(intelligence_level)
    auto = lookup_autonomy(autonomy_level)
    resource = lookup_resource(resource_budget)
    style = lookup_style(response_style)

    # Build and return immutable settings
    return DerivedSettings(
        # From RESPONSE STYLE (independent of how capable the model is)
        response_style=response_style.strip().lower(),
        temperature=style.temperature,
        max_tokens=style.max_tokens,
        # From INTELLIGENCE : capability
        recall_limit=intel.recall_limit,
        model_tier=intel.model_tier,
        brain_query_enabled=intel.brain_query_enabled,
        # From AUTONOMY
        require_hitl=auto.require_hitl,
        tool_approval=auto.tool_approval,
        egress_allowed=auto.egress_allowed,
        # From RESOURCE
        token_limit=resource.token_limit,
    )


def derive_from_knobs(
    intelligence_level: int | None = None,
    autonomy_level: int | None = None,
    resource_budget: float | None = None,
    response_style: str | None = None,
) -> DerivedSettings:
    """
    Derive settings from raw knob values.

    Knob defaults resolve through settings (Capsule -> AgentSetting -> Django
    -> schema default) so they are savable agent behaviour, not magic numbers.

    Args:
        intelligence_level: 1-10 (default from AGENTIQ_INTELLIGENCE_LEVEL)
        autonomy_level: 1-10 (default from AGENTIQ_AUTONOMY_LEVEL)
        resource_budget: per-turn spend (AGENTIQ_RESOURCE_BUDGET)

    Returns:
        DerivedSettings
    """
    from admin.core.helpers.capsule_settings import resolve_setting

    if intelligence_level is None:
        intelligence_level = int(
            resolve_setting("AGENTIQ_INTELLIGENCE_LEVEL", default=DEFAULT_INTELLIGENCE_LEVEL)
        )
    if autonomy_level is None:
        autonomy_level = int(
            resolve_setting("AGENTIQ_AUTONOMY_LEVEL", default=DEFAULT_AUTONOMY_LEVEL)
        )
    if resource_budget is None:
        resource_budget = float(
            resolve_setting("AGENTIQ_RESOURCE_BUDGET", default=DEFAULT_RESOURCE_BUDGET)
        )

    if response_style is None:
        response_style = str(
            resolve_setting("AGENTIQ_RESPONSE_STYLE", default=DEFAULT_RESPONSE_STYLE)
        )

    intel = lookup_intelligence(intelligence_level)
    auto = lookup_autonomy(autonomy_level)
    resource = lookup_resource(resource_budget)
    style = lookup_style(response_style)

    return DerivedSettings(
        response_style=response_style.strip().lower(),
        temperature=style.temperature,
        max_tokens=style.max_tokens,
        recall_limit=intel.recall_limit,
        model_tier=intel.model_tier,
        brain_query_enabled=intel.brain_query_enabled,
        require_hitl=auto.require_hitl,
        tool_approval=auto.tool_approval,
        egress_allowed=auto.egress_allowed,
        token_limit=resource.token_limit,
    )
