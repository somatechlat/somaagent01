# UI-S-02 — Brain / Cognitive (full route host)

Screen UI-S-02 · Routes: **`/cognitive`** · **`/training`** (`main.ts:271` → `soma-cognitive-panel`)
Chrome: **UI-S-00 thin** (abbrev) — own workspace chrome, no chat left-rail (`UI-S-00` §2)
Live view: `webui/src/views/soma-cognitive-panel.ts` (`soma-cognitive-panel`)
IA: `SOMA-UI-IA-001.md` §2.4 · Catalog: `SOMA-UI-CATALOG-001.md` §2 Brain

**Status: LIVE.**

## 0. One-home rule (binding)

**Brain has one UI: canvas surface UI-X-07.** This route mounts the **same**
`<soma-cognitive-panel>` as a full window. It is a second *host*, not a second Brain.

| Home | What it is | Count |
|---|---|---|
| **UI-X-07 canvas surface** | The Brain UI — **owns the field & control map** | **1** |
| `/cognitive` · `/training` (this file) | Same component, full route | same UI |
| Status-strip neuromod readout | Readout → opens UI-X-07 | not a UI |

**No third home.** Forbidden: left-rail Brain · welcome card · facet tab · a second neuromod
control set · an orphan Brain widget (`SOMA-UI-IA-001` §2.4).

**Control map and field map live in UI-X-07 and are not restated here** (anti-triplication).
This file documents only the route chrome, journey, and route-level states.

---

## 1. ASCII wireframe — full-route host (workspace chrome)

```
┌─ UI-S-00 chrome (thin · abbrev) ────────────────────────────────────────────────────────────────┐
│ [≡]  [S] SOMA              ‹clock›   ● ‹conn›   🔔 ‹n›   ▢ ‹project› ▾                          │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│  COGNITIVE / TRAINING — /cognitive · /training                        [Apply Changes]           │
│  (soma-cognitive-panel — same component as canvas UI-X-07)            ← Back to chat            │
│                                                                                                  │
│  ┌─ NEUROMODULATOR READINGS (raw) ────────────────────────────────────────────────────────────┐  │
│  │  DA ‹v›   5-HT ‹v›   NE ‹v›   ACh ‹v›    (raw values — no % meters: no min/max/unit/sync) │  │
│  └────────────────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                                  │
│  ┌─ ADAPTATION PARAMETERS ─────────────────┐  ┌─ MEMORY PARAMETERS ──────────────────────────┐  │
│  │ Learning Rate            ‹v›            │  │ Consolidation Rate           ‹v›             │  │
│  │ Exploration Rate         ‹v›            │  │ Emotional Sensitivity        ‹v›             │  │
│  │ Attention Span           ‹v›            │  └────────────────────────────────────────────┘  │
│  └──────────────────────────────────────────┘                                                    │
│                                                                                                  │
│  ┌─ ACTIVITY LOG ─────────────────────────────────────────────────────────────────────────────┐  │
│  │  ‹icon›  ‹message›                                                      ‹time›             │  │
│  └────────────────────────────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

Wireframe shows the **host** only. The component body (readouts, params, actions) is specified
once in **UI-X-07 §1–§3** — same pixels, same fields, same endpoints.

---

## 2. Real data

Specified once in **UI-X-07 §2** (fields) and **§3** (control map). Summary of the binding:

| Action | Endpoint |
|---|---|
| Read state | `GET /api/v2/somabrain/cognitive/state/{agent_id}` |
| Save params | `PATCH /api/v2/somabrain/cognitive/params/{agent_id}` |
| Sleep cycle | `POST /api/v2/somabrain/cognitive/sleep/{agent_id}` |
| Reset adaptation | `POST /api/v2/somabrain/cognitive/adaptation/reset/{agent_id}` |

Neuromodulators: **DA · 5-HT · NE · ACh — raw values only** (no fake % meters).
Not on this screen: model binding (Settings › Models, UI-S-51) · memory records (`/memory`, UI-S-04).

---

## 3. Numbered journey — full-route tune

| Step | Where | Action | API | Result |
|---|---|---|---|---|
| **1** | `/chat` status strip | Click the neuromod readout | opens **UI-X-07** (the canvas surface) | The one Brain UI opens in the canvas. |
| **2** | UI-X-07 | Click **open full route** | `router → /cognitive` | This screen — same component, full window. |
| **3** | `/cognitive` | Read neuromodulator values | `GET …/state/{agent_id}` | DA · 5-HT · NE · ACh raw. No meters. |
| **4** | `/cognitive` | Edit `learningRate` → **Apply Changes** | `PATCH …/params/{agent_id}` | Saved; activity-log row. |
| **5** | `/cognitive` | **Trigger Sleep Cycle** (dirty → confirm) | `POST …/sleep/{agent_id}` | “In flight (this session)” → Idle. |
| **6** | `/cognitive` | **Reset Adaptation** (confirm) | `POST …/adaptation/reset/{agent_id}` | Params reset. |
| **7** | `/cognitive` | ← Back to chat | `router → /chat` | Chat workspace. |

There is no step that opens a third Brain — status click → UI-X-07 → (optional) `/cognitive`.

---

## 4. States

Shared with UI-X-07 §5 (same component): loading · empty neuro · empty params (`—`) · error load ·
no agent · dirty · saving · save fail · offline.

Route-specific:

| State | Behavior |
|---|---|
| direct load `/cognitive` | Component runs its own state fetch; no agent → “No agent selected — cognitive state cannot be read.” |
| leave with dirty params | Warn only via the Reset/Sleep confirms — no separate route-guard modal. |

---

## 5. Modal overlays

Same as **UI-X-07 §6** (Reset confirm · Sleep-with-dirty confirm). No route-only modal.

---

## 6. Navigation

| In | Out |
|---|---|
| `/cognitive` · `/training` (`main.ts:271`) | ← Back to chat (`/chat`) |
| UI-X-07 **open full route** | Settings › Models (model binding — not Brain) |

**No left-rail Brain entry.** Band E neuromod readout opens UI-X-07, not this route.

---

## 7. Honesty

Identical to **UI-X-07 §7**: raw numbers · no `cognitiveLoad` · untyped dict shows only sent keys ·
no sliders without min/max · missing `agent_id` refuses the read.

---

## 8. Source map

| Source | Role |
|---|---|
| `webui/src/views/soma-cognitive-panel.ts` | The single Brain implementation (this route + UI-X-07) |
| **`UI-X-07-brain.md`** | Canonical field map, control map, wireframe body |
| `SOMA-UI-IA-001.md` §2.4 | Brain once · no third home |
| `webui/src/main.ts:271` | `/cognitive` · `/training` → `soma-cognitive-panel` |

End of Document
