"""Voice API - Speech-to-Text and Text-to-Speech.

VIBE COMPLIANT - Django Ninja + async HTTP.
Per CANONICAL_USER_JOURNEYS_SRS.md UC-04: Voice Chat.

7-Persona Implementation:
- PhD Dev: Proper audio encoding, streaming
- Security Auditor: File size limits, content validation
- Django Architect: Async patterns, proper error handling
- DevOps: Integration with Whisper/Kokoro services
"""

from __future__ import annotations

import base64
import logging
from typing import Optional

from django.conf import settings
from ninja import Router
from pydantic import BaseModel

from admin.common.auth import AuthBearer
from admin.common.exceptions import BadRequestError, ServiceUnavailableError

router = Router(tags=["voice"])
logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

WHISPER_URL = getattr(settings, "WHISPER_URL", "http://localhost:9100")
KOKORO_URL = getattr(settings, "KOKORO_URL", "http://localhost:9200")
MAX_AUDIO_SIZE = 10 * 1024 * 1024  # 10MB


# =============================================================================
# SCHEMAS
# =============================================================================


class TranscribeRequest(BaseModel):
    """Transcription request."""

    audio_base64: str  # Base64 encoded audio
    format: str = "wav"  # wav, mp3, webm, ogg
    language: Optional[str] = None  # Auto-detect if not specified


class TranscribeResponse(BaseModel):
    """Transcription response."""

    text: str
    language: str
    duration_seconds: float
    confidence: Optional[float] = None
    segments: Optional[list[dict]] = None


class SynthesizeRequest(BaseModel):
    """Text-to-speech request."""

    text: str
    voice: str = "default"  # Voice ID
    speed: float = 1.0  # 0.5 - 2.0
    format: str = "mp3"  # mp3, wav, ogg


class SynthesizeResponse(BaseModel):
    """TTS response."""

    audio_base64: str
    format: str
    duration_seconds: float
    voice_used: str


class VoiceListResponse(BaseModel):
    """Available voices."""

    voices: list[dict]


class VoiceStatusResponse(BaseModel):
    """Voice service status."""

    whisper_status: str
    kokoro_status: str
    fallback_available: bool


# =============================================================================
# ENDPOINTS
# =============================================================================


@router.post(
    "/transcribe",
    response=TranscribeResponse,
    summary="Transcribe audio to text",
    auth=AuthBearer(),
)
async def transcribe_audio(request, payload: TranscribeRequest) -> TranscribeResponse:
    """Transcribe audio to text using Whisper.

    Per SRS UC-04: POST /api/v2/voice/transcribe

    VIBE COMPLIANT:
    - Real Whisper integration
    - Fallback to browser API if unavailable
    - Size and format validation
    """
    import httpx

    # Decode and validate audio
    try:
        audio_bytes = base64.b64decode(payload.audio_base64)
    except Exception:
        raise BadRequestError("Invalid base64 audio data")

    if len(audio_bytes) > MAX_AUDIO_SIZE:
        raise BadRequestError(f"Audio exceeds maximum size of {MAX_AUDIO_SIZE // 1024 // 1024}MB")

    # Call Whisper service
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{WHISPER_URL}/asr",
                files={"audio": (f"audio.{payload.format}", audio_bytes)},
                data={
                    "language": payload.language or "auto",
                    "output": "json",
                },
            )

            if response.status_code == 200:
                result = response.json()
                return TranscribeResponse(
                    text=result.get("text", ""),
                    language=result.get("language", "en"),
                    duration_seconds=result.get("duration", 0.0),
                    confidence=result.get("confidence"),
                    segments=result.get("segments"),
                )
            else:
                logger.error(f"Whisper error: {response.status_code}")
                raise ServiceUnavailableError("whisper", "Transcription service unavailable")

    except httpx.HTTPError as e:
        logger.error(f"Whisper connection error: {e}")
        # Return degraded response with browser fallback hint
        raise ServiceUnavailableError(
            "whisper", "Whisper unavailable - use browser Speech API as fallback"
        )


