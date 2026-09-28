# UI-S-47 — Voice sessions

**Voice sessions** — Voice workspace column (alias /platform/voice/sessions) — route `/voice/sessions` — facet **Voice**.
Chrome abbreviated (UI-S-00). Facet tabs and surface rail are visible.

```
┌─ UI-S-00 chrome (abbrev) ────────────────────────────────────────────────────────────────────────┐
│ capsule: <capsule.name>                                                                         │
│ version: <version>    lifecycle: <lifecycle>                                                    │
│ persona knobs: (IQ <val>)(auto <val>)(budget <val>)                                             │
│ derived AgentIQ RO (greyed, never inputs):                                                      │
│   temperature <v>  max_tokens <v>  rlm_iterations <v>                                           │
│   recall_limit <v>  model_tier <v>  brain_query_enabled <v>                                     │
│   require_hitl <v>  tool_approval <v>  egress_allowed <v>                                       │
│   token_limit <v>  cost_tier <v>  thinking_budget <v>                                           │
├─────────────────────────────────────────────────────────────────────────────────────────────────┤
│ facet tabs x6:  [Soul][Brain][Hands][Memory][Body][Governance]                                  │
│ command palette: <Cmd-K>                                                                        │
├────────────────────────────────────────────────────────────────────────┼────────────────────────┤
│ WORKSPACE  facet: Voice                                                │ SURFACE RAIL x8        │
│  route: /voice/sessions                                                │  [1] Files             │
│  Voice sessions     filter: [state]  window: [24h][7d] [custom]        │  [2] Tools             │
│                                                                        │  [3] Browser           │
│  | session id | persona | state | started | duration | [open][x] |     │  [4] Editor            │
│  | <id>       | <name>  | <st>  | <ts>    | <dur>    | [open][x] |     │  [5] Debug             │
│  | <id>       | <name>  | <st>  | <ts>    | <dur>    | [open][x] |     │  [6] Capsule           │
│  | <id>       | <name>  | <st>  | <ts>    | <dur>    | [open][x] |     │  [7] Brain             │
│  | <id>       | <name>  | <st>  | <ts>    | <dur>    | [open][x] |     │  [8] Desktop           │
│                                                                        │       GATED (UI-X-08)  │
│  page <n> of <n>              [prev] [next]                            │                        │
│                                                                        │                        │
│  Note: session rows come from the voice session API.                   │                        │
│  No session is drawn that the API did not return.                      │                        │
├────────────────────────────────────────────────────────────────────────┼────────────────────────┤
│ instance strip: <session_id>  state: <state>  started: <ts>                                     │
│ neuro meters x4 (RO): DA <v>  5-HT <v>  NE <v>  ACh <v>                                         │
│   neuromodulator synced_at: <ts>   (no value without a real sync)                               │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
```

**Control map.**

| # | UI-C-* | control | notes |
|---|---|---|---|
| 1 | UI-C-063 | state filter | Filters on the real session state values the API reports. |
| 2 | UI-C-094 | time-window selector | Passed to the API as-is. |
| 3 | UI-C-102 | voice session row | session id, persona, state, started, duration all `‹ live value ›`. |
| 4 | UI-C-068 | open (secondary) | Opens UI-M-01 drawer with the session detail/transcript. |
| 5 | UI-C-069 | delete session (destructive) | Opens UI-M-03. disabled-when: caller lacks voice-admin role — disabled-reason: "Requires the voice-admin role." |
| 6 | UI-C-078 | pagination | Disabled when the API reports no further page — disabled-reason: "No further page." |

**State variants.**

- **Loading.** Skeleton rows plus a `loading` chip in the workspace header. No counts, charts or metrics are drawn while loading.
- **Empty.** "No voice sessions in this window."
- **Error.** "Couldn't load voice sessions. ‹ reason from API ›"
- **Permission-denied.** "You don't have access to voice sessions. Requires the voice-user role."
- **Offline.** You're offline. Changes will not be saved until the connection returns.

**Modal overlays.** UI-M-01 Drawer — session detail (transcript, timing, persona used). UI-M-03 Dialog — "Delete voice session <session_id>?" (destructive).
