# SOMA-TRIAD-ARCH-001 — Triad Architecture Description & Remediation Plan

## Document Control

| Field | Value |
|-------|-------|
| Document Title | Soma Triad Architecture Description — Agent / Brain / Memory |
| Document Identifier | SOMA-TRIAD-ARCH-001 |
| Version | 2.0.0 |
| Date | 2026-09-27 |
| Status | Draft — findings open, remediation plan approved for execution |
| Author | SomaTech Engineering |
| Approver | — |
| Classification | Internal |
| ISO Reference | ISO/IEC/IEEE 42010:2011 — Architecture Description |
| Related | `docs/project/ARCHITECTURE-INVARIANTS.md` (normative), `docs/development/VIBE_CODING_RULES.md` (engineering law), `docs/project/PLAN-TRIAD-SEAMLESS.md` (delivery) |

## Revision History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0.0 | 2026-09-27 | SomaTech Engineering | Initial description. Memory lane verified live. |
| 2.0.0 | 2026-09-27 | SomaTech Engineering | Rebuilt from full source read of all three repos. Target architecture (§4), remediation plan (§11), scale review (§10) added. Findings register re-opened with source citations. |

---

## 1. Purpose and Scope

### 1.1 Purpose

To describe the architecture of the Soma triad — `somaAgent01` (agent), `somabrain` (brain),
`somafractalmemory` (memory) — as an ISO/IEC/IEEE 42010 architecture description, and to
state the single target architecture and the ordered remediation that reaches it.

This document is written **from source**, not from intent. Every claim below cites the file
and line it came from. Runtime claims are marked *[live]* and were exercised against the
running services on 2026-09-27.

### 1.2 Scope

In scope: the three services, their memory and recall lane, the wire contracts between
them, design patterns, clean-code posture, fail-safe behaviour, scale readiness, and the
remediation programme.

Out of scope: model quality, prompt engineering, capacity procurement.

### 1.3 Stakeholders and Concerns

| Stakeholder | Concern | Section |
|---|---|---|
| Platform engineering | Does memory persist and recall correctly at 10⁶–10⁸ rows? | §5, §6, §10 |
| Security | Fail-closed boundaries, tenant isolation, no leaked secrets | §8 |
| QA | Does the test suite prove anything? | §7 |
| Operations | What runs, what is degraded | §3.3, §12 |

---

## 2. Normative References and Terminology

### 2.1 Normative

| Reference | Role |
|---|---|
| ISO/IEC/IEEE 42010:2011 | Architecture description content and structure |
| `docs/project/ARCHITECTURE-INVARIANTS.md` | Normative invariants; violation is a defect |
| `docs/development/VIBE_CODING_RULES.md` | Engineering law: no mocks, no stubs, real data only |

### 2.2 Terminology

| Term | Definition |
|---|---|
| **Seam** | `services/common/memory_contract.py` — single authority for memory DTOs, coordinate derivation, embedding |
| **Lane** | The complete path a write or read takes across service boundaries |
| **Canonical lane** | Exactly one path per operation; no row written or read twice through independent code |
| **Store** | `somafractalmemory` — durable row + vector persistence |
| **Coord** | 3-float address in `[-1,1]³`, the row's primary key in the store |
| **Fail-closed** | On ambiguity, outage or missing config, deny or raise. Never silent success. |
| **Fail-open** | The defect opposite of fail-closed: missing evidence becomes permission or empty success |

---

## 3. Architecture Views (as-built)

### 3.1 Context

```
  User
   │ chat turn
   ▼
┌────────────────────────────────┐
│ somaAgent01                    │
│  V3ChatOrchestrator            │── select_model ──► Groq (litellm)
│  FanoutMemoryGateway           │
│   memory_gateway.py:38         │
└───────┬────────────────┬───────┘
        │ remember()      │ remember()
        ▼                 ▼
┌───────────────┐  ┌──────────────┐
│ SomaBrain     │  │ SFMAdapter   │
│ Adapter       │  │              │
│ somabrain_    │  │ sfm_         │
│ adapter.py    │  │ adapter.py   │
└──────┬────────┘  └──────┬───────┘
       │ POST /memory/     │ POST /memories
       │ remember          │   (DIRECT)
       ▼                   │
┌────────────────┐         │
│ somabrain      │         │
│ MemoryService  │         │
│ MultiTenant-   │         │
│  Memory        │         │
│ MemoryClient   │         │
└──────┬─────────┘         │
       │ POST /memories    │
       │   (VIA BRAIN)     │
       └─────────┬─────────┘
                 ▼
       ┌─────────────────────┐
       │ somafractalmemory   │
       │ 768-dim · Milvus    │
       │ Django ORM rows     │
       └─────────────────────┘
```

