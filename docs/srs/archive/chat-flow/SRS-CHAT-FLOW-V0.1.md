# SRS: Chat Flow & Granular Governance V.0.1

**Document ID:** SA01-SRS-CHAT-FLOW-2026-01
**Version:** 0.1
**Status:** DRAFT (Canonical Reference)
**Compliance:** ISO/IEC 29148:2018

---

## 1. Scope

This Software Requirements Specification (SRS) defines the end-to-end flow of the **SomaAgent01 Chat System**, strictly enforcing the **Granular Governance** architecture. It details the runtime interaction between the User, Agent, Capsule, and the underlying Permission System (SpiceDB/OPA), ensuring that every action is Observably Traceable ("Zero-Loss") and Granularly Permitted.

---

## 2. Data Architecture (ER Diagrams)

### 2.1 The "Granular Trinity" & Runtime Session

The runtime context is formed by the intersection of **User (Profile)**, **Agent (Capsule)**, and **Identity (Persona/Role)**.

```mermaid
erDiagram
    User ||--o{ UserPreferences : "has profile"
    User ||--o{ Session : "initiates"

    Session }o--|| Capsule : "binds to"
    Session }o--|| Persona : "adopts"

    Capsule ||--o{ Capability : "possesses (physical)"
    Capsule ||--|| AgentConfig : "configured by"

    %% The Runtime Permission Context
    Session {
        uuid id PK
        uuid user_id FK
        uuid capsule_id FK
        string persona_id FK
        string role_id
        timestamp created_at
    }
```

### 2.2 Configuration Sovereignty (Agent & Tools)

Configuration is strictly database-driven (Rule 91).

```mermaid
erDiagram
    AgentConfig {
        uuid agent_id PK,FK
        uuid chat_model_id FK
        json mcp_servers
        float temperature
    }

    Capability {
        uuid id PK
        string name UK
        json schema "OpenAPI tool definition"
        json config "MCP connection/args"
        bool is_enabled
    }

    Capsule }o--o{ Capability : "M2M (Static Allow)"
```

---

## 3. Functional Flows (Sequence Diagrams)

### 3.1 Phase 1: The Simple Message Loop
**Scenario**: User sends "Hello".

```mermaid
sequenceDiagram
    actor User
    participant API as /api/chat
    participant Session as SessionManager
    participant LLM as LLM Service
    participant Audit as AuditLog

    User->>API: POST "Hello"
    API->>Session: Load(session_id)
    Session->>LLM: Generate(system_prompt + "Hello")
    LLM-->>Session: "Hello! How can I help?"
    Session-->>Audit: Log(UserMsg, AgentMsg)
    API-->>User: 200 OK "Hello!..."
```

---

### 3.2 Phase 2: Granular Discovery (The "Hidden" Layer)
**Scenario**: User asks "What tools do you have?".
**Rule**: Tools forbidden to the User are *removed* from the context.

```mermaid
sequenceDiagram
    participant Builder as PromptBuilder
    participant Cap as Capsule (Body)
    participant Spice as SpiceDB (Auth)
    participant LLM as LLM Context

    Builder->>Cap: Get All Capabilities
    Cap-->>Builder: [CheckStatus, ResetDB, CreateTool]

    loop For Each Tool
        Builder->>Spice: CheckPermission(user, tool)
        alt Allowed
            Spice-->>Builder: OK
            Builder->>LLM: Add Tool Schema
        else Denied
            Spice-->>Builder: DENIED
            Builder->>LLM: SKIP (Invisible)
        end
    end

    Note right of LLM: LLM only sees [CheckStatus].<br/>It does NOT know ResetDB exists.
```

---

### 3.3 Phase 3: Tool Execution (The "Panopticon" Loop)
**Scenario**: Agent tries to call `weather_tool`.
**Rule**: Must pass 4-Phase pipeline + observability.

```mermaid
sequenceDiagram
    participant Agent
    participant Trace as OpenTelemetry
    participant Audit as AuditPublisher
    participant Policy as OPA
    participant Tool as ToolExecutor
    participant Telemetry as TelemetryPub

    Agent->>Trace: StartSpan("exec_tool")

    rect rgb(240, 240, 240)
        Note over Agent, Policy: Governance Pipeline
        Agent->>Policy: Evaluate(User + Context)
        Policy-->>Agent: ALLOW
    end

    Agent->>Audit: Publish("tool.execution.start")

    Agent->>Tool: Execute()
    Tool-->>Agent: Result ("20°C")

    Agent->>Telemetry: Emit Metric ("latency", 200ms)
    Agent->>Audit: Publish("tool.execution.complete")
    Agent->>Trace: EndSpan()
```

---

### 3.4 Phase 4: Dynamic Evolution (The "Genesis" Cycle)
**Scenario**: Agent wants to *create* a new tool `pandas_analyser`.
**Rule**: Requires OS-level permissions first.

```mermaid
sequenceDiagram
    participant Agent
    participant OS as ShellTool
    participant Pkg as PackageManager
    participant Reg as Registry (Capability)

    Note over Agent: Step 1: Access System
    Agent->>OS: Execute("ls -la")
    OS->>Spice: Check(tool:shell:execute)
    Spice-->>OS: ALLOW
    OS-->>Agent: File Listing

    Note over Agent: Step 2: Provisioning
    Agent->>Pkg: Install("pandas")
    Pkg->>Spice: Check(tool:pkg:install)
    Spice-->>Pkg: ALLOW
    Pkg-->>Agent: Installed

    Note over Agent: Step 3: Registration
    Agent->>Reg: CreateCapability("pandas_analyser", config=...)
    Reg->>Spice: Check(tool:create)
    Spice-->>Reg: ALLOW
    Reg-->>Agent: Capability Created (Pending Link)
```

---

## 4. Multimodal Integration
(See `SRS-MULTIMODAL-2025-12` for full specs)

The Agent's Multimodal Model is defined in `Capsule.image_model`, `Capsule.voice_model`, etc.

**Execution Flow**:
1.  **Request**: `GenerateImage("Sunset")`
2.  **Lookup**: `Capsule.image_model_id` -> `LLMModelConfig`
3.  **Execute**: Via `MultimodalExecutor` (governed by same Trace/Audit loop).

---

## 5. Security & Governance Matrix

| Action | Resource | Permission Required | Failure Mode |
|--------|----------|---------------------|--------------|
| **See Tool** | Tool Definition | `view` (Implicitly checked at discovery) | Tool Hidden (Invisible) |
| **Run Tool** | Tool Execution | `execute` | PermissionDenied Audit Event |
| **Run Shell** | OS Shell | `tool:shell:execute` | Execution Blocked |
| **Install Pkg** | PackageManager | `tool:package_manager:install` | Installation Blocked |
| **Create Tool** | Capability Registry | `tool:create` | Creation Denied |

---

## 6. Observability Requirements

Every interaction MUST produce:
1.  **Trace ID**: Propagated from API -> Agent -> Tool -> Audit.
2.  **Audit Record**: Stored in Kafka (`audit.events`) or fallback DB.
3.  **Telemetry**: Metrics for billing and usage monitoring.

**End of Specification**
