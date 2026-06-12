# SRS-650-LINE-SOVEREIGNTY — VIBE Rule 245 Enforcement

| Field | Value |
|-------|-------|
| **System** | SomaAgent01, SomaBrain, SomaFractalMemory |
| **Document ID** | SRS-650-LINE-SOVEREIGNTY-2026-05-21 |
| **Version** | 1.1 |
| **Date** | 2026-05-21 |
| **Status** | Draft |
| **Author** | SOMA Architecture Team |
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

This document specifies requirements for enforcing VIBE Rule 245 (Linear Sovereignty) across the SOMA ecosystem. Linear Sovereignty mandates that no Python module shall exceed 650 lines of code.

### 1.2 Scope

**Included:**
- Decomposition of oversized Python modules in SomaBrain and SomaAgent01
- Backward compatibility via `__init__.py` re-exports
- Verification procedures for line count, import integrity, and E2E behavior

**Excluded:**
- Migration files (excluded by convention)
- Third-party dependencies
- Auto-generated code

### 1.3 Definitions

| Term | Definition |
|------|------------|
| **Linear Sovereignty** | VIBE Rule 245: No module exceeds 650 lines of source code |
| **Pattern-Based Split** | Decomposition following named design patterns (e.g., middleware, validators, core) |
| **Backward Compatibility** | Original import paths continue working via `__init__.py` re-exports |

### 1.4 References

| ID | Document | Version | Location |
|----|----------|---------|----------|
| REF-001 | VIBE Rule 245 | 1.0 | `docs/standards/VIBE.md` |
| REF-002 | VIBE Rule 102 | 1.0 | `docs/standards/VIBE.md` |
| REF-003 | SRS-TEST-MODULES | 1.1 | `docs/srs/SRS-TEST-MODULES.md` |
| REF-004 | SRS-SAAS-INFRASTRUCTURE | 2.1 | `docs/srs/SRS-SAAS-INFRASTRUCTURE.md` |

---

## 2. Product Description

### 2.1 Product Perspective

The 650-line limit is a code quality constraint applied across the SOMA ecosystem. SomaFractalMemory is already compliant. SomaBrain has 14 violating files totaling +8,547 excess lines. SomaAgent01 has 8 violating files totaling +1,088 excess lines. This specification defines the decomposition requirements to achieve compliance.

### 2.2 Product Functions

| ID | Function | Description |
|----|----------|-------------|
| FUNC-001 | Line Count Enforcement | Verify no Python module exceeds 650 lines |
| FUNC-002 | Pattern-Based Decomposition | Split oversized modules by component responsibility |
| FUNC-003 | Import Re-export | Maintain backward compatibility via `__init__.py` |
| FUNC-004 | Import Verification | Confirm all original import paths continue working |
| FUNC-005 | E2E Verification | Confirm system behavior is unchanged after decomposition |

### 2.3 User Characteristics

| User Type | Role | Technical Level | Access |
|-----------|------|-----------------|--------|
| Backend Developer | Refactor and maintain modules | Advanced | All source code |
| Code Reviewer | Verify compliance during review | Intermediate | Pull requests |
| CI/CD Pipeline | Automated line count checks | Automated | All repositories |

### 2.4 Constraints

| ID | Constraint | Description |
|----|------------|-------------|
| CON-001 | 650-Line Maximum | No Python module (excluding migrations) may exceed 650 lines |
| CON-002 | Backward Compatibility | All original import paths must continue working |
| CON-003 | Zero Downtime | Refactoring must not require service restart during deployment |

### 2.5 Assumptions and Dependencies

| ID | Assumption / Dependency | Impact if Invalid |
|----|------------------------|-------------------|
| AD-001 | Modules can be decomposed without circular imports | Refactoring blocked |
| AD-002 | `makemigrations` detects model moves correctly | Database schema out of sync |
| AD-003 | Automated import test suite exists | Re-export regressions undetected |

