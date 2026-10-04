"""Django settings for development / local testing.

All service URLs come from environment variables.
Defaults target the local Docker Compose standalone stack.
"""

import os
from pathlib import Path

from services.common.unified_secret_manager import get_secret_manager

BASE_DIR = Path(__file__).resolve().parent.parent

# Secrets are read from Vault only (VIBE 164), never from ENV.
# VIBE 4 / 91: no fallback. A missing credential is a hard failure, not a
# licence to invent one — a fabricated key silently invalidates every session
# on restart and hides the misconfiguration from whoever has to fix it.
SECRET_KEY = get_secret_manager().get_credential("django_secret_key")
if not SECRET_KEY:
    raise RuntimeError(
        "VIBE Rule 164 VIOLATION: django_secret_key is missing. "
        "Set it in Vault at secret/agent/credentials/django_secret_key. "
        "It is never generated, never defaulted and never read from ENV."
    )
DEBUG = os.environ.get("DJANGO_DEBUG", "true").lower() == "true"
ALLOWED_HOSTS = os.environ.get("SA01_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

# Deployment mode
SA01_DEPLOYMENT_MODE = os.environ.get("SA01_DEPLOYMENT_MODE", "STANDALONE")

# Keycloak
# No localhost fallback (SOMA-STD-CONFIG-001). Identity provider topology
# is administrator-managed; an unconfigured URL surfaces at the OIDC client.
KEYCLOAK_URL = os.environ.get("KEYCLOAK_URL")
KEYCLOAK_REALM = os.environ.get("KEYCLOAK_REALM", "somaagent")
KEYCLOAK_CLIENT_ID = os.environ.get("KEYCLOAK_CLIENT_ID", "somaagent-api")
# Absent becomes None, never "". An empty string reads as "configured with a
# blank secret" and is then sent to Keycloak as though it were real — a working
# default that hides the misconfiguration. None is the honest "not configured"
# and matches services/gateway/settings.py (VIBE Rule 91).
KEYCLOAK_CLIENT_SECRET = get_secret_manager().get_credential("keycloak_client_secret") or None
SA01_KEYCLOAK_URL = KEYCLOAK_URL

# AAAS / Multi-tenancy
AAAS_DEFAULT_TENANT_ID = os.environ.get(
    "AAAS_DEFAULT_TENANT_ID", "cb6fc5b8-9525-4e81-8b6d-8ccf86460e9c"
)

# Vault
# VAULT_TOKEN is deliberately NOT mirrored here. It is the bootstrap root
# credential that vault_secrets.py authenticates TO Vault with — storing it in
# Vault would be circular, and a settings mirror of it would be a second copy of
# a secret that does nothing. Read it from ENV or VAULT_TOKEN_FILE at the point
# of authentication (services/common/vault_secrets.py).
# No localhost fallback. vault_secrets already refuses an unset VAULT_ADDR
# (VIBE Rule 164); a default here would hide that misconfiguration.
VAULT_ADDR = os.environ.get("VAULT_ADDR")
VAULT_MOUNT = os.environ.get("VAULT_MOUNT", "secret")

# SomaBrain (cognitive processing + memory conditioning)
# No localhost fallback and no default token — ARCHITECTURE-INVARIANTS §6.
# A missing URL or token must surface as MemoryConfigurationError (fail-closed),
# never as a silent request to localhost with a baked-in credential.
SOMABRAIN_URL = os.environ.get("SOMABRAIN_URL")
SOMABRAIN_MEMORY_HTTP_TOKEN = get_secret_manager().get_credential("somabrain_memory_http_token")

# ---------------------------------------------------------------------------
# Deployment service endpoints (SOMA-STD-CONFIG-001). Empty when unset.
# Call sites resolve through admin.core.helpers.service_urls.require_service_url
# and refuse an unconfigured endpoint — there is no guessed host.
# ---------------------------------------------------------------------------
OPA_URL = os.environ.get("OPA_URL") or os.environ.get("SA01_OPA_URL") or ""
LLM_API_URL = os.environ.get("LLM_API_URL") or os.environ.get("SA01_LLM_API_URL") or ""
IMAGE_GEN_URL = os.environ.get("IMAGE_GEN_URL") or os.environ.get("SA01_IMAGE_GEN_URL") or ""
DIAGRAM_URL = os.environ.get("DIAGRAM_URL") or os.environ.get("SA01_DIAGRAM_URL") or ""
MERMAID_CLI_URL = (
    os.environ.get("MERMAID_CLI_URL") or os.environ.get("SA01_MERMAID_CLI_URL") or ""
)
WHISPER_URL = os.environ.get("WHISPER_URL") or os.environ.get("SA01_WHISPER_URL") or ""
WHISPER_API_URL = (
    os.environ.get("WHISPER_API_URL") or os.environ.get("SA01_WHISPER_API_URL") or ""
)
KOKORO_URL = os.environ.get("KOKORO_URL") or os.environ.get("SA01_KOKORO_URL") or ""
KOKORO_TTS_URL = (
    os.environ.get("KOKORO_TTS_URL") or os.environ.get("SA01_KOKORO_TTS_URL") or ""
)
AGENTVOICEVOX_BASE_URL = (
    os.environ.get("AGENTVOICEVOX_BASE_URL")
    or os.environ.get("SA01_VOICEVOX_URL")
    or ""
)
BRIDGE_BASE_URL = (
    os.environ.get("BRIDGE_BASE_URL") or os.environ.get("WA_BRIDGE_BASE_URL") or ""
)
PROMETHEUS_URL = (
    os.environ.get("PROMETHEUS_URL") or os.environ.get("SA01_PROMETHEUS_URL") or ""
)
KAFKA_BOOTSTRAP_SERVERS = (
    os.environ.get("KAFKA_BOOTSTRAP_SERVERS")
    or os.environ.get("SA01_KAFKA_BOOTSTRAP_SERVERS")
    or ""
)
GOOGLE_REDIRECT_URI = os.environ.get("GOOGLE_REDIRECT_URI") or ""
GOOGLE_JAVASCRIPT_ORIGIN = os.environ.get("GOOGLE_JAVASCRIPT_ORIGIN") or ""
SMTP_HOST = os.environ.get("SMTP_HOST") or ""
SMTP_PORT = os.environ.get("SMTP_PORT") or ""

# SomaFractalMemory (vector memory storage + semantic search)
SOMAFRACTALMEMORY_URL = os.environ.get("SOMAFRACTALMEMORY_URL")
SOMA_API_TOKEN = get_secret_manager().get_credential("soma_api_token")

# Shared embedding dimension for the memory seam (ARCHITECTURE-INVARIANTS §2).
# MEM_EMBED_DIM (here) MUST equal SOMA_VECTOR_DIM (SFM's settings/infra.py).
# This is the authority; env is the 12-factor override. Nothing else in the
# codebase may invent a dimension.
MEM_EMBED_DIM = int(os.environ.get("MEM_EMBED_DIM", "768"))

# Memory seam transport + namespace (ARCHITECTURE-INVARIANTS §6).
# Adapters read these via services.common.memory_contract.get_memory_setting()
# and must never touch os.environ directly — this file is the one authority.
MEM_HTTP_TIMEOUT = float(os.environ.get("MEM_HTTP_TIMEOUT", "5.0"))
SFM_NAMESPACE = os.environ.get("SFM_NAMESPACE", "api_ns")
SOMABRAIN_NAMESPACE = os.environ.get("SOMABRAIN_NAMESPACE", "default")

# ---------------------------------------------------------------------------
# MEMORY TOOLS / SEAM — fully configurable. No hardcoded tool parameters.
# Read via services.common.memory_contract.get_memory_setting().
# ---------------------------------------------------------------------------
MEM_RECALL_TOP_K = int(os.environ.get("MEM_RECALL_TOP_K", "8"))
MEM_PROXIMITY_TOP_K = int(os.environ.get("MEM_PROXIMITY_TOP_K", "10"))
MEM_HISTORY_LIMIT = int(os.environ.get("MEM_HISTORY_LIMIT", "20"))
MEM_CHAT_NAMESPACE = os.environ.get("MEM_CHAT_NAMESPACE", "chat_history")
MEM_DEFAULT_KIND = os.environ.get("MEM_DEFAULT_KIND", "episodic")
MEM_DEFAULT_SALIENCE = float(os.environ.get("MEM_DEFAULT_SALIENCE", "0.5"))
MEM_DEFAULT_SOURCE = os.environ.get("MEM_DEFAULT_SOURCE", "agent-chat")
MEM_WRITE_TIMEOUT_S = float(os.environ.get("MEM_WRITE_TIMEOUT_S", "10.0"))
MEM_RECALL_TIMEOUT_S = float(os.environ.get("MEM_RECALL_TIMEOUT_S", "2.5"))
MEM_HISTORY_TIMEOUT_S = float(os.environ.get("MEM_HISTORY_TIMEOUT_S", "2.5"))

# Degraded-mode Kafka queue (memory-replicator replay → SomaBrain).
MEMORY_WAL_TOPIC = os.environ.get("MEMORY_WAL_TOPIC", "memory.wal")
MEMORY_DEGRADED_TOPIC = os.environ.get("MEMORY_DEGRADED_TOPIC", "degradation.events")

# Cognitive / tool feedback rewards (SomaBrain FeedbackRequest.utility).
TOOL_REWARD_SUCCESS = float(os.environ.get("TOOL_REWARD_SUCCESS", "1.0"))
TOOL_REWARD_FAILURE = float(os.environ.get("TOOL_REWARD_FAILURE", "0.0"))
SOMABRAIN_CONTEXT_CONFIDENCE_DEFAULT = float(
    os.environ.get("SOMABRAIN_CONTEXT_CONFIDENCE_DEFAULT", "0.5")
)

# Temporal async-cycle schedule cadence. Deployment env may override at boot;
# the schema default lives only on SettingsModel (R-VAL-01 — one number, one
# place), so this bridge carries no default of its own.
SA01_SLEEP_CYCLE_HOURS = os.environ.get("SA01_SLEEP_CYCLE_HOURS")
SA01_JOB_ADVANCE_SECONDS = os.environ.get("SA01_JOB_ADVANCE_SECONDS")
SA01_OUTBOX_REPLAY_SECONDS = os.environ.get("SA01_OUTBOX_REPLAY_SECONDS")

# ---------------------------------------------------------------------------
# LLM / HTTP / MODEL runtime tunables — Django settings is the authority.
# ---------------------------------------------------------------------------
LLM_CONNECT_TIMEOUT_S = float(os.environ.get("SA01_LLM_CONNECT_TIMEOUT", "5.0"))
LLM_READ_TIMEOUT_S = float(os.environ.get("SA01_LLM_READ_TIMEOUT", "15.0"))
LLM_MAX_RETRIES = int(os.environ.get("SA01_LLM_MAX_RETRIES", "1"))
LLM_RETRY_BASE_DELAY_S = float(os.environ.get("SA01_LLM_RETRY_BASE_DELAY_S", "0.4"))
LLM_RETRY_BACKOFF_CAP_S = float(os.environ.get("SA01_LLM_RETRY_BACKOFF_CAP_S", "2.0"))
LLM_RETRY_AFTER_CAP_S = float(os.environ.get("SA01_LLM_RETRY_AFTER_CAP_S", "3.0"))

HTTP_CONNECT_TIMEOUT_S = float(os.environ.get("SA01_HTTP_CONNECT_TIMEOUT", "5.0"))
HTTP_READ_TIMEOUT_S = float(os.environ.get("SA01_HTTP_READ_TIMEOUT", "10.0"))
HTTP_SLOW_READ_TIMEOUT_S = float(os.environ.get("SA01_HTTP_SLOW_READ_TIMEOUT", "30.0"))

DEFAULT_VOICE_MODEL = os.environ.get("SA01_DEFAULT_VOICE_MODEL", "gpt-4o-mini")
DEFAULT_CHAT_MODEL_PROVIDER = os.environ.get("SA01_DEFAULT_CHAT_MODEL_PROVIDER", "openrouter")
DEFAULT_CHAT_MODEL_NAME = os.environ.get("SA01_DEFAULT_CHAT_MODEL_NAME", "")
DEFAULT_UTIL_MODEL_PROVIDER = os.environ.get("SA01_DEFAULT_UTIL_MODEL_PROVIDER", "openrouter")
DEFAULT_UTIL_MODEL_NAME = os.environ.get("SA01_DEFAULT_UTIL_MODEL_NAME", "")
DEFAULT_EMBED_MODEL_PROVIDER = os.environ.get("SA01_DEFAULT_EMBED_MODEL_PROVIDER", "huggingface")
DEFAULT_EMBED_MODEL_NAME = os.environ.get("SA01_DEFAULT_EMBED_MODEL_NAME", "")

# Circuit breaker knobs (SomaBrain / external service resilience).
CB_FAILURE_THRESHOLD = int(os.environ.get("CB_FAILURE_THRESHOLD", "5"))
CB_RESET_TIMEOUT_S = float(os.environ.get("CB_RESET_TIMEOUT_S", "30.0"))

# Speech realtime (endpoint is topology → env/URL).
SPEECH_REALTIME_MODEL = os.environ.get("SPEECH_REALTIME_MODEL", "")
SPEECH_REALTIME_VOICE = os.environ.get("SPEECH_REALTIME_VOICE", "")
SPEECH_REALTIME_ENDPOINT = os.environ.get("SPEECH_REALTIME_ENDPOINT", "")

# AgentIQ knobs (Capsule-overridable; see SOMA-SETTINGS-MODEL-001 §7.2).
AGENTIQ_INTELLIGENCE_LEVEL = int(os.environ.get("AGENTIQ_INTELLIGENCE_LEVEL", "5"))
AGENTIQ_AUTONOMY_LEVEL = int(os.environ.get("AGENTIQ_AUTONOMY_LEVEL", "5"))
AGENTIQ_RESOURCE_BUDGET = float(os.environ.get("AGENTIQ_RESOURCE_BUDGET", "0.10"))

# Redis
REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", "20379"))
SA01_REDIS_URL = os.environ.get("SA01_REDIS_URL", f"redis://{REDIS_HOST}:{REDIS_PORT}/0")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.postgres",
    "django.contrib.sessions",
    "django.contrib.messages",
    "channels",
    "admin.core",
    "admin.aaas",
    "admin.bridges",
    "admin.chat",
    "admin.agents",
    "admin.llm",
    "admin.capsules",
    "admin.files",
    "admin.gateway",
    "admin.memory",
    "admin.modules",
    "admin.multimodal",
    "admin.notifications",
    "admin.orchestrator",
    "admin.somabrain",
    "admin.tools",
    "admin.ui",
    "admin.utils",
    "admin.voice",
]

