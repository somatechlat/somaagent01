# Requirements Document

## Introduction

This specification defines the requirements for a **complete UI/UX redesign** of the SomaAgent01 Web Interface. The redesign will create a state-of-the-art, lightning-fast, modern AI agent interface that provides all necessary tools for interacting with the agent system while maintaining full integration with the existing production backend.

### Vision

Create a world-class AI agent interface that is:
- **Lightning Fast**: Sub-100ms interactions, optimized rendering, minimal bundle size
- **State-of-the-Art Architecture**: Modern component-based design with reactive state management
- **AI-Native**: Purpose-built for AI agent interactions with real-time streaming, tool visualization, and cognitive state awareness
- **Accessible**: WCAG 2.1 AA compliant, keyboard navigable, screen reader friendly
- **Responsive**: Seamless experience across desktop, tablet, and mobile devices
- **Dark-First**: Modern dark theme with optional light mode, reducing eye strain for extended use

### Current State Analysis

**Existing Backend (KEEP - Production Ready):**
- Gateway FastAPI service on port 21016
- SSE streaming via `/v1/sessions/{id}/events`
- Settings API at `/v1/settings/sections`
- Upload API at `/v1/uploads`
- Health API at `/v1/health`
- Session management APIs
- Kafka event bus integration
- PostgreSQL persistence
- Redis caching
- OPA policy enforcement

**Current UI Issues (REPLACE):**
- Fragmented architecture with mixed legacy and modern code
- Inconsistent styling across components
- Slow initial load times
- Limited real-time feedback
- Poor mobile experience
- Accessibility gaps
- No design system or component library

### Goals

1. Complete visual and architectural redesign of the entire Web UI
2. Create a unified design system with reusable components
3. Achieve sub-100ms interaction response times
4. Implement real-time streaming with visual feedback
5. Provide comprehensive AI agent tooling interface
6. Maintain 100% backend API compatibility
7. Achieve WCAG 2.1 AA accessibility compliance
8. Support internationalization (i18n) for all UI text
9. Enable progressive web app (PWA) capabilities
10. Implement comprehensive Playwright test coverage

## Glossary

- **Design System**: Collection of reusable components, patterns, and guidelines
- **Alpine.js**: Lightweight reactive JavaScript framework for UI state
- **SSE**: Server-Sent Events for real-time streaming from backend
- **PWA**: Progressive Web App with offline capabilities
- **WCAG**: Web Content Accessibility Guidelines
- **Token**: Individual unit of text in LLM streaming responses
- **Tool Call**: Agent executing a specific capability (code, search, memory)
- **Cognitive State**: Agent's neuromodulation levels (dopamine, serotonin, etc.)
- **Session**: Conversation context with history and state
- **Persona**: Agent personality configuration

## Requirements

### Requirement 1: Design System Foundation - Modern AI Interface

**User Story:** As a developer, I want a comprehensive design system optimized for AI agent interfaces, so that all UI components are consistent, beautiful, and maintainable.

#### Acceptance Criteria - Color System

1. WHEN the design system is created THEN the System SHALL define a dark-first color palette:
   - Background: `--bg-primary: #0a0a0f`, `--bg-secondary: #12121a`, `--bg-tertiary: #1a1a2e`
   - Surface: `--surface-1: #1e1e2e`, `--surface-2: #252536`, `--surface-3: #2d2d44`
   - Accent: `--accent-primary: #6366f1` (indigo), `--accent-secondary: #8b5cf6` (violet)
   - Success: `--success: #10b981`, Warning: `--warning: #f59e0b`, Error: `--error: #ef4444`
   - Text: `--text-primary: #f8fafc`, `--text-secondary: #94a3b8`, `--text-muted: #64748b`
2. WHEN the design system is created THEN the System SHALL define gradient accents for AI elements:
   - `--gradient-ai: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a855f7 100%)`
   - `--gradient-glow: radial-gradient(circle, rgba(99,102,241,0.15) 0%, transparent 70%)`
3. WHEN light mode is active THEN the System SHALL invert the palette with light backgrounds and dark text

#### Acceptance Criteria - Typography

4. WHEN the design system is created THEN the System SHALL define typography using Inter font family:
   - Display: 48px/1.1, font-weight 700
   - H1: 32px/1.2, font-weight 600
   - H2: 24px/1.3, font-weight 600
   - H3: 20px/1.4, font-weight 500
   - Body: 14px/1.6, font-weight 400
   - Small: 12px/1.5, font-weight 400
   - Code: JetBrains Mono, 13px/1.5
5. WHEN text renders THEN the System SHALL use `-webkit-font-smoothing: antialiased` for crisp rendering

#### Acceptance Criteria - Spacing & Layout

6. WHEN the design system is created THEN the System SHALL define spacing scale (4px base):
   - `--space-1: 4px`, `--space-2: 8px`, `--space-3: 12px`, `--space-4: 16px`
   - `--space-5: 20px`, `--space-6: 24px`, `--space-8: 32px`, `--space-10: 40px`
7. WHEN the design system is created THEN the System SHALL define border radius:
   - `--radius-sm: 4px`, `--radius-md: 8px`, `--radius-lg: 12px`, `--radius-xl: 16px`, `--radius-full: 9999px`

#### Acceptance Criteria - Elevation & Effects

8. WHEN the design system is created THEN the System SHALL define elevation shadows:
   - `--shadow-sm: 0 1px 2px rgba(0,0,0,0.3)`
   - `--shadow-md: 0 4px 6px rgba(0,0,0,0.4)`
   - `--shadow-lg: 0 10px 15px rgba(0,0,0,0.5)`
   - `--shadow-glow: 0 0 20px rgba(99,102,241,0.3)`
