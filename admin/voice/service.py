"""High‑level orchestration service for the voice subsystem.

The :class:`VoiceService` class glues together the capture, provider client,
adapter and speaker components.  It also records metrics and tracing spans.
All heavy‑weight objects are created lazily in ``__init__`` so that importing the
module has no side effects (

Typical usage inside a Django Ninja endpoint::

    async def voice_endpoint():
        service = VoiceService(config)
        await service.start()
        # ``run`` blocks until the capture generator finishes (e.g., client
        # disconnects).  In a real implementation the endpoint would stream
        # data back to the client.
        await service.run()

The implementation below is intentionally minimal – it provides the required
public API while delegating the actual audio handling to the previously defined
modules.
"""

from __future__ import annotations

import base64
import logging
from typing import Awaitable, Optional, TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:
    from admin.core.helpers.config import Config
    from admin.llm.models import LLMModelConfig
    from admin.voice.models import VoiceModel, VoicePersona, VoiceSession  # type: ignore[import]

import httpx
from django.conf import settings
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone

from admin.common.exceptions import BadRequestError, ServiceUnavailableError
from admin.common.messages import get_message, SuccessCode
from admin.voice.schemas import (
    LLMConfigListOut,
    LLMConfigOut,
    SynthesizeRequest,
    SynthesizeResponse,
    TranscribeRequest,
    TranscribeResponse,
    VoiceListResponse,
    VoiceModelListOut,
    VoiceModelOut,
    VoicePersonaCreate,
    VoicePersonaListOut,
    VoicePersonaOut,
    VoicePersonaUpdate,
    VoiceSessionListOut,
    VoiceSessionOut,
    VoiceSessionStats,
    VoiceStatusResponse,
)

from .audio_capture import AudioCapture
from .metrics import record_error, VOICE_SESSION_DURATION_SECONDS, VOICE_SESSIONS_TOTAL
from .provider_selector import _BaseClient, get_provider_client
from .speaker import Speaker
from .tracing import span
from .voice_adapter import VoiceAdapter

logger = logging.getLogger(__name__)

WHISPER_URL = getattr(settings, "WHISPER_URL", "http://localhost:9100")
KOKORO_URL = getattr(settings, "KOKORO_URL", "http://localhost:9200")
MAX_AUDIO_SIZE = 10 * 1024 * 1024  # 10MB

_voice_models: tuple[type, type, type] | None = None


def _get_voice_models() -> tuple[type, type, type]:
    """Lazy import voice models to avoid AppRegistryNotReady during app loading."""
    global _voice_models
    if _voice_models is None:
        from admin.voice.models import VoiceModel, VoicePersona, VoiceSession

        _voice_models = (VoiceModel, VoicePersona, VoiceSession)
    return _voice_models


class VoiceService:
    """Orchestrates a single voice interaction session.

    Parameters
    ----------
    config:
        Global configuration object from which the voice settings are derived.
    """

    def __init__(self, config: Config) -> None:
        """Initialize the instance."""

        self._config = config
        self._capture: AudioCapture | None = None
        self._speaker: Speaker | None = None
        self._client: _BaseClient | None = None
        self._adapter: VoiceAdapter | None = None
        self._session_task: Awaitable[None] | None = None

    def _setup_components(self) -> None:
        """Instantiate all low‑level components.

        This method is called lazily the first time the service is started.
        """
        voice_cfg = self._config.voice
        self._capture = AudioCapture(voice_cfg.audio)
        self._speaker = Speaker(voice_cfg.audio)
        self._client = get_provider_client(self._config)
        assert self._capture and self._speaker and self._client  # for mypy
        self._adapter = VoiceAdapter(self._capture, self._client, self._speaker)

    async def start(self) -> None:
        """Prepare the service and record metrics.

        This method must be called before ``run``.  It increments the session
        counter and creates the component instances.
        """
        VOICE_SESSIONS_TOTAL.inc()
        self._setup_components()

    async def run(self) -> None:
        """Execute the full audio pipeline.

        The method records a duration histogram and ensures any raised errors are
        accounted for in the ``VOICE_ERRORS_TOTAL`` metric.
        """
        if not self._adapter:
            raise RuntimeError("VoiceService.start() must be called before run()")
        with span("voice_session") as end_span:
            with VOICE_SESSION_DURATION_SECONDS.time():
                try:
                    await self._adapter.run()
                except Exception as exc:  # pragma: no cover – defensive
                    record_error("adapter")
                    raise
                finally:
                    # Ensure the span is closed even on error.
                    end_span()


# =============================================================================
# VOICE SERVICE HELPERS FOR API ENDPOINTS
# =============================================================================


def _persona_to_out(persona: VoicePersona) -> VoicePersonaOut:
    """Map a VoicePersona ORM instance to its API schema."""
    VoiceModel, VoicePersona, VoiceSession = _get_voice_models()
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


