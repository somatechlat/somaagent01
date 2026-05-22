# SRS-SAAS-INFRASTRUCTURE — AAAS Deployment Architecture

| Field | Value |
|-------|-------|
| **System** | SomaAgent01 |
| **Document ID** | SRS-SAAS-INFRASTRUCTURE-2026-05-21 |
| **Version** | 2.1 |
| **Date** | 2026-05-21 |
| **Status** | Draft |
| **Author** | SOMA Architecture Team |
| **Owner** | Infrastructure Team |

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

This document specifies the architecture and operational requirements for the SOMA AAAS (Autonomous Adaptive Agent Stack) Infrastructure. The AAAS infrastructure is a standalone deployment artifact that orchestrates the SOMA Triad (Agent, Brain, Memory) in a zero-dependency container environment.

### 1.2 Scope

**Included:**
- Container orchestration and startup sequencing
- Network topology and port allocation
- Backing service dependency management (Postgres, Redis, Kafka, Milvus, Keycloak, Vault)
- Runtime configuration injection
- Process supervision via supervisord

**Excluded:**
- Application business logic (defined in respective repository SRS documents)
- LLM inference models and training pipelines
- Data migration strategies beyond schema application

### 1.3 Definitions

| Term | Definition |
|------|------------|
| **AAAS** | Autonomous Adaptive Agent Stack — the containerized deployment unit |
| **SOMA Triad** | The three-layer architecture: SomaFractalMemory (Layer 2), SomaBrain (Layer 3), SomaAgent01 (Layer 4) |
| **Brain-First Strategy** | Schema migration order: SomaBrain first, then FractalMemory, then Agent01 |
| **HITL** | Human-in-the-Loop |

### 1.4 References

| ID | Document | Version | Location |
|----|----------|---------|----------|
| REF-001 | SRS-AGENTIQ | 6.0 | `docs/srs/SRS-AGENTIQ.md` |
| REF-002 | SRS-SOMABRAIN-INTEGRATION | 1.0 | `docs/srs/SRS-SOMABRAIN-INTEGRATION.md` |
| REF-003 | Docker Compose Specification | 3.8 | `infra/aaas/docker-compose.yml` |
| REF-004 | Supervisor Configuration | 1.0 | `infra/aaas/aaas/supervisord.conf` |

---

## 2. Product Description

### 2.1 Product Perspective

The AAAS infrastructure provides the runtime environment, network topology, and backing services required to execute the SOMA Stack. It is designed as a completely independent deployment artifact that does not contain application code. Application code is injected at runtime via Docker volumes (development) or COPY directives (production). The infrastructure is defined in `infra/aaas/docker-compose.yml` and orchestrated by `infra/aaas/start_aaas.sh`.

### 2.2 Product Functions

| ID | Function | Description |
|----|----------|-------------|
| FUNC-001 | Hardware Detection | Detect CUDA availability and set `SOMA_HARDWARE_MODE` |
| FUNC-002 | Infrastructure Wait-Loop | Poll TCP ports for backing services and block until ready |
| FUNC-003 | Sequential Schema Migration | Execute Django migrations in Brain-First order |
| FUNC-004 | Process Supervision | Manage Agent, Brain, and Memory as distinct processes |
| FUNC-005 | Network Bridging | Provide internal bridge network with external port forwarding |

### 2.3 User Characteristics

| User Type | Role | Technical Level | Access |
|-----------|------|-----------------|--------|
| DevOps Engineer | Deployment and operations | Advanced | Full infrastructure access |
| Backend Developer | Application development | Intermediate | Docker volume mounts, logs |
| QA Engineer | Test execution | Intermediate | Test environment ports |

### 2.4 Constraints

| ID | Constraint | Description |
|----|------------|-------------|
| CON-001 | Container-First | All services must run within a single Docker Compose network |
| CON-002 | Port Range | External ports must use the 639xx range to avoid conflicts |
| CON-003 | PID 1 | supervisord must execute as PID 1 inside the container |
| CON-004 | No Hardcoded Config | All configuration via `.env` files or HashiCorp Vault |

### 2.5 Assumptions and Dependencies

| ID | Assumption / Dependency | Impact if Invalid |
|----|------------------------|-------------------|
| AD-001 | Docker and Docker Compose are installed on the host | Deployment fails entirely |
| AD-002 | Host ports 63900-63999 are available | Port binding conflicts occur |
| AD-003 | Postgres, Redis, Kafka, and Milvus images are pullable | Backing services fail to start |
| AD-004 | Django manage.py files exist in each layer | Migrations cannot execute |

---

## 3. Specific Requirements

