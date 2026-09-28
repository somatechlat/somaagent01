# UI-S-14 — Instances

Screen UI-S-14 · Facet: Capsule · Route: NEW (not present in `webui/src/main.ts` today).
Source view per `SOMA-UI-IDREG-001.md`: NEW. Related: the chrome instance strip (UI-C-015).

## 1. ASCII wireframe — whole screen inside UI-S-00 chrome

```
┌─[capsule ▾] ‹capsule.name› [v‹semver›][‹lifecycle›]───────── IQ[──●──] AUTO[─●─] BUDGET[─●─] ⌘K─┐
│ derived (RO): temp ‹› max_tok ‹› rlm ‹› recall ‹› tier ‹› hitl ‹› tokens ‹› cost ‹› think ‹›      │
├─ Soul  Brain  Hands  Memory  Body  Governance ──────────────────────────────────────────────────┤
│ LEFT NAV │ WORKSPACE — Instances [1]                                    │ SURFACES x8             │
│  Chat    │ ┌────────────────────────────────────────────────────────┐  │ [Files][Tools][Browser] │
│  Capsule*│ │ FILTER [2] ‹status ▾│   SEARCH [3] ‹filter.instances…│  │  │ [Editor][Debug][Capsule]│
│  Module  │ │ ┌────────────────────────────────────────────────────┐ │  │ [Brain][Desktop†] †GATED│
│  Platform│ │ │ INSTANCE TABLE [4]                                 │ │  │                         │
│  Ops     │ │ │ ‹instance.id›  ‹status›  ‹ts›  ‹capsule.name›  [⋯]│ │  │                         │
│  Settings│ │ │ ‹instance.id›  ‹status›  ‹ts›  ‹capsule.name›  [⋯]│ │  │                         │
│          │ │ │ ‹instance.id›  ‹status›  ‹ts›  ‹capsule.name›  [⋯]│ │  │                         │
│          │ │ │ (scroll)                                           │ │  │                         │
│          │ │ └────────────────────────────────────────────────────┘ │  │                         │
│          │ │ DETAIL [5]  ‹instance.id› · ‹instance.status›          │  │                         │
│          │ │ [ Restart ] [6]     [ Stop ] [7]                       │  │                         │
│          │ └────────────────────────────────────────────────────────┘  │                         │
├──────────┴──────────────────────────────────────────────────────────────┴─────────────────────────┤
│ INSTANCES ‹instance.id› ‹instance.status› │ NEURO: DA ‹› 5-HT ‹› NE ‹› ACh ‹› │ synced ‹ts›      │
└───────────────────────────────────────────────────────────────────────────────────────────────────┘
```

## 2. Control map

| # | UI-C-* | control | notes |
|---|---|---|---|
| 1 | — | Workspace region (Instances) | Screen shell. |
| 2 | UI-C-069 | Status filter select | Instance states as stored. |
| 3 | UI-C-021 | Search | Filters the table live. |
| 4 | UI-C-084 | Instance table | Rows `‹instance.id›` / `‹status›` / `‹ts›` / `‹capsule.name›`. |
| 5 | UI-C-085 | Instance detail panel | Read-only fields from the instance record. |
| 5 | UI-C-028 | Row action menu (⋯) | Restart / Stop / Copy id. Stop opens UI-M-03. |
| 6 | UI-A-038 | Restart instance | Restarts the selection. |
| 7 | UI-A-039 | Stop instance | DESTRUCTIVE — always opens UI-M-03. |

## 3. State variants

- **loading** — Table shows 5 skeleton rows. Verbatim label: "Loading instances…"
- **empty** — `UI-C-023` verbatim: "No instances are running for this capsule."
  Empty under a filter verbatim: "No instances match this filter. Clear the filter to see all."
- **error** — `UI-C-024` verbatim: "Instances could not be loaded. Retry, or check that the
  somaAgent01 API is reachable."
- **permission-denied** — Restart/Stop disabled with inline reason
  "Instance actions require the operator role." `UI-C-025` verbatim:
  "You do not have permission to manage instances. Ask a platform admin for the operator role."
- **offline** — Table shows last cached page ("Showing the last synced page."); actions disabled
  with reason "Instance actions are unavailable offline." Chrome instance strip does the same.

## 4. Modal overlays

| Trigger | Modal | Contents |
|---|---|---|
| UI-A-039 Stop instance | UI-M-03 Dialog | "Stop ‹instance.id›? Running work will be interrupted." Cancel / Stop. |
| Table row open | UI-M-01 Drawer (420px) | Full instance record; ESC closes, focus trap. |
| — | UI-M-02 | Not used by this screen. |

## 5. Honesty notes

Instance ids, statuses and timestamps are store placeholders. The chrome instance strip and this
table read the same store — neither invents counts.

End of Document
