# SOMA-UI-DUP-AUDIT-001 — Memory / Brain / Settings placement audit

## Document Control

| Field | Value |
|---|---|
| Document Title | Duplication audit & corrected wireframes — Memory, Brain, Settings, Models |
| Document Identifier | SOMA-UI-DUP-AUDIT-001 |
| Version | 1.0.0 |
| Date | 2026-10-13 |
| Status | Draft |
| Classification | Internal |
| Author | SomaTech Engineering (soma-ui-engineer) |
| Approver | — |
| ISO Reference | ISO 9241-210:2019 |
| Next Review | 2027-01-13 |
| Authority | `docs/design/SOMA-UI-IA-001.md` §2–§3 (single-home table is LAW) |
| Related | `SOMA-UI-CONTROL-MAPS-001.md`, `SOMA-UI-NAV-001.md`, `SOMA-UI-AGENT-FRONTEND-MASTER-001.md`, `SOMA-UI-NAV-AUDIT-001.md` |
| Rule | IA-001 over any earlier draft wireframe. Docs only — no product code in this issue. |

## Revision History

| Version | Date | Author | Description |
|---|---|---|---|
| 1.0.0 | 2026-10-13 | soma-ui-engineer | Operator audit: why Brain is in the right panel; full Memory/Brain/Settings/Models occurrence table; surface vs config separation; corrected wireframes; control-map deltas. |

---

## 0. Operator answers (short)

### Q1 — Why is Brain in the right panel?

**CORRECT. Keep it there. Do not move Brain to Settings-only.**

IA-001 §2.4 and §3 bind Brain to **one UI**: the right-canvas surface **UI-X-07**. The right panel *is* that canvas registry (`soma-right-panel.ts` SURFACES: Files…Brain…Desktop). Label `Brain` / key `brain` / id `UI-X-07` is the **cognitive live surface** (`<soma-cognitive-panel>`).

| Placement | Verdict | Why |
|---|---|---|
| Right canvas tab `Brain` (UI-X-07) | **CORRECT — the one home** | Live neuromods, sleep, per-agent cognitive params |
| Settings › SomaBrain tab | **CORRECT — but CONFIG only** | URL / namespace / retention / sleep interval / consolidation toggle. Not a second cognitive surface |
| Left rail | **CORRECT absence** | IA-001 forbids Brain in left rail |
| Welcome | **CORRECT absence** | No Brain card / headline |
| `/cognitive` · `/training` full-page mount | **WRONG — second home** | Competing full-page cognitive surface (see §2) |

Settings must **not** absorb the cognitive surface. IA-001: “SomaBrain settings tab is CONFIG not the cognitive surface.” Settings knobs ≠ live Brain.

### Q2 — Are Memory and Brain duplicated?

**Not as content homes. Memory and Brain are different features with different homes.**

| Feature | One home | What it shows |
|---|---|---|
| **Memory** | `/memory` (UI-S-04) | Stored memories, recall, forget, Remember form |
| **Brain (cognitive live)** | canvas UI-X-07 | Neuromodulators, sleep/consolidation, adaptation params |
| **SomaBrain (config)** | Settings › SomaBrain | Operator endpoint, retention, sleep interval |

They share *status language* (Brain connected / memory_ok) and Memory may *call* the brain API. That is **data dependency, not UI duplication**.

**What does look like duplication today (must fix):**

1. Cognitive panel has **two mounts**: canvas UI-X-07 **and** `/cognitive` · `/training` full page.
2. `soma-settings-somabrain.ts` still deep-links **“Open /cognitive”** — promotes the second home.
3. Control Maps §3 “SOMABRAIN MANAGER” mixes live neuromods + capsule knobs + diagnostics in one wireframe — blurs surface vs config.
4. Latent `soma-welcome-dashboard.ts` still ships Memory + Settings action cards (IA-001 §2.1 forbidden).

### Q3 — Should Brain live only in Settings, not the right panel?

**No.** Settings is the only home for **Models / Voice / Channels config**. Brain’s **live cognitive surface** is canvas-only. Moving Brain into Settings would create a second cognitive UI or bury a live surface under config forms. Keep the three-way split in §3.

---

## 1. Single-home law (copy from IA-001 §3 — binding)

