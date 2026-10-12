# RAPID-DATA-REMEDIATION-001 — Database · Simplification · Performance

## Document Control

| Field | Value |
|---|---|
| Document Title | RAPID-DATA-REMEDIATION-001 — Database · Simplification · Performance |
| Document Identifier | SOMA-PM-RAPID-DATA-REMEDIATION-001 |
| Version | 1.0.0 |
| Date | 2026-10-09 |
| Status | Draft |
| Classification | Internal |
| Author | SomaTech Engineering |
| Approver | Operator (Human) |
| ISO Reference | ISO 9001:2015 — Quality Management Systems — Requirements |
| Next Review | 2027-01-09 |
| Related | `docs/standards/SOMA-RAPID-DEVELOPMENT-001.md` · `docs/standards/SOMA-STD-CODING-001.md` · `docs/standards/SOMA-STD-TRIAD-001.md` |
| Coordination | `docs/plans/a2a/` CLAIMS · INBOX · OUTBOX · LEDGER |
| Audience | All agents on the Soma triad |

## Revision History

| Version | Date | Author | Description |
|---|---|---|---|
| 1.0.0 | 2026-10-09 | SomaTech Engineering | Initial issue from the three-way audit (database · simplification · performance). |

---

## 0. Authority and non-negotiables

These are load-bearing. Every line of work in this plan obeys them.

| # | Rule | Source |
|---|---|---|
| R1 | **NO SHIMS. NO FAKES. NO MOCKS. NO STUBS. NO PLACEHOLDERS. NO TODOs.** Real code only. | CLAUDE.md LAW · VIBE · T-8 |
| R2 | **NO HARDCODED VALUES** — a default IS a hardcoded value. Env is topology only. | RAPID Rule 1 · R-VAL-04 |
| R3 | **ONE SETTINGS CHAIN:** Capsule → AgentSetting → InfrastructureConfig → SettingsModel → RAISE. | RAPID Rule 3 |
| R4 | **SECRETS: VAULT ONLY.** KV v2 read→merge→write→read-back. Never a file. | RAPID Rule 5 |
| R5 | **FAIL-CLOSED.** Missing required value = refusal naming the setting. | RAPID Rule 6 |
| R6 | **NEVER WEAKEN A GATE TO PASS A TEST.** | RAPID Rule 7 |
| R7 | **T-1 MEMORY SEAM:** only `MemoryGateway` → `SomaBrainAdapter`. Never an SFM client. | TRIAD T-1 |
| R8 | **DELETE, DO NOT BACK UP.** No compatibility aliases. | RAPID Rule 9 |
| R9 | **Done = human Playwright green** on real services — not skip-gated, not mocked. | RAPID Done definition |
| R10 | **A2A is mandatory.** Claim before large edit. Log every commit. Never delete peers' entries. | Global rules |

**Stack lock:** Django Ninja · Django ORM · Lit 3.x · Milvus (via SomaBrain) · Temporal · Vault. No React/Alpine/FastAPI/SQLAlchemy/Qdrant.

---

## 1. Problem statement (measured, not assumed)

Three independent audits of `somaAgent01` on 2026-10-09 found **11 critical / 20 high / 29 medium** defects concentrated in four places:

1. **Data integrity** — auth-hash columns with no UNIQUE and no index; chat tables are a soft-reference island (no FK, no cascade); `Message.content` was dropped and re-added across migrations with no backfill; zero `CheckConstraint`s in the entire schema; `IdempotencyRecord.check_and_set` is racy.
2. **Hot-path latency** — N+1 on the conversation list (one `Message` query per row); every authenticated request writes `last_seen_at`; no Postgres connection reuse; sequential SomaBrain writes per turn.
3. **Drift-prone duplication** — API-key minting copied in two apps (already bug-drifted); three live response envelopes; health probes copied 3×; `process_turn`/`stream_turn` are 800 LOC twins; 88 settings names defined in 2–3 modules.
4. **Missing schema enforcement** — unbounded `rollout_percentage` / `Job.priority`; "one active Constitution" is help_text only; money stored as `FloatField`; `wal_timestamp` is a float.

The bridges app, ZDL outbox family, and AuditLog show the team **can** design a schema correctly. The debt is concentrated, therefore fixable.

---

## 2. Goal

> Every table has correct types, uniqueness, and indexes. Every hot path is single-digit-ms. Every contract has one implementation. Proven by `tests/e2e/test_human_chat_session.spec.js` green in the UI, covering chatting, changing settings, creating models, and every user action.

---

## 3. Architecture under remediation

```
browser → WS /ws/v2/chat/{capsule_id} → ChatConsumer
        → ChatOrchestrator (process_turn | stream_turn)
        → MemoryGateway → SomaBrainAdapter → SomaBrain → somafractalmemory (Milvus)
        → Postgres (Django ORM) transcript
        → Temporal (async)
```

