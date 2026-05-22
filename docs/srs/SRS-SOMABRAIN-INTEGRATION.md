# SRS-SOMABRAIN-INTEGRATION — L3 Cognitive Engine

| Field | Value |
|-------|-------|
| **System** | SomaAgent01 |
| **Document ID** | SRS-SOMABRAIN-INTEGRATION-2026-01-16 |
| **Version** | 5.1 |
| **Date** | 2026-01-16 |
| **Status** | Approved |
| **Author** | SomaAgent01 Engineering |
| **Owner** | Core Platform Team |

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
5. [Revision History](#5-revision-history)

---

## 1. Introduction

### 1.1 Purpose

This document specifies the requirements for integrating SomaBrain, the Layer 3 Cognitive Engine, into the SomaAgent01 platform. SomaBrain provides memory recall, memory storage, and adaptive learning capabilities for AI agent capsules.

### 1.2 Scope

**In Scope:**
- Integration of SomaBrain recall, memorize, and learn operations into the chat flow
- Capsule-based memory configuration (no hardcoded parameters)
- SomaFractalMemory fallback when SomaBrain is unavailable
- Deployment mode abstraction (AAAS direct import vs. standalone HTTP client)
- OpenTelemetry tracing for all cognitive operations

**Out of Scope:**
- Implementation details of SomaBrain internal embedding models
- PostgreSQL schema design for the persistence layer
- UI for memory visualization

### 1.3 Definitions

| Term | Definition |
|------|------------|
| SomaBrain | Layer 3 Cognitive Engine providing memory and learning services |
| SomaFractalMemory | Independent memory fallback service, operable without SomaBrain |
| Capsule | The portable agent configuration unit containing persona, memory, and learned preferences |
| AAAS Mode | Deployment mode using direct Python imports for zero-latency cognitive calls |
| Standalone Mode | Deployment mode using HTTP clients to external cognitive services |
| AgentIQ | Cost and capability derivation system for model selection |

### 1.4 References

| ID | Document | Version | Location |
|----|----------|---------|----------|
| REF-001 | SRS-CHAT-FLOW-MASTER.md | 3.0 | docs/srs/SRS-CHAT-FLOW-MASTER.md |
| REF-002 | SRS-CAPSULE-PORTABILITY.md | 3.0 | docs/srs/SRS-CAPSULE-PORTABILITY.md |
| REF-003 | SomaBrain Service API | 1.0 | services/common/brain_bridge.py |
| REF-004 | Django Models | Current | admin/core/models/core.py |

---

## 2. Product Description

### 2.1 Product Perspective

SomaBrain integrates into Phase 4 (Recall), Phase 9 (Memorize), and Phase 10 (Learn) of the 13-phase chat flow. It reads all memory configuration from `capsule.body.persona.memory` and persists learned preferences to `capsule.body.learned`. The system maintains a three-tier memory hierarchy:

1. PostgreSQL — persistence layer (always active)
2. SomaBrain — primary cognitive and memory engine
3. SomaFractalMemory — fallback memory engine (independent from Brain)

### 2.2 Product Functions

| ID | Function | Description |
|----|----------|-------------|
| FUNC-001 | Memory Recall | Retrieve relevant memories for a given query using capsule-defined recall settings |
| FUNC-002 | Memory Memorize | Store interaction content into memory using capsule-defined memorize settings |
| FUNC-003 | Adaptive Learning | Update capsule learned preferences (lane, tool, model, neuromodulator) based on feedback |
| FUNC-004 | Sub-LM Query | Answer RLM uncertainty queries via the ask() operation using recalled memories |
| FUNC-005 | Deployment Abstraction | Switch between AAAS direct import and standalone HTTP client modes |

### 2.3 User Characteristics

| User Type | Role | Technical Level | Access |
|-----------|------|-----------------|--------|
| System Agent | AI Agent Runtime | N/A | Internal API only |
| Platform Engineer | DevOps / SRE | High | Configuration of deployment modes |
| Capsule Designer | Agent Configurator | Medium | Memory settings via capsule JSON |

### 2.4 Constraints

| ID | Constraint | Description |
|----|------------|-------------|
| CON-001 | No Hardcoded Limits | Memory recall limits, thresholds, and history limits must originate from capsule configuration |
| CON-002 | Fallback Required | SomaFractalMemory must remain available when SomaBrain is unreachable |
| CON-003 | Tenant Isolation | All memory operations must respect capsule tenant boundaries |

### 2.5 Assumptions and Dependencies

| ID | Assumption / Dependency | Impact if Invalid |
|----|------------------------|-------------------|
| AD-001 | SomaBrain service is reachable on port 30101 in standalone mode | Falls back to SomaFractalMemory; degraded but functional |
| AD-002 | SomaFractalMemory service is reachable on port 10101 in standalone mode | Falls back to PostgreSQL-only persistence |
| AD-003 | Capsule.body contains valid persona.memory and learned schemas | Chat flow skips cognitive enhancement phases |
| AD-004 | PostgreSQL is available with Django ORM | Complete chat flow failure |

---

## 3. Specific Requirements

### 3.1 Functional Requirements

#### 3.1.1 Memory Operations

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-SBI-001 | The system shall provide a recall() operation that retrieves relevant memories for a given query. | Must | Test | Approved |
| REQ-SBI-002 | The recall() operation shall read recall_limit, history_limit, similarity_threshold, and recall_mode exclusively from capsule.body.persona.memory. | Must | Inspection | Approved |
| REQ-SBI-003 | The system shall provide a memorize() operation that stores content into the memory layer. | Must | Test | Approved |
| REQ-SBI-004 | The memorize() operation shall read memorize_mode and embedding_model exclusively from capsule.body.persona.memory. | Must | Inspection | Approved |
| REQ-SBI-005 | The system shall provide a learn() operation that updates capsule.body.learned based on interaction results and feedback. | Must | Test | Approved |

**Rationale:** Cognitive operations must be fully configurable per capsule to enable portable agent personalities.

**Dependencies:** REQ-SBI-001 depends on SRS-CAPSULE-PORTABILITY REQ-CP-003 (Capsule body schema).

---

#### 3.1.2 Learning Adaptation

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-SBI-006 | The learn() operation shall update lane_preferences when feedback indicates success, incrementing the used lane preference by 0.05 up to a maximum of 1.0. | Should | Test | Approved |
| REQ-SBI-007 | The learn() operation shall update tool_preferences, incrementing by 0.1 on success or decrementing by 0.1 on failure, bounded to [0.0, 1.0]. | Should | Test | Approved |
| REQ-SBI-008 | The learn() operation shall update neuromodulator_state.dopamine by 0.05 on successful feedback. | Should | Test | Approved |
| REQ-SBI-009 | The learn() operation shall persist all updated learned state via capsule.asave(update_fields=["body"]). | Must | Test | Approved |

**Rationale:** Persistent learning enables agents to adapt behavior over time without external reconfiguration.

**Dependencies:** REQ-SBI-006 depends on REQ-SBI-005.

---

#### 3.1.3 Sub-LM and RLM Integration

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-SBI-010 | The system shall provide an ask() operation that answers Sub-LM queries from the RLM when the RLM signals uncertainty. | Should | Test | Approved |
| REQ-SBI-011 | The ask() operation shall augment the query with recalled memories and the capsule personality traits before generating a response. | Should | Test | Approved |

**Rationale:** Sub-LM queries enable the RLM to delegate factual or memory-based questions to the cognitive engine.

---

#### 3.1.4 Deployment Mode Abstraction

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-SBI-012 | The system shall support AAAS mode, using direct Python imports from somabrain.cognitive.CognitiveCore with zero network latency. | Must | Test | Approved |
| REQ-SBI-013 | The system shall support standalone mode, using HTTP clients to SomaBrain (port 30101) and SomaFractalMemory (port 10101). | Must | Test | Approved |
| REQ-SBI-014 | The system shall select deployment mode based on the SA01_DEPLOYMENT_MODE environment setting. | Must | Inspection | Approved |

**Rationale:** Deployment mode abstraction enables the same codebase to run in integrated (AAAS) and distributed (standalone) topologies.

---

### 3.2 Non-Functional Requirements

#### 3.2.1 Performance

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-PERF-001 | AAAS mode recall latency shall not exceed 50ms for top-10 results. | 50 ms | Load Test |
| NFR-PERF-002 | Standalone mode recall latency shall not exceed 100ms for top-10 results. | 100 ms | Load Test |

#### 3.2.2 Reliability

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-REL-001 | SomaFractalMemory fallback shall activate within 500ms of SomaBrain timeout. | 500 ms | Chaos Test |
| NFR-REL-002 | Cognitive operation failure shall not cause chat flow failure; the system shall degrade gracefully. | 100% | Fault Injection |

#### 3.2.3 Observability

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-OBS-001 | All recall, memorize, and learn operations shall emit OpenTelemetry spans with capsule_id and success attributes. | 100% | Inspection |

---

### 3.3 External Interface Requirements

#### 3.3.1 Software Interfaces

| Interface | Protocol | Format | Authentication |
|-----------|----------|--------|----------------|
| SomaBrain HTTP API | HTTP/1.1 | JSON | Bearer token |
| SomaFractalMemory HTTP API | HTTP/1.1 | JSON | Bearer token |
| SomaBrain Direct Import | Python module | Python objects | N/A (in-process) |
| PostgreSQL | TCP | Django ORM | Database credentials |

#### 3.3.2 Hardware Interfaces

None.

---

### 3.4 Design Constraints

| ID | Constraint | Source |
|----|------------|--------|
| DC-001 | Memory configuration must be stored in capsule.body.persona.memory, not in code constants. | SRS-CAPSULE-PORTABILITY |
| DC-002 | OTEL tracing must use @tracer.start_as_current_span decorator pattern. | Platform Observability Standard |
| DC-003 | AAAS mode must use the existing Django database connection; no separate connection pool. | AAAS Architecture |

---

## 4. Traceability

### 4.1 Requirements Traceability Matrix

| REQ ID | Description | Source | Design | Implementation | Test |
|--------|-------------|--------|--------|----------------|------|
| REQ-SBI-001 | recall() operation | Chat Flow Phase 4 | admin/core/chat_orchestrator.py | services/common/brain_bridge.py | tests/unit/test_brain_recall.py |
| REQ-SBI-002 | recall() reads capsule config | Capsule Schema | admin/core/chat_orchestrator.py | services/common/brain_bridge.py | tests/unit/test_capsule_memory.py |
| REQ-SBI-003 | memorize() operation | Chat Flow Phase 9 | admin/core/chat_orchestrator.py | services/common/brain_bridge.py | tests/unit/test_brain_memorize.py |
| REQ-SBI-004 | memorize() reads capsule config | Capsule Schema | admin/core/chat_orchestrator.py | services/common/brain_bridge.py | tests/unit/test_capsule_memory.py |
| REQ-SBI-005 | learn() operation | Chat Flow Phase 10 | admin/core/chat_orchestrator.py | services/common/brain_bridge.py | tests/unit/test_brain_learn.py |
| REQ-SBI-006 | Lane preference update | Adaptive Learning | admin/core/chat_orchestrator.py | services/common/brain_bridge.py | tests/unit/test_brain_learn.py |
| REQ-SBI-007 | Tool preference update | Adaptive Learning | admin/core/chat_orchestrator.py | services/common/brain_bridge.py | tests/unit/test_brain_learn.py |
| REQ-SBI-008 | Neuromodulator update | Adaptive Learning | admin/core/chat_orchestrator.py | services/common/brain_bridge.py | tests/unit/test_brain_learn.py |
| REQ-SBI-009 | Persist learned state | Capsule Persistence | admin/core/models/core.py | services/common/brain_bridge.py | tests/unit/test_capsule_save.py |
| REQ-SBI-010 | ask() Sub-LM operation | RLM Integration | admin/core/chat_orchestrator.py | services/common/brain_bridge.py | tests/unit/test_brain_ask.py |
| REQ-SBI-011 | ask() memory augmentation | RLM Integration | admin/core/chat_orchestrator.py | services/common/brain_bridge.py | tests/unit/test_brain_ask.py |
| REQ-SBI-012 | AAAS direct import mode | Deployment Modes | config/settings_registry.py | services/common/adapters/brain_direct.py | tests/integration/test_aaas_mode.py |
| REQ-SBI-013 | Standalone HTTP client mode | Deployment Modes | config/settings_registry.py | admin/core/somabrain_client.py | tests/integration/test_standalone_mode.py |
| REQ-SBI-014 | Deployment mode selection | Deployment Modes | config/settings_registry.py | config/settings_registry.py | tests/unit/test_settings.py |

### 4.2 Requirement to Test Case Mapping

| REQ ID | Test Case ID | Test Method | Expected Result |
|--------|--------------|-------------|-----------------|
| REQ-SBI-001 | TC-SBI-001 | Unit Test | recall() returns list of memory objects |
| REQ-SBI-002 | TC-SBI-002 | Unit Test | recall_limit matches capsule value, not default |
| REQ-SBI-005 | TC-SBI-003 | Unit Test | learn() modifies capsule.body.learned |
| REQ-SBI-009 | TC-SBI-004 | Unit Test | asave() called with update_fields=["body"] |
| REQ-SBI-012 | TC-SBI-005 | Integration Test | AAAS mode completes recall in <50ms |
| REQ-SBI-013 | TC-SBI-006 | Integration Test | Standalone mode routes to SOMABRAIN_URL |
| NFR-OBS-001 | TC-SBI-007 | Inspection | OTEL span attributes contain capsule_id |

---

## 5. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 5.0 | 2026-01-16 | Engineering | Initial canonical version |
| 5.1 | 2026-05-21 | Engineering | Refactored to ISO/IEC/IEEE 29148:2018 template; removed personas, emojis, excessive code; added REQ numbering and traceability matrix |

---

*Document conforms to ISO/IEC/IEEE 29148:2018 — Systems and Software Engineering — Life Cycle Processes — Requirements Engineering.*
