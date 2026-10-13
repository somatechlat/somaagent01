# CM-04 — SomaBrain Manager Control Map

## Document Control

| Field | Value |
|---|---|
| Document Title | Control Map — SomaBrain Manager (neuromods / knobs / diagnostics / connection) |
| Document Identifier | SOMA-UI-CM-04 |
| Version | 1.0.0 |
| Date | 2026-10-13 |
| Status | Draft |
| Author | SomaTech Engineering (soma-ui-engineer) |
| Classification | Internal |
| ISO Reference | ISO 9241-210:2019 |
| Next Review | 2027-01-13 |
| Related | `SOMA-UI-AGENT-FRONTEND-MASTER-001.md` §3.3 · `SOMA-UI-BINDINGS-001.md` §3 · `UI-S-02` · `UI-S-56` · `UI-X-07` |
| Live sources | `webui/src/views/soma-cognitive-panel.ts` · `webui/src/views/soma-settings-somabrain.ts` · `webui/src/components/soma-agent-iq.ts` · `webui/src/components/soma-capsule-editor.ts` |
| Routes | `/cognitive` · `/training` · `/settings/somabrain` · canvas `UI-X-07` (same cognitive component) |

## Revision History

| Version | Date | Author | Description |
|---|---|---|---|
| 1.0.0 | 2026-10-13 | soma-ui-engineer | Control map for neuromodulator readouts, AgentIQ knobs, SomaBrain connection settings, sleep/consolidation, diagnostics. |

---

## 1. ASCII wireframe — SomaBrain Manager (consolidated design)

```
┌─ SomaBrain Manager ────────────────────────────────────────────────────────────────────────────┐
│ SB-01 Connection  ● ok   SB-02 tenant   SB-03 latency   SB-04 last success                     │
├─ Neuromodulators (raw values only — no invented %) ────────────────────────────────────────────┤
│ SB-10 DA 0.62   SB-11 5-HT 0.41   SB-12 NE 0.73   SB-13 ACh 0.55   (server keys as sent)       │
├─ Sleep / consolidation ────────────────────────────────────────────────────────────────────────┤
│ SB-20 phase: idle | SB-21 last run | SB-22 queue | SB-23 [Trigger sleep cycle]                 │
├─ Knobs (Capsule.persona_config.knobs) ─────────────────────────────────────────────────────────┤
│ SB-30 intelligence [====|-----] 7    SB-31 autonomy [====|-----] 7                             │
│ SB-32 resource     [==|-------] 0.5  SB-33 style    [balanced ▾]                               │
│ SB-34 derived readouts (12, read-only)    SB-35 [Save knobs]  SB-36 [Reset]                    │
├─ Adaptation params (per-agent /cognitive) ─────────────────────────────────────────────────────┤
│ SB-40 param sliders (server keys)   SB-41 [Save params]  SB-42 [Reset adaptation]              │
├─ Diagnostics ──────────────────────────────────────────────────────────────────────────────────┤
│ SB-50 memory_ok ●  SB-51 sfm circuit ●  SB-52 planner gated (feature flag)                     │
│ SB-53 [Open Memory]  SB-54 [Open Cognitive]                                                    │
└───────────────────────────────────────────────────────────────────────────────────────────────┘
```

## 2. ASCII wireframe — Settings › SomaBrain (live connection knobs)

