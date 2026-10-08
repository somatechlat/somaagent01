# SOMA-UI-IA-001 — Information architecture audit (corrected)

## Document Control

| Field | Value |
|---|---|
| Document Title | Agent Soma — IA audit & single-home rules |
| Document Identifier | SOMA-UI-IA-001 |
| Version | 1.0.0 |
| Date | 2026-10-08 |
| Status | **Authoritative for all mocks** |
| Reference | Agent Zero `webui/components/welcome/welcome-screen.html`, `sidebar/left-sidebar.html` (structure only) |
| Rule | **No triplicated homes.** Settings never in the chat left rail. |

---

## 1. What was wrong (audit)

| Triplication | Where it appeared | Verdict |
|---|---|---|
| **Memory as welcome hero card** | UI-S-29, old `soma-chat` welcome, early CHAT-WORKSPACE draft | **WRONG** — Memory is utility, not a start-work action |
| **Models + Channels in welcome** | UI-S-29, `soma-chat` welcome | **WRONG** — those are Settings |
| **Models in chat left rail** | UI-S-07, CHAT-WORKSPACE §3, `soma-chat` nav | **WRONG** — Models = Settings › Models only |
| **Channels in chat left rail** | `soma-chat` nav | **WRONG** — Settings › Integrations only |
| **Brain in 3+ places** | left rail + canvas + facet + status click | **WRONG** — Brain **surface only** (UI-X-07) + optional status click opens that same surface |
| **Memory canvas tab** | early UI-X drafts | **WRONG** — deleted |
| **Settings / Models / Channels cluster on welcome** | UI-S-29 | **WRONG** |

---

## 2. Correct IA (binding)

### 2.1 Welcome (first screen after login) — A0 pattern, Soma skin

**Primary CTA = the composer.**  
**Brain status = 12px ambient indicator in chat top** (A0 `sync-status` language) — never a banner.  
**Memory = visual aide** (glyph / soft glow / ghost chip) — never principal text.  
**Source:** Agent Zero welcome + `_discovery` + `system-resources` + `sync-status`.

```
┌────────────────────────────────────────────────────────────────┐
│  [≡] [S] SOMA        14:32  ◉  ○  ◌  🔔  ▢ project             │
│                      brain sync mem                            │
│                                                                 │
│                      Hello! I'm Soma                            │
│                  How can I help you today?                      │
│                                                                 │
│           ┌────────────────────────────────────────┐            │
│           │  Message Soma…                    ➤  │            │
│           └────────────────────────────────────────┘            │
│                                                                 │
│     [ real warnings only · dismissable ]                        │
│                                                                 │
│     Quick: [Files] [Modules] [New chat]   (no Memory / Settings) │
│                                                                 │
│     Connect channels                                            │
│     [Telegram] [WhatsApp] [Email]   (if unconfigured)           │
│                                                                 │
│     System   RAM ████ 62% · CPU 24% · Disk 43%                  │
│                                                                 │
│     Footer: SomaTech · Cognitive AI Agent                       │
└────────────────────────────────────────────────────────────────┘
```

| Allowed on welcome | Forbidden on welcome |
|---|---|
| Hero + **composer** (hero) | Write / Research / Analyze / Code cards |
| Status **micro-row** (Brain ◉ · Sync ○ · Memory ◌) | Memory / Brain hero cards or headline text |
| Quick Actions: Files · Modules · New chat only | **Memory / Settings / Models / Channels / Brain cards** |
| Connect Channels (TG/WA/Email) when unconfigured | Settings cluster in Band A |
| System Resources (RAM/CPU/Disk) from diagnostics API | Fake metrics / invented banners |
| Real operational warnings | Projects picker without API |

Quick Actions open their **single home**. Channels CTA → bridges/Integrations (Vault keys).  
System panel hidden if diagnostics API is down.  
\*Tasks only when scheduler is live.

### 2.2 Chat left rail (once in every conversation)

```
┌──────────────────────┐
│  SOMA           [◀]  │
│  ┌────────────────┐  │
│  │ 🔍 Search…     │  │
│  └────────────────┘  │
│  [ + New chat ]      │
│                      │
│  TODAY               │
│  ▸ Analyze Q3 data   │
│    Soma · 2h         │
│  ▸ Fix WS bug        │
│  YESTERDAY           │
│  ▸ API docs          │
│                      │
│  ─────────────────   │
│  🧠 Memory           │  ← ONLY Memory entry in chat chrome
│  ⚙ Settings          │  ← ONLY Settings entry (Models inside)
│  ─────────────────   │
│  👤 Test User  [↗]   │  ← profile + logout
└──────────────────────┘
```

| In left rail | Not in left rail |
|---|---|
| Search · New chat · **chat list** (rename/export/delete) | Models |
| **Memory** (→ `/memory`) | Channels |
| **Settings** (→ `/settings`) | Brain |
| User + logout | Voice · Plugins · Billing |

**A0 parity:** chats + tasks + bottom preferences. We put **Memory + Settings** in the bottom zone (same place A0 puts preferences), not as a second nav dump.

---

### 2.3 Chat column (in-thread)

