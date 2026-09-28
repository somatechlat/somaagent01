# UI-S-46 — Voice chat

**Voice chat** — Voice workspace column (aliases /platform/voice/chat, /voice) — route `/voice/chat` — facet **Voice**.
Chrome abbreviated (UI-S-00). Facet tabs and surface rail are visible.

```
┌─ UI-S-00 chrome (abbrev) ────────────────────────────────────────────────────────────────────────┐
│ capsule: <capsule.name>                                                                         │
│ version: <version>    lifecycle: <lifecycle>                                                    │
│ persona knobs: (IQ <val>)(auto <val>)(budget <val>)                                             │
│ derived AgentIQ RO (greyed, never inputs):                                                      │
│   temperature <v>  max_tokens <v>  rlm_iterations <v>                                           │
│   recall_limit <v>  model_tier <v>  brain_query_enabled <v>                                     │
│   require_hitl <v>  tool_approval <v>  egress_allowed <v>                                       │
│   token_limit <v>  cost_tier <v>  thinking_budget <v>                                           │
├─────────────────────────────────────────────────────────────────────────────────────────────────┤
│ facet tabs x6:  [Soul][Brain][Hands][Memory][Body][Governance]                                  │
│ command palette: <Cmd-K>                                                                        │
├────────────────────────────────────────────────────────────────────────┼────────────────────────┤
│ WORKSPACE  facet: Voice                                                │ SURFACE RAIL x8        │
│  route: /voice/chat                                                    │  [1] Files             │
│  Voice chat            persona: [<persona.name> v]  [End session]      │  [2] Tools             │
│                                                                        │  [3] Browser           │
│  ┌── transcript ─────────────────────────────────────────┐             │  [4] Editor            │
│  │ you   : <utterance>                     <ts>           │            │  [5] Debug             │
│  │ agent : <utterance>                     <ts>           │            │  [6] Capsule           │
│  │ you   : <utterance>                     <ts>           │            │  [7] Brain             │
│  └────────────────────────────────────────────────────────┘            │  [8] Desktop           │
│                                                                        │       GATED (UI-X-08)  │
│  mic: [state machine: idle|listening|thinking|speaking]                │                        │
│  ┌──────────────────────────────────────────────┐                      │                        │
│  │ level meter: ‹ live level ›                   │                     │                        │
│  └──────────────────────────────────────────────┘                      │                        │
│  [Hold to talk]  [Mute]  [Type instead]                                │                        │
│                                                                        │                        │
│  Composer: [type a message...                ] [Send]                  │                        │
├────────────────────────────────────────────────────────────────────────┼────────────────────────┤
│ instance strip: <session_id>  state: <state>  started: <ts>                                     │
│ neuro meters x4 (RO): DA <v>  5-HT <v>  NE <v>  ACh <v>                                         │
│   neuromodulator synced_at: <ts>   (no value without a real sync)                               │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
```

**Control map.**

| # | UI-C-* | control | notes |
|---|---|---|---|
| 1 | UI-C-063 | persona selector | Options from the real persona list (UI-S-48). Empty list disables the call with its reason. |
| 2 | UI-C-098 | mic / voice capture control | Implements the mic/TTS state machine (idle/listening/thinking/speaking). One state at a time; no visual implies capture when the mic is not open. |
| 3 | UI-C-099 | audio level / waveform meter | Draws only while the mic is open and levels are live. Otherwise the meter is empty, not animated. |
| 4 | UI-C-065 | Mute toggle | Local mute. Reflects real device state. |
| 5 | UI-C-067 | Send (primary) | For the text composer fallback. |
| 6 | UI-C-069 | End session (destructive) | Opens UI-M-03. disabled-when: no active session — disabled-reason: "No active voice session." |

**State variants.**

- **Loading.** Skeleton rows plus a `loading` chip in the workspace header. No counts, charts or metrics are drawn while loading.
- **Empty.** "No voice session yet. Press Hold to talk to start."
- **Error.** "Couldn't start the voice session. ‹ reason from API ›"
- **Permission-denied.** "You don't have access to voice chat. Requires the voice-user role."
- **Offline.** "You're offline. Voice chat needs a connection."

**Modal overlays.** UI-M-02 Full-screen — transcript focus (explicit dismiss only). UI-M-03 Dialog — "End this voice session?" (destructive).
