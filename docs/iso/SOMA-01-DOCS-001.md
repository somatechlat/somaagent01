# SOMA-01-DOCS-001 — Document Control and Traceability Procedure

## Document Control

| Field | Value |
|---|---|
| Document Title | Document Control and Traceability Procedure |
| Document Identifier | SOMA-01-DOCS-001 |
| Version | 1.2.0 |
| Date | 2026-09-27 |
| Status | Draft |
| Author | SomaTech Engineering |
| Approver | — |
| Classification | Internal |
| ISO Reference | ISO 9001:2015 — Quality Management Systems — Requirements |
| Next Review | 2026-12-27 |
| Related | `SOMA-01-QMS-001.md`, `SOMA-A0-PARITY-001.md`, `docs/standards/SOMA-STD-CODING-001.md`, `docs/standards/SOMA-STD-CONFIG-001.md` |
| Source of truth | This document, `docs/iso/DOCUMENT-REGISTER.md`, `scripts/check_docs.py` |
| Audience | All engineering contributors and any agent acting on this repository |

## Revision History

| Version | Date | Author | Description |
|---|---|---|---|
| 1.0.0 | 2026-09-27 | SomaTech Engineering | Initial issue. Establishes mandatory document control, identifier scheme, register, and automated compliance check. |
| 1.1.0 | 2026-09-27 | SomaTech Engineering | §3.3 rewritten as the `SOMA-<DOMAIN>-<TYPE>-<NNN>` scheme with a domain→directory map. Rule C-12 added (filename stem == identifier). Register generation automated via `scripts/gen_register.py`. Documentation tree renamed and reorganised to match. |
| 1.2.0 | 2026-09-28 | SomaTech Engineering | §3.3.4 added: annexed design artefacts under `docs/design/mockups/` use sub-identifier names, are inventoried as `Compliance = Annex`, and are exempt from C-03…C-09 and C-12. Register summary gained an Annexes row. |

## Normative References

| ID | Reference | Role |
|---|---|---|
| N-1 | SOMA-01-QMS-001 | Quality management system; §7 Document Reference Matrix is the suite registry |
| N-2 | ISO 9001:2015 | Clause 7.5 Documented information — control of documents and records |
| N-3 | SOMA-A0-PARITY-001 | Feature-clone-not-code-clone, Plan Gate, error-honesty rules |
| N-4 | PLAN-TRIAD-SEAMLESS | W5-3 requires Approver and Next Review on ISO documents |
| N-5 | docs/standards/SOMA-STD-CODING-001.md | Standing engineering rules that reference this procedure |
| N-5b | docs/standards/SOMA-STD-CONFIG-001.md | Configuration and service endpoint resolution standard |

---

## 1. Purpose and Scope

### 1.1 Purpose

This procedure makes every documented artefact in `docs/` **controlled**: identified, registered, versioned, traceable, and reviewable. It exists because ISO 9001:2015 clause 7.5 requires documented information to be controlled — and because this repository previously had **no automated enforcement** of that control.

Verification of the prior state (2026-09-27):

| Check | Result |
|---|---|
| Docs linter in `scripts/` | none — only `generate_somabrain_image.py`, `generate_somafractal_image.py` |
| Docs target in `Makefile` | none — `help dev dev-worker test check migrate build build-standalone up down clean health reset-infra` |
| Docs job in `.github/workflows/ci.yml` | none — lint, typecheck, unit-tests only |
| `Next Review` field in any existing document | absent from every document in the suite |
| Document register | none |

This procedure closes that gap.

### 1.2 Scope

Applies to **every** `*.md` file under `docs/`, without exception. The tree is organised by document domain (see §3.3.1):

| Directory | Holds |
|---|---|
| `docs/iso/` | Controlled ISO-tier documents (strictest tier) |
| `docs/architecture/` | Architecture descriptions and invariants |
| `docs/requirements/` | Software requirement specifications |
| `docs/operations/` | Deployment, runbooks, topology diagrams |
| `docs/design/` | UI/UX specification and wireframes |
| `docs/modules/` | Capsule Module system specifications |
| `docs/project/` | Plans, charters, work breakdown structures |
| `docs/standards/` | Coding rules, templates, format standards |
| `docs/reports/` | Audits, analyses, comparison matrices |
| `docs/tasks/` | Task lists, work packages, handoffs |

