# Eye of God UIX — Requirements Document

## Document Control

| Field | Value |
|-------|-------|
| **Document ID** | SA01-EOG-REQ-2025-12 |
| **Version** | 3.0 |
| **Date** | 2025-12-21 |
| **Status** | CANONICAL |
| **Classification** | ENTERPRISE |
| **Derived From** | SA01-EOG-SRS-2025-12 |

---

## 1. Introduction

This document defines the EARS-format requirements for the **Eye of God (EOG)** unified interface architecture. All requirements are derived from the Software Requirements Specification (SRS.md).

**Key Architecture Decisions:**
- **UI Layer**: Lit 3.x Web Components (MILLIONS of concurrent users)
- **API Layer**: Django Ninja (ALL projects - SomaAgent01, SomaBrain, etc.)
- **MVC Layer**: Django 5.x with PostgreSQL
- **Permissions**: SpiceDB (Google Zanzibar - 1M+ checks/second)
- **Theming**: AgentSkin (REQUIRED - 26+ CSS variables)
- **Voice**: Dual-mode (Local STT/TTS OR AgentVoiceBox for speech-on-speech)

---

## 2. Glossary

| Term | Definition |
|------|------------|
| **Agent_Mode** | Operational state: STD, TRN, ADM, DEV, RO, DGR |
| **AgentSkin** | Theme system using CSS Custom Properties (26+ variables) |
| **AgentVoiceBox** | External voice service with full speech-on-speech capability |
| **Django_Ninja** | Fast async API framework for Django with OpenAPI 3.1 |
| **Kokoro** | Local TTS engine (82M-200M ONNX models, CPU/GPU) |
| **Lit** | Google's Web Components library with reactive properties |
| **Local_Voice** | On-device STT (Whisper) + TTS (Kokoro), NO speech-on-speech |
| **SpiceDB** | Google Zanzibar-based permission system for scale |
| **Whisper** | Local STT engine (OpenAI Whisper, CPU/GPU detection) |

---

## 3. Requirements

### Requirement 1: UI Layer Architecture (Lit Web Components)

**User Story:** As a developer, I want a modular, reactive UI built with Lit Web Components supporting millions of concurrent users, so that I can create fast, encapsulated, and themeable interfaces at scale.

#### Acceptance Criteria

1. THE UI_Layer SHALL use Lit 3.x Web Components with Shadow DOM encapsulation
2. WHEN a component renders THEN the UI_Layer SHALL complete rendering within 16ms (60fps)
3. THE UI_Layer SHALL expose reactive properties via Lit's `@property` decorator
4. WHEN theme variables change THEN the UI_Layer SHALL update all components within 50ms
5. THE UI_Layer SHALL lazy-load non-critical components via dynamic imports
6. WHEN the application loads THEN the UI_Layer SHALL achieve First Contentful Paint < 1.5s
7. THE UI_Layer SHALL use CSS Custom Properties for all themeable values
8. WHEN offline THEN the UI_Layer SHALL serve cached assets via Service Worker
9. THE UI_Layer SHALL support 1,000,000+ concurrent WebSocket connections
10. THE UI_Layer SHALL render at 60fps during all user interactions

---

### Requirement 2: Django + Django Ninja Backend (ALL PROJECTS)

**User Story:** As a backend developer, I want a unified Django + Django Ninja architecture across all projects (SomaAgent01, SomaBrain, etc.), so that I can build scalable, maintainable APIs with consistent patterns.

#### Acceptance Criteria

1. THE Backend SHALL use Django 5.x with async ORM support for ALL projects
2. THE Backend SHALL expose all REST APIs via Django Ninja with OpenAPI 3.1 schema
3. WHEN an API request arrives THEN the Backend SHALL respond within 50ms (p95)
4. THE Backend SHALL use Django's migration system for all schema changes
5. WHEN database queries execute THEN the Backend SHALL use connection pooling (pgbouncer)
6. THE Backend SHALL implement CQRS pattern for read-heavy endpoints
7. WHEN WebSocket connections are needed THEN the Backend SHALL use Django Channels 4.x
8. THE Backend SHALL expose Django Admin for superuser operations only
9. THE Backend SHALL handle 100,000+ requests/second per node
10. THE Backend SHALL use Pydantic schemas for all request/response validation

---

### Requirement 3: Permission System (SpiceDB / Google Zanzibar)

