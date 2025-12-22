# Eye of God UIX — Implementation Tasks

## Document Control

| Field | Value |
|-------|-------|
| **Document ID** | SA01-EOG-TASKS-2025-12 |
| **Version** | 1.0 |
| **Date** | 2025-12-21 |
| **Status** | CANONICAL |
| **Implements** | SA01-EOG-UI-ARCH-2025-12 |

---

## Task Overview

| Phase | Tasks | Duration | Dependencies |
|-------|-------|----------|--------------|
| Phase 1: Foundation | 1-8 | 2 weeks | None |
| Phase 2: Core Features | 9-16 | 2 weeks | Phase 1 |
| Phase 3: Voice Integration | 17-22 | 2 weeks | Phase 2 |
| Phase 4: Advanced Features | 23-28 | 2 weeks | Phase 3 |
| Phase 5: Optimization | 29-34 | 2 weeks | Phase 4 |

---

## Phase 1: Foundation

### Task 1: Django Project Setup
- [ ] Create Django 5.x project structure at `somaAgent01/ui/backend/`
- [ ] Configure settings for development and production
- [ ] Set up Django Ninja API router
- [ ] Configure ASGI with Django Channels
- [ ] Add PostgreSQL connection with pgbouncer
- [ ] Add Redis connection for caching and channels

**Files:**
- `ui/backend/eog/settings/base.py`
- `ui/backend/eog/settings/development.py`
- `ui/backend/eog/settings/production.py`
- `ui/backend/eog/urls.py`
- `ui/backend/eog/asgi.py`
- `ui/backend/api/router.py`

**Acceptance Criteria:**
- Django server starts on port 8020
- `/api/v2/health` returns 200 OK
- `/api/v2/docs` shows OpenAPI documentation

---

### Task 2: SpiceDB Integration
- [ ] Deploy SpiceDB container in docker-compose
- [ ] Create permission schema (schema.zed)
- [ ] Implement SpiceDB gRPC client
- [ ] Create `@require_permission` decorator
- [ ] Add permission caching with Redis (TTL 60s)
- [ ] Implement fail-closed behavior

**Files:**
- `ui/backend/permissions/schema.zed`
- `ui/backend/permissions/client.py`
- `ui/backend/permissions/decorators.py`
- `docker-compose.yml` (SpiceDB service)

**Acceptance Criteria:**
- Permission checks complete in < 10ms (p95)
- Fail-closed when SpiceDB unavailable
- Cache invalidation on role changes

---

### Task 3: Lit Project Setup
- [ ] Initialize Lit 3.x project with Vite
- [ ] Configure TypeScript with strict mode
- [ ] Set up @vaadin/router for SPA routing
- [ ] Configure @lit/context for state management
- [ ] Add @lit-labs/signals for reactive state
- [ ] Set up Web Test Runner for testing

**Files:**
- `ui/frontend/package.json`
- `ui/frontend/vite.config.ts`
- `ui/frontend/tsconfig.json`
- `ui/frontend/web-test-runner.config.js`
- `ui/frontend/src/index.ts`

**Acceptance Criteria:**
- `npm run dev` starts dev server with HMR
- `npm run build` produces optimized bundle
- `npm run test` runs component tests

---

### Task 4: Base UI Components
- [ ] Create `eog-button` component
- [ ] Create `eog-input` component
- [ ] Create `eog-select` component
- [ ] Create `eog-toggle` component
- [ ] Create `eog-slider` component
- [ ] Create `eog-spinner` component
- [ ] Create `eog-modal` component
- [ ] Create `eog-toast` component

**Files:**
- `ui/frontend/src/components/eog-button.ts`
- `ui/frontend/src/components/eog-input.ts`
- `ui/frontend/src/components/eog-select.ts`
- `ui/frontend/src/components/eog-toggle.ts`
- `ui/frontend/src/components/eog-slider.ts`
- `ui/frontend/src/components/eog-spinner.ts`
- `ui/frontend/src/components/eog-modal.ts`
- `ui/frontend/src/components/eog-toast.ts`
- `ui/frontend/src/components/index.ts`

