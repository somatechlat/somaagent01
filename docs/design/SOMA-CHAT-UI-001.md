# SOMA-CHAT-UI-001 — Chat UI/UX (Agent Soma)

| Field | Value |
|---|---|
| Document Title | Agent Soma — Chat workspace UI/UX |
| Document Identifier | SOMA-CHAT-UI-001 |
| Version | 1.0.0 |
| Date | 2026-10-08 |
| Status | Draft |
| Classification | Internal |
| Author | SomaTech Engineering |
| Approver | — |
| ISO Reference | ISO 9241-210:2019 |
| Base | Agent Zero webui structure + Soma Capsule / Memory / Tools |
| Tokens | `--aaas-*` light/dark (`tokens.css`) |

## Revision History

| Version | Date | Author | Description |
|---|---|---|---|
| 1.0.0 | 2026-10-08 | SomaTech Engineering | Initial merged chat workspace + welcome + model flow. |

---

# 1. Welcome

First screen after login.

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                              │
│                                  Hello, Test User                                            │
│                           What can I help you with today?                                    │
│                                                                                              │
│                      ┌────────────────────────────────────────┐                              │
│                      │ [+]  Ask anything…                  [➤]│                              │
│                      └────────────────────────────────────────┘                              │
│                                                                                              │
│  Quick Actions                                                                               │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                        │
│  │ 💬           │ │ 📂           │ │ 🤖           │ │ ⚙️           │                        │
│  │ New chat     │ │ Files        │ │ Agents       │ │ Settings     │                        │
│  │ Start a      │ │ Browse and   │ │ Manage your  │ │ Models,      │                        │
│  │ conversation │ │ manage files │ │ agents       │ │ voice, tools │                        │
│  │           ›  │ │           ›  │ │           ›  │ │           ›  │                        │
│  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘                        │
│  ┌──────────────┐ ┌──────────────┐                                                           │
│  │ 🎤           │ │ 📊           │                                                           │
│  │ Voice        │ │ Brain        │                                                           │
│  │ Personas and │ │ Cognition and│                                                           │
│  │ speech       │ │ neuromod     │                                                           │
│  │           ›  │ │           ›  │                                                           │
│  └──────────────┘ └──────────────┘                                                           │
│                                                                                              │
│  Recent                                                                                      │
│  ┌────────────────────────────────────────────────────────────────────────┐                  │
│  │ 💬  Analyze sales data Q3                              2 hours ago     │                  │
│  │ 💬  Write API documentation                            Yesterday       │                  │
│  │ 💬  Debug WebSocket connection                         2 days ago      │                  │
│  └────────────────────────────────────────────────────────────────────────┘                  │
│                                                                                              │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

**Quick Actions** (each opens a real screen)

| Card | Opens |
|---|---|
| New chat | Creates conversation, focuses composer |
| Files | Files browser |
| Agents | Agent list |
| Settings | Settings workspace |
| Voice | Voice personas |
| Brain | Cognition / neuromod |

**Fields**

| Control | Behavior |
|---|---|
| Composer | Same chat input as workspace. `+` menu. Enter sends. |
| Quick Action card | Opens that screen |
| Recent list | Opens that conversation |

---

