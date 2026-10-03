# Triad Full Integration — AGENT + BRAIN + MEMORY Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** One working agent chat, fully integrated with SomaBrain and SomaFractalMemory — every stub and fallback deleted, one write lane, one credential authority, one deploy, all settings centralized under RBAC, all UI/UX screens finished.

**Architecture:** The canonical lane is **T-1: Agent → SomaBrain → SFM**. SomaBrain is the sole writer to the store; the agent holds one adapter and never an SFM client. Embedding and coordinate are computed once in the seam (`services/common/memory_contract.py`). Transport is gRPC-over-UDS in standalone (kernel ACLs, mode 0600, no bearer) and gRPC-over-TCP+mTLS distributed. Secrets live only in Vault; every missing credential fails closed.

**Tech Stack:** Django 5 + Django Ninja, Django ORM, Milvus, Lit 3.x (3.3.3), HashiCorp Vault, gRPC, LiteLLM/Groq, Postgres 15, Redis, Vite 5 + TypeScript.

**Normative authority (read before touching code):**
- `docs/architecture/SOMA-ARCH-INVARIANTS-001.md` — T-1…T-8, open defects #6–#17
- `docs/iso/SOMA-TRIAD-ARCH-001.md` §4 target, §11 remediation R-01…R-10, §12 verification
- `docs/standards/SOMA-STD-CODING-001.md` — VIBE rules (no stubs, no mocks, no shims, fail-closed)
- `docs/project/SOMA-PM-PLAN-TRIAD-001.md` — waves W1–W5

**Definition of done** (`SOMA-ARCH-INVARIANTS-001.md` §9), against real services:
1. One chat turn with a real Groq model stores a memory.
2. Both stores ack it — or the failed ack is queued and retried.
3. The next turn's context contains that memory in the memory lane.
4. `pytest tests/e2e/test_triad_integration.py` is green.
5. No second coordinate scheme, no second embedding path, no second protocol.

---

## Measured state — 2026-10-03 (verified in the working tree, not from docs)

Do not redo what is already true. Do not trust the parity docs' "EXISTS" rows — several name views deleted in `4d01f09a`/`c4383eee`.

### Already done

| Item | Evidence |
|---|---|
| R-03 delete fake services | `infra/mocks/` absent |
| R-01 one write lane on the hot path | `memory_gateway.py:29-100` SomaBrain-only; `sfm_adapter.py` deleted |
| BrainBridge stub | `aaas/brain.py` gone |
| `unified_urls.py` fake mounts | gone |
| somabrain silent direct→HTTP fallback | now raises |
| somabrain/aaas + SFM/aaas (Lago/SaaS) | deleted (uncommitted) |
| Vault secret migration | zero live secret assignments in `.env` |
| **Tool loop IS wired** | `tool_calling.py:208` passes `tools=` into `acompletion`; results fed back |
| **Stream deltas ARE rendered** | `saas-chat.ts:1595,2379` live `_streamContent` → `saas-message` |
| **Markdown renderer IS real** | `webui/src/utils/markdown.ts` (XSS-safe, escape-first) |
| **Model provider UI IS real** | `saas-settings-models.ts` — providers, Vault write-only keys, slots, presets, catalog |

### Not done — these are the gaps this plan closes

| Gap | Evidence |
|---|---|
| **WS chat is completely broken** | `consumers/chat.py:579` passes `capsule_id=` to `ChatTurn`, which has no such field → `TypeError`, swallowed at `:648`. **No WS turn ever reaches `stream_turn`.** |
| Credential authority (401) | 3 Vault instances, 3 independently seeded tokens |
| R-02 one coordinate authority | 3 live `_stable_coord` + 1 `make_coordinate` |
| Defect #6 second chat pipeline | `process_message.py:250,280` bypasses the seam |
| `Capsule.chat_model` ignored | FK written by `admin/llm/api.py:570-580`, never read by `select_model` |
| Hardcoded fake model catalog | `model_router.py:217-259` (`gpt-4o`, `claude-sonnet-4`, …) |
| Django `Message` rows never written | history REST `GET /conversations/{id}/messages` returns empty |
| Tool-approval channel is a stub | `tool_calling.py:281-300` writes a fail-closed error; no future is ever created |
| Logout never calls the API | `saas-chat.ts:2046`, `main.ts:252` clear storage only — session survives |
| Attachments metadata-only | UI sends `{name,type,size}`, no bytes; capability detection always `{"text"}` |
| Right-rail surfaces | 8 required (UI-X-01…08), 2 exist |
| Settings editors | ~16–20 of 316 (5–6%) |
| Uncommitted work | 250 files: somaAgent01 61, somabrain 173, SFM 15 |

---

## Execution order

```
Phase 0  Land the working tree          (nothing is safe until this is done)
Phase 1  Unblock the chat path          (the TypeError — chat does not run at all)
Phase 2  Purge                          (stubs, fallbacks, lies, dead code)
Phase 3  One coordinate authority       (T-2 — R-02)
Phase 4  Close the second pipelines     (defects #6, #7, #8, #13)
Phase 5  One deploy, one Vault          (wires the triad live; kills the 401)
Phase 6  Make chat fully work           (model intent, transcript, controls)
Phase 7  Settings complete + RBAC
Phase 8  UI/UX complete
Phase 9  Proof, bounds, hardening       (T-6, T-7, T-8, degradation, DoD)
```

Waves are barriers: Phase N+1 starts when Phase N's exit test is green.

---

## Phase 0 — Land the working tree

**Why first:** ~250 files of finished de-SaaS, stub-removal and transport work sit uncommitted across three repos. One bad reset destroys weeks. R-10 is listed last in the remediation doc; in practice it must happen first.

**Rules:** `git status --porcelain` before every `git add`. Stage only your own lane. Assert `git show --name-only` touches nothing belonging to a peer session. No Claude attribution on any commit.

### Task 0.1 — Inventory and stage somaAgent01

**Step 1.** `git status --porcelain` → confirm 61 entries (37 M, 22 D, 2 ??).
**Step 2.** The two untracked files (`tests/unit/test_identity_local_login.py`, `tests/unit/test_redis_pool_loop_restart.py`) are test additions and belong with the batch.
**Step 3.** `python3 -m compileall admin services config tests -q` → zero errors.
**Step 4.** `pytest tests/unit -q --timeout=120` → record the number. If the suite needs a real credential it must **skip**, never pass on a dummy.
**Step 5.** Commit in logical slices (do not squash unrelated surgery):
- `refactor(admin): delete budget, features, integrations and audit surfaces`
- `fix(admin): route chat, memory and context through the memory seam`
- `test: drop FakeStore and keep only the claims that are pure`
- `fix(config): fail closed on MinIO endpoint and absent credentials`