# Database credentials MUST come from Vault - zero hardcoded passwords (VIBE 164)
_db_name = os.environ.get("TEST_DB_NAME", "somaagent")
_db_user = os.environ.get("TEST_DB_USER", "somaagent")
# No ephemeral fallback. A generated password is a fake: no database accepts
# it, so every connection fails later and far from the real cause. Fail here,
# naming the Vault path, instead.
_db_password = get_secret_manager().get_credential("test_db_password")
if not _db_password:
    raise RuntimeError(
        "VIBE Rule 164 VIOLATION: test_db_password is missing. "
        "Set it in Vault at secret/agent/credentials/test_db_password. "
        "It is never generated and never read from ENV."
    )
_db_host = os.environ.get("TEST_DB_HOST", "localhost")
_db_port = os.environ.get("TEST_DB_PORT", "63932")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": _db_name,
        "USER": _db_user,
        "PASSWORD": _db_password,
        "HOST": _db_host,
        "PORT": _db_port,
    }
}

USE_TZ = True
TIME_ZONE = "UTC"
# Operator-configurable locale (SOMA-SETTINGS-MODEL-001.md D-12).
LANGUAGE_CODE = os.environ.get("SA01_LANGUAGE_CODE", "en-us")
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

ROOT_URLCONF = "services.gateway.urls"
ASGI_APPLICATION = "config.asgi.application"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# Channel-layer transport. This module is authoritative for standalone/dev
# deployments; services/gateway/settings.py is authoritative for gateway/
# production deployments. Both read SA01_CHANNEL_LAYER_BACKEND so an operator
# can move a deployment onto Redis without editing code (D-14).
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": os.environ.get(
            "SA01_CHANNEL_LAYER_BACKEND", "channels.layers.InMemoryChannelLayer"
        ),
    },
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "WARNING",
        },
    },
}
