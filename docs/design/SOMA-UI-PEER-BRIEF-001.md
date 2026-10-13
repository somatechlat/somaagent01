# SOMA-UI-PEER-BRIEF-001 — Peer seat UI/UX implementation brief

## Document Control

| Field | Value |
|---|---|
| Document Title | Agent Soma — peer UI/UX implementation brief (seat B) |
| Document Identifier | SOMA-UI-PEER-BRIEF-001 |
| Version | 1.0.0 |
| Date | 2026-10-13 |
| Status | Draft |
| Classification | Internal |
| Author | soma-ui-engineer (seat A) |
| Approver | — |
| ISO Reference | ISO 9241-210:2019 · ISO 9001:2015 clause 7.5 |
| Next Review | 2027-01-13 |
| Audience | UI-peer-seat-B (component/view implementation) and any agent acting on `webui/` |
| Source of truth | `.mimocode/plans/1791848460320-quick-engine.md` (operator master plan) · `SOMA-UI-MODULE-CATALOG-001.md` · `SOMA-UI-CONTROL-MAPS-001.md` + `control-maps/CM-*` · `SOMA-UI-IA-001.md` · `SOMA-UI-BINDINGS-001.md` · `SOMA-UI-NAV-001.md` · `SOMA-UI-AGENT-FRONTEND-MASTER-001.md` |
| Related | `docs/plans/a2a/CLAIMS.md` · `OUTBOX.md` · `SOMA-UI-SKINS-001.md` · `SOMA-ARCH-SKINS-001.md` · `SOMA-STD-TRIAD-001.md` |
| Stack law | Lit 3.x only · Django Ninja · no React/Alpine · no shims/fakes/mocks/stubs · real REST/WS only |
| Honesty law | LIVE / PLANNED / GATED only. GATED = present-but-disabled + blocking reason. Never "coming soon". Never silent empty. |

## Revision History

| Version | Date | Author | Description |
|---|---|---|---|
| 1.0.0 | 2026-10-13 | soma-ui-engineer | Initial peer brief. Ownership split, naming law, contracts for shell / toast+tray+bell / Profile+password / Agent package export-import + Hands tools install / File Manager / Chat settings (CoT), collision inventory, build order. |

---

## 0. Purpose

This brief is the **implementation contract** for seat B (peer session). Seat A owns skin-sdk, token vocabulary, and design/control-map docs. Seat B implements modules to the contracts below. Both seats are merge-additive; neither reverts the other.

**Operator master plan:** `.mimocode/plans/1791848460320-quick-engine.md`.  
**If this brief and the master plan disagree, the master plan wins on product intent; MODULE-CATALOG + CM-* win on control-level API shapes; live code wins on what already exists (code is truth).**

---

## 1. Ownership split (A2A)

| Seat | Owns | Forbidden |
|---|---|---|
| **A — soma-ui-engineer** | `webui/src/skin-sdk/**` · `webui/src/styles/tokens.css` · `webui/src/styles/skin-aliases.css` · `webui/src/services/skin-applier.ts` · `webui/src/services/skin-boot.ts` · `docs/design/**` (incl. `control-maps/`) | component/view implementation |
| **B — UI-peer-seat-B** | `webui/src/components/**` · `webui/src/views/**` **implementation** of MODULE-CATALOG L0–L4 + CM-* PLANNED rows | `skin-sdk/**`, `tokens.css`, `skin-aliases.css`, skin-applier, skin-boot |
| **Both (merge-additive)** | `webui/src/main.ts` routes · `webui/src/components/index.ts` · `webui/src/views/index.ts` · `docs/plans/a2a/*` (append-only) | never revert peer edits; never rewrite A2A history |

**Claim before large edit** (`docs/plans/a2a/CLAIMS.md`). Shared files = append/merge only.

### 1.1 Existing ACTIVE claims (do not revert)

