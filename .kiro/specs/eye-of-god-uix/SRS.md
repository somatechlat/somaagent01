# Eye of God UIX — Software Requirements Specification (SRS)

## Document Control

| Field | Value |
|-------|-------|
| **Document ID** | SA01-EOG-SRS-2025-12 |
| **Version** | 1.0 |
| **Date** | 2025-12-21 |
| **Status** | CANONICAL |
| **Classification** | ENTERPRISE |
| **Supersedes** | SA01-EOG-REQ-2025-12 (merged) |

---

## 1. Introduction

### 1.1 Purpose

This Software Requirements Specification (SRS) defines the complete requirements for the **Eye of God (EOG)** unified interface architecture for SomaAgent01. This document serves as the single source of truth for all UI/UX, API, permissions, settings, voice integration, and theming requirements.

### 1.2 Scope

EOG encompasses:
- **UI Layer**: Lit 3.x Web Components with Shadow DOM
- **API Layer**: Django Ninja async REST/WebSocket
- **MVC Layer**: Django 5.x with PostgreSQL
- **Permissions**: SpiceDB (Google Zanzibar model)
- **Theming**: AgentSkin system (REQUIRED)
- **Voice**: Dual-mode (Local Whisper/Kokoro OR AgentVoiceBox)
- **Desktop**: Tauri 2.0 with shared Lit components
- **CLI**: Rust + Ratatui terminal dashboard

### 1.3 Design Principles

1. **Strict Layer Separation** - UI knows NOTHING about Django internals
2. **API-First** - All communication via Django Ninja REST/WebSocket
3. **Permission-First** - Every action checked via SpiceDB before execution
4. **Scale-First** - Architecture supports 1M+ concurrent users
5. **Offline-First** - Service Worker caching, optimistic updates
6. **Voice-Agnostic** - User chooses Local or AgentVoiceBox provider

---

## 2. Glossary

| Term | Definition |
|------|------------|
| **Agent_Mode** | Operational state determining available features (STD/TRN/ADM/DEV/RO/DGR) |
| **AgentSkin** | Theme system using CSS Custom Properties (26+ variables) |
| **AgentVoiceBox** | External voice service (OpenAI-compatible API, Kokoro TTS, Faster-Whisper STT) |
| **Django_Ninja** | Fast async API framework for Django with OpenAPI 3.1 |
| **Kokoro** | Local TTS engine (82M-200M ONNX models) |
| **Lit** | Google's Web Components library with reactive properties |
| **Local_Voice** | On-device STT/TTS using Whisper + Kokoro |
| **Module** | Self-contained Lit Web Component with defined permissions |
| **Permission** | Authorization to perform a specific action on a resource |
| **Persona** | Agent personality/behavior configuration within a tenant |
| **Profile** | Custom role configuration created by system administrators |
| **Role** | Named collection of permissions assignable to users |
| **Shadow_DOM** | Encapsulated DOM tree for component isolation |
| **Skin** | Visual theme configuration (CSS variables, metadata) |
| **SpiceDB** | Google Zanzibar-based permission system for scale |
| **Tauri** | Rust-based desktop application framework |
| **Tenant** | Isolated organizational unit with separate data and config |
| **Whisper** | Local STT engine (OpenAI Whisper, various model sizes) |

---

## 3. Agent Modes

### 3.1 Mode Definitions

| Mode | Code | Description | Use Case |
|------|------|-------------|----------|
| **STANDARD** | `STD` | Normal operation with user-level access | Regular users |
| **TRAINING** | `TRN` | Learning mode with cognitive parameter access | Model fine-tuning |
| **ADMIN** | `ADM` | Full system control and configuration | System administrators |
| **DEVELOPER** | `DEV` | Module SDK access and debugging tools | UI/Module developers |
| **READONLY** | `RO` | View-only access for auditing | Auditors, observers |
| **DEGRADED** | `DGR` | Limited functionality during service issues | Automatic failover |

### 3.2 Mode Transition Rules

- Users can only transition to modes they have permission for
- DEGRADED mode is system-triggered (no user action required)
- Mode changes emit `mode.changed` WebSocket event
- All mode transitions are logged to audit trail

---

## 4. Complete Permission Matrix

### 4.1 Role Hierarchy (SpiceDB Schema)

```
SYSADMIN (Platform Owner)
    └── ADMIN (Tenant Administrator)
            ├── DEVELOPER (Module/UI Developer)
            ├── TRAINER (Cognitive Parameter Access)
            └── USER (Standard Operations)
                    └── VIEWER (Read-Only Access)
```

### 4.2 Feature Permissions by Mode

| Feature | STD | TRN | ADM | DEV | RO | SYSADMIN |
|---------|-----|-----|-----|-----|-----|----------|
| Chat/Conversation | ✅ | ✅ | ✅ | ✅ | 👁️ | ✅ |
| Memory Read | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Memory Write | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| Memory Delete | ❌ | ❌ | ✅ | ❌ | ❌ | ✅ |
| Memory Export | ❌ | ❌ | ✅ | ❌ | ❌ | ✅ |
| Tool Execution | ✅ | ⚠️ | ✅ | ✅ | ❌ | ✅ |
| Browser Agent | ✅ | ❌ | ✅ | ✅ | ❌ | ✅ |
| Code Execution | ✅ | ❌ | ✅ | ✅ | ❌ | ✅ |
| Settings View | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Settings Edit | ❌ | ⚠️ | ✅ | ⚠️ | ❌ | ✅ |
| API Keys View | ❌ | ❌ | ✅ | ❌ | ❌ | ✅ |
| API Keys Edit | ❌ | ❌ | ✅ | ❌ | ❌ | ✅ |
| Voice Settings | ✅ | ✅ | ✅ | ✅ | 👁️ | ✅ |
| Theme Apply | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| Theme Upload | ❌ | ❌ | ✅ | ❌ | ❌ | ✅ |

