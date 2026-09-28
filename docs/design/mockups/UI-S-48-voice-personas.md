# UI-S-48 — Voice personas

**Voice personas** — Voice workspace column (alias /platform/voice/personas) — route `/voice/personas` — facet **Voice**.
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
│  route: /voice/personas                                                │  [1] Files             │
│  Voice personas                              [+ New persona]           │  [2] Tools             │
│                                                                        │  [3] Browser           │
│  ┌───────────────────┐ ┌───────────────────┐ ┌───────────────────┐     │  [4] Editor            │
│  │ <persona.name>    │ │ <persona.name>    │ │ <persona.name>    │     │  [5] Debug             │
│  │ voice <voice.id>  │ │ voice <voice.id>  │ │ voice <voice.id>  │     │  [6] Capsule           │
│  │ locale <locale>   │ │ locale <locale>   │ │ locale <locale>   │     │  [7] Brain             │
│  │ [preview] [edit]  │ │ [preview] [edit]  │ │ [preview] [edit]  │     │  [8] Desktop           │
│  │ [set default]     │ │ [set default]     │ │ [set default]     │     │       GATED (UI-X-08)  │
│  └───────────────────┘ └───────────────────┘ └───────────────────┘     │                        │
│                                                                        │                        │
│  Preview plays a real sample from the voice service.                   │                        │
│  If no sample exists the control is disabled with its reason.          │                        │
├────────────────────────────────────────────────────────────────────────┼────────────────────────┤
│ instance strip: <session_id>  state: <state>  started: <ts>                                     │
│ neuro meters x4 (RO): DA <v>  5-HT <v>  NE <v>  ACh <v>                                         │
│   neuromodulator synced_at: <ts>   (no value without a real sync)                               │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
```

**Control map.**

| # | UI-C-* | control | notes |
|---|---|---|---|
| 1 | UI-C-081 | persona card | name/voice/locale from the persona record. |
| 2 | UI-C-068 | preview (secondary) | Plays a real sample. disabled-when: no sample is stored — disabled-reason: "No sample stored for this persona." |
| 3 | UI-C-068 | edit (secondary) | Opens UI-M-01 drawer with the persona form. |
| 4 | UI-C-067 | set default (primary) | disabled-when: already default — disabled-reason: "This persona is already the default." |
| 5 | UI-C-069 | delete persona (destructive) | Opens UI-M-03. disabled-when: persona is in use — disabled-reason: "This persona is in use by an active session." |

**State variants.**

- **Loading.** Skeleton rows plus a `loading` chip in the workspace header. No counts, charts or metrics are drawn while loading.
- **Empty.** "No voice personas yet. Create one to start talking to your agent."
- **Error.** "Couldn't load voice personas. ‹ reason from API ›"
- **Permission-denied.** "You don't have access to voice personas. Requires the voice-admin role."
- **Offline.** You're offline. Changes will not be saved until the connection returns.

**Modal overlays.** UI-M-01 Drawer — persona create/edit (name, voice, locale, sample). UI-M-03 Dialog — "Delete persona <persona.name>?" (destructive).
