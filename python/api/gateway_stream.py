from __future__ import annotations

import os
from typing import Any, Iterator

import httpx
from flask import Response

from python.helpers.api import ApiHandler, Request
from python.helpers.print_style import PrintStyle


class GatewayStream(ApiHandler):
    @classmethod
    def requires_auth(cls) -> bool:
        return False  # SSE proxy must be public on the UI server

    @classmethod
    def requires_csrf(cls) -> bool:
        return False  # EventSource does not send CSRF headers; allow without CSRF

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["GET"]

    async def process(self, input: dict[str, Any], request: Request) -> Response:
        """Proxy Gateway SSE to the UI as a WSGI-friendly generator.

        Flask/Werkzeug expects a sync iterable for streaming responses. Returning
        an async generator triggers 'TypeError: async_generator is not iterable'.
        We therefore use the synchronous httpx.Client.stream and yield bytes.
        """
        session_id = request.args.get("session_id") or request.args.get("sid")
        if not session_id:
            return Response("Missing session_id", status=400, mimetype="text/plain")

        base = os.getenv("UI_GATEWAY_BASE", os.getenv("GATEWAY_BASE_URL", "http://localhost:21016")).rstrip("/")
        primary = f"{base}/v1/session/{session_id}/events"
        host_alias = os.getenv("SOMA_CONTAINER_HOST_ALIAS", "host.docker.internal")
        gw_port = os.getenv("GATEWAY_PORT", "21016")
        fallback = f"http://{host_alias}:{gw_port}/v1/session/{session_id}/events"

        headers = {}
        if (bearer := os.getenv("UI_GATEWAY_BEARER")):
            headers["Authorization"] = f"Bearer {bearer}"

        def stream_from(url: str) -> Iterator[bytes]:
            with httpx.Client(timeout=None) as client:
                with client.stream("GET", url, headers=headers) as resp:
                    resp.raise_for_status()
                    for chunk in resp.iter_bytes():
                        yield chunk

        def sse_generator() -> Iterator[bytes]:
            try:
                yield from stream_from(primary)
                return
            except Exception as exc:
                try:
                    if fallback.rstrip("/") != primary.rstrip("/"):
                        yield from stream_from(fallback)
                        return
                except Exception as exc2:
                    msg = f"event: error\ndata: {type(exc2).__name__}: {str(exc2)}\n\n"
                    PrintStyle.error(f"GatewayStream error: {exc}; fallback: {exc2}")
                    yield msg.encode("utf-8")

        headers_resp = {
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
        return Response(sse_generator(), headers=headers_resp)
