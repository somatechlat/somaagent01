# Vibe Coding Rules — Violations Report

Started: 2025-12-18

This is a progressive, append-only audit report for violations of `VIBE_CODING_RULES.md`.

## Entry format

- **Date**: YYYY-MM-DD
- **Rule**: (e.g. Rule 1 — NO BULLSHIT)
- **File**: path
- **Location**: line number(s) when available
- **Finding**: what violates the rule and why it matters
- **Evidence**: short excerpt (kept minimal)
- **Suggested fix**: concrete remediation (no placeholders)

## Findings

### 2025-12-18 — Sweep #1 (repo-wide)

**Audit notes**
- Coverage + directory exclusions are recorded in `VIOLATIONSLOG.md`.
- This sweep includes *docs + tests* as well as production code; violations are logged where the repo text contradicts `VIBE_CODING_RULES.md` (e.g., presence of TODO/stub/mock keywords, “prototype” modules, bypass switches, and invented/non-existent APIs).

#### VCR-2025-12-18-001
- **Date**: 2025-12-18
- **Rule**: Rule 1 — NO BULLSHIT (invented/broken APIs)
- **File**: `src/gateway/routers/chat.py`
- **Location**: 18, 22-23, 55
- **Finding**: The module claims it is “fully functional” but imports non-existent symbols and calls non-existent interfaces; it will fail to import and cannot run as written.
- **Evidence**: `from services.common.audit_store import get_audit_store` + `from .models import ChatMessage, ChatPayload` + `get_audit_store().secret_manager`
- **Suggested fix**: Align with the existing repository layer (`integrations/repositories.py`) by importing `get_audit_store()` and using an actual credential source (e.g., `services.gateway.main.get_llm_credentials_store()` as used by `services/gateway/routers/llm.py`); remove/replace the missing relative imports (`.models`, `._detect_provider_from_base`, `._gateway_slm_client`) with real modules that exist in this repo.

#### VCR-2025-12-18-002
- **Date**: 2025-12-18
- **Rule**: Rule 1 — NO BULLSHIT (missing module)
- **File**: `src/gateway/routers/session.py`
- **Location**: 18-21
- **Finding**: Imports a module that does not exist in the repository; the router cannot import.
- **Evidence**: `from services.common.postgres_session_store import ( ... )`
- **Suggested fix**: Replace with the canonical session implementation that *does* exist (`services/common/session_repository.py` + `PostgresSessionStore`) and/or reuse the singleton accessor (`integrations/repositories.py:get_session_store`), then update the dependency injection wiring accordingly.

#### VCR-2025-12-18-003
- **Date**: 2025-12-18
- **Rule**: Rule 1 — NO BULLSHIT (invented method call)
- **File**: `services/gateway/routers/chat_full.py`
- **Location**: 38
- **Finding**: Calls `PostgresSessionStore.get()` but the class in `services/common/session_repository.py` does not define `get`; this endpoint will raise at runtime.
- **Evidence**: `session = await store.get(session_id)`
- **Suggested fix**: Use `await store.get_envelope(session_id)` (existing API) or implement a real `get()` method on the store and use it consistently across the codebase (prefer the existing `get_envelope`).

#### VCR-2025-12-18-004
- **Date**: 2025-12-18
- **Rule**: Rule 1 — NO BULLSHIT + Rule 4 — REAL IMPLEMENTATIONS ONLY (no placeholders)
- **File**: `python/integrations/opa_middleware.py`
- **Location**: 41-42, 96-110
- **Finding**: Policy enforcement defaults to fail-open and the module exports a no-op placeholder client; the module also contains unreachable duplicate code (copy/paste) in `enforce_policy()`.
- **Evidence**: `env_fail_open = (cfg.env(\"SA01_OPA_FAIL_OPEN\", \"true\") ...` + duplicate `return EnforcePolicy` + `def opa_client(): ... return None`
- **Suggested fix**: Remove the unreachable duplicate return; delete `opa_client()` or replace it with a real client/factory; change default behaviour to fail-closed unless an explicit dev-only setting is enabled and audited.

