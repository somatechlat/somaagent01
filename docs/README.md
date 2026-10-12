# SOMA-STD-INDEX-001 — Documentation Tree Index

## Document Control

| Field | Value |
|---|---|
| Document Title | Documentation Tree Index |
| Document Identifier | SOMA-STD-INDEX-001 |
| Version | 1.1.0 |
| Date | 2026-10-08 |
| Status | Draft |
| Author | SomaTech Engineering |
| Approver | — |
| Classification | Internal |
| ISO Reference | ISO 9001:2015 — Quality Management Systems — Requirements |
| Next Review | 2026-12-28 |
| Related | `docs/iso/SOMA-01-DOCS-001.md`, `docs/iso/DOCUMENT-REGISTER.md` |
| Source of truth | The working tree under `docs/`; inventory regenerated from files on disk |
| Audience | All contributors and any agent working in this repository |
| Scope | Every `*.md` under `docs/` |

## Revision History

| Version | Date | Author | Description |
|---|---|---|---|
| 1.0.0 | 2026-09-28 | SomaTech Engineering | Initial issue. Brought under ISO document control. |
| 1.1.0 | 2026-10-08 | SomaTech Engineering | Rebuilt: single Document Control block; directory map and domain inventories regenerated from the live tree (source of truth = files on disk, not hand-edited lists). Added `docs/plans/` and `docs/design/mockups/` annex policy. |

## 1. How this tree is organised

Every controlled document is named by its Document Identifier:

```
SOMA-<DOMAIN>-<TYPE>-<NNN>.md
```

The **domain token decides the directory**, and the **filename stem is the identifier**.
Rules: `docs/iso/SOMA-01-DOCS-001.md` §3.3. Enforcement: `scripts/check_docs.py`
(`C-01`…`C-12`). Run with `make docs-check`; regenerate the master register with
`make docs-register` (`scripts/gen_register.py` → `docs/iso/DOCUMENT-REGISTER.md`).

This index is **derived**. When files are added, renamed, or removed under `docs/`,
update this file from the register and the working tree — do not invent entries.

## 2. Directories

| Directory | Domain | Contents |
|---|---|---|
| `docs/iso/` | `01` / topic | Controlled ISO-tier documents (quality manual, procedures, assessments, register). |
| `docs/architecture/` | `ARCH` | System architecture descriptions and invariants. |
| `docs/requirements/` | `SRS` | Software requirement specifications, one per subsystem or concern. |
| `docs/operations/` | `OPS` | Deployment modes, plans, runbooks. `images/` holds referenced diagrams. |
| `docs/design/` | `UI` | UI/UX specification and wireframes. |
| `docs/design/mockups/` | annex | Screen mockups (annex class; exempt from Document Control per SOMA-01-DOCS-001 §3.3.4). |
| `docs/modules/` | `MOD` | Capsule Module system: architecture and technical specification. |
| `docs/project/` | `PM` | Project management: charter, WBS, RACI, milestones, change log, SOW. |
| `docs/standards/` | `STD` | Coding rules, templates, format standards. Bind day-to-day work. |
| `docs/reports/` | `RPT` | Audits, analyses, comparison matrices, status. |
| `docs/tasks/` | `TASK` | Task lists, work packages, handoffs. |
| `docs/plans/` | `PM` / date | Implementation and wiring plans. Mixed: ISO-named and date-named. |
| `docs/plans/a2a/` | operational | Multi-agent coordination channels (CLAIMS / INBOX / LEDGER / OUTBOX). **Not** ISO-controlled documents. |

## 3. Documents by domain

Inventory below matches the working tree on 2026-10-08.

### `docs/iso/`

