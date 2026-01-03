# SomaAgent01 — Web UI Requirements (AgentSkin + Admin Console)

**Scope**  
A greenfield Web UI (no legacy) that delivers:  
1) Themed AgentSkin experience (chat-first) with installable modules.  
2) Admin console to manage modes, personas/capsules, tools/models, memory, uploads, security, and observability.  

**Non‑Goals**  
- No backward compatibility with the previous webui.  
- No stub/placeholder features; everything must be real or clearly marked read-only.  

---

## 1) UI Architecture
- **Shell layout**: top bar (status, mode badge, theme switch, command palette), left rail (nav + modules), main canvas (router outlet), right rail (context/decision trace), global toasts/modals.  
- **Design tokens**: AgentSkin 26 required CSS vars (bg, text, accent, semantic, borders, shadows, interactive, gradients) plus animations: theme-switch 300 ms blur/fade; card hover lift/scale.  
- **Routing**: hash or lightweight router; module routes under `/m/{moduleId}`; admin routes under `/admin/*`.  
- **Data stores (frontend)**:  
  - `themeStore` (active theme, preview, cache)  
  - `modulesStore` (manifests, enable/disable, load state)  
  - `settingsStore` (user-scoped UI prefs)  
  - `adminStore` (mode, persona defaults, tool gates, policies)  
  - `eventBus` (pub/sub for modules, decision trace, notifications)  
- **Module system**:  
  - Manifest (JSON) with id, name, version, entry ES module, routes/panels/commands, permissions, i18n, styles (namespaced vars), integrity hash, optional signature.  
  - Loader validates manifest (AJV), HTTPS-only, optional SRI; sandbox via iframe for untrusted modules.  
  - Capability registry: routes, panels, widgets, command-palette actions.  
- **Themes**:  
  - Load local `/themes/{name}.json` or remote HTTPS; validate against `agentskin.schema.json`; block `url(`; enforce WCAG AA on key pairs.  
  - Persist `active-theme`, `theme-{name}` in localStorage; emit `theme-changed`.  
  - Theme gallery (grid, preview, drag/drop import, split-screen preview, revert).  

---

## 2) Core Screens
- **Chat workspace**: message list, composer, attachments, streaming, decision trace panel, persona selector.  
- **Settings (user)**: theme, speech devices, proxies/timeouts, personal shortcuts.  
- **Admin console** (see Section 3).  
- **Modules**: first-party Project module (kanban/table/detail), future plugins.  

---

## 3) Admin Console (separate from user settings)
- **Modes**: Training / Testing / Production (admin-only). Each mode applies safety/profile defaults, tool/model allowlists, logging level, outbound restrictions.  
- **Personas & Capsules**: CRUD personas (id, name, description, constitution ref); set default persona per user/tenant/capsule; persona tool/model loadouts; persona budgets; capsule default persona.  
- **Tools & Models**: enable/disable per mode/tenant/persona; sandbox flag; concurrency and timeout per tool; map models (LLM/utility/embedding/vision) to personas/capsules/modes; confidence scoring toggle/mode.  
- **Memory & SomaBrain**: base URL/API key/TLS, retries; namespace; semantic recall toggle; cache WM limit; retention/redaction settings; persona-scoped memory views.  
- **Uploads & Attachments**: uploads enable, max size/files, ClamAV on/off, stream max, quarantine flag; attachment quota/usage (read-only); persona tagging.  
- **Policy & Security**: OPA/OpenFGA endpoints, data path, cache TTL, fail-open (admin only), internal token, JWT secret (masked), Vault addr/namespace/token/verify, masking rules paths.  
- **Observability & Ops**: log level, OTLP endpoint, health polling intervals, degradation thresholds, circuit breaker metrics host/port, service metrics ports (read-only).  
- **Kafka/Temporal status**: show hosts/queues/topics (read-only); allow topic/queue overrides only for admin.  
- **Backups**: trigger/restore; backup location.  
- **Audit**: log every admin change (who, what, mode, persona/tenant scope).  

