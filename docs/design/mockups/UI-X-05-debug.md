# UI-X-05 — Debug

Surface **UI-X-05 Debug** · Right canvas (Band D) · Facet: Surface · Chrome: UI-S-00 abbreviated
Registry: `webui/src/components/soma-right-panel.ts` → `SURFACES` key `debug`
Backing (live): real WS frame ring buffer (`websocket-client.ts` `wsFrameLog` / `onWsFrame`)
Nav: `SOMA-UI-NAV-001.md` §2 canvas

**Status: LIVE (developer mode).** Present and available. No `blockedReason`.

---

## 1. ASCII wireframe — docked in the canvas

```
┌─ chrome (abbrev) ──────────────────────┬ RIGHT CANVAS · UI-X-05 Debug                                  ┐
│  chat workspace (UI-S-07)              │ [📁 Files][🔧 Tools][🌐 Browser†][💻 Editor]                  │
│  ┌────────────────────────────────┐    │ [🐞 Debug][📦 Capsule][🧠 Brain][🖥 Desktop†]                  │
│  │ screen content in context      │    ├──────────────────────────────────────────────────────────────┤
│  │ surface rail select: Debug     │    │  Debug  UI-X-05                                              │
│  └────────────────────────────────┘    │  [filter frames__________]  [Clear stream]                   │
│                                        │                                                                │
│                                        │  ┌─ WS frame log (newest first) ───────────────────────────┐  │
│                                        │  │ ‹ts›  ←  ‹type›  ‹payload preview…›                     │  │
│                                        │  │ ‹ts›  →  ‹type›  ‹payload preview…›                     │  │
│                                        │  │ ‹ts›  ←  ‹type›  ‹payload preview…›                     │  │
│                                        │  └─────────────────────────────────────────────────────────┘  │
│                                        │                                                                │
│  instance ‹session_id› ‹state›         │  ← inbound   → outbound                                      │
│                                        │  Hover row → full JSON payload (title).                      │
└────────────────────────────────────────┴──────────────────────────────────────────────────────────────┘
```

---

## 2. Control map

| # | Control | Behavior | Live? |
|---|---|---|---|
| 1 | Frame log | Real frames from `wsFrameLog`, reversed (newest first). Columns: `ts` · `dir` (`←` in / `→` out) · `type` · payload preview (120 chars + `…`). | live |
| 2 | Filter frames | Matches `type` or stringified `payload` (case-insensitive). Filters the real buffer only. | live |
| 3 | Clear stream | Local view buffer only (`clearedBefore = now`). Does **not** stop collection or clear the server. | live |
| 4 | Payload title | Full JSON on hover via `title` attribute. | live |
| 5 | Pause toggle / request inspector drawer | **Not drawn** in this surface today. | absent |

Nothing is synthesised to fill the pane. An empty log is an empty log.

---

## 3. States

| State | Verbatim |
|---|---|
| empty | “No events yet.” |
| empty (after clear) | “No events yet.” (local clear only) |
| empty (filter) | “No events yet.” |
| loading | Not applicable — frames append as they arrive. |
| error | Not applicable — the buffer is client-local. |
| offline | New frames stop; painted rows remain. |

No counts, charts, or metrics.

---

## 4. Modal overlays

None. Full payload is the row `title` (hover), not a drawer.

---

## 5. Navigation

| In | Out |
|---|---|
| Canvas tab **Debug** (registry order 5/8) | — (self-contained read surface) |

Cross-link: `SOMA-UI-NAV-001.md` §2 canvas · §5 acceptance.
**No Memory tab in the canvas.**

---

## 6. Honesty

- Every row is a real WS frame with its real timestamp and direction.
- Preview truncation is display-only; the full payload is available on hover.
- Clear is explicitly local — never claimed to stop the stream.

---

## 7. Source map

| Source | Role |
|---|---|
| `webui/src/components/soma-right-panel.ts` | `_renderDebug` · `_payloadPreview` · `_payloadTitle` |
| `webui/src/services/websocket-client.ts` | `wsFrameLog` · `onWsFrame` · `WsFrame` |

End of Document
