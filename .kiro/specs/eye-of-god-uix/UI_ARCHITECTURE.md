# Eye of God UIX — Complete UI Layer Architecture

## Document Control

| Field | Value |
|-------|-------|
| **Document ID** | SA01-EOG-UI-ARCH-2025-12 |
| **Version** | 1.0 |
| **Date** | 2025-12-21 |
| **Status** | CANONICAL |
| **Scale Target** | MILLIONS of concurrent users |

---

## 1. Architecture Overview

### 1.1 Technology Stack

| Layer | Technology | Purpose | Scale |
|-------|------------|---------|-------|
| **Components** | Lit 3.x | Web Components, Shadow DOM | Millions |
| **State** | Lit Context + Signals | Reactive state management | Per-session |
| **Routing** | @vaadin/router | Client-side SPA routing | N/A |
| **API Client** | Fetch + WebSocket | Django Ninja communication | Pooled |
| **Build** | Vite 5.x | Fast builds, HMR, tree-shaking | N/A |
| **Testing** | Web Test Runner + Playwright | Component + E2E tests | N/A |
| **Theming** | AgentSkin (CSS Custom Properties) | 26+ design tokens | Runtime |

### 1.2 System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         BROWSER (Lit 3.x SPA)                                │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        EOG-APP (Root Shell)                          │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐  │   │
│  │  │ EOG-HEADER  │  │ EOG-SIDEBAR │  │ EOG-MAIN    │  │ EOG-TOAST  │  │   │
│  │  │ (Mode/User) │  │ (Navigation)│  │ (Router)    │  │ (Notifs)   │  │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         VIEWS (Pages)                                │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │   │
│  │  │ EOG-CHAT │ │EOG-MEMORY│ │EOG-TOOLS │ │EOG-ADMIN │ │EOG-VOICE │  │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         STORES (State)                               │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │   │
│  │  │AuthStore │ │ModeStore │ │ThemeStore│ │PermStore │ │VoiceStore│  │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────────┘
                                   │
                    HTTPS/WSS (Connection Pool)
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      DJANGO NINJA API GATEWAY (Port 8020)                    │
├─────────────────────────────────────────────────────────────────────────────┤
│  /api/v2/*  (REST)  │  /ws/v2/*  (WebSocket)  │  /openapi.json  (Schema)   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Component Hierarchy

### 2.1 Complete Component Tree

```
eog-app (Root Shell)
├── eog-providers (Context Providers Wrapper)
│   ├── eog-auth-provider
│   ├── eog-mode-provider
│   ├── eog-theme-provider
│   ├── eog-permission-provider
│   └── eog-voice-provider
│
├── eog-header
│   ├── eog-logo
│   ├── eog-mode-selector
│   ├── eog-search-bar
│   ├── eog-notifications
│   └── eog-user-menu
│       ├── eog-avatar
│       └── eog-dropdown
│
├── eog-sidebar
│   ├── eog-nav-section (Chat)
│   ├── eog-nav-section (Memory)
│   ├── eog-nav-section (Tools)
│   ├── eog-nav-section (Cognitive)
│   ├── eog-nav-section (Settings)
│   └── eog-sidebar-footer
│
├── eog-main (Router Outlet)
│   ├── eog-chat-view
│   │   ├── eog-conversation-list
│   │   ├── eog-chat-panel
│   │   │   ├── eog-message-list
│   │   │   │   └── eog-message (repeated)
│   │   │   ├── eog-chat-input
│   │   │   │   ├── eog-textarea
│   │   │   │   ├── eog-voice-button
│   │   │   │   └── eog-send-button
│   │   │   └── eog-typing-indicator
│   │   └── eog-context-panel
│   │
│   ├── eog-memory-view
│   │   ├── eog-memory-search
│   │   ├── eog-memory-filters
│   │   ├── eog-memory-grid
│   │   │   └── eog-memory-card (repeated)
│   │   └── eog-memory-detail
│   │
│   ├── eog-tools-view
│   │   ├── eog-tool-catalog
│   │   │   └── eog-tool-card (repeated)
│   │   └── eog-tool-executor
│   │
│   ├── eog-cognitive-view
│   │   ├── eog-neuromod-panel
│   │   │   ├── eog-neuromod-gauge (dopamine)
│   │   │   ├── eog-neuromod-gauge (serotonin)
│   │   │   ├── eog-neuromod-gauge (noradrenaline)
│   │   │   └── eog-neuromod-gauge (acetylcholine)
│   │   ├── eog-adaptation-panel
│   │   └── eog-sleep-panel
│   │
│   ├── eog-settings-view
│   │   ├── eog-settings-tabs
│   │   ├── eog-settings-agent
│   │   ├── eog-settings-external
│   │   ├── eog-settings-connectivity
│   │   │   └── eog-voice-settings (NEW)
│   │   └── eog-settings-system
│   │
│   ├── eog-themes-view
│   │   ├── eog-theme-gallery
│   │   │   └── eog-theme-card (repeated)
│   │   ├── eog-theme-preview
│   │   └── eog-theme-upload
│   │
│   ├── eog-admin-view
│   │   ├── eog-user-management
│   │   ├── eog-tenant-management
│   │   └── eog-system-health
│   │
│   └── eog-audit-view
│       ├── eog-audit-filters
│       └── eog-audit-table
│
├── eog-voice-overlay (Floating Voice UI)
│   ├── eog-voice-visualizer
│   ├── eog-voice-transcript
│   └── eog-voice-controls
│
└── eog-toast-container
    └── eog-toast (repeated)
```

---

## 2. Component Catalog

### 2.1 Primitive Components (Design System)

| Component | Tag | Purpose | Props |
|-----------|-----|---------|-------|
| Button | `<eog-button>` | Primary action trigger | `variant`, `disabled`, `loading`, `size` |
| Input | `<eog-input>` | Text input field | `type`, `placeholder`, `value`, `error`, `disabled` |
| Select | `<eog-select>` | Dropdown selection | `options`, `value`, `placeholder`, `disabled` |
| Toggle | `<eog-toggle>` | Boolean switch | `checked`, `disabled`, `label` |
| Slider | `<eog-slider>` | Range input | `min`, `max`, `value`, `step`, `label` |
| Modal | `<eog-modal>` | Dialog overlay | `open`, `title`, `closable`, `size` |
| Toast | `<eog-toast>` | Notification popup | `type`, `message`, `duration`, `dismissable` |
| Card | `<eog-card>` | Content container | `variant`, `padding`, `elevation` |
| Tabs | `<eog-tabs>` | Tab navigation | `tabs`, `active`, `orientation` |
| Spinner | `<eog-spinner>` | Loading indicator | `size`, `color` |
| Badge | `<eog-badge>` | Status indicator | `variant`, `count`, `dot` |
| Avatar | `<eog-avatar>` | User/agent image | `src`, `name`, `size`, `status` |
| Icon | `<eog-icon>` | SVG icon wrapper | `name`, `size`, `color` |
| Tooltip | `<eog-tooltip>` | Hover information | `content`, `position`, `delay` |
| Progress | `<eog-progress>` | Progress bar | `value`, `max`, `variant`, `label` |

### 2.2 Layout Components

| Component | Tag | Purpose | Props |
|-----------|-----|---------|-------|
| App Shell | `<eog-app>` | Root application | `theme`, `mode`, `user` |
| Header | `<eog-header>` | Top navigation bar | `title`, `user`, `mode` |
| Sidebar | `<eog-sidebar>` | Side navigation | `collapsed`, `items`, `active` |
| Main | `<eog-main>` | Content area | `padding`, `scroll` |
| Panel | `<eog-panel>` | Collapsible section | `title`, `collapsed`, `icon` |
| Split | `<eog-split>` | Resizable split view | `direction`, `sizes`, `min` |
| Grid | `<eog-grid>` | CSS Grid wrapper | `columns`, `gap`, `responsive` |
| Stack | `<eog-stack>` | Flex stack layout | `direction`, `gap`, `align` |

### 2.3 View Components (Pages)

| Component | Tag | Route | Permission |
|-----------|-----|-------|------------|
| Chat | `<eog-chat>` | `/chat` | `tenant->use` |
| Memory | `<eog-memory>` | `/memory` | `tenant->view` |
| Tools | `<eog-tools>` | `/tools` | `tenant->view` |
| Settings | `<eog-settings>` | `/settings` | `tenant->view` |
| Themes | `<eog-themes>` | `/themes` | `tenant->view` |
| Voice | `<eog-voice>` | `/voice` | `tenant->use` |
| Cognitive | `<eog-cognitive>` | `/cognitive` | `tenant->train` |
| Admin | `<eog-admin>` | `/admin` | `tenant->administrate` |
| Audit | `<eog-audit>` | `/audit` | `tenant->administrate` |
| Scheduler | `<eog-scheduler>` | `/scheduler` | `tenant->use` |

### 2.2 Component Categories

| Category | Components | Purpose |
|----------|------------|---------|
| **Shell** | eog-app, eog-header, eog-sidebar, eog-main | Application structure |
| **Providers** | eog-*-provider | Context/state injection |
| **Views** | eog-*-view | Page-level containers |
| **Panels** | eog-*-panel | Feature sections |
| **Forms** | eog-input, eog-select, eog-toggle, eog-slider | User input |
| **Display** | eog-card, eog-table, eog-list, eog-badge | Data presentation |
| **Feedback** | eog-toast, eog-modal, eog-spinner, eog-skeleton | User feedback |
| **Voice** | eog-voice-*, eog-visualizer | Voice interaction |

### 2.3 Lazy Loading Strategy

```typescript
// Route-based code splitting
const routes = [
  { path: '/', component: 'eog-chat-view' },
  { path: '/memory', component: 'eog-memory-view', action: () => import('./views/eog-memory-view.js') },
  { path: '/tools', component: 'eog-tools-view', action: () => import('./views/eog-tools-view.js') },
  { path: '/cognitive', component: 'eog-cognitive-view', action: () => import('./views/eog-cognitive-view.js') },
  { path: '/settings', component: 'eog-settings-view', action: () => import('./views/eog-settings-view.js') },
  { path: '/themes', component: 'eog-themes-view', action: () => import('./views/eog-themes-view.js') },
  { path: '/admin', component: 'eog-admin-view', action: () => import('./views/eog-admin-view.js') },
  { path: '/audit', component: 'eog-audit-view', action: () => import('./views/eog-audit-view.js') },
];
```

---

## 3. State Management

### 3.1 Store Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    STORE LAYER (Lit Context)                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ AuthStore   │  │ ModeStore   │  │ ThemeStore  │             │
│  │ - user      │  │ - current   │  │ - active    │             │
│  │ - token     │  │ - available │  │ - list      │             │
│  │ - tenant    │  │ - loading   │  │ - preview   │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ PermStore   │  │ VoiceStore  │  │ SettingsStore│            │
│  │ - cache     │  │ - provider  │  │ - agent     │             │
│  │ - roles     │  │ - state     │  │ - external  │             │
│  │ - loading   │  │ - config    │  │ - system    │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ ChatStore   │  │ MemoryStore │  │ CognitiveStore│           │
│  │ - messages  │  │ - items     │  │ - neuromod  │             │
│  │ - sessions  │  │ - filters   │  │ - adaptation│             │
│  │ - streaming │  │ - selected  │  │ - sleep     │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Store Implementations

#### AuthStore

```typescript
// File: src/stores/auth-store.ts
import { createContext } from '@lit/context';
import { signal, computed } from '@lit-labs/signals';

export interface User {
  id: string;
  email: string;
  name: string;
  avatar?: string;
  roles: string[];
  tenant_id: string;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  tenant_id: string | null;
  loading: boolean;
  error: string | null;
}

export const authContext = createContext<AuthState>('auth-state');

class AuthStore {
  private _user = signal<User | null>(null);
  private _token = signal<string | null>(null);
  private _loading = signal(false);
  private _error = signal<string | null>(null);

  readonly isAuthenticated = computed(() => this._user.get() !== null);
  readonly tenantId = computed(() => this._user.get()?.tenant_id ?? null);

  get state(): AuthState {
    return {
      user: this._user.get(),
      token: this._token.get(),
      tenant_id: this.tenantId.get(),
      loading: this._loading.get(),
      error: this._error.get(),
    };
  }

  async login(email: string, password: string): Promise<void> {
    this._loading.set(true);
    this._error.set(null);
    try {
      const response = await fetch('/api/v2/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      if (!response.ok) throw new Error('Login failed');
      const data = await response.json();
      this._user.set(data.user);
      this._token.set(data.token);
      localStorage.setItem('eog_token', data.token);
    } catch (e) {
      this._error.set(String(e));
    } finally {
      this._loading.set(false);
    }
  }

  logout(): void {
    this._user.set(null);
    this._token.set(null);
    localStorage.removeItem('eog_token');
  }

  async restoreSession(): Promise<void> {
    const token = localStorage.getItem('eog_token');
    if (!token) return;
    this._loading.set(true);
    try {
      const response = await fetch('/api/v2/auth/me', {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) throw new Error('Session expired');
      const data = await response.json();
      this._user.set(data.user);
      this._token.set(token);
    } catch {
      localStorage.removeItem('eog_token');
    } finally {
      this._loading.set(false);
    }
  }
}

export const authStore = new AuthStore();
```

### 2.4 Feature Components

| Component | Tag | Purpose | Props |
|-----------|-----|---------|-------|
| Chat Message | `<eog-chat-message>` | Single message | `role`, `content`, `timestamp`, `status` |
| Chat Input | `<eog-chat-input>` | Message composer | `placeholder`, `disabled`, `voice` |
| Memory Card | `<eog-memory-card>` | Memory item display | `memory`, `actions` |
| Memory Search | `<eog-memory-search>` | Memory query | `query`, `filters` |
| Tool Card | `<eog-tool-card>` | Tool display | `tool`, `status`, `execute` |
| Tool Executor | `<eog-tool-executor>` | Tool execution UI | `tool`, `params`, `result` |
| Settings Form | `<eog-settings-form>` | Settings editor | `schema`, `values`, `tab` |
| Theme Preview | `<eog-theme-preview>` | Theme comparison | `theme`, `split` |
| Theme Editor | `<eog-theme-editor>` | Theme customization | `theme`, `variables` |
| Voice Indicator | `<eog-voice-indicator>` | Voice status | `state`, `level`, `provider` |
| Voice Controls | `<eog-voice-controls>` | Voice buttons | `recording`, `playing`, `muted` |
| Neuro Panel | `<eog-neuro-panel>` | Neuromodulator display | `dopamine`, `serotonin`, `noradrenaline` |
| Adaptation Panel | `<eog-adaptation-panel>` | Adaptation weights | `weights`, `history` |
| User Menu | `<eog-user-menu>` | User dropdown | `user`, `mode`, `logout` |
| Mode Selector | `<eog-mode-selector>` | Mode switcher | `current`, `available` |

---

## 3. State Management

### 3.1 Store Architecture (Lit Context)

```
┌─────────────────────────────────────────────────────────────────┐
│                     STORE HIERARCHY                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    ROOT PROVIDER                         │   │
│  │  <eog-store-provider>                                    │   │
│  │    ├── AuthStore (token, user, tenant)                   │   │
│  │    ├── ModeStore (current, available, loading)           │   │
│  │    ├── ThemeStore (active, themes, preview)              │   │
│  │    ├── PermStore (permissions, cache)                    │   │
│  │    ├── VoiceStore (provider, state, config)              │   │
│  │    ├── SettingsStore (tabs, values, dirty)               │   │
│  │    └── ChatStore (messages, streaming, session)          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Store Definitions

#### AuthStore
```typescript
interface AuthState {
  token: string | null;
  user: User | null;
  tenant: Tenant | null;
  loading: boolean;
  error: string | null;
}

interface AuthActions {
  login(credentials: Credentials): Promise<void>;
  logout(): Promise<void>;
  refresh(): Promise<void>;
  setTenant(tenantId: string): Promise<void>;
}
```

#### ModeStore
```typescript
interface ModeState {
  current: AgentMode;  // 'STD' | 'TRN' | 'ADM' | 'DEV' | 'RO' | 'DGR'
  available: AgentMode[];
  loading: boolean;
  error: string | null;
}

interface ModeActions {
  setMode(mode: AgentMode): Promise<void>;
  refresh(): Promise<void>;
}
```

#### ThemeStore
```typescript
interface ThemeState {
  active: Theme;
  themes: Theme[];
  preview: Theme | null;
  loading: boolean;
}

interface ThemeActions {
  apply(themeId: string): Promise<void>;
  preview(theme: Theme): void;
  upload(file: File): Promise<Theme>;
  reset(): void;
}
```

#### VoiceStore

```typescript
// File: src/stores/voice-store.ts
import { createContext } from '@lit/context';
import { signal, computed } from '@lit-labs/signals';

export type VoiceProvider = 'disabled' | 'local' | 'agentvoicebox';
export type VoiceState = 'idle' | 'listening' | 'processing' | 'speaking' | 'error';

export interface VoiceConfig {
  provider: VoiceProvider;
  local: {
    stt_engine: 'whisper' | 'faster-whisper';
    stt_model_size: 'tiny' | 'base' | 'small' | 'medium' | 'large';
    tts_engine: 'kokoro' | 'browser';
    tts_voice: string;
    tts_speed: number;
    vad_threshold: number;
    language: string;
  };
  agentvoicebox: {
    base_url: string;
    ws_url: string;
    api_token: string;
    model: string;
    voice: string;
    turn_detection: boolean;
  };
  audio: {
    input_device: number;
    output_device: number;
    sample_rate: number;
  };
}

export interface VoiceStoreState {
  enabled: boolean;
  provider: VoiceProvider;
  state: VoiceState;
  config: VoiceConfig;
  transcript: string;
  error: string | null;
}

export const voiceContext = createContext<VoiceStoreState>('voice-state');

class VoiceStore {
  private _enabled = signal(false);
  private _provider = signal<VoiceProvider>('disabled');
  private _state = signal<VoiceState>('idle');
  private _transcript = signal('');
  private _error = signal<string | null>(null);
  private _config = signal<VoiceConfig>(this.defaultConfig());

  readonly isActive = computed(() => 
    this._enabled.get() && this._state.get() !== 'idle' && this._state.get() !== 'error'
  );

  readonly canUseSpeechOnSpeech = computed(() => 
    this._provider.get() === 'agentvoicebox'
  );

  get state(): VoiceStoreState {
    return {
      enabled: this._enabled.get(),
      provider: this._provider.get(),
      state: this._state.get(),
      config: this._config.get(),
      transcript: this._transcript.get(),
      error: this._error.get(),
    };
  }

  private defaultConfig(): VoiceConfig {
    return {
      provider: 'disabled',
      local: {
        stt_engine: 'whisper',
        stt_model_size: 'base',
        tts_engine: 'kokoro',
        tts_voice: 'am_onyx',
        tts_speed: 1.0,
        vad_threshold: 0.5,
        language: 'en-US',
      },
      agentvoicebox: {
        base_url: '',
        ws_url: '',
        api_token: '',
        model: 'ovos-voice-1',
        voice: 'default',
        turn_detection: true,
      },
      audio: {
        input_device: 0,
        output_device: 0,
        sample_rate: 24000,
      },
    };
  }

  setProvider(provider: VoiceProvider): void {
    this._provider.set(provider);
    this._enabled.set(provider !== 'disabled');
  }

  setState(state: VoiceState): void {
    this._state.set(state);
  }

  setTranscript(text: string): void {
    this._transcript.set(text);
  }

  updateConfig(partial: Partial<VoiceConfig>): void {
    this._config.set({ ...this._config.get(), ...partial });
  }

  setError(error: string | null): void {
    this._error.set(error);
    if (error) this._state.set('error');
  }
}

export const voiceStore = new VoiceStore();
```

#### VoiceStore
```typescript
interface VoiceState {
  enabled: boolean;
  provider: 'local' | 'agentvoicebox' | 'disabled';
  state: 'idle' | 'listening' | 'processing' | 'speaking' | 'error';
  config: VoiceConfig;
  audioLevel: number;
  error: string | null;
}

interface VoiceActions {
  setProvider(provider: string): Promise<void>;
  startListening(): Promise<void>;
  stopListening(): void;
  speak(text: string): Promise<void>;
  cancel(): void;
  testConnection(): Promise<boolean>;
}
```

#### PermStore
```typescript
interface PermState {
  permissions: Map<string, boolean>;
  loading: boolean;
  cacheExpiry: number;
}

interface PermActions {
  check(resource: string, action: string): Promise<boolean>;
  refresh(): Promise<void>;
  invalidate(): void;
}
```

---

## 4. Service Layer

### 4.1 API Client Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     SERVICE LAYER                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    ApiClient (Base)                      │   │
│  │  - baseUrl: /api/v2                                      │   │
│  │  - timeout: 30000ms                                      │   │
│  │  - retries: 3                                            │   │
│  │  - interceptors: [auth, tenant, error]                   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                           │                                      │
│           ┌───────────────┼───────────────┐                     │
│           ▼               ▼               ▼                     │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐               │
│  │ AuthService │ │SettingsService│ │ VoiceService │             │
│  │ /auth/*     │ │ /settings/* │ │ /voice/*    │               │
│  └─────────────┘ └─────────────┘ └─────────────┘               │
│           │               │               │                     │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐               │
│  │ ThemeService│ │ MemoryService│ │ ToolService │               │
│  │ /themes/*  │ │ /memory/*   │ │ /tools/*    │               │
│  └─────────────┘ └─────────────┘ └─────────────┘               │
│           │               │               │                     │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐               │
│  │ CognitiveService│ │ AdminService│ │ PermService │            │
│  │ /cognitive/*│ │ /admin/*    │ │ /permissions/*│             │
│  └─────────────┘ └─────────────┘ └─────────────┘               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 WebSocket Client

```typescript
interface WSClientConfig {
  url: string;           // /ws/v2/events
  reconnect: boolean;    // true
  maxRetries: number;    // 5
  backoff: number;       // 1000ms (exponential)
  heartbeat: number;     // 20000ms
}

interface WSClient {
  connect(): Promise<void>;
  disconnect(): void;
  send(event: WSEvent): void;
  subscribe(type: string, handler: EventHandler): Unsubscribe;
  onReconnect(handler: () => void): void;
}

// Event Types
type WSEventType = 
  | 'mode.changed'
  | 'settings.changed'
  | 'theme.changed'
  | 'voice.started'
  | 'voice.speech_started'
  | 'voice.speech_stopped'
  | 'voice.transcription'
  | 'voice.response_started'
  | 'voice.audio_delta'
  | 'voice.response_done'
  | 'voice.error'
  | 'chat.message'
  | 'chat.typing'
  | 'chat.done'
  | 'system.keepalive';
```

#### ThemeStore

```typescript
// File: src/stores/theme-store.ts
import { createContext } from '@lit/context';
import { signal } from '@lit-labs/signals';

export interface Theme {
  id: string;
  name: string;
  version: string;
  author: string;
  variables: Record<string, string>;
}

export interface ThemeState {
  active: Theme | null;
  list: Theme[];
  preview: Theme | null;
  loading: boolean;
}

export const themeContext = createContext<ThemeState>('theme-state');

class ThemeStore {
  private _active = signal<Theme | null>(null);
  private _list = signal<Theme[]>([]);
  private _preview = signal<Theme | null>(null);
  private _loading = signal(false);

  get state(): ThemeState {
    return {
      active: this._active.get(),
      list: this._list.get(),
      preview: this._preview.get(),
      loading: this._loading.get(),
    };
  }

  applyTheme(theme: Theme): void {
    const root = document.documentElement;
    Object.entries(theme.variables).forEach(([key, value]) => {
      root.style.setProperty(`--eog-${key}`, value);
    });
    this._active.set(theme);
    localStorage.setItem('eog_theme', theme.id);
  }

  previewTheme(theme: Theme | null): void {
    this._preview.set(theme);
    if (theme) {
      const root = document.documentElement;
      Object.entries(theme.variables).forEach(([key, value]) => {
        root.style.setProperty(`--eog-${key}`, value);
      });
    } else if (this._active.get()) {
      this.applyTheme(this._active.get()!);
    }
  }

  async loadThemes(): Promise<void> {
    this._loading.set(true);
    try {
      const response = await fetch('/api/v2/themes');
      const data = await response.json();
      this._list.set(data.themes);
    } finally {
      this._loading.set(false);
    }
  }

  async restoreTheme(): Promise<void> {
    const themeId = localStorage.getItem('eog_theme');
    if (!themeId) return;
    await this.loadThemes();
    const theme = this._list.get().find(t => t.id === themeId);
    if (theme) this.applyTheme(theme);
  }
}

export const themeStore = new ThemeStore();
```

---

## 4. Service Layer

### 4.1 Service Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      SERVICE LAYER                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    ApiClient (Base)                      │   │
│  │  - request<T>(method, path, options): Promise<T>        │   │
│  │  - setToken(token): void                                │   │
│  │  - retry logic, timeout, error handling                 │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                   │
│         ┌────────────────────┼────────────────────┐             │
│         ▼                    ▼                    ▼             │
│  ┌─────────────┐      ┌─────────────┐      ┌─────────────┐     │
│  │ AuthService │      │ ChatService │      │ MemoryService│    │
│  │ - login()   │      │ - send()    │      │ - recall()  │     │
│  │ - logout()  │      │ - stream()  │      │ - remember()│     │
│  │ - refresh() │      │ - history() │      │ - delete()  │     │
│  └─────────────┘      └─────────────┘      └─────────────┘     │
│                                                                  │
│  ┌─────────────┐      ┌─────────────┐      ┌─────────────┐     │
│  │ ThemeService│      │ SettingsService│   │ VoiceService│     │
│  │ - list()    │      │ - get()     │      │ - connect() │     │
│  │ - upload()  │      │ - update()  │      │ - disconnect()│   │
│  │ - delete()  │      │ - validate()│      │ - send()    │     │
│  └─────────────┘      └─────────────┘      └─────────────┘     │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                  WebSocketClient                         │   │
│  │  - connect(url): void                                   │   │
│  │  - disconnect(): void                                   │   │
│  │  - send(event): void                                    │   │
│  │  - on(event, handler): void                             │   │
│  │  - reconnect with exponential backoff                   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. Routing Configuration

### 5.1 Route Definitions

```typescript
const routes: Route[] = [
  { path: '/', redirect: '/chat' },
  { path: '/chat', component: 'eog-chat', permission: 'tenant->use' },
  { path: '/chat/:sessionId', component: 'eog-chat', permission: 'tenant->use' },
  { path: '/memory', component: 'eog-memory', permission: 'tenant->view' },
  { path: '/memory/:coordinate', component: 'eog-memory', permission: 'tenant->view' },
  { path: '/tools', component: 'eog-tools', permission: 'tenant->view' },
  { path: '/tools/:toolId', component: 'eog-tool-executor', permission: 'tenant->use' },
  { path: '/settings', component: 'eog-settings', permission: 'tenant->view' },
  { path: '/settings/:tab', component: 'eog-settings', permission: 'tenant->view' },
  { path: '/themes', component: 'eog-themes', permission: 'tenant->view' },
  { path: '/themes/:themeId', component: 'eog-theme-editor', permission: 'tenant->administrate' },
  { path: '/voice', component: 'eog-voice', permission: 'tenant->use' },
  { path: '/cognitive', component: 'eog-cognitive', permission: 'tenant->train' },
  { path: '/admin', component: 'eog-admin', permission: 'tenant->administrate' },
  { path: '/admin/users', component: 'eog-admin-users', permission: 'tenant->administrate' },
  { path: '/admin/tenants', component: 'eog-admin-tenants', permission: 'tenant->manage' },
  { path: '/audit', component: 'eog-audit', permission: 'tenant->administrate' },
  { path: '/scheduler', component: 'eog-scheduler', permission: 'tenant->use' },
  { path: '/login', component: 'eog-login', public: true },
  { path: '/logout', component: 'eog-logout', public: true },
  { path: '(.*)', component: 'eog-not-found', public: true },
];
```

### 5.2 Route Guards

```typescript
async function routeGuard(context: RouterContext, commands: Commands): Promise<void> {
  const { route, params } = context;
  
  // Public routes bypass auth
  if (route.public) return;
  
  // Check authentication
  const authStore = getStore('auth');
  if (!authStore.token) {
    return commands.redirect('/login');
  }
  
  // Check permission
  if (route.permission) {
    const permStore = getStore('perm');
    const allowed = await permStore.check(route.permission);
    if (!allowed) {
      return commands.redirect('/unauthorized');
    }
  }
}
```

---

## 6. AgentSkin Theme System

### 6.1 CSS Custom Properties (26 Required)

```css
:root {
  /* Background Colors */
  --eog-bg-void: #0f172a;
  --eog-bg-surface: rgba(30, 41, 59, 0.85);
  --eog-bg-elevated: rgba(51, 65, 85, 0.9);
  
  /* Glass Effects */
  --eog-glass-surface: rgba(30, 41, 59, 0.85);
  --eog-glass-border: rgba(255, 255, 255, 0.05);
  --eog-glass-blur: blur(20px);
  
  /* Text Colors */
  --eog-text-main: #e2e8f0;
  --eog-text-dim: #64748b;
  --eog-text-accent: #3b82f6;
  
  /* Accent Colors */
  --eog-accent-primary: #3b82f6;
  --eog-accent-secondary: #8b5cf6;
  --eog-accent-success: #22c55e;
  --eog-accent-warning: #f59e0b;
  --eog-accent-danger: #ef4444;
  
  /* Shadows */
  --eog-shadow-soft: 0 10px 40px -10px rgba(0, 0, 0, 0.5);
  --eog-shadow-glow: 0 0 20px rgba(59, 130, 246, 0.3);
  
  /* Border Radius */
  --eog-radius-sm: 4px;
  --eog-radius-md: 8px;
  --eog-radius-lg: 16px;
  --eog-radius-full: 9999px;
  
  /* Spacing */
  --eog-spacing-xs: 4px;
  --eog-spacing-sm: 8px;
  --eog-spacing-md: 16px;
  --eog-spacing-lg: 24px;
  --eog-spacing-xl: 32px;
  
  /* Typography */
  --eog-font-sans: 'Space Grotesk', system-ui, sans-serif;
  --eog-font-mono: 'JetBrains Mono', monospace;
  --eog-text-xs: 10px;
  --eog-text-sm: 12px;
  --eog-text-base: 14px;
  --eog-text-lg: 16px;
  --eog-text-xl: 20px;
}
```

### 4.2 WebSocket Client Implementation

```typescript
// File: src/services/websocket-client.ts

