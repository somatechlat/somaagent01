"""SomaBrain integration for agent memory and cognitive operations."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from agent import Agent

from admin.core.helpers.print_style import PrintStyle
from admin.core.somabrain_client import SomaClientError

# Neuromodulator clamping ranges (from SomaBrain neuromod.py)
# These are the physiological ranges enforced by SomaBrain
NEUROMOD_CLAMP_RANGES: Dict[str, tuple[float, float]] = {
    "dopamine": (0.0, 0.8),
    "serotonin": (0.0, 1.0),
    "noradrenaline": (0.0, 0.1),
    "acetylcholine": (0.0, 0.5),
}


def clamp_neuromodulator(name: str, value: float) -> float:
    """Clamp neuromodulator value to physiological range.

    Args:
        name: Neuromodulator name (dopamine, serotonin, noradrenaline, acetylcholine)
        value: Raw value to clamp

    Returns:
        Clamped value within physiological range
    """
    min_val, max_val = NEUROMOD_CLAMP_RANGES.get(name, (0.0, 1.0))
    return max(min_val, min(max_val, value))


async def store_memory(
    agent: "Agent",
    content: Dict[str, Any],
    memory_type: str = "interaction",
) -> Optional[str]:
    """Store memory in SomaBrain with proper metadata."""
    try:
        memory_payload = {
            "value": {
                "content": content,
                "type": memory_type,
                "agent_number": agent.number,
                "persona_id": agent.persona_id,
                "session_id": agent.session_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            "tenant": agent.tenant_id,
            "namespace": "wm",
            "key": f"{memory_type}_{agent.session_id}_{datetime.now(timezone.utc).timestamp()}",
            "tags": [memory_type, f"agent_{agent.number}"],
            "importance": 0.8,
            "novelty": 0.7,
            "trace_id": agent.session_id,
        }
        result = await agent.soma_client.remember(memory_payload)
        coordinate = result.get("coordinate")
        if coordinate:
            PrintStyle(font_color="cyan", padding=False).print(
                f"Stored {memory_type} memory: {str(coordinate)[:20]}..."
            )
            return str(coordinate)
    except SomaClientError as e:
        PrintStyle(font_color="red", padding=False).print(f"Failed to store memory: {e}")
    return None


async def recall_memories(
    agent: "Agent",
    query: str,
    top_k: int = 5,
    memory_type: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Recall memories from SomaBrain based on query."""
    try:
        result = await agent.soma_client.recall(
            query=query,
            top_k=top_k,
            tenant=agent.tenant_id,
            namespace="wm",
            tags=[memory_type] if memory_type else None,
        )
        memories = result.get("results", [])
        if memories:
            PrintStyle(font_color="cyan", padding=False).print(f"Recalled {len(memories)} memories")
        return memories
    except SomaClientError as e:
        PrintStyle(font_color="red", padding=False).print(f"Failed to recall memories: {e}")
        return []


async def get_adaptation_state(agent: "Agent") -> Optional[Dict[str, Any]]:
    """Get current adaptation state from SomaBrain.

    Uses GET /context/adaptation/state endpoint which returns retrieval weights,
    utility weights, history length, and learning rate.
    """
    try:
        result = await agent.soma_client.get_adaptation_state(
            tenant_id=agent.tenant_id,
            persona_id=agent.persona_id,  # Accepted for compatibility, not used by SomaBrain
        )
        if result:
            agent.data["adaptation_state"] = result
            return result
    except SomaClientError as e:
        PrintStyle(font_color="orange", padding=False).print(f"Failed to get adaptation state: {e}")
    return None


async def get_neuromodulators(agent: "Agent") -> Optional[Dict[str, float]]:
    """Get current neuromodulator state from SomaBrain."""
    try:
        result = await agent.soma_client.get_neuromodulators(
            tenant_id=agent.tenant_id,
            persona_id=agent.persona_id,
        )
        if result:
            agent.data["neuromodulators"] = result
            return result
    except SomaClientError as e:
        PrintStyle(font_color="orange", padding=False).print(f"Failed to get neuromodulators: {e}")
    return None


async def update_neuromodulators(
    agent: "Agent",
    dopamine_delta: float = 0.0,
    serotonin_delta: float = 0.0,
    noradrenaline_delta: float = 0.0,
    acetylcholine_delta: float = 0.0,
) -> bool:
    """Update neuromodulator levels in SomaBrain with proper clamping.

    Args:
        agent: The agent instance
        dopamine_delta: Change in dopamine level
        serotonin_delta: Change in serotonin level
        noradrenaline_delta: Change in noradrenaline level
        acetylcholine_delta: Change in acetylcholine level

    Returns:
        True if update succeeded, False otherwise
    """
    try:
        current = agent.data.get("neuromodulators", {})
        # Apply deltas and clamp to physiological ranges
        new_levels = {
            "dopamine": clamp_neuromodulator(
                "dopamine", current.get("dopamine", 0.4) + dopamine_delta
            ),
            "serotonin": clamp_neuromodulator(
                "serotonin", current.get("serotonin", 0.5) + serotonin_delta
            ),
            "noradrenaline": clamp_neuromodulator(
                "noradrenaline", current.get("noradrenaline", 0.0) + noradrenaline_delta
            ),
            "acetylcholine": clamp_neuromodulator(
                "acetylcholine", current.get("acetylcholine", 0.0) + acetylcholine_delta
            ),
        }
        result = await agent.soma_client.update_neuromodulators(
            tenant_id=agent.tenant_id,
            persona_id=agent.persona_id,
            neuromodulators=new_levels,
        )
        if result:
            agent.data["neuromodulators"] = new_levels
            return True
    except SomaClientError as e:
        PrintStyle(font_color="orange", padding=False).print(
            f"Failed to update neuromodulators: {e}"
        )
    return False


