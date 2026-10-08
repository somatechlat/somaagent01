# UI-S-56-settings-somabrain — Settings — SomaBrain

**Settings — SomaBrain** — section **SomaBrain** inside the one Settings shell — route `/settings` (SomaBrain tab) or `/settings/somabrain`.
Chrome abbreviated (UI-S-00). Left section nav includes **SomaBrain**; tab active for sysadmin / org_admin.
Memory remains one home at `/memory` (UI-S-04). Right-rail **Brain** (UI-X-07) stays per-agent live state — this screen is **platform setup + operator knobs**.

**Field truth.** Connection fields bind settings entity `somabrain` (`admin/core/api/settings_v2.py`): `SOMABRAIN_URL`, `SOMABRAIN_NAMESPACE`. Secrets are Vault-only — UI never displays a full token; rotate via Vault path note. Health strip uses live connector/diagnostics only (`/api/v2/core/…` / brain health). Cognitive defaults bind existing settings keys only (no invented keys). Live agent gauges use `/api/v2/somabrain/cognitive/state/{agent_id}` and sleep status — same routes as UI-X-07. Temporal strip is present-but-disabled if `SA01_TEMPORAL_HOST` unset (blocking reason printed).

**Language law.** No Memory section here. Secrets: "Set / rotate in Vault — never shown in full."

**Design direction (Lit 3.x).** Dense, scannable operator panel; Material icons only (`neurology`, `memory`, `schedule`, `link`); amber for unavailable; no card-in-card; no emoji.

## Purpose

Configure SomaBrain connectivity, memory lane health, cognitive defaults, and optional live agent cognitive read-only controls for platform operators.

```
┌─ UI-S-00 chrome (abbrev) ─────────────────────────────────────────────────────────────────────────┐
│ ☰ SOMA    Settings · SomaBrain                    [Search settings…]        [Save] [Cancel]       │
├──────────────┬───────────────────────────────────────────────────────────────────────────────────┤
│ SECTION NAV  │  SOMABR brain + memory platform                                 ● online / warn   │
│  Agent       │                                                                                   │
│  Models      │  CONNECTION                                                                       │
│  Voice       │  SOMABRAIN_URL          [‹live URL›                         ]                     │
│  Interface   │  SOMABRAIN_NAMESPACE    [chat_history                      ]                     │
│  Tools       │  Memory HTTP token      [••••••••  set in Vault        ]  [ Test connection ]     │
│  Integrations│  Last check: ‹status · latency · memory_ok›                                       │
│  **SomaBrain●**│                                                                                 │
│  Connectivity│  MEMORY LANE (T-1)                                                                │
│  Advanced    │  remember · recall · forget   ·  durable-before-hop on  ·  breaker ‹state›         │
│              │  [ Open /memory dashboard ]                                                       │
│              │                                                                                   │
│              │  COGNITIVE DEFAULTS (platform)                                                    │
│              │  Confidence default     [0.5  ]                                                   │
│              │  Reward Kafka topic     [reward.events]                                           │
│              │  Sleep cycle (hours)    [6    ]  → SleepCycleWorkflow                             │
│              │  [ Save defaults ]                                                                │
│              │                                                                                   │
│              │  LIVE AGENT (optional)                                                            │
│              │  Agent [‹agent name› ▾]   neuromod gauges · sleep · last_sleep  (read-only)       │
│              │  [ Trigger sleep ] [ Reset adaptation ]  (approval-gated)                         │
│              │                                                                                   │
│              │  TEMPORAL                                                                          │
│              │  workers ‹Running|unavailable› · schedules ‹…›   or gated: "SA01_TEMPORAL_HOST     │
│              │  not set on this deployment."                                                     │
├──────────────┴───────────────────────────────────────────────────────────────────────────────────┤
│ status: ‹load/save› · secrets never shown full · rotate in Vault · permission: settings:edit     │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

## Field table (API field)

| Human label | Control | API field | Notes |
|---|---|---|---|
| SomaBrain URL | text | `SOMABRAIN_URL` | settings entity `somabrain` |
| Namespace | text | `SOMABRAIN_NAMESPACE` | settings entity `somabrain` |
| Memory HTTP token | password + rotate note | Vault secret | never full display |
| Test connection | button | live health | honest fail text |
| Confidence default | number | existing cognitive setting key only | no invented key |
| Reward topic | text | `SOMABRAIN_TOPIC_REWARD_EVENTS` | if present in settings |
| Sleep cycle hours | number | Temporal schedule setting | if present |
| Live agent | select | agent list | optional |
| Neuromod / sleep | gauges | `/somabrain/cognitive/*` | read-only here |

## Control map

| # | control | notes |
|---|---|---|
| 1 | section nav | Settings shell + SomaBrain tab |
| 2 | connection fields | PUT settings `somabrain` |
| 3 | Test connection | GET health; no fake latency |
| 4 | token row | Vault pointer only |
| 5 | memory lane status | real breaker / health |
| 6 | Open /memory | navigates UI-S-04 |
| 7 | cognitive defaults | existing keys only |
| 8 | live agent gauges | same API as UI-X-07 |
| 9 | Temporal strip | gated honest disabled |
| 10 | Save | settings write; fail-closed |

## States

- **Loading.** Skeleton rows; no invented URL.
- **Unavailable.** Amber: "SomaBrain unreachable. Chat continues; memory writes queue."
- **Error.** "Couldn't load SomaBrain settings. ‹reason›"
- **Permission-denied.** "Requires settings edit permission."
- **Temporal gated.** Blocking reason: host not configured.

**Modals.** None destructive. Token rotate is external Vault.
