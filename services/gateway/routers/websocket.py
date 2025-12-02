"""WebSocket endpoints extracted from gateway monolith."""

from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


@router.websocket("/v1/speech/realtime/ws")
async def speech_realtime_ws(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            data = await ws.receive_text()
            await ws.send_text(f"echo:{data}")
    except WebSocketDisconnect:
        await ws.close()


@router.websocket("/v1/session/{session_id}/stream")
async def session_stream(ws: WebSocket, session_id: str):
    await ws.accept()
    try:
        await ws.send_text(f"stream_start:{session_id}")
        while True:
            data = await ws.receive_text()
            await ws.send_text(f"stream:{session_id}:{data}")
    except WebSocketDisconnect:
        await ws.close()