**The two arrows into the store are the central architectural defect.** See §5.

### 3.2 Logical

| Component | File | Responsibility |
|---|---|---|
| Memory contract | `services/common/memory_contract.py` (265 L) | `MemoryWrite`/`Hit`/`Ack`, `MemoryGateway` protocol, `make_coord`, `embed_text` |
| Gateway | `services/common/memory_gateway.py` (215 L) | `FanoutMemoryGateway` — sole entry point |
| SFM adapter | `services/common/adapters/sfm_adapter.py` (240 L) | Store dialect for somafractalmemory |
| Brain adapter | `services/common/adapters/somabrain_adapter.py` (219 L) | Store dialect for somabrain |
| Brain memory façade | `somabrain/memory/remember.py`, `recall_ops.py` | WM/LTM lifecycle |
| Brain pool | `somabrain/memory/pool.py` (56 L) | `MultiTenantMemory.for_namespace()` → one `MemoryClient` per ns |
| Brain client | `somabrain/memory/client/` (9 modules) | HTTP to somafractalmemory |
| Store API | `somafractalmemory/api/routers/{memory,search}.py` | `/memories`, `/memories/search`, `/memories/{coord}` |
| Store auth | `somafractalmemory/api/auth.py` | `StandaloneAuth` — bearer `SOMA_API_TOKEN` |

### 3.3 Physical *[live, 2026-09-27]*

| Service | Port | State |
|---|---|---|
| somafractalmemory api | 10101 | healthy |
| somabrain app | 30101 | healthy |
| somaagent standalone | 20020 | **unhealthy** |
| somaagent webui | — | **restart loop** |
| milvus / postgres / redis / kafka / opa / vault / minio / jaeger | 10530 / 30106 / 30100 / 30102 / 30104 / 30200 / 30109 / 30111 | healthy |

---

## 4. Target Architecture — the single canonical lane

This is the architecture the codebase must converge to. It is stated first so every
finding in §5–§9 is measured against it.

### 4.1 Invariants (normative)

| ID | Invariant |
|---|---|
| **T-1** | **One writer to the store.** SomaBrain is the only component that writes to somafractalmemory. |
| **T-2** | **One coordinate authority.** `_stable_coord`, coord serialization and the embed dimension live in one shared module imported by all three repos. No copy, no comment-agreement. |
| **T-3** | **One embedding authority.** The vector for a memory is computed exactly once and travels precomputed on every path. |
| **T-4** | **One lane per operation.** One `remember` → one row. One `recall` → one hit per row. |
| **T-5** | **Fail-closed at every boundary.** Missing config, missing identity, missing auth, or unreachable dependency ⇒ deny or raise. Never a silent default tenant, never an empty list dressed as success. |
| **T-6** | **Durable writes.** A memory write is accepted into a durable outbox before the network hop, and is replayed until the store acknowledges it. No write is lost to a restart. |
| **T-7** | **Bounded resources.** Every cache, pool and buffer has a declared bound and eviction policy. |
| **T-8** | **Tests prove behaviour against real services.** No mocks, no stubs, no fakes. Integration tests run against live infra and skip when it is absent. |

### 4.2 Target topology

```
  User
   │
   ▼
┌─────────────────────────────────┐
│ somaAgent01                     │
│  MemoryGateway ──► SomaBrainGateway   (one adapter on the hot path)
└──────────────┬──────────────────┘
               │  POST /memory/remember|recall|forget   (ONE lane)
               ▼
┌─────────────────────────────────┐
│ somabrain                       │
│  MemoryService (circuit breaker)│
│  outbox → durable queue         │── T-6
│  MemoryClient                   │
└──────────────┬──────────────────┘
               │  POST /memories          (ONE writer)
               ▼
┌─────────────────────────────────┐
│ somafractalmemory               │
│  768-dim Milvus + ORM rows      │
└─────────────────────────────────┘

   shared: soma-memory-contract  (T-2)  imported by all three
```

