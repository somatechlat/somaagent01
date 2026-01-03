# Eye of God UIX — Technical Design Document

## Document Control

| Field | Value |
|-------|-------|
| **Document ID** | SA01-EOG-DES-2025-12 |
| **Version** | 1.0 |
| **Date** | 2025-12-21 |
| **Status** | DRAFT |
| **Classification** | CANONICAL |
| **Implements** | SA01-EOG-REQ-2025-12 |

---

## 1. Architecture Overview

### 1.1 System Context Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENTS                                         │
├─────────────────┬─────────────────┬─────────────────┬───────────────────────┤
│   Web Browser   │  Tauri Desktop  │   Rust CLI      │   External A2A        │
│   (Lit 3.x)     │  (Lit + Rust)   │   (Ratatui)     │   Agents              │
└────────┬────────┴────────┬────────┴────────┬────────┴───────────┬───────────┘
         │                 │                 │                     │
         │ HTTPS/WSS       │ IPC + HTTPS     │ HTTPS               │ HTTPS
         ▼                 ▼                 ▼                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DJANGO NINJA API GATEWAY                             │
│                              (Port 8020)                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ REST API     │  │ WebSocket    │  │ OpenAPI 3.1  │  │ Rate Limiter │    │
│  │ (Ninja)      │  │ (Channels)   │  │ Schema       │  │ (Redis)      │    │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘    │
└────────┬────────────────┬────────────────┬────────────────┬─────────────────┘
         │                │                │                │
         ▼                ▼                ▼                ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│    SpiceDB      │ │   PostgreSQL    │ │     Redis       │ │     Kafka       │
│  (Permissions)  │ │   (Primary DB)  │ │   (Cache/WS)    │ │   (Events)      │
│  Port 50051     │ │   Port 5432     │ │   Port 6379     │ │   Port 9092     │
└─────────────────┘ └─────────────────┘ └─────────────────┘ └─────────────────┘
```

### 1.2 Parallel Build Strategy

**CRITICAL**: This is a PARALLEL BUILD, not a replacement of FastAPI.

| Component | Current (FastAPI) | New (Django Ninja) | Coexistence |
|-----------|-------------------|--------------------| ------------|
| Gateway | Port 8010 | Port 8020 | Both run simultaneously |
| WebUI | `/webui/` (Alpine.js) | `/ui/` (Lit 3.x) | Both served |
| API Prefix | `/v1/` | `/api/v2/` | No collision |
| WebSocket | `/ws/` | `/ws/v2/` | Separate channels |

**Migration Path:**
1. Phase 1: Django Ninja runs alongside FastAPI (feature parity)
2. Phase 2: Lit UI consumes Django Ninja API exclusively
3. Phase 3: Gradual traffic migration via nginx routing
4. Phase 4: FastAPI deprecated after 6-month overlap

---

## 2. Component Design

### 2.1 Django Project Structure

```
somaAgent01/ui/
├── backend/                          # Django + Django Ninja
│   ├── eog/                          # Django project root
│   │   ├── __init__.py
│   │   ├── settings/
│   │   │   ├── __init__.py
│   │   │   ├── base.py               # Common settings
│   │   │   ├── development.py        # Dev overrides
│   │   │   └── production.py         # Prod overrides
│   │   ├── urls.py                   # Root URL config
│   │   ├── asgi.py                   # ASGI entry (Channels)
│   │   └── wsgi.py                   # WSGI fallback
│   │
│   ├── api/                          # Django Ninja API app
│   │   ├── __init__.py
│   │   ├── router.py                 # Main NinjaAPI instance
│   │   ├── schemas/                  # Pydantic schemas
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── settings.py
│   │   │   ├── themes.py
│   │   │   ├── modes.py
│   │   │   ├── memory.py
│   │   │   └── tools.py
│   │   ├── endpoints/                # API endpoint modules
│   │   │   ├── __init__.py
│   │   │   ├── auth.py               # /api/v2/auth/*
│   │   │   ├── settings.py           # /api/v2/settings/*
│   │   │   ├── themes.py             # /api/v2/themes/*
│   │   │   ├── modes.py              # /api/v2/modes/*
│   │   │   ├── memory.py             # /api/v2/memory/*
│   │   │   ├── tools.py              # /api/v2/tools/*
│   │   │   ├── cognitive.py          # /api/v2/cognitive/*
│   │   │   └── admin.py              # /api/v2/admin/*
│   │   └── middleware/
│   │       ├── __init__.py
│   │       ├── tenant.py             # X-Tenant-Id extraction
│   │       ├── permission.py         # SpiceDB check
│   │       └── audit.py              # Audit logging
│   │
│   ├── core/                         # Django models app
│   │   ├── __init__.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── tenant.py
│   │   │   ├── user.py
│   │   │   ├── settings.py
│   │   │   ├── theme.py
│   │   │   ├── feature_flag.py
│   │   │   └── audit_log.py
│   │   ├── admin.py
│   │   └── migrations/
│   │
│   ├── permissions/                  # SpiceDB integration
│   │   ├── __init__.py
│   │   ├── client.py                 # SpiceDB gRPC client
│   │   ├── schema.zed                # Permission schema
│   │   └── decorators.py             # @require_permission
│   │
│   ├── realtime/                     # Django Channels
│   │   ├── __init__.py
│   │   ├── consumers.py              # WebSocket consumers
│   │   ├── routing.py                # WS URL routing
│   │   └── events.py                 # Event types
│   │
│   ├── manage.py
│   ├── requirements.txt
│   └── pyproject.toml
```

### 2.2 Lit Frontend Structure

```
somaAgent01/ui/
├── frontend/                         # Lit Web Components
│   ├── src/
│   │   ├── components/               # Reusable UI components
│   │   │   ├── eog-button.ts         # <eog-button>
│   │   │   ├── eog-input.ts          # <eog-input>
│   │   │   ├── eog-select.ts         # <eog-select>
│   │   │   ├── eog-toggle.ts         # <eog-toggle>
│   │   │   ├── eog-slider.ts         # <eog-slider>
│   │   │   ├── eog-modal.ts          # <eog-modal>
│   │   │   ├── eog-toast.ts          # <eog-toast>
│   │   │   ├── eog-card.ts           # <eog-card>
│   │   │   ├── eog-tabs.ts           # <eog-tabs>
│   │   │   └── index.ts              # Barrel export
│   │   │
│   │   ├── views/                    # Page-level components
│   │   │   ├── eog-app.ts            # Root app shell
│   │   │   ├── eog-chat.ts           # Chat interface
│   │   │   ├── eog-settings.ts       # Settings panel
│   │   │   ├── eog-themes.ts         # Theme gallery
│   │   │   ├── eog-memory.ts         # Memory browser
│   │   │   ├── eog-tools.ts          # Tool catalog
│   │   │   ├── eog-cognitive.ts      # Cognitive panel
│   │   │   ├── eog-admin.ts          # Admin dashboard
│   │   │   └── eog-audit.ts          # Audit logs
│   │   │
│   │   ├── stores/                   # State management (Lit Context)
│   │   │   ├── auth-store.ts         # Auth state + token
│   │   │   ├── mode-store.ts         # Agent mode state
│   │   │   ├── settings-store.ts     # Settings cache
│   │   │   ├── theme-store.ts        # Active theme
│   │   │   └── permission-store.ts   # Permission cache
│   │   │
│   │   ├── services/                 # API clients
│   │   │   ├── api-client.ts         # Base fetch wrapper
│   │   │   ├── websocket-client.ts   # WS connection manager
│   │   │   ├── auth-service.ts       # Auth API calls
│   │   │   ├── settings-service.ts   # Settings API calls
│   │   │   ├── theme-service.ts      # Theme API calls
│   │   │   └── permission-service.ts # SpiceDB proxy calls
│   │   │
│   │   ├── styles/                   # Global styles
│   │   │   ├── tokens.css            # CSS custom properties
│   │   │   ├── reset.css             # CSS reset
│   │   │   └── themes/
│   │   │       ├── default-light.json
│   │   │       └── midnight-dark.json
│   │   │
│   │   ├── utils/                    # Utilities
│   │   │   ├── validators.ts         # Input validation
│   │   │   ├── formatters.ts         # Data formatting
│   │   │   └── constants.ts          # App constants
│   │   │
│   │   └── index.ts                  # Entry point
│   │
│   ├── public/
│   │   ├── index.html
│   │   └── favicon.ico
│   │
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   └── web-test-runner.config.js
```

### 2.3 SpiceDB Permission Schema

```zed
// File: somaAgent01/ui/backend/permissions/schema.zed

