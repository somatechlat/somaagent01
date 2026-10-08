# SOMA-PM-RAPID-WIRING-001 — Full wiring plan: SomaAgent01 → SomaBrain cognition + UI/UX

## Document Control

| Field | Value |
|---|---|
| Document Title | Full wiring plan: SomaAgent01 → SomaBrain cognition + UI/UX |
| Document Identifier | SOMA-PM-RAPID-WIRING-001 |
| Version | 1.0.0 |
| Date | 2026-10-08 |
| Status | Draft |
| Author | SomaTech Engineering |
| Approver | — |
| Classification | Internal |
| ISO Reference | ISO 9001:2015 — Quality Management Systems — Requirements |
| Next Review | 2027-01-08 |
| Related | `SOMA-RAPID-DEVELOPMENT-001`, `SOMA-STD-TRIAD-001`, `SOMA-STD-CODING-001`, `2026-10-03-100-percent-wiring`, `SOMA-PM-PLAN-CHAT-COGNITION-001`, `SOMA-RPT-STATUS-001`, `SOMA-UI-IA-001`, `SOMA-ARCH-INVARIANTS-001` |
| Source of truth | Four ECC explore sweeps 2026-10-08 + prior ADV waves |
| Audience | Operator, agent seats, A2A peers |
| Scope | `somaAgent01` primary; `somabrain` / `somafractalmemory` via A2A partition |

## Revision History

| Version | Date | Author | Description |
|---|---|---|---|
| 1.0.0 | 2026-10-08 | SomaTech Engineering | Initial issue. Merged RAPID W1–W4, wiring A–F, cognitive map, UI inventory into one wave sequence. Brought under ISO document control. |

---

## 0. Authority (obey in this order)

1. `SOMA-RAPID-DEVELOPMENT-001` (owner standing order; Rules 1–12; THE ONE PATH)
2. `SOMA-STD-CODING-001` (VIBE) · `SOMA-STD-TRIAD-001` (same rules all repos)
3. `SOMA-ARCH-INVARIANTS-001` (T-1…T-8)
4. `SOMA-RPT-STATUS-001` + `SOMA-AGENT-HANDOFF-001` (measured open defects)
5. `2026-10-03-100-percent-wiring` (B1–B30) · `SOMA-PM-PLAN-CHAT-COGNITION-001`
6. `SOMA-UI-IA-001` (authoritative IA) · `SOMA-UI-BINDINGS-001` · `SOMA-01-UIUX-001…005`
7. `AGENT.md` — **correct it**; do not obey over code/docs above

**Done means:** `bunx playwright test tests/e2e --grep-invert @debug` green on the live stack, plus `pytest tests/e2e/test_triad_integration.py -v` **zero skips**.

---

## 1. Definition of done — “fully wired to SomaBrain cognition + UI”

| # | Proof |
|---|---|
| 1 | Human suite green: login, stream, turn controls, settings URL repoint, model CRUD, AgentIQ save, role-honest settings, **codeword save→recall**, logout |
| 2 | Triad e2e green **no skips** |
| 3 | One path: one `_stable_coord`, zero off-seam remember/recall, every agent URL exists in brain router, both RAPID hardcode greps empty |
| 4 | **Cognition visible:** panel Save/Sleep/Reset hit real routes; neuromod changes a readout; sleep FSM returns ACTIVE; degraded recall says degraded |
| 5 | `sysadmin` chats *and* configures; two capsules different tools; compose healthy **incl. Temporal workers**; kill-brain drill = honest message + `memory.wal` replay |
| 6 | `check_docs.py` → 0 failing; no control without handler; no setting without reader |

---

## 2. Unified wave sequence (one skeleton: RAPID W1–W4 only)

Wiring Phases A–F, CHAT-COGNITION, and STATUS P-phases are **items inside** these waves — never parallel wave systems.

### Wave 1 — UNBLOCK (sequential; stop gate = codeword recall)

