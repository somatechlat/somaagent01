# Settings Persistence Requirements

## REQ-PERSIST-001: Feature Flags Database Persistence
**Priority:** HIGH  
**Status:** NOT IMPLEMENTED  
**Category:** Configuration Management

### Problem Statement
Currently, 14 feature flags are read-only from environment variables (`SA01_FEATURE_PROFILE`, `SA01_ENABLE_*`). These cannot be changed via UI and require container restart.

### Current State
```bash
# Environment variables only:
SA01_FEATURE_PROFILE=enhanced
SA01_ENABLE_sse_enabled=true
SA01_ENABLE_semantic_recall=true
SA01_ENABLE_browser_support=true
# ... 11 more flags
```

**Storage:** Environment variables only (not persisted)  
**Impact:** No UI control, requires restart, not tenant-specific

### Required Implementation

#### 1. Database Schema
```sql
CREATE TABLE feature_flags (
    id SERIAL PRIMARY KEY,
    key TEXT UNIQUE NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT false,
    profile_override TEXT CHECK (profile_override IN ('minimal', 'standard', 'enhanced', 'max')),
    tenant TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_feature_flags_tenant ON feature_flags(tenant, key);
```

#### 2. Store Implementation
**File:** `services/common/feature_flags_store.py`
```python
class FeatureFlagsStore:
    async def get_flags(self, tenant: str) -> dict:
        """Get all feature flags for tenant."""
        pass
    
    async def set_flag(self, tenant: str, key: str, enabled: bool) -> bool:
        """Set feature flag."""
        pass
    
    async def get_profile(self, tenant: str) -> str:
        """Get feature profile (minimal/standard/enhanced/max)."""
        pass
```

#### 3. UI Integration
Add new section to `ui_settings`:
```json
{
  "id": "feature_flags",
  "tab": "system",
  "title": "Feature Flags",
  "description": "Enable/disable system features",
  "fields": [
    {"id": "profile", "title": "Feature Profile", "type": "select", 
     "options": ["minimal", "standard", "enhanced", "max"]},
    {"id": "sse_enabled", "title": "Server-Sent Events", "type": "toggle"},
    {"id": "semantic_recall", "title": "Semantic Memory Recall", "type": "toggle"},
    {"id": "browser_support", "title": "Browser Automation", "type": "toggle"}
    // ... 11 more flags
  ]
}
```

#### 4. Agent Reload Trigger
```python
# On flag change:
await agent_manager.reload_agent(tenant_id)
```

### Acceptance Criteria
- [ ] `feature_flags` table created and accessible
- [ ] UI exposes all 14 feature flags
- [ ] Changes persist to PostgreSQL
- [ ] Environment variables override database values
- [ ] Agent reloads on flag change (< 5s)
- [ ] Multi-tenant support (flags per tenant)

---

## REQ-PERSIST-002: AgentConfig UI Exposure
**Priority:** MEDIUM  
**Status:** NOT IMPLEMENTED  
**Category:** Configuration Management

### Problem Statement
5 AgentConfig settings are currently code-level only (`profile`, `knowledge_subdirs`, `memory_subdir`, `code_exec_ssh_*`, `additional`). These cannot be changed without modifying code.

### Current State
```python
# AgentConfig (code-level only):
@dataclass
class AgentConfig:
    profile: str = "enhanced"
    memory_subdir: str = ""
    knowledge_subdirs: list[str] = ["default", "custom"]
    code_exec_ssh_enabled: bool = True
    code_exec_ssh_addr: str = "localhost"
    code_exec_ssh_port: int = 55022
    code_exec_ssh_user: str = "root"
    # ... ssh_pass already in Vault
```

**Storage:** Python dataclass (not persisted)  
**Impact:** No UI control, hardcoded defaults

### Required Implementation

#### 1. Add to ui_settings
Extend `ui_settings` JSONB with new section:
```json
{
  "id": "agent_config",
  "tab": "system",
  "title": "Agent Configuration",
  "description": "Core agent behavior settings",
  "fields": [
    {"id": "profile", "title": "Agent Profile", "type": "select",
     "options": ["minimal", "standard", "enhanced", "max"], 
     "value": "enhanced"},
    {"id": "knowledge_subdirs", "title": "Knowledge Directories", 
     "type": "json", "value": ["default", "custom"]},
    {"id": "memory_subdir", "title": "Memory Subdirectory", 
     "type": "text", "value": ""},
    {"id": "code_exec_ssh_enabled", "title": "SSH Code Execution", 
     "type": "toggle", "value": true},
    {"id": "code_exec_ssh_addr", "title": "SSH Host", 
     "type": "text", "value": "localhost"},
    {"id": "code_exec_ssh_port", "title": "SSH Port", 
     "type": "number", "value": 55022},
    {"id": "code_exec_ssh_user", "title": "SSH User", 
     "type": "text", "value": "root"}
  ]
}
```

#### 2. AgentConfig Loader
```python
# Load from PostgreSQL instead of defaults:
async def load_agent_config(tenant: str) -> AgentConfig:
    settings = await ui_settings_store.get("global")
    agent_config_section = find_section(settings, "agent_config")
    
    return AgentConfig(
        profile=get_field(agent_config_section, "profile", "enhanced"),
        knowledge_subdirs=get_field(agent_config_section, "knowledge_subdirs", ["default"]),
        memory_subdir=get_field(agent_config_section, "memory_subdir", ""),
        code_exec_ssh_enabled=get_field(agent_config_section, "code_exec_ssh_enabled", True),
        # ...
    )
```

#### 3. Validation
```python
# Validate knowledge subdirectories exist:
async def validate_knowledge_subdirs(subdirs: list[str]) -> bool:
    for subdir in subdirs:
        path = Path(f"/knowledge/{subdir}")
        if not path.exists():
            raise ValueError(f"Knowledge subdirectory '{subdir}' does not exist")
    return True
```

### Acceptance Criteria
- [ ] UI exposes AgentConfig section with 7 fields
- [ ] Settings persist to `ui_settings` JSONB
- [ ] Agent initialization reads from database
- [ ] Directory path validation implemented
- [ ] Changes require agent reload
- [ ] Backward compatible with existing agents

---

## Implementation Summary

### Settings Persistence Status
**Total Settings:** 100+  
**Currently Persisted:** 80 (80%)  
**Remaining:** 20 (20%)

| Storage | Settings | Status |
|---------|----------|--------|
| PostgreSQL `ui_settings` | 60 | ✅ ACTIVE |
| Vault | 10 | ✅ ACTIVE |
| Environment (read-only) | 14 | ⚠️ REQ-PERSIST-001 |
| Code-level (no persistence) | 5 | ⚠️ REQ-PERSIST-002 |

### Dependencies
- REQ-PERSIST-001 depends on: PostgreSQL, Agent reload mechanism
- REQ-PERSIST-002 depends on: `ui_settings_store.py` extension

### Related Documents
- `COMPLETE_AGENT_SETTINGS_CATALOG.md` - Full settings list
- `services/common/ui_settings_store.py` - Current implementation
- `services/common/unified_secret_manager.py` - Vault integration
