# SRS-BUDGET-SYSTEM — Universal Resource Budgeting

| Field | Value |
|-------|-------|
| **System** | SomaAgent01 + SomaBrain + SomaFractalMemory |
| **Document ID** | SRS-BUDGET-SYSTEM-2026-01-16 |
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

This document specifies the Universal Budget System, a centralized, Django-native pattern for enforcing resource limits across the entire SOMA Stack. It provides a single decorator-based gate, a generic metric registry, and async usage recording to Lago.

### 1.2 Scope

**In scope:**
- Metric registry and definitions (`admin/core/budget/registry.py`)
- Budget gate decorator (`admin/core/budget/gate.py`)
- Plan limit resolution (`admin/core/budget/limits.py`)
- Usage tracking via Django cache (Redis)
- Async Lago event emission
- Per-metric enablement toggles

**Out of scope:**
- Lago billing engine implementation (see [SRS-LAGO-BILLING.md](./SRS-LAGO-BILLING.md))
- Chat/agent execution logic
- Tenant authentication and authorization

### 1.3 Definitions

| Term | Definition |
|------|------------|
| **BudgetedMetric** | Immutable definition of a budgeted resource (code, unit, tier, limit, cost, Lago mapping). |
| **Budget Gate** | The `@budget_gate` decorator that enforces limits before and after function execution. |
| **Tenant** | An isolated customer workspace identified by `tenant_id`. |
| **Plan** | A subscription tier (Free, Starter, Team, Enterprise) that determines limits. |
| **Metric** | A measurable resource such as tokens, tool calls, images, voice minutes. |
| **Pre-enforcement** | Checking usage against limits BEFORE executing the protected action. |
| **Toggle** | A per-metric enable/disable switch controlled at platform or tenant level. |
| **Lockable** | A metric that cannot be toggled off (always enforced). |

### 1.4 References

| ID | Document | Version | Location |
|----|----------|---------|----------|
| REF-001 | SRS-LAGO-BILLING | 1.0 | `docs/srs/SRS-LAGO-BILLING.md` |
| REF-002 | Django Cache Framework | 4.2 | https://docs.djangoproject.com/en/4.2/topics/cache/ |
| REF-003 | Lago API Documentation | Latest | https://getlago.com/docs/api-reference |

---

## 2. Product Description

### 2.1 Product Perspective

The Universal Budget System sits at Phase 2 of the SOMA chat flow, immediately after authentication and before capsule loading. It integrates with Django cache (Redis) for fast counter storage and with the Lago external billing service for async usage recording. The system is deployed as part of the `admin/core/budget/` package within SomaAgent01.

### 2.2 Product Functions

| ID | Function | Description |
|----|----------|-------------|
| FUNC-001 | Metric Registration | Define budgeted metrics in a centralized registry with units, tiers, and Lago mappings. |
| FUNC-002 | Budget Enforcement | Intercept protected operations via `@budget_gate` to enforce pre- and post-action limits. |
| FUNC-003 | Plan Limit Resolution | Resolve per-tenant limits based on subscribed plan tier. |
| FUNC-004 | Usage Recording | Increment monthly usage counters in Django cache after successful execution. |
| FUNC-005 | Async Billing Events | Emit non-blocking usage events to Lago for invoice generation. |
| FUNC-006 | Metric Toggle Management | Enable or disable individual metrics at platform or tenant level. |

### 2.3 User Characteristics

| User Type | Role | Technical Level | Access |
|-----------|------|-----------------|--------|
| Tenant Admin | Configure toggles and view budgets | Intermediate | Agent Settings UI |
| Platform Engineer | Add new metrics, adjust plan limits | Advanced | Registry / limits modules |
| End User | Consumes budgeted resources | Basic | Subject to 402 enforcement |

### 2.4 Constraints

