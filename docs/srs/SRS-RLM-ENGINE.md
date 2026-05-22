# SRS-RLM-ENGINE — Recursive Language Model Execution

| Field | Value |
|-------|-------|
| **System** | SomaAgent01 |
| **Document ID** | SRS-RLM-ENGINE-2026-05-21 |
| **Version** | 5.1 |
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

This document specifies the Recursive Language Model (RLM) execution engine for SomaAgent01. The RLM engine enables complex multi-step reasoning by orchestrating a Mind-Body loop: the Mind LLM proposes actions, the Body executes them, and the Brain provides supplemental knowledge when the Mind is uncertain.

### 1.2 Scope

**In scope:**
- RLM settings derivation from capsule knobs
- Mind-Body action loop
- Brain.ask() sub-LM integration
- Learned preference persistence
- Temporal workflow orchestration
- SAGA compensation on failure
- Dead Letter Queue handling

**Out of scope:**
- LLM provider internals
- General chat flow orchestration (see SRS-CHAT-FLOW-MASTER)
- Context building (see SRS-CONTEXT-BUILDING)
- Model routing (see SRS-MODEL-ROUTING)

### 1.3 Definitions

| Term | Definition |
|------|------------|
| RLM | Recursive Language Model — a reasoning architecture using an action loop |
| Mind | The LLM instance that proposes reasoning steps |
| Body | The execution environment (REPL/tool runner) that carries out actions |
| Brain.ask() | Sub-LM query to SomaBrain for factual or memory-based answers |
| SAGA | Long-running transaction pattern with compensating actions |
| DLQ | Dead Letter Queue for failed events |

### 1.4 References

| ID | Document | Version | Location |
|----|----------|---------|----------|
| REF-001 | SRS-CHAT-FLOW-MASTER | 3.1 | `docs/srs/SRS-CHAT-FLOW-MASTER.md` |
| REF-002 | SRS-CONTEXT-BUILDING | 5.1 | `docs/srs/SRS-CONTEXT-BUILDING.md` |
| REF-003 | SRS-MODEL-ROUTING | 1.1 | `docs/srs/SRS-MODEL-ROUTING.md` |
| REF-004 | RLM Core | — | `tmp/rlm/rlm/core/rlm.py` |
| REF-005 | SomaBrain Integration | — | `admin/agents/services/somabrain_integration.py` |
| REF-006 | Temporal Worker | — | `services/conversation_worker/temporal_worker.py` |
| REF-007 | Compensation | — | `services/common/compensation.py` |
| REF-008 | DLQ | — | `services/common/dlq.py` |

---

## 2. Product Description

### 2.1 Product Perspective

The RLM engine executes in Phase 8 of the 12-phase chat flow, after initial LLM generation and before SomaBrain learning. It is wrapped in a Temporal workflow for durability, with SAGA compensation and DLQ handling for fault tolerance.

### 2.2 Product Functions

| ID | Function | Description |
|----|----------|-------------|
| FUNC-001 | Derive Settings | Compute `max_iterations`, `max_depth`, `thinking_tokens`, `memory_recall_limit`, and `brain_query_enabled` from capsule intelligence level |
| FUNC-002 | Mind Propose | Invoke the Mind LLM to generate the next action given current state |
| FUNC-003 | Body Execute | Run the proposed action (tool call or REPL command) |
| FUNC-004 | Brain Ask | Query SomaBrain as a sub-LM when the Mind expresses uncertainty |
| FUNC-005 | State Update | Advance the loop state with observations from Body or Brain |
| FUNC-006 | Loop Control | Terminate when the action is `complete` or `max_iterations` is reached |
| FUNC-007 | Temporal Orchestrate | Run the conversation workflow via Temporal for durability |
| FUNC-008 | Compensate | Execute compensating actions on workflow failure |
| FUNC-009 | DLQ Route | Send unrecoverable events to the Dead Letter Queue |

### 2.3 User Characteristics

| User Type | Role | Technical Level | Access |
|-----------|------|-----------------|--------|
| End User | Chat participant | Low | Indirect (via improved reasoning quality) |
| Agent Developer | Persona author | Medium | Knobs configuration (`intelligence_level`) |
| Platform Engineer | System maintainer | High | Temporal UI, DLQ inspection |

### 2.4 Constraints