### Task 0.2 — Land somabrain (173 entries)
`python3 -m compileall somabrain -q`. Slices: `refactor(brain): delete the aaas commerce surface`, `feat(brain): gRPC transport with UDS and TCP bindings`, `fix(brain): one field assembly for every store body`. Assert `git show --name-only` stays inside `somabrain/`.

### Task 0.3 — Land somafractalmemory (15 entries)
Include the untracked `somafractalmemory/migrations/0006_drop_apikey_usagerecord.py`. Slices: `refactor(sfm): delete the aaas product surface`, `fix(sfm): no credential defaults in django settings`.

### Task 0.4 — Exit

```bash
for r in somaAgent01 somabrain somafractalmemory; do
  git -C ../$r status --porcelain | wc -l   # expect 0
done
```

---

## Phase 1 — Unblock the chat path (highest priority)

**The single defect that makes "the agent chat" not work at all.** Everything else in this plan is unreachable until this is fixed.

### Task 1.1 — Fix the `ChatTurn` TypeError

**Files:**
- Modify: `services/gateway/consumers/chat.py:570-581`
- Test: `tests/unit/test_ws_chat_turn_construction.py`

**Defect (verified):** `_handle_chat` builds:

```python
turn = ChatTurn(
    capsule=self.capsule,
    ...
    capsule_id=self.agent_id,          # ← NOT a ChatTurn field
    agent_mode=agent_mode,
)
```

`ChatTurn` is a plain `@dataclass` (`admin/core/chat_orchestrator.py:150-175`) whose fields are `capsule, iq_settings, tool_registry, user_id, tenant_id, user_message, conversation_id, attachments, history, agent_mode`. There is no `capsule_id` and no custom `__init__`. The call raises `TypeError`, which is swallowed at `consumers/chat.py:648-651` (`except Exception` → `internal_error` + `close(4000)`). **No WebSocket chat turn ever reaches `stream_turn`.**

**Step 1. Write the failing test:**

```python
from dataclasses import fields
from admin.core.chat_orchestrator import ChatTurn


def test_chat_turn_has_no_capsule_id_field():
    """consumers/chat.py must not pass capsule_id — ChatTurn carries a Capsule."""
    names = {f.name for f in fields(ChatTurn)}
    assert "capsule_id" not in names


def test_consumer_turn_kwargs_match_chatturn():
    """Every kwarg the consumer passes must exist on ChatTurn."""
    import inspect
    from admin.core.chat_orchestrator import ChatTurn
    allowed = {f.name for f in fields(ChatTurn)}
    # the consumer's construction site, spelled as it is in consumers/chat.py
    used = {
        "capsule", "iq_settings", "tool_registry", "user_id", "tenant_id",
        "user_message", "conversation_id", "history", "agent_mode",
    }
    assert used <= allowed
```

**Step 2. Run it.** Expected: FAIL — the second test models the real construction and would fail the moment `capsule_id` is reintroduced; add a direct assertion that `inspect.signature(ChatTurn).parameters` covers what the consumer passes, or better, refactor so the consumer calls a typed factory.

**Step 3. Implement.** Remove `capsule_id=self.agent_id`. The Capsule is already on the turn (`capsule=self.capsule`). If `agent_id` is genuinely needed downstream, add `agent_id: str = ""` to `ChatTurn` as a real field and pass that — never a name the dataclass does not declare.

**Prefer:** a factory `build_turn_from_consumer(consumer, content)` in `services/gateway/consumers/chat.py` that returns a `ChatTurn`, so a future field change breaks in one place.

**Step 4. Run tests.** PASS. Then drive one live WS turn end-to-end and confirm `stream_turn` is reached (not `internal_error`).

**Step 5. Commit.** `fix(chat): the websocket path reaches the orchestrator`

### Task 1.2 — Stop swallowing the pipeline

**Files:** `services/gateway/consumers/chat.py:648-651`

**Defect:** `except Exception` → generic `internal_error` hid the TypeError above for the entire time it existed.

**Step 1.** Log with `logger.exception` and include the exception type in the WS `error` payload code field (e.g. `code="internal_error"` plus a `detail` with `type(exc).__name__`). Never leak a stack trace to the client.
**Step 2.** Do **not** catch `TypeError`/`AttributeError` from turn construction — let a construction bug fail the test suite instead of the user.
**Step 3.** Commit: `fix(chat): surface the failure that hid the broken turn`

### Task 1.3 — Regression guard for the WS contract

**Files:** `tests/unit/test_ws_chat_turn_construction.py` (extend)

**Step 1.** Assert every inbound type the UI sends (`chat.message`, `chat.send`, `chat`, `feedback`, `ping`, control set) has a handler, and every outbound type the UI listens for is actually emitted somewhere in `consumers/chat.py`.
**Step 2.** This catches the already-known dead listeners: `title_update` and outbound `chat.message` are declared but never sent.
**Step 3.** Commit: `test: the ws contract is the contract`

### Phase 1 exit test

```bash
pytest tests/unit/test_ws_chat_turn_construction.py -v
# then, live: one WS chat turn returns chat.delta and chat.done, never internal_error
```

---

## Phase 2 — Purge everything that is stub, fallback, or a lie

### Task 2.1 — Delete the hardcoded model catalog (BLOCKER)

**Files:** `admin/core/model_router.py:143-144`, `:217-259`
**Test:** `tests/unit/test_model_router_fail_closed.py`

**Defect (verified):** `_get_fallback_catalog()` returns five fabricated rows (`gpt-4o`, `claude-sonnet-4-20250514`, `gpt-4o-mini`, `gemini-2.5-flash`, `llama-3.3-70b`) with invented priorities and cost tiers. On `ImportError` from the ORM, chat proceeds as if a real catalog were configured. This is exactly the hardcoded-value / fake-return pattern the rules forbid.

**Step 1. Write the failing test:** with the ORM unavailable, `select_model` must raise `NoCapableModelError` (or `LLMNotConfiguredError`), never return a fabricated model.

