# SOMA-UI-CONTROL-MAPS-001 — Control Maps and Build Plan

## Document Control

| Field | Value |
|---|---|
| Document Title | Control Maps and Build Plan |
| Document Identifier | SOMA-UI-CONTROL-MAPS-001 |
| Version | 1.1.1 |
| Date | 2026-10-13 |
| Status | Draft |
| Author | SomaTech Engineering |
| Approver | — |
| Classification | Internal |
| ISO Reference | ISO 9241-210:2019 · ISO 9001:2015 clause 7.5 |
| Next Review | 2027-01-13 |
| Related | `SOMA-UI-AGENT-FRONTEND-MASTER-001.md`, `SOMA-UI-MODULE-CATALOG-001.md`, `SOMA-01-UIUX-005.md`, `SOMA-UI-IDREG-001.md`, `SOMA-UI-TEMPLATE-001.md`, `SOMA-UI-BINDINGS-001.md`, `SOMA-UI-MOCKUPS-001.md`, `docs/design/mockups/UI-X-01-files.md`, `docs/design/mockups/UI-S-04-memory.md`, `docs/design/mockups/UI-S-56-settings-somabrain.md` |
| Source of truth | Live `webui/src/` tree for LIVE marks · `SOMA-UI-AGENT-FRONTEND-MASTER-001.md` §3 for PLANNED module design · named REST/WS paths only |
| Audience | UI/UX contributors, product engineering, any agent acting on somaAgent01 |
| Scope | File Manager · Memory Manager · SomaBrain Manager · Command Palette · Chat upgrades · Settings knobs. Design and control specification only. |
| Law | NO MOCKS. NO FAKES. NO STUBS. GATED = present-but-disabled + blocking reason. Every control binds to a real API/WS or states why it cannot. |

## Revision History

| Version | Date | Author | Description |
|---|---|---|---|
| 1.0.0 | 2026-10-13 | SomaTech Engineering | Initial issue. Control maps for File Manager, Memory Manager, SomaBrain Manager, Command Palette, Chat, Settings, Skins, Canvas. |
| 1.0.1 | 2026-10-13 | soma-ui-engineer | Placement delta (see `SOMA-UI-DUP-AUDIT-001.md` §5): §3 must split UI-X-07 live Brain vs Settings›SomaBrain config; IQ knobs leave §3; SB-C04 replaces `Open /cognitive`. Authority = IA-001. |
| 1.1.0 | 2026-10-13 | SomaTech Engineering | ISO Document Control completed (Status enum, Audience, Scope, Normative References). Every control table carries ID, label, type, API, states, disabled-when, disabled-reason, status. Live/PLANNED marks re-derived from `webui/src` and `UI-X-01` / `UI-S-04` / `UI-S-56` source maps. Disagreement register added. Build plan exits made testable. |

## Normative References

| ID | Reference | Role |
|---|---|---|
| N-1 | `SOMA-UI-TEMPLATE-001.md` | House ISO template, honesty rules, per-screen block shape |
| N-2 | `SOMA-01-DOCS-001.md` | Document control and traceability procedure |
| N-3 | `SOMA-A0-PARITY-001.md` | Honesty rules; disabled-with-reason |
| N-4 | `SOMA-UI-IDREG-001.md` | Authoritative screen/surface ID allocation |
| N-5 | `SOMA-UI-AGENT-FRONTEND-MASTER-001.md` | Module design targets, build order, gap rationale |
| N-6 | `SOMA-UI-MODULE-CATALOG-001.md` | M-001…M-053 module contracts, states, skin surfaces |
| N-7 | `SOMA-01-UIUX-005.md` | Settings placement matrix, secrets rule, honesty notes H-01…H-08 |
| N-8 | `SOMA-UI-BINDINGS-001.md` | Click-path map: mock control → live API/WS |
| N-9 | `docs/design/mockups/UI-X-01-files.md` | LIVE Files surface truth (what is actually drawn today) |
| N-10 | `docs/design/mockups/UI-S-04-memory.md` | Memory one-home law and control map |
| N-11 | `docs/design/mockups/UI-S-56-settings-somabrain.md` | SomaBrain settings field truth |
| N-12 | `admin/core/agentiq/settings.py`, `admin/core/agentiq/derivation.py` | 3 knobs → 12 derived readouts (never editable) |

---

## 1. Purpose and Scope

### 1.1 Purpose

This document is the **control-map specification** for the six product surfaces named in the operator brief:

1. File Manager (M-024 / UI-X-01 v2)
2. Memory Manager (UI-S-04)
3. SomaBrain Manager (UI-S-56 + UI-X-07 + AgentIQ)
4. Command Palette (M-021)
5. Chat upgrades (UI-S-07 P0/P1)
6. Settings knobs (UI-S-50…57)

For **every button and field** it records: identifier, label, control type, API/WS binding, render states, disabled-when, disabled-reason, and delivery status (`LIVE` / `PLANNED` / `GATED`). ASCII wireframes fix the region layout. A build plan converts the maps into ordered, testable delivery phases.

This is a **design and specification document**. It contains no product code, no mocks, and no fabricated API shapes.

### 1.2 In Scope

- Control enumeration for the six surfaces above (primary chrome + empty/error/gated states).
- ASCII wireframes for each surface.
- API/WS binding names taken from live code or from the master design's required new endpoints.
- Build plan with phase exits and acceptance.
- Disagreement register where live code and design docs name different paths.

### 1.3 Out of Scope

- Product implementation (Lit components, Django routes, tests).
- Mock data, demo fallbacks, placeholder rows.
- Secret values (N-7 §10; secrets render as presence-only).
- Platform/admin screens outside the six surfaces (those live in UI-S-* mockups).
- Backend service design beyond the named API contracts the UI requires.

### 1.4 How to read the control tables

| Column | Meaning |
|---|---|
| ID | Stable control identifier (`FM-*`, `MM-*`, `SB-*`, `CP-*`, `CH-*`, `ST-*`). Not renumbered once issued. |
| Label | User-visible label (or structural role when unlabeled). |
| Type | Control primitive from N-6 L0 (`button`, `input:text`, `select`, `toggle`, `stat`, …). |
| API | Exact REST/WS path or `local` / `—` when there is no I/O. Required-new endpoints are marked **NEW API**. |
| States | Render states the control MUST implement. |
| disabled-when | Condition that disables the control. `—` = never disabled by design. |
| disabled-reason | Verbatim blocking reason shown when disabled. `—` = not applicable. A disabled control with an empty reason is a compliance failure (N-1 §4). |
| Status | `LIVE` = present in `webui/src` with a real handler · `PLANNED` = target API named, ships with code + tests · `GATED` = present-or-required-but-disabled with reason. |

### 1.5 Status legend

| Mark | Meaning | Allowed without a reason? |
|---|---|---|
| **LIVE** | In `webui/src` today with a real handler bound to a real API/WS. | n/a |
| **PLANNED** | Designed here; target API named; ships with code + tests after operator GO. | disabled-reason required if the control is drawn early |
| **GATED** | Present-but-disabled. Blocking reason is part of the control. | **No — reason is mandatory** |

**Honesty rules (binding, from N-1 §4 / N-3 / N-7 H-01…H-08):**

- NEVER write "coming soon" as a specification value or a disabled-reason.
- NEVER invent metrics, counts, API shapes, or demo fallback rows.
- Empty ≠ error. A failed load is the error state, not "0".
- Counts with no count API render `—`, never `0`, never a guess.
- Derived AgentIQ values are read-only readouts beside their knobs. Never editors.
- Secrets render as presence + "rotate in Vault". Never a value, never a fabricated fragment.

---

## 2. Control Identifier Register

Control IDs in this document use a per-surface prefix. They are **not** the `UI-C-*` range of N-4, which is already contested (defect M-01 in `SOMA-UI-MOCKUPS-001.md`: two batches allocated overlapping `UI-C-*` numbers). A future IDREG revision SHALL either absorb these IDs or publish a single global table; until then this document is the authority for `FM-*` / `MM-*` / `SB-*` / `CP-*` / `CH-*` / `ST-*`.

| Prefix | Surface | Screen / module | Count (this doc) |
|---|---|---|---|
| FM-* | File Manager | M-024 · UI-X-01 v2 | FM-01…FM-28 |
| MM-* | Memory Manager | UI-S-04 | MM-01…MM-26 |
| SB-* | SomaBrain Manager | UI-S-56 · UI-X-07 · AgentIQ | SB-01…SB-30 |
| CP-* | Command Palette | M-021 | CP-01…CP-14 |
| CH-* | Chat upgrades | UI-S-07 | CH-01…CH-34 |
| ST-* | Settings knobs | UI-S-50…57 | ST-01…ST-40 |

