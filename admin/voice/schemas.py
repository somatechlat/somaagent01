"""Voice API Schemas - Pydantic models for API."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# =============================================================================
# TRANSCRIPTION SCHEMAS (STT/TTS)
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
# VOICE PERSONA SCHEMAS
# =============================================================================


class VoicePersonaBase(BaseModel):
    """Base schema for VoicePersona."""

    name: str = Field(..., description="Persona display name")
    description: str = Field("", description="Persona description")
    voice_id: str = Field("af_heart", description="TTS voice ID")
    voice_speed: float = Field(1.0, ge=0.5, le=2.0, description="Speech speed")
    stt_model: str = Field("whisper-1", description="STT model")
    stt_language: str = Field("en", description="STT language code")
    system_prompt: str = Field("", description="System prompt for LLM")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="LLM temperature")
    max_tokens: int = Field(1024, ge=1, le=32000, description="Max response tokens")
    turn_detection_enabled: bool = Field(True, description="Enable VAD")
    turn_detection_threshold: float = Field(0.5, ge=0.0, le=1.0)
    silence_duration_ms: int = Field(500, ge=100, le=3000)


class VoicePersonaCreate(VoicePersonaBase):
    """Schema for creating a VoicePersona."""

    llm_config_id: Optional[UUID] = Field(None, description="LLM config FK")


class VoicePersonaUpdate(BaseModel):
    """Schema for updating a VoicePersona."""

    name: Optional[str] = None
    description: Optional[str] = None
    voice_id: Optional[str] = None
    voice_speed: Optional[float] = None
    stt_model: Optional[str] = None
    stt_language: Optional[str] = None
    llm_config_id: Optional[UUID] = None
    system_prompt: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    turn_detection_enabled: Optional[bool] = None
    turn_detection_threshold: Optional[float] = None
    silence_duration_ms: Optional[int] = None
    is_active: Optional[bool] = None


class VoicePersonaOut(VoicePersonaBase):
    """Schema for VoicePersona response."""

    id: UUID
    tenant_id: str
    llm_config_id: Optional[UUID] = None
    llm_config_name: Optional[str] = None
    is_active: bool
    is_default: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        """Config class implementation."""

        from_attributes = True


class VoicePersonaListOut(BaseModel):
    """Paginated list of personas."""

    items: list[VoicePersonaOut]
    total: int
    page: int
    page_size: int


# =============================================================================
# VOICE SESSION SCHEMAS
# =============================================================================


class VoiceSessionOut(BaseModel):
    """Schema for VoiceSession response."""

    id: UUID
    tenant_id: str
    persona_id: Optional[UUID] = None
    persona_name: Optional[str] = None
    user_id: Optional[str] = None
    status: str
    duration_seconds: float
    input_tokens: int
    output_tokens: int
    audio_seconds: float
    turn_count: int
    created_at: datetime
    ended_at: Optional[datetime] = None

    class Config:
        """Config class implementation."""

        from_attributes = True


class VoiceSessionListOut(BaseModel):
    """Paginated list of sessions."""

    items: list[VoiceSessionOut]
    total: int
    page: int
    page_size: int


class VoiceSessionStats(BaseModel):
    """Aggregated session stats."""

    active_count: int
    total_count: int
    total_tokens: int
    total_audio_seconds: float


# =============================================================================
# VOICE MODEL SCHEMAS
# =============================================================================


class VoiceModelOut(BaseModel):
    """Schema for VoiceModel (TTS voices)."""

    id: UUID
    name: str
    provider: str
    voice_id: str
    language: str
    gender: str
    description: str
    is_active: bool
    is_default: bool

    class Config:
        """Config class implementation."""

        from_attributes = True


class VoiceModelListOut(BaseModel):
    """List of voice models."""

    items: list[VoiceModelOut]
    total: int
