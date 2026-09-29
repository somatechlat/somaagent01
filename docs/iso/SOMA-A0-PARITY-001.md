# SOMA-A0-PARITY-001 — Agent Zero Feature Parity Matrix, UI/UX Specification, Remediation & Ownership Plan

## Document Control

| Field | Value |
|---|---|
| Document Title | Soma × Agent Zero — Feature Parity Matrix, UI/UX Development Specification, Code Remediation & Ownership Plan |
| Document Identifier | SOMA-A0-PARITY-001 |
| Version | 1.0.0 |
| Date | 2026-09-27 |
| Status | Draft |
| Author | SomaTech Engineering |
| Approver | — |
| Classification | Internal |
| ISO Reference | ISO 9001:2015 — Quality Management Systems — Requirements |
| Next Review | 2026-12-28 |
| Related | `SOMA-TRIAD-ARCH-001.md`, `SOMA-ARCH-INVARIANTS-001.md`, `SOMA-UI-SPEC-002.md`, `SOMA-UI-SPEC-001.md`, `SOMA-PM-PLAN-TRIAD-001.md`, `SOMA-STD-CODING-001.md` |
| Source of truth | Live source of `somaAgent01`, `somabrain`, `somafractalmemory` + `/Users/macbookpro201916i964gb1tb/Downloads/agent-zero-main` |
| Audience | **Agent swarm** (multi-agent execution). Each work package (WP) is independently assignable. |

## Revision History

| Version | Date | Author | Description |
|---------|------|--------|-------------|

| 1.0.0 | 2026-09-28 | SomaTech Engineering | Brought under ISO document control. Prior status value `**Draft — FOR EXECUTION APPROVAL. No production code until Plan Gate is signed.**` is outside the closed set `Draft \| In Review \| Approved \| Obsolete`; normalised to `Draft` — no approver has signed this document. |
| 1.0.0 | 2026-09-27 | SomaTech Engineering | Initial: full A0 feature inventory, Soma gap matrix, UI/UX development spec, Capsule-module contract (WhatsApp/Telegram/Email as Capsules), duplicate-code remediation, ownership map, swarm work packages. |

---

## 0. EXECUTION GATE (read first)

| Rule | Binding |
|------|---------|
| **NO PRODUCTION CODE** until this document is approved | User directive 2026-09-27 |
| Feature **clone**, not code clone | Implement Agent Zero *behaviours* with Soma architecture, Soma code style, Soma Capsules |
| UI/UX may be copied then **improved 100%** | Lit 3.x design system (not Alpine); Soma visual identity |
| Remove **all** duplicated / triplicated code | Canonical ownership (§8); every removal is a WP with exit criteria |
| Everything production | No mocks, no stubs, no no-ops, no fake responses (VIBE) |
| ISO record | Every WP produces evidence (file:line, test result, screenshot) into this series |
| Rapid development | Parallel WP swarm after Gate; order in §10 |

---

## 1. PURPOSE AND SCOPE

### 1.1 Purpose

To define, in one place, everything required to:

1. Reach **feature parity** with Agent Zero (behaviours, screens, settings) inside the Soma Cognitive Triad.
2. Ship a **complete UI/UX** (chat + settings + canvas + bridges) that is a deliberate improvement over Agent Zero.
3. Represent WhatsApp / Telegram / Email / Slack bridges and all plugins as **Soma Capsules**.
4. **Eliminate duplicated and triplicated code** across the three repos, with single ownership.
5. Give an **agent swarm** unambiguous work packages, acceptance criteria, and file targets.

### 1.2 Scope

| In | Out |
|----|-----|
| Feature parity matrix (§5) | Model quality / prompt science |
| UI/UX complete screens & components (§6) | Capacity procurement |
| Capsule plugin contract (§7) | Marketing site |
| Dedup remediation + ownership (§8–9) | Upstream Agent Zero modifications |
| Swarm work packages & verification (§10–11) | Non-triad repos (avenderPOD, yachaq, …) |

### 1.3 Product stance — how Soma is already better

| Dimension | Agent Zero | Soma (target) | Verdict |
|-----------|------------|---------------|---------|
| Agent identity | Profile + settings JSON | **Capsule** (soul/body/hands/governance/lineage, signed Constitution) | Soma superior |
| Memory | FAISS + local files | **Brain (WM/LTM) + SFM (768-dim Milvus)**, one canonical lane | Soma superior |
| Multi-tenancy | Single user | Tenant isolation, AAAS, tiers, billing | Soma superior |
| Governance | None | Constitution, Ed25519, AgentIQ derivation, UnifiedGate (OPA/SpiceDB) | Soma superior |
| Extensibility | Plugins (loose) | **Capsules + Capabilities** (typed, policy-bound) | Soma superior |
| Deployment | Single container | Standalone **and** AAAS enterprise stack | Soma superior |
| Plugin contract | Mature, ergonomic | Must adopt (§7 maps A0 → Capsule) | A0 superior today → clone |
| Chat UX completeness | Mature | Partial (no queue/branch/tool UI) | A0 superior today → clone + improve |
| Settings UX | Deep, progressive | Thin | A0 superior today → clone + improve |
| Messaging bridges | WA/TG/Email real | **Zero** | A0 superior → Capsule-ize |
| Skills / Knowledge / MCP | Real | Stub | A0 superior → clone |
| Tool calling E2E | Real | **Inert** (tools never passed to LLM) | Critical gap |
| Test honesty | OK | Mocked suites + infra/mocks | Must fix (R-03/R-04) |

**Design principle:** Keep Soma’s identity, memory, and governance. Clone Agent Zero’s *product surface* (what the user can do). Improve density, clarity, accessibility, and multi-tenant UX.

---

## 2. NORMATIVE REFERENCES

| ID | Reference | Role |
|----|-----------|------|
| N-1 | `SOMA-TRIAD-ARCH-001.md` §4 invariants T-1…T-8 | Memory lane law |
| N-2 | `SOMA-ARCH-INVARIANTS-001.md` | Violations are defects |
| N-3 | `SOMA-STD-CODING-001.md` | No mocks/stubs/fakes; real data only |
| N-4 | `SOMA-UI-SPEC-002.md` | Existing screen map (extend, do not discard) |
| N-5 | Agent Zero source `agent-zero-main/` | Feature inventory source |
| N-6 | ISO 9241-210 | HCD process for UI/UX |
| N-7 | ISO/IEC 25010 | Product quality model (used as checklist) |

---

## 3. ARCHITECTURE TARGET (unchanged from TRIAD-ARCH, restated for swarm)

```
User / Bridge / API
        │
        ▼
┌───────────────────────────────────────────┐
│ somaAgent01                                │
│  V3ChatOrchestrator + ToolRegistry         │
│  MemoryGateway ──► SomaBrainAdapter ONLY   │
│  Capsule (identity) + Capability (tools)   │
│  Capsule Modules (bridges, skills, MCP…)   │
└──────────────────┬────────────────────────┘
                   │  POST /memory/remember|recall|forget
                   ▼
┌───────────────────────────────────────────┐
│ somabrain                                  │
│  MemoryService (sole façade) + outbox T-6  │
│  MemoryClient (sole HTTP to store)         │
└──────────────────┬────────────────────────┘
                   │  POST /memories   (ONE WRITER)
                   ▼
┌───────────────────────────────────────────┐
│ somafractalmemory                          │
│  768-dim Milvus + ORM rows                 │
└───────────────────────────────────────────┘

shared: soma-memory-contract  (coord, embed, DTOs)
```

Invariants T-1…T-8 remain binding. **Feature work must not violate them.**

---

## 4. FEATURE PARITY MATRIX

