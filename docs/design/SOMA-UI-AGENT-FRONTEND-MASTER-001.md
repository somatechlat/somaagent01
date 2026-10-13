# SOMA-AGENT FRONTEND + TOOLS MASTER DESIGN
# (PLAN ONLY — NO CODE UNTIL OPERATOR SAYS GO)

**Law:** NO MOCKS / FAKES / STUBS / SHIMS. Every control has a real handler or an honest disabled reason.  
**Stack:** Lit 3.x · Django Ninja · Temporal · Vault · T-1 MemoryGateway · Skins SDK (live)  
**Source of truth:** our `webui/src` + `services/tool_executor` + docs (FEATMATRIX, TOOLS-001, MODULE-CATALOG, UI-CATALOG)

---

## 1. AGENT ZERO — TOOLS (what they have)

From FEATMATRIX §2.2 + TOOLS-001 §5.7 full A0 inventory (~29 tools / 42 plugins):

| # | A0 tool | What it does | Soma today | WHY we need it |
|---|---|---|---|---|
| 1 | `response` | end loop / final answer | LIVE (orchestrator) | core loop |
| 2 | `code_execution` | python / node / terminal PTY | **PARTIAL** (`code_execute` cannot import installed pkgs) | agent must run real analysis |
| 3 | `input` | keyboard into running terminal | PLANNED (only with shell opt-in) | interactive sessions |
| 4 | `text_editor` | read/write/patch files | **LIVE** PathGuard | edit work |
| 5 | `office_artifact` | docx/xlsx/pptx/odt create/edit | **MISSING** | deliver real documents |
| 6 | `document_query` | RAG over uploads | **LIVE** (Brain, better than FAISS) | answer from user docs |
| 7 | `memory` + `behaviour` | save/load/forget + rules | **LIVE** (T-1, superior) | continuity |
| 8 | `goal` | per-chat goals | MISSING | track multi-step work |
| 9 | `browser` | navigate/click/type/screenshot | MISSING (UI gated honest) | research + form fill |
| 10 | `search_engine` | web search | **LIVE** (SearxNG) | current facts |
| 11 | `scheduler` | cron/adhoc tasks | MISSING tools (Temporal exists) | recurring work |
| 12 | `skills` | load skill markdown | MISSING | reusable expertise |
| 13 | `vision_load` | image → model | MISSING tool (multimodal exists) | read screenshots/docs |
| 14 | `call_subordinate` | spawn sub-agent | MISSING tool (gateway exists) | parallel specialists |
| 15 | `notify_user` | notify | MISSING tool (API exists) | alert human |
| 16 | `wait` / delay | sleep | MISSING | pacing |
| 17 | `git` | status/diff/log/commit | **MISSING** | code work |
| 18 | `a2a_chat` | agent-to-agent | PLANNED | multi-agent |
| 19 | `unknown` | error feedback | LIVE | honesty |
| 20 | `mcp_handler` | external MCP tools | MISSING runtime | ecosystem tools |
| 21 | `parallel_tools` | concurrent tool runs | MISSING (sequential) | speed |
| — | `computer_use_remote` | control user host | **DENY (do not clone)** | security |

**A0 plugins (42):** email, telegram, whatsapp, kokoro TTS, whisper STT, desktop (XFCE), editor, onboarding, whats_new, chat_branching, time_travel, plugin_installer, skills_cli, backup, self_update, discovery, validator…  

**Soma LIVE kit (24):** timestamp · memory_* (6) · code_execute · file_read · http_fetch · document_ingest · canvas_append · file_list/search/write/patch · research_report · job_status · document_index/query · web_search/web_read · packages_ensure/list · os_packages_ensure  

**Soma gaps vs A0 that MATTER for our product (why):**

| Gap | Why it fulfils a real task |
|---|---|
| **artifact_*** (docx/xlsx/pptx/pdf) | “Make me a report/deck/spreadsheet” — core agent value |
| **chart_render** | data → plots in workroot |
| **browser_*** | research, fill forms, screenshot proof |
| **git_*** | code agent work in workroot |
| **notify_user** | long jobs must wake the human |
| **scheduler_*** | “every morning summarize…” |
| **skills** | load a domain playbook into context |
| **vision_load** | understand images user attached |
| **call_subordinate** | parallel research/code specialists |
| **file_build** | multi-step document assembly |
| **parallel tools** | independent calls at once |
| **MCP** | external tool ecosystem |
| **code↔venv fix** | packages_ensure is useless if code cannot import |

**Do NOT clone (security):** host Chrome connector, computer_use_remote, remote PTY, free `sh -c` shell.

---

## 2. AGENT ZERO — UI/UX (how many surfaces)

A0 web UI = **~20 major screens / areas** (888 webui files in their tree):

