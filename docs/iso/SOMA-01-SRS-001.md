# SOMAAGENT01 — SOFTWARE REQUIREMENTS SPECIFICATION

## Document Control

| Field | Value |
|---|---|
| Document Title | SomaAgent01 Master Software Requirements Specification |
| Document Identifier | SOMA-01-SRS-001 |
| Version | 1.0.0 |
| Date | 2026-06-15 |
| Status | Draft |
| Author | SomaTech Engineering |
| Approver | — |
| Classification | Internal |
| ISO Reference | ISO 9001:2015 — Quality Management Systems — Requirements |
| Next Review | 2026-12-28 |

## Revision History

| Version | Date | Author | Description |
|---------|------|--------|-------------|

| 1.0.0 | 2026-09-28 | SomaTech Engineering | Brought under ISO document control. Prior status value `Baseline` is outside the closed set `Draft \| In Review \| Approved \| Obsolete`; normalised to `Draft` — no approver has signed this document. |
| 1.0.0 | 2026-06-15 | SomaTech Engineering | Initial master SRS consolidating 22 domain SRS documents; formalized with requirement IDs and traceability |

## Normative References

| Document | Identifier | Location |
|----------|------------|----------|
| System Architecture | SOMA-01-ARCH-001 | `docs/iso/SOMA-01-ARCH-001.md` |
| Security Assessment | SOMA-01-SEC-001 | `docs/iso/SOMA-01-SEC-001.md` |
| Quality Manual | SOMA-01-QMS-001 | `docs/iso/SOMA-01-QMS-001.md` |
| Domain SRS Documents | Various | `docs/requirements/` (22 files) |

---

## 1. INTRODUCTION

### 1.1 Purpose
This document specifies the software requirements for SomaAgent01, the gateway component of the Soma Cognitive Triad. It consolidates requirements from 22 domain-specific SRS documents into a single traceable specification.

### 1.2 Scope
SomaAgent01 is an enterprise multi-agent cognitive platform providing agent orchestration, multi-tenant management, real-time chat, and cognitive memory integration. It operates in Standalone mode (agent-only) and AAAS mode (integrated with SomaBrain and SomaFractalMemory).

### 1.3 Definitions

| Term | Definition |
|------|------------|
| REQ-XXX-NNN | Unique requirement identifier (category-sequence) |
| MoSCoW | Must, Should, Could, Won't prioritization |
| V&V | Verification and Validation |

---

## 2. FUNCTIONAL REQUIREMENTS

### 2.1 Authentication & Identity (REQ-AUTH)

| ID | Requirement | Priority | Source | Verification |
|----|-------------|----------|--------|-------------|
| REQ-AUTH-001 | System SHALL authenticate users via Keycloak OIDC | Must | SRS-SECURITY-MULTITENANCY | Integration test |
| REQ-AUTH-002 | System SHALL validate JWT tokens with RS256 algorithm | Must | SRS-SECURITY-MULTITENANCY | Unit test |
| REQ-AUTH-003 | System SHALL enforce JWT issuer validation by default | Must | SOMA-01-AUDIT-002 | Config test |
| REQ-AUTH-004 | System SHALL support OAuth2 PKCE flow for SSO | Must | SRS-SECURITY-MULTITENANCY | Integration test |
| REQ-AUTH-005 | System SHALL implement account lockout after 5 failed attempts within 15 minutes | Must | SRS-SECURITY-MULTITENANCY | Integration test |
| REQ-AUTH-006 | System SHALL support multi-factor authentication | Should | SRS-SECURITY-MULTITENANCY | Integration test |
| REQ-AUTH-007 | System SHALL support password reset via email | Should | SRS-SECURITY-MULTITENANCY | E2E test |
| REQ-AUTH-008 | System SHALL store session data in Redis with 15-minute TTL | Must | SRS-SECURITY-MULTITENANCY | Integration test |
| REQ-AUTH-009 | System SHALL NOT store JWT tokens in localStorage | Must | SOMA-01-SEC-001 | Frontend test |
| REQ-AUTH-010 | System SHALL support cookie-based JWT with httpOnly flag | Must | SOMA-01-SEC-001 | Frontend test |

### 2.2 Authorization & Access Control (REQ-AC)