Screen and surface identifiers stay those of N-4 (`UI-S-*`, `UI-X-*`, `UI-M-*`). This document does not allocate new screen IDs.

---

## 3. FILE MANAGER (UI-X-01 v2 · M-024)

**Module:** M-024 `soma-file-manager` (N-6) · **Surface:** UI-X-01 right canvas · optional full route `/files`  
**Modes:** `browse` · `select` (composer attach) · `manage`  
**Skin surface:** `right_panel`  
**API legend:**

| Binding | Status |
|---|---|
| `GET /api/v2/filesv2/` (`FileListResponse`) | LIVE |
| `POST /api/v2/filesv2/upload` → presign / `upload-local/{file_id}` | LIVE (service; FM toolbar exposure PLANNED) |
| Authorized download URL (`GET …/download-url` pattern in `soma-right-panel.ts`) | LIVE |
| `GET /api/v2/workroot/tree` | **NEW API — required** (PathGuard jail) |
| `PUT /api/v2/filesv2/{id}/content` | **NEW API — required** (unlocks editor Save) |
| `POST /api/v2/workroot/mkdir` | **NEW API — required** |
| `DELETE /api/v2/filesv2/{id}` | **NEW API — required** (destructive; confirm UI-M-03) |

**Live truth today (N-9):** UI-X-01 draws a **flat filesv2 list** + open + download + retry + empty source note. It draws **no tree, no upload chrome, no delete/rename chrome**. The File Manager below is the M-024 target; rows marked LIVE are already real in the thin surface or in shared services.

### 3.1 Wireframe — File Manager docked in canvas

```
┌─ UI-S-00 chrome (abbrev) ────────────────┬─ RIGHT CANVAS · UI-X-01 Files (M-024) ──────────────┐
│  chat workspace (UI-S-07)                │ [📁 Files][🔧 Tools][🌐 Browser†][💻 Editor]        │
│                                          │ [🐞 Debug][📦 Capsule][🧠 Brain][🖥 Desktop†]        │
│                                          ├────────────────────────────────────────────────────┤
│                                          │  📁 Files              [🔍 Search files…] [↑][⋮]   │
│                                          │  workroot / docs / reports /                        │
│                                          ├──────────────┬─────────────────────────────────────┤
│                                          │ TREE (30%)   │ LIST / PREVIEW (70%)                │
│                                          │ ▾ workroot   │ Name         Size    Mod.  Actions   │
│                                          │   ▾ docs     │ 📄 brief.md  4 KB   2m    ⬇ ✎ 🗑     │
│                                          │     ▾ reports│ 📊 q3.xlsx   82 KB  1h    ⬇ 👁 🗑     │
│                                          │       q3.md  │ 🖼 chart.png  1.2 MB 1d    ⬇ 👁 🗑    │
│                                          │     notes.txt│ ─────────────────────────────────     │
│                                          │   ▾ out      │ PREVIEW (mime policy)               │
│                                          │ ▾ filesv2    │ ┌─────────────────────────────────┐ │
│                                          │   upload.bin │ │ markdown | code+hl | image |    │ │
│                                          │              │ │ pdf iframe | binary metadata    │ │
│                                          │ [+ New folder│ └─────────────────────────────────┘ │
│                                          ├──────────────┴─────────────────────────────────────┤
│                                          │ [Upload ▾] [New folder] [Refresh]                   │
│                                          │ Selected: q3.md · 4 KB · text/markdown              │
│                                          │ [Download] [Open in Editor] [Attach to chat]        │
│                                          │ status: 12 files · 2.1 MB · showing 12 of 12        │
└──────────────────────────────────────────┴────────────────────────────────────────────────────┘
† GATED surfaces stay on the rail with their reason (UI-X-03 / UI-X-08).
```

### 3.2 Control map — every button and field

| ID | Label | Type | API | States | disabled-when | disabled-reason | Status |
|---|---|---|---|---|---|---|---|
| FM-01 | Files (title) | label | — | always | — | — | LIVE |
| FM-02 | Search files | input:search | client filter over loaded rows; server search **NEW API** `GET /api/v2/workroot/search` | idle · typing · results · empty | — | — | PLANNED (client filter may ship first) |
| FM-03 | Upload menu ▾ | button:menu | opens FM-04 / FM-05 | closed · open | `files:write` denied | Requires `files:write` permission. | PLANNED (API LIVE via composer) |
| FM-04 | Upload files… | menu-item | `POST /api/v2/filesv2/upload` | idle · uploading % · error · done | upload transport missing | File upload endpoint is not available on this deployment. | PLANNED |
| FM-05 | Upload folder… | menu-item | **NEW API** `POST /api/v2/filesv2/upload` (multi) | idle · uploading | folder upload not enabled | Folder upload is not enabled on this deployment. | GATED |
| FM-06 | Overflow ⋮ | button:menu | menu FM-07…FM-09 | closed · open | — | — | PLANNED |
| FM-07 | Refresh | menu-item | re-run `GET /api/v2/filesv2/` (+ tree when present) | idle · loading · error | — | — | PLANNED (list refresh exists as action) |
| FM-08 | New folder | menu-item | **NEW API** `POST /api/v2/workroot/mkdir` | idle · busy · error | workroot API absent | Workroot directory API is not available. Cannot create folders. | GATED |
| FM-09 | Select mode | menu-item | sets `mode=select` (composer) | off · on | — | — | PLANNED |
| FM-10 | Breadcrumb segment | link | sets controlled `path` | default · hover · active | — | — | PLANNED |
| FM-11 | Breadcrumb root label | label | rootId label | always | — | — | PLANNED |
| FM-12 | Tree expand/collapse | button:icon | local `expandedIds` | collapsed · expanded · loading | tree API absent | Workroot tree API is not available. | GATED |
| FM-13 | Tree node | button | select path → list | default · selected · loading | tree API absent | Workroot tree API is not available. | GATED |
| FM-14 | File row | row | select / open | default · hover · selected · focused | — | — | LIVE |
| FM-15 | Row name cell | text | `FileOut.original_name \|\| name` | always | — | — | LIVE |
| FM-16 | Row meta cell | text | `mime_type` · `version` · `size_bytes` | value · `—` when missing | — | — | LIVE |
| FM-17 | Download ⬇ | button:icon | authorized download URL → bytes | idle · busy · error | no file selected | Select a file to download. | LIVE |
| FM-18 | Preview 👁 | button:icon | open preview pane (FM-22) | idle · busy | mime unsupported | Preview is not available for this file type. Download it instead. | PLANNED (open-in-editor LIVE) |
| FM-19 | Edit ✎ | button:icon | open UI-X-04 editor | RO · dirty · save-error | write API absent | Editor Save is disabled until the file write API exists. | LIVE RO / GATED write |
| FM-20 | Delete 🗑 | button:icon | **NEW API** `DELETE /api/v2/filesv2/{id}` | confirm · busy · error | write API absent or `files:write` denied | Delete requires the file write API and `files:write` permission. | GATED |
| FM-21 | Rename | menu-item | **NEW API** `PATCH /api/v2/filesv2/{id}` | idle · busy · error | write API absent | Rename requires the file write API. | GATED |
| FM-22 | Preview body | pane | mime policy (N-6 M-024) | loading · rendered · empty · unsupported | — | — | PLANNED |
| FM-23 | Preview toolbar: Download | button | same as FM-17 | idle · busy | no file selected | Select a file to download. | PLANNED |
| FM-24 | Preview toolbar: Open in Editor | button | UI-X-04 | busy | no file selected | Select a file to open. | LIVE |
| FM-25 | Footer: Attach to chat | button | `soma-file-select` → composer | idle · busy | mode ≠ select or no selection | Select one or more files to attach. | PLANNED |
| FM-26 | Footer: Download selected | button | same as FM-17 (batch) | idle · busy | empty selection | Select a file to download. | PLANNED |
| FM-27 | Status: file count · size | text | `FileListResponse.total` + client sum | value · `—` | — | — | LIVE (count of shown; total when provided) |
| FM-28 | Status: showing N of total | text | `total` vs `files.length` | hidden when total ≤ shown | — | — | LIVE |
| FM-29 | Empty state | empty-state | — | "No files in the working set." + source note | — | — | LIVE |
| FM-30 | Error state + Retry | error-state | re-fetch | error · retrying | — | — | LIVE |
| FM-31 | Upload tray (per file) | list | upload queue | uploading · done · failed · cancelled | — | — | PLANNED |
| FM-32 | Upload tray: Cancel | button:icon | abort upload | idle · cancelled | upload finished | Upload already finished. | PLANNED |
| FM-33 | Upload tray: Retry | button:icon | re-upload failed item | idle · busy | upload not failed | Only failed uploads can be retried. | PLANNED |
| FM-34 | Permission empty | empty-state | — | "You need `files:read` to browse files." | — | — | LIVE |

