"""SomaBrain integration for agent memory and cognitive operations."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from agent import Agent

from python.helpers.print_style import PrintStyle
from python.integrations.soma_client import SomaClientError


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
) -> bool:
    """Update neuromodulator levels in SomaBrain."""
    try:
        current = agent.data.get("neuromodulators", {})
        new_levels = {
            "dopamine": max(0.0, min(1.0, current.get("dopamine", 0.4) + dopamine_delta)),
            "serotonin": max(0.0, min(1.0, current.get("serotonin", 0.5) + serotonin_delta)),
            "noradrenaline": max(
                0.0, min(1.0, current.get("noradrenaline", 0.0) + noradrenaline_delta)
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
        # Try to get existing persona first
        try:
            existing = await agent.soma_client.get_persona(agent.persona_id)
            if existing:
                return True
        except SomaClientError:
            pass  # Persona doesn't exist, create it

        # Create new persona
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
