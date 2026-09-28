# UI-S-08 — Message detail

Screen UI-S-08 · Facet: Chat · Route: `/chat/:id`
Source view per `SOMA-UI-IDREG-001.md`: `saas-chat` (`webui/src/views/saas-chat.ts`).
Note: `webui/src/main.ts:390` matches `path.startsWith('/chat/')` and mounts the same `saas-chat`
component; there is no separate message-detail view today.

## 1. ASCII wireframe — whole screen inside UI-S-00 chrome

```
┌─[capsule ▾] ‹capsule.name› [v‹semver›][‹lifecycle›]───────── IQ[──●──] AUTO[─●─] BUDGET[─●─] ⌘K─┐
│ derived (RO): temp ‹› max_tok ‹› rlm ‹› recall ‹› tier ‹› hitl ‹› tokens ‹› cost ‹› think ‹›      │
├─ Soul  Brain  Hands  Memory  Body  Governance ──────────────────────────────────────────────────┤
│ LEFT NAV │ WORKSPACE — Message detail [1]                              │ SURFACES x8             │
│  Chat *  │ ┌────────────────────────────────────────────────────────┐  │ [Files][Tools][Browser] │
│  Capsule │ │ ‹message.role› · ‹message.ts›          [ Copy ] [2]   │  │ [Editor][Debug][Capsule]│
│  Module  │ │ ┌────────────────────────────────────────────────────┐ │  │ [Brain][Desktop†] †GATED│
│  Platform│ │ │ ‹message.text›                                   │ │  │                         │
│  Ops     │ │ │ (full body, wrapped)                             │ │  │                         │
│  Settings│ │ └────────────────────────────────────────────────────┘ │  │                         │
│          │ │ META [3]  model ‹model.id›  tokens ‹ live value ›      │  │                         │
│          │ │           cost ‹ live value ›   latency ‹ live value › │  │                         │
│          │ │ TOOL-CALL TRACE [4]                                    │  │                         │
│          │ │  1. ‹tool.name›  ‹status›  ‹ts›                        │  │                         │
│          │ │  2. ‹tool.name›  ‹status›  ‹ts›                        │  │                         │
│          │ │ [ Branch from here ] [5]    [ Open conversation ] [6]  │  │                         │
│          │ └────────────────────────────────────────────────────────┘  │                         │
├──────────┴──────────────────────────────────────────────────────────────┴─────────────────────────┤
│ INSTANCES ‹instance.id› ‹instance.status› │ NEURO: DA ‹› 5-HT ‹› NE ‹› ACh ‹› │ synced ‹ts›      │
└───────────────────────────────────────────────────────────────────────────────────────────────────┘
```

## 2. Control map

| # | UI-C-* | control | notes |
|---|---|---|---|
| 1 | — | Workspace region (Message detail) | Screen shell. |
| 2 | UI-A-025 | Copy message | Copies the stored body verbatim. |
| 3 | UI-C-063 | Message meta readout | READ-ONLY: model id + token/cost/latency as `‹ live value ›`. |
| 4 | UI-C-064 | Tool-call trace list | Ordered rows from the run record; no invented steps. |
| 5 | UI-A-026 | Branch from message | Opens a new conversation rooted at this message. |
| 6 | UI-A-032 | Open conversation | Returns to UI-S-07 for `‹conversation.id›`. |

## 3. State variants

- **loading** — Body skeleton; verbatim label: "Loading message…"
- **empty** — Verbatim: "This message has no body." Trace empty verbatim: "No tool calls on this message."
- **error** — `UI-C-024` verbatim: "Message could not be loaded. It may have been deleted."
  Unknown id fallback verbatim: "Message not found."
- **permission-denied** — `UI-C-025` verbatim:
  "You do not have permission to read this message. Ask a platform admin for the member role."
- **offline** — Body renders if cached, with note "Showing the cached copy." Otherwise
  verbatim: "Message is unavailable offline." Branch disabled with reason "Branch is unavailable offline."

## 4. Modal overlays

| Trigger | Modal | Contents |
|---|---|---|
| Trace row expand | UI-M-01 Drawer (420px) | Tool-call arguments/result as stored (secrets masked). |
| — | UI-M-02 / UI-M-03 | Not used by this screen. |

## 5. Honesty notes

Token, cost and latency figures are placeholders — never fabricated numbers. Tool arguments shown
in the drawer mask any secret material as `sk-••••••••aBcD` with a "rotate in Vault" note.

End of Document