Files outside `docs/` (source code, tests, infrastructure) are out of scope for registration, but any document they reference from `docs/` must itself be registered.

### 1.3 Out of Scope

- Source code comments and docstrings
- Generated documentation output
- Git commit messages and pull request bodies
- Third-party vendored documentation

---

## 2. Normative Requirements

Requirements use **SHALL** (mandatory) and **SHALL NOT** (prohibited) per `SOMA-01-SRS-001` §2 convention.

| ID | Requirement | Priority | Source | Verification |
|---|---|---|---|---|
| REQ-DOCS-001 | Every `*.md` under `docs/` **SHALL** appear in `docs/iso/DOCUMENT-REGISTER.md` with a valid Document Identifier. Unregistered files **SHALL** fail the compliance check. | Must | N-2, 1.1 | Inspection (`scripts/check_docs.py`) |
| REQ-DOCS-002 | Every controlled document **SHALL** open with a `## Document Control` table containing, at minimum, the fields listed in §3.1. | Must | N-2 | Inspection |
| REQ-DOCS-003 | Every controlled document **SHALL** contain a `## Revision History` table with the exact columns `Version`, `Date`, `Author`, `Description`. | Must | N-2 | Inspection |
| REQ-DOCS-004 | Every controlled document **SHALL** carry a `Next Review` date. Documents past that date **SHALL** be flagged overdue by the register. | Must | N-4 | Inspection |
| REQ-DOCS-005 | The `Approver` field **SHALL** always be present. When unsigned its value **SHALL** be `—`. A blank or missing Approver is non-compliant. | Must | N-4 | Inspection |
| REQ-DOCS-006 | `Status` **SHALL** be one of `Draft`, `In Review`, `Approved`, `Obsolete`. `Classification` **SHALL** be one of `Internal`, `Confidential`. | Must | N-1 | Inspection |
| REQ-DOCS-007 | Any edit to a document whose Status is `Approved` **SHALL** bump its `Version`, append a `Revision History` row, and reset `Status` to `Draft`. Approved content **SHALL NOT** be silently overwritten. | Must | N-2 | Analysis (diff review) |
| REQ-DOCS-008 | Identifiers **SHALL** match the patterns in §3.3. A document or artefact identifier that does not match its declared kind **SHALL** fail the compliance check. | Must | N-1 | Inspection |
| REQ-DOCS-009 | The register **SHALL** agree with the QMS §7 Document Reference Matrix. Divergence **SHALL** fail the compliance check. | Must | N-1 | Inspection |
| REQ-DOCS-010 | Requirements-bearing documents **SHALL** include a traceability matrix mapping each requirement identifier to its verification method and status. | Must | N-2 | Inspection |
| REQ-DOCS-011 | Evidence claims **SHALL** cite `file:line` or an equivalent resolvable reference. Unsourced assertions **SHALL NOT** be presented as verified fact. | Must | N-3 | Inspection |
| REQ-DOCS-012 | Documents **SHALL NOT** claim a capability is complete without the evidence named in its acceptance criteria. For user interface work the evidence **SHALL** include Playwright results. | Must | N-3 | Analysis |
| REQ-DOCS-013 | The compliance check **SHALL** be runnable locally (`make docs-check`) and in continuous integration. | Must | this procedure | Test |
| REQ-DOCS-014 | Pre-existing documents that do not yet comply **SHALL** be listed as tracked findings with a remediation owner. They **SHALL NOT** be silently exempted from the register. | Must | this procedure | Inspection |
| REQ-DOCS-015 | A disabled control, feature or surface **SHALL** state its blocking reason in the document that specifies it. Placeholder copy such as "coming soon" **SHALL NOT** appear as a specification value. | Must | N-3 | Inspection |

---

## 3. Document Control Requirements

### 3.1 Mandatory Document Control fields

Every controlled document opens with a `## Document Control` table using these field names **exactly**. The names are inherited from `SOMA-01-QMS-001` and are not interchangeable with synonyms.

