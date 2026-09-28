# ARCHITECTURE INVARIANTS — what must be perfect

**Date:** 2026-09-26
**Owner:** somaplanet
**Status:** normative — any code that violates an invariant here is a defect, not a style choice.

This is the contract for the triad (somaAgent01 ↔ somabrain ↔ somafractalmemory).
Companion to `SOMA-PM-PLAN-TRIAD-001.md` (delivery waves). This document says
*what must be exactly right*; the plan says *who builds it and when*.

---

## 0. Single source of truth

**ONE** memory contract. **ONE** gateway. **TWO** adapters. Nothing else.

```
services/common/memory_contract.py     ← DTOs + coord + embed  (AUTHORITY)
services/common/memory_gateway.py      ← MemoryGateway impl    (ONLY entry point)
services/common/adapters/sfm_adapter.py        ┐
services/common/adapters/somabrain_adapter.py  ┘ (ONLY store dialects)
```

Every memory read/write in the agent goes through `MemoryGateway`.
If you find yourself defining another `Memory*Protocol` / `*MemoryPort` /
`store_memory()` / `recall_memory()`, **stop** — you are rebuilding the mess
that was just deleted.

### Deleted on 2026-09-26 (do not resurrect)

| File | Lines | Why it was wrong |
|---|---|---|
| `services/common/ports/memory_port.py` | 154 | A prior "consolidate 9 entry points" attempt nobody imported |
| `admin/core/domain/ports/adapters/memory_adapter.py` | 22 | `MemoryAdapterPort` #1 |
| `admin/core/infrastructure/adapters/memory_adapter.py` | 118 | wrapper nobody called |
| `admin/core/application/use_cases/memory/store_memory.py` | 107 | `MemoryAdapterPort` #2 (redefined!) |
| `admin/core/application/use_cases/conversation/store_memory.py` | 223 | `MemoryClientProtocol` #3 |
| `admin/somabrain/services/memory_integration.py` | 140 | a fourth high-level façade |
| `services/common/adapters/memory_direct.py` | 149 | a **parallel** adapter stack, last touched May, zero importers |
| `services/common/adapters/memory_http.py` | 265 | same stack, the other half |
| `services/common/protocols/__init__.py` | 142 | `BrainServiceProtocol` + `MemoryServiceProtocol` — 3rd/4th dialect |
| `services/common/adapters/__init__.py` *(rewritten)* | 52 | `get_memory_service()` — a factory with zero callers that routed to the dead stack |

That is **1 232 lines** of memory machinery that did nothing. Four protocols for
one concept, two adapter stacks for one store. That is why memory did not work.

Also removed 2026-09-26: the `SOMA_MEMORY_URL` env alias (its only consumer was
the deleted `memory_http.py`). The seam reads `SFM_URL` / `SOMAFRACTALMEMORY_URL`.

---

## 1. INVARIANT — one coordinate scheme

```
make_coord(tenant_id, kind, ts, text) -> str
```

**The rules:**

1. `make_coord` in `memory_contract.py` is the **only** coordinate writer in the
   agent. There is no second one, anywhere, ever.
2. The returned string is SFM's row key: `",".join(str(f) for f in floats)` over
   a point in `[-1,1)^3`, exactly `Memory.coord_to_key` of the parsed tuple
   (`somafractalmemory/admin/core/models.py:78-80`).
3. The hash is BLAKE2b `digest_size=12` → three `uint32/2**32` → `(2a-1, 2b-1, 2c-1)`,
   seeded `f"{COORD_UNIVERSE}::{tenant}|{kind}|{ts}|{text}"`. This is
   byte-identical to SomaBrain's `_stable_coord`
   (`somabrain/memory/client/serialization.py:9`) applied to the same preimage.
4. Non-numeric coordinate strings are rejected by SFM with **400**. Never invent
   a string key.

**Why it matters:** three coordinate writers existed
(`chat_orchestrator._make_coordinate`, `scripts/generate_somafractal_image.make_coordinate`,
and the seam). Three keys for one memory means recall finds nothing.

