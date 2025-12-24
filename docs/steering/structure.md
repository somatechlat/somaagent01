# Project Structure

## Top-Level Layout

```
├── services/           # Microservices (Kafka consumers, Gateway, workers)
├── src/                # Core domain logic (Clean Architecture)
├── python/             # Agent runtime, tools, helpers, tasks
├── webui/              # Frontend static files
├── prompts/            # Agent behavior prompts (system prompts, templates)
├── instruments/        # Custom agent instruments
├── integrations/       # External service integrations
├── infra/              # Infrastructure configs (Helm, K8s, Kafka, SQL)
├── policy/             # OPA authorization policies
├── schemas/            # JSON schemas for validation
├── tests/              # Test suites (unit, e2e, playwright)
├── scripts/            # Utility scripts
├── docs/               # Documentation (MkDocs)
```

## Services (`services/`)

Microservices following thin-facade pattern:

- `gateway/` - FastAPI HTTP gateway, serves UI, routes to Kafka
- `conversation_worker/` - Processes conversation messages from Kafka
- `tool_executor/` - Executes agent tools in sandboxed environment
- `memory_replicator/` - Replicates memory events
- `memory_sync/` - Syncs memory to persistent storage
- `outbox_sync/` - Transactional outbox pattern for reliability
- `common/` - Shared utilities (stores, telemetry, auth, etc.)

## Core Domain (`src/core/`)

Clean Architecture layers:

- `application/` - Use cases, DTOs, services
- `domain/` - Entities, value objects, ports (interfaces)
- `infrastructure/` - Adapters, repositories, external integrations
- `config/` - Centralized configuration
- `messaging/` - Kafka/event messaging utilities

## Python Runtime (`python/`)

- `somaagent/` - Agent orchestration, cognitive processing
- `helpers/` - Utility modules (memory, MCP, scheduling, etc.)
- `tasks/` - Celery tasks for async processing
- `tools/` - Agent tool implementations
- `api/` - FastA2A API router
- `extensions/` - Agent lifecycle hooks
- `integrations/` - External service clients

## File Size Limits

| File Type | Max Lines |
|-----------|-----------|
| `main.py` entry points | 150 |
| `service.py` files | 200 |
| `python/helpers/` | 300 |
| `python/tasks/` | 200 |
| `python/somaagent/` | 200 |
| Other Python files | 500 |

## Decomposition Patterns

When files exceed limits:

1. **Extract by Domain**: Split by business domain
2. **Extract by Layer**: Separate `*_models.py`, `*_repository.py`, `*_service.py`
3. **Extract Utilities**: Move to `validation.py`, `telemetry.py`, `auth.py`
4. **Thin Facades**: Keep entry points thin, delegate to extracted modules

## Key Files

- `agent.py` - Main agent entry point
- `docker-compose.yaml` - Full stack definition
- `Makefile` - Build and dev commands
- `pyproject.toml` - Python project config
- `prompts/default/agent.system.md` - Core agent behavior prompt
