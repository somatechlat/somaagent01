# SOMA COGNITIVE TRIAD — PROJECT CHARTER

## Document Control

| Field | Value |
|---|---|
| Document Title | Soma Cognitive Triad Project Charter |
| Document Identifier | SOMA-PM-CHARTER-001 |
| Version | 1.1.0 |
| Date | 2026-06-15 |
| Status | Approved |
| Author | SomaTech Engineering |
| Approver | — |
| Classification | Internal |
| ISO Reference | ISO 9001:2015 — Quality Management Systems — Requirements |
| Next Review | 2026-12-28 |

## Revision History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0.0 | 2026-06-15 | SomaTech Engineering | Initial project charter |
| 1.1.0 | 2026-06-15 | SomaTech Engineering | Corrected budget calculations; added normative references to ISO suite; added change control reference |

## Normative References

| Document | Identifier | Location |
|----------|------------|----------|
| Architecture (Agent) | SOMA-01-ARCH-001 | `docs/iso/SOMA-01-ARCH-001.md` |
| Architecture (Brain) | SOMA-BR-ARCH-001 | `somabrain/docs/iso/SOMA-BR-ARCH-001.md` |
| Architecture (SFM) | SOMA-SFM-ARCH-001 | `somafractalmemory/docs/iso/SOMA-SFM-ARCH-001.md` |
| Audit (Agent) | SOMA-01-AUDIT-002 | `docs/iso/SOMA-01-AUDIT-002.md` |
| Security (Agent) | SOMA-01-SEC-001 | `docs/iso/SOMA-01-SEC-001.md` |
| Risk Register (Agent) | SOMA-01-RISK-001 | `docs/iso/SOMA-01-RISK-001.md` |
| Quality Manual | SOMA-01-QMS-001 | `docs/iso/SOMA-01-QMS-001.md` |
| Production Readiness | SOMA-01-PROD-001 | `docs/iso/SOMA-01-PROD-001.md` |
| Compatibility Matrix | SOMA-01-COMPAT-001 | `docs/iso/SOMA-01-COMPAT-001.md` |
| AAAS Deployment | SOMA-01-AAAS-001 | `docs/iso/SOMA-01-AAAS-001.md` |
| Work Breakdown | SOMA-PM-WBS-001 | `docs/project/SOMA-PM-WBS-001.md` |
| Deliverables | SOMA-PM-DELIV-001 | `docs/project/SOMA-PM-DELIV-001.md` |
| Milestones | SOMA-PM-MILE-001 | `docs/project/SOMA-PM-MILE-001.md` |
| Communication | SOMA-PM-COMM-001 | `docs/project/SOMA-PM-COMM-001.md` |
| Change Control | SOMA-PM-CHANGE-001 | `docs/project/SOMA-PM-CHANGE-001.md` |

---

## 1. PROJECT OVERVIEW

### 1.1 Project Name
**Soma Cognitive Triad — Production Readiness Program**

### 1.2 Project Sponsor
SomaTech LAT — Engineering Leadership

### 1.3 Project Manager
SomaTech Engineering Team Lead

### 1.4 Project Purpose
Bring the Soma Cognitive Triad (SomaAgent01 + SomaBrain + SomaFractalMemory) from pre-production state to production-ready deployment, enabling single-click AAAS (Agent As A Service) deployment of complete cognitive AI agents.

### 1.5 Business Case
- **Market Need**: Enterprise customers need autonomous AI agents with persistent memory, cognitive reasoning, and multi-tenant isolation
- **Competitive Advantage**: The Soma Triad's biologically-inspired architecture (HRR vectors, neuromodulation, sleep consolidation) is unique in the market
- **Revenue Model**: AAAS subscription tiers (Starter, Pro, Enterprise) with per-tenant usage metering and plan limits

---

## 2. SCOPE

### 2.1 In Scope

| Component | Current State | Target State |
|-----------|--------------|--------------|
| SomaAgent01 | D+ (~45%), 15 tests, no CI/CD | Production ready, 70%+ test coverage, full CI/CD |
| SomaBrain | Late Beta (~75%), 95 tests | Production ready, documentation complete |
| SomaFractalMemory | Production Ready (v0.2.0) | Hardened, ML-grade embeddings |
| AAAS Deployment | Manual, fragmented | Single-click, version-matched |
| ISO Documentation | Created (v2.0.0) | Reviewed, maintained, audited |

