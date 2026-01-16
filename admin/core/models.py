"""Core Django ORM Models for Agent Domain.

100% Django ORM -
Replaces raw SQL stores with Django models.
"""

from __future__ import annotations

import uuid
from typing import Optional

from django.db import models
from django.utils import timezone

# =============================================================================
# SESSION MODELS (replaces session_repository.py)
# =============================================================================


class Session(models.Model):
    """Chat session - replaces PostgresSessionStore."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session_id = models.CharField(max_length=255, unique=True, db_index=True)
    persona_id = models.CharField(max_length=255, null=True, blank=True)
    tenant = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta class implementation."""

        db_table = "sessions"
        ordering = ["-created_at"]

    def __str__(self):
        """Return string representation."""

        return f"Session({self.session_id})"


class SessionEvent(models.Model):
    """Session event - replaces events table."""

    id = models.BigAutoField(primary_key=True)
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name="events")
    event_type = models.CharField(max_length=100, db_index=True)
    payload = models.JSONField(default=dict)
    role = models.CharField(max_length=50, default="user")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        """Meta class implementation."""

        db_table = "session_events"
        ordering = ["created_at"]


# =============================================================================
# CONSTITUTION MODELS (The Supreme Law)
# =============================================================================


class Constitution(models.Model):
    """The Supreme Regulatory Document.

    IMMUTABLE: Once signed, this record cannot be changed.
    All Capsules must reference a valid, active Constitution.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    version = models.CharField(max_length=50, help_text="Semantic Version (e.g., 1.0.0)")

    # Cryptographic Proof
    content_hash = models.CharField(
        max_length=64, unique=True, help_text="SHA-256 Hash of normalized content"
    )
    signature = models.TextField(help_text="Ed25519 Signature of the content_hash")

    # The Law
    content = models.JSONField(help_text="The ")

    # Metadata
    is_active = models.BooleanField(default=False, help_text="Only one can be active at a time")
    created_at = models.DateTimeField(auto_now_add=True)
    activated_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        """Meta class implementation."""

        db_table = "constitutions"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["is_active"]),
            models.Index(fields=["content_hash"]),
        ]

    def __str__(self):
        """Return string representation."""

        return f"Constitution(v{self.version}:{self.content_hash[:8]})"


# =============================================================================
# CAPSULE MODELS (replaces capsule_store.py)
# =============================================================================


class Capsule(models.Model):
    """Capsule definition - The Atomic Unit of Agent Identity (Rule 91).

    The Capsule acts as the "Sole Unit" of exchange, containing:
    1.  Identity (Soul)
    2.  Body (Model Configs via FK)
    3.  Hands (capabilities via M2M)
    4.  Memory (MemoryConfig via FK)

    Lifecycle: DRAFT → ACTIVE → ARCHIVED
    """

    # Status choices for lifecycle management
    STATUS_DRAFT = "draft"
    STATUS_ACTIVE = "active"
    STATUS_ARCHIVED = "archived"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_ACTIVE, "Active"),
        (STATUS_ARCHIVED, "Archived"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, db_index=True)
    version = models.CharField(max_length=50, default="1.0.0")

    # Tenant FK for proper referential integrity
    tenant = models.ForeignKey(
        'saas.Tenant',
        on_delete=models.CASCADE,
        related_name='capsules',
        db_index=True,
        help_text="Owning tenant",
    )

    description = models.TextField(blank=True)

    # Lifecycle Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_DRAFT,
        db_index=True,
        help_text="Lifecycle state: draft, active, archived",
    )

    # Version Lineage (for edit-spawns-new-version pattern)
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children",
        help_text="Parent capsule this was cloned from",
    )

    # Governance & Security
    constitution = models.ForeignKey(
        Constitution,
        on_delete=models.PROTECT,
        related_name="capsules",
        null=True,
        help_text="The binding legal framework",
    )
    constitution_ref = models.JSONField(
        default=dict, blank=True, help_text="Cross-system reference: {'checksum': str, 'url': str}"
    )
    registry_signature = models.TextField(
        null=True, blank=True, help_text="Ed25519 Signature from Registry Authority"
    )
    certified_at = models.DateTimeField(
        null=True, blank=True, help_text="Timestamp of certification"
    )

    # The Soul (Identity)
    system_prompt = models.TextField(default="", help_text="Base cognitive instruction set")
    personality_traits = models.JSONField(
        default=dict, help_text="Big 5 Traits (Openness, etc.) 0.0-1.0"
    )
    neuromodulator_baseline = models.JSONField(
        default=dict, help_text="Baseline chemical state (Dopamine, etc.)"
    )
    learning_config = models.JSONField(
        default=dict,
        help_text="GMD Hyperparameters (eta, lambda, alpha) & Reward Thresholds",
    )

    # ═══════════════════════════════════════════════════════════════════
    # 2. BODY: MODEL SOVEREIGNTY (Foreign Keys Only - Rule 91)
    # ═══════════════════════════════════════════════════════════════════

    # 🧠 PRIMARY BRAIN
    chat_model = models.ForeignKey(
        'llm.LLMModelConfig',
        related_name='capabilities_chat',
        on_delete=models.PROTECT,
        null=True, # Allowed to be null in draft
        help_text="The main cognitive engine (e.g. gpt-4-turbo)"
    )

    # 👁️ VISION & IMAGE
    image_model = models.ForeignKey(
        'llm.LLMModelConfig',
        related_name='capabilities_image',
        on_delete=models.SET_NULL, null=True, blank=True,
        help_text="Image generation model (e.g. dall-e-3)"
    )

    # 🗣️ VOICE (TTS/STT)
    voice_model = models.ForeignKey(
        'llm.LLMModelConfig',
        related_name='capabilities_voice',
        on_delete=models.SET_NULL, null=True, blank=True,
        help_text="Voice synthesis model (e.g. elevenlabs-v1)"
    )

    # 🌐 BROWSER
    browser_model = models.ForeignKey(
        'llm.LLMModelConfig',
        related_name='capabilities_browser',
        on_delete=models.SET_NULL, null=True, blank=True,
        help_text="Web browsing and vision model (e.g. perplexity)"
    )

    # ═══════════════════════════════════════════════════════════════════
    # 3. HANDS: TOOLS & CAPABILITIES
    # ═══════════════════════════════════════════════════════════════════

    capabilities = models.ManyToManyField(
        'Capability',
        related_name='capsules',
        blank=True,
        help_text="Active tools/MCP servers available to this agent"
    )

    # ═══════════════════════════════════════════════════════════════════
    # 4. MEMORY & HISTORY
    # ═══════════════════════════════════════════════════════════════════

    memory_config = models.ForeignKey(
        'somabrain.MemoryConfig',
        on_delete=models.PROTECT,
        null=True, blank=True,
        help_text="Memory retention and retrieval strategy"
    )

    # Legacy Fields (Deprecated - Rule 91)
    # kept for migration, do not use for new logic
    schema = models.JSONField(default=dict, help_text="DEPRECATED: Use Capability M2M")
    config = models.JSONField(default=dict, help_text="DEPRECATED: Use Model Configs")
    capabilities_whitelist = models.JSONField(default=list, help_text="DEPRECATED: Use Capability M2M")
    resource_limits = models.JSONField(default=dict, help_text="Max wall clock, concurrency, etc.")

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta class implementation."""

        db_table = "capsules"
        unique_together = [["name", "version", "tenant"]]
        indexes = [
            models.Index(fields=["tenant", "status"]),
            models.Index(fields=["tenant", "name", "version"]),
        ]

    def __str__(self):
        """Return string representation."""

        return f"Capsule({self.name}:{self.version}:{self.status})"

    @property
    def is_certified(self) -> bool:
        """Check if capsule has been certified."""
        return bool(self.registry_signature and self.status == self.STATUS_ACTIVE)

    @property
    def soul(self) -> dict:
        """Return Soul (identity) as dict."""
        return {
            "system_prompt": self.system_prompt,
            "personality_traits": self.personality_traits,
            "neuromodulator_baseline": self.neuromodulator_baseline,
        }

    @property
    def body(self) -> dict:
        """Return Body (capabilities) as dict."""
        return {
            "capabilities_whitelist": self.capabilities_whitelist,
            "resource_limits": self.resource_limits,
        }


