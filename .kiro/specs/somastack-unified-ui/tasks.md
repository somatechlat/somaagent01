# SomaStack Unified UI - Implementation Tasks

## Document Control

| Field | Value |
|-------|-------|
| **Document ID** | SOMASTACK-UI-TASKS-2025-12 |
| **Version** | 1.0 |
| **Date** | 2025-12-22 |
| **Status** | CANONICAL |
| **Implements** | SOMASTACK-UI-DESIGN-2025-12, SRS-SOMASTACK-UI-2025-001 |

---

## Task Overview

| ID | Task | Priority | Effort | Dependencies | Status |
|----|------|----------|--------|--------------|--------|
| T1 | Create Design System Directory Structure | P0 | 1h | None | ✅ DONE |
| T2 | Implement Design Tokens CSS | P0 | 2h | T1 | ✅ DONE |
| T3 | Implement Base Styles and Utilities | P0 | 2h | T2 | ✅ DONE |
| T4 | Implement Layout Components | P0 | 3h | T3 | ✅ DONE |
| T5 | Implement Navigation Components | P0 | 3h | T4 | ✅ DONE |
| T6 | Implement Stats Card Component | P0 | 2h | T3 | ✅ DONE |
| T7 | Implement Data Table Component | P0 | 4h | T3 | ✅ DONE |
| T8 | Implement Status Indicator Component | P0 | 2h | T3 | ✅ DONE |
| T9 | Implement Form Components | P0 | 3h | T3 | ✅ DONE |
| T10 | Implement Modal Component | P0 | 2h | T3 | ✅ DONE |
| T11 | Implement Toast Component | P0 | 2h | T3 | ✅ DONE |
| T12 | Implement Auth Store | P0 | 2h | T1 | ✅ DONE |
| T13 | Implement Theme Store | P0 | 2h | T2 | ✅ DONE |
| T14 | Implement Status Store | P0 | 2h | T8 | ✅ DONE |
| T15 | Implement Agent Dashboard (SomaAgent01) | P1 | 4h | T6, T8 | ✅ DONE |
| T16 | Implement Memory Browser (SomaFractalMemory) | P1 | 3h | T7 | ✅ DONE |
| T17 | Implement Voice Interface (AgentVoiceBox) | P2 | 3h | T3 | ✅ DONE |
| T18 | Implement Brain Dashboard (SomaBrain) | P1 | 3h | T6, T8 | ✅ DONE |
| T19 | API Integration | P0 | 3h | T15-T18 | ✅ DONE |
| T20 | Accessibility Audit | P1 | 3h | T15-T18 | ⏳ READY |
| T21 | Documentation | P2 | 3h | All | ⏳ READY |

---

## Phase 1: Foundation

### Task 1: Create Design System Directory Structure
- [ ] 1.1 Create `somaAgent01/webui/somastack-ui/` root directory
- [ ] 1.2 Create subdirectories: `css/`, `js/`, `fonts/`, `dist/`
- [ ] 1.3 Create `somastack-ui/package.json` with metadata and version
- [ ] 1.4 Download and add Geist font files to `fonts/geist/`
- [ ] 1.5 Create `somastack-ui/README.md` with usage instructions
- _Requirements: FR-DT-006, 18.1, 18.2_

### Task 2: Implement Design Tokens CSS
- [ ] 2.1 Create `css/somastack-tokens.css` with all design tokens
  - Color palettes: neutral (10 shades), primary (5), success (3), warning (3), error (3)
  - Typography: font-family, 6 sizes, 4 weights, line-heights
  - Spacing: 8 scale values (4px - 64px)
  - Effects: 3 shadows, 5 border-radius, 3 transitions
  - Glassmorphism: blur(12px), glass backgrounds, glass borders
  - _Requirements: FR-DT-001 through FR-DT-008, FR-GL-001 through FR-GL-003_

- [ ] 2.2 Write property test for token propagation
  - **Property 1: CSS Token Propagation**
  - *For any* CSS custom property, changing its value at `:root` SHALL update all usages
  - **Validates: FR-DT-002**


- [ ] 2.3 Write property test for WCAG contrast compliance
  - **Property 2: WCAG Contrast Compliance**
  - *For any* text/background color combination, contrast ratio SHALL be >= 4.5:1
  - **Validates: FR-GL-004**