| Claimant | Paths | Note |
|---|---|---|
| `MiMoCode-soma-chat-uiux` | `soma-chat.ts`, `soma-message.ts`, `soma-tool-timeline.ts`, `soma-composer.ts` | Chat reliability + bubble/cards polish |
| `MiMoCode-wave6-webui-roles` | `soma-settings-models.ts`, `soma-admin-api-keys.ts`, `soma-chat.ts`, `soma-personal-profile.ts`, `soma-right-panel.ts`, `soma-login.ts`, `soma-register.ts`, `soma-forgot-password.ts` | Model Roles UX + URL hard-delete |
| `MiMoCode-AgentSkin-SDK` / seat A | `skin-sdk/**`, `skin-applier.ts`, `skin-boot.ts`, `tokens.css` | Skin vocabulary + applier |
| `MiMoCode-UI-orchestrator` | `webui/src/styles/`, `webui/src/skin-sdk/` (L0 tokens+glass freeze) | **Overlaps seat A** — tokens/schema authority stays seat A; orchestrator freeze is welcome as a gate, not a second vocabulary |
| `MiMoCode-UI-notify` | `soma-toast-stack.ts`, `soma-notification-tray.ts`, `soma-notification-bell.ts`, `soma-notification-center.ts` | §5 implementation lane |
| `MiMoCode-UI-profile` | `soma-profile.ts`, `soma-password-modal.ts`, `soma-personal-profile.ts` | §6 implementation lane |
| `MiMoCode-UI-hands` | `soma-agent-package.ts`, `soma-agent-hands.ts`, `soma-agent-export-modal.ts` | §7 implementation lane |
| `MiMoCode-UI-files` | `soma-file-manager.ts`, `soma-artifacts.ts`, `file-manager/*` | §8 implementation lane |
| `MiMoCode-UI-brain` | `soma-somabrain-manager.ts`, `soma-settings-somabrain.ts` | Brain manager lane (label law: "Brain") |
| `MiMoCode-UI-chatprefs` | `soma-chat-settings.ts`, `soma-reasoning-block.ts` | §9 CoT lane |
| `MiMoCode-UI-docs` | `docs/design/_superseded/`, `SOMA-UI-MASTER-001.md` | doc cleanup; do not fight seat A on control-maps |

Coordinate in A2A before editing a path another seat holds. Prefer **new files** over editing hot shared files. The UI-* lanes above **are** seat B work split by feature — this brief is their shared contract.

---

## 2. NAMING LAW (operator — absolute)

| Layer | Language |
|---|---|
| **UI labels (user-facing chrome)** | **Agent · Hands · Brain · Memory · Soul · Body · Rules · Tools · Settings** — **never show "Capsule" to users** |
| **Domain / code / APIs** | `Capsule`, `capsule_id`, `persona_config` (technical identifiers stay) |
| **Export/Import** | Product name **"Agent package"** (`.soma-agent` file); internally = Capsule document |

### 2.1 Concrete renames in chrome

| Old (wrong in UI) | New (product) | Where |
|---|---|---|
| Capsule tab / surface | **Agent** | canvas tab `UI-X-06`, workspace title |
| Capsule editor tabs | **Profile · Brain · Hands · Memory · Body · Rules** | agent workspace (was Soul/Brain/Hands/Memory/Body/Governance — use product set above unless mockup annex says otherwise) |
| Capsule export | **Export agent package** | modal title, buttons |
| Capsule import | **Import agent package** | modal title, buttons |
| SomaBrain settings tab label | **Brain** (tooltip "cognition & modulators") | Settings shell |
| "Save capsule" | **Save agent** | editor primary action |

**Allowed:** "Capsule" in code comments, Python models, API field names, docs that describe domain objects.  
**Forbidden:** "Capsule" in any user-visible label, button, tab, toast, empty-state, or aria-label of product chrome.

---

## 3. HARD LAWS (both seats)