1. Chat workspace (streaming, markdown, code, branches)
2. Message detail
3. Attachments / images in chat
4. Chat history sidebar + search
5. Chat branching / regenerate
6. Canvas / right panel (multi-surface)
7. Browser in canvas
8. Linux desktop in canvas
9. Document editor in canvas
10. Code editor in canvas
11. File browser
12. Settings (13 sections)
13. Model provider setup
14. Secrets management
15. Agent profile editor
16. Plugin marketplace
17. Skills management
18. MCP management
19. Backup/restore
20. Notifications · welcome/onboarding · login · changelog · time travel

**Soma today:** ~15 of those **EXISTS** (chat, streaming, attachments, images, history, search, export, canvas host 6/8, settings 9 tabs, models, capsule, auth, welcome, skins).  
**PARTIAL:** markdown, editor, secrets, backup, notifications, responsive.  
**MISSING:** highlight, branching, file tree depth, plugins UI, skills UI, command palette, time travel.

---

## 3. OUR MODULES — detailed design (based on OUR code)

Every module below is **real Lit**, restyles via **Skin SDK** (`--skin-*` + aliases), binds **real REST/WS**, and ships **honest empty/error/disabled** states.

### 3.1 FILE MANAGER (M-024) — first-class

**Why:** A0 file browser + our filesv2 + PathGuard tools are half-done in UI. Users need browse → open → edit → download → attach.

```
┌─ soma-file-manager ──────────────────────────────────────────────┐
│ [breadcrumb: workroot / project / docs]          [search] [+]   │
├──────────────┬───────────────────────────────────────────────────┤
│ TREE         │ LIST / PREVIEW                                    │
│ ▸ workroot   │  name           size    modified    actions       │
│   ▸ docs     │  report.md      12 KB   2m ago      ⬇ ✎ 🗑       │
│   ▸ out      │  chart.png      84 KB   5m ago      ⬇ 👁         │
│   └ src      │  ─────────────────────────────────────            │
│ ▸ filesv2    │  PREVIEW: markdown | code+hljs | image | pdf      │
│              │  (binary = metadata + download only)              │
├──────────────┴───────────────────────────────────────────────────┤
│ [Upload ▾] [New folder] [Refresh]     status: 12 files · 2.1 MB │
└──────────────────────────────────────────────────────────────────┘
```

| Part | Binding (real) | Notes |
|---|---|---|
| Tree | `GET /api/v2/workroot/tree` (**NEW API — required**) | PathGuard jail |
| List | `GET /api/v2/filesv2/` + workroot list | exists today for filesv2 |
| Upload | `POST /api/v2/filesv2/upload` | exists |
| Download | signed URL | exists |
| Write | `PUT /api/v2/filesv2/{id}/content` (**NEW**) | editor Save enables only then |
| Open→Editor | UI-X-04 | exists RO |
| Attach to chat | composer | exists |
| Skin | `right_panel` surface | skin SDK |

**Modes:** `browse` · `select` (composer) · `manage`  
**States:** loading · empty · error+retry · uploading · partial  
**Honesty:** no workroot API → hide tree, show reason (never fake tree).

---

### 3.2 MEMORY MANAGER (M-memory / UI-S-04)

**Why:** memory is our **advantage** vs A0. Must be operable, not a black box.

```
┌─ Memory ─────────────────────────────────────────────────────────┐
│ [Search recall…]          filter: all | wm | ltm    [Remember]  │
├──────────────────────────────────────────────────────────────────┤
│  WM  12   LTM  840   last write 2m ago      brain ● connected   │
├──────────────────────────────────────────────────────────────────┤
│  ▣ 2026-10-13 09:41   text: "User prefers dark UI…"   score .91 │
│     source: chat · coord 0x3f…   [Open] [Forget] [Copy coord]   │
│  ▣ 2026-10-12 22:10   text: "Deploy runs on :20080"    score .87 │
├──────────────────────────────────────────────────────────────────┤
│  Remember: [textarea]                    [Save to Brain]         │
│  Probe:    [query]  → recall live · shows scores + provenance    │
└──────────────────────────────────────────────────────────────────┘
```

| Control | Real API | Honesty |
|---|---|---|
| List / recall | `POST /api/v2/memory/recall` · `GET /memory/` | empty ≠ error |
| Counts | no count API → show **`—`** | never fake 0 |
| Remember | `POST /memory/save` (gateway) | fail closed on brain down |
| Forget | `POST /memory/forget` | approval if bare coord |
| Proximity | `memory_proximity` tool | live scores |
| Status chip | brain diagnostics | degraded = visible |

**Skin:** core tokens (not a surface — Memory has one home `/memory`).

---

### 3.3 SOMABRAIN MANAGER (cognitive + settings)

**Why:** operators must see/tune brain without fake meters.

