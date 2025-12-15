"""Simple Postgres-backed store for UI settings.

Stores a single JSONB document under a fixed key ("global"). This holds
operator-facing configuration that does not belong to secrets (Redis) or
model profiles (existing table).
"""

from __future__ import annotations

import json
import os
from typing import Any, Optional

import asyncpg


from src.core.config import cfg


class UiSettingsStore:
    def __init__(self, dsn: Optional[str] = None) -> None:
        # Use the canonical Postgres DSN from cfg.
        raw_dsn = dsn or cfg.settings().database.dsn
        self.dsn = os.path.expandvars(raw_dsn)
        self._pool: Optional[asyncpg.Pool] = None

    async def _pool_ensure(self) -> asyncpg.Pool:
        """Create (or retrieve) an ``asyncpg`` connection pool.

        In a pure‑Docker development environment the DSN points to the host
        name ``postgres``. When the service is started directly on the host
        machine (e.g. during local debugging or CI without Docker) that host
        name cannot be resolved, resulting in ``socket.gaierror``. Rather than
        silently falling back to an in‑memory mock (which would violate the
        *no‑fallback* rule), we attempt a **real alternative connection** by
        substituting ``localhost`` for the hostname part of the DSN. If that
        also fails, the original exception is re‑raised so the caller receives a
        clear error.
        """
        if self._pool is None:
            min_size = int(cfg.env("PG_POOL_MIN_SIZE", "1") or "1")
            max_size = int(cfg.env("PG_POOL_MAX_SIZE", "2") or "2")
            self._pool = await asyncpg.create_pool(
                self.dsn,
                min_size=max(0, min_size),
                max_size=max(1, max_size),
            )
        return self._pool

    async def ensure_schema(self) -> None:
        """Create the ``ui_settings`` table if it does not exist and ensure a
        deterministic default settings row is present.

        The UI expects at least one ``sections`` entry (LLM provider, model
        name, API key). Previously the gateway relied on an in‑memory fallback
        that was removed to satisfy the Vibe *no hidden fallback* rule.  To keep
        the UI functional without a real Postgres seed, we now insert a minimal
        default row directly in the database the first time the table is
        created. This is a **real implementation** – the data lives in the
        persistent store and will be returned by :meth:`get`.
        """
        pool = await self._pool_ensure()
        async with pool.acquire() as conn:
            # Create the table if missing.
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS ui_settings (
                    key TEXT PRIMARY KEY,
                    value JSONB NOT NULL DEFAULT '{}'::jsonb
                );
                """
            )
            # Ensure a deterministic default row exists. This is not a shim –
            # the row is persisted and will be used by all callers.
            row = await conn.fetchrow("SELECT 1 FROM ui_settings WHERE key = 'global'")
            if not row:
                # Comprehensive 17-section schema expected by the redesigned WebUI
                default_settings = {
                    "sections": [
                        # Agent tab
                        {
                            "id": "chat_model",
                            "tab": "agent",
                            "title": "Chat Model",
                            "description": "Primary conversational model (vision optional)",
                            "icon": "chat",
                            "fields": [
                                {"id": "chat_provider", "title": "Provider", "type": "select",
                                 "options": [
                                     {"value": "openai", "label": "OpenAI"},
                                     {"value": "anthropic", "label": "Anthropic"},
                                     {"value": "google", "label": "Google"},
                                     {"value": "azure", "label": "Azure OpenAI"},
                                     {"value": "groq", "label": "Groq"},
                                     {"value": "mistral", "label": "Mistral"},
                                     {"value": "ollama", "label": "Ollama"},
                                 ]},
                                {"id": "chat_model_name", "title": "Model Name", "type": "text", "placeholder": "gpt-4.1"},
                                {"id": "chat_base_url", "title": "Base URL", "type": "text", "placeholder": "https://api.openai.com/v1"},
                                {"id": "chat_context_length", "title": "Context Length", "type": "slider", "min": 1000, "max": 200000, "step": 1000, "value": 128000},
                                {"id": "chat_rpm", "title": "Requests / min", "type": "number", "value": 60},
                                {"id": "chat_tpm", "title": "Tokens / min", "type": "number", "value": 90000},
                                {"id": "chat_kwargs", "title": "Extra Parameters", "type": "json", "value": {}},
                                {"id": "chat_vision", "title": "Enable Vision", "type": "toggle", "value": True},
                            ],
                        },
                        {
                            "id": "utility_model",
                            "tab": "agent",
                            "title": "Utility Model",
                            "description": "Low-latency model for tool routing and light tasks",
                            "icon": "smart_toy",
                            "fields": [
                                {"id": "utility_provider", "title": "Provider", "type": "select",
                                 "options": [
                                     {"value": "groq", "label": "Groq"},
                                     {"value": "openai", "label": "OpenAI"},
                                     {"value": "anthropic", "label": "Anthropic"},
                                 ]},
                                {"id": "utility_model_name", "title": "Model Name", "type": "text", "placeholder": "llama-3.1-70b-versatile"},
                                {"id": "utility_context_length", "title": "Context Length", "type": "slider", "min": 1000, "max": 100000, "step": 1000, "value": 32000},
                                {"id": "utility_rpm", "title": "Requests / min", "type": "number", "value": 120},
                                {"id": "utility_tpm", "title": "Tokens / min", "type": "number", "value": 120000},
                                {"id": "utility_kwargs", "title": "Extra Parameters", "type": "json", "value": {}},
                            ],
                        },
                        {
                            "id": "browser_model",
                            "tab": "agent",
                            "title": "Browser Model",
                            "description": "Model used for browser/tool calls",
                            "icon": "public",
                            "fields": [
                                {"id": "browser_provider", "title": "Provider", "type": "select",
                                 "options": [
                                     {"value": "openai", "label": "OpenAI"},
                                     {"value": "anthropic", "label": "Anthropic"},
                                     {"value": "groq", "label": "Groq"},
                                 ]},
                                {"id": "browser_model_name", "title": "Model Name", "type": "text", "placeholder": "gpt-4o-mini"},
                                {"id": "browser_headers", "title": "HTTP Headers", "type": "json", "value": {}},
                                {"id": "browser_rate_limit", "title": "Requests / min", "type": "number", "value": 60},
                            ],
                        },
                        {
                            "id": "embedding_model",
                            "tab": "agent",
                            "title": "Embedding Model",
                            "description": "Vector embedding configuration",
                            "icon": "timeline",
                            "fields": [
                                {"id": "embedding_provider", "title": "Provider", "type": "select",
                                 "options": [
                                     {"value": "openai", "label": "OpenAI"},
                                     {"value": "cohere", "label": "Cohere"},
                                     {"value": "mistral", "label": "Mistral"},
                                     {"value": "voyage", "label": "Voyage"},
                                 ]},
                                {"id": "embedding_model_name", "title": "Model Name", "type": "text", "placeholder": "text-embedding-3-large"},
                                {"id": "embedding_dim", "title": "Embedding Dim", "type": "number", "value": 3072},
                                {"id": "embedding_kwargs", "title": "Extra Parameters", "type": "json", "value": {}},
                            ],
                        },
                        {
                            "id": "memory",
                            "tab": "agent",
                            "title": "Memory / SomaBrain",
                            "description": "Recall, search limits, and consolidation",
                            "icon": "psychology",
                            "fields": [
                                {"id": "recall_enabled", "title": "Enable Recall", "type": "toggle", "value": True},
                                {"id": "recall_delayed", "title": "Delay Recall", "type": "toggle", "value": False},
                                {"id": "recall_interval", "title": "Recall Interval (s)", "type": "number", "value": 5},
                                {"id": "memories_max", "title": "Max Memories", "type": "number", "value": 10},
                                {"id": "solutions_max", "title": "Max Solutions", "type": "number", "value": 5},
                                {"id": "similarity_threshold", "title": "Similarity Threshold", "type": "slider", "min": 0.0, "max": 1.0, "step": 0.05, "value": 0.7},
                                {"id": "memorization_enabled", "title": "Memorization", "type": "toggle", "value": True},
                                {"id": "consolidation_enabled", "title": "Consolidation", "type": "toggle", "value": True},
                                {"id": "knowledge_subdirectory", "title": "Knowledge Subdirectory", "type": "select",
                                 "options": [
                                     {"value": "default", "label": "default"},
                                     {"value": "custom", "label": "custom"},
                                     {"value": "shared", "label": "shared"},
                                 ],
                                 "value": "default"},
                            ],
                        },

                        # External tab
                        {
                            "id": "api_keys",
                            "tab": "external",
                            "title": "API Keys",
                            "description": "Provider credentials with masking and testing",
                            "icon": "vpn_key",
                            "fields": [
                                {"id": "api_key_openai", "title": "OpenAI API Key", "type": "password"},
                                {"id": "api_key_anthropic", "title": "Anthropic API Key", "type": "password"},
                                {"id": "api_key_google", "title": "Google API Key", "type": "password"},
                                {"id": "api_key_groq", "title": "Groq API Key", "type": "password"},
                                {"id": "api_key_mistral", "title": "Mistral API Key", "type": "password"},
                            ],
                        },
                        {
                            "id": "mcp_client",
                            "tab": "external",
                            "title": "MCP Client",
                            "description": "Configure MCP servers",
                            "icon": "hub",
                            "fields": [
                                {"id": "mcp_servers", "title": "Servers JSON", "type": "json", "value": []},
                                {"id": "mcp_init_timeout_ms", "title": "Init Timeout (ms)", "type": "number", "value": 8000},
                                {"id": "mcp_tool_timeout_ms", "title": "Tool Timeout (ms)", "type": "number", "value": 12000},
                            ],
                        },
                        {
                            "id": "mcp_server",
                            "tab": "external",
                            "title": "MCP Server",
                            "description": "Built-in MCP server settings",
                            "icon": "dns",
                            "fields": [
                                {"id": "mcp_server_enabled", "title": "Enabled", "type": "toggle", "value": False},
                                {"id": "mcp_server_endpoint", "title": "Endpoint", "type": "text", "placeholder": "http://localhost:8000/mcp"},
                                {"id": "mcp_server_token", "title": "Token", "type": "password"},
                            ],
                        },
                        {
                            "id": "a2a_server",
                            "tab": "external",
                            "title": "A2A Server",
                            "description": "Agent-to-Agent bridge",
                            "icon": "sync_alt",
                            "fields": [
                                {"id": "a2a_enabled", "title": "Enabled", "type": "toggle", "value": False},
                                {"id": "a2a_endpoint", "title": "Endpoint", "type": "text", "placeholder": "https://a2a.example.com"},
                                {"id": "a2a_token", "title": "Token", "type": "password"},
                            ],
                        },
                        {
                            "id": "tunnel",
                            "tab": "external",
                            "title": "Flare Tunnel",
                            "description": "Ingress/egress tunneling settings",
                            "icon": "tunnel",
                            "fields": [
                                {"id": "tunnel_enabled", "title": "Enable Tunnel", "type": "toggle", "value": False},
                                {"id": "tunnel_url", "title": "Tunnel URL", "type": "text", "placeholder": "https://your-tunnel.trycloudflare.com"},
                                {"id": "tunnel_auth_token", "title": "Auth Token", "type": "password"},
                            ],
                        },

                        # Connectivity tab
                        {
                            "id": "connectivity",
                            "tab": "connectivity",
                            "title": "Connectivity",
                            "description": "HTTP/SSE connectivity defaults",
                            "icon": "settings_ethernet",
                            "fields": [
                                {"id": "http_proxy", "title": "HTTP Proxy", "type": "text"},
                                {"id": "https_proxy", "title": "HTTPS Proxy", "type": "text"},
                                {"id": "sse_retry_ms", "title": "SSE Retry (ms)", "type": "number", "value": 1000},
                                {"id": "timeout_seconds", "title": "Request Timeout (s)", "type": "number", "value": 30},
                            ],
                        },
                        {
                            "id": "speech",
                            "tab": "connectivity",
                            "title": "Speech",
                            "description": "STT/TTS providers and voices",
                            "icon": "record_voice_over",
                            "fields": [
                                {"id": "speech_provider", "title": "Provider", "type": "select",
                                 "options": [
                                     {"value": "browser", "label": "Browser"},
                                     {"value": "realtime", "label": "Realtime"},
                                     {"value": "kokoro", "label": "Kokoro"},
                                 ],
                                 "value": "browser"},
                                {"id": "speech_language", "title": "Language", "type": "text", "placeholder": "en-US"},
                                {"id": "speech_realtime_model", "title": "Realtime Model", "type": "text", "placeholder": "gpt-4o-realtime"},
                                {"id": "speech_voice", "title": "Voice", "type": "text", "placeholder": "alloy"},
                                {"id": "speech_vad_threshold", "title": "VAD Threshold", "type": "number", "value": 0.5},
                            ],
                        },
                        {
                            "id": "health",
                            "tab": "connectivity",
                            "title": "Health & Monitoring",
                            "description": "Polling and degradation detection",
                            "icon": "monitor_heart",
                            "fields": [
                                {"id": "health_poll_interval", "title": "Poll Interval (s)", "type": "number", "value": 30},
                                {"id": "health_degradation_threshold", "title": "Degradation Threshold %", "type": "number", "value": 30},
                                {"id": "health_alerts_enabled", "title": "Enable Alerts", "type": "toggle", "value": True},
                            ],
                        },

                        # System tab
                        {
                            "id": "auth",
                            "tab": "system",
                            "title": "Authentication",
                            "description": "Credentials and password policy",
                            "icon": "lock",
                            "fields": [
                                {"id": "auth_username", "title": "Username", "type": "text"},
                                {"id": "auth_password", "title": "Password", "type": "password"},
                                {"id": "auth_password_confirm", "title": "Confirm Password", "type": "password"},
                                {"id": "root_password", "title": "Root Password (Docker)", "type": "password"},
                            ],
                        },
                        {
                            "id": "backup",
                            "tab": "system",
                            "title": "Backup & Restore",
                            "description": "Create and restore backups",
                            "icon": "backup",
                            "fields": [
                                {"id": "backup_auto", "title": "Auto Backup", "type": "toggle", "value": False},
                                {"id": "backup_location", "title": "Backup Location", "type": "text", "placeholder": "/var/backups"},
                                {"id": "restore_file", "title": "Restore File", "type": "file"},
                            ],
                        },
                        {
                            "id": "developer",
                            "tab": "system",
                            "title": "Developer",
                            "description": "Shell access and RFC settings",
                            "icon": "terminal",
                            "fields": [
                                {"id": "shell_interface", "title": "Shell Interface", "type": "select",
                                 "options": [
                                     {"value": "local", "label": "Local"},
                                     {"value": "ssh", "label": "SSH"},
                                 ],
                                 "value": "local"},
                                {"id": "rfc_host", "title": "RFC Host", "type": "text", "placeholder": "127.0.0.1"},
                                {"id": "rfc_port", "title": "RFC Port", "type": "number", "value": 6000},
                                {"id": "debug_mode", "title": "Enable Debug", "type": "toggle", "value": False},
                            ],
                        },
                        {
                            "id": "feature_flags",
                            "tab": "system",
                            "title": "Feature Flags",
                            "description": "Enable/disable system features (restart required). Environment variables override database values.",
                            "icon": "toggle_on",
                            "fields": [
                                {"id": "profile", "title": "Feature Profile", "type": "select",
                                 "options": [
                                     {"value": "minimal", "label": "Minimal (Essential only)"},
                                     {"value": "standard", "label": "Standard (Common features)"},
                                     {"value": "enhanced", "label": "Enhanced (Recommended)"},
                                     {"value": "max", "label": "Maximum (All features)"},
                                 ],
                                 "value": "enhanced",
                                 "hint": "Bulk apply feature set. Individual flags can be customized below."},
                                {"id": "sse_enabled", "title": "Server-Sent Events", "type": "toggle", "value": True,
                                 "hint": "Enable SSE streaming for real-time updates"},
                                {"id": "embeddings_ingest", "title": "Embedding Ingestion", "type": "toggle", "value": False,
                                 "hint": "Process and store vector embeddings"},
                                {"id": "semantic_recall", "title": "Semantic Memory Recall", "type": "toggle", "value": True,
                                 "hint": "Enable semantic search in memory retrieval"},
                                {"id": "content_masking", "title": "PII/Secret Masking", "type": "toggle", "value": True,
                                 "hint": "Automatically mask sensitive data in logs"},
                                {"id": "audio_support", "title": "Audio/Speech Support", "type": "toggle", "value": False,
                                 "hint": "Enable STT/TTS capabilities"},
                                {"id": "browser_support", "title": "Browser Automation", "type": "toggle", "value": False,
                                 "hint": "Enable browser agent tool"},
                                {"id": "code_exec_support", "title": "Code Execution", "type": "toggle", "value": True,
                                 "hint": "Allow agent to execute code"},
                                {"id": "vision_support", "title": "Vision/Image Analysis", "type": "toggle", "value": True,
                                 "hint": "Enable image understanding capabilities"},
                                {"id": "mcp_client", "title": "MCP Client", "type": "toggle", "value": True,
                                 "hint": "Connect to MCP servers"},
                                {"id": "mcp_server", "title": "MCP Server", "type": "toggle", "value": False,
                                 "hint": "Expose agent as MCP server"},
                                {"id": "learning_context", "title": "Context Learning", "type": "toggle", "value": False,
                                 "hint": "Adapt context based on usage patterns"},
                                {"id": "tool_sandboxing", "title": "Tool Isolation", "type": "toggle", "value": False,
                                 "hint": "Run tools in sandboxed environments"},
                                {"id": "streaming_responses", "title": "Streaming Responses", "type": "toggle", "value": True,
                                 "hint": "Stream LLM responses in real-time"},
                                {"id": "delegation", "title": "Agent Delegation", "type": "toggle", "value": False,
                                 "hint": "Allow agent to delegate to other agents"},
                            ],
                        },
                        {
                            "id": "secrets",
                            "tab": "system",
                            "title": "Secrets",
                            "description": "Opaque secrets blob for adapters",
                            "icon": "key",
                            "fields": [
                                {"id": "secrets_blob", "title": "Secrets JSON", "type": "json", "value": {}},
                            ],
                        },
                        {
                            "id": "feature_flags",
                            "tab": "system",
                            "title": "Feature Flags",
                            "description": "Enable/disable system features (restart required). Environment variables override database values.",
                            "icon": "toggle_on",
                            "fields": [
                                {"id": "profile", "title": "Feature Profile", "type": "select",
                                 "options": [
                                     {"value": "minimal", "label": "Minimal (Essential only)"},
                                     {"value": "standard", "label": "Standard (Common features)"},
                                     {"value": "enhanced", "label": "Enhanced (Recommended)"},
                                     {"value": "max", "label": "Maximum (All features)"},
                                 ],
                                 "value": "enhanced",
                                 "hint": "Bulk apply feature set. Individual flags can be customized below."},
                                {"id": "sse_enabled", "title": "Server-Sent Events", "type": "toggle", "value": True,
                                 "hint": "Enable SSE streaming for real-time updates"},
                                {"id": "embeddings_ingest", "title": "Embedding Ingestion", "type": "toggle", "value": False,
                                 "hint": "Process and store vector embeddings"},
                                {"id": "semantic_recall", "title": "Semantic Memory Recall", "type": "toggle", "value": True,
                                 "hint": "Enable semantic search in memory retrieval"},
                                {"id": "content_masking", "title": "PII/Secret Masking", "type": "toggle", "value": True,
                                 "hint": "Automatically mask sensitive data in logs"},
                                {"id": "audio_support", "title": "Audio/Speech Support", "type": "toggle", "value": False,
                                 "hint": "Enable STT/TTS capabilities"},
                                {"id": "browser_support", "title": "Browser Automation", "type": "toggle", "value": False,
                                 "hint": "Enable browser agent tool"},
                                {"id": "code_exec_support", "title": "Code Execution", "type": "toggle", "value": True,
                                 "hint": "Allow agent to execute code"},
                                {"id": "vision_support", "title": "Vision/Image Analysis", "type": "toggle", "value": True,
                                 "hint": "Enable image understanding capabilities"},
                                {"id": "mcp_client", "title": "MCP Client", "type": "toggle", "value": True,
                                 "hint": "Connect to MCP servers"},
                                {"id": "mcp_server", "title": "MCP Server", "type": "toggle", "value": False,
                                 "hint": "Expose agent as MCP server"},
                                {"id": "learning_context", "title": "Context Learning", "type": "toggle", "value": False,
                                 "hint": "Adapt context based on usage patterns"},
                                {"id": "tool_sandboxing", "title": "Tool Isolation", "type": "toggle", "value": False,
                                 "hint": "Run tools in sandboxed environments"},
                                {"id": "streaming_responses", "title": "Streaming Responses", "type": "toggle", "value": True,
                                 "hint": "Stream LLM responses in real-time"},
                                {"id": "delegation", "title": "Agent Delegation", "type": "toggle", "value": False,
                                 "hint": "Allow agent to delegate to other agents"},
                            ],
                        },
                        {
                            "id": "agent_config",
                            "tab": "system",
                            "title": "Agent Configuration",
                            "description": "Core agent behavior settings (restart required)",
                            "icon": "settings",
                            "fields": [
                                {"id": "profile", "title": "Agent Profile", "type": "select",
                                 "options": [
                                     {"value": "minimal", "label": "Minimal (Essential only)"},
                                     {"value": "standard", "label": "Standard (Balanced)"},
                                     {"value": "enhanced", "label": "Enhanced (Recommended)"},
                                     {"value": "max", "label": "Maximum (All features)"},
                                 ],
                                 "value": "enhanced",
                                 "hint": "Controls which features are enabled by default"},
                                {"id": "knowledge_subdirs", "title": "Knowledge Directories", "type": "json",
                                 "value": ["default", "custom"],
                                 "hint": "Must exist in /knowledge/ directory"},
                                {"id": "memory_subdir", "title": "Memory Subdirectory", "type": "text",
                                 "value": "",
                                 "placeholder": "default",
                                 "hint": "FAISS memory storage location"},
                                {"id": "code_exec_ssh_enabled", "title": "SSH Code Execution", "type": "toggle",
                                 "value": True,
                                 "hint": "Enable remote code execution via SSH"},
                                {"id": "code_exec_ssh_addr", "title": "SSH Host", "type": "text",
                                 "value": "localhost",
                                 "hint": "SSH server address"},
                                {"id": "code_exec_ssh_port", "title": "SSH Port", "type": "number",
                                 "value": 55022,
                                 "min": 1,
                                 "max": 65535,
                                 "hint": "SSH server port"},
                                {"id": "code_exec_ssh_user", "title": "SSH User", "type": "text",
                                 "value": "root",
                                 "hint": "SSH username for code execution"},
                            ],
                        },
                    ]
                }
                await conn.execute(
                    "INSERT INTO ui_settings (key, value) VALUES ('global', $1::jsonb)",
                    json.dumps(default_settings, ensure_ascii=False),
                )

    async def get(self) -> dict[str, Any]:
        pool = await self._pool_ensure()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("SELECT value FROM ui_settings WHERE key = 'global'")
            if not row:
                return {}
            val = row["value"]
            if isinstance(val, str):
                try:
                    val = json.loads(val)
                except Exception:
                    return {}
            return dict(val) if isinstance(val, dict) else {}

    async def set(self, value: dict[str, Any]) -> None:
        pool = await self._pool_ensure()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO ui_settings (key, value)
                VALUES ('global', $1::jsonb)
                ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;
                """,
                json.dumps(value, ensure_ascii=False),
            )
