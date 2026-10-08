# SOMA — CHAT WORKSPACE UI/UX (Agent Soma)

## Document Control

| Field | Value |
|---|---|
| Document Title | Agent Soma — Complete Chat Workspace UI/UX |
| Document Identifier | SOMA-UI-CHAT-WORKSPACE-001 |
| Version | 1.0.0 |
| Date | 2026-10-08 |
| Status | Draft |
| Classification | Internal |
| ISO Reference | ISO 9241-210:2019 |
| Source of truth | **Soma design system + product** (Agent Zero = capability insight only, never a clone) |
| Related | UI-S-00…53 · UI-X-01…08 · SOMA-UI-SPEC-001 · SOMA-UI-MODEL-ADMIN-001 · SOMA-UI-UX-001 |
| Forbidden | Word **“slot”** · SaaS / Eye of God branding · placeholder metrics · fake surfaces |

---

## 0. Design stance

**Agent Soma is its own product.** We keep Soma identity (dark canvas, cards, neuromodulators, memory as a first-class citizen, multi-tenant honesty) and take only *structural capability ideas* from Agent Zero (process groups, message queue, canvas dock, progressive settings).

| We keep (Soma) | We improve (vs A0) | We never copy |
|---|---|---|
| Soma Black / Blue / Violet tokens | Memory is inspectable beside the thread | A0 Alpine HTML/JS |
| Capsule + tenant + Constitution | Tool provenance stays visible | A0 CSS / layout clones |
| Neuromod status (DA/5-HT/NE/ACh) | No hidden model-setup debt | A0 “extension slot” jargon |
| Used for · Chat / Help / Memory | Density modes keep provenance | A0 chat naming / strings |
| Vault-only keys | HITL is explicit and honest | |

---

## 1. Workspace architecture (the one screen)

Three vertical bands + two persistent strips. **Chat is the hero.**

```
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│  A · CHAT TOP (40px)  thin — NOT a settings bar                                                │
│  [≡]  [S] SOMA                 ‹clock›   ● ‹conn›   🔔 ‹n›   ▢ ‹project› ▾                    │
├──────────────┬───────────────────────────────────────────────────────────────┬───────────────┤
│              │                                                               │               │
│  B · LEFT    │                    C · CHAT COLUMN                             │  D · RIGHT    │
│  RAIL        │                                                               │  CANVAS       │
│  264px       │   C1  Title · model label · Pause/Nudge/Stop/Reset             │  360–520px    │
│  (collapsible│   C2  Memory pulse (recall n · top hit · [Open Memory])        │  (resizable)  │
│   → 56px)    │   C3  Message stream (process groups)                          │               │
│              │   C4  HITL / approval bar (when needed)                        │  Surface tabs │
│  New chat    │   C5  Composer (drafts · queue · attach · voice)               │  + docked     │
│  Search      │                                                               │  surface      │
│  Chats       │                                                               │               │
│  ───         │                                                               │               │
│  🧠 Memory   │  ← ONE home for memory (route /memory)                         │  NO Memory    │
│  ⚙ Settings  │  ← ONE Settings (Models inside Settings)                       │  tab here     │
│  ───         │                                                               │               │
│  👤 user     │                                                               │               │
│  Sign out    │                                                               │               │
├──────────────┴───────────────────────────────────────────────────────────────┴───────────────┤
│  E · STATUS (28px)  turn ‹live› · ctx ‹live› · recall ‹live› · tools ‹live› · model ‹live›    │
│                      DA/5-HT/NE/ACh ‹live› only if cognitive API mounted                       │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
```

**Breakpoints**

| Width | Left | Chat | Canvas |
|---|---|---|---|
| ≥1440 | 280 | flex | 440 |
| ≥1200 | 264 | flex | 400 |
| ≥992 | 240 | flex | collapsible |
| ≥768 | overlay | flex | hidden (sheet) |
| <768 | hamburger | flex | full-screen sheet |

---

## 2. Band A — Top bar

| Element | Behavior |
|---|---|
| **SOMA** wordmark | Gradient S mark; click → Welcome |
| **Agent ▾** | Switch agent/capsule; shows name + model binding |
| **● Online** | Connection chip (Online / Degraded / Offline) with last-sync tooltip |
| **Model chip** | Active chat model (`DeepSeek 2.8 · Groq`); click → Models |
| **Mode** | STD · TRN · ADM · DEV · RO · DGR (color-coded pill) |
| **⌘K** | Command palette (chats, settings, surfaces, actions) |
| **🔔 / ⚙️ / 👤** | Notifications · Settings workspace · Profile |

No clutter. No A0 “extension slots” on the chrome.

---

## 3. Band B — Left rail (conversations + wayfinding)

