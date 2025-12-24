# Zero Data Loss Architecture - SRS Specification

**Document ID:** SA01-ZDL-ARCHITECTURE-2025-12
**Version:** 1.0
**Created:** 2025-12-24
**Status:** CANONICAL — Architectural Standard

---

## 1. Executive Summary

This document specifies the **Zero Data Loss (ZDL)** architecture for SomaAgent01.
All data operations MUST guarantee durability through:
- Transactional Outbox Pattern (PostgreSQL + Django)
- Kafka Exactly-Once Semantics
- Dead Letter Queue Handling
- Idempotency Keys

**RULE: NO DATA CAN BE LOST. EVER.**

---

## 2. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    ZERO DATA LOSS ARCHITECTURE                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐    │
│  │   Service    │────▶│  PostgreSQL  │────▶│    Kafka     │    │
│  │  (Django)    │     │  Transaction │     │   (Exactly   │    │
│  │              │     │  + Outbox    │     │    Once)     │    │
│  └──────────────┘     └──────────────┘     └──────────────┘    │
│         │                    │                    │             │
│         │                    │                    │             │
│         ▼                    ▼                    ▼             │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐    │
│  │ Idempotency  │     │   Outbox     │     │  Dead Letter │    │
│  │    Keys      │     │  Publisher   │     │    Queue     │    │
│  └──────────────┘     └──────────────┘     └──────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Transactional Outbox Pattern

### 3.1 Django Model: OutboxMessage

**Location:** `admin/core/models.py`

```python
class OutboxMessage(models.Model):
    """Transactional Outbox for guaranteed message delivery."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    idempotency_key = models.CharField(max_length=255, unique=True, db_index=True)
    
    # Message metadata
    topic = models.CharField(max_length=255, db_index=True)
    partition_key = models.CharField(max_length=255, null=True, blank=True)
    
    # Payload
    payload = models.JSONField()
    headers = models.JSONField(default=dict)
    
    # State tracking
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    published_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)
    
    # Retry logic
    attempts = models.IntegerField(default=0)
    max_attempts = models.IntegerField(default=5)
    next_retry_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(null=True, blank=True)
    
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PUBLISHED = "published", "Published"
        FAILED = "failed", "Failed"
        DEAD = "dead", "Dead Letter"
    
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    
    class Meta:
        db_table = "outbox_messages"
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["topic", "status"]),
            models.Index(fields=["next_retry_at"]),
        ]
```

### 3.2 Usage Pattern

```python
from django.db import transaction

@transaction.atomic
def remember_memory(payload: dict, tenant_id: str):
    """Store memory with guaranteed delivery to SomaBrain."""
    
    # Generate idempotency key
    idempotency_key = f"memory:{tenant_id}:{payload['id']}"
    
    # 1. Create the memory record
    memory = Memory.objects.create(
        tenant_id=tenant_id,
        payload=payload,
    )
    
    # 2. Create outbox entry IN SAME TRANSACTION
    OutboxMessage.objects.create(
        idempotency_key=idempotency_key,
        topic="somabrain.memory.remember",
        partition_key=tenant_id,
        payload={
            "memory_id": str(memory.id),
            "tenant_id": tenant_id,
            "payload": payload,
        },
        headers={
            "idempotency_key": idempotency_key,
            "source": "somaagent01",
        }
    )
    
    return memory
```

---

## 4. Outbox Publisher Service

### 4.1 Publisher Worker

**Location:** `services/common/outbox_publisher.py`

```python
class OutboxPublisher:
    """Publishes pending outbox messages to Kafka with exactly-once semantics."""
    
    BATCH_SIZE = 100
    POLL_INTERVAL = 1.0  # seconds
    
    async def run(self):
        """Main publisher loop."""
        while True:
            try:
                await self._publish_batch()
            except Exception as e:
                logger.error(f"Outbox publisher error: {e}")
            await asyncio.sleep(self.POLL_INTERVAL)
    
    @transaction.atomic
    async def _publish_batch(self):
        """Publish a batch of pending messages."""
        # Lock rows for update to prevent duplicate publishing
        messages = OutboxMessage.objects.select_for_update(skip_locked=True).filter(
            status=OutboxMessage.Status.PENDING,
            next_retry_at__lte=timezone.now(),
        ).order_by("created_at")[:self.BATCH_SIZE]
        
        for message in messages:
            try:
                await self._publish_message(message)
                message.status = OutboxMessage.Status.PUBLISHED
                message.published_at = timezone.now()
                message.save()
            except Exception as e:
                self._handle_failure(message, e)
```

### 4.2 Kafka Configuration

