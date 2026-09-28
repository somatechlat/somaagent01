# SOMA-STD-INDEX-001 — Documentation Tree Index

## Document Control

| Field | Value |
|---|---|
| Document Title | SOMA-STD-INDEX-001 — Documentation Tree Index |
| Document Identifier | SOMA-STD-INDEX-001 |
| Version | 1.0.0 |
| Date | 2026-09-28 |
| Status | Draft |
| Author | SomaTech Engineering |
| Approver | — |
| Classification | Internal |
| ISO Reference | ISO 9001:2015 — Quality Management Systems — Requirements |
| Next Review | 2026-12-28 |

## Revision History

| Version | Date | Author | Description |
|---|---|---|---|
| 1.0.0 | 2026-09-28 | SomaTech Engineering | Initial issue. Brought under ISO document control. |


| Field | Value |
|---|---|
| Document Title | Documentation Tree Index |
| Document Identifier | SOMA-STD-INDEX-001 |
| Version | 1.0.0 |
| Date | 2026-09-27 |
| Status | Draft |
| Author | SomaTech Engineering |
| Approver | — |
| Classification | Internal |
| ISO Reference | ISO 9001:2015 — Quality Management Systems — Requirements |
| Next Review | 2026-12-27 |
| Related | `docs/iso/SOMA-01-DOCS-001.md`, `docs/iso/DOCUMENT-REGISTER.md` |
| Source of truth | The working tree; inventory is regenerated from it |
| Audience | All contributors and any agent working in this repository |
| Scope | Every `*.md` under `docs/` |

## Revision History

| Version | Date | Author | Description |
|---|---|---|---|
| 1.0.0 | 2026-09-27 | SomaTech Engineering | Initial issue. Documentation tree renamed to the `SOMA-<DOMAIN>-<TYPE>-<NNN>` scheme and reorganised by domain. |

## 1. How this tree is organised

Every document is named by its Document Identifier:

```
SOMA-<DOMAIN>-<TYPE>-<NNN>.md
```

The **domain token decides the directory**, and the **filename stem is the identifier**.
The rules are in `docs/iso/SOMA-01-DOCS-001.md` §3.3 and are enforced by
`scripts/check_docs.py` (rules `C-01`…`C-12`). Compliance is checked with
`make docs-check`; the inventory below is regenerated with `make docs-register`.

## 2. Directories

| Directory | Domain | Contents |
|---|---|---|
| `docs/iso/` | ``01` / topic` | Controlled ISO-tier documents. The suite's authority: quality manual, procedures, assessments, and the register itself. |
| `docs/architecture/` | ``ARCH`` | System architecture descriptions and the invariants that must hold. |
| `docs/requirements/` | ``SRS`` | Software requirement specifications (SRS), one per subsystem or concern. |
| `docs/operations/` | ``OPS`` | Deployment modes, plans and runbooks. `images/` holds generated topology diagrams. |
| `docs/design/` | ``UI`` | UI/UX specification, parity plan and wireframes. |
| `docs/modules/` | ``MOD`` | The Capsule Module system: architecture and technical specification. |
| `docs/project/` | ``PM`` | Project management artefacts: charter, WBS, RACI, milestones, change log, SOW. |
| `docs/standards/` | ``STD`` | Coding rules, templates and format standards. These bind day-to-day work. |
| `docs/reports/` | ``RPT`` | Audits, analyses and comparison matrices. |
| `docs/tasks/` | ``TASK`` | Task lists, work packages and handoff notes. |

## 3. Documents by domain

### `docs/iso/`

