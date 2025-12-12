# Design Document: WebUI Complete Redesign

## Overview

This design document specifies the technical architecture for a complete UI/UX redesign of the SomaAgent01 Web Interface. The implementation creates a state-of-the-art, lightning-fast, AI-native interface with a modern component-based architecture, reactive state management, and full integration with the existing production backend.

### Goals

1. Create a unified design system with CSS custom properties
2. Implement card-based settings interface with all 17 sections
3. Build AI-native chat interface with streaming visualization
4. Achieve sub-100ms interaction response times
5. Maintain 100% backend API compatibility
6. Achieve WCAG 2.1 AA accessibility compliance

### Non-Goals

- Backend API changes (use existing endpoints)
- Database schema changes
- Authentication flow changes (use existing JWT/cookie)

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PRESENTATION LAYER                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     WebUI (Alpine.js + CSS)                          │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐  │   │
│  │  │ Design      │  │ Components  │  │ Features    │  │ Layouts    │  │   │
│  │  │ System      │  │ Library     │  │ Modules     │  │            │  │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CORE LAYER                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ API Client  │  │ State Store │  │ Event Bus   │  │ SSE Manager │        │
│  │ (fetchApi)  │  │ (Alpine)    │  │ (emit/on)   │  │ (streaming) │        │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           GATEWAY (Existing)                                 │
│  /v1/sessions, /v1/settings/sections, /v1/uploads, /v1/health, SSE         │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Directory Structure

```
webui/
├── design-system/              # Design tokens and base styles
│   ├── tokens.css              # CSS custom properties (colors, spacing, etc.)
│   ├── typography.css          # Font scales and text styles
│   ├── animations.css          # Transitions and keyframes
│   └── utilities.css           # Utility classes
│
├── components/                 # Reusable UI components
│   ├── button/
│   │   ├── button.css
│   │   └── button.html         # Alpine component template
│   ├── card/
│   │   ├── card.css
│   │   └── card.html
│   ├── input/
│   │   ├── input.css
│   │   └── input.html
│   ├── modal/
│   │   ├── modal.css
│   │   └── modal.html
│   ├── select/
│   ├── toggle/
│   ├── slider/
│   ├── tooltip/
│   ├── toast/
│   ├── avatar/
│   ├── badge/
│   └── dropdown/
│
├── features/                   # Feature modules
│   ├── chat/
│   │   ├── chat.store.js       # Chat state management
│   │   ├── chat.api.js         # Chat API calls
│   │   ├── chat.css            # Chat-specific styles
│   │   ├── message-list.html   # Message list component
│   │   ├── message-item.html   # Single message component
│   │   ├── chat-input.html     # Input area component
│   │   └── index.js
│   ├── settings/
│   │   ├── settings.store.js
│   │   ├── settings.api.js
│   │   ├── settings.css
│   │   ├── settings-modal.html
│   │   ├── settings-card.html
│   │   ├── model-card.html     # Reusable model settings card
│   │   └── index.js
│   ├── capsules/               # Capsule marketplace & loader
│   │   ├── capsules.store.js
│   │   ├── capsules.api.js
│   │   ├── capsules.events.js
│   │   └── index.js
│   ├── project-manager/        # Provider-agnostic project UI
│   │   ├── pm.store.js
│   │   ├── pm.api.js           # Adapter registry + calls
│   │   ├── providers/          # Plane, ProjectOpen, MS Project adapters
│   │   └── index.js
│   ├── memory/
│   │   ├── memory.store.js
│   │   ├── memory.api.js
│   │   └── index.js
│   ├── scheduler/
│   │   ├── scheduler.store.js
│   │   ├── scheduler.api.js
│   │   └── index.js
│   ├── health/
│   │   ├── health.store.js
│   │   ├── health.api.js
│   │   └── index.js
│   └── upload/
│       ├── upload.store.js
│       ├── upload.api.js
│       └── index.js
│
├── layouts/
│   ├── app-shell.html          # Main application shell
│   ├── sidebar.html            # Sidebar navigation
│   └── header.html             # Header bar
│
├── core/
│   ├── api/
│   │   ├── client.js           # HTTP client with interceptors
│   │   └── endpoints.js        # Centralized endpoint definitions
│   ├── state/
│   │   └── store.js            # Alpine store factory
│   ├── events/
│   │   ├── types.js            # Event type constants
│   │   └── bus.js              # Event emitter
│   ├── sse/
│   │   └── manager.js          # SSE connection manager
│   └── index.js
│
├── i18n/
│   ├── en.json
│   └── es.json
│
└── index.html                  # Entry point
```