| Feature | Home | Allowed deep links | Forbidden |
|---|---|---|---|
| Composer / chat | `/chat` | welcome CTA | — |
| Conversations | left rail | ⌘K | — |
| **Memory** | `/memory` | left rail · C2 Open Memory · composer “Memory Context” | welcome card · canvas tab · mini-panel |
| **Models** | `/settings/models` | model chip · ⌘K | left rail · welcome |
| **Channels** | `/settings/channels` (Integrations) | Settings only | left rail · welcome |
| **Brain (live cognitive)** | canvas **UI-X-07** | status/IQ click → **same surface** | left rail · welcome · second panel · full-page `/cognitive` |
| **Settings** | `/settings` | left rail · ⚙️ | welcome card |
| **Voice run** | composer mic | — | left rail |
| **Voice config** | Settings › Voice | — | chat chrome |
| **SomaBrain config** | Settings › SomaBrain | `/settings/somabrain` | cognitive widgets on this tab |

---

## 2. DUPLICATION AUDIT table

Legend: **CORRECT** = matches IA-001 · **WRONG** = violates IA-001 · **DEEP LINK OK** = allowed entry to the single home · **GAP** = missing required behavior · **LATENT** = wrong surface still in tree even if unmounted.

### 2.1 Memory

| # | file:line | What is there | Verdict | Correct form |
|---|---|---|---|---|
| M1 | `webui/src/views/soma-chat.ts:3009-3010` | Left rail nav-link `Memory` → `/memory` | **CORRECT** | The only chat-chrome Memory entry |
| M2 | `webui/src/views/soma-chat.ts:3237-3247` | C2 `Open Memory` → `/memory?turn=current` | **DEEP LINK OK** | C2 is readout + one link, not a Memory UI |
| M3 | `webui/src/components/soma-composer-menu.ts:148` | Composer menu → `/memory` | **DEEP LINK OK** | “Memory Context” path |
| M4 | `webui/src/views/soma-memory-view.ts` (whole) | Full Memory manager UI-S-04 | **CORRECT** | Sole Memory UI |
| M5 | `webui/src/components/soma-right-panel.ts` SURFACES | No `memory` key | **CORRECT** | Memory never on canvas |
| M6 | `webui/src/components/soma-welcome-dashboard.ts:18` | Welcome action card `Memory` | **WRONG** | Remove card (IA-001 §2.1). Welcome may use ambient glyph only |
| M7 | `webui/src/views/soma-chat.ts:3215-3219` | Top strip Memory status dot + “Memory” label | **CORRECT (ambient)** | Micro-row indicator, not a home |
| M8 | `docs/design/SOMA-UI-NAV-001.md:111` | “Never: canvas tab, welcome card, chat mini-panel” | **CORRECT (doc)** | Keep; enforce M6 |

### 2.2 Brain (live cognitive surface)

| # | file:line | What is there | Verdict | Correct form |
|---|---|---|---|---|
| B1 | `webui/src/components/soma-right-panel.ts:69` | Surface `{ key: 'brain', id: 'UI-X-07', label: 'Brain' }` | **CORRECT** | The one Brain UI |
| B2 | `webui/src/components/soma-right-panel.ts:857-858` | `case 'brain': <soma-cognitive-panel>` | **CORRECT** | Same component as live surface |
| B3 | `webui/src/main.ts:272-275` | `/cognitive` · `/training` → full-page `soma-cognitive-panel` | **WRONG** | Delete route **or** redirect to `/chat` + `workspaceStore.setSurface('brain')`. No second home |
| B4 | `webui/src/views/soma-settings-somabrain.ts:708-714` | Button `Open /cognitive` | **WRONG** | Replace with “Open Brain surface” → chat + `setSurface('brain')` |
| B5 | `webui/src/views/soma-settings-somabrain.ts:727-728` | Honest note “Cognitive knobs are per-agent on /cognitive” | **WRONG (copy)** | “on the Brain canvas surface (UI-X-07)” |
| B6 | `webui/src/views/soma-chat.ts:3008-3015` | Left rail = Memory + Settings only | **CORRECT** | No Brain in left rail |
| B7 | `webui/src/components/soma-agent-header.ts:266` | IQ badge `@click → setSurface('brain')` | **DEEP LINK OK** | Status/IQ click opens **same** surface (IA-001 §2.4) |
| B8 | `webui/src/components/soma-status-dot.ts:30-31` | `:host([interactive])` styled but **no click handler** | **GAP** | Optional: brain/mem dots may open same surface; today they are non-interactive (honest) |
| B9 | `webui/src/views/soma-chat.ts:3202-3204` | Brain status dot + label in top vital row | **CORRECT (ambient)** | 12px language, not a banner |
| B10 | Welcome / left rail Brain cards | none found | **CORRECT** | Forbidden placements absent |
| B11 | `docs/design/SOMA-UI-NAV-001.md:55` | Route table lists `/cognitive` as UI-X-07 home | **WRONG (doc)** | Align to IA-001: canvas only |
| B12 | `docs/design/SOMA-UI-NAV-001.md:114` | “Brain home = `/cognitive` + canvas Brain” | **WRONG (doc)** | One home: canvas UI-X-07 |

