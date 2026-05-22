# SRS-TEST-MODULES — Module-Based Test Suite Design

| Field | Value |
|-------|-------|
| **System** | SomaAgent01 |
| **Document ID** | SRS-TEST-MODULES-2026-05-21 |
| **Version** | 1.1 |
| **Date** | 2026-05-21 |
| **Status** | Draft |
| **Author** | QA Team |
| **Owner** | Engineering |

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

This document specifies the module-based test suite design for the SomaAgent01 system. It defines test coverage requirements across Unit, AAAS Direct, and Integration test categories for each core module, following the 12-Phase Chat Flow architecture.

### 1.2 Scope

**Included:**
- Test suite organization by module (AgentIQ, Context Builder, Chat Orchestrator, Budget System, Feature Flags, Model Router, Multimodal, Tool System, SomaBrain Client, Billing, Permission Matrix)
- Test execution commands and environment requirements
- Coverage requirements for Unit, AAAS Direct, and Integration test types

**Excluded:**
- E2E HTTP endpoint tests (covered in SRS-TEST-WORKBENCH)
- Cross-repository test flow validation (covered in SRS-TEST-WORKBENCH)
- Performance and load testing

### 1.3 Definitions

| Term | Definition |
|------|------------|
| **Unit Test** | Pure logic verification with no external dependencies |
| **AAAS Direct Test** | Test executed against real infrastructure (Postgres, Redis, Milvus) |
| **Integration Test** | Cross-module verification requiring multiple components |
| **12-Phase Chat Flow** | The canonical message processing pipeline from tenant resolution through response delivery |
| **AAAS** | Autonomous Adaptive Agent Stack |

### 1.4 References

| ID | Document | Version | Location |
|----|----------|---------|----------|
| REF-001 | SRS-AGENTIQ | 6.0 | `docs/srs/SRS-AGENTIQ.md` |
| REF-002 | SRS-CHAT-FLOW-MASTER | 1.0 | `docs/srs/SRS-CHAT-FLOW-MASTER.md` |
| REF-003 | SRS-TEST-WORKBENCH | 1.0 | `docs/srs/SRS-TEST-WORKBENCH.md` |
| REF-004 | SRS-SAAS-INFRASTRUCTURE | 2.1 | `docs/srs/SRS-SAAS-INFRASTRUCTURE.md` |

---

## 2. Product Description

### 2.1 Product Perspective

The test suite is an integral part of the SomaAgent01 development lifecycle. Tests are organized by module and test type, with AAAS Direct tests requiring the AAAS infrastructure stack defined in SRS-SAAS-INFRASTRUCTURE. The test hierarchy follows: Unit (no infra) -> AAAS Direct (real infra) -> Integration (cross-module).

### 2.2 Product Functions

| ID | Function | Description |
|----|----------|-------------|
| FUNC-001 | Unit Test Execution | Run pure logic tests without external services |
| FUNC-002 | AAAS Direct Test Execution | Run tests against real Postgres, Redis, Milvus, and SpiceDB |
| FUNC-003 | Integration Test Execution | Run cross-module verification tests |
| FUNC-004 | Test Discovery | Pytest-based automatic test discovery per module directory |
| FUNC-005 | Coverage Reporting | Generate coverage reports for each test category |

### 2.3 User Characteristics

| User Type | Role | Technical Level | Access |
|-----------|------|-----------------|--------|
| Backend Developer | Write and run unit tests | Intermediate | Unit test directories |
| QA Engineer | Execute AAAS Direct and integration tests | Advanced | Full test suite |
| CI/CD Pipeline | Automated test execution | Automated | All test commands |

### 2.4 Constraints

| ID | Constraint | Description |
|----|------------|-------------|
| CON-001 | AAAS Direct Requires Infra | AAAS Direct tests require `SA01_INFRA_AVAILABLE=1` and running Docker Compose stack |
| CON-002 | Pytest Only | All tests must be compatible with pytest framework |
| CON-003 | No Hardcoded Values | Tests must use Django settings or UUID isolation (VIBE Rule 91) |

### 2.5 Assumptions and Dependencies

| ID | Assumption / Dependency | Impact if Invalid |
|----|------------------------|-------------------|
| AD-001 | Docker Compose stack defined in `infra/aaas/docker-compose.yml` is available | AAAS Direct tests cannot execute |
| AD-002 | Pytest and pytest-django are installed in the virtual environment | Test execution fails |
| AD-003 | Django settings module is set for each test category | Database-backed tests fail |

