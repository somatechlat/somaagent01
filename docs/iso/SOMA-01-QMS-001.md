# SOMA-01-QMS-001 — Quality Manual

## Document Control

| Field | Value |
|---|---|
| Document Title | SomaAgent01 Quality Manual |
| Document Identifier | SOMA-01-QMS-001 |
| Version | 2.2.2 |
| Date | 2026-10-03 |
| Status | Draft |
| Author | SomaTech Engineering |
| Approver | — |
| Classification | Internal |
| ISO Reference | ISO 9001:2015 — Quality Management Systems — Requirements |
| Next Review | 2026-12-28 |

## Revision History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0.0 | 2025-12-30 | SomaTech Engineering | Initial quality manual |
| 1.1.0 | 2026-06-01 | SomaTech Engineering | Updated quality objectives and process map |
| 2.0.0 | 2026-06-15 | SomaTech Engineering | Code-verified deep analysis; updated quality metrics; revised improvement plan |
| 2.1.0 | 2026-09-27 | SomaTech Engineering | §7 registers SOMA-01-DOCS-001 and SOMA-01-DOCS-002 |
| 2.1.1 | 2026-09-27 | SomaTech Engineering | §7 registers SOMA-01-UIUX-005 (Settings Parity Matrix) |
| 2.2.0 | 2026-09-28 | SomaTech Engineering | §7 extended to register the full UI/UX suite: SOMA-01-UIUX-001…004 and the three design controls SOMA-UI-MOCKUPS-001, SOMA-UI-IDREG-001, SOMA-UI-TEMPLATE-001. |
| 2.2.1 | 2026-09-28 | SomaTech Engineering | §7 extended to register the seven ISO-series documents that were in `docs/iso/` but absent from the matrix: SOMA-01-SRS-001, SOMA-01-SDP-001, SOMA-01-VV-001, SOMA-01-OPS-001, SOMA-01-RELEASE-001, SOMA-01-AAAS-001, SOMA-01-COMPAT-001. Closes check rule C-10. |
| 2.2.2 | 2026-10-03 | SomaTech Engineering | §7 registers SOMA-UI-SKINS-001 (Capsule Skins — Theming Framework Specification). |
| 2.2.3 | 2026-10-03 | SomaTech Engineering | §7 registers SOMA-STD-CONFIG-001 (Configuration and Service Endpoint Resolution). |

---

## 1. Quality Policy

### 1.1 Policy Statement

SomaTech Engineering is committed to delivering a reliable, secure, and maintainable enterprise multi-agent cognitive platform that meets customer requirements and applicable regulatory standards.

### 1.2 VIBE Quality Standard

All development on SomaAgent01 shall adhere to the VIBE (Verification, Integration, Build, Enforcement) coding standard (`docs/standards/SOMA-STD-CODING-001.md`), which defines the following seven rules:

1. **No mocks, no placeholders, no TODOs** — Production-grade code only; tests use real infrastructure
2. **Check architecture before coding** — Understand existing patterns before implementing
3. **Modify existing files when possible** — Prefer editing over creating new files
4. **Production-grade code only** — No shortcuts, no "implement later"
5. **Documentation must match reality** — Docs describe implementation, not intent
6. **Understand full flow before implementing** — Trace the complete execution path
7. **Use actual services and data** — No fakeredis; no synthetic test data in integration tests

### 1.3 Django Purity Standards

| Rule | Allowed | Prohibited |
|------|---------|------------|
| ORM | Django ORM | SQLAlchemy |
| Migrations | Django Migrations | Alembic |
| API Framework | Django Ninja | FastAPI |
| Frontend | Lit 3.x Web Components | React, Alpine.js |
| Vector Database | Milvus 2.3 | Qdrant |

---

## 2. Quality Objectives

### 2.1 Measurable Quality Objectives

