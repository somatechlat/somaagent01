# UI-X-06 — Capsule

Surface **UI-X-06 Capsule** · Right canvas (Band D) · Facet: Surface · Chrome: UI-S-00 abbreviated
Registry: `webui/src/components/soma-right-panel.ts` → `SURFACES` key `capsule`
Backing (live): `<soma-capsule-editor>` — `GET` / `PATCH /agents/{agent_id}/capsule`
Nav: `SOMA-UI-NAV-001.md` §2 canvas · Capsule screens UI-S-11…14

**Status: LIVE.** Present and available. No `blockedReason`.

---

## 1. ASCII wireframe — docked in the canvas

```
┌─ chrome (abbrev) ──────────────────────┬ RIGHT CANVAS · UI-X-06 Capsule                                ┐
│  chat workspace (UI-S-07)              │ [📁 Files][🔧 Tools][🌐 Browser†][💻 Editor]                  │
│  ┌────────────────────────────────┐    │ [🐞 Debug][📦 Capsule][🧠 Brain][🖥 Desktop†]                  │
│  │ screen content in context      │    ├──────────────────────────────────────────────────────────────┤
│  │ surface rail select: Capsule   │    │  Capsule  UI-X-06                                            │
│  └────────────────────────────────┘    │  [ Soul ] [ Learning ]                    [Save] [Reset]     │
│                                        │                                                                │
│                                        │  ┌─ Soul tab ──────────────────────────────────────────────┐  │
│                                        │  │  system_prompt                                         │  │
│                                        │  │  ‹system_prompt›                                       │  │
│                                        │  │                                                          │  │
│                                        │  │  personality_traits                                    │  │
│                                        │  │  ‹key›  [number input ‹value›]                         │  │
│                                        │  │  …  (or: “This capsule stores no personality traits.”) │  │
│                                        │  │                                                          │  │
│                                        │  │  neuromodulator_baseline                               │  │
│                                        │  │  ‹key›  [number input ‹value›]                         │  │
│                                        │  └─────────────────────────────────────────────────────────┘  │
│                                        │                                                                │
│                                        │  ┌─ Learning tab ─────────────────────────────────────────┐  │
│                                        │  │  learning_config (free-form JSON)                      │  │
│                                        │  │  ‹server object›                                       │  │
│                                        │  └─────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────┴──────────────────────────────────────────────────────────────┘
```

---

## 2. Control map

| # | Control | API / behavior | Live? |
|---|---|---|---|
| 1 | Tab: Soul | `system_prompt` · `personality_traits` · `neuromodulator_baseline` — the PERSONALITY fields the API stores. | live |
| 2 | Tab: Learning | `learning_config` — free-form JSON object; no invented schema. | live |
| 3 | system_prompt | Text area bound to the server string. | live |
| 4 | personality_traits rows | One number input per **server-sent key**. Empty → “This capsule stores no personality traits.” | live |
| 5 | neuromodulator_baseline rows | One number input per server-sent key. | live |
| 6 | Save | `PATCH /agents/{agent_id}/capsule` with the four fields. Disabled until dirty. | live |
| 7 | Reset | Restores buffers from the last `GET` response. | live |

**Not on this surface (honest omissions):** version rail, checksum, lifecycle chips, archive, instance rows, five-tab Soul/Body/Hands/Memory/Governance fiction — those are not what `CapsuleConfigOut` serves and are not drawn. Identity/capsule list lives in UI-S-11…14.

---

## 3. States

| State | Verbatim / behavior |
|---|---|
| loading | Spinner in the surface body. |
| empty (traits) | “This capsule stores no personality traits.” |
| error (load) | Surface error text; no fake defaults. |
| dirty | Save enabled. |
| saving | Save disabled; no optimistic flash of unconfirmed values. |
| no agent | Editor cannot bind `agent_id` — shows the missing-selection reason, not a guess. |

---

## 4. Modal overlays

| Trigger | Modal | Contents |
|---|---|---|
| Reset with dirty buffers | UI-M-03 | “Discard unsaved capsule changes?” Cancel / Discard. |

---

## 5. Navigation

| In | Out |
|---|---|
| Canvas tab **Capsule** (registry order 6/8) | UI-S-11…14 Capsule list/detail (full capsule IA) |

Cross-link: `SOMA-UI-NAV-001.md` §2 canvas · §5 acceptance.
**No Memory tab in the canvas** — Memory records are UI-S-04 only.

---

## 6. Honesty

- Only the four PERSONALITY fields the API classifies are edited (`admin/core/helpers/capsule_settings.py`).
- Keys come from the server object; nothing is pre-seeded.
- A previous five-tab version with invented model names, recall limits, and a fake “Certified (Ed25519)” claim is gone — not kept as decoration.

---

## 7. Source map

| Source | Role |
|---|---|
| `webui/src/components/soma-capsule-editor.ts` | Live editor (embedded by `soma-right-panel`) |
| `GET /agents/{agent_id}/capsule` | `CapsuleConfigOut` |
| `PATCH /agents/{agent_id}/capsule` | `CapsuleConfigUpdate` |
| `CapsuleConfig` | `agent_id, capsule_id, name, description, status, system_prompt, personality_traits, neuromodulator_baseline, learning_config` |

End of Document
