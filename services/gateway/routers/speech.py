"""Speech endpoints extracted from gateway monolith (minimal functional)."""
from __future__ import annotations

import base64
from typing import Optional

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel

router = APIRouter(prefix="/v1/speech", tags=["speech"])


class TranscribeRequest(BaseModel):
    language: Optional[str] = None


@router.post("/transcribe")
async def transcribe(file: UploadFile = File(...), req: TranscribeRequest | None = None) -> JSONResponse:
    data = await file.read()
    # Minimal: just return fake transcription length
    return JSONResponse({"text": f"transcribed {len(data)} bytes", "language": req.language if req else None})


class KokoroSynthesizeRequest(BaseModel):
    text: str
    voice: Optional[str] = None
    speed: Optional[float] = None


@router.post("/tts/kokoro")
async def kokoro_tts(req: KokoroSynthesizeRequest) -> JSONResponse:
    if not req.text:
        raise HTTPException(status_code=400, detail="missing_text")
    audio_b64 = base64.b64encode(req.text.encode()).decode()
    return JSONResponse({"audio": audio_b64})


class RealtimeSessionRequest(BaseModel):
    locale: Optional[str] = None
    device: Optional[str] = None


class RealtimeSessionResponse(BaseModel):
    session_id: str
    ws_url: str
    expires_at: float
    caps: dict | None = None


@router.post("/realtime/session", response_model=RealtimeSessionResponse)
async def realtime_session(_: RealtimeSessionRequest) -> RealtimeSessionResponse:
    return RealtimeSessionResponse(session_id="session-1", ws_url="ws://localhost/rt", expires_at=0.0, caps=None)


class OpenAIRealtimeAnswer(BaseModel):
    api_base: str
    api_key: str
    model: str


@router.post("/openai/realtime/offer", response_model=OpenAIRealtimeAnswer)
async def openai_realtime_offer(body: OpenAIRealtimeAnswer) -> OpenAIRealtimeAnswer:
    return body
