# SOMA vs AGENT ZERO — UI Parity Gap Report & Module Roadmap

## Document Control

| Field | Value |
|---|---|
| Document Title | UI Parity Gap Report and Target Module Architecture |
| Document Identifier | SOMA-RPT-UI-PARITY-GAP-001 |
| Version | 1.0.0 |
| Date | 2026-10-12 |
| Status | Draft |
| Author | SomaTech Engineering (front-end architecture lane) |
| Classification | Internal |
| Source of truth | `webui/src/` live tree (2026-10-12); `docs/reports/SOMA-RPT-FEATMATRIX-001.md` §2.3/§3/§5 as benchmark; `docs/design/SOMA-UI-CATALOG-001.md` §4; `docs/design/SOMA-UI-SKINS-001.md`; `docs/iso/SOMA-01-UIUX-001.md` UI-X-01…08 |
| Related | `SOMA-UI-PARITY-002.md` (clone-and-better plan), `SOMA-PM-PLAN-TRIAD-001.md` W4-1…W4-5, `SOMA-RPT-UIUX-AUDIT-001.md` |
| A2A | `webui/` is claimed ACTIVE by MiMoCode-somaAgent01 (`docs/plans/a2a/CLAIMS.md:4`). This report is docs-only analysis; implementers must claim before code. |

---

## 0. Executive summary

**The FEATMATRIX-001 §2.3 UI matrix is stale.** It records the product state at matrix authoring time; the live `webui/` tree (Oct 2026) has closed several of its "MISSING" rows and replaced fake surfaces with honest ones. Counting against live code:

| Verdict | Count | IDs |
|---|---|---|
| EXISTS (parity or better) | 14 | U-01, U-02, U-05, U-06, U-07, U-09, U-10, U-11, U-16, U-17, U-22, U-26, U-28, U-29 |
| PARTIAL / honest-gated | 11 | U-03*, U-04, U-12, U-13, U-14, U-15, U-20, U-21, U-23, U-25, U-27 |
| MISSING | 5 | U-08, U-18, U-19†, U-24, U-30 (+ skins runtime) |

\* U-03 is the one true **CRITICAL** remaining UI gap (no syntax highlighter; `webui/package.json` ships Lit only). † U-19 is present-but-disabled by honest rule, not an omission.

**Headline deltas vs the matrix (all upgrades):** model provider setup (U-17, matrix CRITICAL) is now a real write path; file attachments (U-05), chat export (U-09), chat search (U-10), canvas host (U-11), and image display (U-06) exist. **Headline remaining product risk:** chat output quality (markdown+code highlight), File Manager depth (tree/write/search), browser surface, and the skins runtime that makes the product "skinnable".

---

## 1. A2A coordination status (`docs/plans/a2a/`)

| Claim | Owner | Scope | Status |
|---|---|---|---|
| `webui/` | MiMoCode-somaAgent01 | UI/UX report + plan + later implementation | ACTIVE (`CLAIMS.md:4`) |
| `docs/design/` | MiMoCode-somaAgent01 | UI/UX docs + plan | ACTIVE (`CLAIMS.md:5`) |
| File tools set | MiMoCode-somaAgent01 | filesv2 upload, right-panel Files/Editor honesty, composer attachments | ACTIVE (`CLAIMS.md:48`) |
| `docs/architecture/SOMA-ARCH-SKINS-001.md` | architect-skins | Skinnable UI theme architecture (new doc only) | ACTIVE (`CLAIMS.md:167`) |

LEDGER `2026-10-09T01:20:00Z` locks the file-tools inventory: PathGuard + file_list/search/read/write/patch tools + filesv2 upload/list live. OPEN at that date: workroot→filesv2 bridge, filesv2 tenant bind, editor save, FileBuild, `file_read` line ranges. **Implication: the File Manager module below is partly backend-bound (editor save, workdir listing). UI must keep present-but-disabled honesty on those controls — no shims.**

---

## 2. U-01 … U-30 parity gap report (live evidence)

Severity: **S1** blocks product use · **S2** degrades daily use · **S3** completeness · **S4** polish. Status is measured against live code, not the matrix text.

