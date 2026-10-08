# UI-S-07 — Chat workspace (Agent Soma)

Screen UI-S-07 · Routes: `/` · `/chat` · `/chat/:id` · `/workspace` (all mount `soma-chat`)  
Canonical bands: `SOMA-UI-CHAT-WORKSPACE-001.md` · IA law: `SOMA-UI-IA-001.md` · Live: `webui/src/views/soma-chat.ts`

**Product:** Agent Soma enterprise operator chat. Real APIs only. **Memory once (`/memory`).**  
Forbidden: word “slot” · SaaS / Eye of God branding · invented metrics · mock data · Settings/Models/Channels/Brain/Memory cards on welcome.

---

## 0. Design law (this screen)

| Rule | Binding |
|---|---|
| **Composer is the hero** | Welcome state: nothing competes with the input |
| **One home per feature** | Memory → `/memory` · Models → Settings›Models · Channels → Settings›Integrations · Brain → canvas UI-X-07 |
| **Thin chat top** | Time · connection · notifications · project. **No settings cluster** |
| **Left rail** | Search · New chat · chats · **Memory** · **Settings** · user. No Models/Channels/Voice |
| **Honest values** | Every `‹live›` from a named API/WS frame. Missing → `—` or GATED. Never fabricate |
| **Turn controls live in C1** | Pause / Nudge / Stop / Reset sit with the turn, not in global chrome |

---

## 1. State A — WELCOME / EMPTY CHAT (first screen after login)

**A0 source:** `welcome-screen.html` · `sync-status.html` · `_discovery` cards · `_30_system_resources.py`  
**Soma APIs:** `GET /core/brain-connector` · `GET /api/v2/memory/` · `GET …/somabrain/admin/diagnostics` · `GET/POST /api/v2/bridges/channels` · `GET /api/v2/notifications` · `GET /api/v2/chat/conversations`

---

### 1.0 Status micro-row (always on · Brain is an icon, never a banner)

```
  14:32    ◉     ○     ◌     🔔     ▢ Q3 Launch ▾
           │     │     │     │     └── project (omit if no API)
           │     │     │     └── notifications (badge if unread)
           │     │     └── Memory aide (muted glyph · pulse when LTM ready)
           │     └── Sync / WS
           └── BRAIN connector  ← 12px circle + tooltip
```

| State | Visual | Token | Tooltip |
|---|---|---|---|
| Healthy | filled disc r=6 | `#00c340` | `Brain · Connected` |
| Degraded | filled disc + soft pulse | `#ff6b00` | `Brain · Degraded` |
| Handshake | ring + `pendingPulse` 1.2s | `#f0a000` | `Brain · Connecting…` |
| Disconnected | stroked ring | `#e40138` | `Brain · Disconnected` |
| Unknown | hollow grey | `#6b7280` | `Brain · Status unavailable` |

- Size **12px** in chat top. `role="img"` + `aria-label` = tooltip text.
- Click → Brain surface (UI-X-07). Data: `GET /core/brain-connector` (existing poll).
- Memory glyph `◌` is an **aide only** — tooltip `Memory ready` / `Memory unavailable`. Never headline copy.

---

### 1.1 Complete welcome wireframe

