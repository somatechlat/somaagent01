# Implementation Plan: Architecture Refactor

**CRITICAL PRINCIPLE**: This refactor PRESERVES and BUILDS UPON existing production infrastructure. We do NOT duplicate existing implementations - we create domain ports (interfaces) that wrap them.

## Current File Sizes (Verified)

| File | Lines | Target | Status |
|------|-------|--------|--------|
| `agent.py` | 4092 | < 200 | Pending |
| `services/conversation_worker/main.py` | 3022 | < 150 | Pending |
| `python/helpers/settings.py` | 1793 | < 200 | Pending |
| `python/helpers/task_scheduler.py` | 1276 | < 300 | Pending |
| `python/helpers/mcp_handler.py` | 1087 | < 300 | Pending |
| `python/helpers/memory.py` | 1010 | < 300 | Pending |
| `python/tasks/core_tasks.py` | 764 | < 300 | Pending |
| `services/common/session_repository.py` | 681 | < 300 | Pending |
| `services/gateway/main.py` | 438 | < 100 | Pending |

## Existing Production Infrastructure (DO NOT DUPLICATE)

| Component | Location | Action |
|-----------|----------|--------|
| `PostgresSessionStore`, `RedisSessionCache` | `services/common/session_repository.py` | ✅ Wrapped with port |
| `KafkaEventBus` | `services/common/event_bus.py` | ✅ Wrapped with port |
| `PolicyClient` | `services/common/policy_client.py` | ✅ Wrapped with port |
| `SomaBrainClient` | `python/integrations/somabrain_client.py` | ✅ Wrapped with port |
| `ToolRegistry`, `ExecutionEngine` | `services/tool_executor/` | Pending port interface |
| `SecretManager` | `services/common/secret_manager.py` | Pending port interface |
| `MemoryReplicaStore` | `src/core/infrastructure/repositories/` | ✅ Moved to infrastructure, port created |
| `cfg` configuration | `src/core/config/` | Keep as-is (canonical) |

---

## Phase 1: Domain Ports (Interfaces Only) ✅ COMPLETE

- [x] 1. Create domain port interfaces
  - [x] 1.1 Create session repository port
    - Created `src/core/domain/ports/__init__.py`
    - Created `src/core/domain/ports/repositories/__init__.py`
    - Created `src/core/domain/ports/repositories/session_repository.py` with `SessionRepositoryPort` ABC
    - Interface matches existing `PostgresSessionStore` methods exactly
    - _Requirements: 1.4, 11.1, 11.4_

  - [x] 1.2 Create session cache port
    - Created `src/core/domain/ports/repositories/session_cache.py` with `SessionCachePort` ABC
    - Interface matches existing `RedisSessionCache` methods exactly
    - _Requirements: 9.2, 11.2_

  - [x] 1.3 Create memory adapter port
    - Created `src/core/domain/ports/adapters/__init__.py`
    - Created `src/core/domain/ports/adapters/memory_adapter.py` with `MemoryAdapterPort` ABC
    - Interface matches existing `somabrain_client` async functions
    - _Requirements: 1.3, 7.1, 7.2_

  - [x] 1.4 Create policy adapter port
    - Created `src/core/domain/ports/adapters/policy_adapter.py` with `PolicyAdapterPort` ABC
    - Interface matches existing `PolicyClient.evaluate` method
    - _Requirements: 3.2_

  - [x] 1.5 Create event bus port
    - Created `src/core/domain/ports/adapters/event_bus.py` with `EventBusPort` ABC
    - Interface matches existing `KafkaEventBus` methods exactly
    - _Requirements: 11.3_

  - [x] 1.6 Create tool registry port
    - Created `src/core/domain/ports/adapters/tool_registry.py` with `ToolRegistryPort` ABC
    - Interface matches existing `services/tool_executor/tool_registry.py`
    - _Requirements: 6.2_

  - [x] 1.7 Create execution engine port
    - Created `src/core/domain/ports/adapters/execution_engine.py` with `ExecutionEnginePort` ABC
    - Interface matches existing `services/tool_executor/execution_engine.py`
    - _Requirements: 3.5_

  - [x] 1.8 Create secret manager port
    - Created `src/core/domain/ports/adapters/secret_manager.py` with `SecretManagerPort` ABC
    - Interface matches existing `services/common/secret_manager.py`
    - _Requirements: 4.4_

