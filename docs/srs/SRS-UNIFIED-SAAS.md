# Software Requirements Specification

## Unified SaaS Platform: SomaAgent01 + SomaBrain + SomaFractalMemory

---

## Document Control

| Field | Value |
|-------|-------|
| Document ID | SA01-SRS-UNIFIED-SAAS-2026-01 |
| Version | 1.0.0 |
| Classification | Internal |
| Status | Draft |
| Effective Date | 2026-01-01 |
| Review Date | 2026-07-01 |
| Owner | Project Maintainers |
| Standard | ISO/IEC/IEEE 29148:2018 |

### Revision History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0.0 | 2026-01-01 | Codex | Initial unified SaaS SRS |

### Approval Signatures

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Product Owner | _________________ | _________________ | ________ |
| Technical Lead | _________________ | _________________ | ________ |
| QA Lead | _________________ | _________________ | ________ |
| Security Officer | _________________ | _________________ | ________ |

---

## Table of Contents

1. Introduction  
2. Overall Description  
3. Specific Requirements  
4. System Features  
5. External Interface Requirements  
6. Non-Functional Requirements  
7. Security Requirements  
8. Data Requirements  
9. Constraints  
10. Assumptions and Dependencies  
11. Acceptance Criteria  
12. Traceability Matrix  
13. Appendices  

---

## 1. Introduction

### 1.1 Purpose

This SRS defines the unified SaaS requirements for a three-repository system:
SomaAgent01 (control plane), SomaBrain (cognitive runtime), and
SomaFractalMemory (memory service). The document specifies requirements for
StandAlone operation of each service and full SomaStackClusterMode integration
when deployed together as a single SaaS.

### 1.2 Scope

#### 1.2.1 System Name
Unified SomaStack SaaS Platform (USSP)

#### 1.2.2 In-Scope Repositories

| Repository | Role | Default Port |
|-----------|------|--------------|
| somaAgent01 | SaaS control plane, UI, API gateway | 20020 |
| somabrain | Cognitive runtime and orchestration | 9696 |
| somafractalmemory | Memory storage and recall | 9595 |

#### 1.2.3 Out of Scope
- UI design system specifications (covered by existing UI SRS documents)
- Detailed database design (covered by ORM models and DDS where applicable)
- Cloud provisioning specifics (covered by deployment SRS)

### 1.3 Definitions, Acronyms, and Abbreviations

#### 1.3.1 Definitions

| Term | Definition |
|------|------------|
| StandAlone Mode | A single service runs independently with its own auth, storage, and config |
| SomaStackClusterMode | All three services run together with shared auth, tenant identity, and permissions |
| Control Plane | The system of record for tenants, users, agents, and billing |
| Cognitive Plane | The runtime that executes agent cognition and response generation |
| Memory Plane | The memory storage and retrieval subsystem |
| SpiceDB | Zanzibar-based authorization service used for fine-grained permissions |

#### 1.3.2 Acronyms

| Acronym | Expansion |
|---------|-----------|
| API | Application Programming Interface |
| JWT | JSON Web Token |
| OPA | Open Policy Agent |
| RBAC | Role-Based Access Control |
| SRS | Software Requirements Specification |

### 1.4 References

- SomaAgent01: `docs/srs/` and `AGENT.md`
- SomaBrain: `somabrain/` settings and SaaS auth code
- SomaFractalMemory: `somafractalmemory/` settings and SaaS auth code
- ISO/IEC/IEEE 29148:2018 (requirements structure)

---

## 2. Overall Description

### 2.1 Product Perspective

The unified SaaS platform consists of three Django-based services that must
operate independently in StandAlone mode and operate as a tightly integrated
SomaStackClusterMode SaaS when deployed together. SomaAgent01 is the control
plane. SomaBrain is the
cognitive runtime and must operate in tandem with SomaFractalMemory for memory
operations.

### 2.2 Product Functions

- Tenant and user management
- Agent creation and lifecycle management
- Cognitive orchestration and model execution
- Memory recall and storage
- Unified authentication and authorization
- Audit and observability

### 2.3 User Classes and Characteristics

- Platform administrators (control plane)
- Tenant administrators
- Agent developers and trainers
- End users (chat and inference)
- Service operators (DevOps/SRE)

### 2.4 Operating Environment

- Django 5.x with Django Ninja
- PostgreSQL, Redis, Kafka, Milvus (as configured per service)
- SpiceDB for permissions in SomaStackClusterMode
- OPA for policy enforcement where applicable

### 2.5 Design and Implementation Constraints

All services must maintain Django-only patterns and must not introduce
non-Django frameworks. Real infrastructure is required for tests.