```
┌─ Settings › SomaBrain ─────────────────────────────────────────────────────────────────────────┐
│ SS-01 base URL   SS-02 namespace   SS-03 retention   SS-04 sleep interval   SS-05 enabled      │
│ SS-06 [Save] [Revert]   SS-07 connector state   SS-08 [Open /memory] [Open /cognitive]         │
│ SS-09 honest note: "Cognitive knobs are per-agent on /cognitive."                              │
└───────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Control map — Cognitive panel (`/cognitive`, UI-X-07)

| ID | Label | Type | Binding / API | States | Disabled reason | A11y | Status |
|---|---|---|---|---|---|---|---|
| SB-01 | Connection status | status-dot | `GET /api/v2/core/brain-connector` + cognitive load | ok, degraded, error | — | `status` with text label | LIVE |
| SB-02 | Tenant | readout | cognitive state response | default / `—` | — | text | LIVE |
| SB-03 | Latency | readout | diagnostics when server reports | default / `—` | No latency field → `—` (never invent ms) | text | LIVE |
| SB-04 | Last success | readout | connector `last_success` | default / `—` | — | text | LIVE |
| SB-10 | Neuromodulator gauge (per key) | meter | `GET /api/v2/somabrain/cognitive/state/{agent_id}` → `neuromodulators: dict` | loading, empty, value | Server sent no readings → “No neuromodulator readings were reported.” | `meter` + numeric text (raw) | LIVE |
| SB-10a | Neuromod live update | readout | WS/stream update `{neuromodulators}` | updating | — | polite live region | LIVE |
| SB-20 | Sleep phase | readout | sleep status route | default / `—` | No phase field → `—` | text | LIVE |
| SB-21 | Last sleep run | readout | same | default / `—` | — | text | LIVE |
| SB-22 | Consolidation queue | readout | same | default / `—` | — | text | LIVE |
| SB-23 | Trigger sleep cycle | button | sleep trigger API on cognitive admin | default, busy, error | — | `button` | LIVE |
| SB-30 | intelligence_level | slider | `GET/PATCH /agents/{id}/capsule` → `persona_config.knobs.intelligence_level` | default, dirty, saved | No capsule selected — knobs are not loaded. | `slider` valuetext | LIVE |
| SB-31 | autonomy_level | slider | `knobs.autonomy_level` | same | same | same | LIVE |
| SB-32 | resource_level | slider | `knobs.resource_level` | same | same | same | LIVE |
| SB-33 | style | select | `knobs.style` (e.g. balanced) | same | same | `combobox` | LIVE |
| SB-34 | Derived settings (12) | readout | derived from 3 knobs (AgentIQ derivation) | default | **Never independently editable** (REQ-UIXS-003) | list of derived values | LIVE (RO) |
| SB-35 | Save knobs | button | `PATCH /agents/{id}/capsule` | default, disabled-when-clean, busy | No capsule selected — cannot save knobs. | `button` | LIVE |
| SB-36 | Reset knobs | button | local reset to server values | default, disabled-when-clean | — | `button` | LIVE |
| SB-40 | Adaptation param (per key) | slider | cognitive `adaptation_params` | default, dirty | — | `slider` | LIVE |
| SB-41 | Save params | button | cognitive params save | default, busy | — | `button` | LIVE |
| SB-42 | Reset adaptation | button | cognitive reset adaptation | default, confirm, busy | — | `button` class warning | LIVE |
| SB-50 | memory_ok | status-dot | cognitive / brain diagnostics | ok, error | — | status | LIVE |
| SB-51 | sfm circuit | status-dot | brain-connector `circuit` | ok, open, error | — | status | LIVE |
| SB-52 | Planner flag | readout | feature flags | gated / on | Planner behind feature flag → visible + reason | `status` | GATED |
| SB-53 | Open Memory | button | navigate `/memory` | default | — | `button` | LIVE |
| SB-54 | Open Cognitive | button | navigate `/cognitive` | default | — | `button` | LIVE |
| SB-55 | Back | button | `/chat` | default | — | `button` | LIVE |
| SB-60 | Neuromod % meters (invented) | — | — | **forbidden** | Catalog law: raw values only — no fake % meters | — | GATED (never build) |
| SB-61 | Sleep phase fabricator | — | — | **forbidden** | No fake “REM/deep” without server phase | — | GATED (never build) |
| SB-62 | Global knobs (not per-agent) | — | — | **forbidden** | Knobs are per-agent Capsule; Settings note SS-09 points there | — | GATED |

---

## 4. Control map — Settings › SomaBrain (connection)

| ID | Label | Type | Binding / API | States | Disabled reason | A11y | Status |
|---|---|---|---|---|---|---|---|
| SS-01 | Brain base URL | input.text | operator settings store (`sb-url`) | default, focus, dirty, error | — | labelled `#sb-url` | LIVE |
| SS-02 | Namespace | input.text | settings (`sb-ns`) | same | — | `#sb-ns` | LIVE |
| SS-03 | Retention | input.number/text | settings (`sb-retention`) | same | — | `#sb-retention` | LIVE |
| SS-04 | Sleep interval | input.number/text | settings (`sb-sleep`) | same | — | `#sb-sleep` | LIVE |
| SS-05 | Enabled | toggle | settings (`change` handler) | on, off | — | `switch` | LIVE |
| SS-06a | Save | button | save settings (source-tagged) | default, dirty, saving, saved, error | — | `button` | LIVE |
| SS-06b | Revert | button | `_revert` local | default, dirty | — | `button` | LIVE |
| SS-07 | Connector state | readout | `GET /core/brain-connector` | ok, warn, error (`data-testid="connector-state"`) | — | text status | LIVE |
| SS-08a | Open Memory | button | navigate `/memory` | default | — | `button` | LIVE |
| SS-08b | Open Cognitive | button | navigate `/cognitive` | default | — | `button` | LIVE |
| SS-09 | Honest note | readout | — | always | — | “Cognitive knobs are per-agent on /cognitive.” | LIVE |
| SS-10 | API key / secret | input.password | **Vault write-only** | masked set / unset | Value never redisplayed; rotate in Vault | masked field | GATED (by policy) |
| SS-11 | Migrate / reconnect wizard | button | target brain connector admin | default | No wizard API → “Reconnect wizard needs the brain connector admin API.” | `button` | PLANNED |