```
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│ A · CHAT TOP 40px   [≡] [S] SOMA     14:32  ◉  ○  ◌  🔔 2  ▢ Q3 Launch ▾                     │
│                               brain sync mem  notifs project                                  │
├──────────────┬───────────────────────────────────────────────────────────────┬───────────────┤
│ B · LEFT     │              C · WELCOME (max-width 960 · centered)           │ D · CANVAS    │
│   264px      │                                                               │  collapsed    │
│  [S] Soma    │                      Hello! I'm Soma                          │  56px rail    │
│              │                   How can I help you today?                   │  [▤][⌘][🌐…]  │
│  🔍 Search   │                                                               │  NO Memory    │
│  + New chat  │              ╔══════════════════════════════════╗              │  tab          │
│              │              ║  Message Soma…          📎  🎤  ➤ ║              │               │
│  Conversations              ╚══════════════════════════════════╝              │               │
│  ──          │               + · Memory Context · Clear · Export              │               │
│  ▸ Q3 Launch │                                                               │               │
│  ▸ API docs  │         [ ⚠ real warnings only · dismiss × ]                  │               │
│              │         examples: Vault sealed · Brain disconnected           │               │
│  ──          │                                                               │               │
│  🧠 Memory   │         Quick actions                                          │               │
│  ⚙ Settings  │      ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐            │               │
│  ──          │      │Memory│ │ Files│ │Tasks*│ │Module│ │Setti│            │               │
│  👤 User     │      └──────┘ └──────┘ └──────┘ └──────┘ └──────┘            │               │
│  [Sign out]  │         (*Tasks only if scheduler API is live)                │               │
│              │                                                               │               │
│              │      Connect channels                      Manage ›           │               │
│              │      ┌──────────┐ ┌──────────┐ ┌──────────┐                  │               │
│              │      │ Telegram │ │ WhatsApp │ │  Email   │                  │               │
│              │      │ Connect  │ │ Connect  │ │ Connect  │                  │               │
│              │      └──────────┘ └──────────┘ └──────────┘                  │               │
│              │      (card only when UNCONFIGURED · else ● Connected chip)    │               │
│              │                                                               │               │
│              │      System                              [↻]            [×]   │               │
│              │      RAM  ██████████░░░░░░  62%   12.4 / 32 GB               │               │
│              │      CPU  ████░░░░░░░░░░░░  24%   8 cores                    │               │
│              │      (RAM+CPU only — diagnostics API; disk/load/net omitted)  │               │
│              │                                                               │               │
│              │         SomaTech · Cognitive AI Agent                         │               │
├──────────────┴───────────────────────────────────────────────────────────────┴───────────────┤
│ E · STATUS quiet   ready · model ‹live› · synced ‹live›                                      │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

### 1.2 What is ON the welcome (owner decision)

| # | Block | Role | Data |
|---|---|---|---|
| 1 | Hero | `Hello! I'm Soma` / `How can I help you today?` | static copy |
| 2 | **Composer** | Primary CTA — the only hero action | WS `chat.message` |
| 3 | **Status micro-row** | Brain ◉ · Sync ○ · Memory ◌ (ambient) | `GET /core/brain-connector` |
| 4 | Quick Actions | Files · Modules · New chat only (no Memory card) | routes/modals |
| 5 | Connect Channels | Telegram · WhatsApp · Email when unconfigured | `GET /api/v2/bridges/channels` |
| 6 | System | RAM · CPU · Disk · Load · Net meters | `GET …/somabrain/admin/diagnostics` |
| 7 | Warnings | Real operational issues only | connector / Vault / metrics |
| 8 | Recent | Last conversations (compact) | `GET /api/v2/chat/conversations` |
| 9 | Footer | `SomaTech · Cognitive AI Agent` | static |

### 1.3 What is OFF the welcome

| Forbidden | Why |
|---|---|
| Write / Research / Analyze / Code cards | Invented · not A0 · not product |
| Memory / Brain as hero cards or headline text | Memory is a **visual aide** |
| Models · Channels · Voice marketing grid | Wrong homes |
| Settings / Agent / mode cluster in Band A | A0 chat-top is thin |
| Fake RAM / invented banners / projects picker without API | Honesty |

---

### 1.4 Quick Actions map

| Card | Icon | Action | Home |
|---|---|---|---|
| Memory | — | **not on welcome** | left rail `/memory` only |
| Files | `folder_open` | open Files surface / file modal | UI-X-01 |
| Tasks | `schedule` | scheduler modal | **GATED** if no API |
| Modules | `extension` | `/settings/tools` | UI-S-55 |
| Settings | `settings` | `/settings` | UI-S-50 shell |

No `Website` wide card (A0 has it; Soma brand is not a marketing grid). Optional text link in footer only.

---

### 1.5 Connect Channels (A0 `_discovery` merge)

| id | Title | Copy | Shown when | CTA |
|---|---|---|---|---|
| `discovery-telegram` | Telegram | Chat on Telegram wherever you are. | no `bot_token` | `Connect` → Settings›Integrations / bridges |
| `discovery-whatsapp` | WhatsApp | Send and receive WhatsApp messages. | no `phone_number_id` | `Connect` → Settings›Integrations |
| `discovery-email` | Email | Let Soma read and send emails on your behalf. | no handler username | `Connect` → Settings›Integrations |