| ID | Requirement | Priority | Source | Verification |
|----|-------------|----------|--------|-------------|
| REQ-AC-001 | System SHALL enforce authorization via OPA policy engine | Must | SRS-PERMISSION-MATRIX | Integration test |
| REQ-AC-002 | System SHALL enforce authorization via SpiceDB (Zanzibar) | Must | SRS-PERMISSION-MATRIX | Integration test |
| REQ-AC-003 | System SHALL implement UnifiedGate with three-layer check (OPA + SpiceDB + Capsule scope) | Must | SRS-AGENTIQ | Unit test |
| REQ-AC-004 | System SHALL fail-closed on any authorization error | Must | SOMA-01-SEC-001 | Unit test |
| REQ-AC-005 | System SHALL implement multi-tenant data isolation via ORM query filtering | Must | SRS-SECURITY-MULTITENANCY | Integration test |
| REQ-AC-006 | Permission check endpoints SHALL call real SpiceDB/OPA (not return stubs) | Must | SOMA-01-AUDIT-002 | Integration test |
| REQ-AC-007 | System SHALL implement rate limiting with sliding window algorithm | Must | SRS-SECURITY-MULTITENANCY | Load test |
| REQ-AC-008 | Rate limiter SHALL fail-closed on Redis errors | Must | SOMA-01-SEC-001 | Unit test |

### 2.3 Chat & Conversation (REQ-CHAT)

| ID | Requirement | Priority | Source | Verification |
|----|-------------|----------|--------|-------------|
| REQ-CHAT-001 | System SHALL support real-time chat via WebSocket | Must | SRS-CHAT-FLOW-MASTER | Integration test |
| REQ-CHAT-002 | System SHALL support REST-based chat API | Must | SRS-CHAT-FLOW-MASTER | Integration test |
| REQ-CHAT-003 | Chat SHALL process through 12-phase V3 orchestrator pipeline | Must | SRS-CHAT-FLOW-MASTER | Unit test |
| REQ-CHAT-004 | Chat SHALL stream LLM responses token-by-token via WebSocket deltas | Must | SRS-CHAT-FLOW-MASTER | E2E test |
| REQ-CHAT-005 | Chat SHALL support tool execution when LLM requests tools | Should | SRS-TOOL-SYSTEM | Integration test |
| REQ-CHAT-006 | Chat SHALL store messages in PostgreSQL (always, zero data loss) | Must | SRS-CHAT-FLOW-MASTER | Integration test |
| REQ-CHAT-007 | Chat SHALL store memories in SomaBrain (AAAS mode) with SFM fallback | Should | SRS-SOMABRAIN-INTEGRATION | Integration test |
| REQ-CHAT-008 | Chat SHALL implement circuit breakers on external service calls | Must | SRS-CHAT-FLOW-MASTER | Unit test |
| REQ-CHAT-009 | Chat SHALL use tiktoken for accurate token counting | Must | SRS-CONTEXT-BUILDING | Unit test |
| REQ-CHAT-010 | WebSocket SHALL authenticate via JWT from subprotocol, query string, header, or cookie | Must | SRS-CHAT-FLOW-MASTER | Integration test |
| REQ-CHAT-011 | WebSocket SHALL send heartbeat pings every 30 seconds | Should | SRS-CHAT-FLOW-MASTER | Integration test |
| REQ-CHAT-012 | WebSocket SHALL pre-load capsule, IQ, and tool registry at connection time | Should | SRS-CHAT-FLOW-MASTER | Performance test |

### 2.4 Agent & Capsule Management (REQ-AGENT)

| ID | Requirement | Priority | Source | Verification |
|----|-------------|----------|--------|-------------|
| REQ-AGENT-001 | System SHALL support CRUD operations for agents (Capsules) | Must | SRS-DATA-MODELS | API test |
| REQ-AGENT-002 | System SHALL derive AgentIQ settings from Capsule body | Must | SRS-AGENTIQ | Unit test |
| REQ-AGENT-003 | System SHALL support agent lifecycle: DRAFT → ACTIVE → ARCHIVED | Must | SRS-DATA-MODELS | Integration test |
| REQ-AGENT-004 | System SHALL support per-agent tool registry | Should | SRS-TOOL-SYSTEM | Integration test |
| REQ-AGENT-005 | System SHALL support per-agent neuromodulator baselines | Should | SRS-SOMABRAIN-INTEGRATION | Integration test |