| ID | Constraint | Description |
|----|------------|-------------|
| CON-001 | No Hardcoded Settings | All RLM parameters must derive from `capsule.body.persona.knobs`; no constants in engine code |
| CON-002 | Intelligence Gating | `brain_query_enabled` is false for intelligence levels 1–3 |
| CON-003 | Temporal Timeout | Workflow schedule-to-close timeout is 300 seconds |

### 2.5 Assumptions and Dependencies

| ID | Assumption / Dependency | Impact if Invalid |
|----|------------------------|-------------------|
| AD-001 | Temporal server is reachable | Workflow cannot be scheduled; request falls back to synchronous path |
| AD-002 | SomaBrain is available for Brain.ask() | Sub-LM queries disabled; Mind operates without supplemental memory |
| AD-003 | LLM fallback chain is operational | RLM cannot execute if no LLM provider is available |

---

## 3. Specific Requirements

### 3.1 Functional Requirements

#### 3.1.1 Settings Derivation

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-001 | The system shall derive RLM settings from `capsule.body.persona.knobs.intelligence_level` using a deterministic mapping. | Must | Test | Approved |
| REQ-002 | For intelligence level 1–3, the system shall set `max_iterations=1`, `max_depth=1`, `thinking_tokens=512`, and `brain_query_enabled=false`. | Must | Test | Approved |
| REQ-003 | For intelligence level 4–6, the system shall set `max_iterations=2`, `max_depth=2`, `thinking_tokens=1024`, and `brain_query_enabled=true`. | Must | Test | Approved |
| REQ-004 | For intelligence level 7–8, the system shall set `max_iterations=3`, `max_depth=3`, `thinking_tokens=2048`, and `brain_query_enabled=true`. | Must | Test | Approved |
| REQ-005 | For intelligence level 9–10, the system shall set `max_iterations=5`, `max_depth=5`, `thinking_tokens=4096`, and `brain_query_enabled=true`. | Must | Test | Approved |

**Rationale:** Settings must scale with agent intelligence without hardcoding.

**Dependencies:** None

#### 3.1.2 Mind-Body Loop

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-006 | The system shall initialize the RLM engine with derived settings before entering the action loop. | Must | Test | Approved |
| REQ-007 | The system shall invoke the Mind LLM on each iteration to propose the next action. | Must | Test | Approved |
| REQ-008 | If the proposed action is `brain_query`, the system shall call `brain.ask()` with the question, `capsule_id`, and `memory_config`. | Must | Test | Approved |
| REQ-009 | If the proposed action is `tool_call`, the system shall execute the tool via the Body REPL and capture the observation. | Must | Test | Approved |
| REQ-010 | If the proposed action is `complete`, the system shall terminate the loop and return the result to the caller. | Must | Test | Approved |
| REQ-011 | The system shall update the loop state after each action before proceeding to the next iteration. | Must | Test | Approved |
| REQ-012 | The system shall enforce `max_iterations` as a hard upper bound on loop iterations. | Must | Test | Approved |

**Rationale:** The Mind-Body loop is the core RLM reasoning pattern.

**Dependencies:** REQ-001

#### 3.1.3 Brain.ask() Integration

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-013 | The system shall check `brain_query_enabled` before issuing a `brain.ask()` call; if false, it shall return "Brain queries disabled at this intelligence level". | Must | Test | Approved |
| REQ-014 | When `brain_query_enabled` is true, the system shall query SomaBrain with the capsule context and memory configuration. | Must | Test | Approved |

**Rationale:** Brain queries are computationally expensive and gated by intelligence level.

**Dependencies:** REQ-008

#### 3.1.4 Learned Preferences

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-015 | The system shall read `capsule.body.learned.rlm_preferences` to adapt behavior, including `preferred_depth`, `brain_query_success_rate`, and `avg_iterations`. | Should | Test | Approved |
| REQ-016 | The system shall persist updated RLM statistics back to `capsule.body.learned.rlm_preferences` after execution. | Should | Test | Approved |

**Rationale:** Learned preferences enable agent personalization over time.

**Dependencies:** REQ-006