**Preview policy (no fake renderers):**

| Mime | Preview | Control |
|---|---|---|
| `text/*`, `application/json`, source | `soma-code-editor` readonly | FM-22 |
| `image/*` | `<img>` from authorized URL | FM-22 |
| `application/pdf` | iframe from authorized URL | FM-22 |
| markdown | `soma-doc-viewer` | FM-22 |
| binary / unknown | metadata card + Download only | FM-22 + FM-17 |

**States (module-level):** `loading` (tree skeleton) · `empty` · `error` + retry · `uploading` · `partial` (list ok, tree failed → banner).  
**A11y:** `role="tree"`/`treeitem` + `aria-expanded` · list `role="table"` · every icon button `aria-label` · focus ring `--skin-focus-ring`.  
**Honesty:** no tree is invented when the API returns a flat list. No upload/delete chrome while those endpoints are absent on this surface (N-9 §2). Missing `mime_type` renders `—`.

---

## 4. MEMORY MANAGER (UI-S-04)

**Route:** `/memory` — **the one Memory home** (IA law). All other entries route here.  
**Component:** `webui/src/views/soma-memory-view.ts`  
**API:**

| Action | Endpoint | Status |
|---|---|---|
| List | `GET /api/v2/memory/` | LIVE |
| Recall | `POST /api/v2/memory/recall` `{query}` | LIVE |
| Remember | `POST /api/v2/memory/save` `{text}` (`MemorySaveIn`) | LIVE (see X-02) |
| Forget | `POST /api/v2/memory/forget` `{coord}` | LIVE |
| Counts WM/LTM | **no count API** | honest `—` / GATED |
| Brain status | `GET /api/v2/core/brain-connector` | LIVE |

### 4.1 Wireframe — Memory workspace

```
┌─ UI-S-00 chrome (thin · abbrev) ────────────────────────────────────────────────────────────────┐
│ [≡] [S] SOMA     ‹clock›   ● ‹conn›   🔔 ‹n›   ▢ ‹project› ▾                                   │
├───────────────────────┬──────────────────────────────────────────────────────────────────────────┤
│ LEFT (this route)     │  MEMORY                                            [⟳ Refresh] [Export]  │
│  ← Back to chat       │  [Search recall…                    ] [Run probe]  layer [both ▾]        │
│  ─────────────────    │                                                                          │
│  TYPE                 │  FILTER  this turn [clear]     ← present when ?turn=current              │
│  [All ▾]              │                                                                          │
│   conversation        │  ┌─ THIS TURN (readout of this turn's recall) ──────┐                    │
│   fact                │  │  ‹n› hits · "Nothing recalled this turn."        │                    │
│   episode             │  │  ‹score›  ‹summary›                              │                    │
│   semantic            │  └──────────────────────────────────────────────────┘                    │
│  ─────────────────    │                                                                          │
│  SORT                 │  ┌─ MEMORY DASHBOARD (API numbers only — no count API) ────────────────┐ │
│  [Newest ▾]           │  │  [WM —]   [LTM —]   [recall ‹live›]   [list ‹live›]                 │ │
│   oldest              │  │  GATED      GATED     this turn         GET /api/v2/memory/         │ │
│   relevance           │  │  (no count API — show — until one ships. Never 0, never a guess.)   │ │
│  ─────────────────    │  └─────────────────────────────────────────────────────────────────────┘ │
│  Total                │  ACTIONS  [Open record] [Remember…] [Forget…] [Export JSON]              │
│  ‹n | —›              │                                                                          │
│                       │  ┌─ RESULT GRID / TIMELINE (server order) ────────────────────────────┐  │
│                       │  │ [kind] ‹summary or content›                      ‹score | —›      │  │
│                       │  │ ‹created_at | —›                        [copy] [Forget…]          │  │
│                       │  │ [kind] ‹summary or content›                      ‹score | —›      │  │
│                       │  └───────────────────────────────────────────────────────────────────┘  │
│                       │  ┌─ REMEMBER / PROBE ────────────────────────────────────────────────┐   │
│                       │  │ Remember [textarea "Text to store as a memory"] [Save to Brain]   │   │
│                       │  │ Probe    [input query]                       [Run recall]         │   │
│                       │  └───────────────────────────────────────────────────────────────────┘   │
└───────────────────────┴──────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Control map — every button and field

| ID | Label | Type | API | States | disabled-when | disabled-reason | Status |
|---|---|---|---|---|---|---|---|
| MM-01 | Title "Memory" | label | — | always | — | — | LIVE |
| MM-02 | Search recall | input:search | `POST /api/v2/memory/recall` | idle · loading · results · empty · error | — | — | LIVE |
| MM-03 | Run probe | button | same as MM-02 | idle · busy · error | empty query | Enter a query to run a recall probe. | LIVE |
| MM-04 | Layer filter `both\|wm\|ltm` | select | client filter when server sends layer | both · wm · ltm | server sends no layer field | Layer is not reported by the API for these rows. | GATED / design |
| MM-05 | This-turn chip + clear | chip + button:icon | `?turn=current` param | hidden · shown | — | — | LIVE (param) |
| MM-06 | This-turn hits panel | readout | this-turn recall rows | populated · empty ("Nothing recalled this turn.") | — | — | LIVE (readout) |
| MM-07 | Type filter chips | chip-group | client filter on `kind` | all · conversation · fact · episode · semantic | — | — | LIVE |
| MM-08 | Sort | select | client sort | newest · oldest · relevance | — | — | LIVE |
| MM-09 | Total Memories | stat | `GET /api/v2/memory/` `total` | value · `—` | — | — | LIVE |
| MM-10 | WM count | stat | **no count API** | `—` | count API absent | No working-memory count API exists. Showing — until one ships. | GATED (honest `—`) |
| MM-11 | LTM count | stat | **no count API** | `—` | count API absent | No long-term count API exists. Showing — until one ships. | GATED (honest `—`) |
| MM-12 | recall count tile | stat | this-turn hit count | value · `0` only when API returned an empty list | — | — | LIVE |
| MM-13 | list count tile | stat | `GET /api/v2/memory/` `total` | value · `—` | — | — | LIVE |
| MM-14 | Brain status badge | badge | `GET /api/v2/core/brain-connector` | ok · degraded · down | — | — | LIVE |
| MM-15 | Memory row | row | select / open detail | default · hover · selected | — | — | LIVE |
| MM-16 | Row kind chip | badge | row `kind` | conversation · fact · episode · semantic · untyped | — | — | LIVE |
| MM-17 | Row score | text | row `score` | value · `—` | — | — | LIVE |
| MM-18 | Row copy | button:icon | clipboard | idle · copied | — | — | LIVE |
| MM-19 | Row Forget… | button:icon | `POST /api/v2/memory/forget` `{coord}` | confirm · busy · error | row has no `coord` | This row has no coord — it cannot be forgotten. | LIVE (confirm UI-M-03) |
| MM-20 | Open record | button | drawer UI-M-01 (FM fields) | loading · open | — | — | PLANNED |
| MM-21 | Record drawer: Copy | button | clipboard | copied | — | — | PLANNED |
| MM-22 | Record drawer: Copy coord | button | clipboard | copied | no coord | This record has no coord. | PLANNED |
| MM-23 | Record drawer: Forget… | button | same as MM-19 | confirm · busy | no coord | This record has no coord — it cannot be forgotten. | PLANNED |
| MM-24 | Record drawer: Close | button | close UI-M-01 | always | — | — | PLANNED |
| MM-25 | Remember… (header) | button | focus MM-27 | idle | — | — | LIVE |
| MM-26 | Forget… (header) | button | requires selected row | idle · confirm | no selection | Select a memory to forget. | LIVE |
| MM-27 | Remember text | textarea | `POST /api/v2/memory/save` `{text}` | idle · saving · error | brain down | SomaBrain is unreachable. Memory writes are fail-closed. | LIVE |
| MM-28 | Save to Brain | button | same as MM-27 | idle · busy · error | empty text or brain down | Enter text to store. / SomaBrain is unreachable. | LIVE |
| MM-29 | Probe query | input | same as MM-02 | idle · typing | — | — | LIVE |
| MM-30 | Export JSON | button | client Blob of loaded rows | idle · done | no rows loaded | There are no loaded rows to export. | LIVE |
| MM-31 | Refresh | button | re-run `GET /api/v2/memory/` | idle · loading · error | — | — | LIVE |
| MM-32 | ← Back to chat | button | `router → /chat` | always | — | — | LIVE |
| MM-33 | Empty state | empty-state | — | "No memories match ‹query›" / "No memories yet." | — | — | LIVE |
| MM-34 | Error state + Retry | error-state | re-fetch | error · retrying | — | — | LIVE |
| MM-35 | Loading skeleton | skeleton | — | loading | — | — | LIVE |
| MM-36 | Permission denied | empty-state | — | "You need `memory:read` to view memories." | — | — | LIVE |

**States:** loading · empty · error · denied · offline (chrome banner; keep last rows).  
**Honesty:** WM/LTM tiles are never `0` without a count API. A failed load is not an empty workspace. `score` missing renders `—`. There is no second Memory surface (N-10 §0).

---

## 5. SOMABRAIN MANAGER (UI-S-56 · UI-X-07 · AgentIQ)

> **DELTA 1.0.1 — IA-001 is authority (`SOMA-UI-DUP-AUDIT-001.md` §5).** Split this mixed surface:
> - **5A Settings › SomaBrain = CONFIG only** (SB-01…08): URL / namespace / retention / sleep_interval / consolidation + connector status. No neuromods, no adaptation sliders.
> - **5B Brain live = canvas UI-X-07 only** (`<soma-cognitive-panel>`): neuromods, sleep, adaptation/memory params, activity log. **Not** a full-page `/cognitive` home.
> - **5C AgentIQ knobs = Capsule** (SB-18…35): Settings › Agent / Capsule or chat dock — never labeled “Brain settings”.
> - **SB-10 `Open /cognitive` is WRONG.** Use **SB-10R Open Brain surface** → `/chat` + `workspaceStore.setSurface('brain')`.

**Audience:** sysadmin / org_admin (settings) · agent owner (knobs) · operator (diagnostics).  
**Components:** `webui/src/views/soma-settings-somabrain.ts` · `webui/src/views/soma-cognitive-panel.ts` · `webui/src/components/soma-agent-iq.ts`  
**API:**

| Group | Endpoint | Status |
|---|---|---|
| Connection knobs | `GET/PUT /api/v2/core/settings/somabrain` | LIVE |
| Connector health | `GET /api/v2/core/brain-connector` | LIVE |
| Cognitive state | `GET /api/v2/somabrain/cognitive/state/{agent_id}` | LIVE |
| Sleep status | `GET /api/v2/somabrain/cognitive/sleep/status/{agent_id}` | LIVE |
| AgentIQ knobs | `GET/PUT /api/v2/core/agentiq/{capsule_id}` | LIVE (see X-01) |
| Derived readouts | returned by AgentIQ GET/PUT (`admin/core/agentiq/derivation.py`) | LIVE read-only |
| Secrets | Vault pointer only | never a token field |

**Not on this surface (no live write API — do not invent):** Kafka reward topic editor · Temporal worker restart · SFM URL · OPA policy editor · live neuromodulator editing.

### 5.1 Wireframe — SomaBrain manager (settings + diagnostics + knobs)

```
┌─ UI-S-00 chrome (abbrev) ───────────────────────────────────────────────────────────────────────┐
│ ☰ SOMA    Settings · SomaBrain              [Search…]                     [Save] [Cancel]       │
├──────────────┬───────────────────────────────────────────────────────────────────────────────────┤
│ SECTION NAV  │  SOMABRAIN CONNECTION                                    ● / ○ connector         │
│  Agent       │  URL            [ ‹url›                          ]  ← SOMABRAIN_URL              │
│  Models      │  Namespace      [ ‹namespace›                    ]  ← SOMABRAIN_NAMESPACE       │
│  Voice       │  Retention days [ ‹retention_days› ]                                         │
│  Interface   │  Sleep interval [ ‹sleep_interval› ]  (seconds)                               │
│  Tools       │  Consolidation  [ ● enable ]           ← consolidation_enabled                  │
│  Integrations│                                                                              │
│  SomaBrain●  │  CONNECTOR STATUS  (GET /api/v2/core/brain-connector) — read-only               │
│  Agent admin │  connector ‹ok|degraded|unavailable› · circuit ‹state› · last ping ‹…›          │
│  Connectivity│  [ Open /memory ]   [ Open Brain surface ]  ← NOT /cognitive (UI-X-07 only)       │
│  Advanced    │                                                                              │
│              │  NEUROMODULATORS (GET /api/v2/somabrain/cognitive/state/{id}) — raw values       │
│              │  DA ‹v›   5-HT ‹v›   NE ‹v›   ACh ‹v›        (omit row if API down)            │
│              │                                                                              │
│              │  SLEEP / CONSOLIDATION (GET …/sleep/status/{id})                                 │
│              │  phase ‹awake|sleeping|—› · last_sleep ‹ts|—› · trigger in flight ‹this session›│
│              │                                                                              │
│              │  AGENTIQ KNOBS (GET/PUT /api/v2/core/agentiq/{capsule_id})                      │
│              │  intelligence  [====|-----] 7     autonomy  [====|-----] 7                      │
│              │  resource      [==|-------] 0.5   style     [balanced ▾]                        │
│              │  [Reset]  [Save knobs]                                                          │
│              │  DERIVED (read-only — never editable)                                           │
│              │  temperature · max_tokens · rlm_iterations · recall_limit · model_tier ·         │
│              │  brain_query_enabled · require_hitl · tool_approval · egress_allowed ·           │
│              │  token_limit · cost_tier · thinking_budget                                       │
│              │                                                                              │
│              │  NOT AVAILABLE AS FIELDS (no write API — honest note)                            │
│              │  "Memory token lives in Vault. Cognitive knobs are per-agent on the Brain        │
│              │   canvas surface (UI-X-07). Temporal host is deploy env, not this form."         │
├──────────────┴──────────────────────────────────────────────────────────────────────────────────┤
│ status: ‹load/save› · PUT /api/v2/core/settings/somabrain · permission: settings:edit           │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Control map — every button and field

