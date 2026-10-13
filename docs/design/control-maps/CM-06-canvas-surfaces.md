# CM-06 — Canvas Surfaces Control Map (UI-X-01…08)

## Document Control

| Field | Value |
|---|---|
| Document Title | Control Map — Right canvas surface rail (UI-X-01…UI-X-08) |
| Document Identifier | SOMA-UI-CM-06 |
| Version | 1.0.0 |
| Date | 2026-10-13 |
| Status | Draft |
| Author | SomaTech Engineering (soma-ui-engineer) |
| Classification | Internal |
| ISO Reference | ISO 9241-210:2019 |
| Next Review | 2027-01-13 |
| Related | `SOMA-UI-BINDINGS-001.md` §1 right-rail · `UI-X-01`…`UI-X-08` mockups · `SOMA-UI-MODULE-CATALOG-001.md` M-025…M-028 |
| Live source | `webui/src/components/soma-right-panel.ts` (`SURFACES` registry, `_renderRailButton`, surface hosts) |
| Law | Present-but-disabled with `blockedReason` (REQ-UIX-020). No Memory tab. Honest gates only. |

## Revision History

| Version | Date | Author | Description |
|---|---|---|---|
| 1.0.0 | 2026-10-13 | soma-ui-engineer | Full rail + per-surface control map with GATED reasons copied from code. |

---

## 1. ASCII wireframe

