# CM-02 — File Manager Control Map

## Document Control

| Field | Value |
|---|---|
| Document Title | Control Map — File Manager (tree / list / preview / upload) |
| Document Identifier | SOMA-UI-CM-02 |
| Version | 1.0.0 |
| Date | 2026-10-13 |
| Status | Draft |
| Author | SomaTech Engineering (soma-ui-engineer) |
| Classification | Internal |
| ISO Reference | ISO 9241-210:2019 |
| Next Review | 2027-01-13 |
| Related | `SOMA-UI-AGENT-FRONTEND-MASTER-001.md` §3.1 · `SOMA-UI-MODULE-CATALOG-001.md` M-024 · `UI-X-01-files.md` · `SOMA-UI-BINDINGS-001.md` §1 right-rail |
| Live sources | `webui/src/components/soma-right-panel.ts` (`_renderFiles`, `_loadFiles`, `_openFileInEditor`) · `webui/src/services/file-upload.ts` |
| Planned module | **M-024 `soma-file-manager`** (+ sub-tags breadcrumb/tree/list/preview/upload-tray/toolbar) |
| Routes | Canvas surface `UI-X-01` (live thin list) · planned first-class `/files` and composer select mode |

## Revision History

| Version | Date | Author | Description |
|---|---|---|---|
| 1.0.0 | 2026-10-13 | soma-ui-engineer | Full File Manager control map: live UI-X-01 list + planned tree/list/preview/upload/manage controls with real target APIs. |

---

## 1. ASCII wireframe — planned File Manager (M-024)

```
┌─ soma-file-manager  mode: browse | select | manage ────────────────────────────────────────────┐
│ FM-00 breadcrumb: workroot / project / docs          FM-01 search    FM-02 [+] new   FM-03 ⟳   │
├──────────────┬─────────────────────────────────────────────────────────────────────────────────┤
│ TREE         │ LIST / DETAIL                                         FM-04 view: detail|compact│
│ FM-10 ▸ root │  FM-20 columns: name | size | modified | actions                              │
│ FM-11   ▸ docs│  FM-21 row: report.md   12 KB  2m   FM-21a ⬇ FM-21b ✎ FM-21c 🗑 FM-21d 👁    │
│ FM-12   ▸ out │  FM-21 row: chart.png   84 KB  5m   …                                          │
│ FM-13   └ src │  FM-22 pagination: showing N of total                                          │
│ FM-14 (skeleton)├──────────────────────────────────────────────────────────────────────────────┤
│              │ PREVIEW (FM-30…)                                                               │
│              │  markdown | code+hljs | image | pdf | binary metadata + download only           │
├──────────────┴────────────────────────────────────────────────────────────────────────────────┤
│ FM-40 [Upload ▾]  FM-41 [New folder]  FM-42 [Refresh]     FM-43 status: 12 files · 2.1 MB     │
│ FM-44 upload tray: per-file progress · cancel · retry · clear                                 │
└───────────────────────────────────────────────────────────────────────────────────────────────┘
```

## 2. ASCII wireframe — live canvas UI-X-01 (today)

```
┌ RIGHT CANVAS · UI-X-01 Files ─────────────────────────────────────────────┐
│ [📁 Files][🔧 Tools][🌐 Browser†][💻 Editor][🐞 Debug][📦 Capsule][🧠 Brain][🖥 Desktop†] │
├──────────────────────────────────────────────────────────────────────────┤
│  X01-01 file rows (FileOut): name · mime · version · size_bytes          │
│  X01-02 row open → UI-X-04 Editor                                        │
│  X01-03 showing N of total (only when total > shown)                     │
│  X01-04 empty-state source note                                          │
│  X01-05 Retry (error state)                                              │
└──────────────────────────────────────────────────────────────────────────┘
† GATED — see CM-06
```

---

## 3. Control map — live UI-X-01 (shipped)

| ID | Label | Type | Binding / API | States | Disabled reason | A11y | Status |
|---|---|---|---|---|---|---|---|
| X01-01 | File row | list-row | `GET /api/v2/filesv2/?page=1&per_page=50` → `FileListResponse` | loading, empty, error, populated | — | `listitem`; fields `original_name \|\| name`, `mime_type` (`—` if missing), `version`, `size_bytes` | LIVE |
| X01-02 | Open file (click / Enter / Space) | list-row action | `GET /filesv2/{id}/download-url` → open in UI-X-04 Editor (RO) | default, busy | — | keyboard operable row | LIVE |
| X01-03 | showing N of total | readout | `total` from `FileListResponse` | only when `total > files.length` | — | text | LIVE |
| X01-04 | Empty-state source note | readout | — | empty | — | explains filesv2-only scope; workroot tools have no list API here | LIVE |
| X01-05 | Retry | button | re-run `GET /filesv2/` | error | — | aria-label “Retry listing files” | LIVE |
| X01-06 | Surface tab Files | tabs | surface registry key `files` | default, active | — | `tab` in `tablist` | LIVE |
| X01-07 | Upload / new folder / delete / rename | — | — | **absent** | Not drawn: no upload/delete on this surface today | — | GATED (absent-by-honesty) |

