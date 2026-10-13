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
| infra/platform/platform/docker-compose.yml services/conversation_worker/temporal_worker.py services/delegation_gateway/temporal_worker.py services/gateway/settings.py | MiMoCode-somaAgent01 | W1.10 Temporal host authority | 2026-10-08T14:42:13Z | ACTIVE |
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
| docs/iso/ docs/README.md docs/standards/ docs/architecture/ docs/requirements/ docs/operations/ docs/project/ docs/reports/ docs/tasks/ docs/modules/ | MiMoCode-somaAgent01 | ISO docs-truth pass: fix DC headers, register, README index to match source; no code moves | 2026-10-08T22:30:00Z | ACTIVE |
| services/tool_executor/tools.py services/tool_executor/assistant_tools/ services/common/path_guard.py | MiMoCode-somaAgent01 | W3.1-W3.2 file tools | 2026-10-08T21:19:56Z | ACTIVE |
| services/conversation_worker/temporal_worker.py | MiMoCode-somaAgent01 | W3.3 ResearchReportWorkflow | 2026-10-08T21:19:56Z | ACTIVE |
| path/prefix | agent | task | started_at | status |
|---|---|---|---|---|
| admin/core/authz.py | MiMoCode-somaAgent01 | role:tool_execute grants | 2026-10-08T22:00:36Z | ACTIVE |
| admin/core/models/core.py admin/core/helpers | MiMoCode-somaAgent01 | capsule bootstrap default-kit capabilities | 2026-10-08T22:00:36Z | ACTIVE |
| services/tool_executor/request_handler.py | MiMoCode-somaAgent01 | Kafka path reuses decide_and_authorize_tool | 2026-10-08T22:00:36Z | ACTIVE |
| infra/platform infra/standalone tests/e2e | MiMoCode-somaAgent01 | Temporal workers + codeword e2e | 2026-10-08T22:00:36Z | ACTIVE |
| 2026-10-08T22:02:54Z | MiMoCode-somaAgent01 | W3.3 ResearchReportWorkflow + research_report/job_status tools (research_workflow.py, assistant_tools/research_report.py, tests) | 2026-10-08T22:02:54Z | ACTIVE |
| path/prefix | agent | task | started_at | status |
|---|---|---|---|---|
| admin/core/authz.py | MiMoCode-somaAgent01 | grant cognitive:view to sysadmin/agent_owner | 2026-10-08T23:47:26Z | ACTIVE |
| admin/core/api/settings_v2.py services/common/authorization.py | MiMoCode-somaAgent01 | settings 403 fix | 2026-10-08T23:47:26Z | ACTIVE |
| webui/src/views/soma-settings.ts webui/src/views/soma-settings-somabrain.ts | MiMoCode-somaAgent01 | Settings SomaBrain + BrainSetting UI | 2026-10-08T23:47:26Z | ACTIVE |
| path/prefix | agent | task | started_at | status |
|---|---|---|---|---|
| admin/filesv2/api.py config/settings.py webui/src/services/file-upload.ts webui/src/components/soma-right-panel.ts tests/unit/test_filesv2_upload.py tests/unit/test_ninja_error_return_convention.py | MiMoCode-somaAgent01 | Mission F file tools UI/UX (upload record-before-presign, honest Files/Editor states, composer attachment upload) | 2026-10-09T01:11:30Z | ACTIVE |
| path/prefix | agent | task | started_at | status |
|---|---|---|---|---|
| services/tool_executor/package_profiles.py services/tool_executor/assistant_tools/packages_ensure.py services/conversation_worker/package_ensure_workflow.py tests/unit/test_package_ensure_tools.py | MiMoCode-somaAgent01 | TOOLS-001 §5.4 packages_ensure landing | 2026-10-09T02:25:49Z | ACTIVE |
| services/tool_executor/assistant_tools/__init__.py services/tool_executor/default_tools.py admin/core/models/core.py admin/core/tool_calling.py services/conversation_worker/temporal_worker.py docs/architecture/SOMA-ARCH-TOOLS-001.md (§5.4 rows only) | MiMoCode-somaAgent01 | packages_ensure registration/policy/doc rows (shared files — merge, do not revert peer web_search edits) | 2026-10-09T02:25:49Z | ACTIVE |
| services/tool_executor/os_package_profiles.py services/conversation_worker/os_package_ensure_workflow.py services/tool_executor/assistant_tools/os_packages_ensure.py tests/unit/test_os_package_ensure_tools.py | MiMoCode-somaAgent01 | TOOLS-001 os_packages_ensure allowlisted container packages (new files) | 2026-10-09T03:40:00Z | ACTIVE |
| services/tool_executor/default_tools.py services/conversation_worker/temporal_worker.py admin/core/models/core.py admin/core/tool_calling.py services/tool_executor/assistant_tools/research_report.py docs/architecture/SOMA-ARCH-TOOLS-001.md (§5.4.1 subsection + approval example only) | MiMoCode-somaAgent01 | os_packages_ensure registration (shared files — merge additively, do not revert peer packages_ensure/web_search edits) | 2026-10-09T03:40:00Z | ACTIVE |
| path/prefix | agent | task | started_at | status |
|---|---|---|---|---|
| docs/architecture/SOMA-ARCH-JEV-001.md docs/project/SOMA-PM-PLAN-JEV-INTEGRATION-001.md | MiMoCode-somaAgent01 | OpenJev architecture audit + integration plan (docs only) | 2026-10-09T15:50:00Z | ACTIVE |
| path/prefix | agent | task | started_at | status |
|---|---|---|---|---|
| services/common/decisions/ admin/modules/mod_jev/ admin/core/tool_calling.py | soma-jev-engineer | JEV H.0+W-J1+W-J2: client, real OpenJev dependency, mod_jev, guardrail choke | 2026-10-09T16:45:00Z | ACTIVE |
| .mimocode/agent/ CLAUDE.md | MiMoCode-somaAgent01 | Triad profile correction for JEV workstream | 2026-10-09T16:45:00Z | ACTIVE |
| path/prefix | agent | task | started_at | status |
|---|---|---|---|---|
| docs/plans/2026-10-09-RAPID-DATA-REMEDIATION-001.md docs/reports/ | MiMoCode-somaAgent01 | RAPID-DATA-REMEDIATION-001 plan + three-way audit report | 2026-10-09T17:35:00Z | RELEASED — no code landed; suite topology unresolved |
| admin/platform/models/profiles.py admin/platform/migrations/ | MiMoCode-somaAgent01 | W0.1+W0.2 ApiKey.key_hash + UserSession.refresh_token_hash UNIQUE/index | 2026-10-09T17:35:00Z | RELEASED — no code landed; suite topology unresolved |
| admin/core/models/zdl.py | MiMoCode-somaAgent01 | W0.3 atomic IdempotencyRecord.check_and_set | 2026-10-09T17:35:00Z | RELEASED — no code landed; suite topology unresolved |
| admin/core/models/core.py admin/core/migrations/ | MiMoCode-somaAgent01 | W0.5 CHECK constraints + W3.2/W3.4/W3.8 indexes/types (shared — merge additive) | 2026-10-09T17:35:00Z | RELEASED — no code landed; suite topology unresolved |
| admin/auth/mfa.py | MiMoCode-somaAgent01 | W0.6 MFA fail-first (remove dead QR/backup codes) | 2026-10-09T17:35:00Z | RELEASED — no code landed; suite topology unresolved |
| admin/chat/api/chat.py admin/chat/models.py admin/chat/migrations/ | MiMoCode-somaAgent01 | W1.1 N+1 + W1.4 index + W3.1 chat FKs + W4.7 keyset pagination | 2026-10-09T17:35:00Z | RELEASED — no code landed; suite topology unresolved |
| config/settings.py | MiMoCode-somaAgent01 | W1.2 CONN_MAX_AGE + W1.7 GZip (shared — merge additive, do not revert peer Temporal/JEV edits) | 2026-10-09T17:35:00Z | RELEASED — no code landed; suite topology unresolved |
| admin/common/auth.py | MiMoCode-somaAgent01 | W1.3 throttle last_seen_at write | 2026-10-09T17:35:00Z | RELEASED — no code landed; suite topology unresolved |
| admin/core/chat_orchestrator.py | MiMoCode-somaAgent01 | W1.5 parallel SomaBrain writes + W4.1 TurnPlan extraction (shared — merge additive) | 2026-10-09T17:35:00Z | RELEASED — no code landed; suite topology unresolved |
| admin/core/helpers/capsule_settings.py | MiMoCode-somaAgent01 | W1.6 AgentSetting resolution cache | 2026-10-09T17:35:00Z | RELEASED — no code landed; suite topology unresolved |
| admin/core/api/settings_v2.py | MiMoCode-somaAgent01 | W1.8 bulk settings save | 2026-10-09T17:35:00Z | RELEASED — no code landed; suite topology unresolved |
| admin/common/api_keys.py admin/gateway/api/gateway.py admin/platform/api/settings.py | MiMoCode-somaAgent01 | W2.1 unify mint_api_key | 2026-10-09T17:35:00Z | RELEASED — no code landed; suite topology unresolved |
| admin/common/responses.py | MiMoCode-somaAgent01 | W2.2 one envelope + timestamp fix | 2026-10-09T17:35:00Z | RELEASED — no code landed; suite topology unresolved |
| admin/common/health_probe.py admin/core/api/health.py admin/platform/api/health.py admin/core/infrastructure/health_checker.py | MiMoCode-somaAgent01 | W2.3 shared health probes | 2026-10-09T17:35:00Z | RELEASED — no code landed; suite topology unresolved |
| admin/llm/__init__.py admin/core/permissions.py | MiMoCode-somaAgent01 | W2.4 dead re-export removal + W2.6 Actions constants | 2026-10-09T17:35:00Z | RELEASED — no code landed; suite topology unresolved |
| admin/filesv2/models.py admin/filesv2/migrations/ | MiMoCode-somaAgent01 | W3.3 partial index live rows | 2026-10-09T17:35:00Z | RELEASED — no code landed; suite topology unresolved |
| schemas/spicedb/schema.zed | MiMoCode-somaAgent01 | W3.9 strip subscription_tier / view_billing | 2026-10-09T17:35:00Z | RELEASED — no code landed; suite topology unresolved |
| path/prefix | agent | task | started_at | status |
|---|---|---|---|---|
| webui/src/ docs/plans/a2a/CLAIMS.md docs/plans/a2a/LEDGER.md | MiMoCode-somaAgent01 | FULL UI/UX audit webui vs design suite (SOMA-01-UIUX-001..005, UI-S-*) + priority indicator/settings fixes | 2026-10-12T21:28:28Z | ACTIVE |
| webui/src/services/api-client.ts webui/src/views/soma-chat.ts | MiMoCode-somaAgent01 | W4.2 ApiClient adoption + keyed repeat/virtualizer | 2026-10-09T17:35:00Z | RELEASED — no code landed; suite topology unresolved |
| services/common/memory_gateway.py | MiMoCode-somaAgent01 | W4.9 outbox happy-path create+IntegrityError (preserve T-6) | 2026-10-09T17:35:00Z | RELEASED — no code landed; suite topology unresolved |
| path/prefix | agent | task | started_at | status |
|---|---|---|---|---|
| services/common/decisions/ admin/modules/mod_clef/ admin/core/tool_calling.py policy/confidence.rego | soma-clef-engineer | Clef W-C1+W-C2: client, mod_clef, guardrail choke, brain write | 2026-10-09T19:30:00Z | ACTIVE |
| docs/architecture/SOMA-ARCH-CLEF-001.md | MiMoCode-architect | Clef replaces OpenJev — full revised architecture (docs only) | 2026-10-09T19:48:00Z | ACTIVE |
| path/prefix | agent | task | started_at | status |
|---|---|---|---|---|
| docs/ (all *.md) AGENT.md CLAUDE.md .mimocode/agent/ | triad-iso-docs | OpenJev removal + Clef truth-pass: inventory, supersede JEV docs, write Clef controlled docs, profiles | 2026-10-09T20:30:00Z | ACTIVE |
| path/prefix | agent | task | started_at | status |
|---|---|---|---|---|
| services/common/decisions/ admin/modules/mod_clef/ admin/core/tool_calling.py policy/confidence.rego | soma-clef-engineer | SUPERSEDES soma-jev-engineer claims (OpenJev removed → Clef live). W-C1+W-C2 as-built. | 2026-10-09T20:30:00Z | ACTIVE |
| docs/architecture/SOMA-ARCH-CLEF-001.md docs/architecture/SOMA-ARCH-JEV-001.md docs/architecture/SOMA-ARCH-JEV-002.md docs/project/SOMA-PM-JEV-PIN-001.md docs/project/SOMA-PM-PLAN-JEV-INTEGRATION-001.md docs/project/SOMA-PM-PLAN-CLEF-INTEGRATION-001.md | triad-iso-docs | Supersede JEV docs → Clef; truth-pass CLEF-001; write CLEF plan | 2026-10-09T20:30:00Z | ACTIVE |
| path/prefix | agent | task | started_at | status |
|---|---|---|---|---|
| services/gateway/providers.py admin/core/api/general.py admin/core/api/llm.py services/common/api_key_store.py config/settings.py admin/core/helpers/service_urls.py admin/core/chat_orchestrator.py services/common/memory_contract.py services/common/adapters/somabrain_adapter.py | MiMoCode-rapid-prod | WAVE1-RAPID: kill phantom integrations.repositories + non-persisting ApiKeyStore + DEBUG default + A-1 settings resolver + orchestrator silent [] + forget honesty + embed docs. NOT touching decisions/mod_clef/tool_calling (clef claims ACTIVE). | 2026-10-10T15:30:00Z | ACTIVE |
| .mimocode/agent/soma-deadcode-remover.md .mimocode/agent/soma-dedup-engineer.md .mimocode/agent/soma-e2e-prover.md .mimocode/agent/soma-vault-authorer.md .mimocode/agent/soma-infra-health.md .mimocode/agent/soma-prod-hardening.md | MiMoCode-rapid-prod | WAVE1-RAPID: create missing specialized agent profiles for RAPID roster | 2026-10-10T15:30:00Z | ACTIVE |
| infra/standalone/init_vault.py | MiMoCode-rapid-wave14 | RAPID WAVE 1.4 A: shared somabrain_memory_http_token contract — write→read-back length assert + documented one-value authority | 2026-01-10T00:00:00Z | ACTIVE |
| docs/standards/SOMA-STD-BOOTSTRAP-001.md infra/standalone/ services/common/vault_secrets.py services/common/unified_secret_manager.py | MiMoCode-somaAgent01 | SOMA-STD-BOOTSTRAP-001 secret-lifecycle blueprint (no-secrets-on-disk) | 2026-10-10T17:36:35Z | ACTIVE |
| path/prefix | agent | task | started_at | status |
|---|---|---|---|---|
| infra/standalone/vault_scoped_tokens.py infra/standalone/docker-compose.yml | soma-vault-authority | F-10 wire scoped tokens (stop mounting root in app/tests) + F-11 token delivery to T0_DIR tmpfs + F-19 re-unseal watch | 2026-10-10T18:30:00Z | ACTIVE |
| path/prefix | agent | task | started_at | status |
|---|---|---|---|---|
| infra/standalone/vault.hcl infra/standalone/docker-compose.yml infra/standalone/vault_unseal.py services/gateway/settings.py services/common/vault_secrets.py docs/standards/SOMA-STD-BOOTSTRAP-001.md (§3 append only) | soma-prod-hardening | F-16 audit device + F-20 JWT strict + F-22 vault cache TTL + break-glass notes (shared files — merge additive, do not revert peer edits) | 2026-10-10T18:00:00Z | ACTIVE |
| path/prefix | agent | task | started_at | status |
|---|---|---|---|---|
| services/gateway/settings.py admin/core/helpers/settings_model.py admin/core/helpers/capsule_settings.py infra/standalone/docker-compose.yml tests/unit/test_settings_model_drift.py | MiMoCode-somaAgent01 | SOMA-STD-CONFIG-001 R-BEH-01: finish gateway behaviour migration — SettingsModel.get + schema defaults, _behaviour() only, strip behaviour ENV (shared with soma-prod-hardening — merge additive, JWT_ISSUER_STRICT default preserved true) | 2026-10-10T19:00:00Z | ACTIVE |
| path/prefix | agent | task | started_at | status |
|---|---|---|---|---|
| services/gateway/settings.py admin/core/helpers/settings_model.py admin/core/helpers/settings_defaults.py admin/core/helpers/capsule_settings.py services/common/memory_contract.py services/common/memory_gateway.py admin/core/chat_orchestrator.py somabrain/somabrain/settings/django_core.py somabrain/somabrain/brain_settings/models.py somabrain/somabrain/transport/codec.py | soma-dedup-engineer | AP-03 one schema default (MEM_PROXIMITY_TOP_K / MEM_DEFAULT_SOURCE) + Rule 91 fail-closed SettingsModel.get/_behaviour + BRAIN_DEFAULTS circuit one-site + forget 3-outcome protocol doc. Under MiMoCode-somaAgent01 R-BEH-01 wave — merge additive, do not revert peer edits. NOT touching decisions/mod_clef/tool_calling (clef ACTIVE). | 2026-10-11T01:00:00Z | ACTIVE |
| admin/core/helpers/secrets.py | MiMoCode | hard-delete file-backed secret store; Vault-only redaction | 2026-10-11T17:52:57Z | ACTIVE |
| docs/standards/SOMA-STD-SECURITY-001.md docs/plans/a2a/ infra/standalone/bootstrap_exec.py infra/standalone/docker-compose.yml infra/standalone/vault_unseal.py infra/standalone/init_vault.py infra/standalone/vault_scoped_tokens.py infra/standalone/vault_inject.py infra/standalone/vault-policies/ | security-reviewer | SOMA-STD-SECURITY-001 sole security design + agent-seat minimal fixes under that standard (no ad-hoc patterns). Peer seats implement same pattern via A2A ACK. | 2026-10-11T19:46:26Z | ACTIVE |

