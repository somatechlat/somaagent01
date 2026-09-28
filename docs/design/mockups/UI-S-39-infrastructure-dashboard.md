# UI-S-39 — Infrastructure dashboard

**Infrastructure dashboard** — Ops workspace column (alias /saas/infrastructure) — route `/platform/infrastructure` — facet **Ops**.
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
│  route: /platform/infrastructure                                       │  [1] Files             │
│  Infrastructure dashboard                        [refresh]             │  [2] Tools             │
│  Every row is a real service. No status is drawn without a check.      │  [3] Browser           │
│                                                                        │  [4] Editor            │
│  ┌── compute ────────────────────────────────────────────┐             │  [5] Debug             │
│  │ <service.name>   <state>   last check <ts>  [inspect] │             │  [6] Capsule           │
│  │ <service.name>   <state>   last check <ts>  [inspect] │             │  [7] Brain             │
│  └────────────────────────────────────────────────────────┘            │  [8] Desktop           │
│  ┌── data ───────────────────────────────────────────────┐             │       GATED (UI-X-08)  │
│  │ <service.name>   <state>   last check <ts>  [inspect] │             │                        │
│  │ <service.name>   <state>   last check <ts>  [inspect] │             │                        │
│  └────────────────────────────────────────────────────────┘            │                        │
│  ┌── edge ───────────────────────────────────────────────┐             │                        │
│  │ <service.name>   <state>   last check <ts>  [inspect] │             │                        │
│  └────────────────────────────────────────────────────────┘            │                        │
│                                                                        │                        │
│  Dependency graph (read-only)                                          │                        │
│  │ <service> --> <service> --> <service> │                             │                        │
├────────────────────────────────────────────────────────────────────────┼────────────────────────┤
│ instance strip: <session_id>  state: <state>  started: <ts>                                     │
│ neuro meters x4 (RO): DA <v>  5-HT <v>  NE <v>  ACh <v>                                         │
│   neuromodulator synced_at: <ts>   (no value without a real sync)                               │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
```

**Control map.**

| # | UI-C-* | control | notes |
|---|---|---|---|
| 1 | UI-C-095 | service status row | name/state/last-check come from the infrastructure health API. Group headers are labels only. |
| 2 | UI-C-073 | state chip | Rendered only from a real check result. Never defaulted to green. |
| 3 | UI-C-068 | inspect (secondary) | Opens UI-M-01 drawer with the service detail. |
| 4 | UI-C-093 | dependency graph frame | Read-only. Edges come from the service registry — no edge is invented. |

**State variants.**

- **Loading.** Skeleton rows plus a `loading` chip in the workspace header. No counts, charts or metrics are drawn while loading.
- **Empty.** "No services registered. Register a service to see it here."
- **Error.** "Couldn't load infrastructure status. ‹ reason from API ›"
- **Permission-denied.** "You don't have access to infrastructure status. Requires the platform-admin role."
- **Offline.** You're offline. Changes will not be saved until the connection returns.

**Modal overlays.** UI-M-01 Drawer — service detail (checks, endpoints, recent incidents).
