# SRS-CONTEXT-BUILDING — Prompt Assembly

| Field | Value |
|-------|-------|
| **System** | SomaAgent01 |
| **Document ID** | SRS-CONTEXT-BUILDING-2026-05-21 |
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

This document specifies the ContextBuilding subsystem of SomaAgent01, which assembles LLM prompts from capsule configuration, conversation history, recalled memories, available tools, and the current user message.

### 1.2 Scope

**In scope:**
- System prompt construction from `capsule.body.persona`
- Injection prompt handling
- Lane-based token allocation
- Memory recall integration
- Tool capability formatting

**Out of scope:**
- LLM generation (see SRS-CHAT-FLOW-MASTER)
- Model routing (see SRS-MODEL-ROUTING)
- RLM execution (see SRS-RLM-ENGINE)

### 1.3 Definitions

| Term | Definition |
|------|------------|
| Capsule | The persistent agent configuration and state container |
| Context Lane | A named partition of the prompt context (system, history, memory, tools, buffer) |
| Injection Prompt | A persona-defined prompt segment triggered at a specific position |
| SomaBrain | Cognitive memory and learning subsystem |

### 1.4 References

| ID | Document | Version | Location |
|----|----------|---------|----------|
| REF-001 | SRS-CHAT-FLOW-MASTER | 3.1 | `docs/srs/SRS-CHAT-FLOW-MASTER.md` |
| REF-002 | Context Builder | — | `admin/core/context/builder.py` |
| REF-003 | Lane Allocator | — | `admin/core/context/lanes.py` |
| REF-004 | Context Models | — | `admin/core/context/models.py` |
| REF-005 | SomaBrain Client | — | `admin/core/somabrain_client.py` |

---

## 2. Product Description

### 2.1 Product Perspective

ContextBuilding is Phase 5 of the 12-phase chat flow. It receives a loaded capsule, the user message, and conversation history, and produces a `BuiltContext` object that the LLM layer consumes. In AAAS mode, all calls are direct Python imports with zero HTTP latency.

### 2.2 Product Functions

| ID | Function | Description |
|----|----------|-------------|
| FUNC-001 | Load System Prompt | Retrieve base system prompt from `capsule.body.persona.core.system_prompt` |
| FUNC-002 | Inject Prompts | Append injection prompts triggered at start position |
| FUNC-003 | Allocate Lanes | Compute token budget per context lane |
| FUNC-004 | Format History | Truncate and format conversation history to fit lane budget |
| FUNC-005 | Recall Memories | Query SomaBrain for relevant memories within lane budget |
| FUNC-006 | Format Tools | List enabled capabilities and tools within lane budget |
| FUNC-007 | Assemble Context | Combine all lanes into a single `BuiltContext` object |

### 2.3 User Characteristics

| User Type | Role | Technical Level | Access |
|-----------|------|-----------------|--------|
| End User | Chat participant | Low | Indirect (via chat response quality) |
| Agent Developer | Persona author | Medium | Capsule configuration API |
| Platform Engineer | System maintainer | High | Direct code access |

### 2.4 Constraints

| ID | Constraint | Description |
|----|------------|-------------|
| CON-001 | No Hardcoded Prompts | System prompts must originate from `capsule.body.persona`; no hardcoded strings in the builder |
| CON-002 | Token Budget | Total context must not exceed `max_tokens` derived from capsule knobs |

### 2.5 Assumptions and Dependencies

| ID | Assumption / Dependency | Impact if Invalid |
|----|------------------------|-------------------|
| AD-001 | Capsule contains valid persona configuration | Context cannot be built; request fails |
| AD-002 | SomaBrain recall is available | Memory lane is empty; chat continues degraded |

---

## 3. Specific Requirements

### 3.1 Functional Requirements

#### 3.1.1 System Prompt Construction

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-001 | The system shall retrieve the base system prompt from `capsule.body.persona.core.system_prompt`. | Must | Test | Approved |
| REQ-002 | The system shall append any injection prompts from `capsule.body.persona.prompts.injection_prompts` where `trigger == "start"` to the system prompt, each separated by a newline. | Must | Test | Approved |

