"""Minimal tool implementations for SomaAgent 01.

These are placeholder open-source utilities until the full SKM Tool Service
integration is complete. They execute real logic (no mocks), but are kept
simple for safety.
"""
from __future__ import annotations

import datetime
from typing import Any, Dict


class ToolExecutionError(Exception):
    """Raised when a tool fails."""


class BaseTool:
    name: str

    async def run(self, args: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError


class EchoTool(BaseTool):
    name = "echo"

    async def run(self, args: Dict[str, Any]) -> Dict[str, Any]:
        text = args.get("text")
        if not isinstance(text, str):
            raise ToolExecutionError("echo requires a 'text' field")
        return {"message": text}


class TimestampTool(BaseTool):
    name = "timestamp"

    async def run(self, args: Dict[str, Any]) -> Dict[str, Any]:
        fmt = args.get("format", "%Y-%m-%dT%H:%M:%SZ")
        try:
            now = datetime.datetime.utcnow().strftime(fmt)
        except Exception as exc:  # pragma: no cover - invalid format
            raise ToolExecutionError(f"Invalid format '{fmt}': {exc}") from exc
        return {"message": now}


AVAILABLE_TOOLS = {tool.name: tool for tool in [EchoTool(), TimestampTool()]}
