# Design Document: Alembic Migrations for somaAgent01

## Overview

This design establishes Alembic as the database migration system for somaAgent01, replacing raw SQL init scripts with version-controlled, reversible migrations. The implementation uses SQLAlchemy 2.0 with async PostgreSQL support via asyncpg, integrating with the existing docker-compose infrastructure.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     somaAgent01 Project                         │
├─────────────────────────────────────────────────────────────────┤
│  alembic.ini                    # Alembic configuration         │
│  migrations/                                                    │
│  ├── env.py                     # Migration environment setup   │
│  ├── script.py.mako             # Migration template            │
│  └── versions/                                                  │
│      └── 001_initial_schema.py  # Initial migration             │
│                                                                 │
│  src/core/infrastructure/db/                                    │
│  ├── models/                    # SQLAlchemy model definitions  │
│  │   ├── __init__.py                                           │
│  │   ├── base.py                # Base model class              │
│  │   ├── enums.py               # PostgreSQL ENUM types         │
│  │   ├── task_registry.py       # Task/tool registry models     │
│  │   ├── multimodal.py          # Multimodal capability models  │
│  │   ├── tools.py               # Tool catalog models           │
│  │   └── embeddings.py          # Session embeddings model      │
│  └── session.py                 # Async session factory         │
│                                                                 │
│  scripts/                                                       │
│  └── run-migrations.sh          # Docker entrypoint script      │
└─────────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### 1. Alembic Configuration (`alembic.ini`)

Configuration file in project root:
- Database URL from `SA01_DB_DSN` environment variable
- Migration script location: `migrations/`
- SQLAlchemy URL interpolation enabled
- Logging configuration for migration output

### 2. Migration Environment (`migrations/env.py`)

Handles both online (connected) and offline (SQL generation) migrations:

```python
# Pseudocode for env.py structure
from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine
from src.core.infrastructure.db.models import Base

def get_url() -> str:
    """Get database URL from environment."""
    return os.environ.get("SA01_DB_DSN", "postgresql+asyncpg://soma:soma@localhost:5432/somaagent01")

def run_migrations_offline():
    """Generate SQL without database connection."""
    context.configure(url=get_url(), target_metadata=Base.metadata)
    with context.begin_transaction():
        context.run_migrations()

async def run_migrations_online():
    """Run migrations with async database connection."""
    engine = create_async_engine(get_url())
    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)
```

### 3. SQLAlchemy Models

#### Base Model (`src/core/infrastructure/db/models/base.py`)

```python
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import MetaData

# Naming convention for constraints (enables autogenerate)
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=convention)
```

#### ENUM Types (`src/core/infrastructure/db/models/enums.py`)

```python
import enum
from sqlalchemy import Enum as SAEnum

class AssetType(str, enum.Enum):
    IMAGE = "image"
    VIDEO = "video"
    DIAGRAM = "diagram"
    SCREENSHOT = "screenshot"
    DOCUMENT = "document"

class JobStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ExecutionStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"

class CapabilityHealth(str, enum.Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"

class CostTier(str, enum.Enum):
    FREE = "free"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    PREMIUM = "premium"
```

#### Model Definitions

Each model maps to existing tables with full type fidelity:

| Model Class | Table | Key Types |
|-------------|-------|-----------|
| `TaskRegistry` | `task_registry` | TEXT[], JSONB |
| `TaskArtifact` | `task_artifacts` | UUID, TEXT |
| `MultimodalAsset` | `multimodal_assets` | UUID, BYTEA, JSONB, ENUM |
| `MultimodalCapability` | `multimodal_capabilities` | JSONB, ENUM (composite PK) |
| `MultimodalJobPlan` | `multimodal_job_plans` | UUID, JSONB, ENUM |
| `MultimodalExecution` | `multimodal_executions` | UUID, REAL, JSONB, ENUM |
| `AssetProvenance` | `asset_provenance` | UUID (FK), TEXT, JSONB |
| `MultimodalOutcome` | `multimodal_outcomes` | UUID, REAL, BOOLEAN |
| `Prompt` | `prompts` | UUID, TEXT, INTEGER |
| `ToolCatalog` | `tool_catalog` | TEXT (PK), JSONB, TEXT[] |
| `TenantToolFlag` | `tenant_tool_flags` | TEXT (composite PK), BOOLEAN |
| `SessionEmbedding` | `session_embeddings` | UUID (FK), VECTOR(384), JSONB |

