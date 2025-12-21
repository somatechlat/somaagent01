# Vibe Coding Rules — Audit Coverage Log

Started: 2025-12-18

Purpose: progressive, append-only record of which repo folders were audited for **VIBE_CODING_RULES.md** violations.

## Scope & exclusions

This audit focuses on **first-party project code + config**.

Excluded from deep violation scanning (third-party, generated, or runtime artifacts that are not authored/maintained as part of the project):
- `.git/`
- `.venv/`
- `node_modules/`
- `**/__pycache__/`
- `.pytest_cache/`
- `.ruff_cache/`
- `logs/`
- `kafka-logs/`
- `tmp/`
- `webui/vendor/`
- `webui/js/transformers@3.0.2.js` (vendored/minified third-party artifact)

If you want these included anyway, say so and I will run a separate “vendor/generated sweep” (it will be noisy because upstream packages often contain TODO/FIXME, etc.).

## Folders checked (recursive)

### 2025-12-18 — Sweep #1

Scanned recursively:
- .
- .github
- .github/workflows
- .kiro
- .kiro/specs
- .kiro/steering
- .vscode
- agents
- bin
- conf
- docs
- docs/agent-onboarding
- docs/architecture
- docs/development-manual
- docs/flows
- docs/guides
- docs/i18n
- docs/i18n/en
- docs/onboarding-manual
- docs/reference
- docs/technical-manual
- docs/technical-manual/runbooks
- docs/technical-manual/security
- docs/ui-integration
- docs/user-manual
- docs/user-manual/features
- infra
- infra/helm
- infra/helm/delegation
- infra/helm/delegation/templates
- infra/helm/gateway
- infra/helm/gateway/templates
- infra/helm/outbox-sync
- infra/helm/outbox-sync/templates
- infra/helm/overlays
- infra/helm/patches
- infra/helm/soma-infra
- infra/helm/soma-infra/charts
- infra/helm/soma-infra/charts/auth
- infra/helm/soma-infra/charts/etcd
- infra/helm/soma-infra/charts/etcd/templates
- infra/helm/soma-infra/charts/kafka
- infra/helm/soma-infra/charts/kafka/templates
- infra/helm/soma-infra/charts/opa
- infra/helm/soma-infra/charts/opa/templates
- infra/helm/soma-infra/charts/postgres
- infra/helm/soma-infra/charts/postgres/templates
- infra/helm/soma-infra/charts/prometheus
- infra/helm/soma-infra/charts/prometheus/templates
- infra/helm/soma-infra/charts/redis
- infra/helm/soma-infra/charts/redis/templates
- infra/helm/soma-infra/charts/vault
- infra/helm/soma-infra/charts/vault/templates
- infra/helm/soma-infra/templates
- infra/helm/soma-stack
- infra/helm/soma-stack/templates
- infra/helm/somaagent01
- infra/helm/somaagent01/templates
- infra/k8s
- infra/k8s/base
- infra/k8s/overlays
- infra/k8s/overlays/dev
- infra/k8s/overlays/development
- infra/k8s/overlays/development/patches
- infra/k8s/overlays/local
- infra/k8s/overlays/production
- infra/k8s/overlays/production/patches
- infra/kafka
- infra/memory
- infra/observability
- infra/observability/alerts
- infra/observability/grafana
- infra/observability/grafana/dashboards
- infra/observability/grafana/provisioning
- infra/observability/grafana/provisioning/dashboards
- infra/observability/grafana/provisioning/datasources
- infra/postgres
- infra/postgres/init
- infra/sql
- instruments
- instruments/custom
- instruments/default
- integrations
- memory
- observability
- orchestrator
- policy
- postgres-backups
- prompts
- python
- python/extensions
- python/extensions/agent_init
- python/extensions/before_main_llm_call
- python/extensions/error_format
- python/extensions/hist_add_before
- python/extensions/hist_add_tool_result
- python/extensions/message_loop_end
- python/extensions/message_loop_prompts_after
- python/extensions/message_loop_prompts_before
- python/extensions/message_loop_start
- python/extensions/monologue_end
- python/extensions/monologue_start
- python/extensions/reasoning_stream
- python/extensions/reasoning_stream_chunk
- python/extensions/reasoning_stream_end
- python/extensions/response_stream
- python/extensions/response_stream_chunk
- python/extensions/response_stream_end
- python/extensions/system_prompt
- python/extensions/tool_execute_after
- python/extensions/tool_execute_before
- python/extensions/util_model_call_before
- python/helpers
- python/integrations
- python/observability
- python/somaagent
- python/tools
- redis-conf
- schemas
- schemas/audit
- schemas/config
- scripts
- scripts/benchmarks
- scripts/entrypoints
- scripts/load
- services
- services/common
- services/conversation_worker
- services/delegation_gateway
- services/delegation_worker
- services/gateway
- services/gateway/routers
- services/gateway/tests
- services/memory_replicator
- services/memory_service
- services/memory_service/grpc_generated
- services/memory_sync
- services/multimodal
- services/outbox_sync
- services/tool_executor
- services/ui
- services/ui_proxy
- src
- src/core
- src/core/application
- src/core/application/dto
- src/core/application/services
- src/core/application/use_cases
- src/core/application/use_cases/conversation
- src/core/application/use_cases/memory
- src/core/application/use_cases/tools
- src/core/clients
- src/core/config
- src/core/domain
- src/core/domain/entities
- src/core/domain/memory
- src/core/domain/ports
- src/core/domain/ports/adapters
- src/core/domain/ports/repositories
- src/core/domain/value_objects
- src/core/infrastructure
- src/core/infrastructure/adapters
- src/core/infrastructure/external
- src/core/infrastructure/repositories
- src/core/messaging
- src/gateway
- src/gateway/routers
- src/voice

