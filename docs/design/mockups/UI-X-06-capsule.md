# UI-X-06 — Capsule

**Capsule** — Right-rail panel in context — route `right-rail surface [6]` — facet **Surface**.
Chrome abbreviated (UI-S-00). Facet tabs and surface rail are visible.

```
┌─ chrome (abbrev) ──────────────────────┬ RIGHT RAIL · UI-X-06 Capsule                                                                   ┐
│  capsule <capsule.name> v<version>     │ Surface: Capsule                                                                               │
│  <lifecycle>  knobs (IQ <v>)(auto <v>)(│ ┌─ capsule summary ───────────────────────────────────────────────────────┐                    │
│  derived AgentIQ RO: <readouts, greyed>│ │ name <capsule.name>                                                      │                   │
│  facets [Soul][Brain][Hands][Memory][Bo│ │ version <version>   lifecycle <lifecycle>                                │                   │
│  <Cmd-K>                               │ │ parent <version-or->                                                     │                   │
│                                        │ │ checksum <checksum>                                                      │                   │
│  WORKSPACE (abbrev)                    │ └──────────────────────────────────────────────────────────────────────────┘                   │
│  ┌────────────────────────────────┐    │ ┌─ version rail ──────────────────────────────────────────────────────────┐                    │
│  │ screen content in context        │  │ │ v<version>  (current)                                                    │                   │
│  │ (see UI-S-07 chat workspace)     │  │ │ v<version>  [diff to parent]                                             │                   │
│  │ surface rail select: UI-X-06 Capsule│ │ v<version>  [diff to parent]                                             │                   │
│  └────────────────────────────────┘    │ └──────────────────────────────────────────────────────────────────────────┘                   │
│                                        │ ┌─ instances ─────────────────────────────────────────────────────────────┐                    │
│  instance <session_id> <state>         │ │ <session_id> <state> <started>                                           │                   │
│  neuro RO DA <v> 5-HT <v> NE <v> ACh <v│ └──────────────────────────────────────────────────────────────────────────┘                   │
│                                        │ [inspect] [archive]                                                                            │
└────────────────────────────────────────┴────────────────────────────────────────────────────────────────────────────────────────────────┘
```

**Control map.**

| # | UI-C-* | control | notes |
|---|---|---|---|
| 1 | UI-C-113 | capsule summary panel | Name/version/lifecycle/checksum are `‹ live value ›` from the capsule record. Checksum is never invented. |
| 2 | UI-C-118 | version rail with diff-to-parent | Edit always spawns a child version; the rail never shows an in-place mutation. |
| 3 | UI-C-102 | instance row | Real CapsuleInstance rows (session_id, state, started). |
| 4 | UI-C-068 | inspect (secondary) | Opens UI-M-01 drawer with the full capsule record. |
| 5 | UI-C-069 | archive (destructive) | Opens UI-M-03. disabled-when: lifecycle is already archived — disabled-reason: "This capsule version is already archived." |

**State variants.**

- **Loading.** Skeleton rows plus a `loading` chip in the workspace header. No counts, charts or metrics are drawn while loading.
- **Empty.** "No capsule version selected. Pick a version from the rail."
- **Error.** "Couldn't load the capsule. ‹ reason from API ›"
- **Permission-denied.** "You don't have access to this capsule. Ask the owner for read access."
- **Offline.** You're offline. Changes will not be saved until the connection returns.

**Modal overlays.** UI-M-01 Drawer — capsule inspect (full record, lineage). UI-M-03 Dialog — "Archive capsule version <version>?" (destructive).
