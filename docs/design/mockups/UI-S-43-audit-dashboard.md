# UI-S-43 — Audit dashboard

**Audit dashboard** — Ops workspace column (summary; the log itself is UI-S-44) — route `/platform/audit` — facet **Ops**.
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
│  route: /platform/audit                                                │  [1] Files             │
│  Audit dashboard                 window: [24h][7d][30d] [custom]       │  [2] Tools             │
│                                                                        │  [3] Browser           │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐               │  [4] Editor            │
│  │ <value>   │ │ <value>   │ │ <value>   │ │ <value>   │               │  [5] Debug             │
│  │ events    │ │ actors    │ │ failures  │ │ top action│               │  [6] Capsule           │
│  │ from API  │ │ from API  │ │ from API  │ │ from API  │               │  [7] Brain             │
│  └───────────┘ └───────────┘ └───────────┘ └───────────┘               │  [8] Desktop           │
│                                                                        │       GATED (UI-X-08)  │
│  Top actions                                                           │                        │
│  | action | count | share |                                            │                        │
│  | <act>  | <n>   | <pct> |                                            │                        │
│  | <act>  | <n>   | <pct> |                                            │                        │
│                                                                        │                        │
│  Failure trend (chart frame)                                           │                        │
│  │ series: <series.name>  points from API │                            │                        │
│  │ .......'-.._..-'/.......'-.._..-'/.....│                            │                        │
│                                                                        │                        │
│  [Open audit log -> /audit]                                            │                        │
├────────────────────────────────────────────────────────────────────────┼────────────────────────┤
│ instance strip: <session_id>  state: <state>  started: <ts>                                     │
│ neuro meters x4 (RO): DA <v>  5-HT <v>  NE <v>  ACh <v>                                         │
│   neuromodulator synced_at: <ts>   (no value without a real sync)                               │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
```

**Control map.**

| # | UI-C-* | control | notes |
|---|---|---|---|
| 1 | UI-C-094 | time-window selector | 24h/7d/30d/custom. Passed to the API as-is. |
| 2 | UI-C-091 | summary tile | Every tile value is `‹ live value ›` from the audit summary API. |
| 3 | UI-C-071 | top actions table | Rows are real action names from the audit stream. |
| 4 | UI-C-093 | failure trend chart frame | No points are drawn without data. |
| 5 | UI-C-076 | Open audit log link | Routes to /audit (UI-S-44). |

**State variants.**

- **Loading.** Skeleton rows plus a `loading` chip in the workspace header. No counts, charts or metrics are drawn while loading.
- **Empty.** "No audit events in this window."
- **Error.** "Couldn't load the audit dashboard. ‹ reason from API ›"
- **Permission-denied.** "You don't have access to the audit dashboard. Requires the audit-admin role."
- **Offline.** You're offline. Changes will not be saved until the connection returns.

**Modal overlays.** UI-M-01 Drawer — inspect a summary row in detail.