### 4. Initial Migration

The initial migration (`001_initial_schema.py`) will:

1. Create all ENUM types using `CREATE TYPE IF NOT EXISTS`
2. Create all tables with `IF NOT EXISTS` for idempotency
3. Create all indexes with `IF NOT EXISTS`
4. Insert seed data using `ON CONFLICT DO NOTHING`

```python
# Pseudocode for initial migration structure
def upgrade():
    # Create ENUMs (idempotent)
    op.execute("DO $$ BEGIN CREATE TYPE asset_type AS ENUM (...); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    
    # Create tables (idempotent via IF NOT EXISTS in raw SQL or check)
    if not table_exists("task_registry"):
        op.create_table("task_registry", ...)
    
    # Create indexes (idempotent)
    op.create_index("idx_name", "table", ["col"], if_not_exists=True)
    
    # Seed data (idempotent via ON CONFLICT)
    op.execute("INSERT INTO tool_catalog (...) ON CONFLICT DO NOTHING")

def downgrade():
    # Drop in reverse order respecting FK constraints
    op.drop_table("asset_provenance")
    op.drop_table("multimodal_executions")
    # ... etc
```

### 5. Docker Integration

#### Migration Script (`scripts/run-migrations.sh`)

```bash
#!/bin/bash
set -e

echo "Running database migrations..."
alembic upgrade head

if [ $? -eq 0 ]; then
    echo "Migrations completed successfully"
else
    echo "Migration failed!" >&2
    exit 1
fi
```

#### Docker Compose Changes

```yaml
# Remove SQL init script mount from postgres service
postgres:
  volumes:
    - postgres_data:/var/lib/postgresql/data
    - ./postgres-backups:/backups
    # REMOVED: - ./infra/postgres/init:/docker-entrypoint-initdb.d:ro

# Add migration service or modify gateway startup
gateway:
  command:
    - sh
    - -c
    - |
      ./scripts/run-migrations.sh && \
      python3 -m uvicorn services.gateway.main:app --host 0.0.0.0 --port 8010
```

## Data Models

### Entity Relationship Diagram