## Components and Interfaces

### Design System Tokens

Based on the reference dashboard styling (tmp/DASHBOARD), the design system uses a clean, modern approach with glassmorphism effects and smooth transitions.

```css
/* design-system/tokens.css */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

:root {
  /* Typography */
  --font-sans: "Inter", system-ui, -apple-system, sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', monospace;
  
  /* Colors - Light Theme (Default for reference compatibility) */
  --bg-primary: #f3f4f6;
  --bg-secondary: #ffffff;
  --bg-tertiary: #e5e7eb;
  --surface-1: #ffffff;
  --surface-2: #f9fafb;
  --surface-3: #f3f4f6;
  
  --text-primary: #111827;
  --text-secondary: #4b5563;
  --text-muted: #6b7280;
  
  --border-color: #e5e7eb;
  --accent-color: #4f46e5;
  --accent-hover: #4338ca;
  --accent-primary: #6366f1;
  --accent-secondary: #818cf8;
  
  --success: #10b981;
  --warning: #f59e0b;
  --danger: #ef4444;
  --error: #ef4444;
  --info: #3b82f6;
  
  /* Glass Effects */
  --glass-bg: rgba(255, 255, 255, 0.7);
  --glass-border: rgba(255, 255, 255, 0.5);
  --glass-blur: blur(12px);
  
  /* Gradients */
  --gradient-ai: linear-gradient(135deg, #6366f1 0%, #818cf8 50%, #a855f7 100%);
  --gradient-glow: radial-gradient(circle, rgba(99,102,241,0.15) 0%, transparent 70%);
  
  /* Spacing */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 20px;
  --space-6: 24px;
  --space-8: 32px;
  --space-10: 40px;
  
  /* Border Radius */
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-xl: 1rem;
  --radius-full: 9999px;
  
  /* Shadows */
  --shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
  --shadow-md: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06);
  --shadow-lg: 0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -2px rgba(0,0,0,0.05);
  --shadow-glow: 0 0 20px rgba(99,102,241,0.3);
  
  /* Animation */
  --duration-fast: 150ms;
  --duration-normal: 200ms;
  --duration-slow: 300ms;
  --ease-out: cubic-bezier(0.16, 1, 0.3, 1);
  --ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
  --transition-all: all 0.3s ease;
}

/* Dark Theme */
[data-theme="dark"] {
  --bg-primary: #0f172a;
  --bg-secondary: #1e293b;
  --bg-tertiary: #334155;
  --surface-1: #1e293b;
  --surface-2: #334155;
  --surface-3: #475569;
  
  --text-primary: #f9fafb;
  --text-secondary: #9ca3af;
  --text-muted: #6b7280;
  
  --border-color: #374151;
  --accent-color: #6366f1;
  --accent-hover: #818cf8;
  
  --glass-bg: rgba(30, 41, 59, 0.7);
  --glass-border: rgba(255, 255, 255, 0.1);
}

/* Base Reset */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: var(--font-sans);
  background-color: var(--bg-primary);
  color: var(--text-primary);
  transition: background-color 0.3s ease, color 0.3s ease;
  overflow-x: hidden;
}

/* Glassmorphism Utilities */
.glass {
  background: var(--glass-bg);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid var(--glass-border);
  box-shadow: var(--shadow-md);
}

.glass-panel {
  background: var(--glass-bg);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-xl);
}

/* Layout Utilities */
.flex-center {
  display: flex;
  align-items: center;
  justify-content: center;
}

.flex-between {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.grid-cols-dashboard {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.5rem;
}

/* Typography */
h1, h2, h3, h4, h5, h6 {
  color: var(--text-primary);
  font-weight: 600;
  line-height: 1.25;
}

/* Custom Scrollbar */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: var(--text-secondary);
  border-radius: 4px;
  opacity: 0.5;
}

::-webkit-scrollbar-thumb:hover {
  background: var(--text-primary);
}

/* Transition Utility */
.transition-all {
  transition: var(--transition-all);
}
```

