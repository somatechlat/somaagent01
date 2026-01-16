# SRS-CAPSULE-SYSTEM-ISO-COMPLETE
## ISO/IEC/IEEE 29148:2018 Compliant Specification
## SOMA Capsule Registry, Security, Encryption & Constitution

| Document ID | SRS-CAPSULE-SYSTEM-ISO-001 |
|-------------|---------------------------|
| Version | 1.0.0 |
| Date | 2026-01-03 |
| Status | APPROVED |
| Classification | Internal - Engineering |
| Authors | 7-Persona VIBE Analysis Team |

---

# TABLE OF CONTENTS

1. [Executive Summary](#1-executive-summary)
2. [System Architecture](#2-system-architecture)
3. [Constitution Subsystem](#3-constitution-subsystem)
4. [Capsule Registry Subsystem](#4-capsule-registry-subsystem)
5. [Security & Cryptography](#5-security--cryptography)
6. [Policy Enforcement](#6-policy-enforcement)
7. [UML Diagrams & Flows](#7-uml-diagrams--flows)
8. [7-Persona Deep Analysis](#8-7-persona-deep-analysis)
9. [Recommendations](#9-recommendations)
10. [Implementation Roadmap](#10-implementation-roadmap)

---

# 1. EXECUTIVE SUMMARY

## 1.1 Purpose
This document specifies the complete architecture for the SOMA Capsule System—the cryptographic trust infrastructure that governs Agent identity, capability, and legal compliance across the SOMA cognitive stack.

## 1.2 Scope
| Component | Description | Status |
|-----------|-------------|--------|
| **Constitution** | Immutable regulatory framework (SHA-256 + Ed25519) | ✅ Implemented |
| **Capsule Registry** | Certified agent identity store | ✅ Implemented |
| **Security Layer** | Ed25519 signing, JCS canonicalization | ✅ Implemented |
| **Policy Enforcement** | Egress, HITL, Resource limits | ✅ Implemented |
| **AgentCapsuleCreator** | Lit 3 UI for capsule authoring | ❌ Not Implemented |

## 1.3 Compliance Matrix
| Standard | Requirement | Status |
|----------|-------------|--------|
| ISO/IEC 29148 | Requirements specification | ✅ |
| RFC 8785 | JSON Canonicalization Scheme | ✅ |
| Ed25519 | Digital signatures | ✅ |
| VIBE Coding | No mocks, real implementations | ✅ |

---

# 2. SYSTEM ARCHITECTURE

## 2.1 Trust Hierarchy
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SOMA TRUST ARCHITECTURE                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   CONSTITUTION (The Law)                                                    │
│   ├── SHA-256 Content Hash                                                  │
│   ├── Ed25519 Signature                                                     │
│   └── Immutable JSON Content                                                │
│                          │                                                  │
│                          ▼                                                  │
│   REGISTRY (The Authority)                                                  │
│   ├── Ed25519 Private Signing Key                                           │
│   ├── JCS Canonicalization (RFC 8785)                                       │
│   └── Capsule Certification Pipeline                                        │
│                          │                                                  │
│                          ▼                                                  │
│   CAPSULE (The Agent)                                                       │
│   ├── Soul: System Prompt + Personality + Neuromodulators                   │
│   ├── Body: Capabilities Whitelist + Resource Limits                        │
│   ├── constitution_ref: {id, content_hash}                                  │
│   └── registry_signature: Ed25519 Certification                             │
│                          │                                                  │
│                          ▼                                                  │
│   RUNTIME (The Execution)                                                   │
│   ├── Signature Verification                                                │
│   ├── Constitution Hash Check                                               │
│   └── Policy Enforcement (Egress, HITL, Resources)                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 2.2 Component Map
| Component | Location | Lines | Purpose |
|-----------|----------|-------|---------|
| Constitution Model | `admin/core/models.py:59-93` | 35 | Django ORM for Constitution |
| Capsule Model | `admin/core/models.py:101-152` | 52 | Django ORM for Capsule |
| RegistryService | `services/registry_service.py` | 203 | Ed25519 signing/verification |
| CapsuleEnforcer | `services/common/capsule_enforcer.py` | 442 | Policy enforcement hooks |
| CapsuleStore | `services/common/capsule_store.py` | 111 | Redis-backed persistence |
| Capsule SDK | `admin/agents/services/capsule.py` | 115 | HTTP client for Registry |

---

# 3. CONSTITUTION SUBSYSTEM

## 3.1 Data Model
```python
class Constitution(models.Model):
    id = models.UUIDField(primary_key=True)
    version = models.CharField(max_length=50)  # "1.0.0"
    
    # Cryptographic Proof
    content_hash = models.CharField(max_length=64, unique=True)  # SHA-256
    signature = models.TextField()  # Ed25519 signature
    
    # The Law (Immutable)
    content = models.JSONField()  # VIBE Rules, Ethical Constraints
    
    # State
    is_active = models.BooleanField(default=False)
    activated_at = models.DateTimeField(null=True)
    revoked_at = models.DateTimeField(null=True)
```

## 3.2 Requirements
| ID | Requirement | Priority |
|----|-------------|----------|
| REQ-CONST-001 | Constitution SHALL be immutable once signed | P0 |
| REQ-CONST-002 | Only ONE Constitution may be active at a time | P0 |
| REQ-CONST-003 | Constitution content_hash MUST use SHA-256 | P0 |
| REQ-CONST-004 | Constitution signature MUST use Ed25519 | P0 |
| REQ-CONST-005 | All Capsules MUST reference active Constitution | P0 |

## 3.3 Constitution Content Schema
```json
{
  "version": "1.0.0",
  "name": "SOMA System Constitution",
  "principles": [
    "Agent SHALL NOT deceive the human operator",
    "Agent SHALL respect privacy boundaries",
    "Agent SHALL operate within defined resource limits"
  ],
  "vibe_rules": {
    "no_mocks": true,
    "real_implementations_only": true,
    "complete_type_hints": true
  },
  "ethical_constraints": {
    "max_autonomy_level": 3,
    "require_human_approval_above": 7
  }
}
```

---

# 4. CAPSULE REGISTRY SUBSYSTEM

## 4.1 Data Model
```python
class Capsule(models.Model):
    id = models.UUIDField(primary_key=True)
    name = models.CharField(max_length=255)
    version = models.CharField(max_length=50, default="1.0.0")
    tenant = models.CharField(max_length=255)
    
    # Governance
    constitution = models.ForeignKey(Constitution, on_delete=models.PROTECT)
    registry_signature = models.TextField(null=True)  # Ed25519
    
    # Soul (Identity)
    system_prompt = models.TextField()
    personality_traits = models.JSONField()  # Big 5: 0.0-1.0
    neuromodulator_baseline = models.JSONField()  # Dopamine, Serotonin, etc.
    
    # Body (Capabilities)
    capabilities_whitelist = models.JSONField()  # List of Tool IDs
    resource_limits = models.JSONField()  # wall_clock, concurrency
    
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = [["name", "version", "tenant"]]
```

## 4.2 Requirements
| ID | Requirement | Priority |
|----|-------------|----------|
| REQ-CAP-001 | Capsule SHALL contain Soul + Body + Constitution Ref | P0 |
| REQ-CAP-002 | Certified Capsules are IMMUTABLE (version-on-edit) | P0 |
| REQ-CAP-003 | Capsule MUST bear registry_signature for activation | P0 |
| REQ-CAP-004 | Capsule export SHALL include full signature chain | P0 |
| REQ-CAP-005 | Capsule deletion requires zero active sessions | P1 |

## 4.3 Capsule States
```mermaid
stateDiagram-v2
    [*] --> Draft : Create
    Draft --> Active : Sign & Certify
    Active --> Archived : Soft Delete
    Archived --> Active : Restore
    Archived --> [*] : Hard Delete
    Active --> NewVersion : Edit (Creates Clone)
    NewVersion --> Draft
```

---

# 5. SECURITY & CRYPTOGRAPHY

## 5.1 Cryptographic Stack
| Layer | Algorithm | Key Size | Library |
|-------|-----------|----------|---------|
| Signing | Ed25519 | 256-bit | PyNaCl |
| Hashing | SHA-256 | 256-bit | hashlib |
| Canonicalization | JCS (RFC 8785) | N/A | jcs |
| Encoding | Base64 | N/A | base64 |

## 5.2 Key Management
```python
# Environment Variables (MUST use Vault/Secrets Manager in Production)
SOMA_REGISTRY_PRIVATE_KEY  # Base64-encoded Ed25519 seed (32 bytes)
```

> [!CAUTION]
> In Production, the private key MUST be stored in AWS Secrets Manager or HashiCorp Vault. Environment variables are ONLY acceptable for StandAlone development mode.

## 5.3 Signing Flow
```python
# RegistryService.certify_capsule()

# 1. Construct payload (Soul + Body + Constitution Ref)
payload = {
    "name": capsule.name,
    "version": capsule.version,
    "tenant": capsule.tenant,
    "constitution_ref": {
        "id": str(constitution.id),
        "content_hash": constitution.content_hash
    },
    "soul": {
        "system_prompt": capsule.system_prompt,
        "personality_traits": capsule.personality_traits,
        "neuromodulator_baseline": capsule.neuromodulator_baseline
    },
    "body": {
        "capabilities_whitelist": capsule.capabilities_whitelist,
        "resource_limits": capsule.resource_limits
    }
}

# 2. Canonicalize (RFC 8785 JCS)
canonical_bytes = jcs.canonicalize(payload)

# 3. Sign with Ed25519
signed = signing_key.sign(canonical_bytes, encoder=Base64Encoder)
signature_b64 = signed.signature.decode('utf-8')

# 4. Store signature
capsule.registry_signature = signature_b64
```

## 5.4 Verification Flow
```python
# RegistryService.verify_capsule_integrity()

# 1. Reconstruct canonical payload (exact match of signing)
# 2. Decode signature from Base64
# 3. Verify with Ed25519 public key
verify_key.verify(canonical_bytes, base64.b64decode(registry_signature))
```

## 5.5 Security Requirements
| ID | Requirement | Priority |
|----|-------------|----------|
| REQ-SEC-001 | Capsule signature MUST be verified at every boot | P0 |
| REQ-SEC-002 | Invalid signature SHALL prevent Agent startup | P0 |
| REQ-SEC-003 | Constitution hash mismatch SHALL block execution | P0 |
| REQ-SEC-004 | All signing operations MUST use atomic transactions | P0 |
| REQ-SEC-005 | Audit log MUST record all certification events | P0 |

---

# 6. POLICY ENFORCEMENT

## 6.1 Enforcer Architecture
```python
class CapsuleEnforcer:
    def __init__(self, capsule: CapsuleRecord):
        self.egress = EgressEnforcer(capsule)    # Network policies
        self.resources = ResourceEnforcer(capsule)  # Time/concurrency
        self.hitl = HITLEnforcer(capsule)        # Human approval
        self.export = ExportEnforcer(capsule)    # RL data export
```

## 6.2 Egress Policy
| Mode | Behavior |
|------|----------|
| `open` | All domains allowed (except blocked list) |
| `restricted` | Only whitelisted domains allowed |
| `none` | No network egress permitted |

## 6.3 Resource Limits
| Parameter | Default | Description |
|-----------|---------|-------------|
| `max_wall_clock_seconds` | 300 | Max execution time |
| `max_concurrent_nodes` | 10 | Max parallel tool calls |

## 6.4 HITL Modes
| Mode | Behavior |
|------|----------|
| `none` | Never require human approval |
| `required` | Always require approval |
| `optional` | Require if risk_score > threshold |

## 6.5 Enforcement Requirements
| ID | Requirement | Priority |
|----|-------------|----------|
| REQ-ENF-001 | Tool calls MUST check allowed_tools whitelist | P0 |
| REQ-ENF-002 | Egress MUST be blocked for prohibited domains | P0 |
| REQ-ENF-003 | Wall clock exceeded SHALL terminate execution | P0 |
| REQ-ENF-004 | HITL denials MUST be logged to audit trail | P0 |

---

# 7. UML DIAGRAMS & FLOWS

## 7.1 Capsule Certification Sequence
```mermaid
sequenceDiagram
    participant U as User
    participant C as AgentCapsuleCreator (UI)
    participant V as Validator
    participant R as RegistryService
    participant DB as PostgreSQL
    
    rect rgb(240, 248, 255)
    note right of U: Stage 1: Drafting
    U->>C: Define Soul (Prompt, Traits)
    U->>C: Define Body (Tools, Limits)
    C->>DB: Save Draft Capsule
    end
    
    rect rgb(255, 250, 205)
    note right of U: Stage 2: Validation
    C->>V: Validate Schema
    V-->>C: OK / Errors
    end
    
    rect rgb(230, 230, 250)
    note right of U: Stage 3: Certification
    C->>R: Request Publication
    R->>DB: Load Active Constitution
    R->>R: Bind Constitution Ref
    R->>R: Canonicalize (JCS RFC 8785)
    R->>R: Sign (Ed25519)
    R->>DB: Save registry_signature
    end
    
    rect rgb(224, 255, 255)
    note right of U: Stage 4: Output
    R-->>C: Return Certified Capsule
    C-->>U: "Agent Ready for Activation"
    end
```

## 7.2 Runtime Verification Sequence
```mermaid
sequenceDiagram
    participant U as User
    participant A as AgentService
    participant R as RegistryService
    participant C as CapsuleEnforcer
    participant B as SomaBrain
    
    U->>A: Start Session (CapsuleID)
    A->>A: Load Capsule from DB
    
    A->>R: verify_capsule_integrity()
    
    alt Invalid Signature
        R-->>A: False (SECURITY ALERT)
        A-->>U: ERROR: UNSAFE CAPSULE - BLOCKED
    else Valid Signature
        R-->>A: True
        A->>A: Verify Constitution Hash (Active Match)
        
        alt Constitution Mismatch
            A-->>U: ERROR: STALE CONSTITUTION
        else Valid Constitution
            A->>C: Initialize Enforcers
            C->>C: Start Wall Clock Timer
            A->>B: PUSH Identity (System Prompt)
            B-->>A: Context Ready
            A-->>U: Session Started
        end
    end
```

## 7.3 Tool Execution with Policy Check
```mermaid
sequenceDiagram
    participant A as Agent
    participant E as CapsuleEnforcer
    participant T as ToolExecutor
    participant N as NetworkLayer
    
    A->>E: check_tool_call(tool_name, risk_score, domain)
    
    E->>E: Check prohibited_tools
    alt Tool Prohibited
        E-->>A: DENY
    end
    
    E->>E: Check allowed_tools whitelist
    alt Tool Not Whitelisted
        E-->>A: DENY
    end
    
    E->>E: Check egress policy (if domain)
    alt Domain Blocked
        E-->>A: DENY
    end
    
    E->>E: Check HITL requirements
    alt HITL Required
        E-->>A: REQUIRE_HITL
    else HITL Not Required
        E-->>A: ALLOW
        A->>T: Execute Tool
        T->>N: Make Request (if network)
        N-->>T: Response
        T-->>A: Result
    end
```

## 7.4 Capsule Lifecycle State Machine
```mermaid
stateDiagram-v2
    [*] --> Draft : User Creates Capsule
    
    Draft --> Validating : Submit for Review
    Validating --> Draft : Validation Failed
    Validating --> Certifying : Validation Passed
    
    Certifying --> Active : Registry Signs
    
    Active --> Archived : Soft Delete
    Archived --> Active : Restore
    
    Active --> Editing : User Edits
    Editing --> Draft : Creates New Version (Clone)
    
    Archived --> [*] : Hard Delete (0 sessions)
    
    note right of Active : Immutable
    note right of Draft : Mutable
```

## 7.5 Screen Flow: AgentCapsuleCreator
```mermaid
flowchart TD
    subgraph Entry
        A[Dashboard: My Agents] --> B{New or Edit?}
    end
    
    subgraph Creation
        B -->|New| C[Step 1: Basic Info<br/>Name, Version, Description]
        C --> D[Step 2: Soul Editor<br/>System Prompt, Personality Sliders]
        D --> E[Step 3: Body Editor<br/>Tool Selector, Resource Limits]
        E --> F[Step 4: Review<br/>Constitution Binding, Preview]
    end
    
    subgraph Actions
        F --> G{Publish?}
        G -->|Draft| H[Save as Draft]
        G -->|Publish| I[Registry Certification]
        I --> J{Signature OK?}
        J -->|Yes| K[Agent Active ✓]
        J -->|No| L[Error: Fix Issues]
        L --> E
    end
    
    subgraph Export
        K --> M[Export .capsule.json]
        K --> N[Start Session]
    end
```

---

# 8. 7-PERSONA DEEP ANALYSIS

## 8.1 PhD Developer (Architecture)
| Finding | Severity | Recommendation |
|---------|----------|----------------|
| Ed25519 implementation is correct | ✅ OK | None |
| JCS canonicalization properly imported | ✅ OK | None |
| Constitution FK uses PROTECT | ✅ OK | Prevents orphaned capsules |
| Missing: Version history chain | ⚠️ MEDIUM | Add `parent_id` FK for version lineage |

## 8.2 Security Auditor (Cryptography)
| Finding | Severity | Recommendation |
|---------|----------|----------------|
| Private key in env var | ⚠️ HIGH | Production MUST use Vault/Secrets Manager |
| No key rotation mechanism | ⚠️ MEDIUM | Implement key versioning |
| Signature verified on every boot | ✅ OK | REQ-SEC-001 satisfied |
| Missing: Signature revocation list | ⚠️ LOW | Add CRL for compromised capsules |

## 8.3 DevOps Engineer (Infrastructure)
| Finding | Severity | Recommendation |
|---------|----------|----------------|
| CapsuleStore uses Redis | ✅ OK | Fast lookups |
| PostgreSQL for models | ✅ OK | ACID compliance |
| Missing: Health check for Registry | ⚠️ LOW | Add `/health` endpoint |
| No metrics on signing ops | ⚠️ LOW | Add Prometheus counters |

## 8.4 QA Lead (Testing)
| Finding | Severity | Recommendation |
|---------|----------|----------------|
| No unit tests for RegistryService | ❌ HIGH | Create `test_registry_service.py` |
| No integration tests for certification | ❌ HIGH | Test full signing flow |
| CapsuleEnforcer has good coverage | ✅ OK | Enforcement logic tested |

## 8.5 PM (Features)
| Finding | Severity | Recommendation |
|---------|----------|----------------|
| AgentCapsuleCreator UI missing | ❌ HIGH | Implement Lit 3 components |
| No capsule export/import UI | ⚠️ MEDIUM | Add export button |
| Version comparison missing | ⚠️ LOW | Add diff view between versions |

## 8.6 Data Engineer (Schema)
| Finding | Severity | Recommendation |
|---------|----------|----------------|
| Constitution has proper indexes | ✅ OK | `is_active`, `content_hash` indexed |
| Capsule unique constraint correct | ✅ OK | `[name, version, tenant]` |
| Missing: Audit log for changes | ⚠️ MEDIUM | Add Django signals for AuditLog |

## 8.7 UX Specialist (Interface)
| Finding | Severity | Recommendation |
|---------|----------|----------------|
| No UI for capsule creation | ❌ HIGH | Build AgentCapsuleCreator |
| Constitution binding should be read-only | ✅ Designed | Prevents confusion |
| Need visual signature status indicator | ⚠️ MEDIUM | Show ✓/✗ badge |

---

# 9. RECOMMENDATIONS

## 9.1 Critical (P0)
| ID | Recommendation | Effort |
|----|----------------|--------|
| REC-001 | Implement AgentCapsuleCreator UI (Lit 3) | 5 days |
| REC-002 | Add unit tests for RegistryService | 1 day |
| REC-003 | Move private key to Vault in Production | 0.5 days |
| REC-004 | Add version parent_id for lineage tracking | 0.5 days |

## 9.2 High (P1)
| ID | Recommendation | Effort |
|----|----------------|--------|
| REC-005 | Implement key rotation mechanism | 2 days |
| REC-006 | Add Prometheus metrics for signing ops | 0.5 days |
| REC-007 | Add Django signals for AuditLog | 0.5 days |
| REC-008 | Create capsule export/import endpoints | 1 day |

## 9.3 Medium (P2)
| ID | Recommendation | Effort |
|----|----------------|--------|
| REC-009 | Add certificate revocation list (CRL) | 1 day |
| REC-010 | Add version diff view in UI | 1 day |
| REC-011 | Add Registry health endpoint | 0.25 days |

---

# 10. IMPLEMENTATION ROADMAP

## Phase 1: Core Security (Week 1)
- [ ] REC-002: Unit tests for RegistryService
- [ ] REC-003: Vault integration for production keys
- [ ] REC-004: Add parent_id to Capsule model

## Phase 2: UI Development (Weeks 2-3)
- [ ] REC-001: AgentCapsuleCreator components
  - [ ] `<capsule-identity-panel>` (Soul editor)
  - [ ] `<capsule-capability-panel>` (Body editor)
  - [ ] `<capsule-governance-panel>` (Constitution display)
  - [ ] `<capsule-preview-card>` (Summary view)

## Phase 3: Operations (Week 4)
- [ ] REC-005: Key rotation mechanism
- [ ] REC-006: Prometheus metrics
- [ ] REC-007: AuditLog signals
- [ ] REC-008: Export/Import API

---

**END OF DOCUMENT**

*SRS-CAPSULE-SYSTEM-ISO-001 v1.0.0*
*Generated by 7-Persona VIBE Analysis Team*
# SRS-CAPSULE-REGISTRY-ISO.md
**Software Requirements Specification (ISO/IEC/IEEE 29148:2018 Compatible)**
**Project:** SomaAgent01 - Capsule Registry & Constitution
**Version:** 2.2.0 (AgentCapsuleCreator Expanded)
**Date:** 2026-01-03
**Status:** DRAFT (Waiting Sign-off)

---

## 1. Introduction

### 1.1 Purpose
The purpose of this document is to definitively specify the architecture, data models, and operational flows for the **SomaAgent01 Capsule Registry** and the **System Constitution**. This specification serves as the binding "Covenant" between the Human Operator and the Artificial Intelligence, establishing the immutable laws and the atomic units (Capsules) that operate under them.

### 1.2 Scope
This standard encompasses:
1.  **The Constitution**: A cryptographic, immutable regulatory framework governing all Agent actions.
2.  **The Capsule**: The atomic, portable unit of Agent Identity (Soul) and Capability (Body).
3.  **The Registry**: The centralized, authoritative, and **cryptographically secured** management system for Capsules.
4.  **The AgentCapsuleCreator**: The Lit 3-based visual administration interface.
5.  **Governance**: The cryptographic signing and enforcement of the Constitution.

---

## 2. Terms and Definitions

*   **Constitution**: The supreme regulatory document (signed JSON) defining the ethical and operational boundaries.
*   **Capsule**: A versioned, portable object composed of a Persona ("Soul") and a Tool/Policy Configuration ("Body").
*   **Registry**: The centralized system responsible for storing, serving, and **Certifying** Capsules.
*   **Certified Capsule**: A Capsule that has been cryptographically signed by the Registry Authority.
*   **Provenance**: The unbreakable chain of trust from Constitution -> Registry -> Capsule.

---

## 3. System Architecture & Models

### 3. Systems Architecture & Models

#### 3.0 Architecture Overview (UML)
```mermaid
classDiagram
    class Constitution {
        +UUID id
        +String hash
        +String signature
        +JSON content
        +verify()
    }
    class Registry {
        -PrivateKey key
        +sign(Capsule)
        +verify(Capsule)
    }
    class Capsule {
        +UUID id
        +String constitution_ref
        +String registry_signature
        +Soul soul
        +Body body
    }
    class SomaBrain {
        +RuntimeMemory
        +execute()
    }
    
    Constitution "1" <.. "N" Capsule : Governs
    Registry "1" --> "N" Capsule : Certifies
    Capsule "1" --> "1" SomaBrain : Pushes Identity To
```

### 3.1 The Constitution (The Law)
**REQ-CONST-001 [Supremacy]**: The Constitution SHALL be the supreme regulator.
**REQ-CONST-002 [Immutability]**: The Constitution Object SHALL be immutable once signed.
**REQ-CONST-003 [Integrity]**: The Constitution SHALL be cryptographically signed (SHA-256) to prevent tampering.

### 3.2 The Capsule (The Agent)
**REQ-CAP-001 [Atomicity]**: The Capsule SHALL contain *all* necessary information (Soul + Body + Constitution Ref).
**REQ-CAP-002 [Constitution Integration]**: Every Capsule MUST reference the `constitution_id` and `constitution_hash`.
**REQ-CAP-003 [Portability]**: The Capsule SHALL be exportable as a single JSON file.
**REQ-CAP-004 [Certification]**: Every Capsule MUST bear a `registry_signature` verifying it was issued by an Authorized Registry.

#### 3.2.1 Capsule Model Schema
| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Unique Identifier |
| `constitution_ref` | String | Reference to the governing Constitution |
| `registry_signature` | String | **NEW**: Cryptographic signature of the Registry |
| `system_prompt` | String | The "Soul" - Base Instruction Set |
| `allowed_tools` | List | The "Body" - capability whitelist |

---

## 4. Security & Governance

### 4.1 The Unhackable Covenant
**REQ-SEC-001**: The Constitution Hash MUST be validated on every Agent Startup.
**REQ-SEC-002**: If the Constitution Hash does not match, the Agent SHALL REFUSE TO BOOT.

### 4.2 Registry Certification (Root of Trust)
**REQ-SEC-003 [Registry Authority]**: The Registry SHALL possess a private signing key (`REGISTRY_KEY`).
**REQ-SEC-004 [Capsule Signing]**: Upon publication, the Registry SHALL sign the Capsule's content hash with `REGISTRY_KEY`.
**REQ-SEC-005 [Safety Verification]**: Before loading ANY Capsule, the Agent Service SHALL:
1.  Verify the `registry_signature` using the Registry's Public Key.
2.  Verify the `constitution_ref` matches the Active Constitution.
3.  **Reject** any Capsule that fails these checks as "Unsafe".

### 4.2 Capsule Creation Process (The Birth Protocol)

**PRC-CAP-001 [Objective]**: To transform a User's intent into a Certified, Immutable, and Executable Agent Capsule.

**PRC-CAP-002 [Pre-Conditions]**:
1.  System MUST have an **Active Constitution**.
2.  Registry MUST have a loaded **Private Signing Key**.
3.  User MUST be authenticated.

**PRC-CAP-003 [Inputs]**:
*   **Soul Definition**: System Prompt, Traits, Neuromodulators.
*   **Body Definition**: Capability Whitelist, Resource Limits.
*   **Metadata**: Name, Semantic Version.

**PRC-CAP-004 [Process Flow]**:
1.  **Drafting Stage**: User defines Soul and Body in `AgentCapsuleCreator`. State is "Draft".
2.  **Validation Stage**: System validates User Input against the `CapsuleSchema` (JSON Schema). Errors block progress.
3.  **Binding Stage**: System injects the `constitution_ref` (ID + Hash) of the Active Constitution.
4.  **Normalization Stage**: System canonicalizes the JSON (JCS) to strictly order keys and remove whitespace.
5.  **Signing Stage**: Registry computes SHA-256 of the normalized payload and signs it with `REGISTRY_KEY` (Ed25519).
6.  **Certification Stage**: System appends `registry_signature` and sets status to "Active".

**PRC-CAP-005 [Outputs]**:
*   A **Certified Capsule Object** (JSON).
*   An **Audit Log Entry** (Process Completion).

**PRC-CAP-006 [Visual Flow]**:
```mermaid
sequenceDiagram
    participant U as User
    participant C as Creator (UI)
    participant V as Validator
    participant R as Registry
    
    rect rgb(240, 248, 255)
    note right of U: Stage 1: Drafting
    U->>C: Input Identity & Tools
    end
    
    rect rgb(255, 250, 205)
    note right of U: Stage 2: Validation
    C->>V: Validate Schema()
    V-->>C: OK / Errors
    end
    
    rect rgb(230, 230, 250)
    note right of U: Stage 3-5: Certification
    C->>R: Request Publication
    R->>R: Bind Constitution
    R->>R: Canonicalize (JCS)
    R->>R: Sign (Ed25519)
    end
    
    rect rgb(224, 255, 255)
    note right of U: Stage 6: Output
    R-->>C: Return Certified Capsule
    C-->>U: "Agent Ready"
    end
```

### 4.3 Capsule Lifecycle Management (Update & Deletion Protocols)

**PRC-LIF-001 [Immutability Principle]**:
A Certified Capsule (`registry_signature` present) is **IMMUTABLE**. It cannot be modified.
*   **Update Flow**: Editing a Capsule creates a new **Version** (e.g., v1.0.0 -> v1.1.0).
*   **Version Chain**: The new version references the `parent_id` of the original.

**PRC-LIF-002 [Soft Deletion (Archive)]**:
*   **Action**: User clicks "Delete" on an Active Capsule.
*   **System Behavior**: Sets `is_active = False`.
*   **Consequence**: Capsule is hidden from "New Session" lists but remains valid for historical audit.
*   **Reversibility**: Can be un-archived.

**PRC-LIF-003 [Hard Deletion (Purge)]**:
*   **Condition**: Only allowed if the Capsule has **Zero Runtime Sessions** OR User has "Eye of God" permission.
*   **Action**: Permanent removal from Registry and Disk.
*   **Constraint**: Cannot delete a Capsule referenced as a `parent` by others.

**PRC-LIF-004 [Visual Lifecycle]**:
```mermaid
stateDiagram-v2
    [*] --> Draft
    Draft --> Active : Sign & Certify
    Active --> Archived : Soft Delete
    Archived --> Active : Restore
    Archived --> [*] : Hard Delete (If safe)
    Active --> [*] : Hard Delete (Forbidden usually)
```

### 4.4 Runtime Execution (The Life)
```mermaid
sequenceDiagram
    participant U as User (Chat)
    participant A as AgentService
    participant C as Capsule (Stored)
    participant B as SomaBrain (Runtime)
    
    U->>A: Start Session (CapsuleID)
    A->>C: Load Definition
    A->>A: Verify Registry Signature
    alt Invalid Signature
        A-->>U: ERROR: UNSAFE CAPSULE
    else Valid Signature
        A->>A: Verify Constitution Hash
        A->>B: PUSH Identity (System Prompt, Traits)
        B-->>A: Context Ready
        A-->>U: Session Started
    end
```
1.  **Load**: Agent Service loads `Capsule` from Registry.

### 4.4 Audit Trail
**REQ-AUD-001**: All Capsule creations, modifications, and deletions SHALL be logged to the immutable `AuditLog`.

### 4.5 Data Provenance & Inheritance Protocol

**PRC-DAT-001 [The Pull Protocol]**:
*   **Source**: The **Registry** is the only entity authorized to "Pull" data into a Capsule Definition.
*   **Content**: Registry pulls standard schemas (e.g., Tool Definitions) from the **Master Library** to ensure compatibility.
*   **Modification**: The Registry *copies* this data into the Capsule. Future changes to the Master Library do **NOT** affect certified Capsules (Version Locking).

**PRC-DAT-002 [The Push Protocol]**:
*   **Direction**: **One-Way (Registry -> Agent)**.
*   **Content**: The **Registry** pushes the *Identity* (Soul) and *Constitution* to the Agent at Runtime.
*   **Constraint**: The Agent CANNOT push data back to modify its own Capsule Definition. Runtime learning is stored in **SomaBrain Memory**, not the Capsule.

**PRC-DAT-003 [Verification & Control]**:
*   **Verifier**: The **Agent Service Bootloader**.
*   **Mechanism**:
    1.  **Integrity**: Validates `Capsule.registry_signature` (Ed25519) to ensure no bits flipped.
    2.  **Legality**: Validates `Capsule.constitution_ref` matches the Active Constitution Hash.
*   **Failure**: If verification fails, the boot process **HALTS** immediately with `SECURITY_VIOLATION`.

This document represents the COMPLETE and FINAL architectural specification for the Soma Capsule Registry.

### 5.1 Overview
The **AgentCapsuleCreator** is the designated User Interface for the creation, modification, validation, and publication of Soma Agent Capsules. It serves as the primary touchpoint for defining the "Soul" and "Body" of an agent.

### 5.2 Technology Stack
**REQ-UI-TECH-001**: All components SHALL be built using **Lit 3** (Web Components).
**REQ-UI-TECH-002**: State management SHALL use signals/observables to ensure reactivity without heavy framework overhead.
**REQ-UI-TECH-003**: The interface SHALL default to the "Clean Light Theme" VIBE standard.

### 5.3 Functional Requirements

#### 5.3.1 Creator Canvas (The Workspace)
**REQ-ACC-001 [Layout]**: The Canvas SHALL present a unified view of the Capsule being drafted, split into logical domains (Identity, Capability, Governance).
**REQ-ACC-002 [Real-time Validation]**: The Canvas SHALL validate fields in real-time against the Schema (REQ-CAP-001) and provide immediate visual feedback.
**REQ-ACC-003 [Draft Persistence]**: The Canvas SHALL automatically save the current state to LocalStorage (`capsule_draft_{id}`) to prevent data loss.

#### 5.3.2 The Soul Editor (Identity)
**REQ-ACC-SOUL-001 [Prompt Engineering]**: The Creator SHALL provide a multi-line, syntax-highlighted editor for the `system_prompt`.
**REQ-ACC-SOUL-002 [Personality Matrix]**: The Creator SHALL provide visual sliders (0.0 - 1.0) for the Big Five personality traits (Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism).
**REQ-ACC-SOUL-003 [Neuromodulators]**: The Creator SHALL allow configuration of baseline chemical states (Dopamine, Serotonin) via visual gauges.

#### 5.3.3 The Body Editor (Capabilities)
**REQ-ACC-BODY-001 [Tool Selector]**: The Creator SHALL display a searchable list of available Tools and MCP Servers (fetched from Registry).
**REQ-ACC-BODY-002 [Whitelist Logic]**: The user SHALL be able to explicitly `Allow` or `Deny` specific tools. Default state is `Deny All`.
**REQ-ACC-BODY-003 [Resource Limits]**: The Creator SHALL provide numeric inputs for `max_wall_clock_seconds` and `max_concurrent_nodes`.

#### 5.3.4 Governance & Publication: The Secure Protocol
**REQ-ACC-GOV-001 [Constitution Binding]**: 
The Creator SHALL display the *Active Constitution* (ID and SHA-256 Hash) that the Capsule will be bound to. This field is Read-Only and serves as the cryptographic anchor for the Agent's legality.

**REQ-ACC-GOV-002 [Secure Publication Pipeline]**: 
The "Publish" action SHALL trigger the Registry API to execute a strict **Canonicalization-Hashing-Signing** pipeline:
1.  **Normalization (JCS)**: The Capsule Payload (Identity + Capabilities) is normalized using **RFC 8785 (JSON Canonicalization Scheme)** to ensure byte-for-byte consistency.
2.  **Constitution Check**: The system validates that `constitution_ref` points to the currently Active Constitution.
3.  **Binding Hash**: A `binding_hash` is computed: `SHA256(NormalizedCapsule + ConstitutionHash)`. This legally binds the Agent to the Law.
4.  **Signing**: The Registry signs the `binding_hash` using its private **Ed25519** key.
5.  **Certification**: The final Capsule Object is sealed with the `registry_signature` and immutable `version`.

**REQ-ACC-GOV-003 [Export Artifact]**: 
The "Export" action SHALL download the full, certified JSON object (`{name}-{version}.capsule.json`). This file MUST contain the `registry_signature` to be valid in any Soma environment.

### 5.4 Component Architecture (Lit 3)
*   `<agent-capsule-creator>`: Root Orchestrator.
*   `<capsule-identity-panel>`: Soul Editor (Prompts/Traits).
*   `<capsule-capability-panel>`: Body Editor (Tools/Limits).
*   `<capsule-governance-panel>`: Constitution & Signing Status.
*   `<capsule-preview-card>`: Visual summary of the Agent.

---

## 6. Implementation Plans

1.  **Phase 1: Foundation**: Create `Constitution` Model.
2.  **Phase 2: Registry Upgrade**: Implement `Capsule` Model with `registry_signature` field.
3.  **Phase 3: Security**: Implement Crypto-Signing Logic (Ed25519 or RSA) in Registry.
4.  **Phase 4: Creator**: Build the Lit 3 `AgentCapsuleCreator` module adhering to Section 5.

This document represents the COMPLETE and FINAL architectural specification for the Soma Capsule Registry.
