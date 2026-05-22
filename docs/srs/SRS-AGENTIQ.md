# SRS-AGENTIQ — Governor Control Loop

| Field | Value |
|-------|-------|
| **System** | SomaAgent01 |
| **Document ID** | SRS-AGENTIQ-2026-05-21 |
| **Version** | 6.1 |
| **Date** | 2026-05-21 |
| **Status** | Canonical |
| **Author** | Core Engineering Team |
| **Owner** | Security and Governance Team |

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

This document specifies the requirements for AgentIQ, the governor control loop for the SomaAgent01 system. AgentIQ derives all agent settings from three control knobs defined in `capsule.body.persona.knobs` and enforces permissions through a unified gate combining OPA policies, SpiceDB relations, and capsule scope checks.

### 1.2 Scope

**Included:**
- Setting derivation from intelligence, autonomy, and resource knobs
- UnifiedGate permission enforcement
- In-memory OPA caching with zero HTTP latency in AAAS mode
- Chat flow integration (Phases 3 and 4)

**Excluded:**
- Capsule persistence layer (covered in SRS-DATA-MODELS)
- LLM model selection (covered in SRS-MODEL-ROUTING)
- Tool execution logic (covered in SRS-TOOL-SYSTEM)

### 1.3 Definitions

| Term | Definition |
|------|------------|
| **AgentIQ** | The governor control loop responsible for deriving settings and enforcing permissions |
| **UnifiedGate** | Single permission check combining OPA, SpiceDB, and capsule scope |
| **Knobs** | The three control parameters in `capsule.body.persona.knobs`: intelligence_level, autonomy_level, resource_budget |
| **DerivedSettings** | Immutable Pydantic model containing all settings derived from knobs |
| **HITL** | Human-in-the-Loop |
| **AAAS** | Autonomous Adaptive Agent Stack |

### 1.4 References

| ID | Document | Version | Location |
|----|----------|---------|----------|
| REF-001 | SRS-DATA-MODELS | 1.0 | `docs/srs/SRS-DATA-MODELS.md` |
| REF-002 | SRS-CONTEXT-BUILDING | 1.0 | `docs/srs/SRS-CONTEXT-BUILDING.md` |
| REF-003 | SRS-MODEL-ROUTING | 1.0 | `docs/srs/SRS-MODEL-ROUTING.md` |
| REF-004 | SRS-TOOL-SYSTEM | 1.0 | `docs/srs/SRS-TOOL-SYSTEM.md` |
| REF-005 | SRS-TEST-MODULES | 1.1 | `docs/srs/SRS-TEST-MODULES.md` |

---

## 2. Product Description

### 2.1 Product Perspective

AgentIQ is a core component of SomaAgent01 (Layer 4) that operates during the 12-Phase Chat Flow. It integrates with the Capsule model to derive runtime settings and with the governance subsystem to enforce permissions. In AAAS mode, AgentIQ, UnifiedGate, and OPA use in-memory caching with zero HTTP latency.

### 2.2 Product Functions

| ID | Function | Description |
|----|----------|-------------|
| FUNC-001 | Setting Derivation | Derive temperature, max_tokens, model_tier, recall_limit, and rlm_iterations from intelligence_level |
| FUNC-002 | Autonomy Derivation | Derive HITL requirements, tool_approval mode, and egress_allowed from autonomy_level |
| FUNC-003 | Resource Derivation | Derive token_limit, cost_tier, and thinking_budget from resource_budget |
| FUNC-004 | Unified Permission Check | Combine OPA policy, SpiceDB relation, and capsule scope into a single allow/deny decision |
| FUNC-005 | Endpoint Permission Check | Verify endpoint-level permissions without capsule context |

### 2.3 User Characteristics

| User Type | Role | Technical Level | Access |
|-----------|------|-----------------|--------|
| Capsule Owner | Configure persona knobs | Basic | Capsule settings UI |
| Security Engineer | Define OPA policies and SpiceDB relations | Advanced | Governance configuration |
| System Developer | Integrate AgentIQ into chat flow | Advanced | Source code and APIs |

### 2.4 Constraints

| ID | Constraint | Description |
|----|------------|-------------|
| CON-001 | Zero HTTP Latency | In AAAS mode, all derivation and permission checks must use in-memory operations |
| CON-002 | Fail-Closed Security | Any error in permission checking must result in denial |
| CON-003 | Bounded Inputs | Knob values must be clamped to valid ranges (intelligence: 1-10, autonomy: 1-10, budget: non-negative) |