| Zone | Content | Memory? |
|---|---|---|
| C1 header | title · model chip · Pause/Nudge/Stop/Reset | no |
| C2 pulse | **readout only** `recall n · [Open Memory]` | link only |
| C3 stream | bubbles · process groups · HITL | no |
| C5 composer | attach · voice · queue · export | “Memory Context” menu → `/memory` |

C2 is **not** a Memory UI. One link.

---

### 2.4 Right canvas — surfaces (one Brain)

```
[Files] [Tools] [Browser†] [Editor] [Debug] [Capsule] [Brain] [Desktop†]
```

| Feature | Canvas | Elsewhere | Count |
|---|---|---|---|
| **Brain** | **UI-X-07 only** | Status neuromod click → same surface | **1 UI** |
| **Memory** | **none** | Left rail `/memory` + C2 link | **1 UI** |
| **Models** | none | Settings › Models | **1 UI** |
| **Capsule** | UI-X-06 | — | 1 |
| Files / Tools / Editor / Debug | UI-X | attach menu may open Files drawer | 1 each |

---

### 2.5 Settings workspace (only home for Models / Voice / Channels)

```
Settings
├── Agent
├── Models          ← ONLY Models UI
├── Voice           ← ONLY Voice config UI
├── Interface
├── Tools
├── Integrations    ← Channels + Vault keys (ONLY)
└── Advanced
```

Chat model chip → Settings › Models. No second models library.

---

## 3. Single-home table (copy this into every mock)

| Feature | Home | Allowed deep links | Forbidden |
|---|---|---|---|
| **Composer / chat** | `/chat` | welcome CTA | — |
| **Conversations** | left rail | ⌘K | — |
| **Memory** | `/memory` | left rail · C2 Open Memory · composer “Memory Context” | welcome card · canvas tab · mini-panel |
| **Models** | `/settings/models` | model chip · ⌘K | left rail · welcome |
| **Channels** | `/settings/channels` (Integrations) | Settings only | left rail · welcome |
| **Brain** | canvas UI-X-07 | status neuromod → same | left rail · welcome · second panel |
| **Settings** | `/settings` | left rail · ⚙️ | welcome card |
| **Voice run** | composer mic | — | left rail |
| **Voice config** | Settings › Voice | — | chat chrome |

---

## 4. Mock files this corrects

| File | Change | Status 2026-10-07 |
|---|---|---|
| `UI-S-07-chat-workspace.md` | Left rail = Memory + Settings only; no Models/Channels/Brain | **CODE STILL WRONG** — `soma-chat.ts:1960` still has Models in left rail |
| `UI-S-29-login.md` | Welcome = composer hero + task cards only | **CODE STILL WRONG** — `_renderWelcome` still action-card grid, composer is not hero |
| `SOMA-UI-CHAT-WORKSPACE-001.md` | Welcome + Band B + Brain-once | Band B mock still lists Models/Channels |
| `UI-X-07-brain.md` | Brain is the one brain UI | PASS (canvas only) |
| `UI-S-04-memory.md` | Remains sole Memory UI | PASS (left-rail `/memory`) |
| `SOMA-UI-NAV-001.md` | Align one-home table | GAP-N1/N2 still open (see NAV-AUDIT) |

### 4.1 Agent Zero layout (source of truth for chrome)

Verified against `~/Downloads/agent-zero-main/webui/`:

| Zone | A0 does | Soma must do | Live gap |
|---|---|---|---|
| **Chat top** | Time/date · sync status · notifications · project selector. **No settings cluster.** (`chat/top-section/chat-top.html`) | Same thin strip. Settings live in the left-rail bottom / `/settings`, never as chat-top pills | `soma-chat` header still packs Agent ▾ · model · mode STD/DEV/TRN/ADM · Pause/Nudge/Stop/Reset — **WRONG** |
| **Welcome** | Hero greeting + **composer as primary CTA** + Quick Actions (Projects/Memory/Tasks/Files/Settings/Plugins) + banners + system card. (`welcome/welcome-screen.html`) | Hero + composer hero + task starters (Write/Research/Analyze/Code). No Settings/Models/Channels/Brain/Memory cards per §2.1 | `_renderWelcome` is a 6-card action grid including Surfaces — competes with composer |
| **Left rail** | Header icons · quick actions · chats · tasks · **bottom: preferences only**. (`sidebar/left-sidebar.html`) | Search · New chat · chat list · Memory · Settings · user | Models still in `nav-links` |
| **Right canvas** | Files/Tools/… surfaces. One Brain surface | Same registry `soma-right-panel` | PASS |
| **API** | `callJsonApi` / `fetchApi` + WS — real endpoints only (`js/api.js`, `js/websocket.js`) | Real Django Ninja + `/ws/v2/chat` only. No mock fallbacks | wiring exists; honesty of `memory_hits` still collapses outage→empty |

---

## 5. Acceptance

- [ ] Welcome has **no** Memory / Models / Channels / Settings / Brain cards  
- [ ] Left rail has **exactly one** Memory and **one** Settings  
- [ ] Models never in chat chrome  
- [ ] Brain appears once as a surface (plus status → same surface)  
- [ ] Memory never on canvas  
- [ ] Chat top is thin (time · conn · notifications · project) — no settings pills  
- [ ] Welcome composer is the primary CTA (A0 pattern)  
- [ ] Every control bound to a real API/WS frame — Playwright proves memory recall in chat, not curl  

End of Document
