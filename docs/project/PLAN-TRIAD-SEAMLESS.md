# PLAN — Seamless Triad: Agent ↔ SomaBrain ↔ SomaFractalMemory

**Date:** 2026-09-26
**Owner:** somaplanet
**Goal:** One chat turn with a real Groq model stores memories in BOTH somabrain and
somafractalmemory and recalls them into the next turn — proven 100% by an automated test.

---

## 0. Why it is not seamless today (the mess we are collapsing)

| # | Break | Where |
|---|-------|-------|
| 1 | **Three API dialects** | Agent `SomaBrainClient` → `/memory/remember\|recall`; BrainBridge → `/api/remember\|recall`; agent SFM adapter → `/api/v1/store\|search` |
| 2 | **SFM endpoints called by the agent do not exist** | real SFM serves `/memories`, `/memories/search`, `/graph/*` (port 10101); `/api/v1/*` exists only in `infra/mocks/` |
| 3 | **Two coordinate writers** | coordinate scheme computed in both agent and SFM → collisions / misses |
| 4 | **Embedding contract broken** | SFM `HashEmbedder` = SHA-256 bag-of-words (not semantic); agent sends real vectors → distance is meaningless |
| 5 | **Two write authorities** | chat pipeline writes SFM directly + `PendingMemory` outbox writes again → duplicates |
| 6 | **Recall path unused** | 5-lane context builder has a memory lane but it is not fed from either store end-to-end |
| 7 | **Config split-brain** | mock ports (20996/20101) vs real ports (9696/10101); `SOMABRAIN_ENABLED=false` / `FRACTALMEMORY_ENABLED=false` in standalone `.env` |
| 8 | **Beliefs never reach AgentIQ** | cognitive loop emits `BeliefUpdate` but derivation never consumes it |

## 1. THE SEAM — one contract, two adapters (this is the simplification)

```
webui ──WS──► gateway consumer ──► ChatOrchestrator (12 phases)
                                      │
                        ┌─────────────┼──────────────┐
                        ▼             ▼              ▼
                  ModelRouter    MemoryGateway     ToolLoop
                 LLMModelConfig   (ONE interface)  (currently dead)
                        │          ┌───┴───┐          │
                        ▼          ▼       ▼          ▼
                  Groq via      SomaBrain  SFM     tool_executor
                  LiteLLM      /api/* or  /memories*
                               /memory/*  (real)
```

**Rules of the seam:**

1. `services/common/memory_contract.py` is the **single authority** for
   `MemoryWrite`, `MemoryHit`, `MemoryAck`, `make_coord()`, `embed_text()`.
2. **Embedding computed ONCE** in the gateway, sent precomputed to both stores →
   both stores share one vector space. Dim = `MEM_EMBED_DIM` (default 256).
3. **Coordinate computed ONCE** via `make_coord(tenant, kind, ts, text)` — same
   function SFM uses to key rows. No second writer.
4. **One write path**: `ChatOrchestrator` → `MemoryGateway.remember()` →
   fan-out (brain + SFM) with per-store ack; `PendingMemory` outbox only retries
   failed acks (never a second write).
5. **One read path**: context memory lane → `MemoryGateway.recall()` → merge,
   dedupe by coord, rank by score.
6. **Env contract**: `SOMABRAIN_URL`, `SFM_URL`, `GROQ_API_KEY` (Vault-managed),
   `MEM_EMBED_DIM`. No localhost fallbacks, no mock ports in prod paths.

### Contract (authoritative — every Wave-1 agent implements this exact shape)

```python
class MemoryWrite(BaseModel):
    text: str
    kind: str = "episodic"            # episodic | semantic | belief
    tenant_id: str
    session_id: str | None = None
    coord: str                        # make_coord(...)
    embedding: list[float] | None     # dim == settings.MEM_EMBED_DIM
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
    store: str
    ok: bool
    error: str | None = None

class MemoryGateway(Protocol):
    async def remember(w: MemoryWrite) -> list[MemoryAck]: ...   # one entry, both stores
    async def recall(query: str, k: int, tenant_id: str) -> list[MemoryHit]: ...
    async def forget(coord: str, tenant_id: str) -> bool: ...
```

**HTTP mapping (adapters must call the REAL service, mocks are irrelevant):**

| Store | remember | recall | forget |
|-------|----------|--------|--------|
| SFM   | `POST {SFM_URL}/memories` | `POST {SFM_URL}/memories/search` | `DELETE {SFM_URL}/memories/{coord}` |
| Brain | verify live path (`/api/remember` vs `/memory/remember`), keep ONE, delete the other | same | `DELETE ...` if exists |

---

## 2. WAVES · POINTS · TODO

**Point codes:** `P0` blocks "chat + memories 100%" · `P1` parity/quality · `P2` polish.
**Effort:** story points 1 / 2 / 3 / 5 / 8.

### WAVE 1 — SEAM (P0 · 18 pts) — *"make the connection perfect"*

| ID | Pts | Todo | Agent |
|----|-----|------|-------|
| W1-1 | 5 | `services/common/memory_contract.py` + `MemoryGateway` + `SomaBrainAdapter` + `SFMAdapter` in somaAgent01; delete `/api/v1/*` dialect; single `make_coord`/`embed_text` | **seam-gateway** |
| W1-2 | 5 | somafractalmemory: align real `/memories`, `/memories/search` to accept precomputed embeddings + `coord`; tenant scoping; drop HashEmbedder as the only path | **sfm-contract** |
| W1-3 | 5 | somabrain: pick ONE remember/recall contract, make BrainBridge speak it, persist beliefs so recall returns them | **brain-contract** |
| W1-4 | 3 | ChatOrchestrator: `_store_to_sfm` → `MemoryGateway.remember()`; outbox retries only failed acks; recall feeds the memory lane | **orchestrator-wire** |
| W1-5 | 3 | Seam E2E test (TDD): chat turn → both stores contain the memory → next turn's context contains it | **seam-proof** |

