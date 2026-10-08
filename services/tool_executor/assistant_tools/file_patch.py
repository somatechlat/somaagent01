"""file_patch — exact old→new text replacement in the workroot (tier 2)."""

from __future__ import annotations

import asyncio
import hashlib
from pathlib import Path
from typing import Any, Dict, Optional

from services.common.path_guard import PathGuard
from services.tool_executor.assistant_tools.base import (
    resolve_guard,
    SomaAssistantTool,
    tool_error,
    workroot_guard,
)


class FilePatchTool(SomaAssistantTool):
    """Replace one exact text fragment in a workroot file; fails unless unique.

    Tier 2: approval-gated like file_write. The old fragment must occur
    exactly once — 0 or 2+ occurrences is a failed call, never a guess.
    """

    name = "file_patch"
    description = (
        "Replace one exact text fragment in a file in the agent work "
        "directory. Fails unless the old fragment occurs exactly once in the "
        "file. Returns path, replacement count, byte sizes, and SHA-256 hash "
        "of the patched content. Requires approval."
    )
    tier = 2

    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "File path relative to the agent work directory.",
                },
                "old": {
                    "type": "string",
                    "description": "Exact text to find; must occur exactly once in the file.",
                },
                "new": {
                    "type": "string",
                    "description": "Replacement text (may be empty to delete the fragment).",
                },
            },
            "required": ["path", "old", "new"],
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
        path_arg = str(data.get("path") or "").strip()
        if not path_arg:
            raise tool_error("path is required")
        old = data.get("old")
        if not isinstance(old, str) or not old:
            raise tool_error("old must be a non-empty string")
        new = data.get("new")
        if not isinstance(new, str):
            raise tool_error("new must be a string")

        g = workroot_guard(guard)
        target = resolve_guard(g, path_arg)
        return await asyncio.to_thread(self._patch, g, target, old, new)

    def _patch(
        self, g: PathGuard, target: Path, old: str, new: str
    ) -> Dict[str, Any]:
        rel = g.relative_to_workroot(target)
        if not target.exists():
            raise tool_error(f"path not found: {rel}")
        if not target.is_file():
            raise tool_error(f"not a file: {rel}")
        try:
            raw_bytes = target.read_bytes()
            raw = raw_bytes.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise tool_error(f"file is not UTF-8 text: {rel}") from exc

        occurrences = raw.count(old)
        if occurrences == 0:
            raise tool_error(f"old text not found in {rel}")
        if occurrences != 1:
            raise tool_error(
                f"old text occurs {occurrences} times in {rel}; must occur exactly once"
            )

        payload = raw.replace(old, new, 1).encode("utf-8")
        target.write_bytes(payload)
        return {
            "path": rel,
            "replacements": 1,
            "bytes_before": len(raw_bytes),
            "bytes": len(payload),
            "hash": hashlib.sha256(payload).hexdigest(),
        }
