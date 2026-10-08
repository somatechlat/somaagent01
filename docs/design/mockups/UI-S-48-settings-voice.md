# UI-S-48-settings-voice — Settings — Voice

**Settings — Voice** — section **Voice** inside the one Settings shell — route `/settings` (Voice tab).
Chrome abbreviated (UI-S-00). Left section nav (7) is visible; Voice is active.
Config home only. Run surfaces stay at `/voice` · `/voice/personas` · `/voice/sessions` (UI-S-46/47/48-voice-personas). DUP-6.

**Field truth.** Persona form edits only `VoicePersonaBase` / `VoicePersonaCreate` / `VoicePersonaUpdate` (`admin/voice/schemas.py` 71–114):
`name` · `description` · `voice_id` · `voice_speed` · `stt_model` · `stt_language` · `system_prompt` · `temperature` · `max_tokens` · `turn_detection_enabled` · `turn_detection_threshold` · `silence_duration_ms` · `llm_config_id` · `is_active` · `is_default`.
No invented fields. Volume and TTS-provider rows in Screen 7C have **no** persona API field — not editable here.

**Language law.** Binding copy is **Used for: Chat / Help / Memory**. The banned admin noun never appears in UI strings.
**Memory rule.** Memory is not a Settings section. Its only home is `/memory` (UI-S-04, left rail).

## Purpose

Create, edit, activate, default, and delete voice personas; run Test speak / Test listen against the live voice API. One Settings Voice section — no second persona library.

## ASCII wireframe — Settings › Voice