> **Placement (delta 1.0.1, IA-001).** Homes are split so no control has two owners:
> **5A** Settings › SomaBrain (config) · **5B** Brain live surface (UI-X-07) · **5C** AgentIQ knobs (Capsule / Settings › Agent).

#### 5A — Settings › SomaBrain (config only)

| ID | Label | Type | API | States | disabled-when | disabled-reason | Status |
|---|---|---|---|---|---|---|---|
| SB-01 | URL | input:url | `PUT …/settings/somabrain` field `url` | loading · dirty · saved · error | `settings:edit` absent | Requires settings edit permission. | LIVE |
| SB-02 | Namespace | input:text | field `namespace` | same | `settings:edit` absent | Requires settings edit permission. | LIVE |
| SB-03 | Retention days | input:number | field `retention_days` | same | `settings:edit` absent | Requires settings edit permission. | LIVE |
| SB-04 | Sleep interval | input:number | field `sleep_interval` | same | `settings:edit` absent | Requires settings edit permission. | LIVE |
| SB-05 | Consolidation | toggle | field `consolidation_enabled` | on · off · disabled | `settings:edit` absent | Requires settings edit permission. | LIVE |
| SB-06 | Save | button | `PUT /api/v2/core/settings/somabrain` | idle · busy · saved · error | not dirty or saving or no `settings:edit` | Requires settings edit permission. / No changes to save. | LIVE |
| SB-07 | Cancel | button | restore last GET values | idle | not dirty | No changes to cancel. | LIVE |
| SB-08 | Connector status row | status | `GET /api/v2/core/brain-connector` | ok · degraded · unavailable | — | — | LIVE |
| SB-09 | Open /memory | button | `router → /memory` | always | — | — | LIVE |
| SB-10 | Open Brain surface | button | `workspaceStore.setSurface('brain')` on `/chat` | always | — | — | LIVE |
| SB-41 | Permission banner | banner | `settings:edit` | shown · hidden | — | — | LIVE |
| SB-42 | Save error banner | banner | PUT failure | shown · hidden | — | — | LIVE |
| SB-43 | Connector unavailable note | banner | connector failure | shown · hidden | — | — | LIVE |

#### 5B — Brain live surface (canvas UI-X-07 only)

