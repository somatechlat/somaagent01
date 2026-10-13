# SOMA-UI-CONTROL-MAPS-INDEX-001 — UI Control Map Register

## Document Control

| Field | Value |
|---|---|
| Document Title | Agent Soma — UI Control Map Register (live + planned) |
| Document Identifier | SOMA-UI-CONTROL-MAPS-INDEX-001 |
| Version | 1.0.0 |
| Date | 2026-10-13 |
| Status | Draft |
| Author | SomaTech Engineering (soma-ui-engineer) |
| Approver | — |
| Classification | Internal |
| ISO Reference | ISO 9241-210:2019 · ISO 9001:2015 clause 7.5 |
| Next Review | 2027-01-13 |
| Source of truth | Live `webui/src/**` inventory · `docs/design/SOMA-UI-BINDINGS-001.md` · `docs/design/SOMA-UI-MODULE-CATALOG-001.md` · `docs/design/SOMA-UI-AGENT-FRONTEND-MASTER-001.md` · `docs/design/mockups/UI-S-*` / `UI-X-*` |
| Stack law | Lit 3.x only · no React/Alpine · no shims/fakes/mocks/stubs · real REST/WS only |
| Honesty law | Every control is LIVE, PLANNED (real target API), or GATED (present-but-disabled + blocking reason). No dead CTA. No invented fields. |

## Revision History

| Version | Date | Author | Description |
|---|---|---|---|
| 1.0.0 | 2026-10-13 | soma-ui-engineer | Initial control-map register. Exhaustive button/field inventory of live `webui/` plus planned File Manager, Memory Manager, SomaBrain Manager, Settings knobs, Command Palette. |

---

## 1. How to read these control maps

| Column | Meaning |
|---|---|
| **ID** | Stable control id, `CM-<doc>-<nn>` (or source `data-testid` when present). |
| **Label** | Visible label / aria-label / title (verbatim where the code sets one). |
| **Type** | `button` · `link` · `input.text` · `input.password` · `input.search` · `input.number` · `input.checkbox` · `input.file` · `textarea` · `select` · `toggle` · `tabs` · `list-row` · `chip` · `status-dot` · `stat` · `modal` · `menu` · `surface` · `readout` |
| **Binding / API** | Exact REST path (`/api/v2/…` unless noted) or WS frame (`/ws/v2/…`) or **local** (client-only state) or **none** (static). |
| **States** | `default · focus · hover · active · disabled · loading · empty · error · dirty` as implemented. |
| **Disabled reason** | Verbatim blocking reason when status is GATED, or `—` when always enabled. |
| **A11y** | Roles / labels / keys the control exposes or MUST expose. |
| **Status** | **LIVE** = handler + real API/WS in shipped `webui/`. **PLANNED** = designed control with a named real target API (module catalog / frontend master). **GATED** = present-but-disabled with a real blocking reason (never a placeholder). |

### Status law (Soma)

1. A PLANNED control MUST name a real target API or honest gate. Specifying “coming soon” as a value is forbidden (`SOMA-01-DOCS-001` REQ-DOCS-015).
2. A GATED control MUST remain visible with its reason (REQ-UIX-020 pattern in `soma-right-panel.ts`).
3. An empty state MUST NOT impersonate an error, and an error MUST NOT impersonate empty (`_loadFailed` pattern).
4. Vault-owned secrets render masked; the value is never redisplayed.
5. Memory has exactly one home: `/memory` (UI-S-04). Canvas has no Memory tab.

---

## 2. Register of control-map documents