**Acceptance Criteria:**
- All components use CSS Custom Properties
- All components have Shadow DOM encapsulation
- All components render in < 16ms

---

### Task 5: Auth Store and Service
- [ ] Create AuthStore with Lit signals
- [ ] Implement login/logout methods
- [ ] Implement session restoration from localStorage
- [ ] Create AuthService for API calls
- [ ] Add JWT token management
- [ ] Create auth context provider

**Files:**
- `ui/frontend/src/stores/auth-store.ts`
- `ui/frontend/src/services/auth-service.ts`
- `ui/backend/api/endpoints/auth.py`
- `ui/backend/api/schemas/auth.py`

**Acceptance Criteria:**
- Login persists token to localStorage
- Session restores on page reload
- Logout clears all auth state

---

### Task 6: WebSocket Client
- [ ] Create WebSocketClient class
- [ ] Implement connection with token auth
- [ ] Add reconnection with exponential backoff
- [ ] Implement heartbeat (20s interval)
- [ ] Add event subscription system
- [ ] Handle connection state changes

**Files:**
- `ui/frontend/src/services/websocket-client.ts`
- `ui/backend/realtime/consumers.py`
- `ui/backend/realtime/routing.py`

**Acceptance Criteria:**
- Reconnects automatically on disconnect
- Heartbeat keeps connection alive
- Events dispatch to subscribers

---

### Task 7: API Client
- [ ] Create base ApiClient class
- [ ] Implement request method with retry logic
- [ ] Add timeout handling (30s default)
- [ ] Implement error handling with ApiError
- [ ] Add token injection from AuthStore
- [ ] Create typed service methods

**Files:**
- `ui/frontend/src/services/api-client.ts`

**Acceptance Criteria:**
- Retries failed requests (3 attempts)
- Throws ApiError with status code
- Injects Bearer token automatically

---

### Task 8: App Shell
- [ ] Create `eog-app` root component
- [ ] Create `eog-header` with mode selector
- [ ] Create `eog-sidebar` with navigation
- [ ] Create `eog-main` router outlet
- [ ] Create `eog-toast-container`
- [ ] Set up route configuration

**Files:**
- `ui/frontend/src/views/eog-app.ts`
- `ui/frontend/src/views/eog-header.ts`
- `ui/frontend/src/views/eog-sidebar.ts`
- `ui/frontend/src/views/eog-main.ts`
- `ui/frontend/public/index.html`

**Acceptance Criteria:**
- App shell renders with header, sidebar, main
- Routes navigate without page reload
- Sidebar collapses on mobile

---

## Phase 2: Core Features

### Task 9: Mode Store and Selector
- [ ] Create ModeStore with available modes
- [ ] Implement mode change with permission check
- [ ] Create `eog-mode-selector` component
- [ ] Add mode persistence per user
- [ ] Emit mode.changed WebSocket event
- [ ] Handle DEGRADED mode transition

**Files:**
- `ui/frontend/src/stores/mode-store.ts`
- `ui/frontend/src/components/eog-mode-selector.ts`
- `ui/backend/api/endpoints/modes.py`
- `ui/backend/api/schemas/modes.py`

**Acceptance Criteria:**
- Mode changes require permission
- Mode persists across sessions
- DEGRADED mode triggers automatically

---

### Task 10: Theme Store and AgentSkin
- [ ] Create ThemeStore with theme list
- [ ] Implement theme application via CSS variables
- [ ] Create theme validation (26 variables, no url())
- [ ] Add contrast ratio validation (WCAG AA)
- [ ] Create `eog-theme-card` component
- [ ] Implement theme preview mode

**Files:**
- `ui/frontend/src/stores/theme-store.ts`
- `ui/frontend/src/utils/theme-loader.ts`
- `ui/frontend/src/styles/agentskin-bridge.css`
- `ui/frontend/src/styles/themes/default-light.json`
- `ui/frontend/src/styles/themes/midnight-dark.json`
- `ui/frontend/src/styles/themes/high-contrast.json`

