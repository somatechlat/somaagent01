# UI-S-48 — Voice personas (run surface)

Screen UI-S-48 · Route: `/voice/personas` · Authenticated  
Live: `webui/src/views/soma-voice-personas.ts` · Router: `webui/src/main.ts`  
**Voice config home = Settings › Voice (UI-S-48-settings-voice) ONLY.** This screen is a run-oriented persona picker.

**Product:** Agent Soma voice run surface. Thin workspace chrome.  
Forbidden on screen: the word "slot" · SaaS / Eye of God branding · fake metrics · facet tabs · surface rail · IQ knobs · chat left rail · second persona CRUD library.

---

## 1. Purpose

Pick a voice persona for a voice run, preview it, and deep-link to Settings › Voice for all management (create/edit/default/delete). **This is not a second persona library.** Persona CRUD lives only in Settings › Voice (UI-S-48-settings-voice).

---

## 2. ASCII wireframe — `/voice/personas` (desktop)

```
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│ [←]  SOMA · Voice personas                     [Manage in Settings › Voice]                   │
├──────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                              │
│  Voice personas                                                                              │
│  Pick a persona for your next voice run. Manage them in Settings › Voice.                     │
│                                                                                              │
│  ┌───────────────────┐ ┌───────────────────┐ ┌───────────────────┐                            │
│  │ <persona.name>    │ │ <persona.name>    │ │ <persona.name>    │                            │
│  │ voice <voice_id>  │ │ voice <voice_id>  │ │ voice <voice_id>  │                            │
│  │ stt <stt_language>│ │ stt <stt_language>│ │ stt <stt_language>│                            │
│  │ ● default         │ │ ○ active          │ │ ○ active          │                            │
│  │ [Preview] [Use]   │ │ [Preview] [Use]   │ │ [Preview] [Use]   │                            │
│  └───────────────────┘ └───────────────────┘ └───────────────────┘                            │
│                                                                                              │
│  Preview plays a real sample from the voice service.                                         │
│  If no sample exists the control is disabled with its reason.                                │
│                                                                                              │
│  [Manage in Settings › Voice]  →  /settings  (Voice section, UI-S-48-settings-voice)          │
│                                                                                              │
├──────────────────────────────────────────────────────────────────────────────────────────────┤
│ status: <load state> · source: GET /api/v2/voice/personas · <n> personas                     │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
```

**Chrome law.** Thin workspace top ([←] back · brand · manage link). No chat left rail, no canvas, no facet tabs, no surface rail. **No create/edit/delete here** — those live only in Settings › Voice.

---

## 3. User journey (numbered clicks)

1. From voice run (UI-S-46) or voice sessions (UI-S-47) → `/voice/personas`.
2. Browse persona cards (name · voice_id · stt_language · default/active).
3. Click **[Preview]** → `POST /api/v2/voice/synthesize` → plays real sample.
4. Click **[Use]** → selects persona for the voice run → returns to `/voice`.
5. Click **[Manage in Settings › Voice]** → `/settings` (Voice section) → full CRUD (UI-S-48-settings-voice).

---

## 4. Control map

| # | Control | Binding |
|---|---|---|
| 1 | Persona card | `name` · `voice_id` · `stt_language` · `is_active` · `is_default` from `GET /api/v2/voice/personas`. |
| 2 | Preview (secondary) | `POST /api/v2/voice/synthesize` → plays `audio_base64`. disabled-when: no sample stored — disabled-reason: `No sample stored for this persona.` |
| 3 | Use (primary) | Selects persona for the current voice run. Routes to `/voice`. |
| 4 | Manage in Settings › Voice | href `/settings` (Voice section) → UI-S-48-settings-voice. **All CRUD lives there.** |

---

## 5. Field / behavior

| Field | Source | Behavior |
|---|---|---|
| persona name | `VoicePersonaOut.name` | Read-only on this screen. |
| voice_id | `VoicePersonaOut.voice_id` | Read-only. |
| stt_language | `VoicePersonaOut.stt_language` | Read-only. |
| is_default | `VoicePersonaOut.is_default` | Read-only chip. |
| is_active | `VoicePersonaOut.is_active` | Read-only chip. |

**No write operations on this screen.** Create / edit / set-default / delete → Settings › Voice only.

---

## 6. States (verbatim)

| State | Verbatim |
|---|---|
| loading | `Loading voice personas...` |
| empty | `No voice personas yet. Create one in Settings › Voice.` |
| error | `Couldn't load voice personas. ‹ reason from API ›` |
| permission | `You don't have access to voice personas. Requires the voice-admin role.` |
| offline | `You're offline. Voice personas need a connection.` |
| preview gated | `No sample stored for this persona.` |

---

## 7. Navigation in / out

| Direction | Target | Notes |
|---|---|---|
| In | `/voice/personas` | From UI-S-46 voice run / UI-S-47 sessions. |
| Out | `/voice` | [Use] selects persona → voice run. |
| Out | `/settings` (Voice) | Manage in Settings › Voice → UI-S-48-settings-voice. |
| Out | `/voice/sessions` | [←] back. |

---

## 8. Single-home law

| Feature | Home | This screen |
|---|---|---|
| Persona CRUD | **Settings › Voice** (UI-S-48-settings-voice) | **never** |
| Persona picker | `/voice/personas` (this screen) | yes |
| Voice run | `/voice` (UI-S-46) | link only |
| Voice config | Settings › Voice | link only |

---

## 9. Acceptance

- [ ] No persona create/edit/delete on this screen — CRUD only in Settings › Voice
- [ ] No facet tabs, surface rail, IQ knobs, chat left rail
- [ ] All copy verbatim per §6

End of Document
