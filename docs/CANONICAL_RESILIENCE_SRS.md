# CANONICAL RESILIENCE SRS

**Document ID:** SA01-SRS-RESILIENCE-2025-12
**Version:** 1.0
**Created:** 2025-12-24
**Status:** CANONICAL — Single Source of Truth

> **MERGED FROM:** RESILIENCE_ARCHITECTURE.md, ZERO_DATA_LOSS_ARCHITECTURE.md, ZERO_DATA_LOSS_IMPLEMENTATION.md, AGENT_SERVICE_MAP.md, INFRASTRUCTURE_INTEGRATION.md

---

## 1. Executive Summary

This SRS defines the **complete resilience architecture** for SomaAgent01, ensuring:
- **Agent NEVER stops responding** to users
- **Zero data loss** via transactional outbox pattern
- **Automatic failover** for all external services
- **Reusable degradation handling** across all agent components

---

## 2. Core Principles

| Principle | Description |
|-----------|-------------|
| **NEVER STOP** | Agent continues responding even when dependencies fail |
| **ZERO DATA LOSS** | All data queued and synced on recovery |
| **AUTOMATIC FAILOVER** | LLM/audio/storage switch without intervention |
| **CENTRALIZED MONITORING** | Single DegradationMonitor for all services |
| **REUSABLE PATTERNS** | Same degradation handling across all journeys |

---

## 3. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     SOMAAGENT01 RESILIENCE LAYER                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                     CENTRALIZED DEGRADATION MONITOR                     │ │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐          │ │
│  │  │SomaBrain│ │Database │ │  Kafka  │ │   LLM   │ │  Audio  │          │ │
│  │  │ Status  │ │ Status  │ │ Status  │ │ Status  │ │ Status  │          │ │
│  │  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘          │ │
│  │       │           │           │           │           │                │ │
│  │       └───────────┴───────────┴───────────┴───────────┘                │ │
│  │                           │                                             │ │
│  │               ┌───────────▼───────────┐                                │ │
│  │               │  DegradationStatus    │◄──────────────────────────────│ │
│  │               │  (Agent-Wide State)   │  ALL JOURNEYS READ THIS       │ │
│  │               └───────────────────────┘                                │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                    ZERO DATA LOSS LAYER                                 │ │
│  │  ┌────────────────────────────────────────────────────────────────────┐│ │
│  │  │ OutboxMessage ──▶ publish_outbox ──▶ Kafka (exactly-once)          ││ │
│  │  │ PendingMemory ──▶ sync_memories ──▶ SomaBrain (on recovery)        ││ │
│  │  │ DeadLetterMessage ──▶ Admin visibility + replay                    ││ │
│  │  │ IdempotencyRecord ──▶ Prevents duplicate processing                ││ │
│  │  └────────────────────────────────────────────────────────────────────┘│ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Monitored Services

| Service | Health Check | Circuit Breaker | Fallback Mode |
|---------|--------------|-----------------|---------------|
| **SomaBrain** | HTTP `/health` | ✅ | PendingMemory queue |
| **PostgreSQL** | `SELECT 1` | ✅ | ❌ Critical |
| **Kafka** | Producer connect | ✅ | OutboxMessage queue |
| **Redis** | `PING` | ❌ | Session-only |
| **Temporal** | gRPC system info | ❌ | Queue tasks |
| **LLM Providers** | LLMDegradationService | ✅ | Fallback chain |
| **Audio TTS** | MultimodalDegradation | ✅ | browser/native |
| **Audio STT** | MultimodalDegradation | ✅ | browser/native |
| **Storage** | MultimodalDegradation | ✅ | local/redis |

---

## 5. Fallback Chains

### 5.1 LLM Providers

| Use Case | Primary | Fallback 1 | Fallback 2 | Fallback 3 |
|----------|---------|------------|------------|------------|
| **Chat** | openai/gpt-4o | anthropic/claude-3-5 | openrouter/qwen | - |
| **Coding** | anthropic/claude-3-5 | openai/gpt-4o | deepseek/coder | - |
| **Fast** | openai/gpt-4o-mini | claude-3-haiku | llama-3.1-8b | - |

### 5.2 Audio Providers

| Service | Primary | Fallback 1 | Fallback 2 | Fallback 3 |
|---------|---------|------------|------------|------------|
| **TTS** | elevenlabs | openai/tts-1 | kokoro/local | browser/native |
| **STT** | openai/whisper | deepgram | browser/native | - |

### 5.3 Storage Providers

| Service | Primary | Fallback 1 | Fallback 2 |
|---------|---------|------------|------------|
| **Storage** | s3 | local/filesystem | redis/temp |

---

## 6. Django Models (Zero Data Loss)

