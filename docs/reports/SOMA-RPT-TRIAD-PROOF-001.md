# SOMA-RPT-TRIAD-PROOF-001 — somaAgent01 → SomaBrain → SomaFractalMemory live proof

**Date:** 2026-10-12T21:40Z
**Operator:** MiMoCode-tribo (A2A seat)
**Stack under test (live, untouched):** agent `:20020` · brain `:30101` · sfm `:10101`
**Credentials used:** `test@soma.dev` / `testpassword123` (agent session `ses_K-uzb1zqlxJekfj4iTPQ-VvWZWQmiQAVrq6EtjGIpX0`)
**LAW asserted:** T-1 (agent memory ONLY MemoryGateway → SomaBrainAdapter), T-6 (durable-before-hop, brain sole SFM writer), no shims/fakes/mocks, settings-chain only.

---

## 1. T-1 import law — ZERO SFM client in agent (services/ + admin/)

Command (rg, non-test):

```
rg -n '^\s*(from|import)\s+\S*(somafractal|fractalmemory|soma_fractal)' services/ admin/ config/
```

**Result: exit 1 (no matches).** There is no Python import of SomaFractalMemory anywhere in `services/` or `admin/`.

Non-import string/comment hits are documentation only — none is a client:

| file:line | nature |
|---|---|
| `services/common/memory_gateway.py:3` | docstring: "The agent never talks to SFM." |
| `services/common/adapters/__init__.py:5` | docstring: "SomaBrain is the sole bridge to somafractalmemory (T-1)." |
| `services/common/adapters/somabrain_adapter.py:75` | `ForgetResponse.store` default label `"somafractalmemory"` (store name, not a client) |
| `services/common/memory_contract.py:45` | `MemoryStoreName = Literal["somabrain", "somafractalmemory"]` (type label) |
| `services/tool_executor/memory_tools.py:509` | docstring: "Never calls somafractalmemory directly" |
| `admin/memory/api/memory.py:3` | docstring: "Agent never talks to somafractalmemory." |
| `services/gateway/settings.py:271-274` | `SOMAFRACTALMEMORY_URL = ""` — settings-chain key, empty, **never read by any client** |
| `admin/core/helpers/settings_model.py:224-225` | settings-model field (admin-owned parameter) |

Hardcoded SFM port scan (`rg '10101' services/ admin/ --glob '!*test*'`) → **no matches**.

**Memory path (the only one):**
`admin/memory/api/memory.py:53` → `services/common/memory_gateway.py:241 get_memory_gateway()` → `services/common/memory_gateway.py:233 SomaBrainAdapter(...)` → HTTP `POST {SOMABRAIN_URL}/memory/remember` (`services/common/adapters/somabrain_adapter.py:317`).

Chat write path: `admin/core/chat_orchestrator.py:1481-1536 _remember_via_gateway` → `MemoryGateway.remember_text` (one write path). Chat read path: `admin/core/chat_orchestrator.py:1548-1571 _recall_memories` → `MemoryGateway.recall`.

**Verdict 1: PASS.** T-1 holds. Agent speaks SomaBrain only.

---

## 2. Live remember → Brain `/memory/remember` → SFM hop

### 2a. HTTP proof (agent → Brain)

```
POST http://127.0.0.1:20020/api/v2/memory/save
Authorization: Bearer ses_K-uzb1zqlxJekfj4iTPQ-VvWZWQmiQAVrq6EtjGIpX0
{"text":"PROOF-TRIAD-1791840792-XYZZY live remember proof somaAgent01 MemoryGateway SomaBrain SFM hop",
 "kind":"episodic","salience":0.9}
```

**HTTP 200 response:**
```json
{"saved": true,
 "memory_id": "0.7558789788745344,0.42311042081564665,-0.2364507201127708",
 "tenant_id": "cb6fc5b8-9525-4e81-8b6d-8ccf86460e9c",
 "acks": [{"ok": true, "store": "somabrain",
           "coord": "0.7558789788745344,0.42311042081564665,-0.2364507201127708",
           "error": null}]}
```

The agent ack is `store=somabrain` (never `somafractalmemory`) — T-1 visible at the wire.

### 2b. Brain DB proof of the written coord (T-6 outbox = durable-before-hop)

```
docker exec somabrain-somabrain_standalone_postgres-1 psql -U somabrain -d somabrain \
  -c "SELECT id, topic, status, payload->>'key' FROM outbox_events
      WHERE payload::text LIKE '%PROOF-TRIAD-1791840792-XYZZY%';"
```

