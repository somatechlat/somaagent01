# UI-X-05 — Debug

**Debug** — Right-rail panel in context — route `right-rail surface [5]` — facet **Surface**.
Chrome abbreviated (UI-S-00). Facet tabs and surface rail are visible.

```
┌─ chrome (abbrev) ──────────────────────┬ RIGHT RAIL · UI-X-05 Debug                                                                     ┐
│  capsule <capsule.name> v<version>     │ Surface: Debug     filter [__________]  [pause] [clear]                                        │
│  <lifecycle>  knobs (IQ <v>)(auto <v>)(│ ┌─ event stream ──────────────────────────────────────────────────────────┐                    │
│  derived AgentIQ RO: <readouts, greyed>│ │ <ts> <event.type> <summary>  [inspect]                                   │                   │
│  facets [Soul][Brain][Hands][Memory][Bo│ │ <ts> <event.type> <summary>  [inspect]                                   │                   │
│  <Cmd-K>                               │ │ <ts> <event.type> <summary>  [inspect]                                   │                   │
│                                        │ │ <ts> <event.type> <summary>  [inspect]                                   │                   │
│  WORKSPACE (abbrev)                    │ └──────────────────────────────────────────────────────────────────────────┘                   │
│  ┌────────────────────────────────┐    │ ┌─ request inspector ─────────────────────────────────────────────────────┐                    │
│  │ screen content in context        │  │ │ request <id>  status <code>  dur <ts>                                    │                   │
│  │ (see UI-S-07 chat workspace)     │  │ │ headers (read-only)  body (truncated)                                    │                   │
│  │ surface rail select: UI-X-05 Debug  │ └──────────────────────────────────────────────────────────────────────────┘                   │
│  └────────────────────────────────┘    │ [WS frame log] [open full-screen (UI-M-02)]                                                    │
│                                        │                                                                                                │
│  instance <session_id> <state>         │                                                                                                │
│  neuro RO DA <v> 5-HT <v> NE <v> ACh <v│                                                                                                │
└────────────────────────────────────────┴────────────────────────────────────────────────────────────────────────────────────────────────┘
```

**Control map.**

| # | UI-C-* | control | notes |
|---|---|---|---|
| 1 | UI-C-111 | debug event stream | Real WS/API events only. Frames are `‹ live value ›`; nothing is synthesised to fill the pane. |
| 2 | UI-C-112 | request inspector | Read-only echo of the selected request/response. |
| 3 | UI-C-070 | filter input | Filters the live stream. |
| 4 | UI-C-065 | pause toggle | Pauses rendering of new events. Does not stop collection. |
| 5 | UI-C-068 | WS frame log (secondary) | Opens UI-M-01 drawer with the frame log. |

**State variants.**

- **Loading.** Skeleton rows plus a `loading` chip in the workspace header. No counts, charts or metrics are drawn while loading.
- **Empty.** "No events yet. Interact with the agent to see traffic."
- **Error.** "Couldn't attach to the event stream. ‹ reason from API ›"
- **Permission-denied.** "You don't have access to the debug surface. Requires the developer role."
- **Offline.** You're offline. Changes will not be saved until the connection returns.

**Modal overlays.** UI-M-01 Drawer — event/frame inspector. UI-M-02 Full-screen — raw frame payload (explicit dismiss only).
