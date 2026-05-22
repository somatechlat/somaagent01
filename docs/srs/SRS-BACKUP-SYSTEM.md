# SRS-BACKUP-SYSTEM — Agent Backup & Disaster Recovery

| Field | Value |
|-------|-------|
| **System** | SomaAgent01 |
| **Document ID** | SRS-BACKUP-SYSTEM-2026-01-16 |
| **Version** | 3.0.0 |
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

This document specifies the backup, audit trail, and disaster recovery system for SomaAgent01. The system guarantees reversibility of changes via snapshot semantics, full traceability of actor actions, and replayability of resource history from immutable audit logs.

### 1.2 Scope

**In scope:**
- Immutable audit logging (`admin/aaas/models/audit.py`)
- Capsule export with cryptographic signing
- Capsule import with signature and constitution verification
- Rollback to previous states using `old_value` snapshots
- History replay from audit logs
- Full backup bundle generation (PostgreSQL, Redis, code, Docker)
- Disaster recovery procedures and RTO/RPO targets

**Out of scope:**
- SomaBrain Constitution storage and serving (external to SomaAgent01)
- Real-time replication of runtime state
- Automated failover of chat sessions

### 1.3 Definitions

| Term | Definition |
|------|------------|
| **AuditLog** | An append-only database record capturing WHO, WHAT, WHEN, and WHY for every mutable operation. |
| **Capsule** | The complete agent identity, configuration, and signature bundle. |
| **Constitution** | The canonical governance document served by SomaBrain L3; never stored locally. |
| **Export Bundle** | A signed artifact containing one or more capsules plus metadata. |
| **Rollback** | Restoring a resource to a previous state using its `old_value` from an AuditLog entry. |
| **Replay** | Reconstructing the full history of a resource by ordered AuditLog entries. |
| **RTO** | Recovery Time Objective: target time to restore service after disaster. |
| **RPO** | Recovery Point Objective: maximum acceptable data loss window. |

### 1.4 References

| ID | Document | Version | Location |
|----|----------|---------|----------|
| REF-001 | SomaBrain Constitution API | 1.0 | `https://somabrain.l3/constitution/version` |
| REF-002 | PostgreSQL Documentation | 15 | https://www.postgresql.org/docs/15/ |
| REF-003 | Ed25519 Signature Standard | RFC 8032 | https://tools.ietf.org/html/rfc8032 |

---

## 2. Product Description

### 2.1 Product Perspective

The Backup System spans the SomaAgent01 data layer and file system. It relies on PostgreSQL for the append-only `audit_logs` table, Redis for ephemeral settings, and the file system for export bundles. Cryptographic signing binds capsules to the SomaBrain Constitution via Ed25519 signatures. The system is invoked by administrative operations, export/import services, and disaster recovery runbooks.

### 2.2 Product Functions

| ID | Function | Description |
|----|----------|-------------|
| FUNC-001 | Audit Logging | Record every mutable operation with actor, action, resource, old/new values, and context. |
| FUNC-002 | Cryptographic Export | Sign capsule export bundles with Ed25519 and log the export action. |
| FUNC-003 | Verified Import | Validate export signatures, capsule signatures, and Constitution checksums before restoring. |
| FUNC-004 | Rollback | Revert a resource to a prior state captured in an AuditLog `old_value`. |
| FUNC-005 | History Replay | Reconstruct the complete timeline of a resource from ordered AuditLog entries. |
| FUNC-006 | Full Backup | Generate a complete backup bundle including database, cache, code, and container images. |
| FUNC-007 | Disaster Recovery | Rebuild the environment from backups within defined RTO/RPO targets. |

### 2.3 User Characteristics

| User Type | Role | Technical Level | Access |
|-----------|------|-----------------|--------|
| Platform Operator | Execute backups, imports, and disaster recovery | Advanced | Admin API / CLI |
| Tenant Admin | Request capsule exports and view audit history | Intermediate | Agent Settings UI |
| Security Auditor | Review audit logs and signature chains | Advanced | Read-only database access |

### 2.4 Constraints

| ID | Constraint | Description |
|----|------------|-------------|
| CON-001 | Append-Only Audit | `audit_logs` table must not allow UPDATE or DELETE operations. |
| CON-002 | External Constitution | The Constitution must be fetched from SomaBrain at runtime; local storage is prohibited. |
| CON-003 | Admin-Only Rollback | Rollback operations require SpiceDB admin permission. |
| CON-004 | Re-Certification | Imported capsules must be re-certified before activation. |