| path/prefix | agent | task | started_at | status |
|---|---|---|---|---|
| services/common/chat_service.py tests/unit/test_chat_service_memory_honesty.py | MiMoCode-somaAgent01 | CONDITION-001 wave: C1 de-fake chat_service memory honesty (TDD) | 2026-10-12T13:16:34Z | ACTIVE |
| docs/reports/SOMA-RPT-CONDITION-001.md | MiMoCode-somaAgent01 | Full condition report (code-truth) | 2026-10-12T13:16:34Z | ACTIVE |
| infra/standalone/docker-compose.shared-network.yml infra/standalone/docker-compose.yml (shared — merge additive) | MiMoCode-somaAgent01 | Docker attach to live somabrain + health/CHAT proof | 2026-10-12T13:16:34Z | ACTIVE |
| tests/e2e/test_degradation_auto.py tests/unit/test_degradation_doctrine.py | MiMoCode-somaAgent01 | Degradation auto-down + auto-recover proof | 2026-10-12T13:17:00Z | ACTIVE |
| path/prefix | agent | task | started_at | status |
|---|---|---|---|---|
| admin/core/CURRENT_PLAN.md admin/core/MASTER_FIX_TODO.md admin/core/MASTER_TODO_LIST.md admin/core/UNIFIED_AUDIT_AND_PLAN.md docs/ (orphan scan) | triad-docs-remediation | Documentation + source-comment remediation: hard-delete orphans, fix wrong docs, comment audit, ISO control gaps | 2026-10-12T09:00:00Z | ACTIVE |