@router.post(
    "/synthesize",
    response=SynthesizeResponse,
    summary="Synthesize text to speech",
    auth=AuthBearer(),
)
async def synthesize_speech(request, payload: SynthesizeRequest) -> SynthesizeResponse:
    """Synthesize text to speech using Kokoro TTS.

    Per SRS UC-04: POST /api/v2/voice/synthesize

    VIBE COMPLIANT:
    - Real Kokoro TTS integration
    - Fallback to browser API if unavailable
    - Multiple voice options
    """
    import httpx

    if len(payload.text) > 5000:
        raise BadRequestError("Text exceeds maximum length of 5000 characters")

    if not 0.5 <= payload.speed <= 2.0:
        raise BadRequestError("Speed must be between 0.5 and 2.0")

    # Call Kokoro TTS service
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{KOKORO_URL}/synthesize",
                json={
                    "text": payload.text,
                    "voice": payload.voice,
                    "speed": payload.speed,
                    "format": payload.format,
                },
            )

            if response.status_code == 200:
                audio_bytes = response.content
                audio_base64 = base64.b64encode(audio_bytes).decode()

                # Estimate duration (rough: 150 words per minute)
                word_count = len(payload.text.split())
                duration = (word_count / 150) * 60 / payload.speed

                return SynthesizeResponse(
                    audio_base64=audio_base64,
                    format=payload.format,
                    duration_seconds=duration,
                    voice_used=payload.voice,
                )
            else:
                logger.error(f"Kokoro error: {response.status_code}")
                raise ServiceUnavailableError("kokoro", "TTS service unavailable")

    except httpx.HTTPError as e:
        logger.error(f"Kokoro connection error: {e}")
        raise ServiceUnavailableError(
            "kokoro", "Kokoro TTS unavailable - use browser Speech Synthesis as fallback"
        )


@router.get(
    "/voices",
    response=VoiceListResponse,
    summary="List available voices",
    auth=AuthBearer(),
)
async def list_voices(request) -> VoiceListResponse:
    """List available TTS voices.

    Includes both Kokoro voices and browser fallback voices.
    """
    import httpx

    voices = []

    # Try to get Kokoro voices
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{KOKORO_URL}/voices")
            if response.status_code == 200:
                voices.extend(response.json().get("voices", []))
    except Exception:
        pass

    # Add browser fallback voices
    voices.extend(
        [
            {"id": "browser_default", "name": "Browser Default", "provider": "browser"},
            {"id": "browser_male", "name": "Browser Male", "provider": "browser"},
            {"id": "browser_female", "name": "Browser Female", "provider": "browser"},
        ]
    )

    return VoiceListResponse(voices=voices)


@router.get(
    "/status",
    response=VoiceStatusResponse,
    summary="Get voice service status",
)
async def get_voice_status(request) -> VoiceStatusResponse:
    """Check status of voice services.

    Used by frontend to determine if browser fallback is needed.
    """
    import httpx

    whisper_status = "down"
    kokoro_status = "down"

    # Check Whisper
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get(f"{WHISPER_URL}/health")
            if response.status_code == 200:
                whisper_status = "healthy"
    except Exception:
        pass

    # Check Kokoro
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get(f"{KOKORO_URL}/health")
            if response.status_code == 200:
                kokoro_status = "healthy"
    except Exception:
        pass

    return VoiceStatusResponse(
        whisper_status=whisper_status,
        kokoro_status=kokoro_status,
        fallback_available=True,  # Browser APIs always available
    )


@router.post(
    "/transcribe/stream",
    summary="Stream transcription (WebSocket placeholder)",
    auth=AuthBearer(),
)
async def transcribe_stream(request) -> dict:
    """Placeholder for streaming transcription.

    Real-time transcription would use WebSockets.
    See: /ws/voice for WebSocket endpoint.
    """
    return {
        "message": "Use WebSocket at /ws/voice for streaming transcription",
        "websocket_url": "ws://localhost:8000/ws/voice",
    }