1. **NO SHIMS · NO FAKES · NO MOCKS · NO STUBS · NO PLACEHOLDERS · NO TODO PASSES.** Real code only.
2. **Lit 3.x** only. `@customElement('soma-*')`. No React/Alpine.
3. **Theming:** `var(--skin-*)` + alias map only. **ZERO hardcoded hex / px magic / host strings** in components (tokens/constants only). Fail lint on `#` / literal URLs under `webui/src` except `skin-sdk/` templates + `tokens.css`.
4. **Modular:** one file per `soma-*` module · props · slots · events · states · skin surface · permission. No god-files.
5. **Honesty:** LIVE / PLANNED / GATED. GATED = visible + blocking reason. Empty ≠ error (`_loadFailed` pattern). Failure → visible error, never silent empty.
6. **Homes (IA-001):** Memory once at `/memory` · Models full-screen inside Settings · left rail = Memory + Settings only (plus search / new chat / chat list / profile) · no Memory/Settings/Models hero cards on welcome · composer = hero · thin top strip.
7. **Every control has a real handler** or honest disabled state. No dead CTA.
8. **Secrets:** presence only ("key in Vault ✓"). Never redisplay values.
9. **Done:** live Playwright on real services — not skip-gated, not mocked.

---

## 4. Contract — Shell (L1)

**Modules:** `soma-app-shell` (M-018) · `soma-topbar` (M-019) · `soma-sidebar` (M-020 refactor)  
**Authority:** MODULE-CATALOG L1 · IA-001 §2 · CM-01 chrome · plan §E.2

### 4.1 Shell

| Item | Contract |
|---|---|
| Tag | `soma-app-shell` |
| Props | `sessionReady` · `route` · `rightRailOpen` · `sidebarCollapsed` · `skinId?` (sets `--skin-*` on `:host`) |
| Slots | `top` · `rail` · `main` · `right` · `overlays` (toasts, palette, drawers) |
| Events | `soma-shell-toggle-rail` · `soma-shell-toggle-sidebar` · `soma-shell-navigate` `{ path }` |
| States | booting · ready · session-missing → `/login` · offline (WS down banner) |
| Skin surface | `chrome` + `--skin-sidebar-width`, `--skin-header-height` |

### 4.2 Topbar (thin strip)

| Item | Contract |
|---|---|
| Tag | `soma-topbar` |
| Content | brand · ambient status (Brain ◉ · Sync ○ · Memory ◌ — 12px, never banner) · **bell + unread badge** · project chip · profile |
| Props | `brainState?` · `syncState?` · `memoryState?` · `notificationsUnread` · `projectLabel?` · `user?` |
| Events | `soma-open-notifications` · `soma-open-profile` · `soma-open-command-palette` · `soma-status-click` `{ kind: 'brain'\|'sync'\|'memory' }` |
| Law | Memory status click → `/memory` only. Brain status click → Brain surface (UI-X-07), never a second panel. Unknown status = hidden, not fake. |

### 4.3 Sidebar

| Profile | Contents |
|---|---|
| `chat` | Search · New chat · chat list (rename/export/delete) · **Memory** → `/memory` · **Settings** → `/settings` · user + logout |
| `admin` | `ADMIN_NAV` sections |

**Refactor debt:** strip Models / Channels / Brain from chat rail (IA law).  
**States:** loading list · empty · error (`_loadFailed`) · grouped by day.

### 4.4 Routes (merge-additive into `main.ts`)

Keep existing routes (NAV-001). Add only when the view ships: `/notifications`, `/files` (if File Manager gets a route — else canvas-only is fine). No invented routes.

---

## 5. Contract — Toast + tray + bell (notifications)

**Modules:** `soma-toast` / `soma-toast-host` (M-008) · `soma-notification-center` (M-022) · tray popover  
**Authority:** MODULE-CATALOG M-008/M-022 · plan §D · CM-10 AD-30 · SPEC-001 Toast row

### 5.1 Toast stack

