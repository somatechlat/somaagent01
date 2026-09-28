# UI-X-03 — Browser

**Browser** — Right-rail panel in context — route `right-rail surface [3]` — facet **Surface**.
Chrome abbreviated (UI-S-00). Facet tabs and surface rail are visible.

```
┌─ chrome (abbrev) ──────────────────────┬ RIGHT RAIL · UI-X-03 Browser                                                                   ┐
│  capsule <capsule.name> v<version>     │ Surface: Browser                                                                               │
│  <lifecycle>  knobs (IQ <v>)(auto <v>)(│ ┌─ url bar ───────────────────────────────────────────────────────────────┐                    │
│  derived AgentIQ RO: <readouts, greyed>│ │ <url>                                                     [go] [reload] │                    │
│  facets [Soul][Brain][Hands][Memory][Bo│ └──────────────────────────────────────────────────────────────────────────┘                   │
│  <Cmd-K>                               │ ┌─ viewport ──────────────────────────────────────────────────────────────┐                    │
│                                        │ │                                                                          │                   │
│  WORKSPACE (abbrev)                    │ │   <page content rendered by worker>                                      │                   │
│  ┌────────────────────────────────┐    │ │   (or the reason the viewport cannot render)                             │                   │
│  │ screen content in context        │  │ │                                                                          │                   │
│  │ (see UI-S-07 chat workspace)     │  │ └──────────────────────────────────────────────────────────────────────────┘                   │
│  │ surface rail select: UI-X-03 Browser│ [back][forward][reload]  [screenshot] [pick element]                                           │
│  └────────────────────────────────┘    │ When no browser worker is attached the viewport shows                                          │
│                                        │ the reason. It never shows a fake page.                                                        │
│  instance <session_id> <state>         │                                                                                                │
│  neuro RO DA <v> 5-HT <v> NE <v> ACh <v│                                                                                                │
└────────────────────────────────────────┴────────────────────────────────────────────────────────────────────────────────────────────────┘
```

**Control map.**

| # | UI-C-* | control | notes |
|---|---|---|---|
| 1 | UI-C-109 | URL bar + viewport | Viewport renders only when a browser worker is attached. Otherwise it prints the attachment reason. |
| 2 | UI-C-068 | go / reload / back / forward | disabled-when: no browser worker — disabled-reason: "No browser worker attached." |
| 3 | UI-C-077 | screenshot | Captures via the real worker. disabled-when: no browser worker — disabled-reason: "No browser worker attached." |
| 4 | UI-C-068 | pick element (secondary) | disabled-when: the worker cannot pick — disabled-reason: "Element picking is not supported by this worker." |

**State variants.**

- **Loading.** Viewport shows a neutral `loading` frame. No page content is faked while loading.
- **Empty.** "No page loaded. Enter a URL to browse."
- **Error.** "Couldn't load the page. ‹ reason from API ›"
- **Permission-denied.** "You don't have access to the browser surface. Requires the Hands facet access."
- **Offline.** You're offline. Changes will not be saved until the connection returns.

**Modal overlays.** UI-M-02 Full-screen — open the current page in a focus viewport (explicit dismiss only).