| Identifier | Title | File |
|---|---|---|
| `SOMA-01-DOCS-002` | Document Register | `docs/iso/DOCUMENT-REGISTER.md` |
| `SOMA-01-AAAS-001` | Soma AAAS Deployment Specification | `docs/iso/SOMA-01-AAAS-001.md` |
| `SOMA-01-ARCH-001` | SomaAgent01 System Architecture Document | `docs/iso/SOMA-01-ARCH-001.md` |
| `SOMA-01-AUDIT-002` | SomaAgent01 Code-Verified Deep Audit Report | `docs/iso/SOMA-01-AUDIT-002.md` |
| `SOMA-COMPAT-001` | Soma Cognitive Triad Version Compatibility Matrix | `docs/iso/SOMA-01-COMPAT-001.md` |
| `SOMA-01-DOCS-001` | Document Control and Traceability Procedure | `docs/iso/SOMA-01-DOCS-001.md` |
| `SOMA-01-OPS-001` | SomaAgent01 Operations Runbook | `docs/iso/SOMA-01-OPS-001.md` |
| `SOMA-01-PROD-001` | SomaAgent01 Production Readiness Assessment | `docs/iso/SOMA-01-PROD-001.md` |
| `SOMA-01-QMS-001` | SomaAgent01 Quality Manual | `docs/iso/SOMA-01-QMS-001.md` |
| `SOMA-01-RELEASE-001` | SomaAgent01 v2.0.0 Release Notes | `docs/iso/SOMA-01-RELEASE-001.md` |
| `SOMA-01-RISK-001` | SomaAgent01 Risk Register | `docs/iso/SOMA-01-RISK-001.md` |
| `SOMA-01-SDP-001` | SomaAgent01 Software Development Plan | `docs/iso/SOMA-01-SDP-001.md` |
| `SOMA-01-SEC-001` | SomaAgent01 Security Assessment Report | `docs/iso/SOMA-01-SEC-001.md` |
| `SOMA-01-SRS-001` | SomaAgent01 Master Software Requirements Specification | `docs/iso/SOMA-01-SRS-001.md` |
| `SOMA-01-VV-001` | SomaAgent01 Verification and Validation Plan | `docs/iso/SOMA-01-VV-001.md` |
| `SOMA-A0-PARITY-001` | Soma × Agent Zero — Feature Parity Matrix, UI/UX Development Specification, Code Remediation & Ownership Plan | `docs/iso/SOMA-A0-PARITY-001.md` |
| `SOMA-BRAIN-COMPLIANCE-001` | SOMA-BRAIN-COMPLIANCE-001 | `docs/iso/SOMA-BRAIN-COMPLIANCE-001.md` |
| `SOMA-SETTINGS-MODEL-001` | Soma Settings Model and Configuration Inventory | `docs/iso/SOMA-SETTINGS-MODEL-001.md` |
| `SOMA-TRIAD-ARCH-001` | Soma Triad Architecture Description — Agent / Brain / Memory | `docs/iso/SOMA-TRIAD-ARCH-001.md` |

### `docs/architecture/`

| Identifier | Title | File |
|---|---|---|
| `—` | SOMA-ARCH-INVARIANTS-001 | `docs/architecture/SOMA-ARCH-INVARIANTS-001.md` |
| `SOMA-ARCH-REDESIGN-001` | Enterprise Architecture Redesign | `docs/architecture/SOMA-ARCH-REDESIGN-001.md` |

### `docs/requirements/`