```
┌─ SomaBrain ──────────────────────────────────────────────────────┐
│ Connection  ● ok   tenant=standalone   latency 42ms              │
├─ Neuromodulators (raw — no invented %) ──────────────────────────┤
│  DA  0.62     5-HT  0.41     NE  0.73     ACh  0.55              │
├─ Sleep / consolidation ──────────────────────────────────────────┤
│  phase: idle · last run 3h ago · queue 0                         │
├─ Knobs (Capsule.persona_config.knobs) ───────────────────────────┤
│  intelligence  [====|-----] 7    autonomy [====|-----] 7         │
│  resource      [==|-------] 0.5  style    [balanced ▾]           │
│  [Save knobs]  → PATCH /agents/{id}/capsule                      │
├─ Diagnostics ────────────────────────────────────────────────────┤
│  memory_ok ●   sfm circuit ●   planner gated (feature flag)      │
└──────────────────────────────────────────────────────────────────┘
```

| Data | Real source | Rule |
|---|---|---|
| Neuromod | `GET /api/v2/somabrain/cognitive/state/{agent_id}` | **raw values only** |
| Knobs | Capsule `persona_config.knobs` | real PATCH |
| Sleep | sleep status route | honest phase |
| Settings | SomaBrain settings tab | live knobs only |

**UI law:** no fake % meters (catalog §Brain neuromod).

---

### 3.4 SETTINGS + KNOBS (one shell)

**Why:** A0 has 13 settings sections; we have 9 tabs. Need depth + **Model Roles** + skins.

```
┌─ Settings ───────────────────────────────────────────────────────┐
│ Agent│Models│Voice│Interface│Tools│Integrations│SomaBrain│…│      │
├──────────────────────────────────────────────────────────────────┤
│ Interface                                                          │
│  Theme   [Dark ▾]                                                  │
│  Skins   ┌ gallery: 6 packs · Preview · Apply · Uninstall ┐      │
│  Language [en ▾]   Timezone [UTC ▾]                                │
├──────────────────────────────────────────────────────────────────┤
│ Models                                                             │
│  Roles: Chat │ Utility │ Embedding │ Vision │ Decision(Clef)       │
│  Providers: groq / mimo / anthropic / …  Key in Vault ✓            │
│  [Load models] [Restore bundled presets]                           │
├──────────────────────────────────────────────────────────────────┤
│ Tools                                                              │
│  catalog: enable/disable + tier + approval required                │
└──────────────────────────────────────────────────────────────────┘
```

| Knob group | Where | Binding |
|---|---|---|
| Agent persona | Settings › Agent + Capsule editor | CapsuleConfig |
| Model Roles (5) | Settings › Models | `/llm/roles` |
| API keys | Models / Integrations | Vault write-only |
| IQ knobs | Agent + SomaBrain | `persona_config.knobs` |
| Tool policy | Settings › Tools | `GET/PUT /tools/catalog` |
| Skins / theme | Interface | skin-sdk (live) |
| Feature flags | System | live |

---

### 3.5 CHAT WORKSPACE (hero)

**Why:** product feel. A0 wins on markdown/code/branching.

```
┌ sidebar ┐┌ chat ────────────────────────────────────┐┌ canvas ┐
│ New chat││ user: …                                   ││ Files   │
│ search  ││ assistant: markdown + code + tools        ││ Tools   │
│ history ││ ┌ tool.timeline  approve/deny ──────────┐ ││ Browser │
│ …       ││ └───────────────────────────────────────┘ ││ Editor  │
│ Memory  ││ [composer + attach + mic + queue]         ││ Debug   │
│ Settings││                                          ││ Capsule │
└─────────┘└──────────────────────────────────────────┘│ Brain   │
                                                       └─────────┘
```

**Must add (why):** syntax highlight (readability) · tables (data answers) · branching (try alternatives) · in-chat search · drag-drop attach · message edit/regenerate.

---

### 3.6 COMMAND PALETTE (M-021)

**Why:** power users; A0-class navigation without mouse.

```
⌘K  ┌──────────────────────────────────────┐
    │ > open memory                        │
    │   apply skin · soma brand            │
    │   new chat · export · settings models │
    │   file manager · switch surface      │
    └──────────────────────────────────────┘
```

Real actions only (routes, skins, chat commands). No fake rows.

---

### 3.7 CANVAS SURFACES (UI-X-01…08)

| ID | Surface | Status | Build if |
|---|---|---|---|
| 01 | Files | thin list | → full File Manager |
| 02 | Tools | LIVE | deepen log |
| 03 | Browser | GATED honest | real Playwright container tool |
| 04 | Editor | RO + Save disabled | real PUT/content route |
| 05 | Debug | LIVE | keep |
| 06 | Capsule | LIVE | add version diff |
| 07 | Brain | LIVE | align with SomaBrain manager |
| 08 | Desktop | GATED honest | only if remote-desktop capability |