Legend: **P0** = ship for chat E2E + production identity · **P1** = parity core · **P2** = advanced · **P3** = polish  
Status: **DONE** · **PARTIAL** · **STUB** (fake/hardcoded) · **MISSING** · **N/A**

### 4.1 Chat core

| ID | Agent Zero feature | A0 evidence | Soma today | Target (Soma form) | Pri | Owner repo/module | Acceptance |
|----|-------------------|-------------|------------|--------------------|-----|-------------------|------------|
| CH-01 | Send message + streaming reply | `api/message.py`, `webui/js/messages.js` | PARTIAL — `saas-chat.ts` WS `/ws/v2/chat/{id}` + `chat.delta` | Stream tokens + tool events; no placeholder text | **P0** | agent01 `chat_orchestrator`, `consumers/chat.py`, `webui/views/saas-chat.ts` | Playwright: send → live tokens; no `placeholder response` string ever |
| CH-02 | Attachments (file/image) | `chat/attachments/*`, `api/upload.py` | PARTIAL — composer chips; send path unproven | Full upload → `admin/files` → multimodal to LLM | **P0** | `admin/files`, `admin/multimodal`, `saas-composer.ts` | File + image round-trip in chat E2E |
| CH-03 | Message queue (queue while agent runs) | `message_queue_*`, `chat/message-queue/` | **MISSING** | Queue panel + send-later + reorder | P1 | `webui` + `consumers/chat.py` | Queue N messages during stream; flush order preserved |
| CH-04 | Pause / Nudge / Stop / Reset / Terminate | `pause`, `nudge`, `api_reset_chat`, `stop` | **MISSING** in UI (WS has typing/ping) | Top-bar controls bound to orchestrator interrupt | **P0** | `chat_orchestrator`, `saas-chat.ts` | Pause freezes; nudge injects; stop ends turn |
| CH-05 | Chat branching | `_chat_branching` | **MISSING** | Branch at any message → new conversation with prefix | P2 | `admin/chat`, `saas-chat` | Branch creates fork with shared history prefix |
| CH-06 | Chat compaction (summarize history) | `_chat_compaction` | **MISSING** | Compact to summary message; keep original in storage | P1 | `admin/core/context`, `admin/chat` | Token count drops; recall still works |
| CH-07 | Chat naming (manual + auto) | `_chat_naming` | PARTIAL — `title_update` WS event | Auto-name via utility model + rename UI | P1 | `admin/chat`, `saas-chat` | Title updates without reload |
| CH-08 | History / load / remove / export | `history_get`, `chat_load/remove/export` | PARTIAL — conversation list | Full history modal, search, export markdown/JSON | P1 | `admin/chat`, `saas-chat` | Export file downloads; delete is hard-delete |
| CH-09 | Multi-conversation sidebar + folders + pin | `sidebar/chats`, `_sidebar_folders`, `_pin_to_top` | PARTIAL — list only | Folders, pin, drag order, search | P2 | `webui/src` sidebar | Pin persists across reload |
| CH-10 | Slash commands | `_commands` | **MISSING** | `/command` palette in composer | P2 | `saas-composer` | Commands listed and executed |
| CH-11 | Process steps / tool call collapsible UI | `messages/process-group/*` | **MISSING** (Phase 9 empty) | Live tool-call timeline in message | **P0** | `chat_orchestrator`, `saas-chat` | Tool call shows name/args/result |
| CH-12 | Message action buttons (copy, branch, retry) | `messages/action-buttons/` | **MISSING** | Copy / regenerate / branch / feedback | P1 | `saas-chat` | Copy puts markdown on clipboard |
| CH-13 | Interventions mid-loop | `handle_intervention` in `agent.py` | **MISSING** | User message during run is inserted next loop | P1 | `chat_orchestrator` | Mid-stream message visible to model |
| CH-14 | Full-screen input modal | `modals/full-screen-input/` | **MISSING** | Expand composer | P3 | `saas-composer` | Expand/collapse restores draft |
| CH-15 | Notifications panel | `notifications/*`, `notify_user` | PARTIAL — `admin/notifications` | Agent→user notify + history + mark-read | P1 | `admin/notifications`, `webui` | Notification appears while chat open |

### 4.2 Models, providers, settings

| ID | Agent Zero feature | Soma today | Target | Pri | Owner | Acceptance |
|----|-------------------|------------|--------|-----|-------|------------|
| MD-01 | Provider registry (OpenAI, Anthropic, Google, Groq, Ollama, custom) | PARTIAL — `LLMModelConfig` + LiteLLM (data-driven) | Full provider presets UI like A0 `_model_config` | **P0** | `admin/llm`, `saas-settings` | Add Groq/OpenAI/Ollama row → chat uses it |
| MD-02 | Model presets + per-chat/agent/project override | **MISSING** | Preset picker + chat-level override | P1 | `admin/llm`, `saas-chat` top | Switch model mid-conversation |
| MD-03 | Model search / catalog | **MISSING** | Search providers’ model lists | P2 | `admin/llm` | Search returns live catalog |
| MD-04 | API keys management UI | PARTIAL — `saas-admin-api-keys` | Per-provider key vault + test connection | **P0** | `admin/secrets`, `admin/apikeys` | Key saved → provider works; never echoed |
| MD-05 | Model setup gate (block chat until model configured) | `model-setup-gate.html` | First-run wizard if no model | P1 | `saas-chat` | Gate shows when zero models |
| MD-06 | Utility / chat / embedding model split | PARTIAL (FKs on Capsule) | Explicit 3-role model config UI | **P0** | Capsule body + `saas-settings` | Capsule shows 3 model slots |
| MD-07 | LiteLLM global kwargs | **MISSING** | Advanced provider kwargs editor | P3 | `admin/llm` | Kwargs persist and apply |
| MD-08 | Agent profiles (default, developer, researcher…) | PARTIAL — Capsule templates | Profile gallery like A0 `agents/*` | P1 | `admin/agents`, Capsule | Create from profile |

### 4.3 Memory, knowledge, context

| ID | Agent Zero feature | Soma today | Target | Pri | Owner | Acceptance |
|----|-------------------|------------|--------|-----|-------|------------|
| MEM-01 | Memory save/load/forget tools | PARTIAL — gateway + tools partial | Real tools; **forget works** (brain delete) | **P0** | triad memory lane | forget → recall empty (T-4) |
| MEM-02 | Memory dashboard UI | PARTIAL — `saas-memory-view` | A0-style dashboard: search, detail, delete | P1 | `admin/memory`, `webui` | Search hits live Brain+SFM |
| MEM-03 | Knowledge import / reindex | STUB — `admin/knowledge` hardcoded | Real ingest → chunk → embed → SFM | P1 | `admin/knowledge`, SFM | PDF/txt indexed and recalled |
| MEM-04 | Behaviour rules (memory) | PARTIAL — Capsule `persona_config` | Behaviour editor in UI | P2 | Capsule editor | Rule affects replies |
| MEM-05 | Context window meter | `_context_window` | Token budget meter (5-lane) in chat | P1 | `context/lanes.py`, webui | Meter matches orchestrator budget |
| MEM-06 | Context doctor (JSON repair) | **MISSING** | Auto-repair malformed tool JSON | P2 | orchestrator | Broken JSON recovers |
| MEM-07 | Solutions / habits memory | Brain has consolidation | Surface in UI | P2 | somabrain | Consolidated facts visible |
| MEM-08 | Document query (RAG tool) | STUB | Real `document_query` tool | P1 | tool_executor | Ask about uploaded doc |

### 4.4 Tools, code, files, editors