```python
import pytest
from admin.core.model_router import select_model, NoCapableModelError


@pytest.mark.asyncio
async def test_select_model_refuses_without_orm(monkeypatch):
    import admin.core.model_router as mr

    def _boom(*_a, **_k):
        raise ImportError("no orm")

    monkeypatch.setattr(mr, "_load_active_models", _boom)
    with pytest.raises(NoCapableModelError):
        await select_model(required_capabilities={"text"})
```

**Step 2. Run it.** Expected: FAIL — the fallback catalog currently returns rows.
**Step 3. Implement.** Delete `_get_fallback_catalog` entirely. Replace the `except ImportError` branch with a raise chained from the import error.
**Step 4.** `pytest tests/unit/test_model_router_fail_closed.py -v` → PASS.
**Step 5. Commit.** `fix(llm): fail closed when the model catalog is unavailable`

### Task 2.2 — Make `Capsule.chat_model` actually select the model

**Files:** `admin/core/model_router.py:91-176`, `admin/core/chat_orchestrator.py:520-528`, `:841-848`
**Test:** `tests/unit/test_model_router_capsule.py`

**Defect (verified):** `select_model` reads `capsule_body["allowed_models"]` only. The FK `Capsule.chat_model` → `LLMModelConfig` (`admin/core/models/core.py:201-207`) is **written** by `admin/llm/api.py:570-580` and **never read**. Binding a chat model in the admin UI has zero effect on agent chat. AgentIQ `temperature`, `model_tier`, `max_tokens` are likewise dropped (`chat_orchestrator.py:407` logs `model_tier` and discards it; `get_chat_model(provider, name)` at `:584`/`:855` receives no temperature/max_tokens).

**Step 1. Write the failing test:** a Capsule with `chat_model` set forces that model when it is active and capable; `temperature`/`max_tokens` reach the LLM call kwargs.

**Step 2. Run it.** Expected: FAIL.

**Step 3. Implement.**
1. Add `preferred_model_id: int | None = None` to `select_model`. When set, prefer that model; fall through to the priority sort only if it is inactive or incapable — and log a warning, never silently ignore.
2. Add `prefer_cost_tier: str | None` at the call sites, sourced from `iq.model_tier` (the parameter already exists at `model_router.py:95` and is never passed).
3. Thread `temperature` / `max_tokens` from `DerivedSettings` into `get_chat_model(...)` / `acompletion`.

**Step 4. Run tests.** PASS.
**Step 5. Commit.** `fix(llm): capsule model intent and agent iq reach the model call`

### Task 2.3 — Rename the lying class

**Files:** `services/common/memory_gateway.py` + every importer.

`FanoutMemoryGateway` no longer fans out — its own docstring admits it (`memory_gateway.py:31`). A name that contradicts the code invites the next engineer to reintroduce fan-out.

**Step 1.** `grep -rn "FanoutMemoryGateway" --include="*.py"`.
**Step 2.** Rename the class to `BrainMemoryGateway` (keep `MemoryGateway` as the Protocol at `memory_contract.py:102`).
**Step 3.** `python3 -m compileall services admin -q` then `pytest tests/unit -q`.
**Step 4.** Commit: `refactor(memory): name the gateway for what it is`

### Task 2.4 — Close the dead control branches

Verified dead code in the chat path — each is either implemented or deleted, never left as a lie:

| # | Location | Problem | Verdict |
|---|---|---|---|
| 1 | `tool_calling.py:271-300` | tool-approval branch emits `tool.approval_request` then **immediately** writes a fail-closed error ("No approval channel yet") | **Implement** the round-trip: `run_tool_loop` awaits a future; `consumers/chat.py:708-719` resolves `self._tool_approvals`, which is currently only ever `pop`ped and never created |
| 2 | `consumers/chat.py:151` `_nudge_queue` | written on `chat.nudge`, **never drained** into the running turn | Implement (drain into `messages`) or delete the field and the inbound type |
| 3 | `consumers/chat.py:152` `_turn_task` | never assigned; `chat.stop`/`chat.reset` guard on it and are no-ops | Run the stream as `self._turn_task` so cancel works |
| 4 | `chat_orchestrator.py:608-610`, `:872-874` | `except CircuitBreakerError` around `run_tool_loop` — nothing in that path raises it (the CB only wraps `select_model`) | Wrap `_astream`/`run_tool_loop` in `self._cb_llm.call`, or delete the dead handler |
| 5 | `chat_orchestrator.py:624-625` | Phase 10 "Response Formatting" body is `result.phase_completed = 10` | Implement or delete the phase |
| 6 | `chat_orchestrator.py:437,458` | `suggested_tools` computed and never used | Feed into `tools_for_llm` ranking, or delete |
| 7 | `consumers/chat.py:74,77` | `MSG_CHAT_RESPONSE`/`MSG_TITLE_UPDATE` declared, never sent | Emit or delete |
| 8 | `default_tools.py:20` | `"response"` tool name with no handler in `AVAILABLE_TOOLS` | Delete the name |
| 9 | `chat_orchestrator.py:921-933` `_load_capsule` | DEPRECATED, unused | Delete |
| 10 | `chat_orchestrator.py:1245-1262` `trigger_sleep_cycle` | "should be called periodically" — no caller | Wire to a scheduler or delete |

**Step 1.** For each row: write the behaviour test first where it is an "implement", otherwise assert the symbol is gone.
**Step 2.** Implement or delete — never both a stub and a comment.
**Step 3.** Commit: `fix(chat): dead branches either work or are gone`

### Task 2.5 — De-mock the remaining test doubles (R-04)

Nine files still import `unittest.mock`/`MagicMock`/`monkeypatch.setattr`:
`tests/unit/test_deployment_mode_fail_closed.py`, `test_settings_model_drift.py`, `test_settings_conformance.py`, `test_settings_read_gate.py`, `test_settings_write_gate.py`, `test_identity_local_login.py`, `test_settings_changed_event.py`, `test_memory_contract.py`, `test_minio_object_store.py`

**Rule (R-04):** each is either (a) re-expressed against a real service with `pytest.skip` when unreachable, or (b) kept only if it proves a pure function with no doubles. Add a CI guard that greps the tree and fails on `unittest.mock|MagicMock` outside `tests/pure/`.

**Commit:** `test: behavioural claims run against real services`

### Task 2.6 — Sweep residual fail-opens

