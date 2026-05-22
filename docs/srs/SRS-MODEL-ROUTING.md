# SRS-MODEL-ROUTING — LLM Model Selection

| Field | Value |
|-------|-------|
| **System** | SomaAgent01 |
| **Document ID** | SRS-MODEL-ROUTING-2026-05-21 |
| **Version** | 1.1 |
| **Date** | 2026-05-21 |
| **Status** | Approved |
| **Author** | SomaAgent01 Engineering |
| **Owner** | Platform Team |

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

This document specifies the Model Routing subsystem of SomaAgent01, which selects the optimal LLM for a given request based on required capabilities, capsule constraints, tenant isolation, cost preferences, and policy enforcement.

### 1.2 Scope

**In scope:**
- Capability detection from message content and attachments
- Model catalog querying and filtering
- Capsule-level model allowlists
- Tenant-scoped model access
- Cost tier filtering
- SpiceDB permission checks
- OPA policy enforcement
- Audit logging of selection decisions

**Out of scope:**
- LLM invocation and generation (see SRS-CHAT-FLOW-MASTER)
- Fallback chain execution (see SRS-CHAT-FLOW-MASTER)
- Model provider billing (see SRS-BUDGET-SYSTEM)

### 1.3 Definitions

| Term | Definition |
|------|------------|
| Capability | A model feature such as `text`, `vision`, `audio`, `video`, or `document` |
| Cost Tier | A classification (`free`, `low`, `standard`, `premium`) indicating relative cost |
| LLMModelConfig | The Django ORM model that serves as the single source of truth for available models |
| SelectedModel | A dataclass representing the chosen model and its metadata |
| Tenant | An isolated organizational boundary in the multi-tenant system |

### 1.4 References

| ID | Document | Version | Location |
|----|----------|---------|----------|
| REF-001 | SRS-CHAT-FLOW-MASTER | 3.1 | `docs/srs/SRS-CHAT-FLOW-MASTER.md` |
| REF-002 | Model Router | — | `admin/core/model_router.py` |
| REF-003 | LLM Models | — | `admin/llm/models.py` |
| REF-004 | SpiceDB Client | — | `services/common/spicedb_client.py` |
| REF-005 | OPA Policy | — | `policy/soma_development.rego` |

---

## 2. Product Description

### 2.1 Product Perspective

Model Routing executes during Phase 4 of the 12-phase chat flow, between Context Building and Tool Discovery. It queries the `LLMModelConfig` catalog, applies capsule and tenant constraints, verifies permissions via SpiceDB and OPA, and returns a `SelectedModel` for downstream LLM invocation.

### 2.2 Product Functions

| ID | Function | Description |
|----|----------|-------------|
| FUNC-001 | Detect Capabilities | Inspect message and attachments to determine required model capabilities |
| FUNC-002 | Query Catalog | Retrieve active models from `LLMModelConfig` |
| FUNC-003 | Filter by Capabilities | Exclude models that do not support all required capabilities |
| FUNC-004 | Apply Capsule Constraints | Restrict selection to `capsule.body.allowed_models` when present |
| FUNC-005 | Apply Tenant Isolation | Restrict selection to models available to the requesting tenant |
| FUNC-006 | Apply Cost Tier | Prefer models matching the requested cost tier |
| FUNC-007 | Sort by Priority | Order remaining candidates by priority descending |
| FUNC-008 | Verify Permissions | Check SpiceDB and OPA policies before final selection |
| FUNC-009 | Log Selection | Persist the decision to `ModelSelectionLog` |

### 2.3 User Characteristics

| User Type | Role | Technical Level | Access |
|-----------|------|-----------------|--------|
| End User | Chat participant | Low | Indirect (model chosen automatically) |
| Tenant Admin | Organization manager | Medium | Capsule `allowed_models` configuration |
| Platform Operator | Infrastructure engineer | High | `LLMModelConfig` admin panel |

### 2.4 Constraints

| ID | Constraint | Description |
|----|------------|-------------|
| CON-001 | Single Source of Truth | The `LLMModelConfig` ORM model is the only authoritative source for available models |
| CON-002 | No Match Handling | If no model matches all constraints, the system shall raise `NoCapableModelError` |

### 2.5 Assumptions and Dependencies

| ID | Assumption / Dependency | Impact if Invalid |
|----|------------------------|-------------------|
| AD-001 | PostgreSQL is available for `LLMModelConfig` queries | Use cached model list |
| AD-002 | SpiceDB schema defines `model:use` permission | Governance falls back to capsule |
| AD-003 | OPA policy defines tenant cost tier rules | Policy check skipped |

---

## 3. Specific Requirements

### 3.1 Functional Requirements