### 2.3 SomaBrain Settings (config, not cognitive surface)

| # | file:line | What is there | Verdict | Correct form |
|---|---|---|---|---|
| S1 | `webui/src/views/soma-settings.ts:661` | Tab `SomaBrain` | **CORRECT** | Config home |
| S2 | `webui/src/views/soma-settings-somabrain.ts:517-623` | URL, namespace, retention, sleep_interval, consolidation | **CORRECT** | Operator/infra knobs |
| S3 | `webui/src/views/soma-settings-somabrain.ts:646-696` | Connector status (read-only health) | **CORRECT** | Status for *config*, not neuromod meters |
| S4 | `webui/src/views/soma-settings-somabrain.ts:700-706` | `Open /memory` deep link | **DEEP LINK OK** | Allowed Memory entry |
| S5 | `webui/src/views/soma-cognitive-panel.ts:590-593` | “SomaBrain Connected/Unavailable” in cognitive sidebar | **CORRECT (status)** | Status of live surface, not settings UI |
| S6 | Control Maps §3.1 wireframe | Neuromod + Sleep + **IQ knobs** + diagnostics on one “SomaBrain Manager” | **WRONG (doc)** | Split: UI-X-07 live vs Settings config (see §5) |
| S7 | `soma-chat.ts` dock `soma-agent-iq` (3309-3335) | Live Capsule knobs in chat dock | **AMBIGUOUS** | Persona knobs live in Settings › Agent + Capsule; dock is a *live tune* affordance, not a Memory/Brain home. Label must say “Capsule knobs”, never “Brain settings” |

### 2.4 Models

| # | file:line | What is there | Verdict | Correct form |
|---|---|---|---|---|
| Mo1 | `webui/src/views/soma-settings.ts:656` | Settings tab `Models` | **CORRECT** | Only Models UI |
| Mo2 | `webui/src/main.ts:336-343` | `/settings/models` deep-links Settings activeTab=models | **CORRECT** | Same shell |
| Mo3 | `webui/src/views/soma-chat.ts:3264-3272` | Model chip → `/settings/models` | **DEEP LINK OK** | Allowed |
| Mo4 | Left rail (`soma-chat.ts:3008-3015`) | No Models link | **CORRECT** | IA-001 forbids Models in rail |
| Mo5 | `soma-settings.ts:989-1018` | Models hub card + “Open Models Settings” | **CORRECT** | Within Settings shell |
| Mo6 | Welcome action cards | No Models card in `_renderWelcome` | **CORRECT** | — |

### 2.5 Settings / welcome / chrome

| # | file:line | What is there | Verdict | Correct form |
|---|---|---|---|---|
| W1 | `soma-chat.ts:3403-3415` | Welcome Quick: Files · Modules · New chat | **CORRECT** | IA-001 §2.1 |
| W2 | `soma-chat.ts:3418-3446` | Connect channels (unconfigured) | **CORRECT** | Allowed when unconfigured |
| W3 | `soma-chat.ts:3449-3500` | System RAM/CPU | **CORRECT** | Diagnostics-backed |
| W4 | `soma-welcome-dashboard.ts:16-20` | New Chat · Memory · Settings cards | **WRONG (latent)** | Memory/Settings cards forbidden; component exported (`components/index.ts:21`) but not routed — **delete or rewrite** |
| W5 | `soma-chat.ts:3012-3013` | Left rail Settings → `/settings` | **CORRECT** | Only Settings entry |
| W6 | `docs/design/SOMA-UI-NAV-001.md:98` | LEFT lists `/settings/models` | **WRONG (doc)** | Left rail = Memory + Settings only (IA-001 §2.2) |

---

## 3. Three surfaces that must not overlap