| Identifier | Title | File |
|---|---|---|
| `—` | SOMA-SRS-AGENTIQ-001 | `docs/requirements/SOMA-SRS-AGENTIQ-001.md` |
| `—` | SOMA-SRS-ARCHPATTERNS-001 | `docs/requirements/SOMA-SRS-ARCHPATTERNS-001.md` |
| `—` | SOMA-SRS-BACKUP-001 | `docs/requirements/SOMA-SRS-BACKUP-001.md` |
| `—` | SOMA-SRS-BUDGET-001 | `docs/requirements/SOMA-SRS-BUDGET-001.md` |
| `—` | SOMA-SRS-CAPSULEPORT-001 | `docs/requirements/SOMA-SRS-CAPSULEPORT-001.md` |
| `—` | SOMA-SRS-CHATFLOW-001 | `docs/requirements/SOMA-SRS-CHATFLOW-001.md` |
| `—` | SOMA-SRS-CONTEXT-001 | `docs/requirements/SOMA-SRS-CONTEXT-001.md` |
| `—` | SOMA-SRS-DATAMODELS-001 | `docs/requirements/SOMA-SRS-DATAMODELS-001.md` |
| `—` | SOMA-SRS-FEATFLAGS-001 | `docs/requirements/SOMA-SRS-FEATFLAGS-001.md` |
| Withdrawn | SOMA-SRS-LAGOBILLING-001 | `docs/requirements/SOMA-SRS-LAGOBILLING-001.md` — **WITHDRAWN**: the external billing integration this specified does not exist in this system. Retained as a tombstone only. |
| `—` | SOMA-SRS-MODELROUTING-001 | `docs/requirements/SOMA-SRS-MODELROUTING-001.md` |
| `—` | SOMA-SRS-MULTIMODAL-001 | `docs/requirements/SOMA-SRS-MULTIMODAL-001.md` |
| `—` | SOMA-SRS-MULTITENANCY-001 | `docs/requirements/SOMA-SRS-MULTITENANCY-001.md` |
| `—` | SOMA-SRS-PERMISSIONS-001 | `docs/requirements/SOMA-SRS-PERMISSIONS-001.md` |
| `—` | SOMA-SRS-RLM-001 | `docs/requirements/SOMA-SRS-RLM-001.md` |
| `—` | SOMA-SRS-SAASINFRA-001 | `docs/requirements/SOMA-SRS-SAASINFRA-001.md` |
| `—` | SOMA-SRS-SOMABRAIN-001 | `docs/requirements/SOMA-SRS-SOMABRAIN-001.md` |
| `—` | SOMA-SRS-SOVEREIGNTY-001 | `docs/requirements/SOMA-SRS-SOVEREIGNTY-001.md` |
| `—` | SOMA-SRS-TESTBENCH-001 | `docs/requirements/SOMA-SRS-TESTBENCH-001.md` |
| `—` | SOMA-SRS-TESTMODULES-001 | `docs/requirements/SOMA-SRS-TESTMODULES-001.md` |
| `—` | SOMA-SRS-TOOLS-001 | `docs/requirements/SOMA-SRS-TOOLS-001.md` |

### `docs/operations/`

| Identifier | Title | File |
|---|---|---|
| `—` | SOMA-OPS-AAAS-001 | `docs/operations/SOMA-OPS-AAAS-001.md` |
| `—` | SOMA-OPS-DEPLOY-001 | `docs/operations/SOMA-OPS-DEPLOY-001.md` |
| `—` | SOMA-OPS-MODES-001 | `docs/operations/SOMA-OPS-MODES-001.md` |
| `—` | SOMA-OPS-PLAN-001 | `docs/operations/SOMA-OPS-PLAN-001.md` |
| `—` | SOMA-OPS-SOFTMODES-001 | `docs/operations/SOMA-OPS-SOFTMODES-001.md` |

### `docs/design/`

| Identifier | Title | File |
|---|---|---|
| `SOMA-UI-MOCKUPS-001` | Soma Agent Screen Mockups and Wireframes | `docs/design/SOMA-UI-MOCKUPS-001.md` |
| `—` | SOMA-UI-PARITY-002 | `docs/design/SOMA-UI-PARITY-002.md` |
| `SOMA-UI-SPEC-001` | Soma Agent Definitive UI/UX Specification | `docs/design/SOMA-UI-SPEC-001.md` |
| `SOMA-UI-UX-001` | Soma Agent UI/UX Complete Specification | `docs/design/SOMA-UI-SPEC-002.md` |

### `docs/modules/`

| Identifier | Title | File |
|---|---|---|
| `SOMA-MOD-ARCH-001` | Soma Agent Modular Architecture — Core vs Optional Modules | `docs/modules/SOMA-MOD-ARCH-001.md` |
| `SOMA-MOD-SPEC-001` | Soma Agent Module System Technical Specification | `docs/modules/SOMA-MOD-SPEC-001.md` |

### `docs/project/`

