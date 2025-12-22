
OK PLESE KEEP IMPLE,ENTING AS THE WHOLE PERSONAS AL THE TIME AND HAVE THE VIBE CODING RULES ALWYS IN YOUR MIND, act here ass the full peronas in the rules and use them alwqys here i nthis session , TEST ALWAYS ON REAL INFRA EXCEP FOR UNIT TESTING when you have finished coding a milestone or whatever # Requirements Document

## Introduction

This feature establishes Alembic as the database migration system for somaAgent01, replacing the current raw SQL init scripts approach. Alembic provides version-controlled, reversible database schema management that is essential for production-grade systems.

## Glossary

- **Alembic**: A lightweight database migration tool for SQLAlchemy that provides version control for database schemas
- **Migration**: A Python script that defines schema changes (upgrade) and their reversal (downgrade)
- **Revision**: A unique identifier for each migration in the version history
- **Head**: The most recent migration revision
- **Base**: The initial state before any migrations
- **SQLAlchemy_Models**: Python classes that define database table structures using SQLAlchemy ORM

## Requirements

### Requirement 1: Alembic Configuration

**User Story:** As a developer, I want Alembic properly configured in somaAgent01, so that I can manage database schema changes through version-controlled migrations.

#### Acceptance Criteria

1. THE Alembic_Configuration SHALL include an `alembic.ini` file in the project root with correct database connection settings
2. THE Alembic_Configuration SHALL include a `migrations/` directory with `env.py` configured for async PostgreSQL via asyncpg
3. WHEN the `SA01_DB_DSN` environment variable is set, THE Alembic_Configuration SHALL use it for database connections
4. THE Alembic_Configuration SHALL support both sync and async database operations

### Requirement 2: SQLAlchemy Model Definitions

**User Story:** As a developer, I want SQLAlchemy models that match the existing database schema, so that Alembic can track and manage schema changes.

#### Acceptance Criteria

1. THE SQLAlchemy_Models SHALL define all existing tables: `task_registry`, `task_artifacts`, `multimodal_assets`, `multimodal_capabilities`, `multimodal_job_plans`, `multimodal_executions`, `asset_provenance`, `multimodal_outcomes`, `prompts`, `tool_catalog`, `tenant_tool_flags`, `session_embeddings`
2. THE SQLAlchemy_Models SHALL include all PostgreSQL ENUM types: `asset_type`, `job_status`, `execution_status`, `capability_health`, `cost_tier`
3. THE SQLAlchemy_Models SHALL preserve all existing constraints, indexes, and foreign key relationships
4. THE SQLAlchemy_Models SHALL use appropriate SQLAlchemy types including `JSONB`, `ARRAY`, `UUID`, and pgvector's `VECTOR` type

### Requirement 3: Initial Migration from Existing Schema

**User Story:** As a developer, I want an initial migration that captures the current database schema, so that existing deployments can be brought under Alembic management.

#### Acceptance Criteria

1. THE Initial_Migration SHALL create all tables currently defined in `infra/postgres/init/*.sql` files
2. THE Initial_Migration SHALL include all seed data from the existing SQL scripts (tool_catalog entries, multimodal_capabilities entries, prompts)
3. THE Initial_Migration SHALL be idempotent and safe to run on databases with existing schema
4. WHEN running on an empty database, THE Initial_Migration SHALL create the complete schema
5. WHEN running on a database with existing tables, THE Initial_Migration SHALL detect and skip already-created objects

### Requirement 4: Docker Integration

**User Story:** As a developer, I want Alembic migrations to run automatically during container startup, so that the database schema is always up-to-date.

#### Acceptance Criteria

1. WHEN the postgres container starts, THE Docker_Integration SHALL NOT run raw SQL init scripts
2. THE Docker_Integration SHALL provide a migration entrypoint script that runs `alembic upgrade head`
3. WHEN migrations fail, THE Docker_Integration SHALL log errors and prevent service startup
4. THE Docker_Integration SHALL support running migrations as a separate init container or startup command

### Requirement 5: Development Workflow

**User Story:** As a developer, I want clear commands for creating and running migrations, so that I can safely evolve the database schema.

#### Acceptance Criteria

1. THE Development_Workflow SHALL include Makefile targets: `make db-migrate`, `make db-upgrade`, `make db-downgrade`, `make db-history`
2. WHEN creating a new migration, THE Development_Workflow SHALL use `alembic revision --autogenerate -m "description"`
3. THE Development_Workflow SHALL document the migration workflow in README or CONTRIBUTING.md
4. IF a migration fails, THEN THE Development_Workflow SHALL provide clear rollback instructions

### Requirement 6: Backward Compatibility

**User Story:** As a developer, I want the migration to preserve all existing data and functionality, so that the transition to Alembic is seamless.

#### Acceptance Criteria

1. THE Backward_Compatibility SHALL preserve all existing table data during migration
2. THE Backward_Compatibility SHALL maintain all existing foreign key relationships
3. THE Backward_Compatibility SHALL keep all existing indexes and constraints
4. WHEN downgrading migrations, THE Backward_Compatibility SHALL restore the previous schema state without data loss where possible