| Identifier | Title | File | Status |
|---|---|---|---|
| SOMA-01-DOCS-002 | Document Register | `docs/iso/DOCUMENT-REGISTER.md` | Draft |
| SOMA-01-Soma Platform-001 | Soma Soma Platform Deployment Specification | `docs/iso/SOMA-01-Soma Platform-001.md` | Draft |
| SOMA-01-ARCH-001 | SomaAgent01 System Architecture Document | `docs/iso/SOMA-01-ARCH-001.md` | Draft |
| SOMA-01-AUDIT-002 | SomaAgent01 Code-Verified Deep Audit Report | `docs/iso/SOMA-01-AUDIT-002.md` | Draft |
| SOMA-01-COMPAT-001 | Soma Cognitive Triad Version Compatibility Matrix | `docs/iso/SOMA-01-COMPAT-001.md` | Draft |
| SOMA-01-DEPLOY-001 | Deployment Model Specification — Standalone and Enterprise | `docs/iso/SOMA-01-DEPLOY-001.md` | Draft |
| SOMA-01-DOCS-001 | Document Control and Traceability Procedure | `docs/iso/SOMA-01-DOCS-001.md` | Draft |
| SOMA-01-OPS-001 | SomaAgent01 Operations Runbook | `docs/iso/SOMA-01-OPS-001.md` | Draft |
| SOMA-01-PROD-001 | SomaAgent01 Production Readiness Assessment | `docs/iso/SOMA-01-PROD-001.md` | Draft |
| SOMA-01-QMS-001 | SomaAgent01 Quality Manual | `docs/iso/SOMA-01-QMS-001.md` | Draft |
| SOMA-01-RELEASE-001 | SomaAgent01 v2.0.0 Release Notes | `docs/iso/SOMA-01-RELEASE-001.md` | Draft |
| SOMA-01-RISK-001 | SomaAgent01 Risk Register | `docs/iso/SOMA-01-RISK-001.md` | Draft |
| SOMA-01-SDP-001 | SomaAgent01 Software Development Plan | `docs/iso/SOMA-01-SDP-001.md` | Draft |
| SOMA-01-SEC-001 | SomaAgent01 Security Assessment Report | `docs/iso/SOMA-01-SEC-001.md` | Draft |
| SOMA-01-SRS-001 | SomaAgent01 Master Software Requirements Specification | `docs/iso/SOMA-01-SRS-001.md` | Draft |
| SOMA-01-STD-001 | Standards Register — Normative and Applied External Standards | `docs/iso/SOMA-01-STD-001.md` | Draft |
| SOMA-01-UIUX-001 | User Interface — Screen & Feature Specification | `docs/iso/SOMA-01-UIUX-001.md` | Draft |
| SOMA-01-UIUX-002 | User Interface — Modal & Overlay Specification | `docs/iso/SOMA-01-UIUX-002.md` | Draft |
| SOMA-01-UIUX-003 | User Interface — Component & Module Catalogue | `docs/iso/SOMA-01-UIUX-003.md` | Draft |
| SOMA-01-UIUX-004 | User Interface — Verification & Traceability | `docs/iso/SOMA-01-UIUX-004.md` | Draft |
| SOMA-01-UIUX-005 | User Interface — Settings Parity Matrix | `docs/iso/SOMA-01-UIUX-005.md` | Draft |
| SOMA-01-VV-001 | SomaAgent01 Verification and Validation Plan | `docs/iso/SOMA-01-VV-001.md` | Draft |
| SOMA-A0-PARITY-001 | Soma × Agent Zero — Feature Parity Matrix… | `docs/iso/SOMA-A0-PARITY-001.md` | Draft |
| SOMA-BRAIN-COMPLIANCE-001 | SomaBrain No-Fakes / No-Bypasses Audit | `docs/iso/SOMA-BRAIN-COMPLIANCE-001.md` | Draft |
| SOMA-SETTINGS-MODEL-001 | Soma Settings Model and Configuration Inventory | `docs/iso/SOMA-SETTINGS-MODEL-001.md` | Draft |
| SOMA-TRIAD-ARCH-001 | Soma Triad Architecture Description — Agent / Brain / Memory | `docs/iso/SOMA-TRIAD-ARCH-001.md` | Draft |

### `docs/architecture/`

