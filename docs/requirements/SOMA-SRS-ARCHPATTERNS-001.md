# SRS-ARCHITECTURAL-PATTERNS — Modular Design Patterns

| Field | Value |
|-------|-------|
| **System** | SomaAgent01 |
| **Document ID** | SRS-ARCH-PATTERNS-2026-001 |
| **Version** | 1.1 |
| **Date** | 2026-01-21 |
| **Status** | Approved |
| **Author** | Soma Engineering |
| **Owner** | Architecture Team |

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

This document specifies the architectural patterns enforced across all SomaAgent01 repositories to ensure maintainable, testable, and scalable code. It defines mandatory technology choices, layer separation, domain segregation, and quality targets.

### 1.2 Scope

**In scope:**
- Mandatory framework stack (Django + Django Ninja)
- Layered application architecture (API, Schema, Service, Model)
- Domain model segregation by bounded context
- Schema-endpoint separation
- Dependency direction rules
- Code quality metrics and targets

**Out of scope:**
- Infrastructure deployment patterns (Kubernetes, Docker)
- CI/CD pipeline configuration
- Frontend framework patterns (covered by separate frontend standards)

### 1.3 Definitions

| Term | Definition |
|------|------------|
| API Layer | HTTP routing, authentication, and request/response handling modules (`api.py`) |
| Bounded Context | A defined boundary within which a particular domain model is applicable |
| Django Ninja | A web framework for building APIs with Django and Python type hints |
| Domain Model | Group of related models representing a bounded business context |
| Model Layer | Django ORM models handling persistence (`models.py` or `models/`) |
| Schema Layer | Pydantic-based data validation and serialization contracts (`schemas.py`) |
| Service Layer | Business logic and orchestration modules (`*_service.py`) |
| VIBE Rule | Internal coding standard governing file size, complexity, and structure |

### 1.4 References

| ID | Document | Version | Location |
|----|----------|---------|----------|
| REF-001 | SRS-DATA-MODELS | 5.1 | `docs/srs/SRS-DATA-MODELS.md` |
| REF-002 | SRS-SECURITY-MULTITENANCY | 1.1 | `docs/srs/SRS-SECURITY-MULTITENANCY.md` |
| REF-003 | Django Documentation | 5.0 | https://docs.djangoproject.com |
| REF-004 | Django Ninja Documentation | 1.0 | https://django-ninja.dev |
| REF-005 | ISO/IEC 25010:2023 | 2023 | Systems and Software Quality Requirements and Evaluation |

---

## 2. Product Description

### 2.1 Product Perspective

The architectural patterns defined in this document apply to all backend code in the SomaAgent01 platform. They form the structural foundation that enables multiple teams to work concurrently on different domains without creating circular dependencies or inconsistent APIs.

### 2.2 Product Functions

| ID | Function | Description |
|----|----------|-------------|
| FUNC-001 | Framework Enforcement | Ensure all backend services use Django and Django Ninja consistently |
| FUNC-002 | Layer Separation | Isolate HTTP handling, data contracts, business logic, and persistence into distinct layers |
| FUNC-003 | Domain Segregation | Organize models and services by bounded context to minimize coupling |
| FUNC-004 | Quality Enforcement | Maintain code complexity and file size within defined thresholds |
| FUNC-005 | Dependency Control | Enforce unidirectional dependencies from API to Model layers |

### 2.3 User Characteristics

| User Type | Role | Technical Level | Access |
|-----------|------|-----------------|--------|
| Backend Developer | Implements features and fixes | High | All backend modules |
| Code Reviewer | Reviews pull requests | High | All backend modules |
| QA Engineer | Writes automated tests | Medium | Test modules and fixtures |
| DevOps Engineer | Maintains build pipelines | Medium | CI configuration and lint rules |

### 2.4 Constraints

| ID | Constraint | Description |
|----|------------|-------------|
| CON-001 | Django Only | All APIs must use Django Ninja; FastAPI, Starlette, and standalone uvicorn are prohibited |
| CON-002 | Django ORM Only | All database models must use Django ORM; SQLAlchemy is prohibited |
| CON-003 | Django Migrations Only | All schema changes must use Django migrations; Alembic is prohibited |
| CON-004 | Ninja Auth | Authentication must use Django auth combined with `django-ninja` AuthBearer |
| CON-005 | Centralized Settings | All configuration must use Django settings module |

### 2.5 Assumptions and Dependencies

| ID | Assumption / Dependency | Impact if Invalid |
|----|------------------------|-------------------|
| AD-001 | All developers are familiar with Django and Django Ninja patterns | Inconsistent implementation and review overhead |
| AD-002 | Linting and CI pipelines enforce file size and complexity limits | Quality degradation if checks are bypassed |
| AD-003 | Django 5.x remains the supported LTS or stable version | Framework upgrade required |

---

## 3. Specific Requirements