---

## 3. Specific Requirements

### 3.1 Functional Requirements

#### 3.1.1 SomaBrain app.py Decomposition

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-001 | The system shall decompose `somabrain/app.py` (4,242 lines) into modules each not exceeding 650 lines. | Must | Test | Draft |
| REQ-002 | The `SimpleOPAEngine` component (lines 65-88) shall be relocated to `app/opa.py`. | Must | Inspection | Draft |
| REQ-003 | The `CognitiveMiddleware` component (lines 658-725) shall be relocated to `app/middleware.py`. | Must | Inspection | Draft |
| REQ-004 | The `CognitiveInputValidator` component (lines 728-804) shall be relocated to `app/validators.py`. | Must | Inspection | Draft |
| REQ-005 | The `SecurityMiddleware` component (lines 807-867) shall be relocated to `app/middleware.py`. | Must | Inspection | Draft |
| REQ-006 | The `UnifiedBrainCore` component (lines 2126-2247) shall be relocated to `core/unified_brain.py`. | Must | Inspection | Draft |
| REQ-007 | The `AutoScalingFractalIntelligence` component (lines 2290-2440) shall be relocated to `core/auto_scaling.py`. | Must | Inspection | Draft |
| REQ-008 | The `ComplexityDetector` component (lines 2443-2473) shall be relocated to `core/complexity.py`. | Must | Inspection | Draft |
| REQ-009 | The admin endpoints (lines 1065-1542) shall be relocated to `api/endpoints/admin_internal.py`. | Must | Inspection | Draft |
| REQ-010 | The health endpoints (lines 2549-2809) shall be relocated to `api/endpoints/health.py`. | Must | Inspection | Draft |
| REQ-011 | The lifecycle handlers (lines 4019-4242) shall be relocated to `app/lifecycle.py`. | Must | Inspection | Draft |
| REQ-012 | The scoring functions (lines 173-506) shall be relocated to `scoring/candidate_scoring.py`. | Must | Inspection | Draft |
| REQ-013 | After decomposition, `from somabrain.app import app` shall continue to work. | Must | Test | Draft |
| REQ-014 | After decomposition, all 65 existing API endpoints shall remain functional. | Must | Test | Draft |
| REQ-015 | After decomposition, the health check endpoint `GET /health` shall continue to respond with 200 OK. | Must | Test | Draft |

**Rationale:** `app.py` is the most critical file in SomaBrain. Decomposition must preserve all existing behavior.

#### 3.1.2 SomaBrain memory_client.py Decomposition

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-016 | The system shall decompose `somabrain/memory_client.py` (2,420 lines) into modules each not exceeding 650 lines. | Must | Test | Draft |
| REQ-017 | The base client class shall be relocated to `memory_client/base.py`. | Must | Inspection | Draft |
| REQ-018 | The HTTP transport layer shall be relocated to `memory_client/http.py`. | Must | Inspection | Draft |
| REQ-019 | The batch operations logic shall be relocated to `memory_client/batch.py`. | Must | Inspection | Draft |
| REQ-020 | The tenant isolation logic shall be relocated to `memory_client/tenant.py`. | Must | Inspection | Draft |
| REQ-021 | The circuit breaker logic shall be relocated to `memory_client/resilience.py`. | Must | Inspection | Draft |