| ID | Agent Zero feature | Soma today | Target | Pri | Owner | Acceptance |
|----|-------------------|------------|--------|-----|-------|------------|
| TL-01 | Tool calling E2E (function calling) | **BROKEN** — `tools_for_llm` never passed; Phase 9 no-op | Pass `tools=` to LiteLLM; execute via ToolRegistry; stream tool events | **P0** | `chat_orchestrator`, `tool_executor` | Echo/timestamp/file tools actually run |
| TL-02 | Code execution (python/node/shell) | PARTIAL — `CodeExecutionTool` | Sandbox sessions + output stream in UI | **P0** | `tool_executor/sandbox_manager` | Code runs and result in chat |
| TL-03 | File browser + workdir | PARTIAL — `admin/files` | A0-parity tree, upload, download, rename, delete, extract | P1 | `admin/files`, webui | CRUD on workdir files |
| TL-04 | Text editor / code editor canvas | `_editor`, `_text_editor` | Right-canvas editor surface | P2 | webui canvas | Edit + save file |
| TL-05 | Tool policy / approval UI | Capsule `tool_policy` JSON | Approve / deny / auto UI + prompt | **P0** | Capsule + webui | Approval modal on dangerous tool |
| TL-06 | Search engine tool | **MISSING** | DuckDuckGo/Searx tool as Capability | P1 | tool_executor | Search returns results to model |
| TL-07 | MCP client (stdio/sse/http) | STUB — settings toggle | Real MCP connect → Capabilities | P1 | `admin/tools`, new mcp client | MCP tool appears and runs |
| TL-08 | MCP server (expose Soma tools) | STUB | FastMCP server + token | P2 | `admin/tools` | External client lists tools |
| TL-09 | Subagents / call_subordinate | PARTIAL — delegation_gateway | Named sub-capsule delegation | P2 | orchestrator | Sub-task completes and returns |
| TL-10 | A2A protocol | STUB | Wire or feature-flag off | P2 | `admin/a2a` | Agent card reachable |
| TL-11 | Skills tool + catalog | **MISSING** | Skill store, inject into prompt | P1 | `admin` skills domain | Skill markdown loaded into turn |
| TL-12 | Scheduler tool + cron | STUB | Real scheduler worker + jobs | P2 | `admin/scheduler` | Cron fires agent turn |
| TL-13 | Goal tracking tool | **MISSING** | Per-chat goal + tool | P2 | orchestrator | Goal visible and updated |
| TL-14 | Vision load / image understanding | PARTIAL — multimodal | Vision tool + image in chat | P1 | `admin/multimodal` | Image Q&A works |
| TL-15 | Office artifacts | `_office` | ODF/docx generate as Capability | P3 | tool_executor | Docx produced |
| TL-16 | Browser automation | PARTIAL — `browser-use` dep | Playwright tool + canvas panel | P2 | tool_executor + canvas | Navigate and screenshot |
| TL-17 | Desktop (VNC) surface | **MISSING** | Optional desktop canvas | P3 | webui canvas | — |

### 4.5 Messaging bridges (as Capsules) — P0 for product

| ID | Agent Zero feature | A0 evidence | Soma today | Target (Capsule form) | Pri | Acceptance |
|----|-------------------|-------------|------------|----------------------|-----|------------|
| BR-01 | WhatsApp bridge | `plugins/_whatsapp_integration/` (Baileys Node `whatsapp-bridge/bridge.js`, QR, poll, reply ext) | **MISSING** (integrations stub only) | **WhatsApp Capsule** — Channel, session, inbound/outbound, QR pairing, group/DM context, slash commands | **P0** | Send WA message → agent replies via Capsule; QR connect works |
| BR-02 | Telegram bridge | `plugins/_telegram_integration/` (aiogram, webhook/poll, multi-bot, draft edits) | **MISSING** | **Telegram Capsule** — bot token, webhook, typing/draft, group topics | **P0** | TG bot replies with streaming draft |
| BR-03 | Email bridge | `plugins/_email_integration/` (IMAP/SMTP handlers) | **MISSING** (SMTP only for auth mail) | **Email Capsule** — IMAP poll, SMTP send, thread context | P1 | Email in → reply out |
| BR-04 | Slack / Discord | partial A0 ecosystem | **MISSING** | **Slack/Discord Capsule** (feature-flagged) | P2 | — |
| BR-05 | Bridge UI config | `plugins/*/webui/config.html` | **MISSING** | Capsule module settings screens (§6.4) | **P0** | Configure + test connection in UI |
| BR-06 | Per-channel system prompt context | `system_prompt/_20_wa_context.py` etc. | N/A | Capsule `persona_config.channel_context` | **P0** | Agent knows channel + contact |
| BR-07 | Outbound retry / DLQ | bridge_manager | N/A | `services/bridge_worker` + `dlq_store` | **P0** | Failed send retried; never silent-drop |
| BR-08 | Attachments across bridges | attachment_reader/writer | N/A | Shared media pipeline → `admin/files` | P1 | Image WA → LLM sees image |
| BR-09 | Multi-tenant channel binding | N/A (A0 single-user) | N/A | Channel → tenant → Capsule binding | **P0** | No cross-tenant message leak |

### 4.6 Voice

| ID | Agent Zero feature | Soma today | Target | Pri | Acceptance |
|----|-------------------|------------|--------|-----|------------|
| VO-01 | STT (Whisper) in composer | Button no-op; `admin/voice` real | Wire mic → transcribe → composer | **P0** | Speak → text in input |
| VO-02 | TTS playback | PARTIAL | Stream TTS on reply (opt-in) | P1 | Hear reply |
| VO-03 | Voice personas | PARTIAL — `saas-voice-personas` | Persona pick + preview | P1 | Persona changes voice |
| VO-04 | Voice sessions history | PARTIAL — `saas-voice-sessions` | Session list + play | P2 | — |

### 4.7 Platform, security, ops

| ID | Agent Zero feature | Soma today | Target | Pri | Acceptance |
|----|-------------------|------------|--------|-----|------------|
| PF-01 | Backup / restore | Brain has API; agent UI export-only | Triad backup UI + API | P1 | Restore test passes |
| PF-02 | Tunnel / remote access | **MISSING** | Optional tunnel module | P3 | — |
| PF-03 | Notifications | PARTIAL | Complete (CH-15) | P1 | — |
| PF-04 | OAuth / login hardening | PARTIAL Keycloak/OIDC | Login, MFA, session fix (no localStorage tokens) | **P0** | Tokens httpOnly; MFA works |
| PF-05 | Tool access policy | Capsule `tool_policy` | + `_tool_access` parity (per-project sparse) | P1 | Denied tool never runs |
| PF-06 | Infection check (prompt injection) | **MISSING** | Scan external content before prompt | P1 | Injected prompt neutralized |
| PF-07 | Plugin install/scan/validate | STUB `admin/plugins` | Real Capsule Module host (§7) | **P0** | Install + enable module works |
| PF-08 | Feature flags / tiers | PARTIAL — FeatureRegistry | Every module toggleable (billing, LDAP, OPA…) | **P0** | Disable module removes UI + routes |
| PF-09 | Onboarding / welcome / whats-new | PARTIAL | First-run wizard + discovery cards | P1 | New user reaches first chat |
| PF-10 | Time travel / workdir history | **MISSING** | Git-like snapshots | P3 | — |
| PF-11 | Self-update | **MISSING** | Release channel UI | P3 | — |
| PF-12 | Orchestrator (external coding agents) | **MISSING** | Optional Codex/Claude Code connectors | P3 | — |
| PF-13 | Desktop app shell | **MISSING** | PWA / desktop wrapper | P3 | — |
| PF-14 | Migrate from A0/other agents | **MISSING** | Import chats/config | P2 | — |
| PF-15 | Audit log | PARTIAL — `saas-audit-log` | Every mutation audited | P1 | — |

