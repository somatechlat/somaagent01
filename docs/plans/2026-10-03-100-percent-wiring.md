# 100% Wiring Plan — Agent + SomaBrain + SomaFractalMemory + Temporal

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Use 100% of SomaBrain, 100% of SFM and 100% of the agent's own features — every real capability wired end to end, Temporal owning the full async cycle, and a degradation doctrine that never lies about what worked.

**Authority (read first, non-negotiable):**
- `docs/standards/SOMA-STD-CODING-001.md` — VIBE law: no stubs, no mocks, no shims, no TODOs, no hardcoded values, fail-closed, documentation is truth
- `docs/architecture/SOMA-ARCH-INVARIANTS-001.md` — T-1…T-8, defects #6–#17, definition of done
- `docs/iso/SOMA-TRIAD-ARCH-001.md` — findings F-01…F-12, remediation R-01…R-10
- `docs/plans/2026-10-03-triad-full-integration.md` — the seam plan already in flight

**Measured 2026-10-03.** Every claim below was verified in the tree. Where docs disagree with code, **code wins**.

---

## 0. The measured truth

### What is real and wired
- T-1 lane: `ChatOrchestrator → MemoryGateway → SomaBrainAdapter → POST /memory/* → SomaBrain → POST /memories* → SFM`. Agent has **no SFM client**.
- gRPC transport package on the brain side (7 RPCs) — implemented, tested, **never started in the running process**.
- SFM: memory CRUD + search (Postgres + Milvus), graph link/neighbors/path, health, bearer auth, tenant scoping, soft delete, precomputed-embedding seam.
- Brain: memory WM/LTM, context builder + planner, adaptation engine + tau annealing, cognitive `eval_step`, sleep FSM, constitution engine + OPA bridge, oak option manager, predictors, outbox.
- Agent: 12-phase orchestrator, tool loop (tools DO reach `acompletion`), streaming to UI, AgentIQ derivation, capsule system, LLM layer with timeouts/retries.

### What is broken or lying (the reason "100%" is not true today)

| # | Defect | Where | Class |
|---|---|---|---|
| B1 | Agent calls **7 phantom paths** that 404 (`/memory/recent`, `/memory/pending`, `/weights`, `/context/build`, `/learning/reward`, `/cognitive/params/{id}`, `/admin/migrate/*`) | `admin/core/somabrain_client.py` | contract break |
| B2 | Field mismatches on real routes — `confidence`/`suggested_tools` never returned; `/cognitive/act` payload wrong | `chat_orchestrator.py:443-458`, `somabrain_client.py` | silent no-op |
| B3 | `update_neuromodulators` **does not exist** in the brain | agent call sites | phantom |
| B4 | **Two neuromod stores** — `/neuromod/adjust` does not affect `/cognitive/act` | `somabrain/api/endpoints/neuromod.py:31-41` vs `bootstrap/singletons.py` | broken wiring |
| B5 | `POST/PUT /api/oak/option/*` **always 500** (dict vs attribute) | `oak.py:73-77,99-103` | bug |
| B6 | `POST /api/sleep/transition` **always 500** (missing method) | `sleep.py:240` | bug |
| B7 | health path `TypeError` — `map_cb_to_sleep` 1 arg vs 3 | `api/endpoints/health.py:145` | bug |
| B8 | `prepare_bulk_items` `NameError` — `payload` before bind | `somabrain/memory/remember.py:272` | bug |
| B9 | gRPC Brain service never started | `transport/serve.py:461` test-only | undeployed |
| B10 | Temporal **workers never started**; workflow starters are live | `infra/aaas/aaas/supervisord.conf` | dead lane |
| B11 | `OutboxMessage` is a **dead letter** — no publisher exists | `admin/core/signals.py:158-189` | dead lane |
| B12 | conversation.inbound payload contract mismatch (`conversation_id`/`content` vs `session_id`/`message`) | `signals.py:179-184` vs `conversation_worker/main.py:175` | broken contract |
| B13 | `ProcessMessageUseCase` bypasses the seam, **swallows errors** | `process_message.py:250,280,310` | data loss |
| B14 | Agent WAL is **after-failure**, not durable-before-hop → **T-6 violated** | `chat_orchestrator.py:1060-1086` | invariant break |
| B15 | `_MEMORY_STORES` synthesizes 2 failed acks vs 1 real → **double-queue** | `chat_orchestrator.py:77,1063-1066` | bug |
| B16 | `MemoryGateway` — hottest path — has **no circuit breaker** | `memory_gateway.py` | degradation gap |
| B17 | SFM degraded recall returns `[]` — agent cannot tell "no history" from "SFM down" | `somabrain/memory/hybrid.py:213-219` | fail-open |
| B18 | Two replay authorities: `PendingMemory`+`sync_memories` vs Kafka WAL | ~~`admin/core/models/zdl.py`, `degraded_memory_queue.py`~~ **deleted** | fixed — `memory.wal` only |
| B19 | SFM `k_hop` accepted and **ignored** (always 1-hop) | `somafractalmemory/api/routers/graph.py:78,96-98` | lying API |
| B20 | SFM `memory_type="belief"` accepted but not modelled — invisible to stats | `schemas.py:33` vs `models.py:23-27` | contract break |
| B21 | SFM `importance` always 0, and fallback ranking orders by it | `services.py:217-224,478` | dead field |
| B22 | SFM precomputed embedding **lost** if Milvus down at write | `services.py:258-262` | data loss |
| B23 | Unauthenticated: constitution **load**, OPA **policy write**, features, calibration | `v1.py:116-148` | security |
| B24 | `require_admin_auth` == `require_auth` — every token gets `admin:read` | `core/security/legacy_auth.py:181-219` | security |
| B25 | Django `Message` rows never written — REST history empty | `admin/chat/` | data loss |
| B26 | `services/common/api_key_store.py` is an in-memory **test double in production** | `services/gateway/providers.py:70-74` | test double |
| B27 | `_get_fallback_catalog()` fabricates 5 models | `admin/core/model_router.py:217-260` | fake data |
| B28 | `Capsule.chat_model` written and never read | `admin/core/models/core.py:201` | dead config |
| B29 | Settings-only **ghosts** in SFM: hybrid, decay, pruning, importance, JWT, OPA, CB, batch, rate-limit, CORS | `somafractalmemory/settings/infra.py` | claimed-but-absent |
| B30 | `optimize_hyperparameters` fake; `transfer_parameters` no-op | `somabrain/learning/adaptation/engine.py:519-530` | stub |