definition user {}

definition tenant {
    relation sysadmin: user
    relation admin: user
    relation developer: user
    relation trainer: user
    relation member: user
    relation viewer: user
    
    // Computed permissions
    permission manage = sysadmin
    permission administrate = sysadmin + admin
    permission develop = sysadmin + admin + developer
    permission train = sysadmin + admin + trainer
    permission use = sysadmin + admin + developer + trainer + member
    permission view = sysadmin + admin + developer + trainer + member + viewer
}

definition agent_mode {
    relation tenant: tenant
    relation allowed_role: tenant#admin | tenant#developer | tenant#trainer | tenant#member | tenant#viewer
    
    permission activate = allowed_role
}

definition setting_section {
    relation tenant: tenant
    relation edit_role: tenant#sysadmin | tenant#admin
    relation view_role: tenant#sysadmin | tenant#admin | tenant#developer | tenant#trainer | tenant#member | tenant#viewer
    
    permission edit = edit_role
    permission view = view_role
}

definition cognitive_parameter {
    relation tenant: tenant
    
    permission view = tenant->view
    permission edit = tenant->train + tenant->administrate
}

definition theme {
    relation tenant: tenant
    relation owner: user
    
    permission view = tenant->view
    permission apply = tenant->use
    permission edit = owner + tenant->administrate
    permission delete = tenant->administrate
}

definition tool {
    relation tenant: tenant
    relation required_mode: agent_mode
    
    permission execute = tenant->use & required_mode->activate
    permission view = tenant->view
    permission configure = tenant->administrate
}

definition memory {
    relation tenant: tenant
    
    permission read = tenant->view
    permission write = tenant->use
    permission delete = tenant->administrate
    permission export = tenant->administrate
}
```

---

## 3. API Design

### 3.1 Django Ninja Router Configuration

```python
# File: somaAgent01/ui/backend/api/router.py

from ninja import NinjaAPI
from ninja.security import HttpBearer

class BearerAuth(HttpBearer):
    def authenticate(self, request, token: str):
        # Validate JWT token
        # Return user or None
        pass

api = NinjaAPI(
    title="Eye of God API",
    version="2.0.0",
    urls_namespace="eog_api",
    auth=BearerAuth(),
    docs_url="/docs",
    openapi_url="/openapi.json",
)

# Register endpoint routers
from api.endpoints import auth, settings, themes, modes, memory, tools, cognitive, admin

api.add_router("/auth", auth.router, tags=["Authentication"])
api.add_router("/settings", settings.router, tags=["Settings"])
api.add_router("/themes", themes.router, tags=["Themes"])
api.add_router("/modes", modes.router, tags=["Agent Modes"])
api.add_router("/memory", memory.router, tags=["Memory"])
api.add_router("/tools", tools.router, tags=["Tools"])
api.add_router("/cognitive", cognitive.router, tags=["Cognitive"])
api.add_router("/admin", admin.router, tags=["Admin"])
```

### 3.2 Endpoint Mapping (FastAPI → Django Ninja)

| FastAPI Endpoint | Django Ninja Endpoint | Notes |
|------------------|----------------------|-------|
| `GET /v1/health` | `GET /api/v2/health` | Health check |
| `GET /v1/sessions` | `GET /api/v2/sessions` | Session list |
| `POST /v1/llm/invoke` | `POST /api/v2/llm/invoke` | LLM invocation |
| `GET /v1/runtime-config` | `GET /api/v2/settings/runtime` | Runtime config |
| `GET /v1/capsules` | `GET /api/v2/capsules` | Capsule registry |
| `POST /v1/chat` | `POST /api/v2/chat` | Chat message |
| `GET /v1/memory/recall` | `GET /api/v2/memory/recall` | Memory recall |
| `POST /v1/memory/remember` | `POST /api/v2/memory/remember` | Memory store |
| `GET /v1/tools` | `GET /api/v2/tools` | Tool catalog |
| `POST /v1/tools/execute` | `POST /api/v2/tools/execute` | Tool execution |
| `GET /v1/feature-flags` | `GET /api/v2/settings/flags` | Feature flags |
| `WS /ws/chat` | `WS /ws/v2/chat` | Chat WebSocket |
| `WS /ws/events` | `WS /ws/v2/events` | Event stream |

### 3.3 Schema Examples

```python
# File: somaAgent01/ui/backend/api/schemas/settings.py

from ninja import Schema
from typing import Optional, Dict, Any
from enum import Enum

class SettingsTab(str, Enum):
    AGENT = "agent"
    EXTERNAL = "external"
    CONNECTIVITY = "connectivity"
    SYSTEM = "system"

class ModelConfig(Schema):
    provider: str
    model: str
    context_length: int = 4096
    rpm: int = 60
    tpm: int = 100000
    vision: bool = False

class AgentSettings(Schema):
    chat_model: ModelConfig
    utility_model: ModelConfig
    browser_model: Optional[ModelConfig] = None
    embedding_model: Optional[ModelConfig] = None
    memory_enabled: bool = True
    recall_interval: int = 30
    max_memories: int = 100
    similarity_threshold: float = 0.7

class SettingsResponse(Schema):
    tab: SettingsTab
    data: Dict[str, Any]
    updated_at: str
    version: int

class SettingsUpdateRequest(Schema):
    tab: SettingsTab
    data: Dict[str, Any]
    version: int  # Optimistic locking
```

```python
# File: somaAgent01/ui/backend/api/schemas/themes.py

from ninja import Schema
from typing import Optional, Dict, List
from pydantic import HttpUrl

class ThemeVariables(Schema):
    bg_void: str
    glass_surface: str
    glass_border: str
    text_main: str
    text_dim: str
    accent_slate: str
    # ... 26 total variables

class Theme(Schema):
    id: str
    name: str
    version: str
    author: str
    description: Optional[str] = None
    variables: ThemeVariables
    preview_url: Optional[HttpUrl] = None
    downloads: int = 0
    rating: float = 0.0
    tags: List[str] = []

class ThemeListResponse(Schema):
    themes: List[Theme]
    total: int
    page: int
    page_size: int
```

---

## 4. Lit Component Design

### 4.1 Base Component Pattern

```typescript
// File: somaAgent01/ui/frontend/src/components/eog-button.ts