### 3.1 Functional Requirements

#### 3.1.1 Startup Orchestration

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-001 | The system shall detect CUDA availability at container startup and set `SOMA_HARDWARE_MODE` to "GPU" or "CPU". | Must | Test | Draft |
| REQ-002 | The system shall poll TCP ports for Postgres (5432), Redis (6379), and Kafka (9092) and block execution until all are confirmed ready. | Must | Test | Draft |
| REQ-003 | The system shall execute Django migrations in strict order: SomaBrain first, FractalMemory second, Agent01 last. | Must | Test | Draft |
| REQ-004 | The system shall launch supervisord as PID 1 to manage Agent, Brain, and Memory processes. | Must | Test | Draft |

**Rationale:** Prevents race conditions during initialization and ensures data integrity across dependent schema layers.

**Dependencies:** REQ-002 must complete before REQ-003.

#### 3.1.2 Network Topology

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-005 | The system shall create a dedicated internal bridge network named `soma_stack_net`. | Must | Inspection | Draft |
| REQ-006 | The system shall expose external ports in the 639xx range mapped to internal service ports as defined in the service port table. | Must | Test | Draft |
| REQ-007 | The system shall isolate inter-service communication to the internal bridge network. | Must | Inspection | Draft |

#### 3.1.3 Service Port Allocation

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-008 | SomaAgent01 API shall be accessible on host port 63900 mapped to internal port 9000. | Must | Test | Draft |
| REQ-009 | SomaBrain API shall be accessible on host port 63996 mapped to internal port 9696. | Must | Test | Draft |
| REQ-010 | SomaMemory API shall be accessible on host port 63901 mapped to internal port 10101. | Must | Test | Draft |
| REQ-011 | Postgres shall be accessible on host port 63932 mapped to internal port 5432. | Must | Test | Draft |
| REQ-012 | Redis shall be accessible on host port 63979 mapped to internal port 6379. | Must | Test | Draft |
| REQ-013 | Milvus shall be accessible on host port 63953 mapped to internal port 19530. | Must | Test | Draft |
| REQ-014 | Kafka shall be accessible on host port 63992 mapped to internal port 9092. | Must | Test | Draft |
| REQ-015 | Keycloak shall be accessible on host port 63980 mapped to internal port 8080. | Must | Test | Draft |
| REQ-016 | Vault shall be accessible on host port 63982 mapped to internal port 8200. | Must | Test | Draft |

---

### 3.2 Non-Functional Requirements

#### 3.2.1 Performance

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-PERF-001 | Infrastructure wait-loop shall complete within 60 seconds of all services reporting healthy. | 60s | Test |
| NFR-PERF-002 | Sequential migrations shall complete within 120 seconds for empty databases. | 120s | Test |

#### 3.2.2 Reliability

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-REL-001 | supervisord shall restart any crashed process automatically. | 100% restart rate | Test |
| NFR-REL-002 | The startup script shall exit with non-zero status if any backing service fails to become ready within 300 seconds. | Fail-fast | Test |

#### 3.2.3 Scalability

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-SCL-001 | The network topology shall support adding new services without reassigning existing ports. | Add 5 services | Analysis |

#### 3.2.4 Maintainability

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-MNT-001 | The startup orchestrator script shall be versioned independently of application logic. | Separate versioning | Inspection |

---

### 3.3 External Interface Requirements

#### 3.3.1 Software Interfaces

| Interface | Protocol | Format | Authentication |
|-----------|----------|--------|----------------|
| SomaAgent01 API | HTTP/1.1 | JSON | Bearer Token |
| SomaBrain API | HTTP/1.1 | JSON | Bearer Token |
| SomaMemory API | HTTP/1.1 | JSON | Bearer Token |
| Postgres | TCP | SQL | Password |
| Redis | TCP | RESP | Password |
| Kafka | TCP | Binary | SASL/SSL |
| Milvus | gRPC/HTTP | Protobuf/JSON | Token |
| Keycloak | HTTP/1.1 | JSON | OAuth 2.0 |
| Vault | HTTP/1.1 | JSON | Token |

#### 3.3.2 Hardware Interfaces

No hardware interfaces are required. GPU detection is performed via software (PyTorch CUDA check).

---

### 3.4 Design Constraints

| ID | Constraint | Source |
|----|------------|--------|
| DC-001 | All configuration variables injected via `.env` or HashiCorp Vault; no hardcoded values permitted. | VIBE Rule 91 |
| DC-002 | Orchestrator isolation: `start_aaas.sh` is self-contained and versioned independently. | Architecture Decision |
| DC-003 | Source code injection at runtime via Docker volumes (dev) or COPY (prod). | Deployment Strategy |