```
┌─ right canvas (Band D) ────────────────────────────────────────────────────────────────────────┐
│ X-00 tab-rail: [📁 Files][🔧 Tools][🌐 Browser†][💻 Editor][🐞 Debug][📦 Capsule][🧠 Brain][🖥 Desktop†] │
│ † GATED — still on the rail with reason (tooltip + disabled)                                    │
├────────────────────────────────────────────────────────────────────────────────────────────────┤
│  <active surface host>                                                                          │
│  X-01…X-08 controls per surface (tables below)                                                  │
└────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Surface registry (from code)

| Key | ID | Icon | Label | blockedReason (verbatim) | Status |
|---|---|---|---|---|---|
| files | UI-X-01 | folder | Files | — | LIVE |
| tools | UI-X-02 | construction | Tools | — | LIVE |
| browser | UI-X-03 | public | Browser | “Bind a browser model on UI-S-02 first” | GATED |
| editor | UI-X-04 | code | Editor | — | LIVE (RO) |
| debug | UI-X-05 | bug_report | Debug | — | LIVE |
| capsule | UI-X-06 | medication | Capsule | — | LIVE |
| brain | UI-X-07 | neurology | Brain | — | LIVE |
| desktop | UI-X-08 | desktop_windows | Desktop | “Requires a remote-desktop capability in somaAgent01. Not available today.” | GATED |

---

## 3. Control map — rail + chrome

| ID | Label | Type | Binding / API | States | Disabled reason | A11y | Status |
|---|---|---|---|---|---|---|---|
| X-00 | Surface tab-rail | tabs | local `active` surface key | default | — | `tablist` aria-label “Right-rail surfaces” | LIVE |
| X-00a | Rail button (enabled) | tabs | `_selectTab(s.key)` | active, inactive | — | `tab` aria-label = label | LIVE |
| X-00b | Rail button (gated) | tabs | select shows reason panel | disabled | verbatim `blockedReason` | `tab` aria-disabled + title = reason | GATED |
| X-00c | Canvas open/collapse | surface | host open state | open, collapsed | — | region | LIVE |
| X-00d | Surface change event | — | `soma-surface-change` `{key}` | — | — | CustomEvent | LIVE |

---

## 4. UI-X-01 Files

| ID | Label | Type | Binding / API | States | Disabled reason | A11y | Status |
|---|---|---|---|---|---|---|---|
| X01-01 | File rows | list-row | `GET /api/v2/filesv2/` | loading, empty, error | — | list (detail in CM-02) | LIVE |
| X01-02 | Open in editor | list-row action | download-url → UI-X-04 | default | — | operable row | LIVE |
| X01-03 | showing N of total | readout | `total` | conditional | — | text | LIVE |
| X01-05 | Retry | button | reload | error | — | aria-label “Retry listing files” | LIVE |

---

## 5. UI-X-02 Tools

| ID | Label | Type | Binding / API | States | Disabled reason | A11y | Status |
|---|---|---|---|---|---|---|---|
| X02-01 | Tool list | list-row | `GET /tools` `{tools[ToolInfo], count}` | loading, empty, error | — | list | LIVE |
| X02-02 | Schema expand | button | local over `parameters` | collapsed, expanded | — | aria-expanded | LIVE |
| X02-03 | Live tool ring buffer | readout | WS `tool.call` / `tool.done` | streaming | — | `log` | LIVE |
| X02-04 | Tool filter | input.search | local filter | idle | — | `searchbox` | PLANNED |
| X02-05 | Run tool (manual) | button | target tool execute API | default | Manual invoke not exposed → “Manual tool invoke is not exposed on this deployment.” | `button` | PLANNED |

---

## 6. UI-X-03 Browser (GATED)

| ID | Label | Type | Binding / API | States | Disabled reason | A11y | Status |
|---|---|---|---|---|---|---|---|
| X03-01 | Browser surface host | surface | — | gated | “Bind a browser model on UI-S-02 first” | `region` + reason | GATED |
| X03-02 | URL bar | input.text | Playwright container (future) | disabled | same | disabled + reason | PLANNED |
| X03-03 | Navigate / click / type / screenshot | button | container-only Playwright (never host Chrome) | disabled | same | disabled + reason | PLANNED |
| X03-04 | Browser model bind hint | readout | links UI-S-02 Models | default | — | `link` | LIVE (hint) |

---

## 7. UI-X-04 Editor

| ID | Label | Type | Binding / API | States | Disabled reason | A11y | Status |
|---|---|---|---|---|---|---|---|
| X04-01 | Editor buffer | textarea/code | signed download body (RO) | loading, readonly | — | `textbox` readonly | LIVE |
| X04-02 | Save | button | target `PUT /api/v2/filesv2/{id}/content` (**NEW**) | disabled | SAVE_DISABLED_REASON (code constant): content write API not mounted | aria-label “Save — disabled. {reason}” | GATED |
| X04-03 | Download | button | signed URL | default | — | `button` | LIVE |
| X04-04 | Close / back to list | button | local surface switch | default | — | `button` | LIVE |
| X04-05 | Language chip | readout | mime | default | — | text | LIVE |
| X04-06 | Dirty indicator | readout | local | clean, dirty | — | status | PLANNED |

---

## 8. UI-X-05 Debug

| ID | Label | Type | Binding / API | States | Disabled reason | A11y | Status |
|---|---|---|---|---|---|---|---|
| X05-01 | Frame filter | input.search | local over `wsFrameLog` | idle | — | aria-label “Filter frames” | LIVE |
| X05-02 | Clear stream | button | local clear | default | — | `button` | LIVE |
| X05-03 | Frame log | list-row | WS frames `{id, type, dir, ts, payload}` | streaming | — | `log` aria-label “WebSocket frames” | LIVE |
| X05-04 | Frame detail expand | button | local | collapsed | — | aria-expanded | LIVE |
| X05-05 | Export frames | button | client Blob | default | — | `button` | PLANNED |

---

## 9. UI-X-06 Capsule

| ID | Label | Type | Binding / API | States | Disabled reason | A11y | Status |
|---|---|---|---|---|---|---|---|
| X06-01 | Capsule editor | surface | `GET /agents/{id}/capsule` | loading, empty, error | — | region | LIVE |
| X06-02 | Save | button | `PATCH /agents/{id}/capsule` | dirty, busy | — | `button` | LIVE |
| X06-03 | Reload | button | GET capsule | default | — | `button` | LIVE |
| X06-04 | Export | button | client export | default | — | `button` | LIVE |
| X06-05 | Archive | button | `POST /agents/{id}/archive` | confirm | — | `button` danger | LIVE |
| X06-06 | Soul / Learning tabs | tabs | local | active | — | `tab` | LIVE |
| X06-07 | Version diff rail | surface | capsule versions API | default | Not shipped → “Version diff ships with capsule history API.” | region | PLANNED |

---

## 10. UI-X-07 Brain

| ID | Label | Type | Binding / API | States | Disabled reason | A11y | Status |
|---|---|---|---|---|---|---|---|
| X07-01 | Cognitive panel | surface | **same component** as `/cognitive` (not a second Brain UI) | loading, error | — | region | LIVE |
| X07-02… | (all SB-* from CM-04) | — | see CM-04 | — | — | — | LIVE |

---

## 11. UI-X-08 Desktop (GATED)

| ID | Label | Type | Binding / API | States | Disabled reason | A11y | Status |
|---|---|---|---|---|---|---|---|
| X08-01 | Desktop surface host | surface | — | gated | “Requires a remote-desktop capability in somaAgent01. Not available today.” | `region` + reason | GATED |
| X08-02 | Connect / session | button | remote-desktop capability (future) | disabled | same | disabled + reason | PLANNED |
| X08-03 | Screenshot / input | button | same | disabled | same | disabled + reason | PLANNED |

---

## 12. Cross-surface laws

| Law | Enforcement |
|---|---|
| No Memory tab in canvas | Registry has 8 keys; Memory is `/memory` only |
| Gated surfaces stay on rail | `blockedReason` present → `aria-disabled` + title |
| One Brain UI | UI-X-07 mounts `soma-cognitive-panel` |
| Files is list-only today | No invented tree/upload (CM-02) |
| Editor Save honest gate | disabled + SAVE_DISABLED_REASON |

---

## 13. Source map

| Source | Role |
|---|---|
| `webui/src/components/soma-right-panel.ts` | `SURFACES`, rail, files/tools/browser/editor/debug/capsule/brain/desktop hosts |
| `webui/src/components/soma-capsule-editor.ts` | UI-X-06 |
| `webui/src/views/soma-cognitive-panel.ts` | UI-X-07 |
| `webui/src/services/websocket-client.ts` | UI-X-05 frame log |

End of Document