| ID | AGENT ZERO feature | Matrix said | SOMA status now | Sev | File:line evidence |
|---|---|---|---|---|---|
| U-01 | Chat interface | ✓ (different tech) | **EXISTS** — Lit 3.x chat workspace, 3-pane chrome | — | `webui/src/views/soma-chat.ts:1-10` (left history / stream / composer), routes `webui/src/main.ts:124-128,316-327` |
| U-02 | Message streaming SSE/WS | ✓ | **EXISTS** — WS deltas + streaming flag on bubbles | — | `webui/src/services/websocket-client.ts`; `webui/src/components/soma-message.ts:1195` (`aria-live` while streaming) |
| U-03 | Code syntax highlighting | ✗ MISSING | **MISSING** — no highlighter in bundle; code blocks are escaped text + copy button only | **S1** | `webui/src/utils/markdown.ts:22-24` ("does NOT claim token-level syntax highlighting — no highlighter ships in this bundle"); `webui/package.json` deps: lit only (no shiki/prism/highlight.js) |
| U-04 | Markdown rendering | ✗ basic only | **PARTIAL** — XSS-safe custom renderer: fences, inline code, bold/italic/strike, links, ul/ol, headings, blockquotes, HR. No tables, no nested lists, not CommonMark-complete | **S1** | `webui/src/utils/markdown.ts:4-6,105-190`; rendered via `unsafeHTML` at `webui/src/components/soma-message.ts:17,1195` |
| U-05 | File attachments in chat | ✗ MISSING | **EXISTS** — composer chips → `POST /api/v2/filesv2/upload` (presigned or local); `file_id` only after accepted bytes; failure surfaces on the message | — | `webui/src/components/soma-composer.ts:31,401-404,550-560`; `webui/src/services/file-upload.ts:1-34,18-23`; send path `webui/src/views/soma-chat.ts:2688-2717` |
| U-06 | Image display in chat | ✗ MISSING | **EXISTS** — attachment cards with image detection + `media-frame img`; non-media = download card | — | `webui/src/components/soma-message.ts:27-39,566-570,641` |
| U-07 | Chat history / sidebar | ✓ | **EXISTS** — searchable conversation list with rename/delete/export | — | `webui/src/views/soma-chat.ts:5-7`; `webui/src/components/soma-sidebar.ts` (nav shell) |
| U-08 | Chat branching | ✗ MISSING | **MISSING** — turn controls are pause/resume/nudge/stop/reset only; no branch tree / regenerate-from-turn | **S2** | `webui/src/views/soma-chat.ts:2495-2545` (`chat.pause|resume|nudge|stop|reset`); no branch model in `ChatMessage` `soma-chat.ts:35-49` |
| U-09 | Chat export | ✗ MISSING | **EXISTS** — JSON export (per-conversation + active), honest empty-state | — | `webui/src/views/soma-chat.ts:1919-1952,2577-2605` |
| U-10 | Chat search | ✗ MISSING | **EXISTS** — sidebar search field over conversations | — | `webui/src/views/soma-chat.ts:218-249` (`.search-input`) |
| U-11 | Canvas panel (right side) | ✗ MISSING | **EXISTS** — 8-surface right-rail host (UI-X-01…08), typed registry, honest gates | — | `webui/src/components/soma-right-panel.ts:2-17,32-77`; catalog `docs/design/SOMA-UI-CATALOG-001.md:147-153` |
| U-12 | Browser in canvas | ✗ MISSING | **GATED (honest)** — present-but-disabled with reason; no viewport backend | **S2** | `webui/src/components/soma-right-panel.ts:60-64` (`blockedReason: 'Bind a browser model on UI-S-02 first'`) |
| U-13 | Linux desktop in canvas | ✗ MISSING | **GATED (honest)** per REQ-UIX-007 | S4 | `webui/src/components/soma-right-panel.ts:71-76` (fixed reason "Requires a remote-desktop capability…") |
| U-14 | Document editor in canvas | ✗ MISSING | **PARTIAL** — Editor surface LIVE read-only; Save is present-but-disabled (no filesv2 PUT/content route) | **S2** | `webui/src/components/soma-right-panel.ts:187-192` (save-reason constant); bindings `docs/design/SOMA-UI-BINDINGS-001.md:84` (read buffer, signed download only) |
| U-15 | Code editor in canvas | ✗ MISSING | **PARTIAL** — same Editor surface; no syntax highlighting in editor either (inherits U-03) | **S2** | `webui/src/components/soma-right-panel.ts:66` (UI-X-04), `:594-619` editor chrome |
| U-16 | Settings panel | Agent Zero RICHER | **EXISTS (near parity)** — multi-tab settings + models + SomaBrain + channels + feature flags + secrets status + export | — | `webui/src/views/soma-settings.ts:51-90,1056-1083,1228-1245`; `webui/src/views/soma-settings-models.ts` (1647 lines); dynamic entity forms `webui/src/main.ts:207-221` |
| U-17 | Model provider setup | ✗ no UI, **CRITICAL** | **EXISTS (was matrix CRITICAL — closed)** — providers from live `/llm/providers`; API key write-only to Vault via `PUT /secrets/providers/{id}`; `has_api_key` never echoes material | — | `webui/src/views/soma-settings-models.ts:5-16,33,634-656,702`; route `webui/src/main.ts:139-144,335-343` |
| U-18 | Plugin marketplace / hub | ✗ MISSING | **MISSING** — zero plugin surface in webui | S3 | grep `plugin` across `webui/src` → 0 hits |
| U-19 | Skills management | ✗ MISSING | **PRESENT-BUT-DISABLED (honest)** — composer menu states no `/skills` registry API; local `activeSkills` has no server catalog | S3 | `webui/src/components/soma-composer-menu.ts:153-157`; `webui/src/stores/composer-store.ts:9,20,56-61` |
| U-20 | Secrets management UI | ✗ MISSING | **PARTIAL** — real API-keys admin (server-minted, shown once) + provider key status/write; not arbitrary secret CRUD like A0 `secrets/` | **S2** | `webui/src/views/soma-admin-api-keys.ts:7-13,159-161`; `webui/src/views/soma-settings.ts:638-640,1369-1375,1471-1474` |
| U-21 | MCP server management | ✗ MISSING | **PARTIAL** — MCP client feature flag + honest note "No MCP server registry is exposed by this deployment" | S3 | `webui/src/views/soma-settings.ts:51,88,1056-1083` |
| U-22 | Agent profile editor | ✗ MISSING | **EXISTS** — capsule editor (GET/PATCH `/agents/{id}/capsule`) + persona knobs | — | `webui/src/components/soma-capsule-editor.ts:315,338,363`; `webui/src/views/soma-settings.ts:1023` (`persona_config.knobs`) |
| U-23 | Backup / restore UI | ✗ MISSING | **PARTIAL** — "Backup" section exports config (flags + key-status booleans only); no restore, no archive | S3 | `webui/src/views/soma-settings.ts:1228-1245` (`export-config` → `_exportConfig`) |
| U-24 | Time travel (snapshots) | ✗ MISSING | **MISSING** | S4 | no surface/route in `webui/src/main.ts` |
| U-25 | Notification system | ✓ admin/notifications | **PARTIAL** — per-user notification prefs (agentReplies, activitySummary); no notification center / in-app feed | S3 | `webui/src/views/soma-personal-profile.ts:37,532-547` |
| U-26 | Dark / light theme | ✓ | **EXISTS (polarity only)** — `data-theme` boot + toggle; **skins runtime NOT implemented** (specified in SOMA-UI-SKINS-001); `/themes` renders present-but-disabled with blocking reason | **S2** (skins) | `webui/src/services/theme-boot.ts:6,15-25`; `webui/src/main.ts:371-401`; `webui/src/styles/tokens.css:7` ("Supports theming via AgentSkin" — aspiration, no reader) |
| U-27 | Responsive design | both missing | **PARTIAL** — scattered `@media` in chat components; still desktop-first product | S4 | `@media` present in `soma-composer.ts`, `soma-message.ts`, `soma-chat.ts`, `soma-chat-topbar.ts` |
| U-28 | Login page | ✓ | **EXISTS** — login, register, forgot-password, MFA, OAuth callback; reset/verify honestly disabled (no backend route) | — | `webui/src/main.ts:54-109,301-305`; `webui/src/views/soma-login.ts` |
| U-29 | Welcome / onboarding | ✗ MISSING | **PARTIAL→EXISTS** — welcome dashboard with action cards when chat empty; `/onboarding` and `/invite/*` redirect to `/register` (no wizard) | S3 | `webui/src/components/soma-welcome-dashboard.ts:1-30`; `webui/src/main.ts:277-283` |
| U-30 | What's new / changelog | ✗ MISSING | **MISSING** | S4 | grep `changelog` → 0 hits |