### 3.1 Functional Requirements

#### 3.1.1 Framework Stack

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-ARCH-001 | The system shall use Django as the sole web framework for all backend services. | Must | Inspection | Approved |
| REQ-ARCH-002 | The system shall use Django Ninja as the sole API framework for HTTP endpoint definitions. | Must | Inspection | Approved |
| REQ-ARCH-003 | The system shall use Django ORM for all database persistence. | Must | Inspection | Approved |
| REQ-ARCH-004 | The system shall use Django migrations for all database schema changes. | Must | Inspection | Approved |
| REQ-ARCH-005 | The system shall use Django auth combined with `django-ninja` AuthBearer for API authentication. | Must | Inspection | Approved |
| REQ-ARCH-006 | The system shall use Django settings as the centralized configuration mechanism. | Must | Inspection | Approved |
| REQ-ARCH-007 | The system shall prohibit the use of FastAPI, Starlette, SQLAlchemy, and Alembic in any backend module. | Must | Inspection | Approved |

**Rationale:** Technology uniformity reduces cognitive load, simplifies onboarding, and enables shared tooling and middleware.

#### 3.1.2 Layered Architecture

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-ARCH-008 | The system shall organize backend modules into four layers: API Layer (`api.py`), Schema Layer (`schemas.py`), Service Layer (`*_service.py`), and Model Layer (`models/` or `models.py`). | Must | Inspection | Approved |
| REQ-ARCH-009 | The system shall ensure dependencies flow downward only: API depends on Schema and Service; Service depends on Model and Enum; Schema depends on Enum. | Must | Inspection | Approved |
| REQ-ARCH-010 | The system shall prohibit upward dependencies (e.g., Model layer shall not import from Service or API layers). | Must | Inspection | Approved |
| REQ-ARCH-011 | The system shall define all data contracts (request/response shapes) in `schemas.py` using Pydantic models. | Must | Inspection | Approved |
| REQ-ARCH-012 | The system shall define all HTTP handlers (routing, auth, serialization) in `api.py`. | Must | Inspection | Approved |
| REQ-ARCH-013 | The system shall implement business logic and orchestration in dedicated service modules (`*_service.py`). | Must | Inspection | Approved |

**Rationale:** Layer separation enables independent testing, reduces coupling, and clarifies responsibility boundaries.

#### 3.1.3 Domain Model Segregation

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-ARCH-014 | The system shall split models by bounded context into separate files or packages under `admin/<domain>/models/`. | Must | Inspection | Approved |
| REQ-ARCH-015 | The system shall use `__init__.py` within model packages to define public exports. | Must | Inspection | Approved |

#### 3.1.4 Enum Extraction

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-ARCH-016 | The system shall define enums and constants in dedicated modules (e.g., `scheduler_enums.py`) to avoid circular imports and enable reuse. | Must | Inspection | Approved |

---

### 3.2 Non-Functional Requirements

#### 3.2.1 Performance

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-PERF-001 | API endpoint handler overhead (excluding business logic) shall be less than or equal to 5 ms. | 5 ms | Test |

#### 3.2.2 Security

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-SEC-001 | Authentication middleware shall run on every API request before business logic execution. | 100% coverage | Inspection |

#### 3.2.3 Reliability

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-REL-001 | Service layer functions shall be independently unit testable without HTTP client setup. | 100% coverage | Test |

#### 3.2.4 Scalability

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-SCL-001 | Domain model segregation shall allow independent deployment of bounded contexts if needed in future architecture. | N/A | Analysis |

#### 3.2.5 Maintainability

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-MNT-001 | Each source file shall not exceed 650 lines (VIBE Rule 245). | 650 lines | Lint / CI |
| NFR-MNT-002 | Each function shall have cyclomatic complexity less than or equal to 10. | 10 | Lint / CI |
| NFR-MNT-003 | Overall test coverage shall be greater than or equal to 80%. | 80% | Coverage report |
| NFR-MNT-004 | Service decomposition shall split files exceeding 650 lines into focused sub-modules. | 650 lines | Lint / CI |

---

### 3.3 External Interface Requirements

#### 3.3.1 User Interfaces

No direct user interface requirements are specified in this document.

#### 3.3.2 Software Interfaces

| Interface | Protocol | Format | Authentication |
|-----------|----------|--------|----------------|
| Django Admin | HTTPS | HTML | Django session |
| Django Ninja API | HTTPS / REST | JSON | JWT (AuthBearer) |

#### 3.3.3 Hardware Interfaces

No hardware interface requirements are specified in this document.

---

### 3.4 Design Constraints

| ID | Constraint | Source |
|----|------------|--------|
| DC-001 | All APIs must use Django Ninja, not FastAPI. | REQ-ARCH-002 |
| DC-002 | All database access must use Django ORM with tenant-scoped querysets. | REQ-ARCH-003 |
| DC-003 | All schema changes must use Django migrations. | REQ-ARCH-004 |
| DC-004 | File size must not exceed 650 lines. | NFR-MNT-001 |
| DC-005 | Function cyclomatic complexity must not exceed 10. | NFR-MNT-002 |