#### VCR-2025-12-18-005
- **Date**: 2025-12-18
- **Rule**: Rule 1 — NO TODOs
- **File**: `services/tool_executor/multimodal_executor.py`
- **Location**: 436
- **Finding**: A TODO remains in production code; outcome cost is hard-coded to 0.0 despite a real cost value being available earlier.
- **Evidence**: `cost_cents=0.0, # TODO: Propagate from result`
- **Suggested fix**: Populate the outcome from the real provider result (the surrounding code already uses `result.cost_cents` for tracking); remove the TODO.

#### VCR-2025-12-18-006
- **Date**: 2025-12-18
- **Rule**: Rule 4 — REAL IMPLEMENTATIONS ONLY (no “demo/hypothetical/hardcoded” logic)
- **File**: `services/tool_executor/multimodal_executor.py`
- **Location**: 469-475
- **Finding**: Provider selection is explicitly “for now hardcoding” and includes “hypothetical for ranking demo”, indicating non-production selection logic.
- **Evidence**: `# For now hardcoding registered names ...` + `# Fallback/alternative (hypothetical for ranking demo)`
- **Suggested fix**: Derive candidates from the real registry/capability metadata (single source of truth) and remove “demo/hypothetical” branches or gate them behind a clearly defined, documented dev-mode flag.

#### VCR-2025-12-18-007
- **Date**: 2025-12-18
- **Rule**: Rule 1 — NO TODOs
- **File**: `webui/js/speech_browser.js`
- **Location**: 222
- **Finding**: TODO comment indicates unresolved behaviour in voice activity logic.
- **Evidence**: `// TODO? a better way to ignore agent's voice?`
- **Suggested fix**: Implement a deterministic “ignore playback” strategy (e.g., tag/track the output audio stream or use explicit speech-synthesis state events) and remove the TODO.

#### VCR-2025-12-18-008
- **Date**: 2025-12-18
- **Rule**: Rule 1 — NO stubs + Rule 3 — NO shims/hacks
- **File**: `webui/js/scheduler.js`
- **Location**: 544-568, 1442-1481
- **Finding**: The component is described and treated as a “stub” that is merged at runtime with a “full implementation”, including a “hack” that writes a global function.
- **Evidence**: `// Initialize plan stub ...` + `merges the pre-initialized stub with the full implementation` + `// hack to expose deleteTask`
- **Suggested fix**: Consolidate to a single canonical scheduler component initialization path; remove runtime patch/merge behaviour and global exports; normalize task plans via a single helper that guarantees the shape from API → UI.

#### VCR-2025-12-18-009
- **Date**: 2025-12-18
- **Rule**: Rule 1 — NO guesses (“probably”) + Rule 4 — REAL IMPLEMENTATIONS ONLY
- **File**: `services/gateway/routers/uploads_full.py`
- **Location**: 256-260
- **Finding**: `SCAN_PENDING` is not handled; the code comments about “probably” bypassing and then does nothing (`pass`).
- **Evidence**: `# Given current logic, we probably treat as error-ish or bypass ...` + `pass`
- **Suggested fix**: Define and implement an explicit policy for `SCAN_PENDING` (e.g., block with retryable 503, or quarantine until scan completes); do not silently pass.

#### VCR-2025-12-18-010
- **Date**: 2025-12-18
- **Rule**: Rule 1 — NO “hack” / Rule 4 — REAL IMPLEMENTATIONS ONLY
- **File**: `models.py`
- **Location**: 922-930, 952-962
- **Finding**: The core model wrapper contains multiple “hack” blocks for compatibility (Gemini schema and invalid JSON post-processing).
- **Evidence**: `# hack from browser-use to fix json schema for gemini ...` + `# another hack for browser-use post process invalid jsons`
- **Suggested fix**: Move these behaviours behind a clearly documented compatibility layer with tests, strict input/output contracts, and feature flags; remove “hack” blocks once the behaviour is formalised and verified.