### 2.1 Matrix gaps §3.1–3.3 re-scored against live code

| Matrix gap | Name | Matrix | Live verdict |
|---|---|---|---|
| GAP-C01 | One-command Docker start | CRITICAL | Out of UI scope (infra). Unchanged. |
| GAP-C02 | Model provider setup UI | CRITICAL | **CLOSED** — `soma-settings-models.ts` real write path (see U-17) |
| GAP-C03 | Chat UI markdown + code | CRITICAL | **OPEN** — markdown partial, highlight **MISSING** (U-03/U-04) |
| GAP-C04 | File operations tool | CRITICAL | Backend tools live (LEDGER 2026-10-09); **UI depth open** (tree/workroot/write) |
| GAP-C05 | Git operations tool | CRITICAL | Backend; no UI dependency |
| GAP-C06 | Canvas panel | CRITICAL | **PARTIAL** — host + 6/8 surfaces live; Browser/Desktop gated; Files/Editor thin |
| GAP-C07 | Plugin system | CRITICAL | **OPEN** (P-01…P-05) + U-18 |
| GAP-C08 | Skills system | CRITICAL | **OPEN** (backend) — UI honestly disabled (U-19) |
| GAP-C09 | Projects workspaces | CRITICAL | **OPEN** — no project switcher UI |
| GAP-C10 | Subagent delegation | CRITICAL | Backend |
| GAP-H01 | File attachments | HIGH | **CLOSED** (U-05) |
| GAP-H02 | Secrets management UI | HIGH | **PARTIAL** (U-20) |
| GAP-H03 | Agent profile editor | HIGH | **CLOSED** (U-22) |
| GAP-H04 | Backup / restore UI | HIGH | **PARTIAL** (U-23) |
| GAP-H05 | Chat branching | HIGH | **OPEN** (U-08) |
| GAP-H06/H07 | Doc/code editor in canvas | HIGH | **PARTIAL** (U-14/U-15, save backend-bound) |
| GAP-H08 | Browser automation in canvas | HIGH | **GATED** (U-12) |
| GAP-H09 | Prompt templates UI | HIGH | Not in U-01..30; no composable template UI |
| GAP-H10 | Extension hooks UI | HIGH | Depends on P-05 |
| GAP-M01/M02 | Chat export / search | MEDIUM | **CLOSED** (U-09/U-10) |
| GAP-M04 | Onboarding wizard | MEDIUM | **PARTIAL** (U-29) |
| GAP-M05/M06/M07/M08 | Time travel / desktop / notify tool / parallel tools | MEDIUM | Open / GATED / open / open |