**User Story:** As a security architect, I want a globally consistent, high-performance permission system supporting millions of checks per second, so that I can enforce access control at enterprise scale.

#### Acceptance Criteria

1. THE Permission_System SHALL deploy SpiceDB as the permission authority
2. WHEN a permission check executes THEN the Permission_System SHALL respond within 10ms (p95)
3. THE Permission_System SHALL support 1,000,000+ permission checks per second
4. WHEN SpiceDB is unavailable THEN the Permission_System SHALL deny all requests (fail-closed)
5. THE Permission_System SHALL cache permission decisions in Redis with TTL 60s
6. WHEN a role changes THEN the Permission_System SHALL propagate changes within 5 seconds
7. THE Permission_System SHALL support hierarchical role inheritance
8. THE Permission_System SHALL provide default roles: SysAdmin, Admin, Developer, Trainer, User, Viewer
9. WHEN a user requests an action THEN the Permission_System SHALL verify tenant isolation

---

### Requirement 4: AgentSkin Theme System (REQUIRED)

**User Story:** As a user, I want to customize the visual appearance using the AgentSkin theme system, so that I can personalize my workspace with validated, secure themes.

#### Acceptance Criteria

1. THE Theme_System SHALL use CSS Custom Properties for all themeable values (26 variables minimum)
2. WHEN theme is applied THEN the Theme_System SHALL inject variables within 50ms
3. THE Theme_System SHALL support theme JSON format with name, version, author, variables
4. WHEN theme file is dropped THEN the Theme_System SHALL validate against JSON Schema
5. THE Theme_System SHALL persist active theme to localStorage
6. WHEN theme contains `url()` in CSS values THEN the Theme_System SHALL reject (XSS prevention)
7. THE Theme_System SHALL provide default themes: Default Light, Midnight Dark, High Contrast
8. THE Theme_System SHALL support remote theme loading via HTTPS only
9. WHEN theme is previewed THEN the Theme_System SHALL show split-screen comparison
10. THE Theme_System SHALL validate WCAG AA contrast ratios (4.5:1 minimum)
11. THE Theme_System SHALL enforce rate limiting (10 uploads/hour/user)

---

### Requirement 5: Local Voice System (STT + TTS)

**User Story:** As a user, I want to use local voice capabilities (Whisper STT + Kokoro TTS) running on my device, so that I can have voice input/output without external dependencies.

#### Acceptance Criteria

1. THE Local_Voice SHALL provide STT via Whisper (CPU or GPU auto-detection)
2. THE Local_Voice SHALL provide TTS via Kokoro (CPU or GPU auto-detection)
3. THE Local_Voice SHALL NOT support real-time speech-on-speech (use AgentVoiceBox for that)
4. WHEN GPU is available THEN the Local_Voice SHALL use CUDA-optimized models
5. WHEN GPU is unavailable THEN the Local_Voice SHALL fallback to CPU models
6. THE Local_Voice SHALL support Whisper model sizes: tiny, base, small, medium, large
7. THE Local_Voice SHALL support Kokoro model sizes: 82M, 200M
8. WHEN voice is enabled THEN the Local_Voice SHALL preload models at startup
9. THE Local_Voice SHALL support 15+ languages via Kokoro TTS
10. THE Local_Voice SHALL detect hardware architecture at Docker build time

---

### Requirement 6: AgentVoiceBox Integration (Speech-on-Speech)

**User Story:** As a user, I want full real-time speech-on-speech capability via AgentVoiceBox, so that I can have natural voice conversations with the agent.

#### Acceptance Criteria

1. THE AgentVoiceBox SHALL provide full real-time speech-on-speech capability
2. THE AgentVoiceBox SHALL connect via WebSocket to /v1/realtime endpoint
3. THE AgentVoiceBox SHALL support OpenAI Realtime API protocol compatibility
4. THE AgentVoiceBox SHALL support bidirectional audio streaming
5. WHEN AgentVoiceBox is active THEN the System SHALL achieve latency < 150ms end-to-end
6. THE AgentVoiceBox SHALL support turn detection and interruption handling
7. THE AgentVoiceBox SHALL support dual VAD (WebRTC + Silero)
8. THE AgentVoiceBox SHALL support noise reduction and AGC
9. WHEN AgentVoiceBox is local THEN the System SHALL connect to localhost
10. WHEN AgentVoiceBox is remote THEN the System SHALL connect via configured URL
11. THE AgentVoiceBox SHALL support 1000+ concurrent voice sessions per server

