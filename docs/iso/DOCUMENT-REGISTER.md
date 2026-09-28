# SOMA-01-DOCS-002 — Document Register

## Document Control

| Field | Value |
|---|---|
| Document Title | Document Register |
| Document Identifier | SOMA-01-DOCS-002 |
| Version | 1.0.1 |
| Date | 2026-09-27 |
| Status | Draft |
| Author | SomaTech Engineering |
| Approver | — |
| Classification | Internal |
| ISO Reference | ISO 9001:2015 — Quality Management Systems — Requirements |
| Next Review | 2026-12-27 |
| Related | `SOMA-01-DOCS-001.md`, `SOMA-01-QMS-001.md` |
| Source of truth | This file |
| Audience | All contributors and compliance tooling |
| Scope | Every `*.md` under `docs/` |

## Revision History

| Version | Date | Author | Description |
|---|---|---|---|
| 1.0.0 | 2026-09-27 | SomaTech Engineering | Initial issue. Register seeded from the working tree; pre-existing compliance gaps recorded as-is. |
| 1.0.1 | 2026-09-27 | SomaTech Engineering | Identifier corrected to `SOMA-01-DOCS-002` to match the §3.3 pattern. Register now lists itself. |

## 1. Purpose

Authoritative inventory of every `*.md` under `docs/`, as required by `SOMA-01-DOCS-001` §4.
This file is **data**, not analysis. Interpretation lives in `SOMA-01-DOCS-001` and `SOMA-01-UIUX-004`.

`Compliance` is the result of `scripts/check_docs.py` against `SOMA-01-DOCS-001` §5.2. A file marked
`Non-compliant` is a **tracked finding**, not an exemption (REQ-DOCS-014).

## 2. Register