# 2. Chat workspace

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ [S] SOMA   Soma Assistant ▾   ● Online   [deepseek-2.8 · Groq]   [STD]   🔔   ⚙️   👤       │
├───────────────┬──────────────────────────────────────────────────────────┬──────────────────┤
│               │  Analyze Q3 data · deepseek-2.8 · live                   │                  │
│ [🔍 Search…]  │                                          ● 12s           │  [📁 Files]      │
│               ├──────────────────────────────────────────────────────────┤  [🔧 Tools]      │
│ [+ New chat]  │  🧠 recall 3 · wm 2 · ltm 1                              │  [🌐 Browser]    │
│               ├──────────────────────────────────────────────────────────┤  [💻 Editor]     │
│ TODAY         │                                                          │  [🐞 Debug]      │
│ ▸ Analyze Q3  │  ┌────────────────────────────────────────────────────┐  │  [📦 Capsule]    │
│   Soma · 2h   │  │  Can you help me analyze this data?                │  │  [🧠 Brain]     │
│ ▸ Fix WS bug  │  │                                        2:34 PM  ✓  │  │  [🖥 Desktop]   │
│   Soma · 5h   │  └────────────────────────────────────────────────────┘  │                  │
│               │                                                          │  ┌──────────────┐│
│ YESTERDAY     │  ┌────────────────────────────────────────────────────┐  │  │              ││
│ ▸ API docs    │  │  🤖 Soma Assistant                                 │  │  │   Surface    ││
│   Soma · 1d   │  │  Of course! I can help with data analysis.         │  │  │   Content    ││
│               │  │  ```python                                         │  │  │              ││
│ ───────────   │  │  import pandas as pd                               │  │  │              ││
│ 🧠 Memory     │  │  df = pd.read_csv('data.csv')                      │  │  │              ││
│ ⚙️ Settings    │  │  print(df.describe())                              │  │  │              ││
│ ───────────   │  │  ```                                               │  │  │              ││
│ 👤 Test User  │  │  2:34 PM                              [Copy] [↩]   │  │  │              ││
│    ● Online   │  └────────────────────────────────────────────────────┘  │  └──────────────┘│
│               │                                                          │                  │
│               │  ┌────────────────────────────────────────────────────┐  │                  │
│               │  │ 🔧 web_search · success · 1.2s          [Expand]  │  │                  │
│               │  │ query: "Q3 revenue EU"                             │  │                  │
│               │  └────────────────────────────────────────────────────┘  │                  │
│               │                                                          │                  │
│               │  ┌────────────────────────────────────────────────────┐  │                  │
│               │  │ [+]  Ask anything…                         [➤]    │  │                  │
│               │  └────────────────────────────────────────────────────┘  │                  │
│               │    ⏸ Pause Agent    👋 Nudge          queue 2  [⤢]       │                  │
├───────────────┴──────────────────────────────────────────────────────────┴──────────────────┤
│  turn 12.4s · tokens 8.2k · recall 3 · tools 2 · queue 0  │  DA 0.62  5-HT 0.41  NE 0.55  ACh 0.70  │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

**Left rail**

| Item | Action |
|---|---|
| Search | Filters conversation list |
| + New chat | Creates conversation, focuses composer |
| Conversation row | Opens thread. ⋮ menu: Rename · Export · Delete |
| Memory | Opens `/memory` |
| Settings | Opens `/settings` |
| User card | Profile · Logout |

**Chat column**

| Item | Action |
|---|---|
| Title | Rename via ⋮ or title_update |
| Model chip | `provider/name` from `chat.turn_meta` |
| Memory pulse | `recall n · wm n · ltm n` (readout) |
| User bubble | Message + timestamp + ✓ |
| Agent bubble | Markdown, code, files, timestamps, Copy, Retry |
| Tool group | `name · status · duration` + Expand (args, result) |
| HITL bar | Approve · Reject when policy requires |

**Composer row** (Agent Zero layout)

```
[+]  Ask anything…                              [➤]
     ⏸ Pause Agent    👋 Nudge       queue 2   [⤢]
```

| Item | Placement | Action |
|---|---|---|
| `+` | left of input | Menu opens upward: Attach files · Attach folder · MCP Servers · Clear Chat · History · Context |
| Input | center | contenteditable. Enter sends. Shift+Enter newline |
| `➤` | **right of input** | Send. While streaming becomes **Stop** |
| Expand `⤢` | right, second row | Full-screen input |
| **Pause Agent** | **under input**, left | Toggles Pause / Resume Agent |
| **Nudge** | **under input**, next to Pause | Injects steering text |
| Queue chip | under input, right | N queued; drop clears |
| Mic | inside input row | Speech-to-text |

**Right canvas**

| Surface | Content |
|---|---|
| Files | File tree, preview, upload |
| Tools | Live tool timeline for the turn |
| Browser | URL bar, page, screenshot, inspect |
| Editor | File open, syntax, run |
| Debug | WS frame log, filter, clear |
| Capsule | Agent identity, model roles, config |
| Brain | Neuromod DA/5-HT/NE/ACh, model roles, adaptation |
| Desktop | Remote desktop |

**Status strip**

| Value | Source |
|---|---|
| turn duration | live |
| context tokens | `chat.turn_meta.context_tokens` |
| recall / tools / queue | live |
| DA · 5-HT · NE · ACh | cognitive state API |

---

# 3. Process group

```
┌──────────────────────────────────────────────────────────────┐
│ 🔧 web_search · success · 1.2s                      [Expand] │
│ query   "Q3 revenue EU"                                      │
│ hits    3                                                    │
│ ──────────────────────────────────────────────────────────── │
│ 1. EU revenue up 23% in Q3…                                  │
│ 2. Churn down 12%…                                           │
│ 3. Enterprise tier +27%…                                     │
└──────────────────────────────────────────────────────────────┘
```

