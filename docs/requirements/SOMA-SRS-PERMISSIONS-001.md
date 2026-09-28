# SRS-PERMISSION-MATRIX — Permission Matrix and Role Administration

| Field | Value |
|-------|-------|
| **System** | SomaAgent01 |
| **Document ID** | SRS-PERMISSION-MATRIX-2025-12 |
| **Version** | 1.1 |
| **Date** | 2025-12 |
| **Status** | Approved |
| **Author** | Soma Engineering |
| **Owner** | Security Team |

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

This document specifies the role-based access control (RBAC), permission matrix, and role administration requirements for the SomaAgent01 platform. It defines the permission hierarchy, tier-gated features, screen and API access rules, and the SpiceDB authorization schema.

### 1.2 Scope

**In scope:**
- Permission cascade model across Platform, Tenant, Agent, and Resource levels
- Complete permission matrix for all user journeys, screens, and API endpoints
- Subscription tier gating for features and modes
- Role administration interfaces and workflows
- SpiceDB schema definitions for authorization
- Frontend and backend permission enforcement mechanisms

**Out of scope:**
- User interface visual design and styling
- Billing logic for tier pricing
- Keycloak identity provider configuration

### 1.3 Definitions

| Term | Definition |
|------|------------|
| AAAS Admin | Platform super administrator with full system access |
| Agent Owner | User who owns and configures a specific agent |
| Capsule | Agent identity unit containing configuration and capabilities |
| DEV Mode | Developer debugging mode for agent inspection |
| GranularPermission | Fine-grained permission combining a resource and an action |
| PermissionResource | Entity type that can be acted upon (e.g., tenant, agent, conversation) |
| PermissionAction | Operation that can be performed on a resource (e.g., read, delete) |
| Role | Named collection of permissions assignable to users |
| SpiceDB | Open-source fine-grained authorization database |
| STD Mode | Standard chat mode for end users |
| TRN Mode | Trainer mode for cognitive and memory tuning |
| Tier Gating | Feature availability controlled by subscription level |
| Tenant Admin | Administrator within a single tenant |
| Tenant SysAdmin | Super administrator within a single tenant |

### 1.4 References

| ID | Document | Version | Location |
|----|----------|---------|----------|
| REF-001 | SRS-SECURITY-MULTITENANCY | 1.1 | `docs/srs/SRS-SECURITY-MULTITENANCY.md` |
| REF-002 | SRS-DATA-MODELS | 5.0 | `docs/srs/SRS-DATA-MODELS.md` |
| REF-003 | SRS-ARCHITECTURAL-PATTERNS | 1.0 | `docs/srs/SRS-ARCHITECTURAL-PATTERNS.md` |
| REF-004 | SpiceDB Schema Language (Zed) | 1.35 | https://authzed.com/docs |

---

## 2. Product Description

### 2.1 Product Perspective

The permission matrix subsystem sits between the authentication layer (Keycloak) and all platform features. It determines whether an authenticated user may access a screen, execute an API call, or perform an action on a resource. The subsystem is implemented via SpiceDB for fine-grained checks, with Django backend decorators and frontend route guards enforcing the matrix.

### 2.2 Product Functions

| ID | Function | Description |
|----|----------|-------------|
| FUNC-001 | Permission Cascade | Enforce top-down permission inheritance from Platform to Tenant to Agent to Resource |
| FUNC-002 | Tier Gating | Restrict features based on subscription tier (Free, Starter, Team, Enterprise) |
| FUNC-003 | Quota Enforcement | Block operations when tenant or agent quotas are exceeded |
| FUNC-004 | Role Scoping | Restrict role management to the scope in which the role is defined |
| FUNC-005 | Screen Access Control | Gate frontend routes based on user permissions |
| FUNC-006 | API Access Control | Gate REST endpoints based on user permissions |
| FUNC-007 | Role Administration | Create, edit, and delete custom roles with granular permissions |
| FUNC-008 | Permission Inheritance | Derive effective permissions from role assignments and hierarchy |

### 2.3 User Characteristics

| User Type | Role | Technical Level | Access |
|-----------|------|-----------------|--------|
| AAAS Admin | Platform administrator | High | All tenants, roles, permissions, billing |
| Tenant SysAdmin | Tenant super administrator | Medium | Single tenant, full control |
| Tenant Admin | Tenant administrator | Medium | Single tenant, users and agents, no billing |
| Agent Owner | Agent owner | Medium | Agent configuration, users, chat |
| Developer | Agent developer | High | DEV mode, logs, API inspection |
| Trainer | Agent trainer | Medium | TRN mode, cognitive tuning |
| Standard User | End user | Low | Chat, memory read, file upload |
| Viewer | Read-only user | Low | Chat view, memory view |