async def initialize_persona(agent: "Agent") -> bool:
    """Initialize persona in SomaBrain if not exists.

    Checks if persona exists via get_persona, creates via put_persona if not.
    """
    try:
        try:
            existing = await agent.soma_client.get_persona(agent.persona_id)
            if existing:
                return True
        except SomaClientError:
            pass  # Persona doesn't exist, create it

        persona_data = {
            "id": agent.persona_id,
            "tenant_id": agent.tenant_id,
            "display_name": f"Agent {agent.number}",
            "properties": {
                "agent_number": agent.number,
                "profile": agent.config.profile,
            },
        }
        await agent.soma_client.put_persona(agent.persona_id, persona_data)
        return True
    except SomaClientError as e:
        PrintStyle(font_color="orange", padding=False).print(f"Failed to initialize persona: {e}")
        return False


async def track_interaction(
    agent: "Agent",
    interaction_type: str,
    content: Dict[str, Any],
    success: bool = True,
) -> None:
    """Track an interaction for learning and adaptation."""
    try:
        tracking_payload = {
            "interaction_type": interaction_type,
            "content": content,
            "success": success,
            "agent_number": agent.number,
            "session_id": agent.session_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        await store_memory(agent, tracking_payload, "interaction_tracking")
    except Exception as e:
        PrintStyle(font_color="orange", padding=False).print(f"Failed to track interaction: {e}")


# ------------------------------------------------------------------
# New wrapper functions per SomaBrain integration spec
# ------------------------------------------------------------------


async def reset_adaptation_state(
    agent: "Agent",
    base_lr: Optional[float] = None,
    reset_history: bool = True,
) -> bool:
    """Reset adaptation state to defaults for clean benchmarks.

    Args:
        agent: The agent instance
        base_lr: Optional base learning rate override
        reset_history: Whether to clear feedback history

    Returns:
        True if reset succeeded, False otherwise
    """
    try:
        result = await agent.soma_client.adaptation_reset(
            tenant_id=agent.tenant_id,
            base_lr=base_lr,
            reset_history=reset_history,
        )
        if result and result.get("ok"):
            # Clear local adaptation state cache
            agent.data["adaptation_state"] = {}
            PrintStyle(font_color="cyan", padding=False).print(
                "Adaptation state reset successfully"
            )
            return True
    except SomaClientError as e:
        PrintStyle(font_color="orange", padding=False).print(
            f"Failed to reset adaptation state: {e}"
        )
    return False


async def execute_action(
    agent: "Agent",
    task: str,
    *,
    universe: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Execute a cognitive action through SomaBrain.

    Args:
        agent: The agent instance
        task: The task/action description
        universe: Optional universe scope

    Returns:
        ActResponse dict or None on failure
    """
    try:
        result = await agent.soma_client.act(
            task=task,
            universe=universe,
            session_id=agent.session_id,
        )
        if result:
            PrintStyle(font_color="cyan", padding=False).print(
                f"Action executed: salience={result.get('results', [{}])[0].get('salience', 'N/A')}"
            )
            return dict(result)
    except SomaClientError as e:
        PrintStyle(font_color="orange", padding=False).print(f"Failed to execute action: {e}")
    return None


async def transition_sleep_state(
    agent: "Agent",
    target_state: str,
    *,
    ttl_seconds: Optional[int] = None,
) -> bool:
    """Transition agent to specified sleep state.

    Args:
        agent: The agent instance
        target_state: One of "active", "light", "deep", "freeze"
        ttl_seconds: Optional TTL for auto-revert

    Returns:
        True if transition succeeded, False otherwise
    """
    try:
        result = await agent.soma_client.brain_sleep_mode(
            target_state=target_state,
            ttl_seconds=ttl_seconds,
            trace_id=agent.session_id,
        )
        if result:
            PrintStyle(font_color="cyan", padding=False).print(
                f"Sleep state transitioned to: {target_state}"
            )
            return True
    except ValueError as e:
        PrintStyle(font_color="red", padding=False).print(f"Invalid sleep state: {e}")
    except SomaClientError as e:
        PrintStyle(font_color="orange", padding=False).print(
            f"Failed to transition sleep state: {e}"
        )
    return False


async def get_sleep_status(agent: "Agent") -> Optional[Dict[str, Any]]:
    """Get current sleep status from SomaBrain.

    Args:
        agent: The agent instance

    Returns:
        SleepStatusResponse dict or None on failure
    """
    try:
        result = await agent.soma_client.sleep_status()
        if result:
            return dict(result)
    except SomaClientError as e:
        PrintStyle(font_color="orange", padding=False).print(f"Failed to get sleep status: {e}")
    return None


async def get_micro_diagnostics(agent: "Agent") -> Optional[Dict[str, Any]]:
    """Get microcircuit diagnostics from SomaBrain (admin mode).

    Args:
        agent: The agent instance

    Returns:
        Diagnostic info dict or None on failure
    """
    try:
        result = await agent.soma_client.micro_diag()
        if result:
            return dict(result)
    except SomaClientError as e:
        PrintStyle(font_color="orange", padding=False).print(
            f"Failed to get micro diagnostics: {e}"
        )
    return None