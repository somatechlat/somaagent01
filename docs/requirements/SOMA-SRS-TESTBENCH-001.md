# SRS-TEST-WORKBENCH — Cross-Repository Test Audit

| Field | Value |
|-------|-------|
| **System** | SomaStack Triad |
| **Document ID** | SRS-TEST-WORKBENCH-2026-05-21 |
| **Version** | 1.1 |
| **Date** | 2026-05-21 |
| **Status** | Audit Complete |
| **Author** | QA Architecture Team |
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

This document specifies the unified testing standard across the SomaStack Triad repositories (SomaAgent01, SomaBrain, SomaFractalMemory). It audits existing test infrastructure and defines requirements for cross-repository test flows based on real interactions only.

### 1.2 Scope

**Included:**
- Test infrastructure audit for all three repositories
- Canonical test patterns (SomaBrain Gold Standard)
- Cross-repository test flow requirements (Agent Journey)
- Test execution command standards
- Quality gate definitions

**Excluded:**
- Module-level test case definitions (covered in SRS-TEST-MODULES)
- Individual unit test logic
- Performance benchmark thresholds

### 1.3 Definitions

| Term | Definition |
|------|------------|
| **SomaStack Triad** | The three-layer system: SomaFractalMemory (Layer 2), SomaBrain (Layer 3), SomaAgent01 (Layer 4) |
| **Gold Standard** | SomaBrain's test infrastructure, used as the canonical pattern for all repositories |
| **Agent Journey** | The end-to-end interaction chain from chat request through Brain to Memory and back |
| **AAAS Direct** | Tests executed against real infrastructure without mocks |
| **Bridge Test** | Tests verifying direct import chains between repository layers |

### 1.4 References

| ID | Document | Version | Location |
|----|----------|---------|----------|
| REF-001 | SRS-TEST-MODULES | 1.1 | `docs/srs/SRS-TEST-MODULES.md` |
| REF-002 | SRS-SAAS-INFRASTRUCTURE | 2.1 | `docs/srs/SRS-SAAS-INFRASTRUCTURE.md` |
| REF-003 | SomaBrain Integration Test Suite | 1.0 | `tests/integration/test_e2e_real.py` |
| REF-004 | SRS-CHAT-FLOW-MASTER | 1.0 | `docs/srs/SRS-CHAT-FLOW-MASTER.md` |

---

## 2. Product Description

### 2.1 Product Perspective

The unified test workbench provides cross-repository testing standards and audit criteria. SomaBrain serves as the Gold Standard with real infrastructure checks via `conftest.py`, centralized settings, health checks before test execution, and clean separation of concerns. SomaAgent01 and SomaFractalMemory must align with this standard.

### 2.2 Product Functions

| ID | Function | Description |
|----|----------|-------------|
| FUNC-001 | Repository Test Audit | Inventory and assess test coverage per repository |
| FUNC-002 | Pattern Standardization | Apply SomaBrain test patterns to all repositories |
| FUNC-003 | Cross-Repository E2E | Execute tests spanning Agent, Brain, and Memory |
| FUNC-004 | Health Check Enforcement | Verify service availability before executing dependent tests |
| FUNC-005 | Quality Gate Reporting | Report test metrics against defined targets |

### 2.3 User Characteristics

| User Type | Role | Technical Level | Access |
|-----------|------|-----------------|--------|
| QA Architect | Define and enforce standards | Expert | All repositories |
| Backend Developer | Implement tests per standard | Intermediate | Assigned repositories |
| CI/CD Pipeline | Automated cross-repo testing | Automated | All test environments |

### 2.4 Constraints

| ID | Constraint | Description |
|----|------------|-------------|
| CON-001 | Real Interactions Only | No mocks of the HTTP layer between repositories |
| CON-002 | Django Settings | All configuration values must come from Django settings (VIBE Rule 91) |
| CON-003 | UUID Isolation | Test data must use UUIDs to prevent cross-test contamination |

### 2.5 Assumptions and Dependencies

| ID | Assumption / Dependency | Impact if Invalid |
|----|------------------------|-------------------|
| AD-001 | All three repositories are cloneable and runnable in the test environment | Cross-repo tests cannot execute |
| AD-002 | SomaBrain `settings.SOMABRAIN_API_URL` is configured | Brain integration tests fail |
| AD-003 | Docker Compose stack provides all backing services | AAAS Direct tests cannot run |

---

## 3. Specific Requirements

### 3.1 Functional Requirements