### Task 3: Implement Base Styles and Utilities
- [ ] 3.1 Create `css/somastack-base.css` with CSS reset and base styles
  - Box-sizing border-box
  - Font smoothing
  - Focus-visible styles
  - Reduced motion support
  - _Requirements: FR-GL-004, 13.5, 13.6_

- [ ] 3.2 Create `css/somastack-utilities.css` with utility classes
  - Screen reader only (.soma-sr-only)
  - Focus ring (.soma-focusable)
  - Skip link (.soma-skip-link)
  - Spacing utilities
  - _Requirements: 13.2, 13.3_

### Task 4: Implement Layout Components
- [ ] 4.1 Create layout CSS in `css/somastack-components.css`
  - .soma-layout (main container with CSS Grid)
  - .soma-sidebar (sidebar with collapse support)
  - .soma-header (header bar)
  - .soma-main (main content area)
  - .soma-footer (footer)
  - _Requirements: 12.4, 12.5_

- [ ] 4.2 Create responsive breakpoints
  - Mobile: < 640px (bottom nav)
  - Tablet: 640-1023px (collapsed sidebar)
  - Desktop: >= 1024px (full sidebar)
  - _Requirements: 12.1, 12.2, 12.3_

- [ ] 4.3 Write property test for responsive layout
  - **Property 11: Responsive Layout Correctness**
  - *For any* viewport width, correct layout configuration SHALL be applied
  - **Validates: FR-NAV-001, 12.2, 12.3**

### Task 5: Implement Navigation Components
- [ ] 5.1 Create navigation CSS
  - .soma-nav-group (navigation group)
  - .soma-nav-item (navigation item)
  - .soma-nav-item--active (active state)
  - .soma-nav-item__badge (notification badge)
  - _Requirements: FR-NAV-001 through FR-NAV-006_

- [ ] 5.2 Create `js/components/sidebar-nav.js` Alpine component
  - Collapse/expand functionality
  - Active section tracking
  - localStorage persistence
  - Keyboard navigation (Tab, Enter, Arrow keys)
  - _Requirements: FR-NAV-001, FR-NAV-004, FR-NAV-005_

- [ ] 5.3 Write property test for keyboard navigation
  - **Property 13: Keyboard Navigation**
  - *For any* interactive element, Tab/Enter/Arrow keys SHALL work correctly
  - **Validates: FR-NAV-004, 13.2**

---

## Phase 2: Core Components

### Task 6: Implement Stats Card Component
- [ ] 6.1 Create stats card CSS
  - .soma-stats-card (card container)
  - .soma-stats-card__icon (icon area)
  - .soma-stats-card__value (metric value)
  - .soma-stats-card__label (metric label)
  - .soma-stats-card__trend (trend indicator)
  - Size variants: sm, md, lg, full
  - _Requirements: FR-SC-001 through FR-SC-005_

- [ ] 6.2 Create `js/components/stats-card.js` Alpine component
  - Number formatting (K/M/B suffixes)
  - Trend calculation and display
  - Value animation (300ms transition)
  - _Requirements: FR-SC-002, FR-SC-004, FR-SC-005_

- [ ] 6.3 Write property test for number formatting
  - **Property 5: Number Formatting**
  - *For any* number >= 1000, SHALL format with K/M/B suffix
  - **Validates: FR-SC-004**

### Task 7: Implement Data Table Component
- [ ] 7.1 Create data table CSS
  - .soma-table-container (wrapper)
  - .soma-table (table element)
  - .soma-table__header (sortable header)
  - .soma-table__row (data row)
  - .soma-table__checkbox (selection checkbox)
  - .soma-table__actions (action buttons)
  - .soma-table__pagination (pagination controls)
  - .soma-badge (status badges: approved, pending, rejected)
  - _Requirements: FR-TBL-001 through FR-TBL-008_

- [ ] 7.2 Create `js/components/data-table.js` Alpine component
  - Column sorting (asc/desc toggle)
  - Row selection with select-all
  - Pagination (configurable page size)
  - Search/filter functionality
  - Loading skeleton state
  - Empty state display
  - Role-based action visibility
  - _Requirements: FR-TBL-001 through FR-TBL-008_