### 4.3 Why SomaBrain is the sole writer (T-1)

| Option | For | Against | Verdict |
|---|---|---|---|
| **A. Brain writes** | One writer; WM/LTM promotion, consolidation and scoring stay next to persistence; agent survives as a thin client | Brain outage blocks persistence | **ADOPTED** — mitigated by T-6 outbox |
| B. Agent writes | Agent survives brain outage | Brain has no authoritative write path; WM/LTM split loses meaning; two producers still possible | Rejected |
| C. Dual write (as-built) | Redundancy | Two writers, two coordinate derivations, duplicate rows | **Rejected — this is F-01** |

---

## 5. Findings — Memory and Recall Lane

### F-01 · HIGH · Two independent write paths to one store row

`FanoutMemoryGateway.remember` (`memory_gateway.py:59-83`) and `remember_text`
(`:85-128`) each `asyncio.gather` **both** adapters. SomaBrain then persists to the store
itself:

- `somabrain/api/endpoints/memory_remember.py:272` — `"store": "somafractalmemory"`
- `somabrain/api/endpoints/memory_remember.py:276` — `"persisted_to_ltm"`
- `somabrain/memory/remember.py:111-173` `remember_sync_persist` — posts to `/memories`

So one memory produces **two** `POST /memories` through independent code paths.

**Failure mode:** if the two paths ever disagree on coordinate derivation (seed, universe
string, timestamp normalisation), the same fact becomes two distinct rows. They will not
collide, not be deduped, and recall returns the same fact twice with different scores.

**Observed** *[live]*: one remembered text returned two hits sharing
`coord: "0.25,-0.5,0.75"` — one `store:"somabrain", layer:"wm", score:1.0` and one
`store:"somafractalmemory", layer:"ltm", score:-0.014`. T-4 is violated at the API even
though `memory_gateway.py:138-147` dedupes by coord internally.

**Fix:** R-01.

### F-02 · HIGH · Coordinate derivation implemented twice

| Copy | Location | Code |
|---|---|---|
| Agent | `services/common/memory_contract.py:130-141` | `blake2b(seed, digest_size=12)` → 3× `int/2**32` → `2x-1` |
| Brain | `somabrain/memory/client/serialization.py:9-16` | byte-identical maths |

Kept consistent only by a comment: *"Same math as SomaBrain's `_stable_coord`"* (`memory_contract.py:133`).
A comment is not an invariant. **Fix:** R-02.

Related: the preimage is also built twice — `coord_key_material` (`memory_contract.py:119-127`,
`f"{tenant_id}|{kind}|{_norm_ts(ts)}|{text}"`) vs `remember_sync_persist`
(`remember.py:131`, `_stable_coord(f"{uni}::{coord_key}")` via `enrich_payload`). Different
preimage shapes ⇒ different coords for the same fact.

### F-03 · HIGH · `forget` is a documented no-op on the brain

`services/common/adapters/somabrain_adapter.py:173-180`:

```python
async def forget(self, coord: str, tenant_id: str) -> bool:
    """Forget a memory. The brain exposes no memory delete route today."""
    LOGGER.info("SomaBrain forget skipped: no delete route ...")
    return False
```

So `FanoutMemoryGateway.forget` (`memory_gateway.py:150-164`) only removes the SFM row.
The brain's WM copy survives. **A forgotten memory is still recalled.** This is a hard
data-integrity and privacy defect — `forget` is an erasure primitive that does not work.

**Fix:** R-01 (T-1 makes the brain the delete owner) + add `POST /memory/forget` on the brain.

### F-04 · HIGH · `infra/mocks/` — live fake services wired into the compose stack

```
somaAgent01/infra/mocks/somabrain/main.py           (32 L)  fake brain
somaAgent01/infra/mocks/somafractalmemory/main.py   (44 L)  fake store
```

