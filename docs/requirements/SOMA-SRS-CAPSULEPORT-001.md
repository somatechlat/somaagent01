# SRS-CAPSULE-PORTABILITY — Agent Portability and Exchange

| Field | Value |
|-------|-------|
| **System** | SomaAgent01 |
| **Document ID** | SRS-CAPSULE-PORTABILITY-2026-01-16 |
| **Version** | 3.1 |
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

This document specifies the requirements for the Capsule Portability subsystem of SomaAgent01. The Capsule is the sole unit of exchange for a complete agent, containing identity, governance, persona, and learned state. This document defines the schema, export/import semantics, and delegation behavior required for capsule portability across tenants and deployments.

### 1.2 Scope

**In Scope:**
- Capsule body JSON schema version 3.0
- Identity verification via registry signature and content hash
- Governance embedding (OPA policies, SpiceDB relations, permissions matrix)
- Persona completeness (core, prompts, tools, memory, voice, models, knobs)
- Learned state persistence and update
- Export to and import from portable bundles
- Delegation to sub-agents with inherited configuration

**Out of Scope:**
- Capsule UI editor
- Marketplace or distribution mechanism for capsules
- Version migration utilities for pre-v3.0 schemas

### 1.3 Definitions

| Term | Definition |
|------|------------|
| Capsule | The complete portable agent configuration unit containing identity, governance, persona, and learned state |
| Capsule Bundle | A serialized JSON object representing the exportable contents of a capsule |
| Identity | Cryptographic signature and hash verifying capsule authenticity and integrity |
| Governance | Authorization rules including OPA policies, SpiceDB relations, and permissions matrix |
| Persona | The agent's behavioral configuration including core personality, prompts, tools, memory, voice, models, and knobs |
| Learned | Mutable state updated by the cognitive engine, including preferences and neuromodulator values |
| Delegation | Creation of a child capsule inheriting from a parent with role-specific overrides |

### 1.4 References

| ID | Document | Version | Location |
|----|----------|---------|----------|
| REF-001 | SRS-SOMABRAIN-INTEGRATION.md | 5.1 | docs/srs/SRS-SOMABRAIN-INTEGRATION.md |
| REF-002 | SRS-TOOL-SYSTEM.md | 1.1 | docs/srs/SRS-TOOL-SYSTEM.md |
| REF-003 | SRS-CHAT-FLOW-MASTER.md | 3.0 | docs/srs/SRS-CHAT-FLOW-MASTER.md |
| REF-004 | Capsule Django Model | Current | admin/core/models/core.py |
| REF-005 | Capsule Export Service | Current | services/capsule_export.py |

---

## 2. Product Description

### 2.1 Product Perspective

The Capsule is the central data model of SomaAgent01. All chat flow phases read from or write to the capsule. The capsule is tenant-scoped and versioned. Portability enables capsules to be exported from one tenant and imported into another while preserving complete agent behavior.

The capsule consists of four top-level domains:
- Identity: cryptographic verification
- Governance: authorization and policy
- Persona: static behavioral configuration
- Learned: dynamic adaptation state

### 2.2 Product Functions

| ID | Function | Description |
|----|----------|-------------|
| FUNC-001 | Identity Verification | Verify capsule authenticity using Ed25519 signature and SHA256 content hash |
| FUNC-002 | Governance Enforcement | Apply embedded OPA policies and SpiceDB relations during runtime |
| FUNC-003 | Persona Configuration | Provide complete behavioral configuration for the agent |
| FUNC-004 | Learned Persistence | Store and update adaptive state modified by the cognitive engine |
| FUNC-005 | Capsule Export | Serialize the complete agent to a portable bundle |
| FUNC-006 | Capsule Import | Instantiate a new capsule from a portable bundle within a tenant |
| FUNC-007 | Delegation | Create child capsules with inherited configuration and role-specific overrides |

### 2.3 User Characteristics

| User Type | Role | Technical Level | Access |
|-----------|------|-----------------|--------|
| Capsule Designer | Creates and configures agents | Medium | Capsule body JSON editing |
| Tenant Admin | Manages agents within an organization | Medium | Import, export, delegate |
| Security Officer | Audits governance and identity | High | Identity verification, policy review |
| Platform Engineer | Operates the runtime | High | Full database and service access |