class CapsuleInstance(models.Model):
    """Running capsule instance - replaces CapsuleInstanceStore."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    capsule = models.ForeignKey(Capsule, on_delete=models.CASCADE, related_name="instances")
    session_id = models.CharField(max_length=255, db_index=True)
    state = models.JSONField(default=dict)
    status = models.CharField(max_length=50, default="running", db_index=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        """Meta class implementation."""

        db_table = "capsule_instances"


# =============================================================================
# CAPABILITY MODELS (replaces capability_registry.py)
# =============================================================================


class Capability(models.Model):
    """Agent capability - replaces CapabilityRegistry."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True, db_index=True)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=100, db_index=True)
    schema = models.JSONField(default=dict)
    config = models.JSONField(default=dict)
    is_enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta class implementation."""

        db_table = "capabilities"
        verbose_name_plural = "capabilities"

    def __str__(self):
        """Return string representation."""

        return f"Capability({self.name})"


# =============================================================================
# UI SETTINGS MODELS (replaces ui_settings_store.py)
# =============================================================================


class UISetting(models.Model):
    """UI settings per tenant/user - replaces UISettingsStore."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.CharField(max_length=255, db_index=True)
    user_id = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    key = models.CharField(max_length=255, db_index=True)
    value = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta class implementation."""

        db_table = "ui_settings"
        unique_together = [["tenant", "user_id", "key"]]

    def __str__(self):
        """Return string representation."""

        return f"UISetting({self.tenant}:{self.key})"


# =============================================================================
# JOB PLANNER MODELS (replaces job_planner.py)
# =============================================================================


class Job(models.Model):
    """Scheduled job - replaces JobPlanner."""

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("running", "Running"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("cancelled", "Cancelled"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, db_index=True)
    job_type = models.CharField(max_length=100, db_index=True)
    tenant = models.CharField(max_length=255, db_index=True)
    payload = models.JSONField(default=dict)
    status = models.CharField(
        max_length=50, choices=STATUS_CHOICES, default="pending", db_index=True
    )
    priority = models.IntegerField(default=0)
    scheduled_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    result = models.JSONField(null=True, blank=True)
    error = models.TextField(null=True, blank=True)
    retry_count = models.IntegerField(default=0)
    max_retries = models.IntegerField(default=3)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta class implementation."""

        db_table = "jobs"
        ordering = ["-priority", "scheduled_at"]

    def __str__(self):
        """Return string representation."""

        return f"Job({self.name}:{self.status})"