Both are **build contexts in `infra/standalone/docker-compose.yml:186` and `:207`** — i.e.
the standalone stack can run against fake stores. `sfm_adapter.py:11` even documents that
the mocks serve a different dialect (`/api/v1/store|search`) that "must never be used".

**Fix:** R-03 — delete both directories and their compose entries.

### F-05 · HIGH · Mocked test suite proves nothing

`somabrain/tests/unit/memory/test_seam_contract.py` (473 L) — 15 mock markers,
`_FakeResponse`, `_FakeSFM`, `_FakeAsyncClient`, `_FakeTransport`, `_FakeWM`, `_FakeEmbedder`,
`_FakeRequest`, plus `monkeypatch.setattr(MemoryClient, "_init_http", ...)` and
`monkeypatch.setattr(memory_remember, "_get_memory_pool", ...)`. It is structurally incapable
of detecting F-01–F-03.

Also mocked (against VIBE §1/§4):
- `somaAgent01/tests/unit/test_auth.py` — `AsyncMock, patch, MagicMock`
- `somaAgent01/tests/unit/test_rate_limiter.py`
- `somaAgent01/tests/unit/test_unified_gate.py`
- `somaAgent01/tests/phase4_validation_unified_layers.py`
- `somabrain/tests/unit/test_aaas_mode.py` — `@patch("somabrain.memory.client.MemoryClient")`

somafractalmemory's suite is clean (zero mock markers).

**Fix:** R-04.

---

## 6. Wire Contracts (source + *[live]* verified)

| Caller | Request | Target | Response |
|---|---|---|---|
| SomaBrainAdapter | `POST /memory/remember` | brain `:30101` | ack |
| SomaBrainAdapter | `POST /memory/recall` | brain `:30101` | `{results:[...]}` |
| SomaBrainAdapter | `forget` | — | **no route — returns False** (F-03) |
| SFMAdapter / MemoryClient | `POST /memories` | SFM `:10101` | `MemoryStoreResponse {coord, memory_type, embedding_source}` |
| SFMAdapter / MemoryClient | `POST /memories/search` | SFM `:10101` | `MemorySearchResponse {memories:[...]}` |
| SFMAdapter / MemoryClient | `GET /memories/{coord}` | SFM `:10101` | `{memory:{...}}` or `404` |
| SFMAdapter / MemoryClient | `DELETE /memories/{coord}` | SFM `:10101` | `MemoryDeleteResponse {coord, deleted: bool}` |

### 6.1 Delete contract

From `somafractalmemory/api/routers/memory.py:78-91` and `schemas.py:42-46`:

| Outcome | Status | Body |
|---|---|---|
| Row removed | 200 | `{"coord": …, "deleted": true}` |
| Already absent | 200 | `{"coord": …, "deleted": false}` |

**The status code cannot distinguish these.** `MemoryClient._interpret_delete_response`
(`somabrain/memory/client/core.py:80-102`) therefore treats the `deleted` flag as
authoritative and raises on a 2xx that lacks it. This is correct.

### 6.2 Store request shapes (source of truth: `api/schemas.py:19-67`)

```
MemoryStoreRequest  { coord: str, payload: dict, memory_type: episodic|semantic|belief,
                      embedding: float[]|None, tenant_id: str|None }
MemorySearchRequest { query: str="", top_k: int=5, offset: int=0,
                      memory_type: str|None, filters: dict|None,
                      embedding: float[]|None, tenant_id: str|None }
MemoryDeleteResponse{ coord: str, deleted: bool }
```

`SFMAdapter.recall` (`sfm_adapter.py:184`) reads `data.get("memories")` — matches
`MemorySearchResponse.memories`. Correct. `SomaBrainAdapter.recall` reads
`data.get("results")` (`somabrain_adapter.py:167`).

---

## 7. Design Pattern Assessment