```
┌──────────────────────┐
│  SOMA           [◀]  │
│  ┌────────────────┐  │
│  │ 🔍 Search…     │  │
│  └────────────────┘  │
│  [ + New chat ]      │
│                      │
│  TODAY               │
│  ▸ Analyze Q3 data   │  ← active (blue rail)
│    Soma · 2h         │
│  ▸ Fix WS bug        │
│    Soma · 5h         │
│  YESTERDAY           │
│  ▸ API docs          │
│                      │
│  ─────────────────   │
│  🧠 Memory           │
│  🤖 Models           │
│  🎤 Voice            │
│  ⚙️ Settings         │
│  ─────────────────   │
│  ┌────────────────┐  │
│  │ 👤 Test User   │  │
│  │ Soma Assistant │  │
│  └────────────────┘  │
└──────────────────────┘
```

**Chat row actions (hover ⋮):** Rename · Branch · Export · Delete (confirm).

**Chat tree (optional depth):** parent/child with chevron; running chat shows a working pulse.

**States:** empty (“No conversations yet.”) · loading skeletons · offline banner.

---

## 4. Band C — Chat column (the hero)

### C1 · Conversation header + turn controls

```
┌────────────────────────────────────────────────────────────────────────┐
│ Analyze Q3 data                    [Pause] [Stop] [Reset] [Nudge]  [⋯] │
│ Soma Assistant · DeepSeek 2.8 · live                             ● 12s│
└────────────────────────────────────────────────────────────────────────┘
```

| Control | When visible | Action |
|---|---|---|
| Pause / Resume | while streaming | freeze generation |
| Stop | while streaming | end turn |
| Reset | always | clear context (confirm) |
| Nudge | while streaming | inject steering text |
| ⋮ menu | always | Rename · Export · Branch · Delete · Open Memory |

### C2 · Memory pulse strip (readout only — not a second Memory UI)

A thin status line under the header: **what this turn used from memory**.  
It is a **link into the one Memory screen**, never a panel, never a list.

```
┌────────────────────────────────────────────────────────────────────────┐
│ 🧠 recall 3 · wm 2 · ltm 1 · “project Q3 revenue” · [Open Memory]     │
└────────────────────────────────────────────────────────────────────────┘
```

- **Open Memory** → navigates to **`/memory`** (the single Memory workspace) with `?turn=current` filter applied.
- No cards, no timeline, no dashboard here.
- Empty: `🧠 recall 0 · nothing this turn · [Open Memory]`.

### C3 · Message stream — process groups

**Message types (Soma taxonomy):**

| Type | Render |
|---|---|
| **user** | Right-aligned bubble, avatar, timestamp, ✓ |
| **agent** | Left bubble, markdown, code, images, files |
| **process group** | Collapsible unit: tools / steps / reasoning |
| **tool call** | Accent chip `WEB` `MEM` `CODE` `FILE` + status |
| **thinking** | Animated “Working…” + cancellable |
| **error** | Red edge + Retry |
| **info / hint** | Muted inline |
| **HITL request** | Approval bar (C4) |

**Process group chrome (take the idea, Soma look):**

```
┌─ ⚙ web_search · success · 1.2s ────────────────────────────── [Expand] ┐
│  query  "Q3 revenue EU"                                               │
│  hits   3                                                              │
│  1. EU revenue up 23%…                                                 │
│  2. Churn down…                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

- Expand materializes detail; collapse discards DOM (perf).
- Group header metrics stay visible when collapsed (provenance never discarded).
- Density modes: **Comfort** (full rows) / **Compact** (chip + one line) — never hide the tool name.

**Code blocks:** language badge · Copy · Run (when sandbox on) · line numbers.

**Attachments in stream:** thumbnail · name · size · open in Files surface.

### C4 · HITL bar (honest)

```
┌────────────────────────────────────────────────────────────────────────┐
│ ⚠ Approve tool?   web_search · “sensitive query”                       │
│   [ Approve ]   [ Reject ]   [ Edit & approve ]                        │
└────────────────────────────────────────────────────────────────────────┘
```

- Only when policy requires it.
- Offline: disabled with “Approval is unavailable offline.”
- Reject → confirm dialog.

### C5 · Composer

```
┌────────────────────────────────────────────────────────────────────────┐
│ ┌────────────────────────────────────────────────────────────────────┐ │
│ │ 📎  Ask anything…                                          🎤  ➤ │ │
│ └────────────────────────────────────────────────────────────────────┘ │
│  [ + ] [Model: DeepSeek 2.8 ▾]   queue 2   [expand ⤢]                  │
└────────────────────────────────────────────────────────────────────────┘
```

| Feature | Behavior |
|---|---|
| Attach (+) | Files · Image · Folder · Paste clipboard image |
| Drag & drop | Overlay with drop target; multi-file preview chips |
| Voice 🎤 | STT via `/voice/transcribe`; mic level while recording |
| Model ▾ | Quick switch among **Used for: Chat** models |
| Queue | Messages typed while agent runs are queued (numbered); Send-all / Remove |
| expand ⤢ | Fullscreen composer modal |
| Drafts | Per-conversation local draft; survives navigation |
| Code fence | ``` + Enter inserts visual code block |
| Send | Enter; Shift+Enter newline. Disabled while streaming unless queue-on |