### 2.5 Memory Integration (REQ-MEM)

| ID | Requirement | Priority | Source | Verification |
|----|-------------|----------|--------|-------------|
| REQ-MEM-001 | System SHALL integrate with SomaBrain for cognitive memory (AAAS mode) | Must | SRS-SOMABRAIN-INTEGRATION | Integration test |
| REQ-MEM-002 | System SHALL integrate with SomaFractalMemory for vector storage (AAAS mode) | Must | SRS-SOMABRAIN-INTEGRATION | Integration test |
| REQ-MEM-003 | Memory recall SHALL use SomaBrain as primary, SFM as fallback | Must | SRS-SOMABRAIN-INTEGRATION | Integration test |
| REQ-MEM-004 | System SHALL leave failed memory writes pending on the memory.wal outbox for replay | Must | SRS-SOMABRAIN-INTEGRATION | Unit test |
| REQ-MEM-005 | System SHALL work without SomaBrain/SFM in Standalone mode | Must | SRS-SAAS-INFRASTRUCTURE | Integration test |

### 2.6 Context Building (REQ-CTX)

| ID | Requirement | Priority | Source | Verification |
|----|-------------|----------|--------|-------------|
| REQ-CTX-001 | System SHALL build context using 5-lane allocation | Must | SRS-CONTEXT-BUILDING | Unit test |
| REQ-CTX-002 | Context lanes SHALL include: system prompt, history, memory, tools, personality | Must | SRS-CONTEXT-BUILDING | Unit test |
| REQ-CTX-003 | Context SHALL respect token budget from governor | Must | SRS-CONTEXT-BUILDING | Unit test |
| REQ-CTX-004 | Context SHALL degrade gracefully when memory services unavailable | Should | SRS-CONTEXT-BUILDING | Integration test |

### 2.7 Model Routing (REQ-MODEL)

| ID | Requirement | Priority | Source | Verification |
|----|-------------|----------|--------|-------------|
| REQ-MODEL-001 | System SHALL route LLM requests based on required capabilities | Must | SRS-MODEL-ROUTING | Unit test |
| REQ-MODEL-002 | System SHALL support multiple LLM providers via LiteLLM | Must | SRS-MODEL-ROUTING | Integration test |
| REQ-MODEL-003 | System SHALL implement circuit breaker on LLM calls | Must | SRS-MODEL-ROUTING | Unit test |

### 2.8 Multi-Tenancy (REQ-TENANT)

| ID | Requirement | Priority | Source | Verification |
|----|-------------|----------|--------|-------------|
| REQ-TENANT-001 | System SHALL support multi-tenant architecture with data isolation | Must | SRS-SECURITY-MULTITENANCY | Integration test |
| REQ-TENANT-002 | System SHALL enforce per-tenant rate limits | Must | SRS-BUDGET-SYSTEM | Load test |
| REQ-TENANT-003 | System SHALL enforce per-tenant token budgets | Must | SRS-BUDGET-SYSTEM | Integration test |
| REQ-TENANT-004 | System SHALL support subscription tiers (Starter, Pro, Enterprise) | Should | SRS-BUDGET-SYSTEM | Integration test |

### 2.9 Observability (REQ-OBS)

| ID | Requirement | Priority | Source | Verification |
|----|-------------|----------|--------|-------------|
| REQ-OBS-001 | System SHALL expose Prometheus metrics endpoint | Must | SRS-SAAS-INFRASTRUCTURE | Smoke test |
| REQ-OBS-002 | System SHALL implement structured JSON logging | Must | SRS-SAAS-INFRASTRUCTURE | Config test |
| REQ-OBS-003 | System SHALL support OpenTelemetry distributed tracing | Should | SRS-SAAS-INFRASTRUCTURE | Integration test |
| REQ-OBS-004 | System SHALL implement audit logging for all auth events | Must | SRS-SECURITY-MULTITENANCY | Integration test |

### 2.10 Deployment (REQ-DEP)