| ID | Label | Type | API | States | disabled-when | disabled-reason | Status |
|---|---|---|---|---|---|---|---|
| SB-11 | Neuromodulator DA | stat | cognitive state `neuromodulators` | value · `—` | — | — | LIVE (raw only) |
| SB-12 | Neuromodulator 5-HT | stat | same | value · `—` | — | — | LIVE (raw only) |
| SB-13 | Neuromodulator NE | stat | same | value · `—` | — | — | LIVE (raw only) |
| SB-14 | Neuromodulator ACh | stat | same | value · `—` | — | — | LIVE (raw only) |
| SB-15 | Sleep phase | text | sleep status | awake · sleeping · `—` | — | — | LIVE |
| SB-16 | Last sleep | text | cognitive state `last_sleep` | timestamp · `—` | — | — | LIVE |
| SB-17 | Sleep trigger (session) | badge | local in-flight flag | Idle · In flight (this session) | — | — | LIVE (local honesty) |
| SB-38 | Diagnostics: memory_ok | status | diagnostics API | ok · down | — | — | LIVE |
| SB-39 | Diagnostics: sfm circuit | status | diagnostics API | ok · open | — | — | LIVE |
| SB-40 | Diagnostics: planner | status | feature flag | enabled · gated | flag off | Planner is behind a feature flag and is not enabled. | GATED |
#### 5C — AgentIQ knobs (Capsule / Settings › Agent — never labeled "Brain settings")

| ID | Label | Type | API | States | disabled-when | disabled-reason | Status |
|---|---|---|---|---|---|---|---|
| SB-18 | Intelligence knob | range 1–10 | `PUT /api/v2/core/agentiq/{capsule_id}` | clean · dirty · saving · error | no capsule selected | No capsule selected — knobs are not loaded. | LIVE |
| SB-19 | Autonomy knob | range 1–10 | same | same | no capsule selected | No capsule selected — knobs are not loaded. | LIVE |
| SB-20 | Resource budget knob | range $/turn | same | same | no capsule selected | No capsule selected — knobs are not loaded. | LIVE |
| SB-21 | Style knob | select | same (`response_style`) | balanced · concise · … (closed set from API) | no capsule selected | No capsule selected — knobs are not loaded. | LIVE |
| SB-22 | Save knobs | button | `PUT /api/v2/core/agentiq/{capsule_id}` | idle · busy · saved · error | not dirty or busy or no capsule | No changes to save. / No capsule selected — cannot save knobs. | LIVE |
| SB-23 | Reset knobs | button | restore last GET knobs | idle | not dirty or busy | No changes to reset. | LIVE |
| SB-24 | Derived: temperature | derived readout | AgentIQ derivation | value | — | derived from intelligence_level — do not set directly. | LIVE read-only |
| SB-25 | Derived: max_tokens | derived readout | same | value | — | derived from intelligence_level — do not set directly. | LIVE read-only |
| SB-26 | Derived: rlm_iterations | derived readout | same | value | — | derived from intelligence_level — do not set directly. | LIVE read-only |
| SB-27 | Derived: recall_limit | derived readout | same | value | — | derived from intelligence_level — do not set directly. | LIVE read-only |
| SB-28 | Derived: model_tier | derived readout (enum text) | same | value | — | derived from intelligence_level — do not set directly. | LIVE read-only |
| SB-29 | Derived: brain_query_enabled | derived readout | same | value | — | derived from intelligence_level — do not set directly. | LIVE read-only |
| SB-30 | Derived: require_hitl | derived readout (enum text) | same | value | — | derived from autonomy_level — do not set directly. | LIVE read-only |
| SB-31 | Derived: tool_approval | derived readout (enum text) | same | value | — | derived from autonomy_level — do not set directly. | LIVE read-only |
| SB-32 | Derived: egress_allowed | derived readout (enum text) | same | value | — | derived from autonomy_level — do not set directly. | LIVE read-only |
| SB-33 | Derived: token_limit | derived readout | same | value | — | derived from resource_budget — do not set directly. | LIVE read-only |
| SB-34 | Derived: cost_tier | derived readout (enum text) | same | value | — | derived from resource_budget — do not set directly. | LIVE read-only |
| SB-35 | Derived: thinking_budget | derived readout | same | value | — | derived from resource_budget — do not set directly. | LIVE read-only |
| SB-36 | Unset-knob note | text | shows "unset — using derivation default" when knob absent on Capsule | hidden · shown | — | — | PLANNED (honesty H-06) |
| SB-37 | Memory token pointer | secret-masked | Vault | configured · not configured | always | Set in Vault — not editable here. | GATED (by law) |

**Derived rule (N-12, REQ-UIXS-003):** the 12 fields are computed by `derive_all_settings`. The UI MUST NOT re-implement lookup tables. Enumerated readouts render enum text, not selects. `DerivedSettings` is frozen; readouts mirror that immutability.

**IA-001 note (delta 1.0.1):** `Open /cognitive` is not a second Memory/Brain home. SB-10 opens the Brain **canvas surface** (UI-X-07) via `workspaceStore.setSurface('brain')`. Neuromodulator / sleep / adaptation controls live on that surface (5B), not on Settings › SomaBrain.

**Honesty:** no invented % meters — neuromodulators render raw server values only (N-5 §3.3). No localhost fallback for URL (N-7 H-02). Unset knobs are labeled, never presented as stored Capsule values (N-7 H-06).

---

## 6. COMMAND PALETTE (M-021)

**Module:** M-021 `soma-command-palette` (N-6) · **Host:** shell `overlays` slot · **Trigger:** ⌘K / Ctrl+K  
**Status of the whole module:** **PLANNED** (NEW). No palette is mounted in `webui/src` today.  
**Law:** real actions only (routes, skins, chat commands). No fake rows. Memory/Settings entries navigate to their single home.

### 6.1 Wireframe

```
         ┌──────────────────────────────────────────────────────┐
         │ 🔍  type a command…                                  │
         ├──────────────────────────────────────────────────────┤
         │   Open Memory                              · route   │
         │   Apply skin · Soma Brand                  · skin    │
         │   New chat                                 · chat    │
         │   Export conversation                      · chat    │
         │   Settings · Models                        · route   │
         │   File manager · upload                    · action  │
         │   Switch canvas · Brain                    · surface │
         ├──────────────────────────────────────────────────────┤
         │   ↑↓ navigate    ↵ run    esc close                  │
         └──────────────────────────────────────────────────────┘
```

### 6.2 Control map — every button and field

| ID | Label | Type | API | States | disabled-when | disabled-reason | Status |
|---|---|---|---|---|---|---|---|
| CP-01 | Palette host | overlay | open on ⌘K / Ctrl+K | closed · open | — | — | PLANNED |
| CP-02 | Query | input:search | filter `providers.search()` | idle · typing · searching · results · empty | — | — | PLANNED |
| CP-03 | Result row | button | `provider.execute()` | default · hover · active · busy | provider marks disabled | This action is not available right now. | PLANNED |
| CP-04 | Kind chip | badge | row `kind` | route · action · file · conversation · skin · surface | — | — | PLANNED |
| CP-05 | Recent row | button | same as CP-03 | default · hover | no recents | — | PLANNED |
| CP-06 | Provider error banner | banner | partial provider failure | shown (partial results + banner) · hidden | — | — | PLANNED |
| CP-07 | Empty state | empty-state | — | "No commands match ‹query›." | — | — | PLANNED |
| CP-08 | Footer hint | text | — | "↑↓ navigate · ↵ run · esc close" | — | — | PLANNED |
| CP-09 | Close (esc) | key | close overlay | always | — | — | PLANNED |
| CP-10 | Close (backdrop) | click | close overlay | always | — | — | PLANNED |
| CP-11 | Open Memory entry | action | `router → /memory` | always | — | — | PLANNED |
| CP-12 | New chat entry | action | `POST /api/v2/chat/conversations` | busy · error | — | — | PLANNED |
| CP-13 | Settings entries | action | `router → /settings/…` (single home) | always | — | — | PLANNED |
| CP-14 | Apply skin entry | action | SkinApplier (LIVE skin SDK) | busy · error | skin not installed | That skin is not installed. Install it in Settings › Interface. | PLANNED |

**Providers (closed set, no fake rows):** `route` · `action` · `file` (File Manager) · `conversation` · `skin` · `surface` (canvas tab).  
**States:** closed · searching · results · empty · provider-error (partial results + banner).  
**Honesty:** a provider that errors contributes a banner and no rows — never a placeholder row.

---

## 7. CHAT UPGRADES (UI-S-07)

**Component:** `webui/src/views/soma-chat.ts` + `soma-composer.ts` + `soma-message.ts` + `soma-tool-timeline.ts` + `soma-chat-topbar.ts`  
**Scope of this map:** the P0/P1 upgrade set from N-5 §3.5/§5 plus the LIVE chrome those upgrades hang on.