### 4.8 Parity scorecard

| Domain | A0 features counted | Soma DONE | PARTIAL | STUB/MISSING | P0 count |
|--------|---------------------|-----------|---------|--------------|----------|
| Chat core | 15 | 8 | 4 | 3 | 5 |
| Models/settings | 8 | 4 | 3 | 1 | 4 |
| Memory/knowledge | 8 | 3 | 3 | 2 | 1 |
| Tools/code/files | 17 | 5 | 5 | 7 | 3 |
| Bridges | 9 | 5 | 2 | 2 | 6 |
| Voice | 4 | 2 | 2 | 0 | 1 |
| Platform/security | 15 | 6 | 5 | 4 | 3 |
| **TOTAL** | **76** | **33** | **24** | **19** | **23 P0** |

### 4.8.1 Progress log (2026-09-27 execution)

| Item | Status |
|------|--------|
| H1–H4 Health (webui DNS + healthcheck, stack up) | **DONE** |
| A1–A4 Honesty (mocks deleted, stubs 501, UI fakes purged) | **DONE** |
| A5–A7 Fail-closed tenant/allow-list/recall | **DONE** |
| M1–M2 One write lane + real forget | **DONE** |
| C1 Tool calling E2E (tools= + Phase 9) | **DONE** |
| C2–C4 Chat UI (timeline, composer, topbar, WS control) | **DONE** |
| C5 Models settings UI | **DONE** |
| C6 History rename/delete/export | **DONE** |
| D1–D2 Capsule Module host + Channel model | **DONE** |
| D3 WhatsApp Capsule bridge | **DONE** |
| D4 Telegram Capsule bridge | **DONE** |
| D7 Channels settings UI + lifecycle API | **DONE** |
| Brain compliance (fail-closed tenant, recall raise, vault/webhook) | **DONE** |
| C7 Memory dashboard / knowledge ingest | PARTIAL |
| E1–E8 remaining P2/P3 | OPEN |

> Interpretation: Soma has strong foundations (Capsule, memory triad, SaaS) but **product surface parity is low**. Swarm must execute **23 P0 items** first for “agent can chat with all features”, then P1.

---

## 5. UI/UX DEVELOPMENT SPECIFICATION (complete — guides implementation)

### 5.1 Design principles (improved vs A0)

| # | Principle | Improvement over A0 |
|---|-----------|---------------------|
| U-01 | Chat is hero | Larger message column; tool timeline is first-class |
| U-02 | Canvas is context | Unified right rail (files, browser, memory, editor) with surface registry |
| U-03 | Progressive settings | A0 density with Soma section IA and searchable command palette (Cmd-K) |
| U-04 | Dark-first, glass surfaces | Keep Soma `saas-glass-*` language; drop Alpine for Lit 3.x |
| U-05 | Keyboard-first | Full shortcuts map (send, queue, stop, branch, palette) |
| U-06 | Honest UI | Never show fabricated metrics (`brain-store.ts` hardcoded `memoryUsage` **must die**) |
| U-07 | Two modes, one UI | Standalone / AAAS; enterprise adds panels only |
| U-08 | Bridge-aware | Channel badge on every conversation (WhatsApp/Telegram/Web) |

### 5.2 Design system (canonical)

| Token | Value |
|-------|-------|
| Framework | Lit 3.x + TypeScript (VIBE) |
| Type | Inter / JetBrains Mono |
| Color dark | bg `#0a0a0a`, surface `#121214`, text `#fafafa`, accent `#3b82f6`, ok `#22c55e`, warn `#f59e0b`, err `#ef4444` |
| Spacing | 4px grid |
| Radius | 8 / 6 / 4 |
| Components | Extend existing `webui/src/components/saas-*.ts` — **one design system only** |

### 5.3 Screen inventory (complete target)

```
PUBLIC
  /login /register /forgot-password /reset-password /auth/callback /mfa

CORE
  /chat                          HERO — workspace (sidebar + stream + right rail)
  /chat/:conversation_id
  /agents /agents/:id /agents/create
  /capsules /capsules/:id        Capsule editor (soul/body/hands/governance)
  /settings                      Hub with Cmd-K
    /settings/models             providers, presets, keys, test
    /settings/agent              persona, IQ knobs, prompts
    /settings/tools              capabilities, tool policy, MCP
    /settings/memory             Brain/SFM, recall limits, forget-all
    /settings/knowledge          sources, import, reindex
    /settings/skills             catalog, import
    /settings/channels           WhatsApp / Telegram / Email / Slack Capsule modules
    /settings/voice              STT/TTS, personas
    /settings/ui                 theme, language, density, shortcuts
    /settings/modules            feature toggles (billing, LDAP, OPA, Vault, Kafka…)
    /settings/backup             backup/restore
    /settings/security           API keys, sessions, audit
    /settings/tenants            AAAS only
  /profile

RIGHT RAIL SURFACES (chat)
  Files · Browser · Editor · Memory · Channel · Tool timeline
```

### 5.4 Chat workspace — component tree (file targets)

```
webui/src/
├── components/
│   ├── saas-chat-workspace.ts      # layout shell (IMPROVE existing)
│   ├── saas-composer.ts            # input, attachments, mic, queue, slash (REBUILD)
│   ├── saas-composer-menu.ts       # attach, voice, commands (EXTEND)
│   ├── saas-message-list.ts        # NEW stream list
│   ├── saas-message.ts             # NEW markdown + actions
│   ├── saas-tool-timeline.ts       # NEW process-group equivalent
│   ├── saas-message-queue.ts       # NEW
│   ├── saas-chat-topbar.ts         # NEW model picker, pause/nudge/stop, channel badge
│   ├── saas-right-panel.ts         # surface registry (EXTEND)
│   ├── saas-capsule-editor.ts      # EXTEND to full soul/body/hands UI
│   ├── saas-module-card.ts         # NEW module/plugin card (enable/config)
│   ├── saas-bridge-config.ts       # NEW channel module config
│   └── saas-command-palette.ts     # NEW Cmd-K
├── views/
│   ├── saas-chat.ts                # REBUILD to workspace (no placeholders)
│   ├── saas-settings-models.ts     # NEW
│   ├── saas-settings-channels.ts   # NEW
│   ├── saas-settings-tools.ts      # NEW
│   ├── saas-settings-knowledge.ts  # NEW
│   ├── saas-settings-modules.ts    # NEW
│   └── …existing saas-*.ts         # keep; remove mock fallbacks
└── stores/                         # chat, composer, queue, channel, model, memory
```

### 5.5 Settings IA (clone A0 depth, Soma structure)

| Section | Panels | Backing API | Module flag |
|---------|--------|-------------|-------------|
| Models | providers, keys, presets, test | `/api/v2/llm`, `/secrets` | core |
| Agent | persona, IQ, prompts, profiles | `/agents`, `/capsules` | core |
| Tools | capabilities list, policy matrix, MCP client/server | `/tools`, `/capabilities` | core / `mcp` |
| Memory | gateway status, recall, forget, budget | `/memory`, `/somabrain` | core |
| Knowledge | sources, import, index status | `/knowledge` | `knowledge` |
| Skills | catalog, import, scan | new `/skills` | `skills` |
| Channels | WhatsApp, Telegram, Email, Slack | new `/bridges` | `bridge_*` |
| Voice | STT/TTS, personas | `/voice` | `voice` |
| UI | theme, language, density | `/ui` | core |
| Modules | toggle every enterprise feature | `/features`, `/aaas/features` | all |
| Backup | create/inspect/restore | new `/backup` | `backup` |
| Security | keys, sessions, audit | `/apikeys`, `/audit` | core |
| Tenants | AAAS admin | `/aaas/*` | `aaas` |

