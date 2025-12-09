# Contributing to SomaAgent

## File Size Guidelines

To maintain code quality and readability, we enforce file size limits:

| File Type | Max Lines |
|-----------|-----------|
| `main.py` entry points | 150 |
| `service.py` files | 200 |
| Helper modules (`python/helpers/`) | 300 |
| Task modules (`python/tasks/`) | 200 |
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
