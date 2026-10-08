# SOMA-RPT-STATUS-001 — Full code review, wiring status & UI/UX plan

## Document Control

| Field | Value |
|---|---|
| Document Title | Full code review, wiring status & UI/UX continuation plan |
| Document Identifier | SOMA-RPT-STATUS-001 |
| Version | 1.0.0 |
| Date | 2026-10-08 |
| Status | Draft |
| Author | SomaTech Engineering |
| Approver | — |
| Classification | Internal |
| ISO Reference | ISO 9001:2015 — Quality Management Systems — Requirements |
| Next Review | 2027-01-08 |
| Related | `AGENT.md`, `docs/standards/SOMA-STD-CODING-001.md`, `docs/plans/SOMA-AGENT-HANDOFF-001.md`, `docs/plans/2026-10-03-100-percent-wiring.md`, `docs/iso/SOMA-01-DOCS-001.md`, `docs/design/SOMA-UI-IA-001.md` |
| Source of truth | Working tree at review time; code wins over docs |
| Audience | Engineering contributors, Human Operator, A2A peers |
| Scope | `somaAgent01` only (sibling `somabrain` / `somafractalmemory` marked UNVERIFIED where not opened) |

## Revision History

| Version | Date | Author | Description |
|---|---|---|---|
| 1.0.0 | 2026-10-08 | SomaTech Engineering | Initial issue. Brought under ISO document control. Four completed read-only audits plus ADV-1/ADV-2 adversarial waves; B1–B30 re-audit; Temporal/stack matrix; UI/UX continuation plan. |

---

> **Evidence rule (REQ-DOCS-011):** every claim cites `file:line` or is marked UNVERIFIED. Code wins over docs.
> **Review method:** UI open-items audit · wiring/Temporal/stack audit · ADV-1 (B1–B30 re-audit) · ADV-2 (UI honesty, cognitive coverage) · specialist stack review.
> **A2A:** `docs/plans/a2a/` — seat MiMoCode-somaAgent01; peer MiMoCode (somabrain). No product code authorized until Human Operator orders Wave 1.

---

## 1. Executive summary

**One sentence:** The memory lane (T-1) and durable-before-hop (T-6) are real and committed; Temporal has full workflow definitions but workers still cannot attach under AAAS compose; the cognitive control plane has dead routes under a live UI Save button; the UI is largely honest (no DEV_MODE/mocks) but missing turn controls, agent switcher, and thin top strip — that is the UI/UX continuation objective.

| Track | Verdict |
|---|---|
| Agent ↔ SomaBrain memory wiring (T-1) | **PASS** — single seam, no SFM client, no bypass HTTP |
| Durable-before-hop (T-6) + circuit breaker | **PASS** — committed at `f3c23136`+ |
| Temporal 100% for agent | **FAIL (effectively open)** — workers in supervisord but env-name mismatch; no Temporal in standalone |
| Full stack 100% | **4 live / 6 partial / 2 unused** (Kafka standalone empty, OPA/SpiceDB topology empty, OTel/MinIO unused) |
| Cognitive plane wiring | **FAIL** — phantom `SomaBrainClient` methods → HTTP 500 / silent skip |
| UI/UX honesty | **Mostly PASS** — 0 TODO/DEV_MODE/fake metrics; P0 gaps: turn controls, agent switcher, thin top |
| Docs (AGENT.md, plan B-list) | **Drift** — invents modules/files; several “fixed” claims stale |

**Adversarial counts:**
- **ADV-1 (B1–B30 / wiring):** 3 CRITICAL · 6 HIGH · 9 MEDIUM · 3 LOW
- **ADV-2 (UI honesty / cognitive):** 0 CRITICAL · 5 HIGH · 7 MEDIUM · 5 LOW

