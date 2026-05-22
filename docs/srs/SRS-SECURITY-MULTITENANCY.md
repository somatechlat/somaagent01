# SRS-SECURITY-MULTITENANCY — Security and Tenant Isolation

| Field | Value |
|-------|-------|
| **System** | SomaAgent01 |
| **Document ID** | SRS-SECURITY-MULTITENANCY-2026-01-16 |
| **Version** | 1.1 |
| **Date** | 2026-01-16 |
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

This document specifies the security and multi-tenancy requirements for the SomaAgent01 platform. It defines tenant isolation, authentication, authorization, secret management, data encryption, and audit logging requirements necessary to operate a multi-tenant AI agent platform.

### 1.2 Scope

**In scope:**
- Tenant isolation across data stores (PostgreSQL, Milvus, Redis, Kafka, Vault)
- JWT-based authentication via Keycloak
- Fine-grained authorization via SpiceDB with OPA fallback
- Hierarchical secret management via HashiCorp Vault
- Data encryption at rest and in transit
- PII detection and redaction
- Comprehensive audit logging
- Per-tenant rate limiting

**Out of scope:**
- Keycloak deployment and configuration details
- Vault cluster operations and HA setup
- Specific compliance certifications (SOC 2, HIPAA)

### 1.3 Definitions

| Term | Definition |
|------|------------|
| AAAS | Agent-as-a-Service administrative layer |
| AuthContext | Runtime object carrying authenticated user identity, tenant ID, and roles |
| Capsule | Agent identity unit containing configuration, models, and capabilities |
| Fail-closed | Default-deny behavior when authorization system is unavailable |
| OPA | Open Policy Agent, used as fallback authorization provider |
| PII | Personally Identifiable Information |
| SpiceDB | Open-source fine-grained authorization database |
| Tenant | Isolated organizational boundary within the platform |
| Vault | HashiCorp Vault for secret storage and key management |

### 1.4 References

| ID | Document | Version | Location |
|----|----------|---------|----------|
| REF-001 | SRS-PERMISSION-MATRIX | 1.0 | `docs/srs/SRS-PERMISSION-MATRIX.md` |
| REF-002 | SRS-DATA-MODELS | 5.0 | `docs/srs/SRS-DATA-MODELS.md` |
| REF-003 | SRS-ARCHITECTURAL-PATTERNS | 1.0 | `docs/srs/SRS-ARCHITECTURAL-PATTERNS.md` |
| REF-004 | Keycloak Documentation | 24.0 | https://www.keycloak.org/documentation |
| REF-005 | SpiceDB Documentation | 1.35 | https://authzed.com/docs |
| REF-006 | HashiCorp Vault Documentation | 1.17 | https://developer.hashicorp.com/vault/docs |

---

## 2. Product Description

### 2.1 Product Perspective

The security and multi-tenancy subsystem is foundational to the SomaAgent01 platform. All upstream features — chat, memory, tool execution, agent configuration — depend on this subsystem for identity, isolation, and access control. The subsystem integrates with Keycloak for identity, SpiceDB for authorization, Vault for secrets, and PostgreSQL/Milvus/Redis/Kafka for tenant-scoped data persistence.

### 2.2 Product Functions

| ID | Function | Description |
|----|----------|-------------|
| FUNC-001 | Tenant Isolation | Enforce data separation across all persistence layers using tenant identifiers |
| FUNC-002 | Authentication | Validate JWT tokens issued by Keycloak and construct an AuthContext |
| FUNC-003 | Authorization | Evaluate user permissions against resources via SpiceDB with OPA fallback |
| FUNC-004 | Secret Management | Retrieve and store secrets via Vault with hierarchical scoping |
| FUNC-005 | Data Encryption | Encrypt data at rest and in transit; manage keys via Vault |
| FUNC-006 | PII Handling | Detect and redact PII before storage using Microsoft Presidio |
| FUNC-007 | Audit Logging | Record all security-relevant actions with tamper-evident storage |
| FUNC-008 | Rate Limiting | Enforce per-tenant request quotas based on subscription tier |

### 2.3 User Characteristics

| User Type | Role | Technical Level | Access |
|-----------|------|-----------------|--------|
| Platform Admin | AAAS SysAdmin | High | All tenants, platform configuration |
| Tenant Admin | Tenant SysAdmin | Medium | Single tenant, user and agent management |
| Tenant User | Member / Viewer | Low | Assigned agents, chat, read-only memory |
| Service Account | Internal microservice | High | Inter-service mTLS or service token |

