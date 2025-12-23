# SomaAgent01 — Canonical Requirements Specification

**Document ID:** SA01-REQ-CANONICAL-2025-12  
**Version:** 4.0  
**Date:** 2025-12-21  
**Status:** CANONICAL — Single Source of Truth

---

## 1. Introduction

This document serves as the **Single Source of Truth** for all requirements of the SomaAgent01 project. It consolidates all previous specifications into one unified standard.

**Project Goals:**
1. **Clean Architecture:** Strict separation of concerns (Domain, Application, Infrastructure, Presentation)
2. **Security-First:** Zero Trust principles, OPA policies, ClamAV scanning, secure uploads
3. **Modern Web UI:** AI-native, responsive, accessible interface with real-time capabilities
4. **VIBE Compliance:** 100% adherence to Verification, Implementation, Behavior, Execution coding rules
5. **Cognitive Integration:** Full SomaBrain integration for memory, adaptation, and neuromodulation
6. **Multimodal Capabilities:** Image, diagram, video, and document generation

---

## 2. Core Architecture Requirements

### 2.1 Structural Integrity & Design Patterns

| ID | Requirement | Priority |
|----|-------------|----------|
| REQ-ARC-001 | System MUST be organized into Clean Architecture layers: Domain, Application, Infrastructure, Presentation | HIGH |
| REQ-ARC-002 | Monolithic modules MUST be decomposed into single-purpose components (< 300 lines per file) | HIGH |
| REQ-ARC-003 | All configuration MUST be accessed via `src.core.config.cfg.ConfigFacade` singleton | HIGH |
| REQ-ARC-004 | Dependencies MUST be injected into Use Cases and Services | HIGH |

### 2.2 Legacy & Cleanup

| ID | Requirement | Priority |
|----|-------------|----------|
| REQ-CLN-001 | All imports of deleted `persist_chat` module MUST be removed | HIGH |
| REQ-CLN-002 | Backward compatibility wrappers MUST be provided for legacy code until full refactor | MEDIUM |

---

## 3. Security Requirements

### 3.1 Authorization & Policy (OPA)

| ID | Requirement | Priority |
|----|-------------|----------|
| REQ-SEC-001 | All agent tool executions MUST be authorized by Open Policy Agent (OPA) | HIGH |
| REQ-SEC-002 | If OPA is unavailable, system MUST deny the action (Fail-Closed) | HIGH |
| REQ-SEC-003 | Policies MUST restrict tools based on `tenant_id` and `persona_id` | HIGH |

### 3.2 Secure File Uploads

| ID | Requirement | Priority |
|----|-------------|----------|
| REQ-SEC-004 | Large file uploads MUST use TUS protocol for resumability | HIGH |
| REQ-SEC-005 | All uploads MUST be scanned by ClamAV (SCAN_PENDING → QUARANTINED/AVAILABLE) | HIGH |
| REQ-SEC-006 | Upload endpoints MUST be rate-limited using `slowapi` (Redis-backed) | HIGH |

### 3.3 Secrets & Vault

| ID | Requirement | Priority |
|----|-------------|----------|
| REQ-SEC-042 | All provider keys, OPA tokens, SomaBrain creds MUST be sourced from Vault at call time | HIGH |
| REQ-SEC-043 | PII detection/redaction MUST run on ingest before storage or outbound calls | HIGH |

---

## 4. Web UI Requirements

### 4.1 General UX & Design System

| ID | Requirement | Priority |
|----|-------------|----------|
| REQ-UI-001 | UI MUST use "Neon/Glassmorphism" design system (tokens for colors, typography, spacing) | HIGH |
| REQ-UI-002 | Interfaces MUST be fully responsive (Mobile, Tablet, Desktop) | HIGH |
| REQ-UI-003 | Application MUST utilize semantic HTML and pass `axe-core` accessibility scans | HIGH |

### 4.2 Chat Interface

