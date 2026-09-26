# SOMA COGNITIVE TRIAD — WORK BREAKDOWN STRUCTURE

## Document Control

| Field | Value |
|-------|-------|
| Document Title | Soma Cognitive Triad Work Breakdown Structure |
| Document Identifier | SOMA-PM-WBS-001 |
| Version | 1.1.0 |
| Date | 2026-06-15 |
| Status | Active |
| Author | SomaTech Engineering |

## Revision History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0.0 | 2026-06-15 | SomaTech Engineering | Initial WBS |
| 1.1.0 | 2026-06-15 | SomaTech Engineering | Added full team capacity and cross-repo effort breakdown |

---

## 1. WBS HIERARCHY

```
1.0 SOMA COGNITIVE TRIAD — PRODUCTION READINESS
│
├── 1.1 STABILIZE (Phase 1, Weeks 1-2)
│   ├── 1.1.1 Fix startup crash (T1.1)
│   ├── 1.1.2 Commit migrations (T1.2)
│   ├── 1.1.3 Fix permissions stub (T1.3)
│   ├── 1.1.4 Fix WebSocket routing (T1.4, T1.5, T1.6)
│   ├── 1.1.5 Fix dependency issues (T1.7, T1.8, T1.9)
│   ├── 1.1.6 Docker verification (T1.10, T1.11)
│   └── 1.1.7 Phase 1 gate (T1.12)
│
├── 1.2 SECURE (Phase 2, Weeks 3-4)
│   ├── 1.2.1 Fix auth features (T2.1-T2.5)
│   ├── 1.2.2 Frontend security (T2.2, T2.6, T2.8)
│   ├── 1.2.3 Infrastructure security (T2.7, T2.9)
│   ├── 1.2.4 Security scanning (T2.10)
│   └── 1.2.5 Phase 2 gate (T2.11)
│
├── 1.3 CONSOLIDATE (Phase 3, Weeks 5-7)
│   ├── 1.3.1 Unify deployment mode (T3.1)
│   ├── 1.3.2 Unify memory access (T3.2, T3.3)
│   ├── 1.3.3 Unify chat pipeline (T3.4, T3.5, T3.6)
│   ├── 1.3.4 Improve code quality (T3.7, T3.8, T3.9)
│   └── 1.3.5 Phase 3 gate (T3.10)
│
├── 1.4 TEST (Phase 4, Weeks 8-10)
│   ├── 1.4.1 CI/CD setup (T4.1, T4.2)
│   ├── 1.4.2 Unit tests (T4.3)
│   ├── 1.4.3 Integration tests (T4.4, T4.5, T4.6)
│   ├── 1.4.4 Cross-repo tests (T4.7, T4.8)
│   ├── 1.4.5 Coverage target (T4.9)
│   └── 1.4.6 Phase 4 gate (T4.10)
│
├── 1.5 HARDEN (Phase 5, Weeks 11-13)
│   ├── 1.5.1 K8s production manifests (T5.1, T5.2)
│   ├── 1.5.2 Docker/Makefile cleanup (T5.3, T5.4)
│   ├── 1.5.3 Observability (T5.5, T5.6)
│   ├── 1.5.4 Audit and backup (T5.7, T5.8)
│   ├── 1.5.5 Load testing (T5.9)
│   └── 1.5.6 Phase 5 gate (T5.10)
│
├── 1.6 VALIDATE (Phase 6, Weeks 14-16)
│   ├── 1.6.1 Integration validation (T6.1, T6.2)
│   ├── 1.6.2 Deployment validation (T6.3)
│   ├── 1.6.3 Documentation audit (T6.4, T6.5)
│   ├── 1.6.4 Security pentest (T6.6)
│   ├── 1.6.5 DR drill (T6.7)
│   ├── 1.6.6 UAT (T6.8)
│   └── 1.6.7 Phase 6 gate (T6.9)
│
└── 1.7 RELEASE (Phase 7, Weeks 17-18)
    ├── 1.7.1 Release candidate (T7.1)
    ├── 1.7.2 Production deployment (T7.2, T7.3)
    ├── 1.7.3 Post-deploy monitoring (T7.4)
    ├── 1.7.4 Handover (T7.5, T7.6)
    └── 1.7.5 Project closure (T7.7)
```

---

## 2. WBS DICTIONARY

### 1.1 STABILIZE

| WBS | Deliverable | Acceptance Criteria | Effort |
|-----|-------------|---------------------|--------|
| 1.1.1 | App starts without crash | `python manage.py check` passes | 4h |
| 1.1.2 | Migrations committed | `makemigrations --check` passes | 2h |
| 1.1.3 | Permissions check real | /check calls SpiceDB/OPA | 8h |
| 1.1.4 | Chat flow works | WS connect → message → response | 24h |
| 1.1.5 | Dependencies fixed | No path deps, correct env vars | 8h |
| 1.1.6 | Docker verified | Standalone + AAAS compose up | 16h |
| 1.1.7 | Gate signed off | PM + leads approve | 4h |

### 1.2 SECURE

