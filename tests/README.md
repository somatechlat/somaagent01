# SomaAgent01 Test Suite

## Overview

This test suite focuses on **real agent functionality** - no mocks, no stubs, no invented tests. Every test here validates actual agent behavior, memory, tools, and LLM integration.

## Test Organization

### `agent/` - Core Agent Functionality

#### `agent/context/` - Context Management
Tests how the agent manages conversation context, handles conflicting instructions, and switches between goals.

- `test_conflicting_directives.py` - Agent handles conflicting user instructions
- `test_goal_switching.py` - Agent switches context between different tasks
- `test_long_term_recall.py` - Agent recalls facts from long-term memory

#### `agent/conversation/` - Conversation Flow
Tests conversation integrity, worker behavior, and learning capabilities.

- `test_conversation_integrity.py` - Event deduplication, error normalization, streaming
- `test_conversation_worker_*.py` - Worker recall behavior and SSE streaming
- `test_learning_module.py` - Agent learning from interactions

#### `agent/memory/` - Memory & Persistence
Tests memory pipeline, write-through, guarantees, and recall.

- `test_memory_pipeline_e2e.py` - WAL → Replica memory pipeline
- `test_memory_write_through.py` - Memory write-through to SomaBrain
- `test_memory_sync_recovery_e2e.py` - Memory recovery after failures
- `test_memory_guarantees.py` - Memory durability guarantees
- `test_memory_write_outbox_and_gateway_failover.py` - Failover scenarios
- `test_semantic_recall.py` - Semantic memory recall
- `test_admin_memory_*.py` - Memory admin endpoints and filters
- `test_gateway_write_through.py` - Gateway memory write-through

#### `agent/tools/` - Tool Execution
Tests tool catalog, execution, auditing, and file uploads.

- `test_tool_flow.py` - End-to-end tool execution (echo tool)
- `test_tool_events.py` - Tool execution events
- `test_tool_executor.py` - Tool executor with auditing
- `test_tool_catalog.py` - Tool catalog integration
- `test_document_ingest.py` - Document ingestion tool
- `test_chunked_upload_flow.py` - File upload handling
- `test_gateway_tool_request_audit.py` - Tool request auditing
- `test_uploads_write_through.py` - Upload write-through

#### `agent/llm/` - LLM Integration
Tests real LLM invocation, streaming, and auditing.

- `test_llm_integration.py` - Real LLM invoke and streaming
- `test_llm_audit.py` - LLM request auditing

### `integration/` - Integration Tests

Tests for Gateway endpoints, authentication, policy enforcement, and external integrations.

- `test_api_contract_smoke.py` - Gateway API contract smoke tests
- `test_gateway_api_keys.py` - API key authentication
- `test_gateway_public_api.py` - Public Gateway endpoints
- `test_session_repository.py` - Session persistence
- `test_somabrain_client.py` - SomaBrain integration (memory backend)
- `test_opa_middleware.py` - OPA policy enforcement
- `gateway/test_gateway_endpoints.py` - Gateway endpoint tests
- `gateway/test_internal_attachments.py` - Internal attachment handling

### `ui/` - UI Tests

Tests for web UI functionality using Playwright.

- `test_ui_chat.py` - UI chat functionality
- `test_ui_smoke.py` - UI loads correctly
- `playwright/test_full_flow.py` - Full UI interaction flow
- `playwright/test_ui_flows.py` - UI interaction flows

### `chaos/` - Chaos/Reliability Tests

Tests for system reliability under failure conditions.

- `test_memory_recovery.py` - Memory recovery under chaos conditions

### `unit/` - Remaining Unit Tests

Focused unit tests for specific components that require isolation.

## Running Tests

### Run All Agent Tests
```bash
pytest tests/agent/ -v
```

### Run Specific Category
```bash
pytest tests/agent/memory/ -v          # Memory tests
pytest tests/agent/tools/ -v           # Tool tests
pytest tests/agent/llm/ -v             # LLM tests
pytest tests/agent/context/ -v         # Context tests
pytest tests/agent/conversation/ -v    # Conversation tests
```

### Run Integration Tests
```bash
pytest tests/integration/ -v
```

### Run UI Tests
```bash
pytest tests/ui/ -v
```

### Run E2E Tests (requires live stack)
```bash
make dev-up                            # Start stack
pytest tests/agent/ -m e2e -v          # Run E2E tests
```

### Run Live Agent Tests (requires API keys)
```bash
export SA01_AUTH_INTERNAL_TOKEN="<your-token>"
pytest tests/agent/context/ -v        # Live context tests
pytest tests/agent/llm/ -v            # Live LLM tests
```

## Test Markers

- `@pytest.mark.e2e` - End-to-end tests requiring live stack
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.asyncio` - Async tests
- `@pytest.mark.usefixtures("event_loop")` - Tests requiring event loop

## Environment Variables

### Required for Live Tests
- `SA01_GATEWAY_BASE_URL` - Gateway URL (default: http://localhost:21016)
- `SA01_AUTH_INTERNAL_TOKEN` - Internal token for Gateway API
- `SA01_DB_DSN` - Postgres connection string
- `SA01_KAFKA_BOOTSTRAP_SERVERS` - Kafka bootstrap servers

### Optional
- `E2E_HTTP_TIMEOUT` - HTTP timeout for E2E tests (default: 20s)
- `E2E_POLL_TIMEOUT` - Polling timeout (default: 20s)
- `E2E_EXPECT_MEMORY` - Expect memory verification (default: 0)
- `SA01_SOMA_TENANT_ID` - Tenant ID (default: public)

## Test Philosophy

### ✅ We DO
- Test real agent functionality
- Use real servers, real data, real LLMs
- Test memory persistence and recall
- Test tool execution end-to-end
- Test conversation integrity
- Test failure recovery

### ❌ We DO NOT
- Mock agent behavior
- Bypass real integrations
- Invent fake test data
- Test infrastructure plumbing (unless critical to agent)
- Test UI styling or cosmetics
- Test documentation formatting

## Test Count

- **Total**: ~65 test files
- **Agent Core**: ~30 files
- **Integration**: ~10 files
- **UI**: ~4 files
- **Chaos**: 1 file
- **Unit**: ~20 files

## Maintenance

When adding new tests:
1. Place in appropriate `agent/` subdirectory based on functionality
2. Use real data and real integrations
3. Add clear docstrings explaining what agent behavior is tested
4. Use environment variables for configuration
5. Mark appropriately (`@pytest.mark.e2e`, etc.)

When removing tests:
1. Only remove if redundant or testing infrastructure (not agent functionality)
2. Document reason in commit message
3. Update this README

## CI/CD

Tests run in CI with:
- Live Postgres, Kafka, Redis via Docker Compose
- Real Gateway and workers
- Real SomaBrain integration
- Timeout limits to prevent hanging

See `.github/workflows/` for CI configuration.
