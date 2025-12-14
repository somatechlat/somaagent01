# COMPLETE AGENT SETTINGS CATALOG
## All Tunable Parameters That Should Be in the UI

**Total Settings:** 100+ parameters  
**Sources:** ui_settings_store.py, agent_settings_store.py, AgentConfig, features.py, models.py  
**Storage:** PostgreSQL (non-sensitive), Vault (secrets), Environment (overrides)

---

## 📊 CATEGORY 1: LLM MODELS (4 models × ~8 settings each = 32 settings)

### 1.1 Chat Model (Primary Conversational Model)
| Setting ID | Type | Description | Default | Storage |
|------------|------|-------------|---------|---------|
| `chat_provider` | select | Provider (openai, anthropic, google, azure, groq, mistral, ollama) | openai | PostgreSQL |
| `chat_model_name` | text | Model name | gpt-4.1 | PostgreSQL |
| `chat_base_url` | text | Base URL/API endpoint | https://api.openai.com/v1 | PostgreSQL |
| `chat_context_length` | slider | Context window size | 128000 | PostgreSQL |
| `chat_rpm` | number | Requests per minute limit | 60 | PostgreSQL |
| `chat_tpm` | number | Tokens per minute limit (input+output) | 90000 | PostgreSQL |
| `chat_kwargs` | json | Extra model parameters (temperature, top_p, etc.) | {} | PostgreSQL |
| `chat_vision` | toggle | Enable vision capabilities | true | PostgreSQL |

### 1.2 Utility Model (Low-latency for tool routing)
| Setting ID | Type | Description | Default | Storage |
|------------|------|-------------|---------|---------|
| `utility_provider` | select | Provider (groq, openai, anthropic) | groq | PostgreSQL |
| `utility_model_name` | text | Model name | llama-3.1-70b-versatile | PostgreSQL |
| `utility_base_url` | text | Base URL | - | PostgreSQL |
| `utility_context_length` | slider | Context window size | 32000 | PostgreSQL |
| `utility_rpm` | number | Requests per minute | 120 | PostgreSQL |
| `utility_tpm` | number | Tokens per minute | 120000 | PostgreSQL |
| `utility_kwargs` | json | Extra parameters | {} | PostgreSQL |

### 1.3 Browser Model (For browser automation)
| Setting ID | Type | Description | Default | Storage |
|------------|------|-------------|---------|---------|
| `browser_provider` | select | Provider (openai, anthropic, groq) | openai | PostgreSQL |
| `browser_model_name` | text | Model name | gpt-4o-mini | PostgreSQL |
| `browser_base_url` | text | Base URL | - | PostgreSQL |
| `browser_headers` | json | HTTP headers for browser requests | {} | PostgreSQL |
| `browser_rate_limit` | number | Requests per minute | 60 | PostgreSQL |
| `browser_vision` | toggle | Enable vision | true | PostgreSQL |

### 1.4 Embedding Model (Vector embeddings)
| Setting ID | Type | Description | Default | Storage |
|------------|------|-------------|---------|---------|
| `embedding_provider` | select | Provider (openai, cohere, mistral, voyage) | openai | PostgreSQL |
| `embedding_model_name` | text | Model name | text-embedding-3-large | PostgreSQL |
| `embedding_base_url` | text | Base URL | - | PostgreSQL |
| `embedding_dim` | number | Embedding dimensions | 3072 | PostgreSQL |
| `embedding_kwargs` | json | Extra parameters | {} | PostgreSQL |

---

## 📊 CATEGORY 2: MEMORY & KNOWLEDGE (10 settings)

| Setting ID | Type | Description | Default | Storage |
|------------|------|-------------|---------|---------|
| `recall_enabled` | toggle | Enable memory recall | true | PostgreSQL |
| `recall_delayed` | toggle | Delay recall to improve latency | false | PostgreSQL |
| `recall_interval` | number | Recall interval in seconds | 5 | PostgreSQL |
| `memories_max` | number | Max memories to retrieve | 10 | PostgreSQL |
| `solutions_max` | number | Max solutions to retrieve | 5 | PostgreSQL |
| `similarity_threshold` | slider | Similarity threshold (0-1) | 0.7 | PostgreSQL |
| `memorization_enabled` | toggle | Enable memorization | true | PostgreSQL |
| `consolidation_enabled` | toggle | Enable memory consolidation | true | PostgreSQL |
| `knowledge_subdirectory` | select | Knowledge base subdirectory | default | PostgreSQL |
| `memory_subdir` | text | Memory subdirectory | - | AgentConfig |

---

## 📊 CATEGORY 3: MCP (Model Context Protocol) (6 settings)

### 3.1 MCP Client
| Setting ID | Type | Description | Default | Storage |
|------------|------|-------------|---------|---------|
| `mcp_servers` | json | MCP servers configuration JSON | [] | PostgreSQL |
| `mcp_init_timeout_ms` | number | Initialization timeout (ms) | 8000 | PostgreSQL |
| `mcp_tool_timeout_ms` | number | Tool execution timeout (ms) | 12000 | PostgreSQL |