**Send honesty:** if the model has no key / setup gate, show **inline setup** in-thread (not a silent fail). Composer stays typeable.

### Welcome / empty conversation

```
┌────────────────────────────────────────────────────────────────────────┐
│                           Hello, Test User                              │
│                    What can I help you with today?                      │
│           ┌────────────────────────────────────────┐                   │
│           │ [+]  Ask anything…                  [➤] │                   │
│           └────────────────────────────────────────┘                   │
│                                                                        │
│  Quick Actions                                                         │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐   │
│  │ 💬 New chat  │ │ 📂 Files     │ │ 🤖 Agents    │ │ ⚙️ Settings  │   │
│  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘   │
│  ┌──────────────┐ ┌──────────────┐                                     │
│  │ 🎤 Voice     │ │ 📊 Brain     │                                     │
│  └──────────────┘ └──────────────┘                                     │
│                                                                        │
│  Recent                                                                │
│  💬 Project notes review · 2h    💬 Deploy checklist · yesterday        │
└────────────────────────────────────────────────────────────────────────┘
```

Quick actions prefill the composer with a task context (not fake tools).

---

## 5. Band D — Right canvas (surfaces)

One dock, one registry. Tabs are honest: gated surfaces show **why** they are off.

```
┌─────────────────────────────────────────────────────┐
│ [📁 Files] [🔧 Tools] [🌐 Browser†] [💻 Editor]     │
│ [🐞 Debug] [📦 Capsule] [🧠 Brain] [🖥 Desktop†]    │
├─────────────────────────────────────────────────────┤
│  Surface title                    [float] [close]   │
│  ┌───────────────────────────────────────────────┐  │
│  │                                               │  │
│  │              docked surface content           │  │
│  │                                               │  │
│  └───────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
† Browser / Desktop: GATED with blocking reason if capability missing.

**No Memory tab in the canvas.** Memory has exactly one home: left-rail → `/memory`.
C2 “Open Memory” and the ⋮ menu item navigate to that same route.
```

| Surface | Content (live) | Notes |
|---|---|---|
| **Files** | File tree + preview + upload | GET filesv2 |
| **Tools** | Live tool timeline for this turn | WS tool.* |
| **Browser** | URL bar + page + screenshot/inspect | gated if no browser capability |
| **Editor** | File open, syntax, Run when allowed | read-only until write path real |
| **Debug** | WS frame ring, last N events | developer mode |
| **Capsule** | Capsule editor (identity, model roles) | |
| **Brain** | Model roles RO + AgentIQ derived + **neuromod** | open full Brain facet |
| **Desktop** | VNC desktop | **GATED** — “Requires remote-desktop capability.” |

**Canvas modes:** docked (default) · floating modal · collapsed rail (icons only).  
**Mobile:** non-action surfaces open as full-screen sheets.

### Memory — ONE screen only (`/memory`)

**Rule: Memory is implemented once.**  
Canonical component: `soma-memory-view` (extended with dashboard).  
Route: **`/memory`**.  
Entries (all go to the **same** screen — they do not open a second UI):

| Entry | Behavior |
|---|---|
| Left rail **🧠 Memory** | `router → /memory` |
| C2 **Open Memory** | `router → /memory?turn=current` (same view, filter on) |
| ⋮ menu **Open Memory** | same |
| ⌘K “Memory” | same |

**Not allowed:** Memory canvas tab · Memory welcome card · Memory mini-panel in chat · duplicate dashboard.

```
┌─ Memory  (/memory) ───────────────────────────────────────────────────────────────────────────┐
│  [Search recall…          ]  [ Run probe ]     layer [wm|ltm|both ▾]     [← Back to chat]     │
│                                                                                               │
│  FILTER  (from C2 link: “this turn”) [clear]                                                  │
│                                                                                               │
│  ┌─ THIS TURN ─────────────────────┐  ┌─ TIMELINE (newest first) ──────────────────────────┐  │
│  │ 🧠 3 hits                       │  │ 12:04  Q3 EU revenue up 23%…                  0.81│  │
│  │  0.81  Q3 EU revenue…           │  │ 11:58  Customer prefers dark…                0.64│  │
│  │  0.64  Dark mode default        │  │ 11:02  Vault key rotation…                   0.41│  │
│  │  0.41  Key rotation…            │  │ …                                                │  │
│  └─────────────────────────────────┘  └────────────────────────────────────────────────────┘  │
│                                                                                               │
│  DASHBOARD (real API numbers only)                                                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐                                          │
│  │ WM 128   │ │ LTM 42   │ │ recall 3 │ │ forget 1 │                                          │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘                                          │
│   store: somafractalmemory · embed 768 · last sync 12:04  [Refresh]                           │
│                                                                                               │
│  ACTIONS  [Open record] [Forget…] [Export JSON]                                               │
└───────────────────────────────────────────────────────────────────────────────────────────────┘
```