9. WHEN the design system is created THEN the System SHALL define glassmorphism effects:
   - `--glass-bg: rgba(30,30,46,0.8)`
   - `--glass-border: rgba(255,255,255,0.1)`
   - `--glass-blur: blur(12px)`

#### Acceptance Criteria - Animation

10. WHEN the design system is created THEN the System SHALL define animation tokens:
    - `--duration-fast: 150ms`, `--duration-normal: 200ms`, `--duration-slow: 300ms`
    - `--ease-out: cubic-bezier(0.16, 1, 0.3, 1)`
    - `--ease-in-out: cubic-bezier(0.4, 0, 0.2, 1)`
11. WHEN interactive elements are hovered THEN the System SHALL apply smooth transitions (150ms ease-out)
12. WHEN modals/panels open THEN the System SHALL use slide + fade animation (200ms ease-out)

### Requirement 2: Core Layout Architecture

**User Story:** As a user, I want a clean, organized layout, so that I can efficiently navigate and use all features.

#### Acceptance Criteria

1. WHEN the application loads THEN the System SHALL display a three-panel layout: sidebar, main content, and optional detail panel
2. WHEN the sidebar is visible THEN the System SHALL show navigation, session list, and quick actions
3. WHEN the sidebar is collapsed THEN the System SHALL show only icons with tooltips
4. WHEN the main content area is active THEN the System SHALL display the chat interface or selected feature
5. WHEN the detail panel is open THEN the System SHALL show contextual information (settings, memory, tools)
6. WHEN the viewport is less than 768px THEN the System SHALL collapse to single-panel mobile layout
7. WHEN the viewport is between 768px and 1024px THEN the System SHALL use two-panel tablet layout
8. WHEN the user resizes panels THEN the System SHALL persist panel widths to localStorage

### Requirement 3: Navigation System

**User Story:** As a user, I want intuitive navigation, so that I can quickly access all features.

#### Acceptance Criteria

1. WHEN the navigation renders THEN the System SHALL display icons with labels for: Chat, Memory, Tools, Scheduler, Settings, Health
2. WHEN a navigation item is active THEN the System SHALL highlight it with accent color and indicator
3. WHEN the user hovers over navigation THEN the System SHALL show tooltip with feature description
4. WHEN keyboard navigation is used THEN the System SHALL support Tab, Arrow keys, and Enter for selection
5. WHEN the user presses Cmd/Ctrl+K THEN the System SHALL open command palette for quick navigation
6. WHEN the command palette is open THEN the System SHALL support fuzzy search across all features and actions

### Requirement 4: Chat Interface Redesign - AI-Native Experience

**User Story:** As a user, I want a modern, AI-native chat interface, so that I can have natural, visually rich conversations with the AI agent.

#### Acceptance Criteria - Message Display

1. WHEN the chat loads THEN the System SHALL display messages in a scrollable container with smooth auto-scroll
2. WHEN a user message is displayed THEN the System SHALL show it in a card with:
   - Right-aligned position with subtle background (`--surface-2`)
   - User avatar (initials or image) with colored ring
   - Timestamp in muted text below message
   - Max-width of 80% of container
3. WHEN an assistant message is displayed THEN the System SHALL show it in a card with:
   - Left-aligned position with gradient accent border on left edge
   - Agent avatar with AI glow effect (`--shadow-glow`)
   - Timestamp and "Agent" label
   - Full-width capability for code blocks

#### Acceptance Criteria - Streaming & Thinking States

4. WHEN the assistant is thinking THEN the System SHALL display:
   - Animated "thinking" indicator with pulsing dots
   - Subtle glow animation around the message area
   - "Thinking..." text that updates to show elapsed time after 3s
5. WHEN the assistant is streaming THEN the System SHALL:
   - Display tokens progressively with smooth fade-in (50ms per token batch)
   - Show cursor animation at end of text
   - Update scroll position smoothly (not jarring jumps)
6. WHEN streaming completes THEN the System SHALL:
   - Remove cursor animation
   - Add action buttons (copy, regenerate, feedback)
   - Show final timestamp

#### Acceptance Criteria - Rich Content Rendering

7. WHEN a message contains code THEN the System SHALL render with:
   - Syntax highlighting using Prism.js or Shiki
   - Language label in top-right corner
   - Copy button that shows "Copied!" feedback
   - Line numbers for blocks > 5 lines
   - Horizontal scroll for long lines (no wrap)
8. WHEN a message contains markdown THEN the System SHALL render:
   - Headings with appropriate sizing and spacing
   - Bullet and numbered lists with proper indentation
   - Links with accent color and hover underline
   - Bold, italic, strikethrough formatting
   - Blockquotes with left border accent
   - Tables with alternating row colors
9. WHEN a message contains math THEN the System SHALL render LaTeX via KaTeX inline and block
10. WHEN a message contains images THEN the System SHALL display thumbnails with lightbox on click

#### Acceptance Criteria - Input Area

11. WHEN the input area renders THEN the System SHALL display:
    - Multi-line textarea with auto-resize (max 200px height)
    - Placeholder text: "Message Agent Zero..."
    - Character count indicator (shows at 500+ chars)
    - Attachment button for file uploads
    - Microphone button for voice input (if enabled)
    - Send button with gradient accent background
12. WHEN the user types THEN the System SHALL:
    - Support Shift+Enter for new line
    - Support Enter to send (configurable)
    - Show typing indicator to other viewers (if multi-user)
13. WHEN files are attached THEN the System SHALL show preview chips above input
14. WHEN the input is empty THEN the System SHALL disable send button with reduced opacity

#### Acceptance Criteria - Connection Status

15. WHEN SSE connects THEN the System SHALL show green dot indicator in header
16. WHEN SSE disconnects THEN the System SHALL show:
    - Yellow/red indicator based on retry count
    - "Reconnecting..." banner with countdown
    - Manual "Retry Now" button after 3 failed attempts
