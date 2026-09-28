# SRS-FEATURE-FLAGS — System Feature Toggles

| Field | Value |
|-------|-------|
| **System** | SomaAgent01 |
| **Document ID** | SRS-FEATURE-FLAGS-2026-01-16 |
| **Version** | 1.0 |
| **Date** | 2026-01-16 |
| **Status** | CANONICAL |
| **Author** | Platform Engineering |
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
5. [Revision History](#5-revision-history)

---

## 1. Introduction

### 1.1 Purpose

This document specifies the Feature Toggle system for SomaAgent01. It provides a centralized registry, hierarchical dependency management, credential gating, plan locking, and graceful degradation for agent capabilities.

### 1.2 Scope

**In scope:**
- Feature registry and metadata (`admin/core/features/registry.py`)
- Feature enablement evaluation (`admin/core/features/check.py`)
- Endpoint gating via `@require_feature` decorator (`admin/core/features/gate.py`)
- Tenant toggle management API (`admin/api/features.py`)
- Credential validation against Vault

**Out of scope:**
- Budget enforcement (see [SRS-BUDGET-SYSTEM.md](./SRS-BUDGET-SYSTEM.md))
- Billing plan definitions (see [SRS-LAGO-BILLING.md](./SRS-LAGO-BILLING.md))
- Chat execution logic

### 1.3 Definitions

| Term | Definition |
|------|------------|
| **Feature Toggle** | A system capability that can be enabled or disabled per tenant. |
| **Core Tier** | Features that are always enabled and cannot be toggled off. |
| **Optional Tier** | Features that can be activated or deactivated by tenant administrators. |
| **Dependency** | A prerequisite feature that must be enabled before its dependent feature can be activated. |
| **Credential Gate** | A required external API key or secret (stored in Vault) needed to enable a feature. |
| **Plan Lock** | A minimum subscription plan required to access a feature. |
| **Lockable** | A flag indicating whether a feature can be disabled once enabled. |

### 1.4 References

| ID | Document | Version | Location |
|----|----------|---------|----------|
| REF-001 | SRS-BUDGET-SYSTEM | 1.0 | `docs/srs/SRS-BUDGET-SYSTEM.md` |
| REF-002 | SRS-LAGO-BILLING | 1.0 | `docs/srs/SRS-LAGO-BILLING.md` |
| REF-003 | Django Documentation | 4.2 | https://docs.djangoproject.com/en/4.2/ |

---

## 2. Product Description

### 2.1 Product Perspective

The Feature Toggle system is a cross-cutting capability within SomaAgent01. It is evaluated at request time to determine whether a tenant may access a given feature. It depends on the tenant's plan (from Lago/subscription), credential availability (from Vault), and explicit toggle state (from cache).

### 2.2 Product Functions

| ID | Function | Description |
|----|----------|-------------|
| FUNC-001 | Feature Registration | Define all features in a centralized registry with tiers, dependencies, and credentials. |
| FUNC-002 | Enablement Evaluation | Compute whether a feature is enabled for a tenant based on plan, deps, credentials, and toggle. |
| FUNC-003 | Endpoint Gating | Block access to endpoints when the required feature is disabled. |
| FUNC-004 | Toggle Management | Allow tenant administrators to enable/disable optional features via API. |
| FUNC-005 | Credential Binding | Store and validate feature credentials in Vault. |

### 2.3 User Characteristics

| User Type | Role | Technical Level | Access |
|-----------|------|-----------------|--------|
| Tenant Admin | Enable/disable features, provide credentials | Intermediate | Agent Settings UI / API |
| Platform Engineer | Add new features to registry | Advanced | `admin/core/features/registry.py` |
| End User | Subject to feature availability | Basic | None (transparent) |

### 2.4 Constraints

| ID | Constraint | Description |
|----|------------|-------------|
| CON-001 | Core Immutability | Core-tier features cannot be disabled under any condition. |
| CON-002 | Dependency Order | A feature cannot be enabled if any dependency is disabled. |
| CON-003 | Credential Vault | All feature credentials must be stored in Vault, not in settings or code. |

### 2.5 Assumptions and Dependencies

| ID | Assumption / Dependency | Impact if Invalid |
|----|------------------------|-------------------|
| AD-001 | Vault is available for credential storage. | Credential-gated features cannot be enabled. |
| AD-002 | Django cache is available for toggle state storage. | Toggle overrides cannot be persisted. |
| AD-003 | Plan data is resolvable per tenant (from Lago or local cache). | Plan-locked features cannot be evaluated. |

---

## 3. Specific Requirements

### 3.1 Functional Requirements

#### 3.1.1 Feature Registry

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-FTF-001 | The system shall maintain a `FEATURE_REGISTRY` (`admin/core/features/registry.py`) defining each feature by code, name, description, tier, default enabled state, dependencies, required credentials, minimum plan, and lockable flag. | Must | Inspection | Draft |
| REQ-FTF-002 | Core-tier features shall always be enabled and shall not be toggleable. | Must | Test | Draft |

**Core Features (Tier 1)**

| Feature | Code | Lockable |
|---------|------|----------|
| Chat | `chat` | Yes |
| Authentication | `auth` | Yes |
| Capsule | `capsule` | Yes |
| AgentIQ | `agentiq` | Yes |
| Permissions | `permissions` | Yes |

**Optional Features (Tier 2)**

| Feature | Code | Default | Dependencies | Credentials | Min Plan |
|---------|------|---------|--------------|-------------|----------|
| Billing | `billing` | OFF | None | `LAGO_API_URL`, `LAGO_API_KEY` | None |
| Budgeting | `budgeting` | OFF | `billing` | None | None |
| Memory | `memory` | ON | None | None | None |
| Learning | `learning` | OFF | `memory` | None | Starter |
| Tools | `tools` | ON | None | None | None |
| Voice | `voice` | OFF | None | `OPENAI_API_KEY` | Starter |
| Images | `images` | OFF | None | `OPENAI_API_KEY` | Starter |
| Vision | `vision` | OFF | None | `OPENAI_API_KEY` | Starter |
| RLM | `rlm` | OFF | `memory` | None | Team |
| Webhooks | `webhooks` | OFF | `billing` | `LAGO_WEBHOOK_SECRET` | None |
| MCP | `mcp` | OFF | `tools` | None | Team |

**Rationale:** A centralized registry prevents scattered feature checks across the codebase.

**Dependencies:** REQ-FTF-002 depends on REQ-FTF-001.

#### 3.1.2 Feature Evaluation

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-FTF-003 | The system shall evaluate feature enablement by checking, in order: plan tier, dependencies, credentials, and tenant toggle state. | Must | Test | Draft |
| REQ-FTF-004 | If any dependency is disabled, the dependent feature shall be disabled regardless of toggle state. | Must | Test | Draft |
| REQ-FTF-005 | If any required credential is missing in Vault, the feature shall be disabled. | Must | Test | Draft |
| REQ-FTF-006 | If the tenant's plan does not meet the feature's minimum plan, the feature shall be disabled. | Must | Test | Draft |
| REQ-FTF-007 | The system shall provide `can_enable_feature(tenant_id, feature)` returning a diagnostic object listing missing plan, dependencies, or credentials. | Should | Test | Draft |

#### 3.1.3 Feature Gating

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-FTF-008 | The system shall provide a `@require_feature(feature)` decorator that raises `FeatureDisabledError` if the feature is not enabled for the requesting tenant. | Must | Test | Draft |
| REQ-FTF-009 | Disabled feature access shall return a clear, I18N-ready error message keyed by feature code. | Must | Test | Draft |

#### 3.1.4 Administration

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-FTF-010 | The system shall expose `GET /features` returning all features with current enablement state, can-enable diagnostics, tier, and dependencies. | Must | Test | Draft |
| REQ-FTF-011 | The system shall expose `PUT /features/{feature}` to enable or disable an optional feature, validating dependencies and credentials before activation. | Must | Test | Draft |
| REQ-FTF-012 | The system shall expose `POST /features/{feature}/credentials` to store feature credentials in Vault. | Must | Test | Draft |
| REQ-FTF-013 | Tenant toggle overrides shall be stored in cache at key `feature:{tenant_id}:{feature}` with no expiration. | Must | Test | Draft |

**Plan Availability Matrix**

| Feature | Free | Starter | Team | Enterprise |
|---------|------|---------|------|------------|
| `chat` | Yes | Yes | Yes | Yes |
| `auth` | Yes | Yes | Yes | Yes |
| `capsule` | Yes | Yes | Yes | Yes |
| `agentiq` | Yes | Yes | Yes | Yes |
| `permissions` | Yes | Yes | Yes | Yes |
| `billing` | No | Yes | Yes | Yes |
| `budgeting` | No | Yes | Yes | Yes |
| `memory` | Yes | Yes | Yes | Yes |
| `learning` | No | Yes | Yes | Yes |
| `tools` | Yes | Yes | Yes | Yes |
| `voice` | No | Yes | Yes | Yes |
| `images` | No | Yes | Yes | Yes |
| `vision` | No | Yes | Yes | Yes |
| `rlm` | No | No | Yes | Yes |
| `webhooks` | No | Yes | Yes | Yes |
| `mcp` | No | No | Yes | Yes |

---

### 3.2 Non-Functional Requirements

#### 3.2.1 Performance

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-FTF-PERF-001 | Feature enablement check latency | <= 5 ms | Load test |

#### 3.2.2 Security

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-FTF-SEC-001 | Feature credentials shall be stored in Vault, never in code or settings. | 100% | Inspection |
| NFR-FTF-SEC-002 | Toggle API shall enforce tenant isolation; one tenant cannot modify another's toggles. | 100% | Test |

#### 3.2.3 Reliability

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-FTF-REL-001 | Feature check shall fallback to the default state if cache is unreachable. | Yes | Fault injection |

#### 3.2.4 Scalability

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-FTF-SCL-001 | Registry shall support at least 50 features. | 50+ | Inspection |

#### 3.2.5 Maintainability

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-FTF-MNT-001 | Adding a new feature shall require only a registry entry with no changes to evaluation logic. | Yes | Test |

---

### 3.3 External Interface Requirements

#### 3.3.1 User Interfaces

The Agent Settings UI shall display core features as read-only and optional features as toggleable switches. Disabled optional features shall show diagnostic messages indicating missing dependencies, credentials, or plan requirements.

#### 3.3.2 Software Interfaces

| Interface | Protocol | Format | Authentication |
|-----------|----------|--------|----------------|
| Django Cache | Redis protocol | Key/value | Redis AUTH |
| Vault | HTTPS | JSON | Vault token |
| Lago (plan data) | HTTPS | JSON | `LAGO_API_KEY` |

**Cache Keys**

| Key | Purpose |
|-----|---------|
| `feature:{tenant_id}:{feature}` | Tenant toggle override |
| `credentials:{tenant_id}:{feature}` | Credential presence flag |
| `plan:{tenant_id}` | Cached plan code |

#### 3.3.3 Hardware Interfaces

None.

---

### 3.4 Design Constraints

| ID | Constraint | Source |
|----|------------|--------|
| DC-FTF-001 | Feature definitions must be stored in `admin/core/features/registry.py`. | Architecture decision |
| DC-FTF-002 | Core features must have `tier=core` and `lockable=False`. | Design standard |

---

## 4. Traceability

### 4.1 Requirements Traceability Matrix

| REQ ID | Description | Source | Design | Implementation | Test |
|--------|-------------|--------|--------|----------------|------|
| REQ-FTF-001 | Feature registry | Product backlog | `registry.py` | `admin/core/features/registry.py` | `tests/unit/test_feature_registry.py` |
| REQ-FTF-002 | Core features always ON | Product backlog | `registry.py` | `admin/core/features/registry.py` | `tests/unit/test_feature_registry.py` |
| REQ-FTF-003 | Enablement evaluation order | Product backlog | `check.py` | `admin/core/features/check.py` | `tests/unit/test_feature_check.py` |
| REQ-FTF-004 | Dependency enforcement | Product backlog | `check.py` | `admin/core/features/check.py` | `tests/unit/test_feature_check.py` |
| REQ-FTF-005 | Credential gating | Product backlog | `check.py` | `admin/core/features/check.py` | `tests/unit/test_feature_check.py` |
| REQ-FTF-006 | Plan locking | Product backlog | `check.py` | `admin/core/features/check.py` | `tests/unit/test_feature_check.py` |
| REQ-FTF-007 | Can-enable diagnostics | Product backlog | `check.py` | `admin/core/features/check.py` | `tests/unit/test_feature_check.py` |
| REQ-FTF-008 | `@require_feature` decorator | Product backlog | `gate.py` | `admin/core/features/gate.py` | `tests/unit/test_feature_gate.py` |
| REQ-FTF-009 | I18N error messages | Product backlog | Messages module | `admin/common/messages.py` | `tests/unit/test_feature_messages.py` |
| REQ-FTF-010 | GET /features endpoint | Product backlog | `features.py` | `admin/api/features.py` | `tests/api/test_features_api.py` |
| REQ-FTF-011 | PUT /features/{feature} endpoint | Product backlog | `features.py` | `admin/api/features.py` | `tests/api/test_features_api.py` |
| REQ-FTF-012 | POST credentials endpoint | Product backlog | `features.py` | `admin/api/features.py` | `tests/api/test_features_api.py` |
| REQ-FTF-013 | Tenant toggle cache key | Product backlog | Cache design | Django cache | `tests/unit/test_feature_cache.py` |

### 4.2 Requirement to Test Case Mapping

| REQ ID | Test Case ID | Test Method | Expected Result |
|--------|--------------|-------------|-----------------|
| REQ-FTF-001 | TC-FTF-001 | Inspection | Registry contains all defined features with correct fields. |
| REQ-FTF-002 | TC-FTF-002 | Unit test | Attempt to disable core feature raises ForbiddenError. |
| REQ-FTF-003 | TC-FTF-003 | Unit test | Feature enabled only when all checks pass. |
| REQ-FTF-004 | TC-FTF-004 | Unit test | Disabling dependency auto-disables dependent feature. |
| REQ-FTF-005 | TC-FTF-005 | Unit test | Missing credential results in feature disabled. |
| REQ-FTF-006 | TC-FTF-006 | Unit test | Free-plan tenant cannot enable Team-locked feature. |
| REQ-FTF-008 | TC-FTF-008 | Unit test | Decorator raises FeatureDisabledError for disabled feature. |
| REQ-FTF-010 | TC-FTF-010 | API test | GET returns correct enablement map for tenant. |
| REQ-FTF-011 | TC-FTF-011 | API test | PUT enables feature and persists toggle in cache. |
| REQ-FTF-012 | TC-FTF-012 | API test | Credentials stored in Vault and feature becomes eligible. |

---

## 5. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-16 | Platform Engineering | Initial ISO/IEC/IEEE 29148 conformant version. Refactored from ad-hoc SRS. |

---

*Document conforms to ISO/IEC/IEEE 29148:2018 — Systems and Software Engineering — Life Cycle Processes — Requirements Engineering.*