| ID | Requirement | Priority | Source | Verification |
|----|-------------|----------|--------|-------------|
| REQ-DEP-001 | System SHALL support Standalone deployment mode | Must | SOMA-01-ARCH-001 | Docker test |
| REQ-DEP-002 | System SHALL support AAAS deployment mode | Must | SOMA-01-ARCH-001 | Docker test |
| REQ-DEP-003 | System SHALL expose health check endpoint returning service status | Must | SRS-SAAS-INFRASTRUCTURE | Smoke test |
| REQ-DEP-004 | System SHALL run as non-root container user | Must | SOMA-01-SEC-001 | Docker test |
| REQ-DEP-005 | System SHALL support Kubernetes deployment with probes and limits | Should | SOMA-01-PROD-001 | K8s test |

---

## 3. NON-FUNCTIONAL REQUIREMENTS

### 3.1 Performance (REQ-PERF)

| ID | Requirement | Target | Verification |
|----|-------------|--------|-------------|
| REQ-PERF-001 | Chat API p95 latency | < 200ms (excluding LLM) | Load test |
| REQ-PERF-002 | WebSocket connection establishment | < 500ms | Load test |
| REQ-PERF-003 | Health check response time | < 50ms | Load test |
| REQ-PERF-004 | Concurrent WebSocket connections per instance | > 1,000 | Load test |
| REQ-PERF-005 | Memory recall latency (SomaBrain) | < 50ms p95 | Load test |

### 3.2 Reliability (REQ-REL)

| ID | Requirement | Target | Verification |
|----|-------------|--------|-------------|
| REQ-REL-001 | System availability | 99.9% uptime | Monitoring |
| REQ-REL-002 | Circuit breaker recovery time | < 30 seconds | Integration test |
| REQ-REL-003 | Data durability (chat messages) | Zero data loss | Integration test |
| REQ-REL-004 | Graceful degradation when SomaBrain unavailable | SFM fallback + memory.wal outbox | Integration test |

### 3.3 Security (REQ-SEC)

| ID | Requirement | Target | Verification |
|----|-------------|--------|-------------|
| REQ-SEC-001 | No hardcoded secrets in source code | Zero findings | Security scan |
| REQ-SEC-002 | All auth endpoints audited | 100% coverage | Code review |
| REQ-SEC-003 | CSP headers enabled | All responses | Security scan |
| REQ-SEC-004 | CSRF protection on all mutations | 100% coverage | Security scan |
| REQ-SEC-005 | No critical/high security findings in pentest | Zero | Penetration test |

### 3.4 Maintainability (REQ-MAINT)

| ID | Requirement | Target | Verification |
|----|-------------|--------|-------------|
| REQ-MAINT-001 | Test line coverage (somaAgent01) | >= 50% | Coverage report |
| REQ-MAINT-002 | Pyright type errors | < 200 | Type check |
| REQ-MAINT-003 | Ruff lint violations | Zero | Lint check |
| REQ-MAINT-004 | TODO/FIXME markers in production code | Zero | Grep scan |

---

## 4. INTERFACE REQUIREMENTS

### 4.1 External Interfaces (REQ-INT)

| ID | Interface | Protocol | Specification |
|----|-----------|----------|---------------|
| REQ-INT-001 | SomaBrain API | HTTP/1.1 + SSE | `soma-compatibility.json` endpoints |
| REQ-INT-002 | SomaFractalMemory API | HTTP/1.1 | `soma-compatibility.json` endpoints |
| REQ-INT-003 | Keycloak OIDC | HTTP/1.1 + OIDC | Keycloak 24 protocol |
| REQ-INT-004 | SpiceDB | gRPC | `authzed.api.v1` protobuf |
| REQ-INT-005 | OPA | HTTP/1.1 REST | `/v1/data/soma/allow` |
| REQ-INT-006 | PostgreSQL | TCP | psycopg v3 wire protocol |
| REQ-INT-007 | Redis | TCP | redis-py protocol |
| REQ-INT-008 | Kafka | TCP | aiokafka protocol |
| REQ-INT-009 | LiteLLM | HTTP/1.1 | OpenAI-compatible API |
| REQ-INT-010 | Vault | HTTP/1.1 REST | KV v2 secrets engine |

---

## 5. CONSTRAINTS