export type WSEventType = 
  | 'mode.changed'
  | 'settings.changed'
  | 'theme.changed'
  | 'voice.started'
  | 'voice.speech_started'
  | 'voice.speech_stopped'
  | 'voice.transcription'
  | 'voice.response_started'
  | 'voice.audio_delta'
  | 'voice.response_done'
  | 'voice.error'
  | 'assistant.started'
  | 'assistant.delta'
  | 'assistant.final'
  | 'system.keepalive';

export interface WSEvent<T = unknown> {
  type: WSEventType;
  data: T;
  timestamp: number;
}

type EventHandler<T = unknown> = (event: WSEvent<T>) => void;

export class WebSocketClient {
  private ws: WebSocket | null = null;
  private handlers = new Map<WSEventType, Set<EventHandler>>();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 10;
  private reconnectDelay = 1000;
  private heartbeatInterval: number | null = null;
  private url: string = '';
  private token: string = '';

  connect(url: string, token: string): void {
    this.url = url;
    this.token = token;
    this.doConnect();
  }

  private doConnect(): void {
    const wsUrl = `${this.url}?token=${encodeURIComponent(this.token)}`;
    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      this.reconnectAttempts = 0;
      this.startHeartbeat();
      this.emit('system.keepalive', { connected: true });
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as WSEvent;
        this.dispatch(data.type, data);
      } catch (e) {
        console.error('Failed to parse WebSocket message:', e);
      }
    };

    this.ws.onclose = () => {
      this.stopHeartbeat();
      this.scheduleReconnect();
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }

  disconnect(): void {
    this.stopHeartbeat();
    this.reconnectAttempts = this.maxReconnectAttempts; // Prevent reconnect
    this.ws?.close();
    this.ws = null;
  }

  send<T>(type: WSEventType, data: T): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type, data, timestamp: Date.now() }));
    }
  }

  on<T>(type: WSEventType, handler: EventHandler<T>): () => void {
    if (!this.handlers.has(type)) {
      this.handlers.set(type, new Set());
    }
    this.handlers.get(type)!.add(handler as EventHandler);
    return () => this.handlers.get(type)?.delete(handler as EventHandler);
  }

  private dispatch(type: WSEventType, event: WSEvent): void {
    this.handlers.get(type)?.forEach(handler => handler(event));
  }

  private emit<T>(type: WSEventType, data: T): void {
    this.dispatch(type, { type, data, timestamp: Date.now() });
  }

  private startHeartbeat(): void {
    this.heartbeatInterval = window.setInterval(() => {
      this.send('system.keepalive', { ping: true });
    }, 20000);
  }

  private stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) return;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts);
    this.reconnectAttempts++;
    setTimeout(() => this.doConnect(), delay);
  }
}