#### 3.1.3 SomaAgent01 core/models.py Decomposition

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-022 | The system shall decompose `admin/core/models.py` into modules each not exceeding 650 lines. | Must | Test | Draft |
| REQ-023 | The `Session` and `SessionEvent` models shall be relocated to `models/session.py`. | Must | Inspection | Draft |
| REQ-024 | The `Capability` model shall be relocated to `models/capability.py`. | Must | Inspection | Draft |
| REQ-025 | The `UISetting` and `FeatureFlag` models shall be relocated to `models/settings.py`. | Must | Inspection | Draft |
| REQ-026 | The `Job` and `SystemTask` models shall be relocated to `models/jobs.py`. | Must | Inspection | Draft |
| REQ-027 | The `Notification` model shall be relocated to `models/notification.py`. | Must | Inspection | Draft |
| REQ-028 | The `Prompt` model shall be relocated to `models/prompt.py`. | Must | Inspection | Draft |
| REQ-029 | The `AuditLog` model shall be relocated to `models/audit.py`. | Must | Inspection | Draft |
| REQ-030 | After decomposition, `from admin.core.models import Capsule` shall continue to work. | Must | Test | Draft |
| REQ-031 | After decomposition, Django migrations shall correctly detect model moves. | Must | Test | Draft |
| REQ-032 | After decomposition, all ForeignKey relationships shall be preserved. | Must | Test | Draft |

**Rationale:** `core/models.py` contains 19 Django models. Splitting by domain preserves model integrity.

#### 3.1.4 SomaAgent01 Remaining Files

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-033 | ~~The system shall decompose `admin/conversations/api.py` to not exceed 650 lines.~~ | Should | Test | **N/A — `admin/conversations/` was deleted; chat endpoints consolidated into `admin/chat/api/chat.py`** |
| REQ-034 | The system shall decompose `admin/permissions/granular.py` to not exceed 650 lines. | Should | Test | Draft |
| REQ-035 | The system shall decompose `admin/voice/api.py` to not exceed 650 lines. | Should | Test | Draft |
| REQ-036 | The system shall decompose `admin/flink/api.py` to not exceed 650 lines. | Should | Test | Draft |
| REQ-037 | The system shall decompose `admin/core/helpers/scheduler_models.py` to not exceed 650 lines. | Should | Test | Draft |
| REQ-038 | The system shall decompose `admin/core/helpers/memory_stores.py` to not exceed 650 lines. | Should | Test | Draft |

---

### 3.2 Non-Functional Requirements

#### 3.2.1 Performance

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-PERF-001 | Import time for re-exported modules shall not increase by more than 10% after decomposition. | 110% baseline | Benchmark |

#### 3.2.2 Security

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-SEC-001 | Decomposition shall not expose internal module paths that were previously inaccessible. | 100% | Inspection |

#### 3.2.3 Reliability

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-REL-001 | Each new module shall have corresponding unit tests. | 100% | Inspection |
| NFR-REL-002 | The system shall pass full E2E regression tests after decomposition. | 100% | Test |

#### 3.2.4 Maintainability

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-MNT-001 | New modules shall follow the existing naming conventions and directory structure. | 100% | Inspection |

---

### 3.3 External Interface Requirements

No external interfaces are affected by this refactoring.

---

### 3.4 Design Constraints

| ID | Constraint | Source |
|----|------------|--------|
| DC-001 | All original import paths must continue working via `__init__.py` re-exports. | VIBE Rule 102 |
| DC-002 | Circular imports must be avoided using `TYPE_CHECKING` and lazy imports where necessary. | Architecture Decision |
| DC-003 | Django model moves must be validated with `makemigrations` after each change. | Django Best Practice |

---

## 4. Traceability

### 4.1 Requirements Traceability Matrix

