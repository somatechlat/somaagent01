# Software Requirements Specification (SRS)
# Intelligent Model Routing System (IMRS)

**Document Version**: 1.1.0
**Date**: 2026-01-14
**Status**: APPROVED
**Author**: SOMA Engineering
**Standard**: ISO/IEC 29148:2018

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Memory Architecture](#2-memory-architecture)
3. [System Features](#3-system-features)
4. [Data Model](#4-data-model)
5. [API Specification](#5-api-specification)
6. [User Interface Requirements](#6-user-interface-requirements)
7. [Non-Functional Requirements](#7-non-functional-requirements)
8. [Appendices](#8-appendices)

---

## 1. Introduction

### 1.1 Purpose

This document specifies the requirements for the **Intelligent Model Routing System (IMRS)**, a subsystem of SomaAgent01 that enables:

1. **Provider Management** - Users create and configure LLM providers (OpenRouter, OpenAI, custom)
2. **Model Catalog** - Automatic discovery and manual registration of LLM models
3. **Agent Configuration** - Per-agent model enablement based on roles/profiles
4. **Feedback Collection** - User and implicit feedback on model performance
5. **Intelligent Routing** - Experience-based model selection using historical performance

### 1.2 Scope

| In Scope | Out of Scope |
|----------|--------------|
| Provider CRUD operations | Provider billing integration |
| Model discovery from provider APIs | Model fine-tuning |
| Per-agent model configuration | Multi-tenant billing |
| User feedback collection (👍/👎) | A/B testing framework |
| Task type detection via tools | Custom embedding models |
| Performance-based model selection | Model inference hosting |

### 1.3 Definitions

| Term | Definition |
|------|------------|
| **Provider** | An LLM API service (OpenRouter, OpenAI, Anthropic, custom) |
| **Model** | A specific LLM available from a provider (gpt-4o, claude-3.5-sonnet) |
| **Agent** | A configured AI assistant with specific capabilities |
| **Capsule** | Agent identity and governance configuration |
| **Task Type** | Category of user request (code, slides, analysis, etc.) |
| **Feedback** | User rating (0-1) of model response quality |

---

## 2. Memory Architecture

### 2.1 Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SOMA MEMORY ARCHITECTURE                                  │
└─────────────────────────────────────────────────────────────────────────────┘

  Agent (L4)                    Kafka WAL                   MemoryReplicator
┌──────────────┐            ┌──────────────┐            ┌──────────────┐
│              │            │              │            │              │
│ 1. Store     │──publish──▶│ memory.wal   │──consume──▶│ SYNC to      │
│    TRACE to  │            │ (durable)    │            │ SomaBrain    │
│    PostgreSQL│            │              │            │              │
│              │            │ Queued until │            │ Updates      │
│ 2. SomaBrain │            │ consumed     │            │ synced=true  │
│    .remember │            │              │            │              │
└──────────────┘            └──────────────┘            └──────────────┘
       │                                                        │
       ▼                                                        ▼
┌──────────────┐                                        ┌──────────────┐
│ PostgreSQL   │         SomaBrain DOWN?                │ SomaBrain    │
│ (REGISTRAR)  │         → Events queue in Kafka        │ (L3)         │
│              │         → PostgreSQL has trace         │              │
│ synced=false │         → NOTHING LOST                 │              │
└──────────────┘                                        └──────────────┘
                                                               │
                                                               ▼
                                                        ┌──────────────┐
                                                        │ SFM (L2)     │
                                                        │ Vectors      │
                                                        └──────────────┘
```

### 2.2 Layer Access Rules

| Caller | Can Access | Via | Direct Access |
|--------|------------|-----|---------------|
| Agent (L4) | SomaBrain (L3) | `SomaBrainClient` | ✅ |
| Agent (L4) | SFM (L2) | - | ❌ **NEVER** |
| Brain (L3) | SFM (L2) | `BrainMemoryFacade` | ✅ |

### 2.3 PostgreSQL as Trace Registrar

PostgreSQL Message table stores **TRACES** only:
- Message ID, role, token_count, model, latency
- `synced_to_brain` flag for MemoryReplicator
- Full content optionally encrypted

### 2.4 SAAS Deployment Modes

| Mode | Config | Memory Access |
|------|--------|---------------|
| Standard SAAS (HTTP) | `SOMA_SAAS_MODE=true` | Agent → HTTP → Brain → HTTP → SFM |
| Unified SAAS (Direct) | `SOMA_SAAS_MODE=direct` | Agent → `BrainMemoryFacade` → SFM (in-process) |

### 2.5 Degradation Mode

When SomaBrain is unavailable:
1. PostgreSQL trace is stored (always succeeds)
2. Kafka WAL event queued
3. MemoryReplicator retries when Brain available
4. **NOTHING IS EVER LOST**

---

## 3. System Features

### 3.1 FR-01: Provider Management

#### 3.1.1 Description
Platform administrators can create, update, and delete LLM providers.

#### 3.1.2 Functional Requirements

| ID | Requirement |
|----|-------------|
| FR-01.1 | System SHALL allow creation of providers with: id, display_name, api_base, models_endpoint |
| FR-01.2 | System SHALL store API keys in Vault at path `secret/llm/{provider_id}` |
| FR-01.3 | System SHALL support provider types: `openrouter`, `openai`, `anthropic`, `azure`, `custom` |
| FR-01.4 | System SHALL sync models by calling provider's models endpoint |
| FR-01.5 | System SHALL track last_synced timestamp for each provider |

---

### 3.2 FR-02: Model Catalog

#### 3.2.1 Functional Requirements

| ID | Requirement |
|----|-------------|
| FR-02.1 | System SHALL store models with: id, provider_id, external_id, display_name |
| FR-02.2 | System SHALL store capabilities as JSONB: `["text", "vision", "code", ...]` |
| FR-02.3 | System SHALL store cost_tier enum: `free`, `low`, `standard`, `premium` |
| FR-02.4 | System SHALL store priority (0-100) for routing weight |
| FR-02.5 | System SHALL store ctx_length (context window size) |

---

### 3.3 FR-03: Agent Model Configuration

#### 3.3.1 Functional Requirements

| ID | Requirement |
|----|-------------|
| FR-03.1 | System SHALL store agent-model mappings with: agent_id, model_id, is_enabled |
| FR-03.2 | System SHALL support priority_override per agent-model pair |
| FR-03.3 | System SHALL filter models by agent's tenant_id |
| FR-03.4 | System SHALL support role-based model restrictions via Capsule.body.allowed_models |

---

### 3.4 FR-04: Feedback Collection

#### 3.4.1 Functional Requirements

| ID | Requirement |
|----|-------------|
| FR-04.1 | System SHALL store rating (0.0-1.0) on Message model |
| FR-04.2 | System SHALL provide API: `POST /api/v2/chat/messages/{id}/feedback` |
| FR-04.3 | System SHALL capture implicit feedback: regenerate=0.0, copy=1.0 |
| FR-04.4 | System SHALL sync feedback to SomaBrain for learning |
| FR-04.5 | System SHALL store feedback_type: `explicit`, `implicit`, `self_eval` |

---

### 3.5 FR-05: Task Type Detection

#### 3.5.1 Detection Sources

| Source | Confidence | Example |
|--------|------------|---------|
| Tool invocation | HIGH | `code_execute` → task_type="code" |
| Attachment MIME | HIGH | `.pdf` → task_type="document" |
| Message keywords | MEDIUM | "PowerPoint" → task_type="slides" |

#### 3.5.2 Tool → Task Type Mapping

```python
TOOL_TO_TASK_TYPE = {
    "code_execute": "code",
    "document_ingest": "document",
    "http_fetch": "research",
    "file_read": "file_ops",
    "canvas_append": "canvas",
    "dalle3_image_gen": "image_gen",
    "mermaid_diagram": "diagram",
    "playwright_screenshot": "screenshot",
}
```

---

### 3.6 FR-06: Intelligent Model Routing

#### 3.6.1 Routing Algorithm

```
INPUTS:
  - required_capabilities: set[str]
  - detected_task_type: str
  - agent_id, tenant_id, capsule_body

ALGORITHM:
  1. Get agent's enabled models from AgentModelConfig
  2. Filter by required_capabilities
  3. Filter by capsule.body.allowed_models
  4. Query performance: AVG(rating) by task_type
  5. score = base_priority * 0.3 + experience_score * 0.7
  6. Return model with highest score
```

---

## 4. Data Model

### 4.1 Message Model (EXTENDED)

```python
class Message(models.Model):
    """Chat message record (TRACE REGISTRAR)."""

    # Core fields (existing)
    id = models.UUIDField(primary_key=True)
    conversation_id = models.UUIDField(db_index=True)
    role = models.CharField(max_length=20)
    content = models.TextField()  # TODO: Encrypt
    token_count = models.IntegerField(default=0)
    model = models.CharField(max_length=100, null=True)
    latency_ms = models.IntegerField(null=True)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    # IMRS fields (NEW)
    rating = models.FloatField(null=True)  # 0.0-1.0
    task_type = models.CharField(max_length=50, null=True)
    tools_used = models.JSONField(default=list)
    feedback_type = models.CharField(max_length=20, null=True)
    feedback_at = models.DateTimeField(null=True)

    # Sync tracking (NEW)
    synced_to_brain = models.BooleanField(default=False)
```

### 4.2 Indexes

```sql
CREATE INDEX ix_message_task_rating ON messages(task_type, rating);
CREATE INDEX ix_message_model_task ON messages(model, task_type);
CREATE INDEX ix_message_synced ON messages(synced_to_brain);
```

---

## 5. API Specification

### 5.1 Feedback API

```
POST /api/v2/chat/messages/{message_id}/feedback
Authorization: Bearer {user_token}
Content-Type: application/json

{
  "rating": 1.0,
  "feedback_type": "explicit"
}

Response 200:
{
  "message_id": "msg-123",
  "rating": 1.0,
  "recorded_at": "2026-01-14T10:30:00Z"
}
```

---

## 6. User Interface Requirements

### 6.1 Chat UI: Feedback

| Element | Behavior |
|---------|----------|
| 👍 Button | On assistant message, submits rating=1.0 |
| 👎 Button | On assistant message, submits rating=0.0 |
| Regenerate | Implicit negative feedback |
| Copy | Implicit positive feedback |

---

## 7. Non-Functional Requirements

### 7.1 Performance

| Metric | Requirement |
|--------|-------------|
| Model routing latency | < 50ms P95 |
| Memory store | Non-blocking (async) |
| Degradation recovery | Automatic via MemoryReplicator |

### 7.2 Security

| Requirement | Implementation |
|-------------|----------------|
| API key storage | Vault only (VIBE Rule 164) |
| Memory content | Encrypted in PostgreSQL trace |
| Layer isolation | Agent cannot access SFM directly |

---

## 8. Appendices

### 8.1 Files Modified

| File | Change |
|------|--------|
| `admin/chat/models.py` | Added IMRS fields, synced_to_brain |
| `services/common/chat_memory.py` | Uses SomaBrainClient, no direct SFM |
| `services/common/chat_service.py` | Removed memory_url, uses SomaBrain |

### 8.2 Migration Required

```bash
python manage.py makemigrations chat
python manage.py migrate
```

---

**END OF DOCUMENT**
