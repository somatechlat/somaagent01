# SOMA-01-RISK-001 — Risk Register

## Document Control

| Field | Value |
|---|---|
| Document Title | SomaAgent01 Risk Register |
| Document Identifier | SOMA-01-RISK-001 |
| Version | 2.0.0 |
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

| 2.0.0 | 2026-09-28 | SomaTech Engineering | Brought under ISO document control. Prior status value `Active` is outside the closed set `Draft \| In Review \| Approved \| Obsolete`; normalised to `Draft` — no approver has signed this document. |
| 1.0.0 | 2025-12-30 | SomaTech Engineering | Initial risk register |
| 1.1.0 | 2026-06-01 | SomaTech Engineering | Updated risk assessments post-initial audit |
| 2.0.0 | 2026-06-15 | SomaTech Engineering | Code-verified deep analysis; updated risk scores based on verified fixes and remaining issues |

---

## 1. Risk Assessment Methodology

### 1.1 Scoring Matrix

**Probability (P):**

| Score | Label | Description |
|-------|-------|-------------|
| 1 | Rare | May occur only in exceptional circumstances |
| 2 | Unlikely | Could occur at some time |
| 3 | Possible | Might occur at some time |
| 4 | Likely | Will probably occur in most circumstances |
| 5 | Certain | Expected to occur in most circumstances |

**Impact (I):**

| Score | Label | Description |
|-------|-------|-------------|
| 1 | Insignificant | Negligible impact |
| 2 | Minor | Some impact; manageable |
| 3 | Moderate | Significant impact; requires management attention |
| 4 | Major | Serious impact; senior management attention needed |
| 5 | Catastrophic | Critical impact; threatens project viability |

**Risk Score** = Probability × Impact

| Score Range | Rating | Action |
|-------------|--------|--------|
| 20–25 | Critical | Immediate action required |
| 12–19 | High | Action required within 2 weeks |
| 6–11 | Medium | Action required within 1 month |
| 1–5 | Low | Monitor and review quarterly |

---

## 2. Risk Register

