# UI-X-08 — Desktop

Surface **UI-X-08 Desktop** · Right canvas (Band D) · Facet: Surface · Chrome: UI-S-00 abbreviated
Registry: `webui/src/components/soma-right-panel.ts` → `SURFACES` key `desktop`
Nav: `SOMA-UI-NAV-001.md` §2 canvas († gated)

**Status: GATED (present-but-disabled).** `blockedReason` (verbatim):
**“Requires a remote-desktop capability in somaAgent01. Not available today.”**

REQ-UIX-020 / REQ-UIX-007: the tab stays on the rail and stays selectable so the surface set is
complete. It is never omitted, never presented as working, and never a “coming soon” placeholder.
Every control is disabled and prints the blocking reason inline. The banned placeholder phrase of §2.3
does not appear.

---

## 1. ASCII wireframe — gated frame in the canvas

```
┌─ chrome (abbrev) ──────────────────────┬ RIGHT CANVAS · UI-X-08 Desktop (GATED)                        ┐
│  chat workspace (UI-S-07)              │ [📁 Files][🔧 Tools][🌐 Browser†][💻 Editor]                  │
│  ┌────────────────────────────────┐    │ [🐞 Debug][📦 Capsule][🧠 Brain][🖥 Desktop†]                  │
│  │ screen content in context      │    ├──────────────────────────────────────────────────────────────┤
│  │ surface rail select: Desktop   │    │  Desktop  UI-X-08          (tab shown disabled)              │
│  └────────────────────────────────┘    │                                                                │
│                                        │  ┌─ disabled frame (aria-disabled) ────────────────────────┐  │
│                                        │  │                                                          │  │
│                                        │  │  Requires a remote-desktop capability in somaAgent01.    │  │
│                                        │  │  Not available today.                                    │  │
│                                        │  │                                                          │  │
│                                        │  │  [ Open desktop session ]   DISABLED                     │  │
│                                        │  │   reason: Requires a remote-desktop capability in        │  │
│                                        │  │   somaAgent01. Not available today.                      │  │
│                                        │  │                                                          │  │
│                                        │  └──────────────────────────────────────────────────────────┘  │
│                                        │                                                                │
│  instance ‹session_id› ‹state›         │  No VNC viewport. No pointer/keyboard/clipboard/screenshot.   │
│                                        │  Nothing that could be mistaken for a live desktop.           │
└────────────────────────────────────────┴──────────────────────────────────────────────────────────────┘
```

---

## 2. Control map

| # | Control | Behavior | Live? |
|---|---|---|---|
| 1 | Tab (Desktop) | Visible + selectable; `aria-disabled="true"`. Tooltip/label = the blocking reason. | gated |
| 2 | Disabled frame | Prints `blockedReason`. No interactive working children. | gated |
| 3 | Open desktop session | Rendered `disabled` with `title` / `aria-label` = the blocking reason. | gated |
| 4 | Pointer / keyboard / clipboard / screenshot / VNC viewport | **Not drawn.** A gated surface has no working-looking controls. | absent |

---

## 3. States

| State | Behavior |
|---|---|
| gated (always) | Disabled frame + disabled button, both with the verbatim reason. |
| loading | **None.** A gated control never shows a spinner or progress. |
| empty | **None.** The surface is gated, not empty. |
| error | **None.** No request is made from a gated control. |
| permission-denied | Same gate reason. |
| offline | Same gate reason (the gate is capability-based, not connectivity-based). |

---

## 4. Modal overlays

None. This surface opens no overlay while gated.

---

## 5. Navigation

| In | Out |
|---|---|
| Canvas tab **Desktop** (registry order 8/8) — selectable, disabled content | — (no destination while gated) |

Cross-link: `SOMA-UI-NAV-001.md` §2 canvas (†) · §5 “Gated surfaces carry blocking reason”.
**No Memory tab in the canvas.**

---

## 6. Honesty

- Blocking reason is the registry string, not a paraphrase.
- No fake desktop frame, no “coming soon” chrome, no demo screenshot.
- The surface remains in the rail so the eight-surface set is complete and auditable.

---

## 7. Source map

| Source | Role |
|---|---|
| `webui/src/components/soma-right-panel.ts` | `SURFACES` `desktop.blockedReason` + `_renderDesktop` |
| REQ-UIX-007 | Desktop capability does not exist in somaAgent01 today |
| REQ-UIX-020 | Present-but-disabled with reason |

End of Document
