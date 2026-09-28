# SOMA-UI-TEMPLATE-001 — House ISO Template

## Document Control

| Field | Value |
|---|---|
| Document Title | House ISO Template |
| Document Identifier | SOMA-UI-TEMPLATE-001 |
| Version | 1.0.0 |
| Date | 2026-09-28 |
| Status | Draft |
| Author | SomaTech Engineering |
| Approver | — |
| Classification | Internal |
| ISO Reference | ISO 9001:2015 — Quality Management Systems — Requirements |
| Next Review | 2026-12-28 |
| Related | `SOMA-01-DOCS-001.md`, `SOMA-01-UIUX-001.md`…`UIUX-005.md`, `SOMA-UI-MOCKUPS-001.md` |
| Source of truth | This document; `scripts/check_docs.py` field rules |
| Audience | Anyone authoring or reviewing a UI/UX suite document |
| Scope | Document Control shape, Revision History shape, honesty rules, per-screen block shape |

## Revision History

| Version | Date | Author | Description |
|---|---|---|---|
| 1.0.0 | 2026-09-28 | SomaTech Engineering | Initial issue. Promoted from a working artefact to a controlled document. |

## Normative References

| ID | Reference | Role |
|---|---|---|
| N-1 | SOMA-01-DOCS-001 | Document control and traceability procedure (the enforcer) |
| N-2 | SOMA-01-QMS-001 | Quality management system; field names inherited from here |
| N-3 | SOMA-A0-PARITY-001 | Honesty rules the template carries forward |
| N-4 | SOMA-UI-IDREG-001 | Authoritative ID allocation |

---

## 1. Purpose and Scope

This document is the **binding authoring template** for every file the UI/UX suite produces.
`scripts/check_docs.py` enforces its Document Control and Revision History shape; the honesty
rules in §4 are enforced by review against `SOMA-A0-PARITY-001`.

A document that departs from this template is non-compliant unless the departure is declared
in `SOMA-01-DOCS-001` §3.3.3 filename exceptions or §3.3.4 annexed design artefacts.

## 2. The controlled-document shape

The template body below is normative for standalone controlled documents. Annexed design
artefacts under `docs/design/mockups/` are exempt from Document Control (see
`SOMA-01-DOCS-001` §3.3.4) but **SHALL** still follow the honesty rules in §4.

Every controlled document MUST follow this exact shape. `scripts/check_docs.py` enforces it.

```markdown
# <DOCUMENT-IDENTIFIER> — <Title Case Name>

## Document Control

| Field | Value |
|---|---|
| Document Title | <Title Case Name> |
| Document Identifier | SOMA-01-UIUX-00N |
| Version | 1.0.0 |
| Date | 2026-09-28 |
| Status | Draft |
| Author | SomaTech Engineering |
| Approver | — |
| Classification | Internal |
| ISO Reference | ISO 9001:2015 — Quality Management Systems — Requirements |
| Next Review | 2026-12-28 |
| Related | `SOMA-01-QMS-001.md`, `SOMA-A0-PARITY-001.md`, `SOMA-01-UIUX-001.md` |
| Source of truth | <path> |
| Audience | <who> |
| Scope | <boundary> |

## Revision History

| Version | Date | Author | Description |
|---|---|---|---|
| 1.0.0 | 2026-09-28 | SomaTech Engineering | Initial issue. |

## Normative References

| ID | Reference | Role |
|---|---|---|
| N-1 | SOMA-01-QMS-001 | Quality management system |
| N-2 | SOMA-01-DOCS-001 | Document control and traceability procedure |
| N-3 | SOMA-A0-PARITY-001 | Feature clone never code clone; Plan Gate; honesty rules |
| N-4 | SOMA-01-UIUX-001 | Screen and feature specification (the master) |
| N-5 | SOMA-UI-IDREG-001.md | Authoritative ID allocation |

## 1. Purpose and Scope
...
## N. ...
...

End of Document
```

## Rules the checker enforces (C-01..C-12)

1. Filename stem MUST equal the Document Identifier (e.g. `SOMA-01-UIUX-001.md`).
2. Fields above are the ONLY Document Control field names. NEVER use "Effective Date",
   "Distribution", "Doc ID", "Document ID", or "Confidentiality" (use `Classification`).
3. `Status` ∈ `Draft | In Review | Approved | Obsolete`.
4. `Classification` ∈ `Internal | Confidential`.
5. `Approver` is always present; `—` when unsigned. Never blank.
6. `Next Review` is `YYYY-MM-DD` and must be in the future.
7. Revision History columns are EXACTLY `Version | Date | Author | Description`.
8. Close every document with `End of Document` on its own line.
9. H1 is `# <ID> — <Title Case>`. Never ALL CAPS.

## Honesty rules (from SOMA-A0-PARITY-001) — binding on every screen spec

- NEVER write "coming soon" as a specification value. A disabled control states its blocking reason.
- NEVER invent metrics, counts or API shapes. Cite `file:line` for every claim about current code.
- Every control row carries a `disabled-when` and a `disabled-reason`. A disabled control with no
  reason is a compliance failure.
- Secrets are shown as a masked placeholder plus "rotate in Vault" — never a value.
- The `desktop` surface (UI-X-08) is GATED: "Requires a remote-desktop capability in somaAgent01.
  Not available today."
- Derived AgentIQ settings (temperature, max_tokens, rlm_iterations, recall_limit, model_tier,
  brain_query_enabled, require_hitl, tool_approval, egress_allowed, token_limit, cost_tier,
  thinking_budget) are READ-ONLY readouts beside the three knobs. Never editable.

## Per-screen block shape (required in UIUX-001 and referenced by mockups)

```
### UI-S-<nn> — <Screen name>

| Field | Value |
|---|---|
| Screen Identifier | UI-S-<nn> |
| Route | /… |
| Facet | Soul \| Brain \| Hands \| Memory \| Body \| Governance \| Chat \| Capsule \| Module \| Platform \| Auth \| Ops \| Voice \| Settings |
| Primary actor | … |
| Stores | … |
| APIs | … |
| Related | UI-M-*, UI-C-*, UI-A-*, UI-F-* |

**Purpose.** one sentence.

**Regions.** left rail / workspace / right rail — what each holds.

**Controls.**
| UI-C-* | control | type | default | validation | disabled-when | disabled-reason |

**Actions.**
| UI-A-* | action | trigger | effect | confirmation | undo |

**States.** loading | empty | error | permission-denied | offline — what renders, verbatim copy

**Features.** UI-F-* list

**Trace.** components | API | UIX-AT-*

**Honesty notes.** what must NOT be faked here
```

End of Document