### 2.4 Constraints

| ID | Constraint | Description |
|----|------------|-------------|
| CON-001 | TLS 1.3 Minimum | All inter-service and external communications must use TLS 1.3 |
| CON-002 | Vault Auto-Unseal | Vault must auto-unseal via AWS KMS; manual unseal is not acceptable for production |
| CON-003 | Default Deny | Any authorization check that cannot complete must result in DENY |
| CON-004 | Tenant ID Propagation | Every database query must include a tenant filter; cross-tenant queries are prohibited |

### 2.5 Assumptions and Dependencies

| ID | Assumption / Dependency | Impact if Invalid |
|----|------------------------|-------------------|
| AD-001 | Keycloak is reachable and issuing valid JWTs | Users cannot authenticate; platform is unavailable |
| AD-002 | SpiceDB is eventually consistent | Permission changes may take seconds to propagate |
| AD-003 | Vault is available for secret retrieval | API calls to LLM providers and integrations fail |
| AD-004 | Presidio analyzer models are loaded | PII may be stored unredacted |
| AD-005 | PostgreSQL TDE is enabled at the infrastructure layer | Data at rest is not encrypted if disabled |

---

## 3. Specific Requirements

### 3.1 Functional Requirements

#### 3.1.1 Tenant Isolation

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-TI-001 | The system shall include a `tenant_id` column on all PostgreSQL tables and enforce tenant-scoped queries. | Must | Test | Approved |
| REQ-TI-002 | The system shall use one Milvus collection per tenant for vector data isolation. | Must | Test | Approved |
| REQ-TI-003 | The system shall prefix all Redis keys with `tenant:{id}:*` to prevent key collision across tenants. | Must | Test | Approved |
| REQ-TI-004 | The system shall use one Kafka topic per tenant with naming convention `soma.{tenant}.events`. | Must | Inspection | Approved |
| REQ-TI-005 | The system shall isolate Vault paths per tenant under `secret/tenants/{id}/*`. | Must | Test | Approved |

**Rationale:** Prevents data leakage between tenants at every persistence layer.

**Dependencies:** REQ-AU-001 (authentication must establish tenant identity before isolation can be enforced).

#### 3.1.2 Authentication

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-AU-001 | The system shall validate incoming JWT tokens against Keycloak on every HTTP request. | Must | Test | Approved |
| REQ-AU-002 | The system shall construct an AuthContext containing `user_id`, `tenant_id`, and `roles` from validated JWT claims. | Must | Test | Approved |
| REQ-AU-003 | The system shall require the `X-Tenant-ID` header on all API requests and validate that it matches the tenant claim in the JWT. | Must | Test | Approved |
| REQ-AU-004 | The system shall propagate `Authorization`, `X-Tenant-ID`, and `X-Trace-ID` headers across all internal service calls. | Must | Inspection | Approved |

**Rationale:** Establishes identity and tenant context for all downstream authorization and isolation checks.

#### 3.1.3 Authorization

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-AZ-001 | The system shall evaluate all resource access requests against SpiceDB before allowing the operation. | Must | Test | Approved |
| REQ-AZ-002 | The system shall fallback to OPA policy evaluation when SpiceDB is unavailable. | Must | Test | Approved |
| REQ-AZ-003 | The system shall deny all access if both SpiceDB and OPA are unavailable (fail-closed). | Must | Test | Approved |
| REQ-AZ-004 | The system shall support hierarchical permissions: Platform > Tenant > Agent > Resource. | Must | Test | Approved |

**Rationale:** Fine-grained authorization with high availability through fallback mechanisms.

#### 3.1.4 Secret Management

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-SM-001 | The system shall store platform-level secrets (LLM provider keys, infrastructure credentials) under `secret/platform/*` in Vault. | Must | Inspection | Approved |
| REQ-SM-002 | The system shall store tenant-specific secrets under `secret/tenants/{tenant_id}/*`. | Must | Test | Approved |
| REQ-SM-003 | The system shall store per-capsule secrets under `secret/capsules/{capsule_id}/*`. | Must | Test | Approved |
| REQ-SM-004 | The system shall expose a UnifiedSecretManager interface for typed secret retrieval by scope. | Must | Test | Approved |
| REQ-SM-005 | The system shall prohibit the storage of API keys or secrets in environment variables. | Must | Inspection | Approved |

