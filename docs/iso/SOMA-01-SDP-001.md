# SOMAAGENT01 — SOFTWARE DEVELOPMENT PLAN

## Document Control

| Field | Value |
|---|---|
| Document Title | SomaAgent01 Software Development Plan |
| Document Identifier | SOMA-01-SDP-001 |
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

| 1.0.0 | 2026-09-28 | SomaTech Engineering | Brought under ISO document control. Prior status value `Active` is outside the closed set `Draft \| In Review \| Approved \| Obsolete`; normalised to `Draft` — no approver has signed this document. |
| 1.0.0 | 2026-06-15 | SomaTech Engineering | Initial Software Development Plan |

---

## 1. PURPOSE

This plan defines the software development lifecycle processes, methods, tools, and standards for the SomaAgent01 project, conforming to ISO/IEC 12207:2017.

---

## 2. LIFECYCLE MODEL

### 2.1 Model: Iterative with Phase Gates

The project follows a 7-phase iterative model with formal gate reviews:

```
REQUIREMENTS → DESIGN → IMPLEMENTATION → TESTING → DEPLOYMENT → MAINTENANCE
     ↑                                                              │
     └──────────────── Feedback Loop ───────────────────────────────┘
```

Each phase has:
- **Entry criteria** (what must be true before starting)
- **Activities** (what is done)
- **Exit criteria / Gate** (what must be true before proceeding)
- **Deliverables** (what is produced)

### 2.2 Phase Definitions

| Phase | Entry Criteria | Key Activities | Exit Criteria | Deliverables |
|-------|---------------|----------------|---------------|--------------|
| 1. Stabilize | Charter approved | Fix P0 blockers, Docker verification | App starts, chat works | Working system |
| 2. Secure | Phase 1 gate passed | Auth hardening, security scanning | All auth features work, scan clean | Secure system |
| 3. Consolidate | Phase 2 gate passed | Unify architecture, remove duplication | Single pipeline, single memory | Consolidated codebase |
| 4. Test | Phase 3 gate passed | CI setup, test writing | 50%+ coverage, CI green | Tested system |
| 5. Harden | Phase 4 gate passed | K8s manifests, monitoring, load testing | K8s ready, baseline established | Hardened system |
| 6. Validate | Phase 5 gate passed | E2E testing, pentest, UAT | All validations pass | Validated system |
| 7. Release | Phase 6 gate passed | RC tagging, prod deployment, handover | Production live, 72h clean | Released system |

---

## 3. DEVELOPMENT PROCESSES

### 3.1 Requirements Process

| Activity | Method | Output |
|----------|--------|--------|
| Requirements elicitation | Domain SRS documents (22 files) | SOMA-01-SRS-001 |
| Requirements analysis | MoSCoW prioritization | Prioritized requirement list |
| Requirements validation | Stakeholder review | Signed-off SRS |
| Requirements traceability | Traceability matrix | REQ → Code → Test mapping |
| Requirements change control | SOMA-PM-CHANGE-001 | Change log |

### 3.2 Design Process

| Activity | Method | Output |
|----------|--------|--------|
| Architecture design | ISO/IEC 42010 views | SOMA-01-ARCH-001 |
| Security design | ISO 27001 controls | SOMA-01-SEC-001 |
| API design | Django Ninja + OpenAPI | OpenAPI schema |
| Database design | Django ORM models | Migration files |
| UI design | Lit 3.x components | Component specs |

### 3.3 Implementation Process

| Activity | Standard | Enforcement |
|----------|----------|-------------|
| Code style | VIBE Coding Rules (7 rules) | Ruff + pre-commit hooks |
| Type safety | Pyright basic mode | CI gate |
| Code formatting | Black (line-length 100) | Pre-commit hook |
| Import sorting | isort (via Ruff) | Pre-commit hook |
| Commit messages | Conventional Commits | PR review |
| Branch strategy | Feature branches → main | PR with review |

### 3.4 Testing Process

| Level | Framework | Infrastructure | Coverage Target |
|-------|-----------|---------------|-----------------|
| Unit | pytest | None (pure Python) | 80% per module |
| Integration | pytest + testcontainers | Docker (PG, Redis, Kafka) | Critical paths |
| E2E | pytest + Playwright | Full Docker stack | User journeys |
| Contract | Manual (compatibility matrix) | Cross-repo | API compatibility |
| Load | Locust or k6 | Staging environment | Performance SLOs |
| Security | Bandit, Safety, TruffleHog | CI | Zero critical findings |

### 3.5 Deployment Process

| Activity | Method | Environment |
|----------|--------|-------------|
| Local development | `make dev` (uvicorn hot reload) | Developer machine |
| Standalone testing | `docker compose up -d` | Local Docker |
| AAAS testing | `docker compose -f docker-compose.aaas.yml up -d` | Local Docker |
| Staging deployment | K8s manifests + Helm | Staging cluster |
| Production deployment | K8s manifests + Helm + canary | Production cluster |

---

## 4. TOOLS AND ENVIRONMENTS

### 4.1 Development Tools

