"""Shared shape and helpers for assistant file tools — SOMA-ARCH-TOOLS-001 §4.1."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from services.common.path_guard import guard_for_env, PathGuard, PathGuardError

WORKROOT_ENV_VAR = "TOOL_WORK_DIR"


@dataclass(frozen=True)
class ToolContext:
    """Identity for one tool call. Server-side; never taken from model args."""

    tenant_id: str = ""
    capsule_id: str = ""
    session_id: str = ""
    user_id: str = ""
    approval_id: str = ""


def tool_error(message: str) -> Exception:
    """Build the executor failure type without a module-level import.

    ``services.tool_executor.tools`` registers this package's tools, so a
    module-level import of it here would close the import cycle.
    """
    from services.tool_executor.tools import ToolExecutionError

    return ToolExecutionError(message)


class SomaAssistantTool:
    """Base shape for assistant file tools (SOMA-ARCH-TOOLS-001 §4.1).

    Structurally matches ``services.tool_executor.tools.BaseTool``
    (``name`` / ``input_schema`` / ``async run``) without subclassing it, for
    the same acyclic-import reason as :func:`tool_error`.
    """

    name: str = ""
    description: str = ""
    tier: int = 1
    needs_workroot: bool = True
    needs_egress: bool = False
    durable: bool = False

    def input_schema(self) -> Dict[str, Any]:
        raise NotImplementedError

    async def run(
        self,
        args: Dict[str, Any],
        *,
        guard: Optional[PathGuard] = None,
        ctx: Optional[ToolContext] = None,
    ) -> Dict[str, Any]:
        raise NotImplementedError


def workroot_guard(guard: Optional[PathGuard]) -> PathGuard:
    """Return the caller's guard, or build one from the required workroot env.

    There is no default workroot: a missing ``TOOL_WORK_DIR`` fails closed.
    """
    if guard is not None:
        return guard
    try:
        return guard_for_env(WORKROOT_ENV_VAR)
    except PathGuardError as exc:
        raise tool_error(str(exc)) from exc


def resolve_guard(guard: PathGuard, path_arg: str) -> Path:
    """Resolve a model-supplied path through PathGuard, as a tool failure."""
    try:
        return guard.resolve(path_arg)
    except PathGuardError as exc:
        raise tool_error(str(exc)) from exc
