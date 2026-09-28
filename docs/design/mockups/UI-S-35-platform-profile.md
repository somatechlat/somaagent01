# UI-S-35 — Platform profile

**Platform profile** — Platform-admin workspace column (same view as /platform/profile) — route `/admin/profile` — facet **Auth**.
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
│  route: /admin/profile                                                 │  [1] Files             │
│  Platform profile                           [Save] [Cancel]            │  [2] Tools             │
│                                                                        │  [3] Browser           │
│  Platform identity                                                     │  [4] Editor            │
│  Name            ┌──────────────────────────┐                          │  [5] Debug             │
│                  │ <platform.name>          │                          │  [6] Capsule           │
│  Support contact └──────────────────────────┘                          │  [7] Brain             │
│                  │ <platform.support_email> │                          │  [8] Desktop           │
│                  ┌──────────────────────────┐                          │       GATED (UI-X-08)  │
│                                                                        │                        │
│  Operator identity (this account)                                      │                        │
│  Role chips: <role>  <role>   Display name ┌────────────────┐          │                        │
│                                 │ <user.name>    │                     │                        │
│                                 ┌────────────────┐                     │                        │
│                                                                        │                        │
│  Danger zone                                                           │                        │
│  [Rotate platform signing key]  (opens UI-M-03)                        │                        │
│  secrets render masked sk-***...aBcD  note: rotate in Vault            │                        │
├────────────────────────────────────────────────────────────────────────┼────────────────────────┤
│ instance strip: <session_id>  state: <state>  started: <ts>                                     │
│ neuro meters x4 (RO): DA <v>  5-HT <v>  NE <v>  ACh <v>                                         │
│   neuromodulator synced_at: <ts>   (no value without a real sync)                               │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
```

**Control map.**

| # | UI-C-* | control | notes |
|---|---|---|---|
| 1 | UI-C-061 | platform name input | Platform display name. No default value invented. |
| 2 | UI-C-061 | support contact input | type=email. |
| 3 | UI-C-087 | operator identity display | Current account; role chips come from the session. |
| 4 | UI-C-067 | Save (primary) | disabled-while: request in flight. |
| 5 | UI-C-084 | signing key readout (masked) | Renders `sk-••••••••aBcD` with a "rotate in Vault" note. Never a real value, never an editable field. |
| 6 | UI-C-069 | Rotate platform signing key (destructive) | Opens UI-M-03. disabled-when: not platform admin — disabled-reason: "Requires the platform-admin role." |

**State variants.**

- **Loading.** Skeleton rows plus a `loading` chip in the workspace header. No counts, charts or metrics are drawn while loading.
- **Empty.** "No platform profile stored yet. Fill in the name and support contact."
- **Error.** "Couldn't load the platform profile. ‹ reason from API ›"
- **Permission-denied.** "You don't have access to platform profile. Requires the platform-admin role."
- **Offline.** You're offline. Changes will not be saved until the connection returns.

**Modal overlays.** UI-M-03 Dialog — "Rotate the platform signing key? Existing signatures will need re-signing." (destructive).
