# SOMA-01-PROD-001 — Production Readiness Assessment

## Document Control

| Field | Value |
|---|---|
| Document Title | SomaAgent01 Production Readiness Assessment |
| Document Identifier | SOMA-01-PROD-001 |
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
| 1.0.0 | 2025-12-30 | SomaTech Engineering | Initial assessment |
| 1.1.0 | 2026-06-01 | SomaTech Engineering | Updated with initial remediation results |
| 2.0.0 | 2026-06-15 | SomaTech Engineering | Code-verified deep analysis; updated scorecard; added 12-week roadmap |

---

## 1. Executive Summary

SomaAgent01 is **NOT production-ready**. The system scores approximately 45% (D+) overall against production readiness criteria. Three P0 critical issues must be resolved before any production deployment, and the 12-week roadmap below addresses all remaining gaps.

**Production Gate Status: BLOCKED**

---

## 2. Production Readiness Scorecard

| Domain | Weight | Score | Weighted | Gate Status |
|--------|--------|-------|----------|-------------|
| Security | 25% | 60% (C+) | 15.0% | **BLOCKED** — Authorization bypass (P0-001) |
| Reliability | 20% | 35% (D) | 7.0% | **BLOCKED** — WebSocket broken (P0-002) |
| Scalability | 15% | 45% (D+) | 6.8% | FAIL — No load testing; single-instance only |
| Observability | 10% | 40% (C-) | 4.0% | FAIL — Prometheus/Grafana partially wired; no alerting |
| Testing | 15% | 25% (D) | 3.8% | **BLOCKED** — 2.8% coverage; no CI/CD |
| Deployment | 10% | 50% (C) | 5.0% | FAIL — Docker configs exist; K8s incomplete; migrations out of sync |
| Documentation | 5% | 70% (B-) | 3.5% | PASS — ISO documentation suite created |
| **Total** | **100%** | — | **45.0%** | **NOT READY** |

---

## 3. Gate Criteria

### 3.1 Mandatory Gates (Must Pass for Production)

| Gate ID | Criterion | Status | Blocker |
|---------|-----------|--------|---------|
| GATE-01 | No P0 security vulnerabilities | **FAIL** | P0-001: Authorization bypass |
| GATE-02 | Core user flows functional | **FAIL** | P0-002: WebSocket routing broken |
| GATE-03 | Database migrations in sync | **FAIL** | P0-003: Migrations out of sync |
| GATE-04 | CI/CD pipeline operational | **FAIL** | No `.github/workflows/` |
| GATE-05 | Test coverage ≥ 40% | **FAIL** | Currently 2.8% |
| GATE-06 | All security controls implemented | **FAIL** | Permissions API bypass |
| GATE-07 | No hardcoded secrets or credentials | **PASS** | SECRET_KEY hardened; bypass removed |
| GATE-08 | Rate limiting operational | **PASS** | Fail-closed implementation verified |
| GATE-09 | Authorization engine operational | **PASS** | UnifiedGate with real OPA/SpiceDB |
| GATE-10 | Health checks operational | **PASS** | Health monitor implemented |

### 3.2 Recommended Gates (Should Pass)

| Gate ID | Criterion | Status |
|---------|-----------|--------|
| GATE-11 | K8s deployment manifests complete | FAIL |
| GATE-12 | Load testing completed | FAIL |
| GATE-13 | Disaster recovery plan documented | FAIL |
| GATE-14 | Runbook for common incidents | FAIL |
| GATE-15 | Dependency vulnerability scanning | FAIL |
| GATE-16 | Audit logging wired to all endpoints | Partial |
| GATE-17 | TLS enforced at all layers | Partial |
| GATE-18 | Data retention policies implemented | FAIL |

---

## 4. Twelve-Week Production Readiness Roadmap

### Phase 1: Critical Fixes (Weeks 1–2)

| Week | Task | Owner | Deliverable | Gate |
|------|------|-------|-------------|------|
| 1 | Fix authorization bypass in `permissions/api.py:336` | Backend | Wire endpoint to UnifiedGate | GATE-01 |
| 1 | Fix WebSocket routing: add `agent_id` to frontend | Frontend | Updated `websocket-client.ts` + agent selector | GATE-02 |
| 1 | Generate and commit Django migrations | Backend | Migration files for `admin/aaas` + `admin/core` | GATE-03 |
| 2 | Fix `RoleRequired` to return 403 | Backend | Updated `auth.py:277` | — |
| 2 | Remove hardcoded hostname in `brain.py:92` | Backend | Environment variable resolution | — |
| 2 | Fix Redis env var inconsistency (`rate_limiter.py:67`) | Backend | Use `SA01_REDIS_URL` | — |

### Phase 2: CI/CD and Testing Foundation (Weeks 3–4)

| Week | Task | Owner | Deliverable | Gate |
|------|------|-------|-------------|------|
| 3 | Create GitHub Actions: lint (ruff + pyright) | DevOps | `.github/workflows/lint.yml` | GATE-04 |
| 3 | Create GitHub Actions: test (pytest) | DevOps | `.github/workflows/test.yml` | GATE-04 |
| 3 | Create GitHub Actions: build (Docker) | DevOps | `.github/workflows/build.yml` | GATE-04 |
| 4 | Add security scanning (bandit, pip-audit) | DevOps | Security workflow | GATE-04 |
| 4 | Write integration tests: auth flow | QA | `tests/integration/test_auth_flow.py` | GATE-05 |
| 4 | Write integration tests: chat orchestrator V3 | QA | `tests/integration/test_v3_orchestrator.py` | GATE-05 |