### 2.4 Constraints

| ID | Constraint | Description |
|----|------------|-------------|
| CON-001 | Role Immutability | System roles (AAAS SysAdmin, Tenant SysAdmin, etc.) shall not be modifiable or deletable |
| CON-002 | Last SysAdmin Protection | The system shall prevent removal of the last AAAS SysAdmin |
| CON-003 | Tier Ceiling | A tenant cannot exceed the maximum limits defined by its subscription tier |
| CON-004 | Cross-Tenant Isolation | A user with a role in Tenant A shall have no permissions in Tenant B |

### 2.5 Assumptions and Dependencies

| ID | Assumption / Dependency | Impact if Invalid |
|----|------------------------|-------------------|
| AD-001 | SpiceDB schema is deployed and synced with application code | Authorization checks fail or return incorrect results |
| AD-002 | Subscription tier data is accurate in PostgreSQL | Tier gating allows or blocks features incorrectly |
| AD-003 | Role changes are propagated to SpiceDB within seconds | Recently assigned permissions may not take effect immediately |
| AD-004 | Frontend route guards and backend decorators enforce the same rules | Users may bypass frontend restrictions via direct API calls |

---

## 3. Specific Requirements

### 3.1 Functional Requirements

#### 3.1.1 Permission Architecture

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-PM-001 | The system shall enforce a permission cascade from Platform to Tenant to Agent to Resource. | Must | Test | Approved |
| REQ-PM-002 | The system shall allow higher-level roles to always access lower-level resources within their scope. | Must | Test | Approved |
| REQ-PM-003 | The system shall gate features by subscription tier: Free, Starter, Team, Enterprise. | Must | Test | Approved |
| REQ-PM-004 | The system shall enforce quota limits (agents, users, tokens, storage) based on tier. | Must | Test | Approved |
| REQ-PM-005 | The system shall scope roles such that a role is only valid within the tenant or agent for which it was created. | Must | Test | Approved |
| REQ-PM-006 | The system shall allow only AAAS Admin users to impersonate other users. | Must | Test | Approved |

**Rationale:** Hierarchical permission model ensures least privilege while enabling administrative override where necessary.

#### 3.1.2 Permission Categories

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-PM-007 | The system shall support Level 0 Platform permissions: `platform:manage`, `platform:manage_tenants`, `platform:manage_tiers`, `platform:manage_roles`, `platform:view_billing`, `platform:impersonate`, `platform:configure`. | Must | Test | Approved |
| REQ-PM-008 | The system shall support Level 1 Tenant permissions: `tenant:manage`, `tenant:administrate`, `tenant:create_agent`, `tenant:delete_agent`, `tenant:view_billing`, `tenant:manage_api_keys`, `tenant:assign_roles`. | Must | Test | Approved |
| REQ-PM-009 | The system shall support Level 2 Agent permissions: `agent:configure`, `agent:activate_adm`, `agent:activate_dev`, `agent:activate_trn`, `agent:activate_std`, `agent:activate_ro`, `agent:manage_users`. | Must | Test | Approved |
| REQ-PM-010 | The system shall support Level 3 Resource permissions: `chat:send`, `chat:view`, `chat:delete`, `memory:read`, `memory:write`, `memory:delete`, `memory:set_retention`, `tools:execute`, `tools:approve_external`, `cognitive:view`, `cognitive:edit`, `voice:use`, `voice:configure`, `rlm:execute`, `capsule:export`. | Must | Test | Approved |
| REQ-PM-011 | The system shall support Level 4 Security/Emergency permissions: `platform:break_glass`, `platform:require_2fa`, `apikey:restrict_ip`, `billing:update_payment`, `billing:cancel_sub`. | Must | Test | Approved |

#### 3.1.3 Tier-Gated Features

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-PM-012 | The system shall make STD and RO modes available on all tiers. | Must | Test | Approved |
| REQ-PM-013 | The system shall make DEV and TRN modes available only on Team and Enterprise tiers. | Must | Test | Approved |
| REQ-PM-014 | The system shall make ADM mode available on Starter, Team, and Enterprise tiers. | Must | Test | Approved |
| REQ-PM-015 | The system shall make Voice, API Access available on Starter, Team, and Enterprise tiers. | Must | Test | Approved |
| REQ-PM-016 | The system shall make Custom LLM, SSO, and SLA available only on Enterprise tier. | Must | Test | Approved |