export const wsClient = new WebSocketClient();
```

### 6.2 Theme JSON Schema

```json
{
  "$schema": "https://somaagent.io/schemas/agentskin-v1.json",
  "type": "object",
  "required": ["name", "version", "variables"],
  "properties": {
    "name": { "type": "string", "minLength": 1, "maxLength": 64 },
    "version": { "type": "string", "pattern": "^\\d+\\.\\d+\\.\\d+$" },
    "author": { "type": "string", "maxLength": 128 },
    "description": { "type": "string", "maxLength": 512 },
    "category": { 
      "type": "string", 
      "enum": ["Professional", "Creative", "Developer", "Gaming", "Accessibility"] 
    },
    "tags": { "type": "array", "items": { "type": "string" }, "maxItems": 10 },
    "variables": {
      "type": "object",
      "required": [
        "bg-void", "glass-surface", "glass-border", "text-main", "text-dim",
        "accent-primary", "accent-secondary", "accent-success", "accent-warning", "accent-danger",
        "shadow-soft", "radius-sm", "radius-md", "radius-lg", "radius-full",
        "spacing-xs", "spacing-sm", "spacing-md", "spacing-lg", "spacing-xl",
        "font-sans", "font-mono", "text-xs", "text-sm", "text-base", "text-lg"
      ],
      "additionalProperties": { "type": "string" }
    }
  }
}
```

### 6.3 Theme Application Logic

```typescript
class ThemeManager {
  private root: HTMLElement;
  private active: Theme | null = null;
  