---

## 3. Specific Requirements

### 3.1 Functional Requirements

- REQ-UNI-001: Each service shall support StandAlone mode without requiring
  external services outside its documented dependencies.
- REQ-UNI-002: SomaStackClusterMode shall provide a unified tenant identity across
  all three services.
- REQ-UNI-003: SomaStackClusterMode shall enforce a shared authorization model across
  all three services.
- REQ-UNI-004: SomaBrain shall require SomaFractalMemory for memory-backed
  operations in SomaStackClusterMode.
- REQ-UNI-005: SomaAgent01 shall remain the system of record for tenants, users,
  and agents in SomaStackClusterMode.
- REQ-UNI-006: The platform shall support per-tenant isolation across all
  storage and query paths.

### 3.2 StandAlone and SomaStackClusterMode Requirements

- REQ-UNI-010: StandAlone mode shall allow each service to start and operate
  without dependency on the other two services.
- REQ-UNI-011: SomaStackClusterMode shall require service-to-service authentication
  for all cross-service calls.
- REQ-UNI-012: Somabrain and somafractalmemory shall be deployed and configured
  as a pair in SomaStackClusterMode.
- REQ-UNI-013: If SomaFractalMemory is unavailable in SomaStackClusterMode, SomaBrain
  shall fail memory-dependent requests with explicit error responses.

### 3.3 Authentication and Authorization Requirements

- REQ-UNI-020: The unified platform shall define a single token claims contract
  used by all three services in SomaStackClusterMode.
- REQ-UNI-021: SomaStackClusterMode shall support JWT-based user authentication for
  UI and service calls.
- REQ-UNI-022: SomaStackClusterMode shall support API-key authentication for
  programmatic access where required.
- REQ-UNI-023: SpiceDB shall be the authoritative source of fine-grained
  permissions in SomaStackClusterMode.
- REQ-UNI-024: Authorization checks shall fail closed when SpiceDB is
  unavailable in SomaStackClusterMode.

### 3.4 Service Integration Requirements

- REQ-UNI-030: SomaAgent01 shall expose tenant, user, and agent identity in
  tokens or headers used by SomaBrain and SomaFractalMemory.
- REQ-UNI-031: SomaBrain shall pass tenant, user, agent, and conversation
  identifiers to SomaFractalMemory for all memory operations.
- REQ-UNI-032: SomaFractalMemory shall enforce namespace and permission checks
  based on the unified authorization model in SomaStackClusterMode.
- REQ-UNI-033: All inter-service URLs and credentials shall be configurable via
  environment variables.

### 3.5 Deployment and Topology Requirements

- REQ-UNI-034: The unified platform shall provide deployment configurations for
  AWS, Kubernetes, Docker, and Local Development targets.
- REQ-UNI-035: The Local Development deployment profile shall enforce a total
  host memory budget of 15 GB for the full stack.
- REQ-UNI-036: Local Development shall use production-like configuration flags
  for auth, logging, and storage, with scaled resource allocations.
- REQ-UNI-037: SomaStackClusterMode deployments shall label or namespace the cluster as
  "SomaStack" for discovery and operations.
- REQ-UNI-038: The platform shall export a topology tree of clusters, services,
  and containers with deterministic ordering.
- REQ-UNI-039: The topology export shall include status and role grouping for
  control plane, cognitive plane, and memory plane services.

---

## 4. System Features

### 4.1 Unified Tenant Identity

- Shared tenant and user identifiers across all services.
- Consistent tenant scoping for data access and auditing.

### 4.2 Dual-Mode Operation

- StandAlone operation with local auth and storage.
- SomaStackClusterMode operation with shared auth and permissions.

### 4.3 Cognition + Memory Pairing

- SomaBrain performs cognition.
- SomaFractalMemory stores and recalls memory.
- SomaStackClusterMode treats these as a single operational unit.

### 4.4 Unified Permissions

- SpiceDB-backed permissions for resource-level access control.
- Role-based fallback in StandAlone mode where configured.

### 4.5 Cluster Topology Export (SomaStack)

- The platform exports a hierarchical view of clusters, services, and containers.
- The topology view is grouped by control, cognitive, and memory planes.
- The export uses the cluster label "SomaStack" in SomaStackClusterMode.

---

## 5. External Interface Requirements

### 5.1 User Interfaces

- SomaAgent01 provides the primary SaaS UI and API surface.
- Somabrain and SomaFractalMemory expose service APIs for runtime use and
  internal integration.

### 5.2 Software Interfaces

- REST/HTTP APIs between services for operational calls.
- gRPC for SpiceDB authorization checks.
- Optional OPA policy evaluation where enabled.

