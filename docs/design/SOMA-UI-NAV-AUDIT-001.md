# SOMA-UI-NAV-AUDIT-001 — Mock ↔ route checklist

## Document Control

| Field | Value |
|---|---|
| Document Title | Navigation audit — every mock vs `main.ts` routes |
| Document Identifier | SOMA-UI-NAV-AUDIT-001 |
| Version | 1.0.0 |
| Date | 2026-10-08 |
| Status | Draft |
| Source of truth | `somaAgent01/webui/src/main.ts` (route table, lines cited) + `docs/design/mockups/*.md` |
| Related | SOMA-UI-NAV-001 · SOMA-UI-MODEL-ADMIN-001 · SOMA-UI-MOCKUPS-001 (7–7G) |
| Rule | One home per feature. Memory once. No invented routes. Settings = one shell, 7 sections. |

---

## 1. Checklist — every `main.ts` route → mock

Evidence column cites `webui/src/main.ts` line of the branch and the mock file.

| # | Route(s) in `main.ts` | View loaded | Mock | Status |
|---|---|---|---|---|
| 1 | `/login` (publicPaths 35; 54) | login / redirect `/chat` | `mockups/UI-S-29-login.md` | OK |
| 2 | `/register` (35; 67) | `soma-register` | `mockups/UI-S-30-register.md` | OK |
| 3 | `/forgot-password` (35; 74) | `soma-forgot-password` | `mockups/UI-S-31-forgot-password.md` | OK |
| 4 | `/reset-password` · `/verify-email` (35; 85) | inline notice (not a view element) | `mockups/UI-S-31-forgot-password.md` | OK (notice documented in mock) |
| 5 | `/auth/callback` (35; 112) | `soma-auth-callback` | `mockups/UI-S-33-auth-callback.md` | OK |
| 6 | `/logout` (285) | redirect `/login` | — (redirect) | OK |
| 7 | `/onboarding` · `/invite/*` (279) | redirect `/register` | `mockups/UI-S-30-register.md` | OK (no separate screen) |
| 8 | `/` · `/index.html` (124) | `soma-chat` | `mockups/UI-S-07-chat-workspace.md` | OK |
| 9 | `/chat` · `/chat/` · `/chat/*` · `/soma/chat` (316) | `soma-chat` | `mockups/UI-S-07-chat-workspace.md` | OK |
| 10 | `/workspace` (323) | `soma-chat` | `mockups/UI-S-07-chat-workspace.md` | OK (alias — see DUP-1) |
| 11 | `/memory` (329) | `soma-memory-view` | `mockups/UI-S-04-memory.md` | OK · Memory once |
| 12 | `/settings` (347) | `soma-settings` | `mockups/UI-S-50-settings-agent.md` (shell + Agent) | OK |
| 13 | `/settings/models` · `/agent/models` (335) | `soma-settings-models` | `mockups/UI-S-51-settings-models.md` | OK |
| 14 | `/settings/channels` · `/agent/channels` (341) | `soma-settings-channels` | `mockups/UI-S-52-settings-channels.md` | OK |
| 15 | `/settings/multimodal` · `/agent/multimodal` (200) | `soma-multimodal-settings` | `mockups/UI-S-49-multimodal-settings.md` | OK |
| 16 | `/settings/mfa` · `/mfa/setup` (301) | `soma-mfa-setup` | `mockups/UI-S-32-mfa-setup.md` | OK |
| 17 | `/cognitive` · `/training` (271) | `soma-cognitive-panel` | `mockups/UI-S-02-brain.md` · `mockups/UI-X-07-brain.md` | OK |
| 18 | `/voice` · `/voice/chat` · `/platform/voice/chat` (399) | `soma-voice-chat` | `mockups/UI-S-46-voice-chat.md` | OK |
| 19 | `/voice/personas` · `/platform/voice/personas` (387) | `soma-voice-personas` | `mockups/UI-S-48-voice-personas.md` | OK |
| 20 | `/voice/sessions` · `/platform/voice/sessions` (393) | `soma-voice-sessions` | `mockups/UI-S-47-voice-sessions.md` | OK |
| 21 | `/profile` (252) | `soma-personal-profile` | `mockups/UI-S-34-personal-profile.md` | OK |
| 22 | `/platform/profile` · `/admin/profile` (238; 245) | `soma-platform-profile` | `mockups/UI-S-35-platform-profile.md` | OK |
| 23 | `/themes` (353) | disabled notice (skins not implemented) | note in `mockups/UI-S-42-marketplace.md` / SKINS | **GAP-N3** (mock claims a different route) |
| 24 | `/soma/dashboard` · `/soma` · `/platform` (133) | `soma-agent-metrics` | claimed `mockups/UI-S-37-platform-dashboard.md` | **GAP-N1** (view mismatch) |
| 25 | `/platform/models` (139) | `soma-settings-models` | `mockups/UI-S-51-settings-models.md` | OK (alias of #13) |
| 26 | `/platform/ratelimits` · `/platform/infrastructure/redis/ratelimits` (147) | `soma-infrastructure-dashboard` (tab ratelimits) | `mockups/UI-S-40-rate-limits.md` | OK |
| 27 | `/platform/integrations` · `/soma/settings/integrations` (156) | `soma-integrations-dashboard` | `mockups/UI-S-41-integrations-dashboard.md` | OK |
| 28 | `/platform/roles` · `/platform/role-matrix` · `/soma/permissions` · `/platform/permissions` (164) | `soma-admin-roles-list` | `mockups/UI-S-23-roles.md` · `mockups/UI-S-24-permissions.md` | OK (one live view, two mock panes) |
| 29 | `/platform/api-keys` (172) | `soma-admin-api-keys` | `mockups/UI-S-53-settings-external-dev.md` | OK |
| 30 | `/admin/metrics` (179) | `soma-agent-metrics` | `mockups/UI-S-45-agent-metrics.md` | OK |
| 31 | `/platform/infrastructure` · `/soma/infrastructure` (186) | `soma-infrastructure-dashboard` | `mockups/UI-S-39-infrastructure-dashboard.md` | OK |
| 32 | `/platform/metrics` · `/soma/metrics` (193) | `platform-metrics-dashboard` | `mockups/UI-S-38-platform-metrics.md` | OK |
| 33 | `/platform/settings/:entity` (207) | `settings-form` (generic) | — | **MISS-M1** |
| 34 | `/admin/users` (224) | `soma-entity-views` → `soma-users-view` | `mockups/UI-S-22-users.md` | OK |
| 35 | `/admin/users/:id` (231) | `soma-user-detail` | `mockups/UI-S-22-users.md` (detail pane) | OK |
| 36 | `/admin/agents` (258) | `soma-entity-views` → `soma-agents-view` | `mockups/UI-S-15-module-list.md` | OK |
| 37 | `/platform/audit` · `/soma/audit` (265) | `soma-audit-dashboard` | `mockups/UI-S-43-audit-dashboard.md` · `mockups/UI-S-44-audit-log.md` | OK (see DUP-4) |
| 38 | `/audit` · `/admin/audit` (308) | `soma-audit-dashboard` | same | OK (aliases) |
| 39 | default fallthrough (408) | `soma-chat` | `mockups/UI-S-07-chat-workspace.md` | OK (never admin home) |

---

## 2. Checklist — every mock → route

| Mock | Claims route (in file) | `main.ts`? | Status |
|---|---|---|---|
| UI-S-00 chrome | shared chrome | n/a | OK (not a route) |
| UI-S-01 soul | chat facet Soul | n/a (facet) | OK (facet, not a path) |
| UI-S-02 brain | `/cognitive` | yes 271 | OK |
| UI-S-03 hands | chat facet Hands | n/a (facet) | OK |
| UI-S-04 memory | `/memory` | yes 329 | OK · Memory once |
| UI-S-05 body | chat facet Body | n/a (facet) | OK |
| UI-S-06 governance | chat facet Governance | n/a (facet) | OK |
| UI-S-07 chat workspace | `/chat` | yes 316 | OK |
| UI-S-08 message detail | chat subview | n/a | OK |
| UI-S-09 conversation export | chat subview | n/a | OK |
| UI-S-10 conversation queue | chat subview | n/a | OK |
| UI-S-11 capsule list | entity views | partial (`/admin/agents` 258) | OK |
| UI-S-12 capsule editor | entity subview | n/a | OK |
| UI-S-13 version rail diff | entity subview | n/a | OK |
| UI-S-14 instances | entity subview | n/a | OK |
| UI-S-15 module list | `/admin/agents` | yes 258 | OK |
| UI-S-16 module detail | entity subview | n/a | OK |
| UI-S-17 capability registry | entity subview | n/a | OK |
| UI-S-18 capability detail | entity subview | n/a | OK |
| UI-S-19 tenants | — | no | **ORPH-M1** (no route; see GAP-N5) |
| UI-S-20 tenant wizard | — | no | **ORPH-M1** |
| UI-S-21 tenant dashboard | — | no | **ORPH-M1** |
| UI-S-22 users | `/admin/users` | yes 224 | OK |
| UI-S-23 roles | `/platform/roles` | yes 164 | OK |
| UI-S-24 permissions | `/platform/permissions` | yes 166 | OK |
| UI-S-25 billing | — | no | **ORPH-M2** (AGENT.md §1.1: standalone agent, no billing routes — main.ts 131–132) |
| UI-S-26 subscriptions | — | no | **ORPH-M2** |
| UI-S-27 usage analytics | — | no | **ORPH-M2** |
| UI-S-28 tier builder | — | no | **ORPH-M2** |
| UI-S-29 login | `/login` | yes 54 | OK |
| UI-S-30 register | `/register` | yes 67 | OK |
| UI-S-31 forgot password | `/forgot-password` | yes 74 | OK |
| UI-S-32 mfa setup | `/mfa/setup` | yes 301 | OK |
| UI-S-33 auth callback | `/auth/callback` | yes 112 | OK |
| UI-S-34 personal profile | `/profile` | yes 252 | OK |
| UI-S-35 platform profile | `/platform/profile` | yes 238 | OK |
| UI-S-36 mode selection | `/mode-select` | **no** | **ORPH-M3** |
| UI-S-37 platform dashboard | `/saas/dashboard` | **no** | **ORPH-M4** / GAP-N1 |
| UI-S-38 platform metrics | `/platform/metrics` | yes 193 | OK |
| UI-S-39 infrastructure dashboard | `/platform/infrastructure` | yes 186 | OK |
| UI-S-40 rate limits | `/platform/ratelimits` | yes 147 | OK |
| UI-S-41 integrations dashboard | `/platform/integrations` | yes 156 | OK |
| UI-S-42 marketplace | `/platform/marketplace` | **no** | **ORPH-M5** |
| UI-S-43 audit dashboard | `/platform/audit` | yes 265 | OK |
| UI-S-44 audit log | `/platform/audit` pane | yes 265 | OK (same surface) |
| UI-S-45 agent metrics | `/admin/metrics` | yes 179 | OK |
| UI-S-46 voice chat | `/voice` | yes 399 | OK |
| UI-S-47 voice sessions | `/voice/sessions` | yes 393 | OK |
| UI-S-48 voice personas | `/voice/personas` | yes 387 | OK |
| UI-S-49 multimodal settings | `/settings/multimodal` | yes 200 | OK |
| UI-S-50 settings agent | `/settings` | yes 347 | OK (shell + Agent) |
| UI-S-51 settings models | `/settings/models` | yes 335 | OK |
| UI-S-52 settings channels | `/settings/channels` | yes 341 | OK |
| UI-S-53 settings external-dev | `/platform/api-keys` | yes 172 | OK |
| UI-X-01…08 surfaces | canvas tabs | n/a (chrome) | OK (not paths) |

---

## 3. DUPLICATE homes

| ID | Feature | Competing homes | Evidence | Resolution |
|---|---|---|---|---|
| **DUP-1** | Chat workspace | `/chat` and `/workspace` both load `soma-chat` | `main.ts` 316 and 323 | Keep both paths → **one** view + one mock (UI-S-07). `/workspace` is an alias only. |
| **DUP-2** | Models library | `/settings/models`, `/agent/models`, `/platform/models` all load `soma-settings-models` | `main.ts` 335 and 139 | One home: **Settings · Models** (UI-S-51). Aliases allowed. No floating second library. |
| **DUP-3** | Integrations keys | Settings · Integrations (UI-S-52) vs platform Integrations dashboard (UI-S-41) vs External & Developer (UI-S-53) | `main.ts` 341 · 156 · 172 | Split by audience: UI-S-52 = agent-owner provider keys + channels; UI-S-41 = platform integrations catalogue; UI-S-53 = platform API keys / developer. Names must stay distinct in nav. |
| **DUP-4** | Audit | `/platform/audit`, `/soma/audit`, `/audit`, `/admin/audit` all load `soma-audit-dashboard`; mocks UI-S-43 + UI-S-44 | `main.ts` 265 and 308 | One surface. UI-S-43 = dashboard chrome, UI-S-44 = log pane of the same screen. Do not present as two destinations. |
| **DUP-5** | Agent metrics | `/admin/metrics` and `/soma/dashboard`·`/platform` both load `soma-agent-metrics` | `main.ts` 179 and 133 | One metrics surface (UI-S-45). `/platform` must not also claim UI-S-37 (see GAP-N1). |
| **DUP-6** | Voice entry | Settings · Voice section + `/voice/*` routes | `main.ts` 387–403; UI-S-46/47/48 | Allowed: Settings section is the config home; `/voice/*` are the run surfaces. One config home only. |
| **DUP-7** | Roles/permissions | `/platform/roles` + `/platform/permissions` + `/soma/permissions` → one `soma-admin-roles-list` | `main.ts` 164–166 | UI-S-23 catalogue + UI-S-24 matrix are panes of one screen. |

**Memory once rule.** Memory appears **once** in the IA: left-rail `/memory` → UI-S-04 (`main.ts` 329). Not in Settings nav (UI-S-50 section list). Not a canvas tab (UI-X surfaces). Entry points that all route to the same view are allowed (C2 Open Memory, ⋮, ⌘K) per UI-S-04. **PASS** in UI-S-50..53: Memory is named only as a “not here” rule and as a Used-for binding label (Chat / Help / Memory) on model cards (UI-S-51) — never as a Settings section.

---

## 4. MISSING mocks

| ID | Route / surface | Evidence | Gap |
|---|---|---|---|
| **MISS-M1** | `/platform/settings/:entity` → `settings-form` | `main.ts` 207–220 | No mock for the generic SettingsForm entity screen. |
| **MISS-M2** | Settings section **Interface** | target nav in `SOMA-UI-MODEL-ADMIN-001.md` §2; Screen 7D in `SOMA-UI-MOCKUPS-001.md` 595–608 | Spec table only — no UI-S mock file. |
| **MISS-M3** | Settings section **Tools** | target nav; Screen 7E at `SOMA-UI-MOCKUPS-001.md` 611–615 | Spec table only — no UI-S mock file. |
| **MISS-M4** | Settings section **Voice** body (7C field table) | `SOMA-UI-MOCKUPS-001.md` 532–592 | Covered only as run surfaces UI-S-46/47/48; no Settings-shell Voice section mock. |
| **MISS-M5** | `/reset-password` · `/verify-email` notice | `main.ts` 85–107 | Inline notice, no component mock (accepted as notice). |

---

## 5. ORPHAN routes & ORPHAN mocks

### ORPHAN mock claims (route not in `main.ts`)

| ID | Mock | Claimed route | Evidence | Action |
|---|---|---|---|---|
| **ORPH-M3** | `mockups/UI-S-36-mode-selection.md` | `/mode-select` | not present in `main.ts` | Remove claim or delete mock. |
| **ORPH-M4** | `mockups/UI-S-37-platform-dashboard.md` | `/saas/dashboard` | not in `main.ts`; live `/platform` loads `soma-agent-metrics` (`main.ts` 133) | Retarget mock to `/platform` → UI-S-45, or drop. |
| **ORPH-M5** | `mockups/UI-S-42-marketplace.md` | `/platform/marketplace` | not in `main.ts` | Remove claim. Marketplace has no route. |
| **ORPH-M1** | UI-S-19 / 20 / 21 (tenants) | (none) | no tenant routes; `main.ts` 131–132 comment: standalone agent | Keep as future / enterprise, or mark gated. |
| **ORPH-M2** | UI-S-25 / 26 / 27 / 28 (billing) | (none) | same comment | Out of scope for this deployment. |

### ORPHAN routes (in `main.ts`, weak or no mock story)

| ID | Route | Evidence | Note |
|---|---|---|---|
| **ORPH-R1** | `/themes` | `main.ts` 353–383 | Present-but-disabled skins notice. Not a settings destination. Documented in SKINS spec. |
| **ORPH-R2** | `/platform/settings/:entity` | `main.ts` 207 | Generic form, no named mock (MISS-M1). |
| **ORPH-R3** | `/onboarding` · `/invite/*` | `main.ts` 279–282 | Redirect to `/register` only. Acceptable. |

### NAV-001 drift (doc vs code)

| ID | NAV-001 says | `main.ts` does | Fix |
|---|---|---|---|
| **GAP-N1** | `/platform` · `/soma/dashboard` · `/soma` → `soma-platform-profile` / UI-S-37 (`SOMA-UI-NAV-001.md` line 53) | loads `soma-agent-metrics` (`main.ts` 133–136) | Correct NAV-001 to UI-S-45, or change the router. Do not keep both claims. |
| **GAP-N2** | Settings shell sections list 7 including Interface/Tools (`SOMA-UI-NAV-001.md` 66–76) | live `soma-settings.ts` `_tabs` (639–646) has 6: Agent, Models, Voice, Integrations, Connectivity, Advanced | Add Interface + Tools tabs; rename Connectivity into Integrations or Tools per spec. |
| **GAP-N3** | `/themes` → “UI-S-42 note” (`SOMA-UI-NAV-001.md` 47) | UI-S-42 claims `/platform/marketplace` | UI-S-42 is not a skins mock. Point the note at the SKINS spec instead. |
| **GAP-N4** | Memory once (`SOMA-UI-NAV-001.md` 97) | UI-S-50..53 do not add Memory to Settings nav | **PASS** after this suite rewrite. |
| **GAP-N5** | Platform / admin block includes tenants/billing mocks in the feature index (`SOMA-UI-NAV-001.md` 118) | no routes | Index must mark 19–28 as non-routed / future. |

---

## 5B. Agent Zero chrome merge (2026-10-07, verified against `~/Downloads/agent-zero-main/webui`)

| # | A0 anchor | Finding | Fix owner |
|---|---|---|---|
| A0-1 | `components/chat/top-section/chat-top.html:19-32` | Chat top = time · sync · notifications · project only. **No model/mode/agent settings cluster.** | `soma-chat.ts` header → thin strip; move Pause/Nudge/Stop/Reset next to turn title (C1), not global settings |
| A0-2 | `components/welcome/welcome-screen.html:16-25` | Welcome primary CTA is the **composer**, not action cards. | `_renderWelcome` → composer hero + task starters only |
| A0-3 | `components/welcome/welcome-screen.html:73-133` | A0 Quick Actions = real product destinations | Soma cards: New chat · Files · Agents · Settings · Voice · Brain |
| A0-4 | `components/sidebar/left-sidebar.html:16-36` | Left rail: header icons · quick actions · chats · tasks · bottom preferences. Settings/Memory live in **bottom zone**, not a mid-nav dump of Models/Channels. | Remove Models from `soma-chat.ts:1960-1962` |
| A0-5 | `js/api.js` + `js/websocket.js` | Single `callJsonApi`/`fetchApi` + one WS client. No parallel clients. | Keep `api-client.ts` + `websocket-client.ts` as the only seams |
| A0-6 | `index.html:199-268` | Layout: left sidebar \| right panel (top + welcome\|messages + input) \| right canvas. No third competing rail. | `soma-chat.ts` render() = sidebar + main + canvas — keep; drop duplicate content inside main |

---

## 6. Settings suite acceptance (this package)

| Check | Result | Evidence |
|---|---|---|
| Settings = ONE workspace shell, 7 sections | **PASS** | `UI-S-50-settings-agent.md` section nav table (Agent · Models · Voice · Interface · Tools · Integrations · Advanced) |
| Models mock matches `ModelIn` + Load models + Vault key + Activate | **PASS** | `UI-S-51-settings-models.md` field map ↔ `admin/llm/api.py` 117–135 |
| Modal Normal / Advanced / Used for | **PASS** | `UI-S-51-settings-models.md` modal wireframe |
| Keys Vault write-only | **PASS** | UI-S-51 key line · UI-S-52 providers · UI-S-53 credentials |
| Used for: Chat / Help / Memory (no banned noun) | **PASS** | UI-S-51 Used for block; zero banned-noun strings in UI-S-50..53 |
| Memory not in Settings nav | **PASS** | UI-S-50 section list omits Memory; rule stated in UI-S-50/52 |
| NAV audit names every gap with file path evidence | **PASS** | this file §3–§5 |

---

## 7. Acceptance checklist (reusable)

- [ ] Every `main.ts` path has exactly one mock (§1)
- [ ] Every mock points at a real `main.ts` path or is marked facet / subview / future (§2)
- [ ] Memory appears once in IA (left rail `/memory`) — §3 Memory once
- [ ] Canvas has 8 surfaces, no Memory tab
- [ ] Settings has one shell with 7 sections — UI-S-50
- [ ] No route in mocks that is not in `main.ts` (except documented future 7H–7T)
- [ ] Zero banned binding noun in UI strings (Used for: Chat / Help / Memory)
- [ ] Keys write-only, Vault-backed, never echoed
- [ ] Model editor fields = `ModelIn` only
- [ ] Gated surfaces carry blocking reason

End of Document
