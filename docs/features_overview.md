# Agent Zero Feature Catalog

A comprehensive rundown of the capabilities delivered by the Agent Zero platform. Each section links to the canonical documentation for deeper dives and implementation specifics.

---

## 1. Agentic Foundation

- **Task-general AI assistant** — Agent Zero orchestrates multi-step workstreams without prescriptive rails. The gateway service (`services/gateway`) coordinates LLM requests, tool invocations, and delegation loops so each task can branch or converge as needed.
- **Operating-system level execution** — Through the tool executor (see `python/tools/*` and `services/tool_executor`), agents can run shell commands, execute Python, manipulate files, and install dependencies. The system writes its own tooling on the fly when native capabilities are insufficient.
- **Multi-agent hierarchy** — Any agent can spawn subordinate agents with scoped prompts (`agents/*`). Superior/subordinate relationships are enforced through message routing and the conversation worker, enabling divide-and-conquer task execution.

## 2. Prompt & Persona System

- **Prompt packs** — Persona definitions live in `agents/` (canonical) and are mirrored into `a0_data/agents/` for packaged deployments. Each persona bundles a `_context.md` and `prompts/agent.system.*.md` files to shape communication, behaviour, and tool usage.
- **Dynamic prompt augmentation** — Runtime modifiers in `prompts/` (memory, behaviour overrides, tool guidance) are composed automatically during each turn, letting the framework inject context (time, memories, task metadata) that the base prompts do not hardcode.
- **Custom prompt profiles** — Developers can clone prompt sets or build new personas and bind them via tenant configuration (`conf/tenants.yaml`) without changing runtime code.

## 3. Persistent Memory & Knowledge

- **SomaBrain backend** — Long-term memory operations default to SomaBrain (HTTP API at `http://127.0.0.1:9696`). Agents store conversations, solutions, and facts that can be recalled automatically. Toggle via `SOMA_BASE_URL` / `SOMA_ENABLED` env vars.
- **Knowledge base ingestion** — Static documentation under `knowledge/` and `prompts/` is indexed so agents can ground responses on curated content. Memory dashboards (UI) expose retrieval and consolidation workflows.

## 4. Tooling & Instruments

- **Built-in tools** — File operations, web search, code execution, document query, and notification utilities are bundled (`python/tools/`). Each tool has structured input/output schemas for reliable orchestration.
- **Instruments framework** — Reusable procedures defined under `instruments/` allow deterministic function calls that complement LLM reasoning. Instruments can be versioned and tested independently of prompts.
- **Custom tool creation** — Users extend the system by adding Python modules, registering them via configuration, or packaging them into capsules (see §8). Tool metadata is auto-discovered at startup.

## 5. Capsule Marketplace & Extensions

- **Capsule registry** — REST service (documented in `docs/SomaAgent01_ModelProfiles.md` and `docs/SomaAgent01_Integration_Roadmap.md`) for publishing reusable capsule bundles with optional Cosign signatures.
- **Marketplace UI** — The web UI surfaces discoverable capsules, signature status, and one-click install flows into `/capsules/installed` via the gateway.
- **SDK support** — `python/somaagent/capsule.py` provides helper functions for programmatic install, verification, and invocation of capsules.

## 6. Conversation Orchestration & Delegation

- **Gateway API** — FastAPI service exposes `/v1/*` routes for session management (`POST /v1/sessions`, `GET /v1/sessions/{id}`, cancel paths) documented in `docs/SomaAgent01_API.md`.
- **Kafka-backed workflow** — Conversation workers consume topics, ensuring resilient message ordering and retry semantics. Scripts like `scripts/kafka_partition_scaler.py` assist with throughput tuning.
- **Delegation gateway** — `services/delegation_gateway` accepts tasks on `/v1/delegation/task`, records metadata in Postgres, and coordinates callback completion for downstream workers (see `docs/development.md`).

## 7. User Interfaces

- **Web UI** — React/HTMX-powered interface under `webui/` with streamed message rendering, color-coded tool outputs, chat transcripts saved to `logs/`. Supports attachments, downloadable transcripts, and settings panels.
- **Terminal interface** — Real-time CLI (`run_ui.py`) with streaming responses, manual intervention controls, and rich formatting.
- **Voice & media** — Audio service (`services/audio_service`) provides Whisper transcription (`WHISPER_MODEL` configurable) and text-to-speech outputs; UI includes microphone capture and playback.