| Tool | Purpose | Version |
|------|---------|---------|
| Python | Runtime | 3.12+ |
| Django | Web framework | 5.1 |
| Django Ninja | API framework | 1.3 |
| Poetry | Dependency management | Latest |
| Black | Code formatting | 25.9+ |
| Ruff | Linting | 0.13+ |
| Pyright | Type checking | Latest |
| pytest | Testing | 8.3+ |
| Docker | Containerization | 24+ |
| Docker Compose | Multi-container orchestration | 2.20+ |
| Git | Version control | 2.x |
| VS Code / Cursor | IDE | Latest |

### 4.2 CI/CD Tools

| Tool | Purpose | Status |
|------|---------|--------|
| GitHub Actions | CI pipeline | TO BE IMPLEMENTED (Phase 4) |
| Docker Hub / GHCR | Image registry | TO BE IMPLEMENTED |
| Helm | K8s package manager | Charts exist |
| Tilt | Local K8s development | Config exists |
| Prometheus | Metrics | Partially wired |
| Grafana | Dashboards | TO BE CONFIGURED |

### 4.3 Infrastructure (per SOMA-01-ARCH-001)

| Service | Standalone Port | AAAS Port | Purpose |
|---------|----------------|-----------|---------|
| PostgreSQL | 20432 | 63932 | Primary database |
| Redis | 20379 | 63979 | Cache, sessions, rate limiting |
| Kafka | 9092 | 9092 | Event streaming |
| Milvus | 19530 | 19530 | Vector search |
| Keycloak | 20880 | 63980 | Identity provider |
| Vault | 20882 | 63982 | Secrets management |
| OPA | 20181 | 8181 | Policy engine |
| SpiceDB | 20051 | 50051 | Authorization |

---

## 5. CONFIGURATION MANAGEMENT

### 5.1 Version Control

| Item | Strategy |
|------|----------|
| Branching | Feature branches from main |
| Merging | PR with at least 1 review |
| Tagging | Semantic versioning (vX.Y.Z) |
| Release notes | CHANGELOG.md per repo |

### 5.2 Configuration Items

| CI Item | Identifier | Location |
|---------|-----------|----------|
| Source code | somaAgent01 | GitHub repository |
| Docker images | somatech/soma-agent | Docker Hub / GHCR |
| K8s manifests | infra/k8s/ | In repository |
| Helm charts | infra/helm/ | In repository |
| Database migrations | admin/*/migrations/ | In repository |
| OPA policies | policy/ | In repository |
| SpiceDB schema | schemas/spicedb/ | In repository |
| ISO documentation | docs/iso/ | In repository |
| Project documentation | docs/project/ | In repository |

---

## 6. REVIEWS AND AUDITS

### 6.1 Review Types

| Review | Frequency | Participants | Output |
|--------|-----------|-------------|--------|
| Code review | Every PR | Author + 1 reviewer | Approved PR |
| Architecture review | Monthly | Leads + architect | ADR if needed |
| Security review | Monthly | Security lead | Security report |
| Documentation review | End of each phase | PM + leads | Updated docs |
| ISO compliance audit | Quarterly | Quality lead | Audit report |

### 6.2 Audit Schedule

| Audit | Date | Scope | Auditor |
|-------|------|-------|---------|
| Phase 1 Gate | Jun 29, 2026 | Stabilization | PM + leads |
| Phase 2 Gate | Jul 13, 2026 | Security | PM + security lead |
| Phase 3 Gate | Aug 3, 2026 | Architecture | PM + backend lead |
| Phase 4 Gate | Aug 24, 2026 | Testing | PM + QA lead |
| Phase 5 Gate | Sep 14, 2026 | Infrastructure | PM + DevOps lead |
| Phase 6 Gate | Oct 5, 2026 | Validation | PM + all leads |
| Production release | Oct 10, 2026 | Full system | All stakeholders |

---

## 7. DEFECT MANAGEMENT

### 7.1 Severity Levels

| Level | Definition | Response Time | Resolution Time |
|-------|-----------|---------------|-----------------|
| Critical (P0) | System crash, data loss, security breach | 1 hour | 24 hours |
| High (P1) | Major feature broken, security vulnerability | 4 hours | 1 week |
| Medium (P2) | Feature partially broken, workaround exists | 1 day | 2 weeks |
| Low (P3) | Minor issue, cosmetic, documentation | 1 week | Next sprint |

### 7.2 Defect Lifecycle

```
NEW → TRIAGED → IN PROGRESS → FIXED → VERIFIED → CLOSED
                ↓                        ↓
              BLOCKED                  REOPENED
```

---

## 8. TRAINING

| Audience | Topic | Method | When |
|----------|-------|--------|------|
| Developers | VIBE coding rules | Self-study + review | Onboarding |
| Developers | Django + Django Ninja | Self-study | Onboarding |
| QA | Test infrastructure (Docker, testcontainers) | Hands-on | Phase 4 |
| Ops | K8s deployment, monitoring, incident response | Training sessions | Phase 7 |
| All | Security awareness | Presentation | Phase 2 |

---

End of Document
