"""Speech endpoints extracted from gateway monolith (minimal functional)."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel

router = APIRouter(prefix="/v1/speech", tags=["speech"])


class TranscribeRequest(BaseModel):
    language: Optional[str] = None


@router.post("/transcribe")
async def transcribe(
    file: UploadFile = File(...), req: TranscribeRequest | None = None
) -> JSONResponse:
    raise HTTPException(status_code=501, detail="Speech transcription not implemented")


class KokoroSynthesizeRequest(BaseModel):
    text: str
    voice: Optional[str] = None
    speed: Optional[float] = None


@router.post("/tts/kokoro")
async def kokoro_tts(req: KokoroSynthesizeRequest) -> JSONResponse:
    if not req.text:
        raise HTTPException(status_code=400, detail="missing_text")
    raise HTTPException(status_code=501, detail="Kokoro TTS not implemented")


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
    raise HTTPException(status_code=501, detail="Realtime session not implemented")


class OpenAIRealtimeAnswer(BaseModel):
    api_base: str
    api_key: str
    model: str


@router.post("/openai/realtime/offer", response_model=OpenAIRealtimeAnswer)
async def openai_realtime_offer(body: OpenAIRealtimeAnswer) -> OpenAIRealtimeAnswer:
    raise HTTPException(status_code=501, detail="OpenAI realtime not implemented")
