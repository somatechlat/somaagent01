# UI-S-02 — Brain — model & IQ

Screen UI-S-02 · Facet: Brain · Route: `/cognitive`
Source view per `SOMA-UI-IDREG-001.md`: `saas-cognitive-panel` (`webui/src/views/saas-cognitive-panel.ts`).
Route matches `webui/src/main.ts:329`.

## 1. ASCII wireframe — whole screen inside UI-S-00 chrome

```
┌─[capsule ▾] ‹capsule.name› [v‹semver›][‹lifecycle›]───────── IQ[──●──] AUTO[─●─] BUDGET[─●─] ⌘K─┐
│ derived (RO): temp ‹› max_tok ‹› rlm ‹› recall ‹› tier ‹› hitl ‹› tokens ‹› cost ‹› think ‹›      │
├─ Soul  ( Brain )  Hands  Memory  Body  Governance ──────────────────────────────────────────────┤
│ LEFT NAV │ WORKSPACE — Brain [1]                                       │ SURFACES x8             │
│  Chat    │ ┌────────────────────────────────────────────────────────┐  │ [Files][Tools][Browser] │
│  Capsule │ │ MODEL [2] ‹model.provider ▾│  ‹model.id ▾│             │  │ [Editor][Debug][Capsule]│
│  Module  │ │ EMBEDDING [3] ‹embedding.model ▾│   DIM ‹embedding.dim›│  │ [Brain][Desktop†] †GATED│
│  Platform│ │ CONTEXT WINDOW [4] ‹context_window›                     │  │                         │
│  Ops     │ │ RECALL STRATEGY [5] ‹recall.strategy ▾│                 │  │                         │
│  Settings│ │                                                            │  │                         │
│          │ │ ── derived AgentIQ (READ-ONLY) [6] ─────────────────────│  │                         │
│          │ │ temperature ‹›   max_tokens ‹›   rlm_iterations ‹›      │  │                         │
│          │ │ recall_limit ‹›  model_tier ‹›   brain_query_enabled ‹› │  │                         │
│          │ │ require_hitl ‹›  tool_approval ‹› egress_allowed ‹›     │  │                         │
│          │ │ token_limit ‹›   cost_tier ‹›    thinking_budget ‹›     │  │                         │
│          │ │                                                            │  │                         │
│          │ │ EVAL READOUT [7]  last_run ‹ts›  result ‹live value ›    │  │                         │
│          │ │ [ Run eval ] [8]     [ Reset knobs to saved ] [9]        │  │                         │
│          │ └────────────────────────────────────────────────────────┘  │                         │
├──────────┴──────────────────────────────────────────────────────────────┴─────────────────────────┤
│ INSTANCES ‹instance.id› ‹instance.status› │ NEURO: DA ‹› 5-HT ‹› NE ‹› ACh ‹› │ synced ‹ts›      │
└───────────────────────────────────────────────────────────────────────────────────────────────────┘
```

## 2. Control map

| # | UI-C-* | control | notes |
|---|---|---|---|
| 1 | — | Workspace region (Brain) | Screen shell; all rows below live inside it. |
| 2 | UI-C-035 | Model provider / model select | Live options from the model store; shows `‹model.id›`. |
| 3 | UI-C-036 | Embedding model select | Adjacent dim chip is a read-only store value, not an input. |
| 4 | UI-C-037 | Context window field | Numeric; validated against the model's documented limit. |
| 5 | UI-C-038 | Recall strategy select | Options come from the memory store. |
| 6 | UI-C-008 | Derived AgentIQ readout block | READ-ONLY, greyed. Never editable here (house rule). |
| 7 | UI-C-039 | Eval readout | READ-ONLY: `‹ timestamp ›` + `‹ live value ›`. |
| 8 | UI-A-011 | Run eval | Starts an eval run; results land in UI-C-039. |
| 9 | UI-A-012 | Reset knobs to saved | Resets IQ/AUTO/BUDGET (UI-C-005…007) to last saved values. |

## 3. State variants

- **loading** — Model and embedding selects show "Loading models…" with `UI-C-027` skeletons
  for the derived block. Eval readout shows "No eval run yet."
- **empty** — Model select placeholder (verbatim): "Select a model for this capsule."
  Eval readout verbatim: "No eval run yet. Run an eval to see a result here."
- **error** — `UI-C-024`, verbatim: "Brain settings could not be loaded. Retry, or check that the
  somaAgent01 API is reachable." Eval failure verbatim: "Eval did not finish. Nothing was changed."
- **permission-denied** — Selects read-only; `UI-C-025`, verbatim:
  "You do not have permission to change brain settings. Ask a platform admin for the capsule-editor role."
- **offline** — Chrome offline banner; Run eval disabled with inline reason
  "Run eval is unavailable offline." Derived readouts keep last painted values.

## 4. Modal overlays

| Trigger | Modal | Contents |
|---|---|---|
| Change model with unsaved eval state | UI-M-03 Dialog | "Switch model and discard the current eval draft?" Cancel / Switch. |
| UI-A-012 with unsaved knob edits | UI-M-03 Dialog | Destructive confirm: "Reset persona knobs to saved values?" |
| — | UI-M-01 / UI-M-02 | Not used by this screen. |

## 5. Honesty notes

The derived block (temperature … thinking_budget) is drawn greyed and labelled READ-ONLY, per
`SOMA-UI-TEMPLATE-001.md`. No numeric defaults are printed; every value is `‹ live value ›`.

End of Document