### 7.1 Wireframe — chat workspace with upgrade points marked

```
┌ sidebar ────────┐┌ chat stream ──────────────────────────────┐┌ canvas (UI-X-*) ┐
│ [New chat]      ││  ‹title›            [Pause][Nudge][Stop]   ││ [Files][Tools]   │
│ [Search…]       ││  ───────────────────────────────────────   ││ [Browser†][Edit] │
│  conversation   ││  user: …                                  ││ [Debug][Capsule] │
│  conversation   ││  assistant: markdown + code + tools        ││ [Brain][Desktop†]│
│  …              ││  ┌ code block [Copy][Download] ─────────┐  ││                  │
│  ───────────    ││  │ highlighted · line numbers · collapse│  ││                  │
│  [Memory]       ││  └──────────────────────────────────────┘  ││                  │
│  [Settings]     ││  ┌ tool.timeline  approve/deny ──────────┐ ││                  │
│  [Profile]      ││  └───────────────────────────────────────┘ ││                  │
│                 ││  branch: ◀ 2/3 ▶  [Create branch]         ││                  │
│                 ││  [composer + attach + mic + queue]         ││                  │
│                 ││  drag-drop / paste → upload tray           ││                  │
└─────────────────┘└────────────────────────────────────────────┘└──────────────────┘
     upgrade points: code highlight · md tables · branch · in-thread search ·
                     drag-drop attach · edit / regenerate / quote
```

### 7.2 Control map — LIVE chrome (context) and every upgrade control

| ID | Label | Type | API | States | disabled-when | disabled-reason | Status |
|---|---|---|---|---|---|---|---|
| CH-01 | New chat | button | `POST /api/v2/chat/conversations` | idle · busy · error | — | — | LIVE |
| CH-02 | Search conversations | input:search | local filter over loaded list | idle · typing · empty | — | — | LIVE |
| CH-03 | Conversation row select | row | `GET /api/v2/chat/conversations/{id}/messages` | default · selected · loading | — | — | LIVE |
| CH-04 | Conversation ⋮ → Rename | menu-item | `PATCH /api/v2/chat/conversations/{id}` | idle · busy · error | — | — | LIVE |
| CH-05 | Conversation ⋮ → Export | menu-item | `GET …/messages` + client Blob | idle · busy | conversation empty | There are no messages to export. | LIVE |
| CH-06 | Conversation ⋮ → Delete | menu-item | `DELETE /api/v2/chat/conversations/{id}` | confirm · busy · error | — | — | LIVE |
| CH-07 | Memory (rail) | link | `router → /memory` | always | — | — | LIVE |
| CH-08 | Settings (rail) | link | `router → /settings` | always | — | — | LIVE |
| CH-09 | User menu → Logout | menu-item | `POST /api/v2/auth/logout` | busy | — | — | LIVE |
| CH-10 | Message list | log | WS `/ws/v2/chat/{id}` stream | loading · empty · streaming · complete | — | — | LIVE |
| CH-11 | Message copy | button:icon | clipboard | copied | — | — | LIVE |
| CH-12 | Tool step expand/collapse | button | local over WS `tool.*` | collapsed · expanded | — | — | LIVE |
| CH-13 | Tool HITL Approve | button | WS `tool.approval` | idle · busy · done | not awaiting approval | This tool call is not awaiting approval. | LIVE |
| CH-14 | Tool HITL Deny | button | WS `tool.approval` | idle · busy · done | not awaiting approval | This tool call is not awaiting approval. | LIVE |
| CH-15 | Composer text | textarea | WS `chat.message` on send | idle · busy · disabled | session not ready | Chat session is not ready. | LIVE |
| CH-16 | Attach (+ menu) | button:menu | `POST /api/v2/filesv2/upload` | idle · uploading · error | — | — | LIVE |
| CH-17 | Mic / STT | button | `POST /api/v2/voice/transcribe` | idle · recording · busy · mic-error | mic unavailable | Microphone capture is not available. | LIVE |
| CH-18 | Send | button | WS `chat.message` | idle · busy | empty text and no attachments | Type a message or attach a file to send. | LIVE |
| CH-19 | Queue chip | badge | local composer queue | hidden · n items | — | — | LIVE |
| CH-20 | Drop queue | button:icon | local `_queue = []` | always | — | — | LIVE |
| CH-21 | Pause / Resume | button | WS `chat.pause` / `chat.resume` | idle · busy | not busy / not paused | No active generation to pause. / Nothing is paused. | LIVE |
| CH-22 | Nudge | button | WS `chat.nudge` | idle · busy | not busy | No active generation to nudge. | LIVE |
| CH-23 | Stop | button | WS `chat.stop` | idle · busy | not busy | No active generation to stop. | LIVE |
| CH-24 | Reset | button | WS `chat.reset` | idle · busy · confirm | — | — | LIVE |
| CH-25 | Turn meta strip | readout | WS `chat.turn_meta` | value · hidden | API/WS absent | — | LIVE |
| CH-26 | **Code syntax highlight** | render (M-029) | none (presentation) | plain (unknown lang) · highlighted · collapsed | — | — | **PLANNED (P0)** |
| CH-27 | Code block Copy | button:icon | clipboard | copied | — | — | **PLANNED (P0)** |
| CH-28 | Code block Download | button:icon | client Blob | idle · done | — | — | **PLANNED (P0)** |
| CH-29 | **Markdown tables** | render (M-031) | none (presentation) | rendered · source-only fallback | — | — | **PLANNED (P0)** |
| CH-30 | Markdown link click | link | policy `allow\|nofollow`; never blind `window.open` | default · external | — | — | **PLANNED (P0)** |
| CH-31 | **In-thread search** | input:search | client filter / jump (M-039) | idle · loading · results · empty | — | — | **PLANNED (P1)** |
| CH-32 | Search result jump | button | scroll-to message | always | — | — | **PLANNED (P1)** |
| CH-33 | **Branch prev / next** | button:icon | server branch index | single · multi · disabled | server sends no branches | Branching is not available for this conversation. | **PLANNED (P1)** |
| CH-34 | **Create branch** | button | branch API (required) | idle · busy | branch API absent | Branching API is not available. | **PLANNED (P1)** |
| CH-35 | **Regenerate** | button | chat API regenerate (required) | idle · busy | message not assistant / not last | Only the latest assistant message can be regenerated. | **PLANNED (P1)** |
| CH-36 | **Edit message** | button:icon | chat API edit (required) | idle · editing · busy | role ≠ user | Only user messages can be edited. | **PLANNED (P1)** |
| CH-37 | **Quote** | button:icon | insert into composer | always | — | — | **PLANNED (P1)** |
| CH-38 | **Delete message** | button:icon | chat API delete (required) | confirm · busy | API absent | Message delete API is not available. | **PLANNED (P1)** |
| CH-39 | **Drag-drop / paste files** | dropzone | `POST /api/v2/filesv2/upload` | idle · uploading · error | — | — | **PLANNED (P0/P1)** |
| CH-40 | Attachment chip remove | button:icon | local | always | upload finished and sent | Attachment already sent with the message. | LIVE |
| CH-41 | Attachment chip retry | button:icon | re-upload | idle · busy | upload not failed | Only failed uploads can be retried. | LIVE |
| CH-42 | Attachment open | button | UI-X-04 / signed URL | idle · busy | no `file_id` | This attachment was not uploaded. | LIVE |
| CH-43 | Mode select (STD/DEV/RO/DGR) | select | local `mode` on next `chat.message` | value | mode locked | This mode is locked in this build. | LIVE |
| CH-44 | Mode TRN / ADM | option | — | locked | always | This mode is locked in this build. | GATED |
| CH-45 | Agent select | select | `GET /api/v2/agents/` + WS reconnect | value · loading | — | — | LIVE |
| CH-46 | Canvas toggle | button | show/hide `soma-right-panel` | open · closed | — | — | LIVE |
| CH-47 | Brain micro-indicator ◉ | status | `GET /api/v2/core/brain-connector` | ok · degraded · unknown (hidden) | — | — | LIVE |
| CH-48 | Model chip (display) | chip | turn_meta model | value · `—` | — | — | LIVE |

**Upgrade priorities (N-5 §5):** P0 = CH-26…CH-30, CH-39 · P1 = CH-31…CH-38.  
**Honesty (N-3):** tool approval never claims allow when OPA denied — denial reason is shown. Streaming stop finalizes honestly. No fake model names on the chip.

---

## 8. SETTINGS KNOBS (UI-S-50…57)