| Identifier | Title | File | Status |
|---|---|---|---|
| SOMA-ARCH-ADR-001 | Architecture Decision: Shared Embedding Dimension is 768 | `docs/architecture/SOMA-ARCH-ADR-001.md` | Draft |
| SOMA-ARCH-INVARIANTS-001 | Architecture Invariants — what must hold | `docs/architecture/SOMA-ARCH-INVARIANTS-001.md` | Draft |
| SOMA-ARCH-REDESIGN-001 | Enterprise Architecture Redesign | `docs/architecture/SOMA-ARCH-REDESIGN-001.md` | Draft |
| SOMA-ARCH-TOOLS-001 | Agent tool framework — file/OS tools | `docs/architecture/SOMA-ARCH-TOOLS-001.md` | Draft |

### `docs/requirements/`

| Identifier | Title | File | Status |
|---|---|---|---|
| SOMA-SRS-AGENTIQ-001 | SRS-AGENTIQ — Governor Control Loop | `docs/requirements/SOMA-SRS-AGENTIQ-001.md` | Draft |
| SOMA-SRS-ARCHPATTERNS-001 | SRS-ARCHITECTURAL-PATTERNS — Modular Design Patterns | `docs/requirements/SOMA-SRS-ARCHPATTERNS-001.md` | Draft |
| SOMA-SRS-BACKUP-001 | SRS-BACKUP-SYSTEM — Agent Backup & Disaster Recovery | `docs/requirements/SOMA-SRS-BACKUP-001.md` | Draft |
| SOMA-SRS-BUDGET-001 | SRS-BUDGET-SYSTEM — Universal Resource Budgeting | `docs/requirements/SOMA-SRS-BUDGET-001.md` | Draft |
| SOMA-SRS-CAPSULEPORT-001 | SRS-CAPSULE-PORTABILITY — Agent Portability and Exchange | `docs/requirements/SOMA-SRS-CAPSULEPORT-001.md` | Draft |
| SOMA-SRS-CHATFLOW-001 | SRS-CHAT-FLOW-MASTER — Agent Architecture with Resilience | `docs/requirements/SOMA-SRS-CHATFLOW-001.md` | Draft |
| SOMA-SRS-CONTEXT-001 | SRS-CONTEXT-BUILDING — Prompt Assembly | `docs/requirements/SOMA-SRS-CONTEXT-001.md` | Draft |
| SOMA-SRS-DATAMODELS-001 | SRS-DATA-MODELS — Data Models and ORM Schema | `docs/requirements/SOMA-SRS-DATAMODELS-001.md` | Draft |
| SOMA-SRS-FEATFLAGS-001 | SRS-FEATURE-FLAGS — System Feature Toggles | `docs/requirements/SOMA-SRS-FEATFLAGS-001.md` | Draft |
| SOMA-SRS-MODELROUTING-001 | SRS-MODEL-ROUTING — LLM Model Selection | `docs/requirements/SOMA-SRS-MODELROUTING-001.md` | Draft |
| SOMA-SRS-MULTIMODAL-001 | SRS-MULTIMODAL — Image, Audio, and Diagram Generation | `docs/requirements/SOMA-SRS-MULTIMODAL-001.md` | Draft |
| SOMA-SRS-MULTITENANCY-001 | SRS-SECURITY-MULTITENANCY — Security and Tenant Isolation | `docs/requirements/SOMA-SRS-MULTITENANCY-001.md` | Draft |
| SOMA-SRS-PERMISSIONS-001 | SRS-PERMISSION-MATRIX — Permission Matrix and Role Administration | `docs/requirements/SOMA-SRS-PERMISSIONS-001.md` | Draft |
| SOMA-SRS-RLM-001 | SRS-RLM-ENGINE — Recursive Language Model Execution | `docs/requirements/SOMA-SRS-RLM-001.md` | Draft |
| SOMA-SRS-SAASINFRA-001 | SRS-SAAS-INFRASTRUCTURE — Soma Platform Deployment Architecture | `docs/requirements/SOMA-SRS-SAASINFRA-001.md` | Draft |
| SOMA-SRS-SOMABRAIN-001 | SRS-SOMABRAIN-INTEGRATION — L3 Cognitive Engine | `docs/requirements/SOMA-SRS-SOMABRAIN-001.md` | Draft |
| SOMA-SRS-SOVEREIGNTY-001 | SRS-650-LINE-SOVEREIGNTY — VIBE Rule 245 Enforcement | `docs/requirements/SOMA-SRS-SOVEREIGNTY-001.md` | Draft |
| SOMA-SRS-TESTBENCH-001 | SRS-TEST-WORKBENCH — Cross-Repository Test Audit | `docs/requirements/SOMA-SRS-TESTBENCH-001.md` | Draft |
| SOMA-SRS-TESTMODULES-001 | SRS-TEST-MODULES — Module-Based Test Suite Design | `docs/requirements/SOMA-SRS-TESTMODULES-001.md` | Draft |
| SOMA-SRS-TOOLS-001 | SRS-TOOL-SYSTEM — Tool Discovery and Execution | `docs/requirements/SOMA-SRS-TOOLS-001.md` | Draft |

