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

ALLOWED_HOSTS = [
    h.strip()
    for h in (os.environ.get("SA01_ALLOWED_HOSTS") or "").split(",")
    if h.strip()
]

# Default security posture for non-debug operation
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_HSTS_SECONDS = os.environ.get("SA01_HSTS_SECONDS") if not DEBUG else 0
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

_db = SettingsRegistry.load().django_database_config
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
AAAS_DEFAULT_MAX_AGENTS = os.environ.get("AAAS_DEFAULT_MAX_AGENTS")
AAAS_DEFAULT_MAX_USERS = os.environ.get("AAAS_DEFAULT_MAX_USERS")
AAAS_DEFAULT_MAX_TOKENS_MONTHLY = os.environ.get("AAAS_DEFAULT_MAX_TOKENS_MONTHLY")
AAAS_DEFAULT_STORAGE_GB = os.environ.get("AAAS_DEFAULT_STORAGE_GB")

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
# Empty when unconfigured — require_setting("temporal_host") refuses rather
# than guess a scheduler. Namespace/queue names are schema identifiers, not
# hosts; their names live here so one reader exists.
TEMPORAL_HOST = os.environ.get("SA01_TEMPORAL_HOST") or ""
TEMPORAL_NAMESPACE = os.environ.get("SA01_TEMPORAL_NAMESPACE") or "default"
TEMPORAL_CONVERSATION_QUEUE = os.environ.get("SA01_TEMPORAL_CONVERSATION_QUEUE") or "conversation"
TEMPORAL_A2A_QUEUE = os.environ.get("SA01_TEMPORAL_A2A_QUEUE") or "a2a"

# Kafka
KAFKA_BOOTSTRAP_SERVERS = get_optional_env(
    "SA01_KAFKA_BOOTSTRAP_SERVERS", "", "Kafka broker for event streaming"
)
KAFKA_CONVERSATION_TOPIC = os.environ.get("CONVERSATION_INBOUND", "conversation.inbound")

# Feature Flags
FEATURE_PROFILE = os.environ.get("SA01_FEATURE_PROFILE", "default")

# Authentication
# VIBE SECURITY: No backdoor flags in production code. Period.
# Authentication is always required. The previous AUTH_REQUIRED flag read
# SA01_AUTH_REQUIRED and could be set to false, which is an auth bypass by
# environment variable. There is no such flag now, and there must not be one.
AUTH_REQUIRED = True

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
# No default here. The schema default lives once, as
# services.common.memory_contract.DEFAULT_MEM_EMBED_DIM, and must equal
# SFM's SOMA_VECTOR_DIM (ARCHITECTURE-INVARIANTS §2).
MEM_EMBED_DIM = int(os.environ["MEM_EMBED_DIM"]) if os.environ.get("MEM_EMBED_DIM") else None
MEM_HTTP_TIMEOUT = os.environ.get("MEM_HTTP_TIMEOUT")
MEM_RECALL_TOP_K = os.environ.get("MEM_RECALL_TOP_K")
MEM_PROXIMITY_TOP_K = os.environ.get("MEM_PROXIMITY_TOP_K")
MEM_HISTORY_LIMIT = os.environ.get("MEM_HISTORY_LIMIT")
MEM_CHAT_NAMESPACE = os.environ.get("MEM_CHAT_NAMESPACE", "chat_history")
MEM_DEFAULT_KIND = os.environ.get("MEM_DEFAULT_KIND", "episodic")
MEM_DEFAULT_SALIENCE = os.environ.get("MEM_DEFAULT_SALIENCE")
MEM_DEFAULT_SOURCE = os.environ.get("MEM_DEFAULT_SOURCE", "agent-chat")
MEM_WRITE_TIMEOUT_S = os.environ.get("MEM_WRITE_TIMEOUT_S")
MEM_RECALL_TIMEOUT_S = os.environ.get("MEM_RECALL_TIMEOUT_S")
MEM_HISTORY_TIMEOUT_S = os.environ.get("MEM_HISTORY_TIMEOUT_S")
MEMORY_WAL_TOPIC = os.environ.get("MEMORY_WAL_TOPIC", "memory.wal")
MEMORY_DEGRADED_TOPIC = os.environ.get("MEMORY_DEGRADED_TOPIC", "degradation.events")
TOOL_REWARD_SUCCESS = os.environ.get("TOOL_REWARD_SUCCESS")
TOOL_REWARD_FAILURE = os.environ.get("TOOL_REWARD_FAILURE")
SOMABRAIN_CONTEXT_CONFIDENCE_DEFAULT = os.environ.get("SOMABRAIN_CONTEXT_CONFIDENCE_DEFAULT")

# Temporal async-cycle schedule cadence. Deployment env may override at boot;
# the schema default lives only on SettingsModel (R-VAL-01 — one number, one
# place), so this bridge carries no default of its own.
SA01_SLEEP_CYCLE_HOURS = os.environ.get("SA01_SLEEP_CYCLE_HOURS")
SA01_JOB_ADVANCE_SECONDS = os.environ.get("SA01_JOB_ADVANCE_SECONDS")
SA01_OUTBOX_REPLAY_SECONDS = os.environ.get("SA01_OUTBOX_REPLAY_SECONDS")

