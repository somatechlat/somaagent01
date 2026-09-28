# UI-S-42 — Marketplace

**Marketplace** — Ops workspace column — route `/platform/marketplace` — facet **Ops**.
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
│  route: /platform/marketplace                                          │  [1] Files             │
│  Marketplace        search: [____________]  category: [<all>]          │  [2] Tools             │
│                                                                        │  [3] Browser           │
│  ┌───────────────────┐ ┌───────────────────┐ ┌───────────────────┐     │  [4] Editor            │
│  │ <item.name>       │ │ <item.name>       │ │ <item.name>       │     │  [5] Debug             │
│  │ <item.summary>    │ │ <item.summary>    │ │ <item.summary>    │     │  [6] Capsule           │
│  │ publisher <name>  │ │ publisher <name>  │ │ publisher <name>  │     │  [7] Brain             │
│  │ version <semver>  │ │ version <semver>  │ │ version <semver>  │     │  [8] Desktop           │
│  │ [details] [install]│ │ [details] [install]│ │ [details] [install]│  │       GATED (UI-X-08)  │
│  └───────────────────┘ └───────────────────┘ └───────────────────┘     │                        │
│                                                                        │                        │
│  ┌───────────────────┐ ┌───────────────────┐                           │                        │
│  │ <item.name>       │ │ <item.name>       │                           │                        │
│  │ [details] [install]│ │ [details] [install]│                         │                        │
│  └───────────────────┘ └───────────────────┘                           │                        │
│                                                                        │                        │
│  Installed items show [configure] and [uninstall] instead.             │                        │
├────────────────────────────────────────────────────────────────────────┼────────────────────────┤
│ instance strip: <session_id>  state: <state>  started: <ts>                                     │
│ neuro meters x4 (RO): DA <v>  5-HT <v>  NE <v>  ACh <v>                                         │
│   neuromodulator synced_at: <ts>   (no value without a real sync)                               │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
```

**Control map.**

| # | UI-C-* | control | notes |
|---|---|---|---|
| 1 | UI-C-070 | search / category filter | Queries the marketplace API. The grid never pre-fills invented items. |
| 2 | UI-C-081 | marketplace item card | name/summary/publisher/version all come from the registry record. |
| 3 | UI-C-068 | details (secondary) | Opens UI-M-01 drawer with the item's real manifest. |
| 4 | UI-C-067 | install (primary) | disabled-when: already installed or caller lacks install permission — disabled-reason printed inline on the card. |
| 5 | UI-C-069 | uninstall (destructive) | Opens UI-M-03. Only rendered for installed items. |

**State variants.**

- **Loading.** Skeleton rows plus a `loading` chip in the workspace header. No counts, charts or metrics are drawn while loading.
- **Empty.** "No marketplace items match this filter."
- **Error.** "Couldn't load the marketplace. ‹ reason from API ›"
- **Permission-denied.** "You don't have access to the marketplace. Requires the platform-admin role."
- **Offline.** You're offline. Changes will not be saved until the connection returns.

**Modal overlays.** UI-M-01 Drawer — item detail (manifest, permissions requested, changelog). UI-M-03 Dialog — "Uninstall <item.name>?" (destructive).
