# Requirements Document

## Introduction

This specification defines the requirements for completing the Web UI architecture modernization for SomaAgent01. The Web UI has been partially refactored to a state-of-the-art modular architecture with Alpine.js, but several features remain disconnected from backend endpoints and the architecture needs completion.

### Goals

1. Complete the feature module architecture for all UI capabilities
2. Align all UI actions with real backend endpoints
3. Implement missing backend endpoints required by the UI
4. Ensure 100% VIBE Coding Rules compliance (no mocks, no stubs)
5. Achieve full Playwright test coverage for all UI features
6. Document the complete architecture for maintainability

### Current Architecture Status

**Working Correctly (VIBE Compliant ✅):**
- Core layer (`webui/core/`) with API client, endpoints, store factory
- Settings feature module with modal, tabs, sections
- Chat feature module with store and API wrapper
- Notifications feature module with toast system
- Playwright tests for Settings modal (8 tests passing)
- Playwright tests for Upload functionality (2 tests passing)
- Gateway health check returns `{"healthy": true}`
- Settings endpoint returns 17 sections

**Incomplete/Missing (VIBE Non-Compliant ❌):**
- Chat backend endpoint `/v1/session/message` not implemented
- Load Chat, New Chat, Save Chat actions not wired to backend
- Restart Agent action not connected
- Memory Dashboard not integrated
- File Browser not integrated
- Voice subsystem UI not connected
- SSE streaming not fully integrated with chat store
- No feature module for Memory operations
- No feature module for Scheduler/Tasks
- No feature module for System Health/Degradation

### VIBE Compliance Score

| Area | Current | Target | Gap |
|------|---------|--------|-----|
| Core Layer | 100% | 100% | ✅ |
| Settings Feature | 100% | 100% | ✅ |
| Chat Feature | 60% | 100% | Backend endpoint |
| Notifications Feature | 100% | 100% | ✅ |
| Memory Feature | 0% | 100% | Missing |
| Scheduler Feature | 0% | 100% | Missing |
| Health Feature | 0% | 100% | Missing |
| Upload Feature | 80% | 100% | Integration |
| Playwright Tests | 70% | 100% | Coverage |
| **Overall** | **~55%** | **100%** | **45%** |

## Glossary

- **Alpine.js**: Lightweight reactive JavaScript framework used for UI state management
- **Feature Module**: Self-contained module with store, API, and public exports
- **Store**: Reactive state container created via `createStore()` factory
- **SSE**: Server-Sent Events for real-time streaming from backend
- **Gateway**: FastAPI HTTP gateway serving the UI and routing to backend services
- **VIBE**: Verification, Implementation, Behavior, Execution coding rules
- **Playwright**: End-to-end testing framework for browser automation

## Requirements

### Requirement 1: Chat Backend Integration

**User Story:** As a user, I want to send messages and receive responses in the chat interface, so that I can interact with the AI agent.

#### Acceptance Criteria

1. WHEN a user sends a message via the chat input THEN the System SHALL POST to `/v1/session/message` with the message content and session ID
2. WHEN the backend receives a message THEN the System SHALL return an SSE stream with assistant responses
3. WHEN SSE events are received THEN the System SHALL update the chat store with message content
4. WHEN the assistant is streaming THEN the System SHALL display a typing indicator and progressive content
5. WHEN the stream completes THEN the System SHALL mark the message as final and enable new input

### Requirement 2: Session Management

**User Story:** As a user, I want to manage chat sessions (create, load, save, delete), so that I can organize my conversations.

#### Acceptance Criteria

1. WHEN a user clicks "New Chat" THEN the System SHALL create a new session via POST `/v1/sessions`
2. WHEN a user clicks "Load Chat" THEN the System SHALL fetch available sessions via GET `/v1/sessions`
3. WHEN a user selects a session THEN the System SHALL load history via GET `/v1/sessions/{id}/history`
4. WHEN a user clicks "Save Chat" THEN the System SHALL persist the session via PUT `/v1/sessions/{id}`
5. WHEN a user deletes a session THEN the System SHALL remove it via DELETE `/v1/sessions/{id}`

### Requirement 3: Memory Feature Module

**User Story:** As a user, I want to access the Memory Dashboard, so that I can view and manage stored memories.

#### Acceptance Criteria

1. WHEN the Memory feature module is created THEN the System SHALL include `memory.store.js` for state management
2. WHEN the Memory feature module is created THEN the System SHALL include `memory.api.js` for backend calls
3. WHEN a user opens Memory Dashboard THEN the System SHALL fetch memories via GET `/v1/memory`
4. WHEN a user searches memories THEN the System SHALL query via POST `/v1/memory/search`
5. WHEN a user deletes a memory THEN the System SHALL remove it via DELETE `/v1/memory/{id}`

### Requirement 4: Scheduler Feature Module

**User Story:** As a user, I want to view and manage scheduled tasks, so that I can automate agent actions.

#### Acceptance Criteria

