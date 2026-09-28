# UI-S-51 — Settings — Models

**Settings — Models** — Settings workspace column, Models tab (alias /agent/models) — route `/settings/models` — facet **Settings**.
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
│  route: /settings/models                                               │  [1] Files             │
│  Settings - Models       tabs: [Agent][Models][Channels][External]     │  [2] Tools             │
│                                                                        │  [3] Browser           │
│  Providers                                                             │  [4] Editor            │
│  | provider | base url | default model | key | [edit] |                │  [5] Debug             │
│  | <name>   | <url>    | <model>       | stored/missing | [edit] |     │  [6] Capsule           │
│  | <name>   | <url>    | <model>       | no key | [edit] |             │  [7] Brain             │
│                                                                        │  [8] Desktop           │
│  Model catalog                                                         │       GATED (UI-X-08)  │
│  | model | provider | enabled | [enable] |                             │                        │
│  | <id>  | <prov>   | yes/no  | [enable] |                             │                        │
│  | <id>  | <prov>   | yes/no  | [enable] |                             │                        │
│                                                                        │                        │
│  Slots (Chat / Utility / Embedding)                                    │                        │
│  | slot | bound model | source |                                       │                        │
│  | chat | <model>     | capsule or tenant default |                    │                        │
│  | utility | <model>  | capsule or tenant default |                    │                        │
│  | embedding | <model>| capsule or tenant default |                    │                        │
│                                                                        │                        │
│  Model setup required? Show the notice only when the API says so.      │                        │
├────────────────────────────────────────────────────────────────────────┼────────────────────────┤
│ instance strip: <session_id>  state: <state>  started: <ts>                                     │
│ neuro meters x4 (RO): DA <v>  5-HT <v>  NE <v>  ACh <v>                                         │
│   neuromodulator synced_at: <ts>   (no value without a real sync)                               │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
```

**Control map.**

| # | UI-C-* | control | notes |
|---|---|---|---|
| 1 | UI-C-101 | provider row | base url, default model, key status from the provider record. Never a hard-coded URL. |
| 2 | UI-C-084 | key status (masked) | stored / missing / no key. When stored, render `sk-••••••••aBcD` + "rotate in Vault". Write-only. |
| 3 | UI-C-071 | model catalog row | Only models the provider actually lists. enable/disable talks to the API. |
| 4 | UI-C-102 | slot binding row | Chat / Utility / Embedding bindings. The source column says whether the value is a capsule or tenant default — it is never silently overridden. |
| 5 | UI-C-068 | Test connection (secondary) | Calls the real connection test. disabled-when: no key stored — disabled-reason: "No API key stored for this provider." |

**State variants.**

- **Loading.** Skeleton rows plus a `loading` chip in the workspace header. No counts, charts or metrics are drawn while loading.
- **Empty.** "Model setup required. Add a provider and bind a chat model."
- **Error.** "Couldn't load models. ‹ reason from API ›"
- **Permission-denied.** "You don't have access to model settings. Requires the agent-owner role."
- **Offline.** You're offline. Changes will not be saved until the connection returns.

**Modal overlays.** UI-M-01 Drawer — key entry and provider edit (write-only secret fields). UI-M-03 Dialog — "Revoke the stored key for <provider.name>?" (destructive).
