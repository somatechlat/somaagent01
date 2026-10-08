"""file_search — literal text search inside the agent workroot (tier 1)."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from services.common.path_guard import PathGuard
from services.tool_executor.assistant_tools.base import (
    resolve_guard,
    SomaAssistantTool,
    tool_error,
    workroot_guard,
)

DEFAULT_MAX_MATCHES = 50
MAX_MATCHES_CAP = 200
MAX_FILES_SCANNED = 500
MAX_FILE_BYTES = 5_000_000
MAX_LINE_CHARS = 200


class FileSearchTool(SomaAssistantTool):
    """Search workroot text files for a literal query; return line-numbered matches.

    Case-insensitive substring match, truncated results; no full file content.
    """

    name = "file_search"
    description = (
        "Search text files in the agent work directory for a literal string "
        "(case-insensitive) and return matching lines with path and line "
        "number. Results are truncated; no full file content is returned."
    )
    tier = 1

    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Literal text to search for (case-insensitive).",
                },
                "path": {
                    "type": "string",
                    "description": "File or directory relative to the agent work directory (default: work directory root).",
                },
                "max_matches": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": MAX_MATCHES_CAP,
                    "description": f"Stop after this many matching lines (default {DEFAULT_MAX_MATCHES}, max {MAX_MATCHES_CAP}).",
                },
            },
            "required": ["query"],
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
        query = data.get("query")
        if not isinstance(query, str) or not query.strip():
            raise tool_error("query is required")
        path_arg = str(data.get("path") or "").strip() or "."
        raw_max = data.get("max_matches")
        if raw_max is None or raw_max == "":
            max_matches = DEFAULT_MAX_MATCHES
        else:
            try:
                max_matches = int(raw_max)
            except (TypeError, ValueError) as exc:
                raise tool_error("max_matches must be an integer") from exc
            max_matches = max(1, min(max_matches, MAX_MATCHES_CAP))

        g = workroot_guard(guard)
        target = resolve_guard(g, path_arg)
        matches, files_scanned, truncated = await asyncio.to_thread(
            self._search, g, target, query, max_matches
        )
        return {
            "query": query,
            "path": g.relative_to_workroot(target),
            "match_count": len(matches),
            "matches": matches,
            "files_scanned": files_scanned,
            "truncated": truncated,
        }

    def _search(
        self, g: PathGuard, target: Path, query: str, max_matches: int
    ) -> Tuple[List[Dict[str, Any]], int, bool]:
        if not target.exists():
            raise tool_error(f"path not found: {g.relative_to_workroot(target)}")
        if target.is_file():
            files = [target]
        elif target.is_dir():
            files = sorted(
                (p for p in target.rglob("*") if p.is_file()),
                key=lambda p: p.as_posix(),
            )
        else:
            raise tool_error(f"not a file or directory: {g.relative_to_workroot(target)}")

        needle = query.casefold()
        matches: List[Dict[str, Any]] = []
        files_scanned = 0
        truncated = False

        for path in files:
            if files_scanned >= MAX_FILES_SCANNED:
                truncated = True
                break
            try:
                raw = path.read_bytes()
            except OSError:
                continue
            if len(raw) > MAX_FILE_BYTES or b"\x00" in raw[:8192]:
                continue
            files_scanned += 1
            rel = g.relative_to_workroot(path)
            for lineno, line in enumerate(raw.decode("utf-8", errors="replace").splitlines(), 1):
                if needle in line.casefold():
                    matches.append({"path": rel, "line": lineno, "text": line[:MAX_LINE_CHARS]})
                    if len(matches) >= max_matches:
                        truncated = True
                        break
            if truncated:
                break

        return matches, files_scanned, truncated