Legend: ✅ Full Access | ⚠️ Limited | 👁️ View Only | ❌ No Access

### 4.3 Cognitive Parameters by Mode

| Parameter | STD | TRN | ADM | DEV | RO | SYSADMIN |
|-----------|-----|-----|-----|-----|-----|----------|
| Neuromodulators View | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Neuromodulators Edit | ❌ | ✅ | ✅ | ❌ | ❌ | ✅ |
| Adaptation Weights | ❌ | ✅ | ✅ | ❌ | ❌ | ✅ |
| Learning Rate | ❌ | ✅ | ✅ | ❌ | ❌ | ✅ |
| Sleep Cycle Trigger | ❌ | ✅ | ✅ | ❌ | ❌ | ✅ |

### 4.4 Settings Sections by Mode

| Settings Section | STD | TRN | ADM | DEV | RO | SYSADMIN |
|------------------|-----|-----|-----|-----|-----|----------|
| Agent Tab - Models | 👁️ | 👁️ | ✅ | 👁️ | 👁️ | ✅ |
| Agent Tab - Memory | 👁️ | ✅ | ✅ | 👁️ | 👁️ | ✅ |
| External Tab - API Keys | ❌ | ❌ | ✅ | ❌ | ❌ | ✅ |
| External Tab - MCP | 👁️ | 👁️ | ✅ | ✅ | 👁️ | ✅ |
| Connectivity Tab - Proxy | ❌ | ❌ | ✅ | ❌ | ❌ | ✅ |
| Connectivity Tab - Voice | ✅ | ✅ | ✅ | ✅ | 👁️ | ✅ |
| System Tab - Auth | ❌ | ❌ | ✅ | ❌ | ❌ | ✅ |
| System Tab - Backup | ❌ | ❌ | ✅ | ❌ | ❌ | ✅ |
| System Tab - Features | 👁️ | 👁️ | ✅ | 👁️ | 👁️ | ✅ |

### 4.5 Tool Permissions by Mode

| Tool Category | STD | TRN | ADM | DEV | RO | SYSADMIN |
|---------------|-----|-----|-----|-----|-----|----------|
| code_execution | ✅ | ⚠️ | ✅ | ✅ | ❌ | ✅ |
| browser_agent | ✅ | ❌ | ✅ | ✅ | ❌ | ✅ |
| memory_save | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| memory_load | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| memory_delete | ❌ | ❌ | ✅ | ❌ | ❌ | ✅ |
| search_engine | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| voice_input | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| voice_output | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| scheduler | ✅ | ❌ | ✅ | ✅ | 👁️ | ✅ |

---

## 5. Complete Settings Architecture

### 5.1 Settings Tab Structure

```
Settings
├── Agent Tab
│   ├── Chat Model (provider, model, context_length, RPM, TPM, vision)
│   ├── Utility Model (provider, model, context_length, RPM, TPM)
│   ├── Browser Model (provider, model, headers, rate_limit)
│   ├── Embedding Model (provider, model, dimensions)
│   └── Memory/SomaBrain (recall_enabled, interval, max_memories, threshold)
│
├── External Tab
│   ├── API Keys (OpenAI, Anthropic, Google, Groq, Mistral)
│   ├── MCP Client (servers JSON, init_timeout, tool_timeout)
│   ├── MCP Server (enabled, endpoint, token)
│   ├── A2A Server (enabled, endpoint, token)
│   └── Tunnel (enabled, URL, auth_token)
│
├── Connectivity Tab
│   ├── Proxy (HTTP/HTTPS proxy configuration)
│   ├── SSE (retry_interval, request_timeout)
│   ├── Voice/Speech (provider, language, voice, VAD_threshold) ← NEW
│   └── Health (poll_interval, degradation_threshold, alerts)
│
└── System Tab
    ├── Authentication (username, password, root_password)
    ├── Backup/Restore (auto_backup, location, restore_file)
    ├── Developer (shell_interface, RFC_host, RFC_port, debug_mode)
    ├── Feature Flags (profile selector + individual toggles)
    ├── Secrets (opaque JSON blob → Vault)
    └── Agent Config (profile, knowledge_dirs, memory_subdir)
```

### 5.2 Voice/Speech Settings (NEW - REQUIRED)

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `voice_provider` | select | `local` | Voice provider: `local` or `agentvoicebox` |
| `voice_enabled` | toggle | `false` | Master switch for voice subsystem |
| `stt_engine` | select | `whisper` | STT engine: `whisper`, `faster-whisper` |
| `stt_model_size` | select | `base` | Whisper model: `tiny`, `base`, `small`, `medium`, `large` |
| `tts_engine` | select | `kokoro` | TTS engine: `kokoro`, `browser`, `openai` |
| `tts_voice` | select | `am_onyx` | Kokoro voice ID |
| `tts_speed` | slider | `1.0` | TTS speed multiplier (0.5-2.0) |
| `vad_threshold` | slider | `0.5` | Voice Activity Detection threshold |
| `language` | select | `en-US` | Speech language code |
| `agentvoicebox_url` | text | `` | AgentVoiceBox server URL (if provider=agentvoicebox) |
| `agentvoicebox_token` | password | `` | AgentVoiceBox API token |
| `audio_input_device` | select | `0` | Microphone device index |
| `audio_output_device` | select | `0` | Speaker device index |
| `audio_sample_rate` | select | `24000` | Audio sample rate (Hz) |

### 5.3 Feature Flags (Complete List)