| # | Item | Seat | Gate |
|---|---|---|---|
| 1.1 | Boot unbrick (Optional import + validator) | agent | `import admin.api` in container |
| 1.2 | Settings resolver sync+async, no swallowed errors | agent | UI URL edit affects both clients |
| 1.3 | Shared agent↔brain credential (KV v2 merge+read-back); kill ENV token | joint | no 401 |
| 1.4 | Transport clean hostname; no DisallowedHost | infra | live 200 |
| 1.5 | Kill 10 phantom `SomaBrainClient` call sites (F01–F06); reward → Kafka only; register or delete `SOMABRAIN_TOPIC_REWARD_EVENTS` + `SOMABRAIN_USE_PLANNER` | agent + brain | PATCH cognitive params 200/405 never AttributeError |
| 1.6 | **R-14:** recall sends `embed_text(query)` top-level | agent | same-vector recall |
| 1.7 | Evaluate contract: one shape both sides; stop inventing `confidence=0.5` | joint | evaluate result used in turn |
| 1.8 | Cognitive panel: write `soma_agent_id`; **fix wrong state endpoint** (`/context/adaptation/state` → needs neuromod/sleep payload); disable controls when no agent | UI | panel non-empty on live stack |
| 1.9 | Adapter `MemoryAck.from_brain_response` | agent | no hardcoded ok=true |
| 1.10 | Temporal one host authority (`SA01_TEMPORAL_HOST`); workers up | agent/infra | `compose ps` workers Running |
| 1.11 | **STOP GATE:** save `CODEWORD-BLUE-FALCON-77` → new conversation → correct recall | e2e | Playwright green |

**Nothing in W2 starts before 1.11.**

### Wave 2 — UI does real work + cognition unlocks (parallel lanes open)

| # | Item | Seat |
|---|---|---|
| 2.1 | One role store (gate for role UI) | agent |
| 2.2 | Settings surface live-edit every URL/knob (W2.1) | UI |
| 2.3 | Models CRUD + key↔model both ways (W2.2) | UI |
| 2.4 | AgentIQ knobs server-derived only (W2.3) — **verify apply_neuromodulators or implement real apply** | UI+agent |
| 2.5 | Post-turn loop unlock: reward Kafka, plan_suggest, thread seed, set_personality (register settings or delete gates) | agent |
| 2.6 | Surfaces: plan/thread status in chat; act payload `task:` match | agent+UI |
| 2.7 | UI honesty: turn topbar **rendered**, agent switcher, memory `_loadFailed`, honest `/settings/tools`+`/settings/workflows`, memory `kind` | UI |
| 2.8 | Hardcode purge greps empty on every landing | all |

### Wave 3 — Chat perfection + full cognition UI

| # | Item | Seat |
|---|---|---|
| 3.1 | Stream latency, tool timeline, lane vocabulary (W3.1) | agent |
| 3.2 | Settings-by-role (W3.2) | UI |
| 3.3 | Zero dummy controls (W3.3) — kill unrendered handlers | UI |
| 3.4 | Thin top strip A0; C2 Open Memory chip | UI |
| 3.5 | Brain: batch recall, one neuromod store live, full sleep FSM client methods (light/freeze/util/policy), sleep_status real, micro_diag | brain seat |
| 3.6 | UI: sleep depth + last_sleep + memory_stats render; mode DGR-only | UI |
| 3.7 | SFM: k_hop/belief/importance/ghosts (sibling) | sfm seat |
| 3.8 | Temporal workflow surface on existing `/gateway` API | UI |

### Wave 4 — Capacity + 100% + hardening

| # | Item |
|---|---|
| 4.1 | Capsule-owned tools (W4.1) |
| 4.2 | Zero-trust one role store (W4.2) |
| 4.3 | Infra 100% or **explicit out-of-scope**: Temporal standalone, Kafka bootstrap, OPA, gRPC, MinIO/OTel honesty |
| 4.4 | Degradation doctrine E6 as ISO doc + kill-brain drill |
| 4.5 | Constitution/OPA/oak/calibration **or document out of scope** (single authority) |
| 4.6 | Notifications centre, first-run model gate, docs truth |
| 4.7 | CI guards F6: no phantom routes, no off-seam remember, check_docs 0 |

**Final gate:** full human suite + triad e2e zero-skip + Definition of Done §1 all true.

---

## 3. Cognitive coverage target (from explore map)