  constructor() {
    this.root = document.documentElement;
  }
  
  apply(theme: Theme): void {
    // Validate theme
    this.validate(theme);
    
    // Apply CSS variables
    for (const [key, value] of Object.entries(theme.variables)) {
      this.root.style.setProperty(`--eog-${key}`, value);
    }
    
    // Store in localStorage
    localStorage.setItem('eog-theme', JSON.stringify(theme));
    
    // Emit event
    this.root.dispatchEvent(new CustomEvent('theme-changed', { detail: theme }));
    
    this.active = theme;
  }
  
  validate(theme: Theme): void {
    // Check for url() in values (XSS prevention)
    for (const value of Object.values(theme.variables)) {
      if (value.includes('url(')) {
        throw new ThemeValidationError('url() not allowed in theme values');
      }
    }
    
    // Validate contrast ratios (WCAG AA)
    const contrast = this.calculateContrast(
      theme.variables['bg-void'],
      theme.variables['text-main']
    );
    if (contrast < 4.5) {
      throw new ThemeValidationError('Insufficient contrast ratio (min 4.5:1)');
    }
  }
}
```

---

## 7. Voice Integration

### 7.1 Voice Component Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    VOICE SUBSYSTEM                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                  <eog-voice-controls>                    │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐    │   │
│  │  │ Record  │  │  Stop   │  │  Mute   │  │ Settings│    │   │
│  │  │ Button  │  │ Button  │  │ Toggle  │  │  Link   │    │   │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                           │                                      │
│                           ▼                                      │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                  <eog-voice-indicator>                   │   │
│  │  ┌─────────────────────────────────────────────────┐    │   │
│  │  │  State: idle | listening | processing | speaking │    │   │
│  │  │  Level: ████████░░░░░░░░ (audio level meter)     │    │   │
│  │  │  Provider: Local | AgentVoiceBox                 │    │   │
│  │  └─────────────────────────────────────────────────┘    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                           │                                      │
│                           ▼                                      │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    VoiceService                          │   │
│  │  ┌─────────────────┐  ┌─────────────────────────────┐   │   │
│  │  │ LocalProvider   │  │ AgentVoiceBoxProvider       │   │   │
│  │  │ - Whisper STT   │  │ - WebSocket /v1/realtime    │   │   │
│  │  │ - Kokoro TTS    │  │ - Bidirectional audio       │   │   │
│  │  │ - WebRTC VAD    │  │ - Turn detection            │   │   │
│  │  └─────────────────┘  └─────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 4.3 Voice Service Implementation

```typescript
// File: src/services/voice-service.ts

import { voiceStore, VoiceProvider } from '../stores/voice-store';
import { wsClient } from './websocket-client';

export class VoiceService {
  private mediaStream: MediaStream | null = null;
  private audioContext: AudioContext | null = null;
  private processor: ScriptProcessorNode | null = null;
  private agentVoiceBoxWs: WebSocket | null = null;

  async initialize(provider: VoiceProvider): Promise<void> {
    if (provider === 'disabled') return;

    // Request microphone access
    this.mediaStream = await navigator.mediaDevices.getUserMedia({
      audio: {
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
        sampleRate: voiceStore.state.config.audio.sample_rate,
      },
    });

    this.audioContext = new AudioContext({
      sampleRate: voiceStore.state.config.audio.sample_rate,
    });

    if (provider === 'agentvoicebox') {
      await this.connectAgentVoiceBox();
    }

    voiceStore.setState('idle');
  }

  private async connectAgentVoiceBox(): Promise<void> {
    const config = voiceStore.state.config.agentvoicebox;
    if (!config.ws_url) throw new Error('AgentVoiceBox WebSocket URL not configured');

    return new Promise((resolve, reject) => {
      this.agentVoiceBoxWs = new WebSocket(config.ws_url);

      this.agentVoiceBoxWs.onopen = () => {
        // Send session configuration
        this.agentVoiceBoxWs!.send(JSON.stringify({
          type: 'session.update',
          session: {
            voice: config.voice,
            model: config.model,
            turn_detection: config.turn_detection ? { type: 'server_vad' } : null,
            input_audio_format: 'pcm16',
            output_audio_format: 'pcm16',
          },
        }));
        resolve();
      };

      this.agentVoiceBoxWs.onmessage = (event) => {
        const data = JSON.parse(event.data);
        this.handleAgentVoiceBoxEvent(data);
      };

      this.agentVoiceBoxWs.onerror = (error) => {
        voiceStore.setError('AgentVoiceBox connection failed');
        reject(error);
      };

      this.agentVoiceBoxWs.onclose = () => {
        voiceStore.setState('idle');
      };
    });
  }

  private handleAgentVoiceBoxEvent(event: any): void {
    switch (event.type) {
      case 'session.created':
      case 'session.updated':
        voiceStore.setState('idle');
        break;
      case 'input_audio_buffer.speech_started':
        voiceStore.setState('listening');
        wsClient.send('voice.speech_started', {});
        break;
      case 'input_audio_buffer.speech_stopped':
        voiceStore.setState('processing');
        wsClient.send('voice.speech_stopped', {});
        break;
      case 'conversation.item.created':
        if (event.item?.content?.[0]?.transcript) {
          voiceStore.setTranscript(event.item.content[0].transcript);
          wsClient.send('voice.transcription', { text: event.item.content[0].transcript });
        }
        break;
      case 'response.audio.delta':
        voiceStore.setState('speaking');
        this.playAudioDelta(event.delta);
        wsClient.send('voice.audio_delta', { delta: event.delta });
        break;
      case 'response.done':
        voiceStore.setState('idle');
        wsClient.send('voice.response_done', {});
        break;
      case 'error':
        voiceStore.setError(event.error?.message || 'Unknown error');
        wsClient.send('voice.error', { error: event.error });
        break;
    }
  }

  startListening(): void {
    if (!this.mediaStream || !this.audioContext) return;

    const source = this.audioContext.createMediaStreamSource(this.mediaStream);
    this.processor = this.audioContext.createScriptProcessor(4096, 1, 1);

    this.processor.onaudioprocess = (event) => {
      const inputData = event.inputBuffer.getChannelData(0);
      const pcm16 = this.floatTo16BitPCM(inputData);
      const base64 = this.arrayBufferToBase64(pcm16.buffer);

      if (voiceStore.state.provider === 'agentvoicebox' && this.agentVoiceBoxWs) {
        this.agentVoiceBoxWs.send(JSON.stringify({
          type: 'input_audio_buffer.append',
          audio: base64,
        }));
      } else if (voiceStore.state.provider === 'local') {
        wsClient.send('voice.input_audio', { audio: base64 });
      }
    };

    source.connect(this.processor);
    this.processor.connect(this.audioContext.destination);
    voiceStore.setState('listening');
    wsClient.send('voice.started', {});
  }

  stopListening(): void {
    this.processor?.disconnect();
    this.processor = null;
    voiceStore.setState('idle');
  }

  private playAudioDelta(base64Audio: string): void {
    const audioData = this.base64ToArrayBuffer(base64Audio);
    const audioBuffer = this.audioContext!.createBuffer(1, audioData.byteLength / 2, 24000);
    const channelData = audioBuffer.getChannelData(0);
    const int16Array = new Int16Array(audioData);
    for (let i = 0; i < int16Array.length; i++) {
      channelData[i] = int16Array[i] / 32768;
    }
    const source = this.audioContext!.createBufferSource();
    source.buffer = audioBuffer;
    source.connect(this.audioContext!.destination);
    source.start();
  }

  private floatTo16BitPCM(input: Float32Array): Int16Array {
    const output = new Int16Array(input.length);
    for (let i = 0; i < input.length; i++) {
      const s = Math.max(-1, Math.min(1, input[i]));
      output[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
    }
    return output;
  }

  private arrayBufferToBase64(buffer: ArrayBuffer): string {
    const bytes = new Uint8Array(buffer);
    let binary = '';
    for (let i = 0; i < bytes.byteLength; i++) {
      binary += String.fromCharCode(bytes[i]);
    }
    return btoa(binary);
  }

  private base64ToArrayBuffer(base64: string): ArrayBuffer {
    const binary = atob(base64);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) {
      bytes[i] = binary.charCodeAt(i);
    }
    return bytes.buffer;
  }

