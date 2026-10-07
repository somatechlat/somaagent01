# SOMA-AGENT-HANDOFF-001 — Handoff to the next agent

| Field | Value |
|---|---|
| Document Title | Soma Triad — full handoff for the next agent |
| Document Identifier | SOMA-AGENT-HANDOFF-001 |
| Version | 1.0.0 |
| Date | 2026-10-07 |
| Status | Active |
| Author | SomaTech Engineering |
| Classification | Internal |
| Scope | somaAgent01 · somabrain · somafractalmemory |
| Authority | `docs/standards/SOMA-STD-CODING-001.md` (VIBE) · `docs/standards/SOMA-RAPID-DEVELOPMENT-001.md` · `docs/standards/SOMA-STD-CONFIG-001.md` |
| Coordination | `somabrain/docs/plans/a2a/` — CLAIMS · INBOX · OUTBOX · LEDGER |

---

## 0. Read this before you write a single line

Three agents worked this triad for two days. The code is better and **still broken in one place that makes memory unusable in conversation**. Everything below is measured, not assumed. Where I say "verified", I ran the command and saw the output.

**The one-sentence state:**

> Chat streams, the brain saves and learns, long-term memory is durable across restarts — **but SFM writes 500, so the agent cannot remember anything in a conversation.**

---

## 1. NON-NEGOTIABLE CONDITIONS

These are not preferences. Every one of them has already been violated once, by me, and caused real damage.

### Rule 1 — NO HARDCODED VALUES. ANYWHERE.
A default **is** a hardcoded value. No literal URL, host, port, path, **or number** in application code.

| Forbidden | Instead |
|---|---|
| `http://localhost:20882`, `:30101` | required env/setting — no default |
| `os.environ.get("X", "default")` | `os.environ.get("X")` and fail closed, or `require_env("X")` |
| `get_memory_setting("X", 5.0)` | `get_memory_setting("X")` |
| `max_workers=1`, `timeout=30` | a named setting, read through the chain |
| `getattr(settings, X, "http://…")` | resolve through the chain or raise |
| `${VAR:-somabrain}` | `${VAR:?set VAR}` |

**R-VAL-04 is the only exception:** an *optional* key's default lives at the **declaration site** (`config/settings.py`, `SettingsModel`, `somabrain/settings/*.py`) and nowhere else. Never at a call site.

`DEFAULT_MEM_EMBED_DIM = 768` in `services/common/memory_contract.py` **is** legal and **must not be deleted** — `tests/unit/test_embed_dim_seam_768.py` asserts it is the *only* place 768 appears as a default (ADR-001).

### Rule 2 — NO FALLBACKS.
A value comes from a real setting or the call **refuses**. Deleting a fallback is always correct; replacing one is not.

### Rule 3 — ONE SETTINGS CHAIN.
```
Capsule (persona_config.settings / memory_pointer)
  → AgentSetting (ORM, per-agent)
    → InfrastructureConfig (the OPERATOR layer — admin-editable)
      → SettingsModel
        → RAISE, naming the setting
```
- **Env is topology only** (URLs, hosts, ports, addressing namespaces). R-OWN-02.
- **Django settings is the authority after boot.** R-OWN-01.
- **Secrets are Vault only.** R-OWN-03. Never `os.environ`, never a file, never `/tmp`.
- **Never invent a setting name.** Grep `config/settings.py`, `admin/core/helpers/settings_model.py`, `somabrain/settings/*.py` FIRST. AP-01's real incident: someone wrote `MEM_RECALL_LIMIT` while `MEM_RECALL_TOP_K` already existed.
- **One vocabulary per concept** (AP-06). Two names for one thing is where drift starts.

`require_setting(name, *, capsule=..., agent_id=...)` — **pass `capsule` and `agent_id`**. Calling it bare skips Capsule and AgentSetting entirely.

### Rule 4 — NO STUBS, MOCKS, SHIMS, BYPASSSES, PLACEHOLDERS, TODOs.
A shim is a bypass. Fix the consumer; never keep the old path alive.
**No invention of any kind.** Inspect the real API, use it, delete the workaround. (I invented three helper functions to unwrap a pymilvus return value instead of reading its API. It is a dict. `result["ids"]` was the answer all along.)

### Rule 5 — SECRETS: VAULT ONLY.
- KV v2 `POST` **replaces the whole document.** Read → merge → write full object → **read back and assert every key survived.** This has already caused data loss.
- Never write a secret to any file including `/tmp`. (I did. It was wrong.)
- `VAULT_TOKEN` env is banned; `VAULT_TOKEN_FILE` only.
- Never log a full token — truncate to 8 chars.

