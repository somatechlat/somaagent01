# 📊 COMPLETE DATA MODELS
## All somaAgent01 Entity Relationships

---

## 1. PERSONA SYSTEM

### Persona Entity

```mermaid
erDiagram
    PERSONA {
        string persona_id PK
        string tenant_id FK
        string display_name
        string description
        text system_prompt
        jsonb neuromodulators
        jsonb adaptation_state
        jsonb metadata
        timestamp created_at
        timestamp updated_at
    }
    
    TENANT {
        string tenant_id PK
        string name
        jsonb config
        boolean active
    }
    
    MEMORY {
        uuid memory_id PK
        string persona_id FK
        string session_id
        string tenant_id FK
        text content
        jsonb metadata
        vector embedding
        float salience_score
        timestamp created_at
    }
    
    SESSION {
        string session_id PK
        string persona_id FK
        string tenant_id FK
        jsonb metadata
        timestamp created_at
        timestamp updated_at
    }
    
    PERSONA ||--o{ MEMORY : "has"
    PERSONA ||--o{ SESSION : "runs"
    TENANT ||--o{ PERSONA : "owns"
    TENANT ||--o{ MEMORY : "isolates"
```

---

## 2. CAPSULE SYSTEM

### Capsule Entity

```mermaid
erDiagram
    CAPSULE {
        string capsule_id PK
        string name
        string description
        string version
        string author
        string category
        jsonb manifest
        boolean installed
        int downloads
        float rating
        string tenant_id FK
        timestamp created_at
        timestamp updated_at
    }
    
    CAPSULE_DEPENDENCY {
        uuid id PK
        string capsule_id FK
        string depends_on_id FK
        string version_constraint
    }
    
    TOOL {
        string tool_name PK
        string capsule_id FK
        string file_path
        string class_name
        jsonb schema
        boolean enabled
        jsonb settings
    }
    
    PROMPT_TEMPLATE {
        uuid id PK
        string capsule_id FK
        string template_name
        text template_content
        jsonb variables
    }
    
    CAPSULE ||--o{ CAPSULE_DEPENDENCY : "requires"
    CAPSULE ||--o{ TOOL : "provides"
    CAPSULE ||--o{ PROMPT_TEMPLATE : "includes"
```

---

## 3. SETTINGS SYSTEM

### Settings Entities

```mermaid
erDiagram
    UI_SETTINGS {
        string key PK
        string tenant_id FK
        jsonb value
        timestamp updated_at
    }
    
    AGENT_SETTINGS {
        uuid id PK
        string tenant_id FK
        string persona_id FK
        string setting_key
        jsonb setting_value
        string storage_type
        timestamp created_at
        timestamp updated_at
    }
    
    MODEL_CONFIG {
        uuid id PK
        string model_type
        string provider
        string model_name
        string base_url
        int context_length
        int rpm
        int tpm
        jsonb kwargs
        boolean vision
        string tenant_id FK
    }
    
    FEATURE_FLAG {
        string flag_key PK
        boolean enabled
        string profile
        string tenant_id FK
    }
    
    TENANT ||--o{ UI_SETTINGS : "has"
    TENANT ||--o{ AGENT_SETTINGS : "configures"
    TENANT ||--o{ MODEL_CONFIG : "uses"
    TENANT ||--o{ FEATURE_FLAG : "controls"
```

---

## 4. SESSION & EVENTS SYSTEM

### Session Events (Event Sourcing)

```mermaid
erDiagram
    SESSION_ENVELOPE {
        string session_id PK
        string persona_id FK
        string tenant_id FK
        jsonb metadata
        timestamp created_at
        timestamp updated_at
    }
    
    SESSION_EVENT {
        bigint id PK
        string session_id FK
        string event_type
        jsonb payload
        timestamp created_at
    }
    
    ATTACHMENT {
        bigint id PK
        string session_id FK
        string tenant_id FK
        string persona_id FK
        string filename
        string mime_type
        bigint size
        string sha256
        string status
        text quarantine_reason
        bytea content
        timestamp created_at
    }
    
    SESSION_ENVELOPE ||--o{ SESSION_EVENT : "contains"
    SESSION_ENVELOPE ||--o{ ATTACHMENT : "has"
```