| ID | Objective | Target | Current | Gap | Timeline |
|----|-----------|--------|---------|-----|----------|
| QO-01 | Test coverage ≥ 40% | 40% | 2.8% | 37.2% | 6 weeks |
| QO-02 | Test coverage ≥ 80% (new features) | 80% | Unknown | — | Ongoing |
| QO-03 | Zero P0 security vulnerabilities | 0 | 3 | 3 | 2 weeks |
| QO-04 | CI/CD pipeline operational | Yes | No | — | 3 weeks |
| QO-05 | All Django migrations in sync | Yes | No | — | 1 week |
| QO-06 | Pyright type errors < 100 | < 100 | 1,402 | ~1,300 | 12 weeks |
| QO-07 | Zero authorization bypasses | 0 | 1 | 1 | 1 week |
| QO-08 | Audit logging on 100% of API endpoints | 100% | ~30% | ~70% | 8 weeks |
| QO-09 | Production readiness score ≥ 80% | 80% | 45% | 35% | 12 weeks |
| QO-10 | All VIBE rules enforced | Yes | Partial | — | Ongoing |

---

## 3. Process Map

### 3.1 Development Lifecycle

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  1. Plan     │───►│  2. Design  │───►│  3. Implement│───►│  4. Test    │
│  (SRS/ADR)  │    │  (ARCH)     │    │  (VIBE rules)│    │  (Real infra)│
└─────────────┘    └─────────────┘    └─────────────┘    └──────┬──────┘
                                                                │