## Architecture Extensions for Capsules & Adapters
- **Capsule Loader**: Fetch manifest (kind, version, integrity, entrypoints, theme assets); verify signature/integrity before dynamic import of JS/CSS.
- **Feature Registry**: Maintain registered adapters (e.g., project-manager providers) and theme packs; emit events on register/unregister.
- **Marketplace UI**: Grid + detail drawer with install/update/rollback, signature badges, compatibility checks, dependency warnings.
- **Provider Adapters**: Each implements provider-neutral interfaces (projects/boards/tasks CRUD, search, assignments, files). UI never imports provider-specific code directly.
- **Theme Packs**: Theme-type capsules register token overrides; ThemeRegistry applies via data-theme or injected CSS module.

## Canvas Visualization Guidance
- Scale by `devicePixelRatio`, debounce resize, reuse contexts to avoid reflows.
- Use CSS variables for all colors to stay theme-compatible.
- Decimate/virtualize for large datasets; incremental updates for streaming/SSE data.
- Clean up listeners on unmount; target <16ms per frame for 60fps.

## In-Browser Code Execution to Canvas
- Runtime: Web Worker hosting Pyodide (Python WASM) as the “venv”; optional future runtimes via adapters.
- IPC protocol: run/cancel/status/stdout/stderr/draw messages; timeouts and resource guards enforced in worker.
- Rendering: OffscreenCanvas preferred; fall back to main-thread canvas helper. Colors read from design-system CSS vars.
- UI shell: Code runner component with run/cancel buttons, live console, canvas pane, status badges.
- Cleanup: Dispose worker/OffscreenCanvas per run; rehydrate tokens on theme change.

## Canvas Module Layering Pattern
- Module Manifest: declares kind, entrypoints, adapters, `canvasTools`, `uiComponents`, and theme packs; registered with feature registry.
- Canvas Renderer: shared host handling DPR scaling, resize observer, event wiring, OffscreenCanvas transfer, theme token injection; pluggable backends (2D default, Pixi/Konva optional).
- Canvas Tool Interface: `init(ctx, theme)`, `render(state)`, `handleEvent(evt)`, `dispose()`; tools may run in a Worker and emit draw commands.
- Component Shell: React/Next wrapper that mounts the renderer, passes props/state, and surfaces controls (run, zoom, filters) without domain logic.
- Compatibility: Tools never import provider-specific code; they consume draw commands/theme only, so swapping providers or backends doesn’t break UI.

### Canvas Theming (Memory/Workflow)
- Use CSS custom properties for all graph backgrounds, borders, strokes, fills; no hardcoded colors.
- Re-render on resize and theme change; scale for DPR>1 for crisp output.
- Apply the same renderer/tool contracts for memory graphs and workflow canvases (timeline/board).

### Memory Data Flow (SomaBrain)
- Data source: gateway/SomaBrain endpoints (e.g., `GET /v1/admin/memory` for admin list, `/v1/memory/search` or `/memory/recall` for recall).
- Auth: Bearer/API token + tenant/persona headers as required.
- Relatedness: prefer backend-provided similarities; if embeddings are returned, compute cosine client-side to build links.
- Live updates: subscribe to SSE if available; otherwise poll at configurable interval.
- Writes: use backend (`/v1/memory/batch` or `/memory/remember`) and re-fetch graph on success.
- Export: use `/v1/memory/export` (NDJSON) or async export job endpoints.

### Component: Button

```html
<!-- components/button/button.html -->
<template x-component="ui-button">
  <button
    :class="{
      'btn': true,
      'btn-primary': variant === 'primary',
      'btn-secondary': variant === 'secondary',
      'btn-ghost': variant === 'ghost',
      'btn-danger': variant === 'danger',
      'btn-icon': variant === 'icon',
      'btn-sm': size === 'sm',
      'btn-lg': size === 'lg',
      'btn-loading': loading
    }"
    :disabled="disabled || loading"
    @click="$dispatch('click')"
  >
    <span x-show="loading" class="btn-spinner"></span>
    <span x-show="!loading" class="btn-content">
      <slot></slot>
    </span>
  </button>
</template>
```