| path/prefix | agent | task | started_at | status |
|---|---|---|---|---|
| docs/architecture/SOMA-ARCH-SEC-TOKEN-001.md docs/standards/SOMA-STD-SECURITY-001.md docs/plans/a2a/ infra/standalone/bootstrap_exec.py infra/standalone/init_vault.py infra/standalone/vault_unseal.py infra/standalone/vault_scoped_tokens.py infra/standalone/vault_inject.py infra/standalone/docker-compose.yml infra/standalone/vault-policies/ services/common/vault_secrets.py services/common/http_egress.py services/tool_executor/tools.py admin/filesv2/api.py | security-reviewer | SOMA-ARCH-SEC-TOKEN-001 ADR (sole trust boundary) + W0-W3 fixes (C-1 SSRF, C-2 IDOR, C-3 generation stamp). Shared files merge-additive with soma-vault-authority / soma-prod-hardening. NOT touching decisions/mod_clef. | 2026-10-12T13:53:10Z | ACTIVE |

| path/prefix | agent | task | started_at | status |
|---|---|---|---|---|
| admin/llm/providers.py admin/llm/api.py admin/llm/migrations/0006_seed_model_catalog.py admin/core/helpers/vendor_api_bases.py admin/secrets/api.py services/common/unified_secret_manager.py webui/src/views/soma-settings-models.ts | MiMoCode-wave1-model-registry | WAVE1 model registry + Clef + 5 model roles: KNOWN_PROVIDER_IDS, model_type decision, 5-role slots, bundled presets, 0006 catalog seed, vault note, provider-list collapse | 2026-10-12T20:00:00Z | ACTIVE |
| path/prefix | agent | task | started_at | status |
|---|---|---|---|---|
| infra/standalone/seed_clef_vault.py admin/core/management/commands/bootstrap_clef.py admin/llm/migrations/0006_seed_clef_decision.py admin/llm/api.py admin/core/helpers/vendor_api_bases.py admin/core/config/registry.py services/common/decisions/clef_client.py | MiMoCode-clef-decision | CLEF decision model live: vault seed, settings chain, LLMModelConfig decision row, decision_role slots/presets, feature flag | 2026-10-12T12:10:00Z | ACTIVE |
| path/prefix | agent | task | started_at | status |
|---|---|---|---|---|
| services/conversation_worker/temporal_worker.py services/conversation_worker/zero_loss_activities.py services/delegation_gateway/temporal_worker.py docs/operations/SOMA-OPS-TEMPORAL-TLS-001.md tests/unit/test_temporal_owns_async_cycle.py | MiMoCode-wave5-temporal | WAVE 5 one Temporal worker (A2A fold) + MemoryReplication/SleepConsolidation/PromotionAudit/ReplayRecovery workflows + mTLS note | 2026-10-12T22:30:00Z | ACTIVE |