---

## 4) Settings Catalog (admin vs. user)

### User Settings (end-user)
**Theme & Personalization**  
- `theme`, `theme_mode`, `theme_preview`.  
**Persona & Session**  
- `persona_current`, `session_restore_persona`.  
**Connectivity**  
- `gateway_base_url`, `sse_enabled`, `http_proxy`, `https_proxy`, `request_timeout_seconds`, `sse_retry_ms`.  
**Speech/Audio**  
- `speech_provider`, `speech_language`, `speech_voice`, `speech_vad_threshold`, `audio_feature_enabled`.  
**Shortcuts & UI**  
- `command_palette_shortcut`, `toast_position`, `density`.  

### Admin Settings — screen by screen
**A. Environment & Modes**  
- `mode`, `mode_profile`, `mode_logging_level`, `mode_tool_allowlist`, `mode_tool_denylist`, `mode_model_tier`, `mode_outbound_restrictions`.  

**B. Personas & Capsules**  
- Personas: `persona_id`, `name`, `description`, `constitution_ref`, `tags`; defaults per user/tenant/capsule; budgets `budget_limit`, `budget_prefix`; persona feature flags; persona tool/model loadouts.  
- Capsules: `default_persona_ref_id`, `role_overrides`, tags.  

**C. Models & LLMs**  
- Chat LLM: `provider`, `model`, `base_url`, `context_length`, `rpm`, `tpm`, `kwargs`, `vision_enabled`, `history_fraction` (`chat_model_ctx_history`), rate limits (`chat_model_rl_requests`, `chat_model_rl_input`, `chat_model_rl_output`).  
- Utility LLM: `provider`, `model`, `base_url`, `context_length`, `rpm`, `tpm`, `kwargs`, `history_fraction` (`util_model_ctx_input`), rate limits (`util_model_rl_requests`, `util_model_rl_input`, `util_model_rl_output`).  
- Browser/tool LLM: `provider`, `model`, `base_url`, `headers`, `rate_limit_rpm` (via RL fields), `vision_enabled`, `kwargs`.  
- Embeddings: `provider`, `model`, `dim`, `base_url`, `timeout_seconds` (`EMBEDDINGS_TIMEOUT`), `max_chars` (`EMBEDDINGS_MAX_CHARS`), `kwargs`, rate limits (`embed_model_rl_requests`, `embed_model_rl_input`, `embed_model_rl_output`).  
- Model Profiles (DB): per `role` + `deployment_mode` → `model`, `base_url`, `api_path`, `temperature`, `extra` (kwargs). Admin UI must list/create/update/delete profiles and bind roles to modes.  
- Global toggles: `enable_multimodal` (SA01_ENABLE_MULTIMODAL_CAPABILITIES), `confidence_enabled`, `confidence_aggregation`, `gemini_compat_enabled`, `json_cleaning_enabled`, `llm_http_timeout`.  
- API keys (masked): `api_key_openai`, `api_key_anthropic`, `api_key_google`, `api_key_groq`, `api_key_mistral`.  

**D. Tools & Executor**  
- `tool_executor_max_concurrent`; `tool_executor_circuit_failure_threshold`; `tool_executor_circuit_reset_timeout_seconds`; `sa01_multimodal_poll_interval`; `canvas_service_url`; `canvas_service_timeout`; `tool_work_dir`; `tool_fetch_timeout`; `sa01_use_outbox`; `tool_sandboxing`; per-tool allow/deny + `timeout`/`concurrency`.  

**E. Memory & SomaBrain**  
- `sa01_soma_base_url`, `sa01_soma_api_key` (masked), `sa01_soma_tenant_id`, `sa01_namespace`, `sa01_memory_namespace`; TLS: `sa01_verify_ssl`, `sa01_tls_ca`, `sa01_tls_cert`, `sa01_tls_key`; timeouts/retries `sa01_soma_timeout_seconds`, `sa01_soma_max_retries`, `sa01_soma_retry_base_ms`; `sa01_semantic_recall_prototype`; `sa01_cache_wm_limit`; recall controls (enabled/delayed/interval/search/result limits/similarity/memorization/consolidation/knowledge_subdir); retention/redaction (`masking_rules_file`, `masking_rules_inline`, `log_redact_token_prefixes`).  