---

## 3. Target UI module architecture (skinnable agent)

Design law: **feature clone, never code clone** (PARITY-002 §0); **one token vocabulary** (`--platform-*` today, skin documents tomorrow per SOMA-UI-SKINS-001); every module is a Lit 3.x package with a stable public element set, lazy-loaded by the shell, and restylable through CSS custom properties only (no appearance in logic).

```
soma-shell (core)                     swappable Lit modules
┌─────────────────────────────────────────────────────────────────┐
│  app-frame  route-registry  auth-gate  skin-applier  toast/notify │
│  surface-registry (UI-X-*)  command-palette  theme-boot          │
└──────────┬──────────────────┬──────────────────┬────────────────┘
           │                  │                  │
     chat-module        workspace-module     admin-module
     ┌───────────┐      ┌────────────────┐   ┌──────────────────┐
     │ chat-view │      │ canvas-host    │   │ settings-shell   │
     │ composer  │      │ file-manager   │   │ model-providers  │
     │ message   │      │ editor         │   │ secrets/api-keys │
     │ tool-timeline│   │ browser-surface│   │ roles/audit/infra│
     │ history-rail│     │ desktop-surface│  │ users/entities   │
     │ export/search│    │ debug/capsule/ │   │ backup-export    │
     └───────────┘      │ brain surfaces │   └──────────────────┘
                        └────────────────┘
     identity-module          domain-module (optional)
     ┌───────────┐            ┌─────────────────────────┐
     │ login/reg │            │ memory-view  cognitive  │
     │ mfa/oidc  │            │ voice-*      profiles   │
     │ profile   │            │ integrations            │
     └───────────┘            └─────────────────────────┘
```

### 3.1 Module boundaries (each swappable)

