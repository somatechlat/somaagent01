# WebUI Architecture

State-of-the-art frontend architecture following VIBE Coding Rules and modern best practices.

## Directory Structure

```
webui/
├── core/                    # Core infrastructure (framework-agnostic)
│   ├── api/                 # API client layer
│   │   ├── client.js        # HTTP client with interceptors
│   │   └── endpoints.js     # Centralized endpoint definitions
│   ├── events/              # Event system
│   │   └── types.js         # Event type constants
│   ├── state/               # State management
│   │   └── store.js         # Alpine store factory
│   └── index.js             # Core module exports
│
├── features/                # Feature modules (domain-driven)
│   ├── chat/                # Chat feature
│   │   ├── chat.store.js    # Chat state management
│   │   ├── chat.api.js      # Chat API calls
│   │   └── index.js         # Public API
│   ├── settings/            # Settings feature
│   │   ├── settings.store.js
│   │   ├── settings.api.js
│   │   └── index.js
│   ├── notifications/       # Notifications feature
│   │   ├── notifications.store.js
│   │   └── index.js
│   └── index.js             # Features exports
│
├── components/              # Reusable UI components
│   ├── chat/                # Chat-specific components
│   ├── messages/            # Message rendering
│   ├── notifications/       # Notification UI
│   └── settings/            # Settings UI components
│
├── css/                     # Stylesheets
├── i18n/                    # Internationalization
├── js/                      # Legacy/utility scripts
├── vendor/                  # Third-party libraries
│
├── config.js                # Configuration (re-exports from core)
├── index.html               # Main HTML entry
├── index.js                 # Application entry point
└── ARCHITECTURE.md          # This file
```

## Core Principles

### 1. Clean Layer Separation

```
┌─────────────────────────────────────────────────────────────┐
│                        UI Layer                              │
│  (index.html, components/, Alpine.js templates)              │
├─────────────────────────────────────────────────────────────┤
│                     Feature Layer                            │
│  (features/chat, features/settings, features/notifications)  │
├─────────────────────────────────────────────────────────────┤
│                      Core Layer                              │
│  (core/api, core/state, core/events)                        │
├─────────────────────────────────────────────────────────────┤
│                    Backend (Gateway)                         │
│  (FastAPI, Kafka, PostgreSQL)                               │
└─────────────────────────────────────────────────────────────┘
```

### 2. Feature Module Pattern

Each feature is self-contained with:
- **Store**: State management (reactive, persistent)
- **API**: Backend communication
- **Index**: Public API exports

```javascript
// Import a feature
import { chatStore, sendMessage } from './features/chat/index.js';

// Or use the features index
import { chat, settings, notifications } from './features/index.js';
```

### 3. Centralized API Endpoints

All API endpoints are defined in one place:

```javascript
// core/api/endpoints.js
export const ENDPOINTS = {
  SESSIONS: '/sessions',
  SESSION_MESSAGE: '/session/message',
  SETTINGS_SECTIONS: '/settings/sections',
  // ...
};

// Usage
import { ENDPOINTS, buildUrl } from './core/api/endpoints.js';
const url = buildUrl(ENDPOINTS.SESSIONS);
```

### 4. Reactive State with Alpine.js

Stores are created using the factory pattern:

```javascript
// Create a store
import { createStore } from './core/state/store.js';

const myStore = createStore('myFeature', {
  items: [],
  isLoading: false,
}, {
  persist: true,           // Enable localStorage persistence
  persistKeys: ['items'],  // Only persist specific keys
});

// Use in Alpine templates
<div x-data x-text="$store.myFeature.items.length"></div>
```

### 5. Type-Safe Events

Event types are constants to prevent typos:

```javascript
import { STREAM, CHAT, SETTINGS } from './core/events/types.js';
import { emit, on } from './core/index.js';

// Subscribe
on(STREAM.ONLINE, () => console.log('Connected'));

// Emit
emit(CHAT.MESSAGE_SENT, { message: 'Hello' });
```

## Data Flow

### Chat Message Flow

```
User Input → chat.api.sendMessage() → Gateway → Kafka
                                                  ↓
UI Update ← chat.store.addMessage() ← SSE Event ←┘
```

### Settings Flow

```
User Opens Modal → settings.store.openSettings()
                          ↓
                   settings.api.fetchSettings()
                          ↓
                   settings.store.setSections()
                          ↓
                   Alpine reactivity updates UI
```

## Backward Compatibility

The architecture maintains backward compatibility:

1. **config.js** re-exports from `core/api/endpoints.js`
2. **settingsModalProxy** is still available globally
3. **fetchApi** is exposed on `globalThis`
4. Legacy event bus functions work unchanged

## Migration Guide

### From Legacy Code

```javascript
// Before
import { API } from './config.js';
const response = await fetch(`${API.BASE}${API.SESSIONS}`);

// After
import { fetchApi } from './core/api/client.js';
import { ENDPOINTS, buildUrl } from './core/api/endpoints.js';
const response = await fetchApi(buildUrl(ENDPOINTS.SESSIONS));
```

### Using Feature Modules

```javascript
// Before (scattered logic)
const response = await fetch('/v1/settings/sections');
const data = await response.json();
// Manual state management...

// After (feature module)
import { fetchSettings, setSections } from './features/settings/index.js';
const { sections } = await fetchSettings();
setSections(sections);
```

## Testing

All tests should continue to pass after refactoring:

```bash
npx playwright test tests/playwright/settings-modal.spec.js
npx playwright test tests/playwright/ui-smoke.spec.js
```

## Performance Considerations

1. **Lazy Loading**: Feature modules can be dynamically imported
2. **Caching**: API client supports response caching
3. **Persistence**: Only necessary state is persisted to localStorage
4. **Event Cleanup**: Subscriptions return unsubscribe functions

## Security

1. **Auth Headers**: Automatically injected by API client
2. **CSRF**: Handled by same-origin credentials
3. **XSS**: Alpine.js escapes by default
4. **Secrets**: Never stored in frontend state
