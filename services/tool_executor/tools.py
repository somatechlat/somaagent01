"""Minimal tool implementations for SomaAgent 01."""

from __future__ import annotations

import asyncio
import datetime
import io
import os
from contextlib import redirect_stdout
from pathlib import Path
from typing import Any, Dict

import httpx


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


class CodeExecutionTool(BaseTool):
    name = "code_execute"

    async def run(self, args: Dict[str, Any]) -> Dict[str, Any]:
        language = args.get("language", "python").lower()
        if language != "python":
            raise ToolExecutionError("Only Python code execution is supported")
        code = args.get("code")
        if not isinstance(code, str) or not code.strip():
            raise ToolExecutionError("Provide Python source via 'code'")

        def _execute() -> dict[str, Any]:
            buffer = io.StringIO()
            local_vars: dict[str, Any] = {}
            try:
                with redirect_stdout(buffer):
                    exec(
                        code,
                        {
                            "__builtins__": {
                                "print": print,
                                "range": range,
                                "len": len,
                            }
                        },
                        local_vars,
                    )
            except Exception as exc:  # pragma: no cover - depends on user code
                raise ToolExecutionError(str(exc)) from exc
            return {
                "stdout": buffer.getvalue(),
                "locals": {
                    key: value for key, value in local_vars.items() if not key.startswith("_")
                },
            }

        return await asyncio.to_thread(_execute)


class FileReadTool(BaseTool):
    name = "file_read"

    async def run(self, args: Dict[str, Any]) -> Dict[str, Any]:
        path_arg = args.get("path")
        if not isinstance(path_arg, str):
            raise ToolExecutionError("'path' argument is required")
        base_dir = Path(os.getenv("TOOL_WORK_DIR", "work_dir")).resolve()
        target = (base_dir / path_arg).resolve()
        if not str(target).startswith(str(base_dir)):
            raise ToolExecutionError("Access outside work directory is not allowed")
        if not target.exists() or not target.is_file():
            raise ToolExecutionError("File not found")
        content = await asyncio.to_thread(target.read_text)
        return {"path": str(target), "content": content}


class HttpFetchTool(BaseTool):
    name = "http_fetch"

    async def run(self, args: Dict[str, Any]) -> Dict[str, Any]:
        url = args.get("url")
        if not isinstance(url, str) or not url.startswith("http"):
            raise ToolExecutionError("Valid 'url' argument required")
        timeout = float(args.get("timeout", 10.0))
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url)
            response.raise_for_status()
            return {
                "url": url,
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "text": response.text,
            }


class CanvasAppendTool(BaseTool):
    name = "canvas_append"

    async def run(self, args: Dict[str, Any]) -> Dict[str, Any]:
        session_id = args.get("session_id")
        if not isinstance(session_id, str) or not session_id:
            raise ToolExecutionError("'session_id' is required")
        pane = args.get("pane", "default")
        content = args.get("content")
        if content is None:
            raise ToolExecutionError("'content' is required")
        metadata = args.get("metadata") or {}
        persona_id = args.get("persona_id")

        canvas_url = os.getenv("CANVAS_SERVICE_URL", "http://localhost:8014")
        endpoint = f"{canvas_url.rstrip('/')}/v1/canvas/event"
        payload = {
            "session_id": session_id,
            "pane": pane,
            "content": str(content),
            "metadata": metadata,
            "persona_id": persona_id,
        }
        async with httpx.AsyncClient(
            timeout=float(os.getenv("CANVAS_SERVICE_TIMEOUT", "5"))
        ) as client:
            response = await client.post(endpoint, json=payload)
            response.raise_for_status()
        return {"status": "queued", "pane": pane}


AVAILABLE_TOOLS = {
    tool.name: tool
    for tool in [
        EchoTool(),
        TimestampTool(),
        CodeExecutionTool(),
        FileReadTool(),
        HttpFetchTool(),
        CanvasAppendTool(),
    ]
}