One lane only. T-1 seam untouched. This plan **never** adds a second memory client.

---

## 4. THE RAPID PLAN — waves

### Wave 0 — P0 data integrity *(must land first, no parallelism on these files)*

| # | Task | Finding | Owner | Files | Gate |
|---|---|---|---|---|---|
| W0.1 | `ApiKey.key_hash` → `unique=True` + index. Dedupe first. | DB-CRIT-1 | somaAgent01 | `admin/platform/models/profiles.py` + migration | Auth lookup is an index scan; duplicate hashes rejected by DB |
| W0.2 | `UserSession.refresh_token_hash` → `unique=True` + partial index | DB-HIGH-8 | somaAgent01 | `admin/platform/models/profiles.py` + migration | Session revoke is an index scan |
| W0.3 | Atomic `IdempotencyRecord.check_and_set` (`transaction.atomic` + `select_for_update`) | DB-CRIT-5 | somaAgent01 | `admin/core/models/zdl.py` | Concurrent double-submit yields one `is_new=True` |
| W0.4 | Backfill `Message.content` for the `chat/0002`→`chat/0004` window from WAL/SomaBrain | DB-CRIT-3 | somaAgent01 + somabrain (recall assist) | data migration | Zero rows with `content=''` AND `coordinate<>''` |
| W0.5 | CHECK constraints: `rollout_percentage` 0–100, `Capsule.status` enum, `Job.priority` bounds, partial unique one-active-`Constitution` | DB-CRIT-4 | somaAgent01 | `admin/core/models/*` + migration | Raw insert of `-999` / `"banana"` rejected by DB |
| W0.6 | Fail-first in MFA setup (remove dead QR + backup-code computation) | SIMP-02 | somaAgent01 | `admin/auth/mfa.py` | `ServiceUnavailableError` raised before any CPU work |

**Wave 0 exit:** migrations apply clean on empty and on populated DB; `pytest tests/unit` green; no `MultipleObjectsReturned` possible on auth.

---

### Wave 1 — hot-path performance *(parallel, non-colliding files)*

| # | Task | Finding | Owner | Files | Gate |
|---|---|---|---|---|---|
| W1.1 | Kill conversation-list N+1 (`Subquery`/`Exists` last-message) | PERF-1 / DB-HIGH-2 | somaAgent01 | `admin/chat/api/chat.py` | `assertNumQueries` ≤ 3 on `list_conversations` |
| W1.2 | `CONN_MAX_AGE` + `CONN_HEALTH_CHECKS` in `DATABASES` | PERF-3 / DB-HIGH-1 | somaAgent01 | `config/settings.py` | `pg_stat_activity` connection count stable under load |
| W1.3 | Throttle `last_seen_at` slide (≤ 1 write / 60s / session) | PERF-2 | somaAgent01 | `admin/common/auth.py` | `pg_stat_statements` shows UPDATE count −10× |
| W1.4 | Composite index `conversations (user_id, tenant_id, status, updated_at)` | PERF-4 | somaAgent01 | `admin/chat/models.py` + migration | `EXPLAIN ANALYZE` = Index Scan, no Sort |
| W1.5 | `asyncio.gather` the two `_remember_via_gateway` writes | PERF-6 | somaAgent01 | `admin/core/chat_orchestrator.py` | `_store_turn` wall time ~2× reduction |
| W1.6 | Cache `AgentSetting` resolution (TTL + invalidate on save) | PERF-5 | somaAgent01 | `admin/core/helpers/capsule_settings.py` | ≤ 1 `AgentSetting` query per chat turn after warm |
| W1.7 | `GZipMiddleware` for API JSON | PERF-8 | somaAgent01 | `config/settings.py` | `curl --compressed` size −60–80% on list endpoints |
| W1.8 | Bulk settings save (`bulk_update`/`bulk_create`) | PERF-7 | somaAgent01 | `admin/core/api/settings_v2.py` | N-key save = 2–3 queries, not 2N |

**Wave 1 exit:** conversation list p95 in single-digit ms at 20 rows; no per-request DB write on the auth path.

---

### Wave 2 — one contract per concern *(parallel by concern)*