#### VCR-2025-12-18-011
- **Date**: 2025-12-18
- **Rule**: Rule 4 — REAL IMPLEMENTATIONS ONLY (“prototype” in production)
- **File**: `services/common/semantic_recall.py`
- **Location**: 34-61
- **Finding**: The implementation is explicitly labeled a prototype and uses a naive in-memory vector store with FIFO eviction.
- **Evidence**: `"""In-memory vector index for semantic recall (prototype).` + `# FIFO eviction for prototype simplicity`
- **Suggested fix**: Either (a) gate this module behind an explicit experimental feature flag and ensure it is not used in production paths, or (b) implement a persistent embedding store + ANN index consistent with the repository’s architecture docs.

#### VCR-2025-12-18-012
- **Date**: 2025-12-18
- **Rule**: Rule 5 — DOCUMENTATION = TRUTH (stale “stub” language)
- **File**: `src/voice/provider_selector.py`
- **Location**: 3-8, 33
- **Finding**: Docstring claims “lightweight stub classes” for incremental development, but the module implements a `Protocol` and returns real clients; documentation is stale.
- **Evidence**: `we provide lightweight stub classes ...` + `keep the stub implementation simple`
- **Suggested fix**: Update the module docstring to describe the current design (protocol + real providers) and remove “stub” language.

#### VCR-2025-12-18-013
- **Date**: 2025-12-18
- **Rule**: Rule 5 — DOCUMENTATION = TRUTH (misleading comment)
- **File**: `webui/js/api.js`
- **Location**: 47
- **Finding**: Comment describes an “env stub” precedence but the implementation does not read from environment; only headers/localStorage/default are used.
- **Evidence**: `explicit header > localStorage override > env stub > default`
- **Suggested fix**: Correct the comment to match reality or implement a real env-based override consistently.

#### VCR-2025-12-18-014
- **Date**: 2025-12-18
- **Rule**: Rule 1 — NO placeholders (“XXX”, fake emails)
- **File**: `prompts/agent.system.tool.scheduler.md`
- **Location**: 176-179
- **Finding**: Example payload includes placeholder values and fake addresses that can leak into real runs if copy/pasted.
- **Evidence**: `"name": "XXX"` + `xxx@yyy.zzz`
- **Suggested fix**: Replace with explicit, non-sensitive example values (e.g., `"name": "WeeklyEmailGreeting"` and `user@example.com`) and label the block as an example.

#### VCR-2025-12-18-015
- **Date**: 2025-12-18
- **Rule**: Rule 1 — NO placeholders (“XXX”)
- **File**: `python/tools/scheduler.py`
- **Location**: 145-155
- **Finding**: In-code example comments include placeholder values.
- **Evidence**: `# "name": "XXX",`
- **Suggested fix**: Remove the placeholder example block or replace with a concrete, clearly-labeled example.

#### VCR-2025-12-18-016
- **Date**: 2025-12-18
- **Rule**: Rule 7 — REAL DATA & SERVERS ONLY / “no bypass”
- **File**: `services/conversation_worker/policy_integration.py`
- **Location**: 24-26
- **Finding**: Environment-controlled bypass returns `True` for policy checks, potentially disabling enforcement.
- **Evidence**: `DISABLE_CONVERSATION_POLICY ... return True`
- **Suggested fix**: Remove this bypass or restrict it to a compile-time dev profile; if it must remain, require explicit acknowledgement + audit logging when enabled.

#### VCR-2025-12-18-017
- **Date**: 2025-12-18
- **Rule**: Rule 1 — NO TODOs (docs)
- **File**: `docs/ui-integration/COMPLETE_AGENTSKIN_UIX_SPEC.md`
- **Location**: 580, 613
- **Finding**: TODOs remain in published spec text.
- **Evidence**: `// TODO: Implement ...`
- **Suggested fix**: Convert TODOs into explicit requirements and track them in `TASKS.md` (or remove them from the spec if out of scope).