---

## 4. Traceability

### 4.1 Requirements Traceability Matrix

| REQ ID | Description | Source | Design | Implementation | Test |
|--------|-------------|--------|--------|----------------|------|
| REQ-ARCH-001 | Django framework enforcement | SRS-ARCHITECTURAL-PATTERNS | `admin/settings.py` | `admin/api.py`, `admin/*/api/*.py` | `tests/django/` |
| REQ-ARCH-002 | Django Ninja API framework | SRS-ARCHITECTURAL-PATTERNS | `admin/api.py` | `admin/api.py`, `admin/*/api/*.py` | `tests/django/` |
| REQ-ARCH-003 | Django ORM only | SRS-ARCHITECTURAL-PATTERNS | `admin/*/models/` | `admin/core/models/`, `admin/aaas/models/`, `admin/*/models.py` | `tests/django/` |
| REQ-ARCH-004 | Django migrations only | SRS-ARCHITECTURAL-PATTERNS | `admin/*/migrations/` | `admin/*/migrations/` | Inspection |
| REQ-ARCH-005 | Django Ninja AuthBearer | SRS-ARCHITECTURAL-PATTERNS | `admin/common/auth.py` | `admin/common/auth.py` | `tests/django/test_auth_integration.py` |
| REQ-ARCH-008 | Four-layer architecture | SRS-ARCHITECTURAL-PATTERNS | `admin/*/` | `admin/*/api.py`, `admin/*/schemas.py`, `admin/*/services/`, `admin/*/models/` | Inspection |
| REQ-ARCH-009 | Downward-only dependencies | SRS-ARCHITECTURAL-PATTERNS | Module structure | `admin/*/` | Static analysis |
| REQ-ARCH-011 | Schema contracts in schemas.py | SRS-ARCHITECTURAL-PATTERNS | `admin/*/schemas.py` | `admin/common/schemas.py`, `admin/*/schemas.py` | Inspection |
| REQ-ARCH-012 | HTTP handlers in api.py | SRS-ARCHITECTURAL-PATTERNS | `admin/*/api.py` | `admin/*/api.py`, `admin/*/api/*.py` | Inspection |
| REQ-ARCH-013 | Business logic in service modules | SRS-ARCHITECTURAL-PATTERNS | `admin/*/services/` | `admin/agents/services/`, `admin/*/services/*.py` | Inspection |
| REQ-ARCH-014 | Domain model segregation | SRS-ARCHITECTURAL-PATTERNS | `admin/*/models/` | `admin/core/models/core.py`, `admin/core/models/zdl.py`, `admin/aaas/models/` | Inspection |
| REQ-ARCH-016 | Enum extraction pattern | SRS-ARCHITECTURAL-PATTERNS | `admin/*/enums.py` | `admin/*/scheduler_enums.py`, `admin/*/choices.py` | Inspection |
| NFR-MNT-001 | Max 650 lines per file | SRS-ARCHITECTURAL-PATTERNS | CI pipeline | `pyproject.toml` | CI lint |
| NFR-MNT-002 | Max cyclomatic complexity 10 | SRS-ARCHITECTURAL-PATTERNS | CI pipeline | `pyproject.toml` | CI lint |
| NFR-MNT-003 | Min 80% test coverage | SRS-ARCHITECTURAL-PATTERNS | CI pipeline | `pyproject.toml` | CI coverage report |

### 4.2 Requirement to Test Case Mapping

| REQ ID | Test Case ID | Test Method | Expected Result |
|--------|--------------|-------------|-----------------|
| REQ-ARCH-005 | TC-ARCH-001 | Unit test | Unauthenticated request to protected endpoint returns 401 |
| REQ-ARCH-009 | TC-ARCH-002 | Static analysis | No circular imports detected between Model and Service layers |
| NFR-MNT-001 | TC-ARCH-003 | Lint | No Python file exceeds 650 lines |
| NFR-MNT-002 | TC-ARCH-004 | Lint | No function exceeds cyclomatic complexity of 10 |
| NFR-MNT-003 | TC-ARCH-005 | Coverage report | Overall coverage is greater than or equal to 80% |

---

## 5. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-21 | Soma Engineering | Initial approved version defining Django stack, layered architecture, and quality targets |
| 1.1 | 2026-05-21 | Soma Engineering | Refactored to ISO/IEC/IEEE 29148:2018 template; removed emoji, caution blocks, and mermaid diagrams; added REQ-XXX numbering, traceability matrix, and References section |

---

*Document conforms to ISO/IEC/IEEE 29148:2018 — Systems and Software Engineering — Life Cycle Processes — Requirements Engineering.*