```
┌─────────────────────────────────────────────────────────────────────────┐
│  A. MEMORY PAGE (UI-S-04)          route /memory                        │
│     Purpose: operate stored memories                                   │
│     Shows: list/recall · scores · forget · Remember form · counts      │
│     APIs:  GET /memory/ · POST /memory/recall|save|forget              │
│     Never: neuromod values · IQ knobs · URL/retention config           │
├─────────────────────────────────────────────────────────────────────────┤
│  B. BRAIN LIVE SURFACE (UI-X-07)   canvas tab only                     │
│     Purpose: see & tune live cognitive state for the selected agent    │
│     Shows: neuromod raw values · sleep/consolidation · adaptation      │
│            params · activity log · Trigger Sleep / Reset Adaptation    │
│     APIs:  GET /somabrain/cognitive/state/{id}                         │
│            GET /somabrain/cognitive/sleep/status/{id}                  │
│            PATCH /somabrain/cognitive/params/{id}                      │
│            POST …/sleep/{id} · …/adaptation/reset/{id}                 │
│     Never: URL/namespace/retention · Memory list · model roles         │
│     Entries: canvas Brain tab · IQ/status click → same surface         │
├─────────────────────────────────────────────────────────────────────────┤
│  C. SOMABRAIN SETTINGS (UI-S-56)   Settings › SomaBrain                │
│     Purpose: operator-owned connector + retention config               │
│     Shows: URL · namespace · retention_days · sleep_interval           │
│            consolidation_enabled · connector status · honest gaps      │
│     APIs:  GET/PUT /core/settings/somabrain · GET /core/brain-connector│
│     Never: neuromod meters · adaptation sliders · Memory rows          │
│     Deep links (allowed): /memory · open Brain surface (not /cognitive)│
└─────────────────────────────────────────────────────────────────────────┘
```

| Question | Answer lives in |
|---|---|
| “What did Soma remember?” | **A** Memory page |
| “What is the brain doing right now?” | **B** Brain surface |
| “Where does SomaBrain connect / how long is retention?” | **C** Settings › SomaBrain |
| “Which model answers chat?” | Settings › **Models** |
| “Enable SomaBrain memory integration toggle?” | Settings feature flags / Advanced — not Memory page |

---

## 4. CORRECTED wireframes (one home each)

### 4.1 Chat chrome (UI-S-07)

```
┌─ left rail ────────┐┌─ chat column ──────────────────────────┐┌─ right canvas ─────────────┐
│ SOMA          [◀]  ││ TOP thin: time · ◉brain ○sync ◌mem     ││ [Files][Tools][Browser†]   │
│ [🔍 Search…]       ││       · 🔔 · project · (NO settings)   ││ [Editor][Debug][Capsule]   │
│ [ + New chat ]     ││ C1 title · model chip → Settings/Models││ [Brain][Desktop†]          │
│ TODAY              ││     Pause Nudge Stop Reset             ││ ─────────────────────────  │
│ ▸ Analyze Q3       ││ C2 recall n · [Open Memory] → /memory  ││ ONE surface active:        │
│ ▸ Fix WS bug       ││ C3 stream · tools · HITL               ││  Brain = UI-X-07           │
│ YESTERDAY          ││ C5 composer · attach · mic · queue     ││  (cognitive panel)         │
│ ▸ API docs         ││    menu “Memory Context” → /memory     ││                            │
│ ────────────────   ││                                      ││  NO Memory tab             │
│ 🧠 Memory → /memory││  [dock: Capsule knobs — label honest] ││  NO Settings tab           │
│ ⚙ Settings → /set. ││                                      ││                            │
│ ────────────────   ││                                      ││                            │
│ 👤 User       [↗]  ││                                      ││                            │
└────────────────────┘└──────────────────────────────────────┘└────────────────────────────┘
```

| Rail item | Allowed | Forbidden |
|---|---|---|
| Search · New chat · chat list | ✓ | — |
| Memory (one) | ✓ → `/memory` | second Memory UI |
| Settings (one) | ✓ → `/settings` | Models / Channels / Brain / Voice links |
| User + logout | ✓ | — |

### 4.2 Right canvas (UI-X-01…08) — Brain once