---

## Phase 2: Infrastructure Adapters (Wrapping Existing Code) ✅ COMPLETE

- [x] 2. Create infrastructure adapters that wrap existing implementations
  - [x] 2.1 Create session repository adapter
    - Created `src/core/infrastructure/adapters/__init__.py`
    - Created `src/core/infrastructure/adapters/session_repository_adapter.py`
    - `PostgresSessionRepositoryAdapter` delegates ALL operations to existing `PostgresSessionStore`
    - _Requirements: 1.4, 9.1, 11.1_

  - [x] 2.2 Create session cache adapter
    - Created `src/core/infrastructure/adapters/session_cache_adapter.py`
    - `RedisSessionCacheAdapter` delegates ALL operations to existing `RedisSessionCache`
    - _Requirements: 9.2, 11.2_

  - [x] 2.3 Create SomaBrain memory adapter
    - Created `src/core/infrastructure/adapters/memory_adapter.py`
    - `SomaBrainMemoryAdapter` delegates to existing `python.integrations.somabrain_client` functions
    - _Requirements: 1.3, 1.6_

  - [x] 2.4 Create policy adapter
    - Created `src/core/infrastructure/adapters/policy_adapter.py`
    - `OPAPolicyAdapter` delegates to existing `services.common.policy_client.PolicyClient`
    - _Requirements: 3.2_

  - [x] 2.5 Create event bus adapter
    - Created `src/core/infrastructure/adapters/event_bus_adapter.py`
    - `KafkaEventBusAdapter` delegates to existing `services.common.event_bus.KafkaEventBus`
    - _Requirements: 11.3_

  - [x] 2.6 Create tool registry adapter
    - Created `src/core/infrastructure/adapters/tool_registry_adapter.py`
    - `ToolRegistryAdapter` wraps existing `services/tool_executor/tool_registry.py`
    - _Requirements: 6.2_

  - [x] 2.7 Create execution engine adapter
    - Created `src/core/infrastructure/adapters/execution_engine_adapter.py`
    - `ExecutionEngineAdapter` wraps existing `services/tool_executor/execution_engine.py`
    - _Requirements: 3.5_

  - [x] 2.8 Create secret manager adapter
    - Created `src/core/infrastructure/adapters/secret_manager_adapter.py`
    - `SecretManagerAdapter` wraps existing `services/common/secret_manager.py`
    - _Requirements: 4.4_

---

## Phase 3: Property Tests for Architecture Compliance

- [ ] 3. Write property tests to enforce architectural rules
  - [x] 3.1 Create property test for domain isolation
    - Create `tests/properties/test_domain_isolation.py`
    - **Property 7: No Direct Infrastructure Imports in Domain**
    - Verify `src/core/domain/` has no imports from `src/core/infrastructure/`
    - _Requirements: 11.4, 12.4_

  - [x] 3.2 Create property test for repository pattern
    - Create `tests/properties/test_repository_pattern.py`
    - **Property 2: Repository Pattern Consistency**
    - Verify application layer uses ports, not direct DB imports
    - _Requirements: 11.1, 11.2, 11.3, 11.4_

  - [x] 3.3 Create property test for config single source
    - Create `tests/properties/test_config_source.py`
    - **Property 4: Configuration Single Source**
    - Verify all config imports from `src.core.config` only
    - _Requirements: 4.1, 4.2_

  - [x] 3.4 Create property test for file sizes
    - Create `tests/properties/test_file_sizes.py`
    - **Property 1: File Size Limits**
    - Verify no file exceeds 500 lines, main.py files < 150 lines
    - _Requirements: 14.1, 14.2_

