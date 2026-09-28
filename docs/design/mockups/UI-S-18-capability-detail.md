# UI-S-18 — Capability detail & hook bindings

Screen UI-S-18 · Facet: Module · Route: NEW (not present in `webui/src/main.ts` today).
Source view per `SOMA-UI-IDREG-001.md`: NEW.

## 1. ASCII wireframe — whole screen inside UI-S-00 chrome

```
┌─[capsule ▾] ‹capsule.name› [v‹semver›][‹lifecycle›]───────── IQ[──●──] AUTO[─●─] BUDGET[─●─] ⌘K─┐
│ derived (RO): temp ‹› max_tok ‹› rlm ‹› recall ‹› tier ‹› hitl ‹› tokens ‹› cost ‹› think ‹›      │
├─ Soul  Brain  Hands  Memory  Body  Governance ──────────────────────────────────────────────────┤
│ LEFT NAV │ WORKSPACE — Capability detail [1]                              │ SURFACES x8             │
│  Chat    │ ┌────────────────────────────────────────────────────────┐  │ [Files][Tools][Browser] │
│  Capsule │ │ ‹capability.name›  ‹kind›  ‹provider›  ‹state›          │  │ [Editor][Debug][Capsule]│
│  Module* │ │ ABOUT [2]  ‹capability.description›                      │  │ [Brain][Desktop†] †GATED│
│  Platform│ │ HOOK BINDINGS [3]                                        │  │                         │
│  Ops     │ │ ┌────────────────────────────────────────────────────┐ │  │                         │
│  Settings│ │ │ ‹hook.name›  ‹trigger ▾│  ‹policy ▾│  [on]  [⋯]   │ │  │                         │
│          │ │ │ ‹hook.name›  ‹trigger ▾│  ‹policy ▾│  [on]  [⋯]   │ │  │                         │
│          │ │ └────────────────────────────────────────────────────┘ │  │                         │
│          │ │ NEW BINDING [4]  trigger ‹trigger ▾│  policy ‹policy ▾│ │  │                         │
│          │ │ [ Save bindings ] [5]     [ Unbind selected ] [6]       │  │                         │
│          │ │ derived (RO): require_hitl ‹›  tool_approval ‹›          │  │                         │
│          │ └────────────────────────────────────────────────────────┘  │                         │
├──────────┴──────────────────────────────────────────────────────────────┴─────────────────────────┤
│ INSTANCES ‹instance.id› ‹instance.status› │ NEURO: DA ‹› 5-HT ‹› NE ‹› ACh ‹› │ synced ‹ts›      │
└───────────────────────────────────────────────────────────────────────────────────────────────────┘
```

## 2. Control map

| # | UI-C-* | control | notes |
|---|---|---|---|
| 1 | — | Workspace region (Capability detail) | Screen shell. |
| 2 | UI-C-096 | About panel | Read-only `‹capability.description›` + provider chip. |
| 3 | UI-C-097 | Hook binding table | Rows: `‹hook.name›`, trigger select, policy select, enable toggle. |
| 4 | UI-C-098 | New binding form | Trigger + policy selects for an additional binding. |
| 4 | UI-C-028 | Row action menu (⋯) | Edit / Unbind. Unbind opens UI-M-03. |
| 5 | UI-A-046 | Save bindings | Writes all binding edits for this capability. |
| 6 | UI-A-047 | Unbind hook | DESTRUCTIVE — always opens UI-M-03. |
| — | UI-C-008 (partial) | `require_hitl` / `tool_approval` readouts | Greyed, read-only, below the form. |

## 3. State variants

- **loading** — Binding table skeleton. Verbatim label: "Loading capability…"
- **empty** — Bindings verbatim: "No hooks bound to this capability yet."
  About placeholder verbatim: "No description provided."
- **error** — `UI-C-024` verbatim: "Capability could not be loaded. It may have been removed."
  Save failure verbatim: "Bindings were not saved. Your edits are still here — try again."
- **permission-denied** — Binding rows read-only; Save/Unbind disabled with inline reason
  "Binding changes require the operator role." `UI-C-025` verbatim:
  "You do not have permission to change hook bindings. Ask a platform admin for the operator role."
- **offline** — Save/Unbind disabled with inline reason "Binding changes are unavailable offline."
  Chrome offline banner shown.

## 4. Modal overlays

| Trigger | Modal | Contents |
|---|---|---|
| UI-A-047 Unbind hook | UI-M-03 Dialog | "Unbind ‹hook.name› from ‹capability.name›?" Cancel / Unbind. |
| Row edit expand | UI-M-01 Drawer (420px) | Full binding record; ESC closes, focus trap. |
| — | UI-M-02 | Not used by this screen. |

## 5. Honesty notes

Hook names, triggers and policies are store placeholders. `require_hitl` and `tool_approval` are
derived AgentIQ settings rendered greyed only.

End of Document