| Item | Contract |
|---|---|
| API | `toast.success(msg, opts)` · `toast.error` · `toast.warn` · `toast.info` — `opts: { timeout, actionLabel, actionEvent, id }` |
| Events | `soma-toast-action` `{ id, actionLabel }` · `soma-toast-dismiss` `{ id }` |
| Placement | bottom-right stack · max 3 visible + counter |
| Dismiss | success/info auto-dismiss (2–5s) · **errors sticky** until dismissed |
| Types | success · error (sticky) · info · job-progress · HITL request (sticky + Approve/Deny) |
| Skin | `--skin-color-bg-card`, semantic colours, `--skin-z-toast`, `--skin-shadow-md`, `--skin-radius-md` |

**Behavior table (plan §D.2):**

| Event | Toast | Tray | Sound |
|---|---|---|---|
| Tool HITL | sticky + [Approve][Deny] | unread | optional |
| Job done | success + [Open] | unread | optional |
| Job failed | error sticky + [Retry] | unread | on |
| Skin applied | success 3s | — | off |
| Memory degraded | warning sticky | unread | off |
| Save settings | success 2s | — | off |
| Permission denied | error 5s | — | off |

### 5.2 Bell + tray

| ID | Control | Binding | Status |
|---|---|---|---|
| NT-10 | Bell + badge | unread count WS/API | PLANNED |
| NT-11 | Tray panel (popover) | `GET /notifications` | PLANNED |
| NT-12 | Filter tabs (All/Mentions/Jobs/System) | client filter | PLANNED |
| NT-13 | Row read | `POST /notifications/{id}/read` | PLANNED |
| NT-14 | Open row | navigate job/chat | PLANNED |
| NT-15 | Mark all read | API | PLANNED |
| NT-16 | Clear read | API | PLANNED |
| NT-17 | Settings ⚙ | Profile → Notifications | PLANNED |
| NT-18 | Empty | "You're all caught up" | PLANNED |
| NT-19 | Error + retry | honest | PLANNED |

**Live API (plan):** `admin/notifications/api/notifications.py` (list/create/read/clear).  
**Honesty:** if the endpoint is absent on the deployment → bell present-but-disabled with reason (`Notifications API is not available.`). **Never** render "0 notifications" as if the API returned empty.

**Optional full center:** `/notifications` table (time · type · title · body · Open/Dismiss · pagination). Linked from tray footer. Route only when the view ships.

**WS:** `notification.event` frame → toast + badge++ · poll `GET /notifications` as fallback. If WS frame type is not live yet, poll-only is honest; do not invent a frame.

### 5.3 Upload tray (File Manager sub-module)

`soma-file-upload-tray` — `items: UploadItem[]` · events `soma-cancel`, `soma-retry`, `soma-clear`.  
Per-file progress · Cancel · Retry (failed only) · Clear. Bound to `file-upload.ts` progress events. See §8.

---

## 6. Contract — Profile + password

**Modules:** deepen `soma-personal-profile.ts` (EXISTS) · change-password modal (UI-M-01)  
**Authority:** CM-11 · plan §C · UI-S-34 · BINDINGS profile rows

### 6.1 Profile screens

| Section | Controls | Binding |
|---|---|---|
| Account | display name · email (read-only, IdP-owned) · phone · tenant (read-only) | `GET/PUT /platform/admin/profile`, `PUT /platform/admin/preferences`, `GET /auth/me` |
| Security | last changed · **Change password** · MFA link · sessions count | CM-11 SC-* |
| Notifications | prefs toggles (agent replies, tool approvals, long jobs) | `PUT /platform/admin/preferences` |
| Sessions | active session list + revoke (PLANNED where API absent) | CM-11 SS-* |

### 6.2 Change-password modal (PR-07…PR-13)

| ID | Control | Notes |
|---|---|---|
| PR-07 | Change password button | opens modal |
| PR-08 | Current password | write-only |
| PR-09 | New password + strength meter | policy min 14 chars (platform rule) |
| PR-10 | Confirm password | mismatch state |
| PR-11 | Update password | `POST /auth/change-password` (or live auth route — **bind to the real route in `admin/auth/api.py`; if absent, GATED with reason, do not invent**) |
| PR-12 | Revoke other sessions (toggle) | optional offer on success |
| PR-13 | Post-success toast | `Password changed.` |

