"""Voice Django ORM Models.


AgentVoice Vox integration for voice personas, sessions, and models.

Per SRS Section 6: VoicePersona, VoiceSession, VoiceModel
References existing LLMModelConfig - NO duplicate model creation.
"""

import datetime
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
        """Meta class implementation."""

        abstract = True


class TenantScopedModel(TimestampedModel):
    """Abstract base with tenant isolation."""

    tenant_id = models.UUIDField(
        db_index=True,
        help_text="Tenant ID for multi-tenancy isolation",
    )

    class Meta:
        """Meta class implementation."""

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

    # Type-checker visible ForeignKey _id attribute. This is `int | None`, not
    # a UUID: the FK targets LLMModelConfig, whose primary key is a
    # BigAutoField (admin/llm/migrations/0001_initial.py). The old
    # `uuid.UUID | None` annotation was a fabrication that made every
    # consumer type-check against a key shape the table cannot produce.
    llm_config_id: int | None

    class Meta:
        """Meta class implementation."""

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
        """Return string representation."""

        return f"{self.name} ({self.voice_id})"


# =============================================================================
# VOICE SESSION
# =============================================================================


class VoiceSession(TenantScopedModel):
    """Real-time voice session.

    Tracks session metrics for operations and analytics.
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

    # Type-checker visible ForeignKey _id attribute
    persona_id: uuid.UUID | None

    @property
    def audio_seconds(self) -> float:
        return self.audio_input_seconds + self.audio_output_seconds

    @property
    def ended_at(self) -> datetime.datetime | None:
        return self.terminated_at

    @ended_at.setter
    def ended_at(self, value: datetime.datetime | None) -> None:
        self.terminated_at = value

    class Meta:
        """Meta class implementation."""

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
        """Return string representation."""

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
            self.duration_seconds = (self.terminated_at - self.started_at).total_seconds()
        self.save(update_fields=["status", "terminated_at", "duration_seconds", "updated_at"])

    def terminate(self, reason: str = ""):
        """Terminate session."""
        self.status = "terminated"
        self.terminated_at = timezone.now()
        self.error_message = reason
        if self.started_at:
            self.duration_seconds = (self.terminated_at - self.started_at).total_seconds()
        self.save()


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

    @property
    def voice_id(self) -> str:
        return self.id

    @property
    def is_default(self) -> bool:
        return False

    class Meta:
        """Meta class implementation."""

        db_table = "voice_models"
        ordering = ["provider", "name"]
        indexes = [
            models.Index(fields=["provider", "is_active"]),
            models.Index(fields=["language"]),
        ]
        verbose_name = "Voice Model"
        verbose_name_plural = "Voice Models"

    def __str__(self):
        """Return string representation."""

        return f"{self.name} ({self.provider})"