#### 3.1.1 SomaBrain Gold Standard Pattern

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-001 | SomaBrain's `tests/integration/test_e2e_real.py` shall serve as the canonical test pattern for all repositories. | Must | Inspection | Approved |
| REQ-002 | All repositories shall load external service URLs from Django settings (e.g., `settings.SOMABRAIN_API_URL`). | Must | Inspection | Draft |
| REQ-003 | All repositories shall implement health checks before test execution via `_app_available()` or equivalent. | Must | Test | Draft |
| REQ-004 | All repositories shall use unique test data generated with `uuid.uuid4()` for test isolation. | Must | Inspection | Draft |
| REQ-005 | All repositories shall make real HTTP calls to downstream services; mocking of the HTTP layer is prohibited. | Must | Inspection | Draft |
| REQ-006 | All repositories shall use tenant headers (`_get_test_headers(tenant_id)`) for multi-tenant isolation in tests. | Must | Inspection | Draft |

**Rationale:** SomaBrain is the Gold Standard. These patterns ensure reproducible, realistic test behavior.

#### 3.1.2 Cross-Repository Test Flow (Agent Journey)

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-007 | The unified test workbench shall verify the Agent Journey: chat request enters SomaAgent01, budget and feature checks execute via Redis, AgentIQ derivation occurs, Brain recall query flows to Memory search, LLM inference occurs, Brain memorize persists to Memory store, and response returns to the client. | Must | Test | Draft |
| REQ-008 | SomaAgent01 shall provide E2E tests for Phase 1 (Tenant Resolution) and Phase 2 (Capsule Load). | Must | Test | Draft |
| REQ-009 | SomaAgent01 shall provide AAAS Direct tests for Phase 3 (Budget Gate). | Must | Test | Draft |
| REQ-010 | SomaAgent01 shall provide tests for Phase 10 (Memory Update) via direct SomaBrain calls. | Must | Test | Draft |
| REQ-011 | SomaAgent01 shall provide tests for Phase 12 (Response Delivery). | Must | Test | Draft |
| REQ-012 | SomaBrain shall provide E2E tests for memory recall and memorize operations via `test_memory_e2e.py`. | Must | Test | Draft |
| REQ-013 | SomaFractalMemory shall provide integration tests for vector search and storage via `test_deep_integration.py`. | Must | Test | Draft |

#### 3.1.3 Bridge Tests (Direct Import Pattern)

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-014 | SomaAgent01 shall provide bridge tests verifying SomaBrain is imported directly (not via HTTP) in AAAS mode. | Must | Test | Draft |
| REQ-015 | SomaAgent01 shall provide bridge tests verifying `SomaBrainClient.recall()` calls SomaBrain directly and returns a list. | Must | Test | Draft |
| REQ-016 | SomaAgent01 shall provide bridge tests verifying `SomaBrainClient.memorize()` persists to the vector store. | Must | Test | Draft |
| REQ-017 | SomaAgent01 shall provide bridge tests verifying `SomaBrainClient.learn()` updates `capsule.body.learned`. | Must | Test | Draft |

#### 3.1.4 SomaFractalMemory Restructure

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-018 | SomaFractalMemory shall restructure its flat `tests/` directory into `tests/unit/`, `tests/integration/`, and `tests/e2e/`. | Must | Inspection | Draft |
| REQ-019 | SomaFractalMemory shall move `test_fast_core_math.py` to `tests/unit/`. | Must | Inspection | Draft |
| REQ-020 | SomaFractalMemory shall move `test_deep_integration.py` and `test_live_integration.py` to `tests/integration/`. | Must | Inspection | Draft |
| REQ-021 | SomaFractalMemory shall move `test_end_to_end_memory.py` to `tests/e2e/`. | Must | Inspection | Draft |

#### 3.1.5 Test Execution Standards

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-022 | SomaAgent01 unit tests shall execute with `pytest tests/unit/ -v`. | Must | Test | Draft |
| REQ-023 | SomaAgent01 AAAS Direct tests shall execute with `DJANGO_SETTINGS_MODULE=services.gateway.settings SA01_INFRA_AVAILABLE=1 pytest tests/aaas_direct/ -v`. | Must | Test | Draft |
| REQ-024 | SomaBrain tests shall execute with `DJANGO_SETTINGS_MODULE=somabrain.settings pytest tests/ -v`. | Must | Test | Draft |
| REQ-025 | SomaFractalMemory tests shall execute with `DJANGO_SETTINGS_MODULE=sfm.settings pytest tests/ -v`. | Must | Test | Draft |

---

### 3.2 Non-Functional Requirements

#### 3.2.1 Performance

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-PERF-001 | Health check functions shall complete within 5 seconds per service. | 5s | Test |

#### 3.2.2 Reliability

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-REL-001 | Tests shall skip gracefully (not fail) when infrastructure is unavailable. | 100% | Test |
| NFR-REL-002 | UUID-based test data shall prevent cross-test contamination. | 100% | Test |