### Rule 6 — FAIL-CLOSED (Rule 91).
A missing required value is a refusal **naming the setting**. Never guess a host.

### Rule 7 — NEVER WEAKEN A GATE TO PASS A TEST.
Absent credential ⇒ failure naming it. No dummy, no skip, no fake state.

### Rule 8 — CHECK FIRST, CODE SECOND.
Read the architecture and the whole file before you touch it. If context is missing, **ask**.

### Rule 9 — NO UNNECESSARY FILES. **DELETE, DO NOT BACK UP.**
Duplicates get deleted and recoded. Never leave a compatibility alias.

### Rule 10 — DOCUMENTATION = TRUTH.
No invented APIs, routes, or field counts. If you cannot verify it, say so.

### Rule 11 — COMMITS.
The owner's own git identity. **No AI attribution of any kind** — no `Co-Authored-By`, no "Generated with Claude Code", no session links. (I put one in. It was wrong.)

### Rule 12 — DESIGN CRITERIA on every decision:
**the rules · millions of transactions · security · speed · latency · thin.**

### THE ONE PATH — never create a lane
```
browser → WS /ws/v2/chat/{capsule_id} → ChatConsumer → V3ChatOrchestrator
  → run_tool_loop → FanoutMemoryGateway → SomaBrainAdapter → SomaBrain → SFM
```
Forbidden: new WS route · new chat consumer · new orchestrator · new memory client · direct SFM connection · new auth check · new role store · new settings resolver · temporary endpoint · parallel config · test-only override · fake Vault · dummy credential.

> **"A bypass is the same violation as a mock."**

Every agent ends its report with: *"I connected via the existing chain, and did not create a new lane."*

---

## 2. THE ARCHITECTURE (verified)

### Memory lane
```
ChatOrchestrator → MemoryGateway → SomaBrainAdapter → POST /memory/{remember,recall,forget}
                                                    → SomaBrain → POST /memories* → SFM (Milvus)
```
**T-1:** SomaBrain is the sole writer to SFM. The agent holds **no** SFM client. `sfm_adapter.py` was deleted 2026-09-27 for this reason. Do not resurrect it.

### Embedding (T-3)
Computed **once** in the gateway by `embed_text()` (`services/common/memory_contract.py`) — SHA-256 token bag-of-words, L2-normalised. Dimension **768** (`MEM_EMBED_DIM` == `SOMA_VECTOR_DIM` == `DEFAULT_MEM_EMBED_DIM`). Sent **precomputed**, top-level, never nested in `payload`.

⚠️ **This embedder is not semantic.** Measured: `embed_text("dog bites man")` vs `embed_text("man bites dog")` → **cos 1.0**. It is lexical feature-hashing. Never present its score as semantic similarity.

### Coordinate (T-2) — **NOT MET**
```
make_coord(tenant_id, kind, ts, text) → BLAKE2b digest_size=12 → 3 floats in [-1,1)³
```
**Two `_stable_coord` definitions exist:**
- `somaAgent01/services/common/memory_contract.py:164` ← authority
- `somabrain/somabrain/memory/client/serialization.py:9`

They produce **byte-identical** output (verified). But T-2 says *"one shared module imported by all three repos. No copy, no comment-agreement."* Docs claim "T-2 MET" — **the docs are wrong.** The shared `soma-memory-contract` package does not exist.

### Idempotency (T-6)
Dedupe key **must** be `f"mem:{coord}"` — not a UUID. *"a random suffix makes the outbox multiply memories."*

---

## 3. WHAT IS DONE — verified live

| Area | State | Evidence |
|---|---|---|
| Admin API boots | ✅ | `import admin.api` OK — was `PydanticUserError: Optional not defined` |
| Shared credential | ✅ | agent == brain == t=0, len 64, byte-identical (was 17 vs 64 → 401 everywhere) |
| Auth anti-enumeration | ✅ | uniform `401 "Invalid credentials"`; `retry_after` audit-only |
| AgentIQ panel | ✅ | `GET /api/v2/core/agentiq` 200, 4 knobs → 10 derived, brain-learned lanes (was 500, every chip a dash) |
| Brain learning | ✅ | `/context/feedback` → `{"accepted": true, "adaptation_applied": true}` |
| Brain co-processing | ✅ | `/context/evaluate` 200 |
| Brain health | ✅ | `healthy 11/11` (was `critical`) |
| Brain saves | ✅ | `memory.store: 1196 sent` |
| Learnable knobs | ✅ | `brain_settings` seeded, 4 tenants × 143–147 |
| LTM durable | ✅ | `CODEWORD-DURABLE-99` at coord `0.41,0.42,0.43` recalled after **many** brain restarts |
| T-5 fail-closed | ✅ | `return []` and `or "default"` swept from the boundary |
| Tenants | ✅ | `getattr(graph_client,"tenant_id","default")` always missed → **all tenants folded into one partition**. Fixed. |
| Lanes | ✅ | one vocabulary; fixed token-loss and token-invention in the budget |
| RBAC | ✅ | `_ADMIN_FLOOR` discarded; `system:configure` exclusive to sysadmin, `org:manage` to org_admin |
| UI honesty | ✅ | 20+ invented values removed; `tsc --noEmit` exit 0 |
| Image secrets | ✅ | `.dockerignore` was **gitignored** — 3 stacks baked credentials into layers |
| Coord in somabrain | ✅ | 2 definitions → 1, wrapper **deleted** not aliased |

