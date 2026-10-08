# UI-X-03 — Browser

Surface **UI-X-03 Browser** · Right canvas (Band D) · Facet: Surface · Chrome: UI-S-00 abbreviated
Registry: `webui/src/components/soma-right-panel.ts` → `SURFACES` key `browser`
Nav: `SOMA-UI-NAV-001.md` §2 canvas

**Status: GATED (present-but-disabled).** `blockedReason` (verbatim):
**“Bind a browser model on UI-S-02 first”**
Secondary note (live): “This deployment exposes no browser binding; binding cannot be verified here.”

REQ-UIX-020: the tab stays on the rail and stays selectable so the surface set is complete. It is never omitted, never presented as working, and never a fake page. The banned placeholder phrase of §2.3 does not appear.

---

## 1. ASCII wireframe — gated frame in the canvas

```
┌─ chrome (abbrev) ──────────────────────┬ RIGHT CANVAS · UI-X-03 Browser (GATED)                        ┐
│  chat workspace (UI-S-07)              │ [📁 Files][🔧 Tools][🌐 Browser†][💻 Editor]                  │
│  ┌────────────────────────────────┐    │ [🐞 Debug][📦 Capsule][🧠 Brain][🖥 Desktop†]                  │
│  │ screen content in context      │    ├──────────────────────────────────────────────────────────────┤
│  │ surface rail select: Browser   │    │  Browser  UI-X-03           (tab shown disabled)             │
│  └────────────────────────────────┘    │                                                                │
│                                        │  ┌─ disabled frame (aria-disabled) ────────────────────────┐  │
│                                        │  │                                                          │  │
│                                        │  │  Bind a browser model on UI-S-02 first                   │  │
│                                        │  │                                                          │  │
│                                        │  │  This deployment exposes no browser binding; binding     │  │
│                                        │  │  cannot be verified here.                                │  │
│                                        │  │                                                          │  │
│                                        │  └──────────────────────────────────────────────────────────┘  │
│                                        │                                                                │
│  instance ‹session_id› ‹state›         │  No URL bar. No viewport. No screenshot. Nothing is drawn     │
│                                        │  that could be mistaken for a live page.                      │
└────────────────────────────────────────┴──────────────────────────────────────────────────────────────┘
```

---

## 2. Control map

| # | Control | Behavior | Live? |
|---|---|---|---|
| 1 | Tab (Browser) | Visible + selectable; `aria-disabled="true"`. Tooltip/label = the blocking reason. | gated |
| 2 | Disabled frame | Prints `blockedReason` + the deployment note. No interactive children. | gated |
| 3 | URL / go / reload / viewport / screenshot | **Not drawn.** A gated surface has no working-looking controls. | absent |

When a browser model binding and a viewport backend exist, this mock is replaced by a working Browser surface — until then the gate is the truth.

---

## 3. States

| State | Behavior |
|---|---|
| gated (always) | Disabled frame with the verbatim reason. |
| loading | **None.** A gated control never shows a spinner. |
| empty | **None.** The surface is gated, not empty. |
| error | **None.** No request is made from a gated surface. |
| permission-denied | Same gate reason (capability-based). |
| offline | Same gate reason (the gate is capability-based, not connectivity-based). |

---

## 4. Modal overlays

None. This surface opens no overlay while gated.

---

## 5. Navigation

| In | Out |
|---|---|
| Canvas tab **Browser** (registry order 3/8) — selectable, disabled content | UI-S-02 Brain (where a browser model would be bound) |

Cross-link: `SOMA-UI-NAV-001.md` §2 canvas († marks gated) · §5 “Gated surfaces carry blocking reason”.
**No Memory tab in the canvas.**

---

## 6. Honesty

- Blocking reason is the registry string, not a paraphrase.
- No fake page, no screenshot, no “coming soon” decoration.
- The surface remains in the rail so the eight-surface set is complete and auditable.

---

## 7. Source map

| Source | Role |
|---|---|
| `webui/src/components/soma-right-panel.ts` | `SURFACES` `browser.blockedReason` + `_renderBrowser` |
| REQ-UIX-020 | Present-but-disabled with reason |
| model-role API | No browser role/binding in this deployment (chat/utility/embedding only) |

End of Document