```css
/* components/button/button.css */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  padding: 10px 20px;
  border-radius: var(--radius-md);
  font-family: var(--font-sans);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-out);
  border: none;
  outline: none;
}

.btn-primary {
  background: var(--gradient-ai);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  filter: brightness(1.1);
  transform: scale(1.02);
}

.btn-primary:active:not(:disabled) {
  transform: scale(0.98);
  filter: brightness(0.95);
}

.btn-secondary {
  background: var(--surface-2);
  border: 1px solid var(--glass-border);
  color: var(--text-primary);
}

.btn-secondary:hover:not(:disabled) {
  background: var(--surface-3);
  border-color: var(--accent-primary);
}

.btn-ghost {
  background: transparent;
  color: var(--text-secondary);
}

.btn-ghost:hover:not(:disabled) {
  background: var(--surface-1);
  color: var(--text-primary);
}

.btn-danger {
  background: var(--error);
  color: white;
}

.btn-danger:hover:not(:disabled) {
  filter: brightness(0.9);
}

.btn-icon {
  width: 40px;
  height: 40px;
  padding: 0;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid currentColor;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
```

### Component: Settings Card

```html
<!-- components/card/settings-card.html -->
<template x-component="settings-card">
  <div 
    class="settings-card"
    :class="{ 'settings-card-expanded': expanded, 'settings-card-dirty': isDirty }"
  >
    <div class="settings-card-header" @click="expanded = !expanded">
      <div class="settings-card-icon" :style="{ color: iconColor }">
        <span class="material-symbols-outlined" x-text="icon"></span>
      </div>
      <div class="settings-card-title-group">
        <h3 class="settings-card-title" x-text="title"></h3>
        <p class="settings-card-description" x-text="description"></p>
      </div>
      <div class="settings-card-summary" x-show="!expanded" x-text="summary"></div>
      <button class="settings-card-toggle">
        <span class="material-symbols-outlined" x-text="expanded ? 'expand_less' : 'expand_more'"></span>
      </button>
    </div>
    <div class="settings-card-content" x-show="expanded" x-collapse>
      <div class="settings-card-divider"></div>
      <div class="settings-card-fields">
        <slot></slot>
      </div>
    </div>
  </div>
</template>
```

### Feature: Settings Store

```javascript
// features/settings/settings.store.js
import { createStore } from '../../core/state/store.js';
import { settingsApi } from './settings.api.js';

export const settingsStore = createStore('settings', {
  // State
  isOpen: false,
  isLoading: false,
  isSaving: false,
  activeTab: 'agent',
  sections: [],
  originalSections: [],
  expandedCards: new Set(),
  
  // Computed
  get isDirty() {
    return JSON.stringify(this.sections) !== JSON.stringify(this.originalSections);
  },
  
  get filteredSections() {
    return this.sections.filter(s => s.tab === this.activeTab);
  },
  
  get tabs() {
    return [
      { id: 'agent', label: 'Agent', icon: 'smart_toy' },
      { id: 'external', label: 'External', icon: 'key' },
      { id: 'connectivity', label: 'Connectivity', icon: 'hub' },
      { id: 'system', label: 'System', icon: 'settings' },
    ];
  },
  
  // Actions
  async open() {
    this.isOpen = true;
    await this.fetchSettings();
  },
  
  close() {
    if (this.isDirty) {
      // Show confirmation dialog
      return;
    }
    this.isOpen = false;
  },
  
  async fetchSettings() {
    this.isLoading = true;
    try {
      const data = await settingsApi.getSections();
      this.sections = data.sections;
      this.originalSections = JSON.parse(JSON.stringify(data.sections));
    } catch (error) {
      console.error('Failed to fetch settings:', error);
    } finally {
      this.isLoading = false;
    }
  },
  
  async saveSettings() {
    this.isSaving = true;
    try {
      await settingsApi.saveSections(this.sections);
      this.originalSections = JSON.parse(JSON.stringify(this.sections));
      this.isOpen = false;
      // Show success toast
    } catch (error) {
      console.error('Failed to save settings:', error);
      // Show error toast
    } finally {
      this.isSaving = false;
    }
  },
  
  setTab(tabId) {
    this.activeTab = tabId;
  },
  
  toggleCard(sectionId) {
    if (this.expandedCards.has(sectionId)) {
      this.expandedCards.delete(sectionId);
    } else {
      this.expandedCards.add(sectionId);
    }
  },
  
  updateField(sectionId, fieldId, value) {
    const section = this.sections.find(s => s.id === sectionId);
    if (section) {
      const field = section.fields.find(f => f.id === fieldId);
      if (field) {
        field.value = value;
      }
    }
  },
});
```

