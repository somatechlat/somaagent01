# PLAN — UI/UX Feature Parity with Agent Zero (clone & better)

**Doc ID:** SOMA-UIUX-PARITY-PLAN-002
**Date:** 2026-09-27
**Owner:** somaplanet — UI/UX lane
**Status:** FOR APPROVAL — no UI production code until Plan Gate is signed (per `SOMA-A0-PARITY-001.md` §0)
**Benchmark:** Agent Zero `webui/` — 278 files (excl. vendor), 41 plugins (40 with `webui/`), 64 settings files, 24 modals
**Parent docs:** `docs/iso/SOMA-A0-PARITY-001.md` (feature matrix, §0 gate), `docs/project/PLAN-TRIAD-SEAMLESS.md` (Wave 4 = UI parity)

---

## 0. Execution gate

Binding, inherited from `SOMA-A0-PARITY-001.md` §0:

1. **No production code until Plan Gate is signed.** This document is the gate artifact.
2. **Feature clone, never code clone.** We reimplement on Lit 3.x + TypeScript + our tokens. We never copy A0's Alpine/HTML/JS.
3. **Every A0 feature must exist and be equal or better.** Where A0 is poor, we improve — and we say why.
4. **No mocks, no stubs, no placeholders, no `coming soon`, no fake metrics.** (VIBE + Annex B.) A surface that is not real must not be clickable.
5. **One design system.** Extend `webui/src/styles/tokens.css` and the existing `saas-*` components. No second token set, no second font stack.
6. **Every work package produces evidence** — Playwright traces for UI, screenshots for visual, and a row in the acceptance matrix.

---

## 1. Isolation contract — two agents, one repo

### 1.1 Current git reality (verified 2026-09-27)

| State | Ref / location | Content |
|---|---|---|
| A | `main` @ `d7bc7cb6` | last clean commit |
| B | `main` **working tree** | **137 uncommitted paths** (41 under `webui/`) |
| C | `feature/no-mocks-agent-ui-sync` @ `33ef37a1` | **other agent**, own worktree at `.worktrees/no-mocks-agent-ui-sync`, commit `fix(webui): wire chat and agent management to real backend (Phase 1)`, **205 files, +28,031 / −16,530** |

Overlap analysis of B's 41 webui paths vs C's webui paths: **26 in common** (the other agent's in-flight UI rewiring), **15 unique to B and on no branch**:

```
webui/index.html                     webui/src/services/theme-boot.ts
webui/package.json                   webui/src/services/websocket-client.ts
webui/package-lock.json              webui/src/stores/brain-store.ts
webui/public/                        webui/src/styles/material-symbols.css
webui/src/components/saas-chat-topbar.ts   webui/src/styles/tokens.css
webui/src/components/saas-message.ts
webui/src/components/saas-tool-timeline.ts
```

> **BLOCKER — unattributed UI work.** Those 15 files contain uncommitted UI/UX work that belongs to nobody's branch. `brain-store.ts` there is where `memoryUsage: 0` lives (the fix for the doc's `12400` complaint), and `tokens.css` is the design-token source. Before any UI work starts this set must be triaged: either it is prior UI-lane work to adopt onto `ui-ux-creation`, or it is the user's own edits to preserve. **Do not overwrite, do not commit to `main`, do not fold into the other agent's branch.**

### 1.2 Branch

- **Branch:** `ui-ux-creation` (created, pointer only, currently at `d7bc7cb6`, **not checked out**).
- **Do not `git checkout` it in this working tree.** A checkout would drag the 137 dirty paths onto the branch and would move the tree under the other agent.
- **Recommended base:** re-point to `feature/no-mocks-agent-ui-sync`, not `main`. Their webui changes *are* the current UI; building on stale components makes the merge unmaintainable. Cost: their branch moves, so periodic rebase is required.

### 1.3 Isolation mechanism — decision required

A branch alone does **not** isolate two agents in one checkout. Choose one:

| Option | Mechanism | Isolation | Cost |
|---|---|---|---|
| **W1 — worktree (recommended)** | `git worktree add .worktrees/ui-ux-creation ui-ux-creation` | **Total.** Matches the convention the other agent already uses (`.worktrees/no-mocks-agent-ui-sync`). Their tree is never touched. | none |
| **W2 — shared checkout, strict file ownership** | branch + surgical diffs | Weak. Any `checkout`/`reset`/`clean` by either agent destroys the other. | high coordination |

**Recommendation: W1.** This session has not been authorised to create a worktree, so this is the one gate item to confirm.