#### 3.1.4 Permission Check Flow

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-PM-017 | The system shall reject unauthenticated requests with HTTP 401. | Must | Test | Approved |
| REQ-PM-018 | The system shall allow AAAS Admin requests to bypass tenant and tier checks (god mode). | Must | Test | Approved |
| REQ-PM-019 | The system shall reject requests for suspended tenants with HTTP 403. | Must | Test | Approved |
| REQ-PM-020 | The system shall reject requests for features not allowed by the tenant's tier with HTTP 403. | Must | Test | Approved |
| REQ-PM-021 | The system shall check SpiceDB for explicit permission grants after authentication and tier validation. | Must | Test | Approved |
| REQ-PM-022 | The system shall reject requests that exceed tenant or agent quotas with HTTP 429. | Must | Test | Approved |

#### 3.1.5 User Journey Permissions

The system shall enforce the following access levels for user journeys:

| Journey | AAAS Admin | Tenant SysAdmin | Tenant Admin | Agent Owner | Developer | Trainer | User | Viewer |
|---------|------------|-----------------|--------------|-------------|-----------|---------|------|--------|
| UC-01 Chat with Agent | Full | Full | Full | Full | Full | Full | Full | View |
| UC-02 Create Conversation | Full | Full | Full | Full | Full | Full | Full | None |
| UC-03 Upload File | Full | Full | Full | Full | Full | Full | Conditional | None |
| UC-04 Voice Chat | Full | Full | Full | Full | Full | Full | Conditional | None |
| UC-05 View Memories | Full | Full | Full | Full | Full | Full | View | View |
| UC-06 Configure Agent | Full | Full | Full | Full | None | None | None | None |
| UC-07 Manage Users | Full | Full | Conditional | None | None | None | None | None |
| UC-08 View Billing | Full | Full | None | None | None | None | None | None |
| UC-09 Create Tenant | Full | None | None | None | None | None | None | None |
| UC-10 Suspend Tenant | Full | None | None | None | None | None | None | None |
| UC-11 Manage Subscriptions | Full | None | None | None | None | None | None | None |
| UC-12 Platform Metrics | Full | None | None | None | None | None | None | None |
| UC-13 Tool Execution | Full | Full | Full | Full | Full | Full | Conditional | None |
| UC-14 Store Memory | Full | Full | Full | Full | Full | Full | Conditional | None |
| UC-15 API Integration | Full | Full | Conditional | Conditional | Conditional | None | None | None |

**Legend:** Full = unrestricted access; View = read-only; Conditional = quota or ownership dependent; None = no access.

#### 3.1.6 Screen Access Permissions

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-PM-023 | The system shall restrict Platform Dashboard (`/aaas`) and Tenant List (`/aaas/tenants`) to AAAS Admin. | Must | Test | Approved |
| REQ-PM-024 | The system shall restrict Tenant Dashboard (`/admin`) to Tenant SysAdmin and Tenant Admin. | Must | Test | Approved |
| REQ-PM-025 | The system shall restrict Agent Overview (`/agent/:id`) and Agent Config (`/agent/:id/config`) to Agent Owner, Tenant Admin, and Tenant SysAdmin. | Must | Test | Approved |
| REQ-PM-026 | The system shall restrict DEV Mode screens (`/dev/*`) to Developer and Agent Owner with DEV mode enabled. | Must | Test | Approved |
| REQ-PM-027 | The system shall restrict TRN Mode screens (`/trn/*`) to Trainer and Agent Owner with TRN mode enabled. | Must | Test | Approved |
| REQ-PM-028 | The system shall restrict Chat View (`/chat`) to all authenticated users, with Viewer limited to read-only. | Must | Test | Approved |