**F. Uploads & Attachments**  
- `uploads_enabled`, `uploads_max_mb`, `uploads_max_files`, `sa01_upload_max_size`; ClamAV: `sa01_clamav_enabled`, `sa01_clamav_stream_max_bytes`, `sa01_clamav_socket`, `sa01_clamav_host`, `sa01_clamav_port`, `sa01_upload_quarantine_on_error`; `sa01_upload_topic`; read-only `disk_usage_bytes`, `max_bytes`.  

**G. Policy & Security**  
- `auth_required`, `sa01_auth_internal_token` (masked), `sa01_jwt_secret` (masked); OPA: `policy_base_url`, `policy_evaluate_url`, `sa01_policy_data_path`, `sa01_policy_cache_ttl`, `sa01_opa_fail_open`; OpenFGA: `sa01_openfga_api_url`, `sa01_openfga_store_id`, `sa01_openfga_cache_ttl`, `sa01_openfga_timeout_seconds`; `policy_requeue_prefix`; Vault: `vault_addr`, `vault_namespace`, `vault_token`/`vault_token_file`, `vault_skip_verify`, `vault_ca_cert`; Masking: `sa01_mask_rules`, `sa01_mask_rules_file`, `log_redact_token_prefixes`.  

**H. Connectivity / Realtime / Routing**  
- `sse_enabled`; Temporal: `sa01_temporal_host`, `sa01_temporal_conversation_queue`, `sa01_temporal_tool_queue`, `sa01_temporal_a2a_queue`; `router_url`; `sa01_worker_gateway_base`; display `sa01_gateway_base_url`; `http_proxy`, `https_proxy`, `request_timeout_seconds`.  

**I. Observability & Health**  
- `log_level`, `sa01_otlp_endpoint`, `health_poll_interval`, `health_degradation_threshold`, `health_alerts_enabled`, `circuit_breaker_metrics_host`, `circuit_breaker_metrics_port`; read-only service metrics hosts/ports.  

**J. Kafka / Event Bus**  
- `kafka_bootstrap_servers`; `kafka_security_protocol`, `kafka_sasl_mechanism`, `kafka_sasl_username`, `kafka_sasl_password`; topics: `conversation_inbound`, `conversation_outbound`, `tool_requests`, `tool_results`, `memory_wal`, `a2a_topic`, `a2a_out_topic`, `delegation_topic`, `audit_topic`, `policy_requeue_prefix`, `task_feedback_topic`.  

**K. Data Stores**  
- `sa01_db_dsn`/`postgres_dsn`, `pg_pool_min_size`, `pg_pool_max_size`; `redis_url`/`sa01_redis_url`.  

**L. Backups & Developer**  
- `backup_auto`, `backup_location`, `restore_file`; `shell_interface` (local/ssh), `rfc_host`, `rfc_port_http`, `rfc_port_ssh`, `debug_mode`.  

**M. Modules & Theme Assets**  
- Module manifest allowlist; install/enable/disable; validate via `module.manifest.schema.json`.  
- Theme import/export per `agentskin.schema.json`; curated themes list; enforce no vendored TODO/FIXME/XXX/HACK.  

**N. Admin Mode Controls (Safety)**  
- Mode change confirmation/scheduling; mode-driven overrides (feature profile, tool/model tiers, outbound restrictions, logging level, rate limits).  

---

## 5) Modes & Safety Model
- Training/Testing/Production modes must drive: model/tool allowlists, rate limits, logging level, outbound restrictions, and safety policies.  
- Mode changes are admin-only, audited, and optionally scheduled.  

---

## 6) Personas/Constitution Model
- Personas represent agent roles (e.g., Researcher, Marketing Expert); each can bind: tools, models, budgets, feature flags, policies, memory scope, capsule defaults, and constitution reference.  
- Constitution text/source stored in persona record or linked document; surfaced read-only in UI with edit where allowed.  