### `docs/operations/`

| Identifier | Title | File | Status |
|---|---|---|---|
| SOMA-OPS-Soma Platform-001 | Soma Platform Standalone Deployment Guide | `docs/operations/SOMA-OPS-Soma Platform-001.md` | Draft |
| SOMA-OPS-DEPLOY-001 | Deployment Guide | `docs/operations/SOMA-OPS-DEPLOY-001.md` | Draft |
| SOMA-OPS-MODES-001 | Deployment Modes — Soma Platform vs STANDALONE | `docs/operations/SOMA-OPS-MODES-001.md` | Draft |
| SOMA-OPS-PLAN-001 | SomaAgent01 — Complete Deployment Plan | `docs/operations/SOMA-OPS-PLAN-001.md` | Draft |
| SOMA-OPS-READINESS-001 | SomaAgent01 Deployment Readiness Plan | `docs/operations/SOMA-OPS-READINESS-001.md` | Draft |
| SOMA-OPS-SOFTMODES-001 | Software Deployment Modes | `docs/operations/SOMA-OPS-SOFTMODES-001.md` | Draft |

Referenced images (not registered Markdown): `docs/operations/images/` — 5 PNGs.

### `docs/design/`

| Identifier | Title | File | Status |
|---|---|---|---|
| SOMA-CHAT-UI-001 | Agent Soma — Chat workspace UI/UX | `docs/design/SOMA-CHAT-UI-001.md` | (non-compliant — tracked gap) |
| SOMA-UI-BINDINGS-001 | UI mock control → live binding map | `docs/design/SOMA-UI-BINDINGS-001.md` | Draft |
| SOMA-UI-CATALOG-001 | Curated UI/UX catalog | `docs/design/SOMA-UI-CATALOG-001.md` | Draft |
| SOMA-UI-CHAT-WORKSPACE-001 | Complete Chat Workspace UI/UX | `docs/design/SOMA-UI-CHAT-WORKSPACE-001.md` | Draft |
| SOMA-UI-IA-001 | IA audit & single-home rules | `docs/design/SOMA-UI-IA-001.md` | Draft (body still claims authority — tracked gap) |
| SOMA-UI-IDREG-001 | Screen Identifier Allocation | `docs/design/SOMA-UI-IDREG-001.md` | Draft |
| SOMA-UI-MOCKUPS-001 | User Interface Mockups Index | `docs/design/SOMA-UI-MOCKUPS-001.md` | Draft |
| SOMA-UI-NAV-001 | Complete UI navigation map | `docs/design/SOMA-UI-NAV-001.md` | Draft |
| SOMA-UI-NAV-AUDIT-001 | Navigation audit — mocks vs `main.ts` routes | `docs/design/SOMA-UI-NAV-AUDIT-001.md` | Draft |
| SOMA-UI-PARITY-002 | UI/UX Feature Parity with Agent Zero | `docs/design/SOMA-UI-PARITY-002.md` | Draft |
| SOMA-UI-SCREENS-001 | Implemented screens, agent flows, mockup sync | `docs/design/SOMA-UI-SCREENS-001.md` | Draft |
| SOMA-UI-SKINS-001 | Capsule Skins — Theming Framework Specification | `docs/design/SOMA-UI-SKINS-001.md` | Draft |
| SOMA-UI-SPEC-001 | Soma Agent Definitive UI/UX Specification | `docs/design/SOMA-UI-SPEC-001.md` | Draft |
| SOMA-UI-SPEC-002 | Soma Agent UI/UX Complete Specification | `docs/design/SOMA-UI-SPEC-002.md` | Draft |
| SOMA-UI-TEMPLATE-001 | House ISO Template | `docs/design/SOMA-UI-TEMPLATE-001.md` | Draft |

