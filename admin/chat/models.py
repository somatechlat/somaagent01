"""Chat Django ORM Models.

VIBE COMPLIANT - Django ORM, no SQLAlchemy.
Per login-to-chat-journey design.md Section 6.1

Models:
- Conversation: Chat conversation record
- Message: Chat message record
"""

from __future__ import annotations

import uuid

from django.db import models
from django.utils import timezone


class Conversation(models.Model):
    """Chat conversation record.

    Per design.md Section 6.1:
    - Links user, agent, and tenant
    - Tracks message count and status
    - Supports title generation
    """

    STATUS_CHOICES = [
        ("active", "Active"),
        ("archived", "Archived"),
        ("deleted", "Deleted"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent_id = models.UUIDField(db_index=True)
    user_id = models.UUIDField(db_index=True)
    tenant_id = models.UUIDField(db_index=True)

    title = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="active",
        db_index=True,
    )
    message_count = models.IntegerField(default=0)

    # Memory mode: session (ephemeral) or persistent
    memory_mode = models.CharField(max_length=20, default="persistent")

    # Metadata for additional context
    metadata = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "conversations"
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["user_id", "status"]),
            models.Index(fields=["agent_id", "status"]),
            models.Index(fields=["tenant_id", "user_id"]),
        ]

    def __str__(self):
        return f"Conversation({self.id}:{self.title or 'Untitled'})"


class Message(models.Model):
    """Chat message record.

    Per design.md Section 6.1:
    - Stores user and assistant messages
    - Tracks token count and latency
    - Links to conversation
    """

    ROLE_CHOICES = [
        ("user", "User"),
        ("assistant", "Assistant"),
        ("system", "System"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation_id = models.UUIDField(db_index=True)

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, db_index=True)
    content = models.TextField()

    # Token tracking
    token_count = models.IntegerField(default=0)

    # Model info (for assistant messages)
    model = models.CharField(max_length=100, null=True, blank=True)
    latency_ms = models.IntegerField(null=True, blank=True)

    # Metadata for additional context (tool calls, etc.)
    metadata = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "messages"
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["conversation_id", "created_at"]),
        ]

    def __str__(self):
        return f"Message({self.id}:{self.role})"


class ConversationParticipant(models.Model):
    """Conversation participant for multi-user conversations.

    Supports future multi-user chat scenarios.
    """

    ROLE_CHOICES = [
        ("owner", "Owner"),
        ("participant", "Participant"),
        ("observer", "Observer"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation_id = models.UUIDField(db_index=True)
    user_id = models.UUIDField(db_index=True)

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="participant")
    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "conversation_participants"
        unique_together = [["conversation_id", "user_id"]]
        indexes = [
            models.Index(fields=["user_id", "conversation_id"]),
        ]

    def __str__(self):
        return f"Participant({self.user_id}:{self.conversation_id})"