### 1.4 File ownership lanes

| Lane | Owner | Paths |
|---|---|---|
| **UI/UX (me)** | UI/UX | `webui/src/components/**`, `webui/src/views/**`, `webui/src/styles/**`, `webui/src/utils/**`, `webui/index.html`, `webui/public/**`, `docs/project/SOMA-UIUX-*` |
| **Backend wiring (them)** | other agent | `admin/**`, `services/**`, `config/**`, `infra/**`, `webui/src/services/api-client.ts`, `webui/src/services/websocket-client.ts`, `webui/src/stores/*` **fetch/state methods** |
| **Overlap — coordinate before touching** | both | `saas-right-panel.ts`, `saas-composer.ts`, `saas-chat-workspace.ts`, `saas-chat-input.ts`, `saas-chat-message-list.ts`, `saas-conversation-list.ts`, `saas-glass-modal.ts`, `components/index.ts`, `webui/package.json` |

**Overlap protocol:** (1) re-read the file at their tip before editing; (2) change render/interaction only, never their data plumbing; (3) never reformat or restructure a shared file; (4) if a shared file needs a large UI change, add a **new** component and swap one line in the shared file to use it.

---

## 2. Rules of the rebuild

1. **Reimplement, don't port.** A0 is Alpine.js + HTML partials + global JS stores. Ours is Lit 3.x + TypeScript + typed stores. Nothing crosses over as code.
2. **Better where A0 is weak** — §3.6 lists the ten deliberate improvements, each with the A0 evidence that justifies it.
3. **Honest UI.** Never render a metric, count or status we did not read from a real API. Never show a control that cannot work. Disabled controls must state *why* (`saas-chat-topbar.ts:28` already does this correctly for nudge).
4. **Keyboard first**, then pointer. Every action reachable without a mouse. WCAG 2.1 AA.
5. **One surface grammar.** Right-rail surfaces, drawers, full-screen focus and dialogs each have exactly one pattern, reused.
6. **Small vertical slices, each demoable.** No big-bang UI rewrite. Each wave ends with something clickable that was not clickable before.
7. **The Capsule is the organising unit of the interface.** Not the plugin, not the settings page, not the chat. A0 is plugin-centric; we are capsule-centric. This section is the authoritative IA and supersedes any plugin-shaped reading of the screen map in §4.

---

## 3. CAPSULE-FIRST INFORMATION ARCHITECTURE (authoritative)

Source of truth is our own model, not A0's screens:
`admin/core/models/core.py:109` `Capsule` · `:421` `CapsuleInstance` · `:443` `Capability` ·
`admin/modules/{models,manifest,registry,hooks}.py` · `services/capsule_export.py`

### 3.1 The six facets are the six primary views

`Capsule` is documented in code as *"The Atomic Unit of Agent Identity (Rule 91)"*. `services/capsule_export.py` already names the facets. The UI is those facets — one tab per facet on the Capsule workspace:

| Facet | Code fields | UI view | What the user does there |
|---|---|---|---|
| **Soul** | `system_prompt`, `personality_traits` (Big 5, 0.0–1.0), `neuromodulator_baseline`, `learning_config` (GMD η/λ/α + reward thresholds) | **Soul** | write the instruction set; tune Big-5 sliders with live description; set neuro baseline; set learning hyperparameters |
| **Brain** | `chat_model`, `image_model`, `voice_model`, `browser_model` (FK → `LLMModelConfig`), `iq_knobs` | **Brain** | bind the four model roles from *real configured* models only; tune IQ knobs |
| **Hands** | `capabilities` M2M → `Capability`; `tool_policy` `{auto_execute, approval_required, denied}` | **Hands** | attach/detach capabilities by category; drag tools across the three policy buckets |
| **Memory** | `memory_pointer` `{tenant, namespace, recall_limit, similarity_threshold}` | **Memory** | point at a namespace; set recall limit + similarity threshold; **live** recall preview against real hits only |
| **Body** | `resource_limits` | **Body** | set resource ceilings; see instance consumption when running |
| **Governance** | `constitution` FK, `constitution_ref` `{checksum, url}`, `registry_signature` (Ed25519), `certified_at` | **Governance** | bind a Constitution; show checksum + signature; certify / see certification state |

Cross-cutting, not a facet but always visible:

