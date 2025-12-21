# Contributing to SomaAgent

## File Size Guidelines

To maintain code quality and readability, we enforce file size limits:

| File Type | Max Lines |
|-----------|-----------|
| `main.py` entry points | 150 |
| `service.py` files | 200 |
| Helper modules (`python/helpers/`) | 300 |
| Agent modules (`python/somaagent/`) | 200 |
| All other Python files | 500 |

## Decomposition Patterns

When a file exceeds its limit, use these patterns to decompose:

### 1. Extract by Domain
Split code by business domain (e.g., `conversation_tasks.py`, `memory_tasks.py`).

### 2. Extract by Layer
Separate concerns into layers:
- `*_models.py` - Data models and types
- `*_repository.py` - Data access
- `*_service.py` - Business logic

### 3. Extract Utilities
Move helper functions to dedicated modules:
- `validation.py` - Input validation
- `telemetry.py` - Metrics and logging
- `auth.py` - Authentication logic

### 4. Thin Facades
Keep entry points thin by delegating to extracted modules:
```python
# main.py - thin facade
from .auth import authorize_request
from .providers import get_bus, get_publisher
from .handlers import handle_message
```

## Pre-commit Hooks

File size checks run automatically on commit. To check manually:
```bash
python scripts/check_file_sizes.py --all
```

## Code Style

- Follow VIBE_CODING_RULES.md
- No mocks, stubs, or placeholders
- Real implementations only
- Document all public APIs

## Configuration Access

All configuration MUST use the canonical `cfg` facade from `src.core.config`:

```python
from src.core.config import cfg

# Get environment variable with SA01_ prefix priority
value = cfg.env("SA01_MY_SETTING", "default")

# Get boolean feature flag
enabled = cfg.flag("SA01_FEATURE_ENABLED")
```

**DO NOT** use `os.getenv()` or `os.environ` directly in production code.

Acceptable exceptions:
- `src/core/config/loader.py` - The canonical loader itself
- Test files - May set env vars directly
- Scripts that copy env for subprocesses

## Tool Catalog

Tools are registered in the PostgreSQL-backed tool catalog:

```python
from services.common.tool_catalog import ToolCatalogStore

# Check if tool is enabled for tenant
enabled = await store.is_enabled("my_tool", tenant_id="tenant-123")

# Register a new tool
await store.register_tool(ToolCatalogEntry(
    name="my_tool",
    description="My tool description",
    params={"input": {"type": "string"}},
    source="builtin",
))
```

## Degradation Manager

Use the DegradationManager for service health tracking:

```python
from services.common.degradation_manager import DegradationManager, ServiceState

manager = DegradationManager()

# Update service status
manager.update_service_status("postgres", ServiceState.HEALTHY)

# Check system health
health = manager.get_system_health()
# Returns: {"overall_state": "healthy", "services": {...}}
```

## Property Tests

Property tests validate architectural invariants. Add new tests to `tests/properties/`:

```python
# tests/properties/test_my_property.py
"""Property N: Description.

**Feature: feature-name, Property N: Description**
**Validates: Requirements X.Y**
"""

def test_my_property():
    """Property N: Description."""
    # Test implementation
    pass
```

Run property tests:
```bash
pytest tests/properties/ -v
```
