# SRS-MULTIMODAL — Image, Audio, and Diagram Generation

| Field | Value |
|-------|-------|
| **System** | SomaAgent01 |
| **Document ID** | SRS-MULTIMODAL-2026-01-16 |
| **Version** | 2.1 |
| **Date** | 2026-01-16 |
| **Status** | Approved |
| **Author** | SomaAgent01 Engineering |
| **Owner** | Core Platform Team |

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
5. [Revision History](#5-revision-history)

---

## 1. Introduction

### 1.1 Purpose

This document specifies the requirements for the multimodal execution subsystem of SomaAgent01. The subsystem enables AI agents to generate and process rich media content including images, diagrams, vision analysis, speech-to-text, and text-to-speech, with dynamic model selection driven by configuration rather than hardcoded values.

### 1.2 Scope

**In Scope:**
- Image generation (DALL-E, Midjourney, Stable Diffusion)
- Diagram rendering (Mermaid)
- Vision analysis (GPT-4o, Claude Vision)
- Speech-to-text (Whisper)
- Text-to-speech (TTS)
- Model selection routing via LLMModelConfig and AgentIQ
- Tenant-scoped execution, secrets, budget, and billing
- Feature flag gating per multimodal capability

**Out of Scope:**
- Video generation (reserved for future release)
- Real-time streaming audio
- Custom model training or fine-tuning

### 1.3 Definitions

| Term | Definition |
|------|------------|
| Multimodal | The generation or processing of non-text media (image, audio, diagram, vision) |
| LLMModelConfig | Database model storing provider model metadata, capabilities, cost tiers, and priorities |
| AgentIQ | Cost-tier and capability derivation system based on capsule knobs and budget |
| Capability | A named multimodal function such as image_generation, vision, audio_transcription, text_to_speech |
| Cost Tier | Classification (free, low, standard, premium, flagship) restricting model selection based on budget |
| Vault | Secret management system for tenant-scoped provider API keys |

### 1.4 References

| ID | Document | Version | Location |
|----|----------|---------|----------|
| REF-001 | SRS-CHAT-FLOW-MASTER.md | 3.0 | docs/srs/SRS-CHAT-FLOW-MASTER.md |
| REF-002 | SRS-CAPSULE-PORTABILITY.md | 3.0 | docs/srs/SRS-CAPSULE-PORTABILITY.md |
| REF-003 | SRS-BUDGET-SYSTEM.md | 1.0 | docs/srs/SRS-BUDGET-SYSTEM.md |
| REF-004 | SRS-FEATURE-FLAGS.md | 1.0 | docs/srs/SRS-FEATURE-FLAGS.md |
| REF-005 | LLM Model Configuration | Current | admin/core/models/core.py |

---

## 2. Product Description

### 2.1 Product Perspective

The multimodal subsystem executes during Phase 9 (Tools + Multimodal) of the 13-phase chat flow. After the LLM emits tool calls, the ToolExecutor parses the call and routes multimodal requests to the MultimodalAPI. The subsystem selects the best provider model dynamically based on required capability, AgentIQ-derived cost tier, capsule allowed_models, and model priority.

### 2.2 Product Functions

| ID | Function | Description |
|----|----------|-------------|
| FUNC-001 | Image Generation | Create images from text prompts using configured provider models |
| FUNC-002 | Vision Analysis | Analyze uploaded images using vision-capable models |
| FUNC-003 | Speech-to-Text | Transcribe audio input to text using configured transcription models |
| FUNC-004 | Text-to-Speech | Synthesize speech from text using configured TTS models |
| FUNC-005 | Diagram Rendering | Render Mermaid diagrams to images via internal service |
| FUNC-006 | Model Routing | Select the best provider model based on capability, cost tier, allowed models, and priority |

### 2.3 User Characteristics

| User Type | Role | Technical Level | Access |
|-----------|------|-----------------|--------|
| End User | Agent consumer | Low | Indirect via chat interface |
| Capsule Designer | Agent configurator | Medium | Configures allowed_models and default models in capsule |
| Platform Admin | Operations | High | Manages LLMModelConfig entries and provider keys in Vault |

### 2.4 Constraints

| ID | Constraint | Description |
|----|------------|-------------|
| CON-001 | No Hardcoded Models | All model names, providers, and API endpoints must originate from LLMModelConfig |
| CON-002 | No Environment Variables for Secrets | Provider API keys must be retrieved from Vault, not os.environ |
| CON-003 | Tenant Isolation | Every multimodal request must be scoped to the authenticated tenant |

### 2.5 Assumptions and Dependencies

| ID | Assumption / Dependency | Impact if Invalid |
|----|------------------------|-------------------|
| AD-001 | LLMModelConfig database contains at least one active model per supported capability | NoCapableModelError raised; request fails |
| AD-002 | Vault contains valid API keys for each provider under tenant-scoped paths | Provider call fails with authentication error |
| AD-003 | Capsule.body.allowed_models is either empty (allow all) or contains valid model names | Empty result if filter excludes all models |
| AD-004 | Feature flags are registered in the feature flag system | Requests bypass gating or return 403 |
| AD-005 | Budget cache (Redis) is reachable for per-metric enforcement | Budget enforcement disabled; potential overuse |

---

## 3. Specific Requirements

### 3.1 Functional Requirements

#### 3.1.1 Capability Detection and Routing

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-MM-001 | The system shall detect the required multimodal capability from the tool call name (e.g., generate_image, analyze_image, transcribe, speak, render_diagram). | Must | Test | Approved |
| REQ-MM-002 | The system shall query LLMModelConfig for active models matching the required capability. | Must | Test | Approved |
| REQ-MM-003 | The system shall filter models by capsule.body.allowed_models when the list is non-empty. | Must | Test | Approved |
| REQ-MM-004 | The system shall derive the cost_tier from AgentIQ based on the capsule resource_budget and apply it to model selection. | Must | Test | Approved |
| REQ-MM-005 | The system shall sort matching models by priority descending and select the highest-priority model. | Must | Test | Approved |
| REQ-MM-006 | The system shall raise NoCapableModelError when no model satisfies all filters. | Must | Test | Approved |

**Rationale:** Dynamic model routing ensures agents use the best available model within budget and policy constraints.

**Dependencies:** REQ-MM-004 depends on SRS-CAPSULE-PORTABILITY REQ-CP-006 (Knobs schema).

---

#### 3.1.2 Tenant Isolation

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-MM-007 | The system shall extract tenant_id from the authenticated request context before executing any multimodal operation. | Must | Test | Approved |
| REQ-MM-008 | The system shall load the tenant's capsule using tenant_id to retrieve allowed_models and AgentIQ settings. | Must | Test | Approved |
| REQ-MM-009 | The system shall retrieve provider API keys from Vault using a tenant-scoped path (secret/tenant/{tenant_id}/api_keys). | Must | Test | Approved |
| REQ-MM-010 | The system shall check budget limits using a tenant-scoped cache key (budget:{tenant_id}:{metric}:{period}). | Must | Test | Approved |
| REQ-MM-011 | The system shall record billing events to Lago with the tenant_id in the external_subscription_id field. | Must | Test | Approved |

**Rationale:** Tenant isolation prevents cross-tenant data leakage and ensures proper per-tenant billing and quota enforcement.

**Dependencies:** REQ-MM-008 depends on REQ-MM-007.

---

#### 3.1.3 Execution and Gating

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-MM-012 | The system shall enforce feature flags via @require_feature decorator before executing multimodal operations. | Must | Test | Approved |
| REQ-MM-013 | The system shall enforce budget gates via @budget_gate decorator with the appropriate metric per capability. | Must | Test | Approved |
| REQ-MM-014 | The system shall execute the selected model via the corresponding provider adapter and return a structured response containing the result URL and model name. | Must | Test | Approved |

**Rationale:** Feature flags and budget gates prevent unauthorized or over-budget usage.

---

#### 3.1.4 Provider Integration

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-MM-015 | The system shall support OpenAI provider for image generation, vision, transcription, and TTS. | Must | Test | Approved |
| REQ-MM-016 | The system shall support internal Mermaid service for diagram rendering. | Must | Test | Approved |
| REQ-MM-017 | The system shall support additional providers (Anthropic, Midjourney, ElevenLabs) via pluggable provider adapters. | Should | Inspection | Approved |

---

### 3.2 Non-Functional Requirements

#### 3.2.1 Performance

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-PERF-001 | Model selection (routing) latency shall not exceed 20ms excluding database query time. | 20 ms | Load Test |
| NFR-PERF-002 | Image generation end-to-end latency shall not exceed 15 seconds for standard-resolution images. | 15 s | Load Test |

#### 3.2.2 Security

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-SEC-001 | API keys shall never be logged or returned in responses. | 100% | Audit / Pen Test |
| NFR-SEC-002 | All tenant-scoped assets shall be stored with Asset.tenant_id for isolation. | 100% | Inspection |

#### 3.2.3 Reliability

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-REL-001 | Provider failures shall trigger circuit breaker logic with exponential backoff. | 3 retries | Chaos Test |

#### 3.2.4 Scalability

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-SCL-001 | The system shall support concurrent multimodal requests per tenant without cross-tenant interference. | 100 req/s per tenant | Load Test |

---

### 3.3 External Interface Requirements

#### 3.3.1 Software Interfaces

| Interface | Protocol | Format | Authentication |
|-----------|----------|--------|----------------|
| OpenAI Images API | HTTPS/JSON | JSON | Bearer (API key from Vault) |
| OpenAI Audio API | HTTPS/JSON | JSON / binary | Bearer (API key from Vault) |
| Anthropic Messages API | HTTPS/JSON | JSON | Bearer (API key from Vault) |
| Vault KV Secrets | HTTPS/JSON | JSON | Vault token |
| Lago Events API | HTTPS/JSON | JSON | Lago API key |
| Redis Budget Cache | RESP | Key-value | Redis AUTH |
| Internal Mermaid Service | HTTP/JSON | SVG/PNG | None (internal) |

#### 3.3.2 Hardware Interfaces

None.

---

### 3.4 Design Constraints

| ID | Constraint | Source |
|----|------------|--------|
| DC-001 | No hardcoded model names, providers, or API endpoints. | Platform Architecture |
| DC-002 | API keys must be retrieved from Vault at runtime, not from environment variables. | Security Policy |
| DC-003 | Feature flags must be checked before budget gates. | Control Flow Standard |
| DC-004 | Provider adapters must inherit from base_provider.BaseProvider. | services/multimodal/base_provider.py |

---

## 4. Traceability

### 4.1 Requirements Traceability Matrix

| REQ ID | Description | Source | Design | Implementation | Test |
|--------|-------------|--------|--------|----------------|------|
| REQ-MM-001 | Capability detection | Chat Flow Phase 9 | services/tool_executor/tools.py | services/tool_executor/multimodal_executor.py | tests/unit/test_multimodal_routing.py |
| REQ-MM-002 | Query LLMModelConfig | Model Routing | admin/core/models/core.py | services/gateway/providers.py | tests/unit/test_model_config_query.py |
| REQ-MM-003 | Filter by allowed_models | Capsule Config | admin/core/models/core.py | services/gateway/providers.py | tests/unit/test_allowed_models_filter.py |
| REQ-MM-004 | AgentIQ cost_tier derivation | Budget System | admin/core/models/core.py | services/common/agent_config_loader.py | tests/unit/test_agentiq_derive.py |
| REQ-MM-005 | Priority-based selection | Model Routing | admin/core/models/core.py | services/gateway/providers.py | tests/unit/test_model_priority.py |
| REQ-MM-006 | NoCapableModelError | Error Handling | admin/core/models/core.py | services/gateway/providers.py | tests/unit/test_no_capable_model.py |
| REQ-MM-007 | tenant_id extraction | Auth Layer | services/gateway/main.py | services/gateway/main.py | tests/integration/test_tenant_auth.py |
| REQ-MM-008 | Tenant capsule load | Multitenancy | admin/core/models/core.py | services/gateway/main.py | tests/integration/test_tenant_capsule.py |
| REQ-MM-009 | Tenant-scoped Vault secrets | Security | services/common/adapters/vault.py | services/common/adapters/vault.py | tests/integration/test_vault_tenant.py |
| REQ-MM-010 | Tenant-scoped budget check | Budget System | services/common/budget_cache.py | services/common/budget_cache.py | tests/unit/test_budget_tenant.py |
| REQ-MM-011 | Lago billing with tenant_id | Billing | services/common/billing.py | services/common/billing.py | tests/integration/test_lago_events.py |
| REQ-MM-012 | Feature flag enforcement | Feature Flags | admin/api/features.py | services/tool_executor/multimodal_executor.py | tests/unit/test_feature_flags.py |
| REQ-MM-013 | Budget gate enforcement | Budget System | services/common/budget_cache.py | services/tool_executor/multimodal_executor.py | tests/unit/test_budget_gate.py |
| REQ-MM-014 | Provider execution | Execution | services/multimodal/base_provider.py | services/multimodal/dalle_provider.py | tests/integration/test_image_generate.py |
| REQ-MM-015 | OpenAI provider support | Provider Adapter | services/multimodal/base_provider.py | services/multimodal/dalle_provider.py | tests/integration/test_openai_provider.py |
| REQ-MM-016 | Mermaid diagram rendering | Diagrams | services/multimodal/mermaid_provider.py | services/multimodal/mermaid_provider.py | tests/unit/test_mermaid_render.py |

### 4.2 Requirement to Test Case Mapping

| REQ ID | Test Case ID | Test Method | Expected Result |
|--------|--------------|-------------|-----------------|
| REQ-MM-001 | TC-MM-001 | Unit Test | generate_image resolves capability to image_generation |
| REQ-MM-003 | TC-MM-002 | Unit Test | Query filtered to allowed_models list |
| REQ-MM-006 | TC-MM-003 | Unit Test | NoCapableModelError raised when no models match |
| REQ-MM-007 | TC-MM-004 | Integration Test | tenant_id present in execution context |
| REQ-MM-009 | TC-MM-005 | Integration Test | Vault path contains tenant_id |
| REQ-MM-012 | TC-MM-006 | Unit Test | 403 returned when feature flag disabled |
| REQ-MM-013 | TC-MM-007 | Unit Test | 402 returned when budget exhausted |
| NFR-SEC-001 | TC-MM-008 | Penetration Test | API keys absent from all logs and responses |

---

## 5. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 2.0 | 2026-01-16 | Engineering | Initial canonical version with multitenancy |
| 2.1 | 2026-05-21 | Engineering | Refactored to ISO/IEC/IEEE 29148:2018 template; removed personas, emojis, excessive code and diagrams; added REQ numbering and traceability matrix |

---

*Document conforms to ISO/IEC/IEEE 29148:2018 — Systems and Software Engineering — Life Cycle Processes — Requirements Engineering.*