| Capability | Today | Target wave |
|---|---|---|
| context_evaluate | wired, payload dropped | W1 contract |
| context_feedback | wired | W2 surface |
| reward | triple-broken | W1 Kafka path |
| neuromod get/adjust | wired lossy / panel wrong endpoint | W1 panel, W2 adjust |
| act | payload mismatch | W2 |
| plan_suggest + threads create | gated off (missing settings) | W2 |
| sleep deep + Temporal | wired; workers blocked | W1 workers; W3 full FSM |
| sleep util/policy/status | absent/miswired | W3 |
| personality | gated off | W2 |
| micro_diag / persona | dead wrappers | W3–W4 |
| constitution / OPA / oak / calibration | no client | W4 or out-of-scope |
| connector health | wired ✅ | — |
| memory T-1 | wired ✅ | prove W1 |

**UI new screens (only if W4 keeps them):** Temporal workflows, notifications, constitution, threads/steps, sleep history, reward telemetry. **Fill existing first:** topbar, switcher, cognitive panel, memory honesty, settings routes.

---

## 4. Parallel lanes + ECC roster

| Lane | Agent | Owns |
|---|---|---|
| Agent seat | `soma-wiring-engineer` | seam, phantoms, Temporal, adapter |
| Cognitive | `soma-cognitive-engineer` | orchestrator cognition, settings gates |
| UI | `soma-ui-engineer` | webui Lit, A0, panel, chat controls |
| Temporal | `soma-temporal-ops` | env, workers, compose proof |
| Brain peer | `brain-memory-engineer` | somabrain/memory + routes |
| Skeptic | `soma-adversarial-skeptic` + `brain-adversarial-skeptic` | **every landing** |
| Docs | `triad-iso-docs` | ISO register |
| Infra | `soma-temporal-ops` + compose | W4.3 |

A2A: claim `docs/plans/a2a/CLAIMS.md` before edits; LEDGER every commit; peer owns `somabrain/memory/*`.

---

## 5. Gates (exact commands)

```bash
# stack
cd infra/standalone && docker compose up -d
# unit (fail-closed without Vault is correct)
DJANGO_SETTINGS_MODULE=services.gateway.settings pytest tests/unit -v
# W1 stop gate
bunx playwright test tests/e2e/test_human_chat_session.spec.js --grep "remembers through SomaBrain"
# W2
bunx playwright test tests/e2e/test_wave2_human_actions.spec.js
bunx playwright test tests/e2e/ui-model-key.spec.js
# W3
bunx playwright test tests/e2e/test_human_chat_session.spec.js
bunx playwright test tests/e2e/test_chat_context_memory.spec.js
# W4 / final
pytest tests/e2e/test_triad_integration.py -v   # zero skips in proof mode
docker compose ps                              # temporal workers Running
python3 scripts/check_docs.py                  # 0 failing
bunx playwright test tests/e2e --grep-invert @debug
```

Hardcode greps on every touched file (RAPID Rule 1) must return empty.

---

## 6. Risks / non-goals

**Risks:** skip-gated e2e (convert to fail-mode); sibling seat cadence; KV v2 wipe; F03 env; empty standalone Kafka; recall ranking shift after R-14; Wave-1 serial temptation.

**Non-goals:** no new WS/orchestrator/memory client/SFM-from-agent; no React/Alpine/FastAPI/SQLAlchemy/Qdrant; no algorithm-tree rewrites; hot chat stays non-Temporal; no skins; MinIO/OTel/LiteLLM-proxy **explicit out of scope unless Operator orders**; no AI attribution on commits.

---

## 7. Recommended immediate order (Operator “GO” ready)

1. **W1.5 + W1.8 cluster** — phantoms + panel endpoint + agent id (highest user-visible leverage, ~hours)
2. **W1.10 Temporal env** — unlocks async honesty
3. **W1.6 R-14** if not already live
4. **W1.3 credential** if 401 still present
5. **W1.11 codeword gate**
6. Then open W2 parallel lanes (UI + settings unlock + role store)

**Skeptic on every landing.** Peer ACK already on agent roster merge.

---

*End of SOMA-PM-RAPID-WIRING-001 v1.0.0*
