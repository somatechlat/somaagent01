"""
Django settings for SomaAgent01 AAAS Admin.

This module is used for Django management commands (makemigrations, migrate, etc.)
This module is the runtime configuration for the gateway.


- Zero hardcoded URLs (Rule 16: Dynamic URL Resolution)
- Zero hardcoded secrets (Rule 47: Zero-Backdoor Mandate)
- Required environment variables enforced with clear error messages
"""

import os
from pathlib import Path

# Import environment configuration helpers
from services.common.env_config import get_optional_env, get_required_env
from services.common.unified_secret_manager import get_secret_manager

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

ENVIRONMENT = os.environ.get("SA01_ENVIRONMENT", "dev").strip().lower()
DEPLOYMENT_MODE = os.environ.get("SA01_DEPLOYMENT_MODE", "dev").strip().lower()
IS_DEV_ENV = ENVIRONMENT in {"dev", "development", "local", "test"} or DEPLOYMENT_MODE in {
    "dev",
    "development",
    "local",
}

# SECURITY WARNING: keep the secret key used in production secret!
# Secret material comes from Vault only (VIBE 164), never from ENV.
#
# No dev exemption. An ephemeral generated key is a fake: it silently
# invalidates every session on restart and hides the misconfiguration from
# whoever has to fix it. Missing is a hard failure in every environment.
SECRET_KEY = get_secret_manager().get_credential("django_secret_key")
if not SECRET_KEY:
    raise ValueError(
        "Missing required secret django_secret_key "
        "(Vault secret/agent/credentials/django_secret_key). "
        "It is never generated, never defaulted and never read from ENV."
    )

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
if DEBUG and not IS_DEV_ENV:
    raise ValueError("DEBUG=true is only allowed in local/dev environments")

allowed_hosts_env = os.environ.get("SA01_ALLOWED_HOSTS", "")
if allowed_hosts_env:
    ALLOWED_HOSTS = [h.strip() for h in allowed_hosts_env.split(",") if h.strip()]
elif IS_DEV_ENV:
    ALLOWED_HOSTS = ["localhost", "127.0.0.1"]
else:
    raise ValueError("Missing required environment variable: SA01_ALLOWED_HOSTS")

# Default security posture for non-debug operation
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_HSTS_SECONDS = int(os.environ.get("SA01_HSTS_SECONDS", "31536000")) if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG

# Application definition
INSTALLED_APPS = [
    # Django core apps
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third party
    "ninja",
    "channels",
    # Local admin apps (alphabetical order)
    "admin.agents",
    "admin.bridges",
    "admin.capsules",
    "admin.chat",
    "admin.core",
    "admin.files",
    "admin.filesv2",
    "admin.flink",
    "admin.gateway",
    "admin.llm",
    "admin.memory",
    "admin.modules",
    "admin.multimodal",
    "admin.somabrain",
    "admin.notifications",
    "admin.orchestrator",
    "admin.aaas",
    "admin.tools",
    "admin.ui",
    "admin.utils",
    "admin.voice",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # SPA static file serving
    "django.contrib.sessions.middleware.SessionMiddleware",
    "admin.common.middleware.SessionMiddleware",
    "admin.common.middleware.CSPMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "services.gateway.urls"
ASGI_APPLICATION = "services.gateway.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
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

# Database
# Topology from ENV, password from Vault. There is no SA01_DB_DSN and there
# never will be: a connection string embeds the password, so putting one in the
# environment puts a credential in a file and in the process table. The single
# place that knows how to reach Postgres is config/settings_registry.py
# (VIBE Rule 100).
from config.settings_registry import SettingsRegistry

_db = SettingsRegistry.load().django_database_config()
_db["CONN_MAX_AGE"] = int(os.environ.get("SA01_DB_CONN_MAX_AGE", "60"))
_db["OPTIONS"] = {
    "connect_timeout": int(os.environ.get("SA01_DB_CONNECT_TIMEOUT", "10")),
}

# VIBE RULE: PostgreSQL ONLY. NO SQLite fallback under any condition.
DATABASES = {"default": _db}

# Internationalization
# Operator-configurable locale (SOMA-SETTINGS-MODEL-001.md D-12).
LANGUAGE_CODE = os.environ.get("SA01_LANGUAGE_CODE", "en-us")
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "static"

# SPA Frontend (webui/dist) - served by WhiteNoise
STATICFILES_DIRS = [
    BASE_DIR / "webui" / "dist",  # Vite production build
]

# WhiteNoise settings for SPA
WHITENOISE_INDEX_FILE = True  # Serve index.html at /
WHITENOISE_ROOT = BASE_DIR / "webui" / "dist"  # Root for SPA assets

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# =============================================================================
# AAAS ADMIN DEFAULTS (Centralized - env overridable)
# =============================================================================

# Default tenant for unauthenticated requests (development only)
AAAS_DEFAULT_TENANT_ID = os.environ.get("AAAS_DEFAULT_TENANT_ID", None)

AAAS_DEFAULT_CHAT_MODEL = os.environ.get("AAAS_DEFAULT_CHAT_MODEL")

# Default tier limits (can be overridden per-tier in database)
AAAS_DEFAULT_MAX_AGENTS = int(os.environ.get("AAAS_DEFAULT_MAX_AGENTS", "10"))
AAAS_DEFAULT_MAX_USERS = int(os.environ.get("AAAS_DEFAULT_MAX_USERS", "50"))
AAAS_DEFAULT_MAX_TOKENS_MONTHLY = int(os.environ.get("AAAS_DEFAULT_MAX_TOKENS_MONTHLY", "10000000"))
AAAS_DEFAULT_STORAGE_GB = float(os.environ.get("AAAS_DEFAULT_STORAGE_GB", "50.0"))

# =============================================================================
# INFRASTRUCTURE SETTINGS (for migrated Django Ninja endpoints)
# =============================================================================

# No DATABASE_DSN setting. A DSN is a password in a string; holding one here as
# a "legacy compatibility" attribute is how a credential ends up in a repr, a
# traceback or a settings dump. Django's DATABASES is the only DB handle, and it
# carries the password as a discrete field from Vault (VIBE Rule 164).

# Redis
REDIS_URL = get_required_env("SA01_REDIS_URL", "Redis connection for caching and channels")

# Temporal
TEMPORAL_HOST = os.environ.get("SA01_TEMPORAL_HOST", "localhost:7233")
TEMPORAL_NAMESPACE = os.environ.get("SA01_TEMPORAL_NAMESPACE", "default")
TEMPORAL_CONVERSATION_QUEUE = os.environ.get("SA01_TEMPORAL_CONVERSATION_QUEUE", "conversation")
TEMPORAL_A2A_QUEUE = os.environ.get("SA01_TEMPORAL_A2A_QUEUE", "a2a")

# Kafka
KAFKA_BOOTSTRAP_SERVERS = get_optional_env(
    "SA01_KAFKA_BOOTSTRAP_SERVERS", "", "Kafka broker for event streaming"
)
KAFKA_CONVERSATION_TOPIC = os.environ.get("CONVERSATION_INBOUND", "conversation.inbound")

# Feature Flags
FEATURE_PROFILE = os.environ.get("SA01_FEATURE_PROFILE", "default")

# Endpoint-level permission mapping for UnifiedGate @require_permission decorator.
# Format: {"permission_name": ["user_id_1", "user_id_2"]} or {"permission_name": "*"}
# "*" allows all authenticated users. Empty/missing = DENY (secure-by-default).
ENDPOINT_PERMISSIONS = {}

# Authentication
AUTH_REQUIRED = os.environ.get("SA01_AUTH_REQUIRED", "true").lower() == "true"
# VIBE SECURITY: No backdoor flags in production code. Period.
# Dev auth bypass is handled via DEBUG=True + policy/soma_development.rego gated to environment=="dev".

# SomaBrain (Cognitive Runtime)
SOMABRAIN_URL = get_optional_env(
    "SOMABRAIN_URL",
    get_optional_env("SA01_SOMA_BASE_URL", "", "SomaBrain cognitive runtime HTTP endpoint"),
    "SomaBrain cognitive runtime HTTP endpoint",
)
SOMABRAIN_BASE_URL = SOMABRAIN_URL  # Alias for compatibility
SOMABRAIN_MEMORY_HTTP_TOKEN = get_secret_manager().get_credential("somabrain_memory_http_token")
# Absent becomes None, never "". An empty string reads as "configured with a blank
# secret" and is then sent as `Authorization: Bearer ` — an unauthenticated call
# that fails at the far end with a 401 nobody can trace back to the missing key.
# None is the honest "not configured", and every consumer refuses to send a
# request on it (VIBE Rule 91).
SOMAFRACTALMEMORY_URL = get_optional_env(
    "SOMAFRACTALMEMORY_URL", "", "SomaFractalMemory store URL (Brain-side only)"
)
# SOMABRAIN_API_KEY used to be defined here as
#     get_credential("somabrain_api_key") or get_credential("soma_api_token") or None
# — a silent cross-credential substitution that let a missing somabrain_api_key
# be papered over with an unrelated token. Nothing in the codebase read the
# attribute, so it was a fallback with no consumer: dead code whose only effect
# was to hide a misconfiguration. Both the setting and the substitution are gone.
# The credential itself still exists in Vault at
# secret/agent/credentials/somabrain_api_key and is read explicitly wherever a
# caller actually needs it.

# ---------------------------------------------------------------------------
# MEMORY TOOLS / SEAM — fully configurable (Django settings is the authority).
# ---------------------------------------------------------------------------
MEM_EMBED_DIM = int(os.environ.get("MEM_EMBED_DIM", "768"))
MEM_HTTP_TIMEOUT = float(os.environ.get("MEM_HTTP_TIMEOUT", "5.0"))
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
MEMORY_WAL_TOPIC = os.environ.get("MEMORY_WAL_TOPIC", "memory.wal")
MEMORY_DEGRADED_TOPIC = os.environ.get("MEMORY_DEGRADED_TOPIC", "degradation.events")
TOOL_REWARD_SUCCESS = float(os.environ.get("TOOL_REWARD_SUCCESS", "1.0"))
TOOL_REWARD_FAILURE = float(os.environ.get("TOOL_REWARD_FAILURE", "0.0"))
SOMABRAIN_CONTEXT_CONFIDENCE_DEFAULT = float(
    os.environ.get("SOMABRAIN_CONTEXT_CONFIDENCE_DEFAULT", "0.5")
)

# LLM / HTTP / MODEL runtime tunables (Django settings authority).
LLM_CONNECT_TIMEOUT_S = float(os.environ.get("SA01_LLM_CONNECT_TIMEOUT", "5.0"))
LLM_READ_TIMEOUT_S = float(os.environ.get("SA01_LLM_READ_TIMEOUT", "15.0"))
LLM_MAX_RETRIES = int(os.environ.get("SA01_LLM_MAX_RETRIES", "1"))
LLM_RETRY_BASE_DELAY_S = float(os.environ.get("SA01_LLM_RETRY_BASE_DELAY_S", "0.4"))
LLM_RETRY_BACKOFF_CAP_S = float(os.environ.get("SA01_LLM_RETRY_BACKOFF_CAP_S", "2.0"))
LLM_RETRY_AFTER_CAP_S = float(os.environ.get("SA01_LLM_RETRY_AFTER_CAP_S", "3.0"))
HTTP_CONNECT_TIMEOUT_S = float(os.environ.get("SA01_HTTP_CONNECT_TIMEOUT", "5.0"))
HTTP_READ_TIMEOUT_S = float(os.environ.get("SA01_HTTP_READ_TIMEOUT", "10.0"))
HTTP_SLOW_READ_TIMEOUT_S = float(os.environ.get("SA01_HTTP_SLOW_READ_TIMEOUT", "30.0"))
DEFAULT_CHAT_MODEL_PROVIDER = os.environ.get("SA01_DEFAULT_CHAT_MODEL_PROVIDER", "openrouter")
DEFAULT_CHAT_MODEL_NAME = os.environ.get("SA01_DEFAULT_CHAT_MODEL_NAME", "")
DEFAULT_UTIL_MODEL_PROVIDER = os.environ.get("SA01_DEFAULT_UTIL_MODEL_PROVIDER", "openrouter")
DEFAULT_UTIL_MODEL_NAME = os.environ.get("SA01_DEFAULT_UTIL_MODEL_NAME", "")
DEFAULT_EMBED_MODEL_PROVIDER = os.environ.get("SA01_DEFAULT_EMBED_MODEL_PROVIDER", "huggingface")
DEFAULT_EMBED_MODEL_NAME = os.environ.get("SA01_DEFAULT_EMBED_MODEL_NAME", "")
CB_FAILURE_THRESHOLD = int(os.environ.get("CB_FAILURE_THRESHOLD", "5"))
CB_RESET_TIMEOUT_S = float(os.environ.get("CB_RESET_TIMEOUT_S", "30.0"))
OPA_URL = get_optional_env("SA01_OPA_URL", "", "Open Policy Agent for authorization policies")

# Voice Services (Whisper STT + Kokoro TTS)
WHISPER_URL = os.environ.get("SA01_WHISPER_URL", "http://localhost:9100")
WHISPER_API_URL = os.environ.get("SA01_WHISPER_API_URL", "http://localhost:8001/transcribe")
KOKORO_URL = os.environ.get("SA01_KOKORO_URL", "http://localhost:9200")
KOKORO_TTS_URL = os.environ.get("SA01_KOKORO_TTS_URL", "http://localhost:8002/synthesize")
AGENTVOICEVOX_BASE_URL = os.environ.get("SA01_VOICEVOX_URL", "http://localhost:65009")

# LLM Service
LLM_API_URL = os.environ.get("SA01_LLM_API_URL", "http://localhost:9000/api/v2/core/llm/chat")
# Absent becomes None, never "" — see the note on SOMABRAIN_MEMORY_HTTP_TOKEN.
# Consumers refuse to call the LLM with a missing key rather than sending
# `Authorization: Bearer ` and getting a 401 back.
LLM_API_KEY = get_secret_manager().get_credential("llm_api_key")
DEFAULT_VOICE_MODEL = os.environ.get("SA01_DEFAULT_VOICE_MODEL", "gpt-4o-mini")

# Multimodal Services
MERMAID_CLI_URL = os.environ.get("SA01_MERMAID_CLI_URL", "http://localhost:9300")
IMAGE_GEN_URL = os.environ.get("SA01_IMAGE_GEN_URL", "http://localhost:8003/generate")
DIAGRAM_URL = os.environ.get("SA01_DIAGRAM_URL", "http://localhost:8004/render")

# Monitoring (AAAS: 63905, K8S: 32905, Local: 9090)
PROMETHEUS_URL = os.environ.get("SA01_PROMETHEUS_URL", "http://localhost:9090")

# =============================================================================
# KEYCLOAK SSO SETTINGS
# =============================================================================

KEYCLOAK_URL = get_required_env("SA01_KEYCLOAK_URL", "Keycloak OIDC identity provider base URL")
KEYCLOAK_REALM = os.environ.get("SA01_KEYCLOAK_REALM", "somaagent")
KEYCLOAK_CLIENT_ID = os.environ.get("SA01_KEYCLOAK_CLIENT_ID", "somaagent-api")
KEYCLOAK_CLIENT_SECRET = get_secret_manager().get_credential("keycloak_client_secret") or None
KEYCLOAK_PUBLIC_KEY = os.environ.get("SA01_KEYCLOAK_PUBLIC_KEY", "")

# JWT Settings for Keycloak
JWT_ALGORITHM = "RS256"
JWT_AUDIENCE = KEYCLOAK_CLIENT_ID
JWT_ISSUER = f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}"

