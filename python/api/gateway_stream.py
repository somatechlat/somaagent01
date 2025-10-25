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
            try:
                async with httpx.AsyncClient(timeout=None) as client:
                    async with client.stream("GET", url, headers=headers) as resp:
                        resp.raise_for_status()
                        async for chunk in resp.aiter_bytes():
                            # Forward raw SSE bytes
                            yield chunk
            except Exception as exc:
                # Emit a terminal SSE error event so the client can handle it
                msg = f"event: error\ndata: {type(exc).__name__}: {str(exc)}\n\n"
                PrintStyle.error(f"GatewayStream error: {exc}")
                yield msg.encode("utf-8")

        headers_resp = {
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
        return Response(sse_generator(), headers=headers_resp)