### 2.2 Out of Scope
- New feature development (only production readiness)
- Frontend redesign (only fix blocking issues)
- Mobile applications
- Third-party SSO integrations beyond Keycloak

### 2.3 Constraints
- No FastAPI, no SQLAlchemy, no React (VIBE mandate)
- All tests require real infrastructure (no mocks)
- PostgreSQL only, Milvus only, Django Ninja only
- Three repos must remain independent but interoperable

### 2.4 Assumptions
- SomaBrain and SomaFractalMemory are maintained by their respective teams
- Keycloak is the identity provider for all environments
- Docker and K8s are the deployment targets
- Python 3.12 is the runtime standard

---

## 3. PROJECT PHASES

### 3.1 Phase Overview

```
PHASE 1: STABILIZE (Weeks 1-2)         ← Fix critical blockers
PHASE 2: SECURE (Weeks 3-4)            ← Close security gaps
PHASE 3: CONSOLIDATE (Weeks 5-7)       ← Unify architecture
PHASE 4: TEST (Weeks 8-10)             ← Build test coverage
PHASE 5: HARDEN (Weeks 11-13)          ← Infrastructure & K8s
PHASE 6: VALIDATE (Weeks 14-16)        ← Cross-repo integration
PHASE 7: RELEASE (Weeks 17-18)         ← Production deployment
```

### 3.2 Phase Details

#### PHASE 1: STABILIZE (Weeks 1-2) — June 16 – June 29, 2026

**Objective**: Fix all P0 blockers so the system can start and chat works end-to-end.

| Task ID | Task | Owner | Start | End | Deliverable |
|---------|------|-------|-------|-----|-------------|
| T1.1 | Fix `browser_use_monkeypatch` startup crash | Backend | Jun 16 | Jun 17 | App starts without crash |
| T1.2 | Commit Django migrations (admin/aaas, admin/core) | Backend | Jun 16 | Jun 16 | Migrations committed, tested |
| T1.3 | Fix permissions/api.py check endpoint stub | Security | Jun 17 | Jun 18 | /check calls real SpiceDB/OPA |
| T1.4 | Fix WebSocket routing (add agent_id resolution) | Frontend | Jun 18 | Jun 20 | Chat connects with agent_id |
| T1.5 | Fix frontend agent list (empty array bug) | Backend | Jun 18 | Jun 19 | /agents returns real data |
| T1.6 | Add agent selector to chat view | Frontend | Jun 20 | Jun 23 | User can select agent |
| T1.7 | Fix pyproject.toml somabrain path dependency | DevOps | Jun 16 | Jun 16 | Optional dep with graceful error |
| T1.8 | Fix BrainBridge URL fallback | Backend | Jun 17 | Jun 17 | Uses settings.SOMABRAIN_URL |
| T1.9 | Fix rate limiter Redis URL | Backend | Jun 17 | Jun 17 | Uses SA01_REDIS_URL |
| T1.10 | Verify standalone Docker deployment | DevOps | Jun 23 | Jun 25 | docker compose up -d works |
| T1.11 | Verify AAAS Docker deployment | DevOps | Jun 25 | Jun 27 | Full triad starts |
| T1.12 | Phase 1 gate review | PM | Jun 27 | Jun 29 | Gate report signed off |

**Phase 1 Exit Criteria**:
- App starts without crash
- Chat flow works end-to-end (WebSocket → V3 → LLM → Stream)
- Standalone and AAAS Docker deployments verified
- All P0 issues resolved

#### PHASE 2: SECURE (Weeks 3-4) — June 30 – July 13, 2026

**Objective**: Close all security gaps to enterprise standards.

