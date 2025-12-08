# Requirements Document

## Introduction

This specification addresses critical architectural issues in the SomaAgent01 codebase. Multiple files exceed 500+ lines, violating Single Responsibility Principle (SRP) and making the codebase difficult to maintain, test, and extend. This refactor applies Clean Architecture, Domain-Driven Design (DDD), and SOLID principles to decompose monolithic modules into focused, testable components.

## Glossary

- **Clean Architecture**: Architectural pattern separating concerns into layers (Domain, Application, Infrastructure, Presentation)
- **DDD**: Domain-Driven Design - organizing code around business domains
- **SRP**: Single Responsibility Principle - each module has one reason to change
- **Repository Pattern**: Abstraction layer between domain and data mapping
- **Service Layer**: Application services orchestrating domain operations
- **Use Case**: Single application operation encapsulating business logic
- **Aggregate**: Cluster of domain objects treated as a single unit
- **Port/Adapter**: Interface (port) with implementation (adapter) for external systems

## Architectural Patterns to Apply

### 1. Clean Architecture Layers
```
src/
├── core/
│   ├── domain/          # Entities, Value Objects, Domain Services
│   ├── application/     # Use Cases, Application Services, DTOs
│   └── infrastructure/  # Repositories, External Adapters, Config
├── services/            # Microservice entry points (thin)
└── shared/              # Cross-cutting concerns (logging, tracing)
```

### 2. Key Patterns
- **Repository Pattern**: Abstract data access behind interfaces
- **Use Case Pattern**: One class per business operation
- **Factory Pattern**: Complex object creation
- **Strategy Pattern**: Interchangeable algorithms (LLM providers, storage backends)
- **Observer Pattern**: Event-driven communication between services
- **Circuit Breaker**: Fault tolerance for external services

## Requirements

### Requirement 1: Decompose ConversationWorker (3022 lines)

**User Story:** As a developer, I want the conversation worker split into focused modules, so that I can understand, test, and modify individual concerns independently.

#### Acceptance Criteria

1. WHEN the conversation worker processes a message THEN the system SHALL delegate to a `MessageProcessor` use case that handles only message routing
2. WHEN the system needs to build LLM context THEN the system SHALL use a dedicated `ContextBuilder` service in `core/application/context/`
3. WHEN the system interacts with SomaBrain THEN the system SHALL use a `SomaBrainAdapter` in `core/infrastructure/external/`
4. WHEN the system manages session state THEN the system SHALL use a `SessionRepository` interface with Postgres/Redis implementations
5. WHEN the system handles tool execution THEN the system SHALL delegate to a `ToolOrchestrator` service
6. WHEN the system performs health monitoring THEN the system SHALL use a dedicated `HealthMonitor` component
7. THE conversation worker main.py SHALL contain only service initialization and Kafka consumer setup (< 150 lines)

### Requirement 2: Decompose Agent Module (4092 lines)

**User Story:** As a developer, I want the agent module split by responsibility, so that each component can evolve independently.

#### Acceptance Criteria

1. WHEN the agent processes user input THEN the system SHALL use an `InputProcessor` use case
2. WHEN the agent selects tools THEN the system SHALL use a `ToolSelector` strategy
3. WHEN the agent generates responses THEN the system SHALL use a `ResponseGenerator` service
4. WHEN the agent manages conversation flow THEN the system SHALL use a `ConversationOrchestrator`
5. WHEN the agent handles errors THEN the system SHALL use an `ErrorHandler` with retry policies
6. THE agent.py file SHALL be reduced to < 200 lines containing only orchestration logic

### Requirement 3: Decompose ToolExecutor (805 lines)

**User Story:** As a developer, I want tool execution separated from policy enforcement and telemetry, so that each concern is independently testable.

#### Acceptance Criteria

1. WHEN a tool request arrives THEN the system SHALL validate it via a `RequestValidator` component
2. WHEN policy evaluation is needed THEN the system SHALL delegate to a `PolicyEnforcer` adapter
3. WHEN tool execution completes THEN the system SHALL emit telemetry via a `TelemetryEmitter` service
4. WHEN audit logging is required THEN the system SHALL use an `AuditLogger` component
5. WHEN memory capture is needed THEN the system SHALL use a `MemoryCapture` use case
6. THE tool_executor/main.py SHALL contain only service bootstrap and event consumption (< 150 lines)

### Requirement 4: Decompose Settings/Config (1793 lines in python/helpers/settings.py)

**User Story:** As a developer, I want configuration management consolidated and simplified, so that there is one clear way to access settings.

#### Acceptance Criteria

1. WHEN any module needs configuration THEN the system SHALL import from `src.core.config` only
2. WHEN configuration is loaded THEN the system SHALL use a single `ConfigLoader` with clear precedence
3. WHEN feature flags are checked THEN the system SHALL use a `FeatureFlagService`
4. WHEN secrets are accessed THEN the system SHALL use a `SecretManager` adapter
5. THE python/helpers/settings.py file SHALL be deleted after migration to `src.core.config`
6. THE src/core/config/ package SHALL have clear separation: models.py (< 200 lines), loader.py (< 150 lines), registry.py (< 200 lines)

### Requirement 5: Decompose Task Scheduler (1276 lines)

**User Story:** As a developer, I want task scheduling separated from task execution, so that scheduling logic is reusable.

