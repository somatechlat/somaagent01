# UI-X-02 — Tools

Surface **UI-X-02 Tools** · Right canvas (Band D) · Facet: Surface · Chrome: UI-S-00 abbreviated
Registry: `webui/src/components/soma-right-panel.ts` → `SURFACES` key `tools`
Backing (live): `GET /api/v2/tools` (`ToolsListResponse`) + live `tool.*` WS frames
Nav: `SOMA-UI-NAV-001.md` §2 canvas

**Status: LIVE.** Present and available. No `blockedReason` on this surface.

---

## 1. ASCII wireframe — docked in the canvas

```
┌─ chrome (abbrev) ──────────────────────┬ RIGHT CANVAS · UI-X-02 Tools                                  ┐
│  chat workspace (UI-S-07)              │ [📁 Files][🔧 Tools][🌐 Browser†][💻 Editor]                  │
│  ┌────────────────────────────────┐    │ [🐞 Debug][📦 Capsule][🧠 Brain][🖥 Desktop†]                  │
│  │ screen content in context      │    ├──────────────────────────────────────────────────────────────┤
│  │ surface rail select: Tools     │    │  Tools  UI-X-02                                              │
│  └────────────────────────────────┘    │                                                                │
│                                        │  ┌─ attached tools ────────────────────────────────────────┐  │
│                                        │  │ ‹tool.name›                                             │  │
│                                        │  │   ‹tool.description›                                   │  │
│                                        │  │   [Show schema] / [Hide schema]                         │  │
│                                        │  │   ┌ schema (JSON, server parameters) ────────────────┐  │  │
│                                        │  │   │ ‹tool.parameters›                               │  │  │
│                                        │  │   └──────────────────────────────────────────────────┘  │  │
│                                        │  │ ‹tool.name›                                             │  │
│                                        │  └─────────────────────────────────────────────────────────┘  │
│                                        │                                                                │
│                                        │  LIVE CALL LOG                                                 │
│                                        │  ┌─────────────────────────────────────────────────────────┐  │
│                                        │  │ ‹tool.name›                    ‹status›      ‹ts›       │  │
│                                        │  │ ‹tool.name›                    ‹status›      ‹ts›       │  │
│                                        │  └─────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────┴──────────────────────────────────────────────────────────────┘
```

---

## 2. Control map

| # | Control | Behavior | Live? |
|---|---|---|---|
| 1 | Attached tool list | `GET /api/v2/tools` → `tools[]` (`name`, `description`, `parameters`). Lazy-loaded on first open. | live |
| 2 | Show / Hide schema | Inline `<pre>` of the real `parameters` object. Only rendered when `parameters` is a non-empty object. | live |
| 3 | Live call log | Rows from `tool.*` WS frames via `toolLogFromFrames()`: `name` · `status` · `ts`. Session-scoped. | live |
| 4 | Enable / disable toggle | **Not in this surface today.** No toggle is drawn. | absent |
| 5 | Approval rules editor | **Not in this surface today.** | absent |

No tool is listed that the API did not return. No call appears that was not a real `tool.*` frame.

---

## 3. States

| State | Verbatim |
|---|---|
| idle / loading | “Loading tools…” |
| empty (list) | “No tools attached to this capsule.” |
| empty (log) | “No tool calls in this session yet.” |
| error | “Tools could not be loaded.” |
| denied | “You need `capability:read` to view tools.” |
| offline | Chrome offline banner; list + log keep last painted rows. |

No counts, charts, or metrics while loading. No fabricated timings.

---

## 4. Modal overlays

None. Schema expands inline (not a drawer). No invented overlay.

---

## 5. Navigation

| In | Out |
|---|---|
| Canvas tab **Tools** (registry order 2/8) | — (self-contained read surface) |

Cross-link: `SOMA-UI-NAV-001.md` §2 canvas · §5 acceptance.
**No Memory tab in the canvas.**

---

## 6. Honesty

- Tool rows and schema are the server’s `ToolInfo`. Empty `parameters` hides the schema button.
- Call-log `status` and `ts` come from the WS frame — never estimated.
- No enable/disable chrome while that capability is not on this surface.

---

## 7. Source map

| Source | Role |
|---|---|
| `webui/src/components/soma-right-panel.ts` | Registry + `_renderTools` + `toolLogFromFrames` |
| `GET /api/v2/tools` | `ToolsListResponse` `{tools, count}` |
| `ToolInfo` | `name`, `description?`, `parameters?` |
| `webui/src/services/websocket-client.ts` | `wsFrameLog` / `onWsFrame` → `tool.*` rows |

End of Document
