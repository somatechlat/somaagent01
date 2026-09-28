# UI-S-17 — Capability registry

Screen UI-S-17 · Facet: Module · Route: NEW (not present in `webui/src/main.ts` today).
Source view per `SOMA-UI-IDREG-001.md`: NEW.

## 1. ASCII wireframe — whole screen inside UI-S-00 chrome

```
┌─[capsule ▾] ‹capsule.name› [v‹semver›][‹lifecycle›]───────── IQ[──●──] AUTO[─●─] BUDGET[─●─] ⌘K─┐
│ derived (RO): temp ‹› max_tok ‹› rlm ‹› recall ‹› tier ‹› hitl ‹› tokens ‹› cost ‹› think ‹›      │
├─ Soul  Brain  Hands  Memory  Body  Governance ──────────────────────────────────────────────────┤
│ LEFT NAV │ WORKSPACE — Capability registry [1]                           │ SURFACES x8             │
│  Chat    │ ┌────────────────────────────────────────────────────────┐  │ [Files][Tools][Browser] │
│  Capsule │ │ SEARCH [2] ‹filter.capabilities…│  KIND [3] ‹kind ▾│   │  │ [Editor][Debug][Capsule]│
│  Module* │ │ ┌────────────────────────────────────────────────────┐ │  │ [Brain][Desktop†] †GATED│
│  Platform│ │ │ CAPABILITY TABLE [4]                               │ │  │                         │
│  Ops     │ │ │ ‹capability.name›  ‹kind›  ‹provider›  ‹state›    │ │  │                         │
│  Settings│ │ │ ‹capability.name›  ‹kind›  ‹provider›  ‹state›    │ │  │                         │
│          │ │ │ ‹capability.name›  ‹kind›  ‹provider›  ‹state›    │ │  │                         │
│          │ │ │ (scroll)                                           │ │  │                         │
│          │ │ └────────────────────────────────────────────────────┘ │  │                         │
│          │ │ [ Register capability ] [5]   [ Refresh ] [6]          │  │                         │
│          │ │ source: ‹registry.source›   last scan ‹ timestamp ›   │  │                         │
│          │ └────────────────────────────────────────────────────────┘  │                         │
├──────────┴──────────────────────────────────────────────────────────────┴─────────────────────────┤
│ INSTANCES ‹instance.id› ‹instance.status› │ NEURO: DA ‹› 5-HT ‹› NE ‹› ACh ‹› │ synced ‹ts›      │
└───────────────────────────────────────────────────────────────────────────────────────────────────┘
```

## 2. Control map

| # | UI-C-* | control | notes |
|---|---|---|---|
| 1 | — | Workspace region (Capability registry) | Screen shell. |
| 2 | UI-C-021 | Capability search | Filters the table live. |
| 3 | UI-C-094 | Kind filter select | Kinds as the registry stores them. |
| 4 | UI-C-095 | Capability table | Rows `‹capability.name›` / `‹kind›` / `‹provider›` / `‹state›`. |
| 4 | UI-C-028 | Row action menu (⋯) | Open / Bind / Unbind. Unbind opens UI-M-03. |
| 5 | UI-A-045 | Register capability | Opens UI-M-03 dialog with the registration fields. |
| 6 | UI-A-004 | Refresh | Re-scans the registry; updates `last scan ‹ timestamp ›`. |

## 3. State variants

- **loading** — Table shows 5 skeleton rows. Verbatim label: "Loading capabilities…"
- **empty** — `UI-C-023` verbatim: "No capabilities registered. Register a capability, or install a module that provides one."
  Empty under a filter verbatim: "No capabilities match this filter. Clear the filter to see all."
- **error** — `UI-C-024` verbatim: "Capability registry could not be loaded. Retry, or check that the
  somaAgent01 API is reachable."
- **permission-denied** — Register/Unbind disabled with inline reason
  "Registry changes require the operator role." Table remains readable; `UI-C-025` verbatim:
  "You do not have permission to change the capability registry. Ask a platform admin for the operator role."
- **offline** — Table shows last cached page ("Showing the last synced page."); Register/Refresh
  disabled with reason "Registry actions are unavailable offline."

## 4. Modal overlays

| Trigger | Modal | Contents |
|---|---|---|
| UI-A-045 Register capability | UI-M-03 Dialog | Name / kind / provider fields + Register / Cancel. |
| Row → Unbind | UI-M-03 Dialog | "Unbind ‹capability.name› from its hook?" Cancel / Unbind. |
| Row → Open | — | Navigates to UI-S-18; no modal. |
| — | UI-M-01 / UI-M-02 | Not used by this screen. |

## 5. Honesty notes

Capability names, kinds, providers and states are store placeholders. Registry source and scan
timestamps are placeholders too — no invented catalogue statistics.

End of Document