**Rationale:** Centralized secret management with scoped access prevents credential leakage.

#### 3.1.5 Data Security

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-DS-001 | The system shall encrypt all PostgreSQL data at rest using Transparent Data Encryption (TDE). | Must | Inspection | Approved |
| REQ-DS-002 | The system shall encrypt all Milvus data at rest using Milvus native encryption. | Must | Inspection | Approved |
| REQ-DS-003 | The system shall enforce TLS 1.3 for all data in transit. | Must | Test | Approved |
| REQ-DS-004 | The system shall use Vault with AWS KMS auto-unseal for encryption key management. | Must | Inspection | Approved |
| REQ-DS-005 | The system shall redact PII from text before persistence using Microsoft Presidio Analyzer and Anonymizer engines. | Must | Test | Approved |

**Rationale:** Protects sensitive data throughout its lifecycle.

#### 3.1.6 Audit Logging

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-AL-001 | The system shall emit an AuditEvent for every security-relevant action including `event_id`, `timestamp`, `tenant_id`, `user_id`, `action`, `resource_type`, `resource_id`, `changes`, `ip_address`, and `user_agent`. | Must | Test | Approved |
| REQ-AL-002 | The system shall retain audit logs in hot storage (PostgreSQL) for 30 days. | Must | Inspection | Approved |
| REQ-AL-003 | The system shall archive audit logs to S3/MinIO cold storage for 7 years. | Must | Inspection | Approved |
| REQ-AL-004 | The system shall stream audit events through Kafka to Elasticsearch for search and alerting. | Must | Inspection | Approved |

**Rationale:** Compliance and forensic analysis require complete, tamper-evident audit trails.

#### 3.1.7 Rate Limiting

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-RL-001 | The system shall enforce per-tenant rate limits based on subscription tier (Free, Starter, Team, Enterprise). | Must | Test | Approved |
| REQ-RL-002 | The system shall return HTTP 429 when a tenant exceeds its quota. | Must | Test | Approved |
| REQ-RL-003 | The system shall store rate limit counters in Redis with tenant-scoped keys. | Must | Inspection | Approved |

**Rationale:** Protects platform resources and enforces subscription boundaries.

---

### 3.2 Non-Functional Requirements

#### 3.2.1 Performance

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-PERF-001 | Authentication (JWT validation) shall complete within 50 ms. | 50 ms | Test |
| NFR-PERF-002 | SpiceDB permission check shall complete within 20 ms at p99. | 20 ms | Test |
| NFR-PERF-003 | Vault secret retrieval shall complete within 30 ms at p99. | 30 ms | Test |

#### 3.2.2 Security

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-SEC-001 | All secrets shall be stored only in Vault; no plaintext secrets in code, logs, or environment variables. | 100% coverage | Inspection |
| NFR-SEC-002 | Authorization fallback shall default to DENY. | 0 false positives | Test |
| NFR-SEC-003 | PII redaction shall run on all user-generated content before persistence. | 100% coverage | Test |

#### 3.2.3 Reliability

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-REL-001 | Authentication service availability shall be 99.99%. | 99.99% | Monitoring |
| NFR-REL-002 | Authorization fallback (OPA) shall activate within 100 ms of SpiceDB unavailability. | 100 ms | Test |

#### 3.2.4 Scalability

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-SCL-001 | The system shall support 10,000+ active tenants with isolated data stores. | 10,000 tenants | Analysis |
| NFR-SCL-002 | The system shall support 1,000,000+ audit events per day. | 1M events/day | Analysis |

#### 3.2.5 Maintainability

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-MNT-001 | Security-critical code paths shall have unit test coverage greater than or equal to 90%. | 90% | Coverage report |
| NFR-MNT-002 | Audit event schema changes shall be versioned and backward-compatible. | N/A | Inspection |

---

### 3.3 External Interface Requirements

#### 3.3.1 User Interfaces

No direct user interface requirements are specified in this document. Security interfaces are exposed through the admin web UI and API.

#### 3.3.2 Software Interfaces

| Interface | Protocol | Format | Authentication |
|-----------|----------|--------|----------------|
| Keycloak | HTTPS / OpenID Connect | JSON / JWT | Client credentials |
| SpiceDB | gRPC | Protobuf | Bearer token (preshared key) |
| Vault | HTTPS / REST | JSON | AppRole / Kubernetes auth |
| OPA | HTTPS / REST | JSON | mTLS or bearer token |
| Kafka | TCP / SASL_SSL | Avro / JSON | SASL/SCRAM |