| # | Pattern | Where | Right? | Applied correctly? | Verdict |
|---|---|---|---|---|---|
| P-01 | Seam / Contract | `memory_contract.py` | Yes | Yes | **CORRECT** |
| P-02 | Adapter (dialect isolation) | `adapters/*` | Yes | Yes | **CORRECT** |
| P-03 | Gateway (single entry) | `FanoutMemoryGateway` | Yes | Yes | **CORRECT** |
| P-04 | **Fan-out dual write** | `memory_gateway.remember` | No | — | **F-01 DEFECT** |
| P-05 | Identity / stable key | 2× `_stable_coord` | Yes | **No** | **F-02 DEFECT** |
| P-06 | Circuit breaker | `MemoryService` | Yes | Yes | **CORRECT** |
| P-07 | Fail-closed boundaries | adapters, `ensure_embedding_dim` | Yes | Mostly | **F-06, F-07** |
| P-08 | Pool per namespace | `MultiTenantMemory` | Yes | **Unbounded** | **F-08** |
| P-09 | Test double | mock suite | No | No | **F-05 DEFECT** |
| P-10 | Async client reuse | `MemoryHTTPTransport` | Yes | Was broken | **F-09 FIXED** |
| P-11 | Outbox / write-ahead | `remember.py:29-85` | Yes | Brain only | **PARTIAL — see T-6** |

---

## 8. Fail-Safe and Security Posture

| Boundary | Behaviour | Source | Verdict |
|---|---|---|---|
| Store URL unset | `MemoryConfigurationError` raised | `sfm_adapter.py:58-63`, `somabrain_adapter.py:48-53` | **Fail-closed** ✓ |
| Missing `SOMA_API_TOKEN` | `authenticate` returns `None` ⇒ 401 | `api/auth.py:43-45` | **Fail-closed** ✓ (log text "auth disabled" is misleading — it actually rejects everything) |
| Wrong token | `hmac.compare_digest` ⇒ 401 | `api/auth.py:48-53` | ✓ constant-time |
| Wrong dimension vector | HTTP 400 `EMBEDDING_DIMENSION_MISMATCH` | `api/utils.py:92-103` | ✓ fail-closed |
| Bad coord string | HTTP 400 | `api/utils.py:23-35` | ✓ |
| Memory backend error | `MemoryServiceError` → 502; timeout → 504 | brain service layer | ✓ |
| Redis down (rate limit) | deny | `rate_limiter.py` | **Fail-closed** ✓ |
| OPA/SpiceDB down | `UnifiedGate` denies | `unified_gate` | **Fail-closed** ✓ |
| **Missing tenant** | **falls back to `"default"`** | `api/utils.py:79` `return auth_tenant or "default"` | **FAIL-OPEN — F-06** |
| **Empty `allowed_namespaces`** | **`return True`** | `api/auth.py:86-87` `if not allowed: return True` | **FAIL-OPEN — F-07** |
| `forget` on brain | silently returns False | `somabrain_adapter.py:173-180` | **FAIL-OPEN — F-03** |
| Store outage on `recall` | `return []` | `sfm_adapter.py:179-181` | **FAIL-OPEN — F-10** |

### 8.1 Secrets — clean

| Check | Result |
|---|---|
| Tracked `.env` files | **None.** Only `.env.example` in all three repos |
| Hardcoded PAT / API key / AWS key in source | **None found** in any of the three repos |
| `ghp_` / `sk-` / `AKIA` / `-----BEGIN` scan | Only a PEM **placeholder** in `somabrain/.github/workflows/ci.yml:326` and a PEM-detection branch in `constitution/__init__.py:218` |
| Tokens in code | Read from env via `get_memory_setting` (`memory_contract.py:171-202`) — settings-first, then env, then caller default |

The leaked PAT from an earlier session exists only in a session transcript, not
in any repository. It is expired and must not be used.

### F-06 · HIGH · Silent default tenant

`api/utils.py:79` — `return auth_tenant or "default"`. A caller who omits `tenant_id`,
omits `X-Soma-Tenant`, and uses the standalone token lands in the shared `"default"` tenant.
That is cross-tenant data mixing by omission. T-5 is violated.

**Fix:** R-05 — reject with 400 when no tenant can be resolved. Never default.

### F-07 · MEDIUM · Namespace check fails open

`api/auth.py:86-87` — `if not allowed: return True`. An empty allow-list grants access.
Currently unreachable because `StandaloneAuth` always sets `["*"]`, but the default is wrong.