| Identifier | Title | File |
|---|---|---|
| `SOMA-PM-CHANGE-001` | Change Control Log | `docs/project/SOMA-PM-CHANGE-001.md` |
| `SOMA-PM-CHARTER-001` | Soma Cognitive Triad Project Charter | `docs/project/SOMA-PM-CHARTER-001.md` |
| `SOMA-PM-CLOSURE-001` | Project Closure Report | `docs/project/SOMA-PM-CLOSURE-001.md` |
| `SOMA-PM-COMM-001` | Communication Plan | `docs/project/SOMA-PM-COMM-001.md` |
| `SOMA-PM-DELIV-001` | Deliverables Register | `docs/project/SOMA-PM-DELIV-001.md` |
| `SOMA-PM-MILE-001` | Milestone Tracker | `docs/project/SOMA-PM-MILE-001.md` |
| `—` | SOMA-PM-PLAN-TRIAD-001 | `docs/project/SOMA-PM-PLAN-TRIAD-001.md` |
| `SOMA-PM-RACI-001` | RACI Matrix (Responsible, Accountable, Consulted, Informed) | `docs/project/SOMA-PM-RACI-001.md` |
| `SOMA-SOW-001` | Soma Cognitive Triad — Full Scope of Work | `docs/project/SOMA-PM-SOW-001.md` |
| `SOMA-PM-WBS-001` | Soma Cognitive Triad Work Breakdown Structure | `docs/project/SOMA-PM-WBS-001.md` |

### `docs/standards/`

| Identifier | Title | File |
|---|---|---|
| `—` | SOMA-STD-CODING-001 | `docs/standards/SOMA-STD-CODING-001.md` |
| `—` | SOMA-STD-TEMPLATE-001 | `docs/standards/SOMA-STD-TEMPLATE-001.md` |
| `—` | SOMA-STD-TOKEN-001 | `docs/standards/SOMA-STD-TOKEN-001.md` |

### `docs/reports/`

| Identifier | Title | File |
|---|---|---|
| `SOMA-FEAT-MATRIX-001` | Agent Zero vs Soma Feature Comparison Matrix | `docs/reports/SOMA-RPT-FEATMATRIX-001.md` |
| `—` | SOMA-RPT-INVENTORY-001 | `docs/reports/SOMA-RPT-INVENTORY-001.md` |
| `—` | SOMA-RPT-REPO-001 | `docs/reports/SOMA-RPT-REPO-001.md` |

### `docs/tasks/`

| Identifier | Title | File |
|---|---|---|
| `—` | SOMA-TASK-AGENTIQ-001 | `docs/tasks/SOMA-TASK-AGENTIQ-001.md` |
| `—` | SOMA-TASK-CONTEXT-001 | `docs/tasks/SOMA-TASK-CONTEXT-001.md` |
| `—` | SOMA-TASK-FLOW-001 | `docs/tasks/SOMA-TASK-FLOW-001.md` |
| `—` | SOMA-TASK-HANDOFF-001 | `docs/tasks/SOMA-TASK-HANDOFF-001.md` |
| `—` | SOMA-TASK-MERGED-001 | `docs/tasks/SOMA-TASK-MERGED-001.md` |
| `—` | SOMA-TASK-RLM-001 | `docs/tasks/SOMA-TASK-RLM-001.md` |
| `—` | SOMA-TASK-SOMABRAIN-001 | `docs/tasks/SOMA-TASK-SOMABRAIN-001.md` |


| Identifier | Title | File |
|---|---|---|

## 4. Where to start

| You want to… | Read |
|---|---|
| Know the rules that bind every document | `docs/iso/SOMA-01-DOCS-001.md` |
| Find a document | `docs/iso/DOCUMENT-REGISTER.md` |
| Know the quality policy | `docs/iso/SOMA-01-QMS-001.md` |
| Know the system architecture | `docs/iso/SOMA-01-ARCH-001.md`, `docs/architecture/SOMA-ARCH-INVARIANTS-001.md` |
| Understand settings and configuration | `docs/iso/SOMA-SETTINGS-MODEL-001.md` |
| Understand the UI/UX plan | `docs/design/SOMA-UI-PARITY-002.md` |
| Follow the day-to-day coding rules | `docs/standards/SOMA-STD-CODING-001.md` |
| Know the triad (Agent / SomaBrain / SomaFractalMemory) | `docs/iso/SOMA-TRIAD-ARCH-001.md` |

End of Document