---

## 3. Specific Requirements

### 3.1 Functional Requirements

#### 3.1.1 AgentIQ (SimpleGovernor)

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-001 | The AgentIQ module shall have unit tests verifying autonomy level derivation from `capsule.body.persona.knobs.autonomy_level`. | Must | Test | Draft |
| REQ-002 | The AgentIQ module shall have unit tests verifying intelligence level affects tool permissions. | Must | Test | Draft |
| REQ-003 | The AgentIQ module shall have unit tests verifying budget ratios (tokens, tools, images) from knobs. | Must | Test | Draft |
| REQ-004 | The AgentIQ module shall have AAAS Direct tests verifying UnifiedGate permission checks against real SpiceDB. | Must | Test | Draft |
| REQ-005 | The AgentIQ module shall have AAAS Direct tests verifying governor denies actions when budget is exhausted. | Must | Test | Draft |

**Rationale:** AgentIQ is the governance and security layer; comprehensive testing is critical.

#### 3.1.2 Context Builder

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-006 | The Context Builder module shall have unit tests verifying default lane allocation percentages (system=15%, history=30%, memory=25%, tools=20%, buffer=10%). | Must | Test | Draft |
| REQ-007 | The Context Builder module shall have unit tests verifying total tokens do not exceed `model.context_window`. | Must | Test | Draft |
| REQ-008 | The Context Builder module shall have unit tests verifying `capsule.body.learned.lane_preferences` override defaults. | Must | Test | Draft |
| REQ-009 | The Context Builder module shall have AAAS Direct tests verifying memory recall populates the memory lane via SomaBrain. | Must | Test | Draft |
| REQ-010 | The Context Builder module shall have AAAS Direct tests verifying available tools populate the tools lane. | Must | Test | Draft |
| REQ-011 | The Context Builder module shall have AAAS Direct tests verifying history lane truncates oldest messages when over limit. | Must | Test | Draft |

#### 3.1.3 Chat Orchestrator (12-Phase Flow)

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-012 | The Chat Orchestrator shall have AAAS Direct tests for Phase 1: tenant resolution from token. | Must | Test | Draft |
| REQ-013 | The Chat Orchestrator shall have AAAS Direct tests for Phase 2: capsule loaded from database. | Must | Test | Draft |
| REQ-014 | The Chat Orchestrator shall have AAAS Direct tests for Phase 3: budget checked before processing. | Must | Test | Draft |
| REQ-015 | The Chat Orchestrator shall have AAAS Direct tests for Phase 4: AgentIQ derives settings from knobs. | Must | Test | Draft |
| REQ-016 | The Chat Orchestrator shall have AAAS Direct tests for Phase 5: context assembled from lanes. | Must | Test | Draft |
| REQ-017 | The Chat Orchestrator shall have AAAS Direct tests for Phase 6: model selected based on task complexity. | Must | Test | Draft |
| REQ-018 | The Chat Orchestrator shall have AAAS Direct tests for Phase 7: LLM called with built context. | Must | Test | Draft |
| REQ-019 | The Chat Orchestrator shall have AAAS Direct tests for Phase 8: tool executed if requested. | Must | Test | Draft |
| REQ-020 | The Chat Orchestrator shall have AAAS Direct tests for Phase 9: image and audio processed. | Must | Test | Draft |
| REQ-021 | The Chat Orchestrator shall have AAAS Direct tests for Phase 10: SomaBrain memorize called. | Must | Test | Draft |
| REQ-022 | The Chat Orchestrator shall have AAAS Direct tests for Phase 11: billing event emitted. | Must | Test | Draft |
| REQ-023 | The Chat Orchestrator shall have AAAS Direct tests for Phase 12: response streamed to client. | Must | Test | Draft |

**Rationale:** The 12-Phase Flow is the core business logic of the system.

#### 3.1.4 Budget System

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-024 | The Budget System shall have unit tests verifying current usage starts at zero. | Must | Test | Draft |
| REQ-025 | The Budget System shall have unit tests verifying increment usage increases the count. | Must | Test | Draft |
| REQ-026 | The Budget System shall have unit tests verifying budget available returns true when under limit. | Must | Test | Draft |
| REQ-027 | The Budget System shall have unit tests verifying budget available returns false when exceeded. | Must | Test | Draft |
| REQ-028 | The Budget System shall have unit tests verifying remaining budget calculation is accurate. | Must | Test | Draft |
| REQ-029 | The Budget System shall have AAAS Direct tests verifying budget enforcement against real Redis. | Must | Test | Draft |

