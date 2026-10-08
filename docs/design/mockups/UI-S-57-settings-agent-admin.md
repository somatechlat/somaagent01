# UI-S-57-settings-agent-admin — Settings — Agent admin (tools & permissions)

**Settings — Agent admin** — operator surface for **what tools the agent may run** — route `/settings` (Agent admin tab) or `/settings/agent-admin`.
Audience: sysadmin / org_admin / agent_owner. Chrome abbreviated (UI-S-00).
Complements UI-S-55 (catalog enable + shared limits). **Every control on this mock has a live API.** Controls without a write API are listed under **Gaps** and are **not** drawn as editable.

**Field truth (live only):**

| Group | API | Exact fields |
|---|---|---|
| Tool catalog | `GET /api/v2/tools/catalog` · `PUT /api/v2/tools/catalog/{name}` | `name`, `description`, `category`, `enabled` |
| Tool schemas (info) | `GET /api/v2/tools` | `name`, `description`, `parameters` |
| Shared limits | `GET/PUT /api/v2/core/settings/agent` | `tool_max_iterations`, `tool_exec_timeout_s`, `tool_result_max_chars` (+ login rate keys — out of this section) |
| AgentIQ knobs | `GET/PUT /api/v2/core/agentiq/{capsule_id}` | **write:** `intelligence_level`, `autonomy_level`, `resource_budget`, `response_style` |
| AgentIQ derived (read-only) | same GET `derived` | `tool_approval`, `require_hitl`, `egress_allowed`, `temperature`, `max_tokens`, `model_tier`, … |
| Capsule identity | `GET/PATCH /api/v2/agents/{agent_id}/capsule` | `name`, `description`, `system_prompt`, `personality_traits`, `neuromodulator_baseline`, `learning_config` |
| Capsule select | `GET /api/v2/agents/` | list agents → pick one for IQ + capsule |

**Explicit Gaps (no HTTP write today — do not invent):**

| Desired | Model exists? | HTTP today |
|---|---|---|
| `tool_policy` 3-bucket editor | yes `Capsule.tool_policy` JSON | **no PUT** on agents API |
| `enabled_capabilities` checkboxes | yes M2M | **no PUT** on agents API |
| Direct edit of derived `tool_approval` / `egress_allowed` | derived only | **read-only** — change via **knobs** only |

This mock therefore administers **catalog enable, shared limits, AgentIQ knobs, derived view, and capsule prompt/personality** — the real Hands surface until a capsule-policy API exists.

**Design.** Dense admin table; Material icons; unlisted tools remain approval (backend law) — not a UI toggle.

## Purpose

Enable/disable tools, set shared tool limits, adjust AgentIQ knobs, and view effective derived autonomy (including tool_approval / require_hitl / egress).

```
┌─ UI-S-00 chrome (abbrev) ─────────────────────────────────────────────────────────────────────────┐
│ ☰ SOMA    Settings · Agent admin             [Search…]                        [Save] [Cancel]     │
├──────────────┬───────────────────────────────────────────────────────────────────────────────────┤
│ SECTION NAV  │  AGENT ADMIN — tools & autonomy                                                   │
│  Agent       │                                                                                   │
│  Models      │  ── TOOL CATALOG ──────────────────────────────────────────────────────────────    │
│  Voice       │  GET /api/v2/tools/catalog · PUT …/catalog/{name}                                │
│  Interface   │  search [____]                                                                   │
│  Tools       │  │ name           │ description          │ category │ enabled │                   │
│  Integrations│  │ file_read      │ …                  │ file     │ ●       │                   │
│  SomaBrain   │  │ file_write     │ …                  │ file     │ ●       │                   │
│  Agent admin●│  │ research_report│ …                  │ …        │ ●       │                   │
│  Connectivity│  (live catalog rows only — no invented tools)                                     │
│  Advanced    │                                                                                   │
│              │  ── SHARED TOOL LIMITS ────────────────────────────────────────────────────────    │
│              │  GET/PUT /api/v2/core/settings/agent                                              │
│              │  Max iterations   [ tool_max_iterations ]                                        │
│              │  Exec timeout (s) [ tool_exec_timeout_s ]                                        │
│              │  Result max chars [ tool_result_max_chars ]                                      │
│              │                                                                                   │
│              │  ── AGENTIQ (per capsule) ─────────────────────────────────────────────────────    │
│              │  Capsule/Agent [ ‹GET /agents› ▾ ]   capsule_id ‹…›                              │
│              │  knobs (PUT /api/v2/core/agentiq/{capsule_id}):                                   │
│              │    intelligence_level [n]  autonomy_level [n]                                     │
│              │    resource_budget [x]     response_style [balanced▾]                             │
│              │  derived (read-only from GET.derived):                                            │
│              │    tool_approval ‹none|dangerous|all› · require_hitl ‹true|false›                 │
│              │    egress_allowed ‹…› · model_tier ‹…› · temperature ‹…›                         │
│              │  [ Save IQ ]  (knobs only — derived is display)                                   │
│              │                                                                                   │
│              │  ── CAPSULE IDENTITY (optional) ──────────────────────────────────────────────    │
│              │  GET/PATCH /api/v2/agents/{agent_id}/capsule                                      │
│              │  name · description · system_prompt · personality_traits (JSON)                  │
│              │  [ Save capsule ]                                                                │
│              │                                                                                   │
│              │  GAPS (no API — not editable here)                                                │
│              │  tool_policy buckets · enabled_capabilities — model fields without HTTP PUT.     │
│              │  [ Open Tools tab (UI-S-55) ] for catalog enable only.                           │
├──────────────┴───────────────────────────────────────────────────────────────────────────────────┤
│ status: ‹load/save› · permission: tool_configure / agent:configure_personality                   │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

## Field table (API field)

| Human label | Control | API |
|---|---|---|
| Tool enabled | toggle | PUT catalog `{name}` body `enabled` |
| Max iterations | number | PUT settings `agent` `tool_max_iterations` |
| Exec timeout | number | `tool_exec_timeout_s` |
| Result max chars | number | `tool_result_max_chars` |
| intelligence_level | number | PUT agentiq knobs |
| autonomy_level | number | PUT agentiq knobs |
| resource_budget | number | PUT agentiq knobs |
| response_style | select | PUT agentiq knobs (`response_styles` list) |
| tool_approval / require_hitl / egress | read-only chips | GET agentiq `derived` |
| capsule name / prompt / personality | text/JSON | PATCH agents capsule |

## Control map

| # | control | API |
|---|---|---|
| 1 | catalog table + enable | tools catalog |
| 2 | three limit numbers | settings `agent` |
| 3 | agent select | GET agents |
| 4 | four IQ knobs | PUT agentiq |
| 5 | derived chips | GET agentiq (no write) |
| 6 | capsule identity fields | PATCH capsule |
| 7 | gaps note | honest — no fake buckets |

## States

- **Loading.** Skeleton tables; catalog empty → "No tools in the catalog yet."
- **IQ save error.** "Couldn't save AgentIQ knobs. ‹reason›"
- **Permission-denied.** "Requires tool_configure / agent:configure_personality."
- **No capsule.** "Selected agent has no capsule."

**Modals.** Save confirm when response_style invalid (enum from `response_styles`).

## Sync note vs older 3-bucket mock

The three-bucket `tool_policy` editor is **specified in PARITY-002 C-5 / UI-S-03 Hands** but **has no HTTP write** on the agents capsule API. Until that endpoint exists, UI-S-57 must not pretend to save buckets. Catalog enable + IQ knobs + shared limits are the complete **real** admin surface today.