| Concept | Code | UI treatment |
|---|---|---|
| **Lifecycle** | `status` `draft → active → archived` | status chip + explicit transition actions (never implicit) |
| **Version lineage** | `parent` / `children` (edit-spawns-new-version) | version rail with diff-to-parent; edit always spawns a child, never mutates in place |
| **Persona knobs** | `persona_config.knobs` `{intelligence_level, autonomy_level, resource_budget}` | three persistent control knobs in the workspace chrome (this is the "control panel") |
| **Neuromodulator state** | `neuromodulator_state` `{dopamine, serotonin, norepinephrine, acetylcholine, last_synced_at}` | live read-only meters, with the sync timestamp shown (honesty: no value without a real sync) |
| **Runtime instance** | `CapsuleInstance` `{session_id, state, status, started_at, completed_at}` | instance strip: running/idle/failed, session id, duration |

### 3.2 Capsule Modules are not plugins — they *contribute* to facets

`admin/modules/manifest.py` defines `module.yaml`. A module never owns a page; it injects into the capsule UI:

```
module.yaml   name, title, version
              settings_sections: [agent|external|developer|mcp|backup|file-browser|skills]
              permissions: [network, vault:read]
              always_enabled, feature_flag, config_schema
module dir    module.yaml · module.config.json · services/ · hooks.py · api.py · prompts/
```

| Module contribution | Where it lands in the UI |
|---|---|
| `settings_sections` | rows injected into the named settings scope — never a new top-level page |
| `permissions` | **Hands** facet — capability rows, and the approval rules in `tool_policy` |
| `api.py` (Ninja `/api/v2/modules/<name>/`) | module-provided panels rendered as slots inside a facet |
| `hooks.py` (`KNOWN_HOOKS`) | visible in **Governance/Debug** as the module's live hook bindings |
| `prompts/` | merged into the Capsule **Soul** `system_prompt` — shown as an ordered, collapsible prompt stack with provenance (which module contributed which fragment) |
| `feature_flag` | gate: module cannot be enabled until the flag is on — UI shows *why*, never a dead toggle |
| `always_enabled` | toggle rendered locked with a reason |
| `config` / `config_schema` | module config form generated from the schema, validated |

Live `KNOWN_HOOKS` (`admin/modules/hooks.py:33`): `message_loop_start`, `system_prompt`, `response_stream`, `tool_execute_after`, `process_chain_end`, `monologue_end`, `job_loop`, `handle_exception` — plus 23 reserved names the UI must show as **reserved/not yet registerable**, never as working toggles.

### 3.3 Global chrome — the app is capsule-shaped

```
┌ Capsule switcher ───────────────────────────────────────────────┐
│  ◀ capsule ▶  name  v1.0.0  ● draft   [knobs: IQ|auto|budget]   │
├──────────┬──────────────────────────────────────────┬───────────┤
│ RAIL     │  WORKSPACE (facet tabs)                  │ RIGHT RAIL│
│          │  Soul · Brain · Hands · Memory · Body ·  │ surfaces  │
│ Capsules │  Governance                              │  files    │
│ Chat     │                                          │  tools    │
│ Modules  │  (one facet at a time, or compare)       │  browser  │
│ Capab.   │                                          │  editor   │
│ Instances│                                          │  debug    │
│ Const.   │                                          │  capsule  │
│ Settings │                                          │  brain    │
└──────────┴──────────────────────────────────────────┴───────────┘
```

**Rail (adaptive, B-9):** Capsules · Chat · Modules · Capabilities · Instances · Constitutions · Settings.

**Workspace:** the six facet tabs. Chat is a *peer* of the facets — the capsule you are talking through is always named in the chrome, and you can inspect/switch it mid-conversation.

**Right rail (surfaces, B-6):** files, tools, browser, editor, debug, capsule, brain — all real or explicitly disabled with a reason.

### 3.4 Where every A0 feature lands in the capsule model

Completeness is preserved — nothing is dropped, it is *re-homed*:

| A0 feature area | Lands in | Note |
|---|---|---|
| chat core (15) | **Chat** + capsule chrome | branching, time-travel, queue, attachments |
| models (8) | **Brain** facet | four model roles + `iq_knobs` |
| memory (8) | **Memory** facet | pointer + live recall preview |
| tools (17) | **Hands** facet + tools surface | capability registry + `tool_policy` buckets |
| bridges (9) | **Modules** (`mod_whatsapp`, `mod_telegram`, `mod_email`) | channel rows inside a facet; QR/connected from real API |
| voice (4) | **Brain** (`voice_model`) + voice views | B-7 state machine |
| platform (15) | **Governance** + **Modules** + Settings | constitution, certification, backup, tunnel, A2A, skills |
| A0 projects (14) | **Capsules** | our replacement — and richer: versioned, certified, lineage |
| A0 plugins (11) | **Modules** + **Capabilities** | list, execute, config, toggles — but facet-contributed |
| A0 24 modals | 3 patterns (B-4) | Drawer / Full-screen / Dialog |
| A0 64 settings files | 4 scopes (B-3) + module-injected rows | no 11-category sprawl |