| Flag | Default | Description |
|------|---------|-------------|
| `sse_enabled` | `true` | Server-Sent Events for streaming |
| `embeddings_ingest` | `true` | Embedding ingestion pipeline |
| `semantic_recall` | `true` | Semantic memory recall |
| `content_masking` | `true` | Sensitive content masking |
| `audio_support` | `false` | Voice/audio subsystem |
| `browser_support` | `true` | Browser agent capability |
| `code_exec` | `true` | Code execution tool |
| `vision_support` | `true` | Vision/image analysis |
| `mcp_client` | `true` | MCP client connections |
| `mcp_server` | `false` | MCP server mode |
| `learning_context` | `true` | Learning context tracking |
| `tool_sandboxing` | `true` | Tool execution sandboxing |
| `streaming_responses` | `true` | Streaming LLM responses |
| `delegation` | `true` | Agent delegation/subordinates |
| `voice_local` | `true` | Local voice (Whisper/Kokoro) |
| `voice_agentvoicebox` | `false` | AgentVoiceBox integration |

### 5.4 Feature Profiles

| Profile | Description | Enabled Flags |
|---------|-------------|---------------|
| `minimal` | Bare minimum | sse, semantic_recall |
| `standard` | Default experience | minimal + browser, code_exec, vision |
| `enhanced` | Full features | standard + audio, mcp_client, delegation |
| `max` | Everything enabled | All flags enabled |

---

## 6. AgentSkin Theme System (REQUIRED)

### 6.1 Theme JSON Schema

```json
{
  "$schema": "https://somaagent.io/schemas/agentskin-v1.json",
  "name": "Theme Name",
  "version": "1.0.0",
  "author": "Author Name",
  "description": "Theme description",
  "category": "Professional|Creative|Developer|Gaming|Accessibility",
  "tags": ["dark", "minimal", "high-contrast"],
  "variables": {
    "bg-void": "#0f172a",
    "glass-surface": "rgba(30, 41, 59, 0.85)",
    "glass-border": "rgba(255, 255, 255, 0.05)",
    "text-main": "#e2e8f0",
    "text-dim": "#64748b",
    "accent-primary": "#3b82f6",
    "accent-secondary": "#8b5cf6",
    "accent-success": "#22c55e",
    "accent-warning": "#f59e0b",
    "accent-danger": "#ef4444",
    "shadow-soft": "0 10px 40px -10px rgba(0, 0, 0, 0.5)",
    "radius-sm": "4px",
    "radius-md": "8px",
    "radius-lg": "16px",
    "radius-full": "9999px",
    "spacing-xs": "4px",
    "spacing-sm": "8px",
    "spacing-md": "16px",
    "spacing-lg": "24px",
    "spacing-xl": "32px",
    "font-sans": "'Space Grotesk', sans-serif",
    "font-mono": "'JetBrains Mono', monospace",
    "text-xs": "10px",
    "text-sm": "12px",
    "text-base": "14px",
    "text-lg": "16px",
    "text-xl": "20px"
  }
}
```

### 6.2 Required CSS Custom Properties (26 minimum)

| Property | Purpose | Example |
|----------|---------|---------|
| `--eog-bg-void` | Background color | `#0f172a` |
| `--eog-glass-surface` | Glass panel background | `rgba(30, 41, 59, 0.85)` |
| `--eog-glass-border` | Glass panel border | `rgba(255, 255, 255, 0.05)` |
| `--eog-text-main` | Primary text color | `#e2e8f0` |
| `--eog-text-dim` | Secondary text color | `#64748b` |
| `--eog-accent-primary` | Primary accent | `#3b82f6` |
| `--eog-accent-secondary` | Secondary accent | `#8b5cf6` |
| `--eog-accent-success` | Success state | `#22c55e` |
| `--eog-accent-warning` | Warning state | `#f59e0b` |
| `--eog-accent-danger` | Danger/error state | `#ef4444` |
| `--eog-shadow-soft` | Soft shadow | `0 10px 40px...` |
| `--eog-radius-sm` | Small border radius | `4px` |
| `--eog-radius-md` | Medium border radius | `8px` |
| `--eog-radius-lg` | Large border radius | `16px` |
| `--eog-radius-full` | Full/pill radius | `9999px` |
| `--eog-spacing-xs` | Extra small spacing | `4px` |
| `--eog-spacing-sm` | Small spacing | `8px` |
| `--eog-spacing-md` | Medium spacing | `16px` |
| `--eog-spacing-lg` | Large spacing | `24px` |
| `--eog-spacing-xl` | Extra large spacing | `32px` |
| `--eog-font-sans` | Sans-serif font | `'Space Grotesk'` |
| `--eog-font-mono` | Monospace font | `'JetBrains Mono'` |
| `--eog-text-xs` | Extra small text | `10px` |
| `--eog-text-sm` | Small text | `12px` |
| `--eog-text-base` | Base text | `14px` |
| `--eog-text-lg` | Large text | `16px` |

### 6.3 Default Themes (REQUIRED)

1. **Default Light** - Clean, professional light theme
2. **Midnight Dark** - Dark theme with blue accents (current glassmorphism)
3. **High Contrast** - WCAG AAA compliant accessibility theme

### 6.4 Theme Security Rules

- NO `url()` in CSS values (XSS prevention)
- HTTPS-only for remote theme loading
- JSON Schema validation required
- WCAG AA contrast ratio validation (4.5:1 minimum)
- Rate limiting: 10 uploads/hour/user

---

## 7. Voice/Speech Integration Architecture

### 7.1 Dual-Mode Voice System

The agent supports TWO voice providers, selectable via Settings:

