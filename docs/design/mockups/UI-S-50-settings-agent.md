# UI-S-50 — Settings — Agent

**Settings — Agent** — Settings workspace column, Agent tab — route `/settings` — facet **Settings**.
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
│  route: /settings                                                      │  [1] Files             │
│  Settings - Agent        tabs: [Agent][Models][Channels][External]     │  [2] Tools             │
│                                          [Save] [Cancel]               │  [3] Browser           │
│                                                                        │  [4] Editor            │
│  Providers / Slots / Keys                                              │  [5] Debug             │
│  | slot | provider | model | key status |                              │  [6] Capsule           │
│  | chat | <prov>   | <mdl> | stored/missing |                          │  [7] Brain             │
│  | utility | <prov> | <mdl> | stored/missing |                         │  [8] Desktop           │
│  | embedding | <prov> | <mdl> | stored/missing |                       │       GATED (UI-X-08)  │
│                                                                        │                        │
│  note: keys are Vault-backed, write-only (never echoed)                │                        │
│        example render: sk-***...aBcD   rotate in Vault                 │                        │
│                                                                        │                        │
│  Memory                                                                │                        │
│  SomaBrain URL  ┌──────────────────────────┐                           │                        │
│                 │ <somabrain.url>          │                           │                        │
│  Collection     └──────────────────────────┘                           │                        │
│                 │ <collection.name>        │                           │                        │
│                 ┌──────────────────────────┐                           │                        │
├────────────────────────────────────────────────────────────────────────┼────────────────────────┤
│ instance strip: <session_id>  state: <state>  started: <ts>                                     │
│ neuro meters x4 (RO): DA <v>  5-HT <v>  NE <v>  ACh <v>                                         │
│   neuromodulator synced_at: <ts>   (no value without a real sync)                               │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
```

**Control map.**

| # | UI-C-* | control | notes |
|---|---|---|---|
| 1 | UI-C-100 | settings tab rail | Agent / Models / Channels / External. Tabs map to UI-S-50..53 routes. |
| 2 | UI-C-101 | provider/slot row | slot, provider, model, key status are `‹ live value ›` from the settings API. |
| 3 | UI-C-084 | masked key display | Write-only. Renders `sk-••••••••aBcD` only when a key exists, plus "rotate in Vault". Never an editable echo of the secret. |
| 4 | UI-C-108 | SomaBrain connection fields | URL and collection name. Values come from the saved config. |
| 5 | UI-C-067 | Save (primary) | disabled-while: request in flight. |
| 6 | UI-C-069 | Reset agent settings (destructive) | Opens UI-M-03. disabled-when: not agent owner — disabled-reason: "Requires the agent-owner role." |

**State variants.**

- **Loading.** Skeleton rows plus a `loading` chip in the workspace header. No counts, charts or metrics are drawn while loading.
- **Empty.** "No agent configuration saved yet. Set a provider and a model slot to begin."
- **Error.** "Couldn't load agent settings. ‹ reason from API ›"
- **Permission-denied.** "You don't have access to agent settings. Requires the agent-owner role."
- **Offline.** You're offline. Changes will not be saved until the connection returns.

**Modal overlays.** UI-M-01 Drawer — key entry (write-only form; never echoes the stored value). UI-M-03 Dialog — "Reset agent settings to defaults?" (destructive).