1. WHEN the Scheduler feature module is created THEN the System SHALL include `scheduler.store.js` for state management
2. WHEN the Scheduler feature module is created THEN the System SHALL include `scheduler.api.js` for backend calls
3. WHEN a user opens Scheduler tab THEN the System SHALL fetch tasks via GET `/v1/scheduler/tasks`
4. WHEN a user creates a task THEN the System SHALL POST to `/v1/scheduler/tasks`
5. WHEN a user deletes a task THEN the System SHALL DELETE `/v1/scheduler/tasks/{id}`

### Requirement 5: Health/Status Feature Module

**User Story:** As a user, I want to see system health status, so that I know if services are operational.

#### Acceptance Criteria

1. WHEN the Health feature module is created THEN the System SHALL include `health.store.js` for state management
2. WHEN the Health feature module is created THEN the System SHALL include `health.api.js` for backend calls
3. WHEN the UI loads THEN the System SHALL fetch health via GET `/v1/health`
4. WHEN SomaBrain is offline THEN the System SHALL display a degradation banner
5. WHEN services recover THEN the System SHALL update the health status automatically

### Requirement 6: Upload Feature Module

**User Story:** As a user, I want to upload files to the agent, so that I can share documents and images.

#### Acceptance Criteria

1. WHEN the Upload feature module is created THEN the System SHALL include `upload.store.js` for state management
2. WHEN the Upload feature module is created THEN the System SHALL include `upload.api.js` for backend calls
3. WHEN a user selects a file THEN the System SHALL upload via POST `/v1/uploads`
4. WHEN upload completes THEN the System SHALL display the attachment in the chat
5. WHEN upload fails THEN the System SHALL display an error notification

### Requirement 7: SSE Integration

**User Story:** As a user, I want real-time updates from the agent, so that I see responses as they stream.

#### Acceptance Criteria

1. WHEN the chat connects THEN the System SHALL establish an SSE connection to `/v1/session/{id}/events`
2. WHEN `assistant.delta` events arrive THEN the System SHALL append content to the current message
3. WHEN `assistant.final` events arrive THEN the System SHALL mark the message complete
4. WHEN `system.keepalive` events arrive THEN the System SHALL update connection status
5. WHEN the connection drops THEN the System SHALL attempt reconnection with exponential backoff

### Requirement 8: Agent Control Actions

**User Story:** As a user, I want to control the agent (restart, pause), so that I can manage its behavior.

#### Acceptance Criteria

1. WHEN a user clicks "Restart" THEN the System SHALL POST to `/v1/agent/restart`
2. WHEN a user clicks "Pause" THEN the System SHALL POST to `/v1/agent/pause`
3. WHEN the agent restarts THEN the System SHALL display a notification
4. WHEN the agent is paused THEN the System SHALL update the UI to show paused state

### Requirement 9: Playwright Test Coverage

**User Story:** As a developer, I want comprehensive Playwright tests, so that UI functionality is verified.

#### Acceptance Criteria

1. WHEN tests run THEN the System SHALL verify Settings modal functionality (existing)
2. WHEN tests run THEN the System SHALL verify Upload functionality (existing)
3. WHEN tests run THEN the System SHALL verify Chat message sending
4. WHEN tests run THEN the System SHALL verify Session management
5. WHEN tests run THEN the System SHALL verify Health status display

### Requirement 10: Error Handling and Notifications

**User Story:** As a user, I want clear error messages, so that I understand when something goes wrong.

#### Acceptance Criteria

1. WHEN an API call fails THEN the System SHALL display a toast notification with the error
2. WHEN the network is offline THEN the System SHALL display an offline banner
3. WHEN validation fails THEN the System SHALL highlight the invalid field
4. WHEN an operation succeeds THEN the System SHALL display a success notification
5. WHEN errors occur THEN the System SHALL log them to the console with context

### Requirement 11: Backward Compatibility

**User Story:** As a developer, I want the new architecture to maintain backward compatibility, so that existing code continues to work.

#### Acceptance Criteria

1. WHEN legacy code uses `config.js` THEN the System SHALL re-export from `core/api/endpoints.js`
2. WHEN legacy code uses `settingsModalProxy` THEN the System SHALL provide the proxy globally
3. WHEN legacy code uses `fetchApi` THEN the System SHALL expose it on `globalThis`
4. WHEN legacy event bus is used THEN the System SHALL route to the new event system
5. WHEN Alpine stores are accessed directly THEN the System SHALL return the correct store

### Requirement 12: Documentation

**User Story:** As a developer, I want clear architecture documentation, so that I can understand and extend the codebase.

#### Acceptance Criteria

1. WHEN ARCHITECTURE.md is updated THEN the System SHALL document all feature modules
2. WHEN a new feature is added THEN the System SHALL include JSDoc comments
3. WHEN API endpoints are used THEN the System SHALL reference them in endpoint definitions
4. WHEN stores are created THEN the System SHALL document their state shape
5. WHEN tests are written THEN the System SHALL include descriptive test names