**Rationale:** Injection prompts allow persona authors to customize behavior without code changes.

**Dependencies:** None

#### 3.1.2 Lane Allocation

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-003 | The system shall define five context lanes: `system`, `history`, `memory`, `tools`, and `buffer`. | Must | Inspection | Approved |
| REQ-004 | The system shall read lane allocation percentages from `capsule.body.learned.lane_preferences` when present. | Must | Test | Approved |
| REQ-005 | If `lane_preferences` is absent, the system shall derive defaults based on `capsule.body.persona.knobs.intelligence_level`: intelligence 1–3 uses equal 20% allocation; 4–6 uses `{system: 0.15, history: 0.30, memory: 0.25, tools: 0.20, buffer: 0.10}`; 7–10 uses `{system: 0.10, history: 0.35, memory: 0.30, tools: 0.15, buffer: 0.10}`. | Must | Test | Approved |

**Rationale:** Brain-learned preferences override defaults; defaults ensure sensible behavior for new agents.

**Dependencies:** REQ-001

#### 3.1.3 Token Budget Derivation

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-006 | The system shall derive `max_tokens` from capsule knobs via `derive_all_settings(capsule)`. | Must | Test | Approved |
| REQ-007 | The system shall allocate each lane a token budget equal to `int(max_tokens * lane_percentage)`. | Must | Test | Approved |

**Rationale:** Token budget must be deterministic and derived from capsule configuration.

**Dependencies:** REQ-005

#### 3.1.4 Memory Recall

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-008 | The system shall recall memories via SomaBrain using the query, `capsule_id`, `recall_limit`, and `similarity_threshold` from `capsule.body.persona.memory`. | Must | Test | Approved |
| REQ-009 | The system shall format recalled memories to fit within the memory lane token budget. | Must | Test | Approved |

**Rationale:** Memory recall must respect capsule-specific memory settings.

**Dependencies:** REQ-007

#### 3.1.5 Tool and History Formatting

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-010 | The system shall format available tools from `capsule.body.persona.tools.enabled_capabilities` to fit within the tools lane token budget. | Must | Test | Approved |
| REQ-011 | The system shall format conversation history to fit within the history lane token budget. | Must | Test | Approved |
| REQ-012 | The system shall truncate the user message to fit within the buffer lane token budget. | Must | Test | Approved |

**Rationale:** Each lane must be independently truncatable to preserve overall context size.

**Dependencies:** REQ-007

#### 3.1.6 Context Assembly

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-013 | The system shall return a `BuiltContext` object containing `system`, `history`, `memory`, `tools`, and `buffer` fields. | Must | Test | Approved |

**Rationale:** The `BuiltContext` object is the contract between ContextBuilding and the LLM layer.

**Dependencies:** REQ-008, REQ-010, REQ-011, REQ-012

### 3.2 Non-Functional Requirements

#### 3.2.1 Performance

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-PERF-001 | Context building shall complete within 5 ms under normal conditions. | <5 ms | Test |
| NFR-PERF-002 | Context building shall complete within 2 ms when memory recall is skipped due to degradation. | <2 ms | Test |

#### 3.2.2 Reliability

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-REL-001 | If SomaBrain recall fails, the memory lane shall be empty and the request shall continue. | — | Test |

#### 3.2.3 Maintainability

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-MNT-001 | Lane allocation logic shall be isolated in a dedicated module. | — | Inspection |

---

### 3.3 External Interface Requirements

#### 3.3.1 User Interfaces

Not applicable.

#### 3.3.2 Software Interfaces

| Interface | Protocol | Format | Authentication |
|-----------|----------|--------|----------------|
| SomaBrain | Direct import (AAAS) or HTTP (STANDALONE) | Python objects / JSON | Internal |
| Capsule Store | Django ORM | Python objects | Django auth |

#### 3.3.3 Hardware Interfaces