### 5.6 UX flows (must implement)

1. **First run** → login → model gate → create Capsule from profile → first chat → memory confirmation.
2. **Chat turn** → compose (text+file+voice) → stream (+ tool timeline) → actions (copy/branch/retry) → memory write visible.
3. **Bridge setup** → Channels → WhatsApp → QR → test message → channel badge on new chats.
4. **Tool approval** → model requests tool → approval modal (if policy) → execute → result in timeline.
5. **Module off** → disable WhatsApp module → UI + routes + workers stop (fail-closed).

### 5.7 UI acceptance (Playwright, no false “ready”)

| Test | Assertion |
|------|-----------|
| UI-AT-01 | Login → chat loads, zero `placeholder` strings in DOM |
| UI-AT-02 | Send message → `chat.delta` tokens render progressively |
| UI-AT-03 | Tool call renders timeline with args + result |
| UI-AT-04 | Model switcher changes active model for next turn |
| UI-AT-05 | Settings → Channels → WhatsApp shows QR or connected state from real API |
| UI-AT-06 | Cmd-K opens palette and routes to settings |
| UI-AT-07 | No hardcoded metrics (grep `12400` / `getMock`) in bundle |
| UI-AT-08 | WCAG: focus rings, contrast AA on primary surfaces |

---

## 6. CAPSULE MODULE CONTRACT (A0 plugin → Soma)

### 6.1 Mapping

| A0 plugin concept | Soma Capsule Module |
|-------------------|---------------------|
| `plugin.yaml` | `module.yaml` (name, title, version, settings_sections, always_enabled, permissions) |
| `default_config.yaml` | `module.config.json` defaults + Capsule `persona_config.modules.*` |
| `api/*.py` | Ninja router mounted under `/api/v2/modules/<name>/` |
| `helpers/` | `admin/modules/<name>/services/` |
| `tools/` | `Capability` rows + `tool_executor` handlers |
| `prompts/` | Prompt fragments merged into Capsule `system_prompt` / channel context |
| `extensions/python/<point>/` | Django signals + orchestrator hooks (`message_loop_start`, `process_chain_end`, …) |
| `extensions/webui/<point>/` | Lit slots (`chat-input-end`, `settings-panel`, `canvas-surface`) |
| `webui/config.html` | `saas-bridge-config` / module settings view |
| WhatsApp Node bridge | `services/bridge_worker` process + optional sidecar container |
| Telegram aiogram | same bridge worker with TG driver |
| Email IMAP/SMTP | same bridge worker with mail driver |

### 6.2 Built-in Capsule Modules (first wave)

| Module ID | Title | Feature flags | Pri |
|-----------|-------|---------------|-----|
| `mod_whatsapp` | WhatsApp Channel | `bridge_whatsapp` | P0 |
| `mod_telegram` | Telegram Channel | `bridge_telegram` | P0 |
| `mod_email` | Email Channel | `bridge_email` | P1 |
| `mod_mcp` | MCP Client/Server | `mcp` | P1 |
| `mod_skills` | Skills | `skills` | P1 |
| `mod_knowledge` | Knowledge/RAG | `knowledge` | P1 |
| `mod_memory_dashboard` | Memory Dashboard | core | P1 |
| `mod_backup` | Backup & Restore | `backup` | P1 |
| `mod_voice` | Voice STT/TTS | `voice` | P0 |
| `mod_browser` | Browser Tool | `browser_use` | P2 |
| `mod_code` | Code Execution | core | P0 |
| `mod_scheduler` | Scheduler | `scheduler` | P2 |

### 6.3 Bridge Capsule — data model (spec only)

| Entity | Fields (normative) |
|--------|-------------------|
| `Channel` | id, tenant FK, capsule FK, kind (whatsapp/telegram/email/slack/web), status, config JSON, credentials ref (Vault), created_at |
| `BridgeSession` | channel FK, external_user/chat id, state (pending/active/paused), context JSON |
| `InboundMessage` | channel, session, external_id, direction, payload, attachments, received_at, processed_at |
| `OutboundMessage` | channel, session, payload, status (queued/sent/failed), attempts, last_error, idempotency_key |

**Security (T-5):** webhook HMAC verify; no silent default tenant; credentials in Vault/secrets store only; fail-closed on missing channel binding.

### 6.4 Hooks required in orchestrator (parity with A0 extensions)

| Hook | When | Bridge use |
|------|------|------------|
| `message_loop_start` | before LLM | load channel context |
| `system_prompt` | prompt build | inject channel/persona |
| `response_stream` | tokens | Telegram draft edit / WA typing |
| `tool_execute_after` | tool done | forward result |
| `process_chain_end` | turn end | send reply to channel |
| `monologue_end` | session end | typing cleanup |
| `job_loop` | worker tick | poll WA/TG/IMAP |
| `handle_exception` | error | notify channel on failure |

---

## 7. CODE REMEDIATION — DEDUPLICATION (no more dup/trip)

### 7.1 Severity-ordered findings (from audit)

| ID | Finding | Copies | Risk | Canonical owner | Dies |
|----|---------|--------|------|-----------------|------|
| D-01 | `_stable_coord` + preimage | **5** | HIGH | `soma-memory-contract` | 4 defs + 3 wrappers |
| D-02 | Competing embedders (3 algorithms) | **3** | HIGH | `soma-memory-contract.embed_text` | SFM `HashEmbedder`, Brain `TinyDeterministicEmbedder` for seam |
| D-03 | Dual write path to store | 2 writers | HIGH | Brain sole writer (T-1) | Fanout dual-write; SFMAdapter off hot path |
| D-04 | `forget` no-op on brain | 1 | HIGH | Brain `POST /memory/forget` | fake True/False |
| D-05 | Tenant resolvers + headers | **3** | HIGH | `resolve_tenant` (accept both headers during migration) | 2 extras |
| D-06 | Competing memory façades | **7** in Brain | HIGH | `memory/client/` + `MemoryService` | `controls/memory_client`, `direct_backend`+`backends`, FractalClientAdapter re-key |
| D-07 | Embed-dim 768 constant | **3 repos** | MED | contract constant | local defaults |
| D-08 | DTO twins (`RecallHit`×3, `MemoryAck`×2, …) | many | MED | contract DTOs | `core/models.py` mem DTOs, 2× RecallHit |
| D-09 | HTTP helpers / bearer builders | 3+15 sites | MED | thin `soma-http` | per-site httpx, `memory_client_helpers` (DEAD) |
| D-10 | SFM dual auth | 2 | MED | `admin/aaas/auth.py` | `StandaloneAuth` dup (keep tenant-pin behaviour) |
| D-11 | Settings resolvers | **6** | MED | Django settings + `get_memory_setting` | `env_config`, `unified_settings`, mode class dup |
| D-12 | infra/mocks + wrong dialect | 2 | HIGH | delete mocks | `infra/mocks/**` |
| D-13 | Mocked tests | 5 files | MED | live integration tests | `test_seam_contract.py` etc. |
| D-14 | Broken import `memory.backend`→`memory_client` | 1 | HIGH | fix to `client` | — |
| D-15 | Two design systems + dual token storage | 2 UIs | MED | `saas-*` + cookie auth | `eog-tier-builder`, sessionStorage tokens, `getMockIntegrations` |
| D-16 | Stub APIs pretending production (`plugins/api.py`, `integrations`, `knowledge`, `scheduler`) | many | HIGH | real implementations | hardcoded Plugin lists |
| D-17 | Triple error catalogs / compatibility.json | 3 | LOW | shared or documented split | overlap values |
| D-18 | Phase 9 tool execution no-op | 1 | **P0** | real tool executor | fake `phase_completed=9` |