| Task ID | Task | Owner | Start | End | Deliverable |
|---------|------|-------|-------|-----|-------------|
| T2.1 | Fix RoleRequired (401 → 403) | Security | Jun 30 | Jun 30 | Proper 403 responses |
| T2.2 | Move frontend JWT to httpOnly cookies | Frontend | Jun 30 | Jul 2 | No localStorage tokens |
| T2.3 | Fix MFA persistence | Backend | Jul 1 | Jul 3 | MFA endpoints functional |
| T2.4 | Fix registration (create real users) | Backend | Jul 3 | Jul 4 | Registration creates Keycloak user |
| T2.5 | Fix password reset flow | Backend | Jul 4 | Jul 7 | Reset emails sent, tokens validated |
| T2.6 | Add CSP headers middleware | Security | Jul 7 | Jul 8 | Content-Security-Policy active |
| T2.7 | Fix K8s hardcoded credentials | DevOps | Jul 8 | Jul 9 | Secrets from Vault/env |
| T2.8 | Add CSRF tokens to frontend fetch | Frontend | Jul 9 | Jul 10 | All mutations have CSRF |
| T2.9 | Fix OPA data path mismatch | Security | Jul 10 | Jul 11 | Client and Rego paths aligned |
| T2.10 | Security scan (Bandit -lll, Safety) | Security | Jul 11 | Jul 12 | Clean scan report |
| T2.11 | Phase 2 gate review | PM | Jul 12 | Jul 13 | Gate report signed off |

**Phase 2 Exit Criteria**:
- All auth features functional (login, register, MFA, reset, logout)
- No localStorage JWT tokens
- Security scan passes clean
- K8s manifests have no hardcoded secrets

#### PHASE 3: CONSOLIDATE (Weeks 5-7) — July 14 – August 3, 2026

**Objective**: Eliminate code duplication, unify architecture.

| Task ID | Task | Owner | Start | End | Deliverable |
|---------|------|-------|-------|-----|-------------|
| T3.1 | Adopt DeploymentMode singleton everywhere | Backend | Jul 14 | Jul 16 | All mode checks use DeploymentMode |
| T3.2 | Consolidate memory access (MemoryPort protocol) | Backend | Jul 16 | Jul 21 | Single memory interface |
| T3.3 | Unify SomaBrain HTTP endpoints | Backend | Jul 17 | Jul 19 | All clients use same paths |
| T3.4 | Wire conversation worker to V3 orchestrator | Backend | Jul 21 | Jul 24 | Single chat pipeline |
| T3.5 | Delete triplicated health/degradation code | Backend | Jul 24 | Jul 25 | Single HealthMonitor |
| T3.6 | Fix degradation API (calls real methods) | Backend | Jul 25 | Jul 28 | No 500s on degradation endpoints |
| T3.7 | Replace regex tool call extraction | Backend | Jul 28 | Jul 29 | Native LLM tool_calls format |
| T3.8 | Fix Pyright type errors (wave 1: top 10 files) | Backend | Jul 29 | Jul 31 | <500 Pyright errors |
| T3.9 | Tighten Ruff rules (remove B008, B904, F841 from ignore) | Backend | Jul 31 | Aug 1 | Stricter linting |
| T3.10 | Phase 3 gate review | PM | Aug 1 | Aug 3 | Gate report signed off |

**Phase 3 Exit Criteria**:
- Single chat pipeline (V3)
- Single memory interface (MemoryPort)
- Single deployment mode resolver
- Pyright errors < 500

#### PHASE 4: TEST (Weeks 8-10) — August 4 – August 24, 2026

**Objective**: Build comprehensive test coverage.

| Task ID | Task | Owner | Start | End | Deliverable |
|---------|------|-------|-------|-----|-------------|
| T4.1 | Set up CI pipeline (GitHub Actions) | DevOps | Aug 4 | Aug 6 | CI runs on every PR |
| T4.2 | Add pytest + Ruff + Pyright to CI | DevOps | Aug 6 | Aug 7 | CI gates active |
| T4.3 | Write chat orchestrator unit tests | QA | Aug 7 | Aug 11 | 12-phase pipeline tested |
| T4.4 | Write auth flow integration tests | QA | Aug 11 | Aug 14 | Login/register/MFA tested |
| T4.5 | Write WebSocket consumer tests | QA | Aug 14 | Aug 18 | WS connect/chat/disconnect |
| T4.6 | Write permissions integration tests | QA | Aug 18 | Aug 19 | UnifiedGate + SpiceDB + OPA |
| T4.7 | Write cross-repo integration tests | QA | Aug 19 | Aug 21 | Agent→Brain→Memory flow |
| T4.8 | Add contract tests (Pact or similar) | QA | Aug 21 | Aug 22 | API compatibility verified |
| T4.9 | Achieve 50%+ test coverage | QA | Aug 4 | Aug 24 | Coverage report |
| T4.10 | Phase 4 gate review | PM | Aug 22 | Aug 24 | Gate report signed off |

