# Resilience & Degradation Architecture

**Document ID:** SA01-RESILIENCE-ARCHITECTURE-2025-12
**Version:** 1.0
**Created:** 2025-12-24
**Status:** CANONICAL — Architectural Standard

---

## 1. Executive Summary

SomaAgent01 implements a **comprehensive resilience architecture** ensuring the agent remains operational even when critical services are unavailable.

### Core Principles
1. **NEVER STOP RESPONDING** - Agent continues even when dependencies fail
2. **ZERO DATA LOSS** - All data queued and synced on recovery
3. **AUTOMATIC FAILOVER** - LLM and service switching without manual intervention
4. **CENTRALIZED MONITORING** - Single source of truth for all service health
5. **PROACTIVE NOTIFICATIONS** - Kafka/Django-based alerting system

---

## 2. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     SOMAAGENT01 RESILIENCE LAYER                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                   DEGRADATION MONITOR                             │   │
│  │                   (Central Health Hub)                            │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐    │   │
│  │  │SomaBrain│ │Database │ │  Kafka  │ │  Redis  │ │   LLM   │    │   │
│  │  │ Health  │ │ Health  │ │ Health  │ │ Health  │ │ Health  │    │   │
│  │  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘    │   │
│  │       │           │           │           │           │          │   │
│  │       └───────────┴───────────┴───────────┴───────────┘          │   │
│  │                           │                                       │   │
│  │                   ┌───────▼───────┐                              │   │
│  │                   │  Cascading    │                              │   │
│  │                   │  Failure      │                              │   │
│  │                   │  Detection    │                              │   │
│  │                   └───────┬───────┘                              │   │
│  │                           │                                       │   │
│  │                   ┌───────▼───────┐                              │   │
│  │                   │ Notification  │──────▶ Kafka Topic           │   │
│  │                   │   Service     │──────▶ Django ORM            │   │
│  │                   └───────────────┘──────▶ Webhooks/Logs         │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    SERVICE-SPECIFIC DEGRADATION                   │   │
│  ├──────────────────────────────────────────────────────────────────┤   │
│  │                                                                    │   │
│  │  ┌────────────────────┐      ┌────────────────────┐              │   │
│  │  │ SomaBrain Degraded │      │    LLM Degraded    │              │   │
│  │  │                    │      │                    │              │   │
│  │  │ • Queue to         │      │ • Switch provider  │              │   │
│  │  │   PendingMemory    │      │ • Use fallback     │              │   │
│  │  │ • Session-only     │      │   chain            │              │   │
│  │  │   context          │      │ • Record in        │              │   │
│  │  │ • Skip cognitive   │      │   circuit breaker  │              │   │
│  │  │   enrichment       │      │                    │              │   │
│  │  │ • Auto-sync on     │      │                    │              │   │
│  │  │   recovery         │      │                    │              │   │
│  │  └────────────────────┘      └────────────────────┘              │   │
│  │                                                                    │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Components

### 3.1 DegradationMonitor (`services/common/degradation_monitor.py`)

Central health monitoring hub that tracks all service health.

**Monitored Components:**
| Component | Health Check Method | Circuit Breaker |
|-----------|---------------------|-----------------|
| `somabrain` | HTTP `/health` | ✅ |
| `database` | Django ORM `SELECT 1` | ✅ |
| `kafka` | AIOKafka producer connect | ✅ |
| `redis` | Redis `PING` | ❌ |
| `temporal` | gRPC system info | ❌ |
| `llm` | LLMDegradationService | ✅ |
| `gateway` | Generic | ❌ |

**Dependency Graph:**
```python
SERVICE_DEPENDENCIES = {
    "gateway": ["database", "redis", "kafka", "temporal"],
    "tool_executor": ["database", "kafka", "somabrain", "temporal", "llm"],
    "conversation_worker": ["database", "kafka", "somabrain", "redis", "temporal", "llm"],
    "auth_service": ["database", "redis"],
}
```

### 3.2 LLMDegradationService (`services/common/llm_degradation.py`)

Automatic LLM provider failover with fallback chains.

**Fallback Chains:**
```python
DEFAULT_CHAINS = {
    "chat": ["openai/gpt-4o", "anthropic/claude-3-5-sonnet", "openrouter/qwen-2.5-72b"],
    "coding": ["anthropic/claude-3-5-sonnet", "openai/gpt-4o", "deepseek/deepseek-coder"],
    "fast": ["openai/gpt-4o-mini", "anthropic/claude-3-haiku", "llama-3.1-8b"],
    "embedding": ["openai/text-embedding-3-small", "local/sentence-transformers"],
}
```

**Provider Status Tracking:**
```python
class LLMProviderStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
```

### 3.3 DegradationNotificationService (`services/common/degradation_notifications.py`)

Centralized notification system for degradation events.

**Notification Channels:**
| Channel | Description |
|---------|-------------|
| `DATABASE` | Django ORM via OutboxMessage |
| `KAFKA` | Topic: `degradation.events` |
| `WEBHOOK` | Registered callbacks |
| `LOG` | Structured JSON logging |

### 3.4 Zero Data Loss Models (`admin/core/models.py`)

Django models for guaranteed data persistence.

| Model | Purpose |
|-------|---------|
| `OutboxMessage` | Transactional outbox for Kafka |
| `DeadLetterMessage` | Failed message storage |
| `IdempotencyRecord` | Exactly-once tracking |
| `PendingMemory` | SomaBrain degradation queue |

