# SOMA COGNITIVE TRIAD — RACI MATRIX

## Document Control

| Field | Value |
|---|---|
| Document Title | RACI Matrix (Responsible, Accountable, Consulted, Informed) |
| Document Identifier | SOMA-PM-RACI-001 |
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
|---|---|---|---|
| 1.0.0 | 2026-09-28 | SomaTech Engineering | Brought under ISO document control: Document Control block normalised and this Revision History added. |

## 1. KEY

| Letter | Role | Meaning |
|--------|------|---------|
| **R** | Responsible | Does the work |
| **A** | Accountable | Ultimately answerable (one per task) |
| **C** | Consulted | Provides input before work |
| **I** | Informed | Notified after completion |

---

## 2. TEAM ROLES

| Code | Role | Repository Focus |
|------|------|-----------------|
| PM | Project Manager | All three |
| BL | Backend Lead | somaAgent01 |
| FL | Frontend Lead | somaAgent01 |
| SL | Security Lead | All three |
| DL | DevOps Lead | All three |
| QL | QA Lead | All three |
| BT | SomaBrain Team | somabrain |
| ST | SFM Team | somafractalmemory |
| ED | Engineering Director | All three |

---

## 3. RACI BY PHASE

### Phase 1: STABILIZE

| Task | PM | BL | FL | SL | DL | QL | BT | ST | ED |
|------|----|----|----|----|----|----|----|----|----|
| T1.1 Fix startup crash | I | **R/A** | I | I | C | I | — | — | I |
| T1.2 Commit migrations | I | **R/A** | I | I | C | I | — | — | I |
| T1.3 Fix permissions stub | I | C | I | **R/A** | I | I | — | — | I |
| T1.4 Fix WebSocket routing | I | C | **R/A** | I | I | I | — | — | I |
| T1.5 Fix agent list | I | **R/A** | C | I | I | I | — | — | I |
| T1.6 Add agent selector | I | C | **R/A** | I | I | I | — | — | I |
| T1.7 Fix path dependency | I | C | I | I | **R/A** | I | C | — | I |
| T1.8 Fix BrainBridge URL | I | **R/A** | I | I | C | I | C | — | I |
| T1.9 Fix rate limiter URL | I | **R/A** | I | I | I | I | — | — | I |
| T1.10 Standalone Docker | I | C | I | I | **R/A** | C | — | C | I |
| T1.11 AAAS Docker | I | C | I | I | **R/A** | C | C | C | I |
| T1.12 Phase 1 gate | **A** | R | R | R | R | R | C | C | I |

### Phase 2: SECURE

| Task | PM | BL | FL | SL | DL | QL | BT | ST | ED |
|------|----|----|----|----|----|----|----|----|----|
| T2.1 Fix RoleRequired | I | C | I | **R/A** | I | I | — | — | I |
| T2.2 httpOnly cookies | I | C | **R/A** | C | I | I | — | — | I |
| T2.3 Fix MFA | I | **R/A** | I | C | I | I | — | — | I |
| T2.4 Fix registration | I | **R/A** | I | C | I | I | — | — | I |
| T2.5 Fix password reset | I | **R/A** | I | C | I | I | — | — | I |
| T2.6 CSP headers | I | C | C | **R/A** | I | I | — | — | I |
| T2.7 K8s credentials | I | I | I | C | **R/A** | I | — | — | I |
| T2.8 CSRF tokens | I | C | **R/A** | C | I | I | — | — | I |
| T2.9 OPA data path | I | I | I | **R/A** | I | I | C | — | I |
| T2.10 Security scan | I | I | I | **R/A** | C | C | — | — | I |
| T2.11 Phase 2 gate | **A** | R | R | R | R | R | C | C | I |

### Phase 3: CONSOLIDATE

| Task | PM | BL | FL | SL | DL | QL | BT | ST | ED |
|------|----|----|----|----|----|----|----|----|----|
| T3.1 DeploymentMode | I | **R/A** | I | I | I | I | — | — | I |
| T3.2 MemoryPort | I | **R/A** | I | I | I | C | C | C | I |
| T3.3 Unify Brain endpoints | I | **R/A** | I | I | I | I | C | — | I |
| T3.4 Wire worker to V3 | I | **R/A** | I | I | I | C | — | — | I |
| T3.5 Delete duplicates | I | **R/A** | I | I | I | C | — | — | I |
| T3.6 Fix degradation API | I | **R/A** | I | I | I | I | — | — | I |
| T3.7 Tool call extraction | I | **R/A** | I | I | I | I | — | — | I |
| T3.8 Pyright errors | I | **R/A** | I | I | I | C | — | — | I |
| T3.9 Tighten Ruff | I | **R/A** | I | I | I | C | — | — | I |
| T3.10 Phase 3 gate | **A** | R | R | R | R | R | C | C | I |