**Honesty:**
- `Last changed` renders `unknown` when `last_password_change` is unbound; `never` only when field is present and null (CM-11 §notes).
- Load failure → `Failed to load profile` (PG-06). Save failure → visible error + toast. Never silent empty form.
- Email permanently read-only — do not offer a fake edit.

**Collision note:** `soma-personal-profile.ts` is under `MiMoCode-wave6-webui-roles` ACTIVE claim. Coordinate; prefer additive modal file (`soma-change-password.ts`) over rewriting the profile view.

---

## 7. Contract — Agent package export/import + Hands tools install

**Authority:** plan §F + §B · SRS-CAPSULEPORT-001 (domain) · CM-05 ST-39 · MODULE-CATALOG M-025/M-046 family

### 7.1 Naming

- UI: **"Agent package"** · file extension **`.soma-agent`** (JSON zip).
- Internally: Capsule document. Code may say `capsule_export`.
- Canvas tab label: **Agent** (was Capsule). Workspace title: `Agent · Default`.

### 7.2 Export modal (PK-*)

```
MODAL Export agent package
│ Agent: Default Agent · v1.0.0
│ Include: [✓ Tools+policy] [✓ Memory config] [✓ Brain models] [✓ Persona]
│          [✓ Skins] [✓ Integrations keys → NO (secrets never)] [ ] Chat history
│ Format: .soma-agent (JSON zip)   [Export] [Cancel]
```

| ID | Label | Type | Binding | Status |
|---|---|---|---|---|
| PK-01 | Export package | button | `GET /agents/{id}/export` **(NEW API — required)** | PLANNED |
| PK-02 | Include checkboxes | checkbox ×7 | export options | PLANNED |
| PK-03 | Import package | button/file | `POST /agents/import` **(NEW API — required)** | PLANNED |
| PK-04 | Conflict strategy | select Skip \| Overwrite \| Rename | import | PLANNED |
| PK-05 | Secrets note | text | honesty: keys NOT in file | PLANNED |
| PK-06 | Preview manifest | panel | name · version · tools n · memory · models n | PLANNED |

**Rules:**
- Secrets never in the package. Show PK-05 always on import preview.
- Until export/import HTTP routes exist: controls **GATED** with reason `Agent package export API is not available.` (never a fake download of empty JSON).
- Live API truth: if `admin/agents` or capsule export service already exposes a route, bind to **that** path (code is truth). Do not invent `/agents/{id}/export` if a different live path exists.

### 7.3 Hands tools install (TH-*)

**Operator law:** the agent package owns tools. Install/enable/policy live **on the agent package**, not as loose global switches only.

```
Agent · Default · Hands
[Profile][Brain][Hands][Memory][Body][Rules]     v1.0.0  [Save agent]

INSTALLED ON THIS AGENT
name            tier  policy        scope    status      actions
timestamp       1     auto          kit      ● on        [policy][remove]
packages_ensure 3     approval      venv     ○ off       [Enable]
browser_use     2–3   approval      net      ⚠ gated     reason: no model

AVAILABLE CATALOG (not installed)
git_status     1   [Install]   notify_user    1   [Install]
```

| ID | Label | Binding | Status |
|---|---|---|---|
| TH-02 | Filter tools | local | PLANNED |
| TH-03 | Install from catalog | `POST /tools/install` → capsule M2M **(NEW API — required)** | PLANNED |
| TH-05 | Policy select auto/approval/deny | `PATCH /agents/{id}/capsule` `tool_policy` | PLANNED |
| TH-07 | Enable/Disable | capabilities M2M | PLANNED |
| TH-08 | Remove tool | M2M remove | PLANNED |
| TH-09 | Install catalog item | install + link | PLANNED |
| TH-10 | Save policy | capsule PATCH | PLANNED |
| TH-11 | Locked kit badge | memory kit non-disableable | GATED reason |
| TH-12 | Gated tool reason | e.g. browser no model | GATED |
| TH-13 | Save agent | `PATCH /agents/{id}/capsule` | LIVE (existing capsule editor) |

