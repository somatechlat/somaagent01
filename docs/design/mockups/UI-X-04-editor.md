# UI-X-04 — Editor

Surface **UI-X-04 Editor** · Right canvas (Band D) · Facet: Surface · Chrome: UI-S-00 abbreviated
Registry: `webui/src/components/soma-right-panel.ts` → `SURFACES` key `editor`
Backing (live): file content opened from **UI-X-01** (read-only)
Nav: `SOMA-UI-NAV-001.md` §2 canvas

**Status: LIVE (read-only).** Present and available. No `blockedReason`.
Honesty (verbatim in UI): “This deployment exposes no file-write endpoint; the buffer is read-only.”

---

## 1. ASCII wireframe — docked in the canvas

```
┌─ chrome (abbrev) ──────────────────────┬ RIGHT CANVAS · UI-X-04 Editor                                 ┐
│  chat workspace (UI-S-07)              │ [📁 Files][🔧 Tools][🌐 Browser†][💻 Editor]                  │
│  ┌────────────────────────────────┐    │ [🐞 Debug][📦 Capsule][🧠 Brain][🖥 Desktop†]                  │
│  │ screen content in context      │    ├──────────────────────────────────────────────────────────────┤
│  │ surface rail select: Editor    │    │  Editor  UI-X-04                                             │
│  └────────────────────────────────┘    │  ‹original_name | name›                    ‹lang›           │
│                                        │                                                                │
│                                        │  This deployment exposes no file-write endpoint; the         │
│                                        │  buffer is read-only. Save stays disabled: filesv2 has no    │
│                                        │  PUT/content route for an existing file.                     │
│                                        │                                                                │
│                                        │  [Save disabled]                                  ‹lang› chip  │
│                                        │                                                                │
│                                        │  ┌─ code (pre) ────────────────────────────────────────────┐  │
│                                        │  │ ‹file content›                                         │  │
│                                        │  │ …                                                       │  │
│                                        │  └─────────────────────────────────────────────────────────┘  │
│                                        │                                                                │
│  instance ‹session_id› ‹state›         │  Save is present but disabled with its reason (REQ-UIX-020).   │
└────────────────────────────────────────┴──────────────────────────────────────────────────────────────┘
```

---

## 2. Control map

| # | Control | Behavior | Live? |
|---|---|---|---|
| 1 | File name + language chip | From the opened `FileOut` (`original_name \|\| name`); `languageOf()` derives the chip from the filename only. | live |
| 2 | Read-only note | Always shown while a file is open. States the missing write endpoint **and** why Save is disabled (no PUT/content route — filesv2 has presigned download/upload only). | live |
| 3 | Code block | Exact server file content in a `<pre>`. No highlighting that would alter text. | live |
| 4 | Save (disabled) | Present-but-disabled with its reason (`title`/`aria-label` + the note). There is no write path for an existing file, so saving would be a lie — but the control states *why* instead of being absent. | live (disabled) |

Open path: UI-X-01 row → `_openFileInEditor` → this surface becomes active.

---

## 3. States

| State | Verbatim |
|---|---|
| empty | “No file open.” |
| loading | “Opening file…” (header already shows name + lang) |
| error | “File content could not be loaded.” |
| offline | Chrome offline banner; last opened buffer remains. |

---

## 4. Modal overlays

None. No discard dialog while the buffer is read-only.

---

## 5. Navigation

| In | Out |
|---|---|
| Canvas tab **Editor** (registry order 4/8) | UI-X-01 Files (open another file) |
| UI-X-01 row click / Enter | — |

Cross-link: `SOMA-UI-NAV-001.md` §2 canvas · §5 acceptance.
**No Memory tab in the canvas.**

---

## 6. Honesty

- Content is the server bytes. Language chip is filename-derived display only.
- Read-only is stated in plain language, not implied by greyed buttons.
- Save exists but is disabled, and the reason names the missing endpoint — a save with no write path would be a lie either way; hiding the control entirely would hide the gap.
- No multi-tab strip until multiple open buffers are real.

---

## 7. Source map

| Source | Role |
|---|---|
| `webui/src/components/soma-right-panel.ts` | `_renderEditor` · `_openFileInEditor` · `languageOf` |
| UI-X-01 `FileOut` | Identity of the open file |
| file content fetch | Server text; null → error state |

End of Document