#### 3.1.5 Feature Flags

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-030 | The Feature Flags module shall have unit tests verifying core features are enabled by default. | Must | Test | Draft |
| REQ-031 | The Feature Flags module shall have unit tests verifying high-tier features are disabled for default tenants. | Must | Test | Draft |
| REQ-032 | The Feature Flags module shall have unit tests verifying Redis override enables features. | Must | Test | Draft |
| REQ-033 | The Feature Flags module shall have unit tests verifying dependency chain enforcement. | Must | Test | Draft |
| REQ-034 | The Feature Flags module shall have AAAS Direct tests verifying feature state against real Redis. | Must | Test | Draft |

#### 3.1.6 Model Router

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-035 | The Model Router shall have unit tests verifying task complexity classification (simple, moderate, complex). | Must | Test | Draft |
| REQ-036 | The Model Router shall have unit tests verifying fallback chain order: Primary to Secondary to Tertiary. | Must | Test | Draft |
| REQ-037 | The Model Router shall have unit tests verifying selected model supports required capabilities (vision, tools). | Must | Test | Draft |
| REQ-038 | The Model Router shall have AAAS Direct tests verifying model configuration loads from real database. | Must | Test | Draft |
| REQ-039 | The Model Router shall have AAAS Direct tests verifying circuit breaker triggers on model failure. | Must | Test | Draft |

#### 3.1.7 Multimodal

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-040 | The Multimodal module shall have AAAS Direct tests verifying image generation checks budget first. | Must | Test | Draft |
| REQ-041 | The Multimodal module shall have AAAS Direct tests verifying vision tasks route to vision-capable models. | Must | Test | Draft |
| REQ-042 | The Multimodal module shall have AAAS Direct tests verifying text-to-speech requires `voice_synthesis` feature enabled. | Must | Test | Draft |

#### 3.1.8 Tool System

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-043 | The Tool System shall have unit tests verifying all registered tools are discoverable. | Must | Test | Draft |
| REQ-044 | The Tool System shall have unit tests verifying tool parameters are validated against schema. | Must | Test | Draft |
| REQ-045 | The Tool System shall have AAAS Direct tests verifying SpiceDB permission check before execution. | Must | Test | Draft |
| REQ-046 | The Tool System shall have AAAS Direct tests verifying tool execution is logged to AuditLog. | Must | Test | Draft |
| REQ-047 | The Tool System shall have AAAS Direct tests verifying tool calls increment the usage counter. | Must | Test | Draft |

#### 3.1.9 SomaBrain Client

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-048 | The SomaBrain Client shall have AAAS Direct tests verifying direct import mode (not HTTP) in AAAS context. | Must | Test | Draft |
| REQ-049 | The SomaBrain Client shall have AAAS Direct tests verifying `recall()` returns semantic memories. | Must | Test | Draft |
| REQ-050 | The SomaBrain Client shall have AAAS Direct tests verifying `memorize()` persists to vector store. | Must | Test | Draft |
| REQ-051 | The SomaBrain Client shall have AAAS Direct tests verifying `learn()` updates `capsule.body.learned`. | Must | Test | Draft |

#### 3.1.10 Billing (Lago)

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-052 | The Billing module shall have AAAS Direct tests verifying billing events are sent to Lago after requests. | Must | Test | Draft |
| REQ-053 | The Billing module shall have AAAS Direct tests verifying tenant subscription tier is resolved from Lago. | Must | Test | Draft |

#### 3.1.11 Permission Matrix

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-054 | The Permission Matrix shall have unit tests verifying role permissions inherit correctly. | Must | Test | Draft |
| REQ-055 | The Permission Matrix shall have unit tests verifying explicit deny takes precedence over allow. | Must | Test | Draft |
| REQ-056 | The Permission Matrix shall have AAAS Direct tests verifying SpiceDB `check_permission` returns correct results. | Must | Test | Draft |

---

### 3.2 Non-Functional Requirements

#### 3.2.1 Performance

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-PERF-001 | Unit tests shall complete within 30 seconds for the full suite. | 30s | Test |
| NFR-PERF-002 | AAAS Direct tests shall complete within 5 minutes for the full suite. | 300s | Test |

#### 3.2.2 Reliability

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-REL-001 | Tests shall use unique test data (UUID isolation) to prevent cross-test contamination. | 100% | Inspection |
| NFR-REL-002 | AAAS Direct tests shall skip gracefully when infrastructure is unavailable. | 100% | Test |