| path/prefix | agent | task | started_at | status |
|---|---|---|---|---|
| admin/core/bootstrap/ admin/core/management/commands/bootstrap_soma.py admin/core/management/commands/bootstrap_platform.py admin/llm/migrations/0005_seed_mimo_flash.py infra/standalone/start.sh Makefile | MiMoCode-wave2-bootstrap | WAVE 2 BOOTSTRAP: bootstrap_soma 8-phase command + mimo-flash seed + start.sh bootstrap gate + Makefile bootstrap/verify-chat | 2026-10-12T23:30:00Z | DONE — all phases + verify_chat_ready green live; Makefile defaults hard-deleted; see LEDGER 2026-10-13 |
| services/common/ admin/ infra/standalone/ services/conversation_worker/ services/delegation_gateway/ services/gateway/ services/bridge_worker/ services/tool_executor/ config/ tests/ webui/src/views/ admin/core/bootstrap/ admin/core/management/commands/ | MiMoCode-law-enforcement | LAW CLEANUP: hard-delete env-config, hardcoded URLs, shims/fakes on uncommitted diff + untracked bootstrap/seed files | 2026-10-12T19:49:06Z | DONE |

| path/prefix | agent | task | started_at | status |
|---|---|---|---|---|
| admin/core/chat_orchestrator.py services/gateway/consumers/chat.py services/gateway/providers.py admin/llm/ services/common/unified_secret_manager.py | MiMoCode-chat-fix | Mission T chat reply path: WS→orchestrator→LLM→reply + honest provider-key Vault path | 2026-10-13T00:00:00Z | ACTIVE |
| tests/e2e/test_human_chat_session.spec.js tests/e2e/test_memory_human_name.spec.js tests/e2e/test_chat_context_memory.spec.js tests/e2e/ | MiMoCode-chat-fix | Mission T Playwright on real services (3 specs) + defects they expose | 2026-10-13T00:00:00Z | ACTIVE |

