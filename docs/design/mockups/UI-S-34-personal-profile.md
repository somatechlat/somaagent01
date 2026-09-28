# UI-S-34 — Personal profile

**Personal profile** — Authenticated workspace column — route `/profile` — facet **Auth**.
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
│  route: /profile                                                       │  [1] Files             │
│  Personal profile                           [Save] [Cancel]            │  [2] Tools             │
│                                                                        │  [3] Browser           │
│  Identity                                                              │  [4] Editor            │
│  ┌── avatar ──┐  Display name  ┌─────────────────────┐                 │  [5] Debug             │
│  │  <avatar>  │  │ <user.name>    │                                    │  [6] Capsule           │
│  └────────────┘  └─────────────────────┘                               │  [7] Brain             │
│  [Upload avatar]  Email  <user.email>  (read-only)                     │  [8] Desktop           │
│                                                                        │       GATED (UI-X-08)  │
│  Security                                                              │                        │
│  [Change password]  [Manage MFA -> /mfa/setup]  [Sign out everywhere]  │                        │
│                                                                        │                        │
│  Active sessions                                                       │                        │
│  | device | ip | last seen | current | [revoke] |                      │                        │
│  | <ua>   | <ip> | <ts>  | yes/no  | [revoke] |                        │                        │
│  | <ua>   | <ip> | <ts>  | yes/no  | [revoke] |                        │                        │
├────────────────────────────────────────────────────────────────────────┼────────────────────────┤
│ instance strip: <session_id>  state: <state>  started: <ts>                                     │
│ neuro meters x4 (RO): DA <v>  5-HT <v>  NE <v>  ACh <v>                                         │
│   neuromodulator synced_at: <ts>   (no value without a real sync)                               │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
```

**Control map.**

| # | UI-C-* | control | notes |
|---|---|---|---|
| 1 | UI-C-087 | avatar / identity display | Avatar is a real upload or a letter fallback — never a stock image. |
| 2 | UI-C-061 | display name input | Editable. |
| 3 | UI-C-073 | email readout | Read-only here. Email change is a separate verified flow and is not drawn as editable. |
| 4 | UI-C-067 | Save (primary) | disabled-while: request in flight. |
| 5 | UI-C-088 | active sessions list | Rows come from the sessions API. No session rows are invented. |
| 6 | UI-C-069 | Sign out everywhere (destructive) | Opens UI-M-03. |

**State variants.**

- **Loading.** Skeleton rows plus a `loading` chip in the workspace header. No counts, charts or metrics are drawn while loading.
- **Empty.** "No active sessions to show."
- **Error.** "Couldn't load your profile. ‹ reason from API ›"
- **Permission-denied.** "You don't have access to this profile. Sign in with your own account."
- **Offline.** You're offline. Changes will not be saved until the connection returns.

**Modal overlays.** UI-M-03 Dialog — "Sign out of all sessions, including this one?" (destructive). Per-row [revoke] uses the same dialog pattern.
