# UI-S-16 — Module detail & config

Screen UI-S-16 · Facet: Module · Route: NEW (not present in `webui/src/main.ts` today).
Source view per `SOMA-UI-IDREG-001.md`: NEW.

## 1. ASCII wireframe — whole screen inside UI-S-00 chrome

```
┌─[capsule ▾] ‹capsule.name› [v‹semver›][‹lifecycle›]───────── IQ[──●──] AUTO[─●─] BUDGET[─●─] ⌘K─┐
│ derived (RO): temp ‹› max_tok ‹› rlm ‹› recall ‹› tier ‹› hitl ‹› tokens ‹› cost ‹› think ‹›      │
├─ Soul  Brain  Hands  Memory  Body  Governance ──────────────────────────────────────────────────┤
│ LEFT NAV │ WORKSPACE — Module detail [1]                                 │ SURFACES x8             │
│  Chat    │ ┌────────────────────────────────────────────────────────┐  │ [Files][Tools][Browser] │
│  Capsule │ │ ‹module.name›  ‹module.ver›  ‹module.state›  [on/off] [2]│  │ [Editor][Debug][Capsule]│
│  Module* │ │ ABOUT [3]  ‹module.description›                          │  │ [Brain][Desktop†] †GATED│
│  Platform│ │ CONFIG [4]                                               │  │                         │
│  Ops     │ │  ‹config.key›  ‹config.value›                            │  │                         │
│  Settings│ │  ‹config.key›  sk-••••••••aBcD   (rotate in Vault)       │  │                         │
│          │ │  ‹config.key›  ‹config.value›                            │  │                         │
│          │ │ DEPENDENCIES [5]  ‹dep.name› ‹dep.state›  ‹dep.name› ‹dep.state›│                   │
│          │ │ HEALTH [6]  ‹ live value ›   as of ‹ timestamp ›         │  │                         │
│          │ │ [ Save config ] [7]    [ Uninstall ] [8]                 │  │                         │
│          │ └────────────────────────────────────────────────────────┘  │                         │
├──────────┴──────────────────────────────────────────────────────────────┴─────────────────────────┤
│ INSTANCES ‹instance.id› ‹instance.status› │ NEURO: DA ‹› 5-HT ‹› NE ‹› ACh ‹› │ synced ‹ts›      │
└───────────────────────────────────────────────────────────────────────────────────────────────────┘
```

## 2. Control map

| # | UI-C-* | control | notes |
|---|---|---|---|
| 1 | — | Workspace region (Module detail) | Screen shell. |
| 2 | UI-C-088 | Module enable toggle | Bound to `‹module.state›`. |
| 3 | UI-C-089 | About panel | Read-only `‹module.description›`. |
| 4 | UI-C-090 | Config form | One row per `‹config.key›`. Secret-typed keys render masked (see wireframe). |
| 5 | UI-C-091 | Dependency list | Read-only `‹dep.name›` / `‹dep.state›` chips. |
| 6 | UI-C-092 | Health readout | READ-ONLY `‹ live value ›` + `‹ timestamp ›`. |
| 7 | UI-A-042 | Save config | Writes module config; secrets are never written back in clear. |
| 8 | UI-A-041 | Uninstall module | DESTRUCTIVE — always opens UI-M-03. |

## 3. State variants

- **loading** — Config form skeleton. Verbatim label: "Loading module…"
- **empty** — Config section verbatim: "This module has no configuration."
  Dependencies verbatim: "No dependencies recorded."
- **error** — `UI-C-024` verbatim: "Module could not be loaded. It may have been uninstalled."
  Save failure verbatim: "Config was not saved. Your values are still here — try again."
- **permission-denied** — Config read-only; Save/Uninstall disabled with inline reason
  "Module changes require the operator role." `UI-C-025` verbatim:
  "You do not have permission to configure this module. Ask a platform admin for the operator role."
- **offline** — Save/Uninstall/toggle disabled with inline reason "Module actions are unavailable offline."
  Health readout keeps its last value and timestamp.

## 4. Modal overlays

| Trigger | Modal | Contents |
|---|---|---|
| UI-A-041 Uninstall module | UI-M-03 Dialog | "Uninstall ‹module.name›? Capabilities it provides will be removed." Cancel / Uninstall. |
| Secret config key "reveal" | UI-M-03 Dialog | Refused inline instead: the row shows "Rotate in Vault" — the UI never reveals a secret. |
| — | UI-M-01 / UI-M-02 | Not used by this screen. |

## 5. Honesty notes

Secret-typed config values render as `sk-••••••••aBcD` with a "rotate in Vault" note — never a
real value, and never a reveal control. Health figures are `‹ live value ›` placeholders.

End of Document