#### 3.1.7 API Endpoint Permissions

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-PM-029 | The system shall restrict AAAS tenant endpoints (`/api/v2/aaas/tenants`) to AAAS Admin. | Must | Test | Approved |
| REQ-PM-030 | The system shall restrict admin user endpoints (`/api/v2/admin/users`) to Tenant SysAdmin and Tenant Admin. | Must | Test | Approved |
| REQ-PM-031 | The system shall restrict agent configuration endpoints (`/api/v2/agent/{id}/config`) to Agent Owner, Tenant Admin, and Tenant SysAdmin. | Must | Test | Approved |
| REQ-PM-032 | The system shall restrict chat message endpoints (`/api/v2/chat/messages`) to all authenticated users except Viewer. | Must | Test | Approved |
| REQ-PM-033 | The system shall restrict memory deletion (`/api/v2/memory/{id}` DELETE) to Agent Owner, Developer, Trainer, and Tenant Admin. | Must | Test | Approved |
| REQ-PM-034 | The system shall restrict cognitive endpoints (`/api/v2/cognitive/*`) to Developer and Trainer with appropriate mode enabled. | Must | Test | Approved |

#### 3.1.8 Role Administration

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-PM-035 | The system shall provide an API to list all roles at `/api/v2/aaas/roles`. | Must | Test | Approved |
| REQ-PM-036 | The system shall provide an API to create, update, and delete custom roles at `/api/v2/aaas/roles`. | Must | Test | Approved |
| REQ-PM-037 | The system shall prevent deletion of a role that has assigned users. | Must | Test | Approved |
| REQ-PM-038 | The system shall prevent modification of system roles. | Must | Test | Approved |
| REQ-PM-039 | The system shall prevent creation of duplicate role names within the same scope. | Must | Test | Approved |
| REQ-PM-040 | The system shall provide a permission browser API at `/api/v2/aaas/permissions`. | Must | Test | Approved |

#### 3.1.9 Edge Cases

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-PM-041 | The system shall warn and block deletion of a role that has assigned users, requiring reassignment first. | Must | Test | Approved |
| REQ-PM-042 | The system shall reject edits to system roles with an error indicating system roles are immutable. | Must | Test | Approved |
| REQ-PM-043 | The system shall reject duplicate role creation with an error naming the existing role. | Must | Test | Approved |
| REQ-PM-044 | The system shall prevent removal of the last AAAS SysAdmin. | Must | Test | Approved |
| REQ-PM-045 | The system shall warn when reducing tier limits below current tenant usage. | Should | Test | Approved |

#### 3.1.10 SpiceDB Schema Requirements

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-PM-046 | The system shall define a `platform` resource in SpiceDB for top-level platform permissions. | Must | Inspection | Approved |
| REQ-PM-047 | The system shall define a `tenant` resource with relations for `sysadmin`, `admin`, `developer`, `trainer`, `member`, `viewer`, and `subscription`. | Must | Inspection | Approved |
| REQ-PM-048 | The system shall define an `agent` resource with relations for `tenant`, `owner`, `admin`, `developer`, `trainer`, `user`, and `viewer`. | Must | Inspection | Approved |
| REQ-PM-049 | The system shall define a `subscription_tier` resource to support tier-based permission derivation. | Must | Inspection | Approved |
| REQ-PM-050 | The system shall define a `feature` resource with relations to `subscription_tier` and `tenant` for feature flagging. | Must | Inspection | Approved |

#### 3.1.11 Frontend Enforcement

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-PM-051 | The system shall implement frontend route guards that check required permissions before rendering a screen. | Must | Test | Approved |
| REQ-PM-052 | The system shall hide or disable UI actions (buttons, links) when the user lacks the required permission. | Must | Test | Approved |

#### 3.1.12 Backend Enforcement

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-PM-053 | The system shall implement Django Ninja decorators (`require_permission`) that enforce permissions on API endpoints. | Must | Test | Approved |
| REQ-PM-054 | The system shall cache user permissions in Redis to reduce SpiceDB query load. | Should | Test | Approved |
| REQ-PM-055 | The system shall log all permission denials for audit and security monitoring. | Must | Test | Approved |

---

### 3.2 Non-Functional Requirements

#### 3.2.1 Performance

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-PERF-001 | Permission check response time shall be less than or equal to 20 ms at p99. | 20 ms | Test |
| NFR-PERF-002 | Frontend route guard evaluation shall complete synchronously without network round-trips. | 0 ms network | Inspection |

#### 3.2.2 Security

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-SEC-001 | Frontend permission checks shall be duplicated on the backend; frontend enforcement is for UX only. | 100% backend coverage | Test |
| NFR-SEC-002 | Permission changes shall propagate to SpiceDB within 5 seconds. | 5 s | Test |

#### 3.2.3 Reliability

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-REL-001 | Permission caching shall have a TTL of 60 seconds to balance performance and consistency. | 60 s | Inspection |