17. WHEN reconnection succeeds THEN the System SHALL:
    - Fetch missed messages since last event ID
    - Show "Reconnected" toast notification

### Requirement 5: Tool Execution Visualization

**User Story:** As a user, I want to see tool executions clearly, so that I understand what the agent is doing.

#### Acceptance Criteria

1. WHEN a tool is called THEN the System SHALL display a tool card with icon, name, and status
2. WHEN a tool is executing THEN the System SHALL show animated progress indicator
3. WHEN a tool completes successfully THEN the System SHALL show success state with green indicator
4. WHEN a tool fails THEN the System SHALL show error state with red indicator and error message
5. WHEN a code execution tool runs THEN the System SHALL display code input and output in collapsible sections
6. WHEN a search tool runs THEN the System SHALL display search query and results summary
7. WHEN a memory tool runs THEN the System SHALL display memory operation type and affected items
8. WHEN the user clicks a tool card THEN the System SHALL expand to show full details
9. WHEN multiple tools run THEN the System SHALL display them in chronological order with timeline

### Requirement 6: Session Management

**User Story:** As a user, I want to manage my chat sessions, so that I can organize conversations.

#### Acceptance Criteria

1. WHEN the session list loads THEN the System SHALL fetch sessions via GET `/v1/sessions`
2. WHEN sessions are displayed THEN the System SHALL show name, date, and message count
3. WHEN the user clicks "New Chat" THEN the System SHALL create session via POST `/v1/sessions`
4. WHEN the user selects a session THEN the System SHALL load history via GET `/v1/sessions/{id}/history`
5. WHEN the user renames a session THEN the System SHALL update via PUT `/v1/sessions/{id}`
6. WHEN the user deletes a session THEN the System SHALL remove via DELETE `/v1/sessions/{id}` with confirmation
7. WHEN sessions are searched THEN the System SHALL filter by name and content
8. WHEN sessions are sorted THEN the System SHALL support date, name, and message count ordering

### Requirement 7: Settings Interface - Card-Based Architecture

**User Story:** As a user, I want a beautiful, card-based settings interface, so that I can easily configure all aspects of the agent and system.

#### Acceptance Criteria - Core Structure

1. WHEN settings open THEN the System SHALL display a full-screen modal with sidebar navigation and content area
2. WHEN settings load THEN the System SHALL fetch all 17 sections via GET `/v1/settings/sections`
3. WHEN settings are displayed THEN the System SHALL organize by tabs: Agent, External, Connectivity, System
4. WHEN a tab is selected THEN the System SHALL show all sections for that tab as individual cards
5. WHEN cards render THEN the System SHALL display them in a responsive grid (1-3 columns based on viewport)

#### Acceptance Criteria - Card Design

6. WHEN a settings card renders THEN the System SHALL display: icon, title, description, and expand/collapse toggle
7. WHEN a card is collapsed THEN the System SHALL show summary of key values (e.g., "Provider: OpenRouter, Model: gpt-4.1")
8. WHEN a card is expanded THEN the System SHALL reveal all fields with smooth animation (200ms ease-out)
9. WHEN a card has unsaved changes THEN the System SHALL show a visual indicator (dot or highlight)
10. WHEN hovering a card THEN the System SHALL show subtle elevation change (shadow increase)

#### Acceptance Criteria - Model Cards (Chat, Utility, Browser, Embedding)

11. WHEN a model card renders THEN the System SHALL display provider dropdown with icons for each provider
12. WHEN a model card renders THEN the System SHALL display model name input with autocomplete suggestions
13. WHEN a model card renders THEN the System SHALL display API base URL input (optional, with placeholder)
14. WHEN a model card renders THEN the System SHALL display context length slider (1K-200K range)
15. WHEN a model card renders THEN the System SHALL display rate limit inputs (requests/min, tokens/min)
16. WHEN a model card renders THEN the System SHALL display kwargs editor (key-value pairs)
17. WHEN Chat Model card renders THEN the System SHALL display vision toggle switch
18. WHEN Browser Model card renders THEN the System SHALL display HTTP headers editor
19. WHEN provider changes THEN the System SHALL update model suggestions dynamically

#### Acceptance Criteria - Memory/SomaBrain Card

20. WHEN Memory card renders THEN the System SHALL display recall settings group (enabled, delayed, interval)
21. WHEN Memory card renders THEN the System SHALL display search limits (memories max, solutions max)
22. WHEN Memory card renders THEN the System SHALL display similarity threshold slider (0.0-1.0)
23. WHEN Memory card renders THEN the System SHALL display memorization settings (enabled, consolidation)
24. WHEN Memory card renders THEN the System SHALL display knowledge subdirectory selector

#### Acceptance Criteria - API Keys Card

25. WHEN API Keys card renders THEN the System SHALL display one row per detected provider
26. WHEN an API key field renders THEN the System SHALL mask the value with dots by default
27. WHEN show/hide toggle is clicked THEN the System SHALL reveal/hide the API key value
28. WHEN an API key is set THEN the System SHALL show green checkmark indicator
29. WHEN an API key is empty THEN the System SHALL show warning indicator
30. WHEN test connection is clicked THEN the System SHALL POST to `/v1/settings/test-connection` and show result

#### Acceptance Criteria - MCP/A2A Cards

31. WHEN MCP Client card renders THEN the System SHALL display JSON editor for server configuration
32. WHEN MCP Client card renders THEN the System SHALL display timeout inputs (init, tool)
33. WHEN MCP Server card renders THEN the System SHALL display enabled toggle and token display
34. WHEN A2A Server card renders THEN the System SHALL display enabled toggle and endpoint info
35. WHEN token field renders THEN the System SHALL show copy button and regenerate button

