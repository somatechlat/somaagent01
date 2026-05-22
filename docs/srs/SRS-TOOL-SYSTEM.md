# SRS-TOOL-SYSTEM — Tool Discovery and Execution

| Field | Value |
|-------|-------|
| **System** | SomaAgent01 |
| **Document ID** | SRS-TOOL-SYSTEM-2026-01-16 |
| **Version** | 1.1 |
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

This document specifies the requirements for the Tool Discovery and Execution subsystem of SomaAgent01. The subsystem governs which tools are available to an agent during a chat turn, validates tool calls from the LLM, executes tools via the Model Context Protocol (MCP) or native handlers, and records all executions for audit and billing.

### 1.2 Scope

**In Scope:**
- 4-phase tool discovery gate (registry, capsule, SpiceDB, OPA)
- Tool parameter validation against JSON Schema
- Tool execution via MCP and native providers
- Error handling for permission denial, execution failure, and timeout
- Execution metrics and audit logging
- Budget gate integration for tool calls

**Out of Scope:**
- Tool UI marketplace
- Real-time tool streaming responses
- Third-party tool marketplace certification

### 1.3 Definitions

| Term | Definition |
|------|------------|
| Capability | A registered tool or function exposed to the agent, defined in the Capability model |
| 4-Phase Gate | The discovery pipeline comprising registry enabled check, capsule M2M filter, SpiceDB permission check, and OPA policy check |
| MCP | Model Context Protocol for standardized tool server communication |
| SpiceDB | Fine-grained authorization system storing tool:execute permissions |
| OPA | Open Policy Agent for dynamic policy evaluation on tool execution |
| Native Provider | Tool implementation executing directly within the SomaAgent01 codebase |

### 1.4 References

| ID | Document | Version | Location |
|----|----------|---------|----------|
| REF-001 | SRS-CHAT-FLOW-V0.3.md | 0.3 | docs/srs/SRS-CHAT-FLOW-V0.3.md |
| REF-002 | SRS-BUDGET-SYSTEM.md | 1.0 | docs/srs/SRS-BUDGET-SYSTEM.md |
| REF-003 | Capability Model | Current | admin/core/models/core.py |
| REF-004 | SpiceDB Schema | Current | policy/tool_policy.rego |
| REF-005 | OPA Policy | Current | policy/soma_development.rego |

---

## 2. Product Description

### 2.1 Product Perspective

The Tool System spans Phase 5 (Tool Discovery) and Phase 7 (Tool Execution) of the 12-phase chat flow. During discovery, the system progressively filters the global capability registry against the capsule, user permissions, and runtime policies. During execution, parsed tool calls are validated, routed to the appropriate provider, and results are returned to the LLM context.

### 2.2 Product Functions

| ID | Function | Description |
|----|----------|-------------|
| FUNC-001 | Tool Discovery | Filter global capabilities through the 4-phase gate to produce the discoverable tool set |
| FUNC-002 | Tool Validation | Validate LLM-emitted tool call parameters against the capability JSON Schema |
| FUNC-003 | Tool Execution | Route validated tool calls to MCP or native providers and collect results |
| FUNC-004 | Audit Recording | Log every tool execution with tool_name, user_id, tenant_id, and outcome |
| FUNC-005 | Budget Enforcement | Apply @budget_gate(metric="tool_calls") to each execution |

### 2.3 User Characteristics

| User Type | Role | Technical Level | Access |
|-----------|------|-----------------|--------|
| End User | Chat participant | Low | Uses tools indirectly via agent |
| Agent Operator | Tenant administrator | Medium | Configures capsule capabilities and MCP servers |
| Security Admin | Compliance officer | High | Defines OPA policies and SpiceDB relations |
| Platform Engineer | DevOps / SRE | High | Configures MCP server endpoints and timeouts |

### 2.4 Constraints

| ID | Constraint | Description |
|----|------------|-------------|
| CON-001 | Schema Compliance | All tool parameters must validate against the JSON Schema stored in Capability.schema |
| CON-002 | Permission Denial | Tools failing SpiceDB or OPA checks must be hidden from the LLM, not exposed with errors |
| CON-003 | Budget Limit | Tool executions exceeding the tenant budget limit must be rejected before provider invocation |

### 2.5 Assumptions and Dependencies

| ID | Assumption / Dependency | Impact if Invalid |
|----|------------------------|-------------------|
| AD-001 | Capability registry contains accurate is_enabled flags and schemas | LLM receives incorrect or broken tools |
| AD-002 | SpiceDB is reachable for permission checks | All tools hidden; chat degrades to text-only |
| AD-003 | OPA is reachable for policy checks | Policy violations not blocked; security risk |
| AD-004 | MCP servers are configured with valid commands and environment | Native tools fail to initialize |
| AD-005 | Budget cache is reachable | Budget enforcement disabled; potential overuse |

