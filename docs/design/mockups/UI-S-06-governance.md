# UI-S-06 — Governance — constitution & hooks

Screen UI-S-06 · Facet: Governance · Route: NEW (not present in `webui/src/main.ts` today).
Source view per `SOMA-UI-IDREG-001.md`: NEW.

## 1. ASCII wireframe — whole screen inside UI-S-00 chrome

```
┌─[capsule ▾] ‹capsule.name› [v‹semver›][‹lifecycle›]───────── IQ[──●──] AUTO[─●─] BUDGET[─●─] ⌘K─┐
│ derived (RO): temp ‹› max_tok ‹› rlm ‹› recall ‹› tier ‹› hitl ‹› tokens ‹› cost ‹› think ‹›      │
├─ Soul  Brain  Hands  Memory  Body  ( Governance ) ──────────────────────────────────────────────┤
│ LEFT NAV │ WORKSPACE — Governance [1]                                  │ SURFACES x8             │
│  Chat    │ ┌────────────────────────────────────────────────────────┐  │ [Files][Tools][Browser] │
│  Capsule │ │ CONSTITUTION [2]                                       │  │ [Editor][Debug][Capsule]│
│  Module  │ │ ┌────────────────────────────────────────────────────┐ │  │ [Brain][Desktop†] †GATED│
│  Platform│ │ │ ‹constitution.text›                                │ │  │                         │
│  Ops     │ │ │ (multi-line editor)                                │ │  │                         │
│  Settings│ │ └────────────────────────────────────────────────────┘ │  │                         │
│          │ │ HOOKS [3]                                              │  │                         │
│          │ │  ‹hook.name›  ‹trigger ▾│  severity ‹severity ▾│ [on] │  │                         │
│          │ │  ‹hook.name›  ‹trigger ▾│  severity ‹severity ▾│ [on] │  │                         │
│          │ │  [+ add hook]                                          │  │                         │
│          │ │ derived (RO): require_hitl ‹›  tool_approval ‹›        │  │                         │
│          │ │ [ Save constitution ] [4]   [ Test hooks ] [5]         │  │                         │
│          │ └────────────────────────────────────────────────────────┘  │                         │
├──────────┴──────────────────────────────────────────────────────────────┴─────────────────────────┤
│ INSTANCES ‹instance.id› ‹instance.status› │ NEURO: DA ‹› 5-HT ‹› NE ‹› ACh ‹› │ synced ‹ts›      │
└───────────────────────────────────────────────────────────────────────────────────────────────────┘
```

## 2. Control map

| # | UI-C-* | control | notes |
|---|---|---|---|
| 1 | — | Workspace region (Governance) | Screen shell. |
| 2 | UI-C-054 | Constitution editor | Multi-line; validation: non-empty on save. |
| 3 | UI-C-055 | Hook binding list | Rows: name, trigger select, severity select, enable toggle. |
| 3 | UI-C-056 | Hook trigger / severity selects | Options from the hook registry; no invented enum. |
| 4 | UI-A-019 | Save constitution | Writes the Governance section of the capsule. |
| 5 | UI-A-020 | Test hooks | Dry-runs bindings; output lands in a UI-M-01 drawer. |
| — | UI-C-008 (partial) | `require_hitl` / `tool_approval` readouts | Greyed, read-only, beside the hook list. |

## 3. State variants

- **loading** — Editor and hook list skeleton. Verbatim label: "Loading governance…"
- **empty** — Constitution placeholder (verbatim):
  "Write the rules this agent must never break." Hook list verbatim: "No hooks bound yet."
- **error** — `UI-C-024` verbatim: "Governance could not be loaded. Retry, or check that the
  somaAgent01 API is reachable." Test failure verbatim: "Hook test did not finish. No bindings were changed."
- **permission-denied** — Editor and list read-only; `UI-C-025` verbatim:
  "You do not have permission to edit governance. Ask a platform admin for the tenant-admin role."
- **offline** — Save and Test disabled with inline reasons "Save is unavailable offline." /
  "Test is unavailable offline." Chrome offline banner shown.

## 4. Modal overlays

| Trigger | Modal | Contents |
|---|---|---|
| UI-A-020 Test hooks | UI-M-01 Drawer (420px) | Dry-run result list per binding; ESC closes, focus trap. |
| Remove last hook / discard constitution | UI-M-03 Dialog | Destructive confirm: "Remove the last hook binding?" / "Discard unsaved constitution edits?" |
| — | UI-M-02 | Not used by this screen. |

## 5. Honesty notes

Hook names, triggers and severities are store placeholders. `require_hitl` and `tool_approval` are
derived AgentIQ settings shown greyed only. No policy outcomes are fabricated.

End of Document