**Row:**
| id | topic | status | mem_key |
|---|---|---|---|
| 5 | `memory.store` | `failed`→replayed | `cb6fc5b8-…\|episodic\|2026-10-12 21:33:12.396685+00:00\|PROOF-TRIAD-1791840792-XYZZY live remember proof…` |

This is the seam coord key material in the Brain's SFM-write outbox — the write reached Brain and was queued for the SFM hop (T-6).

### 2c. Brain → SFM hop status — ATTEMPTED, FAIL-CLOSED (pre-existing defect)

Brain app log (same window):

```
ERROR memory_remember … Background LTM persist failed; outbox row stays pending for replay.
  tenant=standalone key=cb6fc5b8-…|PROOF-TRIAD-1791840792-XYZZY… event_id=5:
  Memory service unavailable (circuit open); queued locally for replay
…
RuntimeError: Memory service unavailable (remember persist failed): {'detail': 'Unauthorized'}
```

SFM API log:

```
WARNING django.request Unauthorized: /memories
172.28.0.3 - - "POST /memories HTTP/1.1" 401
```

SFM DB (`somafractalmemory` schema) after the write:

```
SELECT count(*) FROM sfm_memories;   → 0
```

**Root cause (code truth, both repos):**

| side | evidence |
|---|---|
| Brain sends bearer | `somabrain/somabrain/memory/sfm_auth.py:63-88` resolves Vault `memory_http_token` (= `somabrain_memory_http_token`). Live token sha256[:16] = `42a895c76e73d147`, len 43. |
| SFM expects bearer | `somafractalmemory/somafractalmemory/settings/django_core.py:174-176` `SOMA_API_TOKEN` from Vault `soma_api_token`. Live token sha256[:16] = `42a895c76e73d147`, len 43. **Same value — token is NOT the problem.** |
| SFM rejects anyway | `somafractalmemory/somafractalmemory/api/auth.py:55-62`: token matches, then `SOMA_BOUND_TENANT` is read; empty → `return None` → HTTP 401. |
| `SOMA_BOUND_TENANT` never seeded | `somafractalmemory/somafractalmemory/settings/django_core.py:185` `resolve_optional("SOMA_BOUND_TENANT")`; tunable default `None` (`settings/model.py:159-165`); **absent from** `somafractalmemory/infra/standalone/docker-compose.yml` environment block and from every seed script. Live value = empty. |

Secondary hazard if `SOMA_BOUND_TENANT` is simply set to a constant: `somafractalmemory/somafractalmemory/api/utils.py:70-80` then **403s** any caller whose `X-Soma-Tenant` ≠ the bound tenant, while Brain sends `X-Soma-Tenant = namespace` (`somabrain/somabrain/memory/client/core.py:36` `self.tenant = tenant or self.namespace`), e.g. `agent_e8b1845f_chat_history`. A one-line env fix alone is not sufficient — the binding contract must be reconciled (Brain must present the bound tenant, or SFM must define the standalone tenant policy).

**Verdict 2: PARTIAL.**
- Agent → Brain `/memory/remember`: **PASS** (HTTP 200, ack ok).
- Brain durable accept + SFM-write queue (T-6): **PASS** (outbox row id=5, topic `memory.store`).
- Brain → SFM store hop: **FAIL (pre-existing)** — SFM 401 from unbound `SOMA_BOUND_TENANT`. Outbox row correctly stays pending for replay; no shim was introduced. Live stack was not modified.

---

## 3. Live recall → Brain → SFM search

```
POST http://127.0.0.1:20020/api/v2/memory/recall
{"query":"live remember proof somaAgent01 MemoryGateway","top_k":10}
```

**HTTP 200** (abridged):

```
total 4
 0.020985335370532796 STREAM-OK
-0.0017019193746972618 User: Remember this codeword: CHATWRITE-1791840792-XYZZY…
-0.004972357045660137 What is my name?
-0.05216683150538675  PROOF-TRIAD-1791840792-XYZZY live remember proof somaAgent01 MemoryGateway SomaB…
```

The written marker **is returned** through Agent → MemoryGateway → SomaBrainAdapter → Brain `/memory/recall`. `store` label on every hit is `"somabrain"`.

Caveat (same defect as §2c): Brain log shows `LTM recall failed for namespace=…: Memory search failed with status 401` and `LTM recall failed … Memory service unavailable (circuit open)`, so the hit is served from Brain working-memory, not from SFM `/memories/search`. SFM search cannot return the memory while auth rejects every caller and `sfm_memories` is empty.

**Verdict 3: PARTIAL.** Agent → Brain recall of the written memory: **PASS**. Brain → SFM search leg: **FAIL (same pre-existing 401)**.

---

## 4. Chat turn writes memory (live call)