**Acceptance Criteria:**
- Theme applies in < 50ms
- Invalid themes rejected with errors
- Preview shows split-screen comparison

---

### Task 11: Settings Views
- [ ] Create `eog-settings-view` with tabs
- [ ] Create `eog-settings-agent` tab
- [ ] Create `eog-settings-external` tab
- [ ] Create `eog-settings-connectivity` tab
- [ ] Create `eog-settings-system` tab
- [ ] Implement settings persistence

**Files:**
- `ui/frontend/src/views/eog-settings-view.ts`
- `ui/frontend/src/views/eog-settings-agent.ts`
- `ui/frontend/src/views/eog-settings-external.ts`
- `ui/frontend/src/views/eog-settings-connectivity.ts`
- `ui/frontend/src/views/eog-settings-system.ts`
- `ui/backend/api/endpoints/settings.py`
- `ui/backend/api/schemas/settings.py`

**Acceptance Criteria:**
- Settings save immediately on change
- Sensitive fields masked with asterisks
- API keys stored in Vault (not PostgreSQL)

---

### Task 12: Permission Store
- [ ] Create PermissionStore with cache
- [ ] Implement permission check method
- [ ] Add cache invalidation on role change
- [ ] Create `@can` directive for templates
- [ ] Integrate with SpiceDB client
- [ ] Handle permission denied gracefully

**Files:**
- `ui/frontend/src/stores/permission-store.ts`
- `ui/frontend/src/services/permission-service.ts`
- `ui/frontend/src/utils/can-directive.ts`

**Acceptance Criteria:**
- Permission checks cached for 60s
- UI elements hidden when no permission
- Permission denied shows toast message

---

### Task 13: Chat View
- [ ] Create `eog-chat-view` layout
- [ ] Create `eog-conversation-list` sidebar
- [ ] Create `eog-chat-panel` main area
- [ ] Create `eog-message` component
- [ ] Create `eog-chat-input` with voice button
- [ ] Implement streaming response display

**Files:**
- `ui/frontend/src/views/eog-chat-view.ts`
- `ui/frontend/src/components/eog-conversation-list.ts`
- `ui/frontend/src/components/eog-chat-panel.ts`
- `ui/frontend/src/components/eog-message.ts`
- `ui/frontend/src/components/eog-chat-input.ts`
- `ui/frontend/src/stores/chat-store.ts`

**Acceptance Criteria:**
- Messages stream in real-time
- Conversation history persists
- Voice button integrated in input

---

### Task 14: Chat Backend
- [ ] Create chat endpoint `/api/v2/chat`
- [ ] Implement Kafka message publishing
- [ ] Create WebSocket consumer for responses
- [ ] Handle streaming events (delta, final)
- [ ] Add tool execution markers
- [ ] Implement conversation history

**Files:**
- `ui/backend/api/endpoints/chat.py`
- `ui/backend/api/schemas/chat.py`
- `ui/backend/realtime/consumers.py`
- `ui/backend/realtime/events.py`

**Acceptance Criteria:**
- Chat messages published to Kafka
- Responses stream via WebSocket
- Tool execution shows in UI

---

### Task 15: Themes View
- [ ] Create `eog-themes-view` gallery
- [ ] Create `eog-theme-gallery` grid
- [ ] Create `eog-theme-preview` panel
- [ ] Create `eog-theme-upload` dropzone
- [ ] Implement theme download/install
- [ ] Add theme rating system

**Files:**
- `ui/frontend/src/views/eog-themes-view.ts`
- `ui/frontend/src/components/eog-theme-gallery.ts`
- `ui/frontend/src/components/eog-theme-preview.ts`
- `ui/frontend/src/components/eog-theme-upload.ts`
- `ui/backend/api/endpoints/themes.py`
- `ui/backend/api/schemas/themes.py`

**Acceptance Criteria:**
- Themes display in responsive grid
- Upload validates JSON schema
- Rate limiting (10 uploads/hour)

---

