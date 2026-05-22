"""Schemas for tool execution use cases."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class ExecuteToolInput:
    """Input for tool execution."""

    tenant: str
    persona_id: str
    tool_name: str
    args: Dict[str, Any] = field(default_factory=dict)
    session_id: str = ""


@dataclass
class ExecuteToolOutput:
    """Output from tool execution."""

    status: str
    result: Dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0
    logs: List[str] = field(default_factory=list)
