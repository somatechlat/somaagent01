"""file_list — directory listing inside the agent workroot (tier 1)."""

from __future__ import annotations

import asyncio
import fnmatch
from pathlib import Path
from typing import Any, Dict, Optional

from services.common.path_guard import PathGuard
from services.tool_executor.assistant_tools.base import (
    resolve_guard,
    SomaAssistantTool,
    tool_error,
    workroot_guard,
)

MAX_ENTRIES = 200


class FileListTool(SomaAssistantTool):
    """List names, types, and sizes of entries in a workroot directory.

    PathGuard-gated like every file tool; returns metadata only, never file
    content.
    """

    name = "file_list"
    description = (
        "List the entries of a directory inside the agent work directory: "
        "name, type (dir/file), and size in bytes. Returns metadata only, "
        "never file content."
    )
    tier = 1

    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Directory path relative to the agent work directory (default: work directory root).",
                },
                "glob": {
                    "type": "string",
                    "description": "Optional name pattern filter, e.g. '*.md' or 'notes_*'.",
                },
            },
            "additionalProperties": False,
        }

    async def run(
        self,
        args: Dict[str, Any],
        *,
        guard: Optional[PathGuard] = None,
        ctx: Optional[Any] = None,
    ) -> Dict[str, Any]:
        data = args or {}
        path_arg = str(data.get("path") or "").strip() or "."
        pattern = str(data.get("glob") or "").strip()
        g = workroot_guard(guard)
        target = resolve_guard(g, path_arg)
        return await asyncio.to_thread(self._list, g, target, pattern)

    def _list(self, g: PathGuard, target: Path, pattern: str) -> Dict[str, Any]:
        rel = g.relative_to_workroot(target)
        if not target.exists():
            raise tool_error(f"path not found: {rel}")
        if not target.is_dir():
            raise tool_error(f"not a directory: {rel}")

        entries = []
        truncated = False
        for child in sorted(target.iterdir(), key=lambda p: p.name):
            if pattern and not _matches(g, child, pattern):
                continue
            if len(entries) >= MAX_ENTRIES:
                truncated = True
                break
            if child.is_dir():
                kind, size = "dir", None
            elif child.is_file():
                kind, size = "file", child.stat().st_size
            else:
                kind, size = "other", None
            entries.append({"name": child.name, "type": kind, "size": size})

        return {
            "path": rel,
            "count": len(entries),
            "entries": entries,
            "truncated": truncated,
        }


def _matches(g: PathGuard, child: Path, pattern: str) -> bool:
    if "/" in pattern:
        try:
            return fnmatch.fnmatch(g.relative_to_workroot(child), pattern)
        except ValueError:
            return False
    return fnmatch.fnmatch(child.name, pattern)
