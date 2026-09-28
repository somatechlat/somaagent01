# UI-S-37 — Platform dashboard

**Platform dashboard** — Ops workspace column (aliases /saas, /platform) — route `/saas/dashboard` — facet **Ops**.
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
│  route: /saas/dashboard                                                │  [1] Files             │
│  Platform dashboard                                   [refresh]        │  [2] Tools             │
│  scope: <tenant.name>   tier: <tier.name>                              │  [3] Browser           │
│                                                                        │  [4] Editor            │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐               │  [5] Debug             │
│  │ <value>   │ │ <value>   │ │ <value>   │ │ <value>   │               │  [6] Capsule           │
│  │ label     │ │ label     │ │ label     │ │ label     │               │  [7] Brain             │
│  │ from API  │ │ from API  │ │ from API  │ │ from API  │               │  [8] Desktop           │
│  └───────────┘ └───────────┘ └───────────┘ └───────────┘               │       GATED (UI-X-08)  │
│                                                                        │                        │
│  Service status                                                        │                        │
│  | service | status | last check |                                     │                        │
│  | <name>  | <state>| <ts>       |                                     │                        │
│  | <name>  | <state>| <ts>       |                                     │                        │
│                                                                        │                        │
│  Recent activity                                                       │                        │
│  | <ts> | <actor> | <event> | [inspect] |                              │                        │
│  | <ts> | <actor> | <event> | [inspect] |                              │                        │
├────────────────────────────────────────────────────────────────────────┼────────────────────────┤
│ instance strip: <session_id>  state: <state>  started: <ts>                                     │
│ neuro meters x4 (RO): DA <v>  5-HT <v>  NE <v>  ACh <v>                                         │
│   neuromodulator synced_at: <ts>   (no value without a real sync)                               │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
```

**Control map.**

| # | UI-C-* | control | notes |
|---|---|---|---|
| 1 | UI-C-091 | KPI tile | Label and `‹ live value ›` come from the platform metrics API. Never a hard-coded number. |
| 2 | UI-C-095 | service status row | status from the health endpoint; last-check timestamp only when the service reports one. |
| 3 | UI-C-092 | recent activity feed | Real audit/activity events only. |
| 4 | UI-C-068 | refresh (secondary) | Re-fetches all tiles in place. |
| 5 | UI-C-073 | tenant / tier chips | Context chips naming the current scope. |

**State variants.**

- **Loading.** Skeleton rows plus a `loading` chip in the workspace header. No counts, charts or metrics are drawn while loading.
- **Empty.** "No platform activity yet. Events will appear here as the platform is used."
- **Error.** "Couldn't load the platform dashboard. ‹ reason from API ›"
- **Permission-denied.** "You don't have access to the platform dashboard. Requires the platform-admin role."
- **Offline.** You're offline. Changes will not be saved until the connection returns.

**Modal overlays.** UI-M-01 Drawer — [inspect] on an activity row opens the event detail drawer.
