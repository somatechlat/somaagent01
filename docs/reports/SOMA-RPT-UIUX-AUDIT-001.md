# SOMA-RPT-UIUX-AUDIT-001 — WebUI full UI/UX audit vs official design suite

**Date:** 2026-10-13
**Scope:** `webui/src/**` only (somaAgent01)
**Sources of truth:** `docs/iso/SOMA-01-UIUX-001..005.md`, `docs/design/mockups/UI-S-*.md` + `UI-X-*.md`, `docs/design/SOMA-UI-MOCKUPS-001.md`, `docs/design/SOMA-UI-PARITY-002.md`, `webui/src/main.ts` (route ground truth)
**Law:** no env-var config · no hardcoded URLs · no mocks/fakes/shims · settings chain only · **Model Roles** (never "slots") · fail-closed honest UI states
**Live stack:** Agent `:20020` · WebUI `:20080` · Brain `:30101` (`memory_ok=true`)

---

## 0. Verification

| Check | Command | Result |
|---|---|---|
| TypeScript | `bun node_modules/typescript/bin/tsc --noEmit` (in `webui/`) | **PASS** — exit 0 |
| Python | `python3 -m py_compile admin/memory/api/memory.py admin/llm/api.py` | **PASS** — exit 0 |
| Env-var reads in `webui/src` | `rg 'process\.env\|import\.meta\.env\|VITE_\|REACT_APP_\|NODE_ENV'` | **0 hits** |
| Hardcoded hosts/ports | `rg 'localhost\|127\.0\.0\.1\|0\.0\.0\.0\|:<port>'` (excl. comments/placeholders) | **0 hits** |
| Secret-like literals | `rg "'sk-…'\|Bearer …\|api_key=\|password="` | **0 hits** |
| Banned "slot" wording | `rg '\bslot\b'` excluding HTML `slot=`/`<slot>` | **0 hits** (one `</slot>` HTML tag only) |

Node on this host is broken (`libada.3.dylib` broken self-referential symlink under `/usr/local/opt/ada-url`); `tsc` was run through Bun's runtime instead. Not a webui issue.

---

## 1. Priority findings

### P1 — Memory indicator (`soma-chat.ts` `_memoryDot`) — **PASS (was already correct)**

`webui/src/views/soma-chat.ts:1685` maps `status.state === 'ok'` → `StatusDotState 'ok'`.
`webui/src/components/soma-status-dot.ts:57` paints `'ok'` as filled `#10B981` (green).

Live proof:
```
GET /api/v2/memory/status
{"state":"ok","summary":"Memory ready","read_ok":true,"write_ok":true,
 "degraded":false,"circuit":"CircuitState.CLOSED","brain_status":"critical","reason":""}
```
→ UI green. **Honest:** `state` is computed server-side as `write_ok ∧ read_ok ∧ circuit ≠ open`
(`admin/memory/api/memory.py:117`). `brain_status:"critical"` is the brain's *overall* health
string, not the memory lane — the memory dot correctly ignores it (the brain dot is driven
separately by `/core/brain-connector`). Failure path (`catch`) sets `'warn'` + queued banner —
never green on an unreachable API.

### P2 — Memory panel UI-S-04 — **FAIL → FIXED**

| # | Control (UI-S-04 §3) | Before | After |
|---|---|---|---|
| 1 | Search / recall probe | live | live |
| 2 | **Run probe** button | **MISSING** | **ADDED** |
| 7 | **WM / LTM tiles** | **MISSING** | **ADDED** — render `—` + `GATED`, never 0 |
| 10 | Total Memories | fell back to `memories.length` (invented) | `response.total` only, else `—` |
| 12 | **Remember…** | **MISSING** | **ADDED** → `POST /memory/save` |
| 13 | Forget | live (`POST /memory/forget`) | live (total decremented only if known) |
| 14 | Export JSON | live | live |
| 15 | Refresh | live | live |
| 16 | ← Back to chat | live | live |
| 4 | this-turn filter `?turn=current` | **MISSING** | **ADDED** + `[clear]` |

Also fixed: recall hit-count no longer overwrites the list `total` (they are separate dashboard
figures per §3.7).

