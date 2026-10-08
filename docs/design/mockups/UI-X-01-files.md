# UI-X-01 — Files

Surface **UI-X-01 Files** · Right canvas (Band D) · Facet: Surface · Chrome: UI-S-00 abbreviated
Registry: `webui/src/components/soma-right-panel.ts` → `SURFACES` key `files`
Backing (live): `GET /api/v2/filesv2/` (`FileListResponse`)
Nav: `SOMA-UI-NAV-001.md` §2 canvas (no Memory tab) · §3 Files one-home

**Status: LIVE.** Present and available. No `blockedReason` on this surface.

---

## 1. ASCII wireframe — docked in the canvas

```
┌─ chrome (abbrev) ──────────────────────┬ RIGHT CANVAS · UI-X-01 Files                                 ┐
│  chat workspace (UI-S-07)              │ [📁 Files][🔧 Tools][🌐 Browser†][💻 Editor]                  │
│  ┌────────────────────────────────┐    │ [🐞 Debug][📦 Capsule][🧠 Brain][🖥 Desktop†]                  │
│  │ screen content in context      │    ├──────────────────────────────────────────────────────────────┤
│  │ surface rail select: Files     │    │  Files  UI-X-01                                              │
│  └────────────────────────────────┘    │                                                                │
│                                        │  ┌─ file list ─────────────────────────────────────────────┐  │
│                                        │  │ 📄 ‹original_name | name›                               │  │
│                                        │  │    ‹mime_type | —› · v‹version›          ‹size_bytes›   │  │
│                                        │  │ 📄 ‹original_name | name›                               │  │
│                                        │  │    ‹mime_type | —› · v‹version›          ‹size_bytes›   │  │
│                                        │  │ …                                                         │  │
│                                        │  └─────────────────────────────────────────────────────────┘  │
│                                        │  showing ‹n› of ‹total›          (only when total > shown)   │
│                                        │                                                                │
│  instance ‹session_id› ‹state›         │  Click / Enter → open in UI-X-04 Editor (same file).         │
└────────────────────────────────────────┴──────────────────────────────────────────────────────────────┘
† GATED surfaces — see UI-X-03 / UI-X-08. They stay on the rail with the reason.
```

---

## 2. Control map

| # | Control | Behavior | Live? |
|---|---|---|---|
| 1 | File row list | Real `FileOut` rows: `original_name \|\| name`, `mime_type`, `version`, `size_bytes`. Lazy-loaded on first open of the surface. | live |
| 2 | Row open (click / Enter / Space) | Opens the file in **UI-X-04 Editor** (read-only). | live |
| 3 | “showing N of total” | Rendered only when `total > files.length`. Never a guessed remainder. | live |
| 4 | Upload / new folder | **Not in this surface today.** No upload control is drawn. | absent |
| 5 | Delete / rename | **Not in this surface today.** No destructive control is drawn. | absent |

No tree is invented when the API returns a flat list. No preview pane until a preview path exists.

---

## 3. States

| State | Verbatim |
|---|---|
| idle / loading | “Loading files…” |
| empty | “No files in the working set.” |
| error | “Files could not be listed.” |
| denied | “You need `files:read` to browse files.” |
| offline | Chrome offline banner; list keeps last painted rows. |

No counts, charts, or metrics while loading.

---

## 4. Modal overlays

None from this surface. Opening a file selects **UI-X-04** in the same canvas (not a modal).

---

## 5. Navigation

| In | Out |
|---|---|
| Canvas tab **Files** (registry order 1/8) | UI-X-04 Editor (file open) |
| Attach menu (drawer of the same list — not a second tree) | — |

Cross-link: `SOMA-UI-NAV-001.md` §2 canvas · §3 Files one-home · §5 acceptance.
**No Memory tab in the canvas** — Memory is only `/memory` (UI-S-04).

---

## 6. Honesty

- Every row is a `FileOut` from the API. Missing `mime_type` renders `—`.
- `size_bytes` is formatted only for display; the number is the server’s.
- No upload/delete chrome while those endpoints are not wired on this surface.
- A failed load is not an empty workspace — it is the error state.

---

## 7. Source map

| Source | Role |
|---|---|
| `webui/src/components/soma-right-panel.ts` | Registry + `_renderFiles` + `_openFileInEditor` |
| `GET /api/v2/filesv2/` | `FileListResponse` `{files, total, page, per_page}` |
| `FileOut` | `id, name, original_name, mime_type, size_bytes, version, storage_backend, metadata, tags, created_at, updated_at` |

End of Document