```
┌─────────────────────────────────────────────────────────────────┐
│                    VOICE PROVIDER SELECTION                      │
│                                                                  │
│   ┌─────────────────────┐    ┌─────────────────────────────┐   │
│   │   LOCAL VOICE       │    │   AGENTVOICEBOX             │   │
│   │   (On-Device)       │    │   (External Service)        │   │
│   ├─────────────────────┤    ├─────────────────────────────┤   │
│   │ STT: Whisper        │    │ STT: Faster-Whisper         │   │
│   │ TTS: Kokoro         │    │ TTS: Kokoro/phoonnx         │   │
│   │ VAD: WebRTC         │    │ VAD: WebRTC + Silero        │   │
│   │ Latency: ~300ms     │    │ Latency: ~150ms             │   │
│   │ Privacy: Full       │    │ Privacy: Network            │   │
│   │ Cost: $0            │    │ Cost: $0 (self-hosted)      │   │
│   └─────────────────────┘    └─────────────────────────────┘   │
│                                                                  │
│   User selects via: Settings → Connectivity → Voice/Speech      │
└─────────────────────────────────────────────────────────────────┘
```

### 7.2 Local Voice Architecture (Whisper + Kokoro)

```
┌─────────────────────────────────────────────────────────────────┐
│                    LOCAL VOICE PIPELINE                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Microphone → AudioCapture → VAD → Whisper STT → Text          │
│                                                                  │
│   Text → Agent Processing → Response Text                        │
│                                                                  │
│   Response Text → Kokoro TTS → Audio → Speaker                  │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│  Components:                                                     │
│  - AudioCapture (src/voice/audio_capture.py)                    │
│  - VoiceAdapter (src/voice/voice_adapter.py)                    │
│  - LocalClient (src/voice/local_client.py)                      │
│  - Speaker (src/voice/speaker.py)                               │
│  - Whisper (python/helpers/whisper.py)                          │
│  - Kokoro (python/helpers/kokoro_tts.py)                        │
└─────────────────────────────────────────────────────────────────┘
```

### 7.3 AgentVoiceBox Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                 AGENTVOICEBOX INTEGRATION                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   SomaAgent01                    AgentVoiceBox Server            │
│   ┌──────────────┐              ┌──────────────────────┐        │
│   │ VoiceAdapter │──WebSocket──▶│ /v1/realtime         │        │
│   │              │◀─────────────│ (OpenAI-compatible)  │        │
│   └──────────────┘              └──────────────────────┘        │
│                                          │                       │
│                                          ▼                       │
│                                 ┌──────────────────────┐        │
│                                 │ Speech Pipeline      │        │
│                                 │ - Faster-Whisper STT │        │
│                                 │ - Kokoro/phoonnx TTS │        │
│                                 │ - Dual VAD           │        │
│                                 │ - Noise Reduction    │        │
│                                 └──────────────────────┘        │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│  AgentVoiceBox Endpoints:                                        │
│  - WS /v1/realtime (bidirectional audio streaming)              │
│  - POST /v1/audio/speech (TTS)                                  │
│  - POST /v1/audio/transcriptions (STT)                          │
│  - GET /v1/models (available models)                            │
│  - GET /health (health check)                                   │
└─────────────────────────────────────────────────────────────────┘
```

### 7.4 Voice Configuration Models

```python
# Local Voice Config
class LocalVoiceConfig:
    stt_engine: str = "whisper"           # whisper, faster-whisper
    stt_model_size: str = "base"          # tiny, base, small, medium, large
    tts_engine: str = "kokoro"            # kokoro, browser
    tts_voice: str = "am_onyx"            # Kokoro voice ID
    tts_speed: float = 1.0                # 0.5-2.0
    vad_threshold: float = 0.5            # 0.0-1.0
    language: str = "en-US"

# AgentVoiceBox Config
class AgentVoiceBoxConfig:
    base_url: str = ""                    # http://localhost:60200
    ws_url: str = ""                      # ws://localhost:60200/v1/realtime
    api_token: str = ""                   # Bearer token
    model: str = "ovos-voice-1"           # Model name
    voice: str = "default"                # Voice ID
    turn_detection: bool = True           # Server-side VAD
    input_audio_format: str = "pcm16"     # Audio format
    output_audio_format: str = "pcm16"

# Master Voice Config
class VoiceConfig:
    enabled: bool = False                 # Master switch
    provider: str = "local"               # local, agentvoicebox
    local: LocalVoiceConfig
    agentvoicebox: AgentVoiceBoxConfig
    audio_input_device: int = 0
    audio_output_device: int = 0
    sample_rate: int = 24000
```

### 7.5 Voice Provider Selection Logic

```python
def get_voice_provider(config: VoiceConfig):
    if not config.enabled:
        raise VoiceDisabledError("Voice subsystem is disabled")
    
    if config.provider == "local":
        return LocalVoiceProvider(config.local)
    elif config.provider == "agentvoicebox":
        return AgentVoiceBoxProvider(config.agentvoicebox)
    else:
        raise ProviderNotSupportedError(config.provider)