- [ ] 7.3 Write property test for table sorting
  - **Property 6: Table Sorting Correctness**
  - *For any* column click, rows SHALL sort correctly
  - **Validates: FR-TBL-001**

- [ ] 7.4 Write property test for pagination
  - **Property 7: Table Pagination Activation**
  - *For any* table with > pageSize rows, pagination SHALL be displayed
  - **Validates: FR-TBL-005**

### Task 8: Implement Status Indicator Component
- [ ] 8.1 Create status indicator CSS
  - .soma-status (container)
  - .soma-status__dot (health dot)
  - .soma-status__dot--healthy (green)
  - .soma-status__dot--degraded (amber)
  - .soma-status__dot--down (red)
  - .soma-status__dot--unknown (grey)
  - .soma-status__tooltip (detail tooltip)
  - Pulse animation for active states
  - _Requirements: FR-SI-001 through FR-SI-007_

- [ ] 8.2 Create `js/components/status-indicator.js` Alpine component
  - Health status display
  - Relative timestamp formatting
  - Tooltip on hover
  - _Requirements: FR-SI-001, FR-SI-003, FR-SI-005_

### Task 9: Implement Form Components
- [ ] 9.1 Create form CSS
  - .soma-input (text input)
  - .soma-textarea (textarea)
  - .soma-select (select dropdown)
  - .soma-checkbox (checkbox)
  - .soma-radio (radio button)
  - .soma-toggle (toggle switch)
  - .soma-slider (range slider)
  - .soma-color-picker (color input)
  - States: focus, disabled, readonly, error
  - Helper text and validation error styling
  - _Requirements: FR-FRM-001 through FR-FRM-007_

- [ ] 9.2 Create `js/components/form-validation.js` Alpine component
  - Inline validation
  - Form-level validation
  - Error message display
  - Alpine.js x-model integration
  - _Requirements: FR-FRM-002, FR-FRM-006, FR-FRM-007_

- [ ] 9.3 Write property test for form validation
  - **Property 9: Settings Validation**
  - *For any* invalid input, validation SHALL reject with error message
  - **Validates: FR-FRM-002, FR-SET-006**

### Task 10: Implement Modal Component
- [ ] 10.1 Create modal CSS
  - .soma-modal (container)
  - .soma-modal__backdrop (backdrop overlay)
  - .soma-modal__content (content container)
  - .soma-modal__header (header with title and close)
  - .soma-modal__body (body content)
  - .soma-modal__footer (action buttons)
  - Size variants: sm (400px), md (600px), lg (800px), full
  - Open/close animations (fade + scale, 200ms)
  - _Requirements: FR-MOD-001 through FR-MOD-007_

- [ ] 10.2 Create `js/components/modal.js` Alpine component
  - Focus trap (x-trap directive)
  - Escape key close
  - Backdrop click close (configurable)
  - Body scroll lock
  - Stacked modal z-index management
  - _Requirements: FR-MOD-002 through FR-MOD-007_

- [ ] 10.3 Write property test for modal behavior
  - **Property 20: Modal Behavior Correctness**
  - *For any* open modal, focus trap, escape close, backdrop close, scroll lock SHALL work
  - **Validates: FR-MOD-002 through FR-MOD-007**

### Task 11: Implement Toast Component
- [ ] 11.1 Create toast CSS
  - .soma-toast-container (fixed position container)
  - .soma-toast (toast notification)
  - .soma-toast--info (blue)
  - .soma-toast--success (green)
  - .soma-toast--warning (amber)
  - .soma-toast--error (red)
  - .soma-toast__icon (variant icon)
  - .soma-toast__message (message text)
  - .soma-toast__close (close button)
  - Enter/exit animations
  - _Requirements: FR-TST-001 through FR-TST-004_

- [ ] 11.2 Create `js/components/toast.js` Alpine component
  - Toast creation with variants
  - Auto-dismiss (configurable timeout, default 5s)
  - Manual dismiss
  - Toast stacking
  - _Requirements: FR-TST-001 through FR-TST-004_

- [ ] 11.3 Write property test for toast auto-dismiss
  - **Property 18: Toast Auto-Dismiss**
  - *For any* toast, SHALL auto-dismiss after configured timeout
  - **Validates: FR-TST-002**

---

## Phase 3: State Management