| Field | Required | Allowed values | Notes |
|---|---|---|---|
| `Document Title` | yes | free text | Human-readable title |
| `Document Identifier` | yes | per §3.3 | Matches the filename stem |
| `Version` | yes | `x.y.z` semver | Bumped per REQ-DOCS-007 |
| `Date` | yes | `YYYY-MM-DD` | Document issue date |
| `Status` | yes | `Draft` \| `In Review` \| `Approved` \| `Obsolete` | Closed set |
| `Author` | yes | free text | `SomaTech Engineering` by convention |
| `Approver` | yes | free text or `—` | Never blank, never omitted |
| `Classification` | yes | `Internal` \| `Confidential` | Closed set. This is the confidentiality marking; the field is **not** named "Confidentiality" |
| `ISO Reference` | yes | free text | Governing standard(s) |
| `Next Review` | yes | `YYYY-MM-DD` | Review due date |
| `Related` | no | document list | Cross-references |
| `Source of truth` | no | path or description | Authoritative artefact |
| `Audience` | no | free text | Intended readers |
| `Scope` | no | free text | Boundary of applicability |

**Fields that do not exist in this house style and SHALL NOT be invented:** `Effective Date`, `Distribution`, `Doc ID`, `Document ID`, `Revision` (use `Version`), `Confidentiality` (use `Classification`).

### 3.2 Revision History

Immediately after Document Control:

```markdown
## Revision History

| Version | Date | Author | Description |
|---|---|---|---|
| 1.0.0 | 2026-09-27 | SomaTech Engineering | Initial issue. |
```

Columns are exactly `Version`, `Date`, `Author`, `Description`. Every released version has one row. Rows are never deleted.

### 3.3 Identifier scheme

Every controlled document is named **by its Document Identifier**:

```
SOMA-<DOMAIN>-<TYPE>-<NNN>.md
         │       │      └── zero-padded sequence within (DOMAIN, TYPE)
         │       └── short uppercase token for the document's subject
         └── the domain token, which decides the directory
```

The **filename stem is the Document Identifier**. This is rule **C-12**.

#### 3.3.1 Domain → directory

| Domain | Meaning | Directory | Pattern |
|---|---|---|---|
| `01` | Platform ISO-tier controlled document | `docs/iso/` | `SOMA-01-<TYPE>-<NNN>` |
| — | Secondary series (topic-led) | `docs/iso/` | `SOMA-<TOPIC>-<NNN>` |
| `ARCH` | Architecture description & invariants | `docs/architecture/` | `SOMA-ARCH-<TYPE>-<NNN>` |
| `SRS` | Software requirement specification | `docs/requirements/` | `SOMA-SRS-<TOPIC>-<NNN>` |
| `SEC` | Security assessment & risk | `docs/security/` | `SOMA-SEC-<TOPIC>-<NNN>` |
| `OPS` | Operations, deployment, runbooks | `docs/operations/` | `SOMA-OPS-<TOPIC>-<NNN>` |
| `UI` | UI/UX specification & design | `docs/design/` | `SOMA-UI-<TYPE>-<NNN>` |
| `MOD` | Module system | `docs/modules/` | `SOMA-MOD-<TYPE>-<NNN>` |
| `PM` | Project management artefact | `docs/project/` | `SOMA-PM-<TYPE>-<NNN>` |
| `STD` | Standards, conventions, templates | `docs/standards/` | `SOMA-STD-<TOPIC>-<NNN>` |
| `RPT` | Report, analysis, comparison | `docs/reports/` | `SOMA-RPT-<TOPIC>-<NNN>` |
| `TASK` | Task list, handoff, work package | `docs/tasks/` | `SOMA-TASK-<TOPIC>-<NNN>` |

`<TYPE>` and `<TOPIC>` are uppercase `A–Z` and `0–9` only. `<NNN>` is exactly three digits.

Examples: `SOMA-01-QMS-001.md`, `SOMA-SRS-CHATFLOW-001.md`, `SOMA-UI-PARITY-002.md`, `SOMA-PM-WBS-001.md`.

#### 3.3.2 Sub-identifier kinds