### 5.3 Communication Interfaces

- All services shall support TLS termination at the ingress or proxy layer.
- Service-to-service traffic shall support token-based authentication.

---

## 6. Non-Functional Requirements

- REQ-UNI-040: All services shall emit health endpoints suitable for readiness
  and liveness checks.
- REQ-UNI-041: All services shall expose structured logs suitable for centralized
  aggregation.
- REQ-UNI-042: All services shall expose metrics suitable for monitoring system
  latency and error rates.
- REQ-UNI-043: Performance and availability targets shall be defined per
  deployment environment and documented with each release.
- REQ-UNI-044: Local Development resource usage shall stay within the 15 GB
  host memory budget under normal load.
- REQ-UNI-045: The platform shall scale horizontally to support millions of
  transactions per day across control, cognitive, and memory planes.
- REQ-UNI-046: The platform shall sustain high-concurrency workloads without
  cross-tenant data leakage or degraded authorization guarantees.

---

## 7. Security Requirements

- REQ-UNI-050: Secrets shall be provided only via environment variables or
  external secret managers.
- REQ-UNI-051: Authentication tokens shall not be stored in plaintext at rest.
- REQ-UNI-052: Authorization checks shall be enforced at API boundaries.
- REQ-UNI-053: Audit logs shall include tenant and actor identifiers.

---

## 8. Data Requirements

- REQ-UNI-060: Tenant, user, agent, and conversation identifiers shall be
  consistent across services in SomaStackClusterMode.
- REQ-UNI-061: Memory records shall include tenant, agent, and conversation
  identifiers required for access control.
- REQ-UNI-062: Data retention and deletion shall respect tenant scope and
  regulatory controls.

---

## 9. Constraints

- Django-only implementation across all services (ORM, migrations, and Ninja).
- Open-source-only dependencies across all services and deployment tooling.
- No mocks or stubs in production test suites; real infrastructure required.
- Default ports are configurable and may vary by deployment profile.

---

## 10. Assumptions and Dependencies

- SpiceDB is available and reachable in SomaStackClusterMode.
- Keycloak (or equivalent JWT issuer) is available for SaaS user auth when
  enabled.
- PostgreSQL, Redis, Kafka, and Milvus are available according to each
  service's configuration.

---

## 11. Acceptance Criteria

- AC-UNI-001: Each service starts and passes health checks in StandAlone mode.
- AC-UNI-002: SomaStackClusterMode passes cross-service auth checks for tenant-scoped
  requests.
- AC-UNI-003: Permission denials are enforced consistently across all services.
- AC-UNI-004: SomaBrain returns explicit errors when SomaFractalMemory is
  unavailable in SomaStackClusterMode.
- AC-UNI-005: Audit logs record tenant and actor for control-plane actions.
- AC-UNI-006: Deployment artifacts exist for AWS, Kubernetes, Docker, and Local
  Development targets.
- AC-UNI-007: Local Development runs within a 15 GB host memory budget.
- AC-UNI-008: Topology export renders a deterministic tree labeled "SomaStack"
  in SomaStackClusterMode.

---

## 12. Traceability Matrix

| Requirement ID | Section | Primary Component |
|---------------|---------|-------------------|
| REQ-UNI-001 | 3.1 | somaAgent01, somabrain, somafractalmemory |
| REQ-UNI-002 | 3.1 | somaAgent01 |
| REQ-UNI-003 | 3.1 | all services |
| REQ-UNI-004 | 3.1 | somabrain, somafractalmemory |
| REQ-UNI-020 | 3.3 | all services |
| REQ-UNI-023 | 3.3 | somaAgent01, somabrain, somafractalmemory |
| REQ-UNI-031 | 3.4 | somabrain |
| REQ-UNI-034 | 3.5 | all services |
| REQ-UNI-035 | 3.5 | all services |
| REQ-UNI-037 | 3.5 | all services |
| REQ-UNI-038 | 3.5 | somaAgent01 |
| REQ-UNI-040 | 6 | all services |
| REQ-UNI-045 | 6 | all services |
| REQ-UNI-046 | 6 | all services |
| REQ-UNI-050 | 7 | all services |
| REQ-UNI-060 | 8 | all services |

---

## 13. Appendices

### 13.1 Related SRS Documents

- `docs/srs/SRS-DEPLOYMENT-MODES.md`
- `docs/deployment/SOFTWARE_DEPLOYMENT_MODES.md`
- `docs/srs/SRS-AUTHENTICATION.md`
- `docs/srs/SRS-PERMISSION-MATRIX.md`
- `docs/srs/SRS-ARCHITECTURE.md`