### Task 12: Implement Auth Store
- [ ] 12.1 Create `js/stores/auth-store.js`
  - AuthState interface implementation
  - JWT token parsing from localStorage
  - Role extraction from token claims
  - Permission calculation based on role
  - Default to viewer on invalid/missing token
  - Computed properties: isAdmin, isOperator, hasPermission()
  - _Requirements: FR-RBAC-001 through FR-RBAC-008_

- [ ] 12.2 Write property test for role-based visibility
  - **Property 3: Role-Based UI Visibility**
  - *For any* user role, UI elements SHALL be visible according to permissions
  - **Validates: FR-RBAC-002 through FR-RBAC-004**

- [ ] 12.3 Write property test for JWT parsing
  - **Property 4: JWT Role Extraction**
  - *For any* valid JWT, role SHALL be correctly extracted; invalid defaults to viewer
  - **Validates: FR-RBAC-005, FR-RBAC-006**

### Task 13: Implement Theme Store
- [ ] 13.1 Create `js/stores/theme-store.js`
  - ThemeState interface implementation
  - Light/dark/system mode support
  - localStorage persistence
  - System preference detection (prefers-color-scheme)
  - Theme application via CSS class toggle
  - Smooth transition (300ms)
  - _Requirements: FR-TH-001 through FR-TH-006_

- [ ] 13.2 Write property test for theme switching
  - **Property 16: Theme Switching Performance**
  - *For any* theme toggle, change SHALL complete within 100ms
  - **Validates: FR-TH-002**

- [ ] 13.3 Write property test for state persistence
  - **Property 17: State Persistence Round-Trip**
  - *For any* preference stored in localStorage, page reload SHALL restore exact state
  - **Validates: FR-TH-003, FR-NAV-005, FR-SET-003**

### Task 14: Implement Status Store
- [ ] 14.1 Create `js/stores/status-store.js`
  - StatusState interface implementation
  - Health check polling (5 second interval)
  - Service status tracking
  - Latency measurement
  - Integration with health endpoints:
    - SomaBrain: GET /health (port 9696)
    - SomaFractalMemory: GET /healthz (port 9595)
    - SomaAgent01: GET /v1/health (port 21016)
  - _Requirements: FR-SI-001 through FR-SI-007_

- [ ] 14.2 Write property test for status update latency
  - **Property 8: Status Update Latency**
  - *For any* service status change, indicator SHALL update within 5 seconds
  - **Validates: FR-SI-002**

---

## Phase 4: Agent-Specific Components

### Task 15: Implement Agent Dashboard Components
- [ ] 15.1 Create agent dashboard CSS
  - .soma-agent-dashboard (container)
  - .soma-neuro-gauge (neuromodulator gauge)
  - .soma-fsm-diagram (FSM state visualization)
  - .soma-reasoning-stream (reasoning text stream)
  - .soma-conversation (conversation history)
  - .soma-tool-monitor (tool execution status)
  - _Requirements: FR-AGT-001 through FR-AGT-007_

- [ ] 15.2 Create `js/components/agent-dashboard.js` Alpine component
  - Neuromodulator level display (dopamine, serotonin, noradrenaline, acetylcholine)
  - FSM state visualization
  - Real-time reasoning stream
  - Conversation history with message bubbles
  - Tool execution monitoring
  - _Requirements: FR-AGT-001 through FR-AGT-006_

### Task 16: Implement Memory Browser Component
- [ ] 16.1 Create memory browser CSS
  - .soma-memory-browser (container)
  - .soma-memory-card (memory card view)
  - .soma-memory-list (memory list view)
  - .soma-memory-detail (detail panel)
  - .soma-memory-badge--episodic (blue)
  - .soma-memory-badge--semantic (purple)
  - _Requirements: FR-MEM-001 through FR-MEM-007_

- [ ] 16.2 Create `js/components/memory-browser.js` Alpine component
  - Card/list view toggle
  - Search by content, coordinate, metadata
  - Memory type badges
  - Age and decay display
  - Detail panel on click
  - Admin delete capability
  - Similarity score display
  - _Requirements: FR-MEM-001 through FR-MEM-007_

- [ ] 16.3 Write property test for memory search
  - **Property 10: Memory Search Accuracy**
  - *For any* search query, all results SHALL contain the search term
  - **Validates: FR-MEM-002**