  async testConnection(): Promise<boolean> {
    const config = voiceStore.state.config.agentvoicebox;
    if (!config.base_url) return false;
    try {
      const response = await fetch(`${config.base_url}/health`);
      return response.ok;
    } catch {
      return false;
    }
  }

  dispose(): void {
    this.stopListening();
    this.agentVoiceBoxWs?.close();
    this.audioContext?.close();
    this.mediaStream?.getTracks().forEach(track => track.stop());
  }
}

export const voiceService = new VoiceService();
```

### 7.2 Voice Service Implementation

```typescript
interface VoiceProvider {
  connect(): Promise<void>;
  disconnect(): void;
  startListening(): Promise<void>;
  stopListening(): void;
  speak(text: string): Promise<void>;
  cancel(): void;
  onTranscription(handler: (text: string) => void): void;
  onAudioLevel(handler: (level: number) => void): void;
  onStateChange(handler: (state: VoiceState) => void): void;
}

class LocalVoiceProvider implements VoiceProvider {
  private audioContext: AudioContext;
  private mediaStream: MediaStream | null = null;
  private whisperWorker: Worker;
  private kokoroWorker: Worker;
  
  async startListening(): Promise<void> {
    this.mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
    // Process audio through Whisper STT
  }
  
  async speak(text: string): Promise<void> {
    // Generate audio through Kokoro TTS
    const audio = await this.kokoroWorker.synthesize(text);
    await this.playAudio(audio);
  }
}

class AgentVoiceBoxProvider implements VoiceProvider {
  private ws: WebSocket | null = null;
  private config: AgentVoiceBoxConfig;
  
  async connect(): Promise<void> {
    this.ws = new WebSocket(this.config.wsUrl);
    this.ws.onmessage = this.handleMessage.bind(this);
    // Send session.update with configuration
  }
  
  async startListening(): Promise<void> {
    // Start sending audio chunks via WebSocket
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    // Process and send audio
  }
  
  private handleMessage(event: MessageEvent): void {
    const data = JSON.parse(event.data);
    switch (data.type) {
      case 'response.audio.delta':
        this.playAudioChunk(data.delta);
        break;
      case 'conversation.item.input_audio_transcription.completed':
        this.onTranscription?.(data.transcript);
        break;
    }
  }
}
```

---

## 8. Performance Requirements

### 8.1 Core Web Vitals Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| First Contentful Paint (FCP) | < 1.5s | Time to first content |
| Largest Contentful Paint (LCP) | < 2.5s | Time to largest element |
| First Input Delay (FID) | < 100ms | Time to interactive |
| Cumulative Layout Shift (CLS) | < 0.1 | Visual stability |
| Time to Interactive (TTI) | < 3.0s | Full interactivity |

### 8.2 Scale Targets

| Metric | Target | Strategy |
|--------|--------|----------|
| Concurrent WebSocket connections | 1,000,000+ | Horizontal scaling, Redis pub/sub |
| API requests/second/node | 100,000+ | Django Ninja async, connection pooling |
| Permission checks/second | 1,000,000+ | SpiceDB, Redis caching |
| Theme switch latency | < 300ms | CSS Custom Properties, no reflow |
| Component render time | < 16ms | Virtual DOM, Shadow DOM isolation |

### 8.3 Bundle Size Targets

| Bundle | Target | Strategy |
|--------|--------|----------|
| Initial JS | < 100KB gzip | Code splitting, tree shaking |
| Initial CSS | < 20KB gzip | CSS Custom Properties, minimal reset |
| Per-route chunk | < 50KB gzip | Dynamic imports, lazy loading |
| Total app | < 500KB gzip | Aggressive tree shaking |

---

## 9. Accessibility (WCAG 2.1 AA)

### 9.1 Requirements

- All interactive elements keyboard accessible
- Focus indicators visible (2px solid outline)
- ARIA labels on all controls
- Color contrast ratio >= 4.5:1
- Reduced motion support (`prefers-reduced-motion`)
- Screen reader compatible (NVDA, VoiceOver, JAWS)
- Skip navigation links
- Semantic HTML structure

### 9.2 Component Accessibility Patterns

```typescript
@customElement('eog-button')
export class EogButton extends LitElement {
  @property({ type: Boolean, reflect: true }) disabled = false;
  @property({ type: String }) ariaLabel = '';
  
  render() {
    return html`
      <button
        role="button"
        aria-label=${this.ariaLabel || nothing}
        aria-disabled=${this.disabled}
        tabindex=${this.disabled ? -1 : 0}
        @keydown=${this.handleKeydown}
      >
        <slot></slot>
      </button>
    `;
  }
  
  private handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      this.click();
    }
  }
}
```

---

## 10. File Structure

```
somaAgent01/ui/frontend/
├── src/
│   ├── components/           # Primitive components
│   │   ├── eog-button.ts
│   │   ├── eog-input.ts
│   │   ├── eog-select.ts
│   │   ├── eog-toggle.ts
│   │   ├── eog-slider.ts
│   │   ├── eog-modal.ts
│   │   ├── eog-toast.ts
│   │   ├── eog-card.ts
│   │   ├── eog-tabs.ts
│   │   └── index.ts
│   ├── layout/               # Layout components
│   │   ├── eog-app.ts
│   │   ├── eog-header.ts
│   │   ├── eog-sidebar.ts
│   │   ├── eog-main.ts
│   │   └── index.ts
│   ├── views/                # Page components
│   │   ├── eog-chat.ts
│   │   ├── eog-memory.ts
│   │   ├── eog-tools.ts
│   │   ├── eog-settings.ts
│   │   ├── eog-themes.ts
│   │   ├── eog-voice.ts
│   │   ├── eog-cognitive.ts
│   │   ├── eog-admin.ts
│   │   └── index.ts
│   ├── stores/               # State management
│   │   ├── auth-store.ts
│   │   ├── mode-store.ts
│   │   ├── theme-store.ts
│   │   ├── perm-store.ts
│   │   ├── voice-store.ts
│   │   └── index.ts
│   ├── services/             # API clients
│   │   ├── api-client.ts
│   │   ├── ws-client.ts
│   │   ├── auth-service.ts
│   │   ├── voice-service.ts
│   │   └── index.ts
│   ├── styles/               # Global styles
│   │   ├── tokens.css
│   │   ├── reset.css
│   │   └── themes/
│   │       ├── default-light.json
│   │       ├── midnight-dark.json
│   │       └── high-contrast.json
│   ├── utils/                # Utilities
│   │   ├── validators.ts
│   │   ├── formatters.ts
│   │   └── constants.ts
│   ├── router.ts             # Route configuration
│   └── index.ts              # Entry point
├── public/
│   ├── index.html
│   └── favicon.ico
├── package.json
├── vite.config.ts
├── tsconfig.json
└── web-test-runner.config.js
```

---

**Document Status:** COMPLETE

**Next Steps:**
1. Complete design.md with Django models and API schemas
2. Create tasks.md with implementation plan

---

## 5. WebSocket Event System

### 5.1 Event Types and Payloads

| Event Type | Direction | Payload | Description |
|------------|-----------|---------|-------------|
| `mode.changed` | Server→Client | `{ mode: string, previous: string }` | Agent mode changed |
| `settings.changed` | Server→Client | `{ section: string, key: string, value: any }` | Settings updated |
| `theme.changed` | Server→Client | `{ theme_id: string }` | Theme changed |
| `voice.started` | Client→Server | `{}` | Voice session started |
| `voice.speech_started` | Server→Client | `{}` | User started speaking |
| `voice.speech_stopped` | Server→Client | `{}` | User stopped speaking |
| `voice.transcription` | Server→Client | `{ text: string, final: boolean }` | STT result |
| `voice.response_started` | Server→Client | `{}` | Agent started responding |
| `voice.audio_delta` | Server→Client | `{ delta: string }` | Audio chunk (base64) |
| `voice.response_done` | Server→Client | `{}` | Agent finished responding |
| `voice.error` | Server→Client | `{ error: string, code: string }` | Voice error |
| `voice.input_audio` | Client→Server | `{ audio: string }` | Audio input (base64) |
| `voice.cancel` | Client→Server | `{}` | Cancel current response |
| `assistant.started` | Server→Client | `{ session_id: string }` | Assistant started |
| `assistant.thinking.started` | Server→Client | `{}` | Reasoning started |
| `assistant.delta` | Server→Client | `{ content: string }` | Response chunk |
| `assistant.thinking.final` | Server→Client | `{ content: string }` | Reasoning complete |
| `assistant.final` | Server→Client | `{ content: string, done: boolean }` | Response complete |
| `assistant.tool.started` | Server→Client | `{ tool: string }` | Tool execution started |
| `assistant.tool.delta` | Server→Client | `{ output: string }` | Tool output chunk |
| `assistant.tool.final` | Server→Client | `{ output: string }` | Tool execution complete |
| `system.keepalive` | Bidirectional | `{ ping?: boolean }` | Heartbeat |

### 5.2 Event Flow Diagrams

#### Chat Message Flow

```
Client                    Django Ninja                    Agent
  │                           │                             │
  │──POST /api/v2/chat───────▶│                             │
  │                           │──Kafka: chat.request───────▶│
  │                           │                             │
  │◀──WS: assistant.started───│◀──Kafka: assistant.started──│
  │                           │                             │
  │◀──WS: assistant.delta─────│◀──Kafka: assistant.delta────│
  │◀──WS: assistant.delta─────│◀──Kafka: assistant.delta────│
  │◀──WS: assistant.delta─────│◀──Kafka: assistant.delta────│
  │                           │                             │
  │◀──WS: assistant.final─────│◀──Kafka: assistant.final────│
  │                           │                             │
```

#### Voice Flow (AgentVoiceBox)

```
Client                    AgentVoiceBox                   Agent
  │                           │                             │
  │──WS: session.update──────▶│                             │
  │◀──WS: session.created─────│                             │
  │                           │                             │
  │──WS: input_audio.append──▶│                             │
  │──WS: input_audio.append──▶│                             │
  │                           │                             │
  │◀──WS: speech_started──────│                             │
  │                           │                             │
  │◀──WS: speech_stopped──────│                             │
  │                           │──STT: transcription────────▶│
  │◀──WS: conversation.item───│                             │
  │                           │                             │
  │                           │◀──LLM: response─────────────│
  │◀──WS: response.audio.delta│                             │
  │◀──WS: response.audio.delta│                             │
  │◀──WS: response.done───────│                             │
  │                           │                             │