#### Acceptance Criteria

1. WHEN a task is scheduled THEN the system SHALL use a `TaskScheduler` interface
2. WHEN a task executes THEN the system SHALL use task-specific `TaskHandler` implementations
3. WHEN task state changes THEN the system SHALL emit events via `TaskEventEmitter`
4. WHEN task history is queried THEN the system SHALL use a `TaskRepository`
5. THE task_scheduler.py SHALL be split into scheduler/, handlers/, and repository/ modules

### Requirement 6: Decompose MCP Handler (1087 lines)

**User Story:** As a developer, I want MCP protocol handling separated from tool registration, so that protocol changes don't affect tool logic.

#### Acceptance Criteria

1. WHEN MCP messages arrive THEN the system SHALL parse them via `MCPProtocolParser`
2. WHEN tools are registered THEN the system SHALL use a `ToolRegistry` service
3. WHEN MCP responses are built THEN the system SHALL use `MCPResponseBuilder`
4. WHEN MCP connections are managed THEN the system SHALL use `MCPConnectionManager`
5. THE mcp_handler.py SHALL be split into protocol/, registry/, and connection/ modules

### Requirement 7: Decompose Memory Module (1010 lines)

**User Story:** As a developer, I want memory operations separated by type, so that each memory strategy is independently configurable.

#### Acceptance Criteria

1. WHEN short-term memory is accessed THEN the system SHALL use `ShortTermMemoryStore`
2. WHEN long-term memory is accessed THEN the system SHALL use `LongTermMemoryStore`
3. WHEN memory is consolidated THEN the system SHALL use `MemoryConsolidator` service
4. WHEN memory is searched THEN the system SHALL use `MemorySearchService`
5. THE memory.py SHALL be split into stores/, consolidation/, and search/ modules

### Requirement 8: Decompose Gateway Main (438 lines)

**User Story:** As a developer, I want gateway routes separated from middleware, so that routing changes don't affect cross-cutting concerns.

#### Acceptance Criteria

1. WHEN HTTP requests arrive THEN the system SHALL route via dedicated router modules
2. WHEN authentication is needed THEN the system SHALL use `AuthMiddleware`
3. WHEN rate limiting is applied THEN the system SHALL use `RateLimitMiddleware`
4. WHEN health checks run THEN the system SHALL use dedicated health router
5. THE gateway/main.py SHALL contain only FastAPI app initialization (< 100 lines)

### Requirement 9: Decompose Session Repository (681 lines)

**User Story:** As a developer, I want session storage separated from caching, so that storage backends are interchangeable.

#### Acceptance Criteria

1. WHEN sessions are persisted THEN the system SHALL use `SessionStore` interface
2. WHEN sessions are cached THEN the system SHALL use `SessionCache` interface
3. WHEN session events are tracked THEN the system SHALL use `SessionEventStore`
4. THE session_repository.py SHALL be split into store.py, cache.py, and events.py

### Requirement 10: Decompose Core Tasks (764 lines)

**User Story:** As a developer, I want Celery tasks separated by domain, so that task dependencies are clear.

#### Acceptance Criteria

1. WHEN conversation tasks run THEN the system SHALL use `conversation_tasks.py`
2. WHEN memory tasks run THEN the system SHALL use `memory_tasks.py`
3. WHEN maintenance tasks run THEN the system SHALL use `maintenance_tasks.py`
4. THE core_tasks.py SHALL be split into domain-specific task modules

### Requirement 11: Apply Repository Pattern Consistently

**User Story:** As a developer, I want all data access behind repository interfaces, so that storage implementations are swappable.

#### Acceptance Criteria

1. WHEN any module accesses Postgres THEN the system SHALL use a repository interface
2. WHEN any module accesses Redis THEN the system SHALL use a cache interface
3. WHEN any module accesses Kafka THEN the system SHALL use an event bus interface
4. THE system SHALL define interfaces in `core/domain/ports/` and implementations in `core/infrastructure/adapters/`

### Requirement 12: Apply Use Case Pattern

**User Story:** As a developer, I want business operations encapsulated in use cases, so that application logic is testable without infrastructure.

#### Acceptance Criteria

1. WHEN a business operation is performed THEN the system SHALL execute via a use case class
2. WHEN use cases need external services THEN the system SHALL inject them via constructor
3. WHEN use cases return results THEN the system SHALL use typed DTOs
4. THE system SHALL organize use cases in `core/application/use_cases/`

### Requirement 13: Eliminate Re-export Modules

**User Story:** As a developer, I want direct imports without re-export shims, so that import paths are clear and IDE navigation works.

#### Acceptance Criteria

1. WHEN a module is imported THEN the system SHALL import from the canonical location
2. WHEN re-exports exist for compatibility THEN the system SHALL add deprecation warnings
3. THE system SHALL remove all re-export modules within 2 release cycles
4. THE system SHALL update all import statements to use canonical paths

### Requirement 14: File Size Limits

**User Story:** As a developer, I want enforced file size limits, so that modules stay focused.

#### Acceptance Criteria

1. WHEN a Python file exceeds 300 lines THEN the system SHALL flag it for review
2. WHEN a Python file exceeds 500 lines THEN the system SHALL require decomposition
3. THE system SHALL add a pre-commit hook to enforce file size limits
4. THE system SHALL document decomposition patterns in CONTRIBUTING.md
