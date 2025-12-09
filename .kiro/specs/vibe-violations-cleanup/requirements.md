# SomaAgent01 Architecture Requirements - VIBE Compliance

## Introduction

This document defines the requirements for ensuring the SomaAgent01 codebase fully complies with VIBE coding rules. The VIBE rules mandate: NO stubs, NO placeholders, NO mocks, NO fallbacks, NO shims, NO bypasses - only REAL production implementations.

## Glossary

- **VIBE**: Verification, Implementation, Behavior, Execution coding rules
- **SomaBrain**: External cognitive memory service providing neuromodulation, adaptation, and memory consolidation
- **Gateway**: FastAPI HTTP gateway serving UI and routing to Kafka
- **ConversationWorker**: Kafka consumer processing conversation messages
- **ToolExecutor**: Service executing agent tools in sandboxed environment
- **Stub**: Fake implementation that doesn't do real work - VIOLATION
- **Placeholder**: Code that exists only to satisfy imports - VIOLATION
- **Mock**: Fake object for testing that shouldn't be in production - VIOLATION
- **Shim**: Compatibility layer that should be removed - VIOLATION
- **Fallback**: Alternative path when primary fails (in-memory instead of real DB) - VIOLATION

---

## Part 1: VIBE Violations Cleanup (COMPLETE)

### Requirement 1: Delete Voice Stub Files

**User Story:** As a system maintainer, I want all voice stub files deleted, so that only real implementations exist.

#### Acceptance Criteria

1. WHEN the file `src/voice/openai_client.py` is checked THEN the System SHALL NOT exist
2. WHEN the file `src/voice/local_client.py` is checked THEN the System SHALL NOT exist
3. WHEN voice functionality is needed THEN the System SHALL either have REAL implementations or raise ProviderNotSupportedError

**Status:** ✅ COMPLETE

---

### Requirement 2: Delete OPA Placeholder

**User Story:** As a system maintainer, I want the OPA placeholder deleted, so that only the real OPA integration exists.

#### Acceptance Criteria

1. WHEN the file `integrations/opa.py` is checked THEN the System SHALL NOT exist
2. WHEN OPA functionality is needed THEN the System SHALL use `python/integrations/opa_middleware.py` exclusively

**Status:** ✅ COMPLETE

---

### Requirement 3: Delete Gateway Router Placeholders

**User Story:** As a system maintainer, I want all gateway router placeholders deleted.

#### Acceptance Criteria

1. WHEN `services/gateway/routers/tools.py` is checked THEN the System SHALL NOT exist
2. WHEN `services/gateway/routers/auth.py` is checked THEN the System SHALL NOT exist

**Status:** ✅ COMPLETE

---

### Requirement 4: Delete Degradation Monitor Shim

**User Story:** As a system maintainer, I want the degradation monitor shim deleted.

#### Acceptance Criteria

1. WHEN `services/common/degradation_monitor.py` is checked THEN the System SHALL NOT exist
2. WHEN code imports degradation_monitor THEN the System SHALL import from `services.gateway.degradation_monitor`

**Status:** ✅ COMPLETE

---

### Requirement 5: Remove RequeueStore In-Memory Fallback

**User Story:** As a system maintainer, I want the RequeueStore to require Redis, with no in-memory fallback.

#### Acceptance Criteria

1. WHEN RequeueStore is initialized with invalid Redis URL THEN the System SHALL raise ValueError
2. WHEN RequeueStore methods are called THEN the System SHALL use Redis directly

**Status:** ✅ COMPLETE

---

### Requirement 6: Fix Speech Router Fake Transcription

**User Story:** As a system maintainer, I want the speech router to return 501 Not Implemented instead of fake data.

#### Acceptance Criteria

1. WHEN speech transcription is called THEN the System SHALL return 501 Not Implemented
2. WHEN speech endpoint exists THEN the System SHALL NOT return fake transcription data

**Status:** ✅ COMPLETE

---

### Requirement 7: Fix Circuit Breaker NotImplementedError

**User Story:** As a system maintainer, I want the circuit breaker to have real PostgreSQL support.

#### Acceptance Criteria

1. WHEN circuit_breakers.py is checked THEN the System SHALL NOT raise NotImplementedError
2. WHEN PostgreSQL circuit breaker is used THEN the System SHALL have a real implementation

**Status:** ✅ COMPLETE

---

### Requirement 8: Fix DLQ Store Stub Methods

**User Story:** As a system maintainer, I want the DLQ store to have real implementations.

#### Acceptance Criteria

1. WHEN dlq_store.py is checked THEN the System SHALL NOT contain methods marked as "stub"
2. WHEN reprocess functionality is called THEN the System SHALL use real Kafka reprocessing

**Status:** ✅ COMPLETE

---

## Part 2: SomaBrain Integration Architecture

### Requirement 9: SomaBrain Client API Alignment