| Kind | Pattern | Example |
|---|---|---|
| Screen | `UI-S-<NN>` | `UI-S-07` |
| Modal or overlay | `UI-M-<NN>` | `UI-M-02` |
| Surface | `UI-X-<NN>` | `UI-X-04` |
| Control | `UI-C-<NNN>` | `UI-C-014` |
| Action | `UI-A-<NNN>` | `UI-A-022` |
| User-facing feature | `UI-F-<NNN>` | `UI-F-031` |
| Requirement | `REQ-<CAT>-<NNN>` | `REQ-DOCS-001` |
| Acceptance test | `UIX-AT-<NN>` | `UIX-AT-03` |
| Evidence directory | `docs/iso/evidence/<Document-Identifier>/` | `docs/iso/evidence/SOMA-01-UIUX-001/` |

Collision control: `SOMA-A0-PARITY-001` already defines `UI-AT-01`…`UI-AT-08`. New user-interface acceptance tests **SHALL** use the `UIX-AT-NN` namespace and cross-reference the `UI-AT-*` series rather than renumbering it.

#### 3.3.3 Filename exceptions (exactly two)

| File | Identifier | Why it is an exception |
|---|---|---|
| `docs/iso/DOCUMENT-REGISTER.md` | `SOMA-01-DOCS-002` | Fixed machine contract — `scripts/check_docs.py` and `scripts/gen_register.py` locate the register by this path. |
| `docs/README.md` | `SOMA-STD-INDEX-001` | The documentation tree index. `README.md` is the universal repository-index convention and is read before any identifier is known. |

No other document **SHALL** make this exception. `scripts/check_docs.py` rule C-12 enforces the rest.

#### 3.3.4 Annexed design artefacts

Mockups are **annexes**, not standalone controlled documents. They live under `docs/design/mockups/` and are named by sub-identifier:

```
UI-S-<NN>-<slug>.md     one screen mockup
UI-X-<NN>-<slug>.md     one surface mockup
```

Annexes are inventoried in `docs/iso/DOCUMENT-REGISTER.md` with `Compliance = Annex` so that nothing under `docs/` is invisible, but they **SHALL NOT** carry a `## Document Control` or `## Revision History` table of their own. They are governed by the suite's controlled index document, `docs/design/SOMA-UI-MOCKUPS-001.md`, which does carry full document control.

The compliance check enforces exactly two things for an annex:

| Rule | Condition |
|---|---|
| C-01 | the annex is listed in the register |
| C-11 | the filename stem matches `UI-S-<NN>-<slug>` or `UI-X-<NN>-<slug>` |

Rules C-03 … C-09 and C-12 do not apply to annexes.

### 3.4 Status transitions

```
Draft ──► In Review ──► Approved ──► Obsolete
  ▲                        │
  └────── on edit ─────────┘
```

An `Approved` document that is edited **SHALL** return to `Draft` with a bumped `Version` and a new Revision History row.

---

## 4. The Document Register

`docs/iso/DOCUMENT-REGISTER.md` is the authoritative inventory. It **SHALL** list every `*.md` under `docs/` with:

| Column | Content |
|---|---|
| `Document Identifier` | per §3.3 |
| `File` | repository-relative path |
| `Title` | document title |
| `Version` | current version |
| `Status` | current status |
| `Approver` | approver or `—` |
| `Next Review` | review date or `MISSING` |
| `Compliance` | `Compliant` \| `Non-compliant` \| `Pending` |

The register **SHALL NOT** contain prose analysis. It is data. Interpretation lives in this document and in `SOMA-01-UIUX-004`.

---

## 5. Automated Compliance Check

### 5.1 Tooling

| Artefact | Location | Role |
|---|---|---|
| Check script | `scripts/check_docs.py` | Parses the register and every `docs/**/*.md`; emits findings; exits non-zero on failure |
| Register generator | `scripts/gen_register.py` | Regenerates `docs/iso/DOCUMENT-REGISTER.md` from the tree; the register is derived data, never hand-maintained |
| Make target | `make docs-check` / `make docs-register` | Local entry point |
| CI job | `.github/workflows/ci.yml` | Runs the check on every push and pull request |

### 5.2 Check rules

The script **SHALL** fail the build on any of:

