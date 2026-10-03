"""AgentIQ must not lie and must not conflate capability with style.

Two defects measured in the tree:

1. **Two vocabularies for one concept.** ``DerivedSettings.cost_tier`` emits
   ``budget|standard|premium|flagship``. ``LLMModelConfig.cost_tier`` accepts
   ``free|low|standard|premium``. ``prefer_cost_tier`` is passed to
   ``select_model`` and then silently matches nothing for ``budget`` and
   ``flagship``.

2. **Intelligence conflates capability with style.** Raising
   ``intelligence_level`` to get a better model also raises ``temperature``.
   A factual task wants a smart model at *low* temperature. Capability and
   response style are independent axes.
"""

from __future__ import annotations

from admin.core.agentiq.derivation import derive_from_knobs
from admin.core.agentiq.settings import DerivedSettings
from admin.llm.models import LLMModelConfig

_MODEL_TIERS = {c[0] for c in LLMModelConfig.COST_TIER_CHOICES}


def test_every_iq_cost_tier_resolves_to_a_real_model_cost_tier():
    """No IQ value may name a tier the model catalog cannot hold.

    The IQ capability tier (``model_tier``) is what reaches the router.
    """
    from admin.core.agentiq.routing import canonical_cost_tier

    for level in (1, 4, 7, 9):
        iq = derive_from_knobs(intelligence_level=level)
        mapped = canonical_cost_tier(iq.model_tier.value)
        assert mapped in _MODEL_TIERS, (
            f"model_tier {iq.model_tier!r} maps to {mapped!r}, "
            f"which LLMModelConfig does not accept"
        )


def test_canonical_cost_tier_is_total():
    """Every value the IQ table can emit must have exactly one mapping."""
    from admin.core.agentiq.routing import canonical_cost_tier

    for emitted in ("budget", "standard", "premium", "flagship"):
        mapped = canonical_cost_tier(emitted)
        assert mapped in _MODEL_TIERS


def test_temperature_is_not_a_function_of_intelligence():
    """Capability and style are independent axes.

    Two agents at different intelligence levels but the same response style
    must share a temperature; two styles at the same intelligence must not.
    """
    smart_precise = derive_from_knobs(intelligence_level=9, response_style="precise")
    dumb_precise = derive_from_knobs(intelligence_level=2, response_style="precise")
    smart_creative = derive_from_knobs(intelligence_level=9, response_style="creative")

    assert smart_precise.temperature == dumb_precise.temperature, (
        "temperature changed with intelligence - capability and style are conflated"
    )
    assert smart_precise.temperature != smart_creative.temperature
    # Capability still follows intelligence.
    assert smart_precise.model_tier != dumb_precise.model_tier


def test_derived_settings_documents_both_axes():
    """The model must carry both axes, not one fused field set."""
    fields = set(DerivedSettings.model_fields)
    assert "temperature" in fields
    assert "response_style" in fields or "model_tier" in fields