| Document Identifier | File | Title | Version | Status | Approver | Next Review | Compliance |
|---|---|---|---|---|---|---|---|
| SOMA-01-AAAS-001 | docs/iso/SOMA-01-AAAS-001.md | Soma AAAS Deployment Specification | 1.0.0 | Active | — | MISSING | Non-compliant |
| SOMA-01-ARCH-001 | docs/iso/SOMA-01-ARCH-001.md | SomaAgent01 System Architecture Document | 2.0.0 | Pre-Production | — | MISSING | Non-compliant |
| SOMA-01-AUDIT-002 | docs/iso/SOMA-01-AUDIT-002.md | SomaAgent01 Code-Verified Deep Audit Report | 2.0.0 | Active | — | MISSING | Non-compliant |
| SOMA-COMPAT-001 | docs/iso/SOMA-01-COMPAT-001.md | Soma Cognitive Triad Version Compatibility Matrix | 1.0.0 | Active | — | MISSING | Non-compliant |
| SOMA-01-DOCS-001 | docs/iso/SOMA-01-DOCS-001.md | Document Control and Traceability Procedure | 1.0.0 | Draft | — | 2026-12-27 | Compliant |
| SOMA-01-DOCS-002 | docs/iso/DOCUMENT-REGISTER.md | Document Register | 1.0.1 | Draft | — | 2026-12-27 | Compliant |
| SOMA-01-OPS-001 | docs/iso/SOMA-01-OPS-001.md | SomaAgent01 Operations Runbook | 1.0.0 | Active | — | MISSING | Non-compliant |
| SOMA-01-PROD-001 | docs/iso/SOMA-01-PROD-001.md | SomaAgent01 Production Readiness Assessment | 2.0.0 | Active | — | MISSING | Non-compliant |
| SOMA-01-QMS-001 | docs/iso/SOMA-01-QMS-001.md | SomaAgent01 Quality Manual | 2.1.0 | Active | — | MISSING | Non-compliant |
| SOMA-01-RELEASE-001 | docs/iso/SOMA-01-RELEASE-001.md | SomaAgent01 v2.0.0 Release Notes | 2.0.0 | Release Candidate | — | MISSING | Non-compliant |
| SOMA-01-RISK-001 | docs/iso/SOMA-01-RISK-001.md | SomaAgent01 Risk Register | 2.0.0 | Active | — | MISSING | Non-compliant |
| SOMA-01-SDP-001 | docs/iso/SOMA-01-SDP-001.md | SomaAgent01 Software Development Plan | 1.0.0 | Active | — | MISSING | Non-compliant |
| SOMA-01-SEC-001 | docs/iso/SOMA-01-SEC-001.md | SomaAgent01 Security Assessment Report | 2.0.0 | Active | — | MISSING | Non-compliant |
| SOMA-01-SRS-001 | docs/iso/SOMA-01-SRS-001.md | SomaAgent01 Master Software Requirements Specification | 1.0.0 | Baseline | — | MISSING | Non-compliant |
| SOMA-01-VV-001 | docs/iso/SOMA-01-VV-001.md | SomaAgent01 Verification and Validation Plan | 1.0.0 | Active | — | MISSING | Non-compliant |
| SOMA-A0-PARITY-001 | docs/iso/SOMA-A0-PARITY-001.md | Soma × Agent Zero — Feature Parity Matrix, UI/UX Development Specifica | 1.0.0 | **Draft — FOR EXECUTION APPROVAL. No production code until Plan Gate is signed.** | Product Owner (user) | MISSING | Non-compliant |
| SOMA-BRAIN-COMPLIANCE-001 | docs/iso/SOMA-BRAIN-COMPLIANCE-001.md | SOMA-BRAIN-COMPLIANCE-001 — SomaBrain No-Fakes / No-Bypasses Audit | 1.0.0 | Findings open — remediation in progress | — | MISSING | Non-compliant |
| SOMA-TRIAD-ARCH-001 | docs/iso/SOMA-TRIAD-ARCH-001.md | Soma Triad Architecture Description — Agent / Brain / Memory | 2.0.0 | Draft — findings open, remediation plan approved for execution | — | MISSING | Non-compliant |
| — | docs/README.md | 🧠 SomaAgent01: Enterprise Multi-Agent Cognitive Platform | — | — | — | MISSING | Non-compliant |
| — | docs/architecture/saas_independent_deployment.md | AAAS Standalone Deployment Guide | — | — | — | MISSING | Non-compliant |
| — | docs/deployment/DEPLOYMENT.md | 🚀 Deployment Guide | — | — | — | MISSING | Non-compliant |
| — | docs/deployment/DEPLOYMENT_MODES.md | Deployment Modes - AAAS vs STANDALONE | — | — | — | MISSING | Non-compliant |
| — | docs/deployment/SOFTWARE_DEPLOYMENT_MODES.md | Software Deployment Modes | — | — | — | MISSING | Non-compliant |
| — | docs/deployment/SOMAAGENT01_DEPLOYMENT_PLAN.md | 🚀 SOMAAGENT01 — COMPLETE DEPLOYMENT PLAN | — | — | — | MISSING | Non-compliant |
| — | docs/design/INVENTORY.md | System Inventory | — | — | — | MISSING | Non-compliant |
| — | docs/development/VIBE_CODING_RULES.md | ⚡ VIBE CODING RULES ⚡ | — | — | — | MISSING | Non-compliant |
| — | docs/project/ARCHITECTURE-INVARIANTS.md | ARCHITECTURE INVARIANTS — what must be perfect | — | — | — | MISSING | Non-compliant |
| — | docs/project/PLAN-TRIAD-SEAMLESS.md | PLAN — Seamless Triad: Agent ↔ SomaBrain ↔ SomaFractalMemory | — | — | — | MISSING | Non-compliant |
| SOMA-ARCH-REDESIGN-001 | docs/project/SOMA-ARCH-REDESIGN-001.md | Enterprise Architecture Redesign | 1.0.0 | Active | — | MISSING | Non-compliant |
| SOMA-FEAT-MATRIX-001 | docs/project/SOMA-FEAT-MATRIX-001.md | Agent Zero vs Soma Feature Comparison Matrix | 1.0.0 | Active | — | MISSING | Non-compliant |
| SOMA-MOD-ARCH-001 | docs/project/SOMA-MOD-ARCH-001.md | Soma Agent Modular Architecture — Core vs Optional Modules | 1.0.0 | Active | — | MISSING | Non-compliant |
| SOMA-MOD-SPEC-001 | docs/project/SOMA-MOD-SPEC-001.md | Soma Agent Module System Technical Specification | 1.0.0 | Baseline | — | MISSING | Non-compliant |
| SOMA-PM-CHANGE-001 | docs/project/SOMA-PM-CHANGE-001.md | Change Control Log | 1.0.0 | Active | — | MISSING | Non-compliant |
| SOMA-PM-CHARTER-001 | docs/project/SOMA-PM-CHARTER-001.md | Soma Cognitive Triad Project Charter | 1.1.0 | Approved | — | MISSING | Non-compliant |
| SOMA-PM-CLOSURE-001 | docs/project/SOMA-PM-CLOSURE-001.md | Project Closure Report | 1.0.0 | Final | — | MISSING | Non-compliant |
| SOMA-PM-COMM-001 | docs/project/SOMA-PM-COMM-001.md | Communication Plan | 1.0.0 | Active | — | MISSING | Non-compliant |
| SOMA-PM-DELIV-001 | docs/project/SOMA-PM-DELIV-001.md | Deliverables Register | 1.0.0 | Active | — | MISSING | Non-compliant |
| SOMA-PM-MILE-001 | docs/project/SOMA-PM-MILE-001.md | Milestone Tracker | 1.0.0 | Active | — | MISSING | Non-compliant |
| SOMA-PM-RACI-001 | docs/project/SOMA-PM-RACI-001.md | RACI Matrix (Responsible, Accountable, Consulted, Informed) | 1.0.0 | Active | — | MISSING | Non-compliant |
| SOMA-PM-WBS-001 | docs/project/SOMA-PM-WBS-001.md | Soma Cognitive Triad Work Breakdown Structure | 1.1.0 | Active | — | MISSING | Non-compliant |
| SOMA-SOW-001 | docs/project/SOMA-SOW-001.md | Soma Cognitive Triad — Full Scope of Work | 1.0.0 | Approved | — | MISSING | Non-compliant |
| SOMA-UI-MOCKUPS-001 | docs/project/SOMA-UI-MOCKUPS-001.md | Soma Agent Screen Mockups and Wireframes | 1.0.0 | Baseline | — | MISSING | Non-compliant |
| SOMA-UI-SPEC-001 | docs/project/SOMA-UI-SPEC-001.md | Soma Agent Definitive UI/UX Specification | 2.0.0 | Baseline | — | MISSING | Non-compliant |
| SOMA-UI-UX-001 | docs/project/SOMA-UI-UX-001.md | Soma Agent UI/UX Complete Specification | 1.0.0 | Baseline | — | MISSING | Non-compliant |
| — | docs/project/SOMA-UIUX-PARITY-PLAN-002.md | PLAN — UI/UX Feature Parity with Agent Zero (clone & better) | — | — | — | MISSING | Non-compliant |
| — | docs/reports/DEEP_REPO_ANALYSIS.md | > **HISTORICAL SNAPSHOT — 2026-01-25** | — | — | — | MISSING | Non-compliant |
| — | docs/srs/SRS-650-LINE-SOVEREIGNTY.md | SRS-650-LINE-SOVEREIGNTY — VIBE Rule 245 Enforcement | — | — | — | MISSING | Non-compliant |
| — | docs/srs/SRS-AGENTIQ.md | SRS-AGENTIQ — Governor Control Loop | — | — | — | MISSING | Non-compliant |
| — | docs/srs/SRS-ARCHITECTURAL-PATTERNS.md | SRS-ARCHITECTURAL-PATTERNS — Modular Design Patterns | — | — | — | MISSING | Non-compliant |
| — | docs/srs/SRS-BACKUP-SYSTEM.md | SRS-BACKUP-SYSTEM — Agent Backup & Disaster Recovery | — | — | — | MISSING | Non-compliant |
| — | docs/srs/SRS-BUDGET-SYSTEM.md | SRS-BUDGET-SYSTEM — Universal Resource Budgeting | — | — | — | MISSING | Non-compliant |
| — | docs/srs/SRS-CAPSULE-PORTABILITY.md | SRS-CAPSULE-PORTABILITY — Agent Portability and Exchange | — | — | — | MISSING | Non-compliant |
| — | docs/srs/SRS-CHAT-FLOW-MASTER.md | SRS-CHAT-FLOW-MASTER — Complete Agent Architecture with Resilience | — | — | — | MISSING | Non-compliant |
| — | docs/srs/SRS-CONTEXT-BUILDING.md | SRS-CONTEXT-BUILDING — Prompt Assembly | — | — | — | MISSING | Non-compliant |
| — | docs/srs/SRS-DATA-MODELS.md | SRS-DATA-MODELS — Data Models and ORM Schema | — | — | — | MISSING | Non-compliant |
| — | docs/srs/SRS-FEATURE-FLAGS.md | SRS-FEATURE-FLAGS — System Feature Toggles | — | — | — | MISSING | Non-compliant |
| — | docs/srs/SRS-LAGO-BILLING.md | SRS-LAGO-BILLING — Usage Metering & Billing | — | — | — | MISSING | Non-compliant |
| — | docs/srs/SRS-MODEL-ROUTING.md | SRS-MODEL-ROUTING — LLM Model Selection | — | — | — | MISSING | Non-compliant |
| — | docs/srs/SRS-MULTIMODAL.md | SRS-MULTIMODAL — Image, Audio, and Diagram Generation | — | — | — | MISSING | Non-compliant |
| — | docs/srs/SRS-PERMISSION-MATRIX.md | SRS-PERMISSION-MATRIX — Permission Matrix and Role Administration | — | — | — | MISSING | Non-compliant |
| — | docs/srs/SRS-RLM-ENGINE.md | SRS-RLM-ENGINE — Recursive Language Model Execution | — | — | — | MISSING | Non-compliant |
| — | docs/srs/SRS-SAAS-INFRASTRUCTURE.md | SRS-SAAS-INFRASTRUCTURE — AAAS Deployment Architecture | — | — | — | MISSING | Non-compliant |
| — | docs/srs/SRS-SECURITY-MULTITENANCY.md | SRS-SECURITY-MULTITENANCY — Security and Tenant Isolation | — | — | — | MISSING | Non-compliant |
| — | docs/srs/SRS-SOMABRAIN-INTEGRATION.md | SRS-SOMABRAIN-INTEGRATION — L3 Cognitive Engine | — | — | — | MISSING | Non-compliant |
| — | docs/srs/SRS-TEST-MODULES.md | SRS-TEST-MODULES — Module-Based Test Suite Design | — | — | — | MISSING | Non-compliant |
| — | docs/srs/SRS-TEST-WORKBENCH.md | SRS-TEST-WORKBENCH — Cross-Repository Test Audit | — | — | — | MISSING | Non-compliant |
| — | docs/srs/SRS-TOOL-SYSTEM.md | SRS-TOOL-SYSTEM — Tool Discovery and Execution | — | — | — | MISSING | Non-compliant |
| — | docs/srs/TEMPLATE.md | SRS-{FEATURE} — {Title} | — | — | — | MISSING | Non-compliant |
| — | docs/standards/SOMA_TOKEN_FORMAT.md | SOMA Token Format Standard (v1.0) | — | — | — | MISSING | Non-compliant |
| — | docs/superpowers/plans/2026-06-12-docker-cluster-standalone-readiness.md | Docker Cluster Standalone Readiness Implementation Plan | — | — | — | MISSING | Non-compliant |
| — | docs/superpowers/plans/2026-06-12-no-mocks-agent-ui-sync.md | No-Mocks Agent UI/UX Sync Plan | — | — | — | MISSING | Non-compliant |
| — | docs/tasks/AGENT_HANDOFF_SOMAAGENT01.md | > **HISTORICAL SNAPSHOT — 2025-01-26** | — | — | — | MISSING | Non-compliant |
| — | docs/tasks/MASTER-FLOW-TASKS.md | V3 FLOW MASTER TASK TRACKER — COMPLETE IMPLEMENTATION PLAN | — | — | — | MISSING | Non-compliant |
| — | docs/tasks/TASK-AGENTIQ.md | TASK-AGENTIQ: Governor Control Loop Implementation | — | — | — | MISSING | Non-compliant |
| — | docs/tasks/TASK-CONTEXT-BUILDING.md | TASK-CONTEXT-BUILDING: 5-Lane Context Assembly | — | — | — | MISSING | Non-compliant |
| — | docs/tasks/TASK-RLM-ENGINE.md | TASK-RLM-ENGINE: Recursive Language Model Implementation | — | — | — | MISSING | Non-compliant |
| — | docs/tasks/TASK-SOMABRAIN.md | TASK-SOMABRAIN: L3 Cognitive Engine Integration | — | — | — | MISSING | Non-compliant |
| — | docs/tasks/TASKS-MERGED-SOMAAGENT01.md | SomaAgent01 — Merged Tasks & Requirements | — | — | — | MISSING | Non-compliant |

## 3. Summary

| Measure | Count |
|---|---|
| Registered documents | 77 |
| Compliant | 1 |
| Non-compliant (tracked findings) | 76 |

## 4. Tracked remediation

The dominant pre-existing gap is the absence of a `Next Review` field, which no document in the
suite carried before `SOMA-01-DOCS-001`. `PLAN-TRIAD-SEAMLESS` W5-3 mandates it. Remediation is
batched: each document gains `Next Review` (and a `Revision History` where absent) at its next
scheduled revision, per `SOMA-01-QMS-001` IMP-C3 (quarterly documentation review).

Secondary findings recorded by the check include documents whose `Document Identifier` does not
match their filename and documents whose `Status` value is outside the closed set. Each is listed
by `scripts/check_docs.py` output and is not silently passed.

End of Document