#### 3.3.3 Hardware Interfaces

No hardware interface requirements are specified in this document.

---

### 3.4 Design Constraints

| ID | Constraint | Source |
|----|------------|--------|
| DC-001 | All API implementations must use Django Ninja, not FastAPI. | SRS-ARCHITECTURAL-PATTERNS |
| DC-002 | All database access must use Django ORM with tenant-scoped querysets. | SRS-ARCHITECTURAL-PATTERNS |
| DC-003 | SpiceDB schema definitions must be managed via the `admin/permissions/definitions.py` module. | Platform standard |
| DC-004 | Secret retrieval must route through `services/common/unified_secret_manager.py`. | Platform standard |

---

## 4. Traceability

### 4.1 Requirements Traceability Matrix

| REQ ID | Description | Source | Design | Implementation | Test |
|--------|-------------|--------|--------|----------------|------|
| REQ-TI-001 | PostgreSQL tenant_id column | SRS-SECURITY-MULTITENANCY | `admin/aaas/models/tenants.py` | `admin/aaas/models/tenants.py`, `admin/core/models/core.py` | `tests/saas/test_phase1_security_regressions.py` |
| REQ-TI-002 | Milvus collection per tenant | SRS-SECURITY-MULTITENANCY | `admin/core/models/core.py` | `services/memory_replicator/` | `tests/saas/test_phase1_security_regressions.py` |
| REQ-TI-003 | Redis key prefix | SRS-SECURITY-MULTITENANCY | `admin/common/rate_limit.py` | `admin/common/rate_limit.py` | `tests/saas/test_phase1_security_regressions.py` |
| REQ-TI-004 | Kafka topic per tenant | SRS-SECURITY-MULTITENANCY | `config/settings_registry.py` | `services/delegation_gateway/`, `services/conversation_worker/` | Integration test |
| REQ-TI-005 | Vault path isolation | SRS-SECURITY-MULTITENANCY | `services/common/unified_secret_manager.py` | `services/common/unified_secret_manager.py` | `tests/saas/test_phase1_security_regressions.py` |
| REQ-AU-001 | JWT validation | SRS-SECURITY-MULTITENANCY | `admin/auth/api.py` | `admin/auth/api.py`, `admin/common/auth.py` | `tests/django/test_auth_integration.py` |
| REQ-AU-002 | AuthContext construction | SRS-SECURITY-MULTITENANCY | `admin/common/auth.py` | `admin/common/auth.py`, `admin/common/session_manager.py` | `tests/django/test_auth_integration.py` |
| REQ-AU-003 | X-Tenant-ID header validation | SRS-SECURITY-MULTITENANCY | `admin/common/auth.py` | `admin/common/auth.py` | `tests/django/test_auth_integration.py` |
| REQ-AU-004 | Header propagation | SRS-SECURITY-MULTITENANCY | `admin/common/auth.py` | `admin/common/session_manager.py` | `tests/django/test_auth_integration.py` |
| REQ-AZ-001 | SpiceDB permission check | SRS-SECURITY-MULTITENANCY | `admin/permissions/api.py` | `services/common/spicedb_client.py`, `admin/permissions/api.py` | `tests/django/test_auth_integration.py` |
| REQ-AZ-002 | OPA fallback | SRS-SECURITY-MULTITENANCY | `admin/core/permissions.py` | `admin/core/permissions.py` | `tests/saas/test_phase1_security_regressions.py` |
| REQ-AZ-003 | Fail-closed default | SRS-SECURITY-MULTITENANCY | `admin/core/permissions.py` | `admin/core/permissions.py` | `tests/saas/test_phase1_security_regressions.py` |
| REQ-AZ-004 | Hierarchical permissions | SRS-SECURITY-MULTITENANCY | `admin/permissions/definitions.py` | `admin/permissions/definitions.py`, `admin/core/permission_matrix.py` | `tests/django/test_auth_integration.py` |
| REQ-SM-001 | Platform secrets in Vault | SRS-SECURITY-MULTITENANCY | `services/common/unified_secret_manager.py` | `services/common/unified_secret_manager.py` | `tests/saas/test_phase1_security_regressions.py` |
| REQ-SM-002 | Tenant secrets in Vault | SRS-SECURITY-MULTITENANCY | `services/common/unified_secret_manager.py` | `services/common/unified_secret_manager.py` | `tests/saas/test_phase1_security_regressions.py` |
| REQ-SM-003 | Capsule secrets in Vault | SRS-SECURITY-MULTITENANCY | `services/common/unified_secret_manager.py` | `services/common/unified_secret_manager.py` | `tests/saas/test_phase1_security_regressions.py` |
| REQ-SM-004 | UnifiedSecretManager interface | SRS-SECURITY-MULTITENANCY | `services/common/unified_secret_manager.py` | `services/common/unified_secret_manager.py` | `tests/saas/test_phase1_security_regressions.py` |
| REQ-SM-005 | No env var secrets | SRS-SECURITY-MULTITENANCY | `admin/core/helpers/secrets.py` | `admin/core/helpers/secrets.py`, `.env.example` | `tests/saas/test_phase1_security_regressions.py` |
| REQ-DS-001 | PostgreSQL TDE | SRS-SECURITY-MULTITENANCY | Infrastructure as Code | PostgreSQL instance configuration | Security audit |
| REQ-DS-002 | Milvus encryption | SRS-SECURITY-MULTITENANCY | Infrastructure as Code | Milvus instance configuration | Security audit |
| REQ-DS-003 | TLS 1.3 in transit | SRS-SECURITY-MULTITENANCY | `infra/k8s/` | Load balancer / ingress configuration | Security audit |
| REQ-DS-004 | Vault auto-unseal | SRS-SECURITY-MULTITENANCY | `infra/k8s/vault/` | Vault Helm values / configuration | Security audit |
| REQ-DS-005 | PII redaction | SRS-SECURITY-MULTITENANCY | `admin/core/context/models.py` | ContextBuilder redaction logic | `tests/saas/test_phase1_security_regressions.py` |
| REQ-AL-001 | AuditEvent schema | SRS-SECURITY-MULTITENANCY | `admin/aaas/models/audit.py` | `admin/aaas/models/audit.py`, `admin/audit/api.py` | `tests/saas/test_phase1_security_regressions.py` |
| REQ-AL-002 | Hot storage 30 days | SRS-SECURITY-MULTITENANCY | `admin/aaas/models/audit.py` | `admin/aaas/models/audit.py` | Inspection |
| REQ-AL-003 | Cold storage 7 years | SRS-SECURITY-MULTITENANCY | `services/memory_service/` | Archival pipeline | Inspection |
| REQ-AL-004 | Kafka to Elasticsearch | SRS-SECURITY-MULTITENANCY | `config/settings_registry.py` | Kafka Connect / Logstash | Integration test |
| REQ-RL-001 | Tier-based rate limits | SRS-SECURITY-MULTITENANCY | `admin/aaas/models/tiers.py` | `admin/common/rate_limit.py` | `tests/saas/test_phase1_security_regressions.py` |
| REQ-RL-002 | HTTP 429 on exceed | SRS-SECURITY-MULTITENANCY | `admin/common/rate_limit.py` | `admin/common/rate_limit.py` | `tests/saas/test_phase1_security_regressions.py` |
| REQ-RL-003 | Redis counters | SRS-SECURITY-MULTITENANCY | `admin/common/rate_limit.py` | `admin/common/rate_limit.py` | `tests/saas/test_phase1_security_regressions.py` |

### 4.2 Requirement to Test Case Mapping

| REQ ID | Test Case ID | Test Method | Expected Result |
|--------|--------------|-------------|-----------------|
| REQ-AU-001 | TC-SEC-001 | Unit test | Invalid JWT returns 401 |
| REQ-AU-003 | TC-SEC-002 | Unit test | Mismatched X-Tenant-ID returns 403 |
| REQ-AZ-003 | TC-SEC-003 | Integration test | SpiceDB + OPA down returns 403 |
| REQ-SM-005 | TC-SEC-004 | Static analysis | No plaintext API keys in environment variables |
| REQ-DS-005 | TC-SEC-005 | Unit test | PII redaction output contains no detected entities |
| REQ-RL-002 | TC-SEC-006 | Load test | Requests over limit return 429 |

---

## 5. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-16 | Soma Engineering | Initial version |
| 1.1 | 2026-05-21 | Soma Engineering | Refactored to ISO/IEC/IEEE 29148:2018 template; added traceability matrix |

---

*Document conforms to ISO/IEC/IEEE 29148:2018 — Systems and Software Engineering — Life Cycle Processes — Requirements Engineering.*