**Phase 4 Exit Criteria**:
- CI pipeline green on every PR
- 50%+ line coverage for somaAgent01
- All critical paths tested
- Contract tests verify cross-repo compatibility

#### PHASE 5: HARDEN (Weeks 11-13) — August 25 – September 14, 2026

**Objective**: Production-grade infrastructure and deployment.

| Task ID | Task | Owner | Start | End | Deliverable |
|---------|------|-------|-------|-----|-------------|
| T5.1 | Complete K8s manifests (probes, limits, HPA, PDB) | DevOps | Aug 25 | Aug 29 | Production-grade K8s |
| T5.2 | Add NetworkPolicies to K8s | DevOps | Aug 29 | Sep 1 | Network isolation |
| T5.3 | Unify docker-compose (root with profiles) | DevOps | Sep 1 | Sep 3 | Single compose file |
| T5.4 | Fix Makefile (correct Dockerfile paths) | DevOps | Sep 3 | Sep 4 | make build/up/down/test work |
| T5.5 | Add Prometheus ServiceMonitor manifests | DevOps | Sep 4 | Sep 5 | Metrics scraped |
| T5.6 | Add Grafana dashboard configs | DevOps | Sep 5 | Sep 8 | Dashboards as code |
| T5.7 | Wire audit logging to auth endpoints | Backend | Sep 8 | Sep 10 | All auth events audited |
| T5.8 | Add backup/restore procedures | DevOps | Sep 10 | Sep 12 | Documented, tested |
| T5.9 | Load testing (chat endpoint) | QA | Sep 12 | Sep 14 | Performance baseline |
| T5.10 | Phase 5 gate review | PM | Sep 14 | Sep 14 | Gate report signed off |

**Phase 5 Exit Criteria**:
- K8s manifests production-ready
- Monitoring and alerting configured
- Backup/restore documented and tested
- Performance baseline established

#### PHASE 6: VALIDATE (Weeks 14-16) — September 15 – October 5, 2026

**Objective**: Cross-repo integration validation and documentation finalization.

| Task ID | Task | Owner | Start | End | Deliverable |
|---------|------|-------|-------|-----|-------------|
| T6.1 | Full AAAS integration test (3 repos) | QA | Sep 15 | Sep 18 | End-to-end cognitive agent |
| T6.2 | Version compatibility matrix validation | QA | Sep 18 | Sep 19 | COMPAT doc verified |
| T6.3 | Single-click deploy validation | DevOps | Sep 19 | Sep 22 | AAAS deploy works |
| T6.4 | Documentation audit (all 3 repos) | PM | Sep 22 | Sep 24 | Docs match code |
| T6.5 | ISO documentation review cycle | PM | Sep 24 | Sep 26 | All ISO docs reviewed |
| T6.6 | Security penetration test | Security | Sep 26 | Sep 30 | Pentest report clean |
| T6.7 | Disaster recovery drill | DevOps | Sep 30 | Oct 2 | DR procedures validated |
| T6.8 | User acceptance testing | QA | Oct 2 | Oct 5 | UAT signed off |
| T6.9 | Phase 6 gate review | PM | Oct 5 | Oct 5 | Gate report signed off |

**Phase 6 Exit Criteria**:
- Full AAAS stack tested end-to-end
- Single-click deployment verified
- Security pentest passed
- DR drill successful
- UAT signed off

#### PHASE 7: RELEASE (Weeks 17-18) — October 6 – October 19, 2026

**Objective**: Production release and handover.

| Task ID | Task | Owner | Start | End | Deliverable |
|---------|------|-------|-------|-----|-------------|
| T7.1 | Release candidate tagging | DevOps | Oct 6 | Oct 7 | RC images published |
| T7.2 | Production deployment dry run | DevOps | Oct 7 | Oct 9 | Dry run successful |
| T7.3 | Production deployment | DevOps | Oct 9 | Oct 10 | Production live |
| T7.4 | Post-deployment monitoring (72h) | Ops | Oct 10 | Oct 13 | No critical incidents |
| T7.5 | Operations runbook finalization | Ops | Oct 13 | Oct 15 | Runbook complete |
| T7.6 | Team training | PM | Oct 15 | Oct 17 | Ops team trained |
| T7.7 | Project closure | PM | Oct 17 | Oct 19 | Lessons learned, closure report |