| ID | Constraint | Description |
|----|------------|-------------|
| CON-001 | Django Cache | All usage counters and toggle states must use `django.core.cache` (Redis backend). |
| CON-002 | Fail-Closed | Budget exceeded or gate failure must result in a 402 error; never allow unrestricted usage. |
| CON-003 | Lago Code Mapping | Each metric `code` must map to an existing Lago `billable_metric_code`. |
| CON-004 | Async Safety | The decorator must be compatible with async view functions. |

### 2.5 Assumptions and Dependencies

| ID | Assumption / Dependency | Impact if Invalid |
|----|------------------------|-------------------|
| AD-001 | Redis is available as the Django cache backend. | Usage counters and toggles cannot be evaluated; gate fails closed (402). |
| AD-002 | Lago external service is reachable for async event recording. | Billing events are lost; retry queue must handle recovery. |
| AD-003 | `tenant_id` is present on the request object passed to gated functions. | Gate cannot resolve tenant-specific limits; falls back to unknown defaults. |

---

## 3. Specific Requirements

### 3.1 Functional Requirements

#### 3.1.1 Budget Enforcement

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-BGT-001 | The system shall provide a single `@budget_gate(metric)` decorator applicable to any async function to enforce budget limits. | Must | Test | Draft |
| REQ-BGT-002 | For metrics with `enforce_pre=True`, the gate shall check the tenant's current monthly usage against the plan limit before executing the wrapped function. | Must | Test | Draft |
| REQ-BGT-003 | If pre-enforcement detects usage >= limit, the system shall raise `BudgetExhaustedError` with HTTP status 402 and halt execution. | Must | Test | Draft |
| REQ-BGT-004 | After successful execution, the gate shall record actual usage by incrementing the tenant's monthly counter in Django cache. | Must | Test | Draft |
| REQ-BGT-005 | The gate shall emit usage events to Lago asynchronously and non-blocking after post-enforcement recording. | Must | Test | Draft |

**Rationale:** Centralized enforcement ensures consistent limit checking across all SOMA components without duplicating logic.

**Dependencies:** REQ-BGT-001 depends on REQ-BGT-006 (registry); REQ-BGT-005 depends on REF-001 (Lago integration).

#### 3.1.2 Metric Registry

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-BGT-006 | The system shall maintain a `METRIC_REGISTRY` (`admin/core/budget/registry.py`) defining each metric by code, name, unit, tier, default limit, cost per unit, pre-enforcement flag, Lago code, default enabled state, and lockable flag. | Must | Inspection | Draft |
| REQ-BGT-007 | Adding a new metric shall require only registry entry, plan limit entry, and Lago billable metric creation; no changes to `gate.py` shall be required. | Should | Test | Draft |

**Complete Metric Catalog**

| Code | Name | Unit | Tier | Default | $/Unit | Pre | Lago Code | Default Enabled | Lockable |
|------|------|------|------|---------|--------|-----|-----------|-----------------|----------|
| `tokens` | LLM Tokens | count | critical | 100,000 | 0.0001 | Yes | `tokens` | True | True |
| `tool_calls` | Tool Executions | count | critical | 1,000 | 0.01 | Yes | `tool_calls` | True | True |
| `images` | Image Generations | count | critical | 100 | 0.04 | Yes | `image_generations` | True | True |
| `voice_minutes` | Voice Minutes | minutes | critical | 60 | 0.006 | Yes | `voice_minutes` | True | True |
| `api_calls` | API Requests | count | important | 10,000 | 0.00 | Yes | `api_calls` | True | False |
| `memory_tokens` | Memory Storage | tokens | important | 500,000 | 0.0001 | Yes | `memory_tokens` | True | False |
| `vector_ops` | Vector Operations | count | important | 50,000 | 0.001 | No | `vector_ops` | True | False |
| `learning` | Learning Cycles | count | important | 100 | 0.10 | Yes | `learning_credits` | True | False |
| `storage_gb` | File Storage | gb | monitor | 10 | 0.10 | No | `storage_gb` | False | False |
| `sessions` | Concurrent Sessions | count | monitor | 5 | 0.00 | Yes | `sessions` | False | False |