#### Acceptance Criteria - Speech Card

36. WHEN Speech card renders THEN the System SHALL display provider selector (browser, kokoro, realtime)
37. WHEN Speech card renders THEN the System SHALL display STT settings (model size, language, thresholds)
38. WHEN realtime is selected THEN the System SHALL show realtime-specific settings (model, voice, endpoint)
39. WHEN Kokoro is selected THEN the System SHALL show Kokoro-specific toggle

#### Acceptance Criteria - Authentication Card

40. WHEN Auth card renders THEN the System SHALL display login username input
41. WHEN Auth card renders THEN the System SHALL display password input with strength indicator
42. WHEN in Docker THEN the System SHALL display root password input
43. WHEN password is changed THEN the System SHALL require confirmation input

#### Acceptance Criteria - Backup & Restore Card

44. WHEN Backup card renders THEN the System SHALL display "Create Backup" button
45. WHEN Backup card renders THEN the System SHALL display "Restore from Backup" file picker
46. WHEN backup is created THEN the System SHALL trigger download of backup file
47. WHEN restore is initiated THEN the System SHALL show confirmation dialog with warnings

#### Acceptance Criteria - Developer Card

48. WHEN Developer card renders THEN the System SHALL display shell interface selector (local/ssh)
49. WHEN Developer card renders THEN the System SHALL display RFC connection settings
50. WHEN in development mode THEN the System SHALL show additional debug options

#### Acceptance Criteria - Save/Cancel Actions

51. WHEN the user clicks Save THEN the System SHALL PUT to `/v1/settings/sections` with all values
52. WHEN save succeeds THEN the System SHALL show success toast and close modal
53. WHEN save fails THEN the System SHALL show error toast with details and keep modal open
54. WHEN the user clicks Cancel THEN the System SHALL discard changes and close modal
55. WHEN the user has unsaved changes and clicks Cancel THEN the System SHALL show confirmation dialog

### Requirement 8: Memory Dashboard

**User Story:** As a user, I want to view and manage agent memories, so that I can understand and curate stored knowledge.

#### Acceptance Criteria

1. WHEN memory dashboard opens THEN the System SHALL fetch memories via GET `/v1/memory`
2. WHEN memories are displayed THEN the System SHALL show content preview, timestamp, and relevance score
3. WHEN the user searches memories THEN the System SHALL POST to `/v1/memory/search` with query
4. WHEN search results return THEN the System SHALL highlight matching terms
5. WHEN the user deletes a memory THEN the System SHALL DELETE `/v1/memory/{id}` with confirmation
6. WHEN memories are filtered THEN the System SHALL support type (fact, solution, fragment) filtering
7. WHEN memory details are viewed THEN the System SHALL show full content, metadata, and related memories

### Requirement 9: Scheduler Interface

**User Story:** As a user, I want to manage scheduled tasks, so that I can automate agent actions.

#### Acceptance Criteria

1. WHEN scheduler opens THEN the System SHALL fetch tasks via GET `/v1/scheduler/tasks`
2. WHEN tasks are displayed THEN the System SHALL show name, type, schedule, and status
3. WHEN the user creates a task THEN the System SHALL POST to `/v1/scheduler/tasks`
4. WHEN creating a scheduled task THEN the System SHALL provide cron expression builder
5. WHEN creating an ad-hoc task THEN the System SHALL generate and display trigger token
6. WHEN creating a planned task THEN the System SHALL provide datetime picker
7. WHEN the user edits a task THEN the System SHALL PUT to `/v1/scheduler/tasks/{id}`
8. WHEN the user deletes a task THEN the System SHALL DELETE `/v1/scheduler/tasks/{id}`
9. WHEN task status changes THEN the System SHALL update display in real-time via SSE

### Requirement 10: Health & Status Dashboard

**User Story:** As a user, I want to see system health, so that I know if services are operational.

#### Acceptance Criteria

1. WHEN health dashboard loads THEN the System SHALL fetch status via GET `/v1/health`
2. WHEN services are healthy THEN the System SHALL show green status indicators
3. WHEN services are degraded THEN the System SHALL show yellow warning indicators
4. WHEN services are down THEN the System SHALL show red error indicators with details
5. WHEN SomaBrain is offline THEN the System SHALL display degradation banner in header
6. WHEN the SSE connection status changes THEN the System SHALL update connection indicator
7. WHEN health is polled THEN the System SHALL refresh every 30 seconds automatically

### Requirement 11: File Upload System

**User Story:** As a user, I want to upload files to share with the agent, so that I can provide documents and images.

#### Acceptance Criteria

1. WHEN the user drags a file THEN the System SHALL show drop zone overlay
2. WHEN the user drops a file THEN the System SHALL upload via POST `/v1/uploads`
3. WHEN upload is in progress THEN the System SHALL show progress bar with percentage
4. WHEN upload completes THEN the System SHALL display file preview in chat input area
5. WHEN upload fails THEN the System SHALL show error notification with retry option
6. WHEN multiple files are uploaded THEN the System SHALL process them sequentially with queue display
7. WHEN file type is image THEN the System SHALL show thumbnail preview
8. WHEN file type is document THEN the System SHALL show file icon and name

### Requirement 12: Real-Time Streaming

**User Story:** As a user, I want real-time updates, so that I see agent responses as they stream.

#### Acceptance Criteria