Configured → **connected chip** (dot `#22c55e` + name). Keys **Vault write-only**.  
API: `GET /api/v2/bridges/channels` kinds `telegram`/`whatsapp` (admin/bridges/models.py).

---

### 1.6 System Resources (A0 `_30_system_resources`)

| Meter | Format | Bar color |
|---|---|---|
| RAM | `used / total GB` + % | &lt;70% `#22c55e` · 70–85% `#f59e0b` · ≥85% `#ef4444` |
| CPU | `pct% (n cores)` | same thresholds |
| Disk | **omit** — not in diagnostics response | — |
| Load | `1 / 5 / 15` | text only |
| Net | `sent / recv` since boot | text only |

Source: `GET …/somabrain/admin/diagnostics` (psutil). Hide panel if API down. **Never invent numbers.**

---

### 1.7 Banners (real only)

No fictional `POST /banners` in admin. Derive warnings from live checks:

| Condition | Type | Copy | CTA |
|---|---|---|---|
| Brain disconnected | error | `Brain connector disconnected` | `Open Brain` |
| Brain degraded | warning | `Brain connector degraded` | `Open Settings` |
| Vault sealed | error | `Vault sealed — writes will refuse` | `Open Vault runbook` |
| Memory unavailable | warning | `Long-term memory unavailable` | `Open Memory` |

Dismissable (sessionStorage). Priority order: error &gt; warning &gt; info.

---

### 1.8 Design tokens

```
--status-ok: #00c340 · --status-warn: #ff6b00 · --status-bad: #e40138
--status-pending: #f0a000 · --status-idle: #6b7280
--status-size: 12px · radius 8px · meters 999px
A0 surface: color-mix(panel 78%, bg 22%) · blur(18px)
Accent CTA: #4248f1 → hover #353bc5
```

---

### 1.9 Welcome copy (verbatim)

| Element | Copy |
|---|---|
| Hero | `Hello! I'm Soma` |
| Sub | `How can I help you today?` |
| Composer | `Message Soma…` |
| Channels | `Connect channels` |
| Connect CTA | `Connect` |
| System | `System` |
| Empty chats | `No conversations yet. Start a new chat to begin.` |
| Brain ok tooltip | `Brain · Connected` |
| Memory aide | `Memory ready` |

---

## 2. State B — ACTIVE CONVERSATION