### 2.5 Assumptions and Dependencies

| ID | Assumption / Dependency | Impact if Invalid |
|----|------------------------|-------------------|
| AD-001 | Capsule model contains valid `body.persona.knobs` structure | Derivation raises ValueError |
| AD-002 | OPA policies are pre-compiled and available in capsule governance | Policy checks fall back to deny |
| AD-003 | SpiceDB is reachable for relation checks | Relation checks fall back to deny |

---

## 3. Specific Requirements

### 3.1 Functional Requirements

#### 3.1.1 Setting Derivation

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-001 | The system shall derive `temperature` from `intelligence_level` using the Intelligence Table: levels 1-3 yield 0.3, 4-6 yield 0.7, 7-8 yield 0.8, 9-10 yield 0.9. | Must | Test | Draft |
| REQ-002 | The system shall derive `max_tokens` from `intelligence_level` using the Intelligence Table: levels 1-3 yield 512, 4-6 yield 2048, 7-8 yield 4096, 9-10 yield 8192. | Must | Test | Draft |
| REQ-003 | The system shall derive `rlm_iterations` from `intelligence_level`: 1 for levels 1-3, 2 for 4-6, 3 for 7-8, 5 for 9-10. | Must | Test | Draft |
| REQ-004 | The system shall derive `recall_limit` from `intelligence_level`: 5 for levels 1-3, 15 for 4-6, 25 for 7-8, 50 for 9-10. | Must | Test | Draft |
| REQ-005 | The system shall derive `model_tier` from `intelligence_level`: "budget" for 1-3, "standard" for 4-6, "premium" for 7-8, "flagship" for 9-10. | Must | Test | Draft |
| REQ-006 | The system shall derive `brain_query_enabled` from `intelligence_level`: false for levels 1-3, true for 4-10. | Must | Test | Draft |
| REQ-007 | The system shall derive `require_hitl` from `autonomy_level`: true for levels 1-3, false for 4-10. | Must | Test | Draft |
| REQ-008 | The system shall derive `tool_approval` from `autonomy_level`: "all" for 1-3, "dangerous" for 4-6, "none" for 7-10. | Must | Test | Draft |
| REQ-009 | The system shall derive `egress_allowed` from `autonomy_level`: "none" for 1-3, "whitelist" for 4-6, "expanded" for 7-8, "unrestricted" for 9-10. | Must | Test | Draft |
| REQ-010 | The system shall derive `token_limit` from `resource_budget`: 1000 for 0.0-0.10, 10000 for 0.10-0.50, 50000 for 0.50-2.00, 100000 for 2.00+. | Must | Test | Draft |
| REQ-011 | The system shall derive `cost_tier` from `resource_budget`: "budget" for 0.0-0.10, "standard" for 0.10-0.50, "premium" for 0.50-2.00, "flagship" for 2.00+. | Must | Test | Draft |
| REQ-012 | The system shall derive `thinking_budget` from `resource_budget`: 256 for 0.0-0.10, 1024 for 0.10-0.50, 2048 for 0.50-2.00, 4096 for 2.00+. | Must | Test | Draft |
| REQ-013 | The system shall clamp `intelligence_level` to the range [1, 10] before lookup. | Must | Test | Draft |
| REQ-014 | The system shall clamp `autonomy_level` to the range [1, 10] before lookup. | Must | Test | Draft |
| REQ-015 | The system shall reject negative `resource_budget` values by treating them as 0.0. | Must | Test | Draft |

**Rationale:** All settings must be deterministic and derived exclusively from the three knobs to prevent hardcoded configuration drift.

**Dependencies:** REQ-013, REQ-014, REQ-015 must be satisfied before REQ-001 through REQ-012.