### 2.4 Constraints

| ID | Constraint | Description |
|----|------------|-------------|
| CON-001 | Schema Version | All capsules must declare a version field; current canonical version is 3.0 |
| CON-002 | Tenant Isolation | A capsule belongs to exactly one tenant and cannot be shared across tenants without export/import |
| CON-003 | Identity Immutability | Identity fields (registry_signature, content_hash, certified_at) must not change after certification |

### 2.5 Assumptions and Dependencies

| ID | Assumption / Dependency | Impact if Invalid |
|----|------------------------|-------------------|
| AD-001 | Capsule body JSON conforms to the v3.0 schema | Chat flow failures due to missing required sections |
| AD-002 | Ed25519 key pair exists for identity signing and verification | Identity verification always fails |
| AD-003 | Django ORM is available for capsule persistence | Complete platform failure |
| AD-004 | Parent capsule exists when delegation is requested | Delegation fails with foreign key error |

---

## 3. Specific Requirements

### 3.1 Functional Requirements

#### 3.1.1 Capsule Schema

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-CP-001 | The capsule body shall contain a version field set to "3.0". | Must | Inspection | Approved |
| REQ-CP-002 | The capsule body shall contain an identity section with registry_signature, content_hash, and certified_at fields. | Must | Inspection | Approved |
| REQ-CP-003 | The capsule body shall contain a governance section with constitution_id, opa_policies, spicedb_relations, and permissions_matrix. | Must | Inspection | Approved |
| REQ-CP-004 | The capsule body shall contain a persona section with name, description, core, prompts, tools, memory, voice, models, and knobs subsections. | Must | Inspection | Approved |
| REQ-CP-005 | The capsule body shall contain a learned section with lane_preferences, tool_preferences, model_preferences, and neuromodulator_state. | Must | Inspection | Approved |

**Rationale:** The schema completeness ensures that every portable agent contains all configuration required for deterministic behavior.

---

#### 3.1.2 Identity and Governance

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-CP-006 | The system shall verify capsule identity using the registry_signature against the content_hash. | Must | Test | Approved |
| REQ-CP-007 | The governance section shall define tool_execution rules specifying allowed tools and approval requirements. | Must | Inspection | Approved |
| REQ-CP-008 | The governance section shall define egress rules specifying allowed and denied external domains. | Must | Inspection | Approved |
| REQ-CP-009 | The governance section shall define memory rules specifying write permissions and encryption requirements. | Must | Inspection | Approved |

**Rationale:** Identity verification prevents tampering; governance embedding ensures policy travels with the agent.

---

#### 3.1.3 Persona Configuration

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-CP-010 | The persona.core section shall contain system_prompt, personality_traits, and neuromodulator_baseline. | Must | Inspection | Approved |
| REQ-CP-011 | The persona.prompts section shall contain injection_prompts, delegation_prompts, and tool_prompts. | Must | Inspection | Approved |
| REQ-CP-012 | The persona.tools section shall contain enabled_capabilities, mcp_servers, tool_permissions, and egress_whitelist. | Must | Inspection | Approved |
| REQ-CP-013 | The persona.memory section shall contain recall_limit, history_limit, similarity_threshold, and somabrain_settings. | Must | Inspection | Approved |
| REQ-CP-014 | The persona.voice section shall contain stt_model, stt_language, tts_voice_id, tts_speed, and vad_config. | Must | Inspection | Approved |
| REQ-CP-015 | The persona.models section shall contain chat_model_id, image_model_id, browser_model_id, and embedding_model_id. | Must | Inspection | Approved |
| REQ-CP-016 | The persona.knobs section shall contain intelligence_level, autonomy_level, and resource_budget. | Must | Inspection | Approved |

**Rationale:** Persona completeness ensures the agent has all behavioral parameters without runtime defaults.

**Dependencies:** REQ-CP-013 depends on SRS-SOMABRAIN-INTEGRATION REQ-SBI-002.

