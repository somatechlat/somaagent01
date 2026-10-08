# UI-S-12 — Capsule editor

Screen UI-S-12 · Subview of **`/admin/agents`** (`main.ts:258` → `soma-agents-view`) — open from UI-S-11
Chrome: **UI-S-00 thin** (abbrev) · Catalog: `SOMA-UI-CATALOG-001.md` §3 Capsule
Live: `GET/PATCH /api/v2/agents/{agent_id}/capsule` (`CapsuleConfigOut` / `CapsuleConfigUpdate`)

**Status: LIVE.** One capsule per agent. **`CapsuleConfigOut` fields only** —
`name` · `description` · `status` · `system_prompt` · `personality_traits` ·
`neuromodulator_baseline` · `learning_config` (`admin/agents/api/schemas.py:75-97`).

No `semver`, no `lifecycle`, no `capsule.document`, no YAML tabs, no publish pipeline — those are
not fields of `CapsuleConfigOut`/`CapsuleConfigUpdate` and are **not drawn**.

---

## 1. ASCII wireframe — capsule editor (workspace)

```
┌─ UI-S-00 chrome (thin · abbrev) ────────────────────────────────────────────────────────────────┐
│ [≡]  [S] SOMA              ‹clock›   ● ‹conn›   🔔 ‹n›   ▢ ‹project› ▾                          │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│  CAPSULE  ‹name›  ·  ‹capsule_id›  ·  ‹status›                    [Save] [Reset]  ← Back       │
│                                                                                                  │
│  ┌─ IDENTITY ────────────────────────────────────────────────────────────────────────────────┐  │
│  │  Name             [‹name›                              ]   ← name                         │  │
│  │  Description      [‹description | ›                   ]   ← description (optional)        │  │
│  │  Status           ‹status› (read-only — as stored)                                       │  │
│  └────────────────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                                  │
│  ┌─ SYSTEM PROMPT ───────────────────────────────────────────────────────────────────────────┐  │
│  │  ┌──────────────────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ ‹system_prompt›                                                                     │  │  │
│  │  └──────────────────────────────────────────────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                                  │
│  ┌─ PERSONALITY TRAITS (dict) ──────────────────┐  ┌─ NEUROMODULATOR BASELINE (dict) ───────┐  │
│  │  ‹key›            ‹value›                    │  │  DA ‹v›   5-HT ‹v›   NE ‹v›   ACh ‹v› │  │
│  │  ‹key›            ‹value›                    │  │  (raw numbers — no % meters)          │  │
│  │  (only keys the server sent)                 │  │  (only keys the server sent)          │  │
│  └──────────────────────────────────────────────┘  └────────────────────────────────────────┘  │
│                                                                                                  │
│  ┌─ LEARNING CONFIG (dict) ──────────────────────────────────────────────────────────────────┐  │
│  │  ‹key›            ‹value›                                                                 │  │
│  │  (only keys the server sent — untyped dict, no invented sliders)                          │  │
│  └────────────────────────────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Real data — fields & endpoints

| UI block | API field | Type | Editable |
|---|---|---|---|
| Name | `name` | `str` | PATCH |
| Description | `description` | `Optional[str]` | PATCH |
| Status | `status` | `str` | read-only (out) |
| System prompt | `system_prompt` | `str` | PATCH |
| Personality traits | `personality_traits` | `dict` | PATCH (keys as sent) |
| Neuromodulator baseline | `neuromodulator_baseline` | `dict` | PATCH (keys as sent) |
| Learning config | `learning_config` | `dict` | PATCH (keys as sent) |
| Capsule id | `capsule_id` | `str` | read-only |
| Agent id | `agent_id` | `str` | read-only (path) |

| Action | Endpoint | Payload |
|---|---|---|
| Read | `GET /api/v2/agents/{agent_id}/capsule` | — → `CapsuleConfigOut` |
| Save | `PATCH /api/v2/agents/{agent_id}/capsule` | `CapsuleConfigUpdate` (only changed keys) → `{agent_id, capsule_id, updated}` |

Dict fields are **untyped server dicts** — render only keys the server sent. Never invent
min/max/step, never draw sliders without a declared scale.

---

## 3. Control map

| # | Control | API / behavior | Live? |
|---|---|---|---|
| 1 | Name / Description | Text inputs → `name` · `description`. | live |
| 2 | Status | Read-only `status`. | live |
| 3 | System prompt | Textarea → `system_prompt`. | live |
| 4 | Personality traits | Key/value rows from `personality_traits`. | live |
| 5 | Neuromodulator baseline | Key/value rows from `neuromodulator_baseline`. Raw numbers. | live |
| 6 | Learning config | Key/value rows from `learning_config`. | live |
| 7 | Save | `PATCH …/capsule` with changed keys only. Disabled until dirty. | live |
| 8 | Reset | Re-fetch `GET …/capsule`; discards dirty edits (confirm). | live |
| 9 | ← Back | `router →` UI-S-11. | live |

---

## 4. Numbered journey — edit and save a capsule

| Step | Where | Action | API | Result |
|---|---|---|---|---|
| **1** | UI-S-11 | Click **Open** on a row | `router →` UI-S-12 | Editor loads that agent’s capsule. |
| **2** | editor | `GET …/capsule` | `GET /api/v2/agents/{agent_id}/capsule` | Real `CapsuleConfigOut` fields fill the form. |
| **3** | editor | Change `name` / `system_prompt` | — | Dirty → **Save** enabled. |
| **4** | editor | Click **Save** | `PATCH …/capsule` | `{updated: true}`; dirty cleared. |
| **5** | editor | Edit a dict key’s value → **Save** | `PATCH …/capsule` | Dict persisted as sent. |
| **6** | editor | **Reset** with dirty edits | confirm → `GET …/capsule` | Edits discarded; form reverts. |
| **7** | editor | ← Back | `router →` UI-S-11 | List. |

---

## 5. States

| State | Verbatim / behavior |
|---|---|
| loading | “Loading capsule…” — skeleton fields. |
| 404 | “Capsule could not be loaded. It may have been deleted.” |
| empty dict block | “This section is empty. Add the keys this capsule needs.” (only for editable dicts) |
| dirty | **Save** enabled; Reset asks to discard. |
| saving | Button “Saving…”; inputs stay as typed. |
| save fail | “Draft was not saved. Your edits are still here — try again.” |
| permission-denied | Read-only; “Editing requires the capsule-editor role.” |
| offline | Save/Reset disabled: “Saving is unavailable offline.” |

---

## 6. Modal overlays

| Trigger | Modal | Contents |
|---|---|---|
| Reset with dirty edits | UI-M-03 | “Discard unsaved edits?” Cancel / Discard. |
| — | UI-M-01 / UI-M-02 | Not used by this screen. |

---

## 7. Honesty

Only `CapsuleConfigOut` / `CapsuleConfigUpdate` fields render. No version rail here (that is
UI-S-13, **GATED**), no publish step, no invented validation schema. Missing keys show `—` / empty,
never a default guess.

---

## 8. Source map

| Source | Role |
|---|---|
| `GET/PATCH /api/v2/agents/{agent_id}/capsule` | Read/update (`core.py:556-612`) |
| `admin/agents/api/schemas.py:75-97` | `CapsuleConfigOut` · `CapsuleConfigUpdate` |
| `SOMA-UI-CATALOG-001.md` §3 | Real capsule fields |

End of Document
