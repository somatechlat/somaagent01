"""Decision Engine for SomaAgent01.

Handles execution state, logic evaluation, and action selection.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict

from src.core.config import cfg

LOGGER = logging.getLogger(__name__)


@dataclass
class ActionDecision:
    """Result of the decision process."""

    action_type: str  # "GO", "NOGO", "DEFAULT"
    reason: str
    effective_urgency: float
    execution_state: Dict[str, float]


class DecisionEngine:
    """Manages execution logic and makes high-level decisions.

    Stateless; relies on SomaBrain for execution weights.
    """

    def decide(
        self, profile: Any, analysis: Dict[str, Any], weights: Dict[str, float]
    ) -> ActionDecision:
        """Determine GO (Action) vs NOGO (Deliberation) based on urgency and system state.

        Args:
            profile: The active agent profile.
            analysis: Analysis of the incoming message.
            weights: Current execution weights from SomaBrain.
        """
        settings = cfg.settings()
        print(f"DEBUG: settings.decision={getattr(settings, 'decision', 'MISSING')}")
        print(f"DEBUG: settings.external={getattr(settings, 'external', 'MISSING')}")

        # 1. Get base urgency from profile (default 0.5)
        base_urgency = profile.cognitive_params.get("urgency", settings.decision.base_urgency)

        # 2. Apply Execution Weights
        # 'dopamine' -> Action Bias (increases urgency)
        # 'serotonin' -> Stability Score (dampens extreme urgency)
        # Note: Keys are determined by the upstream SomaBrain API contract.

        action_bias = weights.get("dopamine", 0.5)
        stability_score = weights.get("serotonin", 0.5)

        # Simple linear model:
        # Effective Urgency = Base + (Action Bias) - (Stability Score)
        # We center bias effect around 0.5 (so 0.5 is neutral)
        bias_effect = (action_bias - 0.5) * settings.decision.action_bias_multiplier

        # Stability dampens urgency if it's high, or allows it if low
        stability_effect = (stability_score - 0.5) * settings.decision.stability_multiplier

        effective_urgency = base_urgency + bias_effect - stability_effect
        effective_urgency = max(0.0, min(1.0, effective_urgency))

        # 3. Logic Thresholds
        action_type = "DEFAULT"
        reason = "Moderate urgency"

        if effective_urgency >= settings.decision.threshold_go:
            action_type = "GO"
            reason = "High urgency (Action Mode)"
        elif effective_urgency <= settings.decision.threshold_nogo:
            action_type = "NOGO"
            reason = "Low urgency (Deliberation Mode)"

        return ActionDecision(
            action_type=action_type,
            reason=reason,
            effective_urgency=effective_urgency,
            execution_state={
                "action_bias": action_bias,
                "stability_score": stability_score,
                "base_urgency": base_urgency,
            },
        )