### Task 16: Django Models
- [ ] Create Tenant model
- [ ] Create User model with tenant relation
- [ ] Create Settings model (JSON field)
- [ ] Create Theme model
- [ ] Create FeatureFlag model
- [ ] Create AuditLog model
- [ ] Run migrations

**Files:**
- `ui/backend/core/models/tenant.py`
- `ui/backend/core/models/user.py`
- `ui/backend/core/models/settings.py`
- `ui/backend/core/models/theme.py`
- `ui/backend/core/models/feature_flag.py`
- `ui/backend/core/models/audit_log.py`
- `ui/backend/core/migrations/`

**Acceptance Criteria:**
- All models have proper indexes
- Tenant isolation enforced
- Audit log captures all changes

---

## Phase 3: Voice Integration

### Task 17: Voice Store
- [ ] Create VoiceStore with provider state
- [ ] Implement provider selection (local/agentvoicebox)
- [ ] Add voice state machine (idle/listening/processing/speaking)
- [ ] Store voice configuration
- [ ] Handle voice errors
- [ ] Emit voice events to WebSocket

**Files:**
- `ui/frontend/src/stores/voice-store.ts`

**Acceptance Criteria:**
- Provider selection persists
- State transitions are atomic
- Errors surface to UI

---

### Task 18: Local Voice Service
- [ ] Implement microphone capture with Web Audio API
- [ ] Add Voice Activity Detection (WebRTC)
- [ ] Integrate with backend Whisper STT
- [ ] Integrate with backend Kokoro TTS
- [ ] Handle audio playback
- [ ] Implement push-to-talk mode

**Files:**
- `ui/frontend/src/services/voice-service.ts` (local methods)
- `ui/backend/api/endpoints/voice.py`
- `ui/backend/api/schemas/voice.py`

**Acceptance Criteria:**
- STT transcription in < 500ms
- TTS playback smooth
- VAD detects speech accurately

---

### Task 19: AgentVoiceBox Integration
- [ ] Implement WebSocket connection to AgentVoiceBox
- [ ] Handle session.update/session.created events
- [ ] Stream audio via input_audio_buffer.append
- [ ] Handle speech_started/speech_stopped events
- [ ] Process response.audio.delta for playback
- [ ] Implement turn detection handling

**Files:**
- `ui/frontend/src/services/voice-service.ts` (agentvoicebox methods)

**Acceptance Criteria:**
- Full speech-on-speech works
- Latency < 150ms end-to-end
- Interruption handling works

---

### Task 20: Voice Settings UI
- [ ] Create `eog-voice-settings` component
- [ ] Add provider selection cards
- [ ] Add local voice settings (model, voice, speed)
- [ ] Add AgentVoiceBox settings (URL, token)
- [ ] Add audio device selection
- [ ] Implement connection test button

**Files:**
- `ui/frontend/src/views/eog-voice-settings.ts`

**Acceptance Criteria:**
- Provider-specific fields show/hide
- Test connection validates settings
- Settings save immediately

---

### Task 21: Voice Button Component
- [ ] Create `eog-voice-button` component
- [ ] Implement push-to-talk interaction
- [ ] Add visual state indicators (listening/processing/speaking)
- [ ] Add pulse animation for listening
- [ ] Handle disabled state
- [ ] Add tooltip with state description

**Files:**
- `ui/frontend/src/components/eog-voice-button.ts`

**Acceptance Criteria:**
- Button shows current voice state
- Push-to-talk works on desktop/mobile
- Disabled when voice not configured

---

### Task 22: Voice Overlay
- [ ] Create `eog-voice-overlay` floating panel
- [ ] Add audio visualizer (waveform)
- [ ] Show real-time transcript
- [ ] Add voice controls (mute, cancel)
- [ ] Position overlay near voice button
- [ ] Auto-hide when idle

**Files:**
- `ui/frontend/src/components/eog-voice-overlay.ts`
- `ui/frontend/src/components/eog-voice-visualizer.ts`

**Acceptance Criteria:**
- Visualizer shows audio levels
- Transcript updates in real-time
- Overlay dismisses on idle

---