### 2025-12-19 — Sweep #2 (targeted fixes)

Focused scan and remediation of:
- services/gateway/routers
- webui/js
- tests/integration
- ONBOARDING_AGENT.md
- src (duplicate gateway stubs removed)
- src/core/infrastructure (duplicate Somabrain client removed)

### 2025-12-19 — Sweep #3 (tests purge: mocks/fakes/stubs)

Focused scan and remediation of:
- tests/ (removed all files containing mock/fake/stub/monkeypatch/respx usage)

### 2025-12-20 — Sweep #4 (runtime no-op/stub cleanup)

Focused scan and remediation of:
- python/somaagent/context_builder.py
- services/conversation_worker/main.py
- python/helpers/browser_use_monkeypatch.py
- python/helpers/knowledge_import.py
- python/helpers/tunnel_manager.py
- services/common/audit_store.py
- services/common/health_checks.py
- docs/technical-manual/context-builder-flow.md

### 2025-12-20 — Sweep #5 (repo-wide keyword sweep)

Focused scan and remediation of:
- ONBOARDING_AGENT.md
- src/voice/audio_capture.py
- src/voice/speaker.py
- templates
- tests
- tests/agent
- tests/agent/context
- tests/agent/conversation
- tests/agent/llm
- tests/agent/memory
- tests/agent/tools
- tests/chaos
- tests/e2e
- tests/functional
- tests/integration
- tests/integration/gateway
- tests/integration/multimodal
- tests/integrations
- tests/load
- tests/playwright
- tests/playwright/fixtures
- tests/playwright/screenshots
- tests/playwright/tests
- tests/playwright/tests/playwright
- tests/playwright/tests/playwright/screenshots
- tests/properties
- tests/smoke
- tests/temp_data
- tests/ui
- tests/ui/playwright
- tests/unit
- tests/unit/config
- tests/voice
- webui
- webui/components
- webui/components/_examples
- webui/components/chat
- webui/components/chat/attachments
- webui/components/chat/speech
- webui/components/messages
- webui/components/messages/action-buttons
- webui/components/messages/resize
- webui/components/notifications
- webui/components/settings
- webui/components/settings/a2a
- webui/components/settings/backup
- webui/components/settings/external
- webui/components/settings/mcp
- webui/components/settings/mcp/client
- webui/components/settings/mcp/server
- webui/components/settings/memory
- webui/components/settings/secrets
- webui/components/settings/speech
- webui/components/settings/tunnel
- webui/css
- webui/design-system
- webui/i18n
- webui/js
- webui/public
- webui/themes

### 2025-12-18 — Follow-up (duplication focus)

Targeted checks performed:
- Duplicate gateway route stacks and duplicate `/v1/*` prefix mounting patterns.
- Duplicate SSE endpoint implementations (Kafka SSE vs Postgres-poll SSE) under the same path.
- Duplicate policy files by content (`check_tool_policy.rego` vs `policy/tool_policy.rego`).

### 2025-12-20 — Sweep #6 (no-bypass/no-placeholder cleanup)

Focused scan and remediation of:
- sitecustomize.py
- services/common/authorization.py
- services/tool_executor/request_handler.py
- services/common/requeue_store.py
- services/gateway/routers/requeue.py
- tests/agent/tools/test_tool_flow.py
- tests/agent/conversation/test_conversation_integrity.py
- services/tool_executor/multimodal_executor.py
- observability/metrics.py
- TASKS.md
- docs/development-manual/testing-guidelines.md
- docs/reference/CONTEXT_BUILDER_REQUIREMENTS.md
- docs/development-manual/contribution-process.md
- docs/architecture/MULTIMODAL_DESIGN.md

### 2025-12-20 — Sweep #7 (no-alternates / no fallback paths)

Focused scan and remediation of:
- services/common
- python/helpers
- python/integrations
- services/tool_executor
- webui/js
- webui/components
- webui/design-system
- docs (SRS, architecture, UI spec, onboarding)
- tests (integration + unit)
- Makefile

### 2025-12-21 — Sweep #8 (canonical health/session routers)

Focused scan:
- services/gateway/routers

Reason: Confirmed `/v1/health` and `/v1/sessions/{session_id}/events` now exist only in `services.gateway` and replaced the legacy `src.gateway` routers with this canonical implementation.