**Convergence rule (this is the subtle one):**
SomaBrain's long-term memory backend **is** SomaFractalMemory
(`somabrain/memory/pool.py:4-5`, `memory/client/transport.py:206,228`).
So a "write to brain" and a "write to SFM" are the same row — **iff** both
derive the same point. Callers MUST pass `coord_key_material(...)` as the
SomaBrain `key` so brain hashes the same preimage (`remember_text()` does this).
Without it brain hashes the *coordinate string* and writes a second row.

---

## 2. INVARIANT — one embedding space

```
embed_text(text) -> list[float]     # dim == MEM_EMBED_DIM
```

1. The embedding is computed **once**, in the gateway, and sent **precomputed**
   to both stores. Never let each store re-embed.
2. Dimension: `MEM_EMBED_DIM` (agent) **must equal** `SOMA_VECTOR_DIM` (SFM).
   Both default **256**. Milvus collections are fixed-dim at creation — a mismatch
   is a hard failure, not a soft one.
3. SFM writes precomputed vectors **verbatim** to Milvus
   (`embedding_source="precomputed"`). Its `HashEmbedder` is a **fallback only**
   (`embedding_source="hash"`), and hash hits are ranked × 0.25 so they never
   outrank real vectors.
4. Non-finite or wrong-dim vectors are **400**. Fail closed.

**Why it matters:** SFM's `HashEmbedder` (SHA-256 bag-of-words) is not semantic.
If one side hashes and the other embeds, cosine distance is meaningless and
recall returns noise.

---

## 3. INVARIANT — one write path, one read path

**Write:** `ChatOrchestrator` → `MemoryGateway.remember_text(...)` → fan-out to
both stores → one `MemoryAck` per store.

`remember_text()` is the caller-facing entry point: it builds the `MemoryWrite`,
derives the coord **and** the SomaBrain `key` material from the same
`(tenant, kind, ts, text)`, and passes the key so brain converges on the seam
coordinate (see §1). Callers that build a `MemoryWrite` themselves and call
`remember(w)` **must** also pass `key_material` — otherwise brain hashes the
coordinate string and writes a second row.

1. `remember()` **never throws**. A failed store produces `MemoryAck(ok=False, error=...)`.
2. The embedding is computed **once** per write, never once per store.
3. `PendingMemory` outbox retries **only failed acks**. It is never a second
   unconditional write. Its idempotency key **must** be the seam `coord` —
   not a UUID (a random suffix makes the outbox multiply memories).
4. Postgres `Message` rows are the conversation transcript. They are **not**
   semantic memory and must not be treated as recall.

**Read:** `MemoryGateway.recall(query, k, tenant_id)` → merge both stores →
**dedupe by `coord`** keeping the highest score → sort by score desc.

1. The 5-lane context builder's memory lane is fed **only** from `recall()`.
2. A memory written on turn N must appear in turn N+1's memory lane. If it
   does not, the loop is not closed and the feature is not done.

---

## 4. INVARIANT — real endpoints only

| Store | remember | recall | forget |
|---|---|---|---|
| SFM | `POST {SFM_URL}/memories` | `POST {SFM_URL}/memories/search` | `DELETE {SFM_URL}/memories/{coord}` |
| Brain | `POST {SOMABRAIN_URL}/memory/remember` | `POST {SOMABRAIN_URL}/memory/recall` | `POST {SOMABRAIN_URL}/memory/forget` |

1. **Dead dialect — never call it:** `/api/v1/store`, `/api/v1/search`
   (existed only in `infra/mocks/`), and `/api/remember`, `/api/recall`
   (zero routes in somabrain — `BrainBridge` was calling ghosts).
2. Brain routers are mounted at `/memory/` (`somabrain/api/v1.py:96,104`).
   `urls.py` also mounts at `""`, so `/api/memory/*` and `/memory/*` are the
   same handler — pick **one** and use it consistently.
3. `infra/mocks/` is test-only. Proof paths run against real services.

---

## 5. INVARIANT — DTO format

Authored in `services/common/memory_contract.py`. Exact shapes:

```python
class MemoryWrite(BaseModel):
    text: str
    kind: Literal["episodic", "semantic", "belief"] = "episodic"
    tenant_id: str
    session_id: str | None = None
    coord: str
    embedding: list[float] | None = None
    salience: float = 0.5
    source: str = "agent-chat"

class MemoryHit(BaseModel):
    text: str
    coord: str
    score: float
    store: Literal["somabrain", "somafractalmemory"]
    created_at: str

class MemoryAck(BaseModel):
    coord: str
    store: Literal["somabrain", "somafractalmemory"]
    ok: bool
    error: str | None = None
```

