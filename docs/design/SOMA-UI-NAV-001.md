# SOMA-UI-NAV-001 — Full navigation map (real routes)

## Document Control

| Field | Value |
|---|---|
| Document Title | Agent Soma — complete UI navigation map |
| Document Identifier | SOMA-UI-NAV-001 |
| Version | 1.0.0 |
| Date | 2026-10-08 |
| Status | Draft |
| Source of truth | `somaAgent01/webui/src/main.ts` route table + live views |
| Related | SOMA-UI-CHAT-WORKSPACE-001 · UI-S-* · UI-X-* |
| Rule | **No invented routes.** One home per feature. Memory once. |

---

## 1. Real routes (from `main.ts`)

### Public (no auth)

| Route | View | Mock |
|---|---|---|
| `/login` | `soma-login` | UI-S-29 |
| `/register` | `soma-register` | UI-S-30 |
| `/forgot-password` | `soma-forgot-password` | UI-S-31 |
| `/reset-password` · `/verify-email` | reset / verify | UI-S-31 |
| `/auth/callback` | `soma-auth-callback` | UI-S-33 |
| `/logout` | redirect `/login` | — |

### Core (signed-in)

| Route | View | Mock | Nav entry |
|---|---|---|---|
| `/` · `/chat` · `/chat/:id` · `/workspace` | `soma-chat` | **UI-S-07** | default |
| `/memory` | `soma-memory-view` | **UI-S-04** | Left rail **Memory** (only) |
| `/settings` | `soma-settings` | UI-S-50 shell | ⚙️ / left rail |
| `/settings/models` · `/agent/models` | `soma-settings-models` | UI-S-51 | Settings · Models |
| `/settings/channels` · `/agent/channels` | `soma-settings-channels` | UI-S-52 | Settings · Integrations |
| `/settings/multimodal` | multimodal settings | UI-S-49 | Settings · Advanced |
| `/cognitive` · `/training` | `soma-cognitive-panel` | UI-S-02 / UI-X-07 | Brain surface · facet |
| `/voice` · `/voice/chat` | `soma-voice-chat` | UI-S-46 | Settings · Voice |
| `/voice/personas` | `soma-voice-personas` | UI-S-48 | Settings · Voice |
| `/voice/sessions` | `soma-voice-sessions` | UI-S-47 | Settings · Voice |
| `/profile` · `/admin/profile` · `/platform/profile` | `soma-personal-profile` | UI-S-34 | 👤 |
| `/mfa/setup` · `/settings/mfa` | `soma-mfa-setup` | UI-S-32 | Profile |
| `/themes` | skins (disabled) | UI-S-42 note | hidden until real |

### Platform / admin (enterprise)

| Route | View | Mock |
|---|---|---|
| `/platform` · `/soma/dashboard` · `/soma` | `soma-agent-metrics` (live `main.ts:133`) | UI-S-37 / UI-S-45 |
| `/platform/models` | models admin | UI-S-51 |
| `/platform/ratelimits` | rate limits | UI-S-40 |
| `/platform/integrations` | integrations | UI-S-41 |
| `/platform/roles` · `/platform/permissions` | `soma-role-matrix` | UI-S-23/24 |
| `/platform/api-keys` | `soma-admin-api-keys` | UI-S-53 |
| `/platform/infrastructure` | `soma-infrastructure-dashboard` | UI-S-39 |
| `/platform/metrics` | `soma-agent-metrics` / metrics | UI-S-38/45 |
| `/platform/audit` | `soma-audit-dashboard` | UI-S-43/44 |
| `/admin/users` | `soma-user-detail` / users | UI-S-22 |
| `/admin/agents` | `soma-entity-views` agents | UI-S-15 |
| `/admin/metrics` | metrics | UI-S-45 |

### Settings shell sections (in-page, `/settings`)

| Section | Screen | Mock |
|---|---|---|
| Agent | personality, prompt, limits | UI-S-50 / Screen 7 |
| Models | card library + modal | UI-S-51 / 7B |
| Voice | personas, TTS/STT | UI-S-48 / 7C |
| Interface | theme, language, density | 7D |
| Tools | tool enable cards | 7E |
| Integrations | keys Vault, events | 7F / UI-S-52 |
| Advanced | modules, quotas, backup | 7G |

---

## 2. Chat workspace chrome nav

```
TOP     Agent ▾ · model · mode · ⌘K · 🔔 · ⚙️ → /settings · 👤 → /profile
LEFT    New chat · chats · /memory · /settings · /settings/models · user
CHAT    C1 controls · C2 Open Memory → /memory · C3 stream · C4 HITL · C5 composer
CANVAS  Files | Tools | Browser† | Editor | Debug | Capsule | Brain | Desktop†
        (NO Memory tab)
STATUS  metrics + neuromod (Brain surface)
```

---

## 3. One-home rules (audit)

| Feature | Single home | Entry points (same destination) | Never |
|---|---|---|---|
| **Memory** | `/memory` UI-S-04 | left rail, C2 Open Memory, ⋮, ⌘K | canvas tab, welcome card, chat mini-panel |
| **Models** | `/settings/models` | Settings nav, model chip, left rail Models | floating second library |
| **Voice** | `/settings` Voice + `/voice/*` | Settings · Voice | chat-only voice UI |
| **Brain** | `/cognitive` + canvas Brain | facet, canvas surface | duplicate neuromod widgets |
| **Chat** | `/chat` | default, left rail | — |
| **Files** | canvas Files | attach menu (drawer of same) | second file tree |

---

## 4. Feature → screen index (whole product)

| Area | Screens |
|---|---|
| Auth | 29 30 31 32 33 |
| Chat | **07** 08 09 10 |
| Memory | **04** (only) |
| Brain / IQ | 02 · X-07 |
| Capsule / agent | 11 12 13 14 · X-06 |
| Surfaces | X-01…X-08 |
| Settings | 50 51 52 53 + 7D–7G |
| Voice | 46 47 48 49 |
| Platform / ops | 19–28 34–45 |
| Chrome | 00 |

---

## 5. Navigation acceptance

- [ ] Every `main.ts` path has exactly one mock
- [ ] Memory appears once in IA (left rail)
- [ ] Canvas has 8 surfaces, no Memory tab
- [ ] Settings has one shell with 7 sections
- [ ] No route in mocks that is not in `main.ts` (except documented future 7H–7T)
- [ ] Gated surfaces carry blocking reason

End of Document
