"""Minimal tool implementations for SomaAgent 01."""

from __future__ import annotations

import asyncio
import datetime
import io
import logging
import os
from contextlib import redirect_stdout
from pathlib import Path
from typing import Any, Dict

import httpx

import fitz  # PyMuPDF
import pytesseract
from PIL import Image

LOGGER = logging.getLogger(__name__)


class ToolExecutionError(Exception):
    """Raised when a tool fails."""


class BaseTool:
    """Basetool class implementation."""

    name: str

    async def run(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute run.

        Args:
            args: The args.
        """

        raise NotImplementedError

    def input_schema(self) -> Dict[str, Any] | None:
        """Optional JSON Schema for tool inputs.

        Returning a schema enables model-led tool calling (e.g., OpenAI tools API).
        """
        return None


class EchoTool(BaseTool):
    """Echotool class implementation."""

    name = "echo"

    async def run(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute run.

        Args:
            args: The args.
        """

        text = args.get("text")
        if not isinstance(text, str):
            from admin.common.messages import ErrorCode, get_message
            raise ToolExecutionError(get_message(ErrorCode.TOOL_MISSING_ARGUMENT, arg="text"))
        return {"message": text}

    def input_schema(self) -> Dict[str, Any] | None:
        """Execute input schema."""

        return {
            "type": "object",
            "properties": {"text": {"type": "string", "description": "Text to echo back"}},
            "required": ["text"],
            "additionalProperties": False,
        }


class TimestampTool(BaseTool):
    """Timestamptool class implementation."""

    name = "timestamp"

    async def run(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute run.

        Args:
            args: The args.
        """

        fmt = args.get("format", "%Y-%m-%dT%H:%M:%SZ")
        try:
            now = datetime.datetime.now(datetime.timezone.utc).strftime(fmt)
        except Exception as exc:
            LOGGER.warning(
                "Tool validation failed",
                extra={
                    "error": str(exc),
                    "error_type": type(exc).__name__,
                    "tool_data": str(args)[:100],  # truncate for logging
                },
            )
            now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        return {"message": now}

    def input_schema(self) -> Dict[str, Any] | None:
        """Execute input schema."""

        return {
            "type": "object",
            "properties": {
                "format": {
                    "type": "string",
                    "description": "Python datetime format string (default %Y-%m-%dT%H:%M:%SZ)",
                }
            },
            "additionalProperties": False,
        }


class CodeExecutionTool(BaseTool):
    """Codeexecutiontool class implementation."""

    name = "code_execute"

    async def run(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute run.

        Args:
            args: The args.
        """

        language = args.get("language", "python").lower()
        if language != "python":
            from admin.common.messages import ErrorCode, get_message
            raise ToolExecutionError(get_message(ErrorCode.TOOL_INVALID_ARGUMENT, arg="language"))
        code = args.get("code")
        if not isinstance(code, str) or not code.strip():
            from admin.common.messages import ErrorCode, get_message
            raise ToolExecutionError(get_message(ErrorCode.TOOL_MISSING_ARGUMENT, arg="code"))

        def _execute() -> dict[str, Any]:
            """Execute execute."""

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
            except Exception as exc:
                LOGGER.error(
                    "Tool execution failed",
                    extra={
                        "error": str(exc),
                        "error_type": type(exc).__name__,
                        "tool_name": self.name,
                    },
                )
            return {
                "stdout": buffer.getvalue(),
                "locals": {
                    key: value for key, value in local_vars.items() if not key.startswith("_")
                },
            }

        return await asyncio.to_thread(_execute)

    def input_schema(self) -> Dict[str, Any] | None:
        """Execute input schema."""

        return {
            "type": "object",
            "properties": {
                "language": {
                    "type": "string",
                    "enum": ["python"],
                    "description": "Only 'python' is supported",
                },
                "code": {"type": "string", "description": "Python source code to execute"},
            },
            "required": ["code"],
            "additionalProperties": False,
        }


class FileReadTool(BaseTool):
    """Filereadtool class implementation."""

    name = "file_read"

    async def run(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute run.

        Args:
            args: The args.
        """

        path_arg = args.get("path")
        if not isinstance(path_arg, str):
            from admin.common.messages import ErrorCode, get_message
            raise ToolExecutionError(get_message(ErrorCode.TOOL_MISSING_ARGUMENT, arg="path"))
        base_dir = Path(os.environ.get("TOOL_WORK_DIR", "work_dir")).resolve()
        target = (base_dir / path_arg).resolve()
        if not str(target).startswith(str(base_dir)):
            from admin.common.messages import ErrorCode, get_message
            raise ToolExecutionError(get_message(ErrorCode.TOOL_PATH_NOT_ALLOWED))
        if not target.exists() or not target.is_file():
            from admin.common.messages import ErrorCode, get_message
            raise ToolExecutionError(get_message(ErrorCode.TOOL_FILE_NOT_FOUND, path=path_arg))
        content = await asyncio.to_thread(target.read_text)
        return {"path": str(target), "content": content}

    def input_schema(self) -> Dict[str, Any] | None:
        """Execute input schema."""

        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Relative path within work_dir"}
            },
            "required": ["path"],
            "additionalProperties": False,
        }


class HttpFetchTool(BaseTool):
    """Httpfetchtool class implementation."""

    name = "http_fetch"

    async def run(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute run.

        Args:
            args: The args.
        """

        url = args.get("url")
        if not isinstance(url, str) or not url.startswith("http"):
            from admin.common.messages import ErrorCode, get_message
            raise ToolExecutionError(get_message(ErrorCode.TOOL_URL_INVALID))
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

    def input_schema(self) -> Dict[str, Any] | None:
        """Execute input schema."""

        return {
            "type": "object",
            "properties": {
                "url": {"type": "string", "format": "uri", "description": "URL to fetch"},
                "timeout": {"type": "number", "minimum": 0, "default": 10.0},
            },
            "required": ["url"],
            "additionalProperties": False,
        }


class CanvasAppendTool(BaseTool):
    """Canvasappendtool class implementation."""

    name = "canvas_append"

    async def run(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute run.

        Args:
            args: The args.
        """

        session_id = args.get("session_id")
        if not isinstance(session_id, str) or not session_id:
            from admin.common.messages import ErrorCode, get_message
            raise ToolExecutionError(get_message(ErrorCode.TOOL_MISSING_ARGUMENT, arg="session_id"))
        pane = args.get("pane", "default")
        content = args.get("content")
        if content is None:
            from admin.common.messages import ErrorCode, get_message
            raise ToolExecutionError(get_message(ErrorCode.TOOL_MISSING_ARGUMENT, arg="content"))
        metadata = args.get("metadata") or {}
        persona_id = args.get("persona_id")

        canvas_url = os.environ.get("CANVAS_SERVICE_URL")
        if not canvas_url:
            from admin.common.messages import ErrorCode, get_message
            raise RuntimeError(get_message(ErrorCode.TOOL_SERVICE_NOT_CONFIGURED, service="canvas"))
        endpoint = f"{canvas_url.rstrip('/')}/v1/canvas/event"
        payload = {
            "session_id": session_id,
            "pane": pane,
            "content": str(content),
            "metadata": metadata,
            "persona_id": persona_id,
        }
        async with httpx.AsyncClient(
            timeout=float(os.environ.get("CANVAS_SERVICE_TIMEOUT", "5"))
        ) as client:
            response = await client.post(endpoint, json=payload)
            response.raise_for_status()
        return {"status": "queued", "pane": pane}

    def input_schema(self) -> Dict[str, Any] | None:
        """Execute input schema."""

        return {
            "type": "object",
            "properties": {
                "session_id": {"type": "string"},
                "pane": {"type": "string", "default": "default"},
                "content": {"description": "Arbitrary content to append"},
                "metadata": {"type": "object"},
                "persona_id": {"type": ["string", "null"]},
            },
            "required": ["session_id", "content"],
            "additionalProperties": True,
        }


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


class IngestDocumentTool(BaseTool):
    """Ingestdocumenttool class implementation."""

    name = "document_ingest"

    async def run(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute run.

        Args:
            args: The args.
        """

        attachment_id = args.get("attachment_id")
        metadata = args.get("metadata") or {}
        tenant_header = None
        try:
            if isinstance(metadata, dict):
                tenant_header = metadata.get("tenant")
        except Exception:
            tenant_header = None

        # Strict contract: attachment ingestion must be by ID only
        if not (isinstance(attachment_id, str) and attachment_id.strip()):
            from admin.common.messages import ErrorCode, get_message
            raise ToolExecutionError(get_message(ErrorCode.TOOL_MISSING_ARGUMENT, arg="attachment_id"))

        base = os.environ.get("SA01_GATEWAY_BASE")
        if not base:
            from admin.common.messages import ErrorCode, get_message
            raise ToolExecutionError(get_message(ErrorCode.TOOL_SERVICE_NOT_CONFIGURED, service="gateway"))
        base = base.rstrip("/")
        token = os.environ.get("SA01_GATEWAY_INTERNAL_TOKEN")
        if not token:
            from admin.common.messages import ErrorCode, get_message
            raise ToolExecutionError(get_message(ErrorCode.TOOL_SERVICE_NOT_CONFIGURED, service="gateway_token"))
        url = f"{base}/internal/attachments/{attachment_id}/binary"
        headers = {"X-Internal-Token": token}
        if tenant_header:
            headers["X-Tenant-Id"] = str(tenant_header)
        try:
            async with httpx.AsyncClient(
                timeout=float(os.environ.get("TOOL_FETCH_TIMEOUT", "15"))
            ) as client:
                resp = await client.get(url, headers=headers)
                if resp.status_code == 404:
                    from admin.common.messages import ErrorCode, get_message
                    raise ToolExecutionError(get_message(ErrorCode.TOOL_ATTACHMENT_NOT_FOUND))
                resp.raise_for_status()
                data = resp.content
                mime = resp.headers.get("content-type", "application/octet-stream")
                filename = "attachment"
                try:
                    cd = resp.headers.get("content-disposition", "")
                    # naive parse of filename
                    if "filename=" in cd:
                        filename = cd.split("filename=", 1)[1].strip().strip('"')
                except Exception:
                    pass
        except Exception as exc:
            if isinstance(exc, ToolExecutionError):
                # Preserve explicit tool error semantics (e.g., 404 not found)
                raise
            LOGGER.error("Attachment fetch failed", extra={"error": str(exc)})
            from admin.common.messages import ErrorCode, get_message
            raise ToolExecutionError(get_message(ErrorCode.TOOL_ATTACHMENT_FETCH_FAILED))

        text = ""
        try:
            # Text-like
            if mime.startswith("text/") or mime in {"application/json", "application/xml"}:
                try:
                    text = data.decode("utf-8", errors="ignore")
                except Exception:
                    text = data.decode("latin-1", errors="ignore")
            # PDF
            elif (
                mime == "application/pdf" or (filename or "").lower().endswith(".pdf")
            ) and fitz is not None:
                try:
                    import io as _io

                    parts = []
                    with fitz.open(stream=_io.BytesIO(data), filetype="pdf") as doc:
                        for page in doc:
                            parts.append(page.get_text("text"))  # type: ignore[attr-defined]
                    text = "\n".join(parts)
                except Exception as exc:
                    LOGGER.warning("PyMuPDF extraction failed", extra={"error": str(exc)})
            # Images via OCR
            elif mime.startswith("image/") and Image is not None and pytesseract is not None:
                try:
                    import io as _io

                    img = Image.open(_io.BytesIO(data))
                    text = pytesseract.image_to_string(img)
                except Exception as exc:
                    LOGGER.warning("OCR extraction failed", extra={"error": str(exc)})
        except Exception as exc:
            LOGGER.error("Ingestion failed", extra={"error": str(exc)})
            from admin.common.messages import ErrorCode, get_message
            raise ToolExecutionError(get_message(ErrorCode.TOOL_INGESTION_FAILED))

        if not text:
            from admin.common.messages import ErrorCode, get_message
            raise ToolExecutionError(get_message(ErrorCode.TOOL_EXTRACTION_FAILED))

        return {
            "attachment_id": attachment_id,
            "filename": filename,
            "mime": mime or "application/octet-stream",
            "text": text[:400_000],
        }

    def input_schema(self) -> Dict[str, Any] | None:
        """Execute input schema."""

        return {
            "type": "object",
            "properties": {
                "attachment_id": {"type": "string", "description": "Attachment UUID to ingest"},
                "session_id": {"type": ["string", "null"]},
                "persona_id": {"type": ["string", "null"]},
                "metadata": {"type": "object"},
            },
            "required": ["attachment_id"],
            "additionalProperties": True,
        }


# Register tool at import time
AVAILABLE_TOOLS[IngestDocumentTool.name] = IngestDocumentTool()
