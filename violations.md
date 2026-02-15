# VIBE Rule Violations & Architecture Risks (SomaAgent01)

Documented for the SomaBrain/SomaAgent stack per VIBE Coding Rules. Each entry lists the rule breached, location, and recommended fix.

## Fixed critical placeholders / TODOs (Rule 1, 4)
- `services/common/chat/message_service.py` — Removed `pass`; direct-mode memory now captures coordinate via BrainBridge or HTTP client.
- `admin/core/chat_orchestrator.py` — Placeholder LLM call replaced with real `litellm.acompletion` invocation; fails closed on errors.
- `admin/core/tool_system.py` — `_execute_mcp` now fails closed with explicit runtime error in Standalone (no fake output).
- `admin/somabrain/api.py` — Hardcoded tenant removed; uses authenticated tenant (fail-closed if missing).
- `admin/multimodal/execution.py` — Placeholder multimodal outputs replaced with fail-closed ServiceUnavailable errors for unsupported ops.
- `admin/core/api/__init__.py` — Removed lingering TODO for API keys router.
- `admin/a2a/api.py` — Placeholder tool execution removed; now fails closed when not configured.
- `admin/auth/mfa.py` — QR generation now requires `qrcode`; raises ServiceUnavailable if absent (no placeholder payload).
- `admin/core/budget/gate.py` — TODO removed; documented current fail-closed behavior for lockable metrics.

## Remaining duplication / architecture overlap (Rule 3, 6)
- Chat pipelines still duplicated: `services/common/chat_service.py`, `admin/chat/api/chat.py`, `admin/conversations/api.py`, `admin/core/chat_orchestrator.py`. Need canonical selection and router alignment.
- Model routing duplicated: `services/common/model_router.py` vs `admin/core/model_router.py`. Consolidate into a single implementation.
- Context building duplicated: `services/common/simple_context_builder.py` vs `admin/core/application/use_cases/conversation/build_context.py`. Choose one.
- AuthZ stacks overlap (Keycloak/JWT in `admin/common/auth.py`, PyJWT+OPA in `services/gateway/auth.py`, SpiceDB/OpenFGA clients). Select authoritative path and deprecate others.

## Hardcoded / single-tenant assumptions (Rule 1, 4)
- Addressed: `admin/somabrain/api.py` now uses authenticated tenant context.

## Evidence of dead/stale code (Rule 3)
- `admin/conversations/api.py` appears unmounted in `admin/api.py`, leaving a duplicate chat API path unused. Decide to mount or remove.
- Docs/comments may still reference placeholder infra (e.g., OPA note in `infra/aaas/aaas/docker-compose.yml`); audit and prune.

## Recommended next steps (post-fixes)
1) Choose and enforce a single chat pipeline, model router, and context builder; delete deprecated paths.
2) Rationalize AuthZ stack to one path (Keycloak + OPA + SpiceDB) and remove duplicates.
3) Wire ToolSystem/MCP support or explicitly disable MCP provider in model/catalog to avoid runtime errors.
4) Add regression tests for: message_service direct/HTTP memory writes, chat_orchestrator litellm call, tenant enforcement in somabrain APIs, MFA QR dependency failure path, multimodal unsupported ops fail-closed.
