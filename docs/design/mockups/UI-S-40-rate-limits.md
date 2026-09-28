# UI-S-40 — Rate limits

**Rate limits** — Ops workspace column (alias /platform/ratelimits) — route `/platform/infrastructure/redis/ratelimits` — facet **Ops**.
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
│  route: /platform/infrastructure/redis/ratelimits                      │  [1] Files             │
│  Rate limits              scope: [global][tenant][user]                │  [2] Tools             │
│                                                                        │  [3] Browser           │
│  | rule | window | limit | used | remaining | reset | [edit] |         │  [4] Editor            │
│  | <id> | <win>  | <n>   | <n>  | <n>       | <ts>  | [edit] |         │  [5] Debug             │
│  | <id> | <win>  | <n>   | <n>  | <n>       | <ts>  | [edit] |         │  [6] Capsule           │
│  | <id> | <win>  | <n>   | <n>  | <n>       | <ts>  | [edit] |         │  [7] Brain             │
│                                                                        │  [8] Desktop           │
│  Counters are live. No counter value is drawn from the design.         │       GATED (UI-X-08)  │
│                                                                        │                        │
│  ┌── rule detail (selected) ────────────────────────────┐              │                        │
│  │ id <rule.id>                                         │              │                        │
│  │ bucket <rule.bucket>   key <rule.key>                │              │                        │
│  │ strategy <rule.strategy>                             │              │                        │
│  └────────────────────────────────────────────────────────┘            │                        │
│                                                                        │                        │
│  [Reset counters] (UI-M-03 destructive)                                │                        │
├────────────────────────────────────────────────────────────────────────┼────────────────────────┤
│ instance strip: <session_id>  state: <state>  started: <ts>                                     │
│ neuro meters x4 (RO): DA <v>  5-HT <v>  NE <v>  ACh <v>                                         │
│   neuromodulator synced_at: <ts>   (no value without a real sync)                               │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
```

**Control map.**

| # | UI-C-* | control | notes |
|---|---|---|---|
| 1 | UI-C-072 | scope tab strip | global / tenant / user. Switching re-fetches; no cross-scope numbers are cached on screen. |
| 2 | UI-C-096 | rate-limit counter row | limit/used/remaining/reset are `‹ live value ›` from the rate-limit API. |
| 3 | UI-C-068 | edit (secondary) | Opens UI-M-01 drawer to change the rule. |
| 4 | UI-C-071 | rule detail panel | Read-only echo of the selected rule. Not a second editor. |
| 5 | UI-C-069 | Reset counters (destructive) | Opens UI-M-03. disabled-when: caller lacks infrastructure-admin role — disabled-reason: "Requires the infrastructure-admin role." |

**State variants.**

- **Loading.** Skeleton rows plus a `loading` chip in the workspace header. No counts, charts or metrics are drawn while loading.
- **Empty.** "No rate-limit rules configured."
- **Error.** "Couldn't load rate limits. ‹ reason from API ›"
- **Permission-denied.** "You don't have access to rate limits. Requires the infrastructure-admin role."
- **Offline.** You're offline. Changes will not be saved until the connection returns.

**Modal overlays.** UI-M-01 Drawer — rule editor. UI-M-03 Dialog — "Reset counters for rule <rule.id>?" (destructive).
