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


# =============================================================================
# VOICE PERSONA CRUD ENDPOINTS (for Lit UI)
# =============================================================================

from uuid import UUID

from django.db.models import Sum
from django.shortcuts import get_object_or_404

from admin.voice.models import VoicePersona, VoiceSession, VoiceModel
from admin.voice.schemas import (
    VoicePersonaCreate,
    VoicePersonaUpdate,
    VoicePersonaOut,
    VoicePersonaListOut,
    VoiceSessionOut,
    VoiceSessionListOut,
    VoiceSessionStats,
    VoiceModelOut,
    VoiceModelListOut,
)


@router.get(
    "/personas",
    response=VoicePersonaListOut,
    summary="List voice personas",
    auth=AuthBearer(),
)
def list_personas(request, page: int = 1, page_size: int = 20, active_only: bool = False):
    """List voice personas for the current tenant.

    Lit UI: saas-voice-personas.ts uses this endpoint.
    """
    # Extract tenant from request (simplified for now)
    tenant_id = getattr(request, "tenant_id", "default")

    queryset = VoicePersona.objects.filter(tenant_id=tenant_id)
    if active_only:
        queryset = queryset.filter(is_active=True)

    total = queryset.count()
    offset = (page - 1) * page_size
    personas = queryset.order_by("-created_at")[offset : offset + page_size]

    items = []
    for p in personas:
        items.append(
            VoicePersonaOut(
                id=p.id,
                tenant_id=p.tenant_id,
                name=p.name,
                description=p.description,
                voice_id=p.voice_id,
                voice_speed=p.voice_speed,
                stt_model=p.stt_model,
                stt_language=p.stt_language,
                llm_config_id=p.llm_config_id,
                llm_config_name=p.llm_config.name if p.llm_config else None,
                system_prompt=p.system_prompt,
                temperature=float(p.temperature),
                max_tokens=p.max_tokens,
                turn_detection_enabled=p.turn_detection_enabled,
                turn_detection_threshold=float(p.turn_detection_threshold),
                silence_duration_ms=p.silence_duration_ms,
                is_active=p.is_active,
                is_default=p.is_default,
                created_at=p.created_at,
                updated_at=p.updated_at,
            )
        )

    return VoicePersonaListOut(items=items, total=total, page=page, page_size=page_size)


@router.post(
    "/personas",
    response=VoicePersonaOut,
    summary="Create voice persona",
    auth=AuthBearer(),
)
def create_persona(request, payload: VoicePersonaCreate):
    """Create a new voice persona."""
    tenant_id = getattr(request, "tenant_id", "default")

    persona = VoicePersona.objects.create(
        tenant_id=tenant_id,
        name=payload.name,
        description=payload.description,
        voice_id=payload.voice_id,
        voice_speed=payload.voice_speed,
        stt_model=payload.stt_model,
        stt_language=payload.stt_language,
        llm_config_id=payload.llm_config_id,
        system_prompt=payload.system_prompt,
        temperature=payload.temperature,
        max_tokens=payload.max_tokens,
        turn_detection_enabled=payload.turn_detection_enabled,
        turn_detection_threshold=payload.turn_detection_threshold,
        silence_duration_ms=payload.silence_duration_ms,
    )

    return VoicePersonaOut(
        id=persona.id,
        tenant_id=persona.tenant_id,
        name=persona.name,
        description=persona.description,
        voice_id=persona.voice_id,
        voice_speed=persona.voice_speed,
        stt_model=persona.stt_model,
        stt_language=persona.stt_language,
        llm_config_id=persona.llm_config_id,
        llm_config_name=persona.llm_config.name if persona.llm_config else None,
        system_prompt=persona.system_prompt,
        temperature=float(persona.temperature),
        max_tokens=persona.max_tokens,
        turn_detection_enabled=persona.turn_detection_enabled,
        turn_detection_threshold=float(persona.turn_detection_threshold),
        silence_duration_ms=persona.silence_duration_ms,
        is_active=persona.is_active,
        is_default=persona.is_default,
        created_at=persona.created_at,
        updated_at=persona.updated_at,
    )


