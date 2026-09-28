# UI-S-03 — Hands — tools & capabilities

Screen UI-S-03 · Facet: Hands · Route: `/tools`
Source view per `SOMA-UI-IDREG-001.md`: `saas-feature-catalog` (`webui/src/views/saas-feature-catalog.ts`).
Route matches `webui/src/main.ts:432`.

## 1. ASCII wireframe — whole screen inside UI-S-00 chrome

```
┌─[capsule ▾] ‹capsule.name› [v‹semver›][‹lifecycle›]───────── IQ[──●──] AUTO[─●─] BUDGET[─●─] ⌘K─┐
│ derived (RO): temp ‹› max_tok ‹› rlm ‹› recall ‹› tier ‹› hitl ‹› tokens ‹› cost ‹› think ‹›      │
├─ Soul  Brain  ( Hands )  Memory  Body  Governance ──────────────────────────────────────────────┤
│ LEFT NAV │ WORKSPACE — Hands [1]                                       │ SURFACES x8             │
│  Chat    │ ┌────────────────────────────────────────────────────────┐  │ [Files][Tools][Browser] │
│  Capsule │ │ SEARCH [2] ‹filter.tools…│   KIND [3] ‹kind ▾│         │  │ [Editor][Debug][Capsule]│
│  Module  │ │ ┌──────────────────────────────┐ ┌────────────────────┐│  │ [Brain][Desktop†] †GATED│
│  Platform│ │ │ TOOL LIST [4]                │ │ TOOL DETAIL [5]    ││  │                         │
│  Ops     │ │ │  ‹tool.name›        [on/off] │ │ ‹tool.name›        ││  │                         │
│  Settings│ │ │  ‹tool.name›        [on/off] │ │ ‹tool.description› ││  │                         │
│          │ │ │  ‹tool.name›        [on/off] │ │ capability ‹›      ││  │                         │
│          │ │ │  (scroll)                    │ │ approval ‹hitl ‹›  ││  │                         │
│          │ │ └──────────────────────────────┘ │ [ Enable ] [6]     ││  │                         │
│          │ │                                   │ [ Disable ] [7]    ││  │                         │
│          │ │ CAPABILITY FILTER [8] [api][ui][agent]…               │  │                         │
│          │ └────────────────────────────────────────────────────────┘  │                         │
├──────────┴──────────────────────────────────────────────────────────────┴─────────────────────────┤
│ INSTANCES ‹instance.id› ‹instance.status› │ NEURO: DA ‹› 5-HT ‹› NE ‹› ACh ‹› │ synced ‹ts›      │
└───────────────────────────────────────────────────────────────────────────────────────────────────┘
```

## 2. Control map

| # | UI-C-* | control | notes |
|---|---|---|---|
| 1 | — | Workspace region (Hands) | Screen shell. |
| 2 | UI-C-021 | Tool search | Filters UI-C-041 live. |
| 3 | UI-C-041 | Kind filter select | Options from the capability registry. |
| 4 | UI-C-042 | Tool toggle list | Each row: name + enable switch + status chip `‹tool.status›`. |
| 5 | UI-C-043 | Tool detail panel | Read-only description, capability link, approval mode (`require_hitl ‹›` readout). |
| 6 | UI-A-013 | Enable tool | Idempotent; reflects on the instance strip after sync. |
| 7 | UI-A-014 | Disable tool | Destructive confirm via UI-M-03 when the tool is currently in use. |
| 8 | UI-C-044 | Capability filter chips | Multi-select; narrows the list by capability kind. |

## 3. State variants

- **loading** — List shows 6 skeleton rows; detail panel verbatim: "Select a tool to see details."
- **empty** — `UI-C-023` verbatim: "No tools match this filter. Clear the filter, or install a module
  that provides tools." With no filter applied: "No tools are registered for this capsule yet."
- **error** — `UI-C-024` verbatim: "Tool registry could not be loaded. Retry, or check that the
  somaAgent01 API is reachable."
- **permission-denied** — Toggles render off and locked; `UI-C-025` verbatim:
  "You do not have permission to change tools. Ask a platform admin for the capsule-editor role."
  Detail panel remains readable.
- **offline** — Toggles disabled with inline reason "Tool changes are unavailable offline."
  Chrome offline banner is shown.

## 4. Modal overlays

| Trigger | Modal | Contents |
|---|---|---|
| UI-A-014 Disable while in use | UI-M-03 Dialog | "Disable ‹tool.name› while it is in use?" Cancel / Disable. |
| Tool row (open detail larger) | UI-M-01 Drawer (420px) | Same content as UI-C-043; ESC closes, focus trap. |
| — | UI-M-02 | Not used by this screen. |

## 5. Honesty notes

Tool names, descriptions and statuses are store placeholders (`‹tool.name›`). Approval and HITL
figures are readouts of `require_hitl` / `tool_approval` and stay greyed — they are derived
AgentIQ settings and are never editable here.

End of Document