| ID | Requirement | Priority |
|----|-------------|----------|
| REQ-UI-004 | Chat MUST support Server-Sent Events (SSE) for token-by-token streaming | HIGH |
| REQ-UI-005 | Users MUST be able to Create, Load, Rename, and Delete chat sessions | HIGH |
| REQ-UI-006 | Chat input MUST support Drag & Drop file uploads (integrated with TUS) | MEDIUM |

### 4.3 Feature Modules

| ID | Requirement | Priority |
|----|-------------|----------|
| REQ-UI-007 | Settings modal MUST allow configuration of Agent parameters and API keys | HIGH |
| REQ-UI-008 | Memory Dashboard MUST display memory graph nodes/edges and allow semantic search | MEDIUM |
| REQ-UI-009 | Scheduler dashboard MUST allow listing, creating, and deleting scheduled tasks | MEDIUM |
| REQ-UI-010 | Capsule Marketplace MUST allow viewing and installing Agent Capsules | MEDIUM |

---

## 5. System Quality & Verification

### 5.1 Testing (VIBE)

| ID | Requirement | Priority |
|----|-------------|----------|
| REQ-TST-001 | All critical paths MUST have Property-Based Tests (Hypothesis) | HIGH |
| REQ-TST-002 | All UI features MUST have Playwright E2E tests | HIGH |
| REQ-TST-003 | Integration tests MUST run against real containerized services, not mocks | HIGH |

### 5.2 Observability / Health

| ID | Requirement | Priority |
|----|-------------|----------|
| REQ-OBS-001 | `DegradationMonitor` MUST track service health and reduce context window if degraded | HIGH |
| REQ-OBS-002 | Prometheus metrics MUST be exposed for Request Latency, Error Rates, OPA Decisions | HIGH |

---

## 6. Transactional Integrity & Explainability

### 6.1 ACID & Sagas

| ID | Requirement | Priority |
|----|-------------|----------|
| RQ-TX-001 | All Postgres mutations MUST be wrapped in explicit transactions; failures roll back | HIGH |
| RQ-TX-002 | Every workflow step MUST define a compensation step; failures trigger compensations | HIGH |
| RQ-TX-003 | Side effects to Kafka MUST use outbox pattern; compensations emit tombstone events | HIGH |
| RQ-TX-004 | Session/token issuance MUST occur only after transaction commits | HIGH |
| RQ-TX-005 | System MUST expose "describe run/failure" view combining Temporal history, saga/audit rows | HIGH |
| RQ-TX-006 | User/operator cancel MUST map to Temporal cancel and run compensations | HIGH |
| RQ-TX-007 | Prometheus metrics MUST cover: compensations_total, rollback_latency_seconds | HIGH |
| RQ-TX-008 | Calls to irreversible external systems MUST be gated by pre-flight validation/OPA | HIGH |
| RQ-TX-009 | Periodic reconciliation workflow MUST detect orphaned compensations and auto-heal | MEDIUM |
| RQ-TX-010 | OPA checks MUST execute before side effects; Secrets MUST be fetched inside activities | HIGH |

---

## 7. Messaging, Storage, Replication, Backup

### 7.1 Messaging Durability

| ID | Requirement | Priority |
|----|-------------|----------|
| RQ-MSG-001 | Kafka producers MUST be idempotent with acks=all; consumers MUST be idempotent | HIGH |

### 7.2 Upload/Asset Safety

| ID | Requirement | Priority |
|----|-------------|----------|
| RQ-UPL-001 | Uploads MUST write metadata first, then binary; failures leave no orphaned metadata | HIGH |

### 7.3 Data Replication & Backups

| ID | Requirement | Priority |
|----|-------------|----------|
| RQ-REP-001 | Postgres prod MUST be deployed HA with WAL archiving and PITR; quarterly restore tests | HIGH |

### 7.4 Audit Coverage

| ID | Requirement | Priority |
|----|-------------|----------|
| RQ-AUD-001 | All state-changing operations MUST emit structured audit events with correlation_id | HIGH |

---

## 8. Deployment Resource Envelope