---

## 4. Control map — planned File Manager (M-024)

Target APIs are real endpoints named in the frontend master / module catalog. Missing endpoints render the control present-but-disabled with the endpoint name — never a fake tree.

| ID | Label | Type | Binding / API | States | Disabled reason | A11y | Status |
|---|---|---|---|---|---|---|---|
| FM-00 | Breadcrumb path | list-row | `GET /api/v2/workroot/tree` (**NEW — required**) path nodes | default, navigating | Tree API not mounted → breadcrumb hidden, list stays filesv2 | `nav` aria-label “Breadcrumb” | PLANNED |
| FM-01 | Search files | input.search | client filter over current dir list (v1); server search when list API grows | idle, results, empty | — | `searchbox` | PLANNED |
| FM-02 | New / upload menu trigger | menu | opens FM-40 upload + FM-41 new folder | closed, open | — | `button` aria-haspopup | PLANNED |
| FM-03 | Refresh | button | re-run list + tree | default, busy | — | `button` aria-label “Refresh” | PLANNED |
| FM-04 | View mode (detail / compact) | select | local layout state | default | — | `radiogroup` | PLANNED |
| FM-10 | Tree root node | list-row | `GET /api/v2/workroot/tree` | expanded, collapsed, loading | Tree API absent → “Workroot tree is not available on this deployment.” | `treeitem` | PLANNED |
| FM-11 | Tree directory node | list-row | same | expanded, collapsed, loading, selected | same | `treeitem` aria-expanded | PLANNED |
| FM-12 | Tree leaf file node | list-row | same | selected | same | `treeitem` | PLANNED |
| FM-13 | Tree expand/collapse | button | local `expandedIds` | default | — | aria-expanded | PLANNED |
| FM-14 | Tree skeleton | readout | — | loading | — | `aria-hidden` | PLANNED |
| FM-15 | Tree error banner | readout | — | partial (list ok, tree failed) | — | `alert` + reason | PLANNED |
| FM-20 | List header sort | button | local `sort` over server rows | default, sorted | — | `columnheader` aria-sort | PLANNED |
| FM-21 | File row | list-row | `GET /api/v2/filesv2/` (list) + workroot list when mounted | default, selected | — | `row` with name/size/modified | PLANNED |
| FM-21a | Download | button | `GET /filesv2/{id}/download-url` → signed GET | default, busy | — | aria-label “Download” | PLANNED |
| FM-21b | Rename | button | target `PATCH /api/v2/filesv2/{id}` / workroot rename (**NEW**) | default, dirty | Rename API absent → disabled: “Rename needs the filesv2/workroot write API.” | aria-label “Rename” | PLANNED |
| FM-21c | Delete | button | target `DELETE /api/v2/filesv2/{id}` (**NEW**) + confirm | default, pending-confirm | Delete API absent → disabled with reason | aria-label “Delete” | PLANNED |
| FM-21d | Preview | button | opens FM-30 pane | default | — | aria-label “Preview” | PLANNED |
| FM-21e | Attach to chat | button | emits `soma-file-select` → composerStore | default, disabled in manage mode | — | `button` | PLANNED |
| FM-21f | Open in editor | button | open UI-X-04 (RO until write API) | default | — | `button` | PLANNED |
| FM-22 | Pagination “showing N of total” | readout | `FileListResponse.total` | only when total > shown | — | text | PLANNED |
| FM-23 | Multi-select checkbox | input.checkbox | `selection: string[]` | default, selected | — | `checkbox` with row name | PLANNED |
| FM-24 | Bulk download | button | sequential signed URLs | default, disabled when selection empty | Empty selection | `button` | PLANNED |
| FM-25 | Bulk delete | button | bulk DELETE (**NEW**) | default, disabled when selection empty | Empty selection; delete API gated | `button` | PLANNED |
| FM-30 | Preview pane | surface | mime policy below | loading, rendered, error | — | `region` “Preview” | PLANNED |
| FM-31 | Preview — markdown | readout | `soma-doc-viewer` over signed body | rendered | — | semantic markdown | PLANNED |
| FM-32 | Preview — code | readout | `soma-code-editor` readonly | rendered | — | `code` with line numbers opt-in | PLANNED |
| FM-33 | Preview — image | readout | `<img>` from authorized URL | loaded, error | — | `img` alt = filename | PLANNED |
| FM-34 | Preview — PDF | readout | iframe from authorized URL | loaded, error | — | titled iframe | PLANNED |
| FM-35 | Preview — binary/unknown | readout | metadata card + Download only | rendered | — | honest metadata only | PLANNED |
| FM-36 | Preview download | button | signed download | default | — | `button` | PLANNED |
| FM-37 | Preview edit request | button | opens editor dirty mode | default | disabled until `PUT /api/v2/filesv2/{id}/content` (**NEW**) exists | disabled + reason “Editor Save needs the filesv2 content write API.” | PLANNED |
| FM-40 | Upload | input.file | `POST /api/v2/filesv2/upload` → presigned `PUT` or `POST /filesv2/upload-local/{file_id}` | idle, uploading, error | — | `button` + file picker | PLANNED |
| FM-41 | New folder | button | target workroot mkdir (**NEW**) | default | Folder API absent → “New folder needs the workroot write API.” | `button` | PLANNED |
| FM-42 | Refresh toolbar | button | list + tree reload | default, busy | — | `button` | PLANNED |
| FM-43 | Status (n files · size) | readout | derived from list only | default | — | text; never invent size totals | PLANNED |
| FM-44 | Upload tray item | list-row | `file-upload.ts` progress events | uploading, complete, failed | — | `listitem` with progressbar | PLANNED |
| FM-44a | Cancel upload | button | abort XHR/PUT | default | — | `button` | PLANNED |
| FM-44b | Retry upload | button | re-POST upload | default | — | `button` | PLANNED |
| FM-44c | Clear tray | button | local | default | — | `button` | PLANNED |
| FM-50 | Mode browse | surface | default | active | — | — | PLANNED |
| FM-51 | Mode select (composer) | surface | emits `soma-file-select` | active | — | — | PLANNED |
| FM-52 | Mode manage | surface | enables rename/delete/new folder | active | — | — | PLANNED |
| FM-53 | PathGuard jail notice | readout | — | always in manage | — | explains workroot jail | PLANNED |
| FM-54 | Partial banner | readout | — | tree failed, list ok | — | `alert` | PLANNED |
| FM-55 | Error + retry | button | reload | error | — | `button` | PLANNED |