**Install definition (plan §B.5):** (1) definition in catalog · (2) link Capability to agent package · (3) policy row. Never a fake store.

**Fail-closed:** unknown tool → deny · tier 3 → `approval_required` default.

**Permissions (B.6):** sysadmin/org_admin full · agent_owner own package only · trainer/member read-none. Use `soma-permission-guard` + reason on every disabled Install/Policy.

**Settings › Tools** stays the **platform catalog** (install pool). Hands = per-agent install/enable/policy. Do not duplicate Memory homes.

**UI-S-03 / UI-X-06 note:** canvas surface currently labeled Capsule → relabel **Agent**. Keep `soma-capsule-editor.ts` as the technical module name if renaming would break imports; change **labels** first (naming law is about chrome).

---

## 8. Contract — File Manager (M-024)

**Authority:** MODULE-CATALOG M-024 · CM-02 · FRONTEND-MASTER §3.1 · plan T7

| Item | Contract |
|---|---|
| Tag | `soma-file-manager` + sub-tags `soma-file-breadcrumb` · `soma-file-tree` · `soma-file-list` · `soma-file-preview` · `soma-file-upload-tray` · `soma-file-toolbar` |
| Modes | `browse` · `select` (composer) · `manage` |
| Props | `rootId?` · `path` · `selection` · `mode` · `showPreview` · `showUpload` · `showToolbar` · `pageSize?` · `accept?` · `maxUploadBytes?` |
| Events | `soma-path-change` · `soma-file-open` · `soma-file-select` · `soma-file-download` · `soma-upload-start/progress/complete/error` · `soma-file-delete` · `soma-file-rename` · `soma-refresh` |
| States | loading · empty · error+retry · uploading · partial (list ok, tree failed → banner) |
| Skin | `right_panel` surface |

**Bindings (no mocks):**

| Part | API | Honesty |
|---|---|---|
| List | `GET /api/v2/filesv2/` | LIVE today |
| Upload | `POST /api/v2/filesv2/upload` → presigned PUT or `/upload-local/{id}` | LIVE (`file-upload.ts`) |
| Download | signed URL `GET /filesv2/{id}/download-url` | LIVE S3-only — local fallback → honest "Preview unavailable" |
| Tree | `GET /api/v2/workroot/tree` **(NEW API)** | absent → **hide tree, show reason** (never fake tree) |
| Write/Save | `PUT /api/v2/filesv2/{id}/content` **(NEW API)** | absent → editor Save **present-but-disabled** with reason |
| Delete/Rename | only if live routes exist | else GATED with reason |

**Preview policy:** text/code → readonly editor · image → authorized URL · pdf → iframe · markdown → doc viewer · binary → metadata + Download only.

**Reuse:** canvas UI-X-01 · composer insert-file · settings backups. **One** File Manager module — no second file tree.

---

## 9. Contract — Chat settings (CoT)

**Module:** `soma-chat-settings` (new) · prefs store  
**Authority:** plan §0.7 CS-* · T4 · MODULE-CATALOG chat family

### 9.1 Modal structure

```
Chat settings
VISUAL: density · bubble style · font size · timestamps · avatars · confidence · model chip
CHAIN OF THOUGHT: Show reasoning (Off|Collapsed|Expanded) · Reasoning style (Steps|Prose|Raw)
                  Max reasoning lines · Show token usage · Show latency
TOOLS ON CHAT: icon strip checkboxes · Show tool args · Highlight failures · Auto-expand HITL
STREAM / SEND: Stream tokens · Enter sends · Sound on done · Notify on long job
[Cancel] [Save & apply] [↺ reset]
```

### 9.2 Controls (CS-*)