| # | Task | Finding | Owner | Files | Gate |
|---|---|---|---|---|---|
| W2.1 | One `mint_api_key()` + one `ApiKeyOut` + one authz resource name | SIMP-01 | somaAgent01 | new `admin/common/api_keys.py`; `admin/gateway/api/gateway.py`; `admin/platform/api/settings.py` | Both routes call one function; key-format change is one edit |
| W2.2 | One success/error envelope (`api_response`/`error_response`); fix `+00:00Z` timestamp bug | SIMP-03 / SIMP-19 | somaAgent01 | `admin/common/responses.py` + ~16 call sites | api-client unwrap is single-path; ISO-8601 valid |
| W2.3 | Shared health probes (`probe_postgres` / `probe_redis`) | SIMP-07 | somaAgent01 | new `admin/common/health_probe.py`; 3 call sites | One probe implementation; three schemas map `ProbeResult` |
| W2.4 | Delete dead `admin/llm/__init__` re-export layer | SIMP-09 | somaAgent01 | `admin/llm/__init__.py` | Zero external callers of the wrappers (already verified) |
| W2.5 | `ruff --select F401,F841 --fix` + named constants for `"DGR"`, `"health_check"`, permission strings | SIMP-10 / SIMP-08 / SIMP-15 | somaAgent01 | multi | `ruff check` clean; `Actions` constants used at every gate |
| W2.6 | Permission `Actions` constants in `admin/core/permissions.py` | SIMP-08 | somaAgent01 | multi | Zero bare `"resource:…"` literals |

**Wave 2 exit:** one envelope, one key mint, one probe, one permission vocabulary. Drift class eliminated.

---

### Wave 3 — schema structure *(migrations, expand-contract)*

| # | Task | Finding | Owner | Files | Gate |
|---|---|---|---|---|---|
| W3.1 | Chat soft-refs → `db_constraint=False` FKs, then real FKs + backfill | DB-CRIT-2 | somaAgent01 | `admin/chat/models.py` + migrations | Tenant/Agent delete cascades or is PROTECT; zero orphans |
| W3.2 | Index `MemoryReplica (tenant, coord, -created_at)` | DB-HIGH-3 | somaAgent01 | `admin/core/models/core.py` + migration | `get_latest` is an index scan |
| W3.3 | Partial index `files_v2 (tenant_id, user_id) WHERE deleted_at IS NULL` | DB-HIGH-4 | somaAgent01 | `admin/filesv2/models.py` + migration | File list stays index-only as deleted rows grow |
| W3.4 | `MultimodalOutcome.cost_cents` → `DecimalField`; `MemoryReplica.wal_timestamp` → `DateTimeField` | DB-HIGH-5 / DB-HIGH-6 | somaAgent01 | `admin/core/models/core.py` + migrations | Money never a float; time-window queries use Postgres time ops |
| W3.5 | Canonicalize tenant key type (FK/UUIDField; document sinks) | DB-HIGH-7 | somaAgent01 | cross-app | One tenant type; join indexes usable |
| W3.6 | Unify soft-delete behind one `SoftDeleteModel` abstract base + partial indexes | MED-12 | somaAgent01 | `admin/core/models/`, `admin/filesv2/`, `admin/chat/` | One predicate, one manager `alive()` |
| W3.7 | Drop redundant `db_index` where `unique=True` (10 tables) | MED-1 | somaAgent01 | multi + migration | No double-index catalog entries |
| W3.8 | Composite indexes: `jobs (status, scheduled_at, priority)`, `notifications (user_id, is_read, -created_at)`, GIN on `llm_model_configs.capabilities` | MED-2 / MED-3 / MED-9 | somaAgent01 | multi + migration | Queue poll / inbox / model routing are index scans |
| W3.9 | Strip `subscription_tier` / `view_billing` from `schemas/spicedb/schema.zed` | DB-HIGH-9 | somaAgent01 | `schemas/spicedb/schema.zed` | zed definitions map 1:1 to live models |

**Wave 3 exit:** referential integrity is real; every hot filter/sort has an index; no float money; no float timestamps.

---

### Wave 4 — structural simplification *(parallel by module)*

| # | Task | Finding | Owner | Files | Gate |
|---|---|---|---|---|---|
| W4.1 | Extract `TurnPlan` / `_prepare_turn()` shared phases | SIMP-04 | somaAgent01 | `admin/core/chat_orchestrator.py` | `process_turn` and `stream_turn` share one pipeline core; e2e green |
| W4.2 | Route all webui fetches through `ApiClient`; keyed `repeat()` + virtualizer in chat | SIMP-05 / PERF-11 | somaAgent01 | `webui/src/**` | Zero raw `fetch` outside `api-client.ts`; streaming re-render is O(1) |
| W4.3 | Settings base module + adopt `env_config` (keep mode topology) | SIMP-06 | somaAgent01 | `config/`, `services/gateway/settings.py`, `infra/platform/unified_settings.py` | 88 duplicated names → one declaration; mode table intact |
| W4.4 | Split long functions (`run_tool_loop` 255, `_login_local` 179, `_handle_chat` 172) | SIMP-11 | somaAgent01 | multi | Every function < 50 lines (project law) |
| W4.5 | Request dataclasses for 8+ arg functions | SIMP-13 | somaAgent01 | multi | Call sites take a frozen dataclass |
| W4.6 | Replace bare `except Exception` with typed/logged handlers | SIMP-14 | somaAgent01 | multi | Zero silent swallows; every handler logs `exc_info` |
| W4.7 | Keyset pagination for messages; stream `export_conversation` | PERF-9 / PERF-12 | somaAgent01 | `admin/chat/api/chat.py` | Deep page = constant time; export = constant memory |
| W4.8 | Redis SET/ZSET session index | PERF-10 | somaAgent01 | `admin/common/session_store.py` | `list_sessions` = 1–2 round-trips |
| W4.9 | Outbox happy-path `create` + `IntegrityError` (preserve T-6) | PERF-15 | somaAgent01 | `services/common/memory_gateway.py` | Durability contract unchanged; one less SELECT |