# LLM / HTTP / MODEL runtime tunables (Django settings authority).
LLM_CONNECT_TIMEOUT_S = os.environ.get("SA01_LLM_CONNECT_TIMEOUT")
LLM_READ_TIMEOUT_S = os.environ.get("SA01_LLM_READ_TIMEOUT")
LLM_MAX_RETRIES = os.environ.get("SA01_LLM_MAX_RETRIES")
LLM_RETRY_BASE_DELAY_S = os.environ.get("SA01_LLM_RETRY_BASE_DELAY_S")
LLM_RETRY_BACKOFF_CAP_S = os.environ.get("SA01_LLM_RETRY_BACKOFF_CAP_S")
LLM_RETRY_AFTER_CAP_S = os.environ.get("SA01_LLM_RETRY_AFTER_CAP_S")
HTTP_CONNECT_TIMEOUT_S = os.environ.get("SA01_HTTP_CONNECT_TIMEOUT")
HTTP_READ_TIMEOUT_S = os.environ.get("SA01_HTTP_READ_TIMEOUT")
HTTP_SLOW_READ_TIMEOUT_S = os.environ.get("SA01_HTTP_SLOW_READ_TIMEOUT")
DEFAULT_CHAT_MODEL_NAME = os.environ.get("SA01_DEFAULT_CHAT_MODEL_NAME", "")
DEFAULT_UTIL_MODEL_NAME = os.environ.get("SA01_DEFAULT_UTIL_MODEL_NAME", "")
DEFAULT_EMBED_MODEL_NAME = os.environ.get("SA01_DEFAULT_EMBED_MODEL_NAME", "")
CB_FAILURE_THRESHOLD = os.environ.get("CB_FAILURE_THRESHOLD")
CB_RESET_TIMEOUT_S = os.environ.get("CB_RESET_TIMEOUT_S")
OPA_URL = get_optional_env("SA01_OPA_URL", "", "Open Policy Agent for authorization policies")

# Voice Services (Whisper STT + Kokoro TTS).
# Empty when unset — require_service_url() refuses an unconfigured endpoint.
# There is no localhost substitute (SOMA-STD-CONFIG-001 / Rule 16).
WHISPER_URL = get_optional_env("SA01_WHISPER_URL", "", "Whisper STT base URL")
WHISPER_API_URL = get_optional_env(
    "SA01_WHISPER_API_URL", "", "Whisper transcribe endpoint URL"
)
KOKORO_URL = get_optional_env("SA01_KOKORO_URL", "", "Kokoro TTS base URL")
KOKORO_TTS_URL = get_optional_env(
    "SA01_KOKORO_TTS_URL", "", "Kokoro synthesize endpoint URL"
)
AGENTVOICEVOX_BASE_URL = get_optional_env(
    "SA01_VOICEVOX_URL", "", "AgentVoiceVox base URL"
)

# LLM Service
LLM_API_URL = get_optional_env("SA01_LLM_API_URL", "", "Internal LLM chat endpoint URL")
# Absent becomes None, never "" — see the note on SOMABRAIN_MEMORY_HTTP_TOKEN.
# Consumers refuse to call the LLM with a missing key rather than sending
# `Authorization: Bearer ` and getting a 401 back.
LLM_API_KEY = get_secret_manager().get_credential("llm_api_key")
DEFAULT_VOICE_MODEL = os.environ.get("SA01_DEFAULT_VOICE_MODEL", "gpt-4o-mini")

# AuthN / login hardening (administrator-managed; schema defaults on SettingsModel)
LOGIN_RATE_LIMIT = os.environ.get("SA01_LOGIN_RATE_LIMIT")
LOGIN_RATE_WINDOW = os.environ.get("SA01_LOGIN_RATE_WINDOW")

# Voice payload ceilings and multimodal bounds
VOICE_MAX_AUDIO_BYTES = int(os.environ.get("SA01_VOICE_MAX_AUDIO_BYTES", str(10 * 1024 * 1024)))
VOICE_LLM_MAX_TOKENS = os.environ.get("SA01_VOICE_LLM_MAX_TOKENS")
MULTIMODAL_PROMPT_MAX_CHARS = os.environ.get("SA01_MULTIMODAL_PROMPT_MAX_CHARS")
MULTIMODAL_IMAGE_TIMEOUT_S = os.environ.get("SA01_MULTIMODAL_IMAGE_TIMEOUT_S")
MULTIMODAL_DIAGRAM_TIMEOUT_S = os.environ.get("SA01_MULTIMODAL_DIAGRAM_TIMEOUT_S")


# Multimodal Services (empty when unset — never a guessed host)
MERMAID_CLI_URL = get_optional_env("SA01_MERMAID_CLI_URL", "", "Mermaid CLI base URL")
IMAGE_GEN_URL = get_optional_env("SA01_IMAGE_GEN_URL", "", "Image generation endpoint URL")
DIAGRAM_URL = get_optional_env("SA01_DIAGRAM_URL", "", "Diagram render endpoint URL")

# Monitoring
PROMETHEUS_URL = get_optional_env("SA01_PROMETHEUS_URL", "", "Prometheus base URL")

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
JWT_LEEWAY = os.environ.get("SA01_JWT_LEEWAY")
# Disable issuer/audience validation for Docker dev (localhost/container hostname mismatch)
JWT_ISSUER_STRICT = os.environ.get("SA01_JWT_ISSUER_STRICT", "true").lower() == "true"


# =============================================================================
# GOOGLE OAUTH SETTINGS (Secrets from Vault)
# =============================================================================

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = get_secret_manager().get_credential("google_client_secret") or None
GOOGLE_REDIRECT_URI = get_optional_env(
    "GOOGLE_REDIRECT_URI", "", "Google OAuth redirect URI (deployment topology)"
)
GOOGLE_JAVASCRIPT_ORIGIN = get_optional_env(
    "GOOGLE_JAVASCRIPT_ORIGIN", "", "Google OAuth JavaScript origin (deployment topology)"
)

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
