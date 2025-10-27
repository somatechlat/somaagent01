"""Domain helpers for the UI proxy routes."""

from __future__ import annotations

import os
import uuid
from typing import Any, Dict, Iterable, List, Optional

import httpx
from fastapi import HTTPException, Request, UploadFile
from werkzeug.utils import secure_filename

from python.helpers import files
from services.ui_proxy.client import GatewayClient


class UiMessageService:
    """Handle legacy UI message requests by forwarding them to the gateway."""

    def __init__(self, *, upload_dir: str | None = None, internal_prefix: str | None = None) -> None:
        self.upload_dir = upload_dir or os.getenv("UI_PROXY_UPLOAD_DIR", "tmp/uploads")
        self.internal_prefix = internal_prefix or os.getenv(
            "UI_PROXY_UPLOAD_PREFIX", "/git/agent-zero/tmp/uploads"
        )

    async def handle_request(self, request: Request, client: GatewayClient) -> Dict[str, Any]:
        if "multipart/form-data" in (request.headers.get("content-type") or ""):
            return await self._handle_multipart(request, client)
        payload = await request.json()
        return await self._dispatch_to_gateway(client, payload, attachments=[])

    async def _handle_multipart(self, request: Request, client: GatewayClient) -> Dict[str, Any]:
        form = await request.form()
        text = str(form.get("text", ""))
        context_id = form.get("context") or None
        message_id = form.get("message_id") or str(uuid.uuid4())
        uploads: Iterable[UploadFile] = form.getlist("attachments")
        attachments = await self._persist_attachments(uploads, message_id)
        payload = {
            "text": text,
            "context": context_id,
            "message_id": message_id,
        }
        return await self._dispatch_to_gateway(client, payload, attachments=attachments)

    async def _persist_attachments(
        self,
        uploads: Iterable[UploadFile],
        message_id: str,
    ) -> List[str]:
        # File saving is disabled; discard attachments after reading to free resources
        for upload in uploads:
            try:
                _ = await upload.read()  # read and discard
            finally:
                try:
                    await upload.close()
                except Exception:
                    pass
        return []

    async def _dispatch_to_gateway(
        self,
        client: GatewayClient,
        payload: Dict[str, Any],
        *,
        attachments: List[str],
    ) -> Dict[str, Any]:
        text = payload.get("text") or payload.get("message") or ""
        if not isinstance(text, str):
            text = str(text)
        context_id = payload.get("context") or payload.get("session_id")
        persona_id = payload.get("persona_id")
        message_id = payload.get("message_id") or str(uuid.uuid4())

        gateway_payload: Dict[str, Any] = {
            "session_id": context_id,
            "persona_id": persona_id,
            "message": text,
            "attachments": attachments,
            "metadata": {
                "source": "agent-ui",
                "message_id": message_id,
            },
        }
        response = await client.post_message(gateway_payload)
        if response.status_code >= 400:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.json()


class PollAggregator:
    """Compose poll responses using gateway session metadata."""

    def __init__(self, client: GatewayClient, *, max_events: int = 200) -> None:
        self.client = client
        self.max_events = max_events

    async def poll(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        context_id = self._normalise_context(payload.get("context"))

        sessions = await self._fetch_sessions()
        contexts = [self._format_session(session, index) for index, session in enumerate(sessions)]

        if not context_id and contexts:
            context_id = contexts[0]["id"]

        history = await self._fetch_history(context_id) if context_id else {"events": [], "total": 0}
        events: List[Dict[str, Any]] = history.get("events", [])
        total = history.get("total", len(events))
        log_from = int(payload.get("log_from", 0) or 0)

        logs = [self._event_to_log(idx, event) for idx, event in enumerate(events)]
        logs_delta = logs[log_from:]

        return {
            "context": context_id or "",
            "contexts": contexts,
            "tasks": [],
            "logs": logs_delta,
            "log_guid": context_id or "",  # gateway sessions map directly to contexts
            "log_version": total,
            "log_progress": None,
            "log_progress_active": False,
            "paused": False,
            "notifications": [],
            "notifications_guid": "gateway",
            "notifications_version": 0,
            "components": None,
        }

    async def _fetch_sessions(self) -> List[Dict[str, Any]]:
        try:
            response = await self.client.get_contexts()
        except httpx.HTTPStatusError as exc:
            # Treat upstream 5xx as transient and return an empty session list for UI resiliency
            if 500 <= exc.response.status_code < 600:
                return []
            raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text) from exc
        except httpx.HTTPError as exc:
            # Network or protocol error – surface as 502 but keep UI alive with no sessions
            return []

        if isinstance(response, list):
            return response
        if isinstance(response, dict):
            return response.get("sessions", [])
        return []

    async def _fetch_history(self, session_id: str | None) -> Dict[str, Any]:
        if not session_id:
            return {"events": [], "total": 0}
        try:
            history = await self.client.list_events(session_id, limit=self.max_events)
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code in {404, 422}:
                return {"session_id": session_id, "events": [], "total": 0}
            raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text) from exc
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=502, detail=f"Gateway history fetch failed: {exc}") from exc
        return history

    def _format_session(self, session: Dict[str, Any], index: int) -> Dict[str, Any]:
        session_id = str(session.get("session_id"))
        metadata = session.get("metadata") or {}
        name = metadata.get("title") or metadata.get("name") or session_id[-8:]
        created_at = float(session.get("created_at", 0.0) or 0.0)
        updated_at = float(session.get("updated_at", 0.0) or created_at)
        return {
            "id": session_id,
            "name": name,
            "created_at": created_at,
            "no": index + 1,
            "paused": False,
            "last_message": updated_at,
            "type": "user",
            "log_guid": session_id,
            "log_version": 0,
            "log_length": 0,
        }

    def _event_to_log(self, index: int, event: Dict[str, Any]) -> Dict[str, Any]:
        event_id = event.get("event_id") or f"event-{index}"
        event_type = str(event.get("type") or event.get("role") or "info")
        metadata = event.get("metadata") or {}
        heading = metadata.get("heading")
        content = event.get("message") or event.get("content") or event.get("details") or ""

        log_type = self._map_event_type(event_type)
        if not heading:
            heading = self._default_heading(log_type)

        return {
            "id": event_id,
            "no": index + 1,
            "type": log_type,
            "heading": heading,
            "content": content,
            "temp": metadata.get("status") == "streaming",
            "kvps": metadata if metadata else None,
        }

    @staticmethod
    def _default_heading(log_type: str) -> str:
        if log_type == "user":
            return "User message"
        if log_type in {"agent", "response"}:
            return "Soma response"
        if log_type == "error":
            return "Error"
        return log_type.capitalize()

    @staticmethod
    def _map_event_type(event_type: str) -> str:
        if event_type == "user":
            return "user"
        if event_type == "assistant":
            return "response"
        if event_type in {"error", "exception"}:
            return "error"
        if event_type in {"tool", "agent"}:
            return "agent"
        return "info"

    @staticmethod
    def _normalise_context(value: Any) -> Optional[str]:
        if value in {None, "", "null", "None"}:
            return None
        return str(value)
