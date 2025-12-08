# SomaAgent01 – ISO‑Compatible Software Requirements Specification (SRS)

## Document Control
- **Version:** 1.0.0
- **Date:** 2025‑11‑28
- **Author:** SomaAgent01 (generated from upgrade report)
- **Scope:** Modular tool‑first architecture, sandbox manager, deterministic FSM engine, Oak option‑layer, observability, security, and production deployment for the SomaAgent01 orchestrator.

---
### 1. Introduction
#### 1.1 Purpose
Provide a complete, ISO/IEC‑29148‑compliant specification for the enhancement of SomaAgent01 to support Oak‑style option handling, hardened sandboxed tool execution, and a deterministic finite‑state‑machine orchestration model.
#### 1.2 Intended Audience
- Backend developers
- DevOps / SRE engineers
- QA & test engineers
- Product owners
- Security auditors
#### 1.3 Scope
- **Tool Registry** – JSON‑schema‑driven registry (`tool_registry.json`).
- **Sandbox Manager** – Docker‑based isolated execution with `sandbox_policy.yaml`.
- **FSM Engine** – deterministic state machine for orchestrator lifecycle.
- **Oak Option Layer** – `/oak/option` API, feature‑flag gated, OPA‑protected.
- **Observability** – OpenTelemetry traces, Prometheus metrics, structured logging.
- **Security** – mTLS, Vault secret injection, input sanitisation, zero‑trust sandbox.
#### 1.4 References
- ISO/IEC 29148:2021 – Requirements Engineering
- Upgrade report: `/root/somaagent01_full_upgrade_report.md`
- Existing codebase (see repository tree under `/root/somaagent01`).

---
### 2. Overall Description
#### 2.1 Product Perspective
SomaAgent01 is the orchestrator that coordinates tool execution, manages state, and interacts with Somabrain via Kafka events. It provides a unified, extensible platform for AI agents.
#### 2.2 Product Functions
| Function | Description |
|----------|-------------|
| Tool Registry | Central JSON‑schema registry (`tool_registry.json`) describing name, version, input/output schemas, timeout. |
| Sandbox Manager | Executes each tool inside a Docker container respecting `sandbox_policy.yaml` (CPU, memory, syscalls). |
| FSM Engine | Deterministic finite‑state‑machine governing orchestrator states: `Idle`, `Planning`, `Executing`, `Verifying`, `Error`. |
| Oak Option Layer | Feature‑flagged `/oak/option` (POST/PUT/DELETE) with OPA policies `allow_option_creation` / `allow_option_update`. |
| Planner Service | `/oak/plan` endpoint (stateless, latency ≤ 200 ms for up to 500 options). |
| Observability | OpenTelemetry traces, Prometheus metrics (`somaagent_fsm_state`, `sandbox_execution_total`). |
| Security | mTLS, Vault secret injection, input sanitisation, zero‑trust sandbox. |
#### 2.3 User Classes & Characteristics
| Role | Interaction | Privileges |
|------|-------------|------------|
| Developer | Extends tool registry, writes new sandboxed tools | Full repo access |
| Operator | Monitors health, triggers roll‑outs | Read‑only on services |
| Security Auditor | Reviews OPA policies, logs | Read‑only |
| End‑User (tenant) | Calls `/oak/option` and `/oak/plan` via API gateway | Tenant‑scoped read/write |
#### 2.4 Operating Environment
- Kubernetes 1.28+ (GKE/EKS)
- Helm 3.x for deployments
- Docker Engine for sandbox containers
- Kafka 3.5 for event streaming
- PostgreSQL 15 for persistence of options and FSM state
- OPA 0.64 for policy enforcement
- OpenTelemetry collector → Jaeger + Prometheus + Grafana
#### 2.5 Design Constraints
- Zero‑downtime blue‑green deployments.
- All tool inputs must conform to JSON schemas defined in the registry.
- Sandbox containers must run with a minimal root‑less image and a strict seccomp profile.
- Feature flag `ENABLE_OAK` must be togglable at runtime.
#### 2.6 Assumptions & Dependencies
- CI/CD pipeline (GitHub Actions) is functional.
- Vault is available for secret injection.
- Network between services is secured via mTLS.

