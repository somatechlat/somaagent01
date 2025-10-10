# Agent Zero — Canonical Roadmap

Last updated: 2025-10-09
Branch: v0.1.2

This file is the canonical, on-repo roadmap for the Agent Zero project. It consolidates the integrated roadmap, sprint breakdown and current task statuses so developers, QA and DevOps can align on priorities and execution. Update this file by PR when major milestone statuses change.

## High-level objective

Bring the codebase from prototype/dev state to a production-ready stack by:
- Removing silent fallbacks and placeholders for LLM/model calls.
- Ensuring the server starts even when no model/provider is configured.
- Exposing a clear UI notification when a model provider is not configured.
- Migrating to the gRPC memory & message services and wiring the router and tool-executor to them.
- Adding CI matrices for offline vs gated live-provider testing.

## Current sprint breakdown (parallel)

- Sprint P0 — Safety & gate (COMPLETE)
  - Add `USE_LLM` flag, implement `NoLLMWrapper` so server can start without model provider. (Done)

- Sprint A — Provider adapters (in-progress)
  - Implement adapters that map the project `unified_call` API to provider clients (Litellm/OpenRouter/OpenAI). Prefer provider-agnostic wiring via existing LiteLLM wrappers. Add unit tests which mock network calls (request mocking). (In progress)

- Sprint B — Settings API + UI notification (in-progress)
  - Add backend endpoint `GET /api/v1/settings/model` with JSON contract: {use_llm, provider, configured, hint}. UI shows a non-blocking banner when configured==false. Server must not stop because of missing provider. (In progress)

- Sprint C — Wording & docs clean-up (in-progress)
  - Remove words `mock`/`real` from runtime code/messages and replace with neutral terms (`model provider`, `provider not configured`). Update docs and README. (In progress)

- Sprint D — CI & test matrices (in-progress)
  - Add CI workflows: PRs run offline matrix (`USE_LLM=false`), protected/main branches run live-provider gated matrix with secrets. (In progress)

- Sprint E — SKM client / resource manager / scheduler / dedupe (planned)
  - Implement or remove `skm_client` stub, implement resource manager (psutil) and sandbox warm-up, replace job-loop TODOs with APScheduler/asyncio scheduler, deduplicate `a0_data` tree. (Planned)

## Todo list (short)

1. Replace MockChatWrapper with LLM wrapper — in-progress
2. Implement SKM client or remove stub — not-started
3. Add background task runner (defer standardization) — not-started
4. Complete `concat_messages` implementation — not-started
5. Ensure tool implementations are concrete — not-started
6. Resource manager & sandbox warm-up — not-started
7. Job loop scheduler — not-started
8. Deduplicate `a0_data` directory — not-started
9. Update CI pipeline for UI and test matrices — in-progress
10. Documentation refresh — not-started
11. UI: show LLM-not-configured notification — in-progress
12. Remove 'mock'/'real' wording from code/messages — in-progress
13. Create test matrices and CI gating — in-progress

## Acceptance criteria per milestone

- Server startup
  - Server process must start with `USE_LLM=false` and provide endpoints; model calls raise consistent `RuntimeError` messages that the UI surfaces; no process exit due to missing provider.

- UI behavior
  - On load, UI calls `/api/v1/settings/model`. If provider not configured, show a non-blocking admin banner linking to Settings. Normal operations continue (server not blocked).

- Tests & CI
  - PRs run fast offline tests (no provider secrets). Protected branches run live-provider tests guarded by secrets.

## How to update

- Edit this file by PR. For task-level tracking use the project's todo list (or update the `manage_todo_list` tool state). For small changes (status flips) prefer a PR with a short description and link to the issue.

## Contacts / owners

- Backend (LLM adapters, settings endpoint, scheduler): Backend team
- UI (banner + admin UX): Frontend team
- DevOps (CI matrix, Docker Compose): DevOps team

---
Generated/maintained by the development assistant to reflect the integrated roadmap and current progress as of 2025-10-09.