## 8. Security, Policy, and Governance

- **Authentication** — JWT verification enforced by the gateway using secrets stored in Vault (`GATEWAY_JWT_SECRET` or Vault-backed keys). Optional fail-open behaviour toggled by `GATEWAY_REQUIRE_AUTH`.
- **Authorization** — OpenFGA integration for relationship-based access control; policy decisions aggregated through OPA with fallback rules (`POLICY_FAIL_OPEN`). Tenant-specific budgets and allowlists defined in `conf/tenants.yaml`.
- **Secrets management** — Vault dev instance included in Docker stack for storing API keys and tool credentials. Secrets can be injected or rotated without redeploying services.

## 9. Observability & Reliability

- **Health endpoints** — `/health` on major services plus UI status glyph polling for quick glance of dependency state.
- **Metrics & alerts** — Prometheus + Alertmanager stack (optional profile) with circuit-breaker counters exported on `${CIRCUIT_BREAKER_METRICS_PORT:-9610}`. Alert rules archived in `infra/observability/alerts.yml`.
- **Tracing** — OpenTelemetry spans emitted when `OTEL_EXPORTER_OTLP_ENDPOINT` is configured, enabling distributed tracing across gateway, router, and tool executor.
- **Circuit breakers** — Tool executor wraps each tool with failure thresholds (`TOOL_EXECUTOR_CIRCUIT_FAILURE_THRESHOLD`) and reset timers to isolate flaky integrations.

## 10. Deployment Options

- **Local IDE** — Run `python run_ui.py` with optional debugging (`.vscode/launch.json`). Ideal for UI tweaks, prompt iteration, and unit testing.
- **SomaAgent01 Docker stack** — `docker-compose.somaagent01.yaml` provisions the full environment (Kafka, Redis, Postgres, OpenFGA, Vault, Prometheus, delegation services, UI). See `docs/development/somaagent01_docker_compose.md` for runbook.
- **Remote & Infra automation** — `infra/` directory seeds Terraform/Helm references; `DockerfileLocal` builds production images; scripts such as `scripts/run_dev_cluster.sh` align local and CI/CD launches.

## 11. Developer Experience Enhancements

- **RFC bridge** — Remote Function Call system pairs local IDE runs with Docker-hosted execution, enabling hybrid debugging (configure via UI → Settings → Development).
- **Playwright automation** — Browser agent uses Playwright with Chromium binaries (`playwright install chromium`) for web automation tasks.
- **Testing & CI** — `pytest`, integration suites, Ruff linting, and GitHub Actions pipelines guard regressions. Integration tests cover gateway contracts and tenant policies (`tests/integration/test_gateway_public_api.py`).

## 12. Communication & Collaboration Features

- **Notifications system** — UI-level alerts for actions (see `docs/notifications.md`). Supports targeted popups, streaming updates, and custom event handlers.
- **Tunnel service** — `run_tunnel.py` opens secure tunnels for remote access, optionally with QR-code distribution (documented in `docs/tunnel.md`).
- **Multi-channel messaging** — Agents can send subordinate updates, escalate to humans, and leverage quick actions (`docs/SomaAgent01_QuickActions.md`).

## 13. Compliance & Operations Runbooks

- **Deployment guide** — `docs/SomaAgent01_Deployment.md` outlines canonical steps to stand up environments, perform smoke tests, and recover from failures.
- **Runbook** — `docs/SomaAgent01_Runbook.md` codifies incident response, including service restart sequences and health validation.
- **Roadmaps** — `ROADMAP_SPRINTS.md` and `docs/SomaAgent01_Sprint_*.md` files enumerate strategic initiatives and feature backlog for the enterprise stack.

---

### How to Use This Catalog

1. Cross-reference the linked documents before implementing changes to confirm context and dependencies.
2. Update this catalog whenever new services, tools, or UI capabilities ship—especially when API contracts, environment variables, or operational runbooks change.
3. Share with new contributors as the authoritative feature baseline.