**User Story:** As a developer, I want the SomaBrain client to correctly call the real SomaBrain API endpoints.

#### Acceptance Criteria

1. WHEN `get_neuromodulators()` is called THEN the System SHALL call `GET /neuromodulators`
2. WHEN `update_neuromodulators()` is called THEN the System SHALL call `POST /neuromodulators`
3. WHEN `get_adaptation_state()` is called THEN the System SHALL call `GET /context/adaptation/state`
4. WHEN `sleep_cycle()` is called THEN the System SHALL call `POST /sleep/run`
5. WHEN legacy parameters (tenant_id, persona_id) are passed THEN the System SHALL accept them for compatibility but NOT send them to endpoints that don't support them

**Status:** ✅ COMPLETE - soma_client.py correctly implements all endpoints

---

### Requirement 10: Cognitive Processing Integration

**User Story:** As a developer, I want the cognitive processing module to correctly use SomaBrain for neuromodulation and adaptation.

#### Acceptance Criteria

1. WHEN `initialize_cognitive_state()` is called THEN the System SHALL load neuromodulators from SomaBrain
2. WHEN `load_adaptation_state()` is called THEN the System SHALL fetch adaptation weights from SomaBrain
3. WHEN `apply_neuromodulation()` is called THEN the System SHALL apply dopamine, serotonin, noradrenaline to cognitive parameters
4. WHEN cognitive load exceeds 0.8 THEN the System SHALL consider triggering a sleep cycle

**Status:** ✅ VERIFIED - cognitive.py correctly integrates with SomaBrain

---

## Part 3: Messaging Architecture

### Requirement 11: Kafka Event Flow

**User Story:** As a developer, I want the Kafka messaging to use real event publishing with no fallbacks.

#### Acceptance Criteria

1. WHEN events are published THEN the System SHALL use real Kafka producers
2. WHEN Kafka is unavailable THEN the System SHALL use the durable outbox pattern (real PostgreSQL storage)
3. WHEN the outbox is used THEN the System SHALL NOT use in-memory storage

**Status:** ✅ VERIFIED - publisher.py uses real Kafka with outbox fallback to PostgreSQL

---

### Requirement 12: Conversation Worker Processing

**User Story:** As a developer, I want the conversation worker to process messages with real implementations.

#### Acceptance Criteria

1. WHEN a conversation message is received THEN the System SHALL process it through the real message processor
2. WHEN tool execution is needed THEN the System SHALL delegate to the real tool executor service
3. WHEN LLM calls are made THEN the System SHALL use real LLM providers (no mocks)

**Status:** ✅ VERIFIED - conversation_worker uses real implementations

---

## Part 4: Tool Execution Architecture

### Requirement 13: Tool Executor Service

**User Story:** As a developer, I want the tool executor to run real tool implementations.

#### Acceptance Criteria

1. WHEN a tool is executed THEN the System SHALL run the real tool implementation
2. WHEN code execution is requested THEN the System SHALL use real Python/Node.js/bash runtimes
3. WHEN browser automation is requested THEN the System SHALL use real Playwright browser

**Status:** ✅ VERIFIED - tool_executor uses real implementations

---

## Part 5: Memory System Architecture

### Requirement 14: Dual Memory Storage

**User Story:** As a developer, I want the memory system to use real storage backends.

#### Acceptance Criteria

1. WHEN local memory is used THEN the System SHALL use real FAISS vector store
2. WHEN remote memory is used THEN the System SHALL call real SomaBrain endpoints
3. WHEN memory operations fail THEN the System SHALL raise errors (no silent fallbacks)

**Status:** ✅ VERIFIED - memory system uses real FAISS and SomaBrain

---

## Summary

| Category | Requirements | Status |
|----------|--------------|--------|
| VIBE Violations Cleanup | 8 | ✅ COMPLETE |
| SomaBrain Integration | 2 | ✅ COMPLETE |
| Messaging Architecture | 2 | ✅ VERIFIED |
| Tool Execution | 1 | ✅ VERIFIED |
| Memory System | 1 | ✅ VERIFIED |
| **TOTAL** | **14** | **✅ ALL COMPLETE** |

---

## Files Modified/Deleted

### Deleted Files
- `src/voice/openai_client.py`
- `src/voice/local_client.py`
- `integrations/opa.py`
- `services/gateway/routers/tools.py`
- `services/gateway/routers/auth.py`
- `services/common/degradation_monitor.py`
- `tests/voice/test_provider_selector.py`

### Fixed Files
- `src/voice/provider_selector.py`
- `services/gateway/routers/__init__.py`
- `services/gateway/routers/health_full.py`
- `services/gateway/routers/speech.py`
- `services/gateway/circuit_breakers.py`
- `services/common/dlq_store.py`
- `services/common/requeue_store.py`
- `python/integrations/soma_client.py`
- `.kiro/steering/somabrain-api.md`
