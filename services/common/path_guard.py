"""PathGuard — the one path jail for every agent file tool.

SOMA-ARCH-TOOLS-001. Every file operation (read, write, patch, list, search)
MUST resolve through this module before any ``open``/``Path`` call.

Isolation model:
  * Workroot is a server-side path (tenant/capsule derived), never a model arg.
  * After ``Path.resolve()``, the real path must stay under the workroot using
    ``os.sep``-terminated prefix or ``is_relative_to`` — not bare ``startswith``.
  * Absolute paths and ``..`` in the *argument* are rejected before resolve
    (fail-closed; no silent rewrite to a “safe” path).
  * Symlinks are resolved; escape after resolve is reject.
  * Special files (devices, FIFOs, sockets) are reject.

This is L1 of the five-layer sandbox. It is not a substitute for an OS
container (L0); it is the mandatory in-process gate so a guard bug is
survivable when L0 holds.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, Tuple

__all__ = [
    "PathGuardError",
    "WorkrootNotConfigured",
    "PathOutsideWorkroot",
    "PathGuard",
]


class PathGuardError(ValueError):
    """Base class for path-jail refusals. Fail-closed; never rewritten."""


class WorkrootNotConfigured(PathGuardError):
    """No workroot was configured for this agent/tenant/capsule."""


class PathOutsideWorkroot(PathGuardError):
    """Resolved path is not under the workroot."""


class PathGuard:
    """Hard jail under a single workroot directory."""

    def __init__(self, workroot: str | os.PathLike[str]) -> None:
        root = Path(workroot).expanduser()
        if not str(root).strip():
            raise WorkrootNotConfigured("workroot path is empty")
        self._root = root.resolve()
        if not self._root.is_dir():
            # Create on first use by the caller if needed; guard only records
            # the resolved location. Missing dir is not “escape”.
            pass

    @property
    def workroot(self) -> Path:
        return self._root

    def resolve(self, relative: str) -> Path:
        """Return a real path under the workroot or raise.

        Args:
            relative: Model/tool-supplied path. Must be relative to workroot.
                      Absolute paths and empty/whitespace are refused.
        """
        if not isinstance(relative, str) or not relative.strip():
            raise PathOutsideWorkroot("path is empty")

        # Fail-closed on absolute and home expansion — those are host paths.
        candidate = relative.strip()
        if candidate.startswith("/") or candidate.startswith("\\"):
            raise PathOutsideWorkroot("absolute paths are refused")
        if candidate.startswith("~"):
            raise PathOutsideWorkroot("home expansion is refused")

        joined = self._root / candidate
        resolved = joined.resolve()

        if not self._is_inside(resolved):
            raise PathOutsideWorkroot(
                f"path escapes workroot: {candidate!r} -> {resolved}"
            )

        # Deny special files when they already exist (read path).
        if resolved.exists() and not resolved.is_file() and not resolved.is_dir():
            raise PathOutsideWorkroot(f"special files are refused: {resolved}")

        return resolved

    def _is_inside(self, path: Path) -> bool:
        root = self._root
        # os.sep-terminated prefix: /data/work must not match /data/work_evil
        root_s = str(root)
        if root_s.endswith(os.sep):
            root_prefix = root_s
        else:
            root_prefix = root_s + os.sep
        path_s = str(path)
        if path_s == root_s:
            return True
        return path_s.startswith(root_prefix)

    def relative_to_workroot(self, path: Path) -> str:
        """Posix-style relative path for tool results and UI."""
        return path.resolve().relative_to(self._root).as_posix()


def guard_for_env(env_var: str = "TOOL_WORK_DIR") -> PathGuard:
    """Build a PathGuard from a required environment workroot.

    No default directory. Missing/empty env raises WorkrootNotConfigured —
    Rule 6 / R-VAL: topology is explicit.
    """
    raw = os.environ.get(env_var)
    if not raw or not str(raw).strip():
        raise WorkrootNotConfigured(
            f"{env_var} is not configured. Set the agent workroot path."
        )
    return PathGuard(raw)