### Feature: Chat Store with Streaming

```javascript
// features/chat/chat.store.js
import { createStore } from '../../core/state/store.js';
import { chatApi } from './chat.api.js';
import { sseManager } from '../../core/sse/manager.js';

export const chatStore = createStore('chat', {
  // State
  sessionId: null,
  messages: [],
  isStreaming: false,
  isThinking: false,
  currentStreamContent: '',
  connectionStatus: 'disconnected', // connected, disconnected, reconnecting
  inputValue: '',
  attachments: [],
  
  // Actions
  async sendMessage(content) {
    if (!content.trim() && this.attachments.length === 0) return;
    
    // Add user message
    const userMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content,
      attachments: [...this.attachments],
      timestamp: new Date().toISOString(),
    };
    this.messages.push(userMessage);
    this.inputValue = '';
    this.attachments = [];
    
    // Send to backend
    try {
      await chatApi.sendMessage(this.sessionId, content, userMessage.attachments);
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  },
  
  handleStreamEvent(event) {
    switch (event.type) {
      case 'assistant.started':
        this.isStreaming = true;
        this.currentStreamContent = '';
        this.messages.push({
          id: event.data.message_id,
          role: 'assistant',
          content: '',
          isStreaming: true,
          timestamp: new Date().toISOString(),
        });
        break;
        
      case 'assistant.thinking.started':
        this.isThinking = true;
        break;
        
      case 'assistant.thinking.final':
        this.isThinking = false;
        break;
        
      case 'assistant.delta':
        this.currentStreamContent += event.data.content;
        const streamingMsg = this.messages.find(m => m.isStreaming);
        if (streamingMsg) {
          streamingMsg.content = this.currentStreamContent;
        }
        break;
        
      case 'assistant.final':
        this.isStreaming = false;
        const finalMsg = this.messages.find(m => m.isStreaming);
        if (finalMsg) {
          finalMsg.isStreaming = false;
          finalMsg.content = event.data.content || this.currentStreamContent;
        }
        this.currentStreamContent = '';
        break;
        
      case 'assistant.tool.started':
        // Add tool execution card
        break;
        
      case 'assistant.tool.final':
        // Update tool execution card
        break;
    }
  },
  
  connectSSE() {
    if (!this.sessionId) return;
    
    sseManager.connect(this.sessionId, {
      onMessage: (event) => this.handleStreamEvent(event),
      onConnect: () => { this.connectionStatus = 'connected'; },
      onDisconnect: () => { this.connectionStatus = 'disconnected'; },
      onReconnecting: () => { this.connectionStatus = 'reconnecting'; },
    });
  },
  
  disconnectSSE() {
    sseManager.disconnect();
  },
});
```

## Data Models

### Settings Section Model

```typescript
interface SettingsSection {
  id: string;
  tab: 'agent' | 'external' | 'connectivity' | 'system';
  title: string;
  description: string;
  icon: string;
  fields: SettingsField[];
}

interface SettingsField {
  id: string;
  title: string;
  type: 'text' | 'password' | 'select' | 'toggle' | 'slider' | 'textarea' | 'json' | 'button';
  value: any;
  options?: { value: string; label: string; icon?: string }[];
  min?: number;
  max?: number;
  step?: number;
  placeholder?: string;
  required?: boolean;
  action?: string;
  target?: string;
}
```

### Message Model