**Rationale:** A generic registry avoids hard-coding metrics in the gate logic.

**Dependencies:** REQ-BGT-007 depends on REQ-BGT-006.

#### 3.1.3 Plan Limits

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-BGT-008 | The system shall resolve per-tenant limits based on the tenant's plan tier using `PLAN_LIMITS` in `admin/core/budget/limits.py`. | Must | Test | Draft |

**Plan Limits Matrix**

| Metric | Free | Starter ($29) | Team ($99) | Enterprise |
|--------|------|---------------|------------|------------|
| `tokens` | 10,000 | 100,000 | 500,000 | Unlimited |
| `tool_calls` | 100 | 1,000 | 10,000 | Unlimited |
| `images` | 10 | 100 | 500 | Unlimited |
| `voice_minutes` | 10 | 60 | 300 | Unlimited |
| `api_calls` | 1,000 | 10,000 | 100,000 | Unlimited |
| `memory_tokens` | 50,000 | 500,000 | 2,000,000 | Unlimited |
| `vector_ops` | 5,000 | 50,000 | 500,000 | Unlimited |
| `learning` | 10 | 100 | 1,000 | Unlimited |
| `storage_gb` | 1 | 10 | 100 | Unlimited |
| `sessions` | 1 | 5 | 20 | Unlimited |

#### 3.1.4 Usage Recording & Cache

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-BGT-009 | Monthly usage counters shall be stored with cache key `budget:{tenant_id}:{metric}:monthly` and a TTL of 35 days. | Must | Test | Draft |
| REQ-BGT-010 | Daily rate-limit counters shall be stored with cache key `budget:{tenant_id}:{metric}:daily` and a TTL of 25 hours. | Should | Test | Draft |
| REQ-BGT-011 | The system shall provide I18N-ready error messages for budget exceeded scenarios, keyed by metric code (e.g., `BUDGET_TOKENS_EXCEEDED`). | Must | Inspection | Draft |

**I18N Message Codes**

| Code | Message |
|------|---------|
| `BUDGET_TOKENS_EXCEEDED` | Monthly token limit reached. |
| `BUDGET_IMAGES_EXCEEDED` | Image generation limit reached. |
| `BUDGET_VOICE_MINUTES_EXCEEDED` | Voice minutes exhausted. |
| `BUDGET_TOOL_CALLS_EXCEEDED` | Tool execution limit reached. |
| `BUDGET_LOW_WARNING` | You have used {percentage}% of your {metric}. |

#### 3.1.5 Toggle Management

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-BGT-012 | The system shall support per-metric toggles, allowing metrics to be enabled or disabled at platform and tenant levels. | Must | Test | Draft |
| REQ-BGT-013 | Lockable metrics shall ignore tenant toggle overrides and remain enabled. | Must | Test | Draft |
| REQ-BGT-014 | Non-lockable metrics shall support tenant-specific overrides stored in cache at key `toggle:{tenant_id}:{metric}`. | Must | Test | Draft |
| REQ-BGT-015 | The system shall expose `GET /budget/toggles` to return the current enablement state for all metrics. | Must | Test | Draft |
| REQ-BGT-016 | The system shall expose `PUT /budget/toggles/{metric}` to enable or disable a non-lockable metric for a tenant. | Must | Test | Draft |

**Platform Default Toggles**

| Metric | Default |
|--------|---------|
| `tokens`, `tool_calls`, `images`, `voice_minutes` | True (lockable) |
| `api_calls`, `memory_tokens`, `vector_ops`, `learning` | True |
| `storage_gb`, `sessions` | False |

**Rationale:** Toggle support allows enterprise tenants to opt into monitoring metrics without enforcing them by default.

---

### 3.2 Non-Functional Requirements

