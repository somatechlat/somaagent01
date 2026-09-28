# UI-S-28 — Tier builder

**Tier builder** — Platform admin workspace column — route `/platform/tiers` — facet **Platform**.
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
│ WORKSPACE  facet: Platform                                             │ SURFACE RAIL x8        │
│  route: /platform/tiers                                                │  [1] Files             │
│  Tier builder                              [+ Add Tier] [refresh]      │  [2] Tools             │
│  Manage pricing plans and feature bundles                              │  [3] Browser           │
│                                                                        │  [4] Editor            │
│   ┌────────────────┐ ┌────────────────┐ ┌────────────────┐             │  [5] Debug             │
│   │ <tier.name>    │ │ <tier.name>    │ │ <tier.name>    │             │  [6] Capsule           │
│   │ <tier.slug>    │ │ <tier.slug>    │ │ <tier.slug>    │             │  [7] Brain             │
│   │ <price>/<period>│ │ <price>/<period>│ │ <price>/<period>│          │  [8] Desktop           │
│   │ users <limit>  │ │ users <limit>  │ │ users <limit>  │             │       GATED (UI-X-08)  │
│   │ tokens/mo <n>  │ │ tokens/mo <n>  │ │ tokens/mo <n>  │             │                        │
│   │ storage <n> GB │ │ storage <n> GB │ │ storage <n> GB │             │                        │
│   │ <n> tenants    │ │ <n> tenants    │ │ <n> tenants    │             │                        │
│   │ [edit][copy][x]│ │ [edit][copy][x]│ │ [edit][copy][x]│             │                        │
│   └────────────────┘ └────────────────┘ └────────────────┘             │                        │
│                                                                        │                        │
│  Feature bundle matrix (read-only summary)                             │                        │
│  | feature | <tier> | <tier> | <tier> |                                │                        │
│  | <feat>  | on/off | on/off | on/off |                                │                        │
├────────────────────────────────────────────────────────────────────────┼────────────────────────┤
│ instance strip: <session_id>  state: <state>  started: <ts>                                     │
│ neuro meters x4 (RO): DA <v>  5-HT <v>  NE <v>  ACh <v>                                         │
│   neuromodulator synced_at: <ts>   (no value without a real sync)                               │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
```

**Control map.**

| # | UI-C-* | control | notes |
|---|---|---|---|
| 1 | UI-C-081 | tier card | One card per tier. Values are `‹ live value ›` from the tiers API — never drawn as fixed numbers. |
| 2 | UI-C-067 | Add Tier (primary) | Opens UI-M-01 drawer form (Create Tier). |
| 3 | UI-C-068 | refresh (secondary) | Re-fetches the tier list. No cached counts shown. |
| 4 | UI-C-081 | edit / copy / delete on card | delete opens UI-M-03 destructive dialog. disabled-when: caller lacks billing-admin role — disabled-reason: "Requires the billing-admin role." |
| 5 | UI-C-071 | feature bundle matrix | Read-only summary. Not an editor. |

**State variants.**

- **Loading.** Skeleton rows plus a `loading` chip in the workspace header. No counts, charts or metrics are drawn while loading.
- **Empty.** "No tiers yet. Create the first tier to define plans and limits."
- **Error.** "Couldn't load tiers. ‹ reason from API ›"
- **Permission-denied.** "You don't have access to the tier builder. Ask a platform admin for the billing-admin role."
- **Offline.** You're offline. Changes will not be saved until the connection returns.

**Modal overlays.** UI-M-01 Drawer — create/edit tier (feature bundles, limits). UI-M-03 Dialog — "Delete tier <tier.name>? Tenants on this tier keep their current assignment until reassigned." (destructive).