**Shell:** one Settings chrome (M-042) with section nav. Models live **inside** Settings (full-screen section). Memory is **not** a Settings section (its home is `/memory`).  
**Secrets law (N-7 R-SEC-UI-01…05):** presence only + "rotate in Vault". Never a value.

### 8.1 Wireframe — Settings shell (Interface + Models + Tools + AgentIQ excerpts)

```
┌─ UI-S-00 chrome (abbrev) ───────────────────────────────────────────────────────────────────────┐
│ ☰ SOMA    Settings        [Search settings…]                              [Save] [Cancel]        │
├──────────────┬───────────────────────────────────────────────────────────────────────────────────┤
│ SECTION NAV  │  INTERFACE — how the app looks and reads for you                                  │
│  Agent       │   Theme       [system ▼]     Language [en ▼]     Timezone [UTC ▼]                 │
│  Models      │   Date format [YYYY-MM-DD] (read-only)                                           │
│  Voice       │   Agent replies [●]   Activity summary [○]                                       │
│  Interface●  │   SKINS  ┌ gallery: 6 packs · Preview · Apply · Uninstall ┐                      │
│  Tools       │   CHROME (GATED block — reason inline)                                           │
│  Integrations│                                                                              │
│  SomaBrain   │  MODELS                                                                      │
│  Agent admin │   Roles: [Chat ▾] [Utility ▾] [Embedding ▾] [Vision ▾] [Decision/Clef ▾]        │
│  Connectivity│   Providers: groq / mimo / anthropic / …    Key in Vault ✓ (presence only)       │
│  Advanced    │   [Load models]  [Restore bundled presets]                                       │
│              │                                                                              │
│              │  TOOLS                                                                       │
│              │   catalog: [● enable]  tier [▾]  approval required [○]                          │
│              │                                                                              │
│              │  AGENT / IQ (also on /cognitive)                                                │
│              │   intelligence [====|-----] 7   autonomy [====|-----] 7                         │
│              │   resource [==|-------] 0.5     style [balanced ▾]                              │
│              │   derived readouts (read-only) …                                                │
├──────────────┴──────────────────────────────────────────────────────────────────────────────────┤
│ status: ‹load / save› · permission: settings:edit → write, else read-only banner                │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 8.2 Control map — every button and field

| ID | Label | Type | API | States | disabled-when | disabled-reason | Status |
|---|---|---|---|---|---|---|---|
| ST-01 | Section nav | nav | swap section | default · active · locked+reason | section locked | Requires elevated permission for this section. | LIVE |
| ST-02 | Settings search | input:search | client filter of labels | idle · typing · empty | — | — | LIVE |
| ST-03 | Save (header) | button | section-specific PUT | idle · busy · saved · error | not dirty or saving or no `settings:edit` | Requires settings edit permission. / No changes to save. | LIVE |
| ST-04 | Cancel (header) | button | restore last saved values | idle | not dirty | No changes to cancel. | LIVE |
| ST-05 | Theme | select | `PUT /platform/admin/preferences` `theme` | value | no `settings:edit` | Requires settings edit permission. | LIVE |
| ST-06 | Language | select | prefs `language` | value | no `settings:edit` | Requires settings edit permission. | LIVE |
| ST-07 | Timezone | select | prefs `timezone` | value | no `settings:edit` | Requires settings edit permission. | LIVE |
| ST-08 | Date format | read-only | prefs `date_format` (GET only) | value | always | Date format is not editable on this deployment. | LIVE read-only |
| ST-09 | Agent replies | toggle | prefs `notifications.agentReplies` | on · off | no `settings:edit` | Requires settings edit permission. | LIVE |
| ST-10 | Activity summary | toggle | prefs `notifications.activitySummary` | on · off | no `settings:edit` | Requires settings edit permission. | LIVE |
| ST-11 | Skins gallery | component | skin-sdk catalog | loading · populated · empty | — | — | LIVE |
| ST-12 | Skin Preview | button | SkinApplier preview | idle · previewing | — | — | LIVE |
| ST-13 | Skin Apply | button | SkinApplier apply | idle · busy · error | skin missing | That skin pack is not installed. | LIVE |
| ST-14 | Skin Uninstall | button | skin-sdk uninstall | confirm · busy | skin not installed / is active | That skin is not installed. / Unapply the active skin first. | LIVE |
| ST-15 | Install bundled | button | install bundled packs | idle · busy · error | pack already installed | That skin pack is already installed. | LIVE |
| ST-16 | Density | segmented | **no prefs field** | value | always | Density is not persisted yet. | GATED |
| ST-17 | Time format 12h/24h | segmented | **no prefs field** | value | always | Time format is not persisted yet. | GATED |
| ST-18 | Show project bar / clock / connection | per-device toggle | **no prefs field** | value | always | This chrome preference is not persisted yet. | GATED |
| ST-19 | Right panel default | per-device toggle | session-only (`workspace-store`) | value | always | Right-panel default is session-only and is not a saved preference. | GATED |
| ST-20 | Role: Chat model | reference picker | `/api/v2/llm/roles` or `chat_model_id` | value · loading | no configured models | No chat models are configured. Add one in Models. | LIVE |
| ST-21 | Role: Utility model | reference picker | `utility_model_id` | value · loading | no configured models | No utility models are configured. | LIVE |
| ST-22 | Role: Embedding model | reference picker | `embedding_model_id` | value · loading | no configured models | No embedding models are configured. | LIVE |
| ST-23 | Role: Vision model | reference picker | Capsule `image_model` / vision slot | value · loading | no vision-capable models | No vision-capable models are configured. | PLANNED |
| ST-24 | Role: Decision (Clef) | reference picker | decision slot | value · loading | no Clef model configured | No decision model is configured for Clef. | PLANNED |
| ST-25 | Provider row enable | toggle | `llm_provider_configs` | on · off | no `settings:edit` | Requires settings edit permission. | LIVE |
| ST-26 | Provider key | secret-masked | Vault `PUT /secrets/providers/{id}` | set-hidden · unset · editing · testing · error | no `settings:edit` | Requires settings edit permission. Value is never re-displayed. | LIVE (write-only) |
| ST-27 | Provider key Test | button | provider test endpoint | idle · busy · ok · fail | key not set | Set the provider key in Vault first. | LIVE |
| ST-28 | Load models | button | provider model catalog fetch | idle · busy · error | provider not configured | Configure the provider before loading its models. | LIVE |
| ST-29 | Restore bundled presets | button | presets API | idle · busy · confirm | — | — | LIVE |
| ST-30 | Save preset | button | `model_presets` list editor | idle · busy | dirty invalid | Fix the invalid fields before saving the preset. | LIVE |
| ST-31 | Model catalog: Create / Patch | button | `LLMModelConfig` create/patch | idle · busy · invalid-schema | no `settings:edit` | Requires settings edit permission. | LIVE |
| ST-32 | Model catalog: Activate | toggle/button | `is_active` | on · off | no `settings:edit` | Requires settings edit permission. | LIVE |
| ST-33 | Tool enable | toggle | `GET/PUT /api/v2/tools/catalog` | on · off | tool policy denies / no `settings:edit` | Tool policy denies enabling this tool. / Requires settings edit permission. | LIVE |
| ST-34 | Tool tier | select | tool catalog tier field | value | no `settings:edit` | Requires settings edit permission. | LIVE |
| ST-35 | Tool approval required | toggle | tool catalog approval field | on · off | no `settings:edit` | Requires settings edit permission. | LIVE |
| ST-36 | Persona / system prompt | textarea | Capsule `system_prompt` | dirty · saving · error | no `settings:edit` | Requires settings edit permission. | LIVE |
| ST-37 | IQ knobs (Agent section) | range ×3 + select | `PUT /api/v2/core/agentiq/{capsule_id}` | dirty · saving · error | no capsule selected | No capsule selected — knobs are not loaded. | LIVE (see SB-18…23) |
| ST-38 | Derived readouts (Agent section) | derived readout ×12 | AgentIQ derivation | value | always | derived from a knob — do not set directly. | LIVE read-only |
| ST-39 | Export config | button | client download (local draft or capsule export) | idle · done | nothing to export | There is no configuration to export. | LIVE (labelled honestly as local draft until bound to capsule export) |
| ST-40 | Import config | button | `services/capsule_import.py` (required) | idle · busy · error | import API not wired | Import is not wired to the capsule import API on this deployment. | GATED |
| ST-41 | Reset All Settings | button | real reset API (required) | confirm · busy | reset API not wired / no confirm | Reset is not wired to a real reset API. | GATED |
| ST-42 | Permission banner | banner | `settings:edit` | shown · hidden | — | — | LIVE |
| ST-43 | Save error banner | banner | PUT failure | shown · hidden | — | — | LIVE |

**Secrets rule (normative, N-7 §10):** ST-26 and every `L4-secret` row render presence only. The "rotate in Vault" affordance links to the Vault path and SHALL NOT accept a secret value in the Soma UI.

**Honesty:** no demo key fragments (N-7 H-01 / G-06). No hardcoded topology values (N-7 H-02 / G-10). No control without a handler (N-7 H-04 / G-07, G-08, G-15, G-16). No panel that edits nothing (N-7 H-05 / G-13).

---

## 9. Shared state contract (all surfaces)

| State | Render | Forbidden |
|---|---|---|
| loading | skeleton (M-016) matching final layout | counts, metrics, fake rows while loading |
| empty | `soma-empty-state` kind=`empty` | spinning forever; error disguised as empty |
| error | `soma-error-state` + Retry; name the failed request | console-only failure; silent catch |
| gated | `soma-empty-state` kind=`gated` or disabled control + reason | "coming soon"; enabled control with no handler |
| permission-denied | lock + reason + required permission name | generic "forbidden" with no next step |
| offline | chrome banner; keep last painted rows | inventing fresher data |

Module-level mapping is per N-6 (`loading` / `empty` / `error` on every data-bearing module; empty ≠ error).

---

## 10. Build plan (docs → code only after operator GO)

**Plan law (N-5 header):** no product code until the operator says GO. This section is the ordered delivery plan the GO unlocks.

| Phase | Deliverable | Controls in scope | Exit criteria (live proof) |
|---|---|---|---|
| **A — Design lock** | This document + N-5 master design | all IDs | operator approves control maps; no code |
| **B — Backend unlocks** | `GET /api/v2/workroot/tree` · `PUT /api/v2/filesv2/{id}/content` · `POST /api/v2/workroot/mkdir` · `DELETE /api/v2/filesv2/{id}` · PathGuard jail | FM-08, FM-12, FM-13, FM-19, FM-20, FM-21 | unit + PathGuard tests green; no route without jail |
| **C — Readable output + File Manager** | M-029 code highlight · M-031 markdown tables · M-024 File Manager (browse/select/manage) | CH-26…CH-30, FM-01…FM-34 | Playwright file flow on real services (list → open → download → attach) |
| **D — Managers + palette** | Memory depth (MM-20…MM-24) · SomaBrain manager polish (SB-36) · Command Palette (CP-01…CP-14) · chat branching/search/edit (CH-31…CH-38) | MM-*, SB-*, CP-*, CH-31…CH-38 | Playwright chat+memory session green; palette executes real routes only |
| **E — Tool depth** | artifact/chart/notify/scheduler/git/browser tool e2e (N-5 §4) | CH tool timeline + gates | tool e2e on real services; browser tool remains container-only |
| **F — Settings depth + a11y + skins** | ST-16…ST-24 polish · ST-40/41 honest wires or removal · a11y sweep · skins burn-down of hex literals | ST-*, all surfaces | full agent session green; axe clean on the six surfaces; zero disabled-without-reason findings |

### 10.1 Per-PR acceptance (every phase after GO)

- [ ] Real handler or honest GATED mark with reason — no mock rows, no TODO passes.
- [ ] Control table row for every new button/field added or updated here.
- [ ] `npx tsc` clean · `vite build` clean.
- [ ] Playwright human session green on **real** services (not skip-gated, not mocked).
- [ ] No hex colour literals in new components (skin tokens only).
- [ ] Empty ≠ error; counts cite their API; secrets never rendered.

### 10.2 Sequencing constraints

```
B (backend) ──► C (FM + highlight/markdown) ──► D (managers + palette + chat P1) ──► E (tools)
                                                      │
                                                      └──► F (settings depth + a11y)  [can start after C]
