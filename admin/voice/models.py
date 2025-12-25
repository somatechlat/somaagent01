"""Voice Django ORM Models.

VIBE COMPLIANT - 100% Django ORM.
AgentVoice Vox integration for voice personas, sessions, and models.

Per SRS Section 6: VoicePersona, VoiceSession, VoiceModel
References existing LLMModelConfig - NO duplicate model creation.
"""

import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone

# Reference existing LLM model - NO DUPLICATION
from admin.llm.models import LLMModelConfig


# =============================================================================
# CONFIGURATION (from Django settings)
# =============================================================================


def get_voicevox_base_url() -> str:
    """Get AgentVoiceVox base URL from settings."""
    return getattr(settings, "AGENTVOICEVOX_BASE_URL", "http://localhost:65009")


# =============================================================================
# ABSTRACT BASE (reuse pattern from permissions)
# =============================================================================


class TimestampedModel(models.Model):
    """Abstract base with timestamps."""

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class TenantScopedModel(TimestampedModel):
    """Abstract base with tenant isolation."""

    tenant_id = models.UUIDField(
        db_index=True,
        help_text="Tenant ID for multi-tenancy isolation",
    )

    class Meta:
        abstract = True


# =============================================================================
# VOICE PERSONA
# =============================================================================


class VoicePersona(TenantScopedModel):
    """Voice persona for tenant.

    Configures STT, TTS, LLM for a specific agent personality.
    References existing LLMModelConfig - NO duplicate model creation.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    # Voice Settings (TTS)
    voice_id = models.CharField(
        max_length=50,
        default="af_heart",
        help_text="Kokoro voice ID",
    )
    voice_speed = models.FloatField(default=1.0)

    # STT Settings
    stt_model = models.CharField(
        max_length=50,
        default="tiny",
        choices=[
            ("tiny", "Whisper Tiny"),
            ("small", "Whisper Small"),
            ("medium", "Whisper Medium"),
            ("large", "Whisper Large"),
        ],
    )
    stt_language = models.CharField(max_length=10, default="en")

    # LLM Reference - ForeignKey to existing model (NO DUPLICATION)
    llm_config = models.ForeignKey(
        LLMModelConfig,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="voice_personas",
        help_text="Reference to existing LLM model configuration",
    )

    # System prompt (persona-specific)
    system_prompt = models.TextField(blank=True)
    temperature = models.FloatField(default=0.7)
    max_tokens = models.IntegerField(default=1024)

    # Turn Detection (VAD)
    turn_detection_enabled = models.BooleanField(default=True)
    turn_detection_threshold = models.FloatField(default=0.5)
    silence_duration_ms = models.IntegerField(default=500)

    # State
    is_active = models.BooleanField(default=True, db_index=True)
    is_default = models.BooleanField(default=False)

    class Meta:
        db_table = "voice_personas"
        unique_together = [["tenant_id", "name"]]
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["tenant_id", "is_active"]),
            models.Index(fields=["is_default"]),
        ]
        verbose_name = "Voice Persona"
        verbose_name_plural = "Voice Personas"

    def __str__(self):
        return f"{self.name} ({self.voice_id})"

    def to_dict(self):
        """Serialize for API response."""
        return {
            "id": str(self.id),
            "tenant_id": str(self.tenant_id),
            "name": self.name,
            "description": self.description,
            "voice_id": self.voice_id,
            "voice_speed": self.voice_speed,
            "stt_model": self.stt_model,
            "stt_language": self.stt_language,
            # LLM from ForeignKey
            "llm_config_id": str(self.llm_config_id) if self.llm_config_id else None,
            "llm_config_name": self.llm_config.name if self.llm_config else None,
            "llm_provider": self.llm_config.provider if self.llm_config else None,
            "system_prompt": self.system_prompt,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "turn_detection_enabled": self.turn_detection_enabled,
            "turn_detection_threshold": self.turn_detection_threshold,
            "silence_duration_ms": self.silence_duration_ms,
            "is_active": self.is_active,
            "is_default": self.is_default,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# =============================================================================
# VOICE SESSION
# =============================================================================


class VoiceSession(TenantScopedModel):
    """Real-time voice session.

    Tracks metrics for billing and analytics.
    """

    STATUS_CHOICES = [
        ("created", "Created"),
        ("active", "Active"),
        ("completed", "Completed"),
        ("error", "Error"),
        ("terminated", "Terminated"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project_id = models.UUIDField(db_index=True, null=True, blank=True)
    api_key_id = models.UUIDField(null=True, blank=True)
    user_id = models.UUIDField(null=True, blank=True)

    persona = models.ForeignKey(
        VoicePersona,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sessions",
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="created",
        db_index=True,
    )

    # Session Config (snapshot)
    config = models.JSONField(default=dict, blank=True)

    # Metrics
    duration_seconds = models.FloatField(default=0.0)
    input_tokens = models.IntegerField(default=0)
    output_tokens = models.IntegerField(default=0)
    audio_input_seconds = models.FloatField(default=0.0)
    audio_output_seconds = models.FloatField(default=0.0)
    turn_count = models.IntegerField(default=0)

    # Error tracking
    error_code = models.CharField(max_length=50, blank=True)
    error_message = models.TextField(blank=True)

    # Metadata
    metadata = models.JSONField(default=dict, blank=True)

    # Lifecycle timestamps
    started_at = models.DateTimeField(null=True, blank=True)
    terminated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "voice_sessions"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["tenant_id", "status"]),
            models.Index(fields=["project_id"]),
            models.Index(fields=["api_key_id"]),
            models.Index(fields=["-created_at"]),
        ]
        verbose_name = "Voice Session"
        verbose_name_plural = "Voice Sessions"

    def __str__(self):
        return f"Session {self.id} ({self.status})"

    def start(self):
        """Mark session as started."""
        self.status = "active"
        self.started_at = timezone.now()
        self.save(update_fields=["status", "started_at", "updated_at"])

    def complete(self):
        """Mark session as completed normally."""
        self.status = "completed"
        self.terminated_at = timezone.now()
        if self.started_at:
            self.duration_seconds = (
                self.terminated_at - self.started_at
            ).total_seconds()
        self.save(
            update_fields=["status", "terminated_at", "duration_seconds", "updated_at"]
        )

    def terminate(self, reason: str = ""):
        """Terminate session."""
        self.status = "terminated"
        self.terminated_at = timezone.now()
        self.error_message = reason
        if self.started_at:
            self.duration_seconds = (
                self.terminated_at - self.started_at
            ).total_seconds()
        self.save()

    def to_dict(self):
        """Serialize for API response."""
        return {
            "id": str(self.id),
            "tenant_id": str(self.tenant_id),
            "project_id": str(self.project_id) if self.project_id else None,
            "api_key_id": str(self.api_key_id) if self.api_key_id else None,
            "user_id": str(self.user_id) if self.user_id else None,
            "persona_id": str(self.persona_id) if self.persona_id else None,
            "status": self.status,
            "config": self.config,
            "duration_seconds": self.duration_seconds,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.input_tokens + self.output_tokens,
            "audio_input_seconds": self.audio_input_seconds,
            "audio_output_seconds": self.audio_output_seconds,
            "total_audio_seconds": self.audio_input_seconds + self.audio_output_seconds,
            "turn_count": self.turn_count,
            "error_code": self.error_code,
            "error_message": self.error_message,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "terminated_at": (
                self.terminated_at.isoformat() if self.terminated_at else None
            ),
        }


# =============================================================================
# VOICE MODEL (Available Voices) - TTS only, not LLM
# =============================================================================


class VoiceModel(models.Model):
    """Available TTS voice model.

    System-wide catalog of TTS voices (Kokoro, etc).
    NOT for LLM - use LLMModelConfig for that.
    Admin only management.
    """

    id = models.CharField(max_length=50, primary_key=True)  # e.g., "af_heart"
    name = models.CharField(max_length=100)
    provider = models.CharField(max_length=50, default="kokoro")
    language = models.CharField(max_length=10, default="en")
    gender = models.CharField(
        max_length=20,
        blank=True,
        choices=[
            ("male", "Male"),
            ("female", "Female"),
            ("neutral", "Neutral"),
        ],
    )
    description = models.TextField(blank=True)
    sample_url = models.URLField(blank=True)
    is_active = models.BooleanField(default=True, db_index=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "voice_models"
        ordering = ["provider", "name"]
        indexes = [
            models.Index(fields=["provider", "is_active"]),
            models.Index(fields=["language"]),
        ]
        verbose_name = "Voice Model"
        verbose_name_plural = "Voice Models"

    def __str__(self):
        return f"{self.name} ({self.provider})"

    def to_dict(self):
        """Serialize for API response."""
        return {
            "id": self.id,
            "name": self.name,
            "provider": self.provider,
            "language": self.language,
            "gender": self.gender,
            "description": self.description,
            "sample_url": self.sample_url,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