---
### 3. Specific Requirements
#### 3.1 Functional Requirements
| ID | Description |
|----|-------------|
| SA‑FR‑001 | The system shall maintain a JSON‑schema‑driven tool registry (`tool_registry.json`). Each entry includes name, version, input schema, output schema, and timeout. |
| SA‑FR‑002 | The sandbox manager shall execute any tool inside a Docker container defined by `sandbox_policy.yaml`, enforcing CPU, memory, and syscall limits. |
| SA‑FR‑003 | The orchestrator shall implement a deterministic FSM with states `Idle`, `Planning`, `Executing`, `Verifying`, `Error`. State transitions shall be logged and exposed via Prometheus counter `fsm_transition_total`. |
| SA‑FR‑004 | The Oak option layer shall expose POST `/oak/option`, PUT `/oak/option/{id}`, DELETE `/oak/option/{id}` endpoints, gated by feature flag `ENABLE_OAK`. |
| SA‑FR‑005 | Option creation shall persist the option in PostgreSQL, emit a Kafka `OptionCreated` event, and be allowed only if OPA policy `allow_option_creation` evaluates to true. |
| SA‑FR‑006 | Option update shall recalculate utility, emit `OptionUpdated`, and be allowed only if OPA policy `allow_option_update` evaluates to true. |
| SA‑FR‑007 | Planner (`/oak/plan`) shall accept a list of option IDs and return the top‑N plan within 200 ms for up to 500 options. |
| SA‑FR‑008 | All endpoints shall emit OpenTelemetry traces containing tenant ID and request UUID. |
| SA‑FR‑009 | Prometheus metrics shall include `somaagent_fsm_state`, `sandbox_execution_total`, `option_processed_total`. |
| SA‑FR‑010 | All inter‑service communication shall use mTLS with mutual authentication. |
| SA‑FR‑011 | Secrets (e.g., DB credentials, OPA tokens) shall be injected via Vault side‑car; no secret stored on disk. |
#### 3.2 Non‑Functional Requirements
| ID | Category | Requirement |
|----|----------|-------------|
| NFR‑001 | Performance | 99th‑percentile latency ≤ 200 ms for `/oak/plan` under 500 RPS. |
| NFR‑002 | Availability | 99.9 % uptime per month (excluding scheduled maintenance). |
| NFR‑003 | Scalability | Horizontal pod autoscaling based on custom metric `option_processed_total`. |
| NFR‑004 | Security | Zero‑trust sandbox, OPA enforcement, secret rotation every 24 h, input sanitisation. |
| NFR‑005 | Observability | Full OpenTelemetry trace chain, Prometheus metrics, Grafana dashboards with SLO alerts. |
| NFR‑006 | Maintainability | Unit test coverage ≥ 85 %, ADRs for major decisions, CI linting. |
| NFR‑007 | Portability | Deployable on any CNCF‑compatible Kubernetes cluster. |

---
### 4. External Interface Requirements
#### 4.1 User Interfaces
- Swagger UI generated by FastAPI for all REST endpoints.
#### 4.2 Software Interfaces
- Kafka topics: `option_events`, `planner_requests`, `sandbox_results`.
- PostgreSQL tables: `options`, `fsm_state`, `tool_logs`.
- Docker images for sandbox containers (base: `python:3.11-slim`).
- OPA REST API for policy evaluation.
#### 4.3 Communications Interfaces
- HTTP/2 with TLS for all external API calls.
- gRPC optional for internal high‑throughput streams.

---
### 5. System Features (Traceability Matrix)
| Requirement | Source Document |
|-------------|-----------------|
| SA‑FR‑001‑011 | /root/somaagent01_full_upgrade_report.md (functional sections) |
| NFR‑001‑007 | Same report (non‑functional sections) |

---
### 6. Other Requirements
- **Regulatory**: GDPR‑compliant handling of tenant data.
- **Backup & Recovery**: Daily PostgreSQL dump, Docker image versioning for sandbox containers.
- **Disaster Recovery**: Multi‑region Kubernetes cluster with fail‑over.

---
### 7. Appendices
- **A. Glossary** – definitions of Oak, FSM, OPA, sandbox, etc.
- **B. Acronyms** – list of all abbreviations used.
- **C. Revision History**
  | Version | Date | Author | Description |
  |---------|------|--------|-------------|
  | 1.0.0 | 2025‑11‑28 | SomaAgent01 | Initial ISO SRS for SomaAgent01 |

---
*End of Document*