# Unified JWT Settings (for Gateway & Admin)
# -----------------------------------------------------------------------------
JWT_JWKS_URL = os.environ.get("SA01_JWT_JWKS_URL", f"{JWT_ISSUER}/protocol/openid-connect/certs")
JWT_ALGORITHMS = os.environ.get("SA01_JWT_ALGORITHMS", "RS256").split(",")
JWT_LEEWAY = int(os.environ.get("SA01_JWT_LEEWAY", "10"))
# Disable issuer/audience validation for Docker dev (localhost/container hostname mismatch)
JWT_ISSUER_STRICT = os.environ.get("SA01_JWT_ISSUER_STRICT", "true").lower() == "true"


# =============================================================================
# GOOGLE OAUTH SETTINGS (Secrets from Vault)
# =============================================================================

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = get_secret_manager().get_credential("google_client_secret") or None
GOOGLE_REDIRECT_URI = os.environ.get("GOOGLE_REDIRECT_URI", "http://localhost:5173/auth/callback")
GOOGLE_JAVASCRIPT_ORIGIN = os.environ.get("GOOGLE_JAVASCRIPT_ORIGIN", "http://localhost:5173")

# =============================================================================
# DJANGO CACHE (Redis)
# =============================================================================

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
    }
}

# =============================================================================
# DJANGO CHANNELS (Redis-backed)
# =============================================================================