```

---

## 6. Performance Optimization

### 6.1 Scale Targets

| Metric | Target | Strategy |
|--------|--------|----------|
| Concurrent WebSocket connections | 1,000,000+ | Connection pooling, horizontal scaling |
| First Contentful Paint | < 1.5s | Code splitting, preloading, CDN |
| Time to Interactive | < 3s | Lazy loading, service worker |
| API Response Time (p95) | < 50ms | Connection pooling, caching |
| Theme Switch | < 300ms | CSS Custom Properties (no reflow) |
| Component Render | < 16ms | Virtual scrolling, memoization |
| WebSocket Latency | < 100ms | Edge servers, sticky sessions |

### 6.2 Optimization Strategies

#### Code Splitting

```typescript
// vite.config.ts
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor-lit': ['lit', '@lit/context', '@lit-labs/signals'],
          'vendor-router': ['@vaadin/router'],
          'views-chat': ['./src/views/eog-chat-view.ts'],
          'views-memory': ['./src/views/eog-memory-view.ts'],
          'views-settings': ['./src/views/eog-settings-view.ts'],
          'views-admin': ['./src/views/eog-admin-view.ts'],
          'voice': ['./src/services/voice-service.ts', './src/stores/voice-store.ts'],
        },
      },
    },
  },
});
```

#### Virtual Scrolling

```typescript
// For large lists (memory items, audit logs, etc.)
@customElement('eog-virtual-list')
export class EogVirtualList extends LitElement {
  @property({ type: Array }) items: unknown[] = [];
  @property({ type: Number }) itemHeight = 48;
  @property({ type: Number }) overscan = 5;

  @state() private scrollTop = 0;
  @state() private containerHeight = 0;

  private get visibleRange(): { start: number; end: number } {
    const start = Math.max(0, Math.floor(this.scrollTop / this.itemHeight) - this.overscan);
    const visibleCount = Math.ceil(this.containerHeight / this.itemHeight);
    const end = Math.min(this.items.length, start + visibleCount + this.overscan * 2);
    return { start, end };
  }

  render() {
    const { start, end } = this.visibleRange;
    const visibleItems = this.items.slice(start, end);
    const totalHeight = this.items.length * this.itemHeight;
    const offsetY = start * this.itemHeight;

    return html`
      <div class="container" @scroll=${this.handleScroll}>
        <div class="spacer" style="height: ${totalHeight}px">
          <div class="content" style="transform: translateY(${offsetY}px)">
            ${visibleItems.map((item, i) => html`
              <slot name="item" .item=${item} .index=${start + i}></slot>
            `)}
          </div>
        </div>
      </div>
    `;
  }

  private handleScroll(e: Event) {
    this.scrollTop = (e.target as HTMLElement).scrollTop;
  }
}
```

#### Service Worker Caching

```typescript
// sw.ts
const CACHE_NAME = 'eog-v1';
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/assets/main.js',
  '/assets/styles.css',
  '/assets/themes/default-light.json',
  '/assets/themes/midnight-dark.json',
];

self.addEventListener('install', (event: ExtendableEvent) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(STATIC_ASSETS))
  );
});

self.addEventListener('fetch', (event: FetchEvent) => {
  // Cache-first for static assets
  if (STATIC_ASSETS.some(asset => event.request.url.endsWith(asset))) {
    event.respondWith(
      caches.match(event.request).then(cached => cached || fetch(event.request))
    );
    return;
  }

  // Network-first for API calls
  if (event.request.url.includes('/api/')) {
    event.respondWith(
      fetch(event.request).catch(() => caches.match(event.request))
    );
  }
});
```

### 6.3 Connection Pooling for Millions of Users

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    WEBSOCKET SCALING ARCHITECTURE                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   Clients (1M+)                                                              │
│   ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐                                  │
│   │ C1  │ │ C2  │ │ C3  │ │ ... │ │ Cn  │                                  │
│   └──┬──┘ └──┬──┘ └──┬──┘ └──┬──┘ └──┬──┘                                  │
│      │       │       │       │       │                                       │
│      └───────┴───────┴───────┴───────┘                                       │
│                      │                                                        │
│                      ▼                                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                    LOAD BALANCER (nginx/HAProxy)                     │   │
│   │                    - Sticky sessions (IP hash)                       │   │
│   │                    - Health checks                                   │   │
│   │                    - SSL termination                                 │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                      │                                                        │
│      ┌───────────────┼───────────────┬───────────────┐                       │
│      ▼               ▼               ▼               ▼                       │
│   ┌──────┐       ┌──────┐       ┌──────┐       ┌──────┐                     │
│   │ WS-1 │       │ WS-2 │       │ WS-3 │       │ WS-N │                     │
│   │ 10K  │       │ 10K  │       │ 10K  │       │ 10K  │                     │
│   │ conn │       │ conn │       │ conn │       │ conn │                     │
│   └──┬───┘       └──┬───┘       └──┬───┘       └──┬───┘                     │
│      │              │              │              │                          │
│      └──────────────┴──────────────┴──────────────┘                          │
│                      │                                                        │
│                      ▼                                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                         REDIS PUB/SUB                                │   │
│   │                    - Cross-node event broadcast                      │   │
│   │                    - Session state sync                              │   │
│   │                    - Connection tracking                             │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Django Channels Configuration

```python
# File: eog/settings/production.py

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [
                {
                    "address": os.environ.get("REDIS_URL", "redis://localhost:6379"),
                    "db": 0,
                }
            ],
            "capacity": 1500,  # Max messages per channel
            "expiry": 60,      # Message expiry in seconds
        },
    },
}

# WebSocket connection limits per worker
ASGI_APPLICATION = "eog.asgi.application"
WEBSOCKET_MAX_CONNECTIONS = 10000  # Per worker process
WEBSOCKET_HEARTBEAT_INTERVAL = 20  # Seconds
WEBSOCKET_RECONNECT_DELAY = 1000   # Milliseconds
```

---

## 7. AgentSkin Theme Integration

### 7.1 CSS Custom Properties Mapping

```css
/* File: src/styles/agentskin-bridge.css */