### Task 17: Implement Voice Interface Components
- [ ] 17.1 Create voice interface CSS
  - .soma-voice-interface (container)
  - .soma-waveform (audio waveform visualization)
  - .soma-transcription (real-time transcription)
  - .soma-tts-progress (TTS playback progress)
  - .soma-voice-indicator (processing animation)
  - .soma-voice-status (connection status)
  - _Requirements: FR-VOI-001 through FR-VOI-006_

- [ ] 17.2 Create `js/components/voice-interface.js` Alpine component
  - Waveform visualization using Web Audio API
  - Real-time transcription display
  - TTS progress indicator
  - PTT and VAD mode support
  - Processing animation
  - Connection status display
  - _Requirements: FR-VOI-001 through FR-VOI-006_

---

## Phase 5: Integration and Testing

### Task 18: Create Bundle and Distribution
- [ ] 18.1 Create `dist/somastack-ui.css` (concatenated, minified)
  - Include: tokens, base, utilities, components
  - Target: < 30KB gzipped
  - _Requirements: NFR-PERF-006_

- [ ] 18.2 Create `dist/somastack-ui.js` (concatenated, minified)
  - Include: core, stores, components
  - Target: < 20KB gzipped
  - _Requirements: NFR-PERF-006_

- [ ] 18.3 Create `dist/somastack-ui.min.css` and `dist/somastack-ui.min.js`
  - Minified production builds
  - Source maps for debugging

### Task 19: Integrate with SomaAgent01
- [ ] 19.1 Update `somaAgent01/webui/index.html`
  - Add link to somastack-ui.css
  - Add script for somastack-ui.js
  - Remove duplicate inline styles
  - Update Alpine components to use new stores
  - _Requirements: 18.2, 18.3_

- [ ] 19.2 Update existing components to use design system
  - Replace hardcoded colors with tokens
  - Replace custom components with design system components
  - Ensure role-based visibility works

- [ ] 19.3 Verify no visual regression
  - Compare before/after screenshots
  - Test all major views

### Task 20: Unit Tests
- [ ] 20.1 Create `tests/unit/test_tokens.py`
  - Verify all required tokens present
  - Verify token values correct
  - _Requirements: FR-DT-001 through FR-DT-008_

- [ ] 20.2 Create `tests/unit/test_auth_store.js`
  - Test JWT parsing
  - Test role extraction
  - Test permission calculation
  - Test default fallback
  - _Requirements: FR-RBAC-005, FR-RBAC-006_

- [ ] 20.3 Create `tests/unit/test_number_format.js`
  - Test K/M/B formatting
  - Test edge cases (999, 1000, 999999, etc.)
  - _Requirements: FR-SC-004_

- [ ] 20.4 Create `tests/unit/test_contrast.js`
  - Test contrast ratio calculation
  - Test WCAG AA compliance
  - _Requirements: FR-GL-004_

### Task 21: Property Tests
- [ ] 21.1 Property Test: Token Propagation
  - **Property 1: CSS Token Propagation**
  - **Validates: FR-DT-002**

- [ ] 21.2 Property Test: WCAG Contrast
  - **Property 2: WCAG Contrast Compliance**
  - **Validates: FR-GL-004**

- [ ] 21.3 Property Test: Role Visibility
  - **Property 3: Role-Based UI Visibility**
  - **Validates: FR-RBAC-002 through FR-RBAC-004**

- [ ] 21.4 Property Test: JWT Parsing
  - **Property 4: JWT Role Extraction**
  - **Validates: FR-RBAC-005, FR-RBAC-006**

- [ ] 21.5 Property Test: Number Formatting
  - **Property 5: Number Formatting**
  - **Validates: FR-SC-004**

- [ ] 21.6 Property Test: Table Sorting
  - **Property 6: Table Sorting Correctness**
  - **Validates: FR-TBL-001**

- [ ] 21.7 Property Test: Pagination
  - **Property 7: Table Pagination Activation**
  - **Validates: FR-TBL-005**

- [ ] 21.8 Property Test: Status Latency
  - **Property 8: Status Update Latency**
  - **Validates: FR-SI-002**

