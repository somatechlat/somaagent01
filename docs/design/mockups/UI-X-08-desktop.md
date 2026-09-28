# UI-X-08 — Desktop

**Desktop** — Right-rail panel in context — GATED — route `right-rail surface [8]` — facet **Surface**.
Chrome abbreviated (UI-S-00). Facet tabs and surface rail are visible.

GATED — drawn present-but-disabled. Every control prints its blocking reason inline. This is not a "coming soon" placeholder and not a working-looking panel over nothing. Blocking reason (verbatim): "Requires a remote-desktop capability in somaAgent01. Not available today."

```
┌─ chrome (abbrev) ──────────────────────┬ RIGHT RAIL · UI-X-08 Desktop (GATED)                                                           ┐
│  capsule <capsule.name> v<version>     │ Surface: Desktop   STATE: present but DISABLED                                                 │
│  <lifecycle>  knobs (IQ <v>)(auto <v>)(│                                                                                                │
│  derived AgentIQ RO: <readouts, greyed>│ VIEWPORT (GATED)                                                                               │
│  facets [Soul][Brain][Hands][Memory][Bo│   [1] connect     DISABLED                                                                     │
│  <Cmd-K>                               │         reason: Requires a remote-desktop capability in somaAgent01. Not available today.      │
│                                        │   [2] viewport    DISABLED                                                                     │
│  WORKSPACE (abbrev)                    │         reason: Requires a remote-desktop capability in somaAgent01. Not available today.      │
│  ┌────────────────────────────────┐    │                                                                                                │
│  │ screen content in context        │  │ CONTROLS (all DISABLED)                                                                        │
│  │ (see UI-S-07 chat workspace)     │  │   [3] pointer     DISABLED                                                                     │
│  │ surface rail select: UI-X-08 Desktop│         reason: Requires a remote-desktop capability in somaAgent01. Not available today.      │
│  └────────────────────────────────┘    │   [4] keyboard    DISABLED                                                                     │
│                                        │         reason: Requires a remote-desktop capability in somaAgent01. Not available today.      │
│  instance <session_id> <state>         │   [5] clipboard   DISABLED                                                                     │
│  neuro RO DA <v> 5-HT <v> NE <v> ACh <v│         reason: Requires a remote-desktop capability in somaAgent01. Not available today.      │
│                                        │   [6] screenshot  DISABLED                                                                     │
│                                        │         reason: Requires a remote-desktop capability in somaAgent01. Not available today.      │
│                                        │                                                                                                │
│                                        │ This panel is present in the rail so the surface set is                                        │
│                                        │ complete. It is NOT a working panel and it is NOT a                                            │
│                                        │ "coming soon" placeholder. Every control is disabled and                                       │
│                                        │ prints its blocking reason inline.                                                             │
└────────────────────────────────────────┴────────────────────────────────────────────────────────────────────────────────────────────────┘
```

**Control map.**

| # | UI-C-* | control | notes |
|---|---|---|---|
| 1 | UI-C-115 | connect (DISABLED) | disabled-when: always — disabled-reason: "Requires a remote-desktop capability in somaAgent01. Not available today." |
| 2 | UI-C-115 | viewport (DISABLED) | disabled-when: always — disabled-reason: "Requires a remote-desktop capability in somaAgent01. Not available today." |
| 3 | UI-C-115 | pointer (DISABLED) | disabled-when: always — disabled-reason: "Requires a remote-desktop capability in somaAgent01. Not available today." |
| 4 | UI-C-115 | keyboard (DISABLED) | disabled-when: always — disabled-reason: "Requires a remote-desktop capability in somaAgent01. Not available today." |
| 5 | UI-C-115 | clipboard (DISABLED) | disabled-when: always — disabled-reason: "Requires a remote-desktop capability in somaAgent01. Not available today." |
| 6 | UI-C-115 | screenshot (DISABLED) | disabled-when: always — disabled-reason: "Requires a remote-desktop capability in somaAgent01. Not available today." |

**State variants.**

- **Loading.** No loading state. A gated control never shows a spinner or progress.
- **Empty.** Not applicable — the surface is gated, not empty. The gate reason is always shown: "Requires a remote-desktop capability in somaAgent01. Not available today."
- **Error.** Not applicable — no request is made from a gated control. The gate reason is always shown: "Requires a remote-desktop capability in somaAgent01. Not available today."
- **Permission-denied.** "Requires a remote-desktop capability in somaAgent01. Not available today."
- **Offline.** "Requires a remote-desktop capability in somaAgent01. Not available today." (the gate is capability-based, not connectivity-based).

**Modal overlays.** None. This surface opens no overlay while gated.
