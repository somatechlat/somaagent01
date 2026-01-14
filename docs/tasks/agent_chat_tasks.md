# 📋 Agent Chat Implementation Tasks

**Status Legend**: `[ ]` Pending | `[/]` In Progress | `[x]` Complete

---

## Phase 0: Circuit Breaker Consolidation (CRITICAL)

> ⚠️ **TRIPLICATE EFFORT DETECTED** - Must consolidate before proceeding

- [ ] **0.1 Audit Current Implementations**
  - [x] SomaAgent01: `services/common/circuit_breakers.py` → CircuitBreaker class
  - [x] SomaAgent01: `services/common/resilience.py` → CircuitBreakerError
  - [x] SomaAgent01: `services/common/degradation_monitor.py` → DegradationMonitor
  - [x] SomaAgent01: `admin/capabilities/api.py` → CircuitBreakerState
  - [x] SomaBrain: `infrastructure/circuit_breaker.py` → Centralized CircuitBreaker
  - [x] SomaBrain: `infrastructure/cb_registry.py` → Singleton registry

- [ ] **0.2 Define Single Source of Truth**
  - [ ] Decision: SomaBrain `CircuitBreaker` = canonical implementation
  - [ ] SomaAgent01 uses SomaBrain circuit state via SomaBrainClient
  - [ ] DegradationMonitor wraps SomaBrain state (no duplicate logic)

- [ ] **0.3 Consolidate SomaAgent01**
  - [ ] Remove duplicate `CircuitBreaker` class from `circuit_breakers.py`
  - [ ] Update `DegradationMonitor` to query SomaBrain for circuit state
  - [ ] Update all imports across codebase
  - [ ] Delete redundant files if empty after consolidation

---

## Phase 1: Constitution Foundation (SomaBrain)

- [ ] **1.1 Create Constitution Data Migration**
  - [ ] Define CONSTITUTION_V1 document (version, name, rules, articles)
  - [ ] Compute SHA3-512 checksum with JCS canonicalization
  - [ ] Create migration `0003_seed_constitution.py`
  - [ ] Embed public verification key in codebase

- [ ] **1.2 Constitution Verification**
  - [ ] Verify `ConstitutionEngine.load()` with migration-seeded data
  - [ ] Test fail-closed behavior when signature invalid

---

## Phase 2: Capsule System (SomaAgent01)

- [ ] **2.1 Default Test Capsule Migration**
  - [ ] Create migration for default Capsule
  - [ ] Include Soul: system_prompt, personality_traits, neuromodulator_baseline
  - [ ] Include Body: capabilities_whitelist, resource_limits
  - [ ] Bind to Constitution via constitution_ref

- [ ] **2.2 Capsule Injection in Chat Flow**
  - [ ] Modify `chat_service.py` to use `capsule.soul["system_prompt"]`
  - [ ] Remove hardcoded "You are SomaAgent01." string

---

## Phase 3: AgentIQ Governor Integration

- [ ] **3.1 Apply Capsule Resource Limits**
  - [ ] Use `capsule.body.resource_limits` in Governor
  - [ ] Filter tools by `capabilities_whitelist`

---

## Phase 4: Integration Tests

- [x] `tests/agent_chat/__init__.py` - Created
- [x] `tests/agent_chat/conftest.py` - Created
- [x] `tests/agent_chat/test_full_chat_flow.py` - Created
- [x] `tests/agent_chat/test_agentiq_governor.py` - Created
- [ ] `tests/agent_chat/test_constitution.py` - Pending
- [ ] `tests/agent_chat/test_capsule_injection.py` - Pending

---

## Phase 5: Security & Documentation

- [ ] Constitution tamper detection tests
- [ ] Capsule integrity verification tests
- [ ] Update `docs/architecture/` with Constitution flow