### Phase 4: TEST

| Task | PM | BL | FL | SL | DL | QL | BT | ST | ED |
|------|----|----|----|----|----|----|----|----|----|
| T4.1 CI pipeline | I | C | C | C | **R/A** | C | — | — | I |
| T4.2 CI gates | I | C | C | C | **R/A** | C | — | — | I |
| T4.3 Orchestrator tests | I | C | I | I | I | **R/A** | — | — | I |
| T4.4 Auth tests | I | C | I | C | I | **R/A** | — | — | I |
| T4.5 WebSocket tests | I | C | C | I | I | **R/A** | — | — | I |
| T4.6 Permissions tests | I | C | I | C | I | **R/A** | — | — | I |
| T4.7 Cross-repo tests | I | C | I | I | C | **R/A** | C | C | I |
| T4.8 Contract tests | I | C | I | I | C | **R/A** | C | C | I |
| T4.9 Coverage target | I | C | C | I | I | **R/A** | — | — | I |
| T4.10 Phase 4 gate | **A** | R | R | R | R | R | C | C | I |

### Phase 5: HARDEN

| Task | PM | BL | FL | SL | DL | QL | BT | ST | ED |
|------|----|----|----|----|----|----|----|----|----|
| T5.1 K8s manifests | I | C | I | C | **R/A** | I | C | C | I |
| T5.2 NetworkPolicies | I | I | I | C | **R/A** | I | — | — | I |
| T5.3 Unify docker-compose | I | C | I | I | **R/A** | I | — | — | I |
| T5.4 Fix Makefile | I | C | I | I | **R/A** | I | — | — | I |
| T5.5 ServiceMonitor | I | I | I | I | **R/A** | I | — | — | I |
| T5.6 Grafana dashboards | I | C | I | I | **R/A** | I | — | — | I |
| T5.7 Wire audit logging | I | **R/A** | I | C | I | I | — | — | I |
| T5.8 Backup procedures | I | C | I | I | **R/A** | I | — | C | I |
| T5.9 Load testing | I | C | I | I | C | **R/A** | C | C | I |
| T5.10 Phase 5 gate | **A** | R | R | R | R | R | C | C | I |

### Phase 6: VALIDATE

| Task | PM | BL | FL | SL | DL | QL | BT | ST | ED |
|------|----|----|----|----|----|----|----|----|----|
| T6.1 AAAS E2E test | I | C | C | C | C | **R/A** | C | C | I |
| T6.2 COMPAT validation | I | C | I | I | I | **R/A** | C | C | I |
| T6.3 Deploy validation | I | C | I | I | **R/A** | C | C | C | I |
| T6.4 Doc audit | **R/A** | C | C | C | C | C | C | C | I |
| T6.5 ISO review | **R/A** | C | C | C | C | C | C | C | I |
| T6.6 Pentest | I | I | I | **R/A** | C | C | — | — | I |
| T6.7 DR drill | I | C | I | I | **R/A** | C | C | C | I |
| T6.8 UAT | I | C | C | C | C | **R/A** | C | C | I |
| T6.9 Phase 6 gate | **A** | R | R | R | R | R | C | C | I |

### Phase 7: RELEASE

| Task | PM | BL | FL | SL | DL | QL | BT | ST | ED |
|------|----|----|----|----|----|----|----|----|----|
| T7.1 RC tagging | I | C | C | I | **R/A** | C | C | C | I |
| T7.2 Prod dry run | I | C | C | C | **R/A** | C | C | C | I |
| T7.3 Prod deployment | I | C | C | C | **R/A** | C | C | C | I |
| T7.4 Post-deploy monitoring | I | C | C | C | **R/A** | C | C | C | I |
| T7.5 Runbook | I | C | C | C | **R/A** | C | — | — | I |
| T7.6 Training | **R/A** | C | C | C | C | C | — | — | I |
| T7.7 Closure | **R/A** | C | C | C | C | C | C | C | I |

---

End of Document
