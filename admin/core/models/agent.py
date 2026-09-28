"""Agent-related Django ORM models."""

from __future__ import annotations

import uuid

from django.db import models


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
# ASSET MODELS (replaces asset_store.py)
# =============================================================================


class Asset(models.Model):
    """Multimodal asset - replaces AssetStore."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.CharField(max_length=255, db_index=True)
    session_id = models.CharField(max_length=255, db_index=True)
    name = models.CharField(max_length=255, default="")
    asset_type = models.CharField(max_length=50, db_index=True)
    format = models.CharField(max_length=50)
    content = models.BinaryField(null=True, blank=True)
    content_size_bytes = models.BigIntegerField(default=0)
    dimensions = models.JSONField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    mime_type = models.CharField(max_length=100, null=True, blank=True)
    original_filename = models.CharField(max_length=255, null=True, blank=True)
    checksum_sha256 = models.CharField(max_length=64, null=True, blank=True)
    status = models.CharField(max_length=50, default="active")
    tombstone_reason = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "assets"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Asset({self.asset_type}:{self.id})"


# =============================================================================
# EXECUTION MODELS (replaces execution_tracker.py)
# =============================================================================


class ExecutionRecord(models.Model):
    """Execution attempt record - replaces ExecutionTracker raw SQL."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    plan_id = models.CharField(max_length=255, db_index=True)
    step_index = models.IntegerField(default=0)
    tenant_id = models.CharField(max_length=255, db_index=True)
    provider_name = models.CharField(max_length=255)
    provider_id = models.CharField(max_length=255)
    attempt_number = models.IntegerField(default=1)
    status = models.CharField(max_length=50, default="pending")
    asset_id = models.CharField(max_length=255, null=True, blank=True)
    latency_ms = models.FloatField(default=0.0)
    cost_estimate_cents = models.IntegerField(null=True, blank=True)
    quality_score = models.FloatField(null=True, blank=True)
    quality_feedback = models.JSONField(null=True, blank=True)
    error_code = models.CharField(max_length=100, null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "execution_records"
        ordering = ["-started_at"]
        indexes = [
            models.Index(fields=["plan_id", "step_index", "-started_at"]),
        ]

    def __str__(self):
        return f"Execution({self.plan_id}:{self.step_index})"


# =============================================================================
# PROVENANCE MODELS (replaces provenance_recorder.py)
# =============================================================================


class Provenance(models.Model):
    """Data lineage record - replaces ProvenanceRecorder raw SQL."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    asset_id = models.CharField(max_length=255, db_index=True)
    tenant_id = models.CharField(max_length=255, db_index=True)
    operation = models.CharField(max_length=100, null=True, blank=True)
    generation_params = models.JSONField(default=dict, blank=True)
    rework_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "provenance"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Provenance({self.asset_id})"


# =============================================================================
# MODEL PROFILE MODELS (replaces model_profiles.py)
# =============================================================================


class ModelProfile(models.Model):
    """Per-role deployment configuration - replaces ModelProfileStore."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.CharField(max_length=100, db_index=True)
    deployment_mode = models.CharField(max_length=50, default="standard")
    config = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "model_profiles"
        unique_together = [["role", "deployment_mode"]]
        ordering = ["role"]

    def __str__(self):
        return f"ModelProfile({self.role}:{self.deployment_mode})"


# =============================================================================
# MULTIMODAL OUTCOME MODELS (replaces soma_brain_outcomes.py)
# =============================================================================


class MultimodalOutcome(models.Model):
    """SomaBrain operation outcome - replaces SomaBrainOutcomesStore."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task_id = models.CharField(max_length=255, db_index=True)
    step_type = models.CharField(max_length=100, db_index=True)
    status = models.CharField(max_length=50)
    result = models.JSONField(default=dict)
    provider = models.CharField(max_length=100, default="")
    success = models.BooleanField(default=False)
    latency_ms = models.FloatField(default=0.0)
    quality_score = models.FloatField(null=True, blank=True)
    cost_cents = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "multimodal_outcomes"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Outcome({self.task_id}:{self.status})"


# =============================================================================
# DELEGATION TASK MODELS (replaces delegation_store.py)
# =============================================================================


class DelegationTask(models.Model):
    """Task delegation record - replaces DelegationStore raw SQL."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task_id = models.CharField(max_length=255, unique=True, db_index=True)
    payload = models.JSONField(default=dict)
    status = models.CharField(max_length=50, default="received")
    callback_url = models.URLField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    result = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "delegation_tasks"
        ordering = ["-created_at"]

    def __str__(self):
        return f"DelegationTask({self.task_id}:{self.status})"
