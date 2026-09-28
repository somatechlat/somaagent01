# UI-S-52 — Settings — Channels

**Settings — Channels** — Settings workspace column, Channels tab (alias /agent/channels) — route `/settings/channels` — facet **Settings**.
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
│  route: /settings/channels                                             │  [1] Files             │
│  Settings - Channels     tabs: [Agent][Models][Channels][External]     │  [2] Tools             │
│                                           [+ Add Channel]              │  [3] Browser           │
│                                                                        │  [4] Editor            │
│  Capsule modules                                                       │  [5] Debug             │
│  | module | title | enabled | [enable/disable] |                       │  [6] Capsule           │
│  | <name> | <title> | yes/no | [toggle] |                              │  [7] Brain             │
│  (empty notice: "No channel modules registered")                       │  [8] Desktop           │
│                                                                        │       GATED (UI-X-08)  │
│  Add channel                                                           │                        │
│  Kind         [WhatsApp v]   Mode [poll / baileys v]                   │                        │
│  Capsule ID   ┌──────────────────────────┐                             │                        │
│               │ <capsule.id>             │                             │                        │
│  Bot token    └──────────────────────────┘                             │                        │
│  (write-only) | sk-***...aBcD  rotate in Vault                         │                        │
│  Group mode   [mention v]  Allowlist ┌────────────────┐                │                        │
│                                 │ <csv allowlist>  │                   │                        │
│                                 ┌────────────────┐                     │                        │
│  [Create channel]                                                      │                        │
│                                                                        │                        │
│  Configured channels                                                   │                        │
│  | channel | kind | capsule | state | [edit][x] |                      │                        │
├────────────────────────────────────────────────────────────────────────┼────────────────────────┤
│ instance strip: <session_id>  state: <state>  started: <ts>                                     │
│ neuro meters x4 (RO): DA <v>  5-HT <v>  NE <v>  ACh <v>                                         │
│   neuromodulator synced_at: <ts>   (no value without a real sync)                               │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
```

**Control map.**

| # | UI-C-* | control | notes |
|---|---|---|---|
| 1 | UI-C-103 | channel module row | Module name/title/enabled from the registered capsule modules. |
| 2 | UI-C-113 | channel create form | Kind/mode options are the real enum values from the API (e.g. WhatsApp modes poll / baileys, Telegram modes webhook / cloud). Capsule ID is required for dispatch. |
| 3 | UI-C-084 | bot token input (write-only) | Write-only. Renders `sk-••••••••aBcD` when a token exists, plus "rotate in Vault". Never echoed back. |
| 4 | UI-C-063 | group mode / allowlist | Group mode options from the API. Allowlist is a plain CSV field. |
| 5 | UI-C-071 | configured channels table | Rows from the channels API. state is the real dispatch state. |
| 6 | UI-C-069 | delete channel (destructive) | Opens UI-M-03. disabled-when: channel is mid-dispatch — disabled-reason: "Channel is dispatching. Try again when it is idle." |

**State variants.**

- **Loading.** Skeleton rows plus a `loading` chip in the workspace header. No counts, charts or metrics are drawn while loading.
- **Empty.** "No channels configured. Add a channel to start dispatching."
- **Error.** "Couldn't load channels. ‹ reason from API ›"
- **Permission-denied.** "You don't have access to channel settings. Requires the agent-owner role."
- **Offline.** You're offline. Changes will not be saved until the connection returns.

**Modal overlays.** UI-M-01 Drawer — channel configuration edit (token write-only). UI-M-03 Dialog — "Delete channel <channel.id>?" (destructive).