### 2.5 Assumptions and Dependencies

| ID | Assumption / Dependency | Impact if Invalid |
|----|------------------------|-------------------|
| AD-001 | PostgreSQL is available and regularly backed up. | Audit history and application data are lost. |
| AD-002 | Ed25519 private key (`SOMA_REGISTRY_PRIVATE_KEY`) is available in Vault. | Exports cannot be signed; imports cannot be verified. |
| AD-003 | SomaBrain L3 Constitution endpoint is reachable during import. | Constitution checksum verification fails; import rejected. |

---

## 3. Specific Requirements

### 3.1 Functional Requirements

#### 3.1.1 Audit Logging

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-BKP-001 | The system shall maintain an append-only `AuditLog` (`admin/aaas/models/audit.py`, table `audit_logs`) recording `actor_id`, `actor_email`, `tenant`, `action`, `resource_type`, `resource_id`, `old_value`, `new_value`, `ip_address`, `user_agent`, `request_id`, and `created_at`. | Must | Inspection | Draft |
| REQ-BKP-002 | The system shall prevent UPDATE and DELETE operations on `audit_logs` via database constraints or triggers. | Must | Inspection | Draft |
| REQ-BKP-003 | The system shall generate audit entries for the following actions: `capsule.created`, `capsule.updated`, `capsule.certified`, `capsule.archived`, `capsule.exported`, `capsule.imported`, `capsule.cloned`, `capsule.revoked`, `tenant.created`, `agent.created`, `tier.updated`. | Must | Test | Draft |

**AuditLog Model Fields**

| Field | Type | Description |
|-------|------|-------------|
| `actor_id` | UUID | Keycloak user ID |
| `actor_email` | Email | Denormalized for query performance |
| `tenant` | FK | Tenant context |
| `action` | Char | Action code (e.g., `capsule.created`) |
| `resource_type` | Char | Entity type (e.g., `capsule`) |
| `resource_id` | UUID | Affected resource identifier |
| `old_value` | JSON | State before the change |
| `new_value` | JSON | State after the change |
| `ip_address` | GenericIPAddress | Client IP |
| `user_agent` | Text | Client user agent |
| `request_id` | Char | `X-Request-ID` correlation ID |
| `created_at` | DateTime | Timestamp (auto_now_add) |

**Rationale:** Immutable audit logs provide the foundation for traceability, rollback, and replay.

**Dependencies:** REQ-BKP-003 depends on REQ-BKP-001.

#### 3.1.2 Export & Import

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-BKP-004 | The system shall generate capsule export bundles signed with Ed25519 using `SOMA_REGISTRY_PRIVATE_KEY`. | Must | Test | Draft |
| REQ-BKP-005 | The system shall create an `AuditLog` entry with `action=capsule.exported` on every export, capturing the export path and checksum. | Must | Test | Draft |
| REQ-BKP-006 | On import, the system shall verify the export bundle signature, the capsule signature, and the Constitution checksum from SomaBrain. | Must | Test | Draft |
| REQ-BKP-007 | If any verification step fails, the system shall reject the import and log a `capsule.import_failed` audit entry. | Must | Test | Draft |
| REQ-BKP-008 | Successfully imported capsules shall be created in `draft` status and must undergo re-certification before activation. | Must | Test | Draft |
| REQ-BKP-009 | The system shall log `capsule.imported` on successful import with source backup and original capsule IDs. | Must | Test | Draft |

**Import Verification Flow**

1. Load export bundle.
2. Verify export signature (Ed25519).
3. Verify capsule signature (Ed25519).
4. Fetch Constitution from SomaBrain L3.
5. Verify Constitution checksum matches `constitution_ref.checksum`.
6. If all valid, create capsule as DRAFT and log import.
7. If any step invalid, reject and log failure.

#### 3.1.3 Rollback

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-BKP-010 | The system shall support rollback of a resource to a previous state by applying the `old_value` from a selected `AuditLog` entry. | Must | Test | Draft |
| REQ-BKP-011 | Rollback shall require SpiceDB admin permission. | Must | Test | Draft |
| REQ-BKP-012 | After rollback, the system shall create a new `AuditLog` entry with `action=capsule.reverted`, capturing the previous state as `old_value` and the restored state as `new_value`. | Must | Test | Draft |

