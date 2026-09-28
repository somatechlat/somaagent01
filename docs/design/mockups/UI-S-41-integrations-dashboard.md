# UI-S-41 — Integrations dashboard

**Integrations dashboard** — Ops workspace column (alias /saas/settings/integrations) — route `/platform/integrations` — facet **Ops**.
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
│  route: /platform/integrations                                         │  [1] Files             │
│  Integrations dashboard                          [+ Connect]           │  [2] Tools             │
│                                                                        │  [3] Browser           │
│  ┌───────────────────┐ ┌───────────────────┐ ┌───────────────────┐     │  [4] Editor            │
│  │ <integration.name>│ │ <integration.name>│ │ <integration.name>│     │  [5] Debug             │
│  │ <state>           │ │ <state>           │ │ <state>           │     │  [6] Capsule           │
│  │ connected <ts>    │ │ not connected     │ │ error <reason>    │     │  [7] Brain             │
│  │ [configure][x]    │ │ [connect]         │ │ [configure][x]    │     │  [8] Desktop           │
│  └───────────────────┘ └───────────────────┘ └───────────────────┘     │       GATED (UI-X-08)  │
│                                                                        │                        │
│  ┌───────────────────┐ ┌───────────────────┐                           │                        │
│  │ <integration.name>│ │ <integration.name>│                           │                        │
│  │ <state>           │ │ <state>           │                           │                        │
│  │ [configure][x]    │ │ [connect]         │                           │                        │
│  └───────────────────┘ └───────────────────┘                           │                        │
│                                                                        │                        │
│  Credential note: values render masked (sk-***...aBcD)                 │                        │
│  with a rotate-in-Vault note. Never echoed in full.                    │                        │
├────────────────────────────────────────────────────────────────────────┼────────────────────────┤
│ instance strip: <session_id>  state: <state>  started: <ts>                                     │
│ neuro meters x4 (RO): DA <v>  5-HT <v>  NE <v>  ACh <v>                                         │
│   neuromodulator synced_at: <ts>   (no value without a real sync)                               │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
```

**Control map.**

| # | UI-C-* | control | notes |
|---|---|---|---|
| 1 | UI-C-081 | integration card | Name and state from the integrations API. A card never shows a connected state without a real connection record. |
| 2 | UI-C-073 | connection state chip | connected / not connected / error. Error shows `‹ reason from API ›`, not a made-up code. |
| 3 | UI-C-068 | configure / connect | configure opens UI-M-01 drawer. connect starts the real OAuth/API flow. |
| 4 | UI-C-084 | masked credential display | Where a secret exists: `sk-••••••••aBcD` + "rotate in Vault". Write-only — never echoed back from the server. |
| 5 | UI-C-069 | disconnect (destructive) | Opens UI-M-03. disabled-when: not connected — disabled-reason: "No live connection to disconnect." |

**State variants.**

- **Loading.** Skeleton rows plus a `loading` chip in the workspace header. No counts, charts or metrics are drawn while loading.
- **Empty.** "No integrations connected. Connect a service to see it here."
- **Error.** "Couldn't load integrations. ‹ reason from API ›"
- **Permission-denied.** "You don't have access to integrations. Requires the platform-admin role."
- **Offline.** You're offline. Changes will not be saved until the connection returns.

**Modal overlays.** UI-M-01 Drawer — integration configuration (fields per integration, secrets write-only). UI-M-03 Dialog — "Disconnect <integration.name>?" (destructive).