```
[Files] [Tools] [Browser†] [Editor] [Debug] [Capsule] [Brain] [Desktop†]
                                                              ▲
                                                              │
                                              ONLY Brain UI (UI-X-07)
                                              hosts <soma-cognitive-panel>

┌─ UI-X-07 Brain ────────────────────────────────────────────────────────┐
│ ● SomaBrain Connected · agent: … · (raw API numbers only)             │
│ ── Neuromodulator readings ────────────────────────────────────────── │
│   DA  0.62    5-HT  0.41    NE  0.73    ACh  0.55   (no fake % bars)  │
│ ── Sleep ──────────────────────────────────────────────────────────── │
│   state: Awake · last sleep: … · [Trigger Sleep Cycle]                │
│ ── Adaptation params (per-agent, PATCH …/params/{id}) ─────────────── │
│   learningRate [ ]  explorationRate [ ]  attentionSpan [ ]            │
│ ── Memory params ──────────────────────────────────────────────────── │
│   consolidationRate [ ]  emotionalSensitivity [ ]                     │
│   [Apply Changes] [Reset Adaptation]                                  │
│ ── Activity log ───────────────────────────────────────────────────── │
└───────────────────────────────────────────────────────────────────────┘

† gated surfaces stay present-but-disabled with reason (REQ-UIX-020)
```

**Do not also mount this component at `/cognitive`.** Deep links and status clicks must land on this surface.

### 4.3 Settings (only Models / Voice / Channels / SomaBrain-config home)

```
┌─ Settings sidebar ────────┐┌─ Settings main ─────────────────────────────────┐
│ Settings                  ││ header: <Tab> Settings · [Save Changes]        │
│ Agent                     ││                                                │
│ Models     ← ONLY Models  ││  (tab body — one of:)                          │
│ Voice      ← ONLY Voice   ││                                                │
│ Interface                 ││  Models: roles ×5 · providers · Vault keys     │
│ Tools                     ││  Voice: personas · TTS/STT · /voice/* links    │
│ Integrations ← Channels   ││  Integrations: channels + Vault keys           │
│ SomaBrain   ← CONFIG only ││  SomaBrain: URL · NS · retention · sleep int.  │
│ Connectivity              ││         consolidation · connector status       │
│ Advanced                  ││         [Open /memory] [Open Brain surface]    │
│ [← Back to Chat]          ││         honest gaps (no fake knobs)            │
└───────────────────────────┘└────────────────────────────────────────────────┘
```

SomaBrain tab **must not** render neuromod gauges or adaptation sliders.

### 4.4 Memory (UI-S-04) — sole Memory home

```
┌─ /memory ─────────────────────────────────────────────────────────────┐
│ 🧠 Memory          [Search recall…] [filter] [Remember]              │
│ WM —   LTM —   last write —   (API numbers or — ; never invent)      │
│ [queued banner if memory_ok false — honest _memoryUnavailable]       │
│ ───────────────────────────────────────────────────────────────────── │
│ ▣ score · text · source · [Open] [Forget] [Copy coord]               │
│ …                                                                    │
│ Remember [textarea]                         [Save]  → /memory/save   │
│ Probe    [query]                            [Run]   → /memory/recall │
│                                                                      │
│ NO neuromod · NO IQ knobs · NO URL/retention · NO canvas tab         │
└──────────────────────────────────────────────────────────────────────┘
```

### 4.5 SomaBrain (config) vs Brain (live) side-by-side

```
Settings › SomaBrain (CONFIG)              Canvas UI-X-07 (LIVE)
─────────────────────────────              ─────────────────────
URL / namespace / retention_days            Neuromod raw values
sleep_interval (settings field)            Sleep state + trigger
consolidation_enabled (flag)               Adaptation params (PATCH)
connector status (health)                  Memory params (per-agent)
Open /memory                               Activity log
Open Brain surface (NOT /cognitive)        Reset adaptation
Honest gaps (Vault token, BrainSetting)    No endpoint/retention fields
```

---

## 5. Control maps deltas (`SOMA-UI-CONTROL-MAPS-001.md`)

| Section | Today | Delta required |
|---|---|---|
| §2 MEMORY MANAGER | Home `/memory` | **Keep.** Clarify MM-08 “Brain status” = badge only (not a Brain home). Label “Save to Brain” → **“Save memory”** (binding is `/memory/save`) to avoid Brain-home confusion |
| §3 SOMABRAIN MANAGER | One wireframe mixes neuromod + knobs + diagnostics | **Split into:** |
| | | **3A UI-X-07 Brain live** — SB-01…06 readouts · sleep · adaptation/memory params · Trigger Sleep · Reset Adaptation · activity log. Binding: cognitive state/params/sleep routes |
| | | **3B Settings › SomaBrain config** — ST-SB URL · namespace · retention_days · sleep_interval · consolidation_enabled · connector status · Open memory · **Open Brain surface**. Binding: `/core/settings/somabrain`, `/core/brain-connector` |
| | | Remove capsule IQ knobs (intelligence/autonomy/style) from §3 — those are **Settings › Agent / Capsule** (ST-22), not Brain |
| §4 COMMAND PALETTE | “Switch canvas · Brain · surface” | **Keep** (allowed deep link to UI-X-07). Remove any “Open /cognitive” command |
| §5 CHAT | CH-04 Memory rail · CH-05 Settings rail | **Keep** (CORRECT). Add note: no Models/Brain rail rows |
| §6.3 | ST-22 IQ knobs under Tools/Agent/SomaBrain | **Move/label** ST-22 as Agent/Capsule only — not SomaBrain tab |
| §7 CANVAS | UI-X-07 Brain \| panel | **Keep.** Add: “sole Brain UI; `/cognitive` is not a second home” |