---

## 3. Specific Requirements

### 3.1 Functional Requirements

#### 3.1.1 Tool Discovery

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-TS-001 | The system shall perform a 4-phase discovery gate before exposing tools to the LLM. | Must | Test | Approved |
| REQ-TS-002 | Phase 1 shall filter capabilities where Capability.is_enabled equals true. | Must | Test | Approved |
| REQ-TS-003 | Phase 2 shall filter capabilities to those present in the capsule's capability M2M relationship. | Must | Test | Approved |
| REQ-TS-004 | Phase 3 shall query SpiceDB to verify the user has tool:execute permission on the tool resource. | Must | Test | Approved |
| REQ-TS-005 | Phase 4 shall query OPA to evaluate dynamic policy rules for the tool execution context. | Must | Test | Approved |
| REQ-TS-006 | Tools failing any phase shall be excluded from the discoverable set without error exposure to the LLM. | Must | Test | Approved |

**Rationale:** Progressive filtering ensures only authorized, enabled, and policy-compliant tools are exposed.

---

#### 3.1.2 Tool Execution

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-TS-007 | The system shall parse tool calls from the LLM response and validate parameters against Capability.schema. | Must | Test | Approved |
| REQ-TS-008 | The system shall route tool calls with provider="mcp" to the MCP client for remote execution. | Must | Test | Approved |
| REQ-TS-009 | The system shall route tool calls with provider="native" to the native executor for in-process execution. | Must | Test | Approved |
| REQ-TS-010 | The system shall record every tool execution to the audit log including tool_name, user_id, tenant_id, timestamp, and outcome. | Must | Test | Approved |
| REQ-TS-011 | The system shall enforce the @budget_gate(metric="tool_calls") decorator on every tool execution entrypoint. | Must | Test | Approved |

**Rationale:** Parameter validation prevents malformed tool calls; provider routing enables both external and internal tool ecosystems.

**Dependencies:** REQ-TS-007 depends on REQ-TS-001 (discoverable set defines valid tools).

---

#### 3.1.3 Error Handling

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-TS-012 | The system shall raise ToolNotFoundError when the LLM requests a tool not in the discoverable set. | Must | Test | Approved |
| REQ-TS-013 | The system shall raise ToolPermissionDenied when SpiceDB or OPA denies execution at runtime. | Must | Test | Approved |
| REQ-TS-014 | The system shall raise ToolExecutionError when provider execution fails, triggering circuit breaker logic. | Must | Test | Approved |
| REQ-TS-015 | The system shall raise ToolTimeoutError when execution exceeds the configured timeout, returning a partial result if available. | Should | Test | Approved |

**Rationale:** Structured error types enable the chat flow to return meaningful failure messages to the LLM and user.

---

### 3.2 Non-Functional Requirements

#### 3.2.1 Performance

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-PERF-001 | Tool discovery latency shall not exceed 50ms for a capsule with up to 50 capabilities. | 50 ms | Load Test |
| NFR-PERF-002 | Tool execution latency (excluding provider round-trip) shall not exceed 20ms. | 20 ms | Load Test |

#### 3.2.2 Security

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-SEC-001 | Unauthorized tools shall not be discoverable or executable by any user lacking SpiceDB permission. | 100% | Pen Test |
| NFR-SEC-002 | OPA policies shall deny execution for contexts violating tenant-scoped rules. | 100% | Policy Test |

#### 3.2.3 Reliability

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-REL-001 | MCP server failures shall not crash the tool executor; the system shall degrade to remaining tools. | 100% | Fault Injection |
| NFR-REL-002 | Circuit breaker shall open after 5 consecutive failures and close after 30 seconds. | Configurable | Chaos Test |

#### 3.2.4 Observability

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-OBS-001 | The system shall emit metrics for tool_discovery_count, tool_execution_total, tool_execution_duration, and tool_permission_denied. | 100% | Inspection |

---

### 3.3 External Interface Requirements

#### 3.3.1 Software Interfaces

| Interface | Protocol | Format | Authentication |
|-----------|----------|--------|----------------|
| SpiceDB CheckPermission | gRPC/HTTP | JSON | Preshared key |
| OPA Policy Evaluation | HTTP/JSON | JSON | None (local) |
| MCP Server | stdio / SSE | JSON-RPC | None (local process) |
| Native Executor | Python function call | Python dict | N/A (in-process) |
| Audit Log | Async message queue | JSON | Internal |
| Budget Cache | RESP | Key-value | Redis AUTH |

#### 3.3.2 Hardware Interfaces

None.

---

### 3.4 Design Constraints