```
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│ A · CHAT TOP                                                                                   │
│  [≡]  [S] SOMA                    14:32   ● Connected   🔔 2   ▢ Q3 Launch ▾                  │
├──────────────┬───────────────────────────────────────────────────────────────┬───────────────┤
│ B · LEFT     │                 C · CHAT COLUMN                               │ D · CANVAS    │
│              │                                                               │  open 400px   │
│  [🔍 Search] │ C1  Analyze Q3 data                    [Pause][Nudge][Stop][⋯] │  [Files]      │
│  [+ New chat]│      Soma · ‹model from turn_meta› · streaming · 12.4s        │  [Tools]      │
│              ├───────────────────────────────────────────────────────────────┤  [Browser†]   │
│  TODAY       │ C2  🧠 recall 3 · wm 2 · ltm 1 · “Q3 revenue EU” (0.91)       │  [Editor]     │
│  ▸ Analyze…  │      [Open Memory] → /memory?turn=current                     │  [Debug]      │
│    Soma · 2h ├───────────────────────────────────────────────────────────────┤  [Capsule]    │
│  ▸ Fix WS…   │ C3  You                                      14:31           │  [Brain]      │
│  YESTERDAY   │     ┌──────────────────────────────────────────────┐          │  [Desktop†]   │
│  ▸ API docs  │     │ Analyze Q3 data for the EU market. Compare   │          │               │
│  ─────────── │     │ revenue vs plan and call out risks.          │          │  ┌─Tools────┐ │
│  🧠 Memory   │     └──────────────────────────────────────────────┘          │  │web_search│ │
│  ⚙ Settings  │     Soma · 14:31 · streaming                                   │  │success 1.2s│ │
│  ─────────── │     ┌──────────────────────────────────────────────┐          │  └──────────┘ │
│  👤 Test User│     │ Q3 EU revenue is **€4.2M** vs plan €4.8M     │          │  no Memory   │
│  [Sign out]  │     │ (−12%). Three risks:                          │          │  tab         │
│              │     │ 1. DACH pipeline slip…                       │          │               │
│              │     │ 2. Pricing exception rate…                    │          │               │
│              │     │ 3. Churn in mid-market…                       │          │               │
│              │     └──────────────────────────────────────────────┘          │               │
│              │     ⚙ web_search · success · 1.2s                [Expand]     │               │
│              │       query “Q3 revenue EU” · hits 3                          │               │
│              │     ⚙ remember · executed                           [Expand]     │               │
│              ├───────────────────────────────────────────────────────────────┤               │
│              │ C4  ⚠ Approve tool? web_search · “sensitive query”            │               │
│              │     [ Approve ]  [ Reject ]                                   │               │
│              ├───────────────────────────────────────────────────────────────┤               │
│              │ C5  ┌────────────────────────────────────────────────────┐    │               │
│              │     │ Reply to Soma…                          [📎][🎤][➤]│    │               │
│              │     └────────────────────────────────────────────────────┘    │               │
│              │       [+] Attach · Memory Context · Clear · Export            │               │
│              │       queue 2 [drop]   ·   Enter send · ⇧↵ newline           │               │
├──────────────┴───────────────────────────────────────────────────────────────┴───────────────┤
│ E · STATUS  turn 12.4s · ctx 8.2k · recall 3 · tools 2 · queue 2 · model ‹live› · synced 14:32│
│             DA ‹live›  5-HT ‹live›  NE ‹live›  ACh ‹live›   (omit row if cognitive API down)   │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
```

### Band contract

| Band | Contents | Data source |
|---|---|---|
| **A** Chat top | Collapse · SOMA · clock · connection · notifications · project | `GET /core/brain-connector` · project API · WS |
| **B** Left rail | Search · New chat · chat list · Memory · Settings · user | `GET /chat/conversations` · `/auth/me` |
| **C1** Turn header | Title · model · turn state · Pause/Nudge/Stop/Reset/⋯ | WS `chat.turn_meta` · `chat.pause/resume/stop/nudge/reset` |
| **C2** Memory pulse | `recall n · wm n · ltm n · top hit` + **Open Memory** link | `chat.turn_meta.memory_hits[]`. Outage ≠ empty |
| **C3** Stream | User/agent bubbles · process groups · HITL | WS `chat.delta` · `tool.*` |
| **C4** HITL | Approve / Reject | WS `tool.approval_request` → `tool.approval` |
| **C5** Composer | Input · attach · mic · send · queue · menu | WS `chat.message` · `POST /voice/transcribe` |
| **D** Canvas | Files·Tools·Browser†·Editor·Debug·Capsule·Brain·Desktop† | `soma-right-panel` registry. **No Memory tab** |
| **E** Status | Turn/context/recall/tools/queue/model/synced + neuromod | same frames. Fabricated values forbidden |

† GATED — blocking reason inline. Never a fake surface.

---

## 3. Control map → live API/WS

| # | Control | Binding |
|---|---|---|
| 1 | New chat | `POST /chat/conversations` |
| 2 | Conversation row | `GET /chat/conversations/:id/messages` |
| 3 | Rename / Export / Delete | `PATCH` / `GET …/export` / `DELETE /chat/conversations/:id` |
| 4 | Memory (rail) | `/memory` |
| 5 | Settings (rail) | `/settings` |
| 6 | Send | WS `chat.message` |
| 7 | Pause / Resume / Nudge / Stop / Reset | WS `chat.pause` · `chat.resume` · `chat.nudge` · `chat.stop` · `chat.reset` |
| 8 | Open Memory | `/memory?turn=current` |
| 9 | Tool expand | `soma-tool-timeline` args/result |
| 10 | HITL Approve / Reject | WS `tool.approval` |
| 11 | Queue drop | `soma-composer` clear `_queue` |
| 12 | Attach chips | sent with `chat.message` |
| 13 | Mic | `POST /voice/transcribe` |
| 14 | Export | JSON download `soma-chat-{id}.json` |
| 15 | Project picker | project API (top bar) |
| 16 | Notifications | `GET /notifications` (bell) |
| 17 | Surface rail | `soma-right-panel` tabs |
| 18 | Model chip (C1) | navigates `/settings/models` (read-only label) |

