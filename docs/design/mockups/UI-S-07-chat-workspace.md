# UI-S-07 — Chat workspace

Screen UI-S-07 · Facet: Chat · Route: `/chat`
Source view per `SOMA-UI-IDREG-001.md`: `saas-chat` (`webui/src/views/saas-chat.ts`).
Route matches `webui/src/main.ts:390` (also the default landing route, `main.ts:93`).

## 1. ASCII wireframe — whole screen inside UI-S-00 chrome

```
┌─[capsule ▾] ‹capsule.name› [v‹semver›][‹lifecycle›]───────── IQ[──●──] AUTO[─●─] BUDGET[─●─] ⌘K─┐
│ derived (RO): temp ‹› max_tok ‹› rlm ‹› recall ‹› tier ‹› hitl ‹› tokens ‹› cost ‹› think ‹›      │
├─ Soul  Brain  Hands  Memory  Body  Governance ──────────────────────────────────────────────────┤
│ LEFT NAV │ WORKSPACE — Chat [1]                                        │ SURFACES x8             │
│  Chat *  │ ┌──────────────┐ ┌──────────────────────────────────────┐  │ [Files][Tools][Browser] │
│  Capsule │ │ CONVERSATIONS│ │ MESSAGE STREAM [3]                   │  │ [Editor][Debug][Capsule]│
│  Module  │ │ [2]          │ │  ‹message.role›  ‹message.text›      │  │ [Brain][Desktop†] †GATED│
│  Platform│ │  ‹conv.title›│ │  ‹message.role›  ‹message.text›      │  │                         │
│  Ops     │ │  ‹conv.title›│ │  tool call ‹tool.name› ‹status› [4]  │  │                         │
│  Settings│ │  ‹conv.title›│ │  ‹message.role›  ‹message.text›      │  │                         │
│          │ │  [+ New]     │ │                                      │  │                         │
│          │ │              │ │ HITL BAR [5]  "Approve ‹tool.name›?" │  │                         │
│          │ │              │ │  [ Approve ] [6]  [ Reject ] [7]     │  │                         │
│          │ │              │ ├──────────────────────────────────────┤  │                         │
│          │ │              │ │ COMPOSER [8]                         │  │                         │
│          │ │              │ │ ‹compose text…›        [📎][Send][9] │  │                         │
│          │ └──────────────┘ └──────────────────────────────────────┘  │                         │
├──────────┴──────────────────────────────────────────────────────────────┴─────────────────────────┤
│ INSTANCES ‹instance.id› ‹instance.status› │ NEURO: DA ‹› 5-HT ‹› NE ‹› ACh ‹› │ synced ‹ts›      │
└───────────────────────────────────────────────────────────────────────────────────────────────────┘
```

## 2. Control map

| # | UI-C-* | control | notes |
|---|---|---|---|
| 1 | — | Workspace region (Chat) | Screen shell. |
| 2 | UI-C-057 | Conversation list | Rows `‹conv.title›` + `‹conv.ts›`; selection drives the stream. |
| 3 | UI-C-058 | Message stream | Rows carry `‹message.role›` / `‹message.text›` from the store. |
| 4 | UI-C-059 | Tool-call chip | Inline per message: `‹tool.name›` + `‹status›`. Opens UI-S-08 detail. |
| 5 | UI-C-060 | HITL approval bar | Renders only when `require_hitl ‹›` demands it (derived, read-only). |
| 6 | UI-A-023 | Approve tool | Resumes the agent run. |
| 7 | UI-A-024 | Reject tool | Rejects the tool call; run continues or stops per policy. |
| 8 | UI-C-061 | Message composer | Multi-line; attach menu is UI-C-062. |
| 8 | UI-C-062 | Attach menu | Offers the stores the Hands facet actually exposes. |
| 9 | UI-A-021 | Send | Submits the composer. Disabled while streaming (reason: "Wait for the reply to finish."). |
| — | UI-A-022 | Stop generation | Visible while streaming; halts the run. |

## 3. State variants

- **loading** — Stream shows 3 skeleton bubbles; verbatim label: "Loading conversation…"
- **empty** — New conversation state, verbatim: "Start the conversation. Ask ‹capsule.name› anything."
  Empty conversation list verbatim: "No conversations yet."
- **error** — `UI-C-024` verbatim: "The conversation could not be loaded. Retry, or check that the
  somaAgent01 API is reachable." Send failure verbatim: "Message was not sent. It is still in the composer."
- **permission-denied** — Composer read-only; `UI-C-025` verbatim:
  "You do not have permission to post in this conversation. Ask a platform admin for the member role."
  Stream remains readable.
- **offline** — Composer disabled with inline reason "Send is unavailable offline." Draft text is
  kept locally. Chrome offline banner shown. HITL bar disables Approve/Reject with
  "Approval is unavailable offline."

## 4. Modal overlays

| Trigger | Modal | Contents |
|---|---|---|
| Composer attach menu → file picker | UI-M-01 Drawer (420px) | Files surface (UI-X-01) contents; ESC closes, focus trap. |
| Message open-detail (UI-C-059) | — | Navigates to UI-S-08 rather than a modal. |
| Reject tool (UI-A-024) | UI-M-03 Dialog | "Reject this tool call?" Cancel / Reject. |
| — | UI-M-02 | Not used by this screen. |

## 5. Honesty notes

Message text, conversation titles and tool names are store placeholders. The HITL bar's
visibility is a consequence of the derived `require_hitl` readout — that field is never editable
from chat.

End of Document