| REQ ID | Description | Source | Design | Implementation | Test |
|--------|-------------|--------|--------|----------------|------|
| REQ-001 | app.py decomposition | VIBE-245 | `somabrain/app/` | `somabrain/app/opa.py`, `app/middleware.py`, `app/validators.py`, `app/lifecycle.py` | `tests/unit/test_app_imports.py` |
| REQ-002 | SimpleOPAEngine relocation | VIBE-245 | `somabrain/app/opa.py` | `somabrain/app/opa.py` | `tests/unit/test_app_imports.py` |
| REQ-006 | UnifiedBrainCore relocation | VIBE-245 | `somabrain/core/unified_brain.py` | `somabrain/core/unified_brain.py` | `tests/unit/test_app_imports.py` |
| REQ-013 | Backward import compatibility | VIBE-102 | `somabrain/app/__init__.py` | `somabrain/app/__init__.py` | `tests/unit/test_app_imports.py` |
| REQ-014 | API endpoint preservation | VIBE-245 | `somabrain/api/endpoints/` | `somabrain/api/endpoints/*.py` | `tests/integration/test_api_endpoints.py` |
| REQ-015 | Health check preservation | VIBE-245 | `somabrain/api/endpoints/health.py` | `somabrain/api/endpoints/health.py` | `tests/integration/test_health.py` |
| REQ-016 | memory_client.py decomposition | VIBE-245 | `somabrain/memory_client/` | `somabrain/memory_client/base.py`, `http.py`, `batch.py`, `tenant.py`, `resilience.py` | `tests/unit/test_memory_client.py` |
| REQ-022 | core/models.py decomposition | VIBE-245 | `admin/core/models/` | `admin/core/models/session.py`, `capability.py`, `settings.py`, `jobs.py`, `notification.py`, `prompt.py`, `audit.py` | `tests/unit/test_models_import.py` |
| REQ-030 | Capsule import compatibility | VIBE-102 | `admin/core/models/__init__.py` | `admin/core/models/__init__.py` | `tests/unit/test_models_import.py` |
| REQ-031 | Migration detection | VIBE-245 | Django migrations | `makemigrations` output | `tests/django/test_migrations.py` |
| REQ-033 | ~~conversations/api.py decomposition~~ | VIBE-245 | N/A | N/A — `admin/conversations/` deleted; chat endpoints in `admin/chat/api/chat.py` | N/A |
| REQ-034 | permissions/granular.py decomposition | VIBE-245 | `admin/permissions/` | `admin/permissions/*.py` | `tests/unit/test_permissions.py` |
| REQ-035 | voice/api.py decomposition | VIBE-245 | `admin/voice/api/` | `admin/voice/api/*.py` | `tests/unit/test_voice_api.py` |
| REQ-036 | flink/api.py decomposition | VIBE-245 | `admin/flink/api/` | `admin/flink/api/*.py` | `tests/unit/test_flink_api.py` |
| REQ-037 | scheduler_models.py decomposition | VIBE-245 | `admin/core/helpers/` | `admin/core/helpers/*.py` | `tests/unit/test_scheduler_models.py` |
| REQ-038 | memory_stores.py decomposition | VIBE-245 | `admin/core/helpers/` | `admin/core/helpers/*.py` | `tests/unit/test_memory_stores.py` |

### 4.2 Requirement to Test Case Mapping

| REQ ID | Test Case ID | Test Method | Expected Result |
|--------|--------------|-------------|-----------------|
| REQ-001 | TC-650-001 | Shell script | `find . -name "*.py" -not -path "*/migrations/*" -exec wc -l {} \; | awk '$1 > 650 {print}'` returns no output |
| REQ-013 | TC-650-002 | Import test | `from somabrain.app import app` succeeds without error |
| REQ-015 | TC-650-003 | HTTP request | `GET /health` returns status 200 |
| REQ-030 | TC-650-004 | Import test | `from admin.core.models import Capsule` succeeds without error |
| REQ-031 | TC-650-005 | Django command | `python manage.py makemigrations --check --dry-run` exits 0 |
| REQ-032 | TC-650-006 | Database inspection | All ForeignKey constraints remain valid |

---

## 5. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-21 | SOMA Architecture Team | Initial version with architecture analysis and functional requirements |
| 1.1 | 2026-05-21 | SOMA Architecture Team | Refactored to ISO/IEC/IEEE 29148 template; renumbered FR-XXX to REQ-XXX; expanded traceability matrix; added non-functional requirements sections |

---

*Document conforms to ISO/IEC/IEEE 29148:2018 — Systems and Software Engineering — Life Cycle Processes — Requirements Engineering.*