| WBS | Deliverable | Acceptance Criteria | Effort |
|-----|-------------|---------------------|--------|
| 1.2.1 | Auth features work | Login/register/MFA/reset/logout | 32h |
| 1.2.2 | Frontend secured | httpOnly cookies, CSP, CSRF | 24h |
| 1.2.3 | Infra secured | No hardcoded creds, OPA paths correct | 16h |
| 1.2.4 | Security scan clean | Bandit/Safety pass | 8h |
| 1.2.5 | Gate signed off | PM + leads approve | 4h |

### 1.3 CONSOLIDATE

| WBS | Deliverable | Acceptance Criteria | Effort |
|-----|-------------|---------------------|--------|
| 1.3.1 | Single mode resolver | All use DeploymentMode | 16h |
| 1.3.2 | Single memory interface | MemoryPort adopted | 32h |
| 1.3.3 | Single chat pipeline | V3 only, worker wired | 40h |
| 1.3.4 | Code quality improved | <500 Pyright errors, stricter Ruff | 40h |
| 1.3.5 | Gate signed off | PM + leads approve | 4h |

### 1.4 TEST

| WBS | Deliverable | Acceptance Criteria | Effort |
|-----|-------------|---------------------|--------|
| 1.4.1 | CI pipeline | GitHub Actions green | 16h |
| 1.4.2 | Chat tests | 12-phase pipeline covered | 24h |
| 1.4.3 | Auth/WS/Perm tests | Critical paths covered | 40h |
| 1.4.4 | Cross-repo tests | Agent→Brain→Memory tested | 24h |
| 1.4.5 | 50%+ coverage | Coverage report shows 50%+ | 40h |
| 1.4.6 | Gate signed off | PM + leads approve | 4h |

### 1.5 HARDEN

| WBS | Deliverable | Acceptance Criteria | Effort |
|-----|-------------|---------------------|--------|
| 1.5.1 | K8s production | Probes, limits, HPA, PDB, NetworkPolicy | 40h |
| 1.5.2 | Docker/Makefile | Single compose, fixed Makefile | 16h |
| 1.5.3 | Observability | Prometheus + Grafana dashboards | 24h |
| 1.5.4 | Audit/backup | Audit wired, backup tested | 16h |
| 1.5.5 | Load test | Performance baseline | 16h |
| 1.5.6 | Gate signed off | PM + leads approve | 4h |

### 1.6 VALIDATE

| WBS | Deliverable | Acceptance Criteria | Effort |
|-----|-------------|---------------------|--------|
| 1.6.1 | Integration validated | Full triad E2E | 24h |
| 1.6.2 | Deploy validated | Single-click AAAS works | 16h |
| 1.6.3 | Docs audited | ISO docs match code | 16h |
| 1.6.4 | Pentest clean | No critical/high findings | 40h |
| 1.6.5 | DR drill success | Restore within RTO | 16h |
| 1.6.6 | UAT signed off | Stakeholders approve | 24h |
| 1.6.7 | Gate signed off | PM + leads approve | 4h |

### 1.7 RELEASE

| WBS | Deliverable | Acceptance Criteria | Effort |
|-----|-------------|---------------------|--------|
| 1.7.1 | RC images | Versioned Docker images published | 8h |
| 1.7.2 | Prod deployed | Production environment live | 16h |
| 1.7.3 | Monitoring clean | 72h no critical incidents | 8h |
| 1.7.4 | Handover | Runbook + training complete | 24h |
| 1.7.5 | Project closed | Lessons learned documented | 8h |

---

## 3. TOTAL EFFORT SUMMARY

### 3.1 Lead Engineer Hours (Critical Path)

| Phase | Effort (hours) | Weeks | Focus |
|-------|---------------|-------|-------|
| 1. Stabilize | 66 | 2 | Make it start, make chat work |
| 2. Secure | 84 | 2 | Close security gaps |
| 3. Consolidate | 132 | 3 | Unify architecture |
| 4. Test | 148 | 3 | Build coverage, CI/CD |
| 5. Harden | 116 | 3 | K8s, monitoring, load test |
| 6. Validate | 140 | 3 | Cross-repo E2E, pentest, UAT |
| 7. Release | 64 | 2 | Production deploy, handover |
| **TOTAL (Critical Path)** | **750** | **18** | Lead engineer sequential tasks |

### 3.2 Full Team Capacity

| Metric | Value | Notes |
|--------|-------|-------|
| Core team | 5 engineers | Backend, Frontend, Security, DevOps, QA |
| Duration | 18 weeks | Jun 16 – Oct 19, 2026 |
| Hours/week/engineer | 40 | Standard work week |
| Total available | **3,600 hours** | 5 × 40h × 18 weeks |
| Critical path (WBS) | 750 hours | Sequential lead tasks |
| Parallel capacity | 2,850 hours | Available for concurrent work |
| Utilization target | 70% | 2,520 productive hours |
| Buffer | 30% | Unknowns, rework, meetings |

### 3.3 Cross-Repo Effort

| Repo | Hours | Source Document |
|------|-------|----------------|
| somaAgent01 (primary) | 750 | This WBS (SOMA-PM-WBS-001) |
| somabrain (integration support) | 160 | SOMA-BR-EXEC-001 |
| somafractalmemory (integration support) | 120 | SOMA-SFM-EXEC-001 |
| **GRAND TOTAL** | **1,030** | All repos combined |

---

End of Document