### Phase 3: Test Coverage and Build Fixes (Weeks 5–6)

| Week | Task | Owner | Deliverable | Gate |
|------|------|-------|-------------|------|
| 5 | Write integration tests: rate limiter | QA | `tests/integration/test_rate_limiter.py` | GATE-05 |
| 5 | Write integration tests: UnifiedGate | QA | `tests/integration/test_unified_gate.py` | GATE-05 |
| 5 | Write integration tests: WebSocket consumer | QA | `tests/integration/test_websocket.py` | GATE-05 |
| 6 | Fix `pyproject.toml` somabrain dependency | DevOps | Private PyPI or Git dependency | — |
| 6 | Write integration tests: memory adapters | QA | `tests/integration/test_memory.py` | GATE-05 |
| 6 | Achieve 40% test coverage milestone | QA | Coverage report | GATE-05 |

### Phase 4: Architecture Consolidation (Weeks 7–8)

| Week | Task | Owner | Deliverable | Gate |
|------|------|-------|-------------|------|
| 7 | Consolidate conversation-worker with V3 orchestrator | Backend | Single pipeline for all chat paths | — |
| 7 | Replace regex tool call extraction with structured output | Backend | Updated `chat_orchestrator.py:750` | — |
| 8 | Wire audit outbox to all API endpoints | Backend | OutboxMessage publishing | — |
| 8 | Adopt MemoryPort in production adapters | Backend | Unified memory access | — |

### Phase 5: Infrastructure and Deployment (Weeks 9–10)

| Week | Task | Owner | Deliverable | Gate |
|------|------|-------|-------------|------|
| 9 | Complete K8s manifests (health probes, resources, network policies) | DevOps | Updated `infra/k8s/` | GATE-11 |
| 9 | Add environment isolation (dev/staging/prod) | DevOps | Environment configs | — |
| 10 | Document TLS requirements and verify reverse proxy config | DevOps | TLS documentation | — |
| 10 | Implement data retention policies | Backend | Retention configuration | GATE-18 |

### Phase 6: Hardening and Validation (Weeks 11–12)

| Week | Task | Owner | Deliverable | Gate |
|------|------|-------|-------------|------|
| 11 | Load testing with target concurrency | QA | Load test report | GATE-12 |
| 11 | Document incident response runbook | DevOps | Runbook document | GATE-14 |
| 12 | Disaster recovery plan and backup procedures | DevOps | DR documentation | GATE-13 |
| 12 | Final production readiness review | All | Updated scorecard | ALL GATES |

---

## 5. Cross-Repo Dependencies

### 5.1 SomaBrain

| Aspect | Detail |
|--------|--------|
| Repository | `../somabrain` (sibling directory) |
| Package | `somabrain` Python package |
| Integration | `aaas/brain.py` (direct) + `admin/core/somabrain_client.py` (HTTP) |
| Port | 63996 (AAAS) / 9696 (direct) |
| Blocking Issue | `pyproject.toml:21` references as path dependency |
| Required Action | Publish to private PyPI; make import conditional for Standalone mode |

### 5.2 SomaFractalMemory

| Aspect | Detail |
|--------|--------|
| Repository | `../somafractalmemory` (sibling directory) |
| Integration | `services/common/adapters/` (HTTP) |
| Port | 63901 (AAAS) / 10101 (direct) |
| Blocking Issue | None (HTTP-only integration) |
| Required Action | Document API contract; verify adapter implementation |

### 5.3 Infrastructure Dependencies

| Dependency | Version | Mode | Status |
|-----------|---------|------|--------|
| PostgreSQL | 16 | Both | Required |
| Redis | 7 | Both | Required |
| Keycloak | 24 | Both | Required |
| Kafka | 3.7 (KRaft) | AAAS (optional Standalone) | Optional |
| Milvus | 2.3 | Both | Required for vector storage |
| SpiceDB | 1.29 | Both | Schema defined; runtime integration verified |
| OPA | Latest | Both | Policies defined; runtime integration verified |
| HashiCorp Vault | Latest | Both | Optional |

---

## 6. Risk Summary for Production Decision

| Risk | Impact on Production Readiness |
|------|-------------------------------|
| Authorization bypass (P0-001) | **Blocks production** |
| WebSocket broken (P0-002) | **Blocks production** for chat features |
| Migrations out of sync (P0-003) | **Blocks deployment** |
| No CI/CD (P1-001) | Blocks safe production operations |
| 2.8% test coverage (P1-002) | Blocks confidence in changes |
| Path dependency (P1-003) | Blocks CI/CD and Docker builds |

**Recommendation:** Do not proceed to production until all P0 issues are resolved (estimated: Week 2) and CI/CD with ≥40% test coverage is achieved (estimated: Week 6). Full production readiness is estimated at Week 12.

---

End of Document
