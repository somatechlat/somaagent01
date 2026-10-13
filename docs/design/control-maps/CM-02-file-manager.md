# CM-02 — File Manager Control Map

## Document Control

| Field | Value |
|---|---|
| Document Title | Control Map — File Manager (tree / list / preview / upload) |
| Document Identifier | SOMA-UI-CM-02 |
| Version | 1.1.0 |
| Date | 2026-10-13 |
| Status | Draft |
| Author | SomaTech Engineering (soma-ui-engineer) |
| Classification | Internal |
| ISO Reference | ISO 9241-210:2019 |
| Next Review | 2027-01-13 |
| Related | `SOMA-UI-AGENT-FRONTEND-MASTER-001.md` §3.1 · `SOMA-UI-MODULE-CATALOG-001.md` M-024 · `UI-X-01-files.md` · `SOMA-UI-BINDINGS-001.md` §1 right-rail |
| Live sources | `webui/src/components/soma-file-manager.ts` (M-024) · `webui/src/components/soma-right-panel.ts` (`_renderFiles`, `_loadFiles`, `_openFileInEditor`) · `webui/src/services/file-upload.ts` · `webui/src/utils/file-icons.ts` |
| Planned module | **M-024 `soma-file-manager`** (+ sub-tags breadcrumb/tree/list/preview/upload-tray/toolbar) — **partially LIVE** (list/upload/delete/rename-gate/move-gate/tree-chrome) |
| Routes | Canvas surface `UI-X-01` (live thin list) · planned first-class `/files` and composer select mode |

## Revision History

| Version | Date | Author | Description |
|---|---|---|---|
| 1.0.0 | 2026-10-13 | soma-ui-engineer | Full File Manager control map: live UI-X-01 list + planned tree/list/preview/upload/manage controls with real target APIs. |
| 1.1.0 | 2026-10-13 | soma-ui-engineer | As-built M-024 polish: standardized workroot/inbox tree chrome (honest gate), file-type Material icons in list, move/rename/delete/new-folder UX with named-API gates, upload tray, no emojis. |
| 1.2.0 | 2026-10-14 | soma-ui-engineer | As-built repair: list pages through GET /filesv2/ until `total`; preview + download primary body is GET /filesv2/{id}/content (local stream) with signed download-url fallback; modal drop zone calls `uploadFiles`; `bootstrap_identity --roles` so a provisioned principal can resolve `resource:file_*`. |
| 1.3.0 | 2026-10-14 | soma-ui-engineer | Honesty repair: search-no-match is not an empty workspace (Clear search); download/upload/delete failures pushToast (never silent); delete 403 names `resource:file_delete`; duplicate i18n keys removed. Live curl list+upload+content + Playwright files-modal 2/2 on :20080. |

---

## 1. ASCII wireframe — planned File Manager (M-024)

```
┌─ soma-file-manager  mode: browse | select | manage ────────────────────────────────────────────┐
│ FM-00 breadcrumb: workroot / inbox                 FM-01 search    FM-02 Upload   FM-03 Refresh│
├──────────────┬─────────────────────────────────────────────────────────────────────────────────┤
│ TREE         │ LIST / DETAIL                                                                  │
│ FM-10 [folder] workroot │  FM-20 columns: icon | name | size | modified | actions             │
│ FM-11 [inbox]  inbox    │  FM-21 row: [icon] report.md   12 KB  2m   FM-21a..g                 │
│ FM-14 (gate note)       │  FM-22 pagination: showing N of total                               │
│              ├──────────────────────────────────────────────────────────────────────────────┤
│              │ PREVIEW (FM-30…)                                                               │
│              │  markdown | code | image | pdf | binary metadata + download only                │
├──────────────┴────────────────────────────────────────────────────────────────────────────────┤
│ FM-40 [Upload]  FM-41 [New folder]  FM-42 [Refresh]     FM-43 status: 12 files · 2.1 MB        │
│ FM-44 upload tray: per-file state · clear                                                     │
└───────────────────────────────────────────────────────────────────────────────────────────────┘
LAW: icons = Material Symbols only. No emojis in trees, chips, or labels.
```

## 2. ASCII wireframe — live canvas UI-X-01 (today)