---

## 5. Control map — Capsule / AgentIQ (knob host)

| ID | Label | Type | Binding / API | States | Disabled reason | A11y | Status |
|---|---|---|---|---|---|---|---|
| CAP-01 | Tab Soul | tabs | local `_activeTab` | active, inactive | — | `tab` | LIVE |
| CAP-02 | Tab Learning | tabs | local | active, inactive | — | `tab` | LIVE |
| CAP-03 | Save | button | `PATCH /agents/{id}/capsule` | default, busy, error | — | `button` | LIVE |
| CAP-04 | Reload | button | `GET /agents/{id}/capsule` | default, busy | — | `button` | LIVE |
| CAP-05 | Export | button | client export of capsule config | default | — | `button` | LIVE |
| CAP-06 | Archive agent | button | `POST /agents/{id}/archive` | default, confirm | — | `button` danger | LIVE |
| CAP-07 | Persona text field | textarea | capsule config field | dirty | — | labelled textarea | LIVE |
| IQ-01 | Knob input (intelligence/autonomy/…) | input.number/slider | `persona_config.knobs` | dirty | No capsule selected | `slider` | LIVE |
| IQ-02 | Knob select (style/context) | select | knobs | dirty | same | `combobox` | LIVE |
| IQ-03 | Save strip | button | `PATCH /agents/{id}/capsule` | disabled when `!_dirty \|\| _busy` | — | `button` | LIVE |
| IQ-04 | Reset strip | button | local | disabled when `!_dirty` | — | `button` | LIVE |
| IQ-05 | Message / empty | readout | — | “No capsule selected — knobs are not loaded.” | — | `status` | LIVE |

---

## 6. States and honesty

| State | Behavior |
|---|---|
| cognitive load fail | `_loadFailed` banner; gauges empty with error copy (not “0.0”) |
| neuromod empty | “No neuromodulator readings were reported.” |
| knobs dirty | Save enabled; derived readouts refresh after save |
| connector degraded | SS-07 + SB-01 show degraded; Memory still one home |
| planner | GATED chip with feature-flag reason — never a live-looking toggle that does nothing |

**Law:** neuromodulators render **raw server values only**. No invented percentages, no fake normalization bars.

---

## 7. Source map

| Source | Role |
|---|---|
| `webui/src/views/soma-cognitive-panel.ts` | SB-01…SB-55 cognitive surface |
| `webui/src/views/soma-settings-somabrain.ts` | SS-01…SS-09 connection knobs |
| `webui/src/components/soma-agent-iq.ts` | IQ-01…IQ-05 knob strip |
| `webui/src/components/soma-capsule-editor.ts` | CAP-01…CAP-07 |
| `admin/core/agentiq/settings.py` + `derivation.py` | 3 knobs → 12 derived |

End of Document