# =============================================================================
# NOTIFICATION MODELS (replaces notifications_store.py)
# =============================================================================


class Notification(models.Model):
    """User notification - replaces NotificationsStore."""

    TYPE_CHOICES = [
        ("info", "Info"),
        ("warning", "Warning"),
        ("error", "Error"),
        ("success", "Success"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.CharField(max_length=255, db_index=True)
    user_id = models.CharField(max_length=255, db_index=True)
    notification_type = models.CharField(max_length=50, choices=TYPE_CHOICES, default="info")
    title = models.CharField(max_length=255)
    message = models.TextField()
    data = models.JSONField(default=dict, blank=True)
    is_read = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        """Meta class implementation."""

        db_table = "notifications"
        ordering = ["-created_at"]

    def __str__(self):
        """Return string representation."""

        return f"Notification({self.title})"


# =============================================================================
# PROMPT MODELS (replaces prompt_store.py)
# =============================================================================


class Prompt(models.Model):
    """Prompt template - replaces PromptStore."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, db_index=True)
    version = models.CharField(max_length=50, default="1.0.0")
    tenant = models.CharField(max_length=255, db_index=True)
    template = models.TextField()
    variables = models.JSONField(default=list)
    metadata = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta class implementation."""

        db_table = "prompts"
        unique_together = [["name", "version", "tenant"]]

    def __str__(self):
        """Return string representation."""

        return f"Prompt({self.name}:{self.version})"


# =============================================================================
# FEATURE FLAGS MODELS (replaces feature_flags_store.py)
# =============================================================================


class FeatureFlag(models.Model):
    """Feature flag - replaces FeatureFlagsStore."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True, db_index=True)
    description = models.TextField(blank=True)
    is_enabled = models.BooleanField(default=False)
    rollout_percentage = models.IntegerField(default=0)
    tenant_overrides = models.JSONField(default=dict)
    user_overrides = models.JSONField(default=dict)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta class implementation."""

        db_table = "feature_flags"

    def __str__(self):
        """Return string representation."""

        return f"FeatureFlag({self.name}:{self.is_enabled})"


# =============================================================================
# AUDIT MODELS - MOVED TO admin/saas/models/audit.py
# =============================================================================
# NOTE: AuditLog is now in admin.saas.models.AuditLog (canonical location)
# The duplicate here was removed to prevent confusion.
# Table: audit_logs (not agent_audit_logs)


# =============================================================================
# MEMORY REPLICA MODELS
# =============================================================================


class MemoryReplica(models.Model):
    """Memory replica for WAL events.

    Replaces the legacy wal_memory_replica raw SQL table.
    Stores a permanent record of all memory events for retrieval and audit.
    """

    id = models.BigAutoField(primary_key=True)
    event_id = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    session_id = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    persona_id = models.CharField(max_length=255, null=True, blank=True)
    tenant = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    role = models.CharField(max_length=50, null=True, blank=True)
    coord = models.CharField(max_length=255, null=True, blank=True)
    request_id = models.CharField(max_length=255, null=True, blank=True)
    trace_id = models.CharField(max_length=255, null=True, blank=True)
    payload = models.JSONField(default=dict, help_text="The core memory content payload")
    wal_timestamp = models.FloatField(
        null=True, blank=True, db_index=True, help_text="Original WAL event timestamp"
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        """Meta class implementation."""

        db_table = "memory_replica"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["tenant", "session_id"]),
            models.Index(fields=["wal_timestamp"]),
        ]
        verbose_name = "Memory Replica"
        verbose_name_plural = "Memory Replicas"

    def __str__(self):
        """Return string representation."""

        return f"MemoryReplica({self.event_id})"


# NOTE: DeadLetterMessage deleted - use OutboxDeadLetter for all DLQ needs

# =============================================================================
# AGENT SETTINGS MODELS (replaces agent_settings_store.py)
# =============================================================================


class AgentSetting(models.Model):
    """Agent-specific settings - replaces AgentSettingsStore."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent_id = models.CharField(max_length=255, db_index=True)
    key = models.CharField(max_length=255, db_index=True)
    value = models.JSONField()
    is_secret = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta class implementation."""

        db_table = "agent_settings"
        unique_together = [["agent_id", "key"]]

    def __str__(self):
        """Return string representation."""

        return f"AgentSetting({self.agent_id}:{self.key})"


# =============================================================================
# ZERO DATA LOSS INFRASTRUCTURE (Transactional Outbox Pattern)
# =============================================================================


class OutboxMessage(models.Model):
    """Transactional Outbox for guaranteed message delivery.

    Implements the Transactional Outbox Pattern:
    - Messages are stored in same transaction as business data
    - Publisher polls and sends to Kafka
    - Guarantees exactly-once delivery


    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    idempotency_key = models.CharField(max_length=255, unique=True, db_index=True)

    # Message routing
    topic = models.CharField(max_length=255, db_index=True)
    partition_key = models.CharField(max_length=255, null=True, blank=True)

    # Payload
    payload = models.JSONField()
    headers = models.JSONField(default=dict, blank=True)

    # State tracking
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    published_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)

    # Retry logic
    attempts = models.IntegerField(default=0)
    max_attempts = models.IntegerField(default=5)
    next_retry_at = models.DateTimeField(null=True, blank=True, db_index=True)
    last_error = models.TextField(null=True, blank=True)

    class Status(models.TextChoices):
        """Status class implementation."""

        PENDING = "pending", "Pending"
        PUBLISHED = "published", "Published"
        FAILED = "failed", "Failed"
        DEAD = "dead", "Dead Letter"

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )

    class Meta:
        """Meta class implementation."""

        db_table = "outbox_messages"
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["topic", "status"]),
        ]
        ordering = ["created_at"]

    def __str__(self):
        """Return string representation."""

        return f"OutboxMessage({self.topic}:{self.status})"

    def mark_published(self):
        """Mark message as successfully published."""
        self.status = self.Status.PUBLISHED
        self.published_at = timezone.now()
        self.save(update_fields=["status", "published_at"])

    def mark_failed(self, error: str):
        """Mark message as failed, schedule retry if attempts remain."""
        self.attempts += 1
        self.last_error = error

        if self.attempts >= self.max_attempts:
            self.status = self.Status.DEAD
            self.failed_at = timezone.now()
        else:
            self.status = self.Status.FAILED
            # Exponential backoff: 2^attempts seconds
            backoff = 2**self.attempts
            self.next_retry_at = timezone.now() + timezone.timedelta(seconds=backoff)

        self.save()


class DeadLetterMessage(models.Model):
    """Dead Letter Queue storage for failed messages.

    Messages that fail after max retries are stored here for:
    - Manual review
    - Alerting
    - Potential replay


    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Original message reference
    original_outbox_id = models.UUIDField(null=True, blank=True, db_index=True)
    original_topic = models.CharField(max_length=255, db_index=True)
    idempotency_key = models.CharField(max_length=255, db_index=True)

    # Payload
    payload = models.JSONField()
    headers = models.JSONField(default=dict, blank=True)

    # Failure info
    error_message = models.TextField()
    error_type = models.CharField(max_length=255, null=True, blank=True)
    attempts = models.IntegerField(default=0)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    original_created_at = models.DateTimeField(null=True, blank=True)

    # Resolution tracking
    resolved = models.BooleanField(default=False, db_index=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.CharField(max_length=255, null=True, blank=True)
    resolution_notes = models.TextField(null=True, blank=True)

    class Meta:
        """Meta class implementation."""

        db_table = "dead_letter_messages"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["original_topic", "resolved"]),
        ]

    def __str__(self):
        """Return string representation."""

        return f"DLQ({self.original_topic}:{self.id})"

    def resolve(self, resolved_by: str, notes: str = ""):
        """Mark DLQ message as resolved."""
        self.resolved = True
        self.resolved_at = timezone.now()
        self.resolved_by = resolved_by
        self.resolution_notes = notes
        self.save()