#### 3.1.2 UnifiedGate

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-016 | The UnifiedGate shall check OPA policy from `capsule.body.governance.opa_policies` before allowing an action. | Must | Test | Draft |
| REQ-017 | The UnifiedGate shall deny the action if no OPA policy is defined for the requested action (secure-by-default). | Must | Test | Draft |
| REQ-018 | The UnifiedGate shall cache OPA check results using a hash of the policies content for cross-worker safety. | Must | Test | Draft |
| REQ-019 | The UnifiedGate shall check SpiceDB permission from `capsule.body.governance.spicedb_relations` after OPA approval. | Must | Test | Draft |
| REQ-020 | The UnifiedGate shall deny the action if no SpiceDB relation is defined for the requested action (secure-by-default). | Must | Test | Draft |
| REQ-021 | The UnifiedGate shall check capsule scope from `capsule.body.persona.tools.enabled_capabilities` after SpiceDB approval. | Must | Test | Draft |
| REQ-022 | The UnifiedGate shall deny tool actions if the tool is not in `enabled_capabilities`. | Must | Test | Draft |
| REQ-023 | The UnifiedGate shall return true for non-tool actions after OPA and SpiceDB approval. | Must | Test | Draft |
| REQ-024 | The UnifiedGate shall return false (deny) for any exception during the permission check (fail-closed). | Must | Test | Draft |
| REQ-025 | The UnifiedGate shall provide an endpoint permission check method that operates without capsule context, using Django settings `ENDPOINT_PERMISSIONS`. | Must | Test | Draft |
| REQ-026 | The endpoint permission check shall deny if no permission mapping exists in settings. | Must | Test | Draft |
| REQ-027 | The endpoint permission check shall allow if the user is in the explicit allow-list or if the mapping equals "*". | Must | Test | Draft |

**Rationale:** Security requires a fail-closed design where any missing policy, relation, or error results in denial.

#### 3.1.3 Chat Flow Integration

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-028 | During Phase 3 of the chat flow, the system shall call `derive_all_settings(capsule)` to produce a `DerivedSettings` instance. | Must | Test | Draft |
| REQ-029 | During Phase 4 of the chat flow, the system shall call `UnifiedGate.check(capsule, action)` before executing any action. | Must | Test | Draft |
| REQ-030 | All derivation calls shall be traceable via OpenTelemetry. | Should | Inspection | Draft |

---

### 3.2 Non-Functional Requirements

#### 3.2.1 Performance

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-PERF-001 | Setting derivation shall complete in under 1 millisecond. | 1ms | Benchmark |
| NFR-PERF-002 | Cached OPA checks shall complete in under 1 millisecond. | 1ms | Benchmark |

#### 3.2.2 Security

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-SEC-001 | All permission checks shall follow fail-closed semantics. | 100% | Test |
| NFR-SEC-002 | DerivedSettings shall be immutable after creation (frozen Pydantic model). | 100% | Inspection |
| NFR-SEC-003 | Input knob values shall be bounded to prevent injection or overflow. | 100% | Test |

#### 3.2.3 Reliability

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-REL-001 | Derivation shall not raise exceptions for malformed capsules; it shall use safe defaults (level 5, budget 0.10). | 100% | Test |

#### 3.2.4 Maintainability

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-MNT-001 | Derivation tables shall be defined as frozen dataclasses for type safety. | 100% | Inspection |
| NFR-MNT-002 | The derivation function shall be a pure function with no side effects. | 100% | Inspection |

---

### 3.3 External Interface Requirements

#### 3.3.1 Software Interfaces

| Interface | Protocol | Format | Authentication |
|-----------|----------|--------|----------------|
| Capsule Model | In-memory | Pydantic / Django ORM | N/A |
| SpiceDB | gRPC | Protobuf | Preshared Key |
| OPA Engine | In-memory | Python dict | N/A |
| Django Settings | In-memory | Python module | N/A |

---

### 3.4 Design Constraints

| ID | Constraint | Source |
|----|------------|--------|
| DC-001 | In AAAS mode, all derivation and gate checks use in-memory operations with zero HTTP calls. | AAAS Architecture |
| DC-002 | All settings are derived from `capsule.body.persona.knobs`; no hardcoded values permitted. | VIBE Rule 91 |
| DC-003 | OPA cache key must use content hash, not object identity, for cross-worker safety. | Security Requirement |

---

## 4. Traceability

### 4.1 Requirements Traceability Matrix