### 3.5 What the capsule model gives us that A0 cannot do

This is the genuine "better", and it falls out of our own domain model rather than being bolted on:

| # | Capability | A0 | Soma |
|---|---|---|---|
| **C-1** | **Governance & certification** — constitution binding, checksum, Ed25519 `registry_signature`, `certified_at` | none | a Governance facet with real cryptographic state |
| **C-2** | **Version lineage** — `parent`/`children`, edit-spawns-new-version | none | version rail + diff-to-parent; no silent mutation |
| **C-3** | **Cognitive state** — Big-5 traits, neuromodulator baselines and live state | none | Soul sliders + live meters with sync timestamps |
| **C-4** | **Learning config** — GMD η/λ/α + reward thresholds | none | first-class, not a hidden JSON blob |
| **C-5** | **Capability policy** — `auto_execute` / `approval_required` / `denied` | flat plugin toggles | three-bucket policy editor, per-tool `timeout_seconds`, `max_retries` |
| **C-6** | **Model role separation** — chat/image/voice/browser as distinct FKs | one model picker | four explicit roles with per-role status |
| **C-7** | **Module prompt provenance** — `prompts/` merged into `system_prompt` | opaque | visible prompt stack with per-module provenance |
| **C-8** | **Lifecycle + instances** — draft/active/archived, `CapsuleInstance` sessions | none | instance strip with real session state |
| **C-9** | **Feature-flagged modules** — `feature_flag` gate, `always_enabled` | none | honest gate reasons on every disabled control |
| **C-10** | **Tenant-scoped capsules** — `tenant` FK on Capsule and Module | weak | real tenancy in the chrome |

---

### 3.6 Ten deliberate improvements over Agent Zero

Each is grounded in A0 source, not taste.

| # | A0 weakness (evidence) | Soma improvement |
|---|---|---|
| **B-1** | **No command palette.** `webui/js/shortcuts.js` is an API/notification util (`callJsonApi`, `frontendNotification`, `getCurrentContextId`) — not a palette. | **Cmd-K palette**: navigate, run actions, switch capsule/model/surface, jump to any setting. Fuzzy, keyboard-only, shows the binding for each action. |
| **B-2** | **No syntax highlighting.** `webui/js/safe-markdown.js` is 200 lines of DOMPurify + marked + GitHub link prefixes; zero highlighter. | Highlighted code blocks + language chip + copy button + line numbers past N lines. We already have the `onCodeBlock` hook in `utils/markdown.ts`. |
| **B-3** | **Settings sprawl.** 64 files across 11 top-level categories (a2a, agent, backup, developer, external, file-browser, mcp, plugins, secrets, skills, tunnel) with no progressive disclosure. | **4 scopes** (Agent / External / Connectivity / System) + settings search + "Advanced" collapse + role-gated rows. A0's 11 categories map in; nothing is lost, the noise is. |
| **B-4** | **Modal fatigue.** 24 discrete modals (context, file-browser, file-tree, rename, full-screen-input, history, image-viewer, markdown, process-step-detail, scheduler×5, …). | **Exactly three surface patterns**: Drawer (inspect/edit), Full-screen (focus: file, image, message), Dialog (destructive/irreversible only). |
| **B-5** | **40 plugin `webui/` dirs = 40 micro-design-systems**, each visually inconsistent. | Capsule Modules contribute through **typed Lit slots** inside one design system. A module cannot ship its own look. |
| **B-6** | **`surfaces.js` hardcodes `CORE_SURFACES`** (`files` :17, `browser` :40, `desktop` :47, `editor` :54); extension is plugin-only via `registerSurface()` :97. | **Typed Surface registry**: core surfaces + Capsule-Module-registered surfaces, runtime-composed, consistent chrome and error states. |
| **B-7** | **Raw `stt-service.js` / `tts-service.js`** with no visible state machine — permission, recording, transcribing, error are indistinguishable. | Explicit mic/TTS state machine with visible permission, recording, transcribing, and failure states. Composer already has `_micState`; make it legible. |
| **B-8** | **Dev tooling buried.** WebSocket event console + tester live under Settings → developer. | First-class **Debug surface** in the right rail: filterable event stream, request inspector, WS frame log. |
| **B-9** | **Sidebar is 16 files nested 4 deep** (bottom/, chats/, top-section/, tasks/). | **One adaptive rail**: icon rail → labelled rail → sectioned rail, same component, responsive. |
| **B-10** | **Sanitizer bolted on after the fact** — `marked` then `DOMPurify`. | Sanitize by construction in `utils/markdown.ts` (escape-first renderer we already own) plus an explicit XSS test matrix, so honesty is provable rather than assumed. |