def _session_to_out(session: VoiceSession) -> VoiceSessionOut:
    """Map a VoiceSession ORM instance to its API schema."""
    VoiceModel, VoicePersona, VoiceSession = _get_voice_models()
    return VoiceSessionOut(
        id=session.id,
        tenant_id=session.tenant_id,
        persona_id=session.persona_id,
        persona_name=session.persona.name if session.persona else None,
        user_id=session.user_id,
        status=session.status,
        duration_seconds=float(session.duration_seconds),
        input_tokens=session.input_tokens,
        output_tokens=session.output_tokens,
        audio_seconds=float(session.audio_seconds),
        turn_count=session.turn_count,
        created_at=session.created_at,
        ended_at=session.ended_at,
    )


def _voice_model_to_out(model: VoiceModel) -> VoiceModelOut:
    """Map a VoiceModel ORM instance to its API schema."""
    VoiceModel, VoicePersona, VoiceSession = _get_voice_models()
    return VoiceModelOut(
        id=model.id,
        name=model.name,
        provider=model.provider,
        voice_id=model.voice_id,
        language=model.language,
        gender=model.gender,
        description=model.description,
        is_active=model.is_active,
        is_default=model.is_default,
    )


def _llm_config_to_out(config: LLMModelConfig) -> LLMConfigOut:
    """Map an LLMModelConfig ORM instance to its API schema."""

    return LLMConfigOut(
        id=config.id,
        name=config.name,
        display_name=config.display_name or config.name,
        provider=config.provider,
        model_type=config.model_type,
        is_active=config.is_active,
    )


async def transcribe_audio(payload: TranscribeRequest) -> TranscribeResponse:
    """Transcribe audio to text using Whisper."""
    try:
        audio_bytes = base64.b64decode(payload.audio_base64)
    except Exception:
        raise BadRequestError("Invalid base64 audio data")

    if len(audio_bytes) > MAX_AUDIO_SIZE:
        raise BadRequestError(f"Audio exceeds maximum size of {MAX_AUDIO_SIZE // 1024 // 1024}MB")

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
                logger.error("Whisper error: %s", response.status_code)
                raise ServiceUnavailableError("whisper", "Transcription service unavailable")

    except httpx.HTTPError as e:
        logger.error("Whisper connection error: %s", e)
        raise ServiceUnavailableError(
            "whisper", "Whisper unavailable - use browser Speech API as fallback"
        )


async def synthesize_speech(payload: SynthesizeRequest) -> SynthesizeResponse:
    """Synthesize text to speech using Kokoro TTS."""
    if len(payload.text) > 5000:
        raise BadRequestError("Text exceeds maximum length of 5000 characters")

    if not 0.5 <= payload.speed <= 2.0:
        raise BadRequestError("Speed must be between 0.5 and 2.0")

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

                word_count = len(payload.text.split())
                duration = (word_count / 150) * 60 / payload.speed

                return SynthesizeResponse(
                    audio_base64=audio_base64,
                    format=payload.format,
                    duration_seconds=duration,
                    voice_used=payload.voice,
                )
            else:
                logger.error("Kokoro error: %s", response.status_code)
                raise ServiceUnavailableError("kokoro", "TTS service unavailable")

    except httpx.HTTPError as e:
        logger.error("Kokoro connection error: %s", e)
        raise ServiceUnavailableError(
            "kokoro", "Kokoro TTS unavailable - use browser Speech Synthesis as fallback"
        )


async def list_voices() -> VoiceListResponse:
    """List available TTS voices, including browser fallback voices."""
    voices: list[dict] = []

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{KOKORO_URL}/voices")
            if response.status_code == 200:
                voices.extend(response.json().get("voices", []))
    except Exception:
        pass

    voices.extend(
        [
            {"id": "browser_default", "name": "Browser Default", "provider": "browser"},
            {"id": "browser_male", "name": "Browser Male", "provider": "browser"},
            {"id": "browser_female", "name": "Browser Female", "provider": "browser"},
        ]
    )

    return VoiceListResponse(voices=voices)


async def get_voice_status() -> VoiceStatusResponse:
    """Check the health of the Whisper and Kokoro voice services."""
    whisper_status = "down"
    kokoro_status = "down"

    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get(f"{WHISPER_URL}/health")
            if response.status_code == 200:
                whisper_status = "healthy"
    except Exception:
        pass

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
        fallback_available=True,
    )


def list_llm_configs(model_type: str = "chat") -> LLMConfigListOut:
    """List active LLMModelConfig entries for persona LLM selection."""
    from admin.llm.models import LLMModelConfig

    queryset = LLMModelConfig.objects.filter(is_active=True)
    if model_type:
        queryset = queryset.filter(model_type=model_type)

    items = [_llm_config_to_out(m) for m in queryset.order_by("provider", "name")]
    return LLMConfigListOut(items=items, total=len(items))