### 7.2 Remediation waves (risk-ascending)

| Wave | WPs | Theme | Exit criteria |
|------|-----|-------|---------------|
| **W0** | Delete dead `memory_client_helpers/`; fix `memory/backend.py` import; delete `infra/mocks/`; remove mock compose services; kill `getMock*` and hardcoded Plugin list APIs from production path | Safe deletes + honesty | `find infra/mocks` empty; no fake responses on main routes |
| **W1** | Fail-closed tenant (`R-05` from TRIAD-ARCH); empty allow-list deny; recall raises on outage | Security | no-tenant → 400; SFM down → error not `[]` |
| **W2** | One write lane (R-01): Brain-only writer; `forget` real; SFMAdapter ops-only | Architecture T-1/T-4 | one remember ⇒ one `POST /memories`; forget ⇒ recall empty |
| **W3** | `soma-memory-contract` package; switch 3 repos; equality test vectors (32 seeds) | T-2/T-3 | grep `_stable_coord` = 1 definition |
| **W4** | Collapse façades/DTOs/HTTP/tenant/settings intra-repo | Dedup | §7.1 rows D-05…D-11 closed |
| **W5** | Real tests (R-04); CI guards vs mocks and `infra/mocks` | T-8 | grep mock markers = 0 outside allowlist |
| **W6** | Bounded pools (R-06); durable outbox (R-08); agent health (R-09) | Scale + ops | pool metric; write survives restart; containers healthy |
| **W7** | Frontend strangler: one design system, cookie auth only, no fabricated metrics | UI honesty | UI-AT-07 |

### 7.3 Ownership map (RACI — single owner per concern)

