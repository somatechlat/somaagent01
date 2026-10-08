# UI-S-49 — Multimodal settings (Settings › Tools · Multimodal block)

Screen UI-S-49 · Route: `/settings` (Tools tab · Multimodal block) · Authenticated  
Live: `webui/src/views/soma-settings.ts` (Tools section)  
**Settings is ONE shell.** Multimodal is a block inside **Tools** — not a separate route or section.

**Product:** Agent Soma. Settings shell.  
Forbidden on screen: the word "slot" · SaaS / Eye of God branding · fake metrics · facet tabs · surface rail · IQ knobs · chat left rail · Memory as a settings section.

---

## 1. Purpose

Enable/disable multimodal capabilities (image generation, diagram generation, screenshots) and set their options. This is a **block inside Settings › Tools** — not a separate settings section. The 7 Settings sections are: Agent · Models · Voice · Interface · Tools · Integrations · Advanced.

---

## 2. ASCII wireframe — `/settings` (Tools tab · Multimodal block, desktop)

```
┌─ Settings shell ──────────────────────────────────────────────────────────────────────────────┐
│ ☰ SOMA    Settings · Tools     [Search settings…]                            [Save] [Cancel]     │
├──────────────┬───────────────────────────────────────────────────────────────────────────────────┤
│ SECTION NAV  │  TOOLS — what the agent may run                                      [Refresh]   │
│  Agent       │  ┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────────┐     │
│  Models      │  │ ‹tool.name›      [●] │  │ ‹tool.name›      [●] │  │ ‹tool.name›      [○] │     │
│  Voice       │  │ ‹tool.description›   │  │ ‹tool.description›   │  │ ‹tool.description›   │     │
│  Interface   │  │ category ‹category›  │  │ category ‹category›  │  │ category ‹category›  │     │
│  Tools    ●  │  │ [schema ▸]           │  │ [schema ▸]           │  │ [schema ▸]           │     │
│  Integrations│  └──────────────────────┘  └──────────────────────┘  └──────────────────────┘     │
│  Advanced    │  (rows = GET /api/v2/tools/catalog · live names only)                             │
│              │                                                                                   │
│              │  EXECUTION LIMITS (settings entity: agent)                                        │
│              │  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│              │  │ Timeout (seconds)     [30        ]  ← tool_exec_timeout_s                   │   │
│              │  │ Max result size       [‹chars›   ]  ← tool_result_max_chars                 │   │
│              │  │ Max tool iterations   [‹n›       ]  ← tool_max_iterations                   │   │
│              │  └─────────────────────────────────────────────────────────────────────────────┘   │
│              │                                                                                   │
│              │  MULTIMODAL CAPABILITIES (this block — UI-S-49)                                   │
│              │  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│              │  │ [●] Image generation        billable: yes                                    │   │
│              │  │     quality: [standard ▼]   style: [vivid ▼]                                 │   │
│              │  │     note: image generation uses the configured model                         │   │
│              │  │                                                                               │   │
│              │  │ [●] Diagram generation (Mermaid)                                              │   │
│              │  │     format: [svg][png]   theme: [default ▼]                                  │   │
│              │  │                                                                               │   │
│              │  │ [○] Screenshots (Playwright)                                                  │   │
│              │  │     viewport: [1920x1080 ▼]                                                   │   │
│              │  │     GATED: browser worker not attached                                        │   │
│              │  └─────────────────────────────────────────────────────────────────────────────┘   │
│              │                                                                                   │
│              │  Quota (read-only)   <used> / <limit>   window <ts>                               │
├──────────────┴───────────────────────────────────────────────────────────────────────────────────┤
│ status: <load / save state> · source: live catalog · permission: settings:edit                  │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

**Settings shell law.** 7 sections: Agent · Models · Voice · Interface · Tools · Integrations · Advanced. **Memory is NEVER a settings section.** Multimodal is a block inside Tools. No separate `/settings/multimodal` route.

---

## 3. User journey (numbered clicks)

1. Left rail → **⚙ Settings** → `/settings` (Agent section).
2. Click **Tools** in section nav → Tools section (tool cards + execution limits + Multimodal block).
3. Scroll to **MULTIMODAL CAPABILITIES** block.
4. Toggle **Image generation** → quality / style selects appear.
5. Toggle **Diagram generation** → format / theme selects appear.
6. Toggle **Screenshots** → disabled with GATED reason (browser worker not attached).
7. Click **Save** (header) → saves tool toggles + multimodal options.

---

## 4. Control map

| # | Control | Binding |
|---|---|---|
| 1 | Capability toggle card | One card per real capability (image / diagram / screenshot). Not wired → disabled with reason inline. |
| 2 | quality / style / format / theme / viewport selects | Options from the settings API enum. No option invented. |
| 3 | capability enable toggle | `PUT` settings. disabled-when: capability unavailable — disabled-reason printed inline. |
| 4 | quota readout (read-only) | `<used> / <limit>` is `‹ live value ›`. Never an input. |
| 5 | Save (primary, header) | Saves dirty fields via `PUT /api/v2/core/settings/agent`. disabled-while: request in flight. |

---

## 5. Field / behavior

| Field | Source | Behavior |
|---|---|---|
| image generation enabled | settings API | toggle |
| image quality | settings API enum | select. Options from API only. |
| image style | settings API enum | select. Options from API only. |
| diagram generation enabled | settings API | toggle |
| diagram format | `svg` \| `png` | multi-select. |
| diagram theme | settings API enum | select. |
| screenshots enabled | settings API | toggle. GATED when browser worker not attached. |
| screenshot viewport | settings API enum | select. |
| quota | `GET` quota endpoint | read-only `<used> / <limit>`. |

No invented fields. No fake quota numbers.

---

## 6. States (verbatim)

| State | Verbatim |
|---|---|
| loading | `Loading tools...` |
| empty | `No multimodal capabilities are available on this deployment.` |
| error | `Couldn't load multimodal settings. ‹ reason from API ›` |
| permission | `You don't have access to multimodal settings. Requires settings edit permission.` |
| offline | `You're offline. Changes will not be saved until the connection returns.` |
| gated (screenshots) | `GATED: browser worker not attached` |

---

## 7. Navigation in / out

| Direction | Target | Notes |
|---|---|---|
| In | `/settings` → Tools tab | Settings shell section nav. |
| Out | other Settings sections | Section nav: Agent · Models · Voice · Interface · Tools · Integrations · Advanced. |
| Out | `/chat` | Left rail → New chat / SOMA brand. |

---

## 8. Single-home law

| Feature | Home | Forbidden |
|---|---|---|
| Multimodal capabilities | Settings › Tools (this block) | separate route · chat chrome · welcome card |
| Tool catalog enable | Settings › Tools | duplicate catalog |
| Models | Settings › Models (UI-S-51) | anywhere else |
| Memory | `/memory` (UI-S-04) | settings section · welcome card |

---

## 9. Modal overlays

- **UI-M-01** Drawer — capability detail (model bound, quota history).
- **UI-M-02** Full-screen — image/diagram preview (explicit dismiss only).

---

## 10. Acceptance

- [ ] Renders inside the 7-section Settings shell (Tools active)
- [ ] No separate `/settings/multimodal` route
- [ ] Memory is not a settings section
- [ ] GATED capabilities show inline reason — never drawn as available
- [ ] All copy verbatim per §6

End of Document