| path/prefix | agent | task | started_at | status |
|---|---|---|---|---|
| webui/src/views/soma-settings-models.ts webui/src/views/soma-admin-api-keys.ts webui/src/views/soma-chat.ts webui/src/views/soma-personal-profile.ts webui/src/components/soma-right-panel.ts webui/src/views/soma-login.ts webui/src/views/soma-register.ts webui/src/views/soma-forgot-password.ts admin/llm/api.py admin/core/model_router.py | MiMoCode-wave6-webui-roles | WAVE 6 WebUI model roles/presets UX: rename remaining slot wording to Model Roles, 5-role panel, Clef decision binding, presets bind all 5 roles, honest loading/error, HARD DELETE hardcoded URLs/env/placeholder secrets in webui | 2026-10-12T19:51:57Z | ACTIVE |

| path/prefix | agent | task | started_at | status |
|---|---|---|---|---|
| services/gateway/consumers/chat.py services/common/chat_service.py admin/core/chat_orchestrator.py tests/unit/test_ws_chat_error_frames.py tests/unit/test_chat_service_tenant_honesty.py | MiMoCode-wave3-chat | WAVE 3 chat/memory/cognition: bare close + missing error frames + silent failure de-fake + hardcoded defaults | 2026-10-13T00:00:00Z | DONE |