#### 3.2.1 Performance

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-BGT-PERF-001 | Pre-enforcement budget check latency | <= 10 ms | Load test |
| NFR-BGT-PERF-002 | Post-enforcement Lago event overhead | <= 5 ms | Load test |

#### 3.2.2 Security

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-BGT-SEC-001 | Budget gate shall be fail-closed; cache or registry failures result in 402 denial. | 100% | Fault injection |
| NFR-BGT-SEC-002 | Tenant counters and toggles shall be isolated by `tenant_id` in cache key namespaces. | 100% | Inspection |

#### 3.2.3 Reliability

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-BGT-REL-001 | Lago event recording failures shall not block the primary operation. | 100% | Fault injection |
| NFR-BGT-REL-002 | Monthly counter cache TTL shall be >= 35 days. | 35 days | Inspection |

#### 3.2.4 Scalability

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-BGT-SCL-001 | Support at least 10 concurrent metrics per tenant. | 10+ | Load test |
| NFR-BGT-SCL-002 | Decorator shall be stateless and safe for multi-process workers. | Yes | Inspection |

#### 3.2.5 Maintainability

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-BGT-MNT-001 | Metric definitions and plan limits shall reside in separate modules (`registry.py`, `limits.py`). | Yes | Inspection |

---

### 3.3 External Interface Requirements

#### 3.3.1 User Interfaces

The Agent Settings UI shall display core metrics as read-only (lockable) and allow toggling of non-lockable metrics. Budget usage bars shall display remaining limits per metric.

#### 3.3.2 Software Interfaces

| Interface | Protocol | Format | Authentication |
|-----------|----------|--------|----------------|
| Django Cache | Redis protocol | Key/value | Redis AUTH |
| Lago Events API | HTTPS | JSON | `LAGO_API_KEY` header |

**Cache Key Patterns**

| Key | Purpose |
|-----|---------|
| `budget:{tenant_id}:{metric}:monthly` | Monthly usage counter |
| `budget:{tenant_id}:{metric}:daily` | Daily rate-limit counter |
| `plan:{tenant_id}` | Cached plan code (1h TTL) |
| `wallet:{tenant_id}` | Prepaid balance (5m TTL) |
| `toggle:{tenant_id}:{metric}` | Tenant toggle override |

#### 3.3.3 Hardware Interfaces

None.

---

### 3.4 Design Constraints

| ID | Constraint | Source |
|----|------------|--------|
| DC-BGT-001 | Implementation must use `django.core.cache` for all usage and toggle storage. | Architecture decision |
| DC-BGT-002 | Metric `lago_code` values must match existing Lago `billable_metric_code` values. | REF-003 |

---

## 4. Traceability

### 4.1 Requirements Traceability Matrix