Collapsed: name + status + duration.  
Expanded: arguments, result, full detail.

---

# 4. Memory screen

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ Memory                                                              [← Back to chat]        │
│                                                                                              │
│ [Search recall…                          ] [ Run probe ]     layer [both ▾]                 │
│                                                                                              │
│ THIS TURN                           TIMELINE                                                │
│ ┌───────────────────────────────┐   ┌─────────────────────────────────────────────────────┐ │
│ │ 🧠 3 hits                     │   │ 12:04  Q3 EU revenue up 23%                    0.81 │ │
│ │  0.81  Q3 EU revenue…         │   │ 11:58  Customer prefers dark mode              0.64 │ │
│ │  0.64  Dark mode default      │   │ 11:02  Vault key rotation schedule             0.41 │ │
│ │  0.41  Key rotation…          │   │ 10:44  Tool web_search used for Q3 query       0.33 │ │
│ └───────────────────────────────┘   └─────────────────────────────────────────────────────┘ │
│                                                                                              │
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐                                         │
│ │ WM 128   │ │ LTM 42   │ │ recall 3 │ │ forget 1 │                                         │
│ │ working  │ │ durable  │ │ this turn│ │ this week│                                         │
│ └──────────┘ └──────────┘ └──────────┘ └──────────┘                                         │
│  store: somafractalmemory · 768-dim · healthy · synced 12:04                                 │
│                                                                                              │
│ [Open record]   [Forget…]   [Export JSON]                                                    │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

| Control | Behavior |
|---|---|
| Search | Semantic recall, fills timeline |
| Run probe | Executes recall, shows hits |
| Layer filter | wm · ltm · both |
| This-turn hits | Hits used in the current conversation turn |
| Timeline | Newest first. Click opens record drawer |
| WM / LTM / recall / forget | Real counts |
| Open record | Drawer with full stored fields |
| Forget… | Confirm dialog, then POST forget |
| Export JSON | Downloads memory export |

---