| path/prefix | agent | task | started_at | status |
|---|---|---|---|---|
| docs/reports/SOMA-RPT-TRIAD-PROOF-001.md docs/plans/a2a/CLAIMS.md docs/plans/a2a/LEDGER.md | MiMoCode-tribo | TRIAD live proof (T-1/T-6/no-mock): rg + HTTP remember/recall/chat + SFM hop diagnosis. Read-only on code; report + A2A only. | 2026-10-12T21:45:00Z | DONE — agent side PROVEN; Brain→SFM hop blocked by pre-existing SFM SOMA_BOUND_TENANT 401 |

| path/prefix | agent | task | started_at | status |
|---|---|---|---|---|
| webui/src/views/soma-memory-view.ts webui/src/views/soma-chat.ts docs/reports/SOMA-RPT-UIUX-AUDIT-001.md docs/plans/a2a/CLAIMS.md docs/plans/a2a/LEDGER.md | MiMoCode-uiux-audit | FULL UI/UX audit webui vs design suite (UIUX-001..005, UI-S-*) + P1-P6 fixes: memory panel WM/LTM tiles + Remember/Run probe + ?turn=current, chat model LIVE chip (chat_role bound), C2 Open Memory link, honest totals | 2026-10-13T01:30:00Z | DONE — tsc exit 0; no commits |
| docs/architecture/SOMA-ARCH-SKINS-001.md | architect-skins | Skinnable UI theme system architecture (new doc only; no edits to existing arch docs) | 2026-10-12T23:46:50Z | ACTIVE |

| path/prefix | agent | task | started_at | status |
|---|---|---|---|---|
| somafractalmemory/secrets/ somafractalmemory/somafractalmemory/api/auth.py somafractalmemory/somafractalmemory/api/utils.py somabrain/somabrain/api/standalone_auth.py somabrain/somabrain/transactions/event_store.py somabrain/somabrain/services/tiered_memory_registry.py somaAgent01/admin/orchestrator/health_router.py somafractalmemory/infra/standalone/seed_vault.py docs/reports/ | MiMoCode-sec-review-2026-10-13 | Enterprise security review + minimal fixes (secrets-on-disk, admin:read on shared token, tenant fail-closed, unauth health, banned VAULT_TOKEN alias) | 2026-10-13T02:30:00Z | DONE — 7 fixes landed, 6 residuals documented in SOMA-RPT-SEC-REVIEW-2026-10-13; no commits |

| path/prefix | agent | task | started_at | status |
|---|---|---|---|---|
| webui/src/views/soma-chat.ts webui/src/components/soma-message.ts webui/src/components/soma-tool-timeline.ts webui/src/components/soma-composer.ts | MiMoCode-soma-chat-uiux | Chat UI reliability + bubble/cards/media/transitions polish (delta/done commit, live bubble, turn-meta chips, media cards, a11y) | 2026-01-15T00:00:00Z | ACTIVE |

| path/prefix | agent | task | started_at | status |
|---|---|---|---|---|
| webui/src/skin-sdk/ webui/src/services/skin-applier.ts webui/src/services/skin-boot.ts webui/src/styles/skin-aliases.css webui/src/styles/tokens.css | MiMoCode-AgentSkin-SDK | AgentSkin-SDK branch: skin vocabulary + schema + sanitiser + templates + applier (P0-P1 of SOMA-ARCH-SKINS-001). Branch AgentSkin-SDK. Shared webui files merge-additive; do not revert peer chat-uiux / wave6-webui-roles edits. | 2026-10-12T23:58:53Z | ACTIVE |

| path/prefix | agent | task | started_at | status |
|---|---|---|---|---|
| tests/e2e/test_human_chat_session.spec.js tests/e2e/test_memory_human_name.spec.js tests/e2e/test_chat_context_memory.spec.js services/tool_executor/memory_tools.py admin/core/chat_orchestrator.py admin/memory/api/memory.py | MiMoCode-mission-t-playwright | Mission T Playwright: 3 specs green on real services + memory recall ranking defect fix (tier facts>questions, multi-query, list endpoint fact pass) | 2026-10-13T00:15:00Z | DONE — 13/13 passed; see LEDGER 2026-10-13 |