---

### Requirement 7: Voice Provider Selection

**User Story:** As a user, I want to choose between Local Voice and AgentVoiceBox in Settings, so that I can select the voice capability that fits my needs.

#### Acceptance Criteria

1. THE Settings SHALL allow user to select voice provider: local, agentvoicebox, or disabled
2. WHEN provider is "local" THEN the System SHALL use Local_Voice for STT/TTS only
3. WHEN provider is "agentvoicebox" THEN the System SHALL use AgentVoiceBox for full speech-on-speech
4. WHEN provider is "disabled" THEN the System SHALL hide all voice UI elements
5. THE Settings SHALL show provider-specific configuration fields dynamically
6. WHEN provider changes THEN the System SHALL validate new configuration
7. THE Settings SHALL provide "Test Connection" button for AgentVoiceBox
8. WHEN test connection succeeds THEN the Settings SHALL show green checkmark
9. THE Settings SHALL include Voice/Speech section in Connectivity tab
10. WHEN voice provider changes THEN the System SHALL emit settings.changed event

---

### Requirement 8: Mode State Management

**User Story:** As a user, I want to switch between agent modes (STD, TRN, ADM, DEV, RO, DGR) based on my permissions, so that I can access appropriate features for my role.

#### Acceptance Criteria

1. THE Mode_Manager SHALL maintain current mode state per session
2. WHEN mode changes THEN the Mode_Manager SHALL emit `mode.changed` event via WebSocket
3. THE Mode_Manager SHALL persist mode preference per user in PostgreSQL
4. WHEN session starts THEN the Mode_Manager SHALL restore last mode if permitted
5. WHEN user requests mode change THEN the Mode_Manager SHALL verify permissions via SpiceDB
6. IF user lacks permission for target mode THEN the Mode_Manager SHALL reject with HTTP 403
7. WHEN transitioning to DEGRADED mode THEN the Mode_Manager SHALL NOT require user action
8. THE Mode_Manager SHALL log all mode transitions to audit trail
9. THE Mode_Manager SHALL support modes: STD, TRN, ADM, DEV, RO, DGR
10. WHEN mode is DEGRADED THEN the Mode_Manager SHALL disable non-essential features

---

### Requirement 9: Settings Management

**User Story:** As a user, I want to configure agent settings through a tabbed interface with proper validation and persistence, so that I can customize the agent behavior.

#### Acceptance Criteria

1. THE Settings_Manager SHALL organize settings into tabs: Agent, External, Connectivity, System
2. WHEN settings are modified THEN the Settings_Manager SHALL persist to PostgreSQL immediately
3. THE Settings_Manager SHALL validate all inputs against JSON Schema before saving
4. WHEN sensitive fields are displayed THEN the Settings_Manager SHALL mask values with asterisks
5. THE Settings_Manager SHALL support field types: text, password, select, toggle, slider, number, json, file
6. WHEN API keys are saved THEN the Settings_Manager SHALL store in Vault (not PostgreSQL)
7. THE Settings_Manager SHALL emit `settings.changed` event after successful save
8. WHEN settings change THEN the Settings_Manager SHALL trigger agent config reload
9. THE Settings_Manager SHALL include Voice/Speech section in Connectivity tab
10. WHEN voice provider changes THEN the Settings_Manager SHALL show provider-specific fields
11. THE Settings_Manager SHALL support optimistic locking via version field
12. WHEN concurrent edit detected THEN the Settings_Manager SHALL show conflict resolution UI

---

### Requirement 10: Real-Time Communication

**User Story:** As a user, I want real-time updates via WebSocket for mode changes, settings updates, and voice events, so that I can see changes immediately without refreshing.

#### Acceptance Criteria

1. THE Realtime_System SHALL use WebSocket for bidirectional communication
2. WHEN server event occurs THEN the Realtime_System SHALL deliver to client within 100ms
3. THE Realtime_System SHALL support SSE fallback when WebSocket unavailable
4. WHEN connection drops THEN the Realtime_System SHALL reconnect with exponential backoff
5. THE Realtime_System SHALL send heartbeat every 20 seconds
6. WHEN client reconnects THEN the Realtime_System SHALL replay missed events
7. THE Realtime_System SHALL support event types: mode.changed, settings.changed, theme.changed, voice.*
8. THE Realtime_System SHALL authenticate WebSocket connections via token
9. THE Realtime_System SHALL support 10,000 concurrent connections per node
10. WHEN WebSocket fails THEN the Realtime_System SHALL fallback to SSE automatically

