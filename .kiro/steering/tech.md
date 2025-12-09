# Tech Stack & Build System

## Language & Runtime

- Python 3.11+ (< 3.13)
- Node.js (for Playwright tests and UI tooling)

## Core Frameworks

- **FastAPI** + **Uvicorn**: HTTP API gateway and services
- **Celery** + **Redis**: Async task queue (FastA2A workers)
- **aiokafka**: Event streaming between services
- **SQLAlchemy** + **asyncpg/psycopg**: PostgreSQL ORM
- **Pydantic**: Data validation and settings

## Infrastructure

- **Kafka**: Event bus for service communication
- **Redis**: Caching, Celery broker, session storage
- **PostgreSQL**: Primary database
- **OPA (Open Policy Agent)**: Authorization policies

## AI/ML Stack

- **LiteLLM**: LLM provider abstraction
- **LangChain**: Core utilities (langchain-core, langchain-community)
- **tiktoken**: Token counting
- **browser-use**: Browser automation
- **fastmcp/mcp**: Model Context Protocol

## Observability

- **Prometheus**: Metrics collection
- **OpenTelemetry**: Distributed tracing
- **pybreaker**: Circuit breaker pattern

## Code Quality

- **black**: Code formatting (line-length: 100)
- **ruff**: Linting and import sorting
- **pytest**: Testing framework
- **mypy**: Type checking

## Common Commands

```bash
# Development stack
make dev-up              # Start full dev stack (Docker)
make dev-down            # Stop dev stack
make dev-logs            # Tail logs
make dev-rebuild         # Rebuild and restart

# Dependencies only (for local Python dev)
make deps-up             # Start Kafka/Redis/Postgres/OPA
make stack-up            # Run gateway + workers locally

# Code quality
make quality             # Run all checks (format, lint, typecheck, test)
make format              # Format code (black + ruff --fix)
make lint                # Lint code (ruff)
make test                # Run pytest

# Health checks
make health              # Check Gateway health
make health-wait         # Wait for Gateway to be ready

# Docker
make build               # Build Docker images
make docker-image        # Build with canonical tag
```

## Environment Configuration

- Use `src.core.config.env()` for environment reads (not `os.getenv` directly)
- Use `src.core.config.flag()` for feature flags
- Provider credentials managed via Web UI Settings (not env vars)
- Secrets encrypted in Redis via `SA01_CRYPTO_FERNET_KEY`

## Key Environment Variables

- `SA01_DB_DSN`: PostgreSQL connection string
- `SA01_KAFKA_BOOTSTRAP_SERVERS`: Kafka brokers
- `SA01_REDIS_URL`: Redis connection
- `SA01_POLICY_URL`: OPA endpoint
- `SA01_AUTH_INTERNAL_TOKEN`: Internal service auth
- `GATEWAY_PORT`: Gateway HTTP port (default: 21016)