**Exit criteria:** `pytest tests/e2e/test_triad_integration.py` green against real
services (not mocks); one memory written, both stores ack, recall returns it.

### WAVE 2 — REAL GROQ CHAT (P0 · 15 pts)

| ID | Pts | Todo | Agent |
|----|-----|------|-------|
| W2-1 | 3 | Seed `LLMModelConfig`: `groq/openai/gpt-oss-120b`, `groq/openai/gpt-oss-20b`, provider `groq`, capability flags, cost tier, priority | **groq-catalog** |
| W2-2 | 2 | Groq key into Vault `secret/agent/api_keys.groq_api_key`; `POST /llm-providers` path verified; **no key in files** | **vault-keys** |
| W2-3 | 5 | Make agent settings / `Capsule.chat_model` actually influence `select_model` (today they are ignored) — one config path | **model-routing** |
| W2-4 | 3 | `reasoning_format:"hidden"` when tools/JSON; timeouts + retries in `_astream`; circuit breaker on LLM calls | **litellm-hardening** |
| W2-5 | 2 | k8s/compose: `VAULT_ADDR`, `AAAS_DEFAULT_CHAT_MODEL`, model-seeding job; fail-closed `LLMNotConfiguredError` | **deploy-config** |

**Exit criteria:** chat streams from real Groq end-to-end; wrong model string fails
closed with a clear error; no API key anywhere in the repo.

### WAVE 3 — CLOSED LOOP (P0/P1 · 13 pts)

| ID | Pts | Todo | Agent |
|----|-----|------|-------|
| W3-1 | 5 | Phases 9–10 are no-ops: execute tool calls (`tools_for_llm` is built but never passed to `acompletion`) and format results | **tool-loop** |
| W3-2 | 3 | Beliefs → AgentIQ: `BeliefUpdate` consumed by derivation → intelligence/autonomy/resource settings | **belief-iq** |
| W3-3 | 3 | WS contract: ONE message shape (UI send + client dispatch + e2e all differ today) | **ws-contract** |
| W3-4 | 2 | WebUI renders streamed deltas (`_streamContent` is accumulated and never rendered) + markdown | **stream-render** |

**Exit criteria:** agent can call a tool mid-chat and show it; belief state changes
routing; UI shows live tokens.

### WAVE 4 — UI PARITY WITH AGENT ZERO (P1 · 21 pts)

Source inventory: `_research/agent-zero` @ `e3051fb` (888 webui files).

| ID | Pts | Todo | Agent |
|----|-----|------|-------|
| W4-1 | 5 | Screen parity matrix: every Agent Zero screen → our screen → improvement (chat, settings, providers, tools, memory, agents, logs) | **ux-inventory** |
| W4-2 | 5 | Chat screen: history, branches, regeneration, stop, tool-call cards, file/attachments | **ux-chat** |
| W4-3 | 5 | Settings: model/provider/API-key fields real (today fake rows), agent persona, memory toggles | **ux-settings** |
| W4-4 | 3 | Right panel: replace "coming soon" placeholders (memory inspector, tool log) | **ux-panel** |
| W4-5 | 3 | Login/logout real (`/auth/logout`, real identity instead of "John Doe") | **ux-auth** |

**Exit criteria:** every Agent Zero screen exists here, reimplemented on our stack,
with at least one improvement each — clone & better, not copy-paste.

### WAVE 5 — PROOF + OPS + ISO (P1/P2 · 13 pts)

| ID | Pts | Todo | Agent |
|----|-----|------|-------|
| W5-1 | 5 | Verification suite: "chat + memories 100%" — load, recall accuracy, both-store ack, degradation drill | **proof-suite** |
| W5-2 | 3 | Degradation doctrine: brain down / SFM down / LLM down → defined behavior, not crashes | **degradation** |
| W5-3 | 3 | ISO docs: Approver + Next Review filled, Revision History on OPS/RELEASE/VV, RTM, ADR template | **iso-close** |
| W5-4 | 2 | Multi-agent deploy: one capsule per thing, k8s manifests, health probes, rate limits | **deploy-fleet** |

**Exit criteria:** one command proves the end-state; docs pass the compliance
checklist; N agents run in parallel and all chat + memorize.

---

## 3. Rapid-development rules (how the agents run)

1. **Waves are barriers** — Wave N+1 starts when Wave N's exit test is green.
2. **Within a wave, agents are parallel** and own disjoint files.
3. **Contract first** — `memory_contract.py` from W1-1 is the shared spec; the
   brain/SFM agents implement to it, never invent a second dialect.
4. **No mocks in the proof path** — `infra/mocks/` is test-only; the exit criteria
   run against real somabrain + real somafractalmemory.
5. **No secrets in files, ever** — keys live in Vault; CI greps `gsk_[A-Za-z0-9]{16,}`.
6. **Every agent reports:** files changed, contract compliance, test results,
   blockers. Integration review after each wave.

## 4. Total

| Wave | Points | Blocks |
|------|--------|--------|
| 1 SEAM | 18 | everything |
| 2 GROQ | 15 | chat |
| 3 LOOP | 13 | "power of the agent" |
| 4 UI | 21 | parity promise |
| 5 PROOF | 13 | "100%" claim |
| **Total** | **80** | end-state |