def list_personas(
    tenant_id: str,
    page: int = 1,
    page_size: int = 20,
    active_only: bool = False,
) -> VoicePersonaListOut:
    """List voice personas for the given tenant."""
    VoiceModel, VoicePersona, VoiceSession = _get_voice_models()
    queryset = VoicePersona.objects.filter(tenant_id=tenant_id)
    if active_only:
        queryset = queryset.filter(is_active=True)

    total = queryset.count()
    offset = (page - 1) * page_size
    personas = queryset.order_by("-created_at")[offset : offset + page_size]

    items = [_persona_to_out(p) for p in personas]
    return VoicePersonaListOut(items=items, total=total, page=page, page_size=page_size)


def create_persona(tenant_id: str, payload: VoicePersonaCreate) -> VoicePersonaOut:
    """Create a new voice persona for the given tenant."""
    VoiceModel, VoicePersona, VoiceSession = _get_voice_models()
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
    return _persona_to_out(persona)


def get_persona(tenant_id: str, persona_id: UUID) -> VoicePersonaOut:
    """Return a specific voice persona by ID."""
    VoiceModel, VoicePersona, VoiceSession = _get_voice_models()
    persona = get_object_or_404(VoicePersona, id=persona_id, tenant_id=tenant_id)
    return _persona_to_out(persona)


def update_persona(
    tenant_id: str,
    persona_id: UUID,
    payload: VoicePersonaUpdate,
) -> VoicePersonaOut:
    """Update a voice persona."""
    VoiceModel, VoicePersona, VoiceSession = _get_voice_models()
    persona = get_object_or_404(VoicePersona, id=persona_id, tenant_id=tenant_id)

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(persona, field, value)
    persona.save()

    return _persona_to_out(persona)


def delete_persona(tenant_id: str, persona_id: UUID) -> dict:
    """Delete a voice persona."""
    VoiceModel, VoicePersona, VoiceSession = _get_voice_models()
    persona = get_object_or_404(VoicePersona, id=persona_id, tenant_id=tenant_id)
    persona.delete()
    return {
        "success": True,
        "message": get_message(SuccessCode.PERSONA_DELETED, persona_id=str(persona_id)),
    }


def set_persona_default(tenant_id: str, persona_id: UUID) -> dict:
    """Set a persona as the default for the tenant."""
    VoiceModel, VoicePersona, VoiceSession = _get_voice_models()
    VoicePersona.objects.filter(tenant_id=tenant_id, is_default=True).update(is_default=False)

    persona = get_object_or_404(VoicePersona, id=persona_id, tenant_id=tenant_id)
    persona.is_default = True
    persona.save()

    return {
        "success": True,
        "message": get_message(SuccessCode.PERSONA_SET_DEFAULT, name=persona.name),
    }


def list_sessions(
    tenant_id: str,
    page: int = 1,
    page_size: int = 50,
    status: Optional[str] = None,
) -> VoiceSessionListOut:
    """List voice sessions for the given tenant."""
    VoiceModel, VoicePersona, VoiceSession = _get_voice_models()
    queryset = VoiceSession.objects.filter(tenant_id=tenant_id)
    if status:
        queryset = queryset.filter(status=status)

    total = queryset.count()
    offset = (page - 1) * page_size
    sessions = queryset.select_related("persona").order_by("-created_at")[
        offset : offset + page_size
    ]

    items = [_session_to_out(s) for s in sessions]
    return VoiceSessionListOut(items=items, total=total, page=page, page_size=page_size)


def get_session_stats(tenant_id: str) -> VoiceSessionStats:
    """Get aggregated session statistics for the given tenant."""
    VoiceModel, VoicePersona, VoiceSession = _get_voice_models()
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


def terminate_session(tenant_id: str, session_id: UUID) -> dict:
    """Terminate an active voice session."""
    VoiceModel, VoicePersona, VoiceSession = _get_voice_models()
    session = get_object_or_404(VoiceSession, id=session_id, tenant_id=tenant_id)

    if session.status != "active":
        raise BadRequestError(f"Session is not active (status: {session.status})")

    session.status = "terminated"
    session.ended_at = timezone.now()
    session.save()

    return {
        "success": True,
        "message": get_message(SuccessCode.SESSION_TERMINATED, session_id=str(session_id)),
    }


def list_voice_models(active_only: bool = True) -> VoiceModelListOut:
    """List available TTS voice models."""
    VoiceModel, VoicePersona, VoiceSession = _get_voice_models()
    queryset = VoiceModel.objects.all()
    if active_only:
        queryset = queryset.filter(is_active=True)

    models = queryset.order_by("provider", "name")
    items = [_voice_model_to_out(m) for m in models]
    return VoiceModelListOut(items=items, total=len(items))