---

### Requirement 11: Multi-Tenancy

**User Story:** As a platform operator, I want complete tenant isolation for data, settings, and permissions, so that I can serve multiple organizations securely.

#### Acceptance Criteria

1. THE Multi_Tenancy SHALL isolate all data by tenant_id
2. WHEN request arrives THEN the Multi_Tenancy SHALL extract tenant from X-Tenant-Id header
3. THE Multi_Tenancy SHALL enforce tenant isolation in all database queries
4. WHEN user accesses resource THEN the Multi_Tenancy SHALL verify tenant membership via SpiceDB
5. THE Multi_Tenancy SHALL support tenant-specific themes and settings
6. WHEN tenant is created THEN the Multi_Tenancy SHALL provision default roles and settings
7. THE Multi_Tenancy SHALL support tenant hierarchy (parent/child tenants)
8. WHEN tenant is deleted THEN the Multi_Tenancy SHALL cascade delete all tenant data
9. THE Multi_Tenancy SHALL support cross-tenant queries for SYSADMIN only
10. THE Multi_Tenancy SHALL log all cross-tenant access to audit trail

---

### Requirement 12: Security

**User Story:** As a security architect, I want comprehensive security controls including authentication, authorization, input validation, and audit logging, so that I can protect the system from attacks.

#### Acceptance Criteria

1. THE API_Security SHALL require Bearer token authentication for all endpoints
2. WHEN request lacks valid token THEN the API_Security SHALL return HTTP 401
3. THE API_Security SHALL enforce rate limiting (120 requests/minute default)
4. WHEN rate limit exceeded THEN the API_Security SHALL return HTTP 429 with Retry-After
5. THE API_Security SHALL validate all inputs against JSON Schema
6. WHEN SQL injection attempted THEN the API_Security SHALL reject with HTTP 400
7. THE API_Security SHALL set CSP headers: default-src 'self'; style-src 'self' 'unsafe-inline'
8. THE API_Security SHALL log all authentication failures to audit trail
9. WHEN XSS payload detected THEN the API_Security SHALL sanitize and reject
10. THE System SHALL store all secrets in Vault (not PostgreSQL)
11. THE API_Security SHALL enforce HTTPS for all external connections
12. THE API_Security SHALL support JWT token refresh without re-authentication

---

### Requirement 13: Observability

**User Story:** As an operations engineer, I want comprehensive metrics, tracing, and logging, so that I can monitor system health and troubleshoot issues.

#### Acceptance Criteria

1. THE Observability SHALL expose Prometheus metrics on /metrics endpoint
2. THE Observability SHALL track: request_count, request_duration, error_rate, active_connections
3. WHEN error occurs THEN the Observability SHALL increment error counter with labels
4. THE Observability SHALL support OpenTelemetry tracing with trace_id propagation
5. THE Observability SHALL log structured JSON to stdout
6. WHEN latency exceeds SLO THEN the Observability SHALL emit alert
7. THE Observability SHALL track theme_loads_total, permission_checks_total, mode_transitions_total
8. THE Observability SHALL provide Grafana dashboard templates
9. THE Observability SHALL track voice_sessions_total, voice_latency_seconds
10. THE Observability SHALL support distributed tracing across all services

---

### Requirement 14: Performance (MILLIONS OF USERS)

**User Story:** As a platform architect, I want the system to support millions of concurrent users with sub-second response times, so that I can serve enterprise-scale deployments.

#### Acceptance Criteria

1. THE System SHALL support 1,000,000+ concurrent WebSocket connections
2. THE System SHALL achieve First Contentful Paint < 1.5 seconds
3. THE System SHALL achieve Time to Interactive < 3 seconds
4. WHEN theme switches THEN the System SHALL complete transition < 300ms
5. THE API_Layer SHALL achieve response time < 50ms (p95)
6. THE Permission_System SHALL achieve check time < 10ms (p95)
7. THE System SHALL support 10,000 concurrent WebSocket connections per node
8. WHEN under load THEN the System SHALL maintain 99.9% availability
9. THE System SHALL achieve Lighthouse score > 90 for all categories
10. THE Django_Ninja_API SHALL handle 100,000+ requests/second per node
11. THE Lit_UI SHALL render 60fps during all interactions
12. THE System SHALL support horizontal scaling via Kubernetes