#### VCR-2025-12-18-018
- **Date**: 2025-12-18
- **Rule**: Rule 1 — NO TODOs + Rule 4 — REAL IMPLEMENTATIONS ONLY (docs show no-op integrations)
- **File**: `docs/technical-manual/context-builder-flow.md`
- **Location**: 684-685
- **Finding**: Documentation includes TODOs and a no-op callback in an implementation snippet, explicitly describing missing integrations.
- **Evidence**: `Always NORMAL (TODO: integrate ...)` + `No-op callback (TODO: ...)`
- **Suggested fix**: Update the implementation and doc to use the real `DegradationMonitor` + circuit breaker hooks, or remove the snippet until the integration exists.

#### VCR-2025-12-18-019
- **Date**: 2025-12-18
- **Rule**: Rule 1 — NO stubs (docs)
- **File**: `docs/reference/CONTEXT_BUILDER_REQUIREMENTS.md`
- **Location**: 19
- **Finding**: Declares the context builder as “Implemented (stub)” in a production-readiness checklist.
- **Evidence**: `✅ Implemented (stub)`
- **Suggested fix**: Replace with a precise, truthful status (implemented/partial/missing) and link to the actual module(s) and tests that verify behaviour.

#### VCR-2025-12-18-020
- **Date**: 2025-12-18
- **Rule**: Rule 1 — NO mocks (strict reading; tests contain mocks)
- **File**: `tests/` (multiple)
- **Location**: N/A (multiple files)
- **Finding**: The test suite contains direct use of mocking frameworks (`unittest.mock`, `respx.mock`, `MagicMock`, etc.), contradicting a strict reading of VIBE “NO mocks”.
- **Evidence** (file list): `tests/test_policy_enforcement.py`, `tests/integrations/test_somabrain_client.py`, `tests/unit/test_asset_critic_llm.py`, `tests/unit/test_policy_graph_router.py`, `tests/unit/test_multimodal_executor.py`, `tests/voice/test_voice_components.py` (and others).
- **Suggested fix**: Either (a) clarify the scope of `VIBE_CODING_RULES.md` (production code vs tests) to avoid contradictions, or (b) replace mocks with real container-backed integration tests and in-process real service fixtures.

#### VCR-2025-12-18-021
- **Date**: 2025-12-18
- **Rule**: Architecture duplication (session management duplication across routers)
- **File**: `services/gateway/routers/sessions.py`, `services/gateway/routers/sessions_events.py`, `services/gateway/routers/sessions_full.py`, `src/gateway/routers/sse.py`
- **Location**: `services/gateway/routers/sessions.py:29-33`, `services/gateway/routers/sessions_events.py:20-23`, `services/gateway/routers/sessions_full.py:23-28`
- **Finding**: Multiple routers implement overlapping session endpoints and each repeats its own store/schema initialization. This duplicates effort and increases the risk of divergent behaviour and performance regressions.
- **Evidence**: each module creates `PostgresSessionStore(...)` and calls `ensure_schema(...)` in a local helper.
- **Suggested fix**: Centralize session store creation + schema init behind a single dependency/provider (e.g., a `services.gateway.providers.get_session_store()` singleton) and remove redundant routers/endpoints (keep one canonical API surface).

#### VCR-2025-12-18-022
- **Date**: 2025-12-18
- **Rule**: Architecture duplication (SSE endpoint duplication)
- **File**: `src/gateway/routers/sse.py`, `services/gateway/routers/sessions.py`
- **Location**: `src/gateway/routers/sse.py:38-75`, `services/gateway/routers/sessions.py:22,89-113`
- **Finding**: Two independent implementations expose the same SSE endpoint path `/v1/session/{session_id}/events` with different backends (Kafka consumer vs Postgres polling). This duplicates effort and can produce inconsistent semantics, scaling behaviour, and operational flags.
- **Evidence**: `@router.get("/v1/session/{session_id}/events")` (Kafka) vs `router = APIRouter(prefix="/v1/session"...); @router.get("/{session_id}/events")` (Postgres SSE via `stream=true`).
- **Suggested fix**: Choose ONE canonical streaming source for session events (Kafka OR Postgres polling), delete/disable the other endpoint, and standardize feature flags (currently `SA01_SSE_ENABLED` exists in one path but not the other).