| Module | Responsibility | Public elements (today → target) | Swap test |
|---|---|---|---|
| **core-shell** | Routing (`main.ts`), auth gate, skin application, surface registry, global chrome | `soma-sidebar`, `soma-agent-header`, `soma-chat-topbar`, `soma-glass-modal`, `soma-button/toggle/select/status-*` | Replace sidebar nav without touching chat |
| **chat** | Conversation UX: stream, composer, attachments, tool timeline, history, export | `soma-chat`, `soma-message`, `soma-composer`, `soma-composer-menu`, `soma-tool-timeline`, `soma-welcome-dashboard` | Replace message renderer (markdown engine) without touching composer |
| **workspace** | Right-rail canvas + file manager + editors | `soma-right-panel` (host) → target split: `soma-canvas-host`, `soma-file-manager`, `soma-code-editor`, `soma-doc-editor`, `soma-browser-surface`, `soma-desktop-surface` | Swap file-manager backend (filesv2 vs workroot) behind one panel API |
| **admin** | Settings, providers, secrets, roles, audit, infra, entities | `soma-settings`, `soma-settings-models`, `settings-form`, `entity-manager`, `soma-admin-api-keys`, `soma-data-table`, infra charts/cards | Replace settings-form entity catalog without touching model-provider view |
| **identity** | Auth surfaces + user profile | `soma-login`, `soma-register`, `soma-forgot-password`, `soma-mfa-setup`, `soma-auth-callback`, `soma-personal-profile` | Swap Keycloak OIDC vs standalone email/password (two-mode §5) |
| **domain** (feature-flagged) | Memory, cognitive, voice, integrations | `soma-memory-view`, `soma-cognitive-panel`, `voice-*` | Disable module entirely in Standalone slim build |

### 3.2 Skin / theme hooks (required for "skinnable")

Per SOMA-UI-SKINS-001, appearance must become Capsule data. Module contract:

1. **Token floor** — modules read ONLY `var(--skin-*, var(--platform-*))`. Today 1575 hardcoded colour literals vs 468 token reads (SKINS-001 §1.2); the module rebuild must drive that ratio to ~0 literals in new code.
2. **Skin applier in shell** — `core-shell` resolves Capsule → AgentSetting → Django → default (SKINS-001 four-source chain) and writes the resolved skin onto `documentElement` (`--skin-accent`, `--skin-radius`, `--skin-font-ui`, `--skin-font-mono`, `--skin-surface`, `--skin-density`, `--skin-motion`), overlaying `tokens.css`.
3. **Polarity stays orthogonal** — `theme-boot.ts` light/dark remains a boolean inside a skin (already honest at `main.ts:371-401`).
4. **Isolation** — each module's `static styles` consume the hooks only; no module reads another module's DOM for appearance.
5. **No fake skins UI** — until the skins store/API is real, `/themes` stays present-but-disabled with the blocking reason already shipped (`main.ts:388-392`).

### 3.3 Two-mode architecture mapping (FEATMATRIX §5)

| Concern | Standalone mode module build | Enterprise mode module build |
|---|---|---|
| identity | email/password + local session (thin `identity-module`) | OIDC/MFA/impersonation (full `identity-module`) |
| admin | settings + providers + files only | + tenants, roles, audit, metering, infra |
| domain | SomaBrain/SFM embedded panels optional | memory + cognitive + voice required |
| shell | single-agent chrome, no tenant switcher | tenant switcher in `soma-agent-header` |
| Shared | chat, workspace, core-shell, model-providers, tokens/skins — **same modules both modes** (matrix §5 "Shared Core") |

---

## 4. Prioritized module roadmap (max product impact)

Ordering rule: matrix CRITICAL/HIGH first, backend-ready first, user-visible chat quality before admin completeness. Effort figures from FEATMATRIX §3 where available.

### P0 — ship next (product feels like an agent)

| # | Build | Closes | Sev | Why first | Depends on |
|---|---|---|---|---|---|
| P0-1 | **Markdown + code rendering upgrade** — real highlighter (shiki or highlight.js, tokenized, XSS-safe) + tables + nested lists; same engine for chat bubbles and Editor surface | GAP-C03, U-03, U-04, U-15 half | S1 | Every assistant message is a code/mardown surface; matrix CRITICAL, ~1 week | none |
| P0-2 | **File Manager module** (`soma-file-manager`) — tree, upload, search, open→Editor, download; wire workroot↔filesv2 bridge when API lands; Save stays present-but-disabled until PUT exists | GAP-C04/C06 UI side, U-11 depth, U-14 | S1 | Matrix calls file ops + canvas CRITICAL; LEDGER shows backend tools already live | P0-1 (editor render) |
| P0-3 | **Model provider setup polish** — already real; add per-project presets (M-05), slot binding copy (browser model for U-12), key-rotate affordance | U-17 residual, GAP-C02 residual | S2 | CRITICAL row is closed — protect the win and unblock U-12 | none |

### P1 — product completeness (HIGH matrix rows)