#### 3.1.5 Temporal Workflow Orchestration

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-017 | The system shall define a `ConversationWorkflow` Temporal workflow that schedules `process_message_activity` with a 300-second schedule-to-close timeout. | Must | Test | Approved |
| REQ-018 | The `process_message_activity` shall execute the message processor, catch exceptions, trigger compensation, and send failed events to the DLQ. | Must | Test | Approved |
| REQ-019 | On success, the system shall return `{"success": true, "error": null}` from the activity. | Must | Test | Approved |
| REQ-020 | On failure, the system shall return `{"success": false, "error": <message>}` from the activity after compensation and DLQ routing. | Must | Test | Approved |

**Rationale:** Temporal provides durability and recoverability for long-running conversations.

**Dependencies:** None

#### 3.1.6 Compensation and DLQ

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-021 | The system shall execute `compensate_event()` for every workflow failure to reverse partial side effects. | Must | Test | Approved |
| REQ-022 | The system shall send unrecoverable events to the DLQ via `dlq.send_to_dlq(event, exc)`. | Must | Test | Approved |

**Rationale:** SAGA compensation and DLQ ensure data consistency and observability.

**Dependencies:** REQ-018

### 3.2 Non-Functional Requirements

#### 3.2.1 Performance

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-PERF-001 | RLM execution shall complete within the 300-second Temporal timeout. | <300 s | Test |
| NFR-PERF-002 | Each Mind-Body iteration shall reuse the same LLM connection where possible. | — | Inspection |

#### 3.2.2 Security

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-SEC-001 | Tool calls within the Body REPL shall be subject to the same OPA policy checks as standalone tool execution. | 100% | Test |

#### 3.2.3 Reliability

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-REL-001 | RLM shall use the same LLM fallback chain as standard chat generation. | — | Test |
| NFR-REL-002 | Temporal workflow history shall be retained for debugging and replay. | — | Inspection |

#### 3.2.4 Scalability

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-SCL-001 | RLM engine shall support concurrent execution of independent conversation workflows. | — | Test |

#### 3.2.5 Maintainability

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-MNT-001 | RLM settings derivation shall be isolated in a dedicated function. | — | Inspection |

---

### 3.3 External Interface Requirements

#### 3.3.1 User Interfaces

Not applicable.

#### 3.3.2 Software Interfaces

| Interface | Protocol | Format | Authentication |
|-----------|----------|--------|----------------|
| Temporal Server | gRPC | Protobuf | mTLS / API key |
| SomaBrain | Direct import (AAAS) or HTTP (STANDALONE) | Python objects / JSON | Internal |
| LLM Providers | HTTP / REST | JSON | API Key (via LiteLLM) |
| Kafka | TCP | Binary | SASL / SSL |

#### 3.3.3 Hardware Interfaces

Not applicable.

---

### 3.4 Design Constraints

| ID | Constraint | Source |
|----|------------|--------|
| DC-001 | In AAAS mode, RLM and SomaBrain calls shall use direct imports with zero HTTP latency. | Architecture decision |
| DC-002 | RLM shall read from Capsule and never use hardcoded values. | Design standard |
| DC-003 | Temporal queue name shall be `conversation` and host shall be `temporal:7233` by default. | Infrastructure config |

---

## 4. Traceability

### 4.1 Requirements Traceability Matrix