---

## 1. Phase A — Make the contracts true

Nothing else is worth wiring until the two sides agree.

### A1 — Kill the phantom agent→brain calls (B1, B3)
**Files:** `admin/core/somabrain_client.py`, `admin/agents/services/somabrain_integration.py`, `admin/somabrain/api_router.py`, `admin/core/api/migrate.py`
**TDD:** a test asserting every URL the agent builds exists in `somabrain/api/v1.py`'s router table.
**Change:** delete `get_recent`, `get_pending_count`, `get_weights`, `build_context`, `publish_reward` (HTTP form), `update_cognitive_params`, `migrate_export/import`, `update_opa_policy` wrong path — or route them to the route that actually exists. `publish_reward` must go to **Kafka** (`RewardEvent` → `LearnerService`), not HTTP.
**Commit:** `fix(brain-client): no call to a route that does not exist`

### A2 — Fix the field contracts (B2, B4)
**Files:** `admin/core/chat_orchestrator.py:443-458`, `admin/core/somabrain_client.py`, `somabrain/api/endpoints/neuromod.py`, `somabrain/bootstrap/singletons.py`
**Change:**
- `/context/evaluate` handler returns the shape `EvaluateResponse` declares (`api/schemas/context.py:34-44`) — or the agent reads only what is returned. One truth.
- `/cognitive/act` accepts the fields the agent sends, or the agent sends `task/top_k/universe`.
- **One neuromod store.** `/neuromod/adjust` and `/cognitive/act` must share `get_neuromodulators()`. Delete the duplicate registry.
**Commit:** `fix(brain): one neuromodulator store, one evaluate shape`

### A3 — Fix the four brain bugs (B5, B6, B7, B8)
- `oak.py:73-77,99-103` — read the dict keys `create_option` returns (or return the model). 
- `sleep.py:240` — implement `SleepStateManager.transition` or route to `compute_parameters`+`can_transition`.
- `api/endpoints/health.py:145` — pass the 3 args `map_cb_to_sleep` requires.
- `memory/remember.py:272` — bind `payload` before use.
**Commit:** `fix(brain): oak, sleep-transition, health and bulk-item paths work`