**Fix:** R-05 — `if not allowed: return False`.

### F-08 · MEDIUM · Unbounded per-namespace client pool

`somabrain/memory/pool.py:38` — `self._pool: Dict[str, MemoryClient]` grows without bound and
is never evicted. Each `MemoryClient` holds an `httpx.Client` + `httpx.AsyncClient`
(`memory/transport.py:156,189`). At 10⁴ tenants this leaks file descriptors and memory.

**Fix:** R-06 — bounded LRU with idle eviction.

### F-09 · HIGH · Async client bound to one event loop — **FIXED 2026-09-27**

`httpx.AsyncClient` is bound to the loop it first ran on; ASGI replaces loops between
requests ⇒ every `forget` returned `503 Event loop is closed` *[live, deterministic 3/3]*.

Fixed in `somabrain/memory/transport.py:109-132` (loop-aware `async_client` property +
`_new_async_client`) and `client/transport.py:26-38` (live `_http_async` property).
Verified *[live]*: 4/4 forgets → 200 after restart.

### F-10 · MEDIUM · Store outage on recall returns `[]`

`sfm_adapter.py:179-181` and `somabrain_adapter.py:163-164` swallow the failure and return
an empty list. The caller cannot distinguish "no memories" from "memory is down", so a
degraded system silently answers every question with amnesia.

**Fix:** R-05 — raise, or return a typed degraded result the orchestrator must surface.

### F-11 · LOW · Latent 256-dimension fallback

`somafractalmemory/admin/core/services.py:127` — `getattr(settings, "SOMA_VECTOR_DIM", 256)`.
`settings/infra.py:73` always defines it as 768 so this branch is dead today, but the default
contradicts the 768 invariant and will silently misconfigure if the setting ever moves.

**Fix:** R-07 — drop the `256` default; use `settings.SOMA_VECTOR_DIM` directly.

### F-12 · MEDIUM · Agent containers degraded

`somaagent_standalone` unhealthy, `somaagent_webui` in a restart loop *[live]*. Blocks all
end-to-end verification of the chat lane.

**Fix:** R-09.

---

## 9. Clean Code Assessment

| Criterion | Finding | Rating |
|---|---|---|
| Single responsibility | Adapters / gateway / contract each own one concern | Good |
| Duplication | `_stable_coord` ×2, coord preimage ×2 | **Poor** |
| Dead code | 1 232 lines of competing memory façades removed 2026-09-26 | Good (recent) |
| Fail-closed defaults | Strong in adapters; three fail-opens in SFM auth/tenant/recall | Mixed |
| Error honesty | `_interpret_delete_response` raises on ambiguous 2xx | Good |
| Naming | Contract names match the domain | Good |
| Test honesty | 5 files mock; 1 is entirely fake | **Poor** |
| Magic values | 768 is named and shared; one stale `256` remains | Mostly good |
| Module size | `services/common/` has 60+ modules in one flat package | Needs structure |
| Docstrings | Cite real file:line — unusually good | Good |

---

## 10. Scale Review — millions of transactions

| Risk | Where | Verdict |
|---|---|---|
| Dual write amplifies store load 2× | F-01 | **Must fix** |
| Unbounded namespace → client pool | `pool.py:38` | F-08 |
| Outbox is brain-side only; agent write is fire-and-forget | `memory_gateway.py:64-68` | **T-6 violated** |
| `recall` returns unbounded `merged` dict then slices | `memory_gateway.py:138-148` | Bounded by 2×k — OK |
| Search pagination | `MemorySearchRequest.top_k`/`offset` | OK |
| HTTP timeouts | agent 5.0 s (`MEM_HTTP_TIMEOUT`), transport 10.0 s (`transport.py:157`) | OK |
| Connection pooling | `httpx.Limits` from settings (`client/transport.py:64-89`) | OK |
| Retry policy | `post_with_retries_*`, max 2, jitter | OK |
| Circuit breaker | `MemoryService` | OK |
| Coord keyspace | 96-bit BLAKE2b → 3 floats; birthday bound safe past 10⁹ rows | OK |
| Idempotent rewrite | same `tenant|kind|ts|text` ⇒ same coord ⇒ overwrite | **Desirable** — natural dedup |
| Tenant isolation in key | tenant is in the coord preimage (`memory_contract.py:127`) | OK — different tenants cannot collide |
| Sync I/O in async | `run_in_executor` wrappers in `client/core.py:155,168` | Acceptable |
| Observability | Jaeger + Prometheus wired | OK |