---

## 4. Screen map — every A0 screen → Soma → action

> Subordinate to §3. Where this section still says "plugin" or "settings category", read it through the capsule facet lens of §3.1–§3.2. Nothing here contradicts the facets; it is the per-screen detail beneath them.

Status legend: **DONE** real and equal-or-better · **PARTIAL** real but incomplete · **PLACEHOLDER** `coming soon` / fake · **MISSING** no counterpart

### 4.1 Chat — the hero (A0: 18 components + messages + input + queue)

| A0 | Soma today | Status | Action | Improvement |
|---|---|---|---|---|
| `chat-bar-input` / `input-store.js` | `saas-composer.ts` (auto-expand, + menu, mic→real STT, send, queue-while-busy) | **DONE** | — | B-7 mic states |
| `attachments/` (store, dragDropOverlay, inputPreview) | composer `_attachments: File[]` + composerStore | **PARTIAL** | drag-drop overlay + per-file preview chips + type/size rules | inline previews, not a modal |
| `message-queue/message-queue-store.js` + `.html` | composer `_queue: ComposerSendDetail[]` | **PARTIAL** | render the queue visibly with reorder + drop | queue is visible and editable, not silent |
| `top-section/chat-top-store.js` + `chat-top.html` | `saas-chat-topbar.ts` | **PARTIAL** | see §4.1.1 | — |
| `navigation/chat-navigation-store.js` | none | **MISSING** | prev/next unread + jump-to-quote | keyboard `g ]` / `g [` |
| `model-gate-store.js` + `model-setup-gate.html` | none | **MISSING** | first-run model-not-configured gate | one-click open Models settings |
| `messages/simple-action-buttons` | **Copy only** (`saas-message.ts:390`, `:481-488`) | **PARTIAL** | §4.1.2 full action set | actions are inline and quiet, not a toolbar |
| `messages/process-group/` (dom + css) | `saas-tool-timeline.ts` (call/delta/done/approval) | **PARTIAL** | collapsible step groups, duration, arg/result panes | B-4 drawer for detail, not a modal |
| `messages/message-resize-store.js` | none | **MISSING** | wide/narrow message width toggle | remembered per user |
| `chat_branching` (plugin) | none | **MISSING** | branch from any message, side-by-side compare | first-class, not a plugin |
| `chat_compaction` (plugin) | none | **MISSING** | compact long threads with visible summary | user-controlled, undoable |
| `chat_naming` (plugin) | rename in list (`saas-chat.ts`) | **DONE** | auto-title from first turn | — |
| `pin_to_top` (plugin) | none | **MISSING** | pin conversations + messages | — |
| `error_retry` (plugin) | none | **MISSING** | retry failed turn with same/other model | — |
| `time_travel` (plugin) | none | **MISSING** | edit an earlier message and re-run from there | replaces "regenerate all" |
| `context_window` (plugin) | none | **MISSING** | live token/context budget indicator | honest numbers only |
| history modal | searchable list in left rail (rename/delete/export) | **DONE** | export format picker (md/json) | — |
| `context` modal | none | **MISSING** | context inspector drawer | B-4 drawer |
| `full-screen-input` modal | none | **MISSING** | focus composer mode | — |
| `markdown` modal | none | **MISSING** | rendered-message full view | B-2 highlight inside |
| `process-step-detail` modal | `tool.approval_request` → `tool-approval` event (`saas-tool-timeline.ts:296`) | **PARTIAL** | B-4 drawer with args, result, duration, error | — |
| `image-viewer` modal | none | **MISSING** | zoom/pan full-screen image | — |

#### 4.1.1 Chat topbar — buttons (currently PARTIAL)

