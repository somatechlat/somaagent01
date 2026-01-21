"""Zero Data Loss Infrastructure Models.

VIBE Rule 245 Compliant: Extracted from admin/core/models.py.
Implements the Transactional Outbox Pattern for guaranteed message delivery.

Models:
    - OutboxMessage: Transactional outbox for Kafka publishing
    - DeadLetterMessage: Failed message storage for manual review
    - IdempotencyRecord: Exactly-once operation tracking
    - PendingMemory: Degradation mode memory queue
"""

from __future__ import annotations

import uuid
from typing import Optional

from django.db import models
from django.utils import timezone


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
        """Message delivery status."""

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
        """Django model metadata."""

        db_table = "outbox_messages"
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["topic", "status"]),
        ]
        ordering = ["created_at"]

    def __str__(self) -> str:
        """Return string representation."""
        return f"OutboxMessage({self.topic}:{self.status})"

    def mark_published(self) -> None:
        """Mark message as successfully published."""
        self.status = self.Status.PUBLISHED
        self.published_at = timezone.now()
        self.save(update_fields=["status", "published_at"])

    def mark_failed(self, error: str) -> None:
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
        """Django model metadata."""

        db_table = "dead_letter_messages"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["original_topic", "resolved"]),
        ]

    def __str__(self) -> str:
        """Return string representation."""
        return f"DLQ({self.original_topic}:{self.id})"

    def resolve(self, resolved_by: str, notes: str = "") -> None:
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
        """Django model metadata."""

        db_table = "idempotency_records"
        indexes = [
            models.Index(fields=["expires_at"]),
            models.Index(fields=["operation_type", "created_at"]),
        ]

    def __str__(self) -> str:
        """Return string representation."""
        return f"Idempotency({self.idempotency_key})"

    @classmethod
    def check_and_set(
        cls, key: str, operation_type: str, ttl_seconds: int = 86400
    ) -> tuple[bool, Optional["IdempotencyRecord"]]:
        """Check if operation was already processed.

        Args:
            key: Unique idempotency key for the operation.
            operation_type: Type of operation being performed.
            ttl_seconds: Time-to-live for the record (default 24h).

        Returns:
            Tuple of (is_new, record):
            - is_new: True if new operation, False if duplicate.
            - record: The IdempotencyRecord instance.
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
        """Delete expired idempotency records.

        Returns:
            Count of deleted records.
        """
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
        """Django model metadata."""

        db_table = "pending_memories"
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["synced", "created_at"]),
            models.Index(fields=["tenant_id", "synced"]),
        ]

    def __str__(self) -> str:
        """Return string representation."""
        return f"PendingMemory({self.tenant_id}:{self.synced})"

    def mark_synced(self) -> None:
        """Mark memory as successfully synced to SomaBrain."""
        self.synced = True
        self.synced_at = timezone.now()
        self.save(update_fields=["synced", "synced_at"])