---

## 11. Remediation Plan

Ordered. Each step is independently shippable and leaves the system no worse than before.

### R-01 · Collapse to one write lane *(F-01, F-03 — T-1, T-4)*

1. Add `POST /memory/forget` to somabrain, deleting from both WM and its SFM row.
2. Change `FanoutMemoryGateway.remember` to call **only** `SomaBrainAdapter.remember`.
3. Change `FanoutMemoryGateway.forget` to call **only** `SomaBrainAdapter.forget`.
4. Change `FanoutMemoryGateway.recall` to call **only** `SomaBrainAdapter.recall`
   (the brain already merges wm + ltm).
5. Demote `SFMAdapter` to a read-only maintenance tool (ops, repair, backfill), or delete it
   from the hot path. Keep it under `services/common/adapters/` with an explicit
   `# NOT ON THE WRITE LANE` header.
6. Assert one row per memory with a live test: write once, `GET /memories/{coord}` returns
   exactly one record, `recall` returns exactly one hit.

**Exit criteria:** one `remember` ⇒ one `POST /memories`. `forget` returns `True` and a
subsequent `recall` returns no hit for that coord.

### R-02 · One coordinate authority *(F-02 — T-2)*

1. Create `soma-memory-contract` — a tiny published package holding `_stable_coord`,
   `coord_to_str`, `coord_key_material`, `make_coord`, `DEFAULT_MEM_EMBED_DIM = 768`.
2. Import it from `somaAgent01`, `somabrain`, `somafractalmemory`. Delete both local copies.
3. Add a cross-repo contract test with a fixed vector of 32 seeds; every repo must produce
   the identical coord string for each. Run it in all three CI pipelines.

**Exit criteria:** `grep -rn "_stable_coord"` across the three repos returns exactly one
definition.

### R-03 · Delete the fake services *(F-04)*

1. Delete `somaAgent01/infra/mocks/` entirely (both `main.py`, both `Dockerfile`).
2. Remove the two `build: context: ../../infra/mocks/...` services from
   `infra/standalone/docker-compose.yml:186` and `:207`; point the stack at the real services.
3. Add a CI guard: fail the build if any path matches `infra/mocks/**` or `**/fake*.py`.

**Exit criteria:** `find . -path "*infra/mocks*"` returns nothing.

### R-04 · Replace mocked tests with real ones *(F-05 — T-8)*

1. Delete `somabrain/tests/unit/memory/test_seam_contract.py` (473 L).
2. Re-express its six behavioural claims as integration tests against live `:30101` using
   `tests/integration/infra_config.py`, `pytest.skip` when unreachable — the convention in
   `tests/integration/test_memory_e2e.py`.
3. Keep only genuinely pure tests as units (route resolution, pydantic validation).
4. De-mock `tests/unit/test_auth.py`, `test_rate_limiter.py`, `test_unified_gate.py`,
   `test_aaas_mode.py`, `phase4_validation_unified_layers.py` — each against real Redis /
   real OPA / real SpiceDB, skipping when absent.
5. Add a CI guard: fail the build on `unittest.mock`, `MagicMock`, `monkeypatch.setattr`
   outside an allow-list.

**Exit criteria:** `grep -rn "unittest.mock\|MagicMock\|monkeypatch.setattr"` in production
and test trees returns zero.

### R-05 · Close the fail-open boundaries *(F-06, F-07, F-10 — T-5)*

1. `api/utils.py:79` — raise `HttpError(400, …)` when no tenant resolves. Delete the
   `"default"` fallback.
2. `api/auth.py:86-87` — `if not allowed: return False`.
3. `api/auth.py:45` — fix the log line: auth is not "disabled", it rejects all callers.
4. `sfm_adapter.py:179-181` / `somabrain_adapter.py:163-164` — do not return `[]` on
   transport failure. Raise `MemoryRecallUnavailable`; the orchestrator surfaces "memory
   unavailable" rather than answering as if the user has no history.