---

## 5. TOOL EXECUTION SYSTEM

### Tool Execution Entities

```mermaid
erDiagram
    TOOL_EXECUTION {
        uuid execution_id PK
        string session_id FK
        string persona_id FK
        string tenant_id FK
        string tool_name
        jsonb arguments
        jsonb result
        string status
        float duration_seconds
        timestamp started_at
        timestamp completed_at
    }
    
    TOOL_AUDIT {
        uuid audit_id PK
        string execution_id FK
        string action
        string resource
        jsonb context
        string result
        timestamp created_at
    }
    
    DEAD_LETTER_QUEUE {
        uuid id PK
        string topic
        jsonb payload
        text error_message
        int retry_count
        timestamp created_at
        timestamp last_retry_at
    }
    
    TOOL_EXECUTION ||--o{ TOOL_AUDIT : "logged_in"
```

---

## 6. AGENTSKIN SYSTEM

### AgentSkin Entities

```mermaid
erDiagram
    AGENT_SKIN {
        uuid id PK
        string name UNIQUE
        string description
        string version
        string author
        string license
        text[] tags
        jsonb variables
        string preview_url
        int downloads
        decimal rating
        boolean active
        string tenant_id FK
        timestamp created_at
        timestamp updated_at
    }
    
    SKIN_RATING {
        uuid id PK
        uuid skin_id FK
        string user_id
        int rating
        text review
        timestamp created_at
    }
    
    AGENT_SKIN ||--o{ SKIN_RATING : "has"
```

---

## 7. COMPLETE SYSTEM OVERVIEW

### All Systems Integration

```mermaid
erDiagram
    TENANT ||--o{ PERSONA : "owns"
    TENANT ||--o{ SESSION_ENVELOPE : "manages"
    TENANT ||--o{ UI_SETTINGS : "configures"
    TENANT ||--o{ CAPSULE : "installs"
    TENANT ||--o{ AGENT_SKIN : "uses"
    
    PERSONA ||--o{ SESSION_ENVELOPE : "runs"
    PERSONA ||--o{ MEMORY : "stores"
    PERSONA ||--o{ AGENT_SETTINGS : "customizes"
    
    SESSION_ENVELOPE ||--o{ SESSION_EVENT : "records"
    SESSION_ENVELOPE ||--o{ ATTACHMENT : "uploads"
    SESSION_ENVELOPE ||--o{ TOOL_EXECUTION : "triggers"
    
    CAPSULE ||--o{ TOOL : "provides"
    TOOL ||--o{ TOOL_EXECUTION : "executes"
    
    TOOL_EXECUTION ||--o{ TOOL_AUDIT : "audits"
```

---

## 8. STORAGE DISTRIBUTION

### Data Storage by System

| Entity | Storage | Reason |
|--------|---------|--------|
| **Persona** | SomaBrain | Cognitive state, neuromodulation |
| **Memory** | SomaBrain | Vector embeddings, semantic search |
| **Session Events** | PostgreSQL | Event sourcing, full history |
| **Attachments** | PostgreSQL (BYTEA) | Direct blob storage |
| **UI Settings** | PostgreSQL | Non-sensitive config |
| **Agent Settings (secrets)** | Vault | API keys, passwords |
| **Capsules** | In-Memory → PostgreSQL | Plugin metadata |
| **AgentSkins** | PostgreSQL | Theme variables |
| **Tool Executions** | PostgreSQL | Audit trail |
| **Session Cache** | Redis | Fast metadata access |
| **Feature Flags** | Environment | Deployment config |

---

## 9. RELATIONSHIPS SUMMARY

**Total Entities:** 20+  
**Storage Systems:** 4 (PostgreSQL, SomaBrain, Vault, Redis)  
**Key Patterns:**
- Multi-tenancy via `tenant_id`
- Persona isolation via `persona_id`
- Event sourcing for sessions
- Vector storage for memories
- BLOB storage for attachments

**All diagrams use Mermaid ER format for consistency!** 📊