| ID | Requirement | Priority |
|----|-------------|----------|
| RQ-DEP-015 | Entire dev stack MUST respect 15 GB total memory limit | HIGH |
| RQ-DEP-016 | Dev compose/helm MUST mirror prod hardening (health probes, restart=always, etc.) | HIGH |
| RQ-DEP-017 | Resource limits MUST be validated in CI; Prometheus must scrape cgroup memory/cpu | HIGH |

---

## 9. End-to-End Flow Integrity

| ID | Requirement | Priority |
|----|-------------|----------|
| RQ-FLOW-018 | Every hop MUST carry workflow_id, event_id, session_id, tenant, persona, capsule, capability_id | HIGH |
| RQ-FLOW-019 | Multimodal ingest MUST create hash-deduped metadata, run AV scan, produce derived artifacts | HIGH |
| RQ-FLOW-020 | No hardcoded model/tool IDs; Selector MUST use capability registry + OPA | HIGH |
| RQ-FLOW-021 | End-to-end chat P95 ≤ 2s (text), ≤ 5s (vision), TTS start ≤ 800ms | HIGH |
| RQ-FLOW-022 | Gateway and workers MUST remain async; no sync SomaBrain calls on hot paths | HIGH |
| RQ-FLOW-023 | After every step, system MUST call SomaBrain `/remember` and `/context/feedback` | HIGH |
| RQ-FLOW-024 | All flows MUST call OPA with tenant/persona/capsule context | HIGH |
| RQ-FLOW-025 | API and UI MUST expose "Decision Trace" per message | HIGH |
| RQ-FLOW-026 | Degradation monitor MUST feed selector; fallbacks MUST record `fallback_reason` | HIGH |
| RQ-FLOW-027 | Attachments must be hash-deduped; deletes cascade to provenance and SomaBrain | HIGH |
| RQ-FLOW-028 | Importance scoring may be LLM-assisted but MUST be policy-gated | MEDIUM |
| RQ-FLOW-029 | PII/secret detection MUST run on ingest; redaction paths available via compensation | HIGH |
| RQ-FLOW-030 | Real health probes for STT/TTS/Vision/Video providers MUST feed capability health | HIGH |

---

## 10. Tool Registry, Selection, and Learning

| ID | Requirement | Priority |
|----|-------------|----------|
| RQ-TOOL-031 | Tools MUST be represented in Capability Registry schema (same as models) | HIGH |
| RQ-TOOL-032 | Tool invocation MUST flow through selector + OPA; direct dispatch forbidden | HIGH |
| RQ-TOOL-033 | Every tool execution MUST emit full provenance/audit fields | HIGH |
| RQ-TOOL-034 | Each tool call MUST persist SomaBrain `remember` and `/context/feedback` | HIGH |
| RQ-TOOL-035 | Active health probes per tool/provider feed capability health | HIGH |
| RQ-TOOL-036 | Tool-generated assets must use same attachments/provenance/tombstone rules | HIGH |
| RQ-TOOL-037 | Tool discovery endpoints MUST filter by tenant/persona/capsule per allowlists | HIGH |
| RQ-TOOL-038 | CI MUST fail if tool dispatch bypasses selector/OPA | HIGH |

---

## 11. AgentIQ Governor (Capsule-Scoped Intelligence Governance)

| ID | Requirement | Priority |
|----|-------------|----------|
| RQ-AIQ-050 | AgentIQ Governor MUST run after policy gates, before model/tool invocation | HIGH |
| RQ-AIQ-051 | Compute AIQ_pred pre-call and AIQ_obs post-call | HIGH |
| RQ-AIQ-052 | Prompt assembly MUST use lane plans; Buffer lane ≥200 tokens | HIGH |
| RQ-AIQ-053 | Tool discovery MUST be capsule-scoped before Top-K | HIGH |
| RQ-AIQ-054 | Digests MUST retain anchors and carry faithfulness metadata | HIGH |
| RQ-AIQ-055 | Support degradation levels L0–L4 (Normal→Safe) | HIGH |
| RQ-AIQ-056 | Every turn MUST emit RunReceipt | HIGH |
| RQ-AIQ-057 | All AIQ weights/thresholds MUST be live-tunable via UI Settings | MEDIUM |
| RQ-AIQ-058 | Provide regression/chaos suites for AgentIQ invariants | HIGH |
| RQ-AIQ-059 | AgentIQ v1 MUST run in-process with Fast Path and Rescue Path modes | HIGH |

