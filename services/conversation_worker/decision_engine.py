"""Decision Engine for SomaAgent01.

Handles cognitive state, neuromodulation, and action selection (Basal Ganglia).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

LOGGER = logging.getLogger(__name__)


@dataclass
class NeuroState:
    """Represents the current neuromodulatory state of the agent."""
    
    dopamine: float = 0.5  # 0.0 to 1.0; Reward/Action bias
    serotonin: float = 0.5  # 0.0 to 1.0; Mood/Stability bias
    norepinephrine: float = 0.5  # 0.0 to 1.0; Arousal/Attention (reserved for future)
    
    def update(self, dopamine_delta: float = 0.0, serotonin_delta: float = 0.0) -> None:
        """Update neurotransmitter levels with clamping."""
        self.dopamine = max(0.0, min(1.0, self.dopamine + dopamine_delta))
        self.serotonin = max(0.0, min(1.0, self.serotonin + serotonin_delta))


@dataclass
class ActionDecision:
    """Result of the decision process."""
    
    action_type: str  # "GO", "NOGO", "DEFAULT"
    reason: str
    effective_urgency: float
    neuro_state: Dict[str, float]


class DecisionEngine:
    """Manages cognitive state and makes high-level decisions."""

    def __init__(self) -> None:
        self.neuro_state = NeuroState()

    def decide(self, profile: Any, analysis: Dict[str, Any]) -> ActionDecision:
        """Determine GO (Action) vs NOGO (Deliberation) based on urgency and neuro-state.
        
        Refactors and enhances the original _basal_ganglia_filter logic.
        """
        # 1. Get base urgency from profile (default 0.5)
        base_urgency = profile.cognitive_params.get("urgency", 0.5)
        
        # 2. Apply Neuromodulation
        # Dopamine increases action bias (urgency)
        # Serotonin increases stability (dampens extreme urgency)
        
        # Simple linear model for Sprint 5:
        # Effective Urgency = Base + (Dopamine bias) - (Serotonin dampening)
        # We center dopamine effect around 0.5 (so 0.5 is neutral)
        dopamine_effect = (self.neuro_state.dopamine - 0.5) * 0.4  # +/- 0.2 range
        
        # Serotonin dampens urgency if it's high, or allows it if low
        # For now, let's just say high serotonin slightly reduces urgency (calmness)
        serotonin_effect = (self.neuro_state.serotonin - 0.5) * 0.2  # +/- 0.1 range
        
        effective_urgency = base_urgency + dopamine_effect - serotonin_effect
        effective_urgency = max(0.0, min(1.0, effective_urgency))
        
        # 3. Basal Ganglia Logic (Thresholds)
        action_type = "DEFAULT"
        reason = "Moderate urgency"
        
        if effective_urgency >= 0.8:
            action_type = "GO"
            reason = "High urgency (Action bias)"
        elif effective_urgency <= 0.3:
            action_type = "NOGO"
            reason = "Low urgency (Deliberation bias)"
            
        return ActionDecision(
            action_type=action_type,
            reason=reason,
            effective_urgency=effective_urgency,
            neuro_state={
                "dopamine": self.neuro_state.dopamine,
                "serotonin": self.neuro_state.serotonin,
                "base_urgency": base_urgency,
            }
        )

    def update_neurotransmitters(self, event_type: str, outcome: str) -> None:
        """Update neuro-state based on interaction outcomes.
        
        Args:
            event_type: Type of event (e.g., "message", "tool_use")
            outcome: "success", "failure", "neutral"
        """
        d_delta = 0.0
        s_delta = 0.0
        
        if outcome == "success":
            d_delta = 0.1  # Reward
            s_delta = 0.05 # Satisfaction
        elif outcome == "failure":
            d_delta = -0.1 # Disappointment
            s_delta = -0.05 # Instability
            
        self.neuro_state.update(d_delta, s_delta)
        LOGGER.info(
            "NeuroState updated",
            extra={
                "dopamine": self.neuro_state.dopamine,
                "serotonin": self.neuro_state.serotonin,
                "event": event_type,
                "outcome": outcome
            }
        )