| path/prefix | agent | task | started_at | status |
|---|---|---|---|---|
| webui/src/styles/ webui/src/skin-sdk/ | MiMoCode-UI-orchestrator | L0 tokens+glass freeze | 2026-10-13T17:19:52Z | ACTIVE |
| webui/src/components/soma-toast-stack.ts webui/src/components/soma-notification-tray.ts webui/src/components/soma-notification-bell.ts webui/src/components/soma-notification-center.ts | MiMoCode-UI-notify | notifications icon/toast/tray | 2026-10-13T17:19:52Z | ACTIVE |
| webui/src/components/soma-profile.ts webui/src/components/soma-password-modal.ts webui/src/views/soma-personal-profile.ts | MiMoCode-UI-profile | profile + change password | 2026-10-13T17:19:52Z | ACTIVE |
| webui/src/components/soma-agent-package.ts webui/src/components/soma-agent-hands.ts webui/src/components/soma-agent-export-modal.ts | MiMoCode-UI-hands | Agent package export/import + Hands tools | 2026-10-13T17:19:52Z | ACTIVE |
| webui/src/components/soma-file-manager.ts webui/src/components/soma-artifacts.ts webui/src/components/file-manager/* | MiMoCode-UI-files | File Manager + Artifacts | 2026-10-13T17:19:52Z | ACTIVE |
| webui/src/components/soma-somabrain-manager.ts webui/src/views/soma-settings-somabrain.ts | MiMoCode-UI-brain | Brain manager (modulators/mode) | 2026-10-13T17:19:52Z | ACTIVE |
| webui/src/components/soma-chat-settings.ts webui/src/components/soma-reasoning-block.ts | MiMoCode-UI-chatprefs | Chat settings modal + CoT | 2026-10-13T17:19:52Z | ACTIVE |
| docs/design/_superseded/ docs/design/SOMA-UI-MASTER-001.md | MiMoCode-UI-docs | doc merge/delete cleanup | 2026-10-13T17:19:52Z | ACTIVE |

| path/prefix | agent | task | started_at | status |
|---|---|---|---|---|
| webui/src/skin-sdk/ webui/src/styles/tokens.css webui/src/styles/skin-aliases.css webui/src/services/skin-applier.ts webui/src/services/skin-boot.ts docs/design/ docs/design/control-maps/ | soma-ui-engineer | UI/UX seat A: skin-sdk + token vocabulary + design/control-map docs authority (continues MiMoCode-AgentSkin-SDK). Peer seat B owns component/view implementation merge-additive. | 2026-10-13T17:20:28Z | ACTIVE |
| webui/src/components/ webui/src/views/ (implementation of MODULE-CATALOG L0-L4 + CM-* PLANNED rows: shell, toast+tray+bell, Profile+password, Agent package export/import + Hands tools install, File Manager, Chat settings CoT) | UI-peer-seat-B | UI/UX seat B: component implementation to SOMA-UI-PEER-BRIEF-001 contracts. Merge-additive with seat A; do not edit skin-sdk/ or tokens.css. Respect ACTIVE claims (soma-chat-uiux on chat components; wave6-webui-roles on models/profile/right-panel/login). | 2026-10-13T17:20:28Z | ACTIVE |

| path/prefix | agent | task | started_at | status |
|---|---|---|---|---|
| webui/src/components/soma-file-manager.ts webui/src/components/soma-artifacts.ts webui/src/views/soma-chat.ts webui/src/views/soma-personal-profile.ts webui/src/components/soma-user-profile-card.ts webui/src/components/soma-chat-settings.ts webui/src/components/soma-chat-topbar.ts webui/src/components/file-manager/ | soma-deadcode-remover | webui/src dead-code sweep (AgentSkin-SDK): unused imports/unused CSS/emoji-comment junk in file-manager+chat+profile only. No behavior change; keep honest GATED strings. Grep-proven zero callers before each delete. Respect ACTIVE peer claims (merge-additive; do not rewrite peer-owned feature code). | 2026-10-13T18:59:16Z | DONE — dead CSS + zero-caller mode-dropdown cluster removed; tsc clean on swept files; GATED kept; peer rewrite of file-manager/soma-chat observed mid-sweep |

| path/prefix | agent | task | started_at | status |
|---|---|---|---|---|
| webui/src/components/soma-file-manager.ts webui/src/components/soma-message.ts webui/src/components/soma-composer.ts webui/src/utils/file-icons.ts webui/src/views/soma-chat.ts webui/src/components/soma-right-panel.ts webui/src/components/soma-tool-timeline.ts webui/src/components/soma-chat-settings.ts webui/src/components/soma-capsule-editor.ts webui/src/components/soma-agent-header.ts webui/src/views/soma-settings-models.ts webui/src/views/soma-settings.ts webui/src/views/soma-settings-channels.ts webui/src/views/soma-integrations-dashboard.ts webui/src/views/soma-admin-api-keys.ts webui/src/views/soma-memory-view.ts webui/src/components/soma-agent-iq.ts docs/design/control-maps/CM-01-chat-workspace.md docs/design/control-maps/CM-02-file-manager.md docs/design/control-maps/00-INDEX.md | soma-ui-engineer | Chat/file UI enterprise polish: zero emojis (Material icons only), file manager workroot/inbox tree + move/rename/delete honest gates, clean attachment cards, Capsule→Agent product names in UI, CM-01/CM-02 ISO control-map updates. Merge-additive with UI-peer-seat-B / MiMoCode-UI-files / soma-chat-uiux. | 2026-10-13T18:30:00Z | ACTIVE |

| path/prefix | agent | task | started_at | status |
|---|---|---|---|---|
| webui/src/i18n/ webui/src/components/soma-profile-modal.ts webui/src/components/soma-file-manager-modal.ts webui/src/views/soma-settings.ts (minimal _setInterface language → setLocale) | soma-ui-engineer | SOMA-UI-I18N-001: i18n module (t/setLocale/getLocale/onLocaleChange, soma_locale, html lang) + en/es catalogs (profile/files/chat/common parity) + wire t() into profile + file-manager modal chrome + settings language setLocale. Merge-additive with UI-peer-seat-B / MiMoCode-UI-files / wave6-webui-roles. | 2026-10-13T19:30:00Z | ACTIVE |

| path/prefix | agent | task | started_at | status |
|---|---|---|---|---|
| webui/src/views/soma-settings.ts webui/src/views/soma-settings-models.ts webui/src/views/soma-settings-somabrain.ts webui/src/views/soma-personal-profile.ts | soma-ui-engineer | Skin-token migration: replace hex/px literals with var(--skin-*), adopt glassCard+moduleBase, no behavior change. CSS-only. Merge-additive with UI-peer-seat-B / MiMoCode-UI-brain / wave6-webui-roles / MiMoCode-UI-profile. | 2026-10-13T19:55:26Z | ACTIVE |

| path/prefix | agent | task | started_at | status |
|---|---|---|---|---|
| webui/src/components/soma-message.ts webui/src/components/soma-composer.ts webui/src/components/soma-tool-timeline.ts webui/src/components/soma-chat-topbar.ts | soma-ui-engineer | AgentSkin CSS migration (--skin-* only): static styles = glassCard/moduleBase/css; replace hex+px literals with skin tokens; behavior identical. Merge-additive with MiMoCode-soma-chat-uiux / UI-peer-seat-B. | 2026-10-14T12:00:00Z | ACTIVE |

| webui/src/views/soma-memory-view.ts webui/src/components/soma-brain-manager.ts webui/src/views/soma-login.ts webui/src/views/soma-cognitive-panel.ts | soma-ui-engineer | CSS migrate to --skin-* tokens + glassCard/moduleBase | 2026-10-10T00:00:00Z | DONE — glassCard+moduleBase composed; hex/px/--soma-* zeroed in static styles; tsc clean |

| path/prefix | agent | task | started_at | status |
|---|---|---|---|---|
| webui/src/components/soma-file-manager.ts webui/src/components/soma-right-panel.ts webui/src/components/soma-profile-modal.ts webui/src/components/soma-chat-settings.ts | soma-ui-engineer | AgentSkin CSS migration wave 2 (--skin-* only): static styles = glassCard/moduleBase/css; replace hex+px literals with skin tokens; no hex; tsc clean; commit only these four files. Merge-additive with MiMoCode-UI-files / UI-peer-seat-B / MiMoCode-UI-chatprefs / wave6-webui-roles. | 2026-10-14T12:30:00Z | ACTIVE |
| path/prefix | agent | task | started_at | status |
|---|---|---|---|---|
| docs/standards/SOMA-STD-UIUX-001.md docs/design/SOMA-UI-SKINS-001.md (§13A link only) CLAUDE.md (UI/UX row only) | soma-ui-engineer | UI/UX working standard (docs only) | 2026-10-13T00:00:00Z | ACTIVE |

| path/prefix | agent | task | started_at | status |
|---|---|---|---|---|
| tests/e2e/profile-window.spec.ts tests/e2e/files-modal.spec.ts tests/e2e/skins-gallery.spec.ts tests/e2e/chat-display.spec.ts | soma-e2e-prover | Human-like Playwright live UI suite (Profile/Files/Skins/Display) against :20080 — real clicks only, no network mocks, honest GATED assertions | 2026-10-14T20:15:00Z | ACTIVE |
| path/prefix | agent | task | started_at | status |
|---|---|---|---|---|
| tests/e2e/ (run evidence only; no product edits) | soma-e2e-prover | Live Playwright run: profile modal · Files modal · skins gallery against Docker UI :20080 — screenshots tmp/soma-e2e ( /tmp/soma-e2e blocked by sandbox external_directory policy ) | 2026-10-13T20:27:53Z | DONE — 8/8 FAIL at live login (Vault service token expired → identity pepper unreadable → 503 Identity service is not configured). Honest fail-closed. Evidence tmp/soma-e2e/run-20261013T202818Z.log |

| path/prefix | agent | task | started_at | status |
|---|---|---|---|---|
| docs/reports/SOMA-RPT-SEC-VAULT-001.md docs/standards/SOMA-STD-BOOTSTRAP-001.md docs/standards/SOMA-STD-SECURITY-001.md docs/standards/SOMA-LAW-SECURITY-001.md CLAUDE.md docs/iso/DOCUMENT-REGISTER.md docs/plans/a2a/ | security-reviewer | Vault token expiry outage: DOC sync to live code + validated ceremony (orphan no_parent, 720h, T0 named-volume ext4, never root on disk). Docs-only turn. | 2026-10-13T20:50:00Z | DONE — report+errata issued; residual Δ-06 bootstrap_exec non-orphan mint logged for code turn |

| path/prefix | agent | task | started_at | status |
|---|---|---|---|---|
| docs/reports/SOMA-RPT-VAULT-AUTHORITY-001.md | soma-vault-authority | Vault-authority static code-truth audit: skill-claim vs code (single credential, KV merge-safe, read-back, *_FILE, fail-closed, orphan 720h). Docs only; no secret values. | 2026-10-13T21:19:40Z | ACTIVE |

| path/prefix | agent | task | started_at | status |
|---|---|---|---|---|
| docs/reports/SOMA-RPT-SEC-CODE-DOCS-001.md docs/standards/SOMA-LAW-SECURITY-001.md infra/standalone/README.md | security-reviewer | Doc-vs-code security verification report + two doc mismatches fixed (README root-in-T0, LAW policy wording). Docs only. | 2026-10-13T22:00:00Z | ACTIVE |