| # | Build | Closes | Sev | Notes |
|---|---|---|---|---|
| P1-1 | **Canvas browser surface** — real viewport or keep GATED; only ungate when a browser model role + backend exist | GAP-H08, U-12 | S2 | Never a fake iframe |
| P1-2 | **Editor write path** — enable Save when filesv2 PUT/content route lands; dirty state + conflict copy | GAP-H06/H07, U-14/U-15 | S2 | Backend-bound (LEDGER open item) |
| P1-3 | **Secrets management depth** — arbitrary secret rows (read-masked), scope (global/project) | GAP-H02, U-20 | S2 | Keep Vault write-only discipline from U-17 |
| P1-4 | **Chat branching + regenerate-from-turn** | GAP-H05, U-08 | S2 | Needs conversation graph in chat API |
| P1-5 | **Skins runtime MVP** — skin document → `--skin-*` on `:root`, Capsule-owned; retire hardcoded literals in touched modules | U-26 residual, skinnable product | S2 | Spec already exists (SOMA-UI-SKINS-001); A2A claim open on ARCH-SKINS-001 |
| P1-6 | **Prompt template / persona library UI** (capsule-owned, composable) | GAP-H09, C-07 "needs UI" | S2 | Pairs with U-22 capsule editor |

### P2 — platform depth (MEDIUM rows + enterprise)

| # | Build | Closes |
|---|---|---|
| P2-1 | Skills registry UI (ungate composer menu when `/skills` API exists) | U-19, GAP-C08 |
| P2-2 | MCP server registry UI (replace honest "no registry" note when API exists) | U-21 |
| P2-3 | Backup **and restore** (today export-only) | GAP-H04, U-23 |
| P2-4 | Notification center / in-app feed (beyond prefs) | U-25, T-08 |
| P2-5 | Project/workspace switcher UI (per-project instructions, secrets, presets) | GAP-C09, M-01…M-05 |
| P2-6 | Onboarding wizard (multi-step, beyond `/register`) | GAP-M04, U-29 |
| P2-7 | Plugin marketplace shell (needs P-01 plugin system) | U-18, GAP-C07 |

### P3 — polish

Time travel snapshots (U-24) · What's new / changelog (U-30) · Responsive/mobile pass (U-27) · Desktop surface stays GATED until remote-desktop exists (U-13 / REQ-UIX-007).

### W4 mapping (TRIAD Wave 4)

| W4 | Plan item | Covered by |
|---|---|---|
| W4-1 | Screen parity matrix | this report §2 |
| W4-2 | Chat history/branches/regen/stop/tool-cards/attachments | U-07/U-08/U-05 EXISTS except **branching (P1-4)**; stop/tool-cards/attachments shipped |
| W4-3 | Settings real (models/provider/API-key, persona, memory toggles) | **mostly shipped** (U-17/U-22); memory toggles residual in domain module |
| W4-4 | Right panel placeholders | **done** — registry with honest gates (`soma-right-panel.ts:2-7`); depth work is P0-2/P1-2 |
| W4-5 | Login/logout real | **shipped** (`main.ts:285-298` real `apiClient.logout()` + cookie clear) |

---

## 5. Severity rollup

| Sev | Open items |
|---|---|
| **S1** | U-03 syntax highlighting; U-04 markdown completeness; File Manager depth (P0-2) |
| **S2** | U-08 branching; U-12 browser surface; U-14/U-15 editor write+highlight; U-20 secrets depth; U-26 skins runtime; P0-3 provider presets |
| **S3** | U-18 plugins; U-19 skills (honest-disabled); U-21 MCP registry; U-23 backup/restore; U-25 notification center; U-29 wizard |
| **S4** | U-13 desktop (correctly gated); U-24 time travel; U-27 responsive; U-30 changelog |

---

## 6. Acceptance for this report

- [x] FEATMATRIX-001 §2.3, §3.1–3.3, §5 read in full
- [x] `webui/` components/, views/, `main.ts` routes inventoried against the matrix
- [x] U-01…U-30 each marked exists/partial/missing with file:line evidence (honest gates counted as correct, not as "exists")
- [x] Target module architecture defined: core shell / chat / workspace / admin / identity / domain, each a swappable Lit module with skin hooks
- [x] Build order prioritized by matrix criticality + live gaps (P0→P3)
- [x] `docs/plans/a2a/` checked; claims respected; no code edited
- [x] No shims, fakes, mocks, or placeholder product surfaces introduced or recommended

End of Document
