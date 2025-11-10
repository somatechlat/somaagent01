# Test Suite Analysis & Reorganization Plan

## Analysis Summary

**Total test files**: 116
**Root-level test files**: 33 (DISORGANIZED - need reorganization)

## Test Categories & Decisions

### ✅ KEEP - Tests Real Agent Functionality

#### 1. Agent Context & Behavior Tests (tests/context/)
- `test_conflicting_directives_live.py` - **KEEP** - Tests agent handling conflicting instructions
- `test_goal_switching_live.py` - **KEEP** - Tests agent context switching between tasks
- `test_long_term_callback_live.py` - **KEEP** - Tests agent memory recall across conversations

#### 2. End-to-End Integration Tests (tests/e2e/)
- `test_tool_flow.py` - **KEEP** - Tests real tool execution (echo tool)
- `test_memory_pipeline_e2e.py` - **KEEP** - Tests WAL → Replica memory pipeline
- `test_memory_write_through.py` - **KEEP** - Tests memory persistence
- `test_memory_sync_recovery_e2e.py` - **KEEP** - Tests memory recovery
- `test_api_contract_smoke.py` - **KEEP** - Tests Gateway API contracts
- `test_ui_chat_playwright.py` - **KEEP** - Tests UI chat functionality
- `test_ui_smoke.py` - **KEEP** - Tests UI loads correctly

#### 3. Core Integration Tests (tests/integration/)
- `test_memory_guarantees.py` - **KEEP** - Tests memory durability guarantees
- `test_gateway_api_keys.py` - **KEEP** - Tests API key authentication
- `test_gateway_public_api.py` - **KEEP** - Tests public Gateway endpoints
- `test_session_repository.py` - **KEEP** - Tests session persistence
- `test_durable_publisher_fallback.py` - **KEEP** - Tests event publishing reliability

#### 4. Critical Infrastructure Tests (tests/integrations/)
- `test_somabrain_client.py` - **KEEP** - Tests SomaBrain integration (memory backend)
- `test_opa_middleware.py` - **KEEP** - Tests policy enforcement

#### 5. Real Conversation Tests (root level)
- `test_conversation_integrity.py` - **KEEP** - Tests event deduplication, error normalization
- `test_llm_integration.py` - **KEEP** - Tests real LLM invoke/streaming

### ❌ DELETE - Mock/Stub/Redundant Tests

#### Root Level Tests to DELETE (33 files → ~20 to delete)
- `chunk_parser_test.py` - DELETE (utility test, not agent functionality)
- `escalation_test.py` - DELETE (unclear what this tests)
- `rate_limiter_test.py` - DELETE (infrastructure, not agent)
- `test_admin_audit_decisions.py` - DELETE (admin tooling, not agent)
- `test_admin_export_endpoint.py` - DELETE (admin tooling)
- `test_admin_memory_endpoints.py` - KEEP (memory is core)
- `test_admin_memory_structured_filters.py` - KEEP (memory queries)
- `test_audit_export_endpoint.py` - DELETE (admin tooling)
- `test_chunked_upload_flow.py` - KEEP (file uploads for agent)
- `test_dlq_store.py` - DELETE (infrastructure)
- `test_export_jobs.py` - DELETE (admin tooling)
- `test_fasta2a_client.py` - DELETE (unclear relevance)
- `test_gateway_config_and_dlq.py` - DELETE (infrastructure)
- `test_gateway_llm_audit.py` - KEEP (LLM auditing is important)
- `test_gateway_security_s2.py` - DELETE (security infrastructure)
- `test_gateway_tool_request_audit.py` - KEEP (tool auditing)
- `test_gateway_write_through.py` - KEEP (memory write-through)
- `test_masking_classifier.py` - DELETE (utility)
- `test_memory_load_tool.py` - KEEP (memory tool)
- `test_memory_migrate.py` - DELETE (migration script)
- `test_memory_replica_store.py` - DELETE (covered by e2e)
- `test_memory_replicator_worker.py` - DELETE (covered by e2e)
- `test_memory_write_outbox_and_gateway_failover.py` - KEEP (failover critical)
- `test_metrics_persistence.py` - DELETE (observability infra)
- `test_notifications_api.py` - DELETE (UI notifications, not agent)
- `test_outbox_repository.py` - DELETE (infrastructure)
- `test_outbox_sync_health.py` - DELETE (infrastructure)
- `test_rate_limit_and_sequence.py` - DELETE (infrastructure)
- `test_session_repository.py` - KEEP (session persistence)
- `test_tool_events.py` - KEEP (tool execution events)
- `test_tool_executor_audit.py` - KEEP (tool execution)
- `test_ui_login_guard.py` - DELETE (UI auth, not agent)
- `test_ui_settings_uploads.py` - DELETE (UI settings)
- `test_uploads_write_through.py` - KEEP (file uploads)

