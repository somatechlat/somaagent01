# UI-X-01 — Files

**Files** — Right-rail panel in context — route `right-rail surface [1]` — facet **Surface**.
Chrome abbreviated (UI-S-00). Facet tabs and surface rail are visible.

```
┌─ chrome (abbrev) ──────────────────────┬ RIGHT RAIL · UI-X-01 Files                                                                     ┐
│  capsule <capsule.name> v<version>     │ Surface: Files                       [upload] [new folder]                                     │
│  <lifecycle>  knobs (IQ <v>)(auto <v>)(│ ┌─ path bar ──────────────────────────────────────────────────────────────┐                    │
│  derived AgentIQ RO: <readouts, greyed>│ │ <path/breadcrumb>                                                        │                   │
│  facets [Soul][Brain][Hands][Memory][Bo│ └──────────────────────────────────────────────────────────────────────────┘                   │
│  <Cmd-K>                               │ ┌─ tree ────────────────────────┬─ preview ───────────────────────────────┐                    │
│                                        │ │ v <dir>                        │ <file.name>                              │                  │
│  WORKSPACE (abbrev)                    │ │   <file>  <size>               │ <mime> <size>                            │                  │
│  ┌────────────────────────────────┐    │ │   <file>  <size>               │ ┌────────────────────────────────────┐   │                  │
│  │ screen content in context        │  │ │   v <dir>                      │ │ preview body (text / image)         │   │                 │
│  │ (see UI-S-07 chat workspace)     │  │ │     <file>  <size>             │ │ <content or the reason it cannot>   │   │                 │
│  │ surface rail select: UI-X-01 Files  │ │   <dir>                        │ └────────────────────────────────────┘   │                  │
│  └────────────────────────────────┘    │ └────────────────────────────────┴──────────────────────────────────────────┘                  │
│                                        │ [rename] [download] [delete]  search [__________]                                              │
│  instance <session_id> <state>         │                                                                                                │
│  neuro RO DA <v> 5-HT <v> NE <v> ACh <v│                                                                                                │
└────────────────────────────────────────┴────────────────────────────────────────────────────────────────────────────────────────────────┘
```

**Control map.**

| # | UI-C-* | control | notes |
|---|---|---|---|
| 1 | UI-C-105 | file tree | Real tree from the workspace FS API. Nodes are `‹ live value ›`; no folder structure is invented. |
| 2 | UI-C-106 | path / breadcrumb bar | Shows the real current path. |
| 3 | UI-C-107 | preview pane | Text/image preview when the mime is supported. Otherwise the pane states why it cannot preview. |
| 4 | UI-C-077 | upload (file picker) | disabled-while: upload in flight. |
| 5 | UI-C-069 | delete (destructive) | Opens UI-M-03. disabled-when: selection is read-only — disabled-reason: "This path is read-only." |
| 6 | UI-C-070 | search input | Searches the real tree. No results are fabricated. |

**State variants.**

- **Loading.** Skeleton rows plus a `loading` chip in the workspace header. No counts, charts or metrics are drawn while loading.
- **Empty.** "No files here yet. Upload a file or create a folder."
- **Error.** "Couldn't load files. ‹ reason from API ›"
- **Permission-denied.** "You don't have access to these files. Ask the capsule owner for read access."
- **Offline.** You're offline. Changes will not be saved until the connection returns.

**Modal overlays.** UI-M-02 Full-screen — file preview focus (explicit dismiss only). UI-M-03 Dialog — "Delete <file.name>?" (destructive).
