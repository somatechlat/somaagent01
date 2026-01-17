"""
ContextBuilder - Main context assembly engine.

Builds prompts from capsule.body.persona with:
- System prompt from persona.core
- Injection prompts from persona.prompts
- Memory recall from SomaBrain
- Tool descriptions from persona.tools
- Token budgeting via AgentIQ

PhD Developer: Clean async architecture.
Security: No sensitive data leaks.
Performance: 0ms for non-brain operations.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Protocol

from admin.core.agentiq import derive_all_settings
from admin.core.context.lanes import get_lane_allocation
from admin.core.context.models import BuiltContext

if TYPE_CHECKING:
    from admin.core.models import Capsule

logger = logging.getLogger(__name__)


class BrainClientProtocol(Protocol):
    """Protocol for SomaBrain client (dependency injection)."""

    async def recall(
        self,
        query: str,
        capsule_id: str,
        limit: int,
        threshold: float,
    ) -> List[Dict[str, Any]]:
        """Recall memories from brain."""
        ...


class ContextBuilder:
    """
    5-Lane context builder for prompt assembly.

    Uses AgentIQ for token budgeting and lane allocation
    from capsule.body.learned preferences.
    """

    def __init__(self, brain_client: Optional[BrainClientProtocol] = None) -> None:
        """
        Initialize ContextBuilder.

        Args:
            brain_client: Optional SomaBrain client for memory recall
        """
        self._brain_client = brain_client

    async def build(
        self,
        capsule: "Capsule",
        user_message: str,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> BuiltContext:
        """
        Build context from capsule.body.

        Args:
            capsule: Capsule with body containing persona
            user_message: Current user message
            history: Optional conversation history

        Returns:
            BuiltContext with all 5 lanes assembled
        """
        body: Dict[str, Any] = capsule.body or {}
        persona = body.get("persona", {})

        # 1. Derive settings from AgentIQ (0ms)
        settings = derive_all_settings(capsule)
        max_tokens = settings.max_tokens

        # 2. Get lane allocation from learned or defaults
        lanes = get_lane_allocation(capsule)
        token_budget = lanes.allocate(max_tokens)

        # 3. Build system lane
        system = self._build_system_lane(persona, token_budget["system"])

        # 4. Build history lane
        history_str = self._build_history_lane(history or [], token_budget["history"])

        # 5. Build memory lane (async - calls SomaBrain)
        memory_str = await self._build_memory_lane(
            capsule, user_message, persona, token_budget["memory"]
        )

        # 6. Build tools lane
        tools_str = self._build_tools_lane(persona, token_budget["tools"])

        # 7. Build buffer lane
        buffer_str = user_message[: token_budget["buffer"] * 4]  # ~4 chars per token

        # Estimate total tokens
        total = sum(
            len(s) // 4
            for s in [system, history_str, memory_str, tools_str, buffer_str]
        )

        return BuiltContext(
            system=system,
            history=history_str,
            memory=memory_str,
            tools=tools_str,
            buffer=buffer_str,
            total_tokens=total,
        )

    def _build_system_lane(self, persona: Dict[str, Any], budget: int) -> str:
        """Build system prompt from persona.core."""
        core = persona.get("core", {})
        system = core.get("system_prompt", "You are a helpful assistant.")

        # Add injection prompts
        prompts = persona.get("prompts", {})
        injections = prompts.get("injection_prompts", [])
        for injection in injections:
            if injection.get("trigger") == "start":
                system += "\n" + injection.get("content", "")

        # Truncate to budget
        return system[: budget * 4]

    def _build_history_lane(
        self, history: List[Dict[str, str]], budget: int
    ) -> str:
        """Format conversation history."""
        if not history:
            return ""

        parts = []
        char_limit = budget * 4
        current_chars = 0

        # Recent messages first (reverse to get newest)
        for msg in reversed(history[-20:]):  # Last 20 messages max
            role = msg.get("role", "user")
            content = msg.get("content", "")
            formatted = f"{role}: {content}"

            if current_chars + len(formatted) > char_limit:
                break

            parts.insert(0, formatted)
            current_chars += len(formatted)

        return "\n".join(parts)

    async def _build_memory_lane(
        self,
        capsule: "Capsule",
        query: str,
        persona: Dict[str, Any],
        budget: int,
    ) -> str:
        """Build memory lane via SomaBrain recall."""
        if not self._brain_client:
            return "[No memory client configured]"

        memory_config = persona.get("memory", {})
        recall_limit = memory_config.get("recall_limit", 10)
        threshold = memory_config.get("similarity_threshold", 0.7)

        try:
            memories = await self._brain_client.recall(
                query=query,
                capsule_id=str(capsule.id),
                limit=recall_limit,
                threshold=threshold,
            )

            # Format memories
            parts = []
            char_limit = budget * 4
            current_chars = 0

            for mem in memories:
                content = mem.get("content", str(mem))
                if current_chars + len(content) > char_limit:
                    break
                parts.append(f"- {content}")
                current_chars += len(content)

            return "\n".join(parts) if parts else "[No relevant memories]"

        except Exception as exc:
            logger.warning("Memory recall failed: %s", exc)
            return "[Memory recall unavailable]"

    def _build_tools_lane(self, persona: Dict[str, Any], budget: int) -> str:
        """Build tools description lane."""
        tools_config = persona.get("tools", {})
        enabled = tools_config.get("enabled_capabilities", [])
        tool_prompts = persona.get("prompts", {}).get("tool_prompts", {})

        if not enabled:
            return "[No tools enabled]"

        parts = []
        char_limit = budget * 4
        current_chars = 0

        for tool_name in enabled:
            description = tool_prompts.get(tool_name, f"Tool: {tool_name}")
            formatted = f"- {tool_name}: {description}"

            if current_chars + len(formatted) > char_limit:
                break

            parts.append(formatted)
            current_chars += len(formatted)

        return "\n".join(parts)


async def build_context(
    capsule: "Capsule",
    user_message: str,
    history: Optional[List[Dict[str, str]]] = None,
    brain_client: Optional[BrainClientProtocol] = None,
) -> BuiltContext:
    """
    Convenience function to build context.

    Args:
        capsule: Capsule with body
        user_message: User's message
        history: Conversation history
        brain_client: Optional brain client

    Returns:
        BuiltContext
    """
    builder = ContextBuilder(brain_client=brain_client)
    return await builder.build(capsule, user_message, history)