| Doc | Screen family | Primary routes | Live sources | Planned modules covered |
|---|---|---|---|---|
| [CM-01-chat-workspace.md](./CM-01-chat-workspace.md) | Chat hero + chrome + sidebar + composer + messages + tool timeline + welcome | `/` `/chat` `/chat/:id` `/workspace` | `soma-chat.ts`, `soma-composer.ts`, `soma-chat-topbar.ts`, `soma-message.ts`, `soma-tool-timeline.ts`, `soma-sidebar.ts`, `soma-welcome-dashboard.ts` | Branching, in-chat search, syntax highlight, markdown tables |
| [CM-02-file-manager.md](./CM-02-file-manager.md) | File Manager (tree/list/preview/upload) + Files surface | canvas `UI-X-01` · planned `/files` | `soma-right-panel.ts` `_renderFiles`, `file-upload.ts` | **M-024 `soma-file-manager`** full (tree, breadcrumb, upload tray, preview, manage) |
| [CM-03-memory-manager.md](./CM-03-memory-manager.md) | Memory Manager (search/remember/forget) | `/memory` | `soma-memory-view.ts` | Memory Manager depth (probe drawer, store filter honesty) |
| [CM-04-somabrain-manager.md](./CM-04-somabrain-manager.md) | SomaBrain Manager (neuromods/knobs/diagnostics) | `/cognitive` `/training` · settings `/settings/somabrain` · canvas `UI-X-07` | `soma-cognitive-panel.ts`, `soma-settings-somabrain.ts`, `soma-agent-iq.ts` | SomaBrain Manager consolidation, knob save, sleep/consolidation |
| [CM-05-settings.md](./CM-05-settings.md) | Settings × 9 tabs + Models + Channels + Interface skins | `/settings` `/settings/models` `/settings/channels` `/settings/somabrain` `/settings/multimodal` | `soma-settings.ts`, `soma-settings-models.ts`, `soma-settings-channels.ts`, `soma-settings-somabrain.ts`, `settings-form.ts` | Model Roles polish, Tools catalog policy, secret fields |
| [CM-06-canvas-surfaces.md](./CM-06-canvas-surfaces.md) | Canvas UI-X-01…08 rail + each surface | chat right-rail | `soma-right-panel.ts` `SURFACES` | Browser/Desktop honest gates; Editor Save unlock |
| [CM-07-auth.md](./CM-07-auth.md) | Auth family (login, register, forgot, MFA, callback) | `/login` `/register` `/forgot-password` `/reset-password` `/verify-email` `/auth/callback` `/mfa/setup` | `soma-login.ts`, `soma-register.ts`, `soma-forgot-password.ts`, `soma-mfa-setup.ts`, `soma-auth-callback.ts` | — |
| [CM-08-skins-gallery.md](./CM-08-skins-gallery.md) | Skins gallery (Preview / Apply / Uninstall / Revert) | `/themes` · Settings › Interface | `soma-skin-gallery.ts`, `skin-applier.ts`, `skin-sdk/` | Skin install polish |
| [CM-09-command-palette.md](./CM-09-command-palette.md) | Command Palette (⌘K) | global overlay | — (PLANNED) | **M-021 `soma-command-palette`** |
| [CM-10-admin-voice-profile.md](./CM-10-admin-voice-profile.md) | Admin, Voice, Profiles, Entity manager, Infra | `/admin/*` `/voice/*` `/profile` `/platform/*` | `soma-admin-*.ts`, `soma-voice-*.ts`, `soma-personal-profile.ts`, `entity-manager.ts`, `soma-audit-dashboard.ts`, `soma-infrastructure-dashboard.ts` | Notification center (M-022) |
| [CM-11-profile.md](./CM-11-profile.md) | User profile (Account / Security / Notifications / Sessions) + change-password modal | `/profile` · out `/mfa/setup` `/login` | `soma-personal-profile.ts`, `admin/auth/api.py`, `admin/platform/api/users.py`, `services/common/identity/password.py`, `admin/common/session_manager.py` | Change-password (UI-M-01), self session list/revoke, logout-all, avatar upload |

---

## 3. Screen ↔ UI-S / UI-X id crosswalk

| Control-map doc | Mockup ids | Module catalog ids |
|---|---|---|
| CM-01 | UI-S-00 chrome · UI-S-07 chat workspace · UI-S-08 message detail · UI-S-09 export · UI-S-10 queue | M-018…M-020, M-032…M-041 |
| CM-02 | UI-X-01 files · UI-X-01-files-v2 (planned annex) | M-024 + sub-tags |
| CM-03 | UI-S-04 memory | Memory manager depth |
| CM-04 | UI-S-02 brain · UI-X-07 brain · UI-S-56 settings-somabrain | AgentIQ strip, cognitive panel |
| CM-05 | UI-S-50…UI-S-57, UI-S-49 multimodal | M-042…M-045 |
| CM-06 | UI-X-01…UI-X-08 | M-025…M-028 |
| CM-07 | UI-S-29…UI-S-33 | login family |
| CM-08 | UI-S-54 settings-interface · skins | skin-sdk surfaces |
| CM-09 | UI-C-palette (planned annex) | M-021 |
| CM-10 | UI-S-22…24, UI-S-34…45, UI-S-46…48 | M-022, M-023, entity-manager |
| CM-11 | UI-S-34 personal profile · UI-M-01 drawer · UI-M-03 dialog | change-password + self sessions (PLANNED) |