**ADV-2 must-fix (top):** cognitive panel structurally dead (`soma_agent_id` never written); "Read-Only" mode is a no-op (only `DGR` honored); memory/infra failures rendered as empty; `/settings/tools` and `/settings/workflows` fall through to chat; memory type filters dead (no `kind` in API).

---

## 2. Project documents (inventory)

### 2.1 Binding authority

| Doc | Role |
|---|---|
| `AGENT.md` | Agent knowledge base — **partially stale** (see §6 F12/F13) |
| `docs/standards/SOMA-STD-CODING-001.md` | VIBE law |
| `docs/standards/SOMA-RAPID-DEVELOPMENT-001.md` | Wave process + skeptics |
| `docs/plans/SOMA-AGENT-HANDOFF-001.md` | Rules 1–12, THE ONE PATH |
| `docs/architecture/SOMA-ARCH-INVARIANTS-001.md` | T-1…T-8 |
| `docs/plans/2026-10-03-100-percent-wiring.md` | Defect register B1–B30 + Phases A–F |
| `docs/plans/2026-10-04-RAPID-TRIAD-001.md` | Triad rapid plan |
| `docs/plans/SOMA-PM-PLAN-CHAT-COGNITION-001.md` | Chat + cognition PM plan |
| `docs/design/SOMA-UI-*` (15 docs + mockups) | UI IA/NAV/SPEC/BINDINGS — **IA-001 authoritative for mocks** |

### 2.2 UI design set (current)

`SOMA-UI-IA-001` (authoritative), `NAV-001`, `NAV-AUDIT-001`, `SPEC-001/002`, `BINDINGS-001`, `CATALOG-001`, `CHAT-WORKSPACE-001`, `PARITY-002`, `SKINS-001`, `TEMPLATE-001`, `MOCKUPS-001`, `IDREG-001`, `CHAT-UI-001` + `docs/design/mockups/` (UI-S-00…UI-X-08).

### 2.3 Coordination

- Shared A2A: `somabrain/docs/plans/a2a/{CLAIMS,INBOX,OUTBOX,LEDGER}.md` + `2026-10-05-COORDINATION-HANDOFF.md`
- Local A2A: `somaAgent01/docs/plans/a2a/*` (opened this session)
- **Partition (handshaked 2026-10-08):** this seat owns `somaAgent01` (webui, e2e, docs/design, wiring plan, R-15 adapter). Peer owns `somabrain/memory/*` + deploy.

---

## 3. Code status — what works

| Area | Status | Evidence |
|---|---|---|
| T-1 memory seam | **Fixed / live** | `services/common/memory_gateway.py` + `adapters/somabrain_adapter.py` — only `/memory/{remember,recall,forget}`; grep: no SFM client, no `_memory_client` |
| T-6 durable-before-hop | **Fixed** | `memory_gateway.py:178` accept before hop `:190`; post-failure `_MEMORY_STORES` gone |
| Circuit breaker on seam | **Fixed** | `memory_gateway.py:126` `"memory_gateway"` wraps remember/recall |
| Honest degraded recall (agent half) | **Fixed** | `MemoryRecallUnavailable` instead of `[]` (`:206-213`) |
| Temporal lane uses seam | **Fixed** | `process_message.py` takes `MemoryGateway`; workers `build_memory_gateway()` |
| Outbox publisher | **Fixed** | `publish_outbox` + `OutboxReplayWorkflow` |
| Conversation payload contract | **Fixed** | `signals.py` emits `session_id`/`message` |
| Chat UI WS contract | **Fixed** | `/ws/v2/chat/{agent_id}` verified |
| AgentIQ live from API | **Fixed** | UI gate history: `GET /core/agentiq` |
| B27/B28 model catalog / chat_model | **Fixed** | no `_get_fallback_catalog`; `Capsule.chat_model` read |

---

## 4. Code status — what is broken (must-fix)

### 4.1 CRITICAL (ADV-1)