#### 3.2.3 Maintainability

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-MNT-001 | Each module shall have a dedicated test directory matching its source module path. | 100% | Inspection |
| NFR-MNT-002 | Test files shall follow the naming convention `test_{module}_{type}.py`. | 100% | Inspection |

---

### 3.3 External Interface Requirements

#### 3.3.1 Software Interfaces

The test suite interfaces with pytest for execution and the following real services during AAAS Direct tests:

| Interface | Protocol | Format | Authentication |
|-----------|----------|--------|----------------|
| Postgres | TCP | SQL | Password |
| Redis | TCP | RESP | Password |
| Milvus | gRPC/HTTP | Protobuf/JSON | Token |
| SpiceDB | gRPC | Protobuf | Preshared Key |
| Lago API | HTTP/1.1 | JSON | API Key |

---

### 3.4 Design Constraints

| ID | Constraint | Source |
|----|------------|--------|
| DC-001 | All tests must use Django settings for configuration values (VIBE Rule 91). | VIBE Rule 91 |
| DC-002 | AAAS Direct tests must be marked with `@pytest.mark.aaas`. | Test Convention |
| DC-003 | Unit tests must not require any running services. | Test Pyramid |

---

## 4. Traceability

### 4.1 Requirements Traceability Matrix

| REQ ID | Description | Source | Design | Implementation | Test |
|--------|-------------|--------|--------|----------------|------|
| REQ-001 | Autonomy level derivation | SRS-AGENTIQ | `admin/core/agentiq/derivation.py` | `admin/core/agentiq/derivation.py` | `tests/unit/test_agentiq_unit.py` |
| REQ-002 | Intelligence affects permissions | SRS-AGENTIQ | `admin/core/agentiq/tables.py` | `admin/core/agentiq/tables.py` | `tests/unit/test_agentiq_unit.py` |
| REQ-004 | UnifiedGate SpiceDB check | SRS-AGENTIQ | `admin/core/agentiq/unified_gate.py` | `admin/core/agentiq/unified_gate.py` | `tests/aaas_direct/agentiq/test_agentiq_aaas.py` |
| REQ-006 | Lane allocation percentages | SRS-CONTEXT-BUILDING | `admin/core/context/` | `admin/core/context/` | `tests/unit/test_context_builder_unit.py` |
| REQ-009 | Memory recall lane population | SRS-SOMABRAIN-INTEGRATION | `admin/core/somabrain_client.py` | `admin/core/somabrain_client.py` | `tests/aaas_direct/context/test_context_builder_aaas.py` |
| REQ-012 | Phase 1 tenant resolution | SRS-CHAT-FLOW-MASTER | `admin/core/chat_orchestrator.py` | `admin/core/chat_orchestrator.py` | `tests/aaas_direct/orchestrator/test_chat_orchestrator_aaas.py` |
| REQ-013 | Phase 2 capsule load | SRS-CHAT-FLOW-MASTER | `admin/core/models.py` | `admin/core/models.py` | `tests/aaas_direct/orchestrator/test_chat_orchestrator_aaas.py` |
| REQ-014 | Phase 3 budget gate | SRS-BUDGET-SYSTEM | `admin/core/budget/` | `admin/core/budget/` | `tests/aaas_direct/orchestrator/test_chat_orchestrator_aaas.py` |
| REQ-015 | Phase 4 AgentIQ derivation | SRS-AGENTIQ | `admin/core/agentiq/derivation.py` | `admin/core/agentiq/derivation.py` | `tests/aaas_direct/orchestrator/test_chat_orchestrator_aaas.py` |
| REQ-016 | Phase 5 context building | SRS-CONTEXT-BUILDING | `admin/core/context/` | `admin/core/context/` | `tests/aaas_direct/orchestrator/test_chat_orchestrator_aaas.py` |
| REQ-017 | Phase 6 model selection | SRS-MODEL-ROUTING | `admin/core/model_router.py` | `admin/core/model_router.py` | `tests/aaas_direct/orchestrator/test_chat_orchestrator_aaas.py` |
| REQ-018 | Phase 7 LLM inference | SRS-MODEL-ROUTING | `admin/core/model_router.py` | `admin/core/model_router.py` | `tests/aaas_direct/orchestrator/test_chat_orchestrator_aaas.py` |
| REQ-019 | Phase 8 tool execution | SRS-TOOL-SYSTEM | `admin/core/tools/` | `admin/core/tools/` | `tests/aaas_direct/orchestrator/test_chat_orchestrator_aaas.py` |
| REQ-020 | Phase 9 multimodal handling | SRS-MULTIMODAL | `admin/core/multimodal.py` | `admin/core/multimodal.py` | `tests/aaas_direct/orchestrator/test_chat_orchestrator_aaas.py` |
| REQ-021 | Phase 10 memory update | SRS-SOMABRAIN-INTEGRATION | `admin/core/somabrain_client.py` | `admin/core/somabrain_client.py` | `tests/aaas_direct/orchestrator/test_chat_orchestrator_aaas.py` |
| REQ-022 | Phase 11 billing event | SRS-LAGO-BILLING | `admin/core/billing.py` | `admin/core/billing.py` | `tests/aaas_direct/orchestrator/test_chat_orchestrator_aaas.py` |
| REQ-023 | Phase 12 response delivery | SRS-CHAT-FLOW-MASTER | `admin/core/chat_orchestrator.py` | `admin/core/chat_orchestrator.py` | `tests/aaas_direct/orchestrator/test_chat_orchestrator_aaas.py` |
| REQ-024 | Budget starts at zero | SRS-BUDGET-SYSTEM | `admin/core/budget/` | `admin/core/budget/` | `tests/unit/test_budget_system.py` |
| REQ-030 | Core features enabled | SRS-FEATURE-FLAGS | `admin/core/features/` | `admin/core/features/` | `tests/unit/test_features_system.py` |
| REQ-035 | Complexity classification | SRS-MODEL-ROUTING | `admin/core/model_router.py` | `admin/core/model_router.py` | `tests/unit/test_model_router_unit.py` |
| REQ-040 | Image generation budget check | SRS-MULTIMODAL | `admin/core/multimodal.py` | `admin/core/multimodal.py` | `tests/aaas_direct/multimodal/test_multimodal_aaas.py` |
| REQ-043 | Tool registry discovery | SRS-TOOL-SYSTEM | `admin/core/tools/` | `admin/core/tools/` | `tests/unit/test_tool_system_unit.py` |
| REQ-048 | SomaBrain direct import | SRS-SOMABRAIN-INTEGRATION | `admin/core/somabrain_client.py` | `admin/core/somabrain_client.py` | `tests/aaas_direct/somabrain/test_somabrain_client_aaas.py` |
| REQ-052 | Lago event emission | SRS-LAGO-BILLING | `admin/core/billing.py` | `admin/core/billing.py` | `tests/aaas_direct/billing/test_billing_aaas.py` |
| REQ-054 | Permission inheritance | SRS-PERMISSION-MATRIX | `admin/core/permission_matrix.py` | `admin/core/permission_matrix.py` | `tests/unit/test_permission_matrix_unit.py` |