---

### Requirement 15: Accessibility

**User Story:** As a user with disabilities, I want the interface to be fully accessible via keyboard, screen readers, and high contrast modes, so that I can use the system effectively.

#### Acceptance Criteria

1. THE Accessibility SHALL comply with WCAG 2.1 AA standards
2. THE Accessibility SHALL support keyboard navigation for all interactive elements
3. WHEN focus changes THEN the Accessibility SHALL show visible focus indicator
4. THE Accessibility SHALL provide ARIA labels for all controls
5. THE Accessibility SHALL support screen readers (NVDA, VoiceOver, JAWS)
6. WHEN color is used for meaning THEN the Accessibility SHALL provide alternative indicator
7. THE Accessibility SHALL support reduced motion preference
8. THE Accessibility SHALL maintain contrast ratio >= 4.5:1 for all text
9. THE Accessibility SHALL provide skip navigation links
10. THE Accessibility SHALL support text scaling up to 200%

---

### Requirement 16: Cognitive Panel

**User Story:** As a trainer, I want to view and adjust cognitive parameters (neuromodulators, adaptation weights, learning rate), so that I can fine-tune agent behavior.

#### Acceptance Criteria

1. THE Cognitive_Panel SHALL display current neuromodulator levels (dopamine, serotonin, noradrenaline, acetylcholine)
2. WHEN user has TRN or ADM mode THEN the Cognitive_Panel SHALL allow editing neuromodulators
3. THE Cognitive_Panel SHALL display adaptation weights (alpha, beta, gamma, tau)
4. THE Cognitive_Panel SHALL display learning rate with slider control
5. WHEN cognitive parameters change THEN the Cognitive_Panel SHALL call SomaBrain API
6. THE Cognitive_Panel SHALL display cognitive load indicator
7. WHEN cognitive load > 0.8 THEN the Cognitive_Panel SHALL show sleep cycle recommendation
8. THE Cognitive_Panel SHALL provide "Trigger Sleep Cycle" button for TRN/ADM modes
9. THE Cognitive_Panel SHALL display real-time parameter updates via WebSocket
10. THE Cognitive_Panel SHALL validate parameter ranges before submission

---

### Requirement 17: Memory Browser

**User Story:** As a user, I want to browse, search, and manage agent memories, so that I can understand what the agent knows and curate its knowledge.

#### Acceptance Criteria

1. THE Memory_Browser SHALL display memories in paginated list view
2. THE Memory_Browser SHALL support semantic search via query input
3. WHEN memory is selected THEN the Memory_Browser SHALL show full payload details
4. THE Memory_Browser SHALL display memory metadata (timestamp, type, score)
5. WHEN user has ADM mode THEN the Memory_Browser SHALL allow memory deletion
6. WHEN user has ADM mode THEN the Memory_Browser SHALL allow memory export (JSON)
7. THE Memory_Browser SHALL support filtering by memory type (episodic, semantic)
8. THE Memory_Browser SHALL support filtering by date range
9. THE Memory_Browser SHALL display memory count and storage usage
10. THE Memory_Browser SHALL call SomaBrain /recall endpoint for search

---

### Requirement 18: Audit Log Viewer

**User Story:** As an administrator, I want to view audit logs of all system actions, so that I can track user activity and investigate incidents.

#### Acceptance Criteria

1. THE Audit_Viewer SHALL display audit logs in paginated table view
2. THE Audit_Viewer SHALL support filtering by user, action, resource, timestamp
3. THE Audit_Viewer SHALL display: timestamp, user, action, resource, result, details
4. WHEN audit entry is selected THEN the Audit_Viewer SHALL show full JSON payload
5. THE Audit_Viewer SHALL support export to CSV/JSON
6. THE Audit_Viewer SHALL require ADM or SYSADMIN mode
7. THE Audit_Viewer SHALL support real-time streaming of new entries
8. THE Audit_Viewer SHALL retain logs for configurable period (default 90 days)
9. THE Audit_Viewer SHALL support search across all fields
10. THE Audit_Viewer SHALL display log volume metrics

---

### Requirement 19: Tool Catalog

**User Story:** As a user, I want to browse available tools and their permissions, so that I can understand what capabilities the agent has.

#### Acceptance Criteria