---

## 4. Degradation Flows

### 4.1 SomaBrain Unavailable

```
User Message
    │
    ▼
┌─────────────────────────────────────────────────────┐
│ Conversation Worker                                  │
│                                                      │
│ 1. Check DegradationMonitor.components["somabrain"] │
│    → status = UNAVAILABLE                           │
│                                                      │
│ 2. Build context (degraded mode):                   │
│    • Use session messages only (last N turns)       │
│    • Skip long-term memory recall                   │
│    • Skip neuromodulation                           │
│    • Skip cognitive enrichment                      │
│                                                      │
│ 3. Call LLM (still works!)                          │
│    → Response generated                             │
│                                                      │
│ 4. Store memory (guaranteed):                       │
│    • Create PendingMemory record                    │
│    • Idempotency key prevents duplicates            │
│                                                      │
│ 5. Return response to user                          │
└─────────────────────────────────────────────────────┘
    │
    ▼
User receives response (agent NEVER stops)
```

### 4.2 LLM Provider Unavailable

```
LLM Call Request
    │
    ▼
┌─────────────────────────────────────────────────────┐
│ LLMDegradationService                                │
│                                                      │
│ 1. get_available_model("chat")                      │
│    • Check primary: openai/gpt-4o → UNAVAILABLE     │
│    • Check fallback 1: anthropic/claude → HEALTHY   │
│    • Return: anthropic/claude-3-5-sonnet            │
│                                                      │
│ 2. Create LiteLLMChatWrapper with fallback model    │
│                                                      │
│ 3. On success: record_success()                     │
│    On failure: record_failure() → try next fallback │
└─────────────────────────────────────────────────────┘
    │
    ▼
LLM response received (via fallback provider)
```

### 4.3 SomaBrain Recovery

```
SomaBrain comes back online
    │
    ▼
┌─────────────────────────────────────────────────────┐
│ sync_memories Management Command                     │
│                                                      │
│ 1. Detect SomaBrain recovery (health check passes)  │
│                                                      │
│ 2. Query PendingMemory.objects.filter(synced=False) │
│                                                      │
│ 3. For each pending memory:                         │
│    • Call SomaBrainClient.remember()                │
│    • Mark as synced on success                      │
│    • Increment attempts on failure                  │
│                                                      │
│ 4. All memories synced - cognitive richness restored│
└─────────────────────────────────────────────────────┘
```

---

## 5. Django Management Commands

### 5.1 Outbox Publisher
```bash
python manage.py publish_outbox --batch-size=100 --interval=1
```

### 5.2 Memory Sync
```bash
python manage.py sync_memories --batch-size=50 --interval=5
```

---

## 6. Kafka Topics

| Topic | Purpose | Partitions |
|-------|---------|------------|
| `degradation.events` | Service health changes | 3 |
| `somabrain.memory.remember` | Memory storage requests | 6 |
| `conversation.inbound` | User messages | 12 |
| `tool.requests` | Tool execution requests | 6 |
| `*.dlq` | Dead letter queues | 3 |

---

## 7. Metrics (Prometheus)

| Metric | Type | Labels |
|--------|------|--------|
| `service_health_state` | Gauge | service |
| `service_degradation_level` | Gauge | service |
| `service_latency_seconds` | Histogram | service |
| `service_error_rate` | Gauge | service |
| `cascading_failures_total` | Counter | source_service, affected_service |
| `outbox_messages_pending` | Gauge | - |
| `dlq_messages_total` | Counter | topic |

---

## 8. Configuration

### 8.1 Django Settings

```python
# Degradation thresholds
DEGRADATION_RESPONSE_TIME_THRESHOLD = 5.0  # seconds
DEGRADATION_ERROR_RATE_THRESHOLD = 0.1     # 10%
DEGRADATION_CIRCUIT_FAILURE_RATE = 0.3     # 30%

# LLM fallback chains
LLM_FALLBACK_CHAINS = {
    "chat": {
        "primary": "openai/gpt-4o",
        "fallbacks": ["anthropic/claude-3-5-sonnet"],
    },
}

# Notification settings
DEGRADATION_NOTIFICATION_CHANNELS = ["database", "kafka", "log"]
DEGRADATION_SUPPRESSION_WINDOW_MINUTES = 5
```

---

## 9. Files Created

| File | Purpose |
|------|---------|
| `services/common/degradation_monitor.py` | Central health monitoring |
| `services/common/degradation_notifications.py` | Notification service |
| `services/common/llm_degradation.py` | LLM failover service |
| `admin/core/models.py` | ZDL Django models |
| `admin/core/signals.py` | Outbox signals |
| `admin/core/management/commands/publish_outbox.py` | Outbox publisher |
| `admin/core/management/commands/sync_memories.py` | Memory sync |
| `docs/ZERO_DATA_LOSS_ARCHITECTURE.md` | ZDL specification |
| `docs/RESILIENCE_ARCHITECTURE.md` | This document |

---

## 10. Guarantees

| Guarantee | Implementation |
|-----------|----------------|
| **Agent Never Stops** | Degraded mode with session-only context |
| **Zero Data Loss** | Transactional outbox + PendingMemory |
| **Automatic Failover** | LLM fallback chains |
| **Exactly-Once** | Idempotency keys + Kafka txn |
| **Visibility** | Django Admin + Prometheus + Kafka |

---

**Last Updated:** 2025-12-24
**Maintained By:** Architecture Team