Unit suite: **615 → 642 passed**, failures 20 → 2.

---

## 4. WHAT IS OPEN — with exact anchors

### 🔴 P0 — SFM writes 500. Memory unusable in conversation.
```
MilvusVectorStore.insert() returns OmitZeroDict{'insert_count':1,'ids':RepeatedScalarContainer([...]),'cost':0}
services.py stored it verbatim into VectorEmbedding.milvus_id (BigIntegerField) → every write 500
```
- **Fix status:** `milvus_vector.py::insert()` now returns `int(result["ids"][0])` (real dict API). `services.py` stores it directly. All invented helpers (`_milvus_pk`, `_unwrap`, `_primary_key`) **deleted**. Written and compiling; **not yet proven live** — the image is baked and needs rebuild + `POST /memories` → 200 + `GET /memories/{coord}` → found.
- **Prove it:** write `CODEWORD-…` through the **chat**, then ask *"what did I ask you to remember?"* and show the actual reply. Not curl.

### 🔴 P0 — 37 rows with no vector
`VectorEmbedding absence detected  unindexed_memories=37` — written by the broken path, invisible to search, visible to coord lookup. Backfill or declare lost.

### 🟠 P1 — Query-side re-embed discards the store score
`somabrain/memory/client/ranking.py:386-448` re-embeds query and hits with `TinyDeterministicEmbedder` (a **third** algorithm) and overwrites `hit.score`. Missing text key → `new_score = 0.0` unconditionally.
Measured: recall scores **0.0189** where it should be ~1.0.
R-14b landed the contract (all three recall models accept `embedding`, wrong dim → 400). **The send side is missing:** `somabrain_adapter.recall` must send `embedding: embed_text(query, get_mem_embed_dim())` top-level.

### 🟠 P1 — `memory_hits` collapses outage and empty
`chat_orchestrator.py:1062-1073` serialises `None` **and** `[]` both as `"memory_hits": []`. `saas-memory-view.ts` maps a fetch error to *"No Memories Found"*. An outage renders the success-empty state. The sentinel `[Long-term memory unavailable this turn]` lives in the system prompt, not the DOM.

### 🟠 P1 — outbox terminal state is a lie
`workers/outbox_publisher.py:251-259` published to **Kafka topic `memory.store`** and marked `sent`. **Zero consumers of `memory.store`** exist (every subscriber enumerated). A builder added `_write_memory_to_store`; **verify it landed and that `sent` now means store-acked.**
Also: no in-flight status → stale `ev.save()` can reopen a `sent` row. `OUTBOX_MAX_RETRIES` (5) ends replay; `failed` is a dead state.

### 🟡 P2 — open, named
| Item | Anchor |
|---|---|
| Second `_stable_coord` (T-2) | `somabrain/memory/client/serialization.py:9` |
| `mem:{coord}` collides across topics | `graph.link`@X and `memory.store`@X share one slot |
| WAL replay re-stamps `ts` → new coord per replay | `services/memory_replicator/main.py:149-156` |
| `MemoryAck.durability` ignored by consumers | `memory_gateway.py:198` completes the WAL on `ok=True` |
| gRPC lane bypasses the outbox | `somabrain/transport/serve.py:155-157` |
| `wm.promote` enqueue fails (no dedupe key) | `somabrain/memory/promotion.py:437` |
| `outbox_replay.py` / `outbox_clean.py` are near-duplicates, nothing imports either | `admin.py:170` calls `outbox.mark_events_for_replay` which **does not exist** |
| `quantum.py:315` passes a **float** where a tenant is required | `BrainSetting.get("gmd_lambda_reg", default_lambda)` |
| ~15 more `or "default"` sites | `learning/dataset.py:80`, `adaptation/engine.py:72,82,103`, `constitution/__init__.py:206`, `event_store.py:269,311`, `learner_dlq.py:53`, … |
| Stale `somabrain:latest` image | code defaults for `MINIO_ENDPOINT`/`SCHEMA_REGISTRY_URL`; reads `VAULT_TOKEN` from ENV; writes secrets to `os.environ` (AP-05) |
| Temporal undeployed | the only outbox drain; also gates the existing A2A lane |
| `admin/auth/api.py` is 931 lines | Rule 245 caps at 650 |
| Docs describe a fiction | "3 knobs → 12 derived" in 6 documents; reality is **4 → 10** (`rlm_iterations`, `cost_tier`, `thinking_budget` deliberately deleted) |
| `test_vector_clone_on_delete_failure.py` | still asserts the **lossy** delete-before-insert order |

