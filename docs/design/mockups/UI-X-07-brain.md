# UI-X-07 — Brain (the one Brain surface)

Surface **UI-X-07 Brain** · Right canvas (Band D) · Chrome: **UI-S-00 thin** (abbrev)
Registry: `webui/src/components/soma-right-panel.ts` → `SURFACES` key `brain`
Backing (live): `<soma-cognitive-panel>` — the **same component** as screen UI-S-02
IA: `SOMA-UI-IA-001.md` §2.4 · Catalog: `SOMA-UI-CATALOG-001.md` §3 Brain

**Status: LIVE.** Present and available. No `blockedReason`.

## 0. One-home rule (binding)

**Brain appears exactly once as a UI** — this canvas surface. `/cognitive` (UI-S-02) mounts the
same `soma-cognitive-panel` as a full route; it is a second *host*, not a second Brain.

| Home | What it is | Count |
|---|---|---|
| **UI-X-07 canvas surface** | The Brain UI | **1** |
| `/cognitive` · `/training` (UI-S-02) | Same component, full route | same UI |
| Status-strip neuromod readout (Band E) | Readout → opens **this surface** | not a UI |

**No third home.** Forbidden: left-rail Brain · welcome card · facet tab · a second neuromod
control set · an orphan Brain widget anywhere else (`SOMA-UI-IA-001` §2.4).

**This file owns the Brain field & control map** (real API fields). UI-S-02 references it and adds
only route chrome — the control map is not restated there.

---

## 1. ASCII wireframe — docked in the canvas

```
┌─ UI-S-00 chrome (thin · abbrev) ────────┬ RIGHT CANVAS · UI-X-07 Brain                          ┐
│ [≡] [S] SOMA  ‹clock› ● ‹conn› 🔔 ▢      │ [Files][Tools][Browser†][Editor]                      │
│                                         │ [Debug][Capsule][🧠 Brain][Desktop†]                  │
│  C · chat workspace (UI-S-07)           ├───────────────────────────────────────────────────────┤
│  (one screen owns the workspace)        │  Brain  UI-X-07     (soma-cognitive-panel)            │
│                                         │                                                        │
│                                         │  ┌─ NEUROMODULATOR READINGS (raw) ──────────────────┐ │
│                                         │  │  DA ‹v›   5-HT ‹v›   NE ‹v›   ACh ‹v›           │ │
│                                         │  │  (raw server numbers — no % meters: the API      │ │
│                                         │  │   sends no min/max/unit and no sync timestamp)   │ │
│                                         │  └────────────────────────────────────────────────┘ │
│                                         │                                                        │
│                                         │  ┌─ ADAPTATION PARAMS ─────┐ ┌─ MEMORY PARAMS ────┐ │
│                                         │  │ learningRate        ‹v› │ │ memoryConsolidation ‹v›│
│                                         │  │ explorationRate     ‹v› │ │ emotionalSensitivity ‹v›│
│                                         │  │ attentionSpan       ‹v› │ └────────────────────────┘
│                                         │  └──────────────────────────┘                         │
│                                         │                                                        │
│                                         │  [Trigger Sleep Cycle] [Reset Adaptation] [Apply]     │
│                                         │                                                        │
│                                         │  ┌─ ACTIVITY LOG ──────────────────────────────────┐ │
│                                         │  │  ‹icon›  ‹message›                       ‹time› │ │
│                                         │  └────────────────────────────────────────────────┘ │
│                                         │                                                        │
│                                         │  [ open full route → /cognitive (UI-S-02) ]           │
└─────────────────────────────────────────┴────────────────────────────────────────────────────────┘
```

† GATED surfaces show their blocking reason inline. **No Memory tab** — Memory is `/memory` only.

---

## 2. Real data — fields & endpoints

Neuromodulators come from `GET /api/v2/somabrain/cognitive/state/{agent_id}` → `neuromodulators`
flat `name → number`: **DA · 5-HT · NE · ACh — raw values only.** The API sends no min/max/unit and
no sync timestamp, so **percentage meters are never drawn** (REQ-UIX-010).

| Field | Source key | Absent handling |
|---|---|---|
| Neuromodulator readings | `neuromodulators` (flat dict) | “No neuromodulator readings were reported.” |
| Learning Rate | `adaptation_params.learningRate` | `—` (never `0`) |
| Exploration Rate | `adaptation_params.explorationRate` | `—` |
| Attention Span | `adaptation_params.attentionSpan` | `—` |
| Consolidation Rate | `adaptation_params.memoryConsolidation` | `—` |
| Emotional Sensitivity | `adaptation_params.emotionalSensitivity` | `—` |
| SomaBrain status | `state/{agent_id}` returns → Connected | Unavailable |
| Sleep trigger | session-local (Idle · In flight) | — |

AdaptationParams is an **untyped server dict** — only keys the server sent are shown. No declared
min/max/step ⇒ **number inputs, never sliders** (a slider would invent a scale).

**Not drawn (not served by the Cognitive API):** model provider selects · embedding dim · context
window · recall strategy · derived AgentIQ block · eval readout · `cognitiveLoad` (not a field).
Model binding lives in Settings › Models (UI-S-51). Memory records live only at `/memory` (UI-S-04).