### Suggested new/changed control IDs

| ID | Label | Binding | Status |
|---|---|---|---|
| SB-L01 | Neuromod raw values | `GET /somabrain/cognitive/state/{id}` | LIVE |
| SB-L02 | Sleep state / last | `GET /somabrain/cognitive/sleep/status/{id}` | LIVE |
| SB-L03 | Trigger Sleep | `POST /somabrain/cognitive/sleep/{id}` | LIVE |
| SB-L04 | Adaptation params | `PATCH /somabrain/cognitive/params/{id}` | LIVE |
| SB-L05 | Reset Adaptation | `POST …/adaptation/reset/{id}` | LIVE |
| SB-C01 | URL / NS / retention / sleep_interval / consolidation | `GET/PUT /core/settings/somabrain` | LIVE |
| SB-C02 | Connector badge | `GET /core/brain-connector` | LIVE |
| SB-C03 | Open Memory | route `/memory` | LIVE |
| SB-C04 | Open Brain surface | chat + `workspaceStore.setSurface('brain')` | **REPLACE** `Open /cognitive` |
| CH-04a | IQ / status click | `setSurface('brain')` | LIVE (agent-header) |

---

## 6. Required code/doc moves (implementation backlog — no code in this issue)

| Priority | Item | File | Fix |
|---|---|---|---|
| P0 | Kill second Brain home | `main.ts:272-275` | Remove `/cognitive`·`/training` full-page mount **or** redirect to `/chat` + `setSurface('brain')` |
| P0 | Stop promoting second home | `soma-settings-somabrain.ts:708-714` | “Open Brain surface” instead of “Open /cognitive” |
| P0 | Fix copy | `soma-settings-somabrain.ts:727-728` | Point cognitive knobs to UI-X-07, not `/cognitive` |
| P1 | Latent welcome Memory/Settings cards | `soma-welcome-dashboard.ts:16-20` | Delete cards or delete component (unrouted) |
| P1 | Doc drift | `SOMA-UI-NAV-001.md:55,98,114` | Align to IA-001 single-home table |
| P1 | Doc drift | `SOMA-UI-CONTROL-MAPS-001.md` §3 | Split live vs config (§5 above) |
| P2 | Optional status→surface | `soma-status-dot` / chat vitals | If product wants IA “status click → same surface”, add interactive brain dot → `setSurface('brain')` (already true for IQ badge) |
| P2 | Honest knob dock label | `soma-chat.ts` dock | Label “Capsule knobs”, not Brain settings |

### Acceptance (re-check after fixes)

- [ ] Exactly one mount of `soma-cognitive-panel` in the product (canvas UI-X-07)
- [ ] No `/cognitive` full-page cognitive UI (or hard redirect to canvas)
- [ ] Settings › SomaBrain has zero neuromod/adaptation controls
- [ ] Welcome has zero Memory / Settings / Models / Brain cards
- [ ] Left rail = Memory + Settings only
- [ ] Memory never appears as a canvas tab
- [ ] Models only under Settings › Models (+ chip deep link)
- [ ] Playwright: status/IQ click opens the **same** Brain surface as the canvas tab

---

## 7. Traceability

| Finding | Traces to |
|---|---|
| Brain = canvas only | IA-001 §2.4, §3 · right-panel UI-X-07 |
| Memory = `/memory` only | IA-001 §2.2–2.3, §3 · UI-S-04 |
| Settings = Models/Voice/Channels home | IA-001 §2.5 |
| `/cognitive` second home | main.ts:272 · NAV-001:55 · settings-somabrain:708 |
| Welcome cards | welcome-dashboard.ts:18-19 · IA-001 §2.1 |
| Control map mix | CONTROL-MAPS §3 vs IA-001 §2.5 |

---

*End of duplication audit. Authority: IA-001. Code changes require a separate GO wave.*