- [x] 4. Checkpoint: Run all property tests
  - Ensure all tests pass before proceeding to decomposition

---

## Phase 4: Decompose Settings Module (1793 lines → < 200 lines)

- [ ] 5. Extract settings components
  - [x] 5.1 Create settings/fields module
    - Extract `SettingsField`, `SettingsSection`, `SettingsOutput` classes
    - Create `python/helpers/settings_fields.py` (< 150 lines)
    - _Requirements: 4.6_

  - [x] 5.2 Create settings/converters module
    - Extract `convert_out`, `convert_in` functions
    - Create `python/helpers/settings_converters.py` (< 200 lines)
    - _Requirements: 4.2_

  - [x] 5.3 Create settings/defaults module
    - Extract `get_default_settings` and default value logic
    - Create `python/helpers/settings_defaults.py` (< 150 lines)
    - _Requirements: 4.2_

  - [x] 5.4 Refactor settings.py to thin facade
    - Reduce `python/helpers/settings.py` to < 200 lines
    - Keep only: imports, main API functions
    - Delegate to extracted modules
    - _Requirements: 4.6_

- [x] 6. Checkpoint: Verify settings module works
  - Run existing settings tests
  - Verify line count < 200

---

## Phase 5: Decompose ToolExecutor (805 lines → < 150 lines main.py)

- [ ] 7. Extract tool executor components
  - [x] 7.1 Create validation module
    - Extract request validation logic from `services/tool_executor/main.py`
    - Create `services/tool_executor/validation.py` (< 100 lines)
    - _Requirements: 3.1_

  - [x] 7.2 Create telemetry module
    - Extract telemetry/metrics logic
    - Create `services/tool_executor/telemetry.py` (< 100 lines)
    - _Requirements: 3.3_

  - [-] 7.3 Create audit module
    - Extract audit logging logic
    - Create `services/tool_executor/audit.py` (< 100 lines)
    - _Requirements: 3.4_

  - [ ] 7.4 Refactor main.py to thin orchestrator
    - Reduce `services/tool_executor/main.py` to < 150 lines
    - Keep only: service bootstrap, event consumption, delegation
    - _Requirements: 3.6_

- [ ] 8. Checkpoint: Verify tool executor works
  - Run existing tool executor tests
  - Verify main.py line count < 150

---

## Phase 6: Decompose Task Scheduler (1276 lines → < 300 lines)

- [ ] 9. Extract task scheduler components
  - [ ] 9.1 Create scheduler/handlers module
    - Extract task handler implementations
    - Create `python/helpers/scheduler_handlers.py` (< 200 lines)
    - _Requirements: 5.2_

  - [ ] 9.2 Create scheduler/repository module
    - Extract task state management
    - Create `python/helpers/scheduler_repository.py` (< 150 lines)
    - _Requirements: 5.4_

  - [ ] 9.3 Create scheduler/events module
    - Extract event emission logic
    - Create `python/helpers/scheduler_events.py` (< 100 lines)
    - _Requirements: 5.3_

  - [ ] 9.4 Refactor task_scheduler.py
    - Reduce to < 300 lines
    - Keep only: main scheduler interface, delegation
    - _Requirements: 5.5_

- [ ] 10. Checkpoint: Verify task scheduler works
  - Run `tests/test_task_scheduler.py`
  - Verify line count < 300

---

## Phase 7: Decompose MCP Handler (1087 lines → < 300 lines)

