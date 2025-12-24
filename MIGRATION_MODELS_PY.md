# models.py Migration Strategy

## Current State Analysis

**File:** `/models.py` (1,247 lines)
**Purpose:** Custom LiteLLM wrapper with LangChain integration
**Imports models.py (6 files):**
1. `agent.py` - `import models`
2. `initialize.py` - `import models`
3. `preload.py` - `import models`
4. `services/common/agent_config_loader.py` - `from models import ModelConfig, ModelType`
5. `python/helpers/memory.py` - `import models`
6. `python/somaagent/agent_context.py` - `import models`
7. `python/somaagent/agent_config_loader.py` - `import models`
8. `python/somaagent/response_generator.py` - `import models`

## File Contents Breakdown

### Core Classes (Django ORM Candidates)
- `ModelType(Enum)` - CHAT, EMBEDDING
- `ModelConfig` - Model configuration dataclass

### LLM Wrapper Classes (Django Service Layer)
- `LiteLLMChatWrapper` - LangChain SimpleChatModel wrapper
- `ChatGenerationResult` - Streaming result parser
- `LLMNotConfiguredError` - Custom exception

### Utility Functions (Django Utils or Remove)
- `get_api_key()` - Uses UnifiedSecretManager
- `get_rate_limiter()` - Rate limiting logic
- `apply_rate_limiter()` - Async rate limiter
- `_parse_chunk()` - Chat chunk parsing
- `turn_off_logging()` - LiteLLM logging config

## CANNOT DELETE YET - Dependencies

**Blocker:** 8 files actively import this module. 

**Migration Order Required:**
1. Create Django models for `ModelConfig`, `ModelType`
2. Create Django service layer for LLM operations  
3. Update all 8 importing files to use new Django imports
4. Delete `models.py` only after all imports removed

## Recommended Django Structure

```
admin/llm/
├── __init__.py
├── models.py          # ModelConfig, ModelType as Django models
├── services/
│   ├── __init__.py
│   ├── litellm_client.py    # LiteLLMChatWrapper
│   ├── rate_limiter.py      # Rate limiting
│   └── api_keys.py          # API key management
└── exceptions.py      # LLMNotConfiguredError
```

## Action Plan

### Step 1: Create Django LLM App
```bash
cd admin && mkdir -p llm/services
```

### Step 2: Migrate Core Models
```python
# admin/llm/models.py
from django.db import models

class ModelType(models.TextChoices):
    CHAT = "Chat"
    EMBEDDING = "Embedding"

class ModelConfiguration(models.Model):
    """Replaces ModelConfig dataclass"""
    type = models.CharField(max_length=20, choices=ModelType.choices)
    provider = models.CharField(max_length=100)
    name = models.CharField(max_length=200)
    api_base = models.URLField(blank=True)
    ctx_length = models.IntegerField(default=0)
    # ... etc
```

### Step 3: Create Service Layer
Move LLM wrapper logic to `admin/llm/services/litellm_client.py`

### Step 4: Update Imports (8 files)
Replace `import models` with `from admin.llm.models import ModelType, ModelConfiguration`
Replace `import models` with `from admin.llm.services import LiteLLMClient`

### Step 5: Delete models.py
Only after all 8 files updated and tested

## Estimated Effort
- **Days:** 3-4 days
- **Risk:** HIGH - Core LLM functionality
- **Testing:** Required for all LLM operations

## Status
⚠️ **BLOCKED** - Cannot delete until dependencies migrated