---

## 12. Confidence Score Extension

| ID | Requirement | Priority |
|----|-------------|----------|
| RQ-CONF-060 | LLM wrappers MUST request token-level logprobs when supported | HIGH |
| RQ-CONF-061 | Implement `calculate_confidence()` with modes {average|min|percentile_90} | HIGH |
| RQ-CONF-062 | All public responses MUST add `confidence: float|null` when enabled | HIGH |
| RQ-CONF-063 | Events/audit stores MUST persist only scalar confidence (no token logprobs) | HIGH |
| RQ-CONF-064 | Runtime-configurable thresholds: `min_acceptance`, `on_low`, `treat_null_as_low` | HIGH |
| RQ-CONF-065 | Prometheus metrics: confidence avg/EWMA, histogram, missing count, rejected count | HIGH |
| RQ-CONF-066 | Added overhead ≤5ms warm / ≤10ms cold; failure MUST NOT abort responses | HIGH |
| RQ-CONF-067 | Feature-flagged rollout; OpenAPI minor version bump only | MEDIUM |

---

## 13. Multimodal Model Selection & Permissions

| ID | Requirement | Priority |
|----|-------------|----------|
| RQ-MM-001 | Maintain capability registry per modality with max_size/ctx, latency_class, cost_tier, health | HIGH |
| RQ-MM-002 | Model selection MUST be based on intent + modalities, tenant/persona, latency/budget hints | HIGH |
| RQ-MM-003 | `model.use` decisions MUST be checked against OPA before invocation | HIGH |
| RQ-MM-004 | Every selection MUST emit audit fields: workflow_id, session_id, tenant, persona, intent | HIGH |
| RQ-MM-005 | Selector MUST skip providers marked unhealthy/degraded | HIGH |
| RQ-MM-006 | Asset type/format MUST be derived from mime/content-type; defaults from registry | HIGH |
| RQ-MM-010 | Every interaction MUST be persisted to SomaBrain with full provenance | HIGH |
| RQ-MM-011 | Each stored memory MUST trigger `/context/feedback` | HIGH |
| RQ-MM-012 | All SomaBrain writes must include workflow_id/correlation_id | HIGH |
| RQ-MM-013 | Agent UI settings MUST expose SomaBrain configuration | HIGH |
| RQ-MM-014 | Use async SomaBrain client; remove legacy sync helpers | HIGH |

---

## 14. SomaBrain Integration Requirements

### 14.1 Implemented Endpoints

| Endpoint | Method | Status |
|----------|--------|--------|
| `/memory/remember` | POST | ✅ Implemented |
| `/memory/recall` | POST | ✅ Implemented |
| `/memory/recall/stream` | POST | ✅ Implemented |
| `/memory/remember/batch` | POST | ✅ Implemented |
| `/context/evaluate` | POST | ✅ Implemented |
| `/context/feedback` | POST | ✅ Implemented |
| `/context/adaptation/state` | GET | ✅ Implemented |
| `/persona/{pid}` | PUT/GET/DELETE | ✅ Implemented |
| `/neuromodulators` | GET/POST | ✅ Implemented |
| `/sleep/run` | POST | ✅ Implemented |
| `/sleep/status` | GET | ✅ Implemented |
| `/plan/suggest` | POST | ✅ Implemented |
| `/health` | GET | ✅ Implemented |

### 14.2 Missing Endpoints (Gap Analysis)

