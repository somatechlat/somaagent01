# UI-S-53 — Settings — External & Developer

**Settings — External & Developer** — Settings workspace column, External & Developer tab (planned) — route `NEW (no route yet)` — facet **Settings**.
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
│ WORKSPACE  facet: Settings                                             │ SURFACE RAIL x8        │
│  route: NEW (planned)                                                  │  [1] Files             │
│  Settings - External & Developer                                       │  [2] Tools             │
│  tabs: [Agent][Models][Channels][External]                             │  [3] Browser           │
│                                                                        │  [4] Editor            │
│  External services                                                     │  [5] Debug             │
│  | service | credential | status | [edit][rotate] |                    │  [6] Capsule           │
│  | <name>  | sk-***...aBcD | stored/missing | [edit][rotate] |         │  [7] Brain             │
│  | <name>  | sk-***...aBcD | stored/missing | [edit][rotate] |         │  [8] Desktop           │
│  note: rotate in Vault. Credentials are write-only.                    │       GATED (UI-X-08)  │
│                                                                        │                        │
│  Developer                                                             │                        │
│  | tool | state | reason when gated |                                  │                        │
│  | API keys | available | - |                                          │                        │
│  | Feature flags | available | - |                                     │                        │
│  | WebSocket event console | gated | moved to Debug surface (UI-X-05) |│                        │
│  | WebSocket tester | gated | moved to Debug surface (UI-X-05) |       │                        │
│                                                                        │                        │
│  Route note: this screen is NEW per the ID register.                   │                        │
│  No route is wired in webui/src/main.ts today.                         │                        │
├────────────────────────────────────────────────────────────────────────┼────────────────────────┤
│ instance strip: <session_id>  state: <state>  started: <ts>                                     │
│ neuro meters x4 (RO): DA <v>  5-HT <v>  NE <v>  ACh <v>                                         │
│   neuromodulator synced_at: <ts>   (no value without a real sync)                               │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
```

**Control map.**

| # | UI-C-* | control | notes |
|---|---|---|---|
| 1 | UI-C-115 | external credential row | Service name + masked credential `sk-••••••••aBcD` + "rotate in Vault". Write-only. Never a real value. |
| 2 | UI-C-068 | edit (secondary) | Opens UI-M-01 drawer to write a new credential. The drawer never echoes the stored secret. |
| 3 | UI-C-069 | rotate credential (destructive) | Opens UI-M-03. disabled-when: no credential stored — disabled-reason: "No credential stored to rotate." |
| 4 | UI-C-104 | developer tool row | Each row states its real availability. Rows that live in the Debug surface say so; nothing is drawn as a working control over nothing. |
| 5 | UI-C-073 | status chip | available / gated. A gated row prints its blocking reason inline. |

**State variants.**

- **Loading.** Skeleton rows plus a `loading` chip in the workspace header. No counts, charts or metrics are drawn while loading.
- **Empty.** "No external services configured."
- **Error.** "Couldn't load external services. ‹ reason from API ›"
- **Permission-denied.** "You don't have access to external & developer settings. Requires the platform-admin role."
- **Offline.** You're offline. Changes will not be saved until the connection returns.

**Modal overlays.** UI-M-01 Drawer — credential write form (write-only). UI-M-03 Dialog — "Rotate the stored credential for <service.name>?" (destructive).
