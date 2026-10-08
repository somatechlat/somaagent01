# UI-S-46 — Voice chat (run surface)

Screen UI-S-46 · Routes: **`/voice`** · **`/voice/chat`** · **`/platform/voice/chat`**
(`main.ts:407` → `soma-voice-chat`)
Chrome: **UI-S-00 thin** (abbrev) · Catalog: `SOMA-UI-CATALOG-001.md` §2 Voice
Live view: `webui/src/views/soma-voice-chat.ts` (`soma-voice-chat`)

**Status: LIVE — run surface only.**

> **Voice config home = Settings › Voice (UI-S-48-settings-voice) ONLY** (DUP-6).
> This screen is where a voice run happens. It is **not** a persona library and holds **no config
> editor** — create/edit/default/delete live only in Settings › Voice.

---

## 1. ASCII wireframe — voice run workspace

```
┌─ UI-S-00 chrome (thin · abbrev) ────────────────────────────────────────────────────────────────┐
│ [≡]  [S] SOMA              ‹clock›   ● ‹conn›   🔔 ‹n›   ▢ ‹project› ▾                          │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│  VOICE CHAT          persona: [‹persona.name› ▾]   [End session]         ← Back to chat        │
│                       ▲ pick only — manage in Settings › Voice (UI-S-48-settings-voice)          │
│                                                                                                  │
│  ┌─ TRANSCRIPT ──────────────────────────────────────────────────────────────────────────────┐  │
│  │  you   : ‹utterance›                                                   ‹ts›               │  │
│  │  agent : ‹utterance›                                                   ‹ts›               │  │
│  │  you   : ‹utterance›                                                   ‹ts›               │  │
│  └────────────────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                                  │
│  mic state: [ idle | listening | thinking | speaking ]                                            │
│  ┌─ level meter (drawn only while the mic is open) ──────────────────────────────────────────┐  │
│  │  ‹ live level ›                                                                            │  │
│  └────────────────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                                  │
│  [Hold to talk]   [Mute]   [Type instead]                                                        │
│                                                                                                  │
│  ┌─ TEXT COMPOSER (fallback) ────────────────────────────────────────────────────────────────┐  │
│  │  [type a message…                                              ] [Send]                    │  │
│  └────────────────────────────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

No facet tabs, no surface rail, no IQ/AUTO/BUDGET knobs, no instance strip, no chat left rail
(`UI-S-00` §3). Persona management is **not** on this screen.

---

## 2. Real data

| UI element | Source | Absent handling |
|---|---|---|
| Persona options | `GET /api/v2/voice/personas` (`VoicePersonaOut`) | empty list → call disabled with its reason |
| Persona label | `name` · `voice_id` · `is_default` · `is_active` | — |
| Transcript rows | voice session events | no row is drawn the API did not return |
| Level meter | live mic levels | empty (not animated) when the mic is closed |
| Mic state | idle · listening · thinking · speaking | one state at a time |

Synthesis / transcription run against the real voice API:

| Action | Endpoint |
|---|---|
| Speak | `POST /api/v2/voice/synthesize` |
| Listen | `POST /api/v2/voice/transcribe` |
| List personas | `GET /api/v2/voice/personas` |

Streaming transcription stays disabled: `POST /voice/transcribe/stream` is 503 until Django
Channels is wired (`voice/api.py:150-154`).

---

## 3. Control map

| # | Control | API / behavior | Live? |
|---|---|---|---|
| 1 | Persona selector | Options from `GET /api/v2/voice/personas`. Pick only — no CRUD. | live |
| 2 | Hold to talk / mic | Mic state machine (idle/listening/thinking/speaking). One state at a time. | live |
| 3 | Level meter | Draws only while the mic is open and levels are live. | live |
| 4 | Mute | Local mute; reflects real device state. | live |
| 5 | Type instead / Send | Text composer fallback → `chat.message` / voice run. | live |
| 6 | End session | UI-M-03 confirm. Disabled with reason when no active session. | live |
| 7 | Manage in Settings › Voice | `router → /settings` (Voice section) — config home (DUP-6). | live |

---

## 4. Numbered journey — run a voice conversation

| Step | Where | Action | API | Result |
|---|---|---|---|---|
| **1** | `/voice` | Screen loads | `GET /api/v2/voice/personas` | Persona picker filled with real personas. |
| **2** | run | Pick a persona (or use `is_default`) | — | Selector shows `name`. |
| **3** | run | **Hold to talk** | mic opens | State → listening; level meter draws. |
| **4** | run | Release | `POST /api/v2/voice/transcribe` | Utterance lands in the transcript; state → thinking. |
| **5** | run | Agent replies | `POST /api/v2/voice/synthesize` | State → speaking; audio plays. |
| **6** | run | **Type instead** → Send | text fallback | Message lands without the mic. |
| **7** | run | **End session** → confirm | UI-M-03 | Session closed. |
| **8** | run | Need to **manage** personas | — | **Settings › Voice** (UI-S-48-settings-voice) — never here (DUP-6). |

---

## 5. States

| State | Verbatim / behavior |
|---|---|
| loading | Skeleton transcript + `loading` chip. No counts while loading. |
| empty | “No voice session yet. Press Hold to talk to start.” |
| error | “Couldn’t start the voice session. ‹ reason from API ›” |
| no personas | Selector disabled: “No voice personas yet. Create one in Settings › Voice.” |
| permission-denied | “You don’t have access to voice chat. Requires the voice-user role.” |
| offline | “You’re offline. Voice chat needs a connection.” |
| gated stream | Streaming transcription disabled (503 until Channels is wired). |

---

## 6. Modal overlays

| Trigger | Modal | Contents |
|---|---|---|
| End session | UI-M-03 | “End this voice session?” Cancel / End (destructive). |
| Transcript focus | UI-M-02 | Full-screen transcript (explicit dismiss only). |

---

## 7. Honesty

Transcript rows and persona names come from real API values. No invented utterances, no fake level
animation when the mic is closed. Persona CRUD is **not** duplicated here (DUP-6).

---

## 8. Source map

| Source | Role |
|---|---|
| `webui/src/main.ts:407` | `/voice` · `/voice/chat` · `/platform/voice/chat` → `soma-voice-chat` |
| `webui/src/views/soma-voice-chat.ts` | Live run surface |
| `GET /api/v2/voice/personas` | Persona picker |
| `POST /api/v2/voice/synthesize` · `transcribe` | Speak / listen |
| `UI-S-48-settings-voice.md` | The one voice **config** home (DUP-6) |

End of Document