### 3.2 MCP Server (Built-in)
| Setting ID | Type | Description | Default | Storage |
|------------|------|-------------|---------|---------|
| `mcp_server_enabled` | toggle | Enable built-in MCP server | false | PostgreSQL |
| `mcp_server_endpoint` | text | Server endpoint | http://localhost:8000/mcp | PostgreSQL |
| `mcp_server_token` | password | Authentication token | - | Vault |

---

## 📊 CATEGORY 4: CODE EXECUTION & BROWSER (10 settings)

### 4.1 Code Execution / SSH
| Setting ID | Type | Description | Default | Storage |
|------------|------|-------------|---------|---------|
| `code_exec_ssh_enabled` | toggle | Enable SSH execution | true | AgentConfig |
| `code_exec_ssh_addr` | text | SSH host address | localhost | AgentConfig |
| `code_exec_ssh_port` | number | SSH port | 55022 | AgentConfig |
| `code_exec_ssh_user` | text | SSH username | root | AgentConfig |
| `code_exec_ssh_pass` | password | SSH password | - | Vault |
| `shell_interface` | select | Shell interface (local, ssh) | local | PostgreSQL |

### 4.2 Browser
| Setting ID | Type | Description | Default | Storage |
|------------|------|-------------|---------|---------|
| `browser_http_headers` | json | HTTP headers for requests | {} | AgentConfig |

---

## 📊 CATEGORY 5: EXTERNAL SERVICES (12 settings)

### 5.1 API Keys
| Setting ID | Type | Description | Default | Storage |
|------------|------|-------------|---------|---------|
| `api_key_openai` | password | OpenAI API key | - | Vault |
| `api_key_anthropic` | password | Anthropic API key | - | Vault |
| `api_key_google` | password | Google API key | - | Vault |
| `api_key_groq` | password | Groq API key | - | Vault |
| `api_key_mistral` | password | Mistral API key | - | Vault |

### 5.2 A2A (Agent-to-Agent)
| Setting ID | Type | Description | Default | Storage |
|------------|------|-------------|---------|---------|
|`a2a_enabled` | toggle | Enable A2A bridge | false | PostgreSQL |
| `a2a_endpoint` | text | A2A endpoint URL | - | PostgreSQL |
| `a2a_token` | password | A2A auth token | - | Vault |

### 5.3 Flare Tunnel
| Setting ID | Type | Description | Default | Storage |
|------------|------|-------------|---------|---------|
| `tunnel_enabled` | toggle | Enable tunnel | false | PostgreSQL |
| `tunnel_url` | text | Tunnel URL | - | PostgreSQL |
| `tunnel_auth_token` | password | Tunnel auth token | - | Vault |

---

## 📊 CATEGORY 6: CONNECTIVITY & HEALTH (11 settings)

### 6.1 HTTP/Proxy
| Setting ID | Type | Description | Default | Storage |
|------------|------|-------------|---------|---------|
| `http_proxy` | text | HTTP proxy URL | - | PostgreSQL |
| `https_proxy` | text | HTTPS proxy URL | - | PostgreSQL |
| `sse_retry_ms` | number | SSE retry interval (ms) | 1000 | PostgreSQL |
| `timeout_seconds` | number | Request timeout (seconds) | 30 | PostgreSQL |

### 6.2 Speech (STT/TTS)
| Setting ID | Type | Description | Default | Storage |
|------------|------|-------------|---------|---------|
| `speech_provider` | select | Provider (browser, realtime, kokoro) | browser | PostgreSQL |
| `speech_language` | text | Language code | en-US | PostgreSQL |
| `speech_realtime_model` | text | Realtime model | gpt-4o-realtime | PostgreSQL |
| `speech_voice` | text | Voice name | alloy | PostgreSQL |
| `speech_vad_threshold` | number | Voice activity detection threshold | 0.5 | PostgreSQL |

### 6.3 Health & Monitoring
| Setting ID | Type | Description | Default | Storage |
|------------|------|-------------|---------|---------|
| `health_poll_interval` | number | Poll interval (seconds) | 30 | PostgreSQL |
| `health_degradation_threshold` | number | Degradation threshold percentage | 30 | PostgreSQL |
| `health_alerts_enabled` | toggle | Enable health alerts | true | PostgreSQL |

---

## 📊 CATEGORY 7: SYSTEM & SECURITY (10 settings)

### 7.1 Authentication
| Setting ID | Type | Description | Default | Storage |
|------------|------|-------------|---------|---------|
| `auth_username` | text | Username | - | PostgreSQL |
| `auth_password` | password | Password | - | Vault |
| `auth_password_confirm` | password | Confirm password (UI only) | - | - |
| `root_password` | password | Docker root password | - | Vault |

