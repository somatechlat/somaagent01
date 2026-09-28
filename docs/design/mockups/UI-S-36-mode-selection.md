# UI-S-36 — Mode selection

**Mode selection** — Post-auth workspace column (alias /select-mode) — route `/mode-select` — facet **Auth**.
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
│ WORKSPACE  facet: Auth                                                 │ SURFACE RAIL x8        │
│  route: /mode-select                                                   │  [1] Files             │
│  Welcome to SomaAgent                 Signed in as                     │  [2] Tools             │
│  Select how you'd like to continue    <user.name> (<user.email>)       │  [3] Browser           │
│                                                                        │  [4] Editor            │
│  ┌─────────────────────┐  ┌─────────────────────┐                      │  [5] Debug             │
│  │ God Mode            │  │ Enter Tenant        │                      │  [6] Capsule           │
│  │ SAAS Admin          │  │ Impersonate         │                      │  [7] Brain             │
│  │                     │  │                     │                      │  [8] Desktop           │
│  │ [ Continue        ] │  │ Search tenants...   │                      │       GATED (UI-X-08)  │
│  └─────────────────────┘  │ └─────────────────┘ │                      │                        │
│                           │ │ <tenant.name>   │ │                      │                        │
│                           │ │ <n> agents,     │ │                      │                        │
│                           │ │ <n> users <tier>│ │                      │                        │
│                           │ ┌─────────────────┐ │                      │                        │
│                           │ │ <tenant.name>   │ │                      │                        │
│                           │ └─────────────────┘ │                      │                        │
│                           │ [ Continue        ] │                      │                        │
│                           ┌─────────────────────┐                      │                        │
│                                                                        │                        │
│  [Sign out]                                                            │                        │
├────────────────────────────────────────────────────────────────────────┼────────────────────────┤
│ instance strip: <session_id>  state: <state>  started: <ts>                                     │
│ neuro meters x4 (RO): DA <v>  5-HT <v>  NE <v>  ACh <v>                                         │
│   neuromodulator synced_at: <ts>   (no value without a real sync)                               │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
```

**Control map.**

| # | UI-C-* | control | notes |
|---|---|---|---|
| 1 | UI-C-089 | mode card (God Mode / Enter Tenant) | Two selectable cards. Which cards render depends on the caller's real roles — a card the caller cannot use is omitted or disabled with its reason, never shown as available. |
| 2 | UI-C-070 | tenant search input | Filters the tenant picker server-side. No locally fabricated list. |
| 3 | UI-C-090 | tenant picker row | Row shows `<tenant.name>`, counts as `‹ live value ›`, and the tier label from the API. |
| 4 | UI-C-067 | Continue (primary) | disabled-until: a mode (and tenant, when required) is selected. |
| 5 | UI-C-068 | Sign out (secondary) | Clears the session and routes to /login. |

**State variants.**

- **Loading.** Skeleton rows plus a `loading` chip in the workspace header. No counts, charts or metrics are drawn while loading.
- **Empty.** "No tenants available for this account. Ask a platform admin to grant access."
- **Error.** "Couldn't load modes or tenants. ‹ reason from API ›"
- **Permission-denied.** "This account cannot enter God Mode. Requires the platform-admin role."
- **Offline.** You're offline. Changes will not be saved until the connection returns.

**Modal overlays.** None. This screen opens no overlay.