```python
KAFKA_PRODUCER_CONFIG = {
    "bootstrap_servers": settings.KAFKA_BOOTSTRAP_SERVERS,
    "enable_idempotence": True,  # EXACTLY-ONCE
    "acks": "all",               # Wait for all replicas
    "retries": 10,
    "max_in_flight_requests_per_connection": 1,
}
```

---

## 5. Dead Letter Queue

### 5.1 DLQ Topic Structure

| Topic | Purpose |
|-------|---------|
| `somabrain.memory.dlq` | Failed memory operations |
| `conversation.inbound.dlq` | Failed conversation messages |
| `tool.requests.dlq` | Failed tool executions |

### 5.2 DLQ Handler

```python
class DLQHandler:
    """Handles dead letter queue messages for manual review."""
    
    async def process_dlq_message(self, message: dict):
        """Process a DLQ message."""
        # Store in Django for admin review
        DeadLetterMessage.objects.create(
            original_topic=message["original_topic"],
            payload=message["payload"],
            error=message["error"],
            attempts=message["attempts"],
        )
        
        # Alert operations team
        await self._send_alert(message)
```

---

## 6. Idempotency Keys

### 6.1 Key Generation Standards

| Operation | Key Format |
|-----------|------------|
| Memory Remember | `memory:{tenant_id}:{memory_id}` |
| Memory Recall | `recall:{tenant_id}:{query_hash}:{timestamp_bucket}` |
| Conversation Message | `conv:{conversation_id}:{message_id}` |
| Tool Execution | `tool:{execution_id}` |

### 6.2 Idempotency Enforcement

```python
class IdempotencyMiddleware:
    """Ensures operations are processed exactly once."""
    
    async def check_and_set(self, key: str, ttl: int = 86400) -> bool:
        """
        Check if operation was already processed.
        Returns True if NEW (should process), False if DUPLICATE (skip).
        """
        # Use Redis SETNX for atomic check-and-set
        result = await redis.set(f"idempotency:{key}", "1", nx=True, ex=ttl)
        return result is not None
```

---

## 7. Components Affected

### 7.1 Core Services

| Service | Changes Required |
|---------|------------------|
| `services/gateway/` | Add outbox for conversation messages |
| `services/conversation_worker/` | Consume with exactly-once, use outbox for memory |
| `services/tool_executor/` | Outbox for tool results |
| `services/common/` | Outbox publisher, DLQ handler |

### 7.2 Django Models

| Model | Location | Purpose |
|-------|----------|---------|
| `OutboxMessage` | `admin/core/models.py` | Transactional outbox |
| `DeadLetterMessage` | `admin/core/models.py` | DLQ storage |
| `IdempotencyRecord` | `admin/core/models.py` | Idempotency tracking |

### 7.3 Kafka Topics

| Topic | Partitions | Replication | Exactly-Once |
|-------|------------|-------------|--------------|
| `conversation.inbound` | 12 | 3 | ✅ |
| `somabrain.memory.remember` | 6 | 3 | ✅ |
| `tool.requests` | 6 | 3 | ✅ |
| `*.dlq` | 3 | 3 | ✅ |

---

## 8. Implementation Phases

### Phase 1: Core Infrastructure (Priority: CRITICAL)
- [ ] Create OutboxMessage Django model
- [ ] Create DeadLetterMessage Django model
- [ ] Run migrations
- [ ] Implement OutboxPublisher service

### Phase 2: Memory Operations
- [ ] Refactor memory store to use outbox
- [ ] Add idempotency keys to all memory operations
- [ ] Implement DLQ for memory failures

### Phase 3: Conversation Flow
- [ ] Refactor conversation worker to use outbox
- [ ] Add idempotency to message processing
- [ ] Implement exactly-once consumer

### Phase 4: Tool Execution
- [ ] Refactor tool executor to use outbox
- [ ] Add idempotency to tool results
- [ ] Implement DLQ for tool failures

### Phase 5: Monitoring & Alerting
- [ ] Prometheus metrics for outbox depth
- [ ] DLQ depth alerting
- [ ] Sync lag monitoring

---

## 9. Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `outbox_messages_pending` | Gauge | Pending messages in outbox |
| `outbox_messages_published_total` | Counter | Successfully published |
| `outbox_messages_failed_total` | Counter | Failed after max retries |
| `outbox_publish_latency_seconds` | Histogram | Time to publish |
| `dlq_messages_total` | Counter | Messages in DLQ |

---

## 10. Guarantees

✅ **Atomicity** - Message stored in same transaction as business data
✅ **Durability** - PostgreSQL WAL ensures no loss on crash
✅ **Exactly-Once** - Kafka idempotence + consumer offsets
✅ **Idempotency** - Duplicate operations are safely ignored
✅ **Visibility** - All failures tracked in DLQ for review

---

**Last Updated:** 2025-12-24
**Maintained By:** Architecture Team
