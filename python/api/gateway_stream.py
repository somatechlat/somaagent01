from __future__ import annotations

import asyncio
import os
from typing import Any, AsyncIterator

import httpx
from flask import Response

from python.helpers.api import ApiHandler, Request
from python.helpers.print_style import PrintStyle


class GatewayStream(ApiHandler):
    @classmethod
    def get_methods(cls) -> list[str]:
        return ["GET"]

    async def process(self, input: dict[str, Any], request: Request) -> Response:
        session_id = request.args.get("session_id") or request.args.get("sid")
        if not session_id:
            return Response("Missing session_id", status=400, mimetype="text/plain")

        base = os.getenv("UI_GATEWAY_BASE", os.getenv("GATEWAY_BASE_URL", "http://localhost:20016")).rstrip("/")
        url = f"{base}/v1/session/{session_id}/events"

        headers = {}
        if (bearer := os.getenv("UI_GATEWAY_BEARER")):
            headers["Authorization"] = f"Bearer {bearer}"

        # Stream SSE from Gateway and forward to the client
        async def sse_generator() -> AsyncIterator[bytes]:
            async def _stream_from(target_url: str) -> AsyncIterator[bytes]:
                async with httpx.AsyncClient(timeout=None) as client:
                    async with client.stream("GET", target_url, headers=headers) as resp:
                        resp.raise_for_status()
                        async for chunk in resp.aiter_bytes():
                            yield chunk

            # Try primary, then dev fallback via host.docker.internal:<GATEWAY_PORT>
            try:
                async for chunk in _stream_from(url):
                    yield chunk
                return
            except Exception as exc:
                try:
                    host_alias = os.getenv("SOMA_CONTAINER_HOST_ALIAS", "host.docker.internal")
                    gw_port = os.getenv("GATEWAY_PORT", "21016")
                    alt = f"http://{host_alias}:{gw_port}/v1/session/{session_id}/events"
                    if alt.rstrip("/") != url.rstrip("/"):
                        async for chunk in _stream_from(alt):
                            yield chunk
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