class IdempotencyRecord(models.Model):
    """Idempotency tracking for exactly-once operations.

    Stores idempotency keys with TTL to prevent duplicate processing.


    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    idempotency_key = models.CharField(max_length=255, unique=True, db_index=True)

    # Operation result (optional, for response caching)
    operation_type = models.CharField(max_length=100, db_index=True)
    result = models.JSONField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    expires_at = models.DateTimeField(db_index=True)

    class Meta:
        """Meta class implementation."""

        db_table = "idempotency_records"
        indexes = [
            models.Index(fields=["expires_at"]),
            models.Index(fields=["operation_type", "created_at"]),
        ]

    def __str__(self):
        """Return string representation."""

        return f"Idempotency({self.idempotency_key})"

    @classmethod
    def check_and_set(
        cls, key: str, operation_type: str, ttl_seconds: int = 86400
    ) -> tuple[bool, Optional["IdempotencyRecord"]]:
        """
        Check if operation was already processed.

        Returns:
            (is_new, record) - True if new operation, False if duplicate
        """
        expires_at = timezone.now() + timezone.timedelta(seconds=ttl_seconds)

        record, created = cls.objects.get_or_create(
            idempotency_key=key,
            defaults={
                "operation_type": operation_type,
                "expires_at": expires_at,
            },
        )

        if not created:
            # Check if expired
            if record.expires_at < timezone.now():
                # Expired - update and treat as new
                record.expires_at = expires_at
                record.result = None
                record.save()
                return True, record
            # Not expired - duplicate
            return False, record

        return True, record

    @classmethod
    def cleanup_expired(cls) -> int:
        """Delete expired idempotency records. Returns count deleted."""
        deleted, _ = cls.objects.filter(expires_at__lt=timezone.now()).delete()
        return deleted


class PendingMemory(models.Model):
    """Pending memory queue for SomaBrain sync.

    When SomaBrain is unavailable (degradation mode), memories are
    stored here and synced when connection is restored.


    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    idempotency_key = models.CharField(max_length=255, unique=True, db_index=True)

    # Memory data
    tenant_id = models.CharField(max_length=255, db_index=True)
    namespace = models.CharField(max_length=100, default="wm")
    payload = models.JSONField()

    # State
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    synced = models.BooleanField(default=False, db_index=True)
    synced_at = models.DateTimeField(null=True, blank=True)

    # Retry tracking
    sync_attempts = models.IntegerField(default=0)
    last_error = models.TextField(null=True, blank=True)

    class Meta:
        """Meta class implementation."""

        db_table = "pending_memories"
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["synced", "created_at"]),
            models.Index(fields=["tenant_id", "synced"]),
        ]

    def __str__(self):
        """Return string representation."""

        return f"PendingMemory({self.tenant_id}:{self.synced})"

    def mark_synced(self):
        """Mark memory as successfully synced to SomaBrain."""
        self.synced = True
        self.synced_at = timezone.now()
        self.save(update_fields=["synced", "synced_at"])


# =============================================================================
# SENSOR OUTBOX (ZDL Pattern)
# =============================================================================

# Import SensorOutbox so Django detects it for migrations
from admin.core.sensors.outbox import SensorOutbox  # noqa: E402, F401