---

#### 3.1.4 Export and Import

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-CP-017 | The system shall provide an export operation that produces a portable bundle containing version, identity, governance, persona, and learned sections. | Must | Test | Approved |
| REQ-CP-018 | The system shall provide an import operation that instantiates a new Capsule from a portable bundle, associating it with a target tenant. | Must | Test | Approved |
| REQ-CP-019 | The import operation shall validate the bundle schema version before instantiation. | Must | Test | Approved |

**Rationale:** Export/import enables agent portability across tenants and deployments.

---

#### 3.1.5 Delegation

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-CP-020 | The system shall support delegation, creating a child capsule from a parent capsule with a specified role. | Should | Test | Approved |
| REQ-CP-021 | The child capsule shall inherit the parent's complete body and override the system_prompt with the delegation prompt matching the role. | Should | Test | Approved |
| REQ-CP-022 | The child capsule shall set its name to "{parent_name}:{role}". | Should | Inspection | Approved |
| REQ-CP-023 | The child capsule shall maintain a parent reference to the originating capsule. | Should | Inspection | Approved |

**Rationale:** Delegation enables hierarchical agent workflows where sub-agents specialize by role.

---

### 3.2 Non-Functional Requirements

#### 3.2.1 Security

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-SEC-001 | Identity registry_signature shall use Ed25519 cryptographic signatures. | 100% | Inspection |
| NFR-SEC-002 | content_hash shall use SHA256. | 100% | Inspection |
| NFR-SEC-003 | Exported bundles shall not contain internal database primary keys or tenant secrets. | 100% | Inspection |

#### 3.2.2 Reliability

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-REL-001 | Import of a valid v3.0 bundle shall succeed with all sections intact. | 100% | Test |
| NFR-REL-002 | Export shall be atomic; partial exports shall not be returned to the caller. | 100% | Test |

#### 3.2.3 Maintainability

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-MNT-001 | Schema version shall be incremented for any breaking change to the body structure. | 100% | Review |

---

### 3.3 External Interface Requirements

#### 3.3.1 Software Interfaces

| Interface | Protocol | Format | Authentication |
|-----------|----------|--------|----------------|
| Capsule Export API | HTTP/JSON | JSON | Bearer token |
| Capsule Import API | HTTP/JSON | JSON | Bearer token |
| Capsule Database | TCP | Django ORM | Database credentials |

#### 3.3.2 Hardware Interfaces

None.

---

### 3.4 Design Constraints

| ID | Constraint | Source |
|----|------------|--------|
| DC-001 | Capsule body must be stored as JSON in the Django model body field. | admin/core/models/core.py |
| DC-002 | Export must exclude internal fields (id, created_at, updated_at, tenant foreign keys). | Portability Standard |
| DC-003 | Delegation must preserve the full parent body via deep copy. | Data Integrity Standard |

---

## 4. Traceability

### 4.1 Requirements Traceability Matrix