`docs/design/mockups/` — **67 annex files** (`UI-S-00`…`UI-S-57`, `UI-X-01`…`UI-X-08`).
Annex class per SOMA-01-DOCS-001 §3.3.4; full list in `DOCUMENT-REGISTER.md`.

### `docs/modules/`

| Identifier | Title | File | Status |
|---|---|---|---|
| SOMA-MOD-ARCH-001 | Soma Agent Modular Architecture | `docs/modules/SOMA-MOD-ARCH-001.md` | Draft |
| SOMA-MOD-SPEC-001 | Soma Agent Module System Technical Specification | `docs/modules/SOMA-MOD-SPEC-001.md` | Draft |

### `docs/project/`

| Identifier | Title | File | Status |
|---|---|---|---|
| SOMA-PM-CHANGE-001 | Change Control Log | `docs/project/SOMA-PM-CHANGE-001.md` | Draft |
| SOMA-PM-CHARTER-001 | Soma Cognitive Triad Project Charter | `docs/project/SOMA-PM-CHARTER-001.md` | Approved |
| SOMA-PM-CLOSURE-001 | Project Closure Report | `docs/project/SOMA-PM-CLOSURE-001.md` | Draft |
| SOMA-PM-COMM-001 | Communication Plan | `docs/project/SOMA-PM-COMM-001.md` | Draft |
| SOMA-PM-DELIV-001 | Deliverables Register | `docs/project/SOMA-PM-DELIV-001.md` | Draft |
| SOMA-PM-MILE-001 | Milestone Tracker | `docs/project/SOMA-PM-MILE-001.md` | Draft |
| SOMA-PM-PLAN-TRIAD-001 | PLAN — Seamless Triad | `docs/project/SOMA-PM-PLAN-TRIAD-001.md` | Draft |
| SOMA-PM-RACI-001 | RACI Matrix | `docs/project/SOMA-PM-RACI-001.md` | Draft |
| SOMA-PM-SOW-001 | Soma Cognitive Triad — Full Scope of Work | `docs/project/SOMA-PM-SOW-001.md` | Approved |
| SOMA-PM-WBS-001 | Soma Cognitive Triad Work Breakdown Structure | `docs/project/SOMA-PM-WBS-001.md` | Draft |

### `docs/standards/`

| Identifier | Title | File | Status |
|---|---|---|---|
| SOMA-RAPID-DEVELOPMENT-001 | Rapid Development Plan + The Rules | `docs/standards/SOMA-RAPID-DEVELOPMENT-001.md` | Draft |
| SOMA-STD-CODING-001 | Vibe Coding Rules | `docs/standards/SOMA-STD-CODING-001.md` | Draft |
| SOMA-STD-CONFIG-001 | Configuration, Endpoints and Secret Resolution | `docs/standards/SOMA-STD-CONFIG-001.md` | Draft |
| SOMA-STD-TEMPLATE-001 | House ISO Template | `docs/standards/SOMA-STD-TEMPLATE-001.md` | Draft |
| SOMA-STD-TOKEN-001 | Soma Token Format Standard | `docs/standards/SOMA-STD-TOKEN-001.md` | Draft |
| SOMA-STD-TRIAD-001 | Shared triad rules | `docs/standards/SOMA-STD-TRIAD-001.md` | Draft |

### `docs/reports/`