```typescript
interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  attachments?: Attachment[];
  toolCalls?: ToolCall[];
  timestamp: string;
  isStreaming?: boolean;
}

interface ToolCall {
  id: string;
  name: string;
  status: 'pending' | 'running' | 'success' | 'error';
  input: Record<string, any>;
  output?: any;
  error?: string;
  duration?: number;
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Design System Token Completeness
*For any* CSS custom property referenced in component styles, that property SHALL be defined in the design system tokens file.
**Validates: Requirements 1.1, 1.2, 1.6, 1.7, 1.8, 1.9, 1.10**

### Property 2: Responsive Layout Breakpoints
*For any* viewport width, the layout SHALL display the correct panel configuration (3-panel for desktop, 2-panel for tablet, 1-panel for mobile).
**Validates: Requirements 2.6, 2.7**

### Property 3: Settings Card State Consistency
*For any* settings card, the expanded/collapsed state SHALL be visually consistent with the stored state, and unsaved changes SHALL be indicated.
**Validates: Requirements 7.6, 7.7, 7.8, 7.9**

### Property 4: Model Card Field Completeness
*For any* model settings card (Chat, Utility, Browser, Embedding), all required fields (provider, model name, context length) SHALL be rendered.
**Validates: Requirements 7.11, 7.12, 7.13, 7.14**

### Property 5: API Key Masking
*For any* API key field, the value SHALL be masked by default and only revealed when explicitly toggled.
**Validates: Requirements 7.26, 7.27**

### Property 6: Message Role Styling
*For any* chat message, the styling (alignment, avatar, colors) SHALL correctly reflect the message role (user vs assistant).
**Validates: Requirements 4.2, 4.3**

### Property 7: Streaming State Visualization
*For any* streaming assistant message, the UI SHALL display progressive content with cursor animation until the stream completes.
**Validates: Requirements 4.4, 4.5, 4.6**

### Property 8: Code Block Syntax Highlighting
*For any* code block in a message, syntax highlighting SHALL be applied based on the detected or specified language.
**Validates: Requirements 4.7**

### Property 9: SSE Event Handling
*For any* SSE event type (started, delta, final, tool), the chat store SHALL update state correctly and the UI SHALL reflect the change.
**Validates: Requirements 12.2, 12.3, 12.4, 12.7, 12.8**

### Property 10: Backend API Compatibility
*For any* API call made by the UI, the request format SHALL match the existing Gateway endpoint contract.
**Validates: Requirements 30.1, 30.2, 30.3, 30.4, 30.5, 30.6**

## Error Handling

### API Error Handling

```javascript
// core/api/client.js
export async function fetchApi(url, options = {}) {
  try {
    const response = await fetch(url, {
      ...options,
      credentials: 'same-origin',
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new ApiError(response.status, error.detail || 'Request failed');
    }
    
    return response.json();
  } catch (error) {
    if (error instanceof ApiError) throw error;
    throw new ApiError(0, 'Network error');
  }
}

class ApiError extends Error {
  constructor(status, message) {
    super(message);
    this.status = status;
  }
}
```

### SSE Reconnection

```javascript
// core/sse/manager.js
class SSEManager {
  constructor() {
    this.eventSource = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 10;
    this.baseDelay = 1000;
  }
  
  connect(sessionId, callbacks) {
    const url = `/v1/sessions/${sessionId}/events?stream=true`;
    this.eventSource = new EventSource(url);
    
    this.eventSource.onopen = () => {
      this.reconnectAttempts = 0;
      callbacks.onConnect?.();
    };
    
    this.eventSource.onerror = () => {
      this.eventSource.close();
      this.scheduleReconnect(sessionId, callbacks);
    };
    
    this.eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      callbacks.onMessage?.(data);
    };
  }
  
  scheduleReconnect(sessionId, callbacks) {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      callbacks.onDisconnect?.();
      return;
    }
    
    callbacks.onReconnecting?.();
    const delay = Math.min(this.baseDelay * Math.pow(2, this.reconnectAttempts), 30000);
    this.reconnectAttempts++;
    
    setTimeout(() => this.connect(sessionId, callbacks), delay);
  }
}
```

## Testing Strategy

### Dual Testing Approach

This design requires both unit tests and property-based tests:
- **Unit tests**: Verify specific examples, edge cases, and error conditions
- **Property tests**: Verify universal properties that should hold across all inputs

### Property-Based Testing Library

**Library**: fast-check (JavaScript)

Each property-based test MUST:
1. Run a minimum of 100 iterations
2. Be tagged with a comment referencing the correctness property
3. Use the format: `**Feature: webui-complete-redesign, Property {number}: {property_text}**`

### Test Categories

1. **Design System Tests**: Verify CSS variables exist and have valid values
2. **Component Tests**: Verify components render correctly with various props
3. **Store Tests**: Verify state management logic
4. **API Tests**: Verify API calls use correct endpoints and formats
5. **E2E Tests**: Verify full user flows with Playwright