**Exit criteria:** a request with no tenant anywhere returns 400 *[live]*; killing SFM
causes `recall` to raise, not return `[]` *[live]*.

### R-06 · Bound the resource pools *(F-08 — T-7)*

1. `pool.py` — replace `Dict` with an LRU of bounded size (configurable, default 256) with
   idle-timeout eviction and explicit `close()` on eviction.
2. Declare bounds in `ARCHITECTURE-INVARIANTS.md` and add a metric for pool size / evictions.

### R-07 · Remove the stale 256 fallback *(F-11)*

`somafractalmemory/admin/core/services.py:127` → `self.vector_dim = int(settings.SOMA_VECTOR_DIM)`.
Delete the `256`.

### R-08 · Durable agent writes *(T-6)*

Extend the outbox already used in `remember.py:29-85` to the agent lane: `remember` records
to a durable outbox before the network hop and returns `ok: true` meaning *accepted*, with
replay until the brain acknowledges. Guarantees no write lost to a restart under load.

### R-09 · Restore agent health *(F-12)*

`somaagent_standalone` unhealthy and `somaagent_webui` in a restart loop. Investigate before
further chat-pipeline work.

### R-10 · Commit and push

Three repos currently hold uncommitted work (somabrain + somafractalmemory staged; two lint
fixes unstaged; `somaAgent01` at `2825b517` with **no upstream configured**). Requires a
**fresh PAT** — the earlier one is expired and compromised; do not reuse it.

### Execution order

```
R-03  (delete fakes — no risk, immediate)
R-05  (fail-closed — security)
R-07  (stale default — trivial)
R-01  (one write lane — the core)
R-02  (one coordinate authority)
R-04  (real tests — after R-01 so tests target the final lane)
R-06  (bounded pools)
R-08  (durable writes)
R-09  (agent health)
R-10  (commit/push)
```

---

## 12. Verification Matrix

| Target | Evidence | Status |
|---|---|---|
| T-1 one writer | two `POST /memories` paths (§5 F-01) | **NOT MET** |
| T-2 one coord authority | two `_stable_coord` definitions (F-02) | **NOT MET** |
| T-3 one embedding authority | computed once in gateway (`memory_gateway.py:54-57`) | MET |
| T-4 one lane per op | duplicate coord in one recall *[live]* | **NOT MET** |
| T-5 fail-closed | three fail-opens (F-06, F-07, F-10) | **NOT MET** |
| T-6 durable writes | outbox brain-side only | **PARTIAL** |
| T-7 bounded resources | unbounded pool (F-08) | **NOT MET** |
| T-8 real tests | 5 mocked files (F-05) | **NOT MET** |
| Single gateway singleton | `get_memory_gateway()` `memory_gateway.py:202` | MET |
| Two adapters only | `adapters/` is the only dialect owner | MET |
| No secrets in git | only `.env.example` tracked | MET |
| Cross-tenant isolation by key | tenant in coord preimage | MET |
| Delete contract honoured | `_interpret_delete_response` | MET |

---

## 13. Conclusion

The triad's **layering is right.** One seam, one gateway, two adapters, a named contract,
and unusually honest docstrings that cite real file:line. The 2026-09-26 cleanup that removed
1 232 lines of competing memory façades was the correct intervention, and the fail-closed
stance in the adapters and `ensure_embedding_dim` is genuinely good work.

The triad's **lane topology is wrong, and the test suite cannot see that.** One memory is
written twice through independent code paths; the function that gives a memory its identity
exists twice, kept equal by a comment; `forget` silently does nothing on the brain, so a
"forgotten" memory is still recalled; and two fake services sit in the compose file ready to
stand in for the real ones. Under millions of transactions those are not edge cases — they
are the failure mode.

The remediation is ten ordered steps (§11). R-03 and R-05 are immediate and low-risk. R-01
and R-02 are the architecture. Together they turn a system with two writers and two identity
functions into one with a single canonical lane to memory and recall — which is what the
house invariants already demanded and what the code does not yet do.