---

## 4. TOOLS — what we WILL build and why (task-first)

| Build | Task it fulfils | Tier | Real implementation |
|---|---|---|---|
| **code_execute + venv** | “plot this CSV” after packages_ensure | 2 | run workroot venv python (argv) |
| **artifact_create/edit/read** | “make a Word/Excel/Deck/PDF” | 2/2/1 | Temporal ArtifactCreateWorkflow + python-docx/openpyxl/pptx |
| **chart_render** | “chart the data” | 2 | matplotlib in scientific venv → workroot |
| **file_build** | “assemble long report” | 2 | Temporal FileBuildWorkflow |
| **browser_*** | “research and fill form” | 2 | Playwright **container only** |
| **git_status/diff/log** | “what changed in the repo” | 1-2 | PathGuard workroot |
| **notify_user** | “tell me when done” | 1 | notifications_store |
| **scheduler_*** | “run every day 8am” | 2 | Temporal schedules |
| **goal** | multi-step mission control | 2 | per-chat goal store |
| **skills** | domain playbook | 1-2 | markdown inject |
| **vision_load** | “read this screenshot” | 2 | multimodal pipeline |
| **call_subordinate** | parallel specialist agents | 2 | delegation gateway |
| **wait** | pacing | 1 | Temporal timer |
| **parallel tools** | speed | — | asyncio.gather in one choke |
| **MCP** | external tools | 2 | Capability type=mcp |
| **workroot tree API** | File Manager UI | 1 | list/dir REST + PathGuard |
| **filesv2 PUT** | editor Save | 2 | content write route |

**Never build as default kit:** free shell, host browser, computer_use_remote.

---

## 5. UI/UX — what we WILL build (with wireframe role)

| Priority | Module | Wireframe role | Fulfils |
|---|---|---|---|
| P0 | **Syntax highlight + markdown tables** | chat code blocks | readable agent output |
| P0 | **File Manager** | §3.1 | browse/edit/attach files |
| P0 | **workroot tree + filesv2 PUT** | backend | unlocks above |
| P1 | **Chat branching + regenerate** | message tree | alternatives |
| P1 | **Command palette** | §3.6 | navigation power |
| P1 | **Memory manager depth** | §3.2 | operate the advantage |
| P1 | **SomaBrain manager** | §3.3 | tune brain, honest meters |
| P1 | **Settings Model Roles polish** | §3.4 | 5 roles + presets |
| P2 | **Notification center** | toast + feed | long jobs |
| P2 | **Backup restore** | settings | ops |
| P2 | **Skills / plugins UI** | honest gates until API | ecosystem |
| P2 | **Persona library** | capsule versions | identity |
| P3 | **Time travel / changelog** | history | completeness |
| P3 | **Responsive pass** | breakpoints | mobile |

---

## 6. WIRE-FRAME FAMILY (all skinnable)

Every screen uses the same **A0 chrome law** (our IA-001):

- Left rail: New chat · conversations · **one** Memory · **one** Settings  
- Hero: composer + stream + tool timeline  
- Right canvas: 8 surfaces, honest gates  
- Skins: Settings › Interface (live SDK)

Wireframes for each module live in `docs/design/mockups/` (UI-S-*, UI-X-*); **new annexes to add when we build:**  
`UI-X-01-files-v2.md` (File Manager) · `UI-S-04b-memory-manager.md` · `UI-S-56b-somabrain-manager.md` · `UI-C-palette.md`

---

## 7. BUILD ORDER (no code until you approve)

| Phase | Deliverable | Exit (live) |
|---|---|---|
| **A** | Design lock with you (this doc) | you approve |
| **B** | Backend: workroot tree + filesv2 PUT + code_execute venv + SSRF | tests green |
| **C** | UI: highlight + markdown + File Manager | Playwright file flow |
| **D** | UI: branching + palette + memory/brain managers | Playwright chat+memory |
| **E** | Tools: artifact/chart/notify/scheduler/git/browser | tool e2e |
| **F** | Settings depth + skins polish + a11y | full agent session green |

---

## 8. WHAT I NEED FROM YOU (design decisions)

1. **File Manager** — is workroot the primary home (recommended) or filesv2-only?  
2. **Artifacts** — which first: docx / xlsx / pptx / pdf?  
3. **Browser tool** — confirm container-only Playwright (no host Chrome).  
4. **Command palette** — yes/no for P1?  
5. **Memory UI** — keep single `/memory` home (IA law) or also a rail drawer?  
6. **Skins** — any brand packs to add beyond the 6 shipped?  
7. Approve this plan → I will **not write product code** until you say **GO**.

---

*This is the full agent frontend + tools design. Waiting for your direction before implementation.*