| Concern | **A** Accountable (owns) | R Responsible | C Consult | I Inform |
|---------|--------------------------|---------------|-----------|----------|
| Coord / embed / memory DTOs | **soma-memory-contract** | all 3 repos import | QA | PM |
| Memory write lane | **somabrain** | agent MemoryGateway (client only) | SFM | UI |
| Vector store + search | **somafractalmemory** | — | brain | agent |
| Chat orchestrator + tools | **somaAgent01/core** | tool_executor | brain | UI |
| Capsule identity/governance | **somaAgent01/core models** | agents API | security | UI |
| Capsule Modules (plugins) | **somaAgent01/admin/modules** | bridge_worker | security | UI |
| Channels/bridges runtime | **somaAgent01/services/bridge_worker** | modules | security | ops |
| UI design system | **somaAgent01/webui** | — | UX | all |
| Feature flags / tiers | **somaAgent01/features + aaas** | — | PM | UI |
| AuthN/AuthZ | **somaAgent01/auth + unified_gate** | SFM/brain auth adapters | security | all |
| Tests honesty | **each repo tests/** | CI | QA | PM |
| ISO docs | **docs/iso** (this series) | each WP | PM | all |

---

## 8. RAPID DEVELOPMENT PLAN (swarm-ready work packages)

### 8.1 Execution rules for the swarm

1. **One WP = one agent** (or one tight pair). Do not cross WP boundaries without update.
2. Every WP: *read this doc → implement → test → write evidence → mark done*.
3. **No mocks.** Integration tests skip if infra absent (`pytest.skip`), never fake.
4. Cite `file:line` in WP evidence.
5. Respect T-1…T-8. Feature code that dual-writes memory is a defect.
6. UI work runs Playwright verification before any “done” claim.
7. After W0–W2, chat E2E is the daily bar.

### 8.2 Work packages

#### Phase A — Foundation & honesty (parallelizable)

| WP | Title | Depends | Owner target | Done when |
|----|-------|---------|--------------|-----------|
| A1 | Delete dead code (`memory_client_helpers`, broken imports, `core/models.py` mem DTOs) | — | somabrain, agent01 | import graph clean |
| A2 | Delete `infra/mocks/` + compose entries + CI guard | — | agent01 | no mock images |
| A3 | Replace stub API handlers (`plugins`, `integrations`, `knowledge`, `scheduler`) with real empty-state (fail-closed, no fake lists) | — | agent01 | API returns empty + 200 or 501, never fake rows |
| A4 | Kill UI mock fallbacks + hardcoded metrics | — | webui | UI-AT-07 |
| A5 | Fix agent health (webui restart loop, standalone unhealthy) | — | ops/agent01 | both healthy |
| A6 | Fail-closed tenant + empty allow-list (R-05) | — | SFM, brain | live 400 tests |

#### Phase B — Memory lane (core correctness)

| WP | Title | Depends | Done when |
|----|-------|---------|-----------|
| B1 | Real `POST /memory/forget` on brain | A6 | forget ⇒ no recall |
| B2 | Collapse to one write lane (R-01) | B1 | one remember ⇒ one row |
| B3 | Publish `soma-memory-contract` + migrate imports | A1 | 1× `_stable_coord` |
| B4 | One embedder authority + re-embed decision | B3 | vectors comparable |
| B5 | Collapse façades / DTOs / HTTP / settings | B3 | D-05…D-11 closed |
| B6 | Real integration tests + CI mock guard | B2 | T-8 met |
| B7 | Outbox durable agent writes (T-6) + bounded pools (T-7) | B2 | restart-safe |

#### Phase C — Chat E2E (product bar)

| WP | Title | Depends | Done when |
|----|-------|---------|-----------|
| C1 | Pass `tools=` to LLM; stream tool_calls; Phase 9 real execution | A5 | TL-01/TL-02 live |
| C2 | Tool timeline + approval UI | C1 | UI-AT-03 |
| C3 | Composer rebuild: attachments, mic→STT, queue, slash | A4 | CH-01/02/03/10 |
| C4 | Pause/nudge/stop/reset controls | C1 | CH-04 |
| C5 | Model settings + presets + keys UI | A3 | MD-01…MD-06 |
| C6 | Chat history/search/export + naming | C3 | CH-07/08 |
| C7 | Memory dashboard + knowledge import | B2 | MEM-02/03 |
| C8 | Playwright full chat suite | C1–C6 | all UI-AT pass |

#### Phase D — Bridges as Capsules

| WP | Title | Depends | Done when |
|----|-------|---------|-----------|
| D1 | Capsule Module host + `module.yaml` contract + flags | A3, C1 | PF-07 |
| D2 | Channel data model + Vault creds + tenant binding | D1 | BR-09 |
| D3 | WhatsApp Capsule (Baileys-equivalent bridge worker + QR UI) | D2 | BR-01/05/06 |
| D4 | Telegram Capsule (webhook/poll + draft) | D2 | BR-02 |
| D5 | Email Capsule | D2 | BR-03 |
| D6 | Shared media pipeline + DLQ/retry | D3 | BR-07/08 |
| D7 | Channels settings screens | D3 | BR-05 |

#### Phase E — Parity depth

| WP | Title | Depends |
|----|-------|---------|
| E1 | MCP client/server | C1, D1 |
| E2 | Skills + Knowledge complete | C7 |
| E3 | Voice complete (composer + TTS) | C3 |
| E4 | Backup/restore UI | A3 |
| E5 | Branching, compaction, pin/folders | C6 |
| E6 | Security: infection check, session hardening, MFA | A6 |
| E7 | Onboarding / welcome / discovery | C8 |
| E8 | Remaining P2/P3 (browser, scheduler, desktop, tunnel…) | as prioritized |

### 8.3 Timeline (rapid, parallel swarm)

| Week | Focus | Parallel agents |
|------|-------|-----------------|
| 1 | Phase A + B1–B3 | 4–6 |
| 2 | B4–B7 + C1–C2 | 4–6 |
| 3 | C3–C8 | 3–5 |
| 4 | D1–D4 | 4–5 |
| 5 | D5–D7 + E1–E3 | 4–5 |
| 6 | E4–E8 + hardening + ISO evidence closeout | 3–4 |

**Chat-with-all-core-features demo gate:** end of week 3 (Phase C exit).  
**Bridge product demo gate:** end of week 5.

---

## 9. VERIFICATION MATRIX

| Target | Evidence | Method |
|--------|----------|--------|
| Feature parity P0 = 23/23 | §4 scorecard update + tests | WP exit reviews |
| No dup/trip memory identity | grep `_stable_coord` = 1 | CI |
| No mocks in production/tests | grep `MagicMock\|unittest.mock\|infra/mocks` | CI |
| One write lane | live write → single `GET /memories/{coord}` | integration |
| forget erasure | remember → forget → recall empty | integration |
| Fail-closed tenant | request w/o tenant → 400 | integration |
| Chat E2E | Playwright UI-AT-01…08 | CI |
| Bridges | real TG/WA sandbox messages | manual + integration |
| Honest UI | no `getMock`, no `12400` | build grep |
| ISO trail | this doc + per-WP evidence files | docs/iso |

---

## 10. OPEN DECISIONS (need user before certain WPs)

| # | Decision | Options | Default if silent | Blocks |
|---|----------|---------|-------------------|--------|
| OD-1 | `direct_backend` in Brain (in-process SFM) keep or delete? | Keep as AAAS optimization vs delete (HTTP-only) | **Delete** (T-1 simplicity) | B5 |
| OD-2 | Embedder migration | Re-embed all vs accept mixed vectors | **Re-embed** offline job | B4 |
| OD-3 | Shared package layout | `soma-memory-contract` PyPI-style package vs git submodule vs copy-with-CI-equality | **Package in monorepo folder + installable** | B3 |
| OD-4 | Eye-of-god Brain admin UI | Strangler into saas-* vs keep dual UI | **Strangler** | W7 |
| OD-5 | Slack/Discord bridges | Build P2 vs skip | **Skip until WA/TG/Email done** | E8 |
| OD-6 | Commit/push policy + fresh PAT | User supplies PAT; we never reuse old | User | W0 end |

---

## 11. SWARM PROMPT TEMPLATE (copy for sub-agents)

```text
You are a SomaTech engineer executing ONE work package.

Read first (paths on disk):
- docs/iso/SOMA-A0-PARITY-001.md  (this spec — §7.1 findings, §8.2 your WP row)
- docs/iso/SOMA-TRIAD-ARCH-001.md (invariants T-1…T-8)
- docs/architecture/SOMA-ARCH-INVARIANTS-001.md
- docs/standards/SOMA-STD-CODING-001.md

WP: <ID> <title>
Depends: <list>
Done when: <exit criteria>

Rules:
- Real code only. No mocks/stubs/fakes.
- Respect single ownership (§7.3). Do not create parallel frameworks.
- Cite file:line in the PR/evidence note.
- UI: Playwright before claiming done.
- If blocked, STOP and report; do not invent.

Return: files changed, tests run, evidence, blockers.
```

---

## 12. CONCLUSION

Agent Zero wins today on **product surface** (chat UX, settings depth, plugins, bridges). Soma wins on **architecture** (Capsule identity, cognitive memory triad, tenancy, governance). The work is not to become Agent Zero — it is to **install Agent Zero’s product surface onto Soma’s superior substrate**, while **collapsing every duplicated memory/coord/tenant implementation into one canonical lane**.

Execution is 23 P0 parity items, 7 remediation waves, and 30+ work packages, deliverable by an agent swarm in ~6 weeks of rapid parallel work — gated by this document and the T-1…T-8 invariants.

**Awaiting Plan Gate approval to begin W0/A1 (deletes) and C1 (tool calling).**

---

## Annex A — Agent Zero → Soma file map (quick)

| A0 | Soma |
|----|------|
| `agent.py` monologue/message_loop | `admin/core/chat_orchestrator.py` + hooks (§6.4) |
| `plugins/_*` | `admin/modules/<name>` + Capsule Capabilities |
| `api/*.py` | Ninja routers in `admin/api.py` |
| `webui/components/**` | `webui/src/components/saas-*.ts` |
| `webui/js/websocket.js` | `webui/src/services` WS client (`/ws/v2/chat`) |
| `helpers/history.py` | `admin/chat` + Brain WM/LTM |
| `helpers/vector_db.py` | somafractalmemory |
| `tools/*` | `services/tool_executor/` + `Capability` |
| `conf/model_providers.yaml` | `LLMModelConfig` rows + LiteLLM |
| `usr/plugins` | Capsule Module install path (future) |

## Annex B — Error honesty rules (binding)

1. Never return `[]` for “service down” — raise `MemoryRecallUnavailable` (or typed degraded).
2. Never `return True` for missing delete route — implement or raise `NotImplemented`.
3. Never hardcode plugin lists or metrics in UI.
4. Never default tenant to `"default"`.
5. Never claim UI ready without Playwright.

---

## Annex C — Stub / fake inventory (must die or become real)

> Binding: every row is either **DELETE** (prefer) or **IMPLEMENT**. Leaving a fake success path is a defect. Wave W0/WP-A3 owns this list.

### C.1 Backend fakes (somaAgent01)

| Path | Fake behaviour | Action |
|------|----------------|--------|
| `admin/plugins/api.py:78-108` | hardcoded `Plugin(name="Web Search Tool")` | **IMPLEMENT** Capsule Module host (D1) or delete API |
| `admin/plugins/api.py:154-205` | enable/disable return success, no state | **IMPLEMENT** |
| `admin/plugins/api.py:282-309` | fake marketplace download counts | **DELETE** until real registry |
| `admin/integrations/models.py` | self-declared stub model | **REPLACE** by `admin/bridges` + Channel |
| `admin/integrations/api.py:312-336` | `oauth_callback` returns `connected: True` | **IMPLEMENT** token exchange or 501 |
| `admin/capabilities/api.py:136-200` | persist commented out; empty list | **IMPLEMENT** DB-backed Capability CRUD |
| `admin/tenants/api.py:77-132` | empty/fabricated tenants | **IMPLEMENT** |
| `admin/tools/api/tools.py` (was `admin/tools/api.py`, now a package) | `SYSTEM_TOOLS` dict; execute returns `pending` | **IMPLEMENT** via ToolRegistry |
| `admin/orchestrator/api.py:201-217` | Temporal start commented; fake `running` | **IMPLEMENT** or 501 |
| `admin/completions/api.py:108-125` | canned `"Hello! I'm an AI assistant..."` | **DELETE** — fake LLM forbidden |
| `admin/embeddings/api.py:113-125` | zero-vectors `[0.0]*dim` | **IMPLEMENT** via `embed_text` / provider |
| `admin/core/billing.py` | echo dicts, “call the billing API in production” | **DELETED** — file removed entirely; this system has no billing integration |
| `admin/auth/api_sso.py:46-53` | LDAP bind not performed | **IMPLEMENT** ldap3 or 501 |
| ~~`admin/analytics/api.py`~~ | deleted: fabricated empty aggregates, no analytics store behind them | removed — do not rebuild without a real store |
| `admin/multimodal/execution.py:300,423` | Playwright “in production” stubs | **IMPLEMENT** |
| `admin/a2a/api.py` | Temporal stubs | **IMPLEMENT** or flag off |
| `admin/aaas/api/features.py:206` | `return []` | **IMPLEMENT** |
| `admin/aaas/api/integrations.py:128` | provider stub fallback | **DELETE** stub fallback |

### C.2 Infra fakes

| Path | Action |
|------|--------|
| `infra/mocks/somabrain/` | **DELETE** + remove compose service |
| `infra/mocks/somafractalmemory/` | **DELETE** + remove compose service |
| `infra/standalone/docker-compose.yml` profile `mocks` | **DELETE** section |

### C.3 Test fakes (T-8)

| Path | Action |
|------|--------|
| `somabrain/tests/unit/memory/test_seam_contract.py` | **REPLACE** with live integration tests |
| `somaAgent01/tests/unit/test_auth.py`, `test_rate_limiter.py`, `test_unified_gate.py`, `tests/phase4_validation_unified_layers.py` | **DE-MOCK** vs real Redis/OPA |
| `somabrain/tests/unit/test_aaas_mode.py` | **DE-MOCK** |

### C.4 WebUI mock fallbacks (UI-AT-07)

| Path | Action |
|------|--------|
| `saas-integrations-dashboard.ts:221-230` `getMockIntegrations()` | **DELETE** |
| `saas-tier-builder.ts:390-399` `getMockTiers()` | **DELETE** |
| `platform-metrics-dashboard.ts:376-441` `getMockMetrics/SLA` | **DELETE** |
| `saas-feature-catalog.ts:266-275` | **DELETE** |
| `saas-usage-analytics.ts:339-353` | **DELETE** |
| `saas-marketplace.ts:339` demo fallback | **DELETE** |
| `saas-chat-workspace.ts` placeholder reply string | **DELETE** (CH-01) |
| `brain-store.ts:37` `memoryUsage: 12400` | **DELETE** — live metric only |

### C.5 Enterprise modules — honest status

| Module | Status | Action |
|--------|--------|--------|
| Billing | **NONE** — this system has no billing integration | Nothing to keep; both the stub and the external client were removed |
| OPA | **REAL** `services/common/policy_client.py` | Keep |
| SpiceDB | **REAL** `services/common/spicedb_client.py` | Keep |
| Vault | **REAL** `vault_secrets.py` + compose | Keep |
| Kafka | **REAL** `event_bus.py` | Keep |
| Keycloak/JWT | **REAL** `admin/common/auth.py` | Keep |
| LDAP | **STUB** | Implement or feature-flag off |
| Temporal APIs | Partial workers / stub APIs | Implement or flag off |
| MFA | Fail-closed honest stub | Implement before claiming MFA |

---

## Annex D — Agent Zero plugin contract (normative clone source)

### D.1 Manifest (`plugin.yaml`)

```yaml
name: whatsapp_integration
title: WhatsApp
description: ...
version: 1.0.0
settings_sections: [agent]     # agent|external|developer|mcp|backup|file-browser|skills
per_project_config: true
per_agent_config: true
always_enabled: false
```

Toggle state: `.toggle-0` / `.toggle-1`. Runtime config: `config.json` over `default_config.yaml`.

### D.2 Directory capabilities (all optional, convention-discovered)

| Dir | Role | Soma mapping |
|-----|------|--------------|
| `api/<handler>.py` | `ApiHandler.process(input, request)` → `POST /plugins/<name>/<handler>` | Ninja router `/api/v2/modules/<name>/` |
| `extensions/python/<hook>/*.py` | `Extension.execute` at named hook | Django signals + orchestrator hooks §6.4 |
| `extensions/webui/<hook>/*.js\|html` | UI injection (canvas, messages, settings) | Lit slots |
| `tools/<tool>.py` | `Tool` subclass (execute/before/after/progress) | `Capability` + `tool_executor` |
| `prompts/*.md` | prompt fragments | Capsule `system_prompt` / channel context |
| `webui/{config,main}.html` + stores | settings + plugin screen | `saas-bridge-config` / module views |
| `helpers/`, `conf/model_providers.yaml`, `skills/`, `hooks.py` | support code | `admin/modules/<name>/services/` |

### D.3 A0 hook points Soma must expose (parity list)

**Python:** `agent_init`, `banners`, `before_main_llm_call`, `error_format`, `hist_add_before`, `hist_add_tool_result`, `job_loop`, `message_loop_start/end`, `message_loop_prompts_before/after`, `message_loop_result`, `monologue_start/end`, `process_chain_end`, `reasoning_stream{,_chunk,_end}`, `response_stream{,_chunk,_end}`, `startup_migration`, `system_prompt`, `tool_execute_before/after`, `user_message_ui`, `util_model_call_before`, `webui_ws_connect/disconnect/event`.

**WebUI:** `fetch_api_call_{before,after}`, `json_api_call_{before,after}`, `get_message_handler`, `get_process_step_types`, `initFw_end`, `right_canvas_register_surfaces`, `right-canvas-panels`, `set_messages_{before,after}_loop`, `webui_ws_push`.

### D.4 Settings field schema (parity)

`id, title, description, type ∈ {text,number,select,range,textarea,password,switch,button,html}, value, min, max, step, hidden, options, style` per field; sections `{id,title,description,fields,tab}`.

### D.5 Bridge message flow (clone behaviour)

**WhatsApp:** Node/Baileys bridge HTTP (`GET /messages`, `POST /send|edit|send-media|typing`, `GET /qr|health`) → Python poll (`poll_interval_seconds`) → dispatch (allowlist, groups, jid→chat) → agent `communicate` → markdown→WA reply + media. Slash commands + self-chat vs dedicated mode.

**Telegram:** aiogram bots (polling **or** webhook+secret) → allowlist / group_mode (mention|all|off) → per-user context → typing draft → reply. Welcome, callbacks, heartbeat.

**Email:** IMAP/Exchange poll (cron or seconds) → dispatcher model (new chat vs route) → thread-id subjects → SMTP reply + attachments.

Soma: same **behaviours** via `services/bridge_worker` + `Channel/Inbound/Outbound` models + Capsule binding + Vault credentials + DLQ.

---

## Annex E — Chat E2E runbook (acceptance environment)

| # | Requirement | Notes |
|---|-------------|-------|
| 1 | SFM stack :10101 + Milvus/PG/Redis/Vault | memory store |
| 2 | Brain stack :30101 | sole writer |
| 3 | `somaagent_standalone` :20020 healthy | **currently unhealthy F-12** |
| 4 | `somaagent_webui` :20080 healthy | **currently restart loop F-12** |
| 5 | Vault-seeded provider keys `secret/agent/api_keys/*` | no keys in env |
| 6 | `LLMModelConfig` row (e.g. groq/openai/gpt-oss-120b) | |
| 7 | `AAAS_DEFAULT_TENANT_ID` + active Capsule | WS requires conversation_id |
| 8 | Keycloak realm if JWT path used | client `eye-of-god` frontend |
| 9 | **Never** `--profile mocks` | F-04 |

WS contract: `/ws/v2/chat/{capsule_id}` · auth `soma-auth.<jwt>` subprotocol · `chat.delta` / `chat.done` · payload includes `conversation_id`.

---

## Annex F — Swarm launch checklist (for orchestrator agent)

- [ ] User signed Plan Gate (this doc §0)
- [ ] Fresh PAT available for R-10 (never reuse expired/compromised)
- [ ] WP backlog imported (§8.2 A/B/C/D/E)
- [ ] Each swarm agent receives §11 prompt template + its WP row
- [ ] Evidence directory convention: `docs/iso/evidence/<WP-ID>/`
- [ ] Daily bar after Phase C: Playwright chat suite green
- [ ] Feature scorecard (§4.8) updated weekly

---

*End of document — SOMA-A0-PARITY-001 v1.0.0*