1. WHEN chat connects THEN the System SHALL establish SSE to `/v1/sessions/{id}/events?stream=true`
2. WHEN `assistant.started` event arrives THEN the System SHALL create new message placeholder
3. WHEN `assistant.delta` events arrive THEN the System SHALL append tokens to current message
4. WHEN `assistant.thinking.started` event arrives THEN the System SHALL show thinking indicator
5. WHEN `assistant.thinking.final` event arrives THEN the System SHALL hide thinking indicator
6. WHEN `assistant.final` event arrives THEN the System SHALL mark message complete
7. WHEN `assistant.tool.started` event arrives THEN the System SHALL show tool execution card
8. WHEN `assistant.tool.final` event arrives THEN the System SHALL update tool card with result
9. WHEN `system.keepalive` event arrives THEN the System SHALL update last-seen timestamp
10. WHEN connection drops THEN the System SHALL reconnect with exponential backoff (1s, 2s, 4s, max 30s)

### Requirement 13: Keyboard Shortcuts

**User Story:** As a power user, I want keyboard shortcuts, so that I can work efficiently.

#### Acceptance Criteria

1. WHEN the user presses Cmd/Ctrl+K THEN the System SHALL open command palette
2. WHEN the user presses Cmd/Ctrl+N THEN the System SHALL create new chat
3. WHEN the user presses Cmd/Ctrl+, THEN the System SHALL open settings
4. WHEN the user presses Escape THEN the System SHALL close active modal or panel
5. WHEN the user presses Cmd/Ctrl+/ THEN the System SHALL show keyboard shortcuts help
6. WHEN the user presses Up Arrow in empty input THEN the System SHALL load last sent message
7. WHEN shortcuts are used THEN the System SHALL show brief toast confirmation

### Requirement 14: Notifications System

**User Story:** As a user, I want notifications, so that I'm informed of important events.

#### Acceptance Criteria

1. WHEN an action succeeds THEN the System SHALL show success toast (green, 3s auto-dismiss)
2. WHEN an action fails THEN the System SHALL show error toast (red, manual dismiss required)
3. WHEN a warning occurs THEN the System SHALL show warning toast (yellow, 5s auto-dismiss)
4. WHEN info is displayed THEN the System SHALL show info toast (blue, 3s auto-dismiss)
5. WHEN multiple toasts queue THEN the System SHALL stack them with max 3 visible
6. WHEN the user clicks a toast THEN the System SHALL dismiss it immediately
7. WHEN background task completes THEN the System SHALL show notification with action button

### Requirement 15: Accessibility Compliance

**User Story:** As a user with disabilities, I want an accessible interface, so that I can use all features.

#### Acceptance Criteria

1. WHEN any interactive element renders THEN the System SHALL have appropriate ARIA labels
2. WHEN focus moves THEN the System SHALL show visible focus indicator (2px outline)
3. WHEN color conveys meaning THEN the System SHALL also use icons or text
4. WHEN images are displayed THEN the System SHALL have alt text descriptions
5. WHEN forms are used THEN the System SHALL associate labels with inputs
6. WHEN errors occur THEN the System SHALL announce them to screen readers
7. WHEN the user navigates THEN the System SHALL support logical tab order
8. WHEN contrast is measured THEN the System SHALL meet 4.5:1 ratio for text

### Requirement 16: Performance Requirements

**User Story:** As a user, I want a fast interface, so that I can work without delays.

#### Acceptance Criteria

1. WHEN the application loads THEN the System SHALL achieve First Contentful Paint under 1.5 seconds
2. WHEN the application loads THEN the System SHALL achieve Time to Interactive under 3 seconds
3. WHEN the user interacts THEN the System SHALL respond within 100ms
4. WHEN messages render THEN the System SHALL use virtual scrolling for lists over 100 items
5. WHEN assets load THEN the System SHALL use lazy loading for images and heavy components
6. WHEN the bundle is built THEN the System SHALL be under 200KB gzipped (excluding vendor)
7. WHEN animations run THEN the System SHALL maintain 60fps without jank

### Requirement 17: Internationalization

**User Story:** As a non-English user, I want the interface in my language, so that I can use it comfortably.

#### Acceptance Criteria

1. WHEN the UI renders THEN the System SHALL load translations from `/i18n/{locale}.json`
2. WHEN locale changes THEN the System SHALL update all visible text without page reload
3. WHEN a translation is missing THEN the System SHALL fall back to English with console warning
4. WHEN dates are displayed THEN the System SHALL format according to locale
5. WHEN numbers are displayed THEN the System SHALL format according to locale
6. WHEN RTL language is selected THEN the System SHALL mirror layout appropriately

### Requirement 18: Progressive Web App

**User Story:** As a mobile user, I want to install the app, so that I can access it like a native app.

#### Acceptance Criteria

1. WHEN the app is visited THEN the System SHALL register a service worker
2. WHEN offline THEN the System SHALL show cached UI with offline indicator
3. WHEN installable THEN the System SHALL show install prompt on supported browsers
4. WHEN installed THEN the System SHALL launch in standalone mode without browser chrome
5. WHEN the app icon is needed THEN the System SHALL provide multiple sizes (192px, 512px)

### Requirement 19: Component Library

**User Story:** As a developer, I want reusable components, so that I can build features consistently.

#### Acceptance Criteria

1. WHEN Button component is used THEN the System SHALL support variants: primary, secondary, ghost, danger
2. WHEN Input component is used THEN the System SHALL support types: text, password, email, number, textarea
3. WHEN Select component is used THEN the System SHALL support single and multi-select with search
4. WHEN Modal component is used THEN the System SHALL support sizes: small, medium, large, fullscreen
5. WHEN Card component is used THEN the System SHALL support header, body, footer slots
6. WHEN Avatar component is used THEN the System SHALL support image, initials, and icon variants
7. WHEN Badge component is used THEN the System SHALL support status colors and dot indicator
8. WHEN Tooltip component is used THEN the System SHALL support positions: top, right, bottom, left
9. WHEN Dropdown component is used THEN the System SHALL support keyboard navigation
10. WHEN Tabs component is used THEN the System SHALL support horizontal and vertical orientations