**Wave 4 exit:** ~1,800–2,400 LOC removed; every contract has one implementation; orchestrator twins collapsed.

---

### Wave 5 — final gate

| # | Task | Gate |
|---|---|---|
| W5.1 | Full human Playwright suite in the UI | `tests/e2e/test_human_chat_session.spec.js` green — chatting, settings, models, every user action |
| W5.2 | Query-count regression gates | `assertNumQueries` on conversation list, settings save, auth decode |
| W5.3 | `makemigrations --check` in CI with dev Vault | Zero model/migration drift |
| W5.4 | `CREATE INDEX CONCURRENTLY` via `RunSQL(atomic=False)` on large tables | No blocking index builds on `memory_replica`, `messages`, `outbox_messages` |
| W5.5 | ISO docs pass + register update | `check_docs` PASS |

**Final gate:** the full human Playwright suite, in the UI, green. Nothing is done until then.

---

## 5. A2A coordination map

| Peer | Repo | Owns | This plan needs from them |
|---|---|---|---|
| **MiMoCode-somaAgent01** (this seat, PID 5498) | `somaAgent01` | webui, admin/*, services/*, migrations, this plan | — |
| **MiMoCode-somabrain** (PID 3612) | `somabrain` | memory/*, SomaBrain API, SFM/Milvus, OPA | (a) recall assist for W0.4 content backfill; (b) confirm `/memory/remember/batch` exists for W1.5; (c) Milvus/MinIO root-cause still open from 2026-10-09 OUTBOX |
| **Third MiMo seat** (PID 3138, cwd `~/Downloads`) | unidentified | TBD | Identify and declare scope via `INBOX.md` |

**Claim discipline:** every wave row above gets a `CLAIMS.md` row before the first edit. Shared files (`config/settings.py`, `admin/core/models/core.py`, `admin/core/tool_calling.py`) are **merge-additive** — never revert a peer's edits.

---

## 6. Risk register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| W0.1 dedupe finds production duplicate key hashes | Med | Auth break | Dry-run report first; operator adjudicates duplicates before UNIQUE |
| W0.4 backfill finds no recoverable content | Med | Permanent loss for a window | Report the exact row count; never invent content (R1) |
| W3.1 FK migration locks `messages` | Med | Deploy stall | Expand-contract; `CONCURRENTLY` where possible; nullable FK first |
| W1.5 parallel writes re-order coord | Low | Memory noise | Coord is content-derived; verify with recall round-trip |
| W4.1 orchestrator split regresses streaming | Med | Chat break | Keep e2e green per commit; do not merge on red |
| Peer collision on `config/settings.py` | Med | Merge conflict | A2A claim + additive-only edits |
| Milvus/MinIO still down (peer P0) | High | Memory lane amber | Out of this repo's control; agent side stays T-1 and fail-closed |

---

## 7. Definition of Done (per wave)

1. Tests written **first** and proven RED, then GREEN (TDD).
2. `pytest tests/unit` green for the touched surface.
3. No new hardcoded values, fallbacks, stubs, or TODOs (R1–R5).
4. Migrations reversible or explicitly documented as irreversible.
5. `CLAIMS.md` row → `LEDGER.md` commit line.
6. Final: human Playwright green on real services.

---

## 8. What this plan will NOT do

1. **Not touch the T-1 memory seam.** `MemoryGateway → SomaBrainAdapter` stays the only path. No SFM client, no inlined adapter.
2. **Not collapse Temporal workflows** for "simplicity" — activity boundaries are semantics.
3. **Not cache memory recall** — semantic + tenant/session-scoped.
4. **Not replace `TinyDeterministicEmbedder`** — bit-identical to SomaBrain by contract.
5. **Not remove durable-before-hop outbox** (T-6) — only slim the happy path.
6. **Not delete contract tests** (`test_memory_one_path.py`, `test_authz_fail_closed.py`, …).
7. **Not invent settings or routes.** Grep the chain first (RAPID Rule 3).
8. **Not write secrets to any file.**