#### 3.2.4 Scalability

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-SCL-001 | The permission system shall support at least 10,000 custom roles across the platform. | 10,000 roles | Analysis |

#### 3.2.5 Maintainability

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-MNT-001 | Permission definitions shall be centralized in `admin/permissions/definitions.py`. | Single source | Inspection |

---

### 3.3 External Interface Requirements

#### 3.3.1 User Interfaces

Role administration is exposed through the AAAS admin web UI at routes `/aaas/roles/*` and `/aaas/permissions/*`.

#### 3.3.2 Software Interfaces

| Interface | Protocol | Format | Authentication |
|-----------|----------|--------|----------------|
| SpiceDB | gRPC | Protobuf | Bearer token (preshared key) |
| Role Admin API | HTTPS / REST | JSON | JWT (Keycloak) |
| Permission Browser API | HTTPS / REST | JSON | JWT (Keycloak) |

#### 3.3.3 Hardware Interfaces

No hardware interface requirements are specified in this document.

---

### 3.4 Design Constraints

| ID | Constraint | Source |
|----|------------|--------|
| DC-001 | All API implementations must use Django Ninja. | SRS-ARCHITECTURAL-PATTERNS |
| DC-002 | SpiceDB schema changes must be versioned and backward-compatible. | Platform standard |
| DC-003 | Permission decorators must be reusable across all API modules. | Platform standard |

---

## 4. Traceability

### 4.1 Requirements Traceability Matrix