| ID | Constraint | Source |
|----|------------|--------|
| DC-001 | Capability schema must be valid JSON Schema (Draft 7 or later). | Platform Standard |
| DC-002 | MCP server configuration must specify command, args, and timeout. | MCP Protocol v1.0 |
| DC-003 | Tool discovery must complete before LLM invocation (Phase 5 before Phase 6). | Chat Flow Architecture |
| DC-004 | Audit records must be emitted asynchronously to avoid blocking execution. | Performance Standard |

---

## 4. Traceability

### 4.1 Requirements Traceability Matrix

| REQ ID | Description | Source | Design | Implementation | Test |
|--------|-------------|--------|--------|----------------|------|
| REQ-TS-001 | 4-phase discovery gate | Chat Flow Phase 5 | admin/core/models/core.py | services/tool_executor/tools.py | tests/unit/test_tool_discovery.py |
| REQ-TS-002 | Registry enabled filter | Capability Model | admin/core/models/core.py | services/tool_executor/tools.py | tests/unit/test_tool_registry_filter.py |
| REQ-TS-003 | Capsule M2M filter | Capsule Config | admin/core/models/core.py | services/tool_executor/tools.py | tests/unit/test_capsule_tool_filter.py |
| REQ-TS-004 | SpiceDB permission check | Authorization | services/common/spicedb_client.py | services/common/spicedb_client.py | tests/integration/test_spicedb_tools.py |
| REQ-TS-005 | OPA policy check | Policy | policy/tool_policy.rego | services/common/opa_policy_adapter.py | tests/integration/test_opa_tools.py |
| REQ-TS-006 | Silent exclusion on failure | Security | services/tool_executor/tools.py | services/tool_executor/tools.py | tests/unit/test_tool_silent_exclude.py |
| REQ-TS-007 | Parameter validation | Execution | admin/core/models/core.py | services/tool_executor/validation.py | tests/unit/test_tool_validation.py |
| REQ-TS-008 | MCP provider routing | MCP Protocol | admin/core/helpers/mcp_clients.py | admin/core/helpers/mcp_clients.py | tests/integration/test_mcp_execution.py |
| REQ-TS-009 | Native provider routing | Native Execution | services/tool_executor/execution_engine.py | services/tool_executor/execution_engine.py | tests/unit/test_native_execution.py |
| REQ-TS-010 | Audit recording | Audit | services/tool_executor/audit.py | services/tool_executor/audit.py | tests/unit/test_tool_audit.py |
| REQ-TS-011 | Budget gate enforcement | Budget | services/common/budget_cache.py | services/tool_executor/tools.py | tests/unit/test_tool_budget.py |
| REQ-TS-012 | ToolNotFoundError | Error Handling | services/tool_executor/tools.py | services/tool_executor/tools.py | tests/unit/test_tool_errors.py |
| REQ-TS-013 | ToolPermissionDenied | Error Handling | services/tool_executor/tools.py | services/tool_executor/tools.py | tests/unit/test_tool_errors.py |
| REQ-TS-014 | ToolExecutionError | Error Handling | services/common/circuit_breaker.py | services/tool_executor/tools.py | tests/unit/test_tool_errors.py |
| REQ-TS-015 | ToolTimeoutError | Error Handling | services/tool_executor/tools.py | services/tool_executor/tools.py | tests/unit/test_tool_timeout.py |

### 4.2 Requirement to Test Case Mapping

| REQ ID | Test Case ID | Test Method | Expected Result |
|--------|--------------|-------------|-----------------|
| REQ-TS-001 | TC-TS-001 | Unit Test | 4-phase gate returns subset of capabilities |
| REQ-TS-004 | TC-TS-002 | Integration Test | SpiceDB denies unauthorized tool; tool excluded |
| REQ-TS-005 | TC-TS-003 | Integration Test | OPA denies policy violation; tool excluded |
| REQ-TS-007 | TC-TS-004 | Unit Test | Invalid parameters rejected with schema error |
| REQ-TS-008 | TC-TS-005 | Integration Test | MCP tool call returns provider result |
| REQ-TS-010 | TC-TS-006 | Unit Test | Audit log contains tool_name and user_id |
| REQ-TS-011 | TC-TS-007 | Unit Test | Budget exhausted returns 402 before execution |
| NFR-OBS-001 | TC-TS-008 | Inspection | Prometheus metrics contain tool labels |

---

## 5. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-16 | Engineering | Initial final version |
| 1.1 | 2026-05-21 | Engineering | Refactored to ISO/IEC/IEEE 29148:2018 template; removed personas, emojis, excessive code; added REQ numbering and traceability matrix |

---

*Document conforms to ISO/IEC/IEEE 29148:2018 — Systems and Software Engineering — Life Cycle Processes — Requirements Engineering.*