### A4 — SFM contract fixes (B19, B20, B21)
- `graph.py:78,96-98` — honour `k_hop` in `get_neighbors`, or reject it. Never accept and ignore.
- `models.py` — add `belief` to `MemoryType` choices (the seam already sends it), or reject it at the API.
- Write `importance` on store (from the seam's `salience`) so fallback ranking is meaningful.
**Commit:** `fix(sfm): k_hop, belief and importance are real`

### A5 — SFM embedding durability (B22)
A write with a precomputed embedding must not drop the vector when Milvus is briefly down. Record to an outbox and replay — same T-6 shape the brain already uses.
**Commit:** `fix(sfm): a precomputed embedding is never dropped`

---

## 2. Phase B — Wire 100% of SomaBrain

Ordered by what unlocks the most capability.

### B1 — Start the gRPC/UDS service (B9)
**Files:** `somabrain` startup (`services/entry.py` or a `manage.py` command `serve_brain_grpc`), `infra/*/docker-compose.yml` volume `soma_run:/run/soma`
`add_brain_service` already binds the **same** `MemoryService` the HTTP routes use (`transport/serve.py:1-14`) — one write path, one read path. Start it in LOCAL mode on `/run/soma/brain.sock` (0600) and NET on TLS.
**Commit:** `feat(brain): the gRPC service runs in the process`

### B2 — Agent speaks BrainPort (TC-1…TC-3)
**Files:** `services/common/adapters/somabrain_adapter.py`
Bind by `SA01_DEPLOYMENT_MODE` via `resolve_binding` (`port.py:65-95`) — LOCAL → UDS, NET → TCP+TLS+Vault token. **No probe, no fallback.** Garbage mode raises `TransportConfigurationError`.
**Commit:** `feat(transport): the agent uses the brain's own binding`

### B3 — Batch + advanced recall
Wire `/memory/remember/batch` and the advanced recall fields (`min_score`, `scoring_mode`, `session_id`, `pin_results`, `chunk_*`). One round-trip for N writes; scored/sessioned/paged recall.
**Commit:** `feat(memory): batch writes and scored recall through the seam`

### B4 — Cognitive plane
Wire `/cognitive/plan/suggest`, `/cognitive/personality`, `/cognitive/micro/diag`, full sleep FSM (`light`/`freeze`/`util`/`policy` — the agent only sends `deep` today).
**Commit:** `feat(cognitive): plan, personality and the full sleep fsm`

### B5 — Constitution + OPA (and lock them down — B23)
Wire `version`/`validate`/`load` and OPA policy sync into the agent's permission path. **Add auth** to constitution write, OPA policy write, features, calibration.
**Commit:** `feat(policy): constitution and opa are wired and authenticated`

### B6 — Admin/ops surface
Memory admin (rebuild-ANN, outbox replay), brain settings modes, threads, calibration reliability, feature flags, deep health fields — feed the degradation signal.
**Commit:** `feat(ops): the brain control plane is reachable`

### B7 — Honest cleanup
Delete or implement: `optimize_hyperparameters` (fake), `transfer_parameters` (no-op), `predictors/` (dead HeatDiffusion), `math/appr.py`/`bridge.py`/`sinkhorn.py`, `memory/filtering.py` empty stub, `memory/backend.py` ABC with 0 implementers, `learning/rust_engine.py`, `outbox_clean.py` (duplicate of `outbox_replay.py`). Unify the three `SleepState` representations. Unify the two `cog.*.updates` wire schemas.
**Commit:** `refactor(brain): dead code and duplicate authorities are gone`

---

## 3. Phase C — Wire 100% of SFM

### C1 — Use what is real and unused
`GET /graph/path` (relational reasoning — "how are these related"), `GET /memories/search` (ops/tools), `/stats`, `/metrics`, `export_graph` (add a route), AuditLog read endpoint.
**Commit:** `feat(sfm): graph path, stats and audit are reachable`

### C2 — Implement-or-delete the ghosts (B29)
Hybrid search, decay, pruning, importance normalization, JWT, OPA, circuit breaker, batch upsert, rate limiting, CORS, similarity metric — **either implement or delete the settings**. Never ship a config knob with no reader.
**Commit:** `refactor(sfm): every setting has a reader or is gone`

---

## 4. Phase D — Temporal in the full cycle

### D1 — Start the workers (B10)
`infra/aaas/aaas/supervisord.conf` starts `conversation_worker.main` (Kafka) but never `temporal_worker`. Add both temporal workers **or** stop starting workflows from `POST /message` / `POST /a2a/execute`. Prefer: start them.
**Commit:** `feat(temporal): the workers that service the workflows run`

### D2 — Drain or delete the dead outbox (B11, B12)
`conversation_message` → `OutboxMessage(topic="conversation.inbound")` is a dead letter. Either implement the documented `publish_outbox` publisher **and** fix the payload contract (`session_id`/`message` vs `conversation_id`/`content`), or delete the signal→outbox path so it cannot look durable while being dead.
**Commit:** `fix(outbox): the conversation outbox is drained or gone`

### D3 — Seam the Temporal lane (B13)
`ProcessMessageUseCase` takes `MemoryGateway`, not `memory_client`. Delete `MemoryClientProtocol = Any`. Route `remember_text`/`recall`. Both worker call sites use `build_memory_gateway()`.
**Commit:** `fix(chat): the temporal lane writes through the seam`

### D4 — What Temporal should own
- **sleep/consolidation cycle** — schedule `trigger_sleep_cycle` (`chat_orchestrator.py:1245-1262`, method exists, CB-protected)
- **memory outbox replay orchestration**
- **long-running jobs** (`JobPlanner` rows are PENDING forever today)
- **multi-agent delegation** (`A2AWorkflow` — worker not started)
- **tool execution retries**
- **document ingest**
**Commit:** `feat(temporal): the async cycle is scheduled and owned`

---

## 5. Phase E — Degradation doctrine

### E1 — T-6 durable-before-hop (B14)
`remember_text` records to durable storage **before** the network hop; replay until `MemoryAck.ok`. Delete the post-failure block at `chat_orchestrator.py:1060-1086` once pre-hop durability exists. This is the invariant text: *"accepted into a durable outbox before the network hop"*.
**Commit:** `feat(memory): writes are accepted durably before the hop`

### E2 — One replay authority (B18)
Kafka WAL is the only replay authority. `PendingMemory`+`sync_memories` is deleted. The double-queue at `chat_orchestrator.py:1063-1066` is fixed (real ack list, not `_MEMORY_STORES`).
**Commit:** `refactor(memory): one replay authority`

### E3 — Circuit-break the seam (B16)
Wrap `MemoryGateway.remember_text`/`recall` in a breaker (the existing `"somabrain"` one, or a dedicated `"memory_gateway"`). Today the hottest calls are unprotected while cognitive calls are protected.
**Commit:** `feat(memory): the seam is under a circuit breaker`

### E4 — Honest degraded recall (B17)
SFM degraded recall must not return `[]` as if there were no history. Return a degraded flag on the recall response; the agent surfaces "long-term memory unavailable" instead of answering as if the user has none.
**Commit:** `feat(memory): degraded recall says so`

### E5 — Local buffer in front of Kafka
`DurablePublisher.publish` raises with nowhere to land. A broker blip loses the write. Give it a local durable buffer.
**Commit:** `feat(events): a kafka blip cannot lose a write`

### E6 — Degradation doctrine table (ship as docs/iso + code)
| Dependency | Behaviour |
|---|---|
| SomaBrain remember | durable-before-hop; `MemoryAck` means *accepted*; replay until ack |
| SomaBrain recall | typed degraded, never empty-list lie; turn continues with a visible marker |
| SFM from brain | writes queue-before-hop (already); recall carries a degraded flag |
| LLM | fail-closed to the user with the named `ErrorCode` — never invent content |
| Vault | hard fail-closed at process start — **keep, do not soften** |
| Postgres | fail-closed for identity; named `ErrorCode` for "session store unavailable" |
| Redis | fail-open (budgets already fall back) |
| Kafka | fail-closed + local durable buffer; never block the user turn |
| Milvus | out of agent hot path; health signal only |
| Temporal | owns long/scheduled/multi-step work; fail-closed at the API that starts a workflow |

---

## 6. Phase F — Agent 100% + proof

*(to be completed from the agent inventory)*

### F1 — Transcript (B25) — in flight
### F2 — Model catalog + Capsule.chat_model (B27, B28) — in flight
### F3 — api_key_store is a real store (B26)
### F4 — Remaining agent features
### F5 — Proof: `tests/e2e/test_triad_integration.py` green against real services
### F6 — CI guards: no phantom routes, no `def _stable_coord` outside the shared module, no `.remember(` outside the seam, no `unittest.mock` outside allow-list

---

## Invariants that may never be softened

1. **T-1** Agent → SomaBrain → SFM. The agent never holds an SFM client.
2. **T-6** durable-before-hop. Not after-failure.
3. **Fail-closed.** Missing credential raises. Never `or ""` / `or "dummy"`.
4. **Vault-only secrets.** Never written to `os.environ`. No shim, no alias.
5. **A control with no handler is a lie.** A setting with no reader is a lie. A route that is called and does not exist is a lie.
6. **No mocks in the proof path.**
7. **Do not rewrite** the algorithm trees (memory/learning/math/constitution/context/oak/predictors) — fix the seams around them.
8. **No Claude attribution** on any commit or PR.

---

## Definition of done

```bash
pytest tests/e2e/test_triad_integration.py -v                  # green, real services
grep -rn "def _stable_coord" . ../somabrain ../somafractalmemory   # one definition
grep -rn "_memory_client.remember\|_memory_client.recall" admin services  # zero
# every URL the agent builds exists in the brain router table
# every setting has a reader
docker compose -f infra/triad/docker-compose.yml ps            # all healthy, incl. temporal workers
```

One chat turn with a real Groq model: streams to the UI, writes transcript rows, is **durably accepted before the hop**, acked by brain and SFM, recalled into the next turn's memory lane — and when any dependency is down, the user is told the truth and the write is replayed, not lost.