| REQ ID | Description | Source | Design | Implementation | Test |
|--------|-------------|--------|--------|----------------|------|
| REQ-PM-001 | Permission cascade | SRS-PERMISSION-MATRIX | `admin/permissions/definitions.py` | `admin/permissions/api.py`, `admin/core/permission_matrix.py` | `tests/django/test_auth_integration.py` |
| REQ-PM-003 | Tier gating | SRS-PERMISSION-MATRIX | `admin/aaas/models/tiers.py` | `admin/aaas/models/tiers.py`, `admin/aaas/models/features.py` | `tests/django/test_auth_integration.py` |
| REQ-PM-007 | Platform permissions | SRS-PERMISSION-MATRIX | `admin/permissions/definitions.py` | `admin/permissions/definitions.py` | `tests/django/test_auth_integration.py` |
| REQ-PM-008 | Tenant permissions | SRS-PERMISSION-MATRIX | `admin/permissions/definitions.py` | `admin/permissions/definitions.py` | `tests/django/test_auth_integration.py` |
| REQ-PM-009 | Agent permissions | SRS-PERMISSION-MATRIX | `admin/permissions/definitions.py` | `admin/permissions/definitions.py` | `tests/django/test_auth_integration.py` |
| REQ-PM-010 | Resource permissions | SRS-PERMISSION-MATRIX | `admin/permissions/definitions.py` | `admin/permissions/granular.py` | `tests/django/test_auth_integration.py` |
| REQ-PM-012 | STD/RO mode availability | SRS-PERMISSION-MATRIX | `admin/aaas/models/tiers.py` | `admin/aaas/models/features.py` | `tests/django/test_auth_integration.py` |
| REQ-PM-013 | DEV/TRN mode tier restriction | SRS-PERMISSION-MATRIX | `admin/aaas/models/tiers.py` | `admin/aaas/models/features.py` | `tests/django/test_auth_integration.py` |
| REQ-PM-017 | Unauthenticated 401 | SRS-PERMISSION-MATRIX | `admin/common/auth.py` | `admin/common/auth.py` | `tests/django/test_auth_integration.py` |
| REQ-PM-019 | Suspended tenant 403 | SRS-PERMISSION-MATRIX | `admin/aaas/models/tenants.py` | `admin/common/auth.py` | `tests/django/test_auth_integration.py` |
| REQ-PM-021 | SpiceDB permission check | SRS-PERMISSION-MATRIX | `admin/permissions/api.py` | `services/common/spicedb_client.py` | `tests/django/test_auth_integration.py` |
| REQ-PM-022 | Quota exceeded 429 | SRS-PERMISSION-MATRIX | `admin/common/rate_limit.py` | `admin/common/rate_limit.py` | `tests/saas/test_phase1_security_regressions.py` |
| REQ-PM-023 | Platform screen restriction | SRS-PERMISSION-MATRIX | `webui/src/guards/permission-guard.ts` | `webui/src/guards/permission-guard.ts` | E2E test |
| REQ-PM-025 | Agent config screen restriction | SRS-PERMISSION-MATRIX | `webui/src/guards/permission-guard.ts` | `webui/src/guards/permission-guard.ts` | E2E test |
| REQ-PM-029 | AAAS API restriction | SRS-PERMISSION-MATRIX | `admin/permissions/api.py` | `admin/permissions/api.py` | `tests/django/test_auth_integration.py` |
| REQ-PM-030 | Admin user API restriction | SRS-PERMISSION-MATRIX | `admin/aaas/api/users.py` | `admin/aaas/api/users.py` | `tests/django/test_auth_integration.py` |
| REQ-PM-031 | Agent config API restriction | SRS-PERMISSION-MATRIX | `admin/agents/api/agents.py` | `admin/agents/api/agents.py` | `tests/django/test_auth_integration.py` |
| REQ-PM-035 | Role list API | SRS-PERMISSION-MATRIX | `admin/permissions/api.py` | `admin/permissions/api.py` | `tests/django/test_auth_integration.py` |
| REQ-PM-036 | Role CRUD API | SRS-PERMISSION-MATRIX | `admin/permissions/api.py` | `admin/permissions/api.py` | `tests/django/test_auth_integration.py` |
| REQ-PM-037 | Role deletion protection | SRS-PERMISSION-MATRIX | `admin/permissions/api.py` | `admin/permissions/api.py` | `tests/django/test_auth_integration.py` |
| REQ-PM-038 | System role immutability | SRS-PERMISSION-MATRIX | `admin/permissions/models.py` | `admin/permissions/models.py` | `tests/django/test_auth_integration.py` |
| REQ-PM-046 | SpiceDB platform resource | SRS-PERMISSION-MATRIX | `admin/permissions/definitions.py` | `admin/permissions/definitions.py` | Inspection |
| REQ-PM-047 | SpiceDB tenant resource | SRS-PERMISSION-MATRIX | `admin/permissions/definitions.py` | `admin/permissions/definitions.py` | Inspection |
| REQ-PM-048 | SpiceDB agent resource | SRS-PERMISSION-MATRIX | `admin/permissions/definitions.py` | `admin/permissions/definitions.py` | Inspection |
| REQ-PM-051 | Frontend route guards | SRS-PERMISSION-MATRIX | `webui/src/guards/permission-guard.ts` | `webui/src/guards/permission-guard.ts` | E2E test |
| REQ-PM-052 | Action guard UI | SRS-PERMISSION-MATRIX | `webui/src/guards/action-guard.ts` | `webui/src/guards/action-guard.ts` | E2E test |
| REQ-PM-053 | Backend permission decorators | SRS-PERMISSION-MATRIX | `admin/core/permissions.py` | `admin/core/permissions.py` | `tests/django/test_auth_integration.py` |
| REQ-PM-054 | Permission Redis cache | SRS-PERMISSION-MATRIX | `admin/common/auth.py` | `admin/common/auth.py` | `tests/django/test_auth_integration.py` |
| REQ-PM-055 | Permission denial logging | SRS-PERMISSION-MATRIX | `admin/audit/api.py` | `admin/audit/api.py` | `tests/django/test_auth_integration.py` |

### 4.2 Requirement to Test Case Mapping

| REQ ID | Test Case ID | Test Method | Expected Result |
|--------|--------------|-------------|-----------------|
| REQ-PM-017 | TC-PERM-001 | Unit test | Unauthenticated request returns 401 |
| REQ-PM-019 | TC-PERM-002 | Unit test | Request for suspended tenant returns 403 |
| REQ-PM-021 | TC-PERM-003 | Integration test | Unauthorized action returns 403 |
| REQ-PM-037 | TC-PERM-004 | Unit test | Delete role with users returns error |
| REQ-PM-038 | TC-PERM-005 | Unit test | Edit system role returns error |
| REQ-PM-044 | TC-PERM-006 | Unit test | Remove last SysAdmin returns error |
| REQ-PM-053 | TC-PERM-007 | Unit test | Decorator raises 403 for missing permission |

---

## 5. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12 | Soma Engineering | Initial version with full permission matrix, screen access, API access, and SpiceDB schema |
| 1.1 | 2026-05-21 | Soma Engineering | Refactored to ISO/IEC/IEEE 29148:2018 template; removed UI mockups, personas, and emojis; added traceability matrix and REQ-XXX numbering |

---

*Document conforms to ISO/IEC/IEEE 29148:2018 — Systems and Software Engineering — Life Cycle Processes — Requirements Engineering.*