1. `store` is **typed**, never bare `str`.
2. `kind` is **typed**, never a comment listing allowed values.
3. No field may be added without updating both adapters **and** the SFM request
   schema **and** the brain request schema in the same change.
4. Field mapping onto SFM's store request
   (`somafractalmemory/api/schemas.py:22` `MemoryStoreRequest`) — verified
   against the live service on 2026-09-26:

   ```python
   class MemoryStoreRequest(BaseModel):
       coord: str
       payload: dict[str, Any]          # NOT a string — a free-form JSON dict
       memory_type: Literal["episodic", "semantic", "belief"] = "episodic"
       embedding: list[float] | None    # FIRST-CLASS — written verbatim to Milvus
       tenant_id: str | None
   ```

   | `MemoryWrite` | SFM request |
   |---|---|
   | `coord` | `coord` |
   | `kind` | `memory_type` |
   | `tenant_id` | `tenant_id` |
   | `embedding` | `embedding` ← **top level, never inside `payload`** |
   | `text`, `source`, `salience`, `session_id` | keys inside `payload` |

5. **The embedding MUST be sent at the top level.** Nesting it in `payload`
   is accepted (the dict is free-form) but silently drops it: SFM then falls
   back to `HashEmbedder` and ranks the record × 0.25. This bug shipped once
   already — see §8 defect 15.

---

## 6. INVARIANT — configuration

| Var | Meaning | Rule |
|---|---|---|
| `SOMABRAIN_URL` | brain base URL | no localhost fallback (VIBE Rule 91) |
| `SFM_URL` (alias `SOMAFRACTALMEMORY_URL`) | memory base URL | no localhost fallback |
| `MEM_EMBED_DIM` / `SOMA_VECTOR_DIM` | vector dim | must match, default 256 |
| `SOMA_API_TOKEN` | SFM bearer | Vault/env only |
| `SOMABRAIN_MEMORY_HTTP_TOKEN` | brain bearer | Vault/env only |
| `GROQ_API_KEY` | Groq | Vault `secret/agent/api_keys` field `groq_api_key` — **never** in a file |

1. Missing URL → `MemoryConfigurationError` (fail-closed). Never silently no-op.
2. No secret is ever committed. CI greps `gsk_[A-Za-z0-9]{16,}`.

---

## 7. INVARIANT — model string

The model string passed to LiteLLM is **three segments**:

```
groq/openai/gpt-oss-120b
```

1. `LLMModelConfig.name` holds **Groq's own model id** — `openai/gpt-oss-120b`
   (the `openai/` is part of the id, not a provider).
2. `chat_orchestrator.py:435` builds `f"{model.provider}/{model.name}"`.
3. A bare `gpt-oss-120b` produces `groq/gpt-oss-120b` → Groq **model_not_found**.
4. `parallel_tool_calls: false` for gpt-oss (Groq limitation). Do not put
   non-API keys in `kwargs` — they are splatted into `litellm.completion(**kwargs)`.

---

## 8. Defects

### Resolved 2026-09-26 (W1-4 — orchestrator wiring)

| # | Defect | Fix |
|---|---|---|
| 1 | `chat_orchestrator._make_coordinate` — copy-pasted **MD5** coord writer, byte-identical to `scripts/generate_somafractal_image.py:23` | **Deleted**, along with its only caller `_store_to_sfm`. Coordinates now come only from `memory_contract.make_coord()` / `remember_text()`. |
| 2 | `_queue_pending_memory` idempotency key embedded a **UUID** | Key is now `mem:{tenant_id}:{coord}:{retry_store}` — re-queues and double-runs collapse. |
| 3 | `_store_turn` wrote "brain primary / SFM fallback" | Rewritten: both memory units take ONE path, `_remember_via_gateway()` → `remember_text()` fan-out with per-store acks. `PendingMemory` queued only for failed acks. |
| 4 | Memory lane not fed from `recall()` | `_recall_memories()` → `gateway.recall()` runs **before** `build_context` in both `process_turn` and `stream_turn`; `builder._format_memory_hits()` fits hits to the cl100k memory budget. |
| 5 | `memory_created` signal → `OutboxMessage("somabrain.memory.remember")` was a **second unconditional write authority** | Emission removed at both sites. `conversation_message` kept. |

