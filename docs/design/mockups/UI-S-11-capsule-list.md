# UI-S-11 — Capsule list

Screen UI-S-11 · Facet: Capsule · Route: `/workspace`
Source view per `SOMA-UI-IDREG-001.md`: `saas-workspace` (`webui/src/views/saas-workspace.ts`).
Route matches `webui/src/main.ts:396`.

## 1. ASCII wireframe — whole screen inside UI-S-00 chrome

```
┌─[capsule ▾] ‹capsule.name› [v‹semver›][‹lifecycle›]───────── IQ[──●──] AUTO[─●─] BUDGET[─●─] ⌘K─┐
│ derived (RO): temp ‹› max_tok ‹› rlm ‹› recall ‹› tier ‹› hitl ‹› tokens ‹› cost ‹› think ‹›      │
├─ Soul  Brain  Hands  Memory  Body  Governance ──────────────────────────────────────────────────┤
│ LEFT NAV │ WORKSPACE — Capsules [1]                                     │ SURFACES x8             │
│  Chat    │ ┌────────────────────────────────────────────────────────┐  │ [Files][Tools][Browser] │
│  Capsule*│ │ SEARCH [2] ‹filter.capsules…│  STATUS [3] ‹status ▾│   │  │ [Editor][Debug][Capsule]│
│  Module  │ │ SORT [4] ‹sort ▾│        [ + New capsule ] [5]         │  │ [Brain][Desktop†] †GATED│
│  Platform│ │ ┌────────────────────────────────────────────────────┐ │  │                         │
│  Ops     │ │ │ CAPSULE GRID [6]                                   │ │  │                         │
│  Settings│ │ │ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐   │ │  │                         │
│          │ │ │ │‹capsule.name│ │‹capsule.name│ │‹capsule.name│   │ │  │                         │
│          │ │ │ │v‹semver›    │ │v‹semver›    │ │v‹semver›    │   │ │  │                         │
│          │ │ │ │‹lifecycle›  │ │‹lifecycle›  │ │‹lifecycle›  │   │ │  │                         │
│          │ │ │ │  [ Open ]   │ │  [ Open ]   │ │  [ Open ]   │   │ │  │                         │
│          │ │ │ │  [⋯]        │ │  [⋯]        │ │  [⋯]        │   │ │  │                         │
│          │ │ │ └─────────────┘ └─────────────┘ └─────────────┘   │ │  │                         │
│          │ │ └────────────────────────────────────────────────────┘ │  │                         │
│          │ └────────────────────────────────────────────────────────┘  │                         │
├──────────┴──────────────────────────────────────────────────────────────┴─────────────────────────┤
│ INSTANCES ‹instance.id› ‹instance.status› │ NEURO: DA ‹› 5-HT ‹› NE ‹› ACh ‹› │ synced ‹ts›      │
└───────────────────────────────────────────────────────────────────────────────────────────────────┘
```

## 2. Control map

| # | UI-C-* | control | notes |
|---|---|---|---|
| 1 | — | Workspace region (Capsule list) | Screen shell. |
| 2 | UI-C-021 | Search | Filters the grid live. |
| 3 | UI-C-069 | Status filter select | Lifecycle states as stored. |
| 4 | UI-C-073 | Sort select | Fields actually sortable by the store. |
| 5 | UI-A-031 | Create capsule | Opens UI-M-03 dialog (name + confirm) → routes to UI-S-12. |
| 6 | UI-C-074 | Capsule card grid | Cards show `‹capsule.name›`, `v‹semver›`, `‹lifecycle›` only. |
| 6 | UI-C-028 | Card row menu (⋯) | Open / Duplicate / Archive. Archive opens UI-M-03. |

## 3. State variants

- **loading** — Grid shows 6 skeleton cards. Verbatim label: "Loading capsules…"
- **empty** — `UI-C-023` verbatim: "No capsules yet. Create your first capsule to get started."
  Empty under a filter verbatim: "No capsules match this filter. Clear the filter to see all."
- **error** — `UI-C-024` verbatim: "Capsules could not be loaded. Retry, or check that the
  somaAgent01 API is reachable."
- **permission-denied** — Create disabled with inline reason
  "Create capsule requires the capsule-editor role." Grid remains readable; `UI-C-025` verbatim:
  "You do not have permission to manage capsules. Ask a platform admin for the capsule-editor role."
- **offline** — Grid shows last cached page ("Showing the last synced page."); Create/Archive
  disabled with reason "Capsule actions are unavailable offline."

## 4. Modal overlays

| Trigger | Modal | Contents |
|---|---|---|
| UI-A-031 Create capsule | UI-M-03 Dialog | Name field + Create / Cancel. |
| Card menu → Archive | UI-M-03 Dialog | "Archive ‹capsule.name›?" Cancel / Archive. |
| Card Open | — | Navigates to UI-S-12; no modal. |
| — | UI-M-01 / UI-M-02 | Not used by this screen. |

## 5. Honesty notes

Card values are placeholders from the capsule store. Version chips show store values only —
no invented semver strings.

End of Document