import { LitElement, html, css } from 'lit';
import { customElement, property } from 'lit/decorators.js';

@customElement('eog-button')
export class EogButton extends LitElement {
  static styles = css`
    :host {
      display: inline-block;
    }
    
    button {
      padding: var(--eog-spacing-sm) var(--eog-spacing-md);
      border-radius: var(--eog-radius-md);
      border: 1px solid var(--eog-border-color);
      background: var(--eog-surface);
      color: var(--eog-text-main);
      font-family: var(--eog-font-sans);
      font-size: var(--eog-text-sm);
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s ease;
    }
    
    button:hover:not(:disabled) {
      background: var(--eog-surface-hover);
      border-color: var(--eog-border-hover);
    }
    
    button:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
    
    button.primary {
      background: var(--eog-accent);
      color: white;
      border-color: var(--eog-accent);
    }
    
    button.danger {
      background: var(--eog-danger);
      color: white;
      border-color: var(--eog-danger);
    }
  `;

  @property({ type: String }) variant: 'default' | 'primary' | 'danger' = 'default';
  @property({ type: Boolean }) disabled = false;
  @property({ type: Boolean }) loading = false;

  render() {
    return html`
      <button
        class=${this.variant}
        ?disabled=${this.disabled || this.loading}
        @click=${this._handleClick}
      >
        ${this.loading ? html`<eog-spinner size="sm"></eog-spinner>` : ''}
        <slot></slot>
      </button>
    `;
  }

  private _handleClick(e: Event) {
    if (!this.disabled && !this.loading) {
      this.dispatchEvent(new CustomEvent('eog-click', {
        bubbles: true,
        composed: true,
        detail: { originalEvent: e }
      }));
    }
  }
}

declare global {
  interface HTMLElementTagNameMap {
    'eog-button': EogButton;
  }
}
```

### 4.2 Store Pattern (Lit Context)

```typescript
// File: somaAgent01/ui/frontend/src/stores/mode-store.ts

import { createContext } from '@lit/context';
import { LitElement, html } from 'lit';
import { customElement, property } from 'lit/decorators.js';
import { provide } from '@lit/context';

export type AgentMode = 'STD' | 'TRN' | 'ADM' | 'DEV' | 'RO' | 'DGR';

export interface ModeState {
  current: AgentMode;
  available: AgentMode[];
  loading: boolean;
  error: string | null;
}

export const modeContext = createContext<ModeState>('mode-state');

@customElement('eog-mode-provider')
export class EogModeProvider extends LitElement {
  @provide({ context: modeContext })
  @property({ attribute: false })
  state: ModeState = {
    current: 'STD',
    available: ['STD'],
    loading: false,
    error: null,
  };

  async setMode(mode: AgentMode): Promise<void> {
    this.state = { ...this.state, loading: true, error: null };
    
    try {
      const response = await fetch('/api/v2/modes/current', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode }),
      });
      
      if (!response.ok) {
        throw new Error(`Failed to set mode: ${response.status}`);
      }
      
      const data = await response.json();
      this.state = { ...this.state, current: data.mode, loading: false };
      
      // Dispatch event for WebSocket sync
      this.dispatchEvent(new CustomEvent('mode-changed', {
        bubbles: true,
        composed: true,
        detail: { mode: data.mode }
      }));
    } catch (error) {
      this.state = { ...this.state, loading: false, error: String(error) };
    }
  }

  render() {
    return html`<slot></slot>`;
  }
}
```

### 4.3 API Client Service

```typescript
// File: somaAgent01/ui/frontend/src/services/api-client.ts

export interface ApiClientConfig {
  baseUrl: string;
  timeout: number;
  retries: number;
}

export class ApiClient {
  private config: ApiClientConfig;
  private token: string | null = null;

  constructor(config: Partial<ApiClientConfig> = {}) {
    this.config = {
      baseUrl: config.baseUrl ?? '/api/v2',
      timeout: config.timeout ?? 30000,
      retries: config.retries ?? 3,
    };
  }

  setToken(token: string): void {
    this.token = token;
  }