| REQ ID | Description | Source | Design | Implementation | Test |
|--------|-------------|--------|--------|----------------|------|
| REQ-CP-001 | Version field | Capsule Schema | admin/core/models/core.py | admin/core/models/core.py | tests/unit/test_capsule_schema.py |
| REQ-CP-002 | Identity section | Capsule Schema | admin/core/models/core.py | admin/core/models/core.py | tests/unit/test_capsule_identity.py |
| REQ-CP-003 | Governance section | Capsule Schema | admin/core/models/core.py | admin/core/models/core.py | tests/unit/test_capsule_governance.py |
| REQ-CP-004 | Persona section | Capsule Schema | admin/core/models/core.py | admin/core/models/core.py | tests/unit/test_capsule_persona.py |
| REQ-CP-005 | Learned section | Capsule Schema | admin/core/models/core.py | admin/core/models/core.py | tests/unit/test_capsule_learned.py |
| REQ-CP-006 | Identity verification | Security | services/capsule_export.py | services/capsule_export.py | tests/unit/test_capsule_verify.py |
| REQ-CP-007 | Tool execution rules | Governance | policy/soma_development.rego | policy/soma_development.rego | tests/unit/test_governance_tools.py |
| REQ-CP-008 | Egress rules | Governance | policy/soma_development.rego | policy/soma_development.rego | tests/unit/test_governance_egress.py |
| REQ-CP-009 | Memory rules | Governance | policy/soma_development.rego | policy/soma_development.rego | tests/unit/test_governance_memory.py |
| REQ-CP-010 | Core persona fields | Persona | admin/core/models/core.py | admin/core/models/core.py | tests/unit/test_persona_core.py |
| REQ-CP-011 | Prompts fields | Persona | admin/core/models/core.py | admin/core/models/core.py | tests/unit/test_persona_prompts.py |
| REQ-CP-012 | Tools fields | Persona | admin/core/models/core.py | admin/core/models/core.py | tests/unit/test_persona_tools.py |
| REQ-CP-013 | Memory fields | Persona | admin/core/models/core.py | admin/core/models/core.py | tests/unit/test_persona_memory.py |
| REQ-CP-014 | Voice fields | Persona | admin/core/models/core.py | admin/core/models/core.py | tests/unit/test_persona_voice.py |
| REQ-CP-015 | Models fields | Persona | admin/core/models/core.py | admin/core/models/core.py | tests/unit/test_persona_models.py |
| REQ-CP-016 | Knobs fields | Persona | admin/core/models/core.py | admin/core/models/core.py | tests/unit/test_persona_knobs.py |
| REQ-CP-017 | Export operation | Portability | services/capsule_export.py | services/capsule_export.py | tests/unit/test_capsule_export.py |
| REQ-CP-018 | Import operation | Portability | services/capsule_export.py | services/capsule_export.py | tests/unit/test_capsule_import.py |
| REQ-CP-019 | Schema version validation | Portability | services/capsule_export.py | services/capsule_export.py | tests/unit/test_capsule_import.py |
| REQ-CP-020 | Delegation creation | Delegation | admin/core/models/core.py | services/capsule_export.py | tests/unit/test_capsule_delegate.py |
| REQ-CP-021 | Delegation prompt override | Delegation | admin/core/models/core.py | services/capsule_export.py | tests/unit/test_capsule_delegate.py |
| REQ-CP-022 | Delegation naming | Delegation | admin/core/models/core.py | services/capsule_export.py | tests/unit/test_capsule_delegate.py |
| REQ-CP-023 | Parent reference | Delegation | admin/core/models/core.py | services/capsule_export.py | tests/unit/test_capsule_delegate.py |

### 4.2 Requirement to Test Case Mapping

| REQ ID | Test Case ID | Test Method | Expected Result |
|--------|--------------|-------------|-----------------|
| REQ-CP-001 | TC-CP-001 | Inspection | body.version equals "3.0" |
| REQ-CP-006 | TC-CP-002 | Unit Test | verify() returns true for valid signature |
| REQ-CP-006 | TC-CP-003 | Unit Test | verify() returns false for tampered content |
| REQ-CP-017 | TC-CP-004 | Unit Test | Export bundle contains all 5 top-level sections |
| REQ-CP-018 | TC-CP-005 | Integration Test | Imported capsule matches bundle contents |
| REQ-CP-019 | TC-CP-006 | Unit Test | Import of unsupported version raises error |
| REQ-CP-020 | TC-CP-007 | Unit Test | Delegate creates child with parent reference |
| REQ-CP-021 | TC-CP-008 | Unit Test | Child system_prompt matches role delegation prompt |
| NFR-SEC-003 | TC-CP-009 | Inspection | Export bundle contains no internal database IDs |

---

## 5. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 3.0 | 2026-01-16 | Engineering | Initial canonical version with complete capsule architecture |
| 3.1 | 2026-05-21 | Engineering | Refactored to ISO/IEC/IEEE 29148:2018 template; removed personas, emojis, excessive code and diagrams; added REQ numbering and traceability matrix |

---

*Document conforms to ISO/IEC/IEEE 29148:2018 — Systems and Software Engineering — Life Cycle Processes — Requirements Engineering.*