| REQ ID | Description | Source | Design | Implementation | Test |
|--------|-------------|--------|--------|----------------|------|
| REQ-001 | Temperature derivation | SRS-AGENTIQ v6.0 | `admin/core/agentiq/tables.py` | `admin/core/agentiq/tables.py` | `tests/unit/test_agentiq_unit.py` |
| REQ-002 | Max tokens derivation | SRS-AGENTIQ v6.0 | `admin/core/agentiq/tables.py` | `admin/core/agentiq/tables.py` | `tests/unit/test_agentiq_unit.py` |
| REQ-005 | Model tier derivation | SRS-AGENTIQ v6.0 | `admin/core/agentiq/tables.py` | `admin/core/agentiq/tables.py` | `tests/unit/test_agentiq_unit.py` |
| REQ-007 | HITL derivation | SRS-AGENTIQ v6.0 | `admin/core/agentiq/tables.py` | `admin/core/agentiq/tables.py` | `tests/unit/test_agentiq_unit.py` |
| REQ-009 | Egress derivation | SRS-AGENTIQ v6.0 | `admin/core/agentiq/tables.py` | `admin/core/agentiq/tables.py` | `tests/unit/test_agentiq_unit.py` |
| REQ-010 | Token limit derivation | SRS-AGENTIQ v6.0 | `admin/core/agentiq/tables.py` | `admin/core/agentiq/tables.py` | `tests/unit/test_agentiq_unit.py` |
| REQ-013 | Intelligence clamping | Security | `admin/core/agentiq/tables.py` | `admin/core/agentiq/tables.py` | `tests/unit/test_agentiq_unit.py` |
| REQ-016 | OPA policy check | Security | `admin/core/agentiq/unified_gate.py` | `admin/core/agentiq/unified_gate.py` | `tests/aaas_direct/agentiq/test_agentiq_aaas.py` |
| REQ-017 | OPA deny by default | Security | `admin/core/agentiq/unified_gate.py` | `admin/core/agentiq/unified_gate.py` | `tests/aaas_direct/agentiq/test_agentiq_aaas.py` |
| REQ-018 | OPA caching | Performance | `admin/core/agentiq/unified_gate.py` | `admin/core/agentiq/unified_gate.py` | `tests/unit/test_agentiq_unit.py` |
| REQ-019 | SpiceDB check | Security | `admin/core/agentiq/unified_gate.py` | `admin/core/agentiq/unified_gate.py` | `tests/aaas_direct/agentiq/test_agentiq_aaas.py` |
| REQ-024 | Fail-closed exception handling | Security | `admin/core/agentiq/unified_gate.py` | `admin/core/agentiq/unified_gate.py` | `tests/unit/test_agentiq_unit.py` |
| REQ-025 | Endpoint permission check | Security | `admin/core/agentiq/unified_gate.py` | `admin/core/agentiq/unified_gate.py` | `tests/aaas_direct/agentiq/test_agentiq_aaas.py` |
| REQ-028 | Phase 3 derivation call | SRS-CHAT-FLOW-MASTER | `admin/core/chat_orchestrator.py` | `admin/core/chat_orchestrator.py` | `tests/aaas_direct/orchestrator/test_chat_orchestrator_aaas.py` |
| REQ-029 | Phase 4 gate check | SRS-CHAT-FLOW-MASTER | `admin/core/chat_orchestrator.py` | `admin/core/chat_orchestrator.py` | `tests/aaas_direct/orchestrator/test_chat_orchestrator_aaas.py` |

### 4.2 Requirement to Test Case Mapping

| REQ ID | Test Case ID | Test Method | Expected Result |
|--------|--------------|-------------|-----------------|
| REQ-001 | TC-AIQ-001 | Unit test | `lookup_intelligence(5).temperature == 0.7` |
| REQ-005 | TC-AIQ-002 | Unit test | `lookup_intelligence(9).model_tier == "flagship"` |
| REQ-007 | TC-AIQ-003 | Unit test | `lookup_autonomy(2).require_hitl == True` |
| REQ-009 | TC-AIQ-004 | Unit test | `lookup_autonomy(5).egress_allowed == "whitelist"` |
| REQ-013 | TC-AIQ-005 | Unit test | `lookup_intelligence(0)` clamps to range (1,3) |
| REQ-016 | TC-AIQ-006 | AAAS Direct | OPA policy allow=True permits action |
| REQ-017 | TC-AIQ-007 | AAAS Direct | Missing OPA policy results in denial |
| REQ-024 | TC-AIQ-008 | Unit test | Exception in check() returns False |
| REQ-028 | TC-AIQ-009 | AAAS Direct | Chat orchestrator calls derive_all_settings in Phase 3 |
| REQ-029 | TC-AIQ-010 | AAAS Direct | Chat orchestrator calls UnifiedGate.check in Phase 4 |

---

## 5. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-15 | Core Engineering Team | Initial derivation tables |
| 6.0 | 2026-01-16 | Core Engineering Team | AAAS Direct Calls Enforced, UnifiedGate added |
| 6.1 | 2026-05-21 | Core Engineering Team | Refactored to ISO/IEC/IEEE 29148 template; removed personas, emojis, and excessive code blocks; extracted requirements as REQ-XXX |

---

*Document conforms to ISO/IEC/IEEE 29148:2018 — Systems and Software Engineering — Life Cycle Processes — Requirements Engineering.*