- `somabrain/settings/cognitive.py:73` — `SOMABRAIN_MEMORY_HTTP_TOKEN = env.str(..., default="")` → raise when unset and memory is required.
- `somabrain/settings/infra.py:98-102` — `except (SecretNotFound, VaultNotConfigured): pass` → raise. Silent env fallback is a bypass.

**Commit:** `fix(settings): a missing credential is a refusal, not an empty string`

### Phase 2 exit test

```bash
grep -rn "TODO\|FIXME\|NotImplementedError\|_get_fallback_catalog\|changeme" \
  admin services config --include="*.py" | grep -v tests/
# expect zero in production paths
python3 -m compileall admin services config -q
pytest tests/unit -q
```

---

## Phase 3 — One coordinate authority (T-2 / R-02)

**Verified live:** three `_stable_coord` definitions plus a fourth MD5 variant.

| Path | Repo |
|---|---|
| `services/common/memory_contract.py:143` | somaAgent01 |
| `somabrain/somabrain/memory/normalization.py:12` | somabrain |
| `somabrain/somabrain/memory/client/serialization.py:9` | somabrain (duplicate in the same repo) |
| `scripts/generate_somafractal_image.py:23` `make_coordinate` | somaAgent01 |

### Task 3.1 — One shared contract

**Step 1. Write the cross-repo contract test** — 32 fixed seeds; every repo must emit the identical coord string.

```python
# tests/contract/test_coord_across_repos.py
SEEDS = [
    (f"tenant{i}", "episodic", f"2026-10-03T00:{i:02d}:00Z", f"text {i}")
    for i in range(32)
]

def test_all_repos_agree_on_coords():
    from memory_contract import make_coord as agent_coord
    from somabrain.memory.normalization import make_coord as brain_coord
    for tenant, kind, ts, text in SEEDS:
        assert agent_coord(tenant, kind, ts, text) == brain_coord(tenant, kind, ts, text)
```

**Step 2. Run it.** Expected: FAIL.
**Step 3.** Publish one module (`soma-memory-contract`, or a single shared file mounted into all three images) exporting `_stable_coord`, `coord_to_str`, `coord_key_material`, `make_coord`, `DEFAULT_MEM_EMBED_DIM = 768`. Delete the two somabrain local copies and the script's MD5 variant.
**Step 4.** Verify: `grep -rn "def _stable_coord" ` across the three repos returns **exactly one** definition.
**Step 5.** Commit: `refactor(memory): one coordinate authority for the whole triad`

---

## Phase 4 — Close every second pipeline

### Task 4.1 — Defect #6: `ProcessMessageUseCase` bypasses the seam

**Files:** `admin/core/application/use_cases/conversation/process_message.py:233-310`, `services/conversation_worker/main.py:135`, `services/conversation_worker/temporal_worker.py:95`
**Test:** `tests/unit/test_process_message_uses_seam.py`

**Verified:** `self._memory_client.remember(payload)` at `:250` and `:280`, `recall` at `:310` — a second write authority, live only under the Temporal worker (not in the compose topology).

**Step 1.** Failing test: `ProcessMessageUseCase` must take a `MemoryGateway`, not a raw memory client.
**Step 2.** Change the constructor to `gateway: MemoryGateway`; delete `memory_client`. Route through `gateway.remember_text(...)` / `gateway.recall(...)`.
**Step 3.** Update both worker call sites to `build_memory_gateway()`.
**Step 4.** `grep -rn "_memory_client.remember\|_memory_client.recall" admin services` → zero.
**Step 5.** Commit: `fix(chat): the temporal worker writes through the memory seam`

### Task 4.2 — Defects #7 and #8: delete the paper protocols

**Files:** `admin/core/context/builder.py` (`BrainClientProtocol`, `MemoryClientProtocol`), `services/common/protocols/__init__.py:20,66` (`BrainServiceProtocol`, `MemoryServiceProtocol`)

A `Protocol` whose only implementer is the test is a stub surface. Rewire users to `MemoryGateway` / `SomaBrainAdapter` / `MemoryService` directly and delete all four.

**Commit:** `refactor(memory): one protocol, not four`

### Task 4.3 — Defect #13: outbox re-fans-out to a store that already acked

**Files:** `services/common/memory_gateway.py` `remember_text`, `admin/core/chat_orchestrator.py` retry path.

**Step 1.** Failing test: a write that acked is never re-sent when a later write fails and triggers a retry sweep.
**Step 2.** `remember_text(..., stores: Sequence[str] | None = None)`; the outbox retry passes `stores=[failed_store]` only.
**Commit:** `fix(memory): a successful ack is never written again`

### Task 4.4 — Defect #10 + #12

- `admin/chat/models.py` `MessageModel.coordinate` holds message **text** → rename or retype; it blocks real coords.
- `admin/core/somabrain_client.py:270` mints ids with MD5 (`mem_{md5}[:16]`) → use the seam coord, not a hash of the text.

**Commit:** `fix(memory): coordinates are coordinates`

---

## Phase 5 — One deploy, one Vault (kills the 401)

**Verified root cause:** three compose projects, three Vault instances, three independently seeded tokens.

| Vault | Compose project |
|---|---|
| `somaagent_vault` | `somaAgent01/infra/standalone/docker-compose.yml` |
| `somabrain_standalone_vault` | `somabrain/infra/standalone/docker-compose.yml` |
| `somafractalmemory-standalone-vault` | `somafractalmemory/infra/standalone/docker-compose.yml` |

The agent reads `somabrain_memory_http_token` from **its** Vault (`config/settings.py:61`); somabrain reads the same name from **env** (`somabrain/settings/cognitive.py:73`, `default=""`). Two authorities, two values → every call 401.

### Task 5.1 — One Vault, one credential authority

**Files:**
- Create: `infra/triad/docker-compose.yml`
- Modify: `somabrain/somabrain/settings/cognitive.py:73`, `django_core.py:75`
- Modify: `somabrain/somabrain/settings/infra.py:98-102`
- Modify: `infra/standalone/init_vault.py`

**Step 1. Write the failing integration test** — `tests/e2e/test_shared_credential.py`:

```python
def test_agent_token_is_accepted_by_brain():
    """One Vault, one value: the token the agent holds must open the brain."""
    # POST {SOMABRAIN_URL}/memory/recall with Authorization: Bearer <token from Vault>
    # expects 200, never 401
```

**Step 2. Run it against the current stack.** Expected: FAIL with 401.

