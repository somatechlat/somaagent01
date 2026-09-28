# UI-S-44 — Audit log

**Audit log** — Ops workspace column (aliases /admin/audit) — route `/audit` — facet **Ops**.
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
│ WORKSPACE  facet: Ops                                                  │ SURFACE RAIL x8        │
│  route: /audit                                                         │  [1] Files             │
│  Audit log     filter: [actor][action][result]  search: [____]         │  [2] Tools             │
│                                                                        │  [3] Browser           │
│  | time | actor | action | target | result | [inspect] |               │  [4] Editor            │
│  | <ts> | <who> | <act>  | <tgt>  | ok/err | [inspect] |               │  [5] Debug             │
│  | <ts> | <who> | <act>  | <tgt>  | ok/err | [inspect] |               │  [6] Capsule           │
│  | <ts> | <who> | <act>  | <tgt>  | ok/err | [inspect] |               │  [7] Brain             │
│  | <ts> | <who> | <act>  | <tgt>  | ok/err | [inspect] |               │  [8] Desktop           │
│  | <ts> | <who> | <act>  | <tgt>  | ok/err | [inspect] |               │       GATED (UI-X-08)  │
│                                                                        │                        │
│  page <n> of <n>              [prev] [next]  page size [<n>]           │                        │
│                                                                        │                        │
│  Note: log rows are append-only. The UI never edits them.              │                        │
├────────────────────────────────────────────────────────────────────────┼────────────────────────┤
│ instance strip: <session_id>  state: <state>  started: <ts>                                     │
│ neuro meters x4 (RO): DA <v>  5-HT <v>  NE <v>  ACh <v>                                         │
│   neuromodulator synced_at: <ts>   (no value without a real sync)                               │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
```

**Control map.**

| # | UI-C-* | control | notes |
|---|---|---|---|
| 1 | UI-C-070 | filter / search input | actor/action/result filters plus free text. Sent to the API; no client-side invention of rows. |
| 2 | UI-C-100 | audit event row | One row per real event. result is ok/err from the event record, never inferred. |
| 3 | UI-C-068 | inspect (secondary) | Opens UI-M-01 drawer with the event detail. |
| 4 | UI-C-078 | pagination | page/page-size. Disabled when the API reports no further page — disabled-reason: "No further page." |
| 5 | UI-C-080 | copy event id | Copies the real event id to the clipboard. |

**State variants.**

- **Loading.** Skeleton rows plus a `loading` chip in the workspace header. No counts, charts or metrics are drawn while loading.
- **Empty.** "No audit events match this filter."
- **Error.** "Couldn't load the audit log. ‹ reason from API ›"
- **Permission-denied.** "You don't have access to the audit log. Requires the audit-admin role."
- **Offline.** You're offline. Changes will not be saved until the connection returns.

**Modal overlays.** UI-M-01 Drawer — event detail (actor, action, target, result, metadata). UI-M-02 Full-screen — raw event payload for copy/inspection (explicit dismiss only).