| ID | Description | Category | P | I | Score | Rating | Mitigation | Status |
|----|-------------|----------|---|---|-------|--------|------------|--------|
| R-001 | Authorization bypass in `permissions/api.py:336` returns `allowed:true` unconditionally, allowing unauthorized access to protected resources | Security | 5 | 5 | 25 | Critical | Wire endpoint to `UnifiedGate` for real OPA + SpiceDB authorization check | **Open** |
| R-002 | WebSocket chat flow broken: frontend omits `agent_id` required by backend consumer (`consumers/chat.py:136`), making real-time chat non-functional | Functionality | 5 | 5 | 25 | Critical | Update `websocket-client.ts` to include `agent_id`; add agent selector to chat view | **Open** |
| R-003 | Django migrations out of sync for `admin/aaas` and `admin/core`, causing deployment failures and potential data integrity issues | Data Integrity | 4 | 5 | 20 | Critical | Run `makemigrations`, verify generated migrations, commit migration files | **Open** |
| R-004 | Zero CI/CD pipelines (no `.github/workflows/`): no automated testing, security scanning, or deployment, allowing regressions to reach production undetected | Process | 5 | 4 | 20 | Critical | Create GitHub Actions for lint, test, build, and security scanning | **Open** |
| R-005 | Test coverage at 2.8% (15 test files / 528+ source files): insufficient verification of security-critical code paths | Quality | 4 | 4 | 16 | High | Prioritize integration tests for auth, chat orchestrator, rate limiter, UnifiedGate | **Open** |
| R-006 | `pyproject.toml:21` references `somabrain` as `../somabrain` path dependency: non-portable; CI/CD and Docker builds will fail | Build | 4 | 4 | 16 | High | Publish to private PyPI or use Git dependency URL; make import conditional for Standalone | **Open** |
| R-007 | `RoleRequired` in `auth.py:277` returns HTTP 401 instead of 403: clients cannot distinguish authentication failure from authorization denial | Security | 4 | 3 | 12 | High | Return explicit 403 when user is authenticated but lacks required role | **Open** |
| R-008 | Conversation-worker uses separate use-case pipeline bypassing V3 orchestrator: inconsistent chat behavior between WebSocket/REST and Kafka paths | Architecture | 3 | 4 | 12 | High | Consolidate conversation-worker to use V3 orchestrator | **Open** |
| R-009 | 9+ memory entry points being consolidated via `MemoryPort` protocol: fragmented memory access increases bug surface and maintenance cost | Architecture | 3 | 3 | 9 | Medium | Adopt `MemoryPort` in all production adapters; deprecate direct HTTP calls | **In Progress** |
| R-010 | `brain.py:92` falls back to hardcoded Docker hostname `somastack_aaas:9696`: fails outside specific Docker Compose setup | Portability | 3 | 3 | 9 | Medium | Use environment variable resolution with no hardcoded fallback | **Open** |
| R-011 | `rate_limiter.py:67` uses `REDIS_URL` instead of canonical `SA01_REDIS_URL`: environment variable inconsistency may cause connection failures | Configuration | 3 | 3 | 9 | Medium | Standardize on `SA01_REDIS_URL` across all modules | **Open** |
| R-012 | `chat_orchestrator.py:750` uses regex-based tool call extraction: fragile parsing may break with LLM response format changes | Reliability | 3 | 3 | 9 | Medium | Use structured function-calling output format instead of regex | **Open** |
| R-013 | Audit outbox publisher not wired to all endpoints: incomplete audit trail for compliance and incident investigation | Compliance | 3 | 3 | 9 | Medium | Wire `OutboxMessage` publishing to all API endpoints | **Open** |
| R-014 | No TLS enforcement at application layer: assumes reverse proxy TLS termination; misconfiguration exposes data in transit | Security | 2 | 4 | 8 | Medium | Document TLS requirements; add TLS redirect middleware as defense-in-depth | **Open** |
| R-015 | No dependency vulnerability scanning: third-party package vulnerabilities may go undetected | Security | 3 | 3 | 9 | Medium | Add `pip-audit` or `safety` to CI/CD pipeline | **Open** |
| R-016 | 1,402 Pyright type errors: type safety issues may mask runtime bugs | Quality | 2 | 2 | 4 | Low | Address type errors incrementally; add pyright to CI/CD | **Open** |
| R-017 | K8s manifests incomplete: cannot deploy to Kubernetes in production | Infrastructure | 2 | 3 | 6 | Medium | Complete K8s manifests with health probes, resource limits, network policies | **Open** |
| R-018 | No data retention or deletion policies: potential regulatory non-compliance (GDPR, CCPA) | Compliance | 2 | 4 | 8 | Medium | Implement data retention policies; add deletion endpoints | **Open** |

---

## 3. Risk Trend Analysis

| Category | Previous Score (v1.1) | Current Score (v2.0) | Trend |
|----------|----------------------|---------------------|-------|
| Security (top risk) | 25 (hardcoded SECRET_KEY) | 25 (authorization bypass) | → Stable (different risk) |
| Functionality | 25 (NotImplementedError) | 25 (WebSocket routing) | → Stable (different risk) |
| Data Integrity | 20 (SQLite fallback) | 20 (migrations out of sync) | → Stable (different risk) |
| Process | 20 (no CI/CD) | 20 (no CI/CD) | → Stable |
| Quality | 25 (mock-based tests) | 16 (low coverage) | ↓ Improved (mocks addressed) |

**Summary:** Several high-severity risks from the v1.1 audit have been resolved (hardcoded secret key, SQLite fallback, NotImplementedError). New risks have emerged of similar severity (authorization bypass, WebSocket routing, migration sync). Overall risk profile has shifted but not significantly improved in aggregate.

---

## 4. Risk Ownership

| ID | Owner | Review Frequency |
|----|-------|-----------------|
| R-001 | Backend Security | Weekly |
| R-002 | Frontend + Backend | Weekly |
| R-003 | Backend | Weekly |
| R-004 | DevOps | Bi-weekly |
| R-005 | QA + Backend | Monthly |
| R-006 | DevOps | Monthly |
| R-007 | Backend | Monthly |
| R-008 | Architecture | Monthly |
| R-009–R-018 | Engineering | Monthly |

---

## 5. Residual Risk Acceptance

No risks have been formally accepted. All Critical and High risks require mitigation before production deployment. Medium risks should be addressed within the 12-week production readiness roadmap (see SOMA-01-PROD-001).

---

End of Document