---

## 4. Traceability

### 4.1 Requirements Traceability Matrix

| REQ ID | Description | Source | Design | Implementation | Test |
|--------|-------------|--------|--------|----------------|------|
| REQ-001 | CUDA hardware detection | VIBE-91 | `infra/aaas/start_aaas.sh` | `infra/aaas/start_aaas.sh` | `tests/unit/` |
| REQ-002 | Infrastructure wait-loop | VIBE-91 | `infra/aaas/start_aaas.sh` | `infra/aaas/start_aaas.sh` | `tests/integration/` |
| REQ-003 | Sequential migrations | Brain-First Strategy | `infra/aaas/start_aaas.sh` | `infra/aaas/start_aaas.sh` | `tests/integration/` |
| REQ-004 | supervisord PID 1 | Container Best Practice | `infra/aaas/aaas/supervisord.conf` | `infra/aaas/aaas/supervisord.conf` | `tests/integration/` |
| REQ-005 | Internal bridge network | Docker Compose | `infra/aaas/docker-compose.yml` | `infra/aaas/docker-compose.yml` | `tests/integration/` |
| REQ-006 | 639xx port range | Architecture Decision | `infra/aaas/docker-compose.yml` | `infra/aaas/docker-compose.yml` | `tests/integration/` |
| REQ-007 | Inter-service isolation | Security | `infra/aaas/docker-compose.yml` | `infra/aaas/docker-compose.yml` | `tests/integration/` |
| REQ-008 | Agent port 63900 | Port Allocation Table | `infra/aaas/docker-compose.yml` | `infra/aaas/docker-compose.yml` | `tests/integration/` |
| REQ-009 | Brain port 63996 | Port Allocation Table | `infra/aaas/docker-compose.yml` | `infra/aaas/docker-compose.yml` | `tests/integration/` |
| REQ-010 | Memory port 63901 | Port Allocation Table | `infra/aaas/docker-compose.yml` | `infra/aaas/docker-compose.yml` | `tests/integration/` |
| REQ-011 | Postgres port 63932 | Port Allocation Table | `infra/aaas/docker-compose.yml` | `infra/aaas/docker-compose.yml` | `tests/integration/` |
| REQ-012 | Redis port 63979 | Port Allocation Table | `infra/aaas/docker-compose.yml` | `infra/aaas/docker-compose.yml` | `tests/integration/` |
| REQ-013 | Milvus port 63953 | Port Allocation Table | `infra/aaas/docker-compose.yml` | `infra/aaas/docker-compose.yml` | `tests/integration/` |
| REQ-014 | Kafka port 63992 | Port Allocation Table | `infra/aaas/docker-compose.yml` | `infra/aaas/docker-compose.yml` | `tests/integration/` |
| REQ-015 | Keycloak port 63980 | Port Allocation Table | `infra/aaas/docker-compose.yml` | `infra/aaas/docker-compose.yml` | `tests/integration/` |
| REQ-016 | Vault port 63982 | Port Allocation Table | `infra/aaas/docker-compose.yml` | `infra/aaas/docker-compose.yml` | `tests/integration/` |

### 4.2 Requirement to Test Case Mapping

| REQ ID | Test Case ID | Test Method | Expected Result |
|--------|--------------|-------------|-----------------|
| REQ-001 | TC-INFRA-001 | Shell execution | `SOMA_HARDWARE_MODE` set to GPU or CPU |
| REQ-002 | TC-INFRA-002 | Integration test | Script blocks until all ports respond |
| REQ-003 | TC-INFRA-003 | Integration test | Migrations run in Brain, Memory, Agent order |
| REQ-004 | TC-INFRA-004 | Container inspection | `ps -p 1` shows supervisord |
| REQ-005 | TC-INFRA-005 | Docker network ls | `soma_stack_net` exists |
| REQ-008 | TC-INFRA-006 | Port connectivity | `nc -z localhost 63900` succeeds |
| REQ-009 | TC-INFRA-007 | Port connectivity | `nc -z localhost 63996` succeeds |
| REQ-012 | TC-INFRA-008 | Port connectivity | `nc -z localhost 63979` succeeds |

---

## 5. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-21 | Infrastructure Team | Initial version |
| 2.0 | 2026-01-21 | Infrastructure Team | Standardized format |
| 2.1 | 2026-05-21 | SOMA Architecture Team | Refactored to ISO/IEC/IEEE 29148 template |

---

*Document conforms to ISO/IEC/IEEE 29148:2018 — Systems and Software Engineering — Life Cycle Processes — Requirements Engineering.*
