# UI-S-01 — Soul — persona & system prompt

Screen UI-S-01 · Facet: Soul · Route: NEW (not present in `webui/src/main.ts` today).
Source view per `SOMA-UI-IDREG-001.md`: `saas-capsule-editor` (Soul tab of
`webui/src/components/saas-capsule-editor.ts`).

## 1. ASCII wireframe — whole screen inside UI-S-00 chrome

```
┌─[capsule ▾] ‹capsule.name› [v‹semver›][‹lifecycle›]───────── IQ[──●──] AUTO[─●─] BUDGET[─●─] ⌘K─┐
│ derived (RO): temp ‹› max_tok ‹› rlm ‹› recall ‹› tier ‹› hitl ‹› tokens ‹› cost ‹› think ‹›      │
├─ ( Soul )  Brain  Hands  Memory  Body  Governance ──────────────────────────────────────────────┤
│ LEFT NAV │ WORKSPACE — Soul [1]                                     │ SURFACES x8                 │
│  Chat    │ ┌──────────────────────────────────────────────────────┐ │ [Files][Tools][Browser]     │
│  Capsule │ │ PRESET [2]  ‹persona.preset ▾│                       │ │ [Editor][Debug][Capsule]    │
│  Module  │ │ TONE     [3]  ‹tone ▾│         GREETING [4]          │ │ [Brain][Desktop†] †GATED    │
│  Platform│ │ SYSTEM PROMPT                        [5]             │ │                             │
│  Ops     │ │ ┌──────────────────────────────────────────────────┐ │ │                             │
│  Settings│ │ │ ‹system_prompt.text›                           │ │ │                             │
│          │ │ │ (multi-line editor)                            │ │ │                             │
│          │ │ └──────────────────────────────────────────────────┘ │ │                             │
│          │ │ CONSTRAINTS [6]                                      │ │                             │
│          │ │  ‹constraint›  ‹constraint›  [+ add]                 │ │                             │
│          │ │                                                      │ │                             │
│          │ │ [ Save persona ] [7]  [ Revert ] [8]                 │ │                             │
│          │ └──────────────────────────────────────────────────────┘ │                             │
├──────────┴──────────────────────────────────────────────────────────┴─────────────────────────────┤
│ INSTANCES ‹instance.id› ‹instance.status› │ NEURO: DA ‹› 5-HT ‹› NE ‹› ACh ‹› │ synced ‹ts›      │
└───────────────────────────────────────────────────────────────────────────────────────────────────┘
```

## 2. Control map

| # | UI-C-* | control | notes |
|---|---|---|---|
| 1 | UI-C-029 | Soul editor region | Section wrapper for the persona fields below. |
| 2 | UI-C-030 | Persona preset select | Options come from the persona store; default `‹persona.preset›`. |
| 3 | UI-C-031 | Tone select | Bounded by the persona store; no invented option list. |
| 4 | UI-C-032 | Greeting field | Single line; optional. |
| 5 | UI-C-033 | System prompt editor | Multi-line; validation: non-empty on save. |
| 6 | UI-C-034 | Constraint list | Add/remove rows; each row is a short imperative. |
| 7 | UI-A-009 | Save persona | Writes the Soul section of the active capsule. |
| 8 | UI-A-008 | Revert | Discards unsaved Soul edits back to last saved state. |

Derived AgentIQ fields (temperature, max_tokens, rlm_iterations, recall_limit, model_tier,
brain_query_enabled, require_hitl, tool_approval, egress_allowed, token_limit, cost_tier,
thinking_budget) appear only as the READ-ONLY chrome readout strip (UI-C-008). They are never
inputs on this screen.

## 3. State variants

- **loading** — Editor region replaced by `UI-C-027` skeleton bars sized like the prompt box.
  Verbatim label: "Loading persona…"
- **empty** — Prompt box empty with placeholder text (verbatim):
  "Describe who this agent is, how it should speak, and what it must never do."
  Constraint list shows verbatim: "No constraints yet."
- **error** — `UI-C-024` banner above the editor, verbatim:
  "Persona could not be loaded. Retry, or check that the somaAgent01 API is reachable."
  On save failure, verbatim: "Persona was not saved. Your text is still here — try again."
- **permission-denied** — Fields render read-only; `UI-C-025` banner, verbatim:
  "You do not have permission to edit this persona. Ask a platform admin for the capsule-editor role."
- **offline** — Chrome `UI-C-026` banner (verbatim: "You are offline. Edits are held locally and
  will not save until the connection returns."); Save disabled with inline reason
  "Save is unavailable offline."

## 4. Modal overlays

| Trigger | Modal | Contents |
|---|---|---|
| UI-A-008 Revert with unsaved edits | UI-M-03 Dialog | "Discard unsaved persona edits?" Cancel / Discard (destructive). |
| UI-C-034 remove-last-constraint | UI-M-03 Dialog | Destructive confirm only when the list would become empty. |
| — | UI-M-01 / UI-M-02 | Not used by this screen. |

## 5. Honesty notes

Persona text and preset values are placeholders bound to the capsule store. No sample system
prompt is presented as a real capsule value.

End of Document