### Endpoints

| Action | Endpoint |
|---|---|
| Read state | `GET /api/v2/somabrain/cognitive/state/{agent_id}` |
| Save params | `PATCH /api/v2/somabrain/cognitive/params/{agent_id}` |
| Sleep cycle | `POST /api/v2/somabrain/cognitive/sleep/{agent_id}` |
| Reset adaptation | `POST /api/v2/somabrain/cognitive/adaptation/reset/{agent_id}` |

---

## 3. Control map (canonical — shared with UI-S-02)

| # | Control | API / behavior | Live? |
|---|---|---|---|
| 1 | Neuromodulator readouts | Raw `name → number`. **No meters** (REQ-UIX-010). | live |
| 2 | Adaptation parameters | Number inputs; missing key → `—`. | live |
| 3 | Memory parameters | Number inputs; missing key → `—`. | live |
| 4 | Apply Changes | `PATCH …/params/{agent_id}` with the typed dict. Disabled until dirty. | live |
| 5 | Trigger Sleep Cycle | `POST …/sleep/{agent_id}`. Status “In flight (this session)” while running. | live |
| 6 | Reset Adaptation | `POST …/adaptation/reset/{agent_id}`. | live |
| 7 | SomaBrain status | Connected when state returns; else Unavailable. | live |
| 8 | Activity log | Client log of real actions (save / sleep / reset / load failure). No synthetic rows. | live |
| 9 | Open full route | `router → /cognitive` (UI-S-02). Escape hatch — not a second editor. | nav |

Status-strip neuromod values (Band E) are a **readout of the same API** — they never edit params.

---

## 4. Numbered journey — open Brain, tune, sleep

| Step | Where | Action | API | Result |
|---|---|---|---|---|
| **1** | `/chat` | Click canvas tab **Brain** | registry mounts `<soma-cognitive-panel>` | This surface opens (lazy-mounted). |
| **2** | Surface | Read neuromodulator values | `GET …/state/{agent_id}` | DA · 5-HT · NE · ACh as raw numbers. No meters. |
| **3** | Surface | Change `learningRate` | — | Input dirty → **Apply Changes** enabled. |
| **4** | Surface | Click **Apply Changes** | `PATCH …/params/{agent_id}` | Saved; log row; button disables again. |
| **5** | Surface | Click **Trigger Sleep Cycle** (with dirty params) | confirm → `POST …/sleep/{agent_id}` | “In flight (this session)” → Idle; log row. |
| **6** | Surface | Click **Reset Adaptation** | confirm → `POST …/adaptation/reset/{agent_id}` | Params reset; log row. |
| **7** | Band E | Click status-strip neuromod readout | opens **this same surface** | Not a third Brain — the same UI-X-07. |
| **8** | Surface | Click **open full route** | `router → /cognitive` | UI-S-02 — same component, full window. |

---

## 5. States

Identical to the shared component (UI-S-02 hosts the same `soma-cognitive-panel`):

| State | Verbatim / behavior |
|---|---|
| loading | Spinner over the content region. No skeleton values painted. |
| empty (neuro) | “No neuromodulator readings were reported.” |
| empty (params) | Value shows `—`; input accepts a number. Never pre-filled with a guess. |
| error (load) | “Failed to load cognitive state. No values are shown.” |
| no agent | Log row: “No agent selected — cognitive state cannot be read.” SomaBrain → Unavailable. |
| dirty | **Apply Changes** enabled; header reflects unsaved edits. |
| saving | Button label “Saving…”; inputs stay as typed. |
| save fail | Log row with error icon; values stay dirty. Nothing pretends to save. |
| offline | Sleep/reset disabled with inline reason. Last painted readings remain. |

Canvas-specific: the surface is lazy-mounted with the dock; unmounting does not cancel an in-flight save.

---

## 6. Modal overlays

| Trigger | Modal | Contents |
|---|---|---|
| Reset Adaptation | UI-M-03 Dialog | “Reset adaptation parameters?” Cancel / Reset (destructive). |
| Trigger Sleep Cycle with dirty params | UI-M-03 Dialog | “Run sleep cycle with unsaved parameter changes?” Cancel / Run. |
| — | UI-M-01 / UI-M-02 | Not used by this screen. |

---

## 7. Honesty

- Neuromodulator values are raw server numbers, not percentages.
- `cognitiveLoad` is not a field — a 0% load would be invented and is not drawn.
- AdaptationParams is an untyped server dict; only keys the server sent are shown.
- No min/max/unit means no sliders and no gauges.
- Missing `agent_id` refuses the read rather than inventing a path.
- Model role bindings are not drawn here (Settings › Models, UI-S-51) — an unbound role is never shown as a model id.

---

## 8. Source map

| Source | Role |
|---|---|
| `webui/src/components/soma-right-panel.ts` | Embeds `<soma-cognitive-panel>` |
| `webui/src/views/soma-cognitive-panel.ts` | The single Brain implementation |
| `GET/PATCH /api/v2/somabrain/cognitive/…` | State · params · sleep · reset |
| `SOMA-UI-IA-001.md` §2.4 | Brain = one surface · status click → same surface |
| `SOMA-UI-CATALOG-001.md` §3 | Neuromod = raw values only |

End of Document