**Contract note:** mockup names the write `POST /memory/remember`; the mounted router is
`POST /memory/save` with `MemorySaveIn {text, kind, salience}` (`admin/memory/api/memory.py:184`).
Code is truth — the UI calls `/memory/save` and checks `saved:false` honestly.

### P3 — Model registry (`soma-settings-models.ts`) — **PASS**

| Requirement | Evidence | Verdict |
|---|---|---|
| 5 Model Roles | `ROLE_ORDER` = chat/utility/embedding/vision/decision (`soma-settings-models.ts:139`) | PASS |
| Role labels Chat/Help/Memory/Vision/Decisions | `ROLE_LABELS` (`:123`) | PASS |
| **LIVE chip = role-bound** | `_isLive(id) = _usedFor(id).length > 0` (`:589`) — a LIVE chip is emitted only when `/llm/roles` binds that model id | PASS |
| Providers from API | `apiClient.get('/llm/providers')` (`:536`); 0 hardcoded vendor names in file | PASS |
| No "slot" wording | 0 user-facing "slot" strings | PASS |

Live roles (all 5 bound):
```json
{"chat_role":"3","utility_role":"3","embedding_role":"5","vision_role":"9","decision_role":"4"}
```
Model ids are strings on both sides (`ModelRow.id: string`, role values `"3"`), so `===` binding
compares are type-safe.

### P4 — Agent active chat model shows LIVE when chat_role bound — **FAIL → FIXED**

Before: `soma-chat.ts:3072` rendered `_modelLabel` as bare text — no LIVE state, no navigation.
UI-S-07 §3 control 18 requires the model chip to navigate to `/settings/models`, and priority
requires LIVE when `chat_role` is bound.

After:
- `_loadChatRoleBinding()` resolves `GET /llm/roles` → `chat_role` → `GET /llm/models` and keeps
  both `provider/name` and bare `name` label forms (the orchestrator emits
  `chat.turn_meta.model` as `f"{provider}/{name}"` — `admin/core/chat_orchestrator.py:1088`).
- `_modelIsChatRole` is true **only** when the turn model matches that binding.
- LIVE chip renders only under that condition; otherwise the label carries no chip and the tooltip
  says "not bound to chat role". No decorative green.
- The chip is an `<a href="/settings/models">` that routes through the established
  `soma-navigate` custom event (`main.ts:438`).

### P5 — Status indicator honesty — **PASS**

Indicator truth table:

| Indicator | Location | Green condition | Live observation | Honest? |
|---|---|---|---|---|
| Memory dot | `soma-chat.ts:1685` | `/memory/status`.state === `ok` (read_ok ∧ write_ok ∧ circuit≠open) | `state:"ok"` → green | **YES** |
| Brain dot | `soma-chat.ts:1598` | `/core/brain-connector` `connected ∧ circuit==='closed'` | connector-driven | **YES** |
| Sync dot | `soma-chat.ts:3040` | `_connectionStatus==='ok'` | WS-derived | **YES** |
| Chat model LIVE | `soma-chat.ts` `_modelIsChatRole` | turn model ∈ chat_role binding | role-resolution | **YES (this fix)** |
| Model card LIVE | `soma-settings-models.ts:589` | model id bound to ≥1 role | `/llm/roles` | **YES** |
| Model card "Key in Vault" | `:1005` | `provider.has_api_key` from API | `/llm/providers` | **YES** |
| Memory queue chip | `soma-chat.ts` | `_memoryQueued` = state≠ok | derived | **YES** |
| CTX % | `soma-chat.ts` `_contextFillPct` | only when `context_window > 0` | null → no % | **YES** |
| WM / LTM tiles | `soma-memory-view.ts` | never — always `—`/GATED | no count API | **YES** |
| Total Memories | `soma-memory-view.ts` | `response.total` else `—` | server `total` | **YES (fixed)** |

Fail-closed behaviour confirmed: every `catch` path sets `warn`/`—`/`queued`, never green and
never `0`.

### P6 — HARD DELETE env / URLs / placeholder secrets / fake states — **PASS (nothing to delete)**

Already clean on arrival. Sweeps returned zero hits for:
- `process.env` / `import.meta.env` / `VITE_` / `REACT_APP_` / `NODE_ENV`
- `localhost` / `127.0.0.1` / `0.0.0.0` / literal ports (only an explanatory comment in
  `api-client.ts:221` describing what a *non-compliant* client would do)
