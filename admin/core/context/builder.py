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
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from admin.core.agentiq import derive_all_settings
from admin.core.context.lanes import get_lane_allocation
from admin.core.context.models import BuiltContext

if TYPE_CHECKING:
    from admin.core.models import Capsule

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# tiktoken — accurate token counting for the memory lane
# ---------------------------------------------------------------------------
import tiktoken

_ENCODING = tiktoken.get_encoding("cl100k_base")


def _token_count(text: str) -> int:
    """Accurate LLM token count."""
    return len(_ENCODING.encode(text))


# --- Legacy DI surface (deprecated) -----------------------------------------
#
# The ONE memory interface is ``services.common.memory_contract.MemoryGateway``.
# Pass its hits as ``build(..., memory_hits=[...])``. ``brain_client`` exists only
# so older tests can inject SomaBrain. There is NO SFM client slot: the agent
# never talks to somafractalmemory (T-1). SomaBrain is the sole bridge.
#
# Do not type new code against these. Use MemoryGateway.
BrainClientProtocol = Any


class ContextBuilder:
    """
    5-Lane context builder for prompt assembly.

    Uses AgentIQ for token budgeting and lane allocation
    from capsule.body.learned preferences.

    Memory lane:
        Fed from ``MemoryGateway.recall()`` via ``build(..., memory_hits=[...])``
        — ONE read path through SomaBrain. Fail-closed: unavailable recall is
        a sentinel string, never a silent empty lie and never an SFM bypass.
    """

    def __init__(
        self,
        brain_client: Optional[BrainClientProtocol] = None,
    ) -> None:
        """
        Initialize ContextBuilder.

        Args:
            brain_client: DEPRECATED legacy DI slot. Prefer
                ``build(..., memory_hits=...)`` from ``MemoryGateway.recall()``.
        """
        self._brain_client = brain_client

    async def build(
        self,
        capsule: "Capsule",
        user_message: str,
        history: Optional[List[Dict[str, str]]] = None,
        budget_override: Optional[Dict[str, int]] = None,
        memory_hits: Optional[List[Any]] = None,
    ) -> BuiltContext:
        """
        Build context from capsule.body.

        Args:
            capsule: Capsule with body containing persona
            user_message: Current user message
            history: Optional conversation history
            budget_override: Optional explicit token budget per lane from SimpleGovernor
            memory_hits: Optional MemoryGateway.recall() hits (one read path —
                PLAN-TRIAD-SEAMLESS §1 rule 5). ``None`` falls back to the
                legacy brain/SFM clients; ``[]`` means recall ran and found
                nothing.

        Returns:
            BuiltContext with all 5 lanes assembled
        """
        from asgiref.sync import sync_to_async

        body: Dict[str, Any] = getattr(capsule, '_cached_body', None) or (await capsule.async_body() if hasattr(capsule, 'async_body') else capsule.body or {})
        persona = body.get("persona", {})

        # 1. Derive settings from AgentIQ (0ms)
        settings = await sync_to_async(derive_all_settings)(capsule)
        max_tokens = settings.max_tokens

        # 2. Get lane allocation from learned, defaults, or governor override
        if budget_override:
            # Normalize governor keys to context builder keys
            token_budget = {
                "system": budget_override.get("system_policy", budget_override.get("system", 4000)),
                "history": budget_override.get("history", 2000),
                "memory": budget_override.get("memory", 2000),
                "tools": budget_override.get("tools", 1000),
                "buffer": budget_override.get("buffer", 1000),
            }
        else:
            lanes = await get_lane_allocation(capsule)
            token_budget = lanes.allocate(max_tokens)

        # 3. Build system lane
        system = self._build_system_lane(persona, token_budget["system"])

        # 4. Build history lane
        history_str = self._build_history_lane(history or [], token_budget["history"])

        # 5. Build memory lane (async — gateway hits, else SomaBrain/SFM DI)
        memory_str = await self._build_memory_lane(
            capsule, user_message, persona, token_budget["memory"], memory_hits=memory_hits
        )

        # 6. Build tools lane
        tools_str = self._build_tools_lane(persona, token_budget["tools"])

        # 7. Build buffer lane
        buffer_str = user_message[: token_budget["buffer"] * 4]  # ~4 chars per token

        # Estimate total tokens
        total = sum(len(s) // 4 for s in [system, history_str, memory_str, tools_str, buffer_str])

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

    def _build_history_lane(self, history: List[Dict[str, str]], budget: int) -> str:
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
        memory_hits: Optional[List[Any]] = None,
    ) -> str:
        """Build memory lane.

        ``memory_hits`` (MemoryGateway.recall() results) is the one read path
        (PLAN-TRIAD-SEAMLESS §1 rule 5). SomaBrain is the only bridge (T-1);
        the agent never queries somafractalmemory directly.
        """
        if memory_hits is not None:
            return self._format_memory_hits(memory_hits, budget)

        memory_config = persona.get("memory", {})
        recall_limit = memory_config.get("recall_limit", 10)

        # SomaBrain is the sole memory bridge (T-1).
        if self._brain_client:
            try:
                memories = await self._brain_client.recall(
                    query=query,
                    top_k=recall_limit,
                    tenant=str(capsule.tenant_id) if capsule.tenant_id else None,
                    namespace="chat_history",
                )
                if memories:
                    return self._format_memories(memories, budget)
            except Exception as exc:
                logger.warning("SomaBrain recall failed: %s", exc)

        return "[Memory recall unavailable]"

    def _format_memories(self, memories: list[dict], budget: int) -> str:
        """Format memory list into context string."""
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

    def _format_memory_hits(self, hits: List[Any], budget: int) -> str:
        """Format MemoryGateway hits into the memory lane within the token budget.

        Fits as many hits as ``budget`` tokens (tiktoken cl100k) allow.
        """
        if not hits:
            return "[No relevant memories]"

        parts: List[str] = []
        used = 0

        for hit in hits:
            text = getattr(hit, "text", None)
            if text is None and isinstance(hit, dict):
                text = hit.get("text") or hit.get("content") or ""
            text = str(text or "").strip()
            if not text:
                continue

            line = f"- {text}"
            cost = _token_count(line)
            if used + cost > budget:
                if not parts:
                    # Even the first hit does not fit — truncate to budget.
                    truncated = _ENCODING.decode(_ENCODING.encode(line)[: max(1, budget)])
                    parts.append(truncated)
                break
            parts.append(line)
            used += cost

        return "\n".join(parts) if parts else "[No relevant memories]"

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
    budget_override: Optional[Dict[str, int]] = None,
    memory_hits: Optional[List[Any]] = None,
) -> BuiltContext:
    """
    Convenience function to build context.

    Args:
        capsule: Capsule with body
        user_message: User's message
        history: Conversation history
        brain_client: Optional SomaBrain client (legacy DI; prefer memory_hits)
        budget_override: Optional explicit token budget per lane (system, history, memory, tools, buffer)
        memory_hits: Optional MemoryGateway.recall() hits for the memory lane
            (one read path through SomaBrain, T-1).

    Returns:
        BuiltContext
    """
    builder = ContextBuilder(brain_client=brain_client)
    return await builder.build(capsule, user_message, history, budget_override, memory_hits=memory_hits)