| ID | Defect | Where |
|---|---|---|
| **F01** | Routes call nonexistent `SomaBrainClient` methods → `AttributeError` → HTTP 500 | `admin/somabrain/cognitive.py:300`, `core_brain.py:363,440`, `migrate.py:92,128`, `api_router.py:163`, `somabrain_integration.py:42,55,71` |
| **F02** | UI cognitive **Save params** targets F01 (dead control) | `webui/src/views/soma-cognitive-panel.ts:790` → `PATCH /somabrain/cognitive/params/{id}` |
| **F03** | Temporal env mismatch: compose exports `SA01_TEMPORAL_URI`; workers read `SA01_TEMPORAL_HOST` → workers refuse | `infra/aaas/aaas/docker-compose.yml:68` vs `temporal_worker.py:321`, `delegation_gateway/temporal_worker.py:72` |

### 4.2 HIGH (ADV-1 + wiring)

| ID | Defect | Where |
|---|---|---|
| F04 | `get_recent` phantom + `except Exception` → fake `SOMABRAIN_UNAVAILABLE` | `admin/somabrain/api_router.py:163,178-180` |
| F05 | `publish_reward` phantom; reward swallowed at debug | `services/gateway/consumers/chat.py:864,878` |
| F06 | Exported async wrappers over guaranteed `AttributeError` | `admin/agents/services/somabrain_integration.py:42,55,71` |
| F07 | Three Temporal host authorities; dead `settings.py` settings + lying comment | `services/gateway/settings.py:202-206` |
| F08 | `update_neuromodulators` drops tenant/persona | `admin/core/somabrain_client.py:296-305` |
| F09 | AGENT.md claims off-seam memory that is already on-seam | `AGENT.md:285` |
| — | Standalone has **no Temporal service** while registry claims it | `config/settings_registry.py:263` vs `infra/standalone/docker-compose.yml` |
| — | Standalone `kafka_bootstrap_servers: ""` → outbox/WAL nowhere to land | `config/settings_registry.py:248` |

### 4.3 UI honesty — ADV-2 HIGH/MEDIUM (selected)

| ID | SEV | Defect | Evidence |
|---|---|---|---|
| A2-F01 | HIGH | Cognitive panel reads `soma_agent_id` from storage; **no writer exists** — panel always "No agent selected" | `soma-cognitive-panel.ts:736,789`; grep `soma_agent_id` = readers only |
| A2-F02 | HIGH | Save/Sleep/Reset fall back to agent-less 404 paths; failures `console.error` only | `:789-790,809,830`; `cognitive.py:248,281,313,347` |
| A2-F03 | HIGH | Mode picker offers Read-Only; backend honors **only `DGR`** | `soma-chat.ts:1438,1441` vs `chat_orchestrator.py:194,475,875` |
| A2-F04 | HIGH | Welcome "Modules" → `/settings/tools` has no route → falls through to chat | `soma-chat.ts:2982`; `main.ts:415-417` |
| A2-F05 | HIGH | Memory load failure renders **"No Memories Found — Start chatting"** | `soma-memory-view.ts:717-721,630-641` |
| A2-F06 | MED | List API omits `kind` → all cards "untyped"; 4/5 filter chips dead | `admin/memory/api/memory.py:66-77,91-102` |
| A2-F07 | MED | Infra dashboard `error` state declared never set; failures read as "No … data" | `infra-dashboard-controller.ts:141+`; `soma-infrastructure-dashboard.ts:585` |
| A2-F08 | MED | SPEC-002 `/settings/workflows` promised; router removed; silent chat fallthrough | `SOMA-UI-SPEC-002.md:90,494`; `admin/api.py:186` |
| A2-F12 | MED | Non-idempotent `post`/`patch`/`delete` retried 3× → possible duplicate create/forget | `api-client.ts:56-123` |
| A2-F17 | LOW | `soma-welcome-dashboard` ships banned Memory hero card; never rendered | `components/soma-welcome-dashboard.ts:18` |