---

## 5. Preview mime policy (normative)

| Mime | Preview control | Notes |
|---|---|---|
| `text/*`, `application/json`, source | FM-32 code readonly | no fake IDE chrome |
| `image/*` | FM-33 | authorized URL only |
| `application/pdf` | FM-34 | authorized URL only |
| markdown | FM-31 | `soma-doc-viewer` |
| binary / unknown | FM-35 | metadata + download; never a fake renderer |

---

## 6. Modes and states

| Mode | Enabled controls |
|---|---|
| `browse` | FM-00…FM-36, FM-40, FM-42…FM-44 |
| `select` | browse minus destructive; FM-21e attach primary |
| `manage` | browse + FM-21b/c, FM-23…FM-25, FM-41 |

| State | Verbatim |
|---|---|
| loading | “Loading files…” / tree skeleton |
| empty | “No files in the working set.” + source note |
| error | “Files could not be listed.” + failed request + Retry |
| denied | “You need `files:read` to browse files.” |
| uploading | per-file progress rows |
| partial | list ok + tree failure banner |

---

## 7. Honesty notes

1. No tree is invented when the API returns a flat list.
2. No upload/delete chrome while those endpoints are not wired (live UI-X-01 stays thin).
3. A failed load is an error state — never an empty workspace.
4. `size_bytes` is formatted only for display; the number is the server’s.
5. Editor Save stays disabled until `PUT /api/v2/filesv2/{id}/content` exists (real gate, not a stub handler).

---

## 8. Source map

| Source | Role |
|---|---|
| `webui/src/components/soma-right-panel.ts` | Live UI-X-01 list, open, retry |
| `webui/src/services/file-upload.ts` | Upload pipeline for composer + planned tray |
| `SOMA-UI-MODULE-CATALOG-001.md` M-024 | Planned module contract |
| `SOMA-UI-AGENT-FRONTEND-MASTER-001.md` §3.1 | Wireframe + binding table |
| `docs/design/mockups/UI-X-01-files.md` | Live surface mockup |

End of Document