**Phase 7 Exit Criteria**:
- Production deployment successful
- 72h monitoring clean
- Operations team trained
- Project closed

---

## 4. ROLES AND RESPONSIBILITIES

| Role | Responsibility | RACI |
|------|---------------|------|
| Project Manager | Planning, tracking, gate reviews, stakeholder communication | Accountable |
| Backend Lead | Python/Django development, API, orchestrator | Responsible |
| Frontend Lead | Lit/TypeScript, WebSocket, UI components | Responsible |
| Security Lead | Auth, authorization, security scanning | Responsible |
| DevOps Lead | Docker, K8s, CI/CD, infrastructure | Responsible |
| QA Lead | Test strategy, test execution, coverage | Responsible |
| SomaBrain Team | Brain repo changes, integration support | Consulted |
| SFM Team | Memory repo changes, integration support | Consulted |
| Engineering Director | Budget, escalation, go/no-go decisions | Informed |

---

## 5. RISKS

| ID | Risk | Probability | Impact | Score | Mitigation |
|----|------|-------------|--------|-------|------------|
| R1 | SomaBrain changes break Agent integration | 3 | 5 | 15 | Contract tests, compatibility matrix |
| R2 | Test infrastructure flakiness | 4 | 3 | 12 | Docker-based test infra, retry policies |
| R3 | Scope creep (new features during readiness) | 3 | 4 | 12 | Strict scope control, change board |
| R4 | Key staff unavailability | 2 | 5 | 10 | Cross-training, documentation |
| R5 | Security vulnerabilities discovered late | 2 | 5 | 10 | Early security scanning in CI |
| R6 | K8s environment differences | 3 | 3 | 9 | Tilt for local K8s, staging environment |
| R7 | Milvus scaling issues | 2 | 4 | 8 | Load testing, capacity planning |
| R8 | Documentation drift | 3 | 3 | 9 | ISO doc review in Phase 6 |

---

## 6. BUDGET

### 6.1 Engineering Effort

| Metric | Value | Calculation |
|--------|-------|-------------|
| Duration | 18 weeks | Jun 16 – Oct 19, 2026 |
| Core team | 5 engineers | Backend, Frontend, Security, DevOps, QA |
| Hours per engineer per week | 40 | Standard |
| Total person-hours | **3,600** | 18 weeks × 5 engineers × 40 hours |
| Critical path hours (WBS) | 750 | Per SOMA-PM-WBS-001 (lead engineer tasks) |
| Parallel work capacity | 4.8x | 3,600 / 750 (allows parallel execution) |

### 6.2 Cost Breakdown

| Category | Estimate | Notes |
|----------|----------|-------|
| Engineering (5 engineers × 18 weeks) | 3,600 person-hours | Core team, all phases |
| SomaBrain integration support | 160 person-hours | Per SOMA-BR-EXEC-001 |
| SFM integration support | 120 person-hours | Per SOMA-SFM-EXEC-001 |
| Infrastructure (dev/staging/prod) | TBD | Cloud costs per environment |
| External security audit | TBD | Penetration testing (Phase 6) |
| Training | 16 person-hours | Operations team handover |

### 6.3 Phase Effort Distribution

| Phase | Weeks | Engineer-Hours | % of Total |
|-------|-------|---------------|------------|
| 1. Stabilize | 2 | 400 | 11% |
| 2. Secure | 2 | 400 | 11% |
| 3. Consolidate | 3 | 600 | 17% |
| 4. Test | 3 | 600 | 17% |
| 5. Harden | 3 | 600 | 17% |
| 6. Validate | 3 | 600 | 17% |
| 7. Release | 2 | 400 | 11% |
| **TOTAL** | **18** | **3,600** | **100%** |

---

## 7. COMMUNICATION PLAN

| Event | Frequency | Participants | Medium |
|-------|-----------|-------------|--------|
| Daily standup | Daily | Core team | Video call |
| Sprint review | Bi-weekly | Core team + stakeholders | Video call |
| Gate review | End of each phase | PM + leads + sponsor | Document + meeting |
| Stakeholder update | Monthly | Sponsor + directors | Written report |
| Risk review | Bi-weekly | PM + leads | Risk register update |

---

## 8. APPROVAL

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Project Sponsor | | | |
| Project Manager | | | |
| Backend Lead | | | |
| Security Lead | | | |
| DevOps Lead | | | |

---

End of Document