#### 3.1.4 Replay

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-BKP-013 | The system shall provide a replay function that returns the complete ordered history of a resource from `AuditLog` entries, including timestamp, action, actor, before/after state, and context. | Must | Test | Draft |

#### 3.1.5 Disaster Recovery

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-BKP-014 | The system shall generate full backup bundles containing: signed capsule exports, PostgreSQL dump, Redis snapshot, git bundle, and Docker image tarballs. | Must | Test | Draft |
| REQ-BKP-015 | The backup output directory shall include a `manifest.json` with metadata and a top-level signature. | Must | Inspection | Draft |
| REQ-BKP-016 | The disaster recovery runbook shall specify a rebuild sequence: deploy infrastructure, restore PostgreSQL, restore Redis, connect to SomaBrain, verify Constitution, import capsules, verify signatures, re-certify, activate agents. | Must | Inspection | Draft |

**Backup Bundle Structure**

```
/backups/agent_backup_YYYYMMDD_HHMMSS/
├── manifest.json           # Metadata + signature
├── capsules.json           # Signed capsule exports
├── postgres_dump.sql       # All tables including audit_logs
├── redis_backup.json       # Redis settings
├── somaAgent01.bundle      # Git bundle
└── *.tar                   # Docker images
```

---

### 3.2 Non-Functional Requirements

#### 3.2.1 Performance

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-BKP-PERF-001 | AuditLog write latency | <= 20 ms | Load test |
| NFR-BKP-PERF-002 | Export generation time for 100 capsules | <= 30 s | Load test |

#### 3.2.2 Security

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-BKP-SEC-001 | AuditLog table shall be append-only with database-level protections against tampering. | 100% | Inspection |
| NFR-BKP-SEC-002 | Ed25519 signing keys shall be stored in Vault, never in source code or settings. | 100% | Inspection |
| NFR-BKP-SEC-003 | Export and import operations shall be authorized via SpiceDB permissions. | 100% | Test |
| NFR-BKP-SEC-004 | Capsule tampering shall be detectable via signature verification on import. | 100% | Test |

**Security Matrix**

| Threat | Mitigation | Audit |
|--------|------------|-------|
| Capsule tampering | Ed25519 signature | Verified on import |
| Export tampering | Ed25519 export signature | Verified |
| Unauthorized export | SpiceDB permission | `capsule.exported` logged |
| Unauthorized import | SpiceDB permission | `capsule.imported` logged |
| Rollback abuse | Admin-only permission | `capsule.reverted` logged |
| Audit log tampering | Append-only table | Database triggers |

#### 3.2.3 Reliability

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-BKP-REL-001 | Recovery Time Objective (RTO) | <= 4 hours | DR drill |
| NFR-BKP-REL-002 | Recovery Point Objective (RPO) | <= 1 hour | Backup monitoring |

#### 3.2.4 Scalability

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-BKP-SCL-001 | AuditLog shall support at least 10 million records per tenant without query degradation. | 10M+ | Load test |

#### 3.2.5 Maintainability

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-BKP-MNT-001 | Backup scripts shall be version-controlled and executable as standalone Python modules. | Yes | Inspection |
| NFR-BKP-MNT-002 | Rollback and replay functions shall be covered by unit tests. | 100% | Coverage report |

---

### 3.3 External Interface Requirements

#### 3.3.1 User Interfaces

Tenant administrators may request capsule exports and view audit timelines via the Agent Settings UI. Security auditors may query audit logs via read-only database access or admin reporting tools.

#### 3.3.2 Software Interfaces

| Interface | Protocol | Format | Authentication |
|-----------|----------|--------|----------------|
| PostgreSQL | TCP | SQL | PostgreSQL roles |
| Redis | TCP | Key/value | Redis AUTH |
| SomaBrain Constitution | HTTPS | JSON | mTLS / API key |
| Vault | HTTPS | JSON | Vault token |
| File System | Local | Binary/JSON | OS permissions |

#### 3.3.3 Hardware Interfaces

None.

---

### 3.4 Design Constraints

| ID | Constraint | Source |
|----|------------|--------|
| DC-BKP-001 | Constitution must be fetched from SomaBrain L3; local storage is prohibited. | Architecture decision |
| DC-BKP-002 | Backup directory structure shall follow the defined manifest format. | Design standard |
| DC-BKP-003 | `audit_logs` must use append-only semantics at the database layer. | Compliance requirement |

---

## 4. Traceability