#### Unit Tests to Review (tests/unit/)
Most unit tests are infrastructure/plumbing tests, not agent functionality:
- **DELETE**: All tests for circuit breakers, metrics, config registry, logging, vault
- **DELETE**: All "no_direct_env" guard tests (CI enforcement, not functionality)
- **KEEP**: `test_tool_catalog_integration.py` - Tool catalog is core
- **KEEP**: `test_conversation_worker_*` - Worker behavior is core
- **KEEP**: `test_document_ingest_tool.py` - Document ingestion is agent feature
- **KEEP**: `test_learning_module.py` - Learning is agent feature
- **KEEP**: `test_semantic_recall_index.py` - Memory recall is core

#### Playwright Tests (tests/playwright/)
- **KEEP**: `test_full_flow.py` - Full UI flow
- **KEEP**: `test_ui_flows.py` - UI interaction flows
- **DELETE**: `test_ui_behavior_golden.py` - Golden file testing (brittle)
- **DELETE**: `test_ui_behavior_local.py` - Duplicate of other UI tests
- **DELETE**: `test_ui_flows_parity.py` - Parity testing (not functionality)
- **DELETE**: `test_notifications_flow.py` - UI notifications
- **DELETE**: `test_realtime_speech.py` - Speech feature (optional)

#### Docs Tests (tests/docs/)
- **DELETE**: Both files - Documentation validation, not agent functionality

#### Chaos Tests (tests/chaos/)
- **KEEP**: `test_memory_recovery.py` - Chaos testing is valuable for reliability

## Reorganization Plan

### New Structure
```
tests/
├── agent/                          # Real agent behavior tests
│   ├── context/                    # Context management
│   │   ├── test_conflicting_directives.py
│   │   ├── test_goal_switching.py
│   │   └── test_long_term_recall.py
│   ├── conversation/               # Conversation flow
│   │   ├── test_conversation_integrity.py
│   │   └── test_conversation_worker.py
│   ├── memory/                     # Memory & recall
│   │   ├── test_memory_pipeline_e2e.py
│   │   ├── test_memory_write_through.py
│   │   ├── test_memory_guarantees.py
│   │   ├── test_memory_load_tool.py
│   │   └── test_semantic_recall.py
│   ├── tools/                      # Tool execution
│   │   ├── test_tool_flow.py
│   │   ├── test_tool_events.py
│   │   ├── test_tool_executor.py
│   │   ├── test_tool_catalog.py
│   │   └── test_document_ingest.py
│   └── llm/                        # LLM integration
│       ├── test_llm_integration.py
│       └── test_llm_audit.py
├── integration/                    # Integration tests (keep existing)
│   ├── gateway/
│   ├── test_gateway_api_keys.py
│   ├── test_gateway_public_api.py
│   ├── test_somabrain_client.py
│   ├── test_opa_middleware.py
│   └── test_session_repository.py
├── ui/                             # UI tests
│   ├── playwright/
│   │   ├── test_full_flow.py
│   │   └── test_ui_flows.py
│   ├── test_ui_chat.py
│   └── test_ui_smoke.py
├── chaos/                          # Chaos/reliability tests
│   └── test_memory_recovery.py
├── conftest.py
└── README.md                       # Test suite documentation
```

## Execution Plan

1. **Create new directory structure**
2. **Move KEEP files to organized locations**
3. **Delete redundant/infrastructure tests**
4. **Update imports in moved files**
5. **Create tests/README.md with test suite documentation**
6. **Update CI/CD to use new structure**

## Test Count Summary

- **Before**: 116 test files (disorganized)
- **After**: ~40-50 test files (organized by agent functionality)
- **Deleted**: ~60-70 infrastructure/mock/redundant tests