| REQ ID | Description | Source | Design | Implementation | Test |
|--------|-------------|--------|--------|----------------|------|
| REQ-BGT-001 | Single `@budget_gate` decorator | Product backlog | `gate.py` | `admin/core/budget/gate.py` | `tests/unit/test_budget_gate.py` |
| REQ-BGT-002 | Pre-enforcement check | Product backlog | `gate.py` | `admin/core/budget/gate.py` | `tests/unit/test_budget_gate.py` |
| REQ-BGT-003 | 402 on limit exceeded | Product backlog | `exceptions.py` | `admin/core/budget/exceptions.py` | `tests/unit/test_budget_gate.py` |
| REQ-BGT-004 | Post-usage recording | Product backlog | `gate.py` | `admin/core/budget/gate.py` | `tests/unit/test_budget_gate.py` |
| REQ-BGT-005 | Async Lago events | REF-001 | `gate.py` | `admin/core/budget/gate.py` | `tests/integration/test_budget_lago.py` |
| REQ-BGT-006 | Metric registry | Product backlog | `registry.py` | `admin/core/budget/registry.py` | `tests/unit/test_budget_registry.py` |
| REQ-BGT-007 | Add metrics without gate changes | Product backlog | `registry.py` | `admin/core/budget/registry.py` | `tests/unit/test_budget_registry.py` |
| REQ-BGT-008 | Plan limit resolution | Product backlog | `limits.py` | `admin/core/budget/limits.py` | `tests/unit/test_budget_limits.py` |
| REQ-BGT-009 | Monthly counter TTL | Product backlog | Cache config | Django settings | `tests/unit/test_budget_cache.py` |
| REQ-BGT-010 | Daily counter TTL | Product backlog | Cache config | Django settings | `tests/unit/test_budget_cache.py` |
| REQ-BGT-011 | I18N error messages | Product backlog | Messages module | `admin/common/messages.py` | `tests/unit/test_budget_messages.py` |
| REQ-BGT-012 | Metric toggles | Product backlog | Toggle module | `admin/core/budget/toggles.py` | `tests/unit/test_budget_toggles.py` |
| REQ-BGT-013 | Lockable metrics enforced | Product backlog | Toggle module | `admin/core/budget/toggles.py` | `tests/unit/test_budget_toggles.py` |
| REQ-BGT-014 | Tenant toggle overrides | Product backlog | Toggle module | `admin/core/budget/toggles.py` | `tests/unit/test_budget_toggles.py` |
| REQ-BGT-015 | GET toggles endpoint | Product backlog | API design | `admin/api/settings.py` | `tests/api/test_budget_api.py` |
| REQ-BGT-016 | PUT toggle endpoint | Product backlog | API design | `admin/api/settings.py` | `tests/api/test_budget_api.py` |

### 4.2 Requirement to Test Case Mapping

| REQ ID | Test Case ID | Test Method | Expected Result |
|--------|--------------|-------------|-----------------|
| REQ-BGT-001 | TC-BGT-001 | Unit test | Decorator wraps async function without error. |
| REQ-BGT-002 | TC-BGT-002 | Unit test | Request blocked when usage >= limit for pre-enforced metric. |
| REQ-BGT-003 | TC-BGT-003 | Unit test | `BudgetExhaustedError` raised with status 402. |
| REQ-BGT-004 | TC-BGT-004 | Unit test | Cache counter incremented by exact usage after execution. |
| REQ-BGT-005 | TC-BGT-005 | Integration test | Lago event task created without blocking response. |
| REQ-BGT-006 | TC-BGT-006 | Inspection | All 10 metrics defined in registry with correct fields. |
| REQ-BGT-007 | TC-BGT-007 | Unit test | New metric added to registry and limits works without gate changes. |
| REQ-BGT-008 | TC-BGT-008 | Unit test | Limit resolves to plan-specific value. |
| REQ-BGT-009 | TC-BGT-009 | Inspection | Redis TTL for monthly keys >= 35 days. |
| REQ-BGT-010 | TC-BGT-010 | Inspection | Redis TTL for daily keys >= 25 hours. |
| REQ-BGT-011 | TC-BGT-011 | Unit test | Message retrieval returns correct localized string. |
| REQ-BGT-012 | TC-BGT-012 | Unit test | Toggling metric off disables enforcement. |
| REQ-BGT-013 | TC-BGT-013 | Unit test | Lockable metric cannot be toggled off. |
| REQ-BGT-014 | TC-BGT-014 | Unit test | Tenant override stored and read from cache. |
| REQ-BGT-015 | TC-BGT-015 | API test | GET returns JSON map of all metric states. |
| REQ-BGT-016 | TC-BGT-016 | API test | PUT updates tenant toggle and returns new state. |

---

## 5. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-16 | Platform Engineering | Initial ISO/IEC/IEEE 29148 conformant version. Refactored from ad-hoc SRS. |

---

*Document conforms to ISO/IEC/IEEE 29148:2018 — Systems and Software Engineering — Life Cycle Processes — Requirements Engineering.*