┌─────────────┐    ┌─────────────┐    ┌─────────────┐          │
│  7. Monitor │◄───│  6. Deploy  │◄───│  5. Review  │◄─────────┘
│  (Obs stack)│    │  (Docker/K8s)│    │  (Code review)│
└─────────────┘    └─────────────┘    └─────────────┘
```

### 3.2 Process Descriptions

| Phase | Process | Input | Output | Responsible |
|-------|---------|-------|--------|-------------|
| 1. Plan | Requirements analysis | User stories, SRS | Design specifications | PM + Architect |
| 2. Design | Architecture design | Requirements | ARCH document, ADRs | Architect |
| 3. Implement | Code development | Design specs | Source code (VIBE-compliant) | Engineers |
| 4. Test | Testing (unit, integration, e2e) | Source code | Test results, coverage reports | QA + Engineers |
| 5. Review | Code review | Source code + tests | Approved changes | Senior Engineers |
| 6. Deploy | Deployment | Approved changes | Running services | DevOps |
| 7. Monitor | Observability | Runtime metrics | Alerts, health reports | DevOps + SRE |

---

## 4. Quality Controls

### 4.1 Preventive Controls

| Control | Implementation | Status |
|---------|---------------|--------|
| Coding standards | VIBE rules (`docs/standards/SOMA-STD-CODING-001.md`) | Implemented |
| Configuration / endpoints | `docs/standards/SOMA-STD-CONFIG-001.md` | Implemented |
| Django purity | Prohibition lists (SQLAlchemy, FastAPI, React, Qdrant) | Implemented |
| Architecture review | ARCH document; check before coding | Implemented |
| Type checking | Pyright configuration (`pyrightconfig.json`) | Implemented (1,402 errors remain) |
| Linting | Ruff configuration (`pyproject.toml`) | Implemented |
| Pre-commit hooks | Not configured | **Gap** |

### 4.2 Detective Controls

| Control | Implementation | Status |
|---------|---------------|--------|
| Code audit | Deep audit reports (v1.0, v1.1, v2.0) | Implemented |
| Test suite | 15 test files | **Insufficient** (2.8% coverage) |
| CI/CD linting | No pipelines | **Gap** |
| CI/CD testing | No pipelines | **Gap** |
| Security scanning | No SAST/DAST | **Gap** |
| Dependency scanning | No vulnerability scanning | **Gap** |

### 4.3 Corrective Controls

| Control | Implementation | Status |
|---------|---------------|--------|
| Issue tracking | GitHub Issues | Implemented |
| Audit findings tracking | Risk register (SOMA-01-RISK-001) | Implemented |
| Production readiness roadmap | 12-week plan (SOMA-01-PROD-001) | Implemented |
| Hotfix process | Not documented | **Gap** |

---

## 5. Quality Metrics

### 5.1 Current Metrics

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Overall production readiness | 45% | 80% | **Below target** |
| Test coverage | 2.8% | 40% | **Below target** |
| P0 vulnerabilities | 3 | 0 | **Below target** |
| P1 issues | 4 | 0 | **Below target** |
| P2 issues | 3 | 0 | Below target |
| Pyright errors | 1,402 | < 100 | **Below target** |
| Security controls implemented | 7/58 | 50/58 | **Below target** |
| CI/CD pipelines | 0 | ≥ 3 | **Below target** |
| Django apps | 55 | — | Inventory |
| Service modules | 40+ | — | Inventory |
| Test files | 15 | 50+ | **Below target** |

### 5.2 Quality Trend

| Metric | v1.0 (2025-12-30) | v1.1 (2026-06-01) | v2.0 (2026-06-15) | Trend |
|--------|-------------------|-------------------|-------------------|-------|
| Production readiness | ~30% | ~40% | 45% | ↑ Improving slowly |
| P0 vulnerabilities | 8 | 5 | 3 | ↓ Improving |
| Security controls | 2/58 | 5/58 | 7/58 | ↑ Improving |
| Test coverage | ~1% | ~2% | 2.8% | ↑ Improving slowly |
| CI/CD pipelines | 0 | 0 | 0 | → No change |

---

## 6. Improvement Plan

### 6.1 Immediate Improvements (Weeks 1–2)

| ID | Improvement | Expected Impact | Owner |
|----|------------|----------------|-------|
| IMP-01 | Fix P0 authorization bypass | Eliminates critical security risk | Backend |
| IMP-02 | Fix P0 WebSocket routing | Restores core functionality | Frontend + Backend |
| IMP-03 | Sync Django migrations | Enables clean deployments | Backend |
| IMP-04 | Fix RoleRequired 401→403 | Correct HTTP semantics | Backend |

### 6.2 Short-Term Improvements (Weeks 3–6)

| ID | Improvement | Expected Impact | Owner |
|----|------------|----------------|-------|
| IMP-05 | Create CI/CD pipelines | Automated quality gates | DevOps |
| IMP-06 | Achieve 40% test coverage | Regression protection | QA + Backend |
| IMP-07 | Fix somabrain path dependency | Portable builds | DevOps |
| IMP-08 | Add pre-commit hooks | Prevent VIBE violations | DevOps |

### 6.3 Medium-Term Improvements (Weeks 7–12)

| ID | Improvement | Expected Impact | Owner |
|----|------------|----------------|-------|
| IMP-09 | Consolidate conversation-worker with V3 | Consistent chat behavior | Backend |
| IMP-10 | Wire audit logging to all endpoints | Complete audit trail | Backend |
| IMP-11 | Reduce Pyright errors to < 100 | Type safety | Backend |
| IMP-12 | Complete K8s deployment manifests | Production deployment capability | DevOps |
| IMP-13 | Achieve 80% production readiness | Production readiness | All |
| IMP-14 | Document incident response runbook | Operational readiness | DevOps + SRE |

### 6.4 Continuous Improvements

| ID | Improvement | Frequency | Owner |
|----|------------|-----------|-------|
| IMP-C1 | Audit codebase for VIBE compliance | Monthly | QA |
| IMP-C2 | Review and update risk register | Bi-weekly | PM |
| IMP-C3 | Update ISO documentation suite | Quarterly | Engineering |
| IMP-C4 | Dependency vulnerability scanning | Weekly (automated) | DevOps |
| IMP-C5 | Test coverage review | Weekly | QA |

---

## 7. Document Reference Matrix

| Document | Identifier | ISO Reference | Purpose |
|----------|------------|---------------|---------|
| Architecture Document | SOMA-01-ARCH-001 | ISO/IEC/IEEE 42010 | System architecture description |
| Audit Report | SOMA-01-AUDIT-002 | ISO 19011 | Code-verified audit findings |
| Security Assessment | SOMA-01-SEC-001 | ISO 27001 | Security controls and vulnerabilities |
| Risk Register | SOMA-01-RISK-001 | ISO 31000 | Risk identification and mitigation |
| Production Readiness | SOMA-01-PROD-001 | Internal | Production gate criteria and roadmap |
| Quality Manual | SOMA-01-QMS-001 | ISO 9001 | Quality policy, objectives, and processes |
| Document Control and Traceability Procedure | SOMA-01-DOCS-001 | ISO 9001:2015 clause 7.5 | Control of documented information |
| Document Register | SOMA-01-DOCS-002 | ISO 9001:2015 clause 7.5 | Authoritative inventory of `docs/**/*.md` |
| User Interface — Screen & Feature Specification | SOMA-01-UIUX-001 | ISO 9001:2015 clause 7.5 | Master screen, control, action and state specification |
| User Interface — Modal & Overlay Specification | SOMA-01-UIUX-002 | ISO 9001:2015 clause 7.5 | The three modal patterns and their per-screen inventory |
| User Interface — Component & Module Catalogue | SOMA-01-UIUX-003 | ISO 9001:2015 clause 7.5 | Components, stores, controllers and the Capsule Module contract |
| User Interface — Verification & Traceability | SOMA-01-UIUX-004 | ISO 9001:2015 clause 7.5 | RTM, V&V matrix, Playwright coverage and tracked findings |
| User Interface — Settings Parity Matrix | SOMA-01-UIUX-005 | ISO 9001:2015 clause 7.5 | Setting-to-screen placement and parity mapping |
| User Interface Mockups Index | SOMA-UI-MOCKUPS-001 | ISO 9001:2015 clause 7.5 | Controlled index of the ASCII wireframe annexes |
| Screen Identifier Allocation | SOMA-UI-IDREG-001 | ISO 9001:2015 clause 7.5 | Authoritative UI sub-identifier allocation |
| House ISO Template | SOMA-UI-TEMPLATE-001 | ISO 9001:2015 clause 7.5 | Binding authoring template and honesty rules for the UI/UX suite |
| Capsule Skins — Theming Framework Specification | SOMA-UI-SKINS-001 | ISO 9001:2015 clause 7.5 | Feature specification for Capsule-owned theming and skinning |
| Software Requirements Specification | SOMA-01-SRS-001 | ISO 9001:2015 | Normative software requirements for somaAgent01 |
| Software Development Plan | SOMA-01-SDP-001 | ISO/IEC 12207:2017 | Lifecycle, engineering and support process plan |
| Verification and Validation Plan | SOMA-01-VV-001 | ISO 9001:2015 | V&V strategy, acceptance criteria and evidence |
| Operations Runbook | SOMA-01-OPS-001 | ISO 9001:2015 | Operational procedures and incident handling |
| Release Notes | SOMA-01-RELEASE-001 | ISO 9001:2015 | Released content, known issues and upgrade notes |
| AAAS Deployment Specification | SOMA-01-AAAS-001 | ISO 9001:2015 | Agent-as-a-Service deployment topology and contract |
| Deployment Model Specification | SOMA-01-DEPLOY-001 | ISO/IEC 27001:2022; ISO/IEC 42001:2023 | Standalone and Enterprise deployment models, identity sources, RBAC |
| Cognitive Triad Compatibility Matrix | SOMA-01-COMPAT-001 | ISO 9001:2015 | Supported version combinations across the triad |
| Standards Register — Normative and Applied External Standards | SOMA-01-STD-001 | ISO 9001:2015 clause 7.5; ISO/IEC 27001:2022; ISO/IEC 42001:2023 | Single register of every external standard cited or implemented, organised by standards body |
| Configuration and Service Endpoint Resolution | SOMA-STD-CONFIG-001 | ISO 9001:2015 clause 7.5; ISO/IEC 27001:2022 A.8.9 | Four-step configuration pattern, resolution chain, fail-closed endpoints |

---

End of Document
