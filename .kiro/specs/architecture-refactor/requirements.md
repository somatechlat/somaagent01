# Requirements Document

## Introduction

This specification addresses the architectural debt in the SomaAgent01 codebase where several files have grown to 1000-4000+ lines, violating single responsibility principle and making the code difficult to maintain, test, and extend.

## Glossary

- **Monolith File**: A Python module exceeding 500 lines containing multiple unrelated concerns
- **Domain Module**: A focused module handling a single bounded context
- **Service Layer**: Business logic separated from infrastructure concerns

## Requirements

### Requirement 1: Agent Module Decomposition

**User Story:** As a developer, I want the agent.py file (4092 lines) split into focused modules, so that I can understand and modify agent behavior without navigating a massive file.

#### Acceptance Criteria

1. WHEN the agent module is refactored THEN the system SHALL separate AgentContext into `src/core/agent/context.py`
2. WHEN the agent module is refactored THEN the system SHALL separate AgentConfig into `src/core/agent/config.py`
3. WHEN the agent module is refactored THEN the system SHALL separate Agent class into `src/core/agent/agent.py`
4. WHEN the agent module is refactored THEN the system SHALL separate FSM/state logic into `src/core/agent/state_machine.py`
5. WHEN the agent module is refactored THEN the system SHALL keep `agent.py` as a thin re-export facade under 100 lines

### Requirement 2: ConversationWorker Decomposition

**User Story:** As a developer, I want the conversation_worker/main.py (3022 lines) split into focused modules, so that conversation handling logic is maintainable.

#### Acceptance Criteria

1. WHEN the conversation worker is refactored THEN the system SHALL separate message preprocessing into `services/conversation_worker/preprocessing.py`
2. WHEN the conversation worker is refactored THEN the system SHALL separate LLM invocation into `services/conversation_worker/llm_client.py`
3. WHEN the conversation worker is refactored THEN the system SHALL separate memory operations into `services/conversation_worker/memory_ops.py`
4. WHEN the conversation worker is refactored THEN the system SHALL separate escalation logic into `services/conversation_worker/escalation.py`
5. WHEN the conversation worker is refactored THEN the system SHALL separate context building into `services/conversation_worker/context.py`
6. WHEN the conversation worker is refactored THEN the system SHALL keep main.py as orchestration under 300 lines

### Requirement 3: Settings Module Decomposition

**User Story:** As a developer, I want python/helpers/settings.py (1793 lines) split into focused modules, so that settings management is clear and testable.

#### Acceptance Criteria

1. WHEN the settings module is refactored THEN the system SHALL separate type definitions into `python/helpers/settings/types.py`
2. WHEN the settings module is refactored THEN the system SHALL separate conversion logic into `python/helpers/settings/converters.py`
3. WHEN the settings module is refactored THEN the system SHALL separate persistence into `python/helpers/settings/storage.py`
4. WHEN the settings module is refactored THEN the system SHALL separate defaults into `python/helpers/settings/defaults.py`
5. WHEN the settings module is refactored THEN the system SHALL keep `settings/__init__.py` as public API under 100 lines

### Requirement 4: Models Module Decomposition

**User Story:** As a developer, I want models.py (1283 lines) split by domain, so that model definitions are organized by their purpose.

#### Acceptance Criteria

1. WHEN the models module is refactored THEN the system SHALL separate LLM wrappers into `src/core/llm/wrappers.py`
2. WHEN the models module is refactored THEN the system SHALL separate embedding models into `src/core/llm/embeddings.py`
3. WHEN the models module is refactored THEN the system SHALL separate rate limiting into `src/core/llm/rate_limiter.py`
4. WHEN the models module is refactored THEN the system SHALL separate model configuration into `src/core/llm/config.py`
5. WHEN the models module is refactored THEN the system SHALL keep `models.py` as re-export facade under 50 lines

### Requirement 5: Task Scheduler Decomposition

**User Story:** As a developer, I want python/helpers/task_scheduler.py (1276 lines) split into focused modules, so that task scheduling is maintainable.

#### Acceptance Criteria

1. WHEN the task scheduler is refactored THEN the system SHALL separate task models into `python/helpers/scheduler/models.py`
2. WHEN the task scheduler is refactored THEN the system SHALL separate serialization into `python/helpers/scheduler/serialization.py`
3. WHEN the task scheduler is refactored THEN the system SHALL separate scheduler logic into `python/helpers/scheduler/scheduler.py`
4. WHEN the task scheduler is refactored THEN the system SHALL keep `task_scheduler.py` as re-export facade under 50 lines

### Requirement 6: MCP Handler Decomposition

**User Story:** As a developer, I want python/helpers/mcp_handler.py (1087 lines) split into focused modules, so that MCP integration is clear.

#### Acceptance Criteria

1. WHEN the MCP handler is refactored THEN the system SHALL separate tool definitions into `python/helpers/mcp/tools.py`
2. WHEN the MCP handler is refactored THEN the system SHALL separate server models into `python/helpers/mcp/servers.py`
3. WHEN the MCP handler is refactored THEN the system SHALL separate client implementations into `python/helpers/mcp/clients.py`
4. WHEN the MCP handler is refactored THEN the system SHALL separate config parsing into `python/helpers/mcp/config.py`
5. WHEN the MCP handler is refactored THEN the system SHALL keep `mcp_handler.py` as re-export facade under 50 lines

### Requirement 7: Memory Module Decomposition

**User Story:** As a developer, I want python/helpers/memory.py (1010 lines) split into focused modules, so that memory operations are organized.

#### Acceptance Criteria

1. WHEN the memory module is refactored THEN the system SHALL separate memory types into `python/helpers/memory/types.py`
2. WHEN the memory module is refactored THEN the system SHALL separate storage operations into `python/helpers/memory/storage.py`
3. WHEN the memory module is refactored THEN the system SHALL separate retrieval logic into `python/helpers/memory/retrieval.py`
4. WHEN the memory module is refactored THEN the system SHALL keep `memory.py` as re-export facade under 50 lines

### Requirement 8: File Size Enforcement

**User Story:** As a developer, I want automated checks preventing files from exceeding 500 lines, so that architectural debt is caught early.

#### Acceptance Criteria

1. WHEN a Python file exceeds 500 lines THEN the CI system SHALL fail with a clear error message
2. WHEN checking file sizes THEN the system SHALL exclude test files and generated code
3. WHEN a file legitimately needs more lines THEN the system SHALL allow exemptions via `.file-size-exemptions`