```
┌ RIGHT CANVAS · UI-X-01 Files ─────────────────────────────────────────────┐
│ [Files][Tools][Browser†][Editor][Debug][Agent][Brain][Desktop†]  (Material icons in chrome) │
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
| FM-00 | Breadcrumb path | list-row | `GET /api/v2/workroot/tree` (**NEW — required**) path nodes | default, navigating | Tree API not mounted → breadcrumb hidden, list stays filesv2 | `nav` aria-label “Breadcrumb” | GATED (honest-hide) |
| FM-01 | Search files | input.search | client filter over current dir list (v1); server search when list API grows | idle, results, empty | — | `searchbox` aria-label “Search files” | LIVE |
| FM-02 | Upload trigger | button | opens FM-40 file picker | closed, open | — | `button` aria-label “Upload files” | LIVE |
| FM-03 | Refresh | button | re-run list + tree probe | default, busy | — | `button` aria-label “Refresh” | LIVE |
| FM-04 | View mode (detail / compact) | select | local layout state | default | — | `radiogroup` | PLANNED |
| FM-10 | Tree root `workroot` | treeitem | local path chrome (standard location) | default, selected | — | `treeitem` in `tree` “Workroot tree” | LIVE (chrome) |
| FM-11 | Tree child `inbox` | treeitem | local path chrome (standard location) | default, selected | — | `treeitem` | LIVE (chrome) |
| FM-12 | Tree leaf file node | treeitem | `GET /api/v2/workroot/tree` children | selected | Typed tree API/schema absent → children not drawn (never invented) | `treeitem` | GATED |
| FM-13 | Tree expand/collapse | button | local `expandedIds` | default | children require typed tree API | aria-expanded | GATED |
| FM-14 | Tree gate note | readout | probe result of `GET /api/v2/workroot/tree` | gate, partial | — | `status` with reason | LIVE |
| FM-15 | Tree error banner | readout | — | partial (list ok, tree failed) | — | `alert` + reason | PLANNED |
| FM-20 | List header sort | button | local `sort` over server rows | default, sorted | — | `columnheader` aria-sort | PLANNED |
| FM-21 | File row | list-row | `GET /api/v2/filesv2/` pages until `total` (list) + workroot list when mounted | default, selected | — | `listitem` with Material file-type icon (`attachmentIcon`) · name · mime · version · size · modified | LIVE |
| FM-21a | Download | button | `GET /filesv2/{id}/content` blob (local stream) → fallback `GET /filesv2/{id}/download-url` | default, busy | — | aria-label “Download” | LIVE |
| FM-21b | Rename | button | target `PATCH /api/v2/filesv2/{id}` | default, dirty | manage mode only; PATCH not mounted → modal shows “Rename needs the filesv2 write API (PATCH /api/v2/filesv2/{id}).” | aria-label “Rename” | GATED (modal + reason) |
| FM-21c | Delete | button | `DELETE /api/v2/filesv2/{id}` (soft delete) + confirm modal | default, pending-confirm | manage mode only; outside manage → “Switch to manage mode to delete” | aria-label “Delete” | LIVE |
| FM-21d | Preview | button | opens FM-30 pane (`soma-file-preview`) | default | — | aria-label “Preview” | LIVE |
| FM-21e | Attach to chat | button | emits `soma-file-select` → composerStore | default, select mode only | — | `button` aria-label “Attach to chat” | LIVE |
| FM-21f | Open in editor | button | open UI-X-04 (RO until write API) | default | — | `button` | LIVE (RO) |
| FM-21g | Move | button | target `POST /api/v2/workroot/move` (**NEW**) | default, dirty | manage mode only; move API absent → modal shows “Move needs the workroot write API (POST /api/v2/workroot/move).” | aria-label “Move” | GATED (modal + reason) |
| FM-22 | Pagination “showing N of total” | readout | `FileListResponse.total` | only when total > shown | — | text | PLANNED |
| FM-23 | Multi-select checkbox | input.checkbox | `selection: string[]` | default, selected | — | `checkbox` with row name | PLANNED |
| FM-24 | Bulk download | button | sequential signed URLs | default, disabled when selection empty | Empty selection | `button` | PLANNED |
| FM-25 | Bulk delete | button | bulk DELETE (**NEW**) | default, disabled when selection empty | Empty selection; delete API gated | `button` | PLANNED |
| FM-30 | Preview pane | surface | mime policy below; body = `GET /filesv2/{id}/content` | loading, rendered, error | — | `region` “Preview” | LIVE |
| FM-31 | Preview — markdown | readout | rendered body from content stream | rendered | — | semantic markdown | LIVE |
| FM-32 | Preview — code | readout | content stream readonly text | rendered | — | `code` with line numbers opt-in | LIVE |
| FM-33 | Preview — image | readout | content-stream blob URL (authorized bytes) | loaded, error | — | `img` alt = filename | LIVE |
| FM-34 | Preview — PDF | readout | content-stream blob URL | loaded, error | — | titled iframe | LIVE |
| FM-35 | Preview — binary/unknown | readout | metadata card + Download only | rendered | — | honest metadata only | LIVE |
| FM-36 | Preview download | button | content stream → signed download fallback | default | — | `button` | LIVE |
| FM-37 | Preview edit request | button | opens editor dirty mode | default | disabled until `PUT /api/v2/filesv2/{id}/content` (**NEW**) exists | disabled + reason “Editor Save needs the filesv2 content write API.” | PLANNED |
| FM-40 | Upload | input.file | `POST /api/v2/filesv2/upload` → presigned `PUT` or `POST /filesv2/upload-local/{file_id}` | idle, uploading, complete, failed | — | `button` + file picker | LIVE |
| FM-41 | New folder | button | target `POST /api/v2/workroot/mkdir` (**NEW**) | default | Folder API absent → disabled: “New folder needs the workroot write API (POST /api/v2/workroot/mkdir).” | `button` aria-disabled | GATED |
| FM-42 | Refresh toolbar | button | list + tree reload | default, busy | — | `button` aria-label “Refresh” | LIVE |
| FM-43 | Status (n files · size) | readout | derived from list only | default | — | text; never invent size totals | LIVE |
| FM-44 | Upload tray item | list-row | `file-upload.ts` progress events | uploading, complete, failed | — | `listitem` with state text + bar | LIVE |
| FM-44a | Cancel upload | button | abort XHR/PUT | default | — | `button` | PLANNED |
| FM-44b | Retry upload | button | re-POST upload | default | — | `button` | PLANNED |
| FM-44c | Clear tray | button | local `_uploads = []` | default | — | `button` aria-label “Clear upload tray” | LIVE |
| FM-50 | Mode browse | surface | default | active | — | `region` | LIVE |
| FM-51 | Mode select (composer) | surface | emits `soma-file-select` | active | — | `region` | LIVE |
| FM-52 | Mode manage | surface | enables rename/delete/move; new folder still gated | active | — | `region` | LIVE |
| FM-53 | PathGuard jail notice | readout | — | always in manage | — | explains workroot jail | PLANNED |
| FM-54 | Partial banner | readout | — | tree failed, list ok | — | `alert` | PLANNED |
| FM-55 | Error + retry | button | reload list | error | — | `button` aria-label “Retry listing files” | LIVE |

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
4. A filtered-empty list is **not** an empty workspace: “No files match your search.” + Clear search. Only a truly empty loaded set says “No files in the working set.”
5. `size_bytes` is formatted only for display; the number is the server’s.
6. Editor Save stays disabled until `PUT /api/v2/filesv2/{id}/content` exists (real gate, not a stub handler).
7. **No emojis in the File Manager** — tree nodes, row actions, chips, and labels use Material Symbols only (`folder`, `inbox`, `download`, `visibility`, `edit`, `drive_file_move`, `delete`, `attach_file`, `create_new_folder`, `upload`, `refresh`).
8. File-type glyphs come from `utils/file-icons.ts` `attachmentIcon(name, type)` — shared with composer chips and message attachment cards.
9. Move/rename/new-folder keep their named missing-API reasons visible in the modal or `title` — never a silent no-op.
10. Standard tree chrome is `workroot` + `inbox` only. Child nodes are not invented when the typed tree API is absent.
11. Operation failures (download, upload, delete) always surface — tray row and/or `pushToast` — never a silent no-op. Delete 403 names `resource:file_delete`.

---

## 8. Source map

| Source | Role |
|---|---|
| `webui/src/components/soma-file-manager.ts` | M-024 File Manager (list/upload/tree-chrome/rename/delete/move gates) |
| `webui/src/utils/file-icons.ts` | Material file-type icon map (no emojis) |
| `webui/src/components/soma-right-panel.ts` | Live UI-X-01 list, open, retry |
| `webui/src/services/file-upload.ts` | Upload pipeline for composer + planned tray |
| `SOMA-UI-MODULE-CATALOG-001.md` M-024 | Planned module contract |
| `SOMA-UI-AGENT-FRONTEND-MASTER-001.md` §3.1 | Wireframe + binding table |
| `docs/design/mockups/UI-X-01-files.md` | Live surface mockup |

End of Document
