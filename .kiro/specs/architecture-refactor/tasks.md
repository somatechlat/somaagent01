# Implementation Plan: Architecture Refactor

**CRITICAL PRINCIPLE**: This refactor PRESERVES and BUILDS UPON existing production infrastructure. We do NOT duplicate existing implementations - we create domain ports (interfaces) that wrap them.

## Current File Sizes (Baseline)

| File | Lines | Target | Status |
|------|-------|--------|--------|
| `services/conversation_worker/main.py` | 3022 | < 150 | Pending |
| `agent.py` | 4092 | < 200 | Pending |
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
| `PostgresSessionStore`, `RedisSessionCache` | `services/common/session_repository.py` | ✅ Wrapped with port interface |
| `KafkaEventBus` | `services/common/event_bus.py` | ✅ Wrapped with port interface |
| `PolicyClient` | `services/common/policy_client.py` | ✅ Wrapped with port interface |
| `SomaBrainClient` | `python/integrations/somabrain_client.py` | ✅ Wrapped with port interface |
| `ToolRegistry`, `ExecutionEngine` | `services/tool_executor/` | Pending port interface |
| `SecretManager` | `services/common/secret_manager.py` | Pending port interface |
| `MemoryReplicaStore` | `src/core/domain/memory/replica_store.py` | Keep as-is |
| `cfg` configuration | `src/core/config/` | Keep as-is (already canonical) |

---

## Phase 1: Domain Ports (Interfaces Only)

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

---

## Phase 2: Infrastructure Adapters (Wrapping Existing Code)

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

  - [x]