"""Voice API - Speech-to-Text and Text-to-Speech.


Per CANONICAL_USER_JOURNEYS_SRS.md UC-04: Voice Chat.

- PhD Dev: Proper audio encoding, streaming
- Security Auditor: File size limits, content validation
- Django Architect: Async patterns, proper error handling
- DevOps: Integration with Whisper/Kokoro services
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from ninja import Router

from admin.common.auth import AuthBearer
from admin.common.exceptions import ServiceUnavailableError
from admin.voice.schemas import (
    LLMConfigListOut,
    SynthesizeRequest,
    SynthesizeResponse,
    TranscribeRequest,
    TranscribeResponse,
    VoiceListResponse,
    VoiceModelListOut,
    VoicePersonaCreate,
    VoicePersonaListOut,
    VoicePersonaOut,
    VoicePersonaUpdate,
    VoiceSessionListOut,
    VoiceSessionStats,
    VoiceStatusResponse,
)
from admin.voice.service import (
    create_persona,
    delete_persona,
    get_persona,
    get_session_stats,
    get_voice_status,
    list_llm_configs,
    list_personas,
    list_sessions,
    list_voice_models,
    list_voices,
    set_persona_default,
    synthesize_speech,
    terminate_session,
    transcribe_audio,
    update_persona,
)

router = Router(tags=["voice"])


def _tenant_id(request) -> str:
    """Extract tenant identifier from the incoming request."""
    return getattr(request, "tenant_id", "default")


# =============================================================================
# SPEECH ENDPOINTS
# =============================================================================


@router.post(
    "/transcribe",
    response=TranscribeResponse,
    summary="Transcribe audio to text",
    auth=AuthBearer(),
)
async def transcribe_endpoint(request, payload: TranscribeRequest) -> TranscribeResponse:
    """Transcribe audio to text using Whisper.

    Per SRS UC-04: POST /api/v2/voice/transcribe


    - Real Whisper integration
    - Fallback to browser API if unavailable
    - Size and format validation
    """
    return await transcribe_audio(payload)


@router.post(
    "/synthesize",
    response=SynthesizeResponse,
    summary="Synthesize text to speech",
    auth=AuthBearer(),
)
async def synthesize_endpoint(request, payload: SynthesizeRequest) -> SynthesizeResponse:
    """Synthesize text to speech using Kokoro TTS.

    Per SRS UC-04: POST /api/v2/voice/synthesize


    - Real Kokoro TTS integration
    - Fallback to browser API if unavailable
    - Multiple voice options
    """
    return await synthesize_speech(payload)


@router.get(
    "/voices",
    response=VoiceListResponse,
    summary="List available voices",
    auth=AuthBearer(),
)
async def voices_endpoint(request) -> VoiceListResponse:
    """List available TTS voices."""
    return await list_voices()


@router.get(
    "/status",
    response=VoiceStatusResponse,
    summary="Get voice service status",
)
async def status_endpoint(request) -> VoiceStatusResponse:
    """Check status of voice services."""
    return await get_voice_status()


@router.post(
    "/transcribe/stream",
    summary="Stream real-time audio transcription",
    auth=AuthBearer(),
)
async def transcribe_stream(request) -> dict:
    """Stream real-time audio transcription via WebSocket.

    This endpoint is the REST-side declaration of the streaming transcription
    capability. Real-time audio streaming requires a Django Channels WebSocket
    consumer, which is not yet implemented.

    Raises:
        ServiceUnavailableError: Always — streaming transcription requires
            a WebSocket consumer (Django Channels) that is not yet wired.
            Do not implement this endpoint as a REST redirect; callers
            must be told the truth.
    """
    raise ServiceUnavailableError(
        "voice_stream",
        "Real-time streaming transcription requires Django Channels WebSocket support, "
        "which is not yet implemented. Use POST /voice/transcribe for single-shot transcription.",
    )


# =============================================================================
# VOICE PERSONA CRUD ENDPOINTS
# =============================================================================


@router.get(
    "/llm-configs",
    response=LLMConfigListOut,
    summary="List active LLM configurations",
    auth=AuthBearer(),
)
def list_llm_configs_endpoint(request, model_type: str = "chat"):
    """List active LLMModelConfig entries for persona LLM selection."""
    return list_llm_configs(model_type=model_type)


@router.get(
    "/personas",
    response=VoicePersonaListOut,
    summary="List voice personas",
    auth=AuthBearer(),
)
def list_personas_endpoint(
    request,
    page: int = 1,
    page_size: int = 20,
    active_only: bool = False,
):
    """List voice personas for the current tenant."""
    return list_personas(
        tenant_id=_tenant_id(request),
        page=page,
        page_size=page_size,
        active_only=active_only,
    )


@router.post(
    "/personas",
    response=VoicePersonaOut,
    summary="Create voice persona",
    auth=AuthBearer(),
)
def create_persona_endpoint(request, payload: VoicePersonaCreate):
    """Create a new voice persona."""
    return create_persona(tenant_id=_tenant_id(request), payload=payload)


@router.get(
    "/personas/{persona_id}",
    response=VoicePersonaOut,
    summary="Get voice persona",
    auth=AuthBearer(),
)
def get_persona_endpoint(request, persona_id: UUID):
    """Get a specific voice persona by ID."""
    return get_persona(tenant_id=_tenant_id(request), persona_id=persona_id)


@router.put(
    "/personas/{persona_id}",
    response=VoicePersonaOut,
    summary="Update voice persona",
    auth=AuthBearer(),
)
def update_persona_endpoint(request, persona_id: UUID, payload: VoicePersonaUpdate):
    """Update a voice persona."""
    return update_persona(
        tenant_id=_tenant_id(request),
        persona_id=persona_id,
        payload=payload,
    )


@router.delete(
    "/personas/{persona_id}",
    summary="Delete voice persona",
    auth=AuthBearer(),
)
def delete_persona_endpoint(request, persona_id: UUID):
    """Delete a voice persona."""
    return delete_persona(tenant_id=_tenant_id(request), persona_id=persona_id)


@router.post(
    "/personas/{persona_id}/set-default",
    summary="Set persona as default",
    auth=AuthBearer(),
)
def set_persona_default_endpoint(request, persona_id: UUID):
    """Set a persona as the default for the tenant."""
    return set_persona_default(tenant_id=_tenant_id(request), persona_id=persona_id)


# =============================================================================
# VOICE SESSION ENDPOINTS
# =============================================================================


@router.get(
    "/sessions",
    response=VoiceSessionListOut,
    summary="List voice sessions",
    auth=AuthBearer(),
)
def list_sessions_endpoint(
    request,
    page: int = 1,
    page_size: int = 50,
    status: Optional[str] = None,
):
    """List voice sessions for the current tenant."""
    return list_sessions(
        tenant_id=_tenant_id(request),
        page=page,
        page_size=page_size,
        status=status,
    )


@router.get(
    "/sessions/stats",
    response=VoiceSessionStats,
    summary="Get session stats",
    auth=AuthBearer(),
)
def get_session_stats_endpoint(request):
    """Get aggregated session statistics."""
    return get_session_stats(tenant_id=_tenant_id(request))


@router.post(
    "/sessions/{session_id}/terminate",
    summary="Terminate voice session",
    auth=AuthBearer(),
)
def terminate_session_endpoint(request, session_id: UUID):
    """Terminate an active voice session."""
    return terminate_session(tenant_id=_tenant_id(request), session_id=session_id)


# =============================================================================
# VOICE MODEL ENDPOINTS
# =============================================================================


@router.get(
    "/models",
    response=VoiceModelListOut,
    summary="List TTS voice models",
    auth=AuthBearer(),
)
def list_voice_models_endpoint(request, active_only: bool = True):
    """List available TTS voice models."""
    return list_voice_models(active_only=active_only)
