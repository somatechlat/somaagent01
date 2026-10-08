# A2A CLAIMS.md
| path/prefix | agent | task | started_at | status |
|---|---|---|---|---|
| webui/ | MiMoCode-somaAgent01 | UI/UX report + plan + later implementation | 2026-10-08T12:51:34Z | ACTIVE |
| docs/design/ | MiMoCode-somaAgent01 | UI/UX docs + plan | 2026-10-08T12:51:34Z | ACTIVE |
| docs/plans/ | MiMoCode-somaAgent01 | wiring report + UI/UX plan | 2026-10-08T12:51:34Z | ACTIVE |
| services/common/adapters/somabrain_adapter.py | MiMoCode-somaAgent01 | R-15 MemoryAck.from_brain_response | 2026-10-08T12:51:34Z | ACTIVE |
| services/common/memory_contract.py | MiMoCode-somaAgent01 | R-15 contract (already landed; keep honest) | 2026-10-08T12:51:34Z | ACTIVE |
| path/prefix | agent | task | started_at | status |
|---|---|---|---|---|
| admin/somabrain/ admin/agents/services/somabrain_integration.py admin/core/api/migrate.py services/gateway/consumers/chat.py | MiMoCode-somaAgent01 | W1.5 kill phantom SomaBrainClient call sites | 2026-10-08T14:42:13Z | ACTIVE |
| admin/core/somabrain_client.py | MiMoCode-somaAgent01 | W1.5 client methods / reward path | 2026-10-08T14:42:13Z | ACTIVE |
| admin/core/chat_orchestrator.py | MiMoCode-somaAgent01 | W1.5 settings gates + evaluate contract | 2026-10-08T14:42:13Z | ACTIVE |
| webui/src/views/soma-cognitive-panel.ts webui/src/views/soma-chat.ts | MiMoCode-somaAgent01 | W1.8 panel agent-id + data source | 2026-10-08T14:42:13Z | ACTIVE |
| infra/aaas/aaas/docker-compose.yml services/conversation_worker/temporal_worker.py services/delegation_gateway/temporal_worker.py services/gateway/settings.py | MiMoCode-somaAgent01 | W1.10 Temporal host authority | 2026-10-08T14:42:13Z | ACTIVE |
| services/common/adapters/somabrain_adapter.py | MiMoCode-somaAgent01 | W1.9 R-15 MemoryAck | 2026-10-08T14:42:13Z | ACTIVE |
| path/prefix | agent | task | started_at | status |
|---|---|---|---|---|
| admin/auth/ admin/common/auth.py | MiMoCode-somaAgent01 | login: local session + Keycloak /me independence | 2026-10-08T16:49:51Z | ACTIVE |
| admin/somabrain/cognitive.py admin/core/somabrain_client.py | MiMoCode-somaAgent01 | cognitive state → neuromod + sleep proxy | 2026-10-08T16:49:51Z | ACTIVE |
| tests/unit/test_identity_local_login.py tests/unit/test_role_superset.py tests/unit/test_spicedb_verb_coverage.py tests/unit/test_redis_pool_loop_restart.py | MiMoCode-somaAgent01 | triage remaining unit failures | 2026-10-08T16:49:51Z | ACTIVE |
| tests/e2e/ webui/src/views/soma-login.ts | MiMoCode-somaAgent01 | login E2E + codeword gate prep | 2026-10-08T16:49:51Z | ACTIVE |
| path/prefix | agent | task | started_at | status |
|---|---|---|---|---|
| docs/architecture/SOMA-ARCH-TOOLS-001.md | MiMoCode-somaAgent01 | tool framework standard | 2026-10-08T21:07:07Z | ACTIVE |
| services/common/path_guard.py services/tool_executor/path_guard.py | MiMoCode-somaAgent01 | PathGuard foundation | 2026-10-08T21:07:07Z | ACTIVE |
| admin/core/tool_calling.py | MiMoCode-somaAgent01 | invert unlisted→approval + choke point | 2026-10-08T21:07:07Z | ACTIVE |
| path/prefix | agent | task | started_at | status |
|---|---|---|---|---|
| admin/core/tool_calling.py admin/core/chat_orchestrator.py | MiMoCode-somaAgent01 | W2.5 policy choke UnifiedGate per tool | 2026-10-08T21:19:56Z | ACTIVE |
| services/tool_executor/tools.py services/tool_executor/assistant_tools/ services/common/path_guard.py | MiMoCode-somaAgent01 | W3.1-W3.2 file tools | 2026-10-08T21:19:56Z | ACTIVE |
| services/conversation_worker/temporal_worker.py | MiMoCode-somaAgent01 | W3.3 ResearchReportWorkflow | 2026-10-08T21:19:56Z | ACTIVE |
| path/prefix | agent | task | started_at | status |
|---|---|---|---|---|
| admin/core/authz.py | MiMoCode-somaAgent01 | role:tool_execute grants | 2026-10-08T22:00:36Z | ACTIVE |
| admin/core/models/core.py admin/core/helpers | MiMoCode-somaAgent01 | capsule bootstrap default-kit capabilities | 2026-10-08T22:00:36Z | ACTIVE |
| services/tool_executor/request_handler.py | MiMoCode-somaAgent01 | Kafka path reuses decide_and_authorize_tool | 2026-10-08T22:00:36Z | ACTIVE |
| infra/aaas infra/standalone tests/e2e | MiMoCode-somaAgent01 | Temporal workers + codeword e2e | 2026-10-08T22:00:36Z | ACTIVE |
| 2026-10-08T22:02:54Z | MiMoCode-somaAgent01 | W3.3 ResearchReportWorkflow + research_report/job_status tools (research_workflow.py, assistant_tools/research_report.py, tests) | 2026-10-08T22:02:54Z | ACTIVE |