**Not shipped as enabled:** ⌘K palette · Voice left-rail entry · Band-E neuromod when cognitive API absent.

---

## 4. Field / behavior

| Field | Source | Behavior |
|---|---|---|
| Conversation title | WS `title_update` · PATCH | Default `New conversation`. Missing → `—` |
| Model label | `chat.turn_meta.model` | Never `iq_tier` |
| Context tokens / lanes | `chat.turn_meta` | Render only when server sent |
| Memory recall C2 | `memory_hits[]` | Count + top text + score. Outage: `Long-term memory unavailable this turn` + link. Empty: `recall 0 · nothing this turn` |
| Tool step | WS `tool.*` | Name + status always visible; `duration_ms` only if sent |
| Send blocked busy | local | `Still finishing the previous turn — message not sent` |
| Send blocked WS | local | `Not connected — message not sent` |
| Queue | typed while busy | Enqueue; drain one per idle; drop clears |

---

## 5. States (verbatim)

| State | Verbatim |
|---|---|
| welcome empty chat | `Welcome back, ‹first name›` / `What are we working on today?` |
| empty list | `No conversations yet. Start a new chat to begin.` |
| empty search | `No conversations match your search.` |
| list error | `Failed to load conversations. The request did not succeed.` |
| memory empty | `🧠 recall 0 · nothing this turn · [Open Memory]` |
| memory outage | `🧠 recall — · long-term memory unavailable · [Open Memory]` |
| tool empty | `No tool calls` |
| send busy | `Still finishing the previous turn — message not sent` |
| send offline | `Not connected — message not sent` |
| gated surface | `Requires a remote-desktop capability. Not available today.` |
| permission | `You do not have permission to post in this conversation.` |

---

## 6. Journey — first run → memory in chat (the product gate)

```
1. /login → Sign in
2. Land on State A (Welcome). Composer focused. No Memory/Models cards.
3. Click [ Files ] → opens file browser
4. Type “remember CODEWORD-ALPHA-77 is our launch token”
   → Enter
5. User bubble appears immediately (input cleared)
6. Streaming agent reply (no stop-string dump)
7. C2 shows recall hits from chat.turn_meta
8. ⋯ → New chat (fresh conversation)
9. Type “What codeword did I ask you to remember?”
10. Agent answers CODEWORD-ALPHA-77
11. Click [Open Memory] → /memory?turn=current shows the row
12. Left rail Memory is the only Memory home
```

**Gate:** step 10 must pass **in the browser**, not curl.

---

## 7. Breakpoints

| Width | Left | Chat | Canvas |
|---|---|---|---|
| ≥1440 | 280 | flex | 440 |
| ≥1200 | 264 | flex | 400 |
| ≥992 | 240 | flex | collapsible |
| ≥768 | overlay | flex | sheet |
| <768 | hamburger | flex | full-screen sheet |

Welcome stacks: hero → composer → tasks → recent. Never three equal columns of nav cards.

---

## 8. Related

- Chrome: `UI-S-00` · Memory: `UI-S-04` · Message detail: `UI-S-08` · Export: `UI-S-09` · Queue: `UI-S-10`
- Surfaces: `UI-X-01…08` · Login: `UI-S-29` · IA: `SOMA-UI-IA-001` · Bindings: `SOMA-UI-BINDINGS-001`

---

## 9. Acceptance checklist

- [ ] Welcome shows **no** Memory / Models / Channels / Settings / Brain cards
- [ ] Left rail has **exactly one** Memory and **one** Settings
- [ ] Chat top has **no** model/mode/agent settings cluster
- [ ] Composer is the welcome hero
- [ ] Task starters prefill composer only
- [ ] Models never in chat chrome (C1 label may link to Settings›Models)
- [ ] Brain once (canvas) · Memory once (rail `/memory`)
- [ ] Outage ≠ empty on C2
- [ ] Remember→fresh chat→correct answer in Playwright

End of Document
