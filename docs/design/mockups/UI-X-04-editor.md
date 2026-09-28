# UI-X-04 — Editor

**Editor** — Right-rail panel in context — route `right-rail surface [4]` — facet **Surface**.
Chrome abbreviated (UI-S-00). Facet tabs and surface rail are visible.

```
┌─ chrome (abbrev) ──────────────────────┬ RIGHT RAIL · UI-X-04 Editor                                                                    ┐
│  capsule <capsule.name> v<version>     │ Surface: Editor          <file.name>  [save] [discard]                                         │
│  <lifecycle>  knobs (IQ <v>)(auto <v>)(│ ┌─ tabs ──────────────────────────────────────────────────────────────────┐                    │
│  derived AgentIQ RO: <readouts, greyed>│ │ <file.name>* │ <file.name> │                                            │                    │
│  facets [Soul][Brain][Hands][Memory][Bo│ └──────────────────────────────────────────────────────────────────────────┘                   │
│  <Cmd-K>                               │ ┌─ buffer ────────────────────────────────────────────────────────────────┐                    │
│                                        │ │ 1 │ <buffer line>                                                        │                   │
│  WORKSPACE (abbrev)                    │ │ 2 │ <buffer line>                                                        │                   │
│  ┌────────────────────────────────┐    │ │ 3 │ <buffer line>                                                        │                   │
│  │ screen content in context        │  │ │ 4 │ <buffer line>                                                        │                   │
│  │ (see UI-S-07 chat workspace)     │  │ │ 5 │ <buffer line>                                                        │                   │
│  │ surface rail select: UI-X-04 Editor │ └──────────────────────────────────────────────────────────────────────────┘                   │
│  └────────────────────────────────┘    │ dirty: yes/no   encoding <enc>   lang <lang>                                                   │
│                                        │ * marks an unsaved buffer. Save writes through the real                                        │
│  instance <session_id> <state>         │ FS API. Nothing is persisted in the UI alone.                                                  │
│  neuro RO DA <v> 5-HT <v> NE <v> ACh <v│                                                                                                │
└────────────────────────────────────────┴────────────────────────────────────────────────────────────────────────────────────────────────┘
```

**Control map.**

| # | UI-C-* | control | notes |
|---|---|---|---|
| 1 | UI-C-110 | code editor buffer | Buffer content is the real file. Dirty state is tracked from edits, never assumed. |
| 2 | UI-C-072 | file tab strip | Tabs for open files. `*` marks unsaved. |
| 3 | UI-C-067 | save (primary) | Writes through the FS API. disabled-when: buffer is not dirty — disabled-reason: "No unsaved changes." |
| 4 | UI-C-069 | discard (destructive) | Opens UI-M-03. disabled-when: buffer is not dirty — disabled-reason: "No unsaved changes." |
| 5 | UI-C-073 | dirty / encoding / lang readout | Read-only status line. |

**State variants.**

- **Loading.** Skeleton rows plus a `loading` chip in the workspace header. No counts, charts or metrics are drawn while loading.
- **Empty.** "No file open. Open a file from the Files surface."
- **Error.** "Couldn't load the file. ‹ reason from API ›"
- **Permission-denied.** "You don't have access to edit this file. Ask the capsule owner for write access."
- **Offline.** You're offline. Changes will not be saved until the connection returns.

**Modal overlays.** UI-M-03 Dialog — "Discard unsaved changes to <file.name>?" (destructive).