### Still open

| # | Defect | Owner | Consequence |
|---|---|---|---|
| 6 | **Second chat pipeline.** `ProcessMessageUseCase` (`application/use_cases/conversation/process_message.py:323,353`) writes via `self._memory_client.remember(payload)` — it does **not** use the seam. Live only under `services/conversation_worker/` (Temporal), which is **not** in the compose/k8s topology. If that worker is ever deployed it bypasses `MemoryGateway` entirely. | next pass | duplicate/unsynced memories |
| 7 | `BrainClientProtocol` + `MemoryClientProtocol` (`context/builder.py`) still declared; DI args kept for tests | next pass | 2nd/3rd dialect on paper |
| 8 | `BrainServiceProtocol` + `MemoryServiceProtocol` (`services/common/protocols/__init__.py:20,66`) | next pass | 3rd/4th dialect on paper |
| 9 | `delete_provider_key` path ≠ `set_provider_key` path | secret-manager | keys not deletable |
| 10 | `MessageModel.coordinate` holds message **text** | schema | blocks real coords |
| 11 | **Deployed SFM image predates the embedding contract — CONFIRMED live 2026-09-26.** `docker exec` shows the running `MemoryStoreRequest` has only `coord`/`payload`/`memory_type: Literal["episodic","semantic"]` — no `embedding`, no `tenant_id`, no `"belief"`. Rebuild in progress. | ops | precomputed vectors dropped |
| 12 | `somabrain_client.py:270` mints memory ids with MD5 (`mem_{md5}[:16]`) | later | ids collide across writers |
| 13 | Outbox retry re-fans-out to **both** stores, so an already-acked store is written again. Safe only because identical `(tenant, kind, ts, text)` upserts the same coord/key row. Want `remember_text(..., stores=[...])` for strict "successful ack never written again". | W1-1 | duplicate write traffic |
| 14 | `scripts/generate_somafractal_image.py:23` still holds a third MD5 `make_coordinate` (generator script, not in the write path) | later | traps the next copy-paste |
| 15 | **`sfm_adapter.remember()` nested `embedding` inside `payload`** with a comment claiming "the live schema has no first-class embedding field yet" — it does. SFM accepted the write and silently hash-embedded, ranking it × 0.25. | fixed 2026-09-26 | recall returned noise |
| 16 | **Hardcoded credential defaults in committed source** — `config/settings.py` had `"sfm-api-token-123"` twice and `"soma-root-token-2024"` for `VAULT_TOKEN`, plus localhost fallbacks on both store URLs (VIBE Rule 91). | fixed 2026-09-26 | secret in git; silent localhost calls |
| 17 | `config/settings.py:28` hardcodes `AAAS_DEFAULT_TENANT_ID` as a UUID literal | next pass | tenant fixed in source |

**Scope note — what "one write path" actually covers today.** The chat
pipeline (`ChatOrchestrator`, served by `admin/chat/api/chat.py` and
`services/gateway/consumers/chat.py`) writes **only** through `MemoryGateway`.
These other `.remember()` call sites are *different concerns*, not chat
duplication, and each needs its own decision rather than a blind rewrite:

| Call site | Concern | Verdict |
|---|---|---|
| `helpers/memory_stores.py:370` | document/RAG ingest (`doc.page_content`) | migrate to the seam |
| `tool_executor/result_publisher.py:236` | tool-output capture | migrate to the seam |
| `agents/services/somabrain_integration.py:133` | `api/migrate.py` only | migrate or delete |
| `somabrain/api_router.py:201` | HTTP surface for external callers | keep — it is a *server* |
| `application/.../process_message.py:323,353` | Temporal chat worker | **defect #6** |

---

## 9. Definition of done

A feature is done when, against **real** services (no mocks):

1. One chat turn with a real Groq model stores a memory.
2. Both stores ack it — or the failed ack is queued and retried.
3. The next turn's context contains that memory in the memory lane.
4. `pytest tests/e2e/test_triad_integration.py` is green.
5. No second coordinate scheme, no second embedding path, no second protocol.