### 4.1 Requirements Traceability Matrix

| REQ ID | Description | Source | Design | Implementation | Test |
|--------|-------------|--------|--------|----------------|------|
| REQ-BKP-001 | Append-only AuditLog model | Product backlog | `audit.py` | `admin/aaas/models/audit.py` | `tests/unit/test_audit_log.py` |
| REQ-BKP-002 | Prevent UPDATE/DELETE on audit_logs | Compliance | DB triggers | PostgreSQL migration | `tests/unit/test_audit_triggers.py` |
| REQ-BKP-003 | Standard audit event types | Product backlog | `audit.py` | `admin/aaas/models/audit.py` | `tests/unit/test_audit_events.py` |
| REQ-BKP-004 | Signed export bundles | Security req | Export service | `admin/services/export.py` | `tests/unit/test_export_signing.py` |
| REQ-BKP-005 | Export audit entry | Security req | Export service | `admin/services/export.py` | `tests/unit/test_export_audit.py` |
| REQ-BKP-006 | Import verification chain | Security req | Import service | `admin/services/import.py` | `tests/unit/test_import_verification.py` |
| REQ-BKP-007 | Reject failed imports | Security req | Import service | `admin/services/import.py` | `tests/unit/test_import_rejection.py` |
| REQ-BKP-008 | Draft status + re-certification | Product backlog | Import service | `admin/services/import.py` | `tests/unit/test_import_workflow.py` |
| REQ-BKP-009 | Import audit entry | Security req | Import service | `admin/services/import.py` | `tests/unit/test_import_audit.py` |
| REQ-BKP-010 | Rollback via old_value | Product backlog | Rollback service | `admin/services/rollback.py` | `tests/unit/test_rollback.py` |
| REQ-BKP-011 | Admin-only rollback permission | Security req | SpiceDB policy | `policy/backup.rego` | `tests/unit/test_rollback_auth.py` |
| REQ-BKP-012 | Rollback audit entry | Security req | Rollback service | `admin/services/rollback.py` | `tests/unit/test_rollback_audit.py` |
| REQ-BKP-013 | History replay | Product backlog | Replay service | `admin/services/replay.py` | `tests/unit/test_replay.py` |
| REQ-BKP-014 | Full backup bundle generation | DR req | Backup script | `scripts/backup_agent.py` | `tests/integration/test_backup_bundle.py` |
| REQ-BKP-015 | Manifest with signature | DR req | Backup script | `scripts/backup_agent.py` | `tests/integration/test_backup_manifest.py` |
| REQ-BKP-016 | DR rebuild runbook | DR req | Documentation | `docs/deployment/dr_runbook.md` | DR drill checklist |

### 4.2 Requirement to Test Case Mapping

| REQ ID | Test Case ID | Test Method | Expected Result |
|--------|--------------|-------------|-----------------|
| REQ-BKP-001 | TC-BKP-001 | Inspection | `AuditLog` model contains all required fields. |
| REQ-BKP-002 | TC-BKP-002 | SQL test | UPDATE/DELETE on `audit_logs` rejected by trigger. |
| REQ-BKP-004 | TC-BKP-004 | Unit test | Export bundle signature verifies with public key. |
| REQ-BKP-006 | TC-BKP-006 | Unit test | Import succeeds only when all 3 verification steps pass. |
| REQ-BKP-007 | TC-BKP-007 | Unit test | Invalid signature causes rejection and audit failure log. |
| REQ-BKP-010 | TC-BKP-010 | Unit test | Rollback restores exact `old_value` state. |
| REQ-BKP-011 | TC-BKP-011 | Auth test | Non-admin rollback request returns 403. |
| REQ-BKP-013 | TC-BKP-013 | Unit test | Replay returns ordered timeline matching audit entries. |
| REQ-BKP-014 | TC-BKP-014 | Integration test | Backup directory contains all 6 required artifacts. |
| REQ-BKP-016 | TC-BKP-016 | DR drill | System restored within 4 hours with data loss <= 1 hour. |

---

## 5. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 3.0.0 | 2026-01-16 | Platform Engineering | Initial ISO/IEC/IEEE 29148 conformant version. Refactored from ad-hoc SRS. Migrated to requirement tables, traceability matrix, and removed personas/emojis. |

---

*Document conforms to ISO/IEC/IEEE 29148:2018 — Systems and Software Engineering — Life Cycle Processes — Requirements Engineering.*
