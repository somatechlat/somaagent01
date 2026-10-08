# UI-S-00 — Global Chrome (Agent Soma enterprise chat)

Global application shell. Not routable. Every screen UI-S-01…UI-S-53 renders inside this frame.  
IA law: `SOMA-UI-IA-001.md` · Live: `webui/src/main.ts` + `soma-chat.ts` / `soma-right-panel`.

**Product:** enterprise operator chat. Chrome is quiet. Work happens in the workspace.  
Forbidden on chrome: IQ/AUTO/BUDGET knobs · facet tab dump · billing · fake meters · Settings cluster in chat top.

---

## 1. ASCII wireframe — enterprise chat shell (≥1280px)

```
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│ A · CHAT TOP (40px) — always thin. Never a settings bar.                                       │
│  [≡]  [S] SOMA          ‹clock›   ◉   ○   ◌   🔔 ‹n›   ▢ ‹project› ▾                          │
│       brand             time      │   │   │   notifs   project                                 │
│                                  │   │   └── Memory aide (12px glyph · tooltip)                │
│                                  │   └────── Sync/WS (12px circle)                             │
│                                  └────────── BRAIN (12px circle · tooltip · click → UI-X-07)   │
├──────────────┬───────────────────────────────────────────────────────────────┬───────────────┤
│ B · LEFT     │                    C · WORKSPACE                              │ D · CANVAS    │
│   264px      │                    (one screen owns this)                     │  360–520px    │
│              │                                                               │  or 56px rail │
│  [🔍 Search] │   ┌─────────────────────────────────────────────────────┐    │               │
│  [+ New chat]│   │  UI-S-07 chat · UI-S-04 memory · UI-S-50 settings · │    │  [▤ Files]    │
│              │   │  UI-S-51 models · … (routes only)                   │    │  [⌘ Tools]    │
│  Chats       │   └─────────────────────────────────────────────────────┘    │  [🌐 Browser†]│
│  ────────────│                                                               │  [</> Editor] │
│  ▸ active    │                                                               │  [🐞 Debug]   │
│  ▸ …         │                                                               │  [▣ Capsule]  │
│              │                                                               │  [🧠 Brain]   │
│  ────────────│                                                               │  [🖥 Desktop†]│
│  🧠 Memory   │  ← only Memory entry in chat chrome                           │               │
│  ⚙ Settings  │  ← only Settings entry (Models live inside)                   │  NO Memory tab│
│  ────────────│                                                               │  † GATED      │
│  👤 ‹user›   │                                                               │  reason       │
│  [Sign out]  │                                                               │  inline       │
├──────────────┴───────────────────────────────────────────────────────────────┴───────────────┤
│ E · STATUS (28px, optional collapse)                                                           │
│  turn ‹live› · ctx ‹live› · recall ‹live› · tools ‹live› · queue ‹live› · model ‹live› · synced│
│  DA ‹live›  5-HT ‹live›  NE ‹live›  ACh ‹live›     (omit if cognitive API not mounted)          │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Zone law (single-home)

| Zone | Owns | Never |
|---|---|---|
| **A Chat top** | Collapse · brand · time · connection · notifications · project | Models · Mode pills · Agent settings · IQ knobs · ⌘K as primary |
| **B Left rail** | Search · New chat · chat list · Memory · Settings · user | Models · Channels · Voice · Brain · Plugins · Billing |
| **C Workspace** | Exactly one route’s content | Competing rails / second dashboards |
| **D Canvas** | UI-X-01…08 surfaces | Memory tab · second Brain panel |
| **E Status** | Live turn metrics + neuromod (if API) | Fabricated numbers · always-on marketing |

**Chat-specific chrome vs admin chrome:**  
Routes `/memory` · `/settings/*` · `/cognitive` use **their own workspace chrome** (no chat left-rail).  
Only `/chat` mounts the chat rail + canvas. Do not paste chat rail onto Settings.

---

## 3. Control map

| # | Control | Binding |
|---|---|---|
| 1 | Sidebar collapse [≡] | local `soma-chat` / layout store |
| 2 | SOMA brand | `/chat` |
| 3 | Clock | client time (or server if sent) |
| 4 | **Brain micro-indicator** ◉ | 12px circle from `GET /core/brain-connector` — filled `#00c340` / `#ff6b00` pulse / `#f0a000` ring / `#e40138` ring. Tooltip only. Click → UI-X-07. |
| 4b | Sync ○ · Memory ◌ | same 12px language · Memory is aide not text |
| 5 | Notifications 🔔 | `GET /notifications` · mark-read |
| 6 | Project ▾ | project API — `‹project.name›` or `—` |
| 7 | Search | filter conversations (chat) or list (other screens) |
| 8 | New chat | `POST /chat/conversations` |
| 9 | Memory | `/memory` |
| 10 | Settings | `/settings` |
| 11 | User + Sign out | `/auth/me` · logout → `/login` |
| 12 | Canvas tabs | `soma-right-panel` — gated tabs show reason |
| 13 | Status strip | `chat.turn_meta` + cognitive API |

**Not on chrome (by design):** capsule switcher · version/lifecycle chips · IQ/AUTO/BUDGET sliders · derived AgentIQ dump · facet tab strip (Soul/Brain/Hands/Memory/Body/Governance) · tenants/billing nav · instance strip · always-visible neuromod meters when API is down.

Those belong in **Capsule / Brain / Settings** workspaces, not the chat shell.

---

## 4. Breakpoints

| Width | Left | Workspace | Canvas |
|---|---|---|---|
| ≥1440 | 280 | flex | 440 |
| ≥1200 | 264 | flex | 400 |
| ≥992 | 240 | flex | collapsible |
| ≥768 | overlay | flex | sheet |
| <768 | hamburger | flex | full-screen sheet |

---

## 5. Related

Chat: `UI-S-07` · Memory: `UI-S-04` · Settings shell: `UI-S-50` · Surfaces: `UI-X-01…08` · IA: `SOMA-UI-IA-001`

End of Document
