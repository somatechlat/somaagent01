"""Zero Data Loss Signals.

Django signals for automatic outbox entry creation.


"""

from __future__ import annotations

import hashlib
import json
import logging
import uuid
from typing import Any, Dict, Optional

from django.db import transaction
from django.dispatch import receiver, Signal

logger = logging.getLogger(__name__)


# Custom signals for ZDL operations
memory_created = Signal()  # Sent when a memory should be stored
memory_recalled = Signal()  # Sent when a memory is recalled
tool_executed = Signal()  # Sent when a tool execution completes
conversation_message = Signal()  # Sent when a conversation message is created


class OutboxEntryManager:
    """Manager for creating outbox entries.

    Django-pattern manager for transactional outbox operations.
    Use this to ensure messages are published with exactly-once semantics.
    """

    @staticmethod
    def create_entry(
        topic: str,
        payload: Dict[str, Any],
        partition_key: Optional[str] = None,
        idempotency_key: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> "OutboxMessage":
        """Create an outbox entry within the current transaction.

        Args:
            topic: Kafka topic name
            payload: Message payload (will be JSON serialized)
            partition_key: Optional partition key for ordering
            idempotency_key: Optional idempotency key (auto-generated if not provided)
            headers: Optional message headers

        Returns:
            Created OutboxMessage instance
        """
        from admin.core.models import OutboxMessage

        # Generate idempotency key if not provided
        if not idempotency_key:
            payload_hash = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[
                :16
            ]
            idempotency_key = f"{topic}:{uuid.uuid4().hex[:8]}:{payload_hash}"

        return OutboxMessage.objects.create(
            topic=topic,
            payload=payload,
            partition_key=partition_key,
            idempotency_key=idempotency_key,
            headers=headers or {},
        )

    @staticmethod
    @transaction.atomic
    def create_with_record(
        topic: str,
        payload: Dict[str, Any],
        model_instance: Any,
        partition_key: Optional[str] = None,
    ) -> "OutboxMessage":
        """Create outbox entry linked to a model instance.

        Ensures both the model and outbox entry are saved atomically.

        Args:
            topic: Kafka topic name
            payload: Message payload
            model_instance: Django model instance (must be saved)
            partition_key: Optional partition key

        Returns:
            Created OutboxMessage instance
        """
        from admin.core.models import OutboxMessage

        # Save model if not already saved
        if not model_instance.pk:
            model_instance.save()

        # Generate idempotency key from model
        model_name = model_instance.__class__.__name__.lower()
        idempotency_key = f"{topic}:{model_name}:{model_instance.pk}"

        return OutboxMessage.objects.create(
            topic=topic,
            payload=payload,
            partition_key=partition_key,
            idempotency_key=idempotency_key,
            headers={
                "source_model": model_name,
                "source_id": str(model_instance.pk),
            },
        )


# Singleton manager instance
outbox_manager = OutboxEntryManager()


# =============================================================================
# SIGNAL HANDLERS
# =============================================================================


@receiver(memory_created)
def handle_memory_created(sender, **kwargs):
    """Handle memory creation signal - queue for SomaBrain sync.

    Usage:
        from admin.core.signals import memory_created
        memory_created.send(
            sender=MyClass,
            payload={"content": "...", "tags": [...]},
            tenant_id="tenant-123",
            namespace="wm",
        )
    """
    payload = kwargs.get("payload", {})
    tenant_id = kwargs.get("tenant_id", "default")
    namespace = kwargs.get("namespace", "wm")

    outbox_manager.create_entry(
        topic="somabrain.memory.remember",
        payload={
            "payload": payload,
            "tenant": tenant_id,
            "namespace": namespace,
        },
        partition_key=tenant_id,
    )

    logger.debug(f"Memory queued for SomaBrain: tenant={tenant_id}")


@receiver(conversation_message)
def handle_conversation_message(sender, **kwargs):
    """Handle conversation message signal - queue for processing.

    Usage:
        from admin.core.signals import conversation_message
        conversation_message.send(
            sender=MyClass,
            conversation_id="conv-123",
            message_id="msg-456",
            role="user",
            content="Hello!",
        )
    """
    conversation_id = kwargs.get("conversation_id")
    message_id = kwargs.get("message_id")
    role = kwargs.get("role", "user")
    content = kwargs.get("content", "")

    outbox_manager.create_entry(
        topic="conversation.inbound",
        payload={
            "conversation_id": conversation_id,
            "message_id": message_id,
            "role": role,
            "content": content,
        },
        partition_key=conversation_id,
        idempotency_key=f"conv:{conversation_id}:{message_id}",
    )

    logger.debug(f"Conversation message queued: {conversation_id}/{message_id}")


@receiver(tool_executed)
def handle_tool_executed(sender, **kwargs):
    """Handle tool execution signal - queue result.

    Usage:
        from admin.core.signals import tool_executed
        tool_executed.send(
            sender=MyClass,
            execution_id="exec-123",
            tool_name="web_search",
            result={"data": ...},
            success=True,
        )
    """
    execution_id = kwargs.get("execution_id")
    tool_name = kwargs.get("tool_name")
    result = kwargs.get("result", {})
    success = kwargs.get("success", True)

    outbox_manager.create_entry(
        topic="tool.results",
        payload={
            "execution_id": execution_id,
            "tool_name": tool_name,
            "result": result,
            "success": success,
        },
        partition_key=execution_id,
        idempotency_key=f"tool:{execution_id}",
    )

    logger.debug(f"Tool result queued: {tool_name}/{execution_id}")


# =============================================================================
# MODEL MANAGERS (Django Pattern)
# =============================================================================


class OutboxQuerySet:
    """Custom queryset methods for OutboxMessage.

    Add to OutboxMessage.objects as a manager.
    """

    @staticmethod
    def pending():
        """Get pending messages ready for publishing."""
        from django.db.models import Q
        from django.utils import timezone

        from admin.core.models import OutboxMessage

        return (
            OutboxMessage.objects.filter(
                status__in=[OutboxMessage.Status.PENDING, OutboxMessage.Status.FAILED],
            )
            .filter(Q(next_retry_at__isnull=True) | Q(next_retry_at__lte=timezone.now()))
            .order_by("created_at")
        )

    @staticmethod
    def dead():
        """Get dead letter messages."""
        from admin.core.models import OutboxMessage

        return OutboxMessage.objects.filter(status=OutboxMessage.Status.DEAD)

    @staticmethod
    def stats():
        """Get outbox statistics."""
        from django.db.models import Count

        from admin.core.models import OutboxMessage

        return OutboxMessage.objects.values("status").annotate(count=Count("id"))