#### VCR-2025-12-18-023
- **Date**: 2025-12-18
- **Rule**: Architecture duplication / route composition error
- **File**: `services/gateway/service.py`, `services/gateway/main.py`
- **Location**: `services/gateway/service.py:99-109`, `services/gateway/main.py:21-22,88`
- **Finding**: `GatewayService` mounts the already-versioned gateway app under `/v1` and also includes additional routers that themselves define `/v1/...` routes. This creates a duplicated `/v1/v1/...` namespace and multiple overlapping “gateway” stacks (the `services.gateway.*` app + `src.gateway.*` routers).
- **Evidence**: `app.mount("/v1", gateway_app)` and `gateway_app` includes routers whose prefixes already start with `/v1` (e.g., `services/gateway/routers/health.py` uses `APIRouter(prefix="/v1")`); additionally `services/gateway/main.py` includes `build_router()` (also `/v1` prefixed).
- **Suggested fix**: Pick one strategy: (A) mount `gateway_app` at `/` (not `/v1`) OR (B) remove `/v1` prefixes inside the gateway app and keep the external mount at `/v1`; do not mix. Also remove the parallel `src.gateway.routers.*` set or clearly separate it behind a different mount path.

#### VCR-2025-12-18-024
- **Date**: 2025-12-18
- **Rule**: Rule 3 — NO UNNECESSARY FILES (duplicate policy files)
- **File**: `check_tool_policy.rego`, `policy/tool_policy.rego`
- **Location**: N/A (entire file; identical content)
- **Finding**: Two identical Rego policy files exist in different locations, increasing the risk of drift and confusion about which policy is authoritative.
- **Evidence**: `diff check_tool_policy.rego policy/tool_policy.rego` returns no differences.
- **Suggested fix**: Keep a single canonical policy file (prefer `policy/tool_policy.rego`, since docs/scripts reference it) and delete the duplicate; update any remaining references accordingly.

#### VCR-2025-12-18-025
- **Date**: 2025-12-18
- **Rule**: Architecture duplication (health endpoint duplication)
- **File**: `src/gateway/routers/health.py`, `services/gateway/routers/health.py`
- **Location**: `src/gateway/routers/health.py:20-33`, `services/gateway/routers/health.py:21,30-36`
- **Finding**: Two different implementations define the same `/v1/health` endpoint (one “tiny” payload, one full dependency health). If both routers are ever mounted, one will shadow the other depending on registration order.
- **Evidence**: `@router.get("/v1/health")` (src) vs `router = APIRouter(prefix="/v1"); @router.get("/health")` (services).
- **Suggested fix**: Keep a single canonical `/v1/health` contract (either “simple liveness” or “full dependency health”) and expose any other view under a distinct path (e.g., `/v1/health/live` vs `/v1/health/ready`).

#### VCR-2025-12-18-026
- **Date**: 2025-12-18
- **Rule**: Architecture duplication / naming collision (multiple SomaBrain clients)
- **File**: `services/gateway/auth.py`, `python/integrations/somabrain_client.py`, `src/core/clients/somabrain.py`, `services/common/soma_brain_client.py`
- **Location**: `services/gateway/auth.py:18-38`, `python/integrations/somabrain_client.py:23-28`, `src/core/clients/somabrain.py:18-23`, `services/common/soma_brain_client.py:61-76`
- **Finding**: Multiple classes named `SomaBrainClient` exist across layers with different responsibilities (auth/constitution, HTTP API wrapper, compatibility alias, and DB-backed multimodal outcomes). This duplicates effort and creates high risk of importing the wrong client in production code.
- **Evidence**: Same class name appears in multiple modules with different behaviour and storage backends.
- **Suggested fix**: Rename clients by responsibility (e.g., `SomabrainHttpClient`, `SomabrainOutcomesStore`, `ConstitutionClient`) and enforce a single import path per responsibility via the repository/provider layer.
