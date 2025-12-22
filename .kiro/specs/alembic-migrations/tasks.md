# Implementation Plan: Alembic Migrations for somaAgent01

## Overview

This plan converts somaAgent01 from raw SQL init scripts to Alembic-managed migrations. Tasks are ordered to build incrementally: configuration first, then models, then migrations, then Docker integration.

## Tasks

- [x] 1. Set up Alembic configuration and project structure
  - [x] 1.1 Create `alembic.ini` configuration file in project root
    - Configure script_location to `migrations`
    - Set sqlalchemy.url to use `SA01_DB_DSN` environment variable
    - Configure logging for migration output
    - _Requirements: 1.1, 1.3_

  - [x] 1.2 Create `migrations/` directory structure with `env.py`
    - Implement async PostgreSQL support via asyncpg
    - Support both online and offline migration modes
    - Import Base metadata from models
    - _Requirements: 1.2, 1.4_

  - [x] 1.3 Create `migrations/script.py.mako` template
    - Standard Alembic migration template
    - _Requirements: 1.2_

- [x] 2. Create SQLAlchemy model definitions
  - [x] 2.1 Create base model and ENUM types
    - Create `src/core/infrastructure/db/models/base.py` with DeclarativeBase
    - Create `src/core/infrastructure/db/models/enums.py` with all 5 ENUM types
    - Define naming convention for constraints
    - _Requirements: 2.2_

  - [x] 2.2 Create task registry models
    - Create `src/core/infrastructure/db/models/task_registry.py`
    - Define `TaskRegistry` model with TEXT[], JSONB columns
    - Define `TaskArtifact` model with UUID primary key
    - _Requirements: 2.1, 2.3, 2.4_

  - [x] 2.3 Create multimodal models
    - Create `src/core/infrastructure/db/models/multimodal.py`
    - Define `MultimodalAsset`, `MultimodalCapability`, `MultimodalJobPlan`, `MultimodalExecution`, `AssetProvenance`, `MultimodalOutcome` models
    - Include all foreign key relationships and constraints
    - _Requirements: 2.1, 2.3, 2.4_

  - [x] 2.4 Create tool catalog and prompt models
    - Create `src/core/infrastructure/db/models/tools.py` with `ToolCatalog`, `TenantToolFlag`
    - Create `src/core/infrastructure/db/models/prompts.py` with `Prompt` model
    - _Requirements: 2.1, 2.3, 2.4_

  - [x] 2.5 Create session embeddings model
    - Create `src/core/infrastructure/db/models/embeddings.py`
    - Define `SessionEmbedding` model with pgvector VECTOR(384) type
    - _Requirements: 2.1, 2.4_

  - [x] 2.6 Create models package `__init__.py`
    - Export all models and Base
    - _Requirements: 2.1_

  - [x] 2.7 Write property test for schema fidelity
    - **Property 2: Schema Fidelity**
    - **Validates: Requirements 2.3, 6.2, 6.3**

- [x] 3. Checkpoint - Verify models compile
  - Ensure all models import without errors
  - Verify Base.metadata contains all expected tables
  - Ask the user if questions arise

- [x] 4. Create initial migration
  - [x] 4.1 Create initial migration file `migrations/versions/001_initial_schema.py`
    - Create all ENUM types with idempotent DO/EXCEPTION blocks
    - Create all 12 tables with proper column types and constraints
    - Create all indexes
    - Insert seed data for tool_catalog, multimodal_capabilities, prompts
    - Implement downgrade to drop all tables in reverse FK order
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

  - [x] 4.2 Write property test for migration idempotency
    - **Property 3: Migration Idempotency**
    - **Validates: Requirements 3.3, 3.4, 3.5**

  - [x] 4.3 Write property test for migration round-trip
    - **Property 4: Migration Round-Trip**
    - **Validates: Requirements 6.4**

- [x] 5. Checkpoint - Test migrations locally
  - Schema fidelity tests pass (30/30)
  - Migration property tests created (require Docker for execution)
  - Migration file syntax verified
  - Ask the user if questions arise

- [x] 6. Docker integration
  - [x] 6.1 Create migration entrypoint script
    - Create `scripts/run-migrations.sh`
    - Run `alembic upgrade head` with error handling
    - Exit with non-zero on failure
    - _Requirements: 4.2, 4.3_

  - [x] 6.2 Update docker-compose.yaml
    - Gateway command updated to run migrations before starting
    - Init scripts kept for backward compatibility (only run on empty databases)
    - _Requirements: 4.1, 4.4_

  - [x] 6.3 Update Dockerfile if needed
    - Alembic added to requirements.txt
    - Migrations directory copied via existing `COPY . /app`
    - _Requirements: 4.2_

- [x] 7. Development workflow setup
  - [x] 7.1 Add Makefile targets for migrations
    - Add `db-migrate` target for creating new migrations
    - Add `db-upgrade` target for running migrations
    - Add `db-downgrade` target for rolling back
    - Add `db-history` target for viewing migration history
    - Add `db-current` and `db-heads` targets
    - _Requirements: 5.1_

  - [x] 7.2 Update documentation
    - Add migration workflow to CONTRIBUTING.md
    - Document rollback procedures
    - _Requirements: 5.3, 5.4_

- [x] 8. Final checkpoint
  - All tests pass (30 schema fidelity + 8 migration property tests)
  - Docker integration verified via testcontainers
  - Migration idempotency and round-trip properties validated
  - Spec complete

## Notes

- All tasks including property-based tests are required
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- The initial migration uses raw SQL for ENUM creation due to Alembic limitations with PostgreSQL ENUMs