**Step 3. Implement.**
1. One Vault container in the triad compose; agent and brain read the same KV path `secret/agent/credentials/somabrain_memory_http_token`.
2. somabrain stops reading the bearer from env with `default=""`. It reads from Vault and **raises** when absent.
3. Delete `except (SecretNotFound, VaultNotConfigured): pass`.
4. Remove the three per-service Vault services from the standalone composes.

**Step 4. Run the test.** PASS (200).
**Step 5. Commit.** `fix(auth): one credential authority for the whole triad`

### Task 5.2 — One docker line

**Requirement (user, verbatim):** *"the developers will only DEPLOY one docker line … one line and in 30 secs you have all running, all integrated."*

**Files:** `infra/triad/docker-compose.yml`, `Makefile` target `triad`

**Step 1.** `make triad` brings up: postgres, redis, milvus, **one** vault (+init/unseal), somabrain, somafractalmemory, somaagent, webui.
**Step 2.** One network: SFM at `http://somafractalmemory:10101`, brain at `http://somabrain:30101`.
**Step 3.** Health probes on every service; `make triad-status` prints one line each.
**Commit:** `feat(infra): one compose project for the whole triad`

### Task 5.3 — Standalone binding: gRPC over UDS

**Files:** `services/common/adapters/somabrain_adapter.py` (add the LOCAL binding alongside HTTP/NET)
**Reference:** `somabrain/somabrain/transport/port.py`, `uds.py`, `serve.py` — already implemented brain-side.

`BrainPort` already defines LOCAL (gRPC/UDS, mode 0600, **no bearer** — kernel ACLs, and the docstring is explicit that inventing one would be a dummy credential) and NET (gRPC/TCP + TLS 1.3 + Vault token). The agent still speaks HTTP only.

**Step 1.** `SOMA_DEPLOYMENT_MODE=LOCAL` → agent binds `BrainClient` over `/run/soma/brain.sock` via the shared `soma_run:/run/soma` volume.
**Step 2.** `SOMA_DEPLOYMENT_MODE=NET` → TCP + TLS + the one Vault service token. Absent credential is a refusal.
**Step 3.** Unset/unrecognised mode raises `TransportConfigurationError`.
**Step 4.** Integration test: write over UDS, read back over HTTP — same row, same coord (the brain already shares `MemoryService` across bindings).
**Commit:** `feat(transport): the agent speaks the brain's own binding`

### Task 5.4 — Restore agent health (R-09)