```
POST /api/v2/chat/conversations          → {"id":"6df01afe-3e55-431d-b34d-bc1c49b5940c","memory_mode":"persistent", …}
POST /api/v2/chat/conversations/6df01afe-3e55-431d-b34d-bc1c49b5940c/messages
{"content":"Remember this codeword: CHATWRITE-1791840792-XYZZY. Reply with just the codeword.","stream":false}
```

**HTTP 200** assistant reply (model `mimo/mimo-v2.6-flash`) — includes the codeword. Orchestrator then wrote memory **independently of any tool**.

Brain DB outbox (same window):

| id | topic | status | mem_key (abbrev.) |
|---|---|---|---|
| 28 | `memory.store` | claimed | `…\|Remember this codeword: CHATWRITE-1791840792-XYZZY…` |
| 29 | `memory.store` | claimed | `…\|I tried to save it… Codeword: CHATWRITE-1791840792-XYZZY` |
| 30 | `memory.store` | claimed | `…\|User: Remember this codeword: CHATWRITE-… Assistant: …` |

Three real memory writes (user turn, assistant turn, dialogue pair) via `admin/core/chat_orchestrator.py:1506-1508 gateway.remember_text(...)`.

Side observation (not a memory-path mock): the LLM attempted a `memory_save` **tool** that is not registered in this session (`Tool 'memory_save' not found`). That is a tool-catalog gap in the model's toolbelt, not a memory-seam mock — the orchestrator's own write path is real and fired.

**Verdict 4: PASS.** Chat turn writes memory through MemoryGateway → Brain, durable outbox rows visible.

---

## 5. HARD DELETE mock/fake in production path

Commands over `services/` + `admin/` (non-test):

```
rg -n -i 'class .*(Mock|Fake|Stub|Shim|Null|Dummy|InMemory)|def (mock_|fake_|stub_)|MagicMock|unittest\.mock|@patch' \
  services/ admin/ --glob '!*test*'
→ exit 1 (no matches)

rg -n -i '\b(mock|fake|stub|shim|dummy|monkeypatch)\b' \
  services/common/memory_gateway.py services/common/adapters/ services/common/memory_contract.py \
  admin/memory/api/memory.py admin/core/chat_orchestrator.py services/common/chat_service.py
→ 1 hit, comment only:
  services/common/adapters/somabrain_adapter.py:12
  "It was carried by the BrainBridge stub in platform/brain.py, which is deleted"
  (historical note about a file already gone — not a live stub)
```

`platform/brain.py` does not exist. `build_memory_gateway()` constructs a real `SomaBrainAdapter` only (`services/common/memory_gateway.py:224-235`). URL resolution is fail-closed via `require_service_url("SOMABRAIN_URL")` (`somabrain_adapter.py:96-108`) — settings chain, no env fallback, no localhost default (VIBE Rule 91).

**Verdict 5: PASS.** No mock/fake/shim in the production memory path; nothing to hard-delete.

---

## Summary table

| # | Requirement | Result | Evidence |
|---|---|---|---|
| 1 | zero `somafractalmemory` imports in services/+admin/ (non-test) | **PASS** | rg exit 1; table §1 |
| 2 | live remember → Brain → SFM hop; coord in SFM **or** Brain DB | **PASS (Brain DB) / hop FAIL** | HTTP 200 §2a; outbox id=5 §2b; SFM 401 §2c |
| 3 | live recall → Brain → SFM search returns memory | **PASS (Brain) / SFM FAIL** | HTTP 200 hit list §3; SFM search 401 §2c |
| 4 | chat turn writes memory | **PASS** | outbox ids 28-30 §4 |
| 5 | no mock/fake in production path | **PASS** | rg exit 1 §5 |

**Overall: PROVEN for somaAgent01 (T-1 + T-6 agent side). One pre-existing live defect blocks the Brain→SFM store leg: SFM `SOMA_BOUND_TENANT` is unseeded, so `api/auth.py:57-62` fail-closes every caller with 401 even when the bearer matches.**

## Recommended follow-up (NOT done here — live stack must not be broken)

1. Seed `SOMA_BOUND_TENANT` for the SFM deployment (compose env or settings chain) **and** decide the binding contract: either Brain presents that exact tenant on `X-Soma-Tenant`, or SFM standalone must allow a documented tenant-selection policy (`api/utils.py:52-55` already describes the latter, contradicting `api/auth.py:57-62`).
2. After the auth contract is reconciled, let the outbox drain / memory-replicator replay `memory.store` rows — T-6 already preserved every write.
3. Re-run this proof; `sfm_memories` must then contain the `PROOF-TRIAD-*` / `CHATWRITE-*` keys.

**No commits. No live-stack changes. No shims introduced.**
