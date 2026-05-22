# SRS-{FEATURE} — {Title}

| Field | Value |
|-------|-------|
| **System** | SomaAgent01 |
| **Document ID** | SRS-{FEATURE}-{YYYY-MM-DD} |
| **Version** | 1.0 |
| **Date** | {YYYY-MM-DD} |
| **Status** | Draft / Review / Approved |
| **Author** | {Name} |
| **Owner** | {Team} |

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

> Describe the purpose of this document and the system/feature it specifies.

### 1.2 Scope

> Define the boundaries of the system/feature. What is included and what is explicitly excluded.

### 1.3 Definitions

| Term | Definition |
|------|------------|
| {Term} | {Definition} |

### 1.4 References

| ID | Document | Version | Location |
|----|----------|---------|----------|
| REF-001 | {Title} | {Version} | {Path or URL} |

---

## 2. Product Description

### 2.1 Product Perspective

> Describe how this product/feature fits into the overall system architecture. Include context diagrams if applicable.

### 2.2 Product Functions

> High-level summary of the major functions the product must perform.

| ID | Function | Description |
|----|----------|-------------|
| FUNC-001 | {Name} | {Description} |

### 2.3 User Characteristics

> Describe the intended users of this feature, their technical expertise, and access levels.

| User Type | Role | Technical Level | Access |
|-----------|------|-----------------|--------|
| {Type} | {Role} | {Level} | {Access} |

### 2.4 Constraints

> List any constraints on the design or implementation (regulatory, hardware, budget, etc.).

| ID | Constraint | Description |
|----|------------|-------------|
| CON-001 | {Name} | {Description} |

### 2.5 Assumptions and Dependencies

> List assumptions made and external dependencies.

| ID | Assumption / Dependency | Impact if Invalid |
|----|------------------------|-------------------|
| AD-001 | {Description} | {Impact} |

---

## 3. Specific Requirements

### 3.1 Functional Requirements

> Numbered, atomic, verifiable requirements. Each must have a unique ID, description, priority, and verification method.

#### 3.1.1 {Subcategory}

| ID | Requirement | Priority | Verification | Status |
|----|-------------|----------|--------------|--------|
| REQ-001 | {The system shall...} | Must / Should / Could | Test / Inspection / Analysis | Draft |

**Rationale:** {Why this requirement exists.}

**Dependencies:** {List of REQ-IDs this depends on.}

---

### 3.2 Non-Functional Requirements

#### 3.2.1 Performance

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-PERF-001 | {The system shall respond within...} | {Value} | {Method} |

#### 3.2.2 Security

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-SEC-001 | {The system shall enforce...} | {Value} | {Method} |

#### 3.2.3 Reliability

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-REL-001 | {The system shall maintain...} | {Value} | {Method} |

#### 3.2.4 Scalability

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-SCL-001 | {The system shall support...} | {Value} | {Method} |

#### 3.2.5 Maintainability

| ID | Requirement | Target | Verification |
|----|-------------|--------|--------------|
| NFR-MNT-001 | {The system shall allow...} | {Value} | {Method} |

---

### 3.3 External Interface Requirements

#### 3.3.1 User Interfaces

> Describe UI requirements, accessibility standards, responsive design requirements.

#### 3.3.2 Software Interfaces

> Describe APIs, protocols, data formats for external system integration.

| Interface | Protocol | Format | Authentication |
|-----------|----------|--------|----------------|
| {Name} | {Protocol} | {Format} | {Auth} |

#### 3.3.3 Hardware Interfaces

> Describe any hardware interface requirements.

---

### 3.4 Design Constraints

> Constraints imposed by standards, hardware limitations, or other factors.

| ID | Constraint | Source |
|----|------------|--------|
| DC-001 | {Description} | {Source} |

---

## 4. Traceability

### 4.1 Requirements Traceability Matrix

| REQ ID | Description | Source | Design | Implementation | Test |
|--------|-------------|--------|--------|----------------|------|
| REQ-001 | {Brief} | {Source} | {File} | {File} | {Test} |

### 4.2 Requirement to Test Case Mapping

| REQ ID | Test Case ID | Test Method | Expected Result |
|--------|--------------|-------------|-----------------|
| REQ-001 | TC-001 | {Method} | {Result} |

---

## 5. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | {Date} | {Author} | Initial version |

---

*Document conforms to ISO/IEC/IEEE 29148:2018 — Systems and Software Engineering — Life Cycle Processes — Requirements Engineering.*