### 4.3b UI P0 open items (explore-5)

| # | Item | Evidence |
|---|---|---|
| U1 | **Chat turn controls unreachable** — `<soma-chat-topbar>` never rendered; no Pause/Stop/Reset | `soma-chat.ts:22,26,508,2223` |
| U2 | **No agent switcher** — auto-first agent; zero-agent dead end | `soma-chat.ts:1662-1666,2841,3144` |
| U3 | **Thin top strip missing** (IA-001 §2.1) | no header in `soma-chat.ts` |

### 4.3c Cognitive API coverage (ADV-2)

| SomaBrain endpoint | Called by agent | In UI | Status |
|---|---|---|---|
| `context_evaluate` / `context_feedback` / `plan_suggest` / `act` / threads / `brain_sleep_mode` / `update_neuromodulators` / `micro_diag` / persona | YES | No | Wired, invisible |
| `get_neuromodulators` / `get_adaptation_state` | YES | YES | ✅ full |
| `adaptation_reset` / `trigger_sleep_cycle` | YES | Button | ⚠️ broken without agent id (A2-F02) |
| `sleep_status` | YES | **No** (BINDINGS claims yes) | Doc/UI gap (A2-F16) |
| `/gateway/constitution` | Capsule create only | No | Unwired to UI |
| `/core/brain-connector` | YES | YES | ✅ |

### 4.4 Stack matrix (specialist)

| Component | Verdict |
|---|---|
| Temporal | **partial** — F03 blocks workers; standalone absent |
| Kafka | **partial** — standalone bootstrap empty |
| Redis | **live** |
| Milvus | **partial** (health-only in this repo; T-1 correct) |
| OPA | **partial** — unconfigured ⇒ pass-through |
| SpiceDB | **partial** — empty topology ⇒ gate narrow path unused |
| Vault | **live** (fail-closed — suite aborts without it) |
| Keycloak | **partial** (local login also exists — UNVERIFIED sole path) |
| Prometheus | **partial** — `/metrics` on workers; admin route removed |
| OTel | **unused** — no endpoint set; dual env names |
| MinIO | **unused** — zero production callers |
| LiteLLM | **live SDK** / proxy not deployed |

**Goal “100% stack”: 4 live · 6 partial · 2 unused.**

---

## 5. Temporal 100% — gap plan (Phase D)

**Already defined:** `ConversationWorkflow`, `SleepCycleWorkflow`, `JobAdvanceWorkflow`, `OutboxReplayWorkflow`, `A2AWorkflow` + schedules `soma-sleep-cycle|soma-job-advance|soma-outbox-replay`.

| Step | Action | Files |
|---|---|---|
| D1a | **One env key** — export `SA01_TEMPORAL_HOST` (or read `SA01_TEMPORAL_URI`) on both sides | `infra/aaas/aaas/docker-compose.yml:68`, workers |
| D1b | Add Temporal to standalone compose **or** remove registry claim | `infra/standalone/docker-compose.yml`, `config/settings_registry.py:263` |
| D1c | Delete dead `TEMPORAL_HOST`/`TEMPORAL_NAMESPACE` settings + lying comment | `services/gateway/settings.py:202-206` |
| D2 | Prove workers stay up (`docker compose ps`) — not source-grep | replace `test_temporal_owns_async_cycle.py` greps with behavior |
| D4a | Tool retries → Temporal activity `RetryPolicy` | `services/tool_executor/`, `litellm_client.py` |
| D4b | Document ingest → `IngestWorkflow` | `tools.py:360` |
| D4c | Collapse 3 inbound lanes (REST→Temporal, Kafka worker, WS) — Kafka publishes *into* ConversationWorkflow | `sessions.py`, `conversation_worker/main.py`, consumers |
| D4d | Per-turn learning/episodic `asyncio.create_task` → scheduled/child workflow | `chat_orchestrator.py:1556,1584,1777` |
| D5 | Ship degradation doctrine as `docs/iso/` doc (E6) | new ISO doc |