```

### 7.6 Voice Events (WebSocket)

| Event | Direction | Description |
|-------|-----------|-------------|
| `voice.started` | Server→Client | Voice session started |
| `voice.speech_started` | Server→Client | User started speaking |
| `voice.speech_stopped` | Server→Client | User stopped speaking |
| `voice.transcription` | Server→Client | STT result |
| `voice.response_started` | Server→Client | Agent started responding |
| `voice.audio_delta` | Server→Client | Audio chunk (base64) |
| `voice.response_done` | Server→Client | Agent finished responding |
| `voice.error` | Server→Client | Voice error occurred |
| `voice.input_audio` | Client→Server | Audio input (base64) |
| `voice.cancel` | Client→Server | Cancel current response |

---

## 8. Functional Requirements

### 8.1 UI Layer Requirements (Lit Web Components)

| ID | Requirement |
|----|-------------|
| REQ-UI-001 | THE UI_Layer SHALL use Lit 3.x Web Components with Shadow DOM encapsulation |
| REQ-UI-002 | WHEN a component renders THEN the UI_Layer SHALL complete rendering within 16ms (60fps) |
| REQ-UI-003 | THE UI_Layer SHALL expose reactive properties via Lit's `@property` decorator |
| REQ-UI-004 | WHEN theme variables change THEN the UI_Layer SHALL update all components within 50ms |
| REQ-UI-005 | THE UI_Layer SHALL lazy-load non-critical components via dynamic imports |
| REQ-UI-006 | WHEN the application loads THEN the UI_Layer SHALL achieve First Contentful Paint < 1.5s |
| REQ-UI-007 | THE UI_Layer SHALL use CSS Custom Properties for all themeable values |
| REQ-UI-008 | WHEN offline THEN the UI_Layer SHALL serve cached assets via Service Worker |

### 8.2 MVC Layer Requirements (Django + Django Ninja)

| ID | Requirement |
|----|-------------|
| REQ-MVC-001 | THE MVC_Layer SHALL use Django 5.x with async ORM support |
| REQ-MVC-002 | THE MVC_Layer SHALL expose all APIs via Django Ninja with OpenAPI 3.1 schema |
| REQ-MVC-003 | WHEN an API request arrives THEN the MVC_Layer SHALL respond within 50ms (p95) |
| REQ-MVC-004 | THE MVC_Layer SHALL use Django's migration system for all schema changes |
| REQ-MVC-005 | WHEN database queries execute THEN the MVC_Layer SHALL use connection pooling (pgbouncer) |
| REQ-MVC-006 | THE MVC_Layer SHALL implement CQRS pattern for read-heavy endpoints |
| REQ-MVC-007 | WHEN WebSocket connections are needed THEN the MVC_Layer SHALL use Django Channels |
| REQ-MVC-008 | THE MVC_Layer SHALL expose Django Admin for superuser operations only |

### 8.3 Permission System Requirements (SpiceDB)

| ID | Requirement |
|----|-------------|
| REQ-PERM-001 | THE Permission_System SHALL deploy SpiceDB as the permission authority |
| REQ-PERM-002 | WHEN a permission check executes THEN the Permission_System SHALL respond within 10ms (p95) |
| REQ-PERM-003 | THE Permission_System SHALL support 1,000,000+ permission checks per second |
| REQ-PERM-004 | WHEN SpiceDB is unavailable THEN the Permission_System SHALL deny all requests (fail-closed) |
| REQ-PERM-005 | THE Permission_System SHALL cache permission decisions in Redis with TTL 60s |
| REQ-PERM-006 | WHEN a role changes THEN the Permission_System SHALL propagate changes within 5 seconds |
| REQ-PERM-007 | THE Permission_System SHALL support hierarchical role inheritance |
| REQ-PERM-008 | THE Permission_System SHALL provide default roles: SysAdmin, Admin, Developer, User, Viewer |
| REQ-PERM-009 | WHEN a user requests an action THEN the Permission_System SHALL verify tenant isolation |

### 8.4 AgentSkin Theme Requirements (REQUIRED)

| ID | Requirement |
|----|-------------|
| REQ-SKIN-001 | THE Theme_System SHALL use CSS Custom Properties for all themeable values (26 variables minimum) |
| REQ-SKIN-002 | WHEN theme is applied THEN the Theme_System SHALL inject variables within 50ms |
| REQ-SKIN-003 | THE Theme_System SHALL support theme JSON format with name, version, author, variables |
| REQ-SKIN-004 | WHEN theme file is dropped THEN the Theme_System SHALL validate against JSON Schema |
| REQ-SKIN-005 | THE Theme_System SHALL persist active theme to localStorage |
| REQ-SKIN-006 | WHEN theme contains `url()` in CSS values THEN the Theme_System SHALL reject (XSS prevention) |
| REQ-SKIN-007 | THE Theme_System SHALL provide default themes: Default Light, Midnight Dark, High Contrast |
| REQ-SKIN-008 | THE Theme_System SHALL support remote theme loading via HTTPS only |
| REQ-SKIN-009 | WHEN theme is previewed THEN the Theme_System SHALL show split-screen comparison |
| REQ-SKIN-010 | THE Theme_System SHALL validate WCAG AA contrast ratios (4.5:1 minimum) |

### 8.5 Voice/Speech Requirements (NEW)

| ID | Requirement |
|----|-------------|
| REQ-VOICE-001 | THE Voice_System SHALL support dual providers: Local (Whisper/Kokoro) and AgentVoiceBox |
| REQ-VOICE-002 | WHEN voice_provider is "local" THEN the Voice_System SHALL use on-device Whisper STT |
| REQ-VOICE-003 | WHEN voice_provider is "local" THEN the Voice_System SHALL use on-device Kokoro TTS |
| REQ-VOICE-004 | WHEN voice_provider is "agentvoicebox" THEN the Voice_System SHALL connect via WebSocket |
| REQ-VOICE-005 | THE Voice_System SHALL support model selection for Whisper (tiny/base/small/medium/large) |
| REQ-VOICE-006 | THE Voice_System SHALL support voice selection for Kokoro TTS |
| REQ-VOICE-007 | WHEN voice is enabled THEN the Voice_System SHALL emit voice.* WebSocket events |
| REQ-VOICE-008 | THE Voice_System SHALL support Voice Activity Detection (VAD) with configurable threshold |
| REQ-VOICE-009 | WHEN AgentVoiceBox is selected THEN the Voice_System SHALL validate connection on save |
| REQ-VOICE-010 | THE Voice_System SHALL support audio device selection (input/output) |
| REQ-VOICE-011 | THE Voice_System SHALL support sample rate configuration (8kHz-48kHz) |
| REQ-VOICE-012 | WHEN voice error occurs THEN the Voice_System SHALL emit voice.error event with details |

### 8.6 Settings Management Requirements

| ID | Requirement |
|----|-------------|
| REQ-SET-001 | THE Settings_Manager SHALL organize settings into tabs: Agent, External, Connectivity, System |
| REQ-SET-002 | WHEN settings are modified THEN the Settings_Manager SHALL persist to PostgreSQL immediately |
| REQ-SET-003 | THE Settings_Manager SHALL validate all inputs against JSON Schema before saving |
| REQ-SET-004 | WHEN sensitive fields are displayed THEN the Settings_Manager SHALL mask values with asterisks |
| REQ-SET-005 | THE Settings_Manager SHALL support field types: text, password, select, toggle, slider, number, json, file |
| REQ-SET-006 | WHEN API keys are saved THEN the Settings_Manager SHALL store in Vault (not PostgreSQL) |
| REQ-SET-007 | THE Settings_Manager SHALL emit `settings.changed` event after successful save |
| REQ-SET-008 | WHEN settings change THEN the Settings_Manager SHALL trigger agent config reload |
| REQ-SET-009 | THE Settings_Manager SHALL include Voice/Speech section in Connectivity tab |
| REQ-SET-010 | WHEN voice provider changes THEN the Settings_Manager SHALL show provider-specific fields |

### 8.7 Mode State Management Requirements

| ID | Requirement |
|----|-------------|
| REQ-MODE-001 | THE Mode_Manager SHALL maintain current mode state per session |
| REQ-MODE-002 | WHEN mode changes THEN the Mode_Manager SHALL emit `mode.changed` event via WebSocket |
| REQ-MODE-003 | THE Mode_Manager SHALL persist mode preference per user in PostgreSQL |
| REQ-MODE-004 | WHEN session starts THEN the Mode_Manager SHALL restore last mode if permitted |
| REQ-MODE-005 | WHEN user requests mode change THEN the Mode_Manager SHALL verify permissions via SpiceDB |
| REQ-MODE-006 | IF user lacks permission for target mode THEN the Mode_Manager SHALL reject with HTTP 403 |
| REQ-MODE-007 | WHEN transitioning to DEGRADED mode THEN the Mode_Manager SHALL NOT require user action |
| REQ-MODE-008 | THE Mode_Manager SHALL log all mode transitions to audit trail |

### 8.8 Real-Time Communication Requirements

| ID | Requirement |
|----|-------------|
| REQ-RT-001 | THE Realtime_System SHALL use WebSocket for bidirectional communication |
| REQ-RT-002 | WHEN server event occurs THEN the Realtime_System SHALL deliver to client within 100ms |
| REQ-RT-003 | THE Realtime_System SHALL support SSE fallback when WebSocket unavailable |
| REQ-RT-004 | WHEN connection drops THEN the Realtime_System SHALL reconnect with exponential backoff |
| REQ-RT-005 | THE Realtime_System SHALL send heartbeat every 20 seconds |
| REQ-RT-006 | WHEN client reconnects THEN the Realtime_System SHALL replay missed events |
| REQ-RT-007 | THE Realtime_System SHALL support event types: mode.changed, settings.changed, theme.changed, voice.* |
| REQ-RT-008 | THE Realtime_System SHALL authenticate WebSocket connections via token |

---

## 9. Non-Functional Requirements

### 9.1 Performance Requirements (MILLIONS OF USERS)

| ID | Requirement |
|----|-------------|
| REQ-PERF-001 | THE System SHALL support 1,000,000+ concurrent WebSocket connections |
| REQ-PERF-002 | THE System SHALL achieve First Contentful Paint < 1.5 seconds |
| REQ-PERF-003 | THE System SHALL achieve Time to Interactive < 3 seconds |
| REQ-PERF-004 | WHEN theme switches THEN the System SHALL complete transition < 300ms |
| REQ-PERF-005 | THE API_Layer SHALL achieve response time < 50ms (p95) |
| REQ-PERF-006 | THE Permission_System SHALL achieve check time < 10ms (p95) |
| REQ-PERF-007 | THE System SHALL support 10,000 concurrent WebSocket connections per node |
| REQ-PERF-008 | WHEN under load THEN the System SHALL maintain 99.9% availability |
| REQ-PERF-009 | THE System SHALL achieve Lighthouse score > 90 for all categories |
| REQ-PERF-010 | THE Django_Ninja_API SHALL handle 100,000+ requests/second per node |
| REQ-PERF-011 | THE Lit_UI SHALL render 60fps during all interactions |
| REQ-PERF-012 | THE System SHALL support horizontal scaling via Kubernetes |

### 9.2 Security Requirements

| ID | Requirement |
|----|-------------|
| REQ-SEC-001 | THE API_Security SHALL require Bearer token authentication for all endpoints |
| REQ-SEC-002 | WHEN request lacks valid token THEN the API_Security SHALL return HTTP 401 |
| REQ-SEC-003 | THE API_Security SHALL enforce rate limiting (120 requests/minute default) |
| REQ-SEC-004 | WHEN rate limit exceeded THEN the API_Security SHALL return HTTP 429 with Retry-After |
| REQ-SEC-005 | THE API_Security SHALL validate all inputs against JSON Schema |
| REQ-SEC-006 | WHEN SQL injection attempted THEN the API_Security SHALL reject with HTTP 400 |
| REQ-SEC-007 | THE API_Security SHALL set CSP headers: default-src 'self'; style-src 'self' 'unsafe-inline' |
| REQ-SEC-008 | THE API_Security SHALL log all authentication failures to audit trail |
| REQ-SEC-009 | WHEN XSS payload detected THEN the API_Security SHALL sanitize and reject |
| REQ-SEC-010 | THE System SHALL store all secrets in Vault (not PostgreSQL) |

### 9.3 Multi-Tenancy Requirements

| ID | Requirement |
|----|-------------|
| REQ-MT-001 | THE Multi_Tenancy SHALL isolate all data by tenant_id |
| REQ-MT-002 | WHEN request arrives THEN the Multi_Tenancy SHALL extract tenant from X-Tenant-Id header |
| REQ-MT-003 | THE Multi_Tenancy SHALL enforce tenant isolation in all database queries |
| REQ-MT-004 | WHEN user accesses resource THEN the Multi_Tenancy SHALL verify tenant membership via SpiceDB |
| REQ-MT-005 | THE Multi_Tenancy SHALL support tenant-specific themes and settings |
| REQ-MT-006 | WHEN tenant is created THEN the Multi_Tenancy SHALL provision default roles and settings |
| REQ-MT-007 | THE Multi_Tenancy SHALL support tenant hierarchy (parent/child tenants) |
| REQ-MT-008 | WHEN tenant is deleted THEN the Multi_Tenancy SHALL cascade delete all tenant data |

### 9.4 Accessibility Requirements

| ID | Requirement |
|----|-------------|
| REQ-A11Y-001 | THE Accessibility SHALL comply with WCAG 2.1 AA standards |
| REQ-A11Y-002 | THE Accessibility SHALL support keyboard navigation for all interactive elements |
| REQ-A11Y-003 | WHEN focus changes THEN the Accessibility SHALL show visible focus indicator |
| REQ-A11Y-004 | THE Accessibility SHALL provide ARIA labels for all controls |
| REQ-A11Y-005 | THE Accessibility SHALL support screen readers (NVDA, VoiceOver, JAWS) |
| REQ-A11Y-006 | WHEN color is used for meaning THEN the Accessibility SHALL provide alternative indicator |
| REQ-A11Y-007 | THE Accessibility SHALL support reduced motion preference |
| REQ-A11Y-008 | THE Accessibility SHALL maintain contrast ratio >= 4.5:1 for all text |

### 9.5 Observability Requirements

| ID | Requirement |
|----|-------------|
| REQ-OBS-001 | THE Observability SHALL expose Prometheus metrics on /metrics endpoint |
| REQ-OBS-002 | THE Observability SHALL track: request_count, request_duration, error_rate, active_connections |
| REQ-OBS-003 | WHEN error occurs THEN the Observability SHALL increment error counter with labels |
| REQ-OBS-004 | THE Observability SHALL support OpenTelemetry tracing with trace_id propagation |
| REQ-OBS-005 | THE Observability SHALL log structured JSON to stdout |
| REQ-OBS-006 | WHEN latency exceeds SLO THEN the Observability SHALL emit alert |
| REQ-OBS-007 | THE Observability SHALL track theme_loads_total, permission_checks_total, mode_transitions_total |
| REQ-OBS-008 | THE Observability SHALL provide Grafana dashboard templates |

---

## 10. Voice System Detailed Requirements

### 10.1 Local Voice (STT + TTS Only - NO Speech-on-Speech)

| ID | Requirement |
|----|-------------|
| REQ-LVOICE-001 | THE Local_Voice SHALL provide STT via Whisper (CPU or GPU) |
| REQ-LVOICE-002 | THE Local_Voice SHALL provide TTS via Kokoro (CPU or GPU) |
| REQ-LVOICE-003 | THE Local_Voice SHALL NOT support real-time speech-on-speech |
| REQ-LVOICE-004 | THE Local_Voice SHALL detect hardware (CPU/GPU) and select appropriate model |
| REQ-LVOICE-005 | WHEN GPU is available THEN the Local_Voice SHALL use CUDA-optimized models |
| REQ-LVOICE-006 | WHEN GPU is unavailable THEN the Local_Voice SHALL fallback to CPU models |
| REQ-LVOICE-007 | THE Local_Voice SHALL support Whisper model sizes: tiny, base, small, medium, large |
| REQ-LVOICE-008 | THE Local_Voice SHALL support Kokoro model sizes: 82M, 200M |
| REQ-LVOICE-009 | THE Local_Voice SHALL preload models at startup if enabled |
| REQ-LVOICE-010 | THE Local_Voice SHALL support 15+ languages via Kokoro |

### 10.2 AgentVoiceBox Integration (Full Speech-on-Speech)

| ID | Requirement |
|----|-------------|
| REQ-AVB-001 | THE AgentVoiceBox SHALL provide full real-time speech-on-speech capability |
| REQ-AVB-002 | THE AgentVoiceBox SHALL connect via WebSocket to /v1/realtime endpoint |
| REQ-AVB-003 | THE AgentVoiceBox SHALL support OpenAI Realtime API protocol |
| REQ-AVB-004 | THE AgentVoiceBox SHALL support bidirectional audio streaming |
| REQ-AVB-005 | THE AgentVoiceBox SHALL achieve latency < 150ms end-to-end |
| REQ-AVB-006 | THE AgentVoiceBox SHALL support turn detection and interruption handling |
| REQ-AVB-007 | THE AgentVoiceBox SHALL support dual VAD (WebRTC + Silero) |
| REQ-AVB-008 | THE AgentVoiceBox SHALL support noise reduction and AGC |
| REQ-AVB-009 | WHEN AgentVoiceBox is local THEN the System SHALL connect to localhost |
| REQ-AVB-010 | WHEN AgentVoiceBox is remote THEN the System SHALL connect via configured URL |
| REQ-AVB-011 | THE AgentVoiceBox SHALL support 1000+ concurrent voice sessions per server |

### 10.3 Voice Provider Selection

| ID | Requirement |
|----|-------------|
| REQ-VPROV-001 | THE Settings SHALL allow user to select voice provider: local, agentvoicebox, or disabled |
| REQ-VPROV-002 | WHEN provider is "local" THEN the System SHALL use Local_Voice for STT/TTS |
| REQ-VPROV-003 | WHEN provider is "agentvoicebox" THEN the System SHALL use AgentVoiceBox |
| REQ-VPROV-004 | WHEN provider is "disabled" THEN the System SHALL hide all voice UI elements |
| REQ-VPROV-005 | THE Settings SHALL show provider-specific configuration fields |
| REQ-VPROV-006 | WHEN provider changes THEN the System SHALL validate new configuration |
| REQ-VPROV-007 | THE Settings SHALL provide "Test Connection" for AgentVoiceBox |

---

## 11. Django + Django Ninja Architecture (ALL PROJECTS)

### 11.1 Unified Backend Stack

| ID | Requirement |
|----|-------------|
| REQ-DJ-001 | ALL backend services SHALL use Django 5.x as the MVC framework |
| REQ-DJ-002 | ALL REST APIs SHALL use Django Ninja with OpenAPI 3.1 schema |
| REQ-DJ-003 | ALL WebSocket connections SHALL use Django Channels 4.x |
| REQ-DJ-004 | ALL database operations SHALL use Django ORM with async support |
| REQ-DJ-005 | ALL migrations SHALL use Django's migration system |
| REQ-DJ-006 | THE Django_Admin SHALL be available for superuser operations only |

### 11.2 SomaAgent01 Django Migration

| ID | Requirement |
|----|-------------|
| REQ-SA01-DJ-001 | THE SomaAgent01 Gateway SHALL migrate from FastAPI to Django Ninja |
| REQ-SA01-DJ-002 | THE Migration SHALL be parallel (both run simultaneously during transition) |
| REQ-SA01-DJ-003 | THE Django Ninja API SHALL be available at /api/v2/* |
| REQ-SA01-DJ-004 | THE FastAPI SHALL remain at /v1/* during transition period |
| REQ-SA01-DJ-005 | THE Django Ninja SHALL achieve feature parity with FastAPI |
| REQ-SA01-DJ-006 | THE Migration SHALL complete within 6-month overlap period |

### 11.3 SomaBrain Django Migration

| ID | Requirement |
|----|-------------|
| REQ-SB-DJ-001 | THE SomaBrain API SHALL migrate from FastAPI to Django Ninja |
| REQ-SB-DJ-002 | THE SomaBrain SHALL expose /api/v2/remember endpoint |
| REQ-SB-DJ-003 | THE SomaBrain SHALL expose /api/v2/recall endpoint |
| REQ-SB-DJ-004 | THE SomaBrain SHALL expose /api/v2/neuromodulators endpoint |
| REQ-SB-DJ-005 | THE SomaBrain SHALL expose /api/v2/sleep/* endpoints |
| REQ-SB-DJ-006 | THE SomaBrain SHALL expose /api/v2/context/* endpoints |
| REQ-SB-DJ-007 | THE SomaBrain gRPC service SHALL remain for high-performance memory operations |

### 11.4 Django Ninja API Standards

| ID | Requirement |
|----|-------------|
| REQ-NINJA-001 | ALL endpoints SHALL use Pydantic schemas for request/response validation |
| REQ-NINJA-002 | ALL endpoints SHALL return JSON with consistent error format |
| REQ-NINJA-003 | ALL endpoints SHALL include OpenAPI documentation |
| REQ-NINJA-004 | ALL endpoints SHALL support async/await |
| REQ-NINJA-005 | ALL endpoints SHALL include rate limiting via middleware |
| REQ-NINJA-006 | ALL endpoints SHALL include tenant isolation via middleware |
| REQ-NINJA-007 | ALL endpoints SHALL include permission checks via SpiceDB |
| REQ-NINJA-008 | ALL endpoints SHALL include audit logging |

---

## 12. Infrastructure Requirements

### 12.1 Docker/Kubernetes

| ID | Requirement |
|----|-------------|
| REQ-INFRA-001 | THE System SHALL detect CPU/GPU architecture at build time |
| REQ-INFRA-002 | THE System SHALL build appropriate Docker images for detected architecture |
| REQ-INFRA-003 | THE System SHALL support horizontal scaling via Kubernetes |
| REQ-INFRA-004 | THE System SHALL support rolling deployments with zero downtime |
| REQ-INFRA-005 | THE System SHALL support health checks for all services |
| REQ-INFRA-006 | THE System SHALL support resource limits and requests |

### 12.2 Database

| ID | Requirement |
|----|-------------|
| REQ-DB-001 | THE System SHALL use PostgreSQL 16.x as primary database |
| REQ-DB-002 | THE System SHALL use pgbouncer for connection pooling |
| REQ-DB-003 | THE System SHALL support read replicas for scaling |
| REQ-DB-004 | THE System SHALL use Redis 7.x for caching and sessions |
| REQ-DB-005 | THE System SHALL use Milvus for vector storage (SomaBrain) |

### 12.3 Message Queue

| ID | Requirement |
|----|-------------|
| REQ-MQ-001 | THE System SHALL use Kafka 3.x for event streaming |
| REQ-MQ-002 | THE System SHALL use Celery 5.x for background tasks |
| REQ-MQ-003 | THE System SHALL support event replay for missed events |

---

## 13. Success Criteria

### 13.1 Performance Targets

- [ ] 1,000,000+ concurrent WebSocket connections
- [ ] First Contentful Paint < 1.5s
- [ ] Time to Interactive < 3s
- [ ] API response time < 50ms (p95)
- [ ] Permission check < 10ms (p95)
- [ ] Theme switch < 300ms
- [ ] 99.9% uptime SLA

### 13.2 Security Targets

- [ ] Zero XSS vulnerabilities
- [ ] Zero SQL injection vulnerabilities
- [ ] 100% tenant isolation
- [ ] Fail-closed permission model
- [ ] All secrets in Vault

### 13.3 Quality Targets

- [ ] 80% test coverage
- [ ] Lighthouse score > 90
- [ ] WCAG 2.1 AA compliance
- [ ] Zero critical bugs in production

---

**Document Status:** COMPLETE - Ready for Requirements Conversion

**Next Steps:**
1. Convert SRS to EARS-format requirements.md
2. Create design.md with detailed architecture
3. Create tasks.md with implementation plan