### 7.2 Backup & Restore
| Setting ID | Type | Description | Default | Storage |
|------------|------|-------------|---------|---------|
| `backup_auto` | toggle | Enable auto backup | false | PostgreSQL |
| `backup_location` | text | Backup directory path | /var/backups | PostgreSQL |
| `restore_file` | file | Restore file path | - | - |

### 7.3 Developer
| Setting ID | Type | Description | Default | Storage |
|------------|------|-------------|---------|---------|
| `rfc_host` | text | RFC host | 127.0.0.1 | PostgreSQL |
| `rfc_port` | number | RFC port | 6000 | PostgreSQL |
| `debug_mode` | toggle | Enable debug mode | false | PostgreSQL |

### 7.4 Secrets
| Setting ID | Type | Description | Default | Storage |
|------------|------|-------------|---------|---------|
| `secrets_blob` | json | Opaque secrets JSON | {} | PostgreSQL |

---

## 📊 CATEGORY 8: FEATURE FLAGS (14 flags from features.py)

| Feature Key | Description | Profiles (min/std/enh/max) | Default | Storage |
|-------------|-------------|----------------------------|---------|---------|
| `sse_enabled` | Server-sent events | F/T/T/T | enhanced | Environment |
| `embeddings_ingest` | Embedding ingestion | F/F/T/T | enhanced | Environment |
| `semantic_recall` | Semantic memory recall | F/T/T/T | enhanced | Environment |
| `content_masking` | PII/secret masking | F/T/T/T | enhanced | Environment |
| `audio_support` | Audio/speech support | F/F/T/T | enhanced | Environment |
| `browser_support` | Browser automation | F/F/T/T | enhanced | Environment |
| `code_exec_support` | Code execution | T/T/T/T | enhanced | Environment |
| `vision_support` | Vision/image analysis | F/T/T/T | enhanced | Environment |
| `mcp_client` | MCP client | F/T/T/T | enhanced | Environment |
| `mcp_server` | MCP server | F/F/T/T | enhanced | Environment |
| `learning_context` | Context learning | F/F/T/T | enhanced | Environment |
| `tool_sandboxing` | Tool isolation | F/F/T/T | enhanced | Environment |
| `streaming_responses` | Streaming responses | T/T/T/T | enhanced | Environment |
| `delegation` | Agent delegation | F/F/T/T | enhanced | Environment |

**Feature Flag Environment Override:**
- Global profile: `SA01_FEATURE_PROFILE=enhanced`
- Individual flags: `SA01_ENABLE_<FEATURE_KEY>=true/false`

---

## ADDITIONAL SETTINGS (from AgentConfig)

| Setting ID | Type | Description | Default | Storage |
|------------|------|-------------|---------|---------|
| `profile` | select | Agent profile (minimal, standard, enhanced, max) | enhanced | AgentConfig |
| `knowledge_subdirs` | json | Knowledge subdirectories | ["default", "custom"] | AgentConfig |
| `additional` | json | Additional configuration | {} | AgentConfig |

---

## SUMMARY BY STORAGE LOCATION

**PostgreSQL (ui_settings table):** ~60 settings (non-sensitive)
- All LLM model configs (except API keys)
- Memory & knowledge settings
- MCP settings (except tokens)
- Connectivity & health
- System settings (except passwords)

**Vault (via UnifiedSecretManager):** ~10 secrets
- All API keys (openai, anthropic, google, groq, mistral)
- Auth passwords
- SSH passwords
- MCP tokens
- A2A/tunnel tokens

**Environment Variables:** 14 feature flags
- Profile selection: `SA01_FEATURE_PROFILE`
- Individual overrides: `SA01_ENABLE_<KEY>`

**AgentConfig (code-level):** ~5 settings
- Agent profile
- Memory/knowledge subdirs
- SSH config
- Browser headers
- Additional config

---

## TOTAL: 100+ TUNABLE SETTINGS

### By Category:
1. **LLM Models**: 32 settings
2. **Memory & Knowledge**: 10 settings
3. **MCP**: 6 settings
4. **Code Execution & Browser**: 7 settings
5. **External Services**: 12 settings
6. **Connectivity & Health**: 11 settings
7. **System & Security**: 10 settings
8. **Feature Flags**: 14 flags

### By Type:
- **Text fields**: ~30
- **Numbers**: ~20
- **Toggles**: ~25
- **Selects**: ~10
- **JSON**: ~10
- **Passwords**: ~10
- **Sliders**: ~3

---

## IMPLEMENTATION NOTES

1. **Current UI Coverage**: The existing `ui_settings_store.py` already defines 17 sections with most of these settings
2. **Missing from UI**: Feature flags (14), AgentConfig overrides (5)
3. **Secret Handling**: Passwords show as `************` in UI, stored in Vault
4. **Validation**: Each setting should have validation rules (min/max, regex, schema)
5. **Dependencies**: Some settings depend on others (e.g., `chat_vision` requires vision-capable model)
6. **Real-time Updates**: Settings changes should trigger agent reload/reconfiguration
7. **Import/Export**: Support for exporting settings as JSON for backup/migration
