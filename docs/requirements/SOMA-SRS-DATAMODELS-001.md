# SRS-DATA-MODELS — Data Models and ORM Schema

| Field | Value |
|-------|-------|
| **System** | SomaAgent01 |
| **Document ID** | SRS-DATA-MODELS-2026-01-16 |
| **Version** | 5.1 |
| **Date** | 2026-01-16 |
| **Status** | Approved |
| **Author** | Soma Engineering |
| **Owner** | Data Architecture Team |

---

## Table of Contents

1. [Introduction](#1-introduction)
   1.1 [Purpose](#11-purpose)
   1.2 [Scope](#12-scope)
   1.3 [Definitions](#13-definitions)
   1.4 [References](#14-references)
2. [Product Description](#2-product-description)
   2.1 [Product Perspective](#21-product-perspective)
   2.2 [Product Functions](#22-product-functions)
   2.3 [User Characteristics](#23-user-characteristics)
   2.4 [Constraints](#24-constraints)
   2.5 [Assumptions and Dependencies](#25-assumptions-and-dependencies)
3. [Specific Requirements](#3-specific-requirements)
   3.1 [Functional Requirements](#31-functional-requirements)
   3.2 [Non-Functional Requirements](#32-non-functional-requirements)
   3.3 [External Interface Requirements](#33-external-interface-requirements)
   3.4 [Design Constraints](#34-design-constraints)
4. [Traceability](#4-traceability)

---

## 1. Introduction

### 1.1 Purpose

This document specifies the data model requirements for the SomaAgent01 platform. It defines the Django ORM model inventory, domain boundaries, relationships, and constraints that govern how data is structured, stored, and accessed across the platform.

### 1.2 Scope

**In scope:**
- Complete inventory of Django ORM models across all domains
- Entity-relationship definitions and foreign key constraints
- Tenant-scoped data isolation at the model layer
- Zero Data Loss (ZDL) infrastructure models
- LLM model configuration and routing data structures
- Domain model segregation by bounded context

**Out of scope:**
- Database physical schema tuning (indexes, partitioning)
- Migration generation scripts (covered by Django's built-in migration framework)
- Raw SQL queries and stored procedures

### 1.3 Definitions

| Term | Definition |
|------|------------|
| Capsule | Agent identity unit containing governance, models, and capabilities |
| Constitution | Immutable governance document referenced by a capsule |
| Django ORM | Object-Relational Mapper provided by Django framework |
| Domain Model | Group of related models representing a bounded business context |
| FK | Foreign Key, a database constraint enforcing referential integrity |
| LLMModelConfig | Single source of truth for all Large Language Model configurations |
| M2M | Many-to-Many relationship between two entities |
| OutboxMessage | Transactional outbox pattern message for reliable event publishing |
| Tenant | Isolated organizational boundary within the platform |
| ZDL | Zero Data Loss, a set of infrastructure models ensuring message durability |

### 1.4 References

| ID | Document | Version | Location |
|----|----------|---------|----------|
| REF-001 | SRS-SECURITY-MULTITENANCY | 1.1 | `docs/srs/SRS-SECURITY-MULTITENANCY.md` |
| REF-002 | SRS-PERMISSION-MATRIX | 1.1 | `docs/srs/SRS-PERMISSION-MATRIX.md` |
| REF-003 | SRS-ARCHITECTURAL-PATTERNS | 1.0 | `docs/srs/SRS-ARCHITECTURAL-PATTERNS.md` |
| REF-004 | Django Documentation | 5.0 | https://docs.djangoproject.com |

---

## 2. Product Description

### 2.1 Product Perspective

The data model layer is the persistence foundation of SomaAgent01. All business logic, API responses, and background jobs interact with the database through Django ORM models. The model layer enforces tenant isolation, referential integrity, and capability-based LLM routing. It is organized into bounded contexts (domains) to minimize coupling.

### 2.2 Product Functions

| ID | Function | Description |
|----|----------|-------------|
| FUNC-001 | Tenant Isolation | Enforce tenant-scoped data access via `tenant_id` foreign keys and querysets |
| FUNC-002 | Model Routing | Select appropriate LLM model configurations based on required capabilities and cost tier |
| FUNC-003 | Message Durability | Ensure events are reliably published via OutboxMessage and DeadLetterMessage patterns |
| FUNC-004 | Identity Management | Store capsules, constitutions, and agent configurations with versioned governance |
| FUNC-005 | Conversation Persistence | Store conversations, messages, and participant metadata |
| FUNC-006 | Permission Storage | Store roles, granular permissions, resources, and actions for RBAC |
| FUNC-007 | Analytics Storage | Store time-windowed aggregates for usage and anomaly detection |
| FUNC-008 | Billing Metering | Store usage records for external billing system integration |

### 2.3 User Characteristics

| User Type | Role | Technical Level | Access |
|-----------|------|-----------------|--------|
| Backend Developer | Implements business logic | High | Full ORM access within domain boundaries |
| Data Engineer | Manages analytics pipelines | High | Read access to Flink and audit tables |
| Platform Admin | Operates infrastructure | High | Read access to health and infrastructure tables |
| API Consumer | External integrator | Medium | Read/write via API layer only |

### 2.4 Constraints

| ID | Constraint | Description |
|----|------------|-------------|
| CON-001 | Django ORM Only | All database access must use Django ORM; raw SQL is prohibited except in migrations |
| CON-002 | No Hardcoded Models | LLM model references must use foreign keys to `LLMModelConfig`; no hardcoded model names in business logic |
| CON-003 | Tenant Scoping | Every model in the AAAS, Core, Chat, and Voice domains must have a `tenant_id` or tenant foreign key |
| CON-004 | Migration Safety | All schema changes must be applied via Django migrations; manual DDL is prohibited in production |

### 2.5 Assumptions and Dependencies

| ID | Assumption / Dependency | Impact if Invalid |
|----|------------------------|-------------------|
| AD-001 | PostgreSQL is the primary transactional database | All ORM models require redesign if changing database |
| AD-002 | Milvus is the vector database | Vector search and memory features fail if unavailable |
| AD-003 | Redis is available for caching and rate limiting | Performance degrades; rate limiting may fail |
| AD-004 | Django migrations are applied in order | Schema inconsistency and application errors |

---

## 3. Specific Requirements

### 3.1 Functional Requirements

#### 3.1.1 Model Inventory

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-DM-001 | The system shall maintain Django ORM models across the following domains: Core, LLM, Chat, AAAS, Permissions, Voice, Flink, Files, Memory, and Infrastructure. | Must | Inspection | Approved |
| REQ-DM-002 | The system shall define all models in the following files or packages: `admin/core/models/core.py`, `admin/core/models/zdl.py`, `admin/llm/models.py`, `admin/chat/models.py`, `admin/aaas/models/`, `admin/permissions/models.py`, `admin/voice/models.py`, `admin/flink/models.py`, `admin/filesv2/models.py`, `admin/somabrain/models.py`, `admin/core/infrastructure/models.py`. | Must | Inspection | Approved |
| REQ-DM-003 | The system shall maintain at minimum 47 mapped database tables derived from Django models. | Must | Inspection | Approved |

#### 3.1.2 Core Domain

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-DM-004 | The system shall define a `Session` model with fields: `id` (UUID, PK), `session_id` (string, unique), `persona_id` (string), `tenant` (string), `metadata` (JSON), `created_at` (timestamp). | Must | Inspection | Approved |
| REQ-DM-005 | The system shall define a `SessionEvent` model with fields: `id` (bigint, PK), `session_id` (UUID, FK to Session), `event_type` (string), `payload` (JSON), `role` (string), `created_at` (timestamp). | Must | Inspection | Approved |
| REQ-DM-006 | The system shall define a `Constitution` model as an immutable governance document referenced by capsules. | Must | Inspection | Approved |
| REQ-DM-007 | The system shall define a `Capsule` model with identity fields (`id`, `name`, `version`), a `tenant` foreign key, a `constitution` foreign key (PROTECT), model foreign keys (`chat_model`, `image_model`, `voice_model`, `browser_model`), a `capabilities` many-to-many relationship, and a `memory_config` foreign key. | Must | Inspection | Approved |
| REQ-DM-008 | The system shall define a `CapsuleInstance` model representing a running instance of a capsule. | Must | Inspection | Approved |
| REQ-DM-009 | The system shall define a `Capability` model for tool and MCP registry entries. | Must | Inspection | Approved |
| REQ-DM-010 | The system shall define infrastructure models: `UISetting`, `Job`, `Notification`, `Prompt`, `FeatureFlag`, `AgentSetting`. | Must | Inspection | Approved |

#### 3.1.3 Zero Data Loss Models

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-DM-011 | The system shall define an `OutboxMessage` model for the transactional outbox pattern. | Must | Inspection | Approved |
| REQ-DM-012 | The system shall define a `DeadLetterMessage` model for dead-letter queue storage. | Must | Inspection | Approved |
| REQ-DM-013 | The system shall define an `IdempotencyRecord` model for request deduplication. | Must | Inspection | Approved |
| REQ-DM-014 | The system shall define a `MemoryReplica` model for write-ahead log events. | Must | Inspection | Approved |
| REQ-DM-015 | The system shall define a `PendingMemory` model for brain synchronization queue entries. | Must | Inspection | Approved |

#### 3.1.4 LLM Domain

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-DM-016 | The system shall define an `LLMModelConfig` model as the single source of truth for all model configurations with fields: `name` (unique), `display_name`, `model_type`, `provider`, `api_base`, `capabilities` (JSON), `priority`, `cost_tier`, `domains` (JSON), `ctx_length`, `limit_requests`, `limit_input`, `limit_output`, `is_active`. | Must | Inspection | Approved |
| REQ-DM-017 | The system shall route model selection by filtering on required capabilities, allowed cost tiers, capsule-allowed models, and priority, selecting the highest-priority match. | Must | Test | Approved |

#### 3.1.5 Chat Domain

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-DM-018 | The system shall define a `Conversation` model with fields: `id` (UUID, PK), `agent_id` (UUID, FK), `user_id` (UUID, FK), `tenant_id` (UUID, FK), `title`, `status`, `message_count`, `memory_mode`. | Must | Inspection | Approved |
| REQ-DM-019 | The system shall define a `Message` model with fields: `id` (UUID, PK), `conversation_id` (UUID, FK), `role`, `content`, `token_count`, `model`, `latency_ms`, `rating`, `task_type`, `tools_used` (JSON), `synced_to_brain` (boolean). | Must | Inspection | Approved |
| REQ-DM-020 | The system shall define a `ConversationParticipant` model linking users to conversations with a role field. | Must | Inspection | Approved |

#### 3.1.6 AAAS Domain

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-DM-021 | The system shall define a `SubscriptionTier` model with fields: `id` (UUID, PK), `name`, `slug` (unique), `base_price_cents`, `lago_plan_code`, `max_agents`, `max_users_per_agent`, `max_monthly_voice_minutes`, `max_monthly_api_calls`, `feature_defaults` (JSON). | Must | Inspection | Approved |
| REQ-DM-022 | The system shall define a `Tenant` model with fields: `id` (UUID, PK), `name`, `slug` (unique), `tier` (FK to SubscriptionTier), `status`, `keycloak_realm`, `lago_customer_id`, `lago_subscription_id`, `feature_overrides` (JSON). | Must | Inspection | Approved |
| REQ-DM-023 | The system shall define a `TenantUser` model with fields: `id` (UUID, PK), `tenant` (FK), `user_id` (UUID), `email`, `role`, `is_active`. | Must | Inspection | Approved |
| REQ-DM-024 | The system shall define an `Agent` model with fields: `id` (UUID, PK), `tenant` (FK), `name`, `slug`, `status`, `config` (JSON), `feature_settings` (JSON), `primary_capsule` (FK), `skin_id`. | Must | Inspection | Approved |
| REQ-DM-025 | The system shall define an `AgentUser` model linking users to agents with a role field. | Must | Inspection | Approved |
| REQ-DM-026 | The system shall define a `UsageRecord` model for metering data sent to the external billing system. | Must | Inspection | Approved |
| REQ-DM-027 | The system shall define settings models: `PlatformConfig` (global singleton), `AdminProfile`, `TenantSettings`, `UserPreferences`. | Must | Inspection | Approved |

#### 3.1.7 Permissions Domain

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-DM-028 | The system shall define a `Role` model with fields: `id` (UUID, PK), `tenant_id`, `name`, `slug`, `scope`, `is_system`, `is_default`. | Must | Inspection | Approved |
| REQ-DM-029 | The system shall define a `PermissionResource` model with fields: `id` (UUID, PK), `name` (unique), `display_name`, `category`. | Must | Inspection | Approved |
| REQ-DM-030 | The system shall define a `PermissionAction` model with fields: `id` (UUID, PK), `name`, `is_destructive`. | Must | Inspection | Approved |
| REQ-DM-031 | The system shall define a `GranularPermission` model with fields: `id` (UUID, PK), `resource` (FK), `action` (FK), `codename` (unique), and a many-to-many relationship to `Role`. | Must | Inspection | Approved |

#### 3.1.8 Voice Domain

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-DM-032 | The system shall define a `VoicePersona` model with fields: `id` (UUID, PK), `tenant` (FK), `name`, `stt_model` (FK to LLMModelConfig), `tts_llm_model` (FK to LLMModelConfig), `tts_voice_model_id`, `tts_speed`, `personality_config` (JSON). | Must | Inspection | Approved |
| REQ-DM-033 | The system shall define a `VoiceSession` model with fields: `id` (UUID, PK), `tenant` (FK), `persona` (FK), `status`, `duration_seconds`, `bytes_sent`, `bytes_received`. | Must | Inspection | Approved |
| REQ-DM-034 | The system shall define a `VoiceModel` model with fields: `id` (string, PK), `name`, `provider`, `language`, `gender`, `is_active`. | Must | Inspection | Approved |

#### 3.1.9 Flink Domain

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-DM-035 | The system shall define a `FlinkConversationMetrics` model for 1-minute windowed conversation aggregates. | Must | Inspection | Approved |
| REQ-DM-036 | The system shall define a `FlinkUsageAggregate` model for 1-hour windowed usage aggregates. | Must | Inspection | Approved |
| REQ-DM-037 | The system shall define a `FlinkAnomalyAlert` model for 5-minute windowed anomaly alerts. | Must | Inspection | Approved |
| REQ-DM-038 | The system shall define a `FlinkAgentMetrics` model for 1-minute windowed agent aggregates. | Must | Inspection | Approved |

#### 3.1.10 Infrastructure and Other Domains

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-DM-039 | The system shall define infrastructure models: `RateLimitPolicy`, `ServiceHealth`, `InfrastructureConfig`. | Must | Inspection | Approved |
| REQ-DM-040 | The system shall define a `File` model for S3 or local storage metadata. | Must | Inspection | Approved |
| REQ-DM-041 | The system shall define a `MemoryConfig` model for retention policy configuration. | Must | Inspection | Approved |

#### 3.1.11 Relationship Integrity

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-DM-042 | The system shall enforce a foreign key from `Capsule.tenant` to `Tenant` with `on_delete=CASCADE`. | Must | Inspection | Approved |
| REQ-DM-043 | The system shall enforce a foreign key from `Capsule.constitution` to `Constitution` with `on_delete=PROTECT`. | Must | Inspection | Approved |
| REQ-DM-044 | The system shall enforce foreign keys from `Capsule` to `LLMModelConfig` for `chat_model` (PROTECT), `image_model` (SET_NULL), `voice_model` (SET_NULL), and `browser_model` (SET_NULL). | Must | Inspection | Approved |
| REQ-DM-045 | The system shall enforce a many-to-many relationship from `Capsule` to `Capability`. | Must | Inspection | Approved |
| REQ-DM-046 | The system shall enforce a foreign key from `Agent.tenant` to `Tenant` with `on_delete=CASCADE`. | Must | Inspection | Approved |
| REQ-DM-047 | The system shall enforce a many-to-many relationship from `Agent` to `Capsule`, plus a `primary_capsule` foreign key (SET_NULL). | Must | Inspection | Approved |
| REQ-DM-048 | The system shall enforce a foreign key from `Conversation.agent` to `Agent` and from `Conversation.tenant` to `Tenant`. | Must | Inspection | Approved |
| REQ-DM-049 | The system shall enforce a foreign key from `Message.conversation` to `Conversation` with `on_delete=CASCADE`. | Must | Inspection | Approved |
| REQ-DM-050 | The system shall enforce a foreign key from `Tenant.tier` to `SubscriptionTier` with `on_delete=PROTECT`. | Must | Inspection | Approved |

---

### 3.2 Non-Functional Requirements

#### 3.2.1 Performance

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-PERF-001 | Model query response time for single-record lookups shall be less than or equal to 10 ms. | 10 ms | Test |
| NFR-PERF-002 | LLM model routing query shall complete within 20 ms at p99. | 20 ms | Test |

#### 3.2.2 Security

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-SEC-001 | All models with tenant scope shall enforce tenant filtering at the queryset level. | 100% coverage | Inspection |
| NFR-SEC-002 | No model shall store plaintext secrets or API keys. | 0 violations | Inspection |

#### 3.2.3 Reliability

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-REL-001 | OutboxMessage processing shall guarantee at-least-once delivery to Kafka. | 99.99% | Test |
| NFR-REL-002 | Foreign key constraints shall prevent orphaned records in normal operation. | 0 orphans | Test |

#### 3.2.4 Scalability

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-SCL-001 | The Conversation model shall support 10 million rows per tenant with query performance degradation less than or equal to 20% at maximum scale. | 10M rows | Analysis |

#### 3.2.5 Maintainability

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-MNT-001 | Each model file shall not exceed 650 lines; files exceeding this limit shall be split by subdomain. | 650 lines | Inspection |
| NFR-MNT-002 | Model changes shall include corresponding Django migration files committed to version control. | 100% coverage | Inspection |

---

### 3.3 External Interface Requirements

#### 3.3.1 User Interfaces

No direct user interface requirements are specified in this document.

#### 3.3.2 Software Interfaces

| Interface | Protocol | Format | Authentication |
|-----------|----------|--------|----------------|
| PostgreSQL | TCP / SSL | SQL / Django ORM | Username / password + SSL |
| Milvus | gRPC / REST | Protobuf / JSON | Token |
| Kafka | TCP / SASL_SSL | Avro / JSON | SASL/SCRAM |
| Billing API (Lago) | HTTPS / REST | JSON | API key |

#### 3.3.3 Hardware Interfaces

No hardware interface requirements are specified in this document.

---

### 3.4 Design Constraints

| ID | Constraint | Source |
|----|------------|--------|
| DC-001 | All persistence must use Django ORM; SQLAlchemy is prohibited. | SRS-ARCHITECTURAL-PATTERNS |
| DC-002 | Migrations must use Django's built-in migration framework; Alembic is prohibited. | SRS-ARCHITECTURAL-PATTERNS |
| DC-003 | Models must be organized by bounded context in `admin/<domain>/models/`. | SRS-ARCHITECTURAL-PATTERNS |
| DC-004 | No hardcoded model names or provider strings in business logic; all references must use foreign keys. | Platform standard |

---

## 4. Traceability

### 4.1 Requirements Traceability Matrix

| REQ ID | Description | Source | Design | Implementation | Test |
|--------|-------------|--------|--------|----------------|------|
| REQ-DM-001 | Model domain inventory | SRS-DATA-MODELS | `admin/*/models/` | `admin/core/models/`, `admin/llm/models.py`, `admin/chat/models.py`, `admin/aaas/models/`, `admin/permissions/models.py`, `admin/voice/models.py`, `admin/flink/models.py`, `admin/filesv2/models.py`, `admin/somabrain/models.py`, `admin/core/infrastructure/models.py` | `tests/django/` |
| REQ-DM-004 | Session model | SRS-DATA-MODELS | `admin/core/models/core.py` | `admin/core/models/core.py` | `tests/django/` |
| REQ-DM-005 | SessionEvent model | SRS-DATA-MODELS | `admin/core/models/core.py` | `admin/core/models/core.py` | `tests/django/` |
| REQ-DM-006 | Constitution model | SRS-DATA-MODELS | `admin/core/models/core.py` | `admin/core/models/core.py` | `tests/django/` |
| REQ-DM-007 | Capsule model | SRS-DATA-MODELS | `admin/core/models/core.py` | `admin/core/models/core.py` | `tests/django/` |
| REQ-DM-011 | OutboxMessage model | SRS-DATA-MODELS | `admin/core/models/zdl.py` | `admin/core/models/zdl.py` | `tests/django/` |
| REQ-DM-012 | DeadLetterMessage model | SRS-DATA-MODELS | `admin/core/models/zdl.py` | `admin/core/models/zdl.py` | `tests/django/` |
| REQ-DM-013 | IdempotencyRecord model | SRS-DATA-MODELS | `admin/core/models/zdl.py` | `admin/core/models/zdl.py` | `tests/django/` |
| REQ-DM-014 | MemoryReplica model | SRS-DATA-MODELS | `admin/core/models/zdl.py` | `admin/core/models/zdl.py` | `tests/django/` |
| REQ-DM-015 | PendingMemory model | SRS-DATA-MODELS | `admin/core/models/zdl.py` | `admin/core/models/zdl.py` | `tests/django/` |
| REQ-DM-016 | LLMModelConfig model | SRS-DATA-MODELS | `admin/llm/models.py` | `admin/llm/models.py` | `tests/django/` |
| REQ-DM-017 | Model routing algorithm | SRS-DATA-MODELS | `admin/core/model_router.py` | `admin/core/model_router.py` | `tests/unit/` |
| REQ-DM-018 | Conversation model | SRS-DATA-MODELS | `admin/chat/models.py` | `admin/chat/models.py` | `tests/django/` |
| REQ-DM-019 | Message model | SRS-DATA-MODELS | `admin/chat/models.py` | `admin/chat/models.py` | `tests/django/` |
| REQ-DM-020 | ConversationParticipant model | SRS-DATA-MODELS | `admin/chat/models.py` | `admin/chat/models.py` | `tests/django/` |
| REQ-DM-021 | SubscriptionTier model | SRS-DATA-MODELS | `admin/aaas/models/tiers.py` | `admin/aaas/models/tiers.py` | `tests/django/` |
| REQ-DM-022 | Tenant model | SRS-DATA-MODELS | `admin/aaas/models/tenants.py` | `admin/aaas/models/tenants.py` | `tests/django/` |
| REQ-DM-023 | TenantUser model | SRS-DATA-MODELS | `admin/aaas/models/tenants.py` | `admin/aaas/models/tenants.py` | `tests/django/` |
| REQ-DM-024 | Agent model | SRS-DATA-MODELS | `admin/aaas/models/agents.py` | `admin/aaas/models/agents.py` | `tests/django/` |
| REQ-DM-025 | AgentUser model | SRS-DATA-MODELS | `admin/aaas/models/agents.py` | `admin/aaas/models/agents.py` | `tests/django/` |
| REQ-DM-026 | UsageRecord model | SRS-DATA-MODELS | `admin/aaas/models/usage.py` | `admin/aaas/models/usage.py` | `tests/django/` |
| REQ-DM-027 | Settings models | SRS-DATA-MODELS | `admin/aaas/models/profiles.py` | `admin/aaas/models/profiles.py` | `tests/django/` |
| REQ-DM-028 | Role model | SRS-DATA-MODELS | `admin/permissions/models.py` | `admin/permissions/models.py` | `tests/django/` |
| REQ-DM-029 | PermissionResource model | SRS-DATA-MODELS | `admin/permissions/models.py` | `admin/permissions/models.py` | `tests/django/` |
| REQ-DM-030 | PermissionAction model | SRS-DATA-MODELS | `admin/permissions/models.py` | `admin/permissions/models.py` | `tests/django/` |
| REQ-DM-031 | GranularPermission model | SRS-DATA-MODELS | `admin/permissions/models.py` | `admin/permissions/models.py` | `tests/django/` |
| REQ-DM-032 | VoicePersona model | SRS-DATA-MODELS | `admin/voice/models.py` | `admin/voice/models.py` | `tests/django/` |
| REQ-DM-033 | VoiceSession model | SRS-DATA-MODELS | `admin/voice/models.py` | `admin/voice/models.py` | `tests/django/` |
| REQ-DM-034 | VoiceModel model | SRS-DATA-MODELS | `admin/voice/models.py` | `admin/voice/models.py` | `tests/django/` |
| REQ-DM-035 | FlinkConversationMetrics model | SRS-DATA-MODELS | `admin/flink/models.py` | `admin/flink/models.py` | `tests/django/` |
| REQ-DM-036 | FlinkUsageAggregate model | SRS-DATA-MODELS | `admin/flink/models.py` | `admin/flink/models.py` | `tests/django/` |
| REQ-DM-037 | FlinkAnomalyAlert model | SRS-DATA-MODELS | `admin/flink/models.py` | `admin/flink/models.py` | `tests/django/` |
| REQ-DM-038 | FlinkAgentMetrics model | SRS-DATA-MODELS | `admin/flink/models.py` | `admin/flink/models.py` | `tests/django/` |
| REQ-DM-039 | Infrastructure models | SRS-DATA-MODELS | `admin/core/infrastructure/models.py` | `admin/core/infrastructure/models.py` | `tests/django/` |
| REQ-DM-040 | File model | SRS-DATA-MODELS | `admin/filesv2/models.py` | `admin/filesv2/models.py` | `tests/django/` |
| REQ-DM-041 | MemoryConfig model | SRS-DATA-MODELS | `admin/somabrain/models.py` | `admin/somabrain/models.py` | `tests/django/` |
| REQ-DM-043 | Constitution PROTECT FK | SRS-DATA-MODELS | `admin/core/models/core.py` | `admin/core/models/core.py` | `tests/django/` |
| REQ-DM-044 | Capsule model FKs | SRS-DATA-MODELS | `admin/core/models/core.py` | `admin/core/models/core.py` | `tests/django/` |
| REQ-DM-045 | Capsule-Capability M2M | SRS-DATA-MODELS | `admin/core/models/core.py` | `admin/core/models/core.py` | `tests/django/` |
| REQ-DM-047 | Agent-Capsule M2M + primary | SRS-DATA-MODELS | `admin/aaas/models/agents.py` | `admin/aaas/models/agents.py` | `tests/django/` |
| REQ-DM-050 | Tenant-SubscriptionTier FK | SRS-DATA-MODELS | `admin/aaas/models/tenants.py` | `admin/aaas/models/tenants.py` | `tests/django/` |

### 4.2 Requirement to Test Case Mapping

| REQ ID | Test Case ID | Test Method | Expected Result |
|--------|--------------|-------------|-----------------|
| REQ-DM-017 | TC-DM-001 | Unit test | Model routing returns highest-priority allowed model |
| REQ-DM-043 | TC-DM-002 | Integration test | Deleting a referenced Constitution raises ProtectedError |
| REQ-DM-050 | TC-DM-003 | Integration test | Deleting a SubscriptionTier referenced by a Tenant raises ProtectedError |
| REQ-DM-011 | TC-DM-004 | Unit test | OutboxMessage is created and marked processed after successful publish |

---

## 5. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0-4.0 | 2025 | Soma Engineering | Incremental model additions |
| 5.0 | 2026-01-16 | Soma Engineering | Complete 50+ model inventory with ERD diagrams and table index |
| 5.1 | 2026-05-21 | Soma Engineering | Refactored to ISO/IEC/IEEE 29148:2018 template; removed personas, emojis, and excessive code blocks; added REQ-XXX numbering and traceability matrix |

---

*Document conforms to ISO/IEC/IEEE 29148:2018 — Systems and Software Engineering — Life Cycle Processes — Requirements Engineering.*