- `sk-…` / `Bearer …` / assigned api_key / password literals
- mock/fake/shim code (remaining "fake"/"mock" strings are comments documenting their removal)

`api-client.ts` uses relative `baseUrl: '/api/v2'` and httpOnly cookie auth — settings-chain
compliant. Form `placeholder="…"` attributes are input hints, not configured values.

---

## 2. Per-screen parity vs mockups

Route ground truth = `webui/src/main.ts`. Verdict: **PASS** = implemented & honest,
**PARTIAL** = mounted but missing named controls, **GATED** = honest disabled notice,
**N/A** = not in this deployment's IA.

| Mockup | Screen | Route → view | Verdict | Notes |
|---|---|---|---|---|
| UI-S-00 | Chrome / shell | (global, `main.ts`) | PASS | auth gate, publicPaths, honest disabled notices for `/reset-password` `/verify-email` |
| UI-S-04 | Memory | `/memory` → `soma-memory-view` | **PASS** (fixed) | list/recall/forget/remember/export + WM/LTM `—` tiles + `?turn=current` |
| UI-S-07 | Chat workspace | `/chat` `/` → `soma-chat` | **PASS** (fixed) | C2 readout + Open Memory link; model chip LIVE + nav |
| UI-S-29 | Login | `/login` → `soma-login` | PASS | |
| UI-S-30 | Register | `/register` → `soma-register` | PASS | |
| UI-S-31 | Forgot password | `/forgot-password` → `soma-forgot-password` | PASS | |
| UI-S-32 | MFA setup | `/mfa/setup` `/settings/mfa` → `soma-mfa-setup` | PASS | |
| UI-S-33 | Auth callback | `/auth/callback` → `soma-auth-callback` | PASS | |
| UI-S-34 | Personal profile | `/profile` → `soma-personal-profile` | PASS | |
| UI-S-35 | Platform profile | `/platform/profile` `/admin/profile` → `soma-platform-profile` | PASS | |
| UI-S-38 | Platform metrics | `/platform/metrics` → `platform-metrics-dashboard` | PASS | server targets not re-hardcoded client-side |
| UI-S-39 | Infrastructure | `/platform/infrastructure` → `soma-infrastructure-dashboard` | PASS | rate-limits live on same surface |
| UI-S-40 | Rate limits | `/platform/ratelimits` → infra dashboard tab | PASS | one surface (matches IA) |
| UI-S-41 | Integrations | `/platform/integrations` → `soma-integrations-dashboard` | PASS | key masked on read, write-only to Vault |
| UI-S-43 | Audit dashboard | `/platform/audit` `/audit` → `soma-audit-dashboard` | PASS | |
| UI-S-45 | Agent metrics | `/soma/dashboard` `/admin/metrics` → `soma-agent-metrics` | PARTIAL | "Charts placeholder" comment at `soma-agent-metrics.ts:214` — chart area not rendered; no fake numbers drawn |
| UI-S-46 | Voice chat | `/voice/chat` → `soma-voice-chat` | PASS | |
| UI-S-47 | Voice sessions | `/voice/sessions` → `soma-voice-sessions` | PASS | |
| UI-S-48 | Voice personas | `/voice/personas` → `soma-voice-personas` | PASS | |
| UI-S-49 | Multimodal settings | `/settings/multimodal` → `soma-multimodal-settings` | PASS | discloses server-hardcoded ceilings rather than inventing them |
| UI-S-51 | Settings — Models | `/settings/models` `/agent/models` `/platform/models` → `soma-settings-models` | **PASS** | 5 Model Roles, LIVE=role-bound, providers from API |
| UI-S-52 | Settings — Channels | `/settings/channels` → `soma-settings-channels` | PASS | |
| UI-S-56 | Settings — SomaBrain | `/settings/somabrain` → `soma-settings-somabrain` | PASS | |
| UI-S-23/24 | Roles / permissions | `/platform/roles` → `soma-admin-roles-list` | PASS | one screen + matrix pane (old URLs collapse) |
| — | API keys | `/platform/api-keys` → `soma-admin-api-keys` | PASS | fabricated hardcoded key rows already removed (see file header) |
| — | Cognitive panel | `/cognitive` `/training` → `soma-cognitive-panel` | PASS | "Live SomaBrain state only — no hardcoded defaults" |
| — | Agent admin | `/admin/users` `/admin/agents` | PASS | `soma-user-detail` / entity views |
| — | Settings shell | `/settings` → `soma-settings` | PASS | |
| — | Workspace | `/workspace` | PASS | |
| UI-S-01..03/05/06 | Soul/Brain/Hands/Body/Governance | not standalone routes in this deployment | N/A | represented as agent settings / cognitive surfaces per AGENT.md §1.1 |
| UI-S-08..22, 25..28, 36/37, 42/44, 50/53/54/55/57 | detail/tier/marketplace/etc. | no route in `main.ts` | **N/A / deferred** | out of this deployment's IA; no stub screens mounted (fail-closed, correct) |
| UI-X-01..08 | Files/Tools/Browser/Editor/Debug/Capsule/Brain/Desktop | right-panel / capsule surfaces | PARTIAL | `soma-right-panel` + `soma-capsule-editor` present; per-surface depth varies |