| ID | Label | Effect | Status |
|---|---|---|---|
| CS-01 | Message density | row height | PLANNED |
| CS-02 | Bubble style | bubble CSS class | PLANNED |
| CS-03 | Font size | `--skin-text-base` override on chat host | PLANNED |
| CS-04…05 | Timestamps / avatars | meta row / avatar slot | PLANNED |
| CS-06…07 | Confidence / model chip | chips | LIVE (chips) / prefs PLANNED |
| **CS-08** | **Show reasoning** Off/Collapsed/Expanded | **chain-of-thought block on message** | PLANNED |
| CS-09 | Reasoning style Steps/Prose/Raw | CoT render | PLANNED |
| CS-10 | Max reasoning lines | clamp block | PLANNED |
| CS-11…12 | Token usage / latency | turn_meta chips | LIVE data / prefs PLANNED |
| CS-13…20 | Tool icon strip | which tools appear as icons | PLANNED |
| CS-21…23 | Tool args / highlight failures / auto-expand HITL | timeline | PLANNED |
| CS-24…25 | Stream tokens / Enter sends | composer | LIVE / prefs PLANNED |
| CS-26…27 | Sound / notify long job | audio / notifications | PLANNED |
| CS-28…30 | Reset / Save & apply / Cancel | prefs | PLANNED |

### 9.3 Chain-of-thought block (on message)

```
┌ reasoning · collapsed ──────────── [expand] ─┐
│ 1. Read q3.csv  2. Group by region  3. Draft │
└──────────────────────────────────────────────┘
```

**Honesty (critical):**
- Render CoT **only** when the server/WS actually supplies reasoning/thought content. If `chat.done` / turn_meta carries no reasoning field, the block is **hidden** — never invent steps.
- `reasoning_format:"hidden"` is forced server-side for tools/JSON (`litellm_helpers.apply_reasoning_format`). UI must not claim CoT when the provider returned hidden reasoning — show nothing or a GATED note `Reasoning is hidden for this model/tools turn.`
- Prefs persist via `PUT /user/preferences` (or live preferences route). Until the route is live, prefs can be local-only but Save must say so honestly if the API is absent (prefer GATED Save with reason over silent local-only that pretends to persist).

**Files:** prefer new `components/soma-chat-settings.ts` + small hooks in `soma-message.ts` (CoT block) and `soma-composer.ts` (prefs apply). Those chat files are claimed by `soma-chat-uiux` — **coordinate / merge-additive**.

---

## 10. Collision inventory — `webui/src` (seat B risk map)

Derived from tree + CLAIMS.md (2026-10-13). "Risk" = chance of two seats editing the same file.

### 10.1 HIGH risk (hot shared files)

| Path | Size / role | Why hot | Rule |
|---|---|---|---|
| `views/soma-chat.ts` | ~137KB god-file | chat-uiux + wave6 + any chat prefs/CoT | Coordinate every edit; prefer extracted modules |
| `main.ts` | router + boot | every new route | **merge-additive** only |
| `components/soma-right-panel.ts` | ~41KB canvas host | File Manager mount, Agent tab relabel, wave6 | merge-additive; File Manager as child module |
| `views/soma-settings.ts` | ~53KB settings shell | Tools catalog / Brain label / export | merge-additive |
| `components/index.ts` · `views/index.ts` | barrels | every new module | **append exports only** |
| `styles/tokens.css` | token vocabulary | seat A sole owner | peer **read-only**; request tokens via A2A |

### 10.2 MEDIUM risk

| Path | Why | Rule |
|---|---|---|
| `components/soma-sidebar.ts` | rail Memory/Settings law | refactor in place; IA-001 is authority |
| `components/soma-composer.ts` | chat-uiux claim + prefs/CoT apply | merge-additive |
| `components/soma-message.ts` | chat-uiux claim + CoT block | merge-additive; CoT block additive |
| `components/soma-tool-timeline.ts` | chat-uiux claim | merge-additive |
| `views/soma-personal-profile.ts` | wave6 claim + password modal | prefer new modal file |
| `views/soma-cognitive-panel.ts` / settings-somabrain | Brain naming | label-only changes OK |
| `components/soma-capsule-editor.ts` | Agent workspace rename + Hands tab | label + additive tabs |
| `views/soma-login.ts` / register / forgot | wave6 claim | avoid unless auth contract needs it |