| Endpoint | Method | Priority | Mode |
|----------|--------|----------|------|
| `/context/adaptation/reset` | POST | HIGH | STANDARD |
| `/act` | POST | HIGH | STANDARD |
| `/sleep/status/all` | GET | MEDIUM | **ADMIN** |
| `/admin/services` | GET | MEDIUM | **ADMIN** |
| `/admin/services/{name}` | GET | MEDIUM | **ADMIN** |
| `/admin/services/{name}/start` | POST | MEDIUM | **ADMIN** |
| `/admin/services/{name}/stop` | POST | MEDIUM | **ADMIN** |
| `/admin/services/{name}/restart` | POST | MEDIUM | **ADMIN** |
| `/admin/outbox` | GET | LOW | **ADMIN** |
| `/admin/outbox/replay` | POST | LOW | **ADMIN** |
| `/admin/features` | GET/POST | LOW | **ADMIN** |
| `/memory/admin/rebuild-ann` | POST | LOW | **ADMIN** |
| `/config/memory` | GET/PATCH | MEDIUM | STANDARD |
| `/personality` | POST | MEDIUM | STANDARD |
| `/micro/diag` | GET | LOW | **ADMIN** |
| `/cognitive/thread/*` | Various | MEDIUM | STANDARD |
| `/api/util/sleep` | POST | MEDIUM | STANDARD |
| `/api/brain/sleep_mode` | POST | MEDIUM | STANDARD |

**Note:** Admin endpoints are ONLY available when agent is running in ADMIN mode.

### 14.3 User Stories

| ID | Story | Priority |
|----|-------|----------|
| US-001 | As a cognitive agent, I want to reset my adaptation state to defaults | HIGH |
| US-002 | As a cognitive agent, I want to execute actions through SomaBrain's `/act` endpoint | HIGH |
| US-003 | As a system administrator, I want to manage cognitive services (ADMIN mode only) | MEDIUM |
| US-004 | As a cognitive agent, I want to transition between sleep states | MEDIUM |
| US-005 | As a cognitive agent, I want to set and retrieve personality state | MEDIUM |
| US-006 | As a system administrator, I want to get and update memory configuration | MEDIUM |
| US-007 | As a cognitive agent, I want to manage cognitive threads | MEDIUM |
| US-008 | As a system administrator, I want to view sleep status for all tenants (ADMIN mode only) | MEDIUM |
| US-009 | As a system administrator, I want to retrieve microcircuit diagnostics (ADMIN mode only) | LOW |
| US-010 | As a system administrator, I want to manage feature flags (ADMIN mode only) | LOW |

### 14.4 Non-Functional Requirements

| ID | Requirement |
|----|-------------|
| NFR-001 | All new endpoints MUST use existing circuit breaker pattern |
| NFR-002 | All new endpoints MUST leverage existing retry logic with exponential backoff |
| NFR-003 | All new endpoints MUST emit metrics via `SOMA_REQUESTS_TOTAL` and `SOMA_REQUEST_SECONDS` |
| NFR-004 | All new endpoints MUST propagate trace context via `inject()` |
| NFR-005 | All new endpoints MUST raise `SomaClientError` on failure |
| NFR-006 | All new methods MUST have complete type hints |
| NFR-007 | All new methods MUST have docstrings |
| NFR-008 | All integration tests MUST run against live SomaBrain (no mocks) |

---

## 15. AgentSkin UIX Requirements

### 15.1 Product & UX

| ID | Requirement | Priority |
|----|-------------|----------|
| AGS-FEAT-001 | Theme Gallery with preview images, search, filters, ratings | HIGH |
| AGS-FEAT-002 | One-Click Switching without page reload (300ms animation) | HIGH |
| AGS-FEAT-003 | Drag/Drop Install with validation | HIGH |
| AGS-FEAT-004 | Live Preview with split-screen or hover | HIGH |
| AGS-FEAT-005 | Import/Export & Sharing (JSON, QR) | MEDIUM |
| AGS-FEAT-006 | Remote Loading from HTTPS URLs | MEDIUM |
| AGS-FEAT-007 | Admin Controls for upload/approve/reject/delete (ADMIN mode only) | HIGH |
| AGS-FEAT-008 | Custom Palettes with WCAG AA contrast validation | MEDIUM |
| AGS-FEAT-009 | Notifications & Versions with changelog | LOW |
| AGS-FEAT-010 | Analytics for popularity, active users, switch frequency | LOW |
| AGS-FEAT-011 | Performance: Theme load <100ms p95, switch <50ms | HIGH |
| AGS-FEAT-012 | Responsiveness & Accessibility: WCAG AA, keyboard nav | HIGH |
| AGS-FEAT-013 | Required CSS Variables: 26 variables exactly as specified | HIGH |
| AGS-FEAT-014 | Animations: theme-switch keyframes, card hover lift | MEDIUM |

