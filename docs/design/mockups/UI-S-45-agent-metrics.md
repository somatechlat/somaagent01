# UI-S-45 — Agent metrics

**Agent metrics** — Tenant-admin workspace column (alias /tenant/metrics) — route `/admin/metrics` — facet **Ops**.
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
│  route: /admin/metrics                                                 │  [1] Files             │
│  Agent metrics          agent: [<all agents v>]  window: [1h][24h]     │  [2] Tools             │
│                                                                        │  [3] Browser           │
│  | metric | value | unit | window |                                    │  [4] Editor            │
│  | <name> | <v>   | <u>  | <ts>   |                                    │  [5] Debug             │
│  | <name> | <v>   | <u>  | <ts>   |                                    │  [6] Capsule           │
│  | <name> | <v>   | <u>  | <ts>   |                                    │  [7] Brain             │
│  | <name> | <v>   | <u>  | <ts>   |                                    │  [8] Desktop           │
│                                                                        │       GATED (UI-X-08)  │
│  Per-agent breakdown                                                   │                        │
│  | agent | metric | value | window |                                   │                        │
│  | <id>  | <name> | <v>   | <ts>   |                                   │                        │
│  | <id>  | <name> | <v>   | <ts>   |                                   │                        │
│                                                                        │                        │
│  [Open full-screen chart (UI-M-02)]                                    │                        │
├────────────────────────────────────────────────────────────────────────┼────────────────────────┤
│ instance strip: <session_id>  state: <state>  started: <ts>                                     │
│ neuro meters x4 (RO): DA <v>  5-HT <v>  NE <v>  ACh <v>                                         │
│   neuromodulator synced_at: <ts>   (no value without a real sync)                               │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
```

**Control map.**

| # | UI-C-* | control | notes |
|---|---|---|---|
| 1 | UI-C-063 | agent selector | Options come from the tenant's real agent list. |
| 2 | UI-C-094 | time-window selector | Passed to the API as-is. |
| 3 | UI-C-101 | agent metric readout | Each value is `‹ live value ›`. No metric name is invented; only names the API exposes are shown. |
| 4 | UI-C-071 | per-agent breakdown table | Rows scoped to the selected agent/window. |
| 5 | UI-C-067 | Open full-screen chart (primary) | Opens UI-M-02. |

**State variants.**

- **Loading.** Skeleton rows plus a `loading` chip in the workspace header. No counts, charts or metrics are drawn while loading.
- **Empty.** "No agent metrics in this window. Widen the time range or select another agent."
- **Error.** "Couldn't load agent metrics. ‹ reason from API ›"
- **Permission-denied.** "You don't have access to agent metrics. Requires the tenant-admin role."
- **Offline.** You're offline. Changes will not be saved until the connection returns.

**Modal overlays.** UI-M-02 Full-screen — metric chart drill-in (explicit dismiss only).