| REQ ID | Description | Source | Design | Implementation | Test |
|--------|-------------|--------|--------|----------------|------|
| REQ-001 | Derive RLM settings from intelligence | RLM spec | Derivation function | `tmp/rlm/rlm/core/rlm.py` | `tests/agent_chat/test_full_chat_flow.py` |
| REQ-002 | Low intelligence settings (1–3) | Knobs spec | Mapping table | `tmp/rlm/rlm/core/rlm.py` | `tests/agent_chat/test_full_chat_flow.py` |
| REQ-003 | Medium intelligence settings (4–6) | Knobs spec | Mapping table | `tmp/rlm/rlm/core/rlm.py` | `tests/agent_chat/test_full_chat_flow.py` |
| REQ-004 | High intelligence settings (7–8) | Knobs spec | Mapping table | `tmp/rlm/rlm/core/rlm.py` | `tests/agent_chat/test_full_chat_flow.py` |
| REQ-005 | Expert intelligence settings (9–10) | Knobs spec | Mapping table | `tmp/rlm/rlm/core/rlm.py` | `tests/agent_chat/test_full_chat_flow.py` |
| REQ-006 | Initialize engine with settings | RLM spec | Constructor | `tmp/rlm/rlm/core/rlm.py` | `tests/agent_chat/test_full_chat_flow.py` |
| REQ-007 | Mind LLM proposal per iteration | RLM spec | Loop body | `tmp/rlm/rlm/core/rlm.py` | `tests/agent_chat/test_full_chat_flow.py` |
| REQ-008 | brain_query action handling | RLM spec | Branch logic | `tmp/rlm/rlm/core/rlm.py` | `tests/agent_chat/test_full_chat_flow.py` |
| REQ-009 | tool_call action handling | RLM spec | Branch logic | `tmp/rlm/rlm/core/rlm.py` | `tests/agent_chat/test_full_chat_flow.py` |
| REQ-010 | complete action termination | RLM spec | Loop exit | `tmp/rlm/rlm/core/rlm.py` | `tests/agent_chat/test_full_chat_flow.py` |
| REQ-011 | State update after action | RLM spec | State machine | `tmp/rlm/rlm/core/rlm.py` | `tests/agent_chat/test_full_chat_flow.py` |
| REQ-012 | max_iterations enforcement | RLM spec | Guard clause | `tmp/rlm/rlm/core/rlm.py` | `tests/agent_chat/test_full_chat_flow.py` |
| REQ-013 | brain_query_enabled gate | RLM spec | Guard clause | `tmp/rlm/rlm/core/rlm.py` | `tests/agent_chat/test_full_chat_flow.py` |
| REQ-014 | SomaBrain query with context | RLM spec | Client call | `admin/agents/services/somabrain_integration.py` | `tests/agent_chat/test_full_chat_flow.py` |
| REQ-015 | Read learned preferences | Learning spec | Preference reader | `tmp/rlm/rlm/core/rlm.py` | `tests/agent_chat/test_full_chat_flow.py` |
| REQ-016 | Persist updated statistics | Learning spec | Preference writer | `tmp/rlm/rlm/core/rlm.py` | `tests/agent_chat/test_full_chat_flow.py` |
| REQ-017 | ConversationWorkflow definition | Temporal spec | Workflow decorator | `services/conversation_worker/temporal_worker.py` | `tests/agent_chat/test_full_chat_flow.py` |
| REQ-018 | process_message_activity | Temporal spec | Activity decorator | `services/conversation_worker/temporal_worker.py` | `tests/agent_chat/test_full_chat_flow.py` |
| REQ-019 | Success response format | API contract | Return value | `services/conversation_worker/temporal_worker.py` | `tests/agent_chat/test_full_chat_flow.py` |
| REQ-020 | Failure response format | API contract | Return value | `services/conversation_worker/temporal_worker.py` | `tests/saas/test_chat_flow_e2e.py` |
| REQ-021 | SAGA compensation | Reliability spec | Compensation call | `services/common/compensation.py` | `tests/saas/test_chat_flow_e2e.py` |
| REQ-022 | DLQ routing | Reliability spec | DLQ call | `services/common/dlq.py` | `tests/saas/test_chat_flow_e2e.py` |

### 4.2 Requirement to Test Case Mapping

| REQ ID | Test Case ID | Test Method | Expected Result |
|--------|--------------|-------------|-----------------|
| REQ-001 | TC-001 | Unit | Settings match intelligence mapping |
| REQ-002 | TC-002 | Unit | Level 1 returns `brain_query_enabled=false` |
| REQ-005 | TC-003 | Unit | Level 10 returns `max_iterations=5` |
| REQ-012 | TC-004 | Unit | Loop terminates at `max_iterations` |
| REQ-013 | TC-005 | Unit | Brain query skipped when disabled |
| REQ-017 | TC-006 | Integration | Workflow scheduled with 300s timeout |
| REQ-021 | TC-007 | Integration | Compensation called on failure |
| REQ-022 | TC-008 | Integration | Event sent to DLQ on unrecoverable error |

---

## 5. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-10 | Engineering | Initial version |
| 2.0–4.0 | 2026-01-12 to 2026-01-14 | Engineering | Temporal integration, SAGA, DLQ |
| 5.0 | 2026-01-16 | Engineering | AAAS direct calls enforced |
| 5.1 | 2026-05-21 | Engineering | Refactored to ISO/IEC/IEEE 29148 template |

---

*Document conforms to ISO/IEC/IEEE 29148:2018 — Systems and Software Engineering — Life Cycle Processes — Requirements Engineering.*