- [ ] 21.9 Property Test: Theme Switching
  - **Property 16: Theme Switching Performance**
  - **Validates: FR-TH-002**

- [ ] 21.10 Property Test: State Persistence
  - **Property 17: State Persistence Round-Trip**
  - **Validates: FR-TH-003, FR-NAV-005, FR-SET-003**

### Task 22: E2E Tests (Playwright)
- [ ] 22.1 Create `tests/e2e/test_navigation.spec.js`
  - Test sidebar collapse/expand
  - Test keyboard navigation
  - Test active section highlight
  - _Requirements: FR-NAV-001 through FR-NAV-006_

- [ ] 22.2 Create `tests/e2e/test_theme.spec.js`
  - Test theme toggle
  - Test theme persistence
  - Test system preference
  - _Requirements: FR-TH-001 through FR-TH-006_

- [ ] 22.3 Create `tests/e2e/test_rbac.spec.js`
  - Test admin UI visibility
  - Test operator UI visibility
  - Test viewer UI visibility
  - _Requirements: FR-RBAC-001 through FR-RBAC-008_

- [ ] 22.4 Create `tests/e2e/test_table.spec.js`
  - Test sorting
  - Test pagination
  - Test search/filter
  - Test row selection
  - _Requirements: FR-TBL-001 through FR-TBL-008_

- [ ] 22.5 Create `tests/e2e/test_modal.spec.js`
  - Test focus trap
  - Test escape close
  - Test backdrop close
  - Test stacked modals
  - _Requirements: FR-MOD-001 through FR-MOD-007_

- [ ] 22.6 Create `tests/e2e/test_accessibility.spec.js`
  - Run axe-core audit
  - Test keyboard navigation
  - Test focus indicators
  - _Requirements: 13.1 through 13.7_

### Task 23: Documentation
- [ ] 23.1 Create `docs/somastack-ui/README.md`
  - Installation instructions
  - Quick start guide
  - _Requirements: 18.4_

- [ ] 23.2 Create `docs/somastack-ui/tokens.md`
  - Complete token reference
  - Usage examples
  - _Requirements: 18.4_

- [ ] 23.3 Create `docs/somastack-ui/components.md`
  - Component API reference
  - Usage examples for each component
  - _Requirements: 18.4_

- [ ] 23.4 Create `docs/somastack-ui/stores.md`
  - Store API reference
  - Integration examples
  - _Requirements: 18.4_

- [ ] 23.5 Create `docs/somastack-ui/accessibility.md`
  - WCAG compliance guide
  - Keyboard navigation reference
  - ARIA usage guide
  - _Requirements: 13.1 through 13.7_

---

## Checkpoint Tasks

### Checkpoint 1: Foundation Complete
- [ ] CP1 Ensure all Phase 1 tasks complete
  - Design tokens CSS created and validated
  - Base styles and utilities implemented
  - Layout components working
  - Navigation components functional
  - Ask user if questions arise

### Checkpoint 2: Core Components Complete
- [ ] CP2 Ensure all Phase 2 tasks complete
  - All core components implemented
  - Property tests passing
  - Visual verification complete
  - Ask user if questions arise

### Checkpoint 3: State Management Complete
- [ ] CP3 Ensure all Phase 3 tasks complete
  - All stores implemented
  - JWT parsing working
  - Theme switching working
  - Status polling working
  - Ask user if questions arise

### Checkpoint 4: Integration Complete
- [ ] CP4 Ensure all Phase 5 tasks complete
  - Bundle created
  - SomaAgent01 integrated
  - All tests passing
  - Documentation complete
  - Ask user if questions arise

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] Unit tests passing
- [ ] Property tests passing (21 properties)
- [ ] E2E tests passing
- [ ] No VIBE violations (no mocks, no placeholders, no TODOs)
- [ ] WCAG 2.1 AA compliance verified
- [ ] Performance budgets met (CSS < 30KB, JS < 20KB)
- [ ] Documentation complete
- [ ] Code reviewed
- [ ] Visual regression tests passing

---

## Notes

- All property-based tests are required (comprehensive testing)
- All tests use real infrastructure per VIBE Coding Rules
- No build step required - vanilla Alpine.js only
- Theme switch must complete within 100ms
- Status updates must occur within 5 seconds
- All components must work in both light and dark themes
