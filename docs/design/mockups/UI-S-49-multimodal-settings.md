# UI-S-49 — Multimodal settings

**Multimodal settings** — Voice/workspace column (alias /agent/multimodal) — route `/settings/multimodal` — facet **Voice**.
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
│  route: /settings/multimodal                                           │  [1] Files             │
│  Multimodal settings                          [Save] [Cancel]          │  [2] Tools             │
│                                                                        │  [3] Browser           │
│  ┌── Multimodal Capabilities ───────────────────────────┐              │  [4] Editor            │
│  │ [x] Image generation        billable: yes             │             │  [5] Debug             │
│  │     quality: [<std v>]  style: [<vivid v>]            │             │  [6] Capsule           │
│  │     note: image generation uses the configured model  │             │  [7] Brain             │
│  │                                                       │             │  [8] Desktop           │
│  │ [x] Diagram generation (Mermaid)                      │             │       GATED (UI-X-08)  │
│  │     format: [svg][png]   theme: [<default v>]         │             │                        │
│  │                                                       │             │                        │
│  │ [ ] Screenshots (Playwright)                          │             │                        │
│  │     viewport: [<1920x1080 v>]                         │             │                        │
│  │     disabled-reason: browser worker not attached      │             │                        │
│  └───────────────────────────────────────────────────────┘             │                        │
│                                                                        │                        │
│  Quota (read-only)   <used> / <limit>   window <ts>                    │                        │
├────────────────────────────────────────────────────────────────────────┼────────────────────────┤
│ instance strip: <session_id>  state: <state>  started: <ts>                                     │
│ neuro meters x4 (RO): DA <v>  5-HT <v>  NE <v>  ACh <v>                                         │
│   neuromodulator synced_at: <ts>   (no value without a real sync)                               │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
```

**Control map.**

| # | UI-C-* | control | notes |
|---|---|---|---|
| 1 | UI-C-097 | capability toggle card | One card per real capability (image / diagram / screenshot). A capability that is not wired is disabled with its reason, never drawn as available. |
| 2 | UI-C-063 | quality / style / format / viewport selects | Options come from the settings API enum. No option is invented. |
| 3 | UI-C-065 | capability enable toggle | disabled-when: capability unavailable — disabled-reason printed inline on the card. |
| 4 | UI-C-096 | quota readout (read-only) | `<used> / <limit>` is `‹ live value ›`. The readout is never an input. |
| 5 | UI-C-067 | Save (primary) | disabled-while: request in flight. |

**State variants.**

- **Loading.** Skeleton rows plus a `loading` chip in the workspace header. No counts, charts or metrics are drawn while loading.
- **Empty.** "No multimodal capabilities are available on this deployment."
- **Error.** "Couldn't load multimodal settings. ‹ reason from API ›"
- **Permission-denied.** "You don't have access to multimodal settings. Requires the agent-owner role."
- **Offline.** You're offline. Changes will not be saved until the connection returns.

**Modal overlays.** UI-M-01 Drawer — capability detail (model bound, quota history). UI-M-02 Full-screen — image/diagram preview (explicit dismiss only).