| Control | Today | Target |
|---|---|---|
| Pause / Resume | **render-only** (`saas-chat-topbar.ts:284` — "Pause rendering of the stream") | Real stream pause via orchestrator interrupt; relabel to stop lying. Until the gateway supports it, the control must say "pause rendering" honestly or be removed. |
| Nudge | **disabled** (`:28` `nudgeTitle = 'Nudge requires orchestrator interrupt (not yet available on the gateway)'`, `:294`) | Keep disabled-with-reason (this is correct honest UI). Enable when the gateway exposes interrupt. |
| Stop | present | Keep + add confirm-on-stop for long tool runs |
| Reset | present (`:316`) | Keep + confirm dialog (destructive) |
| **New** Model switcher | — | Inline model + capsule switcher, showing real configured models only |
| **New** Context budget | — | token/context indicator (honest) |
| **New** Share / export | export exists | export + copy link |
| **New** Debug | — | toggles the Debug surface (B-8) |

#### 4.1.2 Message actions — every button we need

Copy (exists) · Retry · Regenerate · Edit & re-run (time travel) · Branch from here · Pin · Copy as markdown · Quote into composer · Delete message · Feedback (thumb up/down + reason) · Show raw (unrendered) · Token/cost badge.

### 4.2 Right rail / canvas (A0: `canvas/` + `surfaces.js`)

| A0 | Soma today | Status | Action |
|---|---|---|---|
| `right-canvas-store.js` + html + css | `saas-right-panel.ts` (`SurfaceKey` `:10`) | **PARTIAL** | shared surface chrome |
| `CORE_SURFACES.files` (`surfaces.js:17`) | **`coming soon`** `:222` | **PLACEHOLDER** | real file browser: tree, path bar, preview, upload/download, rename, search |
| `CORE_SURFACES.browser` (`:40`) | **`coming soon`** `:230` | **PLACEHOLDER** | embedded browser surface with honest "not connected" state when no browser worker |
| `CORE_SURFACES.editor` (`:54`) | **`coming soon`** `:238` | **PLACEHOLDER** | editor surface: open from files, syntax highlight (B-2), dirty state, save |
| `CORE_SURFACES.desktop` (`:47`) | no key | **MISSING** | decide: add surface or deliberately exclude (OD) |
| `registerSurface()` (`:97`) | none | **MISSING** | typed surface registry (B-6) |
| tools manager | **`coming soon`** `:214` | **PLACEHOLDER** | tool list with enable/disable, live call log, per-tool args schema |
| capsule / brain panels | real | **DONE** | keep |

**This is the largest visible gap. Four of six rail tabs are fake. Priority 1.**

### 4.3 Settings (A0: 64 files, 11 categories → our 4 tabs)

| A0 category | Lands in our tab | Status | Action |
|---|---|---|---|
| `agent/` (agent, interface, locale, voice, workdir, workdir-file-structure-test) | **Agent** | **PARTIAL** | persona, interface prefs, locale, voice, workdir + file-structure test |
| `external/` (api_keys, api-examples, auth, external_api, litellm, secrets, self-update, update_checker) | **External** | **PARTIAL** | provider keys, API examples, auth, secrets, self-update |
| `mcp/` (client, server, scan) | **Connectivity** | **PARTIAL** | MCP client/server + scan (our settings already reference MCP) |
| `skills/` (import, list, scan) | **Agent** | **MISSING** | skills list/import/scan |
| `backup/` (backup_restore, settings, restore, self-update) | **System** | **MISSING** | backup/restore |
| `developer/` (dev, websocket-event-console, websocket-tester) | **System** + B-8 Debug surface | **MISSING** | event console → Debug surface |
| `a2a/` (a2a-connection, a2a-server) | **Connectivity** | **MISSING** | A2A connection + server |
| `tunnel/` (remote-link, tunnel-section, tunnel-store) | **Connectivity** | **MISSING** | tunnel / remote link |
| `file-browser/` (file-browser-settings) | **System** | **MISSING** | files appearance, limits, archives |
| `plugins/` (plugins-subsection) | Capsule Modules page | **PARTIAL** | module list/toggle/config (our Capsule model) |
| `secrets/` (example-secrets, example-vars) | **External** | **PARTIAL** | secrets + vars |

Existing Soma settings that A0 has **no** equivalent for (keep, and treat as our lead): `saas-settings-models.ts`, `saas-settings-channels.ts`, `saas-multimodal-settings.ts`, tenancy, roles, billing, usage, tiers, marketplace, audit.

### 4.4 Modals — 24 → 3 patterns (B-4)

| A0 modal | Soma pattern |
|---|---|
| context, process-step-detail, file-browser, file-tree, rename | **Drawer** |
| full-screen-input, image-viewer, markdown | **Full-screen** |
| scheduler×5, and any destructive confirm | **Dialog** / dedicated route |

