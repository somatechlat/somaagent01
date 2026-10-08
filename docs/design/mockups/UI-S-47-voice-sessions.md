# UI-S-47 — Voice sessions (run surface)

Screen UI-S-47 · Routes: **`/voice/sessions`** · **`/platform/voice/sessions`**
(`main.ts:401` → `soma-voice-sessions`)
Chrome: **UI-S-00 thin** (abbrev) · Catalog: `SOMA-UI-CATALOG-001.md` §2 Voice
Live view: `webui/src/views/soma-voice-sessions.ts` (`soma-voice-sessions`)

**Status: LIVE — run surface only.**

> **Voice config home = Settings › Voice (UI-S-48-settings-voice) ONLY** (DUP-6).
> This screen lists past voice runs. It holds **no persona editor** — management lives in
> Settings › Voice.

---

## 1. ASCII wireframe — voice sessions workspace

```
┌─ UI-S-00 chrome (thin · abbrev) ────────────────────────────────────────────────────────────────┐
│ [≡]  [S] SOMA              ‹clock›   ● ‹conn›   🔔 ‹n›   ▢ ‹project› ▾                          │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│  VOICE SESSIONS          filter: [state ▾]  window: [24h][7d][custom]          [⟳ Refresh]      │
│                                                                                                  │
│  ┌─ SESSION TABLE (server order) ────────────────────────────────────────────────────────────┐  │
│  │  session id        persona           state            started           duration          │  │
│  │  ‹id›              ‹name | —›        ‹state›          ‹ts›              ‹dur | —›         │  │
│  │  ‹id›              ‹name | —›        ‹state›          ‹ts›              ‹dur | —›         │  │
│  │  (scroll)                                                              [open] [Delete…]   │  │
│  └────────────────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                                  │
│  page ‹n› of ‹n | —›                                    [prev] [next]                            │
│                                                                                                  │
│  Note: session rows come from the voice session API.                                             │
│  No session is drawn that the API did not return.                                                │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

No facet tabs, no surface rail, no IQ/AUTO/BUDGET knobs, no instance strip (`UI-S-00` §3).

---

## 2. Real data

| UI field | Source | Absent handling |
|---|---|---|
| session id | session record | required |
| persona | session record (`name`) | `—` |
| state | session record | as stored |
| started | session record | `—` |
| duration | session record | `—` |
| page / total | list response | `—` (never `0` on failure) |

| Action | Endpoint / behavior |
|---|---|
| List | voice session API (filter by state · window) |
| Open | UI-M-01 drawer — session detail / transcript |
| Delete | UI-M-03 confirm → voice session API |

---

## 3. Control map

| # | Control | API / behavior | Live? |
|---|---|---|---|
| 1 | State filter | Filters on real session states the API reports. | live |
| 2 | Time window | `24h` · `7d` · `custom` — passed to the API as-is. | live |
| 3 | Session row | `id` · `persona` · `state` · `started` · `duration`. | live |
| 4 | Open | UI-M-01 drawer with detail / transcript. | live |
| 5 | Delete… | UI-M-03 confirm (destructive). Disabled with reason without voice-admin. | live |
| 6 | Pagination | Disabled when the API reports no further page. | live |
| 7 | Refresh | Re-fetch the list. | live |

---

## 4. Numbered journey — find and inspect a past run

| Step | Where | Action | API | Result |
|---|---|---|---|---|
| **1** | `/voice/sessions` | Screen loads | voice session API | Session rows paint. |
| **2** | sessions | Filter by `state` / pick a window | voice session API | Table narrows. |
| **3** | sessions | Click **open** on a row | — | UI-M-01 drawer with detail / transcript. |
| **4** | sessions | **Delete…** → confirm | UI-M-03 → voice session API | Row removed. |
| **5** | sessions | **Next** page | voice session API | More rows, or button disabled. |
| **6** | sessions | Need to **manage** personas | — | **Settings › Voice** (UI-S-48-settings-voice) — never here (DUP-6). |

---

## 5. States

| State | Verbatim / behavior |
|---|---|
| loading | “Loading voice sessions…” — skeleton rows. |
| empty | “No voice sessions in this window.” |
| error | “Couldn’t load voice sessions. ‹ reason from API ›” |
| permission-denied | “You don’t have access to voice sessions. Requires the voice-user role.” |
| delete denied | Delete disabled: “Requires the voice-admin role.” |
| offline | “You’re offline. Session data may be stale.” |

---

## 6. Modal overlays

| Trigger | Modal | Contents |
|---|---|---|
| Open row | UI-M-01 Drawer | Session detail (transcript, timing, persona used). |
| Delete… | UI-M-03 | “Delete voice session ‹id›?” Cancel / Delete (destructive). |

---

## 7. Honesty

Rows are session-record fields only. No invented utterances, durations, or counts. Persona CRUD is
**not** duplicated here (DUP-6).

---

## 8. Source map

| Source | Role |
|---|---|
| `webui/src/main.ts:401` | `/voice/sessions` · `/platform/voice/sessions` → `soma-voice-sessions` |
| `webui/src/views/soma-voice-sessions.ts` | Live run surface |
| `UI-S-48-settings-voice.md` | The one voice **config** home (DUP-6) |

End of Document