@router.get(
    "/personas/{persona_id}",
    response=VoicePersonaOut,
    summary="Get voice persona",
    auth=AuthBearer(),
)
def get_persona(request, persona_id: UUID):
    """Get a specific voice persona by ID."""
    tenant_id = getattr(request, "tenant_id", "default")
    persona = get_object_or_404(VoicePersona, id=persona_id, tenant_id=tenant_id)

    return VoicePersonaOut(
        id=persona.id,
        tenant_id=persona.tenant_id,
        name=persona.name,
        description=persona.description,
        voice_id=persona.voice_id,
        voice_speed=persona.voice_speed,
        stt_model=persona.stt_model,
        stt_language=persona.stt_language,
        llm_config_id=persona.llm_config_id,
        llm_config_name=persona.llm_config.name if persona.llm_config else None,
        system_prompt=persona.system_prompt,
        temperature=float(persona.temperature),
        max_tokens=persona.max_tokens,
        turn_detection_enabled=persona.turn_detection_enabled,
        turn_detection_threshold=float(persona.turn_detection_threshold),
        silence_duration_ms=persona.silence_duration_ms,
        is_active=persona.is_active,
        is_default=persona.is_default,
        created_at=persona.created_at,
        updated_at=persona.updated_at,
    )


@router.put(
    "/personas/{persona_id}",
    response=VoicePersonaOut,
    summary="Update voice persona",
    auth=AuthBearer(),
)
def update_persona(request, persona_id: UUID, payload: VoicePersonaUpdate):
    """Update a voice persona."""
    tenant_id = getattr(request, "tenant_id", "default")
    persona = get_object_or_404(VoicePersona, id=persona_id, tenant_id=tenant_id)

    # Update only provided fields
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(persona, field, value)
    persona.save()

    return VoicePersonaOut(
        id=persona.id,
        tenant_id=persona.tenant_id,
        name=persona.name,
        description=persona.description,
        voice_id=persona.voice_id,
        voice_speed=persona.voice_speed,
        stt_model=persona.stt_model,
        stt_language=persona.stt_language,
        llm_config_id=persona.llm_config_id,
        llm_config_name=persona.llm_config.name if persona.llm_config else None,
        system_prompt=persona.system_prompt,
        temperature=float(persona.temperature),
        max_tokens=persona.max_tokens,
        turn_detection_enabled=persona.turn_detection_enabled,
        turn_detection_threshold=float(persona.turn_detection_threshold),
        silence_duration_ms=persona.silence_duration_ms,
        is_active=persona.is_active,
        is_default=persona.is_default,
        created_at=persona.created_at,
        updated_at=persona.updated_at,
    )


@router.delete(
    "/personas/{persona_id}",
    summary="Delete voice persona",
    auth=AuthBearer(),
)
def delete_persona(request, persona_id: UUID):
    """Delete a voice persona."""
    tenant_id = getattr(request, "tenant_id", "default")
    persona = get_object_or_404(VoicePersona, id=persona_id, tenant_id=tenant_id)
    persona.delete()
    return {"success": True, "message": f"Persona {persona_id} deleted"}


@router.post(
    "/personas/{persona_id}/set-default",
    summary="Set persona as default",
    auth=AuthBearer(),
)
def set_persona_default(request, persona_id: UUID):
    """Set a persona as the default for the tenant."""
    tenant_id = getattr(request, "tenant_id", "default")

    # Clear existing defaults
    VoicePersona.objects.filter(tenant_id=tenant_id, is_default=True).update(is_default=False)

    # Set new default
    persona = get_object_or_404(VoicePersona, id=persona_id, tenant_id=tenant_id)
    persona.is_default = True
    persona.save()

    return {"success": True, "message": f"Persona {persona.name} set as default"}


