# UI-X-02 — Tools

**Tools** — Right-rail panel in context — route `right-rail surface [2]` — facet **Surface**.
Chrome abbreviated (UI-S-00). Facet tabs and surface rail are visible.

```
┌─ chrome (abbrev) ──────────────────────┬ RIGHT RAIL · UI-X-02 Tools                                                                     ┐
│  capsule <capsule.name> v<version>     │ Surface: Tools                       filter [__________]                                       │
│  <lifecycle>  knobs (IQ <v>)(auto <v>)(│ ┌─ tool list ─────────────────────────────────────────────────────────────┐                    │
│  derived AgentIQ RO: <readouts, greyed>│ │ [x] <tool.name>        enabled                                           │                   │
│  facets [Soul][Brain][Hands][Memory][Bo│ │     <tool.summary>                                                        │                  │
│  <Cmd-K>                               │ │ [ ] <tool.name>        disabled                                          │                   │
│                                        │ │     <tool.summary>                                                        │                  │
│  WORKSPACE (abbrev)                    │ │ [x] <tool.name>        enabled                                           │                   │
│  ┌────────────────────────────────┐    │ └──────────────────────────────────────────────────────────────────────────┘                   │
│  │ screen content in context        │  │ ┌─ call log ──────────────────────────────────────────────────────────────┐                    │
│  │ (see UI-S-07 chat workspace)     │  │ │ <ts> <tool.name> <result> [inspect]                                      │                   │
│  │ surface rail select: UI-X-02 Tools  │ │ <ts> <tool.name> <result> [inspect]                                      │                   │
│  └────────────────────────────────┘    │ └──────────────────────────────────────────────────────────────────────────┘                   │
│                                        │ [arg schema] [approval rules]                                                                  │
│  instance <session_id> <state>         │                                                                                                │
│  neuro RO DA <v> 5-HT <v> NE <v> ACh <v│                                                                                                │
└────────────────────────────────────────┴────────────────────────────────────────────────────────────────────────────────────────────────┘
```

**Control map.**

| # | UI-C-* | control | notes |
|---|---|---|---|
| 1 | UI-C-108 | tool call log | Real tool invocations only. result is the real outcome; no timings or counts are invented. |
| 2 | UI-C-097 | tool enable/disable toggle | Mirrors the Hands capability state. disabled-when: tool gated by policy — disabled-reason: "Blocked by tool_policy." |
| 3 | UI-C-070 | filter input | Filters the real tool list. |
| 4 | UI-C-068 | arg schema (secondary) | Opens UI-M-01 drawer with the tool's real input schema. |
| 5 | UI-C-071 | approval rules readout | Read-only echo of the current approval rules. Not an editor here. |

**State variants.**

- **Loading.** Skeleton rows plus a `loading` chip in the workspace header. No counts, charts or metrics are drawn while loading.
- **Empty.** "No tools registered for this capsule."
- **Error.** "Couldn't load tools. ‹ reason from API ›"
- **Permission-denied.** "You don't have access to the tools surface. Requires the Hands facet access."
- **Offline.** You're offline. Changes will not be saved until the connection returns.

**Modal overlays.** UI-M-01 Drawer — tool detail: argument schema, approval rules, recent calls.