Not applicable.

---

### 3.4 Design Constraints

| ID | Constraint | Source |
|----|------------|--------|
| DC-001 | In AAAS mode, ContextBuilder and memory recall shall use direct imports with zero HTTP latency. | Architecture decision |
| DC-002 | No hardcoded prompts or lane defaults shall exist outside the capsule configuration or derivation logic. | Design standard |

---

## 4. Traceability

### 4.1 Requirements Traceability Matrix

| REQ ID | Description | Source | Design | Implementation | Test |
|--------|-------------|--------|--------|----------------|------|
| REQ-001 | System prompt from persona.core | Persona spec | Context model | `admin/core/context/builder.py` | `tests/agent_chat/test_full_chat_flow.py` |
| REQ-002 | Injection prompt appending | Persona spec | Context builder | `admin/core/context/builder.py` | `tests/agent_chat/test_full_chat_flow.py` |
| REQ-003 | Five context lanes | Context SRS | Lane model | `admin/core/context/lanes.py` | `tests/agent_chat/test_full_chat_flow.py` |
| REQ-004 | Lane preferences from learned | Learning SRS | Lane allocator | `admin/core/context/lanes.py` | `tests/agent_chat/test_full_chat_flow.py` |
| REQ-005 | Intelligence-based defaults | Knobs spec | Derivation table | `admin/core/context/lanes.py` | `tests/agent_chat/test_full_chat_flow.py` |
| REQ-006 | Max tokens from knobs | Knobs spec | Settings derivation | `admin/core/chat_orchestrator.py` | `tests/agent_chat/test_full_chat_flow.py` |
| REQ-007 | Per-lane token allocation | Context SRS | Budget math | `admin/core/context/builder.py` | `tests/agent_chat/test_full_chat_flow.py` |
| REQ-008 | Memory recall with capsule config | Memory SRS | Brain client | `admin/core/somabrain_client.py` | `tests/agent_chat/test_full_chat_flow.py` |
| REQ-009 | Memory formatting to budget | Context SRS | Formatter | `admin/core/context/builder.py` | `tests/agent_chat/test_full_chat_flow.py` |
| REQ-010 | Tool formatting to budget | Context SRS | Formatter | `admin/core/context/builder.py` | `tests/agent_chat/test_full_chat_flow.py` |
| REQ-011 | History formatting to budget | Context SRS | Formatter | `admin/core/context/builder.py` | `tests/agent_chat/test_full_chat_flow.py` |
| REQ-012 | User message truncation | Context SRS | Truncator | `admin/core/context/builder.py` | `tests/agent_chat/test_full_chat_flow.py` |
| REQ-013 | BuiltContext return | Context SRS | Dataclass | `admin/core/context/models.py` | `tests/agent_chat/test_full_chat_flow.py` |

### 4.2 Requirement to Test Case Mapping

| REQ ID | Test Case ID | Test Method | Expected Result |
|--------|--------------|-------------|-----------------|
| REQ-001 | TC-001 | Unit | System prompt matches `persona.core.system_prompt` |
| REQ-002 | TC-002 | Unit | Injection prompts appended when trigger is "start" |
| REQ-004 | TC-003 | Unit | Lane preferences from `learned` applied |
| REQ-005 | TC-004 | Unit | Default lanes match intelligence level |
| REQ-008 | TC-005 | Integration | Memories recalled using `persona.memory` settings |
| REQ-013 | TC-006 | Unit | `BuiltContext` returned with all five fields |

---

## 5. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-10 | Engineering | Initial version |
| 2.0–4.0 | 2026-01-12 to 2026-01-14 | Engineering | Lane allocation refinements |
| 5.0 | 2026-01-16 | Engineering | AAAS direct calls enforced |
| 5.1 | 2026-05-21 | Engineering | Refactored to ISO/IEC/IEEE 29148 template |

---

*Document conforms to ISO/IEC/IEEE 29148:2018 — Systems and Software Engineering — Life Cycle Processes — Requirements Engineering.*