Open record → drawer (UI-M-01). Forget → confirm (UI-M-03). Retention/decay stay on Memory **facet** UI-S-04 controls if needed — same backend, not a second product surface.

---

## 6. Band E — Status strip

```
turn 12.4s · tokens 8.2k · recall 3 · tools 2 · queue 0
DA 0.62  5-HT 0.41  NE 0.55  ACh 0.70 · synced 12:04 [sync]
```

- Live values only (from brain / cognitive API).
- Click neuromod → Brain surface.
- Collapse to `● live` on small screens.

---

## 7. Agent surfaces (everything “the agent must have”)

| Need | Where it lives |
|---|---|
| Chat + tools + HITL | Band C (hero) |
| Memory (ONE screen `/memory`) | Left rail only — not canvas, not welcome card |
| Brain / neuromod / model roles | Brain canvas surface + Brain facet |
| Files / assets | Files surface |
| Tools catalog | Tools surface + Settings › Tools |
| Capsule identity | Capsule surface + Capsules nav |
| Models / Used for | Models settings (card library) |
| Voice | Voice settings + composer mic |
| Settings workspace | ⚙️ → Agent · Models · Voice · Interface · Tools · Integrations · Advanced |
| Admin / tenants / billing | Platform / Ops nav (enterprise) |
| Gated (Desktop / Browser) | Explicit blocking reason — never a fake panel |

---

## 8. Interaction model

| Shortcut | Action |
|---|---|
| Enter | Send |
| Shift+Enter | Newline |
| Ctrl/Cmd+K | Command palette |
| Ctrl/Cmd+B | Toggle left rail |
| Ctrl/Cmd+J | Toggle canvas |
| Ctrl/Cmd+N | New chat |
| Ctrl/Cmd+U | Attach |
| Escape | Close modal / stop generation |
| ↑ / ↓ in empty composer | Previous / next draft |

---

## 9. Design tokens (locked)

| Token | Value |
|---|---|
| bg | `#0A0A0A` |
| panel | `#111111` |
| surface | `#1A1A1A` |
| border | `#2A2A2A` |
| text | `#E5E5E5` |
| muted | `#666666` |
| accent | `#3B82F6` |
| accent-2 | `#8B5CF6` |
| gradient | `135deg #3B82F6 → #8B5CF6` |
| success / warn / error | `#10B981` / `#F59E0B` / `#EF4444` |
| font | Inter + JetBrains Mono |
| radius | 4 / 8 / 12 / 16 / full |
| space | 4px grid |

---

## 10. States (every panel)

| State | Copy (verbatim) |
|---|---|
| empty chat | “Start the conversation. Ask Soma anything.” |
| empty list | “No conversations yet.” |
| loading | “Loading conversation…” |
| send fail | “Message was not sent. It is still in the composer.” |
| offline | “Send is unavailable offline.” |
| permission | “You do not have permission to post in this conversation.” |
| gated surface | “Requires a remote-desktop capability. Not available today.” |
| memory empty | “No memories stored for this workspace yet.” |

---

## 11. Acceptance (design + later implementation)

1. Chat workspace shows **all bands A–E** in the mock and in `soma-chat.ts` parity.  
2. Memory is **one** screen (`/memory`): pulse strip and menu only deep-link to it. No triplication.  
3. Every canvas tab is real or **honestly gated** (no fake Browser/Desktop).  
4. Zero UI string contains **“slot”**.  
5. Process groups keep provenance (tool name + status) at every density.  
6. HITL / queue / drafts / voice / attach are specified and testable.  
7. Neuromod status is visible and never fabricated.  
8. Playwright human path: login → new chat → send → tool expand → memory inspect → canvas switch → settings.

---

## 12. Source map (merge — do not fork)

| Source | Role |
|---|---|
| `webui/src/views/soma-chat.ts` | Live 3-band chat (sidebar · stream · canvas) |
| `webui/src/components/soma-*.ts` | Composer, message, tool timeline, right panel, topbar, IQ |
| `webui/src/views/soma-memory-view.ts` | Memory list/recall/forget (extend to dashboard) |
| `docs/design/mockups/UI-S-00…UI-X-08` | Control IDs, states, honesty rules |
| `SOMA-UI-SPEC-001` / `MODEL-ADMIN-001` | Tokens, Settings, Models cards |
| Agent Zero webui | **Insight only** — process groups, queue, canvas dock |

---

End of Document