Screens intentionally **not** mounted are better than fake ones: `main.ts` renders an honest
unavailable notice rather than a phantom product surface (e.g. `/reset-password`).

---

## 3. Gaps file:line (remaining, not fixed in this pass)

| Severity | Gap | Location |
|---|---|---|
| LOW | Chart area still a `/* Charts placeholder */` comment — no axes/series rendered (and no fake data) | `webui/src/views/soma-agent-metrics.ts:214` |
| LOW | UI-S-04 "layer wm\|ltm\|both" filter not implemented (mockup marks it `design`, not live) | `webui/src/views/soma-memory-view.ts` |
| LOW | UI-S-04 "Open record" drawer (UI-M-01) not implemented (mockup marks `design`) | `webui/src/views/soma-memory-view.ts` |
| LOW | UI-S-07 C2 wireframe shows `wm n · ltm n`; no count API exists so C2 does not render those two figures (correctly omitted rather than faked) | `webui/src/views/soma-chat.ts` |
| INFO | `GET /memory/` returns `total = len(memories)` (page length, capped by `limit`), not a corpus count — UI shows the server value as-is | `admin/memory/api/memory.py:158` |
| INFO | `/memory/status` can report `state:"ok"` while `brain_status:"critical"` — different lanes; memory dot is correct | `admin/memory/api/memory.py:96` |
| ENV | Host `node` binary broken (ada-url `libada.3.dylib` self-loop symlink). Used Bun for `tsc`. Outside repo scope. | `/usr/local/opt/ada-url/lib/` |

---

## 4. Fixes applied

1. `webui/src/views/soma-memory-view.ts`
   - MEMORY DASHBOARD tiles: WM / LTM / recall / list. WM & LTM render `—` + `GATED`.
   - `Run probe` button bound to `POST /memory/recall`.
   - `Remember…` form → `POST /memory/save` (`MemorySaveIn {text}`), checks `saved:false`.
   - `?turn=current` filter chip + `[clear]`.
   - Total Memories: server `total` only (removed `memories.length` invention).
   - Recall hits tracked separately; no longer clobbers list total.
   - Forget decrements a known total only; never invents one.
2. `webui/src/views/soma-chat.ts`
   - `_loadChatRoleBinding()` resolves `chat_role` → model label forms.
   - `_modelIsChatRole` gates the LIVE chip (green only when turn model is role-bound).
   - Model chip navigates to `/settings/models` via `soma-navigate` (UI-S-07 control 18).
   - C2 recall readout: `recall n` / `recall 0` (only after `chat.turn_meta`) / `recall —` on outage.
   - C2 `Open Memory` link → `/memory?turn=current` in all states.

No commits made (operator order).

---

## 5. Residual risk

- The C2 / model LIVE behaviour depends on `chat.turn_meta` and `/llm/roles` shapes documented
  above; if the orchestrator changes `turn_meta.model` to a bare id, the LIVE comparison needs
  the same label-form tolerance update.
- UI-S-04 `design`-status controls (layer filter, record drawer) remain unimplemented by design —
  they are not marked live in the mockup.
