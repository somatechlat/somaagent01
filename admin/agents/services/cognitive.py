"""Cognitive processing and neuromodulation for agent."""

from __future__ import annotations

from typing import Any, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from agent import Agent

from admin.core.helpers.print_style import PrintStyle


async def initialize_cognitive_state(agent: "Agent") -> None:
    """Initialize advanced cognitive state including neuromodulators and planning."""
    try:
        if "neuromodulators" not in agent.data:
            await agent.get_neuromodulators()
        if "current_plan" not in agent.data:
            agent.data["current_plan"] = None
        if "semantic_context" not in agent.data:
            agent.data["semantic_context"] = {
                "recent_entities": [],
                "interaction_patterns": [],
                "learning_clusters": [],
            }
        if "adaptation_state" not in agent.data:
            agent.data["adaptation_state"] = {}
        if agent.loop_data.iteration > 0 and agent.loop_data.iteration % 100 == 0:
            await consider_sleep_cycle(agent)
    except Exception as e:
        PrintStyle(font_color="orange", padding=False).print(
            f"Failed to initialize cognitive state: {e}"
        )


async def load_adaptation_state(agent: "Agent") -> None:
    """Load and apply adaptation state from SomaBrain for behavior adjustment."""
    try:
        if agent.loop_data.iteration % 25 == 0:
            adaptation_state = await agent.get_adaptation_state()
            if adaptation_state:
                agent.data["adaptation_state"] = adaptation_state
                learning_weights = adaptation_state.get("learning_weights", {})
                if learning_weights:
                    cognitive_params = agent.data.setdefault("cognitive_params", {})
                    exploration_weight = learning_weights.get("exploration", 0.5)
                    cognitive_params["exploration_factor"] = 0.3 + (exploration_weight * 0.7)
                    creativity_weight = learning_weights.get("creativity", 0.5)
                    cognitive_params["creativity_boost"] = creativity_weight > 0.6
                    patience_weight = learning_weights.get("patience", 0.5)
                    cognitive_params["patience_factor"] = 0.3 + (patience_weight * 0.7)
                recent_patterns = adaptation_state.get("recent_patterns", [])
                if recent_patterns:
                    agent.data["recent_learning_patterns"] = recent_patterns[-5:]
    except Exception as e:
        PrintStyle(font_color="orange", padding=False).print(
            f"Failed to load adaptation state: {e}"
        )


async def apply_neuromodulation(agent: "Agent") -> None:
    """Apply current neuromodulator state to cognitive processing."""
    try:
        neuromods = agent.data.get("neuromodulators", {})
        dopamine = neuromods.get("dopamine", 0.4)
        serotonin = neuromods.get("serotonin", 0.5)
        noradrenaline = neuromods.get("noradrenaline", 0.0)

        cognitive_params = agent.data.setdefault("cognitive_params", {})
        cognitive_params["exploration_factor"] = 0.5 + (dopamine * 0.5)
        cognitive_params["creativity_boost"] = dopamine > 0.6
        cognitive_params["patience_factor"] = 0.5 + (serotonin * 0.5)
        cognitive_params["empathy_boost"] = serotonin > 0.6
        cognitive_params["focus_factor"] = 0.5 + (noradrenaline * 0.5)
        cognitive_params["alertness_boost"] = noradrenaline > 0.3

        # Natural decay
        if dopamine > 0.4:
            neuromods["dopamine"] = max(0.4, dopamine - 0.05)
        if serotonin > 0.5:
            neuromods["serotonin"] = max(0.5, serotonin - 0.03)
        if noradrenaline > 0.0:
            neuromods["noradrenaline"] = max(0.0, noradrenaline - 0.02)
    except Exception as e:
        PrintStyle(font_color="orange", padding=False).print(
            f"Failed to apply neuromodulation: {e}"
        )


async def consider_sleep_cycle(agent: "Agent") -> None:
    """Consider initiating a sleep cycle for memory consolidation."""
    try:
        cognitive_load = agent.data.get("cognitive_load", 0.5)
        if cognitive_load > 0.8:
            PrintStyle(font_color="blue", padding=False).print(
                "High cognitive load detected, considering sleep cycle"
            )
            sleep_result = await agent.soma_client.sleep_cycle(
                tenant_id=agent.tenant_id,
                persona_id=agent.persona_id,
                nrem=True,
                rem=True,
            )
            if sleep_result:
                agent.data["last_sleep_cycle"] = sleep_result
                await optimize_cognitive_parameters(agent, sleep_result)
    except Exception as e:
        PrintStyle(font_color="orange", padding=False).print(
            f"Sleep cycle consideration failed: {e}"
        )


async def optimize_cognitive_parameters(agent: "Agent", sleep_result: Dict[str, Any]) -> None:
    """Optimize cognitive parameters after sleep cycle."""
    try:
        consolidation_score = sleep_result.get("consolidation_score", 0.5)
        pruning_score = sleep_result.get("pruning_score", 0.5)

        cognitive_params = agent.data.setdefault("cognitive_params", {})
        cognitive_params["memory_clarity"] = consolidation_score
        cognitive_params["cognitive_efficiency"] = pruning_score

        # Reset cognitive load after sleep
        agent.data["cognitive_load"] = max(0.3, agent.data.get("cognitive_load", 0.5) - 0.3)
    except Exception as e:
        PrintStyle(font_color="orange", padding=False).print(
            f"Failed to optimize cognitive parameters: {e}"
        )


def get_complexity_indicators() -> list[str]:
    """Get list of complexity indicators for planning detection."""
    return [
        "how to",
        "steps",
        "plan",
        "strategy",
        "approach",
        "implement",
        "build",
        "create",
        "develop",
        "design",
        "optimize",
        "improve",
        "enhance",
        "refactor",
        "debug",
        "solve",
        "analyze",
        "evaluate",
        "assess",
        "review",
    ]


def get_contextual_triggers() -> list[str]:
    """Get list of contextual triggers for planning."""
    return [
        "multi-step",
        "phase",
        "stage",
        "milestone",
        "deadline",
        "priority",
        "sequence",
        "workflow",
        "process",
    ]


def should_generate_plan(message: str) -> bool:
    """Determine if a plan should be generated for the given message."""
    message_lower = message.lower()
    indicators = get_complexity_indicators()
    triggers = get_contextual_triggers()

    indicator_count = sum(1 for ind in indicators if ind in message_lower)
    trigger_count = sum(1 for trig in triggers if trig in message_lower)

    return indicator_count >= 2 or trigger_count >= 1