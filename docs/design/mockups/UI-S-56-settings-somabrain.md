# UI-S-56-settings-somabrain — Settings — SomaBrain

**Settings — SomaBrain** — section **SomaBrain** inside the one Settings shell — route `/settings` (SomaBrain tab) or `/settings/somabrain`.
Chrome abbreviated (UI-S-00). Left section nav includes **SomaBrain**.
Audience: sysadmin / org_admin. **Every field below is bound to a live API.** Unavailable capabilities print a blocking reason — they are never drawn as editable controls.

**Field truth (live only):**

| Group | API | Fields (exact) |
|---|---|---|
| Connection | `GET/PUT /api/v2/core/settings/somabrain` | `url` → `SOMABRAIN_URL`, `namespace` → `SOMABRAIN_NAMESPACE`, `retention_days`, `sleep_interval`, `consolidation_enabled` |
| Brain reachability | `GET /api/v2/core/brain-connector` | connector health (circuit + ping) — **read-only status** |
| AgentIQ (per capsule, if operator drills in) | `GET/PUT /api/v2/core/agentiq/{capsule_id}` | knobs: `intelligence_level`, `autonomy_level`, `resource_budget`, `response_style`; **derived read-only** includes `tool_approval`, `require_hitl`, `egress_allowed` |
| Cognitive live (optional drawer) | `GET /api/v2/somabrain/cognitive/state/{agent_id}` + sleep status | same as UI-X-07 — **read-only on this screen** |
| Secrets | Vault | **not** on this API — pointer only, no token field |

**Not on this screen (no live write API — do not invent):** Kafka reward topic editor, Temporal worker restart, SFM URL (separate `memory` settings entity), OPA policy editor.

**Language law.** Memory home remains `/memory`. Secrets: "Set in Vault — not editable here." Material icons only.

## Purpose

Edit SomaBrain connection settings that the operator layer owns; show whether the connector is healthy; link to Memory and Cognitive surfaces.

```
┌─ UI-S-00 chrome (abbrev) ─────────────────────────────────────────────────────────────────────────┐
│ ☰ SOMA    Settings · SomaBrain              [Search…]                        [Save] [Cancel]      │
├──────────────┬───────────────────────────────────────────────────────────────────────────────────┤
│ SECTION NAV  │  SOMABR brain connection                                    ● / ○ connector      │
│  Agent       │                                                                                   │
│  Models      │  CONNECTION  (GET/PUT /api/v2/core/settings/somabrain)                           │
│  Voice       │  URL              [ ‹url from GET.url›                      ]  ← SOMABRAIN_URL  │
│  Interface   │  Namespace        [ ‹namespace›                             ]  ← SOMABRAIN_…     │
│  Tools       │  Retention (days) [ ‹retention_days› ]                                              │
│  Integrations│  Sleep interval   [ ‹sleep_interval› ]  (seconds — maps to settings field only)    │
│  SomaBrain●  │  Consolidation    [ ● enable ]  ← consolidation_enabled                          │
│  Agent admin │                                                                                   │
│  Connectivity│  STATUS  (GET /api/v2/core/brain-connector)  — read-only                          │
│  Advanced    │  connector ‹ok|degraded|unavailable› · circuit ‹state› · last ping ‹…›            │
│              │  [ Open /memory ]  ·  [ Open /cognitive ]                                        │
│              │                                                                                   │
│              │  NOT AVAILABLE AS FIELDS (no write API — honest note)                             │
│              │  "Memory token lives in Vault. Cognitive knobs are per-agent                      │
│              │   (/cognitive). Temporal host is deploy env, not this form."                      │
├──────────────┴───────────────────────────────────────────────────────────────────────────────────┤
│ status: ‹load/save› · PUT /api/v2/core/settings/somabrain · permission: settings:edit            │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

## Field table (API field)

| Human label | Control | Request/response field | Evidence |
|---|---|---|---|
| URL | text/url | `url` | `settings_v2.py` ENTITY `somabrain.url` |
| Namespace | text | `namespace` | same |
| Retention days | number | `retention_days` | same |
| Sleep interval | number | `sleep_interval` | same (seconds) |
| Consolidation | toggle | `consolidation_enabled` | same |
| Connector status | status row | `GET /core/brain-connector` | `health.py` `/brain-connector` |
| Memory link | button | route `/memory` | UI-S-04 |
| Cognitive link | button | route `/cognitive` | UI-X-07 |

Secrets: **no** password field on this form.

## Control map

| # | control | API | notes |
|---|---|---|---|
| 1 | section nav | — | Settings shell |
| 2 | five fields | PUT `settings/somabrain` | only keys in ENTITY_SPECS |
| 3 | status row | GET `brain-connector` | fail closed text on error |
| 4 | links | SPA routes | |
| 5 | Save | PUT | disabled without `settings:edit` |

## States

- **Loading.** Skeleton on five fields; no fake URL.
- **Save error.** "Couldn't save SomaBrain settings. ‹reason›"
- **Connector unavailable.** "SomaBrain unreachable. Chat continues; memory may queue."
- **Permission-denied.** "Requires settings edit permission."

**Modals.** None.

## Gaps (do not mock as editable)

| Desired control | Why absent | Next API needed |
|---|---|---|
| Memory HTTP token | Vault only | ops runbook / Vault UI |
| Temporal host | env deploy | settings entity if operator-owned later |
| Reward topic | not in somabrain ENTITY | add key or drop from mock |
| Live neuromod edit | cognitive API is per-agent panel | keep UI-X-07 / `/cognitive` |