| Identifier | Title | File | Status |
|---|---|---|---|
| SOMA-RPT-FEATMATRIX-001 | Agent Zero vs Soma Feature Comparison Matrix | `docs/reports/SOMA-RPT-FEATMATRIX-001.md` | Draft |
| SOMA-RPT-INVENTORY-001 | System Inventory | `docs/reports/SOMA-RPT-INVENTORY-001.md` | Draft |
| SOMA-RPT-REPO-001 | SomaAgent01 Deep Repo Analysis | `docs/reports/SOMA-RPT-REPO-001.md` | Obsolete |
| SOMA-RPT-STATUS-001 | Full code review, wiring status & UI/UX continuation plan | `docs/reports/SOMA-RPT-STATUS-001.md` | Draft |

### `docs/tasks/`

| Identifier | Title | File | Status |
|---|---|---|---|
| SOMA-TASK-AGENTIQ-001 | TASK-AGENTIQ: Governor Control Loop Implementation | `docs/tasks/SOMA-TASK-AGENTIQ-001.md` | Draft |
| SOMA-TASK-CONTEXT-001 | TASK-CONTEXT-BUILDING: 5-Lane Context Assembly | `docs/tasks/SOMA-TASK-CONTEXT-001.md` | Draft |
| SOMA-TASK-FLOW-001 | V3 Flow Master Task Tracker | `docs/tasks/SOMA-TASK-FLOW-001.md` | Draft |
| SOMA-TASK-HANDOFF-001 | Agent Handoff — SomaAgent01 Repository | `docs/tasks/SOMA-TASK-HANDOFF-001.md` | Obsolete |
| SOMA-TASK-MERGED-001 | Merged Tasks & Requirements | `docs/tasks/SOMA-TASK-MERGED-001.md` | Draft |
| SOMA-TASK-RLM-001 | TASK-RLM-ENGINE: Recursive Language Model Implementation | `docs/tasks/SOMA-TASK-RLM-001.md` | Draft |
| SOMA-TASK-SOMABRAIN-001 | TASK-SOMABRAIN: L3 Cognitive Engine Integration | `docs/tasks/SOMA-TASK-SOMABRAIN-001.md` | Draft |

### `docs/plans/`

| Identifier | Title | File | Notes |
|---|---|---|---|
| — | 100% Wiring Plan | `docs/plans/2026-10-03-100-percent-wiring.md` | Date-named (tracked gap) |
| — | Triad Full Integration | `docs/plans/2026-10-03-triad-full-integration.md` | Date-named (tracked gap) |
| — | RAPID TRIAD 001 | `docs/plans/2026-10-04-RAPID-TRIAD-001.md` | No Document Control (tracked gap) |
| — | AGENT BRIEFING — RAPID TRIAD 001 | `docs/plans/AGENT-BRIEFING-RAPID-TRIAD-001.md` | No Document Control (tracked gap) |
| — | Soma Triad — full handoff | `docs/plans/SOMA-AGENT-HANDOFF-001.md` | Incomplete DC (tracked gap) |
| SOMA-PM-PLAN-CHAT-COGNITION-001 | PLAN — Chat Cognition, Capsule-Owned Tools | `docs/plans/SOMA-PM-PLAN-CHAT-COGNITION-001.md` | Draft |
| — | SOMA-PM-PLAN-TRIAD-COMPLETION-002 | `docs/plans/SOMA-PM-PLAN-TRIAD-COMPLETION-002.md` | Broken DC shape (tracked gap) |
| SOMA-PM-RAPID-WIRING-001 | Full wiring plan: SomaAgent01 → SomaBrain | `docs/plans/SOMA-PM-RAPID-WIRING-001.md` | Draft |

`docs/plans/a2a/` — operational coordination files (`CLAIMS.md`, `INBOX.md`, `LEDGER.md`, `OUTBOX.md`).
Not ISO-controlled; registered as non-compliant tracked gaps under the procedure’s
“every `*.md` must appear in the register” rule.

## 4. How to keep this index honest

1. Source of truth is the **filesystem** under `docs/` plus Document Control headers in each file.
2. After add/rename/delete: run `make docs-register` then update the tables above from the register.
3. Never list a document that does not exist on disk.
4. Never omit a top-level `docs/` directory from §2.
5. Non-compliant files stay listed with an explicit gap note — do not hide them.
