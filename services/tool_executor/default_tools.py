"""Default base tools every Soma agent has — production cognitive kit.

Management model (normative):
- **All memory is managed through SomaBrain** (sole write lane to SFM).
  There is no local vector store, no fake memory, no second identity for a fact.
- Memory tools (recall / save / forget / proximity / get) are **always on**.
- Capsule capabilities only *add* tools; they cannot remove the base kit.

This module is the single list of default tools. Agent creation and
``ToolRegistry`` both read from here so every agent is born capable.
"""

from __future__ import annotations

from typing import Any, Dict, List

# Base tools every agent MUST have. Order is documentation-only.
DEFAULT_AGENT_TOOLS: List[str] = [
    # Core loop
    "response",  # end turn (if registered by tool_calling)
    "echo",
    "timestamp",
    # Cognition — SomaBrain-backed (T-1: one write lane)
    "memory_recall",
    "memory_save",
    "memory_forget",
    "memory_proximity",
    "memory_get",
    # Work
    "code_execute",
    "file_read",
    "http_fetch",
    "document_ingest",
    "canvas_append",
]

# Tools that MUST NEVER be disabled by capsule policy.
NON_DISABLEABLE_TOOLS = frozenset(
    {
        "memory_recall",
        "memory_save",
        "memory_forget",
        "memory_proximity",
        "memory_get",
        "response",
    }
)

# Human descriptions for LLM tool schemas (when handler has none).
DEFAULT_TOOL_DESCRIPTIONS: Dict[str, str] = {
    "memory_recall": "Search SomaBrain long-term memory for facts related to a query. Always use this before answering questions about past conversations, user preferences, or learned facts.",
    "memory_save": "Persist an important fact or episode to SomaBrain memory (works for all future turns). Use for user preferences, commitments, and discoveries.",
    "memory_forget": "Delete a memory by coordinate (privacy erasure).",
    "memory_proximity": "Find memories nearest to a query or coordinate (semantic proximity via SomaBrain scoring).",
    "memory_get": "Fetch one memory by exact coordinate.",
    "echo": "Echo back text (connectivity check).",
    "timestamp": "Return current UTC timestamp.",
    "code_execute": "Execute Python code in the sandbox and return stdout/result.",
    "file_read": "Read a text file from the work directory.",
    "http_fetch": "HTTP GET a URL and return body.",
    "document_ingest": "Ingest document bytes into memory/knowledge.",
    "canvas_append": "Append text to the session canvas.",
}


def is_default_tool(name: str) -> bool:
    return name in DEFAULT_AGENT_TOOLS


def is_non_disableable(name: str) -> bool:
    return name in NON_DISABLEABLE_TOOLS


def select_tools_for_mode(
    tools: List[Dict[str, Any]],
    *,
    tools_enabled: bool,
    tool_count_limit: int,
) -> List[Dict[str, Any]]:
    """Apply Governor degraded/normal policy to LLM tool schemas.

    Degraded mode (SimpleGovernor):
    - ``tools_enabled=False`` → optional tools are dropped
    - REQUIRED memory/response kit stays so the agent remains cognitive
    - result is capped at ``tool_count_limit`` (memory-first)

    Normal mode: all tools, capped at ``tool_count_limit`` (min 10).
    """
    required: List[Dict[str, Any]] = []
    optional: List[Dict[str, Any]] = []
    for t in tools:
        name = (t.get("function") or {}).get("name") if isinstance(t, dict) else None
        if not name:
            continue
        (required if is_non_disableable(name) else optional).append(t)

    if tools_enabled:
        selected = required + optional
        limit = max(tool_count_limit, 10)
    else:
        # Degraded: cognitive kit only (required), still bounded.
        selected = required
        limit = max(tool_count_limit, len(selected))

    return selected[:limit] if limit > 0 else selected


def default_tool_definitions() -> List[Dict[str, Any]]:
    """LLM function-calling schemas for the default kit."""
    from services.tool_executor.tools import AVAILABLE_TOOLS

    out: List[Dict[str, Any]] = []
    for name in DEFAULT_AGENT_TOOLS:
        handler = AVAILABLE_TOOLS.get(name)
        if handler is None:
            continue
        schema = handler.input_schema() if hasattr(handler, "input_schema") else None
        out.append(
            {
                "type": "function",
                "function": {
                    "name": name,
                    "description": DEFAULT_TOOL_DESCRIPTIONS.get(name) or name,
                    "parameters": schema
                    or {"type": "object", "properties": {}, "additionalProperties": True},
                },
            }
        )
    return out


def ensure_default_tools(registry: Any) -> None:
    """Register the default kit onto a ToolRegistry instance."""
    from services.tool_executor.memory_tools import (
        MemoryForgetTool,
        MemoryGetTool,
        MemoryProximityTool,
        MemoryRecallTool,
        MemorySaveTool,
    )
    from services.tool_executor.tools import AVAILABLE_TOOLS

    for tool in (
        MemoryRecallTool(),
        MemorySaveTool(),
        MemoryForgetTool(),
        MemoryProximityTool(),
        MemoryGetTool(),
    ):
        AVAILABLE_TOOLS[tool.name] = tool

    for name in DEFAULT_AGENT_TOOLS:
        handler = AVAILABLE_TOOLS.get(name)
        if handler is None:
            continue
        if hasattr(registry, "get") and registry.get(name) is not None:
            continue
        if hasattr(registry, "register"):
            registry.register(handler, description=DEFAULT_TOOL_DESCRIPTIONS.get(name) or name)
