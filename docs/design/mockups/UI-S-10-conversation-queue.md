# UI-S-10 — Conversation queue

Screen UI-S-10 · Facet: Chat · Route: NEW (not present in `webui/src/main.ts` today).
Source view per `SOMA-UI-IDREG-001.md`: NEW.

## 1. ASCII wireframe — whole screen inside UI-S-00 chrome

```
┌─[capsule ▾] ‹capsule.name› [v‹semver›][‹lifecycle›]───────── IQ[──●──] AUTO[─●─] BUDGET[─●─] ⌘K─┐
│ derived (RO): temp ‹› max_tok ‹› rlm ‹› recall ‹› tier ‹› hitl ‹› tokens ‹› cost ‹› think ‹›      │
├─ Soul  Brain  Hands  Memory  Body  Governance ──────────────────────────────────────────────────┤
│ LEFT NAV │ WORKSPACE — Conversation queue [1]                            │ SURFACES x8             │
│  Chat *  │ ┌────────────────────────────────────────────────────────┐  │ [Files][Tools][Browser] │
│  Capsule │ │ FILTER [2] ‹status ▾│   SEARCH [3] ‹filter.queue…│     │  │ [Editor][Debug][Capsule]│
│  Module  │ │ ┌────────────────────────────────────────────────────┐ │  │ [Brain][Desktop†] †GATED│
│  Platform│ │ │ QUEUE TABLE [4]                                    │ │  │                         │
│  Ops     │ │ │ ‹conv.title›  ‹status›  ‹priority›  ‹ts›   [⋯] [5]│ │  │                         │
│  Settings│ │ │ ‹conv.title›  ‹status›  ‹priority›  ‹ts›   [⋯]    │ │  │                         │
│          │ │ │ ‹conv.title›  ‹status›  ‹priority›  ‹ts›   [⋯]    │ │  │                         │
│          │ │ │ (scroll)                                           │ │  │                         │
│          │ │ └────────────────────────────────────────────────────┘ │  │                         │
│          │ │ PRIORITY for selection [6] ‹priority ▾│                │  │                         │
│          │ │ [ Requeue ] [7]      [ Cancel queued ] [8]             │  │                         │
│          │ └────────────────────────────────────────────────────────┘  │                         │
├──────────┴──────────────────────────────────────────────────────────────┴─────────────────────────┤
│ INSTANCES ‹instance.id› ‹instance.status› │ NEURO: DA ‹› 5-HT ‹› NE ‹› ACh ‹› │ synced ‹ts›      │
└───────────────────────────────────────────────────────────────────────────────────────────────────┘
```

## 2. Control map

| # | UI-C-* | control | notes |
|---|---|---|---|
| 1 | — | Workspace region (Queue) | Screen shell. |
| 2 | UI-C-069 | Status filter select | Options from queue states as stored. |
| 3 | UI-C-021 | Search | Filters the table live. |
| 4 | UI-C-070 | Queue table | Rows `‹conv.title›` / `‹status›` / `‹priority›` / `‹ts›`. |
| 5 | UI-C-028 | Row action menu (⋯) | Requeue / Cancel / Open. Cancel opens UI-M-03. |
| 6 | UI-C-071 | Priority select | Applies to the current selection. |
| 7 | UI-A-029 | Requeue | Moves the selection back to queued. |
| 8 | UI-A-030 | Cancel queued message | DESTRUCTIVE — always opens UI-M-03. |

## 3. State variants

- **loading** — Table shows 5 skeleton rows. Verbatim label: "Loading queue…"
- **empty** — `UI-C-023` verbatim: "The queue is empty. New conversations will appear here as they arrive."
  Empty under a filter verbatim: "No queued conversations match this filter. Clear the filter to see all."
- **error** — `UI-C-024` verbatim: "Queue could not be loaded. Retry, or check that the
  somaAgent01 API is reachable."
- **permission-denied** — Requeue/Cancel disabled with inline reason
  "Queue actions require the operator role." `UI-C-025` verbatim:
  "You do not have permission to manage the conversation queue. Ask a platform admin for the operator role."
- **offline** — Table shows last cached page ("Showing the last synced page."); actions disabled
  with reason "Queue actions are unavailable offline."

## 4. Modal overlays

| Trigger | Modal | Contents |
|---|---|---|
| UI-A-030 Cancel queued message | UI-M-03 Dialog | "Cancel this queued message? It will not be sent." Cancel / Cancel message. |
| Row open | — | Navigates to UI-S-07 / UI-S-08; no modal. |
| — | UI-M-01 / UI-M-02 | Not used by this screen. |

## 5. Honesty notes

Queue rows, statuses and priorities are store placeholders. No queue depth numbers are invented.

End of Document