#### 3.1.1 Capability Detection

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-001 | The system shall always include the `text` capability for every request. | Must | Test | Approved |
| REQ-002 | The system shall add the `vision` capability when any attachment has a MIME type matching `image/*`. | Must | Test | Approved |
| REQ-003 | The system shall add the `video` capability when any attachment has a MIME type matching `video/*`. | Must | Test | Approved |
| REQ-004 | The system shall add the `audio` capability when any attachment has a MIME type matching `audio/*`. | Must | Test | Approved |
| REQ-005 | The system shall add the `document` capability when any attachment has MIME type `application/pdf`. | Must | Test | Approved |

**Rationale:** MIME-based detection ensures the correct multimodal model is selected.

**Dependencies:** None

#### 3.1.2 Model Catalog Querying

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-006 | The system shall query `LLMModelConfig` for models where `is_active=True`. | Must | Test | Approved |
| REQ-007 | The system shall filter the active set to models whose `capabilities` list contains all required capabilities. | Must | Test | Approved |

**Rationale:** Only active, capable models are eligible for selection.

**Dependencies:** REQ-001

#### 3.1.3 Capsule Constraints

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-008 | If `capsule.body.allowed_models` is present and non-empty, the system shall restrict candidates to models whose `name` is in that list. | Must | Test | Approved |

**Rationale:** Capsule-level allowlists give tenant admins fine-grained control.

**Dependencies:** REQ-007

#### 3.1.4 Tenant Isolation

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-009 | The system shall filter candidates to models associated with the requesting tenant when `tenant_id` is provided. | Must | Test | Approved |
| REQ-010 | The system shall enforce that a tenant cannot access models outside its assigned catalog. | Must | Test | Approved |

**Rationale:** Multi-tenancy requires strict model access boundaries.

**Dependencies:** REQ-007

#### 3.1.5 Cost Tier Filtering

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-011 | When a `prefer_cost_tier` is specified, the system shall prefer models whose `cost_tier` matches the preference. | Should | Test | Approved |

**Rationale:** Cost tier preference allows budget-aware routing.

**Dependencies:** REQ-007

#### 3.1.6 Priority Ordering

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-012 | The system shall sort remaining candidate models by `priority` descending (highest priority first). | Must | Test | Approved |

**Rationale:** Priority reflects operational preference (performance, reliability, cost).

**Dependencies:** REQ-007

#### 3.1.7 Selection and Error Handling

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-013 | If at least one candidate remains after all filters, the system shall return a `SelectedModel` containing `provider`, `name`, `display_name`, `capabilities`, `priority`, `cost_tier`, and `reason`. | Must | Test | Approved |
| REQ-014 | If no candidates remain, the system shall raise `NoCapableModelError`. | Must | Test | Approved |

**Rationale:** Explicit failure prevents silent use of an unsuitable model.

**Dependencies:** REQ-012

#### 3.1.8 Permission Verification

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-015 | The system shall check SpiceDB for `model:use` permission on the selected model before returning it to the caller. | Must | Test | Approved |
| REQ-016 | The system shall evaluate OPA policy `soma.model_routing` to verify the model is allowed for the tenant's cost tier. | Must | Test | Approved |

**Rationale:** Both SpiceDB (relationship-based) and OPA (rule-based) enforcements are required.

**Dependencies:** REQ-013

#### 3.1.9 Audit Logging

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-017 | The system shall persist a `ModelSelectionLog` record for every selection decision, including `capsule_id`, `tenant_id`, `turn_id`, `required_capabilities`, `selected_model`, `selected_provider`, `cost_tier`, `reason`, `spicedb_allowed`, and `opa_allowed`. | Must | Test | Approved |

**Rationale:** Audit logs support debugging, compliance, and billing reconciliation.

**Dependencies:** REQ-015, REQ-016

### 3.2 Non-Functional Requirements

#### 3.2.1 Performance

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-PERF-001 | Model selection shall complete within 10 ms when the database is healthy. | <10 ms | Test |
| NFR-PERF-002 | Model selection shall complete within 5 ms when using a cached model list. | <5 ms | Test |

#### 3.2.2 Security

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-SEC-001 | Tenant A shall never see models scoped to Tenant B. | 100% | Test |
| NFR-SEC-002 | Premium models shall be blocked for basic-tier tenants per OPA policy. | 100% | Test |

#### 3.2.3 Reliability

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-REL-001 | If the database is unavailable, the system shall fall back to a cached model list. | — | Test |

#### 3.2.4 Maintainability

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-MNT-001 | The selection algorithm shall be implemented in a single module with clear filter stages. | — | Inspection |

---

### 3.3 External Interface Requirements

#### 3.3.1 User Interfaces

Not applicable.

#### 3.3.2 Software Interfaces