| ID | Constraint | Rationale |
|----|-----------|-----------|
| REQ-CON-001 | Django ORM only (no SQLAlchemy) | VIBE mandate, consistency |
| REQ-CON-002 | Django Ninja only (no FastAPI/DRF) | VIBE mandate, consistency |
| REQ-CON-003 | Lit 3.x only (no React/Alpine) | VIBE mandate, web standards |
| REQ-CON-004 | PostgreSQL only (no SQLite in production) | Data integrity, concurrency |
| REQ-CON-005 | Milvus only (no Qdrant) | Ecosystem consistency |
| REQ-CON-006 | Python 3.12+ required | Runtime standard |
| REQ-CON-007 | No mocks in tests | VIBE mandate, real infrastructure |

---

## 6. REQUIREMENTS TRACEABILITY

### 6.1 Traceability Matrix (Summary)

| Requirement Category | Count | Implemented | Tested | Coverage |
|---------------------|-------|-------------|--------|----------|
| Authentication (REQ-AUTH) | 10 | 8 | 4 | 40% |
| Authorization (REQ-AC) | 8 | 7 | 3 | 38% |
| Chat (REQ-CHAT) | 12 | 10 | 5 | 42% |
| Agent (REQ-AGENT) | 5 | 5 | 2 | 40% |
| Memory (REQ-MEM) | 5 | 4 | 2 | 40% |
| Context (REQ-CTX) | 4 | 4 | 2 | 50% |
| Model (REQ-MODEL) | 3 | 3 | 2 | 67% |
| Tenant (REQ-TENANT) | 4 | 3 | 2 | 50% |
| Observability (REQ-OBS) | 4 | 3 | 1 | 25% |
| Deployment (REQ-DEP) | 5 | 4 | 3 | 60% |
| Performance (REQ-PERF) | 5 | 0 | 0 | 0% |
| Reliability (REQ-REL) | 4 | 3 | 2 | 50% |
| Security (REQ-SEC) | 5 | 3 | 1 | 20% |
| Maintainability (REQ-MAINT) | 4 | 1 | 1 | 25% |
| Interface (REQ-INT) | 10 | 8 | 5 | 50% |
| Constraint (REQ-CON) | 7 | 7 | 7 | 100% |
| **TOTAL** | **95** | **73** | **42** | **44%** |

### 6.2 Detailed Traceability

Full traceability from requirement → code file → test file is maintained in the project tracking system. See `docs/requirements/` for domain-specific traceability.

---

## 7. DOMAIN SRS CROSS-REFERENCE

| Domain SRS | File | Requirements Mapped |
|-----------|------|---------------------|
| Chat Flow Master | `docs/requirements/SOMA-SRS-CHATFLOW-001.md` | REQ-CHAT-001 through REQ-CHAT-012 |
| AgentIQ | `docs/requirements/SOMA-SRS-AGENTIQ-001.md` | REQ-AC-003, REQ-AGENT-002 |
| Security & Multi-tenancy | `docs/requirements/SOMA-SRS-MULTITENANCY-001.md` | REQ-AUTH-*, REQ-AC-*, REQ-TENANT-* |
| Context Building | `docs/requirements/SOMA-SRS-CONTEXT-001.md` | REQ-CTX-* |
| SomaBrain Integration | `docs/requirements/SOMA-SRS-SOMABRAIN-001.md` | REQ-MEM-* |
| Model Routing | `docs/requirements/SOMA-SRS-MODELROUTING-001.md` | REQ-MODEL-* |
| Tool System | `docs/requirements/SOMA-SRS-TOOLS-001.md` | REQ-CHAT-005, REQ-AGENT-004 |
| Permission Matrix | `docs/requirements/SOMA-SRS-PERMISSIONS-001.md` | REQ-AC-* |
| Budget System | `docs/requirements/SOMA-SRS-BUDGET-001.md` | REQ-TENANT-002, REQ-TENANT-003 |
| Data Models | `docs/requirements/SOMA-SRS-DATAMODELS-001.md` | REQ-AGENT-001, REQ-AGENT-003 |
| Feature Flags | `docs/requirements/SOMA-SRS-FEATFLAGS-001.md` | REQ-AGENT (config) |
| SaaS Infrastructure | `docs/requirements/SOMA-SRS-SAASINFRA-001.md` | REQ-OBS-*, REQ-DEP-* |
| Multimodal | `docs/requirements/SOMA-SRS-MULTIMODAL-001.md` | REQ-CHAT (extensions) |
| Backup System | `docs/requirements/SOMA-SRS-BACKUP-001.md` | REQ-REL (data durability) |

---

End of Document
