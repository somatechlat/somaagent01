# UI-S-38 — Platform metrics

**Platform metrics** — Ops workspace column (alias /saas/metrics) — route `/platform/metrics` — facet **Ops**.
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
│  route: /platform/metrics                                              │  [1] Files             │
│  Platform metrics     range: [1h][24h][7d][30d] [custom]               │  [2] Tools             │
│                                                                        │  [3] Browser           │
│  ┌──────────────────────────────────────────────┐                      │  [4] Editor            │
│  │ chart frame: <metric.name>                    │                     │  [5] Debug             │
│  │ y: <unit>   x: <time>                         │                     │  [6] Capsule           │
│  │ series: <series.name>  (values from API)      │                     │  [7] Brain             │
│  │ .......'-.._..-'/.......'-.._..-'/.......     │                     │  [8] Desktop           │
│  └──────────────────────────────────────────────┘                      │       GATED (UI-X-08)  │
│  [Open full-screen (UI-M-02)]  [Export series]                         │                        │
│                                                                        │                        │
│  Metric set                                                            │                        │
│  | metric | current | unit | window |                                  │                        │
│  | <name> | <value> | <u>  | <ts>   |                                  │                        │
│  | <name> | <value> | <u>  | <ts>   |                                  │                        │
│  | <name> | <value> | <u>  | <ts>   |                                  │                        │
├────────────────────────────────────────────────────────────────────────┼────────────────────────┤
│ instance strip: <session_id>  state: <state>  started: <ts>                                     │
│ neuro meters x4 (RO): DA <v>  5-HT <v>  NE <v>  ACh <v>                                         │
│   neuromodulator synced_at: <ts>   (no value without a real sync)                               │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
```

**Control map.**

| # | UI-C-* | control | notes |
|---|---|---|---|
| 1 | UI-C-094 | time-range selector | 1h/24h/7d/30d/custom. Window is passed to the API; the UI never invents points. |
| 2 | UI-C-093 | chart frame | Axes and series labels come from the metric definition. No axis ticks are drawn with fake numbers. |
| 3 | UI-C-071 | metric set table | Each row is a real metric name from the platform metrics API. |
| 4 | UI-C-067 | Export series (primary) | Downloads the series in a server-supported format. No format is listed that the API does not offer. |

**State variants.**

- **Loading.** Skeleton rows plus a `loading` chip in the workspace header. No counts, charts or metrics are drawn while loading.
- **Empty.** "No metric points in this window. Widen the time range."
- **Error.** "Couldn't load platform metrics. ‹ reason from API ›"
- **Permission-denied.** "You don't have access to platform metrics. Requires the platform-admin role."
- **Offline.** You're offline. Changes will not be saved until the connection returns.

**Modal overlays.** UI-M-02 Full-screen — chart drill-in (explicit dismiss only).
