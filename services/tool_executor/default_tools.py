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

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# Base tools every agent MUST have. Order is documentation-only.
DEFAULT_AGENT_TOOLS: List[str] = [
    # Core loop
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
    # Assistant file tools (SOMA-ARCH-TOOLS-001). Appended last so an
    # existing tool_count_limit keeps cutting them before the kit above.
    "file_list",
    "file_search",
    "file_write",
    "file_patch",
    # Durable assistant jobs (SOMA-ARCH-TOOLS-001 §5/§6, W3.3). research_report
    # starts a Temporal workflow; job_status reports a workflow id.
    "research_report",
    "job_status",
]

# Tools that MUST NEVER be disabled by capsule policy.
NON_DISABLEABLE_TOOLS = frozenset(
    {
        "memory_recall",
        "memory_save",
        "memory_forget",
        "memory_proximity",
        "memory_get",
    }
)

# Human descriptions for LLM tool schemas (when handler has none).
DEFAULT_TOOL_DESCRIPTIONS: Dict[str, str] = {
    "memory_recall": "Search SomaBrain long-term memory. Use it only when the memory already given to you is not enough to answer. If the answer is already in that memory, answer directly - do not call this.",
    "memory_save": "Persist an important fact or episode to SomaBrain memory (works for all future turns). Use for user preferences, commitments, and discoveries.",
    "memory_forget": "Delete a memory by coordinate (privacy erasure).",
    "memory_proximity": "Find memories nearest to a query or coordinate (semantic proximity via SomaBrain scoring).",
    "memory_get": "Fetch one memory by exact coordinate.",
    "timestamp": "Return current UTC timestamp.",
    "code_execute": "Execute Python code in the sandbox and return stdout/result.",
    "file_read": "Read a text file from the work directory.",
    "http_fetch": "HTTP GET a URL and return body.",
    "document_ingest": "Ingest document bytes into memory/knowledge.",
    "canvas_append": "Append text to the session canvas.",
    "file_list": "List entries of a directory in the work directory (name, type, size) — metadata only, no file content.",
    "file_search": "Search files in the work directory for literal text; returns matching lines with path and line number, truncated.",
    "file_write": "Create or overwrite a UTF-8 text file in the work directory; returns path, byte count, and SHA-256 hash. Approval-gated.",
    "file_patch": "Replace one exact text fragment in a work-directory file; fails unless it occurs exactly once. Approval-gated.",
    "research_report": "Start a durable research-report job on Temporal for a topic; returns the workflow id immediately (approval-gated). Poll with job_status.",
    "job_status": "Report the status of a durable job by workflow id: Temporal execution status plus the workflow's progress query.",
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

    if limit <= 0:
        return selected

    kept = selected[:limit]
    dropped = [s for s in selected if s not in kept]
    if dropped:
        # A tool that silently vanishes from the model's kit is a behaviour
        # change nobody can see. Log it with the names.
        names = [(d.get("function") or {}).get("name") for d in dropped]
        logger.warning(
            "tool_count_limit=%d dropped %d tool(s) from the model kit: %s",
            limit,
            len(dropped),
            names,
        )
    return kept


def _register_durable_tools() -> None:
    """Put the durable-job tools (research_report, job_status) in AVAILABLE_TOOLS.

    W3.3: they live in ``assistant_tools`` but are registered here (not in
    ``tools.py``) so the registration shares one list with the kit they join.
    """
    from services.tool_executor.assistant_tools.research_report import (
        JobStatusTool,
        ResearchReportTool,
    )
    from services.tool_executor.tools import AVAILABLE_TOOLS

    AVAILABLE_TOOLS.setdefault(ResearchReportTool.name, ResearchReportTool())
    AVAILABLE_TOOLS.setdefault(JobStatusTool.name, JobStatusTool())


def default_tool_definitions() -> List[Dict[str, Any]]:
    """LLM function-calling schemas for the default kit."""
    _register_durable_tools()
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

    _register_durable_tools()

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