Soma today: `saas-glass-modal.ts` (generic shell) + `saas-user-invite-modal.ts` + inline dialogs in `saas-voice-personas.ts`. Keep `saas-glass-modal` as the single Dialog implementation; add Drawer + Full-screen as siblings.

### 4.5 Sidebar (A0: 16 files)

| A0 | Soma | Action |
|---|---|---|
| `left-sidebar.html`, `sidebar-store.js` | left rail in `saas-chat.ts:5` | B-9 adaptive rail component |
| `chats/` (chat-tree, chats-list, chats-store) | searchable list, rename/delete/export | folders/trees, pin-to-top |
| `tasks/` (task-row, task-list, tasks-store) | none | task list surface |
| `bottom/` (preferences-panel, preferences-store, sidebar-bottom) | settings route | quick prefs drawer |
| `top-section/` (header-icons, quick-actions, sidebar-top) | brand + New Chat | quick actions |

### 4.6 Remaining A0 surfaces

| Area | A0 | Soma | Action |
|---|---|---|---|
| Notifications (5) | toast + modal + icons + store | partial toasts | full notification centre |
| Welcome (3) | welcome-screen + store | `saas-onboarding.ts` | keep, add A0-style first-run checklist |
| Sync (3) | sync-status + store | none | sync status indicator |
| Projects (14) | project list/edit/secrets/skills/llm/mcp/instructions/file-structure | `saas-capsule-editor.ts` | map Projects → Capsules; every project-edit subsection needs a Capsule equivalent |
| Plugins (11) | list, execute modal, configs, info, toggles | Capsule Modules | module list, execute, config, toggles |
| `stt-service.js` / `tts-service.js` | raw | `voice-store` + composer mic + `saas-voice-*` views | B-7 state machine |

---

## 5. Feature coverage — 76 A0 features, UI-facing actions

From `SOMA-A0-PARITY-001.md` §4.8 (Chat 15, Models 8, Memory 8, Tools 17, Bridges 9, Voice 4, Platform 15 = 76). The UI lane owns the **user-visible half** of each; backend wiring is the other agent's lane.

| Domain | Total | UI must expose | Highest-priority UI gaps |
|---|---|---|---|
| Chat core | 15 | 15 | branching, time-travel edit, retry, compaction, context budget, message actions |
| Models | 8 | 8 | model setup gate, inline switcher, provider status, per-model caps |
| Memory | 8 | 8 | memory dashboard/knowledge ingest (C7), real counts only |
| Tools | 17 | 17 | **tools manager rail (currently fake)**, approval UX, per-tool schemas |
| Bridges | 9 | 9 | WhatsApp QR/connected from real API, Telegram, Email — channel badges (U-08) |
| Voice | 4 | 4 | B-7 state machine, personas (exists), sessions (exists) |
| Platform | 15 | 15 | capsule modules, backup/restore, tunnel, A2A, skills |

**Rule: no domain may ship at 100% "UI done" while any of its controls is a placeholder.**

---

## 6. Rapid development — waves

Points are story points (1/2/3/5/8). Waves are barriers; work *within* a wave is parallel and owns disjoint files.

### WU-0 · TRIAGE + FOUNDATION (8 pts) — *first*

| ID | Pts | Todo | Owner |
|---|---|---|---|
| WU-0.1 | 2 | **Triage the 15 unattributed dirty webui files** — adopt onto `ui-ux-creation` or preserve. Never overwrite. | UI + user |
| WU-0.2 | 2 | Isolation settled (worktree W1 recommended); `ui-ux-creation` re-pointed to the agreed base | UI |
| WU-0.3 | 2 | Design-token audit + one token set; Drawer / Full-screen / Dialog primitives on `saas-glass-modal` family | UI |
| WU-0.4 | 2 | Typed **Surface registry** (B-6) + shared surface chrome with loading/error/empty states | UI |

**Exit:** three surface patterns render; surface registry accepts a module-registered surface; zero `coming soon` strings remain in code that ships.

### WU-1 · KILL THE PLACEHOLDERS (13 pts) — *highest visible value*

| ID | Pts | Todo |
|---|---|---|
| WU-1.1 | 5 | **Files surface** — tree, path bar, preview, upload/download, rename, search |
| WU-1.2 | 3 | **Tools manager surface** — list, enable/disable, live call log, arg schemas |
| WU-1.3 | 3 | **Editor surface** — open from files, B-2 highlight, dirty state, save |
| WU-1.4 | 2 | **Browser surface** — honest state when no browser worker is attached |

**Exit:** all six rail tabs are real or explicitly disabled with a reason. Playwright: no `coming soon` in DOM.