---

## 5. TRAPS — what went wrong so you do not repeat it

| Mistake | Consequence |
|---|---|
| Hardcoded `max_workers=1`, `timeout=30` | Rule 1 violation |
| "Fixed" it by **inventing 4 setting names** | AP-01 — `MEM_HTTP_TIMEOUT` and `SOMABRAIN_CONSOLIDATION_TIMEOUT_S` already existed |
| `os.environ.get("X", "5.0")` in `config/settings.py` | R-OWN-06 — a code literal as a product default |
| `config/settings.py` had **22 duplicate declarations** | last-one-wins → everything `None` |
| Called `require_setting(name)` **without `capsule`/`agent_id`** | bypassed L2 — Capsule and AgentSetting unreachable |
| Invented `_milvus_pk` / `_unwrap` / `_primary_key` | three layers of shim instead of `result["ids"]` (it is a **dict**) |
| Used `hasattr(x, "__iter__")` on a C-extension container | False → silently returned the container |
| Tested memory with **curl**, not the conversation | "memory works" was true of the API and false of the product |
| Copied a secrets file to `/tmp` | Rule 164 |
| Put `Co-Authored-By` in a commit | Rule 11 |

**The pattern in all of these:** guessing instead of inspecting. Every single one was caught by looking at the real thing.

---

## 6. COORDINATION

`somabrain/docs/plans/a2a/` — use it. CLI: `a2a` on PATH (`claim`, `msg`, `out`, `ledger`, `status`, `handshake`).

```
a2a claim <path> <task>          # BEFORE large edits
a2a ledger <action> <detail>     # every commit
a2a msg <from> <to> <text>       # to a peer
```
- **Respect ACTIVE claims.** Mine are under `ClaudeCode`.
- **Never delete another agent's entries.** Append-only.
- **`A2A_AGENT` defaults to `MiMoCode`.** Set it or your rows are mislabelled (I did this).
- Peer: **MiMoCode** — owns W3 annealing, W6 cognition, `final sweep`, ADV-2 findings. Their C3 tenant-header authority is live and correct.

---

## 7. HOW TO VERIFY

Never claim a pass you did not see. Paste the real output.

```bash
# Rule 1 — must return nothing
grep -rnE 'https?://|localhost|127\.0\.0\.1|host\.docker\.internal|:[0-9]{4,5}' <files> | grep -v '^\s*#'
grep -rnE 'os\.environ\.get\([^)]*,[^)]+\)|\$\{[A-Z0-9_]+:-|getattr\([^,]+,[^,]+,\s*["'"'"']http' <files>
grep -rnE '(TIMEOUT|WORKERS|POOL|LIMIT|SIZE|THRESHOLD|RETRY|BUDGET|WEIGHT|PENALTY|DIM)[A-Z_]*\s*=|[=]\s*[0-9]+\.[0-9]+' <files>
```

Live stack: agent `20020` · brain `30101` · SFM `10101` · webui `20080`.
Login `test@soma.dev` / `testpassword123`.
Vaults **reseal on restart** — run `somaagent_vault_unseal` and `somabrain_standalone_vault_unseal` or nothing boots.

**Deploy with both compose files**, or the `somabrain` DNS alias is never applied:
```
docker compose -f docker-compose.yml -f docker-compose.shared-network.yml up -d
```

---

## 8. DEFINITION OF DONE

From `SOMA-ARCH-INVARIANTS-001.md` §9 — the real gate:

1. One `remember` ⇒ one row via SomaBrain
2. The next turn's memory lane contains that memory (fed **only** from `recall()`)
3. `pytest tests/e2e/test_triad_integration.py` green
4. No second coordinate scheme, no second embedding path, no second protocol

Owner's gate, verbatim: **"What codeword did I ask you to remember?" answers correctly — in the browser, through the conversation.**

And the standing bar: *"make all memory work perfectly · check somabrain it's saving and learning."* Somabrain **is** saving and learning. Memory is **not** yet perfect. That gap is your job.