- [ ] 11. Extract MCP handler components
  - [ ] 11.1 Create mcp/protocol module
    - Extract protocol parsing logic
    - Create `python/helpers/mcp_protocol.py` (< 200 lines)
    - _Requirements: 6.1_

  - [ ] 11.2 Create mcp/registry module
    - Extract tool registration logic
    - Create `python/helpers/mcp_registry.py` (< 150 lines)
    - _Requirements: 6.2_

  - [ ] 11.3 Create mcp/connection module
    - Extract connection management
    - Create `python/helpers/mcp_connection.py` (< 150 lines)
    - _Requirements: 6.4_

  - [ ] 11.4 Refactor mcp_handler.py
    - Reduce to < 300 lines
    - _Requirements: 6.5_

- [ ] 12. Checkpoint: Verify MCP handler works
  - Run existing MCP tests
  - Verify line count < 300

---

## Phase 8: Decompose Memory Module (1010 lines → < 300 lines)

- [ ] 13. Extract memory components
  - [ ] 13.1 Create memory/stores module
    - Extract `ShortTermMemoryStore`, `LongTermMemoryStore`
    - Create `python/helpers/memory_stores.py` (< 200 lines)
    - _Requirements: 7.1, 7.2_

  - [ ] 13.2 Create memory/consolidation module
    - Extract consolidation logic
    - Create `python/helpers/memory_consolidation.py` (< 150 lines)
    - _Requirements: 7.3_

  - [ ] 13.3 Create memory/search module
    - Extract search logic
    - Create `python/helpers/memory_search.py` (< 150 lines)
    - _Requirements: 7.4_

  - [ ] 13.4 Refactor memory.py
    - Reduce to < 300 lines
    - _Requirements: 7.5_

- [ ] 14. Checkpoint: Verify memory module works
  - Run existing memory tests
  - Verify line count < 300

---

## Phase 9: Decompose Gateway (438 lines → < 100 lines main.py)

- [ ] 15. Extract gateway components
  - [ ] 15.1 Verify router modules exist
    - Check `services/gateway/routers/` structure
    - Ensure routes are properly separated
    - _Requirements: 8.1_

  - [ ] 15.2 Create/verify middleware modules
    - Verify `AuthMiddleware` exists or create
    - Verify `RateLimitMiddleware` exists or create
    - _Requirements: 8.2, 8.3_

  - [ ] 15.3 Refactor main.py to thin initializer
    - Reduce `services/gateway/main.py` to < 100 lines
    - Keep only: FastAPI app init, middleware registration, router mounting
    - _Requirements: 8.5_

- [ ] 16. Checkpoint: Verify gateway works
  - Run gateway integration tests
  - Verify main.py line count < 100

---

## Phase 10: Decompose Core Tasks (764 lines → domain-specific modules)

- [ ] 17. Split core tasks by domain
  - [ ] 17.1 Create conversation_tasks module
    - Extract conversation-related Celery tasks
    - Create `python/tasks/conversation_tasks.py` (< 200 lines)
    - _Requirements: 10.1_

  - [ ] 17.2 Create memory_tasks module
    - Extract memory-related Celery tasks
    - Create `python/tasks/memory_tasks.py` (< 200 lines)
    - _Requirements: 10.2_

  - [ ] 17.3 Create maintenance_tasks module
    - Extract maintenance/cleanup tasks
    - Create `python/tasks/maintenance_tasks.py` (< 200 lines)
    - _Requirements: 10.3_

  - [ ] 17.4 Refactor core_tasks.py
    - Reduce to imports and task registration only (< 100 lines)
    - _Requirements: 10.4_

- [ ] 18. Checkpoint: Verify Celery tasks work
  - Run `tests/test_core_tasks_validation.py`
  - Verify all task modules < 200 lines

---

## Phase 11: Decompose Agent Module (4092 lines → < 200 lines)