### 10.3 LOW risk / greenfield (peer free to create)

| Planned module | Suggested path | Notes |
|---|---|---|
| `soma-app-shell` | `components/soma-app-shell.ts` | L1 |
| `soma-topbar` | `components/soma-topbar.ts` | L1 |
| `soma-toast` / host | `components/soma-toast.ts` | L0/L1 |
| `soma-notification-center` / tray | `components/soma-notification-tray.ts` | L1 |
| `soma-change-password` | `components/soma-change-password.ts` | modal |
| `soma-file-manager` + sub-tags | `components/soma-file-manager.ts` (+ sub) | L2 |
| `soma-chat-settings` | `components/soma-chat-settings.ts` | L3 |
| Hands tools manager | `components/soma-agent-hands.ts` (or capsule-tools) | L2; naming law in labels |
| Agent package modals | `components/soma-agent-package.ts` | export/import |
| Upload tray | `components/soma-file-upload-tray.ts` | under File Manager |
| `soma-drawer` · `soma-tabs` · `soma-input` · `soma-card` | `components/soma-*.ts` | L0 primitives per MODULE-CATALOG |

### 10.4 Seat A paths (peer read-only)

`skin-sdk/**` · `styles/tokens.css` · `styles/skin-aliases.css` (may be created by A) · `services/skin-applier.ts` · `services/skin-boot.ts` · `docs/design/**`.

If peer needs a new token or alias, request via A2A OUTBOX — do not fork the vocabulary.

### 10.5 Known defects / dead code (do not "fix" silently)

| Item | Note |
|---|---|
| `components/soma-welcome-dashboard.ts` | ships banned Memory hero card; never rendered (A2-F17) — **delete or leave unused**; do not mount |
| `soma-agent-metrics.ts:214` `/* Charts placeholder */` | unrendered; no fake data — leave or GATED |
| `soma-capsule-editor.ts` name | technical name OK; **labels** must say Agent |
| `skin-aliases.css` | claimed by seat A but may not exist yet — do not create a second alias file |

---

## 11. Build order (focus order from plan)

| Order | Ticket | Deliverable | Exit |
|---|---|---|---|
| 1 | T3 | app-shell + topbar + rail | chrome law (IA-001) |
| 2 | — | toast + tray + bell | notifications honesty |
| 3 | — | Profile + password modal | CM-11 password flow |
| 4 | T7b | Agent package Hands tools manager | install/enable/policy per agent |
| 5 | — | Agent package export/import modals | GATED until APIs live |
| 6 | T7 | File Manager | browse/upload honest |
| 7 | T4 | Chat settings modal (CoT) | prefs apply live |
| 8 | T14 | Playwright | human session green on real services |

Do not start a later item before the previous has `tsc --noEmit` green and an honest empty/error state.

---

## 12. Acceptance checklist (seat B)

- [ ] `npx tsc` / `vite build` green in `webui/`
- [ ] No hardcoded hex/px/hosts in new components (tokens only)
- [ ] Zero user-facing "Capsule" strings in new chrome (rg proof)
- [ ] Every new control: real handler **or** GATED + reason
- [ ] Empty ≠ error on every data surface
- [ ] Memory still one home `/memory`; Models still only in Settings
- [ ] CLAIMS.md updated before large edits; no reverts of peer paths
- [ ] No shims/fakes/mocks/stubs/TODOs
- [ ] Playwright (when authorized) on real services for shell → toast → profile → Hands → files → chat settings

---

## 13. A2A protocol (both seats)

1. Claim paths in `CLAIMS.md` before large edits (append-only).
2. Log lands/commits in `LEDGER.md`.
3. Messages in `INBOX.md` / `OUTBOX.md` (append-only).
4. Shared files = merge-additive. Never delete peer A2A entries.
5. Handshake: peer ACKs this brief in INBOX before implementation wave.

---

*Seat A owns contracts and tokens. Seat B implements. Code is truth. No mocks.*