  async request<T>(
    method: string,
    path: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.config.baseUrl}${path}`;
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...(this.token ? { Authorization: `Bearer ${this.token}` } : {}),
      ...(options.headers ?? {}),
    };

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.config.timeout);

    try {
      const response = await fetch(url, {
        method,
        headers,
        signal: controller.signal,
        ...options,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new ApiError(response.status, error.detail ?? 'Request failed');
      }

      return response.json();
    } catch (error) {
      clearTimeout(timeoutId);
      if (error instanceof ApiError) throw error;
      throw new ApiError(0, String(error));
    }
  }

  get<T>(path: string): Promise<T> {
    return this.request<T>('GET', path);
  }

  post<T>(path: string, body: unknown): Promise<T> {
    return this.request<T>('POST', path, { body: JSON.stringify(body) });
  }

  put<T>(path: string, body: unknown): Promise<T> {
    return this.request<T>('PUT', path, { body: JSON.stringify(body) });
  }

  delete<T>(path: string): Promise<T> {
    return this.request<T>('DELETE', path);
  }
}

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

export const apiClient = new ApiClient();
```


---

## 5. Voice System Design

### 5.1 Voice Provider Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         VOICE PROVIDER ABSTRACTION                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                      VoiceProviderInterface                          │   │
│   │  + start_session() -> SessionId                                      │   │
│   │  + stop_session(session_id)                                          │   │
│   │  + transcribe(audio_bytes) -> str                                    │   │
│   │  + synthesize(text) -> audio_bytes                                   │   │
│   │  + is_available() -> bool                                            │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                    ▲                              ▲                          │
│                    │                              │                          │
│   ┌────────────────┴────────────┐  ┌─────────────┴──────────────────┐      │
│   │     LocalVoiceProvider      │  │   AgentVoiceBoxProvider        │      │
│   │  - whisper_model            │  │  - ws_connection               │      │
│   │  - kokoro_model             │  │  - api_token                   │      │
│   │  - vad_detector             │  │  - realtime_session            │      │
│   │  - audio_capture            │  │  - turn_detector               │      │
│   └─────────────────────────────┘  └────────────────────────────────┘      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Local Voice Implementation

```python
# File: somaAgent01/ui/backend/voice/local_provider.py

from dataclasses import dataclass
from typing import Optional
import numpy as np

@dataclass
class LocalVoiceConfig:
    stt_engine: str = "whisper"
    stt_model_size: str = "base"
    tts_engine: str = "kokoro"
    tts_voice: str = "am_onyx"
    tts_speed: float = 1.0
    vad_threshold: float = 0.5
    language: str = "en-US"
    sample_rate: int = 24000

class LocalVoiceProvider:
    """Local voice provider using Whisper STT + Kokoro TTS.
    
    NOTE: Does NOT support real-time speech-on-speech.
    For speech-on-speech, use AgentVoiceBoxProvider.
    """
    
    def __init__(self, config: LocalVoiceConfig):
        self.config = config
        self._whisper_model = None
        self._kokoro_model = None
        self._vad = None
    
    async def initialize(self) -> None:
        """Load models based on detected hardware (CPU/GPU)."""
        import torch
        device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Load Whisper
        if self.config.stt_engine == "whisper":
            import whisper
            self._whisper_model = whisper.load_model(
                self.config.stt_model_size,
                device=device
            )
        
        # Load Kokoro
        if self.config.tts_engine == "kokoro":
            from kokoro import KokoroTTS
            self._kokoro_model = KokoroTTS(
                voice=self.config.tts_voice,
                device=device
            )
    
    async def transcribe(self, audio: np.ndarray) -> str:
        """Transcribe audio to text using Whisper."""
        result = self._whisper_model.transcribe(
            audio,
            language=self.config.language[:2]
        )
        return result["text"]
    
    async def synthesize(self, text: str) -> np.ndarray:
        """Synthesize text to audio using Kokoro."""
        audio = self._kokoro_model.generate(
            text,
            speed=self.config.tts_speed
        )
        return audio
    
    def is_available(self) -> bool:
        return self._whisper_model is not None and self._kokoro_model is not None
```


### 5.3 AgentVoiceBox Provider Implementation

```python
# File: somaAgent01/ui/backend/voice/agentvoicebox_provider.py

from dataclasses import dataclass
from typing import Optional, Callable
import asyncio
import websockets
import json

@dataclass
class AgentVoiceBoxConfig:
    base_url: str = ""
    ws_url: str = ""
    api_token: str = ""
    model: str = "ovos-voice-1"
    voice: str = "default"
    turn_detection: bool = True
    input_audio_format: str = "pcm16"
    output_audio_format: str = "pcm16"

class AgentVoiceBoxProvider:
    """AgentVoiceBox provider for full speech-on-speech capability.
    
    Connects to AgentVoiceBox server via WebSocket for real-time
    bidirectional audio streaming with OpenAI Realtime API compatibility.
    """
    
    def __init__(self, config: AgentVoiceBoxConfig):
        self.config = config
        self._ws: Optional[websockets.WebSocketClientProtocol] = None
        self._session_id: Optional[str] = None
        self._on_transcription: Optional[Callable] = None
        self._on_audio: Optional[Callable] = None
    
    async def connect(self) -> str:
        """Establish WebSocket connection to AgentVoiceBox."""
        headers = {"Authorization": f"Bearer {self.config.api_token}"}
        self._ws = await websockets.connect(
            self.config.ws_url,
            extra_headers=headers
        )
        
        # Send session.create
        await self._ws.send(json.dumps({
            "type": "session.create",
            "session": {
                "model": self.config.model,
                "voice": self.config.voice,
                "turn_detection": {"type": "server_vad"} if self.config.turn_detection else None,
                "input_audio_format": self.config.input_audio_format,
                "output_audio_format": self.config.output_audio_format,
            }
        }))
        
        # Wait for session.created
        response = json.loads(await self._ws.recv())
        if response["type"] == "session.created":
            self._session_id = response["session"]["id"]
            return self._session_id
        raise ConnectionError(f"Failed to create session: {response}")
    
    async def send_audio(self, audio_base64: str) -> None:
        """Send audio chunk to AgentVoiceBox."""
        await self._ws.send(json.dumps({
            "type": "input_audio_buffer.append",
            "audio": audio_base64
        }))
    
    async def listen(self) -> None:
        """Listen for events from AgentVoiceBox."""
        async for message in self._ws:
            event = json.loads(message)
            event_type = event.get("type")
            
            if event_type == "conversation.item.input_audio_transcription.completed":
                if self._on_transcription:
                    await self._on_transcription(event["transcript"])
            
            elif event_type == "response.audio.delta":
                if self._on_audio:
                    await self._on_audio(event["delta"])
    
    async def disconnect(self) -> None:
        """Close WebSocket connection."""
        if self._ws:
            await self._ws.close()
            self._ws = None
            self._session_id = None
```


---

## 6. AgentSkin Theme System Design

### 6.1 Theme Manager Implementation

```typescript
// File: somaAgent01/ui/frontend/src/services/theme-manager.ts

import { Theme, ThemeVariables } from '../types/theme';

const THEME_STORAGE_KEY = 'eog-active-theme';
const CSS_VAR_PREFIX = '--eog-';

export class ThemeManager {
  private activeTheme: Theme | null = null;
  private root: HTMLElement;

  constructor() {
    this.root = document.documentElement;
  }

  async loadTheme(theme: Theme): Promise<void> {
    // Validate theme
    this.validateTheme(theme);
    
    // Apply CSS variables
    this.applyVariables(theme.variables);
    
    // Store active theme
    this.activeTheme = theme;
    localStorage.setItem(THEME_STORAGE_KEY, JSON.stringify(theme));
    
    // Dispatch event
    window.dispatchEvent(new CustomEvent('theme-changed', { detail: theme }));
  }

  private validateTheme(theme: Theme): void {
    // Check required variables (26 minimum)
    const required = [
      'bg_void', 'glass_surface', 'glass_border', 'text_main', 'text_dim',
      'accent_primary', 'accent_secondary', 'accent_success', 'accent_warning', 'accent_danger',
      'shadow_soft', 'radius_sm', 'radius_md', 'radius_lg', 'radius_full',
      'spacing_xs', 'spacing_sm', 'spacing_md', 'spacing_lg', 'spacing_xl',
      'font_sans', 'font_mono', 'text_xs', 'text_sm', 'text_base', 'text_lg'
    ];
    
    for (const key of required) {
      if (!(key in theme.variables)) {
        throw new Error(`Missing required theme variable: ${key}`);
      }
    }
    
    // Security: Check for url() in values (XSS prevention)
    for (const [key, value] of Object.entries(theme.variables)) {
      if (typeof value === 'string' && value.includes('url(')) {
        throw new Error(`Security violation: url() not allowed in theme variable: ${key}`);
      }
    }
    
    // Validate contrast ratios (WCAG AA)
    this.validateContrast(theme.variables);
  }

  private validateContrast(vars: ThemeVariables): void {
    // Calculate contrast ratio between text and background
    const bgColor = this.parseColor(vars.bg_void);
    const textColor = this.parseColor(vars.text_main);
    const ratio = this.contrastRatio(bgColor, textColor);
    
    if (ratio < 4.5) {
      console.warn(`Theme contrast ratio ${ratio.toFixed(2)} is below WCAG AA (4.5:1)`);
    }
  }

  private applyVariables(variables: ThemeVariables): void {
    for (const [key, value] of Object.entries(variables)) {
      const cssVar = `${CSS_VAR_PREFIX}${key.replace(/_/g, '-')}`;
      this.root.style.setProperty(cssVar, value);
    }
  }

  // Color utility methods
  private parseColor(color: string): [number, number, number] { /* ... */ }
  private luminance(r: number, g: number, b: number): number { /* ... */ }
  private contrastRatio(c1: [number, number, number], c2: [number, number, number]): number { /* ... */ }
}

export const themeManager = new ThemeManager();
```


### 6.2 Default Themes

```json
// File: somaAgent01/ui/frontend/src/styles/themes/midnight-dark.json
{
  "name": "Midnight Dark",
  "version": "1.0.0",
  "author": "SomaAgent Team",
  "description": "Dark theme with blue accents and glassmorphism",
  "category": "Professional",
  "tags": ["dark", "glassmorphism", "professional"],
  "variables": {
    "bg_void": "#0f172a",
    "glass_surface": "rgba(30, 41, 59, 0.85)",
    "glass_border": "rgba(255, 255, 255, 0.05)",
    "text_main": "#e2e8f0",
    "text_dim": "#64748b",
    "accent_primary": "#3b82f6",
    "accent_secondary": "#8b5cf6",
    "accent_success": "#22c55e",
    "accent_warning": "#f59e0b",
    "accent_danger": "#ef4444",
    "shadow_soft": "0 10px 40px -10px rgba(0, 0, 0, 0.5)",
    "radius_sm": "4px",
    "radius_md": "8px",
    "radius_lg": "16px",
    "radius_full": "9999px",
    "spacing_xs": "4px",
    "spacing_sm": "8px",
    "spacing_md": "16px",
    "spacing_lg": "24px",
    "spacing_xl": "32px",
    "font_sans": "'Space Grotesk', sans-serif",
    "font_mono": "'JetBrains Mono', monospace",
    "text_xs": "10px",
    "text_sm": "12px",
    "text_base": "14px",
    "text_lg": "16px",
    "text_xl": "20px"
  }
}
```

---

## 7. WebSocket Real-Time Design

### 7.1 Django Channels Consumer

```python
# File: somaAgent01/ui/backend/realtime/consumers.py

import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async

class EventConsumer(AsyncJsonWebsocketConsumer):
    """WebSocket consumer for real-time events."""
    
    async def connect(self):
        # Authenticate
        token = self.scope.get("query_string", b"").decode()
        user = await self.authenticate(token)
        if not user:
            await self.close(code=4001)
            return
        
        self.user = user
        self.tenant_id = user.tenant_id
        self.group_name = f"tenant_{self.tenant_id}"
        
        # Join tenant group
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        
        # Send initial state
        await self.send_json({
            "type": "connection.established",
            "user_id": str(user.id),
            "tenant_id": str(self.tenant_id)
        })
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
    
    async def receive_json(self, content):
        event_type = content.get("type")
        
        if event_type == "ping":
            await self.send_json({"type": "pong"})
        elif event_type == "mode.change":
            await self.handle_mode_change(content)
        elif event_type == "settings.update":
            await self.handle_settings_update(content)
    
    # Event handlers for group broadcasts
    async def mode_changed(self, event):
        await self.send_json(event)
    
    async def settings_changed(self, event):
        await self.send_json(event)
    
    async def theme_changed(self, event):
        await self.send_json(event)
    
    async def voice_event(self, event):
        await self.send_json(event)
```


---

## 5. Django Models

### 5.1 Core Models

```python
# File: somaAgent01/ui/backend/core/models/tenant.py

from django.db import models
from django.contrib.postgres.fields import ArrayField
import uuid

class Tenant(models.Model):
    """Multi-tenant organization model."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=128, unique=True)
    display_name = models.CharField(max_length=256)
    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True, related_name='children'
    )
    settings = models.JSONField(default=dict)
    feature_flags = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'eog_tenants'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['parent']),
        ]


class User(models.Model):
    """User model with tenant association."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='users')
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=64, unique=True)
    display_name = models.CharField(max_length=128)
    avatar_url = models.URLField(null=True, blank=True)
    roles = ArrayField(models.CharField(max_length=32), default=list)
    preferences = models.JSONField(default=dict)
    last_mode = models.CharField(max_length=8, default='STD')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'eog_users'
        indexes = [
            models.Index(fields=['tenant', 'email']),
            models.Index(fields=['username']),
        ]
```

### 5.2 Settings Models

```python
# File: somaAgent01/ui/backend/core/models/settings.py

from django.db import models
import uuid

class SettingsCategory(models.TextChoices):
    AGENT = 'agent', 'Agent'
    EXTERNAL = 'external', 'External'
    CONNECTIVITY = 'connectivity', 'Connectivity'
    SYSTEM = 'system', 'System'


class TenantSettings(models.Model):
    """Tenant-level settings storage."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('Tenant', on_delete=models.CASCADE, related_name='settings_entries')
    category = models.CharField(max_length=32, choices=SettingsCategory.choices)
    key = models.CharField(max_length=128)
    value = models.JSONField()
    is_secret = models.BooleanField(default=False)
    version = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'eog_tenant_settings'
        unique_together = ['tenant', 'category', 'key']
        indexes = [
            models.Index(fields=['tenant', 'category']),
        ]


class UserSettings(models.Model):
    """User-level settings (preferences)."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='settings_entries')
    key = models.CharField(max_length=128)
    value = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'eog_user_settings'
        unique_together = ['user', 'key']
```

### 5.3 Theme Models

```python
# File: somaAgent01/ui/backend/core/models/theme.py

from django.db import models
from django.contrib.postgres.fields import ArrayField
import uuid

class ThemeCategory(models.TextChoices):
    PROFESSIONAL = 'Professional', 'Professional'
    CREATIVE = 'Creative', 'Creative'
    DEVELOPER = 'Developer', 'Developer'
    GAMING = 'Gaming', 'Gaming'
    ACCESSIBILITY = 'Accessibility', 'Accessibility'


class Theme(models.Model):
    """AgentSkin theme storage."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('Tenant', on_delete=models.CASCADE, related_name='themes')
    owner = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, related_name='themes')
    name = models.CharField(max_length=64)
    version = models.CharField(max_length=16)
    author = models.CharField(max_length=128)
    description = models.TextField(null=True, blank=True)
    category = models.CharField(max_length=32, choices=ThemeCategory.choices)
    tags = ArrayField(models.CharField(max_length=32), default=list)
    variables = models.JSONField()  # 26+ CSS custom properties
    preview_url = models.URLField(null=True, blank=True)
    downloads = models.IntegerField(default=0)
    rating = models.FloatField(default=0.0)
    is_default = models.BooleanField(default=False)
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'eog_themes'
        unique_together = ['tenant', 'name', 'version']
        indexes = [
            models.Index(fields=['tenant', 'category']),
            models.Index(fields=['is_public']),
        ]
```


### 7.2 Frontend WebSocket Client

```typescript
// File: somaAgent01/ui/frontend/src/services/websocket-client.ts

type EventHandler = (event: any) => void;

export class WebSocketClient {
  private ws: WebSocket | null = null;
  private url: string;
  private token: string;
  private handlers: Map<string, Set<EventHandler>> = new Map();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 10;
  private heartbeatInterval: number | null = null;

  constructor(url: string, token: string) {
    this.url = url;
    this.token = token;
  }

  connect(): void {
    this.ws = new WebSocket(`${this.url}?token=${this.token}`);
    
    this.ws.onopen = () => {
      this.reconnectAttempts = 0;
      this.startHeartbeat();
      this.emit('connection.established', {});
    };
    
    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.emit(data.type, data);
    };
    
    this.ws.onclose = (event) => {
      this.stopHeartbeat();
      if (event.code !== 1000) {
        this.reconnect();
      }
    };
    
    this.ws.onerror = () => {
      this.emit('error', { message: 'WebSocket error' });
    };
  }

  private reconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      this.emit('error', { message: 'Max reconnect attempts reached' });
      return;
    }
    
    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
    this.reconnectAttempts++;
    
    setTimeout(() => this.connect(), delay);
  }

  private startHeartbeat(): void {
    this.heartbeatInterval = window.setInterval(() => {
      this.send({ type: 'ping' });
    }, 20000);
  }

  private stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  on(eventType: string, handler: EventHandler): void {
    if (!this.handlers.has(eventType)) {
      this.handlers.set(eventType, new Set());
    }
    this.handlers.get(eventType)!.add(handler);
  }

  off(eventType: string, handler: EventHandler): void {
    this.handlers.get(eventType)?.delete(handler);
  }

  private emit(eventType: string, data: any): void {
    this.handlers.get(eventType)?.forEach(handler => handler(data));
    this.handlers.get('*')?.forEach(handler => handler({ type: eventType, ...data }));
  }

  send(data: any): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }

  disconnect(): void {
    this.stopHeartbeat();
    this.ws?.close(1000);
    this.ws = null;
  }
}
```

---

## 8. SpiceDB Integration Design

### 8.1 Permission Client

```python
# File: somaAgent01/ui/backend/permissions/client.py

from typing import Optional
from authzed.api.v1 import Client, CheckPermissionRequest, CheckPermissionResponse
from authzed.api.v1 import ObjectReference, SubjectReference
import grpc

class SpiceDBClient:
    """SpiceDB client for permission checks."""
    
    def __init__(self, endpoint: str, token: str):
        self.endpoint = endpoint
        self.token = token
        self._client: Optional[Client] = None
    
    def connect(self) -> None:
        credentials = grpc.ssl_channel_credentials()
        self._client = Client(
            self.endpoint,
            credentials,
            options=[("authorization", f"Bearer {self.token}")]
        )
    
    async def check_permission(
        self,
        resource_type: str,
        resource_id: str,
        permission: str,
        subject_type: str,
        subject_id: str
    ) -> bool:
        """Check if subject has permission on resource."""
        request = CheckPermissionRequest(
            resource=ObjectReference(
                object_type=resource_type,
                object_id=resource_id
            ),
            permission=permission,
            subject=SubjectReference(
                object=ObjectReference(
                    object_type=subject_type,
                    object_id=subject_id
                )
            )
        )
        
        response = await self._client.CheckPermission(request)
        return response.permissionship == CheckPermissionResponse.PERMISSIONSHIP_HAS_PERMISSION
```

### 5.4 Voice Configuration Models

```python
# File: somaAgent01/ui/backend/core/models/voice.py

from django.db import models
import uuid

class VoiceProvider(models.TextChoices):
    DISABLED = 'disabled', 'Disabled'
    LOCAL = 'local', 'Local (Whisper/Kokoro)'
    AGENTVOICEBOX = 'agentvoicebox', 'AgentVoiceBox'


class VoiceConfig(models.Model):
    """Voice configuration per tenant."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.OneToOneField('Tenant', on_delete=models.CASCADE, related_name='voice_config')
    enabled = models.BooleanField(default=False)
    provider = models.CharField(max_length=32, choices=VoiceProvider.choices, default='disabled')
    
    # Local Voice Settings
    stt_engine = models.CharField(max_length=32, default='whisper')
    stt_model_size = models.CharField(max_length=16, default='base')
    tts_engine = models.CharField(max_length=32, default='kokoro')
    tts_voice = models.CharField(max_length=64, default='am_onyx')
    tts_speed = models.FloatField(default=1.0)
    vad_threshold = models.FloatField(default=0.5)
    language = models.CharField(max_length=16, default='en-US')
    
    # AgentVoiceBox Settings
    agentvoicebox_url = models.URLField(null=True, blank=True)
    agentvoicebox_ws_url = models.URLField(null=True, blank=True)
    agentvoicebox_token = models.CharField(max_length=256, null=True, blank=True)
    agentvoicebox_model = models.CharField(max_length=64, default='ovos-voice-1')
    
    # Audio Settings
    audio_input_device = models.IntegerField(default=0)
    audio_output_device = models.IntegerField(default=0)
    sample_rate = models.IntegerField(default=24000)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'eog_voice_config'


class FeatureFlag(models.Model):
    """Feature flags per tenant."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('Tenant', on_delete=models.CASCADE, related_name='feature_flags_entries')
    name = models.CharField(max_length=64)
    enabled = models.BooleanField(default=False)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'eog_feature_flags'
        unique_together = ['tenant', 'name']


class AuditLog(models.Model):
    """Audit trail for all actions."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('Tenant', on_delete=models.CASCADE, related_name='audit_logs')
    user = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, related_name='audit_logs')
    action = models.CharField(max_length=64)
    resource_type = models.CharField(max_length=64)
    resource_id = models.CharField(max_length=128, null=True, blank=True)
    old_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'eog_audit_logs'
        indexes = [
            models.Index(fields=['tenant', 'created_at']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['action']),
        ]
```

---

## 6. API Endpoint Schemas

### 6.1 Authentication Endpoints

```python
# File: somaAgent01/ui/backend/api/endpoints/auth.py

from ninja import Router, Schema
from typing import Optional
from datetime import datetime

router = Router()

class LoginRequest(Schema):
    username: str
    password: str
    tenant_id: Optional[str] = None

class LoginResponse(Schema):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int
    user: "UserResponse"

class UserResponse(Schema):
    id: str
    email: str
    username: str
    display_name: str
    avatar_url: Optional[str]
    roles: list[str]
    tenant_id: str
    last_mode: str

class RefreshRequest(Schema):
    refresh_token: str

@router.post("/login", response=LoginResponse)
async def login(request, payload: LoginRequest):
    """Authenticate user and return tokens."""
    pass

@router.post("/refresh", response=LoginResponse)
async def refresh(request, payload: RefreshRequest):
    """Refresh access token."""
    pass

@router.post("/logout")
async def logout(request):
    """Invalidate tokens."""
    pass

@router.get("/me", response=UserResponse)
async def get_current_user(request):
    """Get current authenticated user."""
    pass
```


### 8.2 Permission Decorator

```python
# File: somaAgent01/ui/backend/permissions/decorators.py

from functools import wraps
from ninja import Router
from django.http import HttpRequest
from .client import spicedb_client

def require_permission(resource_type: str, permission: str):
    """Decorator to require SpiceDB permission check."""
    def decorator(func):
        @wraps(func)
        async def wrapper(request: HttpRequest, *args, **kwargs):
            user = request.auth
            resource_id = kwargs.get('id') or kwargs.get('resource_id')
            
            has_permission = await spicedb_client.check_permission(
                resource_type=resource_type,
                resource_id=str(resource_id),
                permission=permission,
                subject_type="user",
                subject_id=str(user.id)
            )
            
            if not has_permission:
                return {"error": "Permission denied"}, 403
            
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator

# Usage example:
# @router.get("/settings/{id}")
# @require_permission("setting_section", "view")
# async def get_settings(request, id: str):
#     ...
```

---

## 9. Database Models

### 9.1 Django Models

```python
# File: somaAgent01/ui/backend/core/models/tenant.py

from django.db import models
import uuid

class Tenant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'eog_tenants'

class User(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    email = models.EmailField()
    display_name = models.CharField(max_length=255)
    current_mode = models.CharField(max_length=10, default='STD')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'eog_users'
        unique_together = ['tenant', 'email']

class Settings(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    tab = models.CharField(max_length=50)
    data = models.JSONField(default=dict)
    version = models.IntegerField(default=1)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    
    class Meta:
        db_table = 'eog_settings'
        unique_together = ['tenant', 'tab']

class Theme(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    version = models.CharField(max_length=50)
    author = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    variables = models.JSONField()
    is_default = models.BooleanField(default=False)
    downloads = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'eog_themes'

class AuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=100)
    resource_type = models.CharField(max_length=100)
    resource_id = models.CharField(max_length=255)
    details = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField(null=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'eog_audit_logs'
        indexes = [
            models.Index(fields=['tenant', 'created_at']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['action']),
        ]
```


---

## 10. Deployment Architecture

### 10.1 Docker Compose (Development)

```yaml
# File: somaAgent01/ui/docker-compose.yml

version: '3.8'

services:
  eog-backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8020:8020"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@postgres:5432/eog
      - REDIS_URL=redis://redis:6379/0
      - SPICEDB_ENDPOINT=spicedb:50051
      - SPICEDB_TOKEN=${SPICEDB_TOKEN}
    depends_on:
      - postgres
      - redis
      - spicedb

  eog-frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - API_URL=http://eog-backend:8020

  postgres:
    image: postgres:16
    environment:
      - POSTGRES_DB=eog
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

  spicedb:
    image: authzed/spicedb:latest
    command: serve
    environment:
      - SPICEDB_GRPC_PRESHARED_KEY=${SPICEDB_TOKEN}
      - SPICEDB_DATASTORE_ENGINE=postgres
      - SPICEDB_DATASTORE_CONN_URI=postgresql://postgres:postgres@postgres:5432/spicedb
    ports:
      - "50051:50051"
    depends_on:
      - postgres

volumes:
  postgres_data:
  redis_data:
```

### 10.2 Kubernetes Deployment (Production)

```yaml
# File: somaAgent01/ui/k8s/deployment.yaml

apiVersion: apps/v1
kind: Deployment
metadata:
  name: eog-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: eog-backend
  template:
    metadata:
      labels:
        app: eog-backend
    spec:
      containers:
        - name: eog-backend
          image: somaagent/eog-backend:latest
          ports:
            - containerPort: 8020
          resources:
            requests:
              memory: "512Mi"
              cpu: "500m"
            limits:
              memory: "2Gi"
              cpu: "2000m"
          livenessProbe:
            httpGet:
              path: /api/v2/health
              port: 8020
            initialDelaySeconds: 10
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /api/v2/health
              port: 8020
            initialDelaySeconds: 5
            periodSeconds: 5
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: eog-backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: eog-backend
  minReplicas: 3
  maxReplicas: 100
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
```

---

## 11. Observability Design

### 11.1 Prometheus Metrics

```python
# File: somaAgent01/ui/backend/observability/metrics.py

from prometheus_client import Counter, Histogram, Gauge

# Request metrics
REQUEST_COUNT = Counter(
    'eog_request_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'eog_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint'],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
)

# WebSocket metrics
WS_CONNECTIONS = Gauge(
    'eog_websocket_connections',
    'Active WebSocket connections',
    ['tenant_id']
)

# Permission metrics
PERMISSION_CHECKS = Counter(
    'eog_permission_checks_total',
    'Total permission checks',
    ['resource_type', 'permission', 'result']
)

PERMISSION_DURATION = Histogram(
    'eog_permission_check_duration_seconds',
    'Permission check duration',
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1]
)

# Theme metrics
THEME_LOADS = Counter(
    'eog_theme_loads_total',
    'Total theme loads',
    ['theme_id']
)

# Mode metrics
MODE_TRANSITIONS = Counter(
    'eog_mode_transitions_total',
    'Total mode transitions',
    ['from_mode', 'to_mode']
)

# Voice metrics
VOICE_SESSIONS = Counter(
    'eog_voice_sessions_total',
    'Total voice sessions',
    ['provider']
)

VOICE_LATENCY = Histogram(
    'eog_voice_latency_seconds',
    'Voice processing latency',
    ['operation'],  # transcribe, synthesize
    buckets=[0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
)
```

---

## 12. Security Design

### 12.1 Authentication Middleware

```python
# File: somaAgent01/ui/backend/api/middleware/auth.py

from ninja.security import HttpBearer
from django.http import HttpRequest
import jwt
from datetime import datetime

class JWTAuth(HttpBearer):
    def authenticate(self, request: HttpRequest, token: str):
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET,
                algorithms=["HS256"]
            )
            
            # Check expiration
            if datetime.utcnow().timestamp() > payload.get("exp", 0):
                return None
            
            # Get user
            user = User.objects.get(id=payload["sub"])
            request.tenant_id = payload.get("tenant_id")
            
            return user
        except (jwt.InvalidTokenError, User.DoesNotExist):
            return None
```

---

**Document Status:** COMPLETE

**Implements Requirements:**
- REQ-1 through REQ-25 from requirements.md
- All SRS sections 1-13

**Next Steps:**
1. Create tasks.md with implementation plan
2. Begin Phase 1 implementation (Django Ninja parallel build)


---

## 13. Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Theme Validation Completeness

*For any* theme JSON object submitted to the Theme_System, the validation function SHALL:
- Verify the presence of all 26 required CSS custom property variables
- Reject any theme containing `url()` in CSS values (XSS prevention)
- Validate WCAG AA contrast ratio (≥4.5:1) between text and background colors
- Reject themes loaded via HTTP (require HTTPS only)

**Validates: Requirements 4.1, 4.3, 4.4, 4.6, 4.8, 4.10**

---

### Property 2: Permission Enforcement Consistency

*For any* user action request and any resource, the Permission_System SHALL:
- Return the same permission decision for identical (user, resource, action) tuples within the cache TTL (60s)
- Deny access when SpiceDB is unavailable (fail-closed)
- Enforce tenant isolation such that users cannot access resources belonging to other tenants
- Propagate role changes to all cached decisions within 5 seconds

**Validates: Requirements 3.4, 3.5, 3.6, 3.7, 3.9, 8.5, 8.6, 11.4, 11.9**

---

### Property 3: Real-time Event Delivery

*For any* server-side event (mode.changed, settings.changed, theme.changed, voice.*), the Realtime_System SHALL:
- Deliver the event to all subscribed clients within 100ms
- Maintain heartbeat at 20-second intervals
- Reconnect with exponential backoff when connection drops
- Replay missed events upon client reconnection
- Authenticate all WebSocket connections via Bearer token

**Validates: Requirements 10.2, 10.4, 10.5, 10.6, 10.8, 10.10**

---

### Property 4: Settings Persistence Round-Trip

*For any* valid settings object, storing then retrieving the settings SHALL produce an equivalent object, where:
- Settings are persisted to PostgreSQL immediately upon modification
- API keys are stored in Vault (not PostgreSQL)
- Optimistic locking via version field prevents concurrent edit conflicts
- Settings changes trigger agent config reload

**Validates: Requirements 9.2, 9.3, 9.6, 9.11**

---

### Property 5: Mode State Consistency

*For any* mode transition request, the Mode_Manager SHALL:
- Verify user has permission for target mode via SpiceDB before transition
- Emit mode.changed WebSocket event after successful transition
- Log all mode transitions to audit trail
- Persist mode preference per user in PostgreSQL
- Restore last permitted mode when session starts

**Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.8**

---

### Property 6: Tenant Data Isolation

*For any* database query and any tenant, the Multi_Tenancy system SHALL:
- Filter all results by tenant_id extracted from X-Tenant-Id header
- Prevent cross-tenant data access except for SYSADMIN role
- Log all cross-tenant access attempts to audit trail
- Cascade delete all tenant data when tenant is deleted
- Provision default roles and settings when tenant is created

**Validates: Requirements 11.1, 11.2, 11.3, 11.5, 11.6, 11.7, 11.8, 11.10**

---

### Property 7: Security Controls Enforcement

*For any* API request, the API_Security layer SHALL:
- Require Bearer token authentication (return 401 if missing/invalid)
- Enforce rate limiting (return 429 with Retry-After when exceeded)
- Validate all inputs against JSON Schema (return 400 for invalid)
- Reject SQL injection attempts (return 400)
- Sanitize and reject XSS payloads
- Set CSP headers on all responses
- Log all authentication failures to audit trail

**Validates: Requirements 12.1, 12.2, 12.3, 12.4, 12.5, 12.6, 12.7, 12.8, 12.9**

---

### Property 8: Voice Provider Selection Consistency

*For any* voice provider selection (local, agentvoicebox, disabled), the System SHALL:
- Use Local_Voice for STT/TTS when provider is "local"
- Use AgentVoiceBox for full speech-on-speech when provider is "agentvoicebox"
- Hide all voice UI elements when provider is "disabled"
- Show provider-specific configuration fields dynamically
- Validate new configuration when provider changes
- Emit settings.changed event when voice provider changes

**Validates: Requirements 7.2, 7.3, 7.4, 7.5, 7.6, 7.10**

---

### Property 9: Component Render Performance

*For any* Lit Web Component in the UI_Layer, rendering SHALL:
- Complete within 16ms (60fps) for all component state changes
- Apply theme variable changes within 50ms
- Use CSS Custom Properties for all themeable values
- Maintain Shadow DOM encapsulation

**Validates: Requirements 1.2, 1.4, 1.7, 1.10**

---

### Property 10: API Response Time SLA

*For any* API request under normal load, the Backend SHALL:
- Respond within 50ms (p95)
- Complete permission checks within 10ms (p95)
- Use Pydantic schemas for all request/response validation

**Validates: Requirements 2.3, 2.10, 3.2**

---

## 14. Error Handling

### 14.1 Error Categories

| Category | HTTP Status | Handling |
|----------|-------------|----------|
| Authentication | 401 | Redirect to login, clear token |
| Authorization | 403 | Show permission denied toast |
| Validation | 400 | Show field-level errors |
| Rate Limit | 429 | Show retry countdown |
| Server Error | 500 | Show generic error, log details |
| Network | 0 | Show offline indicator, retry |

### 14.2 Error Response Schema

```python
class ErrorResponse(Schema):
    error: str           # Error code (e.g., "PERMISSION_DENIED")
    message: str         # Human-readable message
    details: dict = {}   # Additional context
    trace_id: str        # Request trace ID for debugging
```

### 14.3 Frontend Error Handling

```typescript
// Global error handler
window.addEventListener('unhandledrejection', (event) => {
  const error = event.reason;
  if (error instanceof ApiError) {
    switch (error.status) {
      case 401:
        authStore.logout();
        router.navigate('/login');
        break;
      case 403:
        toastStore.show({ type: 'error', message: 'Permission denied' });
        break;
      case 429:
        toastStore.show({ type: 'warning', message: `Rate limited. Retry in ${error.retryAfter}s` });
        break;
      default:
        toastStore.show({ type: 'error', message: error.message });
    }
  }
});
```

---

## 15. Testing Strategy

### 15.1 Dual Testing Approach

The Eye of God UIX uses both unit tests and property-based tests:

- **Unit tests**: Verify specific examples, edge cases, and error conditions
- **Property tests**: Verify universal properties across all inputs using Hypothesis (Python) and fast-check (TypeScript)

### 15.2 Property-Based Testing Configuration

**Backend (Python):**
```python
# pytest.ini
[pytest]
addopts = --hypothesis-show-statistics
hypothesis_profile = ci

# conftest.py
from hypothesis import settings, Verbosity

settings.register_profile("ci", max_examples=100, verbosity=Verbosity.verbose)
settings.register_profile("dev", max_examples=10)
```

**Frontend (TypeScript):**
```typescript
// vitest.config.ts
export default defineConfig({
  test: {
    include: ['**/*.property.test.ts'],
    testTimeout: 30000, // Property tests may take longer
  },
});
```

### 15.3 Test Organization

```
ui/
├── backend/
│   └── tests/
│       ├── unit/
│       │   ├── test_auth.py
│       │   ├── test_settings.py
│       │   └── test_themes.py
│       └── property/
│           ├── test_theme_validation.py      # Property 1
│           ├── test_permission_enforcement.py # Property 2
│           ├── test_tenant_isolation.py      # Property 6
│           └── test_security_controls.py     # Property 7
│
├── frontend/
│   └── src/
│       └── tests/
│           ├── unit/
│           │   ├── eog-button.test.ts
│           │   ├── eog-input.test.ts
│           │   └── auth-store.test.ts
│           └── property/
│               ├── theme-validation.property.test.ts  # Property 1
│               ├── event-delivery.property.test.ts    # Property 3
│               ├── voice-provider.property.test.ts    # Property 8
│               └── render-performance.property.test.ts # Property 9
```

### 15.4 Property Test Examples

**Property 1: Theme Validation (Python)**
```python
# Feature: eye-of-god-uix, Property 1: Theme Validation Completeness
# Validates: Requirements 4.1, 4.3, 4.4, 4.6, 4.8, 4.10

from hypothesis import given, strategies as st
from api.schemas.themes import Theme, validate_theme

@given(st.builds(Theme, variables=st.dictionaries(
    st.text(min_size=1, max_size=32),
    st.text(min_size=1, max_size=64)
)))
def test_theme_validation_rejects_incomplete_themes(theme):
    """For any theme missing required variables, validation SHALL fail."""
    required_vars = ['bg-void', 'text-main', ...]  # 26 required
    if not all(v in theme.variables for v in required_vars):
        result = validate_theme(theme)
        assert not result.valid
        assert 'Missing required variables' in result.errors
```

**Property 6: Tenant Isolation (Python)**
```python
# Feature: eye-of-god-uix, Property 6: Tenant Data Isolation
# Validates: Requirements 11.1, 11.2, 11.3, 11.5, 11.6, 11.7, 11.8, 11.10

from hypothesis import given, strategies as st

@given(
    tenant_a=st.uuids(),
    tenant_b=st.uuids(),
    resource_id=st.uuids()
)
def test_tenant_isolation_prevents_cross_tenant_access(tenant_a, tenant_b, resource_id):
    """For any two different tenants, user from tenant_a SHALL NOT access tenant_b resources."""
    if tenant_a != tenant_b:
        user = create_user(tenant_id=tenant_a)
        resource = create_resource(tenant_id=tenant_b, id=resource_id)
        
        with pytest.raises(PermissionDenied):
            access_resource(user, resource)
```

**Property 9: Component Render Performance (TypeScript)**
```typescript
// Feature: eye-of-god-uix, Property 9: Component Render Performance
// Validates: Requirements 1.2, 1.4, 1.7, 1.10

import { fc } from 'fast-check';
import { EogButton } from '../components/eog-button';

fc.assert(
  fc.property(
    fc.record({
      variant: fc.constantFrom('default', 'primary', 'danger'),
      disabled: fc.boolean(),
      loading: fc.boolean(),
    }),
    async (props) => {
      const el = document.createElement('eog-button') as EogButton;
      Object.assign(el, props);
      document.body.appendChild(el);
      
      const start = performance.now();
      await el.updateComplete;
      const duration = performance.now() - start;
      
      // Render must complete within 16ms (60fps)
      expect(duration).toBeLessThan(16);
      
      document.body.removeChild(el);
    }
  ),
  { numRuns: 100 }
);
```

---

**Document Status:** COMPLETE

**Implements Requirements:**
- REQ-1 through REQ-25 from requirements.md
- All SRS sections 1-13

**Correctness Properties:**
- 10 properties covering all testable acceptance criteria
- Property-based testing with Hypothesis (Python) and fast-check (TypeScript)
- Minimum 100 iterations per property test