> **CM-10 §5 vs CM-11.** CM-10 §5 (PR-01…PR-11) is retained for history but **superseded for `/profile` (UI-S-34)** by CM-11. Platform profile (UI-S-35) stays in CM-10.

---

## 4. Aggregate status rollup (derived from CM-01…CM-10)

Counts were re-derived on 2026-10-13 by scanning the status column of every control-map table row in `CM-*.md` (awk pass over `| ID | … | Status |` rows). Not copied from another document.

| Doc | LIVE | PLANNED | GATED | Rows |
|---|---:|---:|---:|---:|
| CM-01 chat | 72 | 9 | 2 | 83 |
| CM-02 files | 6 | 45 | 1 | 52 |
| CM-03 memory | 31 | 7 | 5 | 43 |
| CM-04 somabrain | 48 | 1 | 5 | 54 |
| CM-05 settings | 136 | 9 | 0 | 145 |
| CM-06 canvas | 28 | 9 | 4 | 41 |
| CM-07 auth | 38 | 0 | 3 | 41 |
| CM-08 skins | 11 | 3 | 1 | 15 |
| CM-09 palette | 0 | 22 | 0 | 22 |
| CM-10 admin/voice/profile | 61 | 8 | 2 | 71 |
| CM-11 profile | 23 | 29 | 2 | 54 |
| **TOTAL** | **454** | **142** | **25** | **621** |

Rollup rule: a control that is visible-but-disabled is GATED (not LIVE). A control whose handler exists but whose upstream API is absent is GATED with the API name in the disabled-reason column. Surface-registry rows inside CM-06 §2 are included in the CM-06 table counts via their rail buttons (X-00b). CM-10 §5 PR-* rows are still counted in the CM-10 line (they remain in that file); CM-11 is the live map for `/profile`.

---

## 5. A0 chrome law (applies to every document)

| Law | Enforcement in these maps |
|---|---|
| Composer = hero | CM-01 controls C-20…C-34 |
| Thin top strip | CM-01 controls C-01…C-08 |
| Left rail = Memory + Settings only (plus conversations / New chat) | CM-01 controls C-10…C-16; no Models/Brain/Memory hero cards on welcome |
| Memory one home `/memory` | CM-03; CM-06 forbids Memory tab |
| Models full-screen inside Settings | CM-05 tab `models`; CM-01 has no Models card |
| Every control has a real handler or honest disabled state | Status column in every map |
| Failure → visible error, never silent empty | States column + Honesty section per doc |

---

## 6. Proven handlers (live click-path sample)

The following controls were re-checked against source during this inventory and have real handlers (file:line in BINDINGS-001 where cited):

| Control | Handler proof |
|---|---|
| Send / Enter | `soma-chat.ts` `_deliverUserMessage` → WS `chat.message` |
| Pause / Resume / Stop / Reset / Nudge | `soma-chat-topbar.ts` `_emit` → `soma-chat.ts` WS `chat.*` |
| HITL Approve / Deny | `soma-tool-timeline.ts` `_onApproval` → WS `tool.approval` |
| New chat | `_startNewChat` → `POST /chat/conversations` |
| Rename / Delete / Export conversation | `PATCH` / `DELETE` / `GET …/messages` + Blob |
| Memory search | `_performSearch` → `POST /memory/recall` |
| Remember | `_submitRemember` → `POST /memory/save` |
| Forget | `_deleteMemory` → `POST /memory/forget` |
| Models Save / Activate / Delete / Test | `soma-settings-models.ts` `_saveModel` `_activate` `_deleteModel` `_testConnection` |
| Skin Apply / Preview / Uninstall / Revert / Install bundled | `soma-skin-gallery.ts` `_applyPack` `_previewPack` `_uninstall` `_revert` `_installBundled` |
| Composer attach / mic / send / menu / drop queue | `soma-composer.ts` + `soma-composer-menu.ts` |
| Surface rail toggle | `soma-chat.ts` `_toggleRightPanel` |
| Capsule Save / Reload / Export / Archive | `soma-capsule-editor.ts` `_save` `_load` `_export` `_archive` |

---

End of Document
