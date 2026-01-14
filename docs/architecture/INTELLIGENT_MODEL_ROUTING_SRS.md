# Software Requirements Specification (SRS)
# Intelligent Model Routing System (IMRS)

**Document Version**: 1.0.0
**Date**: 2026-01-14
**Status**: DRAFT
**Author**: SOMA Engineering
**Standard**: ISO/IEC 29148:2018

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Overall Description](#2-overall-description)
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

### 1.4 References

- VIBE Coding Rules v2026
- SomaAgent01 Architecture Documentation
- SomaBrain Integration Specification
- Django ORM Best Practices

---

## 2. Overall Description

### 2.1 Product Perspective

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SOMA STACK                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────┐   ┌─────────────────┐   ┌──────────────────┐              │
│  │   Admin UI  │──▶│  IMRS Backend   │──▶│  Provider APIs   │              │
│  │             │   │                 │   │  (OpenRouter,    │              │
│  │ - Providers │   │ - ProviderMgr   │   │   OpenAI, etc)   │              │
│  │ - Models    │   │ - ModelCatalog  │   └──────────────────┘              │
│  │ - Agents    │   │ - ModelRouter   │                                      │
│  └─────────────┘   │ - FeedbackMgr   │   ┌──────────────────┐              │
│                    │                 │──▶│  HashiCorp Vault │              │
│  ┌─────────────┐   └────────┬────────┘   │  (API Keys)      │              │
│  │  Chat API   │            │            └──────────────────┘              │
│  │             │◀───────────┘                                               │
│  │ send_message│                         ┌──────────────────┐              │
│  │ + feedback  │────────────────────────▶│  SomaBrain       │              │
│  └─────────────┘                         │  (Learning Store)│              │
│                                          └──────────────────┘              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 User Classes and Characteristics

| User Class | Description | Access Level |
|------------|-------------|--------------|
| **Platform Admin** | Manages providers and global model catalog | Full CRUD on providers/models |
| **Tenant Admin** | Configures agents for their organization | Enable/disable models per agent |
| **Agent User** | Interacts with AI agents | Provide feedback on responses |
| **Agent** | AI system making model decisions | Query router, record outcomes |

### 2.3 Operating Environment

- **Backend**: Django 5.x, Python 3.12+
- **Database**: PostgreSQL 16+
- **Secret Storage**: HashiCorp Vault
- **Memory**: SomaBrain (vector storage for learning)
- **API Style**: Django Ninja (REST)

### 2.4 Design Constraints

| Constraint | Rationale |
|------------|-----------|
| VIBE Rule 164 | API keys MUST be stored in Vault, never in DB or env vars |
| VIBE Rule 85 | Django ORM only, no raw SQL |
| VIBE Rule 9 | Single source of truth for model data |
| 650-line limit | No file exceeds 650 lines |

---

## 3. System Features

### 3.1 FR-01: Provider Management

#### 3.1.1 Description
Platform administrators can create, update, and delete LLM providers. Each provider represents an API service that hosts multiple LLM models.

#### 3.1.2 User Stories

| ID | Story | Priority |
|----|-------|----------|
| US-01.1 | As a Platform Admin, I want to add a new provider so that I can use models from that service | P0 |
| US-01.2 | As a Platform Admin, I want to enter my API key securely so that it is stored in Vault | P0 |
| US-01.3 | As a Platform Admin, I want to sync models from a provider so that I can see all available models | P0 |
| US-01.4 | As a Platform Admin, I want to disable a provider so that all its models become unavailable | P1 |
| US-01.5 | As a Platform Admin, I want to create a custom provider with a custom base URL | P1 |

#### 3.1.3 Functional Requirements

| ID | Requirement |
|----|-------------|
| FR-01.1 | System SHALL allow creation of providers with: id, display_name, api_base, models_endpoint |
| FR-01.2 | System SHALL store API keys in Vault at path `secret/llm/{provider_id}` |
| FR-01.3 | System SHALL support provider types: `openrouter`, `openai`, `anthropic`, `azure`, `custom` |
| FR-01.4 | System SHALL sync models by calling provider's models endpoint (e.g., `/v1/models`) |
| FR-01.5 | System SHALL track last_synced timestamp for each provider |
| FR-01.6 | System SHALL allow deactivation of providers (soft delete) |

---

### 3.2 FR-02: Model Catalog

#### 3.2.1 Description
The system maintains a global catalog of all LLM models discovered from providers or manually registered. Models include capability metadata for intelligent routing.

#### 3.2.2 User Stories

| ID | Story | Priority |
|----|-------|----------|
| US-02.1 | As a Platform Admin, I want to see all models from all providers in one view | P0 |
| US-02.2 | As a Platform Admin, I want to manually add a model not auto-discovered | P1 |
| US-02.3 | As a Platform Admin, I want to set capabilities for each model (vision, code, etc.) | P0 |
| US-02.4 | As a Platform Admin, I want to set cost tier (free, low, standard, premium) | P1 |
| US-02.5 | As a Platform Admin, I want to set priority weight for routing | P1 |

#### 3.2.3 Functional Requirements

| ID | Requirement |
|----|-------------|
| FR-02.1 | System SHALL store models with: id, provider_id, external_id, display_name |
| FR-02.2 | System SHALL store capabilities as JSONB: `["text", "vision", "code", "audio", "long_context", "function_calling"]` |
| FR-02.3 | System SHALL store cost_tier enum: `free`, `low`, `standard`, `premium` |
| FR-02.4 | System SHALL store priority (0-100) for routing weight |
| FR-02.5 | System SHALL store ctx_length (context window size) |
| FR-02.6 | System SHALL store pricing_input and pricing_output (per 1M tokens) |
| FR-02.7 | System SHALL support bulk enable/disable by filter (e.g., "all free models") |

---

### 3.3 FR-03: Agent Model Configuration

#### 3.3.1 Description
Tenant administrators configure which models are available to each agent. Agents can only use models explicitly enabled for them.

#### 3.3.2 User Stories

| ID | Story | Priority |
|----|-------|----------|
| US-03.1 | As a Tenant Admin, I want to enable specific models for my agent | P0 |
| US-03.2 | As a Tenant Admin, I want to bulk-enable all free models for my agent | P1 |
| US-03.3 | As a Tenant Admin, I want to set priority overrides per agent | P2 |
| US-03.4 | As a Tenant Admin, I want to disable a model for my agent without affecting others | P0 |
| US-03.5 | As a Tenant Admin, I want to restrict models by role (e.g., only premium for admins) | P2 |

#### 3.3.3 Functional Requirements

| ID | Requirement |
|----|-------------|
| FR-03.1 | System SHALL store agent-model mappings with: agent_id, model_id, is_enabled |
| FR-03.2 | System SHALL support priority_override per agent-model pair |
| FR-03.3 | System SHALL filter models by agent's tenant_id |
| FR-03.4 | System SHALL support role-based model restrictions via Capsule.body.allowed_models |
| FR-03.5 | System SHALL audit all enable/disable actions with enabled_by and enabled_at |

---

### 3.4 FR-04: Feedback Collection

#### 3.4.1 Description
Users provide feedback on AI responses. The system also captures implicit signals (regenerate, copy, abandon). Feedback is used for model performance learning.

#### 3.4.2 User Stories

| ID | Story | Priority |
|----|-------|----------|
| US-04.1 | As a User, I want to rate a response with 👍/👎 so the agent learns | P0 |
| US-04.2 | As a User, I want my "regenerate" action to count as negative feedback | P1 |
| US-04.3 | As a User, I want my "copy" action to count as positive feedback | P2 |
| US-04.4 | As an Agent, I want to self-evaluate task completion | P2 |

#### 3.4.3 Functional Requirements

| ID | Requirement |
|----|-------------|
| FR-04.1 | System SHALL store rating (0.0-1.0) on Message model |
| FR-04.2 | System SHALL provide API: `POST /api/v2/chat/messages/{id}/feedback` |
| FR-04.3 | System SHALL capture implicit feedback: regenerate=0.0, copy=1.0, continue=0.5 |
| FR-04.4 | System SHALL sync feedback to SomaBrain for learning |
| FR-04.5 | System SHALL store feedback_type: `explicit`, `implicit`, `self_eval` |

---

### 3.5 FR-05: Task Type Detection

#### 3.5.1 Description
The system detects the type of task being requested (code, slides, analysis, etc.) based on user message content, attachments, and tool invocations.

#### 3.5.2 Detection Sources

| Source | Confidence | Example |
|--------|------------|---------|
| Tool invocation | HIGH | `code_execute` → task_type="code" |
| Attachment MIME | HIGH | `.pdf` → task_type="document" |
| Message keywords | MEDIUM | "PowerPoint" → task_type="slides" |

#### 3.5.3 Functional Requirements

| ID | Requirement |
|----|-------------|
| FR-05.1 | System SHALL detect task type from tool calls with mapping: `{"code_execute": "code", "document_ingest": "document", ...}` |
| FR-05.2 | System SHALL detect task type from attachment MIME types |
| FR-05.3 | System SHALL detect task type from message keywords as fallback |
| FR-05.4 | System SHALL store detected task_type on Message model |
| FR-05.5 | System SHALL store tools_used as JSONB on Message model |

#### 3.5.4 Tool → Task Type Mapping

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

KEYWORD_TO_TASK_TYPE = {
    "slides": ["powerpoint", "ppt", "presentation", "slides"],
    "code": ["code", "program", "script", "function", "python", "javascript"],
    "analysis": ["analyze", "examine", "investigate", "review"],
    "summarization": ["summarize", "summary", "condense", "tldr"],
    "translation": ["translate", "translation"],
    "image": ["image", "picture", "photo", "diagram"],
    "document": ["document", "report", "paper", "pdf"],
}
```

---

### 3.6 FR-06: Intelligent Model Routing

#### 3.6.1 Description
When processing a request, the system selects the optimal model based on: required capabilities, agent's enabled models, capsule constraints, cost tier preference, and historical performance.

#### 3.6.2 User Stories

| ID | Story | Priority |
|----|-------|----------|
| US-06.1 | As an Agent, I want to automatically choose the best model for each task | P0 |
| US-06.2 | As an Agent, I want to learn from feedback which models work best | P0 |
| US-06.3 | As an Agent, I want to respect my capsule's allowed_models constraint | P0 |
| US-06.4 | As a User, I want the agent to prefer cheaper models when quality is similar | P2 |

#### 3.6.3 Routing Algorithm

```
INPUTS:
  - required_capabilities: set[str]  # From attachments/tools
  - detected_task_type: str          # From FR-05
  - agent_id: UUID
  - tenant_id: UUID
  - capsule_body: dict               # Contains allowed_models

ALGORITHM:
  1. Get agent's enabled models from AgentModelConfig
  2. Filter by required_capabilities (must have ALL)
  3. Filter by capsule.body.allowed_models (if specified)
  4. Query performance data:
     SELECT model, AVG(rating) as score, COUNT(*) as usage
     FROM messages
     WHERE task_type = detected_task_type
       AND agent_id = agent_id
       AND rating IS NOT NULL
     GROUP BY model
  5. Compute final score:
     score = base_priority * 0.3 + experience_score * 0.7
     (If no experience data, use base_priority only)
  6. Return model with highest score

OUTPUT:
  - SelectedModel(name, provider, display_name, priority, cost_tier)
```

#### 3.6.4 Functional Requirements

| ID | Requirement |
|----|-------------|
| FR-06.1 | System SHALL filter models by agent's enabled models |
| FR-06.2 | System SHALL filter models by required capabilities |
| FR-06.3 | System SHALL filter models by capsule.body.allowed_models |
| FR-06.4 | System SHALL query historical performance by task_type |
| FR-06.5 | System SHALL combine base_priority and experience with configurable weights |
| FR-06.6 | System SHALL fall back to base_priority when no experience data exists |
| FR-06.7 | System SHALL log model selection decisions for debugging |
| FR-06.8 | System SHALL complete routing in < 50ms (P95) |

---

## 4. Data Model

### 4.1 Entity-Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              LLMProvider                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│ id                 │ VARCHAR(50) PK   │ "openrouter", "openai", "custom_1" │
│ display_name       │ VARCHAR(100)     │ "OpenRouter"                        │
│ provider_type      │ VARCHAR(20)      │ openrouter|openai|anthropic|custom  │
│ api_base           │ VARCHAR(255)     │ "https://openrouter.ai/api/v1"      │
│ models_endpoint    │ VARCHAR(255)     │ "/models"                           │
│ api_key_vault_path │ VARCHAR(255)     │ "secret/llm/openrouter"             │
│ rate_limit_rpm     │ INT              │ 200                                 │
│ is_active          │ BOOL             │ true                                │
│ last_synced        │ TIMESTAMP        │                                     │
│ created_by         │ UUID FK          │ User who created                    │
│ created_at         │ TIMESTAMP        │                                     │
│ updated_at         │ TIMESTAMP        │                                     │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ 1:N
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           LLMModelCatalog                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│ id                 │ VARCHAR(255) PK  │ "openrouter/google/gemma-2-9b:free" │
│ provider_id        │ FK → LLMProvider │ "openrouter"                        │
│ external_id        │ VARCHAR(255)     │ "google/gemma-2-9b-it:free"         │
│ display_name       │ VARCHAR(255)     │ "Gemma 2 9B (Free)"                 │
│ model_type         │ VARCHAR(20)      │ "chat" | "embedding"                │
│ capabilities       │ JSONB            │ ["text", "vision", "code"]          │
│ priority           │ INT              │ 0-100 (routing weight)              │
│ cost_tier          │ VARCHAR(20)      │ free|low|standard|premium           │
│ domains            │ JSONB            │ ["medical", "legal"]                │
│ ctx_length         │ INT              │ 128000                              │
│ pricing_input      │ DECIMAL(10,6)    │ 0.00 (per 1M tokens)                │
│ pricing_output     │ DECIMAL(10,6)    │ 0.00 (per 1M tokens)                │
│ is_available       │ BOOL             │ true (from provider)                │
│ metadata           │ JSONB            │ Raw data from provider API          │
│ synced_at          │ TIMESTAMP        │                                     │
│ created_at         │ TIMESTAMP        │                                     │
│ updated_at         │ TIMESTAMP        │                                     │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ N:M via AgentModelConfig
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         AgentModelConfig                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│ id                 │ UUID PK          │                                     │
│ agent_id           │ UUID FK          │ The agent                           │
│ model_id           │ FK → Catalog     │ "openrouter/google/gemma-2-9b:free" │
│ priority_override  │ INT NULL         │ Agent-specific priority             │
│ is_enabled         │ BOOL             │ true                                │
│ enabled_by         │ UUID FK          │ User who enabled                    │
│ enabled_at         │ TIMESTAMP        │                                     │
│ tenant_id          │ UUID FK          │ Multi-tenant isolation              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ Performance tracked via
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            Message (EXTENDED)                                │
├─────────────────────────────────────────────────────────────────────────────┤
│ id                 │ UUID PK          │ EXISTING                            │
│ conversation_id    │ UUID FK          │ EXISTING                            │
│ role               │ VARCHAR(20)      │ EXISTING                            │
│ content            │ TEXT             │ EXISTING                            │
│ model              │ VARCHAR(100)     │ EXISTING - which LLM was used       │
│ latency_ms         │ INT              │ EXISTING - performance metric       │
│ token_count        │ INT              │ EXISTING                            │
│ metadata           │ JSONB            │ EXISTING                            │
│ created_at         │ TIMESTAMP        │ EXISTING                            │
├─────────────────────────────────────────────────────────────────────────────┤
│ rating             │ FLOAT NULL       │ NEW - User feedback (0.0-1.0)       │
│ task_type          │ VARCHAR(50) NULL │ NEW - Detected task category        │
│ tools_used         │ JSONB            │ NEW - ["code_execute", ...]         │
│ feedback_type      │ VARCHAR(20) NULL │ NEW - explicit|implicit|self_eval   │
│ feedback_at        │ TIMESTAMP NULL   │ NEW - When feedback was given       │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Indexes

```sql
-- LLMProvider
CREATE INDEX ix_provider_active ON llm_providers(is_active);

-- LLMModelCatalog
CREATE INDEX ix_model_provider ON llm_model_catalog(provider_id);
CREATE INDEX ix_model_active ON llm_model_catalog(is_available);
CREATE INDEX ix_model_type ON llm_model_catalog(model_type);
CREATE INDEX ix_model_cost_tier ON llm_model_catalog(cost_tier);

-- AgentModelConfig
CREATE INDEX ix_agent_model_agent ON agent_model_config(agent_id);
CREATE INDEX ix_agent_model_enabled ON agent_model_config(agent_id, is_enabled);
CREATE UNIQUE INDEX uq_agent_model ON agent_model_config(agent_id, model_id);

-- Message (for performance queries)
CREATE INDEX ix_message_task_rating ON messages(task_type, rating) WHERE rating IS NOT NULL;
CREATE INDEX ix_message_model_task ON messages(model, task_type) WHERE role = 'assistant';
```

---

## 5. API Specification

### 5.1 Provider Management APIs

#### 5.1.1 List Providers
```
GET /api/v2/admin/providers
Authorization: Bearer {admin_token}

Response 200:
{
  "items": [
    {
      "id": "openrouter",
      "display_name": "OpenRouter",
      "provider_type": "openrouter",
      "api_base": "https://openrouter.ai/api/v1",
      "is_active": true,
      "model_count": 11000,
      "last_synced": "2026-01-14T10:00:00Z"
    }
  ],
  "total": 3
}
```

#### 5.1.2 Create Provider
```
POST /api/v2/admin/providers
Authorization: Bearer {admin_token}
Content-Type: application/json

{
  "id": "my_custom_llm",
  "display_name": "My Custom LLM",
  "provider_type": "custom",
  "api_base": "https://my-llm.example.com/v1",
  "models_endpoint": "/models",
  "api_key": "sk-..." // Stored in Vault, not DB
}

Response 201:
{
  "id": "my_custom_llm",
  "display_name": "My Custom LLM",
  "api_key_vault_path": "secret/llm/my_custom_llm",
  "created_at": "2026-01-14T10:30:00Z"
}
```

#### 5.1.3 Sync Provider Models
```
POST /api/v2/admin/providers/{provider_id}/sync
Authorization: Bearer {admin_token}

Response 200:
{
  "provider_id": "openrouter",
  "models_discovered": 11247,
  "models_added": 47,
  "models_updated": 11200,
  "synced_at": "2026-01-14T10:30:00Z"
}
```

### 5.2 Model Catalog APIs

#### 5.2.1 List Models
```
GET /api/v2/admin/models?provider=openrouter&cost_tier=free&capability=vision
Authorization: Bearer {admin_token}

Response 200:
{
  "items": [
    {
      "id": "openrouter/google/gemma-2-9b:free",
      "provider_id": "openrouter",
      "display_name": "Gemma 2 9B (Free)",
      "capabilities": ["text", "code"],
      "cost_tier": "free",
      "priority": 60,
      "ctx_length": 8192
    }
  ],
  "total": 47,
  "page": 1,
  "per_page": 20
}
```

#### 5.2.2 Create Custom Model
```
POST /api/v2/admin/models
Authorization: Bearer {admin_token}
Content-Type: application/json

{
  "provider_id": "my_custom_llm",
  "external_id": "my-model-v1",
  "display_name": "My Model v1",
  "model_type": "chat",
  "capabilities": ["text", "code", "function_calling"],
  "priority": 70,
  "cost_tier": "standard",
  "ctx_length": 32000
}

Response 201:
{
  "id": "my_custom_llm/my-model-v1",
  ...
}
```

### 5.3 Agent Model Configuration APIs

#### 5.3.1 List Agent's Enabled Models
```
GET /api/v2/agents/{agent_id}/models
Authorization: Bearer {tenant_admin_token}

Response 200:
{
  "agent_id": "abc-123",
  "models": [
    {
      "model_id": "openrouter/gpt-4o",
      "display_name": "GPT-4o",
      "is_enabled": true,
      "priority_override": null
    }
  ],
  "total_enabled": 5
}
```

#### 5.3.2 Enable Models for Agent
```
POST /api/v2/agents/{agent_id}/models
Authorization: Bearer {tenant_admin_token}
Content-Type: application/json

{
  "model_ids": ["openrouter/gpt-4o", "openrouter/claude-3.5-sonnet"],
  "bulk_filter": {
    "provider": "openrouter",
    "cost_tier": "free"
  }
}

Response 200:
{
  "enabled_count": 47,
  "models_enabled": ["openrouter/google/gemma-2-9b:free", ...]
}
```

### 5.4 Feedback API

#### 5.4.1 Submit Feedback
```
POST /api/v2/chat/messages/{message_id}/feedback
Authorization: Bearer {user_token}
Content-Type: application/json

{
  "rating": 1.0,  // 0.0 (bad) to 1.0 (good)
  "feedback_type": "explicit"  // optional, defaults to "explicit"
}

Response 200:
{
  "message_id": "msg-123",
  "rating": 1.0,
  "feedback_type": "explicit",
  "recorded_at": "2026-01-14T10:30:00Z"
}
```

### 5.5 Model Performance API

#### 5.5.1 Get Model Performance
```
GET /api/v2/admin/models/performance?task_type=code&agent_id=abc-123
Authorization: Bearer {admin_token}

Response 200:
{
  "task_type": "code",
  "agent_id": "abc-123",
  "performance": [
    {
      "model": "openrouter/glm-4.5-air",
      "avg_rating": 0.94,
      "usage_count": 47,
      "avg_latency_ms": 2300
    },
    {
      "model": "openrouter/gpt-4o",
      "avg_rating": 0.78,
      "usage_count": 12,
      "avg_latency_ms": 3100
    }
  ]
}
```

---

## 6. User Interface Requirements

### 6.1 Admin UI: Provider Management

| Screen | Elements |
|--------|----------|
| Provider List | Table with: Name, Type, Status, Model Count, Last Synced, Actions |
| Add Provider | Form: Name, Type (dropdown), Base URL, API Key (secure input), Models Endpoint |
| Provider Detail | Info card, Sync button, Model list, Disable button |

### 6.2 Admin UI: Model Catalog

| Screen | Elements |
|--------|----------|
| Model List | Table with filters: Provider, Cost Tier, Capabilities. Columns: Name, Provider, Capabilities, Priority, Actions |
| Add Custom Model | Form: Provider (dropdown), External ID, Display Name, Capabilities (multi-select), Priority, Cost Tier |
| Model Detail | All fields, Edit capabilities/priority, Usage stats |

### 6.3 Admin UI: Agent Model Config

| Screen | Elements |
|--------|----------|
| Agent Models | Table of enabled models with toggle switches. Bulk actions: Enable All Free, Disable All |
| Add Models | Modal with searchable model list, filters, multi-select |

### 6.4 Chat UI: Feedback

| Element | Behavior |
|---------|----------|
| 👍 Button | On assistant message bubble, submits rating=1.0 |
| 👎 Button | On assistant message bubble, submits rating=0.0 |
| Regenerate | Implicit negative feedback on previous response |
| Copy | Implicit positive feedback |

---

## 7. Non-Functional Requirements

### 7.1 Performance

| Metric | Requirement |
|--------|-------------|
| Model routing latency | < 50ms P95 |
| Provider sync (1000 models) | < 30 seconds |
| Feedback submission | < 100ms P95 |
| Model list page load | < 500ms |

### 7.2 Security

| Requirement | Implementation |
|-------------|----------------|
| API key storage | Vault only (VIBE Rule 164) |
| API authentication | JWT with tenant_id claim |
| Provider access | Platform admin only |
| Agent config access | Tenant admin only |
| Feedback submission | Authenticated users only |

### 7.3 Scalability

| Scenario | Capacity |
|----------|----------|
| Providers | Up to 100 |
| Models per provider | Up to 50,000 |
| Agents | Up to 10,000 |
| Feedback records | Unlimited (partitioned by month) |

### 7.4 Reliability

| Requirement | Target |
|-------------|--------|
| Provider API failures | Cached fallback to last known models |
| Vault unavailable | Fail-closed (no LLM calls) |
| Model router failure | Fall back to default model |

---

## 8. Appendices

### 8.1 Migration Plan

| Phase | Changes |
|-------|---------|
| Phase 1 | Create LLMProvider, LLMModelCatalog tables. Migrate from GlobalDefault |
| Phase 2 | Create AgentModelConfig table. Admin UI for model enablement |
| Phase 3 | Add rating, task_type, tools_used to Message. Feedback API |
| Phase 4 | Implement intelligent model router with learning |
| Phase 5 | Performance dashboard and analytics |

### 8.2 Backward Compatibility

- Existing LLMModelConfig table will be migrated to LLMModelCatalog
- Existing model selection logic will be wrapped by new router
- Capsule.body.allowed_models continues to work unchanged

### 8.3 Testing Requirements

| Test Type | Coverage |
|-----------|----------|
| Unit tests | All routing logic, feedback collection |
| Integration tests | Provider sync, Vault integration |
| E2E tests | Full flow: create provider → enable models → chat → feedback |
| Performance tests | Routing latency under load |

---

**END OF DOCUMENT**