### 15.2 Frontend Architecture

| ID | Requirement | Priority |
|----|-------------|----------|
| AGS-FE-001 | Stack: Lit 3.x Web Components, vanilla CSS variables, no build step | HIGH |
| AGS-FE-002 | ThemeLoader SDK with loadLocal, loadRemote, validate, apply, use | HIGH |
| AGS-FE-003 | Lit Web Component with load/restore/apply/preview/upload/drag-drop | HIGH |
| AGS-FE-004 | Theme card dimensions 280×180, radius 12px | MEDIUM |

### 15.3 Backend & Data

| ID | Requirement | Priority |
|----|-------------|----------|
| AGS-BE-001 | API Surface: FastAPI router `/v1/skins` with list/get/upload/delete | HIGH |
| AGS-BE-002 | Storage: PostgreSQL `agent_skins` table with JSONB variables | HIGH |
| AGS-BE-003 | Validation: JSON schema on upload; reject invalid semver, `url()` values | HIGH |
| AGS-BE-004 | Multi-tenancy: Filter queries by tenant_id | HIGH |

### 15.4 Security

| ID | Requirement | Priority |
|----|-------------|----------|
| AGS-SEC-001 | Admin-Only Uploads via OPA (ADMIN mode only) | HIGH |
| AGS-SEC-002 | XSS Hardening: Reject `url()`, `<script>`, non-JSON | HIGH |
| AGS-SEC-003 | Tenant Isolation: All operations scoped by tenant_id | HIGH |
| AGS-SEC-004 | WCAG Enforcement: Contrast validation required | HIGH |

### 15.5 DevOps

| ID | Requirement | Priority |
|----|-------------|----------|
| AGS-OPS-001 | CDN/Caching: cache-control public, max-age 86400 | MEDIUM |
| AGS-OPS-002 | Observability: Prometheus counters/histograms for theme operations | HIGH |
| AGS-OPS-003 | Zero-Downtime: Themes persist in Postgres; rollback <60s | HIGH |
| AGS-OPS-004 | Backups: Daily `pg_dump` of agent_skins | HIGH |

### 15.6 QA

| ID | Requirement | Priority |
|----|-------------|----------|
| AGS-QA-001 | Unit Tests: ThemeLoader validation, XSS blocking, persistence | HIGH |
| AGS-QA-002 | Integration/E2E: Playwright flows for gallery, switch, drag/drop | HIGH |
| AGS-QA-003 | Performance & Accessibility: load <100ms, switch <50ms, WCAG AA | HIGH |

---

## 16. Settings Persistence Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| REQ-PERSIST-001 | Create `feature_flags` table with tenant_id, key, enabled, profile_override | HIGH |
| REQ-PERSIST-002 | Add `agent_config` section to `ui_settings` | MEDIUM |

---

## 17. Dependencies

- SomaBrain service running on port 9696
- SomaFractalMemory service running on port 9595
- Redis, PostgreSQL, Kafka infrastructure
- Valid `SA01_SOMA_BASE_URL` and `SA01_SOMA_API_KEY` configuration

---

## 18. References

- SomaBrain README: `somabrain/README.md`
- SomaFractalMemory README: `somafractalmemory/README.md`
- VIBE Coding Rules: `somaAgent01/VIBE_CODING_RULES.md`
- Steering Files: `somaAgent01/.kiro/steering/`

---

**Last Updated:** 2025-12-21  
**Maintained By:** Development Team