```

- FM Save (FM-19 write) stays GATED until B ships `PUT …/content`.
- CP file provider needs FM list API (already LIVE) — palette can ship in D without B's new routes.
- CH branching/search/edit need their chat APIs named in B/E; until then those controls stay PLANNED and are not drawn as enabled.

---

## 11. Traceability

| Control set | Traces to | Module | Screen/surface | Gaps closed |
|---|---|---|---|---|
| FM-01…FM-34 | N-5 §3.1 · N-6 M-024 · N-9 | M-024 | UI-X-01 | M-09/M-10 file ops/tree · U-05 attachments · U-14/U-15 editors |
| MM-01…MM-36 | N-5 §3.2 · N-10 | memory view | UI-S-04 | Memory operability (advantage vs A0) |
| SB-01…SB-43 | N-5 §3.3 · N-11 · N-12 | settings-somabrain + agent-iq + cognitive | UI-S-56 · UI-X-07 | honest meters; AgentIQ derived rule |
| CP-01…CP-14 | N-5 §3.6 · N-6 M-021 | M-021 | shell overlays | A0-class navigation without mouse |
| CH-01…CH-48 | N-5 §3.5/§5 · N-8 | chat family | UI-S-07 | U-03 highlight · U-04 markdown · U-08 branch · U-10 search |
| ST-01…ST-43 | N-5 §3.4 · N-7 · N-11 | settings shell family | UI-S-50…57 | settings depth + secrets rule + honesty H-01…H-08 |

---

## 12. Disagreement register

Measured differences between live code, mockups, and design docs. None silently reconciled.

| ID | Disagreement | Evidence | Effect on this document |
|---|---|---|---|
| X-01 | Master design writes AgentIQ knobs via `PATCH /agents/{id}/capsule`; live `soma-agent-iq.ts` uses `PUT /api/v2/core/agentiq/{capsule_id}`. | N-5 §3.3 vs `webui/src/components/soma-agent-iq.ts:8,414` | SB-18…SB-23 bind the live `PUT /api/v2/core/agentiq/{capsule_id}`. The capsule PATCH path is not used by the UI. |
| X-02 | `UI-S-04` mockup names Remember as `POST /api/v2/memory/remember`; live view calls `POST /api/v2/memory/save` (`MemorySaveIn`). | N-10 §2 vs `webui/src/views/soma-memory-view.ts:1182-1191` | MM-27/MM-28 bind `POST /api/v2/memory/save`. Mockup path is stale until it is updated. |
| X-03 | `UI-X-01` states "no upload/delete chrome" on the Files surface; N-5 §3.1 wireframe shows upload/delete affordances for the full File Manager. | N-9 §2 vs N-5 §3.1 | FM rows distinguish **thin surface LIVE** (list/open/download) from **M-024 target** (tree/upload/delete). No LIVE mark is claimed for controls the thin surface does not draw. |
| X-04 | `UI-C-*` IDs are not unique across annexes (two overlapping allocations). | `SOMA-UI-MOCKUPS-001.md` defect M-01 | This document uses `FM/MM/SB/CP/CH/ST` prefixes and does not allocate `UI-C-*`. A future IDREG revision MUST publish one global table. |
| X-05 | Master design §3.3 shows style knob values `balanced ▾`; the closed set comes from the AgentIQ API, not from this document. | N-5 §3.3 | SB-21 states "closed set from API". No invented enum members. |
| X-06 | `SOMA-UI-CONTROL-MAPS-001` does not match `check_docs.py` pattern `^SOMA-UI-[A-Z0-9]+-\d{3}$` for `docs/design/` because the title token `CONTROL-MAPS` contains a hyphen. Same class of gap as `SOMA-UI-MODULE-CATALOG-001` and `SOMA-UI-CHAT-WORKSPACE-001`. | `scripts/check_docs.py:57` vs this document's identifier | Register Compliance is computed `Non-compliant` for C-11 only. Content rules (Document Control fields, Status enum, Revision History columns, End of Document) pass. Suite-wide fix is either widening the pattern to `SOMA-UI-[A-Z0-9-]+-\d{3}$` or a DOCS-001 filename exception — out of scope for this document. |

---

## 13. Maintenance

- Any new button or field on the six surfaces **SHALL** get a row in the matching §3–§8 table with all eight columns filled.
- Status changes (PLANNED → LIVE, GATED reason change) **SHALL** update the row and the Revision History in the same change.
- Required-new APIs **SHALL** be implemented under PathGuard / Vault / OPA laws; their rows un-GATE only after the real handler exists.
- This document **SHALL** be reviewed on `Next Review`, or when N-5 build order, N-6 module contracts, or the settings resolution order changes.
- The string "coming soon" **SHALL NOT** appear as a specification value (N-2 REQ-DOCS-015).

---

End of Document