# 5. Settings

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ Settings                                                             [Save]  [Cancel]       │
├──────────────┬──────────────────────────────────────────────────────────────────────────────┤
│ Agent        │                                                                              │
│ Models       │  MODELS · card library                                                       │
│ Voice        │                                                                              │
│ Interface    │  [Search…]   Type [All ▾]                          [+ Add model] [Keys →]    │
│ Tools        │                                                                              │
│ Integrations │  ┌─ ● LIVE ─────────────────────┐  ┌─ Ready ─────────────────────┐          │
│ Advanced     │  │ Chat                         │  │ Chat                         │          │
│              │  │ deepseek-2.8                 │  │ llama-3.3-70b                │          │
│              │  │ DeepSeek 2.8 · Groq          │  │ Llama 3.3 70B · Groq         │          │
│              │  │ api.groq.com/openai/v1       │  │ api.groq.com/openai/v1       │          │
│              │  │ ctx 131072 · in 0 · out 8192 │  │ ctx 131072 · in 0 · out 8192 │          │
│              │  │ vision · priority 10         │  │ priority 10                  │          │
│              │  │ Used for: Chat               │  │ Used for: Help               │          │
│              │  │ key ●ok                      │  │ key ●ok                      │          │
│              │  │ [✓ Active] [Edit] [Test]     │  │ [Activate] [Edit] [Test]     │          │
│              │  └──────────────────────────────┘  └──────────────────────────────┘          │
└──────────────┴──────────────────────────────────────────────────────────────────────────────┘
```

## 5.1 Model full screen

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ [← Back to models]                                                                           │
│ Model — deepseek-2.8 · DeepSeek 2.8 · Groq                              ● LIVE               │
│                                                                                              │
│ [ Normal ]   [ Advanced ]   [ Used for ]                                                     │
├─────────────────────────────────────────────────────────────────────────────────────────────┤
│ NORMAL                                                                                       │
│                                                                                              │
│ Provider          [Groq ▾]                                                                   │
│                                                                                              │
│ Custom URL        [https://api.groq.com/openai/v1          ]                                 │
│                                                                                              │
│ Provider key      [••••••••••••••••          ]  [Save to Vault]   ● saved                   │
│                                                                                              │
│ ┌─ Model list ─────────────────────────────────────────────────────┐                         │
│ │ [ Load models ]                          Source: live · 12 models │                         │
│ │  ● deepseek-2.8                                                      │                         │
│ │  ○ deepseek-2.8-lite                                                 │                         │
│ │  ○ llama-3.3-70b                                                     │                         │
│ │  ○ llama-3.1-8b                                                      │                         │
│ └──────────────────────────────────────────────────────────────────┘                         │
│                                                                                              │
│ Model ID          [deepseek-2.8              ]                                               │
│ Display name      [DeepSeek 2.8              ]                                               │
│ Type              [Chat ▾]                                                                   │
│ Price level       [low ▾]                                                                    │
│ Sees images       [●]          Use this model  [●]                                           │
│                                                                                              │
│ [ Test connection ]                                                                          │
│                                                                                              │
│ ADVANCED                                                                                     │
│                                                                                              │
│ Context window    [131072]     Max output tokens  [8192]                                     │
│ Requests/min      [0]          Input tok/min      [0]     Output tok/min    [0]              │
│ Priority          [10]                                                                       │
│ Good at           [chat, reasoning]        Used in   [general]                               │
│ Extra options     [ { "temperature": 0.7 }                                                  ] │
│ Memory/context    [●]          Vision model   [auto ▾]                                       │
│                                                                                              │
│ USED FOR                                                                                     │
│                                                                                              │
│ [✓] Chat          Primary conversations                                                      │
│ [ ] Help          Summaries and background work                                              │
│ [ ] Memory        Embeddings for memory and search                                           │
│                                                                                              │
│ [ Save model ]   [ Make live ]   [ Delete… ]   [ Close ]                                     │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

## 5.2 Other Settings sections

| Section | Fields |
|---|---|
| **Agent** | Default personality · System instructions · Knowledge folder · Inherit current project · Max failed replies |
| **Voice** | Persona name · Description · Voice ID · Speed · Volume · TTS provider · STT model · Listen language · Turn detection · Stop sensitivity · Silence before stop · Reply model · Persona instructions · Creativity · Max reply length · Active · Default · [Test speak] [Test listen] |
| **Interface** | Theme · Language · Timezone |
| **Tools** | Enable cards per tool · timeout · max size · max iterations |
| **Integrations** | Provider on/off · Key (write-only) · API address · Test connection · Channels |
| **Advanced** | Modules · Quotas · Experimental · Backup/Restore · API keys |

---

# 6. Conversation menu

```
┌──────────────────────┐
│ Rename               │
│ Export               │
│ Delete…              │
└──────────────────────┘
```

Rename → inline field. Export → JSON download. Delete → confirm dialog.

---

# 7. Full flows

## 7.1 First run

```
/login → Sign in → Welcome → type message → Send → stream reply → tool group → memory written
```

## 7.2 Change model

```
Chat model chip → Settings · Models → click card → full model screen
  → Normal: provider, Custom URL, Vault key, Load models, Model ID
  → Advanced: context, tokens, limits, kwargs
  → Used for: Chat / Help / Memory
  → [Save model] [Make live] [Test connection]
  → Back to chat → model chip shows new provider/name
```

## 7.3 Memory

```
Chat C2 [Open Memory] → /memory → this-turn hits + timeline
  → click record → drawer
  → [Forget…] → confirm → forget
  → [Export JSON] → download
```

## 7.4 Tool + HITL

```
Send → tool group appears → Expand → args + result
  → HITL bar → [Approve] or [Reject] → run continues
```

## 7.5 Queue while busy

```
Send message 1 → streaming → type message 2, 3 → queue 2 chip
  → [drop] clears
  → idle → queue drains in order
```

---

# 8. States

| State | Copy |
|---|---|
| Empty chat | "Start the conversation. Ask Soma anything." |
| Empty list | "No conversations yet." |
| Loading | "Loading conversation…" |
| Send fail | "Message was not sent. It is still in the composer." |
| Offline | "Send is unavailable offline." |
| Permission | "You do not have permission to post in this conversation." |
| Memory empty | "No memories stored for this workspace yet." |
| Tool empty | "No tool calls" |
| WS down | "Cannot send — WebSocket disconnected" |
| Busy send | "Still finishing the previous turn — message not sent" |

---

# 9. Component library

| Tag | Purpose |
|---|---|
| `soma-chat` | Workspace shell |
| `soma-chat-topbar` | Title, model, turn controls, connection |
| `soma-message` | Message bubble |
| `soma-tool-timeline` | Process groups |
| `soma-composer` | Input, attach, voice, queue |
| `soma-composer-menu` | + menu |
| `soma-right-panel` | Surface registry |
| `soma-settings` | Settings shell |
| `soma-settings-models` | Model library + full editor |
| `soma-memory-view` | Memory screen |
| `soma-cognitive-panel` | Brain / neuromod |

---

End of Document