Hot chat path stays non-Temporal by design (`test_temporal_owns_async_cycle.py:22-26`) — tokens stream in-process; durability is the outbox/memory lane.

---

## 6. B1–B30 re-audit (in-repo only)

| Status | Defects |
|---|---|
| **FIXED (11)** | B11, B12, B13, B14, B15, B16, B18, B25, B27, B28 + E1/E2/E3/E5 confirmed |
| **PARTIAL/OPEN (5+)** | B1 morphed (F01), B2 soft defaults, B3 drops identity, B9 gRPC still never started, B10 workers cannot start (F03), B17 SFM half, B26 leftovers (F17/F18) |
| **UNVERIFIED (13)** | B4–B8, B19–B24, B29–B30 live in sibling repos — outside this seat |

---

## 7. UI/UX continuation plan (THE OBJECTIVE)

**Objective:** wire the whole agent to the whole SomaBrain, expose 100% cognitive features honestly, give Temporal visibility at 100% of agent async lifecycle, keep Lit 3.x + A0 chrome + THE ONE PATH.

### Phase 0 — Contract freeze (docs only, 0 code risk)

| Task | Files | Gate |
|---|---|---|
| P0.1 Mark every mock Live/Planned in CATALOG | `docs/design/SOMA-UI-CATALOG-001.md` | no silent 62-vs-28 drift |
| P0.2 BINDINGS: every click → real REST/WS | `SOMA-UI-BINDINGS-001.md` | zero invented routes |
| P0.3 Fix AGENT.md inventory (saas-*.ts, workflows/, core/) | `AGENT.md` | matches tree |

### Phase 1 — Close CRITICAL/HIGH backend lies (before new UI)

| Task | Files | Gate |
|---|---|---|
| P1.1 Fix or DELETE F01 routes + F02 Save path | `admin/somabrain/cognitive.py`, `core_brain.py`, `migrate.py`, `api_router.py`, `somabrain_integration.py` | `PATCH /somabrain/cognitive/params` 200 or 405 — never 500 AttributeError |
| P1.2 F05 reward → Kafka `RewardEvent` or delete control | `consumers/chat.py` | no `logger.debug` swallow |
| P1.3 F03/F07 one Temporal host authority | compose + workers + `settings.py` | workers stay up; `compose ps` green |
| P1.4 R-15 adapter `MemoryAck.from_brain_response` | `services/common/adapters/somabrain_adapter.py` (A2A claim held) | no hardcoded `ok=true` |
| P1.5 A2-F01/F02: write agent id into cognitive panel; disable controls when none | `soma-cognitive-panel.ts`, `soma-right-panel.ts`, chat | Save/Sleep/Reset never silent-404 |
| P1.6 A2-F03: enforce `RO`/`DEV` or delete from mode list | `soma-chat.ts`, `chat_orchestrator.py` | no no-op capability claim |

### Phase 2 — Chat workspace P0 UI

| Task | Files | Gate |
|---|---|---|
| P2.1 Render turn controls (Pause/Stop/Reset/Nudge) | `soma-chat.ts` topbar + handlers already present | U1 closed |
| P2.2 Agent switcher + zero-agent onboarding CTA | `soma-chat.ts` | multi-agent selectable |
| P2.3 Thin top strip (time · conn · notifications · project) | new chrome per IA-001 §2.1 | A0 parity |
| P2.4 C2 “Open Memory” from recall chip | `soma-chat.ts:2869` | → `/memory` |
| P2.5 Memory outage ≠ empty list (A2-F05) + infra error state (A2-F07) | `soma-memory-view.ts:717-721`, infra controller | `_loadFailed` banner pattern |
| P2.6 Honest routes: `/settings/tools` + `/settings/workflows` (A2-F04/F08) | `main.ts` | present-but-disabled notice (pattern at `:361-392`) |
| P2.7 Memory `kind` through API or drop filter chips (A2-F06) | `admin/memory/api/memory.py` | filters match real data |

