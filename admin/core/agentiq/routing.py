"""Canonical routing vocabulary between AgentIQ and the model catalog.

AgentIQ derives a ``cost_tier`` from the resource budget. The model catalog
(``LLMModelConfig.cost_tier``) uses its own four values. Two vocabularies for
one concept meant ``prefer_cost_tier`` silently matched nothing for half the
values the IQ table can emit.

One concept, one canonical vocabulary. This module is the only place the two
meet; nothing else may translate between them.

Mapping is total and order-preserving:

    IQ            ->  LLMModelConfig
    budget        ->  free
    low           ->  low
    standard      ->  standard
    premium       ->  premium
    flagship      ->  premium
"""

from __future__ import annotations

from typing import Final

# The canonical, order-preserving collapse. `flagship` has no fifth tier in the
# model catalog, so it maps to the highest tier that exists rather than to a
# value the catalog would reject.
_IQ_TO_MODEL: Final[dict[str, str]] = {
    "budget": "free",
    "low": "low",
    "standard": "standard",
    "premium": "premium",
    "flagship": "premium",
}


def canonical_cost_tier(value: str) -> str:
    """Return the ``LLMModelConfig`` cost tier for an AgentIQ cost tier.

    Raises ``ValueError`` on an unknown value rather than passing it through:
    a tier the catalog cannot hold would silently select nothing.
    """
    key = (value or "").strip().lower()
    try:
        return _IQ_TO_MODEL[key]
    except KeyError:
        raise ValueError(
            f"unknown cost tier {value!r}; expected one of {sorted(_IQ_TO_MODEL)}"
        ) from None
