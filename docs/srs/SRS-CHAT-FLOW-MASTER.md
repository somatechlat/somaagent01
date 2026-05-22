# SRS-CHAT-FLOW-MASTER — Complete Agent Architecture with Resilience

| Field | Value |
|-------|-------|
| **System** | SomaAgent01 |
| **Document ID** | SRS-CHAT-FLOW-MASTER-2026-05-21 |
| **Version** | 3.1 |
| **Date** | 2026-05-21 |
| **Status** | Approved |
| **Author** | SomaAgent01 Engineering |
| **Owner** | Platform Team |

---

## Table of Contents

1. [Introduction](#1-introduction)
   1.1 [Purpose](#11-purpose)
   1.2 [Scope](#12-scope)
   1.3 [Definitions](#13-definitions)
   1.4 [References](#14-references)
2. [Product Description](#2-product-description)
   2.1 [Product Perspective](#21-product-perspective)
   2.2 [Product Functions](#22-product-functions)
   2.3 [User Characteristics](#23-user-characteristics)
   2.4 [Constraints](#24-constraints)
   2.5 [Assumptions and Dependencies](#25-assumptions-and-dependencies)
3. [Specific Requirements](#3-specific-requirements)
   3.1 [Functional Requirements](#31-functional-requirements)
   3.2 [Non-Functional Requirements](#32-non-functional-requirements)
   3.3 [External Interface Requirements](#33-external-interface-requirements)
   3.4 [Design Constraints](#34-design-constraints)
4. [Traceability](#4-traceability)

---

## 1. Introduction

### 1.1 Purpose

This document specifies the complete agent chat flow architecture for SomaAgent01, including the 12-phase request processing pipeline, resilience patterns (circuit breakers, fallback chains), health monitoring, and budget enforcement integration.

### 1.2 Scope

**In scope:**
- Gateway authentication and rate limiting
- Capsule loading and governance checks
- Context building and memory recall
- LLM selection and invocation with fallback chains
- RLM execution
- Tool execution
- Memory memorization and learning
- Event observation and billing
- Circuit breaker and degradation patterns

**Out of scope:**
- UI/UX design (see WebUI SRS)
- Model training or fine-tuning
- Third-party LLM provider internals

### 1.3 Definitions

| Term | Definition |
|------|------------|
| AAAS | Agent-as-a-Service deployment mode |
| Capsule | The persistent agent configuration and state container |
| Circuit Breaker | Resilience pattern that prevents cascade failures |
| RLM | Recursive Language Model execution engine |
| SomaBrain | Cognitive memory and learning subsystem |
| SpiceDB | Authorization and permission database |
| OPA | Open Policy Agent for policy enforcement |

### 1.4 References

| ID | Document | Version | Location |
|----|----------|---------|----------|
| REF-001 | SRS-CONTEXT-BUILDING | 5.0 | `docs/srs/SRS-CONTEXT-BUILDING.md` |
| REF-002 | SRS-MODEL-ROUTING | 1.0 | `docs/srs/SRS-MODEL-ROUTING.md` |
| REF-003 | SRS-RLM-ENGINE | 5.0 | `docs/srs/SRS-RLM-ENGINE.md` |
| REF-004 | Circuit Breaker Implementation | — | `services/common/circuit_breaker.py` |
| REF-005 | Degradation Monitor | — | `services/common/degradation_monitor.py` |
| REF-006 | Health Monitor | — | `services/common/health_monitor.py` |
| REF-007 | Chat Orchestrator | — | `admin/core/chat_orchestrator.py` |

---

## 2. Product Description

### 2.1 Product Perspective

The Chat Flow Master is the central request-processing orchestrator within the SomaAgent01 monolith. It sits between the API Gateway and external services (LLM providers, vector databases, message queues), coordinating a 12-phase pipeline for each user request. Resilience patterns ensure graceful degradation when dependencies fail.

### 2.2 Product Functions

| ID | Function | Description |
|----|----------|-------------|
| FUNC-001 | Authenticate and Rate Limit | Validate JWT and enforce rate limits via Redis |
| FUNC-002 | Budget Gate | Enforce token and tool-call budgets before processing |
| FUNC-003 | Load Capsule | Retrieve agent configuration from PostgreSQL |
| FUNC-004 | Governance Check | Verify permissions via SpiceDB with fallback to capsule governance |
| FUNC-005 | Derive Settings | Compute runtime settings from capsule knobs |
| FUNC-006 | Build Context | Assemble prompt from persona, history, memory, and tools |
| FUNC-007 | Select Model | Choose optimal LLM based on capabilities and constraints |
| FUNC-008 | Invoke LLM | Generate response with fallback chain on failure |
| FUNC-009 | Execute RLM | Run recursive reasoning for complex tasks |
| FUNC-010 | Execute Tools | Invoke approved tools with individual circuit breakers |
| FUNC-011 | Memorize and Learn | Store conversation outcomes in SomaBrain |
| FUNC-012 | Observe and Bill | Emit async events to Kafka for audit and billing |

### 2.3 User Characteristics

| User Type | Role | Technical Level | Access |
|-----------|------|-----------------|--------|
| End User | Chat participant | Low | API/WebUI |
| Tenant Admin | Organization manager | Medium | Admin API |
| Platform Operator | Infrastructure engineer | High | Internal APIs, logs |

### 2.4 Constraints

| ID | Constraint | Description |
|----|------------|-------------|
| CON-001 | PostgreSQL Criticality | If PostgreSQL is unavailable, the system shall return HTTP 503 because capsules cannot be loaded |
| CON-002 | LLM Fallback Exhaustion | If all LLM providers in a fallback chain fail, the request shall fail |
| CON-003 | Budget Enforcement | Requests exceeding budget shall receive HTTP 402 before LLM invocation |

### 2.5 Assumptions and Dependencies

| ID | Assumption / Dependency | Impact if Invalid |
|----|------------------------|-------------------|
| AD-001 | Redis is available for rate limiting | Rate limits skipped gracefully |
| AD-002 | At least one LLM provider is healthy | Chat generation fails |
| AD-003 | Kafka is available for event streaming | Events queued locally, billing delayed |
| AD-004 | SpiceDB schema includes model permissions | Governance falls back to capsule |

---

## 3. Specific Requirements

### 3.1 Functional Requirements

#### 3.1.1 Authentication and Rate Limiting

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-001 | The system shall validate JWT tokens at the gateway before routing to the chat service. | Must | Test | Approved |
| REQ-002 | The system shall enforce per-user rate limits using Redis; if Redis is unavailable, the system shall skip rate limiting and continue processing. | Must | Test | Approved |

**Rationale:** Rate limiting protects backend resources; skipping it on Redis failure is an accepted degradation per the resilience matrix.

**Dependencies:** None

#### 3.1.2 Budget Enforcement

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-003 | The system shall check token budgets via `@budget_gate(metric="tokens")` before entering the LLM generation phase. | Must | Test | Approved |
| REQ-004 | The system shall check tool-call budgets via `@budget_gate(metric="tool_calls")` before executing tools. | Must | Test | Approved |
| REQ-005 | If a budget is exhausted, the system shall return HTTP 402 Payment Required and terminate the turn. | Must | Test | Approved |

**Rationale:** Budget gates prevent runaway costs.

**Dependencies:** REQ-001

#### 3.1.3 Capsule Loading

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-006 | The system shall load the agent capsule from PostgreSQL using the provided capsule identifier. | Must | Test | Approved |
| REQ-007 | If PostgreSQL is unavailable, the system shall return HTTP 503 Service Unavailable and fail fast. | Must | Test | Approved |

**Rationale:** The capsule contains persona, governance, and memory configuration; without it, no agent can operate.

**Dependencies:** REQ-001

#### 3.1.4 Governance and Permissions

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-008 | The system shall query SpiceDB for user permissions on the requested model. | Must | Test | Approved |
| REQ-009 | If SpiceDB is unavailable, the system shall fall back to `capsule.governance` for permission decisions. | Must | Test | Approved |

**Rationale:** Governance must not block on SpiceDB downtime.

**Dependencies:** REQ-006

#### 3.1.5 Settings Derivation

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-010 | The system shall derive all runtime settings (max tokens, temperature, lane allocation) from `capsule.body.persona.knobs` using pure Python logic with no external dependencies. | Must | Inspection | Approved |

**Rationale:** Derivation is computationally trivial and must be deterministic.

**Dependencies:** REQ-006

#### 3.1.6 Context Building

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-011 | The system shall assemble the prompt context from five lanes: system, history, memory, tools, and buffer. | Must | Test | Approved |
| REQ-012 | The system shall allocate token budget per lane according to `capsule.body.learned.lane_preferences` or intelligence-based defaults. | Must | Test | Approved |

**Rationale:** See SRS-CONTEXT-BUILDING for lane details.

**Dependencies:** REQ-010

#### 3.1.7 Memory Recall

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-013 | The system shall recall memories via SomaBrain using a circuit breaker. | Must | Test | Approved |
| REQ-014 | If SomaBrain or Milvus is unavailable, the system shall return empty memories and continue processing. | Must | Test | Approved |

**Rationale:** Memory is non-critical; degraded operation without memory is acceptable.

**Dependencies:** REQ-011

#### 3.1.8 LLM Invocation and Fallback

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-015 | The system shall invoke the selected LLM through a circuit breaker. | Must | Test | Approved |
| REQ-016 | The system shall implement fallback chains per use case: chat (`openai/gpt-4o` → `anthropic/claude-3-5-sonnet` → `openrouter/qwen-2.5-72b`), coding (`anthropic/claude-3-5-sonnet` → `openai/gpt-4o` → `openrouter/deepseek-coder`), and fast (`openai/gpt-4o-mini` → `anthropic/claude-3-haiku` → `openrouter/llama-3.1-8b`). | Must | Test | Approved |
| REQ-017 | If the primary model fails, the system shall attempt each fallback in order. | Must | Test | Approved |
| REQ-018 | If all models in a fallback chain fail, the system shall fail the turn. | Must | Test | Approved |

**Rationale:** Fallback chains ensure high availability across multiple providers.

**Dependencies:** REQ-015

#### 3.1.9 RLM Execution

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-019 | The system shall execute the RLM engine in Phase 8 for complex tasks, using the same LLM fallback chain. | Should | Test | Approved |

**Rationale:** See SRS-RLM-ENGINE for RLM details.

**Dependencies:** REQ-017

#### 3.1.10 Tool Execution

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-020 | The system shall invoke each external tool through its own circuit breaker. | Must | Test | Approved |

**Rationale:** Tool failures must not cascade to the main request.

**Dependencies:** REQ-003

#### 3.1.11 Memorization and Learning

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-021 | The system shall persist conversation memories via SomaBrain using a circuit breaker. | Should | Test | Approved |
| REQ-022 | If SomaBrain is unavailable during memorization, the system shall skip the operation and continue. | Should | Test | Approved |

**Rationale:** Learning is non-critical; data loss on transient failure is acceptable.

**Dependencies:** REQ-013

#### 3.1.12 Event Observation

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-023 | The system shall emit observation events to Kafka asynchronously using fire-and-forget semantics. | Must | Inspection | Approved |
| REQ-024 | If Kafka is unavailable, the system shall queue events locally and retry. | Should | Test | Approved |

**Rationale:** Observation must not block the response path.

**Dependencies:** None

### 3.2 Non-Functional Requirements

#### 3.2.1 Performance

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-PERF-001 | The system shall complete pre-LLM phases (auth through context building) in less than 21 ms under normal conditions. | <21 ms | Test |
| NFR-PERF-002 | The system shall complete pre-LLM phases in less than 16 ms under degraded conditions. | <16 ms | Test |
| NFR-PERF-003 | The system shall invoke LLM within 500–3000 ms depending on model and payload. | 500–3000 ms | Test |

#### 3.2.2 Security

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-SEC-001 | The system shall enforce JWT authentication on every request. | 100% | Test |
| NFR-SEC-002 | The system shall enforce OPA policies before tool execution. | 100% | Test |
| NFR-SEC-003 | The system shall cache OPA decisions with a fallback to DENY all on cache miss if OPA is unavailable. | — | Test |

#### 3.2.3 Reliability

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-REL-001 | Critical services (PostgreSQL, LLM) shall trigger HTTP 503 on failure. | — | Test |
| NFR-REL-002 | Non-critical services (Redis, SpiceDB, Milvus, Kafka) shall degrade gracefully without failing the request. | — | Test |
| NFR-REL-003 | Circuit breakers shall transition between CLOSED, OPEN, and HALF_OPEN states based on failure thresholds and timeouts. | — | Test |

#### 3.2.4 Scalability

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-SCL-001 | The chat flow shall support both AAAS (direct import) and STANDALONE (HTTP) deployment modes. | — | Test |

#### 3.2.5 Maintainability

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-MNT-001 | Each external dependency shall have an isolated circuit breaker configuration. | — | Inspection |

---

### 3.3 External Interface Requirements

#### 3.3.1 User Interfaces

Not applicable. This is a backend service.

#### 3.3.2 Software Interfaces

| Interface | Protocol | Format | Authentication |
|-----------|----------|--------|----------------|
| LLM Providers | HTTP / REST | JSON | API Key (via LiteLLM) |
| SpiceDB | gRPC | Protobuf | mTLS |
| PostgreSQL | TCP | SQL | Password / IAM |
| Redis | TCP | RESP | Password |
| Kafka | TCP | Binary | SASL / SSL |
| Milvus | gRPC | Protobuf | Token |

#### 3.3.3 Hardware Interfaces

Not applicable.

---

### 3.4 Design Constraints

| ID | Constraint | Source |
|----|------------|--------|
| DC-001 | In AAAS mode, all internal service calls shall use direct Python imports (zero HTTP latency). | Architecture decision |
| DC-002 | In STANDALONE mode, internal service calls shall use HTTP with circuit breakers. | Architecture decision |
| DC-003 | Circuit breakers must be configurable per service with `failure_threshold` and `reset_timeout`. | Resilience specification |

---

## 4. Traceability

### 4.1 Requirements Traceability Matrix

| REQ ID | Description | Source | Design | Implementation | Test |
|--------|-------------|--------|--------|----------------|------|
| REQ-001 | JWT validation at gateway | Security spec | Gateway design | `admin/core/chat_orchestrator.py` | `tests/agent_chat/test_full_chat_flow.py` |
| REQ-002 | Redis rate limit with skip fallback | Resilience spec | Circuit breaker pattern | `services/common/circuit_breaker.py` | `tests/agent_chat/test_full_chat_flow.py` |
| REQ-003 | Token budget gate | Budget SRS | Budget decorator | `services/common/budget_manager.py` | `tests/agent_chat/test_full_chat_flow.py` |
| REQ-004 | Tool-call budget gate | Budget SRS | Budget decorator | `services/common/budget_manager.py` | `tests/agent_chat/test_full_chat_flow.py` |
| REQ-005 | HTTP 402 on budget exhaustion | Budget SRS | Error handler | `admin/core/chat_orchestrator.py` | `tests/saas/test_chat_flow_e2e.py` |
| REQ-006 | Capsule load from PostgreSQL | Data model | ORM query | `admin/core/chat_orchestrator.py` | `tests/agent_chat/test_full_chat_flow.py` |
| REQ-007 | HTTP 503 on PostgreSQL failure | Resilience spec | Fail-fast path | `admin/core/chat_orchestrator.py` | `tests/saas/test_chat_flow_e2e.py` |
| REQ-008 | SpiceDB permission query | Auth spec | gRPC client | `services/common/spicedb_client.py` | `tests/agent_chat/test_full_chat_flow.py` |
| REQ-009 | Capsule governance fallback | Resilience spec | Fallback logic | `admin/core/chat_orchestrator.py` | `tests/saas/test_chat_flow_e2e.py` |
| REQ-010 | Pure Python settings derivation | Knobs spec | Derivation functions | `admin/core/chat_orchestrator.py` | `tests/agent_chat/test_full_chat_flow.py` |
| REQ-011 | Five-lane context assembly | Context SRS | Context builder | `admin/core/context/builder.py` | `tests/agent_chat/test_full_chat_flow.py` |
| REQ-012 | Lane allocation from learned or defaults | Context SRS | Lane allocator | `admin/core/context/lanes.py` | `tests/agent_chat/test_full_chat_flow.py` |
| REQ-013 | SomaBrain recall with circuit breaker | Memory SRS | Brain bridge | `services/common/brain_bridge.py` | `tests/agent_chat/test_full_chat_flow.py` |
| REQ-014 | Empty memory fallback | Resilience spec | Degradation service | `services/common/degradation_monitor.py` | `tests/saas/test_chat_flow_e2e.py` |
| REQ-015 | LLM invocation with circuit breaker | Resilience spec | Circuit breaker | `services/common/circuit_breaker.py` | `tests/agent_chat/test_full_chat_flow.py` |
| REQ-016 | Fallback chains per use case | Resilience spec | Degradation monitor | `services/common/degradation_monitor.py` | `tests/saas/test_chat_flow_e2e.py` |
| REQ-017 | Sequential fallback attempts | Resilience spec | Fallback chain | `services/common/degradation_monitor.py` | `tests/saas/test_chat_flow_e2e.py` |
| REQ-018 | Turn failure on chain exhaustion | Resilience spec | Error handler | `admin/core/chat_orchestrator.py` | `tests/saas/test_chat_flow_e2e.py` |
| REQ-019 | RLM execution in Phase 8 | RLM SRS | RLM engine | `tmp/rlm/rlm/core/rlm.py` | `tests/agent_chat/test_full_chat_flow.py` |
| REQ-020 | Per-tool circuit breakers | Tool SRS | Circuit breaker registry | `services/common/circuit_breaker.py` | `tests/agent_chat/test_full_chat_flow.py` |
| REQ-021 | SomaBrain memorize with circuit breaker | Memory SRS | Brain bridge | `services/common/brain_bridge.py` | `tests/agent_chat/test_full_chat_flow.py` |
| REQ-022 | Skip memorization on failure | Resilience spec | Degradation service | `services/common/degradation_monitor.py` | `tests/saas/test_chat_flow_e2e.py` |
| REQ-023 | Async Kafka event emission | Observability spec | Event bus | `services/common/event_bus.py` | `tests/agent_chat/test_full_chat_flow.py` |
| REQ-024 | Local queue on Kafka failure | Resilience spec | DLQ store | `services/common/dlq.py` | `tests/saas/test_chat_flow_e2e.py` |

### 4.2 Requirement to Test Case Mapping

| REQ ID | Test Case ID | Test Method | Expected Result |
|--------|--------------|-------------|-----------------|
| REQ-001 | TC-001 | Unit | Request without JWT rejected |
| REQ-002 | TC-002 | Integration | Request processed when Redis down |
| REQ-003 | TC-003 | Unit | Budget gate blocks over-budget request |
| REQ-005 | TC-004 | E2E | HTTP 402 returned for exhausted budget |
| REQ-007 | TC-005 | E2E | HTTP 503 returned when PostgreSQL down |
| REQ-014 | TC-006 | Integration | Chat continues without memories when Milvus down |
| REQ-017 | TC-007 | Integration | Fallback model used when primary fails |
| REQ-018 | TC-008 | E2E | Turn fails when all LLM providers down |
| REQ-024 | TC-009 | Integration | Events queued locally when Kafka down |

---

## 5. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-10 | Engineering | Initial version |
| 2.0 | 2026-01-14 | Engineering | Added resilience patterns |
| 3.0 | 2026-01-16 | Engineering | AAAS direct calls + budget integration |
| 3.1 | 2026-05-21 | Engineering | Refactored to ISO/IEC/IEEE 29148 template |

---

*Document conforms to ISO/IEC/IEEE 29148:2018 — Systems and Software Engineering — Life Cycle Processes — Requirements Engineering.*
