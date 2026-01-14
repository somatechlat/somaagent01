"""Sensor Outbox Django Model.


Transactional outbox for Zero Data Loss.

Pattern:
1. Agent action + Outbox insert = single transaction
2. Background worker polls outbox
3. Syncs to target service
4. Marks as synced

- Django Architect: ORM patterns
- DevOps: Reliable sync
- Security Auditor: Data integrity
"""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import List

from django.db import models
from django.utils import timezone

logger = logging.getLogger(__name__)


class OutboxEventType(models.TextChoices):
    """Event types for categorization."""

    # Conversation events
    CONVERSATION_MESSAGE = "conversation.message", "Conversation Message"
    CONVERSATION_START = "conversation.start", "Conversation Start"
    CONVERSATION_END = "conversation.end", "Conversation End"

    # Memory events
    MEMORY_CREATE = "memory.create", "Memory Create"
    MEMORY_RECALL = "memory.recall", "Memory Recall"
    MEMORY_UPDATE = "memory.update", "Memory Update"
    MEMORY_DELETE = "memory.delete", "Memory Delete"
    MEMORY_CONSOLIDATE = "memory.consolidate", "Memory Consolidate"

    # LLM events
    LLM_COMPLETION = "llm.completion", "LLM Completion"
    LLM_EMBEDDING = "llm.embedding", "LLM Embedding"
    LLM_ERROR = "llm.error", "LLM Error"

    # Tool events
    TOOL_EXECUTE = "tool.execute", "Tool Execute"
    TOOL_RESULT = "tool.result", "Tool Result"
    TOOL_ERROR = "tool.error", "Tool Error"

    # Cognitive events
    COGNITIVE_STATE = "cognitive.state", "Cognitive State"
    COGNITIVE_SALIENCE = "cognitive.salience", "Cognitive Salience"


class SensorOutbox(models.Model):
    """Transactional outbox for sensor events.

    Zero Data Loss guarantees:
    - Inserted atomically with agent action
    - Never deleted until successfully synced
    - Retry with exponential backoff
    - Dead letter after max retries
    """

    # Event identity
    event_id = models.CharField(max_length=36, primary_key=True)
    event_type = models.CharField(max_length=100, db_index=True)

    # Context
    tenant_id = models.CharField(max_length=36, db_index=True)
    agent_id = models.CharField(max_length=36, db_index=True)
    user_id = models.CharField(max_length=36, blank=True, default="")
    session_id = models.CharField(max_length=36, blank=True, default="")

    # Target service
    target_service = models.CharField(max_length=50, db_index=True)

    # Payload (JSONB for PostgreSQL)
    payload = models.JSONField(default=dict)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Sync status
    synced = models.BooleanField(default=False, db_index=True)
    synced_at = models.DateTimeField(null=True, blank=True)

    # Retry handling
    retry_count = models.IntegerField(default=0)
    next_retry_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True, default="")

    # Dead letter flag
    dead_letter = models.BooleanField(default=False, db_index=True)

    class Meta:
        """Meta class implementation."""

        db_table = "sensor_outbox"
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["synced", "target_service", "created_at"]),
            models.Index(fields=["tenant_id", "event_type"]),
            models.Index(fields=["dead_letter", "created_at"]),
        ]

    def __str__(self) -> str:
        """Return string representation."""

        return f"{self.event_type} ({self.event_id[:8]}...)"

    def mark_synced(self, brain_ref: str = None) -> None:
        """Mark event as successfully synced.

        CRITICAL: Clears payload after sync.
        Content now only lives in SomaBrain.
        Local keeps only the reference.
        """
        self.synced = True
        self.synced_at = timezone.now()
        self.payload = {}  # DELETE content - now only in SomaBrain
        if brain_ref:
            # Store reference to SomaBrain location
            self.last_error = f"brain_ref:{brain_ref}"
        self.save(update_fields=["synced", "synced_at", "payload", "last_error", "updated_at"])
        logger.debug(f"Event {self.event_id} synced, payload cleared")

    def mark_failed(self, error: str, max_retries: int = 10) -> None:
        """Mark event as failed, schedule retry or dead letter."""
        self.retry_count += 1
        self.last_error = error

        if self.retry_count >= max_retries:
            self.dead_letter = True
            logger.warning(f"Event {self.event_id} sent to dead letter after {max_retries} retries")
        else:
            # Exponential backoff: 2^retry_count minutes
            delay = timedelta(minutes=min(2**self.retry_count, 60))
            self.next_retry_at = timezone.now() + delay
            logger.debug(f"Event {self.event_id} scheduled for retry at {self.next_retry_at}")

        self.save(
            update_fields=[
                "retry_count",
                "last_error",
                "dead_letter",
                "next_retry_at",
                "updated_at",
            ]
        )

    @classmethod
    def get_pending(
        cls,
        target_service: str,
        limit: int = 100,
    ) -> List["SensorOutbox"]:
        """Get pending events for a target service.

        Used by sync worker to process outbox.
        """
        now = timezone.now()
        return list(
            cls.objects.filter(
                target_service=target_service,
                synced=False,
                dead_letter=False,
            )
            .filter(models.Q(next_retry_at__isnull=True) | models.Q(next_retry_at__lte=now))
            .order_by("created_at")[:limit]
        )

    @classmethod
    def get_pending_count(cls, target_service: str) -> int:
        """Get count of pending events for monitoring."""
        return cls.objects.filter(
            target_service=target_service,
            synced=False,
            dead_letter=False,
        ).count()

    @classmethod
    def get_dead_letter_count(cls) -> int:
        """Get count of dead letter events for monitoring."""
        return cls.objects.filter(dead_letter=True).count()

    @classmethod
    def cleanup_synced(cls, older_than_days: int = 7) -> int:
        """Cleanup old synced events."""
        cutoff = timezone.now() - timedelta(days=older_than_days)
        deleted, _ = cls.objects.filter(
            synced=True,
            synced_at__lt=cutoff,
        ).delete()
        logger.info(f"Cleaned up {deleted} synced events older than {older_than_days} days")
        return deleted