## Phase 4: Advanced Features

### Task 23: Memory View
- [ ] Create `eog-memory-view` layout
- [ ] Create `eog-memory-search` with filters
- [ ] Create `eog-memory-grid` with virtual scrolling
- [ ] Create `eog-memory-card` component
- [ ] Create `eog-memory-detail` panel
- [ ] Implement memory CRUD operations

**Files:**
- `ui/frontend/src/views/eog-memory-view.ts`
- `ui/frontend/src/components/eog-memory-search.ts`
- `ui/frontend/src/components/eog-memory-grid.ts`
- `ui/frontend/src/components/eog-memory-card.ts`
- `ui/frontend/src/components/eog-memory-detail.ts`
- `ui/frontend/src/stores/memory-store.ts`
- `ui/backend/api/endpoints/memory.py`

**Acceptance Criteria:**
- Virtual scrolling handles 10K+ items
- Search filters by type, date, content
- Delete requires ADM permission

---

### Task 24: Cognitive Panel
- [ ] Create `eog-cognitive-view` layout
- [ ] Create `eog-neuromod-panel` with gauges
- [ ] Create `eog-neuromod-gauge` component
- [ ] Create `eog-adaptation-panel` with weights
- [ ] Create `eog-sleep-panel` with controls
- [ ] Integrate with SomaBrain API

**Files:**
- `ui/frontend/src/views/eog-cognitive-view.ts`
- `ui/frontend/src/components/eog-neuromod-panel.ts`
- `ui/frontend/src/components/eog-neuromod-gauge.ts`
- `ui/frontend/src/components/eog-adaptation-panel.ts`
- `ui/frontend/src/components/eog-sleep-panel.ts`
- `ui/frontend/src/stores/cognitive-store.ts`
- `ui/backend/api/endpoints/cognitive.py`

**Acceptance Criteria:**
- Neuromodulator gauges update in real-time
- Editing requires TRN or ADM mode
- Sleep cycle triggers consolidation

---

### Task 25: Admin Dashboard
- [ ] Create `eog-admin-view` layout
- [ ] Create `eog-user-management` panel
- [ ] Create `eog-tenant-management` panel
- [ ] Create `eog-system-health` panel
- [ ] Add user CRUD operations
- [ ] Add tenant provisioning

**Files:**
- `ui/frontend/src/views/eog-admin-view.ts`
- `ui/frontend/src/components/eog-user-management.ts`
- `ui/frontend/src/components/eog-tenant-management.ts`
- `ui/frontend/src/components/eog-system-health.ts`
- `ui/backend/api/endpoints/admin.py`
- `ui/backend/api/schemas/admin.py`

**Acceptance Criteria:**
- Admin view requires ADM mode
- User creation provisions SpiceDB roles
- Health shows all service statuses

---

### Task 26: Audit Log Viewer
- [ ] Create `eog-audit-view` layout
- [ ] Create `eog-audit-filters` panel
- [ ] Create `eog-audit-table` with virtual scrolling
- [ ] Add date range filter
- [ ] Add action type filter
- [ ] Add user filter

**Files:**
- `ui/frontend/src/views/eog-audit-view.ts`
- `ui/frontend/src/components/eog-audit-filters.ts`
- `ui/frontend/src/components/eog-audit-table.ts`
- `ui/backend/api/endpoints/audit.py`

**Acceptance Criteria:**
- Audit log loads in < 1s
- Filters apply without reload
- Export to CSV available

---

### Task 27: Tool Catalog
- [ ] Create `eog-tools-view` layout
- [ ] Create `eog-tool-catalog` grid
- [ ] Create `eog-tool-card` component
- [ ] Create `eog-tool-executor` panel
- [ ] Show tool permissions by mode
- [ ] Implement tool execution

**Files:**
- `ui/frontend/src/views/eog-tools-view.ts`
- `ui/frontend/src/components/eog-tool-catalog.ts`
- `ui/frontend/src/components/eog-tool-card.ts`
- `ui/frontend/src/components/eog-tool-executor.ts`
- `ui/backend/api/endpoints/tools.py`