```
┌─ UI-S-00 chrome (abbrev) ────────────────────────────────────────────────────────────────────────┐
│ ☰ SOMA    Settings · Voice     [Search settings…]                           [Save] [Cancel]     │
├──────────────┬───────────────────────────────────────────────────────────────────────────────────┤
│ SECTION NAV  │  VOICE — how the agent speaks and listens                           [+ New]      │
│  Agent       │  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  Models      │  │ Persona name          [Support voice               ]  ← name                │   │
│  Voice    ●  │  │ Description           [Calm helper for calls       ]  ← description         │   │
│  Interface   │  │                                                                             │   │
│  Tools       │  │ SPEAKING                                                                    │   │
│  Integrations│  │   Voice ID            [af_heart                    ▼]  ← voice_id           │   │
│  Advanced    │  │   Speaking speed      [1.0 ═════●═══════]             ← voice_speed         │   │
│              │  │                                                                             │   │
│              │  │ LISTENING                                                                   │   │
│              │  │   Speech-to-text      [whisper-1                   ▼]  ← stt_model          │   │
│              │  │   Listen language     [en                          ▼]  ← stt_language      │   │
│              │  │   Detect when to stop [● on]                           ← turn_detection_enabled │
│              │  │   Stop sensitivity    [0.5 ═════●═══════]             ← turn_detection_threshold │
│              │  │   Silence before stop [500] ms                         ← silence_duration_ms│   │
│              │  │                                                                             │   │
│              │  │ REPLIES                                                                     │   │
│              │  │   Model for voice     [‹llm_config_name›          ▼]  ← llm_config_id      │   │
│              │  │   Persona instructions ┌─────────────────────────────────────────────┐      │   │
│              │  │                        │ Speak simply. Confirm before actions.       │      │   │
│              │  │                        └─────────────────────────────────────────────┘      │   │
│              │  │                                             ← system_prompt                 │   │
│              │  │   Creativity (temperature)  [0.7 ═════●════]       ← temperature           │   │
│              │  │   Max reply length          [1024]                   ← max_tokens           │   │
│              │  │                                                                             │   │
│              │  │   [● on] Use this voice  ← is_active    [●] Make default ← is_default      │   │
│              │  └─────────────────────────────────────────────────────────────────────────────┘   │
│              │  [Save voice]  [Test speak]  [Test listen]  [Delete…]                             │
│              │  Persona list: ‹name› · ‹voice_id› · ‹stt_language› · ● active / ● default       │
├──────────────┴───────────────────────────────────────────────────────────────────────────────────┤
│ status: <load / save state> · permission: settings:edit → write, else read-only banner          │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

## Field table (API field)

| Human label | Control | API field | Bounds / notes | Evidence |
|---|---|---|---|---|
| Persona name | text | `name` | required | `schemas.py:74` |
| Description | text | `description` | default `""` | `schemas.py:75` |
| Voice ID | select/text | `voice_id` | default `af_heart`; options `GET /api/v2/voice/voices` | `schemas.py:76`; `api.py:109-118` |
| Speaking speed | slider | `voice_speed` | 0.5–2.0, default 1.0 | `schemas.py:77` |
| Speech-to-text | select | `stt_model` | default `whisper-1` | `schemas.py:78` |
| Listen language | select | `stt_language` | default `en` | `schemas.py:79` |
| Detect when to stop | toggle | `turn_detection_enabled` | default true | `schemas.py:83` |
| Stop sensitivity | slider | `turn_detection_threshold` | 0.0–1.0, default 0.5 | `schemas.py:84` |
| Silence before stop (ms) | number | `silence_duration_ms` | 100–3000, default 500 | `schemas.py:85` |
| Model for voice | select | `llm_config_id` | FK int; options `GET /api/v2/voice/llm-configs?model_type=chat`; display `llm_config_name` | `schemas.py:95`, `122-123`; `api.py:162-171` |
| Persona instructions | textarea | `system_prompt` | default `""` | `schemas.py:80` |
| Creativity (temperature) | slider | `temperature` | 0.0–2.0, default 0.7 | `schemas.py:81` |
| Max reply length | number | `max_tokens` | 1–32000, default 1024 | `schemas.py:82` |
| Use this voice | toggle | `is_active` | update-only (`VoicePersonaUpdate`) | `schemas.py:114`, `124` |
| Make default | toggle | `is_default` | out-only; set via `POST …/set-default` | `schemas.py:125`; `api.py:247-255` |

`llm_config` in design copy = API `llm_config_id` (int FK) + read-only `llm_config_name`.

## Control map

| # | UI-C-* | control | notes |
|---|---|---|---|
| 1 | UI-C-100 | section nav (7) | Agent · Models · Voice · Interface · Tools · Integrations · Advanced. |
| 2 | UI-C-081 | persona row | `name` · `voice_id` · `stt_language` · `is_active` · `is_default` from `VoicePersonaOut`. |
| 3 | UI-C-121 | persona form | All `VoicePersonaCreate` / `VoicePersonaUpdate` fields. Save disabled-while: request in flight. |
| 4 | UI-C-067 | Save voice | `POST /api/v2/voice/personas` or `PUT /api/v2/voice/personas/{id}`. |
| 5 | UI-C-122 | Test speak | `POST /api/v2/voice/synthesize` `{text, voice, speed, format}` → plays `audio_base64`. disabled-when: empty `system_prompt` sample text — disabled-reason: "Enter sample text to speak." |
| 6 | UI-C-123 | Test listen | `POST /api/v2/voice/transcribe` `{audio_base64, format, language}` → shows `text`. disabled-when: no mic capture — disabled-reason: "Microphone capture is not available." |
| 7 | UI-C-068 | set default | `POST /api/v2/voice/personas/{id}/set-default`. disabled-when: already `is_default` — disabled-reason: "This persona is already the default." |
| 8 | UI-C-069 | Delete… | `DELETE /api/v2/voice/personas/{id}` via UI-M-03. |
| 9 | — | permission banner | `system:configure` absent → read-only, Save disabled-reason: "Requires settings edit permission." |

## Numbered journey — create and use a persona

| Step | Where | Action | API | Result |
|---|---|---|---|---|
| **1** | `/settings` (Voice tab) | Click **+ New** | — | Blank persona form. |
| **2** | form | Fill `name` · `voice_id` (required) | — | Save enables. |
| **3** | form | Set `voice_speed` · `stt_model` · `stt_language` · turn detection · `system_prompt` · `temperature` · `max_tokens` | — | Optional fields; defaults per the schema. |
| **4** | form | Click **Save voice** | `POST /api/v2/voice/personas` | 201; row appears in the persona list. |
| **5** | form | Click **Test speak** | `POST /api/v2/voice/synthesize` | Audio plays; `voice_used` shown. |
| **6** | form | Click **Test listen** | `POST /api/v2/voice/transcribe` | `text` printed. |
| **7** | list | Click **Make default** | `POST /api/v2/voice/personas/{id}/set-default` | Previous default cleared. |
| **8** | list | Toggle **Use this voice** → Save | `PUT /api/v2/voice/personas/{id}` | `is_active` updated. |
| **9** | list | Click **Delete…** → confirm | `DELETE /api/v2/voice/personas/{id}` | Row gone. |
| **10** | run | Need a live voice run | — | `/voice` (UI-S-46) — run surface only (DUP-6). |

## States

- **Loading.** Skeleton field blocks. No counts or metrics while loading.
- **Empty.** "No voice personas yet. Create one to start talking to your agent."
- **Error.** "Couldn't load voice personas. ‹ reason from API ›"
- **Permission-denied.** "You don't have access to voice settings. Requires settings edit permission."
- **Offline.** "You're offline. Changes will not be saved until the connection returns."
- **Gated stream.** Streaming transcription stays disabled: `POST /voice/transcribe/stream` is 503 until Django Channels is wired (`voice/api.py:150-154`).

**Modal overlays.** UI-M-03 Dialog — "Delete persona `‹ name ›`?" (destructive).

## Nav

Settings shell section nav = Agent · Models · **Voice** · Interface · Tools · Integrations · Advanced (UI-S-50). No Memory item.
Run surfaces remain `/voice/personas` (UI-S-48-voice-personas), `/voice/sessions` (UI-S-47), `/voice` (UI-S-46).

## Test clicks

| Click | Expect |
|---|---|
| `+ New` → fill `name`/`voice_id` → Save voice | `POST /api/v2/voice/personas` 201; row appears in list |
| Edit row → change `temperature` → Save voice | `PUT /api/v2/voice/personas/{id}` 200 |
| Test speak | `POST /api/v2/voice/synthesize` 200; audio plays; `voice_used` shown |
| Test listen | `POST /api/v2/voice/transcribe` 200; `text` printed |
| Make default | `POST /api/v2/voice/personas/{id}/set-default` 200; previous default cleared |
| Delete… → confirm | `DELETE /api/v2/voice/personas/{id}` 204; row gone |
| Save without `settings:edit` | Save disabled + reason banner |

## file:line evidence

| Evidence | Path |
|---|---|
| Persona fields | `somaAgent01/admin/voice/schemas.py:71-125` |
| CRUD + set-default | `somaAgent01/admin/voice/api.py:174-255` |
| Synthesize / transcribe | `somaAgent01/admin/voice/api.py:69-106` |
| LLM options | `somaAgent01/admin/voice/api.py:162-171` |
| Live form + calls | `somaAgent01/webui/src/views/soma-voice-personas.ts:20-42`, `257-360` |
| Bindings | `somaAgent01/docs/design/SOMA-UI-BINDINGS-001.md:154-159` |
| Screen 7C | `somabrain/docs/project/SOMA-UI-MOCKUPS-001.md:532-592` |
| Nav shell | `somaAgent01/docs/design/mockups/UI-S-50-settings-agent.md:41-53` |