:root {
  /* Map AgentSkin variables to EOG variables */
  --eog-bg-void: var(--bg-void, #0f172a);
  --eog-glass-surface: var(--glass-surface, rgba(30, 41, 59, 0.85));
  --eog-glass-border: var(--glass-border, rgba(255, 255, 255, 0.05));
  --eog-text-main: var(--text-main, #e2e8f0);
  --eog-text-dim: var(--text-dim, #64748b);
  --eog-accent-primary: var(--accent-primary, #3b82f6);
  --eog-accent-secondary: var(--accent-secondary, #8b5cf6);
  --eog-accent-success: var(--accent-success, #22c55e);
  --eog-accent-warning: var(--accent-warning, #f59e0b);
  --eog-accent-danger: var(--accent-danger, #ef4444);
  --eog-shadow-soft: var(--shadow-soft, 0 10px 40px -10px rgba(0, 0, 0, 0.5));
  --eog-radius-sm: var(--radius-sm, 4px);
  --eog-radius-md: var(--radius-md, 8px);
  --eog-radius-lg: var(--radius-lg, 16px);
  --eog-radius-full: var(--radius-full, 9999px);
  --eog-spacing-xs: var(--spacing-xs, 4px);
  --eog-spacing-sm: var(--spacing-sm, 8px);
  --eog-spacing-md: var(--spacing-md, 16px);
  --eog-spacing-lg: var(--spacing-lg, 24px);
  --eog-spacing-xl: var(--spacing-xl, 32px);
  --eog-font-sans: var(--font-sans, 'Space Grotesk', sans-serif);
  --eog-font-mono: var(--font-mono, 'JetBrains Mono', monospace);
  --eog-text-xs: var(--text-xs, 10px);
  --eog-text-sm: var(--text-sm, 12px);
  --eog-text-base: var(--text-base, 14px);
  --eog-text-lg: var(--text-lg, 16px);
  --eog-text-xl: var(--text-xl, 20px);
}
```

### 7.2 Theme Application Logic

```typescript
// File: src/utils/theme-loader.ts

export interface AgentSkinTheme {
  name: string;
  version: string;
  author: string;
  description?: string;
  category?: string;
  tags?: string[];
  variables: Record<string, string>;
}

const REQUIRED_VARIABLES = [
  'bg-void', 'glass-surface', 'glass-border', 'text-main', 'text-dim',
  'accent-primary', 'accent-secondary', 'accent-success', 'accent-warning', 'accent-danger',
  'shadow-soft', 'radius-sm', 'radius-md', 'radius-lg', 'radius-full',
  'spacing-xs', 'spacing-sm', 'spacing-md', 'spacing-lg', 'spacing-xl',
  'font-sans', 'font-mono', 'text-xs', 'text-sm', 'text-base', 'text-lg',
];

const URL_PATTERN = /url\s*\(/i;

export function validateTheme(theme: AgentSkinTheme): { valid: boolean; errors: string[] } {
  const errors: string[] = [];

  // Check required fields
  if (!theme.name) errors.push('Missing required field: name');
  if (!theme.version) errors.push('Missing required field: version');
  if (!theme.variables) errors.push('Missing required field: variables');

  // Check required variables (26 minimum)
  const missingVars = REQUIRED_VARIABLES.filter(v => !(v in theme.variables));
  if (missingVars.length > 0) {
    errors.push(`Missing required variables: ${missingVars.join(', ')}`);
  }

  // Security: Check for url() in values (XSS prevention)
  for (const [key, value] of Object.entries(theme.variables)) {
    if (URL_PATTERN.test(value)) {
      errors.push(`Security violation: url() not allowed in variable "${key}"`);
    }
  }

  // Validate contrast ratios (WCAG AA)
  const textMain = theme.variables['text-main'];
  const bgVoid = theme.variables['bg-void'];
  if (textMain && bgVoid) {
    const ratio = calculateContrastRatio(textMain, bgVoid);
    if (ratio < 4.5) {
      errors.push(`Contrast ratio ${ratio.toFixed(2)} below WCAG AA minimum (4.5:1)`);
    }
  }

  return { valid: errors.length === 0, errors };
}

export function applyTheme(theme: AgentSkinTheme): void {
  const root = document.documentElement;
  
  // Apply all variables with --eog- prefix
  for (const [key, value] of Object.entries(theme.variables)) {
    root.style.setProperty(`--eog-${key}`, value);
  }

  // Also set without prefix for backward compatibility
  for (const [key, value] of Object.entries(theme.variables)) {
    root.style.setProperty(`--${key}`, value);
  }

  // Dispatch theme change event
  window.dispatchEvent(new CustomEvent('eog-theme-changed', { detail: theme }));
}

function calculateContrastRatio(fg: string, bg: string): number {
  const fgLum = getLuminance(parseColor(fg));
  const bgLum = getLuminance(parseColor(bg));
  const lighter = Math.max(fgLum, bgLum);
  const darker = Math.min(fgLum, bgLum);
  return (lighter + 0.05) / (darker + 0.05);
}

function parseColor(color: string): [number, number, number] {
  // Handle hex colors
  if (color.startsWith('#')) {
    const hex = color.slice(1);
    const r = parseInt(hex.slice(0, 2), 16);
    const g = parseInt(hex.slice(2, 4), 16);
    const b = parseInt(hex.slice(4, 6), 16);
    return [r, g, b];
  }
  // Handle rgba
  const match = color.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/);
  if (match) {
    return [parseInt(match[1]), parseInt(match[2]), parseInt(match[3])];
  }
  return [0, 0, 0];
}

function getLuminance([r, g, b]: [number, number, number]): number {
  const [rs, gs, bs] = [r, g, b].map(c => {
    c = c / 255;
    return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
  });
  return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
}
```

---

## 8. Voice UI Components

### 8.1 Voice Button Component

```typescript
// File: src/components/eog-voice-button.ts

import { LitElement, html, css } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';
import { consume } from '@lit/context';
import { voiceContext, VoiceStoreState } from '../stores/voice-store';
import { voiceService } from '../services/voice-service';

@customElement('eog-voice-button')
export class EogVoiceButton extends LitElement {
  static styles = css`
    :host {
      display: inline-block;
    }

    button {
      width: 48px;
      height: 48px;
      border-radius: var(--eog-radius-full);
      border: 2px solid var(--eog-glass-border);
      background: var(--eog-glass-surface);
      color: var(--eog-text-main);
      cursor: pointer;
      transition: all 0.2s ease;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    button:hover:not(:disabled) {
      background: var(--eog-accent-primary);
      border-color: var(--eog-accent-primary);
    }

    button:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }

    button.listening {
      background: var(--eog-accent-danger);
      border-color: var(--eog-accent-danger);
      animation: pulse 1.5s infinite;
    }

    button.processing {
      background: var(--eog-accent-warning);
      border-color: var(--eog-accent-warning);
    }

    button.speaking {
      background: var(--eog-accent-success);
      border-color: var(--eog-accent-success);
    }

    @keyframes pulse {
      0%, 100% { transform: scale(1); }
      50% { transform: scale(1.1); }
    }

    .icon {
      width: 24px;
      height: 24px;
    }
  `;

  @consume({ context: voiceContext, subscribe: true })
  @property({ attribute: false })
  voiceState!: VoiceStoreState;

  @state() private isHolding = false;

  private get isDisabled(): boolean {
    return !this.voiceState.enabled || this.voiceState.provider === 'disabled';
  }

  private get buttonClass(): string {
    return this.voiceState.state;
  }

  render() {
    return html`
      <button
        class=${this.buttonClass}
        ?disabled=${this.isDisabled}
        @mousedown=${this.handleMouseDown}
        @mouseup=${this.handleMouseUp}
        @mouseleave=${this.handleMouseUp}
        @touchstart=${this.handleMouseDown}
        @touchend=${this.handleMouseUp}
        title=${this.getTooltip()}
      >
        ${this.renderIcon()}
      </button>
    `;
  }

  private renderIcon() {
    switch (this.voiceState.state) {
      case 'listening':
        return html`<svg class="icon" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
          <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
        </svg>`;
      case 'processing':
        return html`<eog-spinner size="sm"></eog-spinner>`;
      case 'speaking':
        return html`<svg class="icon" viewBox="0 0 24 24" fill="currentColor">
          <path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02z"/>
        </svg>`;
      default:
        return html`<svg class="icon" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
          <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
        </svg>`;
    }
  }

  private getTooltip(): string {
    if (this.isDisabled) return 'Voice disabled';
    switch (this.voiceState.state) {
      case 'listening': return 'Listening... Release to stop';
      case 'processing': return 'Processing...';
      case 'speaking': return 'Speaking...';
      default: return 'Hold to speak';
    }
  }

  private handleMouseDown(e: Event) {
    e.preventDefault();
    if (this.isDisabled) return;
    this.isHolding = true;
    voiceService.startListening();
  }

  private handleMouseUp() {
    if (!this.isHolding) return;
    this.isHolding = false;
    voiceService.stopListening();
  }
}
```

### 8.2 Voice Settings Component

```typescript
// File: src/views/eog-voice-settings.ts

import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import { voiceStore, VoiceProvider, VoiceConfig } from '../stores/voice-store';
import { voiceService } from '../services/voice-service';

@customElement('eog-voice-settings')
export class EogVoiceSettings extends LitElement {
  static styles = css`
    :host {
      display: block;
      padding: var(--eog-spacing-md);
    }

    .section {
      background: var(--eog-glass-surface);
      border: 1px solid var(--eog-glass-border);
      border-radius: var(--eog-radius-lg);
      padding: var(--eog-spacing-md);
      margin-bottom: var(--eog-spacing-md);
    }

    .section-title {
      font-size: var(--eog-text-lg);
      font-weight: 600;
      margin-bottom: var(--eog-spacing-sm);
      color: var(--eog-text-main);
    }

    .field {
      margin-bottom: var(--eog-spacing-sm);
    }

    .field-label {
      display: block;
      font-size: var(--eog-text-sm);
      color: var(--eog-text-dim);
      margin-bottom: var(--eog-spacing-xs);
    }

    .provider-cards {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: var(--eog-spacing-sm);
    }

    .provider-card {
      padding: var(--eog-spacing-md);
      border: 2px solid var(--eog-glass-border);
      border-radius: var(--eog-radius-md);
      cursor: pointer;
      transition: all 0.2s ease;
      text-align: center;
    }

    .provider-card:hover {
      border-color: var(--eog-accent-primary);
    }

    .provider-card.selected {
      border-color: var(--eog-accent-primary);
      background: rgba(59, 130, 246, 0.1);
    }

    .provider-icon {
      font-size: 32px;
      margin-bottom: var(--eog-spacing-xs);
    }

    .provider-name {
      font-weight: 600;
      color: var(--eog-text-main);
    }

    .provider-desc {
      font-size: var(--eog-text-xs);
      color: var(--eog-text-dim);
    }

    .test-button {
      margin-top: var(--eog-spacing-sm);
    }

    .test-result {
      margin-top: var(--eog-spacing-xs);
      font-size: var(--eog-text-sm);
    }

    .test-result.success {
      color: var(--eog-accent-success);
    }

    .test-result.error {
      color: var(--eog-accent-danger);
    }
  `;

  @state() private config: VoiceConfig = voiceStore.state.config;
  @state() private testResult: { success: boolean; message: string } | null = null;
  @state() private testing = false;

  render() {
    return html`
      <div class="section">
        <div class="section-title">Voice Provider</div>
        <div class="provider-cards">
          ${this.renderProviderCard('disabled', '🔇', 'Disabled', 'No voice features')}
          ${this.renderProviderCard('local', '🎤', 'Local', 'Whisper STT + Kokoro TTS')}
          ${this.renderProviderCard('agentvoicebox', '🗣️', 'AgentVoiceBox', 'Full speech-on-speech')}
        </div>
      </div>

      ${this.config.provider === 'local' ? this.renderLocalSettings() : ''}
      ${this.config.provider === 'agentvoicebox' ? this.renderAgentVoiceBoxSettings() : ''}
      ${this.config.provider !== 'disabled' ? this.renderAudioSettings() : ''}
    `;
  }

  private renderProviderCard(provider: VoiceProvider, icon: string, name: string, desc: string) {
    return html`
      <div
        class="provider-card ${this.config.provider === provider ? 'selected' : ''}"
        @click=${() => this.selectProvider(provider)}
      >
        <div class="provider-icon">${icon}</div>
        <div class="provider-name">${name}</div>
        <div class="provider-desc">${desc}</div>
      </div>
    `;
  }

  private renderLocalSettings() {
    return html`
      <div class="section">
        <div class="section-title">Local Voice Settings</div>
        
        <div class="field">
          <label class="field-label">STT Engine</label>
          <eog-select
            .value=${this.config.local.stt_engine}
            .options=${[
              { value: 'whisper', label: 'Whisper' },
              { value: 'faster-whisper', label: 'Faster Whisper' },
            ]}
            @change=${(e: CustomEvent) => this.updateLocal('stt_engine', e.detail.value)}
          ></eog-select>
        </div>

        <div class="field">
          <label class="field-label">STT Model Size</label>
          <eog-select
            .value=${this.config.local.stt_model_size}
            .options=${[
              { value: 'tiny', label: 'Tiny (fastest)' },
              { value: 'base', label: 'Base (balanced)' },
              { value: 'small', label: 'Small' },
              { value: 'medium', label: 'Medium' },
              { value: 'large', label: 'Large (most accurate)' },
            ]}
            @change=${(e: CustomEvent) => this.updateLocal('stt_model_size', e.detail.value)}
          ></eog-select>
        </div>

        <div class="field">
          <label class="field-label">TTS Engine</label>
          <eog-select
            .value=${this.config.local.tts_engine}
            .options=${[
              { value: 'kokoro', label: 'Kokoro (recommended)' },
              { value: 'browser', label: 'Browser TTS' },
            ]}
            @change=${(e: CustomEvent) => this.updateLocal('tts_engine', e.detail.value)}
          ></eog-select>
        </div>

        <div class="field">
          <label class="field-label">TTS Voice</label>
          <eog-input
            .value=${this.config.local.tts_voice}
            @change=${(e: CustomEvent) => this.updateLocal('tts_voice', e.detail.value)}
          ></eog-input>
        </div>

        <div class="field">
          <label class="field-label">TTS Speed: ${this.config.local.tts_speed.toFixed(1)}x</label>
          <eog-slider
            .value=${this.config.local.tts_speed}
            .min=${0.5}
            .max=${2.0}
            .step=${0.1}
            @change=${(e: CustomEvent) => this.updateLocal('tts_speed', e.detail.value)}
          ></eog-slider>
        </div>

        <div class="field">
          <label class="field-label">VAD Threshold: ${this.config.local.vad_threshold.toFixed(2)}</label>
          <eog-slider
            .value=${this.config.local.vad_threshold}
            .min=${0.0}
            .max=${1.0}
            .step=${0.05}
            @change=${(e: CustomEvent) => this.updateLocal('vad_threshold', e.detail.value)}
          ></eog-slider>
        </div>

        <div class="field">
          <label class="field-label">Language</label>
          <eog-select
            .value=${this.config.local.language}
            .options=${[
              { value: 'en-US', label: 'English (US)' },
              { value: 'en-GB', label: 'English (UK)' },
              { value: 'es-ES', label: 'Spanish' },
              { value: 'fr-FR', label: 'French' },
              { value: 'de-DE', label: 'German' },
              { value: 'ja-JP', label: 'Japanese' },
              { value: 'zh-CN', label: 'Chinese (Simplified)' },
            ]}
            @change=${(e: CustomEvent) => this.updateLocal('language', e.detail.value)}
          ></eog-select>
        </div>
      </div>
    `;
  }

  private renderAgentVoiceBoxSettings() {
    return html`
      <div class="section">
        <div class="section-title">AgentVoiceBox Settings</div>
        
        <div class="field">
          <label class="field-label">Server URL</label>
          <eog-input
            .value=${this.config.agentvoicebox.base_url}
            placeholder="http://localhost:8000"
            @change=${(e: CustomEvent) => this.updateAVB('base_url', e.detail.value)}
          ></eog-input>
        </div>

        <div class="field">
          <label class="field-label">WebSocket URL</label>
          <eog-input
            .value=${this.config.agentvoicebox.ws_url}
            placeholder="ws://localhost:8001/v1/realtime"
            @change=${(e: CustomEvent) => this.updateAVB('ws_url', e.detail.value)}
          ></eog-input>
        </div>

        <div class="field">
          <label class="field-label">API Token</label>
          <eog-input
            type="password"
            .value=${this.config.agentvoicebox.api_token}
            @change=${(e: CustomEvent) => this.updateAVB('api_token', e.detail.value)}
          ></eog-input>
        </div>

        <div class="field">
          <label class="field-label">Model</label>
          <eog-input
            .value=${this.config.agentvoicebox.model}
            @change=${(e: CustomEvent) => this.updateAVB('model', e.detail.value)}
          ></eog-input>
        </div>

        <div class="field">
          <label class="field-label">Voice</label>
          <eog-input
            .value=${this.config.agentvoicebox.voice}
            @change=${(e: CustomEvent) => this.updateAVB('voice', e.detail.value)}
          ></eog-input>
        </div>

        <div class="field">
          <eog-toggle
            .checked=${this.config.agentvoicebox.turn_detection}
            @change=${(e: CustomEvent) => this.updateAVB('turn_detection', e.detail.checked)}
          >Server-side Turn Detection</eog-toggle>
        </div>

        <eog-button
          class="test-button"
          variant="primary"
          ?loading=${this.testing}
          @eog-click=${this.testConnection}
        >Test Connection</eog-button>

        ${this.testResult ? html`
          <div class="test-result ${this.testResult.success ? 'success' : 'error'}">
            ${this.testResult.message}
          </div>
        ` : ''}
      </div>
    `;
  }

  private renderAudioSettings() {
    return html`
      <div class="section">
        <div class="section-title">Audio Settings</div>
        
        <div class="field">
          <label class="field-label">Input Device</label>
          <eog-select
            .value=${String(this.config.audio.input_device)}
            .options=${[{ value: '0', label: 'Default Microphone' }]}
            @change=${(e: CustomEvent) => this.updateAudio('input_device', parseInt(e.detail.value))}
          ></eog-select>
        </div>

        <div class="field">
          <label class="field-label">Output Device</label>
          <eog-select
            .value=${String(this.config.audio.output_device)}
            .options=${[{ value: '0', label: 'Default Speaker' }]}
            @change=${(e: CustomEvent) => this.updateAudio('output_device', parseInt(e.detail.value))}
          ></eog-select>
        </div>

        <div class="field">
          <label class="field-label">Sample Rate</label>
          <eog-select
            .value=${String(this.config.audio.sample_rate)}
            .options=${[
              { value: '16000', label: '16 kHz' },
              { value: '24000', label: '24 kHz (recommended)' },
              { value: '44100', label: '44.1 kHz' },
              { value: '48000', label: '48 kHz' },
            ]}
            @change=${(e: CustomEvent) => this.updateAudio('sample_rate', parseInt(e.detail.value))}
          ></eog-select>
        </div>
      </div>
    `;
  }

  private selectProvider(provider: VoiceProvider) {
    this.config = { ...this.config, provider };
    voiceStore.setProvider(provider);
    this.saveConfig();
  }

  private updateLocal(key: string, value: any) {
    this.config = {
      ...this.config,
      local: { ...this.config.local, [key]: value },
    };
    this.saveConfig();
  }

  private updateAVB(key: string, value: any) {
    this.config = {
      ...this.config,
      agentvoicebox: { ...this.config.agentvoicebox, [key]: value },
    };
    this.saveConfig();
  }

  private updateAudio(key: string, value: any) {
    this.config = {
      ...this.config,
      audio: { ...this.config.audio, [key]: value },
    };
    this.saveConfig();
  }

  private async saveConfig() {
    voiceStore.updateConfig(this.config);
    await fetch('/api/v2/settings/voice', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(this.config),
    });
  }

  private async testConnection() {
    this.testing = true;
    this.testResult = null;
    try {
      const success = await voiceService.testConnection();
      this.testResult = {
        success,
        message: success ? '✓ Connection successful' : '✗ Connection failed',
      };
    } catch (e) {
      this.testResult = { success: false, message: `✗ Error: ${e}` };
    } finally {
      this.testing = false;
    }
  }
}
```

---

## 9. File Structure Summary

```
somaAgent01/ui/
├── backend/                          # Django + Django Ninja
│   ├── eog/                          # Django project
│   │   ├── settings/
│   │   │   ├── base.py
│   │   │   ├── development.py
│   │   │   └── production.py
│   │   ├── urls.py
│   │   ├── asgi.py
│   │   └── wsgi.py
│   ├── api/                          # Django Ninja API
│   │   ├── router.py
│   │   ├── schemas/
│   │   │   ├── auth.py
│   │   │   ├── settings.py
│   │   │   ├── themes.py
│   │   │   ├── modes.py
│   │   │   ├── memory.py
│   │   │   ├── voice.py
│   │   │   └── tools.py
│   │   ├── endpoints/
│   │   │   ├── auth.py
│   │   │   ├── settings.py
│   │   │   ├── themes.py
│   │   │   ├── modes.py
│   │   │   ├── memory.py
│   │   │   ├── voice.py
│   │   │   ├── tools.py
│   │   │   ├── cognitive.py
│   │   │   └── admin.py
│   │   └── middleware/
│   │       ├── tenant.py
│   │       ├── permission.py
│   │       └── audit.py
│   ├── core/                         # Django models
│   │   ├── models/
│   │   │   ├── tenant.py
│   │   │   ├── user.py
│   │   │   ├── settings.py
│   │   │   ├── theme.py
│   │   │   └── audit_log.py
│   │   └── migrations/
│   ├── permissions/                  # SpiceDB
│   │   ├── client.py
│   │   ├── schema.zed
│   │   └── decorators.py
│   ├── realtime/                     # Django Channels
│   │   ├── consumers.py
│   │   ├── routing.py
│   │   └── events.py
│   ├── manage.py
│   └── requirements.txt
│
├── frontend/                         # Lit Web Components
│   ├── src/
│   │   ├── components/               # Reusable components
│   │   │   ├── eog-button.ts
│   │   │   ├── eog-input.ts
│   │   │   ├── eog-select.ts
│   │   │   ├── eog-toggle.ts
│   │   │   ├── eog-slider.ts
│   │   │   ├── eog-modal.ts
│   │   │   ├── eog-toast.ts
│   │   │   ├── eog-card.ts
│   │   │   ├── eog-tabs.ts
│   │   │   ├── eog-spinner.ts
│   │   │   ├── eog-voice-button.ts
│   │   │   └── index.ts
│   │   ├── views/                    # Page components
│   │   │   ├── eog-app.ts
│   │   │   ├── eog-chat-view.ts
│   │   │   ├── eog-settings-view.ts
│   │   │   ├── eog-voice-settings.ts
│   │   │   ├── eog-themes-view.ts
│   │   │   ├── eog-memory-view.ts
│   │   │   ├── eog-tools-view.ts
│   │   │   ├── eog-cognitive-view.ts
│   │   │   ├── eog-admin-view.ts
│   │   │   └── eog-audit-view.ts
│   │   ├── stores/                   # State management
│   │   │   ├── auth-store.ts
│   │   │   ├── mode-store.ts
│   │   │   ├── theme-store.ts
│   │   │   ├── permission-store.ts
│   │   │   ├── voice-store.ts
│   │   │   ├── settings-store.ts
│   │   │   ├── chat-store.ts
│   │   │   └── memory-store.ts
│   │   ├── services/                 # API clients
│   │   │   ├── api-client.ts
│   │   │   ├── websocket-client.ts
│   │   │   ├── auth-service.ts
│   │   │   ├── settings-service.ts
│   │   │   ├── theme-service.ts
│   │   │   ├── voice-service.ts
│   │   │   └── permission-service.ts
│   │   ├── styles/                   # Global styles
│   │   │   ├── tokens.css
│   │   │   ├── reset.css
│   │   │   ├── agentskin-bridge.css
│   │   │   └── themes/
│   │   │       ├── default-light.json
│   │   │       ├── midnight-dark.json
│   │   │       └── high-contrast.json
│   │   ├── utils/                    # Utilities
│   │   │   ├── validators.ts
│   │   │   ├── formatters.ts
│   │   │   ├── theme-loader.ts
│   │   │   └── constants.ts
│   │   ├── index.ts
│   │   └── sw.ts                     # Service Worker
│   ├── public/
│   │   ├── index.html
│   │   └── favicon.ico
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   └── web-test-runner.config.js
│
└── docker/
    ├── Dockerfile.backend
    ├── Dockerfile.frontend
    └── docker-compose.yml
```

---

## 10. Implementation Checklist

### Phase 1: Foundation (Week 1-2)
- [ ] Django project setup with Django Ninja
- [ ] SpiceDB schema and client
- [ ] Lit project setup with Vite
- [ ] Base components (button, input, select, toggle)
- [ ] Auth store and service
- [ ] WebSocket client

### Phase 2: Core Features (Week 3-4)
- [ ] Mode store and selector
- [ ] Theme store and AgentSkin integration
- [ ] Settings views (all tabs)
- [ ] Permission store and decorators
- [ ] Chat view with streaming

### Phase 3: Voice Integration (Week 5-6)
- [ ] Voice store implementation
- [ ] Local voice service (Whisper + Kokoro)
- [ ] AgentVoiceBox integration
- [ ] Voice settings UI
- [ ] Voice button and overlay

### Phase 4: Advanced Features (Week 7-8)
- [ ] Memory view with virtual scrolling
- [ ] Cognitive panel (neuromodulators)
- [ ] Admin dashboard
- [ ] Audit log viewer
- [ ] Tool catalog

### Phase 5: Optimization (Week 9-10)
- [ ] Service worker caching
- [ ] Code splitting optimization
- [ ] Performance testing (1M connections)
- [ ] Accessibility audit (WCAG AA)
- [ ] Security audit

---

**Document Status:** COMPLETE

**Next Steps:**
1. Create `tasks.md` with detailed implementation tasks
2. Begin Phase 1 implementation
3. Set up CI/CD pipeline for parallel build