### 4.2 Requirement to Test Case Mapping

| REQ ID | Test Case ID | Test Method | Expected Result |
|--------|--------------|-------------|-----------------|
| REQ-001 | TC-AGENTIQ-001 | Unit test | Autonomy derived correctly from knobs |
| REQ-004 | TC-AGENTIQ-002 | AAAS Direct | UnifiedGate returns correct permission against SpiceDB |
| REQ-006 | TC-CONTEXT-001 | Unit test | Lane percentages match specification |
| REQ-012 | TC-ORCH-001 | AAAS Direct | Tenant resolved from JWT token |
| REQ-024 | TC-BUDGET-001 | Unit test | Usage counter initialized to zero |
| REQ-035 | TC-ROUTER-001 | Unit test | Task classified into correct complexity bucket |
| REQ-043 | TC-TOOLS-001 | Unit test | All tools discoverable via registry |
| REQ-048 | TC-BRAIN-001 | AAAS Direct | Client mode equals "direct" in AAAS context |
| REQ-052 | TC-BILLING-001 | AAAS Direct | Lago event payload valid and accepted |
| REQ-054 | TC-PERM-001 | Unit test | Child role inherits parent permissions |

---

## 5. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-17 | QA Team | Initial version with module test matrix |
| 1.1 | 2026-05-21 | QA Team | Refactored to ISO/IEC/IEEE 29148 template; extracted requirements as REQ-XXX |

---

*Document conforms to ISO/IEC/IEEE 29148:2018 — Systems and Software Engineering — Life Cycle Processes — Requirements Engineering.*