### Requirement 20: Testing Coverage

**User Story:** As a developer, I want comprehensive tests, so that UI functionality is verified.

#### Acceptance Criteria

1. WHEN Playwright tests run THEN the System SHALL verify all navigation paths
2. WHEN Playwright tests run THEN the System SHALL verify chat message sending and receiving
3. WHEN Playwright tests run THEN the System SHALL verify settings save and load
4. WHEN Playwright tests run THEN the System SHALL verify file upload flow
5. WHEN Playwright tests run THEN the System SHALL verify session management
6. WHEN Playwright tests run THEN the System SHALL verify keyboard shortcuts
7. WHEN Playwright tests run THEN the System SHALL verify accessibility with axe-core
8. WHEN tests complete THEN the System SHALL achieve 80% code coverage minimum



### Requirement 21: Voice Interface

**User Story:** As a user, I want voice input and output, so that I can interact hands-free.

#### Acceptance Criteria

1. WHEN voice input is enabled THEN the System SHALL show microphone button in chat input
2. WHEN the user clicks microphone THEN the System SHALL start speech recognition
3. WHEN speech is recognized THEN the System SHALL populate the chat input with transcribed text
4. WHEN voice output is enabled THEN the System SHALL read assistant responses aloud
5. WHEN TTS is playing THEN the System SHALL show audio waveform visualization
6. WHEN the user clicks stop THEN the System SHALL halt TTS playback immediately

### Requirement 22: Agent Control Panel

**User Story:** As a user, I want to control the agent, so that I can manage its behavior.

#### Acceptance Criteria

1. WHEN agent control panel opens THEN the System SHALL show current agent state (idle, thinking, executing)
2. WHEN the user clicks "Restart" THEN the System SHALL POST to `/v1/agent/restart`
3. WHEN the user clicks "Pause" THEN the System SHALL POST to `/v1/agent/pause`
4. WHEN the user clicks "Resume" THEN the System SHALL POST to `/v1/agent/resume`
5. WHEN cognitive state is available THEN the System SHALL display neuromodulator levels visually
6. WHEN the agent is paused THEN the System SHALL show paused indicator in header

### Requirement 23: Code Editor Integration

**User Story:** As a developer user, I want code editing capabilities, so that I can work with code effectively.

#### Acceptance Criteria

1. WHEN code is displayed THEN the System SHALL use syntax highlighting for 20+ languages
2. WHEN code block renders THEN the System SHALL show language label and copy button
3. WHEN code is editable THEN the System SHALL provide line numbers and basic editing
4. WHEN code is executed THEN the System SHALL show output in collapsible panel
5. WHEN code has errors THEN the System SHALL highlight error lines with markers

### Requirement 24: Search and Filter

**User Story:** As a user, I want to search and filter content, so that I can find information quickly.

#### Acceptance Criteria

1. WHEN global search is triggered THEN the System SHALL search across sessions, memories, and messages
2. WHEN search results display THEN the System SHALL group by type with result counts
3. WHEN the user clicks a result THEN the System SHALL navigate to that item
4. WHEN filters are applied THEN the System SHALL update results in real-time
5. WHEN search is cleared THEN the System SHALL restore default view

### Requirement 25: Data Export

**User Story:** As a user, I want to export my data, so that I can backup or analyze conversations.

#### Acceptance Criteria

1. WHEN export is requested THEN the System SHALL offer formats: JSON, Markdown, PDF
2. WHEN exporting a session THEN the System SHALL include all messages and metadata
3. WHEN exporting memories THEN the System SHALL include content and timestamps
4. WHEN export completes THEN the System SHALL trigger browser download
5. WHEN export fails THEN the System SHALL show error with retry option

### Requirement 26: Theming System

**User Story:** As a user, I want to customize the appearance, so that the interface suits my preferences.

#### Acceptance Criteria

1. WHEN theme settings open THEN the System SHALL show dark/light mode toggle
2. WHEN accent color is selected THEN the System SHALL update all accent-colored elements
3. WHEN font size is adjusted THEN the System SHALL scale all text proportionally
4. WHEN theme changes THEN the System SHALL persist preference to localStorage
5. WHEN system preference changes THEN the System SHALL follow OS dark/light mode if set to "auto"

### Requirement 27: Onboarding Experience

**User Story:** As a new user, I want guided onboarding, so that I understand how to use the system.

#### Acceptance Criteria

1. WHEN a new user visits THEN the System SHALL show welcome modal with quick start guide
2. WHEN onboarding starts THEN the System SHALL highlight key UI elements with tooltips
3. WHEN the user completes onboarding THEN the System SHALL mark as complete in localStorage
4. WHEN the user skips onboarding THEN the System SHALL not show it again
5. WHEN help is requested THEN the System SHALL show contextual help for current feature

### Requirement 28: Error Handling

**User Story:** As a user, I want clear error handling, so that I understand and recover from issues.

#### Acceptance Criteria

1. WHEN an API call fails THEN the System SHALL show user-friendly error message
2. WHEN network is offline THEN the System SHALL show offline banner with retry button
3. WHEN session expires THEN the System SHALL redirect to login with message
4. WHEN validation fails THEN the System SHALL highlight invalid fields with messages
5. WHEN unexpected error occurs THEN the System SHALL show error boundary with report option

### Requirement 29: Mobile Optimization

**User Story:** As a mobile user, I want a touch-optimized interface, so that I can use it on my phone.

#### Acceptance Criteria

