# UI-S-04 — Memory — retention & recall

Screen UI-S-04 · Facet: Memory · Route: `/memory`
Source view per `SOMA-UI-IDREG-001.md`: `saas-memory-view` (`webui/src/views/saas-memory-view.ts`).
Route matches `webui/src/main.ts:402`.

## 1. ASCII wireframe — whole screen inside UI-S-00 chrome

```
┌─[capsule ▾] ‹capsule.name› [v‹semver›][‹lifecycle›]───────── IQ[──●──] AUTO[─●─] BUDGET[─●─] ⌘K─┐
│ derived (RO): temp ‹› max_tok ‹› rlm ‹› recall ‹› tier ‹› hitl ‹› tokens ‹› cost ‹› think ‹›      │
├─ Soul  Brain  Hands  ( Memory )  Body  Governance ──────────────────────────────────────────────┤
│ LEFT NAV │ WORKSPACE — Memory [1]                                      │ SURFACES x8             │
│  Chat    │ ┌────────────────────────────────────────────────────────┐  │ [Files][Tools][Browser] │
│  Capsule │ │ RETENTION [2] ‹retention.policy ▾│   DECAY [3] ──●──   │  │ [Editor][Debug][Capsule]│
│  Module  │ │ PURGE SCOPE [4] ‹scope ▾│     [ Purge… ] [5]           │  │ [Brain][Desktop†] †GATED│
│  Platform│ │ ── recall (read-only derived: recall_limit ‹›) ────────│  │                         │
│  Ops     │ │ RECALL PROBE [6] ‹query…│  [ Run probe ] [7]           │  │                         │
│  Settings│ │ ┌────────────────────────────────────────────────────┐ │  │                         │
│          │ │ │ TIMELINE [8]                                       │ │  │                         │
│          │ │ │  ‹memory.ts›  ‹memory.summary›        ‹score ›    │ │  │                         │
│          │ │ │  ‹memory.ts›  ‹memory.summary›        ‹score ›    │ │  │                         │
│          │ │ │  (scroll — newest first)                           │ │  │                         │
│          │ │ └────────────────────────────────────────────────────┘ │  │                         │
│          │ │ PROBE RESULT [9]  ‹live value ›                        │  │                         │
│          │ └────────────────────────────────────────────────────────┘  │                         │
├──────────┴──────────────────────────────────────────────────────────────┴─────────────────────────┤
│ INSTANCES ‹instance.id› ‹instance.status› │ NEURO: DA ‹› 5-HT ‹› NE ‹› ACh ‹› │ synced ‹ts›      │
└───────────────────────────────────────────────────────────────────────────────────────────────────┘
```

## 2. Control map

| # | UI-C-* | control | notes |
|---|---|---|---|
| 1 | — | Workspace region (Memory) | Screen shell. |
| 2 | UI-C-045 | Retention policy select | Options from the memory store; value `‹retention.policy›`. |
| 3 | UI-C-046 | Decay slider | Persona/memory parameter, not an AgentIQ derived field. |
| 4 | UI-C-047 | Purge scope select | Capsule / session / tenant as the store allows. |
| 5 | UI-A-016 | Purge memories | DESTRUCTIVE — always opens UI-M-03. |
| 6 | UI-C-048 | Recall probe input | Free text; empty-query behaviour is defined by the memory engine, not faked here. |
| 7 | UI-A-015 | Run recall probe | Result lands in UI-C-050. |
| 8 | UI-C-049 | Memory timeline | Rows are store objects: `‹memory.ts›` / `‹memory.summary›` / `‹score ›`. |
| 9 | UI-C-050 | Probe result readout | READ-ONLY `‹ live value ›`. |

## 3. State variants

- **loading** — Timeline shows 5 skeleton rows. Verbatim label above it: "Loading memories…"
- **empty** — `UI-C-023` verbatim: "No memories stored for this capsule yet."
  Probe result with no run yet verbatim: "No probe run yet."
- **error** — `UI-C-024` verbatim: "Memories could not be loaded. Retry, or check that the
  somaBrain memory service is reachable." Probe failure verbatim: "Probe did not finish. Nothing was changed."
- **permission-denied** — Purge disabled with inline reason "Purge requires the capsule-editor role."
  Timeline remains readable; `UI-C-025` verbatim:
  "You do not have permission to change retention. Ask a platform admin for the capsule-editor role."
- **offline** — Probe and Purge disabled with inline reason "Memory actions are unavailable offline."
  Timeline shows last cached page with a note: "Showing the last synced page."

## 4. Modal overlays

| Trigger | Modal | Contents |
|---|---|---|
| UI-A-016 Purge memories | UI-M-03 Dialog | "Permanently delete ‹count› memories in scope ‹scope›?" Cancel / Purge. No undo. |
| Timeline row open | UI-M-01 Drawer (420px) | Full memory record fields as stored; ESC closes, focus trap. |
| — | UI-M-02 | Not used by this screen. |

## 5. Honesty notes

Timeline rows and scores are placeholders (`‹score ›`). No retention durations or memory counts
are invented. `recall_limit` is shown only as the greyed derived readout.

End of Document