**Acceptance Criteria:**
- Tools show permission requirements
- Execution requires appropriate mode
- Output streams in real-time

---

### Task 28: Scheduler View
- [ ] Create `eog-scheduler-view` layout
- [ ] Create `eog-task-list` component
- [ ] Create `eog-task-form` for creation
- [ ] Support scheduled, ad-hoc, planned tasks
- [ ] Show task execution history
- [ ] Implement task CRUD

**Files:**
- `ui/frontend/src/views/eog-scheduler-view.ts`
- `ui/frontend/src/components/eog-task-list.ts`
- `ui/frontend/src/components/eog-task-form.ts`
- `ui/backend/api/endpoints/scheduler.py`

**Acceptance Criteria:**
- Cron expression builder works
- Task history shows last 10 runs
- Manual trigger available

---

## Phase 5: Optimization

### Task 29: Service Worker
- [ ] Create service worker for caching
- [ ] Cache static assets (JS, CSS, fonts)
- [ ] Cache theme JSON files
- [ ] Implement cache-first for static
- [ ] Implement network-first for API
- [ ] Add offline fallback page

**Files:**
- `ui/frontend/src/sw.ts`
- `ui/frontend/vite.config.ts` (SW plugin)

**Acceptance Criteria:**
- Static assets served from cache
- App works offline (read-only)
- Cache updates on new version

---

### Task 30: Code Splitting
- [ ] Configure manual chunks in Vite
- [ ] Split vendor libraries
- [ ] Split views by route
- [ ] Split voice module
- [ ] Analyze bundle size
- [ ] Optimize chunk loading

**Files:**
- `ui/frontend/vite.config.ts`

**Acceptance Criteria:**
- Initial bundle < 100KB
- Largest chunk < 50KB
- All views lazy-loaded

---

### Task 31: Virtual Scrolling
- [ ] Create `eog-virtual-list` component
- [ ] Implement viewport calculation
- [ ] Add overscan for smooth scrolling
- [ ] Support variable item heights
- [ ] Apply to memory grid
- [ ] Apply to audit table

**Files:**
- `ui/frontend/src/components/eog-virtual-list.ts`

**Acceptance Criteria:**
- Renders 10K items smoothly
- Memory usage constant
- Scroll position preserved

---

### Task 32: Performance Testing
- [ ] Set up k6 for load testing
- [ ] Test 10K concurrent WebSocket connections
- [ ] Test API response times under load
- [ ] Test permission check latency
- [ ] Test theme switch performance
- [ ] Document performance baselines

**Files:**
- `ui/tests/k6/websocket-load.js`
- `ui/tests/k6/api-load.js`
- `ui/tests/performance-baseline.md`

**Acceptance Criteria:**
- 10K WS connections per node
- API p95 < 50ms under load
- Permission check p95 < 10ms

---

### Task 33: Accessibility Audit
- [ ] Run axe-core automated tests
- [ ] Test keyboard navigation
- [ ] Test screen reader compatibility
- [ ] Verify focus indicators
- [ ] Verify color contrast
- [ ] Fix all WCAG AA violations

**Files:**
- `ui/frontend/src/tests/a11y.test.ts`
- `ui/docs/accessibility-report.md`

**Acceptance Criteria:**
- Zero axe-core violations
- All controls keyboard accessible
- Screen reader announces correctly

---

### Task 34: Security Audit
- [ ] Run OWASP ZAP scan
- [ ] Test XSS prevention in themes
- [ ] Test CSRF protection
- [ ] Test SQL injection prevention
- [ ] Test rate limiting
- [ ] Document security findings

**Files:**
- `ui/docs/security-report.md`

**Acceptance Criteria:**
- Zero high/critical vulnerabilities
- Theme url() blocked
- Rate limiting enforced

---

## Task Status Legend

- [ ] Not started
- [~] In progress
- [x] Complete
- [!] Blocked

---

**Document Status:** COMPLETE

**Total Tasks:** 34
**Estimated Duration:** 10 weeks