| Interface | Protocol | Format | Authentication |
|-----------|----------|--------|----------------|
| LLMModelConfig | Django ORM | Python objects | Django auth |
| SpiceDB | gRPC | Protobuf | mTLS |
| OPA | HTTP | JSON | Internal |
| LiteLLM Client Factory | Direct import | Python objects | API key (from store) |

#### 3.3.3 Hardware Interfaces

Not applicable.

---

### 3.4 Design Constraints

| ID | Constraint | Source |
|----|------------|--------|
| DC-001 | `LLMModelConfig` is the single source of truth for all model metadata. | Data architecture |
| DC-002 | Selection must be deterministic for identical inputs (same capsule, tenant, message). | Testing requirement |

---

## 4. Traceability

### 4.1 Requirements Traceability Matrix

| REQ ID | Description | Source | Design | Implementation | Test |
|--------|-------------|--------|--------|----------------|------|
| REQ-001 | Always include text capability | Model spec | Detector | `admin/core/model_router.py` | `tests/agent_chat/test_full_chat_flow.py` |
| REQ-002 | Vision capability from image/* | Multimodal spec | MIME detector | `admin/core/model_router.py` | `tests/agent_chat/test_full_chat_flow.py` |
| REQ-003 | Video capability from video/* | Multimodal spec | MIME detector | `admin/core/model_router.py` | `tests/agent_chat/test_full_chat_flow.py` |
| REQ-004 | Audio capability from audio/* | Multimodal spec | MIME detector | `admin/core/model_router.py` | `tests/agent_chat/test_full_chat_flow.py` |
| REQ-005 | Document capability from PDF | Multimodal spec | MIME detector | `admin/core/model_router.py` | `tests/agent_chat/test_full_chat_flow.py` |
| REQ-006 | Query active models | Data model | ORM query | `admin/llm/models.py` | `tests/agent_chat/test_full_chat_flow.py` |
| REQ-007 | Filter by capabilities | Model spec | Query filter | `admin/core/model_router.py` | `tests/agent_chat/test_full_chat_flow.py` |
| REQ-008 | Capsule allowed_models filter | Capsule spec | Constraint filter | `admin/core/model_router.py` | `tests/agent_chat/test_full_chat_flow.py` |
| REQ-009 | Tenant-scoped filtering | Multi-tenancy spec | Tenant filter | `admin/core/model_router.py` | `tests/agent_chat/test_full_chat_flow.py` |
| REQ-010 | Tenant isolation enforcement | Multi-tenancy spec | Access control | `admin/core/model_router.py` | `tests/saas/test_chat_flow_e2e.py` |
| REQ-011 | Cost tier preference | Budget spec | Preference filter | `admin/core/model_router.py` | `tests/agent_chat/test_full_chat_flow.py` |
| REQ-012 | Priority descending sort | Model spec | Sorter | `admin/core/model_router.py` | `tests/agent_chat/test_full_chat_flow.py` |
| REQ-013 | Return SelectedModel | API contract | Dataclass | `admin/core/model_router.py` | `tests/agent_chat/test_full_chat_flow.py` |
| REQ-014 | Raise NoCapableModelError | Error spec | Exception | `admin/core/model_router.py` | `tests/saas/test_chat_flow_e2e.py` |
| REQ-015 | SpiceDB permission check | Auth spec | gRPC check | `services/common/spicedb_client.py` | `tests/agent_chat/test_full_chat_flow.py` |
| REQ-016 | OPA policy evaluation | Policy spec | HTTP check | `policy/soma_development.rego` | `tests/agent_chat/test_full_chat_flow.py` |
| REQ-017 | ModelSelectionLog audit | Audit spec | ORM write | `admin/llm/models.py` | `tests/agent_chat/test_full_chat_flow.py` |

### 4.2 Requirement to Test Case Mapping

| REQ ID | Test Case ID | Test Method | Expected Result |
|--------|--------------|-------------|-----------------|
| REQ-001 | TC-001 | Unit | `text` in capabilities for text-only message |
| REQ-002 | TC-002 | Unit | `vision` added for PNG attachment |
| REQ-007 | TC-003 | Unit | Inactive models excluded |
| REQ-008 | TC-004 | Unit | Selection restricted to allowed_models |
| REQ-010 | TC-005 | Integration | Tenant cannot access other tenant's models |
| REQ-014 | TC-006 | Unit | `NoCapableModelError` raised when no match |
| REQ-015 | TC-007 | Integration | SpiceDB denial blocks model use |
| REQ-017 | TC-008 | Integration | Audit log record created |

---

## 5. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-16 | Engineering | Initial version |
| 1.1 | 2026-05-21 | Engineering | Refactored to ISO/IEC/IEEE 29148 template |

---

*Document conforms to ISO/IEC/IEEE 29148:2018 — Systems and Software Engineering — Life Cycle Processes — Requirements Engineering.*
