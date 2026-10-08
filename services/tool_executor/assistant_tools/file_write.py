"""file_write — create/overwrite a text file in the workroot (tier 2, approval)."""

from __future__ import annotations

import asyncio
import hashlib
from typing import Any, Dict, Optional

from services.common.path_guard import PathGuard
from services.tool_executor.assistant_tools.base import (
    resolve_guard,
    SomaAssistantTool,
    tool_error,
    workroot_guard,
)


class FileWriteTool(SomaAssistantTool):
    """Write UTF-8 text into the workroot; returns path, byte count, SHA-256.

    Tier 2: the capsule policy (or the unlisted = approval default) must gate
    this behind a human approval before it executes.
    """

    name = "file_write"
    description = (
        "Create or overwrite a UTF-8 text file in the agent work directory "
        "(relative path). Returns the path, byte count, and SHA-256 hash of "
        "the written content. Requires approval."
    )
    tier = 2

    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "File path relative to the agent work directory; parent directories are created.",
                },
                "content": {
                    "type": "string",
                    "description": "Full text content to write (UTF-8, overwrites any existing file).",
                },
            },
            "required": ["path", "content"],
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
        content = data.get("content")
        if not isinstance(content, str):
            raise tool_error("content must be a string")

        g = workroot_guard(guard)
        target = resolve_guard(g, path_arg)
        payload = content.encode("utf-8")
        rel = g.relative_to_workroot(target)

        def _write() -> None:
            if target.exists() and not target.is_file():
                raise tool_error(f"not a writable file: {rel}")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(payload)

        await asyncio.to_thread(_write)
        return {
            "path": rel,
            "bytes": len(payload),
            "hash": hashlib.sha256(payload).hexdigest(),
        }