1. THE Tool_Catalog SHALL display all available tools in card grid view
2. THE Tool_Catalog SHALL show tool name, description, category, required mode
3. WHEN tool is selected THEN the Tool_Catalog SHALL show full documentation
4. THE Tool_Catalog SHALL indicate which tools are available in current mode
5. THE Tool_Catalog SHALL support filtering by category
6. THE Tool_Catalog SHALL support search by name/description
7. WHEN user has DEV mode THEN the Tool_Catalog SHALL show tool configuration
8. THE Tool_Catalog SHALL display tool usage statistics
9. THE Tool_Catalog SHALL group tools by category: execution, memory, communication, browser
10. THE Tool_Catalog SHALL show tool dependencies and requirements

---

### Requirement 20: Desktop Application (Tauri)

**User Story:** As a user, I want a native desktop application with system tray integration, so that I can access the agent without a browser.

#### Acceptance Criteria

1. THE Desktop_App SHALL use Tauri 2.0 with shared Lit components
2. THE Desktop_App SHALL support Windows, macOS, and Linux
3. THE Desktop_App SHALL provide system tray icon with quick actions
4. THE Desktop_App SHALL support global hotkey for activation
5. THE Desktop_App SHALL support native notifications
6. THE Desktop_App SHALL support offline mode with cached data
7. THE Desktop_App SHALL auto-update via Tauri updater
8. THE Desktop_App SHALL support deep linking (soma://...)
9. THE Desktop_App SHALL share authentication with web version
10. THE Desktop_App SHALL support local voice (Whisper/Kokoro) natively

---

### Requirement 21: CLI Dashboard (Ratatui)

**User Story:** As a developer, I want a terminal-based dashboard for monitoring and quick interactions, so that I can work without leaving the terminal.

#### Acceptance Criteria

1. THE CLI_Dashboard SHALL use Rust + Ratatui for terminal UI
2. THE CLI_Dashboard SHALL display agent status, mode, and health
3. THE CLI_Dashboard SHALL support quick chat input
4. THE CLI_Dashboard SHALL display streaming responses
5. THE CLI_Dashboard SHALL support keyboard shortcuts for common actions
6. THE CLI_Dashboard SHALL display memory usage and cognitive load
7. THE CLI_Dashboard SHALL support mode switching via keyboard
8. THE CLI_Dashboard SHALL connect via same API as web/desktop
9. THE CLI_Dashboard SHALL support configuration via TOML file
10. THE CLI_Dashboard SHALL support piping input/output for scripting

---

### Requirement 22: Django Migration (SomaAgent01)

**User Story:** As a developer, I want SomaAgent01 to migrate from FastAPI to Django Ninja while maintaining backward compatibility, so that I can benefit from Django's ecosystem.

#### Acceptance Criteria

1. THE Migration SHALL run Django Ninja parallel to FastAPI during transition
2. THE Django_Ninja_API SHALL be available at /api/v2/*
3. THE FastAPI SHALL remain at /v1/* during 6-month transition period
4. THE Django_Ninja SHALL achieve feature parity with FastAPI
5. THE Migration SHALL use nginx for traffic routing between versions
6. WHEN feature parity achieved THEN the Migration SHALL begin traffic migration
7. THE Migration SHALL support rollback to FastAPI if issues detected
8. THE Migration SHALL maintain all existing integrations
9. THE Django_Ninja SHALL use same authentication tokens as FastAPI
10. THE Migration SHALL complete within 6-month overlap period

---

### Requirement 23: Django Migration (SomaBrain)

**User Story:** As a developer, I want SomaBrain to migrate from FastAPI to Django Ninja, so that I can have a unified backend stack across all projects.

#### Acceptance Criteria

1. THE SomaBrain SHALL migrate from FastAPI to Django Ninja
2. THE SomaBrain SHALL expose /api/v2/remember endpoint
3. THE SomaBrain SHALL expose /api/v2/recall endpoint
4. THE SomaBrain SHALL expose /api/v2/neuromodulators endpoint
5. THE SomaBrain SHALL expose /api/v2/sleep/* endpoints
6. THE SomaBrain SHALL expose /api/v2/context/* endpoints
7. THE SomaBrain gRPC service SHALL remain for high-performance memory operations
8. THE Migration SHALL maintain backward compatibility with existing clients
9. THE Django_Ninja SHALL use same Pydantic schemas as FastAPI
10. THE Migration SHALL follow same parallel deployment strategy as SomaAgent01

---

### Requirement 24: Infrastructure (Docker/Kubernetes)

**User Story:** As a DevOps engineer, I want containerized deployment with auto-scaling and zero-downtime updates, so that I can operate the system reliably at scale.

#### Acceptance Criteria

1. THE System SHALL detect CPU/GPU architecture at Docker build time
2. THE System SHALL build appropriate Docker images for detected architecture
3. THE System SHALL support horizontal scaling via Kubernetes
4. THE System SHALL support rolling deployments with zero downtime
5. THE System SHALL support health checks for all services
6. THE System SHALL support resource limits and requests
7. THE System SHALL use PostgreSQL 16.x as primary database
8. THE System SHALL use pgbouncer for connection pooling
9. THE System SHALL use Redis 7.x for caching and sessions
10. THE System SHALL use Kafka 3.x for event streaming

---

### Requirement 25: Feature Flags

**User Story:** As an administrator, I want to enable/disable features via feature flags, so that I can control feature rollout and manage system capabilities.

#### Acceptance Criteria

1. THE Feature_Flags SHALL support flags: sse_enabled, embeddings_ingest, semantic_recall, content_masking
2. THE Feature_Flags SHALL support flags: audio_support, browser_support, code_exec, vision_support
3. THE Feature_Flags SHALL support flags: mcp_client, mcp_server, learning_context, tool_sandboxing
4. THE Feature_Flags SHALL support flags: streaming_responses, delegation, voice_local, voice_agentvoicebox
5. THE Feature_Flags SHALL support feature profiles: minimal, standard, enhanced, max
6. WHEN profile is selected THEN the Feature_Flags SHALL apply all profile flags
7. THE Feature_Flags SHALL persist to PostgreSQL per tenant
8. WHEN flag changes THEN the Feature_Flags SHALL emit settings.changed event
9. THE Feature_Flags SHALL support override at user level
10. THE Feature_Flags SHALL be editable in System tab of Settings (ADM mode only)

---

## 4. Traceability Matrix

| Requirement | SRS Section | Priority | Status |
|-------------|-------------|----------|--------|
| REQ-1: UI Layer | 8.1 | P0 | DEFINED |
| REQ-2: Django Backend | 8.2, 11 | P0 | DEFINED |
| REQ-3: SpiceDB Permissions | 8.3 | P0 | DEFINED |
| REQ-4: AgentSkin Theme | 6, 8.4 | P0 | DEFINED |
| REQ-5: Local Voice | 7, 10.1 | P1 | DEFINED |
| REQ-6: AgentVoiceBox | 7, 10.2 | P1 | DEFINED |
| REQ-7: Voice Provider Selection | 10.3 | P1 | DEFINED |
| REQ-8: Mode State Management | 3, 8.7 | P0 | DEFINED |
| REQ-9: Settings Management | 5, 8.6 | P0 | DEFINED |
| REQ-10: Real-Time Communication | 8.8 | P0 | DEFINED |
| REQ-11: Multi-Tenancy | 9.3 | P0 | DEFINED |
| REQ-12: Security | 9.2 | P0 | DEFINED |
| REQ-13: Observability | 9.5 | P1 | DEFINED |
| REQ-14: Performance | 9.1 | P0 | DEFINED |
| REQ-15: Accessibility | 9.4 | P1 | DEFINED |
| REQ-16: Cognitive Panel | 5 | P1 | DEFINED |
| REQ-17: Memory Browser | 5 | P1 | DEFINED |
| REQ-18: Audit Log Viewer | 9.5 | P2 | DEFINED |
| REQ-19: Tool Catalog | 5 | P2 | DEFINED |
| REQ-20: Desktop (Tauri) | 1.2 | P2 | DEFINED |
| REQ-21: CLI (Ratatui) | 1.2 | P2 | DEFINED |
| REQ-22: Django Migration (SA01) | 11.2 | P0 | DEFINED |
| REQ-23: Django Migration (SomaBrain) | 11.3 | P1 | DEFINED |
| REQ-24: Infrastructure | 12 | P0 | DEFINED |
| REQ-25: Feature Flags | 5.3 | P1 | DEFINED |

---

## 5. Document Approval

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Product Owner | | | |
| Tech Lead | | | |
| Security Lead | | | |
| QA Lead | | | |

---

**Document Status:** COMPLETE - Ready for Review

**Next Steps:**
1. Review requirements with stakeholders
2. Complete design.md with detailed architecture
3. Create tasks.md with implementation plan