### WU-2 · CHAT HERO PARITY (13 pts)

| ID | Pts | Todo |
|---|---|---|
| WU-2.1 | 5 | Message action set (§4.1.2) — 12 actions, quiet inline |
| WU-2.2 | 5 | Branching + time-travel edit + retry/regenerate |
| WU-2.3 | 3 | Attachments drag-drop + previews; visible, reorderable message queue |

**Exit:** every A0 chat action is reachable; branching re-runs and renders a real second branch.

### WU-3 · COMMAND PALETTE + NAV (8 pts)

| ID | Pts | Todo |
|---|---|---|
| WU-3.1 | 5 | **Cmd-K palette** (B-1) — fuzzy nav, actions, capsule/model/surface switch, setting jump |
| WU-3.2 | 3 | Adaptive sidebar rail (B-9) + chat navigation + message resize |

**Exit:** every screen and every action reachable from the keyboard alone.

### WU-4 · SETTINGS COMPLETENESS (8 pts)

| ID | Pts | Todo |
|---|---|---|
| WU-4.1 | 3 | Settings search + Advanced collapse + role-gated rows (B-3) |
| WU-4.2 | 5 | Map in the 8 missing A0 categories: skills, backup/restore, developer/Debug, A2A, tunnel, file-browser prefs, MCP scan, self-update |

**Exit:** every A0 settings row exists in our 4 scopes or is deliberately excluded and recorded.

### WU-5 · POLISH + PROOF (8 pts)

| ID | Pts | Todo |
|---|---|---|
| WU-5.1 | 3 | B-2 syntax highlighting + B-10 XSS matrix |
| WU-5.2 | 2 | B-7 mic/TTS state machine, B-8 Debug surface |
| WU-5.3 | 3 | Playwright suite `UI-AT-01…08` + new: no-placeholder DOM, palette, surfaces, a11y AA |

**Exit:** Playwright green; WCAG AA; zero hardcoded metrics (grep `12400`/`getMock` empty in the bundle).

**Total 58 points.** At 3–6 parallel UI slices, ~2–3 weeks of UI work once the gate is signed.

---

## 7. Acceptance (extend `SOMA-A0-PARITY-001.md` §5.7)

| ID | Test |
|---|---|
| UI-AT-01 | zero `placeholder` / `coming soon` strings in the rendered DOM |
| UI-AT-02 | `chat.delta` renders progressively |
| UI-AT-03 | tool timeline shows args + result + duration; approval request actionable |
| UI-AT-04 | model switcher works against real configured models only |
| UI-AT-05 | WhatsApp QR / connected state from the real API |
| UI-AT-06 | Cmd-K routes to every screen and every action |
| UI-AT-07 | no hardcoded metrics — `12400`, `getMock`, `memoryUsage: <non-zero literal>` absent from the bundle |
| UI-AT-08 | WCAG AA contrast + full keyboard operation |
| **UI-AT-09** | **all six rail surfaces render real content or an explicit, reasoned disabled state** |
| **UI-AT-10** | **no control is clickable without a working handler** |
| **UI-AT-11** | **every message action in §4.1.2 is present and wired** |

---

## 8. Decisions needed before code

| # | Decision | Recommendation |
|---|---|---|
| **D-0** | **Sign the Plan Gate** (required by §0) | — |
| **D-1** | **Triage the 15 unattributed dirty webui files** | preserve; adopt onto `ui-ux-creation` after confirming provenance |
| **D-2** | **Isolation: W1 worktree vs W2 shared checkout** | **W1 worktree** |
| **D-3** | **Branch base: their tip `33ef37a1` vs `main`** | their tip — the live UI |
| **D-4** | A0 `desktop` surface: add, or deliberately exclude? | exclude, record as OD |
| **D-5** | Pause: real orchestrator interrupt, or honest "pause rendering" until the gateway supports it? | honest label now, real pause when interrupt lands |

Standing open decisions from `SOMA-A0-PARITY-001.md` §10 that affect UI: **OD-4** (strangler the eye-of-god UI) and **OD-5** (skip Slack/Discord).

---

## 9. What we will not do

- Copy A0's Alpine/HTML/JS, its plugin-webui layout, or its 24-modal pattern.
- Ship a second design system, a second token set, or per-module theming.
- Put a metric, count or status on screen that a real API did not return.
- Enable a control that cannot work — disabled-with-reason is the only honest alternative (`saas-chat-topbar.ts:28` is the reference implementation).
- Commit another agent's files, or check out a branch in a tree someone else is editing.