- [ ] 19. Extract agent components (LARGEST DECOMPOSITION)
  - [ ] 19.1 Create agent/input_processor module
    - Extract input processing logic
    - Create `python/somaagent/input_processor.py` (< 200 lines)
    - _Requirements: 2.1_

  - [ ] 19.2 Create agent/tool_selector module
    - Extract tool selection strategy
    - Create `python/somaagent/tool_selector.py` (< 200 lines)
    - _Requirements: 2.2_

  - [ ] 19.3 Create agent/response_generator module
    - Extract response generation logic
    - Create `python/somaagent/response_generator.py` (< 200 lines)
    - _Requirements: 2.3_

  - [ ] 19.4 Create agent/conversation_orchestrator module
    - Extract conversation flow management
    - Create `python/somaagent/conversation_orchestrator.py` (< 300 lines)
    - _Requirements: 2.4_

  - [ ] 19.5 Create agent/error_handler module
    - Extract error handling with retry policies
    - Create `python/somaagent/error_handler.py` (< 150 lines)
    - _Requirements: 2.5_

  - [ ] 19.6 Refactor agent.py to thin orchestrator
    - Reduce `agent.py` to < 200 lines
    - Keep only: orchestration logic, delegation
    - _Requirements: 2.6_

- [ ] 20. Checkpoint: Verify agent works
  - Run agent tests
  - Verify agent.py line count < 200

---

## Phase 12: Decompose Conversation Worker (3022 lines → < 150 lines main.py)

- [ ] 21. Extract conversation worker components
  - [ ] 21.1 Create message_processor use case
    - Create `src/core/application/use_cases/conversation/process_message.py`
    - Handle message routing only
    - _Requirements: 1.1_

  - [ ] 21.2 Create context_builder service
    - Create `src/core/application/services/context_builder.py`
    - Dedicated LLM context building
    - _Requirements: 1.2_

  - [ ] 21.3 Create tool_orchestrator service
    - Create `src/core/application/services/tool_orchestrator.py`
    - Handle tool execution coordination
    - _Requirements: 1.5_

  - [ ] 21.4 Create health_monitor component
    - Create `services/conversation_worker/health_monitor.py`
    - Dedicated health monitoring
    - _Requirements: 1.6_

  - [ ] 21.5 Refactor main.py to thin consumer
    - Reduce `services/conversation_worker/main.py` to < 150 lines
    - Keep only: service init, Kafka consumer setup, delegation
    - _Requirements: 1.7_

- [ ] 22. Checkpoint: Verify conversation worker works
  - Run conversation worker tests
  - Verify main.py line count < 150

---

## Phase 13: File Size Enforcement

- [ ] 23. Add automated enforcement
  - [ ] 23.1 Create pre-commit hook for file size
    - Update `.pre-commit-config.yaml` with file size check
    - Create `scripts/check_file_sizes.py` enforcement script
    - _Requirements: 14.3_

  - [ ] 23.2 Document decomposition patterns
    - Update `CONTRIBUTING.md` with file size guidelines
    - Add decomposition examples and patterns
    - _Requirements: 14.4_

- [ ] 24. Final Checkpoint
  - Run ALL tests
  - Verify ALL property tests pass
  - Verify ALL file size limits met
  - Document any remaining technical debt

---

## Summary of Requirements Coverage

| Requirement | Description | Phase | Status |
|-------------|-------------|-------|--------|
| 1 | Decompose ConversationWorker | 12 | Pending |
| 2 | Decompose Agent Module | 11 | Pending |
| 3 | Decompose ToolExecutor | 5 | Pending |
| 4 | Decompose Settings/Config | 4 | Pending |
| 5 | Decompose Task Scheduler | 6 | Pending |
| 6 | Decompose MCP Handler | 7 | Pending |
| 7 | Decompose Memory Module | 8 | Pending |
| 8 | Decompose Gateway | 9 | Pending |
| 9 | Decompose Session Repository | 1-2 | ✅ Complete (ports/adapters) |
| 10 | Decompose Core Tasks | 10 | Pending |
| 11 | Apply Repository Pattern | 1-2 | ✅ Complete (ports/adapters) |
| 12 | Apply Use Case Pattern | 12 | Pending |
| 13 | Eliminate Re-export Modules | All | Ongoing |
| 14 | File Size Limits | 13 | Pending |