### 6.1 OutboxMessage
```python
class OutboxMessage(models.Model):
    idempotency_key = models.CharField(max_length=255, unique=True)
    topic = models.CharField(max_length=255)
    partition_key = models.CharField(max_length=255)
    payload = models.JSONField()
    headers = models.JSONField(default=dict)
    status = models.CharField(choices=STATUS_CHOICES, default='pending')
    attempts = models.IntegerField(default=0)
    max_attempts = models.IntegerField(default=5)
    created_at = models.DateTimeField(auto_now_add=True)
    published_at = models.DateTimeField(null=True)
```

### 6.2 PendingMemory
```python
class PendingMemory(models.Model):
    tenant_id = models.CharField(max_length=255)
    agent_id = models.CharField(max_length=255)
    content = models.TextField()
    metadata = models.JSONField(default=dict)
    synced = models.BooleanField(default=False)
    attempts = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
```

### 6.3 IdempotencyRecord
```python
class IdempotencyRecord(models.Model):
    key = models.CharField(max_length=255, unique=True)
    result = models.JSONField(null=True)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
```

---

## 7. Infrastructure Integration

### 7.1 Environment Variables (from docker-compose.yml)

| Variable | Value | Used For |
|----------|-------|----------|
| `SA01_KAFKA_BOOTSTRAP_SERVERS` | `kafka:9092` | Kafka producer |
| `SA01_DATABASE_URL` | `postgres:5432` | Django ORM |
| `SA01_REDIS_URL` | `redis:6379` | Degradation check |
| `SA01_SOMABRAIN_URL` | `somabrain:9696` | Memory operations |
| `SA01_TEMPORAL_HOST` | `temporal:7233` | Workflow engine |

### 7.2 Kafka Topics

| Topic | Purpose |
|-------|---------|
| `conversation.inbound` | User messages |
| `degradation.events` | Service health alerts |
| `somabrain.memory.remember` | Memory storage |
| `upload.retry` | Failed uploads |
| `backup.tasks` | Backup operations |
| `*.dlq` | Dead letter queues |

---

## 8. Reusable Degradation Pattern

**Every journey MUST check degradation status before operations:**

```python
# Pattern used across ALL agent components
async def handle_operation(request):
    # 1. Check degradation status
    status = await degradation_monitor.get_status()
    
    # 2. Adjust behavior based on status
    if status.somabrain == UNAVAILABLE:
        # Use session-only context
        context = get_session_context(request)
    else:
        # Use full memory
        context = await somabrain.recall(request)
    
    # 3. Get available LLM (with fallback)
    llm = await llm_degradation.get_available_model("chat")
    
    # 4. Execute operation
    result = await llm.generate(context)
    
    # 5. Store with ZDL guarantee
    await outbox_manager.create_entry(
        topic="memory.remember",
        payload=result,
    )
    
    return result
```

---

## 9. Degradation Scenarios

### Scenario 1: SomaBrain Unavailable
- **Detection:** HTTP timeout
- **Response:** PendingMemory queue
- **User Impact:** Session-only context (degraded richness)
- **Recovery:** sync_memories auto-syncs

### Scenario 2: LLM Provider Unavailable
- **Detection:** Consecutive failures
- **Response:** Automatic fallback
- **User Impact:** None (transparent)
- **Recovery:** Primary monitored

### Scenario 3: Audio Service Unavailable
- **Detection:** TTS/STT failures
- **Response:** Browser native fallback
- **User Impact:** "Voice in fallback mode" message
- **Recovery:** Primary monitored

### Scenario 4: Storage Unavailable
- **Detection:** S3/filesystem failure
- **Response:** Queue uploads via Outbox
- **User Impact:** "Upload queued" message
- **Recovery:** Automatic retry

### Scenario 5: Kafka Unavailable
- **Detection:** Producer connect failure
- **Response:** OutboxMessage stores in PostgreSQL
- **User Impact:** None (queued)
- **Recovery:** publish_outbox flushes

---

## 10. Django Management Commands

| Command | Purpose | Frequency |
|---------|---------|-----------|
| `python manage.py publish_outbox` | Flush outbox to Kafka | Every 1s |
| `python manage.py sync_memories` | Sync pending to SomaBrain | Every 5s |

---

## 11. Metrics (Prometheus)

| Metric | Type | Labels |
|--------|------|--------|
| `service_health_state` | Gauge | service |
| `service_degradation_level` | Gauge | service |
| `outbox_messages_pending` | Gauge | - |
| `dlq_messages_total` | Counter | topic |
| `llm_failover_count` | Counter | from_provider, to_provider |

---

## 12. Implementation Files

| File | Purpose |
|------|---------|
| `services/common/degradation_monitor.py` | Central health hub |
| `services/common/degradation_notifications.py` | Kafka/DB alerts |
| `services/common/llm_degradation.py` | LLM failover |
| `services/common/multimodal_degradation.py` | Audio/storage |
| `admin/core/models.py` | ZDL Django models |
| `admin/core/signals.py` | Outbox signals |
| `admin/core/management/commands/publish_outbox.py` | Outbox publisher |
| `admin/core/management/commands/sync_memories.py` | Memory sync |

---

**Last Updated:** 2025-12-24
**Maintained By:** Architecture Team