1. WHEN viewport is mobile THEN the System SHALL use bottom navigation bar
2. WHEN touch is detected THEN the System SHALL increase tap targets to 44px minimum
3. WHEN keyboard opens THEN the System SHALL adjust layout to keep input visible
4. WHEN swiping THEN the System SHALL support gesture navigation (swipe to go back)
5. WHEN pull-to-refresh is used THEN the System SHALL reload current view

### Requirement 30: Backend API Compatibility

**User Story:** As a developer, I want full backend compatibility, so that the new UI works with existing services.

#### Acceptance Criteria

1. WHEN the UI makes API calls THEN the System SHALL use existing Gateway endpoints without modification
2. WHEN authentication is required THEN the System SHALL use existing JWT/cookie mechanism
3. WHEN SSE connects THEN the System SHALL use existing event format and types
4. WHEN settings are saved THEN the System SHALL use existing `/v1/settings/sections` format
5. WHEN uploads are sent THEN the System SHALL use existing `/v1/uploads` multipart format
6. WHEN sessions are managed THEN the System SHALL use existing session API contracts

## Architecture Constraints

### Technology Stack

| Layer | Technology | Justification |
|-------|------------|---------------|
| Framework | Alpine.js 3.x | Lightweight, reactive, existing codebase |
| Styling | CSS Custom Properties + Utility Classes | Performance, theming, no build step |
| Build | Vite (optional) | Fast dev server, optimized production builds |
| Icons | Material Symbols | Comprehensive, variable weight |
| Code Highlighting | Prism.js or Shiki | Lightweight, many languages |
| Markdown | Marked.js | Fast, extensible |
| Math | KaTeX | Fast LaTeX rendering |
| Testing | Playwright | E2E, accessibility, visual regression |

### File Structure

```
webui/
├── design-system/           # Design tokens and base styles
│   ├── tokens.css           # CSS custom properties
│   ├── typography.css       # Font scales
│   ├── colors.css           # Color palette
│   └── animations.css       # Transitions and keyframes
│
├── components/              # Reusable UI components
│   ├── button/
│   ├── input/
│   ├── modal/
│   ├── card/
│   ├── avatar/
│   ├── badge/
│   ├── tooltip/
│   ├── dropdown/
│   ├── tabs/
│   └── toast/
│
├── features/                # Feature modules
│   ├── chat/
│   ├── settings/
│   ├── memory/
│   ├── scheduler/
│   ├── health/
│   ├── upload/
│   └── voice/
│
├── layouts/                 # Page layouts
│   ├── main-layout.html
│   ├── sidebar.html
│   └── mobile-layout.html
│
├── core/                    # Core infrastructure
│   ├── api/
│   ├── state/
│   ├── events/
│   └── utils/
│
├── i18n/                    # Translations
│   ├── en.json
│   └── es.json
│
└── index.html               # Entry point
```

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| First Contentful Paint | < 1.5s | Lighthouse |
| Time to Interactive | < 3s | Lighthouse |
| Interaction Response | < 100ms | Performance API |
| Bundle Size | < 200KB gzipped | Build output |
| Accessibility Score | 100 | Lighthouse |
| Test Coverage | > 80% | Playwright |
| Mobile Usability | 100 | Lighthouse |



### Requirement 31: Screen Layouts - Detailed Specifications

**User Story:** As a user, I want well-designed screen layouts, so that I can efficiently use all features.

#### Acceptance Criteria - Main Application Shell

1. WHEN the application loads THEN the System SHALL display:
   - Header bar (48px height): Logo, breadcrumb, search, notifications bell, user avatar, settings gear
   - Sidebar (240px width, collapsible to 64px): Navigation icons with labels, session list, quick actions
   - Main content area: Dynamic based on selected feature
   - Status bar (24px height): Connection status, agent state, version info

#### Acceptance Criteria - Chat Screen Layout

2. WHEN Chat screen is active THEN the System SHALL display:
   - Session header: Session name (editable), participant count, session actions dropdown
   - Message list: Virtualized scroll, grouped by date, unread indicator
   - Tool execution panel (collapsible right panel, 320px): Active tool cards, execution history
   - Input area: Fixed at bottom, 80px min height

#### Acceptance Criteria - Settings Screen Layout

3. WHEN Settings screen is active THEN the System SHALL display:
   - Full-screen modal overlay with backdrop blur
   - Left sidebar (200px): Tab navigation with icons (Agent, External, Connectivity, System)
   - Content area: Scrollable grid of setting cards
   - Footer: Cancel and Save buttons, unsaved changes indicator

#### Acceptance Criteria - Memory Dashboard Layout

4. WHEN Memory Dashboard is active THEN the System SHALL display:
   - Search bar with filters (type, date range, relevance)
   - Memory grid: Cards showing preview, score, timestamp
   - Detail panel (slide-in from right): Full memory content, metadata, actions

#### Acceptance Criteria - Scheduler Layout

5. WHEN Scheduler is active THEN the System SHALL display:
   - View toggle: List view / Calendar view
   - Task list: Sortable table with columns (Name, Type, Schedule, Status, Actions)
   - Task detail panel: Full task configuration, execution history, logs

### Requirement 32: Button Styles - Detailed Specifications

**User Story:** As a user, I want consistent, beautiful buttons, so that actions are clear and satisfying to use.

#### Acceptance Criteria - Button Variants

1. WHEN Primary button renders THEN the System SHALL display:
   - Background: `--gradient-ai` (indigo to violet gradient)
   - Text: White, font-weight 500
   - Padding: 10px 20px
   - Border-radius: `--radius-md` (8px)
   - Hover: Brightness increase (1.1), subtle scale (1.02)
   - Active: Scale down (0.98), brightness decrease
   - Disabled: Opacity 0.5, cursor not-allowed

2. WHEN Secondary button renders THEN the System SHALL display:
   - Background: `--surface-2`
   - Border: 1px solid `--glass-border`
   - Text: `--text-primary`
   - Hover: Background lightens, border becomes accent