#### 3.2.3 Quality Gates

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-QG-001 | Unit test coverage shall meet or exceed 80%. | 80% | Coverage report |
| NFR-QG-002 | Integration test coverage shall meet or exceed 60%. | 60% | Coverage report |
| NFR-QG-003 | AAAS Direct coverage shall be 100% for all critical paths. | 100% | Coverage report |
| NFR-QG-004 | Zero hardcoded configuration values shall exist in test code. | 100% | Static analysis |
| NFR-QG-005 | Health checks before test execution shall be present in all repositories. | 100% | Inspection |

---

### 3.3 External Interface Requirements

#### 3.3.1 Software Interfaces

| Interface | Protocol | Format | Authentication |
|-----------|----------|--------|----------------|
| SomaBrain API | HTTP/1.1 | JSON | Bearer Token |
| SomaFractalMemory API | HTTP/1.1 | JSON | Bearer Token |
| SomaAgent01 API | HTTP/1.1 | JSON | Bearer Token |
| Redis | TCP | RESP | Password |
| Postgres | TCP | SQL | Password |

---

### 3.4 Design Constraints

| ID | Constraint | Source |
|----|------------|--------|
| DC-001 | All configuration values must be sourced from Django settings; no hardcoded URLs or credentials. | VIBE Rule 91 |
| DC-002 | Cross-repository tests must use the real HTTP layer; mocking between repositories is prohibited. | Architecture Decision |
| DC-003 | Health checks must be implemented in `conftest.py` or equivalent test initialization. | SomaBrain Gold Standard |

---

## 4. Traceability

### 4.1 Requirements Traceability Matrix

| REQ ID | Description | Source | Design | Implementation | Test |
|--------|-------------|--------|--------|----------------|------|
| REQ-001 | SomaBrain Gold Standard pattern | Audit | `tests/integration/test_e2e_real.py` | `tests/integration/test_e2e_real.py` | `tests/integration/` |
| REQ-002 | Django settings for URLs | VIBE Rule 91 | `conftest.py` | `conftest.py` | `tests/integration/` |
| REQ-003 | Health checks before tests | SomaBrain Pattern | `conftest.py` | `conftest.py` | `tests/integration/` |
| REQ-004 | UUID test data isolation | SomaBrain Pattern | Test fixtures | Test fixtures | All test suites |
| REQ-005 | Real HTTP calls only | VIBE Rule | Test design | Test implementations | `tests/integration/` |
| REQ-007 | Agent Journey E2E | Architecture | Cross-repo design | `tests/e2e/` | `tests/e2e/test_chat_flow_e2e.py` |
| REQ-014 | Direct import bridge tests | AAAS Architecture | `admin/core/somabrain_client.py` | `tests/aaas_direct/test_brain_bridge.py` | `tests/aaas_direct/test_brain_bridge.py` |
| REQ-018 | SFM directory restructure | Audit Finding | `somafractalmemory/tests/` | Directory restructure | Directory inspection |
| REQ-022 | Unit test command | Test Convention | `pytest.ini` | Shell command | CI pipeline |
| REQ-023 | AAAS Direct test command | Test Convention | `pytest.ini` | Shell command | CI pipeline |

### 4.2 Requirement to Test Case Mapping

| REQ ID | Test Case ID | Test Method | Expected Result |
|--------|--------------|-------------|-----------------|
| REQ-003 | TC-WB-001 | Integration test | Test suite skips if `/healthz` returns non-200 |
| REQ-007 | TC-WB-002 | E2E test | Full Agent Journey completes with valid response |
| REQ-014 | TC-WB-003 | Bridge test | `SomaBrainClient` has `_direct_brain` attribute in AAAS mode |
| REQ-018 | TC-WB-004 | Inspection | `somafractalmemory/tests/` contains `unit/`, `integration/`, `e2e/` |
| REQ-022 | TC-WB-005 | Shell execution | `pytest tests/unit/ -v` exits 0 |
| REQ-023 | TC-WB-006 | Shell execution | `SA01_INFRA_AVAILABLE=1 pytest tests/aaas_direct/ -v` exits 0 or skips gracefully |

---

## 5. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-17 | QA Architecture Team | Initial audit document |
| 1.1 | 2026-05-21 | QA Architecture Team | Refactored to ISO/IEC/IEEE 29148 template; extracted requirements as REQ-XXX; removed mermaid diagrams and code blocks |

---

*Document conforms to ISO/IEC/IEEE 29148:2018 — Systems and Software Engineering — Life Cycle Processes — Requirements Engineering.*