```
┌─────────────────┐     ┌──────────────────────┐
│  task_registry  │     │   task_artifacts     │
├─────────────────┤     ├──────────────────────┤
│ name (PK)       │     │ id (PK, UUID)        │
│ kind            │     │ name                 │
│ module_path     │     │ version              │
│ callable        │     │ storage_uri          │
│ queue           │     │ sha256               │
│ ...             │     │ ...                  │
└─────────────────┘     └──────────────────────┘

┌─────────────────────┐     ┌─────────────────────┐
│ multimodal_assets   │────▶│  asset_provenance   │
├─────────────────────┤     ├─────────────────────┤
│ id (PK, UUID)       │     │ asset_id (PK, FK)   │
│ tenant_id           │     │ request_id          │
│ asset_type (ENUM)   │     │ execution_id (FK)   │
│ content (BYTEA)     │     │ plan_id (FK)        │
│ ...                 │     │ ...                 │
└─────────────────────┘     └─────────────────────┘
         ▲
         │
┌─────────────────────────┐     ┌─────────────────────┐
│ multimodal_executions   │────▶│ multimodal_job_plans│
├─────────────────────────┤     ├─────────────────────┤
│ id (PK, UUID)           │     │ id (PK, UUID)       │
│ plan_id (FK)            │     │ tenant_id           │
│ step_index              │     │ session_id          │
│ asset_id (FK)           │     │ plan_json (JSONB)   │
│ status (ENUM)           │     │ status (ENUM)       │
│ ...                     │     │ ...                 │
└─────────────────────────┘     └─────────────────────┘

┌─────────────────────────┐
│ multimodal_capabilities │
├─────────────────────────┤
│ tool_id (PK)            │
│ provider (PK)           │
│ modalities (JSONB)      │
│ health_status (ENUM)    │
│ cost_tier (ENUM)        │
│ ...                     │
└─────────────────────────┘

┌─────────────────┐     ┌─────────────────────┐
│  tool_catalog   │────▶│ tenant_tool_flags   │
├─────────────────┤     ├─────────────────────┤
│ name (PK)       │     │ tenant_id (PK)      │
│ description     │     │ tool_name (PK, FK)  │
│ parameters_schema│    │ enabled             │
│ ...             │     │ ...                 │
└─────────────────┘     └─────────────────────┘

┌─────────────────────┐     ┌─────────────────┐
│ session_embeddings  │     │    prompts      │
├─────────────────────┤     ├─────────────────┤
│ id (PK, BIGSERIAL)  │     │ id (PK, UUID)   │
│ session_id (FK)     │     │ name (UNIQUE)   │
│ text                │     │ version         │
│ vector (VECTOR 384) │     │ content         │
│ metadata (JSONB)    │     │ ...             │
└─────────────────────┘     └─────────────────┘

┌─────────────────────┐
│ multimodal_outcomes │
├─────────────────────┤
│ id (PK, UUID)       │
│ plan_id             │
│ task_id             │
│ success             │
│ latency_ms          │
│ quality_score       │
│ ...                 │
└─────────────────────┘
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: DSN Configuration Consistency

*For any* valid PostgreSQL connection string set in `SA01_DB_DSN`, the Alembic configuration SHALL use that exact connection string when establishing database connections.

**Validates: Requirements 1.3**

### Property 2: Schema Fidelity

*For any* SQLAlchemy model definition, the generated DDL (via `metadata.create_all()` or Alembic autogenerate) SHALL produce table structures with identical columns, types, constraints, and indexes as the original SQL init scripts.

**Validates: Requirements 2.3, 6.2, 6.3**

### Property 3: Migration Idempotency

*For any* database state (empty or with existing schema), running `alembic upgrade head` multiple times SHALL produce the same final schema state without errors or duplicate objects.

**Validates: Requirements 3.3, 3.4, 3.5**

### Property 4: Migration Round-Trip

*For any* migration revision, applying `upgrade` followed by `downgrade` SHALL restore the database schema to its previous state (excluding seed data that may be preserved).

**Validates: Requirements 6.4**

## Error Handling

| Error Scenario | Handling Strategy |
|----------------|-------------------|
| Missing `SA01_DB_DSN` | Fall back to default local DSN with warning log |
| Database connection failure | Retry 3 times with exponential backoff, then fail with clear error |
| Migration conflict (duplicate revision) | Fail fast with instructions to resolve |
| Table already exists | Use `IF NOT EXISTS` / check before create for idempotency |
| ENUM type already exists | Use `DO $$ BEGIN ... EXCEPTION WHEN duplicate_object THEN null; END $$;` |
| Foreign key violation on downgrade | Drop dependent tables first (reverse creation order) |
| Seed data conflict | Use `ON CONFLICT DO NOTHING` for idempotent inserts |

## Testing Strategy

### Unit Tests

- Verify model definitions match expected column types
- Verify ENUM definitions match expected values
- Verify constraint naming follows convention

### Property-Based Tests

Using `hypothesis` for property-based testing:

1. **DSN Configuration Property**: Generate random valid DSN strings, verify they're correctly passed to engine
2. **Schema Fidelity Property**: Compare generated DDL against reference SQL
3. **Migration Idempotency Property**: Run upgrade multiple times, verify no errors
4. **Migration Round-Trip Property**: Run upgrade/downgrade cycles, verify schema consistency

### Integration Tests

- Run migrations on empty test database, verify all tables created
- Run migrations on database with existing schema, verify no errors
- Verify seed data present after migration
- Test downgrade path restores previous state

### Test Configuration

- Use `pytest` with `pytest-asyncio` for async tests
- Use `testcontainers` for isolated PostgreSQL instances
- Minimum 100 iterations for property-based tests
- Tag format: **Feature: alembic-migrations, Property N: {property_text}**