3. WHEN Ghost button renders THEN the System SHALL display:
   - Background: Transparent
   - Text: `--text-secondary`
   - Hover: Background `--surface-1`, text `--text-primary`

4. WHEN Danger button renders THEN the System SHALL display:
   - Background: `--error` (#ef4444)
   - Text: White
   - Hover: Darker red, scale effect

5. WHEN Icon button renders THEN the System SHALL display:
   - Square aspect ratio (40px x 40px default)
   - Icon centered, 20px size
   - Border-radius: `--radius-md`
   - Hover: Background `--surface-2`

### Requirement 33: Card Styles - Detailed Specifications

**User Story:** As a user, I want beautiful, functional cards, so that information is organized and scannable.

#### Acceptance Criteria - Base Card

1. WHEN a card renders THEN the System SHALL display:
   - Background: `--surface-1` with `--glass-bg` effect
   - Border: 1px solid `--glass-border`
   - Border-radius: `--radius-lg` (12px)
   - Padding: `--space-5` (20px)
   - Shadow: `--shadow-md`
   - Backdrop-filter: `--glass-blur`

2. WHEN a card is hovered THEN the System SHALL:
   - Increase shadow to `--shadow-lg`
   - Add subtle border glow (accent color at 20% opacity)
   - Transition: 200ms ease-out

#### Acceptance Criteria - Settings Card

3. WHEN a settings card renders THEN the System SHALL display:
   - Header row: Icon (24px, accent color), Title (H3), Collapse toggle
   - Description: Muted text below title
   - Divider: 1px line with gradient fade
   - Content: Form fields with consistent spacing (16px gap)
   - Status indicator: Dot showing saved/unsaved state

4. WHEN settings card is collapsed THEN the System SHALL:
   - Show only header row
   - Display summary text (key values)
   - Animate height change (200ms)

#### Acceptance Criteria - Model Card (Chat, Utility, Browser, Embedding)

5. WHEN a model card renders THEN the System SHALL display:
   - Icon: Model-specific icon (chat bubble, wrench, globe, cube)
   - Provider selector: Dropdown with provider logos
   - Model input: Text field with autocomplete
   - Configuration grid: 2-column layout for settings
   - Advanced toggle: Expandable section for kwargs, rate limits

#### Acceptance Criteria - Tool Execution Card

6. WHEN a tool card renders THEN the System SHALL display:
   - Tool icon with status ring (blue=running, green=success, red=error)
   - Tool name and type
   - Progress indicator (spinner or progress bar)
   - Expandable content: Input args, output result
   - Timestamp and duration

### Requirement 34: Form Input Styles - Detailed Specifications

**User Story:** As a user, I want clear, accessible form inputs, so that I can configure settings easily.

#### Acceptance Criteria - Text Input

1. WHEN text input renders THEN the System SHALL display:
   - Background: `--surface-2`
   - Border: 1px solid `--glass-border`
   - Border-radius: `--radius-md`
   - Padding: 10px 14px
   - Font: Body size (14px)
   - Placeholder: `--text-muted`
   - Focus: Border color `--accent-primary`, subtle glow

2. WHEN input has error THEN the System SHALL:
   - Border color: `--error`
   - Show error message below in red
   - Add error icon inside input

#### Acceptance Criteria - Select/Dropdown

3. WHEN select renders THEN the System SHALL display:
   - Same base styling as text input
   - Chevron icon on right
   - Dropdown panel: `--surface-1` with shadow
   - Options: Hover highlight, selected checkmark
   - Support for option icons (provider logos)

#### Acceptance Criteria - Toggle Switch

4. WHEN toggle renders THEN the System SHALL display:
   - Track: 44px x 24px, `--surface-3` background
   - Thumb: 20px circle, white
   - Active state: Track becomes `--accent-primary`
   - Transition: 150ms ease-out
   - Label: To the right of toggle

#### Acceptance Criteria - Slider

5. WHEN slider renders THEN the System SHALL display:
   - Track: 4px height, `--surface-3`
   - Filled portion: `--accent-primary`
   - Thumb: 16px circle with border
   - Value label: Above thumb or to the side
   - Min/max labels at ends

#### Acceptance Criteria - JSON/Code Editor

6. WHEN JSON editor renders THEN the System SHALL display:
   - Monaco-style editor or Ace
   - Syntax highlighting for JSON
   - Line numbers
   - Error highlighting for invalid JSON
   - Format button to prettify

### Requirement 35: Modal Styles - Detailed Specifications

**User Story:** As a user, I want polished modal dialogs, so that focused tasks are clear and non-disruptive.

#### Acceptance Criteria - Modal Base

1. WHEN modal opens THEN the System SHALL:
   - Display backdrop with blur effect and dark overlay (rgba(0,0,0,0.7))
   - Animate modal from scale(0.95) + opacity(0) to scale(1) + opacity(1)
   - Center modal vertically and horizontally
   - Trap focus within modal
   - Close on Escape key or backdrop click (configurable)

2. WHEN modal renders THEN the System SHALL display:
   - Header: Title, optional subtitle, close X button
   - Body: Scrollable content area
   - Footer: Action buttons (right-aligned)
   - Border-radius: `--radius-xl` (16px)
   - Max-width based on size prop (sm: 400px, md: 600px, lg: 800px, xl: 1000px, full: 95vw)

#### Acceptance Criteria - Settings Modal (Full-Screen)

3. WHEN settings modal opens THEN the System SHALL:
   - Use full-screen variant (95vw x 90vh)
   - Display sidebar navigation on left
   - Display scrollable content on right
   - Persist scroll position per tab
   - Show unsaved changes warning on close attempt