| Rule | Condition |
|---|---|
| C-01 | A `docs/**/*.md` file is not listed in the register |
| C-02 | A registered file does not exist on disk |
| C-03 | A controlled document lacks a `## Document Control` table |
| C-04 | A required field from §3.1 is missing or empty |
| C-05 | `Status` is outside the closed set |
| C-06 | `Classification` is outside the closed set |
| C-07 | `Approver` is blank (an em dash `—` is valid) |
| C-08 | `Next Review` is missing or not a valid date |
| C-09 | A `## Revision History` table is missing or has the wrong columns |
| C-10 | The register and QMS §7 Document Reference Matrix disagree on the set of ISO-series identifiers |
| C-11 | A `Document Identifier` does not match the §3.3 pattern for its file location |
| C-12 | A document's filename stem is not its `Document Identifier` (§3.3.3 exceptions excepted) |

The script **SHALL** report (without failing the build) documents that are registered but non-compliant, so that legacy gaps remain visible rather than hidden.

### 5.3 Failure output

Findings are printed one per line as `RULE | file | message`. A summary line reports compliant, non-compliant and unregistered counts. Exit code is `0` only when there are no failing rules.

---

## 6. Traceability

### 6.1 Chain

Every user-facing feature traces through exactly one chain:

```
REQ-* ──► UI-F-* ──► UI-S-* ──► UI-C-* / UI-A-* ──► component ──► API / store ──► UIX-AT-*
```

The matrix lives in `SOMA-01-UIUX-004` in the house format:

```markdown
| Requirement Category | Count | Implemented | Tested | Coverage |
|---|---|---|---|---|
| … | … | … | … | … |
| **TOTAL** | **…** | **…** | **…** | **…** |
```

### 6.2 Bidirectionality

- Every `UI-F-*` **SHALL** name its screen and at least one acceptance test.
- Every `UI-S-*` **SHALL** list its features.
- Every `UI-M-*` **SHALL** be opened by at least one screen.
- Every `UIX-AT-*` **SHALL** name the feature it verifies.

A feature with no test is `NOT YET`, not omitted.

---

## 7. Relationship to Other Rules

| Document | Relationship |
|---|---|
| `SOMA-01-QMS-001` §7 | Suite registry. This procedure is registered there. §7 and `DOCUMENT-REGISTER.md` **SHALL** agree (REQ-DOCS-009). |
| `docs/standards/SOMA-STD-CODING-001.md` | Carries the standing day-to-day rule. It **SHALL** reference this procedure rather than restate it. |
| `docs/standards/SOMA-STD-CONFIG-001.md` | Carries the configuration / endpoint resolution rule. It **SHALL** reference this procedure rather than restate it. |
| `SOMA-A0-PARITY-001` | Supplies the error-honesty and Plan Gate rules that this procedure makes checkable (REQ-DOCS-012, REQ-DOCS-015). |

`SOMA-STD-CODING-001.md` historically described documentation as *"ISO-style Documenter (clarity, not enforcement)"*. That statement is superseded: documentation control is now **enforced** by REQ-DOCS-001 through REQ-DOCS-015 and `scripts/check_docs.py`.

---

## 8. Acceptance Criteria

| Criterion | Target | Current |
|---|---|---|
| `scripts/check_docs.py` exists and exits non-zero on a violation | yes | Pending |
| `make docs-check` runs the check | yes | Pending |
| CI runs the check on push and pull request | yes | Pending |
| Register lists every `docs/**/*.md` | 100% | Pending |
| Every controlled document has Document Control and Revision History | 100% of new documents | Pending |
| Every controlled document has `Approver` and `Next Review` | 100% of new documents | Pending |
| Register and QMS §7 agree | zero divergence | Pending |
| Pre-existing gaps listed as tracked findings | yes, not silently exempted | Pending |

---

## 9. Document Reference Matrix

This procedure is registered in `SOMA-01-QMS-001` §7 and in `docs/iso/DOCUMENT-REGISTER.md`.

| Document | Identifier | ISO Reference | Purpose |
|---|---|---|---|
| Document Control and Traceability Procedure | SOMA-01-DOCS-001 | ISO 9001:2015 clause 7.5 | Control of documented information |

End of Document