Rebuild all images from the landed tree. `docker compose -f infra/triad/docker-compose.yml ps` → every service healthy. (Today `somaagent_standalone` is unhealthy and the running image predates `start.sh`'s full-triad mode.)

### Phase 5 exit test — THE proof

```bash
pytest tests/e2e/test_triad_integration.py -v
```

Green against real services: one chat turn stores a memory, the brain acks, SFM holds the row, the next turn's context contains it.

---

## Phase 6 — Make chat fully work

### Task 6.1 — Persist the transcript (history is empty today)

**Defect (verified):** `_store_turn` writes only to MemoryGateway/SomaBrain and emits `conversation_message`. Nothing calls `Message.objects.create`. REST `GET /conversations/{id}/messages` (`admin/chat/api/chat.py:448-516`) and export (`:398-440`) therefore return **empty**. The comment at `chat.py:59-61` claiming the trace registrar stores turn text in `Message.coordinate` is false.

**Files:** `admin/core/chat_orchestrator.py` `_store_turn` (`:1123-1170`), `admin/chat/models.py`
**Test:** `tests/unit/test_transcript_persisted.py`

**Step 1.** Failing test: after `process_turn`, `Message.objects.filter(conversation_id=...)` holds the user turn and the assistant turn.
**Step 2.** Write `Message` rows in `_store_turn` (or make REST history read from the memory lane — but a real transcript table is the better answer for export and branching).
**Step 3.** Commit: `fix(chat): the transcript is persisted`

### Task 6.2 — Pass `attachments` through `ChatTurn`

**Defect (verified):** the UI sends `attachments` (`saas-chat.ts:1970`); `_handle_chat` never copies them onto `ChatTurn` (`consumers/chat.py:570-581` has no `attachments=`). `detect_required_capabilities` (`chat_orchestrator.py:754`) therefore always sees `{"text"}` — vision/audio/document routing is dead.

**Step 1.** Failing test: a turn with an image attachment yields `required_capabilities` including `vision`.
**Step 2.** Pass `attachments=payload.get("attachments") or []`.
**Step 3.** Commit: `fix(chat): attachments reach capability detection`

### Task 6.3 — Real file upload (UI sends metadata only)

**Defect (verified):** the composer collects real `File[]` but sends only `{name,type,size}` — no bytes, no upload endpoint. Server never receives file content.

**Step 1.** Add a real upload endpoint (Django Ninja) storing to the object store; return a handle the turn references.
**Step 2.** Composer posts bytes, then sends the handle on the turn.
**Step 3.** Commit: `feat(chat): attachments carry content`

### Task 6.4 — Stop / reset actually stop (UI is client-side only)

**Defect (verified):** `saas-chat.ts` `_stopTurn()` only flips a local flag and finalizes the bubble; **no WS frame is sent** (outgoing types are only `chat.message`, `chat.nudge`, `tool.approval`). The backend keeps generating. `_turn_task` is never assigned, so `chat.stop`/`chat.reset` are no-ops.

**Step 1.** Run the stream as `self._turn_task`; implement `chat.stop` to cancel it.
**Step 2.** UI sends `chat.stop`. Label pause honestly ("pause rendering") or remove it — it currently implies an interrupt that does not exist.
**Commit:** `fix(chat): stop stops`

### Task 6.5 — Tool approval round-trip (or delete it)

See Phase 2 Task 2.4 row 1. The UI already has approve/deny (`saas-chat.ts:1781-1785`) and the consumer has a resolver (`consumers/chat.py:708-719`); nothing creates the futures, so `run_tool_loop` (`tool_calling.py:281-300`) always fail-closes.

**Step 1.** Failing test: a tool with `approval_required` blocks until the UI resolves, and proceeds only on approve.
**Step 2.** Create the future in the consumer, hand it to the loop, await it with a timeout that fails closed.
**Commit:** `feat(tools): approval is a real round-trip`

### Phase 6 exit test

A WS chat turn streams tokens, writes `Message` rows, stores a memory through the seam, and a second turn recalls it; `GET /conversations/{id}/messages` returns both turns; stop cancels the stream.

---

## Phase 7 — Settings complete + RBAC

**Measured surface (2026-10-03).** Raw config reads outside the registry:

| Repo | `os.environ`/`os.getenv`/dotenv | `env.*` (django-environ) |
|---|---|---|
| somaAgent01 | ~489 (404 non-test) | 0 |
| somabrain | ~209 raw | 349 non-test |
| somafractalmemory | ~56 raw | 77 non-test |

### Task 7.1 — STOP WRITING SECRETS INTO ENV (Rule 164 violation, BLOCKER)

**Defect (verified at seven sites):** somabrain takes secrets **out of Vault** and writes them **into `os.environ`**:

| File:line | What is written |
|---|---|
| `somabrain/settings/infra.py:70` | `SOMABRAIN_POSTGRES_DSN` (embedded password) |
| `somabrain/settings/infra.py:77` | `SOMABRAIN_REDIS_URL` |
| `somabrain/settings/infra.py:29` | generic `_set_env_if_present` |
| `somabrain/settings/django_core.py:110` | `SOMABRAIN_POSTGRES_DSN` |
| `somabrain/settings/django_core.py:119-120` | `SOMABRAIN_JWT_SECRET`, `SECRET_KEY` |
| `somabrain/settings/django_core.py:130-131` | `SOMA_API_TOKEN`, `SOMABRAIN_API_TOKEN` |

SFM already removed the equivalent (`somafractalmemory/settings/infra.py:1-16` documents the correct pattern). A secret that is copied into ENV is a secret in ENV — the Vault migration is undone the moment the process starts.

**Step 1. Write the failing test:**

```python
def test_somabrain_never_writes_secrets_to_env(monkeypatch):
    """Rule 164: a secret is read from Vault and used, never exported."""
    import os, somabrain.settings.infra  # noqa: F401
    leaked = [k for k in os.environ if k in {
        "SOMABRAIN_POSTGRES_DSN", "SOMABRAIN_JWT_SECRET", "SECRET_KEY",
        "SOMA_API_TOKEN", "SOMABRAIN_API_TOKEN", "SOMABRAIN_REDIS_URL",
        "SUPERVISOR_HTTP_PASS", "OUTBOX_API_TOKEN",
    }]
    assert leaked == []
```

**Step 2. Run it.** Expected: FAIL.

**Step 3. Implement.** Resolve each secret from Vault at the point of use and hold it in a module-level setting object — never `os.environ`. Read-only properties, not exports.

**Step 4.** Also fix the two vault clients that read a token from env instead of a file:
- `somabrain/core/security/vault_client.py:67-69` (`SOMABRAIN_VAULT_TOKEN`/`VAULT_TOKEN`)
- `somafractalmemory/admin/core/security/vault_client.py:33`

somaAgent01 already does this correctly: token is **file-only** (`services/common/vault_secrets.py:38-42`).

**Step 5. Commit.** `fix(secrets): a secret is never copied into the environment`

### Task 7.2 — One Django settings module, one registry

**Defect (verified):** three Django settings modules run simultaneously in somaAgent01 and only one consults the registry:

| Module | env reads | Used by | Consults `SettingsRegistry`? |
|---|---|---|---|
| `services/gateway/settings.py` | 78 | `manage.py:10`, Makefile | **yes** (`:141-143`, DATABASES only) |
| `config/settings.py` | 64 | `config/asgi.py:10` | no |
| `infra/aaas/unified_settings.py` | 32 | AAAS wsgi/asgi | no |

`config/settings_registry.py` is the declared Rule-100 source of truth for topology. It is not being used as one.

**Step 1.** Map every key in `config/settings.py` and `infra/aaas/unified_settings.py` onto the registry (they already exist as `BaseSettings` fields at `config/settings_registry.py:72-163`).
**Step 2.** Make both modules delegate to `get_settings()` instead of `os.environ`.
**Step 3.** Delete `admin/core/helpers/dotenv.py`'s runtime read/write path (`admin/core/helpers/runtime.py:86-117,266,276` call `load_dotenv(override=True)` / `save_dotenv_value`). It contradicts `settings_registry.py:35-38` ("`.env` files carry no configuration").
**Commit:** `refactor(settings): one registry, one django settings module`

### Task 7.3 — One resolution chain

**Defect (verified):** two documented chains disagree about whether env participates:
- `admin/core/helpers/capsule_settings.py:3-9` — `Capsule > AgentSetting > Django > schema`
- `admin/core/helpers/settings_defaults.py:7-10` — `ORM > env > Django` (and its own header line 9 contradicts its normative docstring at `:100-106`)

**Step 1.** Unify on `Capsule > AgentSetting > Django > schema fallback`, implemented once in `capsule_settings.resolve_setting` (`:138-175`).
**Step 2.** Delete the silent swallows — each is fail-open:
  - `capsule_settings.py:162-163` `except Exception: pass` on AgentSetting lookup (DB down reads as "setting absent")
  - `capsule_settings.py:172-173` same for Django lookup
  - `settings.py:49-50` returns **stale cache** on failure
  - `settings_defaults.py:64-65, 95-96, 143-144` same pattern
  - `admin/llm/api.py:278-279` logs and continues with a default
  - `somabrain/django_core.py:224-225` `get_api_token()` returns `None` on failure
  - `somabrain/infra.py:102-104` `except (SecretNotFound, VaultNotConfigured): pass`
**Step 3.** Fail closed: a load-bearing lookup that fails raises. Only an explicitly optional feature may be absent, and then it is disabled, not defaulted.
**Commit:** `fix(settings): one chain, no swallowed lookups`

### Task 7.4 — `settings_registry.py` for somabrain and SFM

**Verified:** neither repo has one (grep for `settings_registry|SettingsRegistry` returns zero), although both `.env` headers claim one exists.

Mirror the `config/settings_registry.py` pattern — do not invent a second design. Replace the fabricated defaults:
- `somabrain/settings/service_registry.py:35-38` invents `http://localhost:<port>` in development
- `somabrain/runtime_config.py:5-11,50-92` — 3-layer fallback (Django → 4 env name candidates → caller default), parse errors return the default
- `somafractalmemory/settings/infra.py:27-103` — dozens of `default=` values, including model name `"microsoft/codebert-base"` at `:47` and mode `"evented_enterprise"` at `:46`
- `somafractalmemory/api/routers/health.py:126-128` — `localhost` defaults and `SOMA_REDIS_PASSWORD` from `os.environ`
- `somabrain/brain_settings/models.py:113-122` — tenant silently inherits `default` on miss

**Commit:** `feat(settings): registries for the brain and the store`

### Task 7.5 — Collapse the name forks

One name per concept across all three repos (verified live):

| Concept | Names in use today |
|---|---|
| Postgres host | `POSTGRES_HOST`, `SOMA_POSTGRES_HOST`, `TEST_DB_HOST`, `SOMA_DB_HOST` |
| Postgres DSN | `SOMABRAIN_POSTGRES_DSN`, `SOMA_POSTGRES_URL`, legacy `DATABASE_URL` |
| Redis URL | `REDIS_URL`, `SA01_REDIS_URL`, `SOMABRAIN_REDIS_URL` |
| Redis host | `REDIS_HOST`, `SOMABRAIN_REDIS_HOST`, `SOMA_REDIS_HOST` |
| Brain base | `SOMABRAIN_URL`, `SOMABRAIN_API_URL`, `SOMABRAIN_MEMORY_HTTP_ENDPOINT` |
| SFM base | `SOMAFRACTALMEMORY_URL`, `SFM_URL` |
| SFM namespace | `SFM_NAMESPACE`, `SOMA_MEMORY_NAMESPACE` |
| Kafka brokers | `KAFKA_BOOTSTRAP_SERVERS`, `SA01_KAFKA_BOOTSTRAP_SERVERS`, `SOMABRAIN_KAFKA_URL`, `SOMABRAIN_KAFKA_HOST`, `KAFKA_HOST` |
| Vault addr | `VAULT_ADDR`, `SOMABRAIN_VAULT_ADDR`, `SOMA_VAULT_ADDR` |
| Vault token | `VAULT_TOKEN_FILE` (somaAgent01, correct), `VAULT_TOKEN`, `SOMABRAIN_VAULT_TOKEN`, `SOMA_VAULT_TOKEN` |
| Keycloak URL | `KEYCLOAK_URL` vs `SA01_KEYCLOAK_URL` |
| Deploy mode | `SA01_DEPLOYMENT_MODE` vs `SOMA_DEPLOY_MODE`/`SOMABRAIN_MODE` |

**Step 1.** Pick the registry name per concept. **Step 2.** Alias nothing — rename everywhere and delete the old spelling. A compatibility alias is a shim.
**Commit:** `refactor(config): one name per concept`

### Task 7.6 — RBAC gaps

Already gated: `settings_v2.py:250-298`, `admin/config/api.py`, LLM models/slots/presets, with read/write-gate tests in place.

Missing (verified):
1. `save_agent_setting` / `save_capsule_setting` (`capsule_settings.py:178-215`) are bare ORM helpers with **no authorization** and no tenant check.
2. `settings_v2` has **no tenant scoping** — `system:*` only; `InfrastructureConfig` queries filter by service, not tenant (`settings_v2.py:187`).
3. Entity-level, not key-level RBAC (`ENTITY_SPECS` at `settings_v2.py:85-140`).
4. somabrain settings endpoints are api-key-only — `brain_settings.py:31,40,67` — any token holder can flip `BrainSetting` mode.
5. `admin/config/api.py:360` hardcodes the credential inventory `["llm_api_key", "somabrain_memory_http_token", "postgres_password"]` — derive it from Vault listing instead.
6. `admin/aaas/api/settings.py` `create_api_key` hardcodes `scopes=[]` — populate it so keys can be narrowed.

**Commit:** `feat(authz): every settings write is authorized and tenant-scoped`

### Task 7.7 — Settings UI covers the registry

Today ~16–20 of 316 rows have a wired editor (`docs/iso/SOMA-01-UIUX-005.md` §6). Every row classified L1-Operator / L2-Agent / L3-Readonly / L4-Secret gets a surface honouring its edit authority (`REQ-UIXS-002`) — including the 7 service schemas already in `components/settings-form.ts`, which today do **not** implement the L1-gated / L3-readonly / L4-secret rules.

## Phase 8 — UI/UX complete

**Protected — already real, do not rebuild:** chat workspace + streaming + tool timeline · auth suite · `saas-settings-models.ts` (providers/keys/slots/presets/catalog) · channels + modules · multimodal · memory view · cognitive panel · admin API keys · models list · roles/matrix/permissions · users/agents · audit · integrations · ratelimits · metrics · voice · profiles · onboarding · `settings-form` 7 schemas · markdown renderer · WS client · api-client.

### Task 8.1 — Server-side logout (P1 SECURITY)

**Defect (verified):** `main.ts:252` and `saas-chat.ts:2046` clear `localStorage`/`sessionStorage` and redirect. Neither calls `POST /api/v2/auth/logout` (`admin/auth/api.py:299-317`, which deletes the cookies). `checkAuth()` reads the cookie, so **the session survives "Log out."**

**Step 1.** Failing test: logout returns 401 on the next authenticated call.
**Step 2.** Both sites call `POST /api/v2/auth/logout` before clearing storage.
**Commit:** `fix(auth): logging out ends the session`

### Task 8.2 — Kill the fake settings screen

**Defect (verified):** `saas-settings.ts` External tab shows fabricated key rows (`sk-****...****aBcD`, `sk-ant-****...****xYz`) with **dead** Edit/Add buttons (`:656-676`), a hardcoded readonly `http://localhost:9696` SomaBrain URL (`:630`), unbound STT/TTS selects and proxy inputs (`:744-764`), and a Save that persists only feature flags. This is UIUX-004 F-07/F-08/F-09, still open.

**Step 1.** Reuse the real `saas-settings-models.ts` / `/secrets/providers` path for keys, or delete the tab. Never render a key fragment that was not read from the server.
**Step 2.** Bind or remove every input. A control with no handler is a lie.
**Commit:** `fix(ui): the settings screen only shows what is real`

### Task 8.3 — Right-rail surface system (biggest visible gap)

Required UI-X-01…08; today `saas-right-panel.ts` has `SurfaceKey = 'capsule' | 'brain'` and `saas-chat.ts` has a competing `memory | files | channel` rail. Neither matches the spec. The four "coming soon" strings are gone because the tabs were **removed**, which violates `REQ-UIX-020` (a gated capability must be present-and-disabled with a reason, not omitted).

| Surface | Status |
|---|---|
| UI-X-01 Files (tree, preview, upload, search) | placeholder — lists attachment chips only |
| UI-X-02 Tools manager + live call log | MISSING |
| UI-X-03 Browser | MISSING |
| UI-X-04 Editor (syntax highlight, dirty, save) | MISSING |
| UI-X-05 Debug (WS frame log, request inspector) | MISSING |
| UI-X-06 Capsule | EXISTS |
| UI-X-07 Brain | EXISTS |
| UI-X-08 Desktop | MISSING even as disabled-with-reason |

**Step 1.** Build one typed surface registry + shared chrome.
**Step 2.** Implement each surface; Desktop ships as a disabled tab with an honest reason.
**Commit:** `feat(ui): the canvas rail has every surface`

### Task 8.4 — Chat completeness

| Item | Status | Work |
|---|---|---|
| Syntax highlighting | MISSING | `markdown.ts` has an unused `onCodeBlock` hook (copy button, lang chip) — wire it and add a highlighter |
| Image display + viewer | MISSING | zero `<img>`/preview in message rendering |
| Message actions | Copy only | 12-action set per PARITY-002 §4.1.2 (branch, regenerate, edit-rerun, pin, quote, delete, …) |
| Chat branching | MISSING | |
| Conversation queue | chip only | make it reorderable |
| Export | JSON blob | md/json picker + `capsule_export` |
| Cmd-K command palette | MISSING | zero hits in `webui/src` |
| Drawer + Full-screen modals | MISSING | only `saas-glass-modal` exists (UI-M-01, UI-M-02 absent) |

**Commit:** `feat(ui): chat is complete`

### Task 8.5 — Capsule-first chrome and facets

UI-S-00 global chrome, UI-S-01 Soul (system prompt, Big-5, neuro baseline), UI-S-02 Brain (3 knobs + 12 derived readouts), UI-S-03 Hands (tool policy buckets, capabilities, MCP registry), UI-S-05 Body, UI-S-06 Governance, UI-S-13 version rail/diff, UI-S-14 instances. `saas-capsule-editor.ts` today holds 2 fields (system_prompt, personality_traits).

### Task 8.6 — Nav gaps
`/themes` is a placeholder redirect to `/settings`. Composer "Skills" misroutes to `/settings` (`saas-composer-menu.ts:152-155`). Many routed screens are URL-only orphans with no nav entry. No switcher between the chat shell and the admin shell.

### Task 8.7 — Playwright evidence
`tests/e2e/test-browser-chat.spec.ts` is `expect(true).toBe(true)`; the logout test asserts a URL only and passes against the broken behaviour. Replace with real assertions for UI-AT-01…11 / UIX-AT-01…24.

### Task 8.8 — Resolve the scope conflict (decision required)

`AGENT.md` §1.1 says *"no SaaS or billing routes: standalone agent"*. `SOMA-01-UIUX-001.md` requires UI-S-19…28 (tenants, billing, subscriptions, usage, tiers, marketplace) — all deleted in `4d01f09a`/`c4383eee`.

**The standing order is de-SaaS.** Therefore: **descope** UI-S-19…28 and UI-S-42 (marketplace), record them as out-of-scope in the parity docs, and fix the docs rather than rebuilding a commerce suite the user ordered removed. If product later wants it, that is a new decision — not this plan.

---

## Phase 9 — Proof, bounds, hardening

### Task 9.1 — R-06 bound every pool (T-7)
`somabrain/memory/pool.py` is an unbounded `Dict`. Replace with a bounded LRU (default 256), idle-timeout eviction, explicit `close()`. Add a metric.

### Task 9.2 — R-08 durable writes (T-6)
Extend the brain-side outbox to the agent lane: `remember` records durably before the network hop and replays until acked.

### Task 9.3 — R-05 remaining fail-opens
- no tenant → `HttpError(400)`, never `"default"` (`api/utils.py:79`)
- `api/auth.py:86-87` → `if not allowed: return False`
- `api/auth.py:45` → the log line must not claim auth is "disabled" when it rejects all callers
- transport failure → raise `MemoryRecallUnavailable`, never `[]`

### Task 9.4 — Degradation doctrine (W5-2)
Brain down / SFM down / LLM down → defined behaviour, not crashes.

### Task 9.5 — Verification suite (W5-1)
"chat + memories 100%": load, recall accuracy, both-store ack, degradation drill. **One command proves the end-state.**

### Task 9.6 — Refresh the stale verification matrix
`docs/iso/SOMA-TRIAD-ARCH-001.md` §12 still says "T-1 NOT MET". It is now met on the hot path. Re-measure every row against the tree and fix the doc — documentation is truth. Same for `SOMA-01-UIUX-*` rows that name views deleted in `4d01f09a`/`c4383eee`.

### Task 9.7 — ISO close (W5-3)
Approver + Next Review filled, Revision History on OPS/RELEASE/VV, RTM, ADR template. Docs cannot stay `Draft` forever.

---

## Invariants that may never be softened

1. **T-1** Agent → SomaBrain → SFM. The agent never holds an SFM client.
2. **Fail-closed everywhere.** A missing env var raises. A missing token is a refusal, never `or ""` / `or "dummy"`.
3. **Vault-only secrets.** ENV carries topology only. No shim, no deprecated alias, no compatibility variable.
4. **No mocks in the proof path.** Integration tests run against live services and skip when absent.
5. **No Claude attribution** on any commit or PR.
6. **Do not rewrite the somabrain algorithm trees** (memory/learning/math/constitution/context/oak/predictors). Integrate around them.
7. **A control with no handler is a lie.** Wire it or delete it — never render it.

---

## What "done" means

```bash
pytest tests/e2e/test_triad_integration.py -v                    # green, real services
pytest tests/unit/test_ws_chat_turn_construction.py -v           # WS path reaches the orchestrator
grep -rn "def _stable_coord" . ../somabrain ../somafractalmemory # one definition
grep -rE "gsk_[A-Za-z0-9]{16,}|TODO|FIXME" admin services config --include="*.py" | grep -v tests/
docker compose -f infra/triad/docker-compose.yml ps              # every service healthy
```

One chat turn with a real Groq model streams to the UI, stores a memory through the seam, both stores ack it, the next turn recalls it into context, the transcript is persisted, and every screen the parity docs keep is real or explicitly descope.