---

## 7) Module & Theme Assets
- Schemas required: `agentskin.schema.json`, `module.manifest.schema.json`.  
- Themes live in `/themes`; modules load via manifest (HTTPS, validated).  
- No vendored assets with TODO/FIXME/XXX/HACK tokens.  

---

## 8) UX/Accessibility/Performance
- WCAG AA across themes; keyboard navigation for all controls.  
- Theme switch ≤300 ms; chat latency targets unchanged (server-side).  
- No inline secrets; masked fields with reveal + copy guarded by role.  

---

## Appendix A — Environment / cfg.env Inventory (extracted repo-wide)
`A2A_OUT_TOPIC`, `A2A_TOKEN`, `A2A_TOPIC`, `AUDIT_TOPIC`, `AUTH_REQUIRED`, `BASE_URL`, `BUDGET_PREFIX`, `CANVAS_SERVICE_TIMEOUT`, `CANVAS_SERVICE_URL`, `CIRCUIT_BREAKER_METRICS_HOST`, `CIRCUIT_BREAKER_METRICS_PORT`, `CONFIDENCE_AGGREGATION`, `CONFIDENCE_ENABLED`, `CONTEXT_BUILDER_OPTIMAL_BUDGET`, `CONVERSATION_GROUP`, `CONVERSATION_INBOUND`, `CONVERSATION_METRICS_HOST`, `CONVERSATION_METRICS_PORT`, `CONVERSATION_OUTBOUND`, `DELEGATION_GROUP`, `DELEGATION_METRICS_HOST`, `DELEGATION_METRICS_PORT`, `DELEGATION_TOPIC`, `DEPLOYMENT_MODE`, `E2E_EXPECT_MEMORY`, `E2E_HTTP_TIMEOUT`, `E2E_LIVE`, `E2E_POLL_INTERVAL`, `E2E_POLL_TIMEOUT`, `EMBEDDINGS_MAX_CHARS`, `EMBEDDINGS_MODEL`, `EMBEDDINGS_TEST_MODE`, `EMBEDDINGS_TIMEOUT`, `FASTA2A_HEALTH_URL`, `FEATURE_AUDIO`, `FEATURE_FLAGS_TTL_SECONDS`, `GATEWAY_BASE`, `GATEWAY_DISABLE_SSE`, `GATEWAY_HEALTH_URL`, `HEADLESS`, `INTERNAL_API_TOKEN`, `JWT`, `KAFKA_BOOTSTRAP_SERVERS`, `KAFKA_SASL_MECHANISM`, `KAFKA_SASL_PASSWORD`, `KAFKA_SASL_USERNAME`, `KAFKA_SECURITY_PROTOCOL`, `LLM_HTTP_TIMEOUT`, `LOG_LEVEL`, `LOG_REDACT_TOKEN_PREFIXES`, `MEMORY_REPLICATOR_GROUP`, `MEMORY_WAL_TOPIC`, `MESSAGE`, `OPENAI_API_KEY`, `OPENAI_BASE_URL`, `PATH`, `PERSONA_ID`, `PG_POOL_MAX_SIZE`, `PG_POOL_MIN_SIZE`, `PLAYWRIGHT_MODE`, `POLICY_BASE_URL`, `POLICY_EVALUATE_URL`, `POLICY_REQUEUE_PREFIX`, `PORT`, `POSTGRES_DSN`, `PUBLISH_KAFKA_TIMEOUT_SECONDS`, `READINESS_CHECK_TIMEOUT`, `READINESS_DISABLE_KAFKA`, `REDIS_URL`, `REPLICATOR_METRICS_HOST`, `REPLICATOR_METRICS_PORT`, `ROUTER_URL`, `SA01_AUTH_HEADER`, `SA01_AUTH_INTERNAL_TOKEN`, `SA01_BASE_URL`, `SA01_CACHE_WM_LIMIT`, `SA01_CAPSULE_REGISTRY_URL`, `SA01_CLAMAV_ENABLED`, `SA01_CLAMAV_HOST`, `SA01_CLAMAV_PORT`, `SA01_CLAMAV_SOCKET`, `SA01_CLAMAV_STREAM_MAX_BYTES`, `SA01_CONTAINER_HOST_ALIAS`, `SA01_CRYPTO_FERNET_KEY`, `SA01_DB_DSN`, `SA01_ENABLE_MULTIMODAL_CAPABILITIES`, `SA01_FEATURE_PROFILE`, `SA01_GATEWAY_BASE`, `SA01_GATEWAY_BASE_URL`, `SA01_GATEWAY_INTERNAL_TOKEN`, `SA01_GEMINI_COMPAT_ENABLED`, `SA01_JSON_CLEANING_ENABLED`, `SA01_JWT_SECRET`, `SA01_KAFKA_BOOTSTRAP_SERVERS`, `SA01_LLM_BASE_URL`, `SA01_LLM_MODEL`, `SA01_MASK_RULES`, `SA01_MASK_RULES_FILE`, `SA01_MEMORY_NAMESPACE`, `SA01_MULTIMODAL_POLL_INTERVAL`, `SA01_MY_SETTING`, `SA01_NAMESPACE`, `SA01_OPA_FAIL_OPEN`, `SA01_OPENFGA_API_URL`, `SA01_OPENFGA_CACHE_TTL`, `SA01_OPENFGA_STORE_ID`, `SA01_OPENFGA_TIMEOUT_SECONDS`, `SA01_OTLP_ENDPOINT`, `SA01_POLICY_CACHE_TTL`, `SA01_POLICY_DATA_PATH`, `SA01_REDIS_URL`, `SA01_SEMANTIC_RECALL_PROTOTYPE`, `SA01_SOMA_API_KEY`, `SA01_SOMA_BASE_URL`, `SA01_SOMA_MAX_RETRIES`, `SA01_SOMA_RETRY_BASE_MS`, `SA01_SOMA_TENANT_ID`, `SA01_SOMA_TIMEOUT_SECONDS`, `SA01_TEMPORAL_A2A_QUEUE`, `SA01_TEMPORAL_CONVERSATION_QUEUE`, `SA01_TEMPORAL_HOST`, `SA01_TEMPORAL_TOOL_QUEUE`, `SA01_TENANT_HEADER`, `SA01_TENANT_ID`, `SA01_TLS_CA`, `SA01_TLS_CERT`, `SA01_TLS_KEY`, `SA01_UPLOAD_MAX_SIZE`, `SA01_UPLOAD_QUARANTINE_ON_ERROR`, `SA01_UPLOAD_TOPIC`, `SA01_USE_OUTBOX`, `SA01_VERIFY_SSL`, `SA01_WORKER_GATEWAY_BASE`, `SEARXNG_URL`, `SSE_ENABLED`, `TARGET_URL`, `TASK_FEEDBACK_TOPIC`, `TENANT`, `TENANT_CONFIG_PATH`, `TOOL_EXECUTOR_CIRCUIT_FAILURE_THRESHOLD`, `TOOL_EXECUTOR_CIRCUIT_RESET_TIMEOUT_SECONDS`, `TOOL_EXECUTOR_GROUP`, `TOOL_EXECUTOR_MAX_CONCURRENT`, `TOOL_EXECUTOR_METRICS_HOST`, `TOOL_EXECUTOR_METRICS_PORT`, `TOOL_FETCH_TIMEOUT`, `TOOL_REQUESTS_TOPIC`, `TOOL_RESULTS_TOPIC`, `TOOL_WORK_DIR`, `UI_BASE_URL`, `VAULT_ADDR`, `VAULT_CA_CERT`, `VAULT_NAMESPACE`, `VAULT_SKIP_VERIFY`, `VAULT_TOKEN`, `VAULT_TOKEN_FILE`, `WEB_UI_BASE_URL`, `WORKDIR`.  
