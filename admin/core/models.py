"""Core Django ORM Models for Agent Domain.

100% Django ORM - VIBE Compliant.
Replaces raw SQL stores with Django models.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from django.contrib.postgres.fields import ArrayField
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
        db_table = "sessions"
        ordering = ["-created_at"]

    def __str__(self):
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
        db_table = "session_events"
        ordering = ["created_at"]


# =============================================================================
# CAPSULE MODELS (replaces capsule_store.py)
# =============================================================================


class Capsule(models.Model):
    """Capsule definition - replaces CapsuleStore."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, db_index=True)
    version = models.CharField(max_length=50, default="1.0.0")
    tenant = models.CharField(max_length=255, db_index=True)
    description = models.TextField(blank=True)
    schema = models.JSONField(default=dict)
    config = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "capsules"
        unique_together = [["name", "version", "tenant"]]

    def __str__(self):
        return f"Capsule({self.name}:{self.version})"


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
        db_table = "capabilities"
        verbose_name_plural = "capabilities"

    def __str__(self):
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
        db_table = "ui_settings"
        unique_together = [["tenant", "user_id", "key"]]

    def __str__(self):
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
        db_table = "jobs"
        ordering = ["-priority", "scheduled_at"]

    def __str__(self):
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
        db_table = "notifications"
        ordering = ["-created_at"]

    def __str__(self):
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
        db_table = "prompts"
        unique_together = [["name", "version", "tenant"]]

    def __str__(self):
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
        db_table = "feature_flags"

    def __str__(self):
        return f"FeatureFlag({self.name}:{self.is_enabled})"


# =============================================================================
# AUDIT MODELS (replaces audit_store.py)
# =============================================================================


class AuditLog(models.Model):
    """Audit log entry - replaces AuditStore."""

    id = models.BigAutoField(primary_key=True)
    tenant = models.CharField(max_length=255, db_index=True)
    user_id = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    action = models.CharField(max_length=100, db_index=True)
    resource_type = models.CharField(max_length=100, db_index=True)
    resource_id = models.CharField(max_length=255, null=True, blank=True)
    old_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "agent_audit_logs"
        ordering = ["-created_at"]

    def __str__(self):
        return f"AuditLog({self.action}:{self.resource_type})"


# =============================================================================
# DEAD LETTER QUEUE MODELS (replaces dlq_store.py)
# =============================================================================


class DeadLetterMessage(models.Model):
    """Dead letter queue message - replaces DLQStore."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    queue_name = models.CharField(max_length=255, db_index=True)
    original_topic = models.CharField(max_length=255)
    payload = models.JSONField()
    error_message = models.TextField()
    error_type = models.CharField(max_length=255)
    retry_count = models.IntegerField(default=0)
    max_retries = models.IntegerField(default=3)
    is_processed = models.BooleanField(default=False, db_index=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "dead_letter_queue"
        ordering = ["-created_at"]

    def __str__(self):
        return f"DLQ({self.queue_name}:{self.error_type})"


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
        db_table = "agent_settings"
        unique_together = [["agent_id", "key"]]

    def __str__(self):
        return f"AgentSetting({self.agent_id}:{self.key})"
