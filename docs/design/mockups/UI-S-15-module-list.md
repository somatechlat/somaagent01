# UI-S-15 — Module list

Screen UI-S-15 · Facet: Module · Route: NEW (not present in `webui/src/main.ts` today).
Source view per `SOMA-UI-IDREG-001.md`: NEW.

## 1. ASCII wireframe — whole screen inside UI-S-00 chrome

```
┌─[capsule ▾] ‹capsule.name› [v‹semver›][‹lifecycle›]───────── IQ[──●──] AUTO[─●─] BUDGET[─●─] ⌘K─┐
│ derived (RO): temp ‹› max_tok ‹› rlm ‹› recall ‹› tier ‹› hitl ‹› tokens ‹› cost ‹› think ‹›      │
├─ Soul  Brain  Hands  Memory  Body  Governance ──────────────────────────────────────────────────┤
│ LEFT NAV │ WORKSPACE — Modules [1]                                      │ SURFACES x8             │
│  Chat    │ ┌────────────────────────────────────────────────────────┐  │ [Files][Tools][Browser] │
│  Capsule │ │ SEARCH [2] ‹filter.modules…│  SOURCE [3] ‹source ▾│    │  │ [Editor][Debug][Capsule]│
│  Module* │ │ ┌────────────────────────────────────────────────────┐ │  │ [Brain][Desktop†] †GATED│
│  Platform│ │ │ MODULE GRID [4]                                    │ │  │                         │
│  Ops     │ │ │ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐│ │  │                         │
│  Settings│ │ │ │‹module.name› │ │‹module.name› │ │‹module.name› ││ │  │                         │
│          │ │ │ │‹module.ver›  │ │‹module.ver›  │ │‹module.ver›  ││ │  │                         │
│          │ │ │ │‹module.state›│ │‹module.state›│ │‹module.state›││ │  │                         │
│          │ │ │ │ [ Install ]  │ │ [ Installed ]│ │ [ Install ]  ││ │  │                         │
│          │ │ │ │ [⋯]          │ │ [ Configure ]│ │ [⋯]          ││ │  │                         │
│          │ │ │ └──────────────┘ └──────────────┘ └──────────────┘│ │  │                         │
│          │ │ └────────────────────────────────────────────────────┘ │  │                         │
│          │ └────────────────────────────────────────────────────────┘  │                         │
├──────────┴──────────────────────────────────────────────────────────────┴─────────────────────────┤
│ INSTANCES ‹instance.id› ‹instance.status› │ NEURO: DA ‹› 5-HT ‹› NE ‹› ACh ‹› │ synced ‹ts›      │
└───────────────────────────────────────────────────────────────────────────────────────────────────┘
```

## 2. Control map

| # | UI-C-* | control | notes |
|---|---|---|---|
| 1 | — | Workspace region (Module list) | Screen shell. |
| 2 | UI-C-021 | Search | Filters the grid live. |
| 3 | UI-C-086 | Source filter select | Registry sources as configured; no invented catalogue. |
| 4 | UI-C-087 | Module card grid | Cards show `‹module.name›` / `‹module.ver›` / `‹module.state›`. |
| 4 | UI-C-028 | Card menu (⋯) | Install / Uninstall / Open. Uninstall opens UI-M-03. |
| — | UI-A-040 | Install module | Per-card primary action; reflects in `‹module.state›`. |
| — | UI-A-041 | Uninstall module | DESTRUCTIVE — always opens UI-M-03. |
| — | UI-A-043 | Configure | Navigates to UI-S-16. |

## 3. State variants

- **loading** — Grid shows 6 skeleton cards. Verbatim label: "Loading modules…"
- **empty** — `UI-C-023` verbatim: "No modules are registered. Add a module source in Settings to browse modules."
  Empty under a filter verbatim: "No modules match this filter. Clear the filter to see all."
- **error** — `UI-C-024` verbatim: "Module registry could not be loaded. Retry, or check that the
  module source is reachable."
- **permission-denied** — Install/Uninstall disabled with inline reason
  "Module changes require the operator role." Grid remains readable; `UI-C-025` verbatim:
  "You do not have permission to manage modules. Ask a platform admin for the operator role."
- **offline** — Grid shows last cached page ("Showing the last synced page."); Install/Uninstall
  disabled with reason "Module actions are unavailable offline."

## 4. Modal overlays

| Trigger | Modal | Contents |
|---|---|---|
| UI-A-040 Install module | UI-M-03 Dialog | "Install ‹module.name› ‹module.ver›?" Cancel / Install. |
| UI-A-041 Uninstall module | UI-M-03 Dialog | "Uninstall ‹module.name›? Capabilities it provides will be removed." Cancel / Uninstall. |
| Configure | — | Navigates to UI-S-16; no modal. |
| — | UI-M-01 / UI-M-02 | Not used by this screen. |

## 5. Honesty notes

Module names, versions and states are store placeholders. No catalogue sizes or install counts
are invented.

End of Document