### Phase 3 — Cognitive + Temporal surfaces

| Task | Files | Gate |
|---|---|---|
| P3.1 Cognitive panel only after P1.1 | `soma-cognitive-panel.ts` | every control green against real routes |
| P3.2 Temporal workflow surface on existing `/gateway` API | new view + `admin/gateway/api/gateway.py` (`describe`/`execute`/`terminate`) | list/run/fail visible; or document deliberate exclusion |
| P3.3 Sleep FSM depth (light/freeze/util/policy) — after brain B4 | chat dock + cognitive panel | matches live FSM |
| P3.4 Notifications centre (`/notifications` 4 endpoints) | new view | P1.9 |

### Phase 4 — Settings + long tail

| Task | Gate |
|---|---|
| P4.1 Reconcile Settings 8 tabs vs spec 7 (Connectivity) | NAV-001 |
| P4.2 First-run model gate when catalog empty | one-click → `/settings/models` |
| P4.3 Dead CTA `/settings/tools` | route exists or remove |
| P4.4 Uncovered routers: sessions/plugins/ratelimit/assets/embeddings/quality | screen or NAV exclusion |
| P4.5 Dead assets: `soma-welcome-dashboard`, orphan CSS/handlers | delete (Rule 9) |

### Phase 5 — Proof

| Task | Gate |
|---|---|
| P5.1 Behavioral tests replace source-grep proofs | F14/F15 |
| P5.2 E2E fails (not skips) when deps missing in CI proof mode | F16 |
| P5.3 Playwright human-like chat + memory on :20080 | green against live stack |
| P5.4 Definition of done (100% wiring plan §DoD) | triad e2e green incl. temporal workers |

### A0 chrome constraints (non-negotiable)

- Composer = hero · thin top · left-rail **Memory + Settings only**
- Memory **one home** `/memory` · Models **full-screen in Settings**
- Pause/Nudge under composer (after topbar lands)
- Lit 3.x only · no React/Alpine · no new WS route/orchestrator/memory client

---

## 8. Recommended execution order (when coding is authorized)

```
Wave 1 (backend truth):  P1.1 → P1.3 → P1.2 → P1.4 → P1.5 → P1.6   [ADV skeptic each landing]
Wave 2 (chat P0 UI):     P2.1 → P2.2 → P2.3 → P2.4 → P2.5 → P2.6 → P2.7
Wave 3 (cognitive/TL):   P3.1 → P3.2 → P3.3
Wave 4 (settings/tail):  P4.*
Wave 5 (proof):          P5.*  + live triad e2e
```

Every wave: **builder + adversarial skeptic in parallel** (operator directive 2026-10-06). Findings → `docs/plans/a2a/LEDGER.md` as ADV rows.

**Stop condition:** no product code until Human Operator orders Wave 1 (current state: report-only).

---

## 9. Proof assets already present

`tests/unit/test_degradation_doctrine.py`, `test_temporal_owns_async_cycle.py` (needs behavioral rewrite), `test_process_message_uses_seam.py`, `test_memory_one_path.py`, `tests/e2e/test_triad_integration.py` (skip-gated — strengthen).

---

## 10. Review wave log

| Agent | Result |
|---|---|
| explore UI open-items | delivered — §7 + §4.3 |
| explore wiring/Temporal | delivered — §4.4, §5 |
| ADV-1 B1–B30 | 3C/6H/9M/3L — §4.1–4.2, §6 |
| specialist stack | delivered — stack matrix, Phase D order |
| ADV-2 UI honesty | delivered — 0C/5H/7M/5L; folded into §4.3, §4.3c, Phase 1–2 |

---

*End of SOMA-RPT-STATUS-001 v1.0.0*