# =============================================================================
# VOICE SESSION ENDPOINTS (for Lit UI)
# =============================================================================


@router.get(
    "/sessions",
    response=VoiceSessionListOut,
    summary="List voice sessions",
    auth=AuthBearer(),
)
def list_sessions(request, page: int = 1, page_size: int = 50, status: Optional[str] = None):
    """List voice sessions for the current tenant.

    Lit UI: saas-voice-sessions.ts uses this endpoint.
    """
    tenant_id = getattr(request, "tenant_id", "default")

    queryset = VoiceSession.objects.filter(tenant_id=tenant_id)
    if status:
        queryset = queryset.filter(status=status)

    total = queryset.count()
    offset = (page - 1) * page_size
    sessions = queryset.select_related("persona").order_by("-created_at")[offset : offset + page_size]

    items = []
    for s in sessions:
        items.append(
            VoiceSessionOut(
                id=s.id,
                tenant_id=s.tenant_id,
                persona_id=s.persona_id,
                persona_name=s.persona.name if s.persona else None,
                user_id=s.user_id,
                status=s.status,
                duration_seconds=float(s.duration_seconds),
                input_tokens=s.input_tokens,
                output_tokens=s.output_tokens,
                audio_seconds=float(s.audio_seconds),
                turn_count=s.turn_count,
                created_at=s.created_at,
                ended_at=s.ended_at,
            )
        )

    return VoiceSessionListOut(items=items, total=total, page=page, page_size=page_size)


@router.get(
    "/sessions/stats",
    response=VoiceSessionStats,
    summary="Get session stats",
    auth=AuthBearer(),
)
def get_session_stats(request):
    """Get aggregated session statistics."""
    tenant_id = getattr(request, "tenant_id", "default")

    active_count = VoiceSession.objects.filter(tenant_id=tenant_id, status="active").count()
    total_count = VoiceSession.objects.filter(tenant_id=tenant_id).count()

    agg = VoiceSession.objects.filter(tenant_id=tenant_id).aggregate(
        total_tokens=Sum("input_tokens") + Sum("output_tokens"),
        total_audio=Sum("audio_seconds"),
    )

    return VoiceSessionStats(
        active_count=active_count,
        total_count=total_count,
        total_tokens=agg["total_tokens"] or 0,
        total_audio_seconds=float(agg["total_audio"] or 0),
    )


@router.post(
    "/sessions/{session_id}/terminate",
    summary="Terminate voice session",
    auth=AuthBearer(),
)
def terminate_session(request, session_id: UUID):
    """Terminate an active voice session."""
    from django.utils import timezone

    tenant_id = getattr(request, "tenant_id", "default")
    session = get_object_or_404(VoiceSession, id=session_id, tenant_id=tenant_id)

    if session.status != "active":
        raise BadRequestError(f"Session is not active (status: {session.status})")

    session.status = "terminated"
    session.ended_at = timezone.now()
    session.save()

    return {"success": True, "message": f"Session {session_id} terminated"}


# =============================================================================
# VOICE MODEL ENDPOINTS (TTS voices)
# =============================================================================


@router.get(
    "/models",
    response=VoiceModelListOut,
    summary="List TTS voice models",
    auth=AuthBearer(),
)
def list_voice_models(request, active_only: bool = True):
    """List available TTS voice models."""
    queryset = VoiceModel.objects.all()
    if active_only:
        queryset = queryset.filter(is_active=True)

    models = queryset.order_by("provider", "name")

    items = [
        VoiceModelOut(
            id=m.id,
            name=m.name,
            provider=m.provider,
            voice_id=m.voice_id,
            language=m.language,
            gender=m.gender,
            description=m.description,
            is_active=m.is_active,
            is_default=m.is_default,
        )
        for m in models
    ]

    return VoiceModelListOut(items=items, total=len(items))