# Channel-layer transport. This module is authoritative for gateway/production
# deployments; config/settings.py is authoritative for standalone/dev
# deployments. Both read SA01_CHANNEL_LAYER_BACKEND so an operator can move a
# deployment onto Redis without editing code (D-14).
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": os.environ.get(
            "SA01_CHANNEL_LAYER_BACKEND", "channels_redis.core.RedisChannelLayer"
        ),
        "CONFIG": {"hosts": [REDIS_URL]},
    }
}

# =============================================================================
# DJANGO LOGGING
# =============================================================================

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
        "json": {
            "format": "%(levelname)s %(asctime)s %(module)s %(message)s",
            "style": "%",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "json_console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
    },
    "root": {
        "handlers": (
            ["json_console"] if os.environ.get("LOG_FORMAT", "json") == "json" else ["console"]
        ),
        "level": os.environ.get("LOG_LEVEL", "INFO").upper(),
    },
    "loggers": {
        # Django internals
        "django": {"handlers": ["json_console"], "level": "INFO", "propagate": False},
        "django.db.backends": {
            "handlers": ["json_console"],
            "level": "WARNING",
            "propagate": False,
        },
        # Admin apps
        "admin": {"handlers": ["json_console"], "level": "DEBUG", "propagate": False},
        "admin.aaas": {"handlers": ["json_console"], "level": "DEBUG", "propagate": False},
        "admin.core": {"handlers": ["json_console"], "level": "DEBUG", "propagate": False},
        "admin.agents": {"handlers": ["json_console"], "level": "DEBUG", "propagate": False},
        # Services
        "services": {"handlers": ["json_console"], "level": "INFO", "propagate": False},
        "services.common": {"handlers": ["json_console"], "level": "INFO", "propagate": False},
        "services.gateway": {"handlers": ["json_console"], "level": "INFO", "propagate": False},
        "services.tool_executor": {
            "handlers": ["json_console"],
            "level": "INFO",
            "propagate": False,
        },
        "services.conversation_worker": {
            "handlers": ["json_console"],
            "level": "INFO",
            "propagate": False,
        },
        # Orchestrator
        "orchestrator": {"handlers": ["json_console"], "level": "INFO", "propagate": False},
        # Python helpers/agent modules (legacy namespace - to be migrated)
        "python": {"handlers": ["json_console"], "level": "INFO", "propagate": False},
        # Authorization logging
        "authz": {"handlers": ["json_console"], "level": "INFO", "propagate": False},
    },
}
