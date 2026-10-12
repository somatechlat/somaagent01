"""
Django settings for SomaAgent01 Soma Platform Admin.

This module is used for Django management commands (makemigrations, migrate, etc.)
This module is the runtime configuration for the gateway.


- Zero hardcoded URLs (Rule 16: Dynamic URL Resolution)
- Zero hardcoded secrets (Rule 47: Zero-Backdoor Mandate)
- Required environment variables enforced with clear error messages
"""

import os
from pathlib import Path

from services.common.env_config import get_optional_env, get_required_env
from services.common.unified_secret_manager import get_secret_manager

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
    "admin.platform",
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
from django.core.exceptions import ImproperlyConfigured
from admin.core.helpers.settings_model import SettingsModel  # noqa: E402
from config.settings_registry import SettingsRegistry  # noqa: E402


def _behaviour(key: str, default: str | None = None) -> str | None:
    """Resolve a behavioural tunable from SettingsModel (not ENV).

    SOMA-STD-CONFIG-001 R-BEH-01 / AP-05: env is topology only. Knobs live on
    SettingsModel and resolve Capsule > AgentSetting > SettingsModel > default.
    The schema default is declared on the SettingsModel field (R-VAL-01);
    ``default`` here is only a last-resort when the key is absent from the model.
    Rule 91: key-absent maps to ``default``. A config error from the schema
    factory is NOT swallowed — it propagates (fail-closed).
    """
    value = SettingsModel.get(key)
    if value is not None and str(value).strip() != "":
        return str(value)
    return default


_db = SettingsRegistry.load().django_database_config
# Schema defaults live on SettingsModel (R-VAL-01). `or "0"` is only an int()
# coercion guard, not a second default.
def _behaviour_int(key: str, schema_default: str) -> int:
    raw = _behaviour(key, schema_default)
    if raw is None or str(raw).strip() == "":
        raise ImproperlyConfigured(f"{key} is empty; Rule 91 — no silent 0")
    return int(raw)

_db["CONN_MAX_AGE"] = _behaviour_int("sa01_db_conn_max_age", "60")
_db["OPTIONS"] = {
    "connect_timeout": _behaviour_int("sa01_db_connect_timeout", "10"),
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
# Soma Platform ADMIN DEFAULTS (Centralized — behaviour via SettingsModel, not ENV)
# =============================================================================

# SECURITY WARNING: keep the HSTS max-age an operator knob (R-BEH-01).
SECURE_HSTS_SECONDS = 0 if DEBUG else _behaviour("sa01_hsts_seconds")

# Default tenant for unauthenticated requests (development only)
# Defaults are BEHAVIOUR (R-BEH-01) — schema default lives on SettingsModel.
SA01_DEFAULT_TENANT_ID = _behaviour("sa01_default_tenant_id")
SA01_DEFAULT_CHAT_MODEL = _behaviour("sa01_default_chat_model")
SA01_DEFAULT_MAX_AGENTS = _behaviour("sa01_default_max_agents")
SA01_DEFAULT_MAX_USERS = _behaviour("sa01_default_max_users")
SA01_DEFAULT_MAX_TOKENS_MONTHLY = _behaviour("sa01_default_max_tokens_monthly")
SA01_DEFAULT_STORAGE_GB = _behaviour("sa01_default_storage_gb")

# =============================================================================
# INFRASTRUCTURE SETTINGS (for migrated Django Ninja endpoints)
# =============================================================================

# No DATABASE_DSN setting. A DSN is a password in a string; holding one here as
# a "legacy compatibility" attribute is how a credential ends up in a repr, a
# traceback or a settings dump. Django's DATABASES is the only DB handle, and it
# carries the password as a discrete field from Vault (VIBE Rule 164).

# Redis
REDIS_URL = get_required_env("SA01_REDIS_URL", "Redis connection for caching and channels")

# Temporal — ONE host authority: env key SA01_TEMPORAL_HOST.
# This module is the sole reader of that key. Workers and the gateway
# client resolve through django.conf.settings — never a second path
# (registry.temporal_host was a duplicate connect authority; removed).
# Empty host when unconfigured: consumers refuse (Rule 91). There is no
# default scheduler and no TEMPORAL_NAMESPACE (zero readers).
# Queue names are optional schema identifiers; the default lives ONLY
# here (R-VAL-04). Call sites must not invent "conversation"/"a2a".
TEMPORAL_HOST = (os.environ.get("SA01_TEMPORAL_HOST") or "").strip()
TEMPORAL_CONVERSATION_QUEUE = _behaviour("sa01_temporal_conversation_queue")
TEMPORAL_A2A_QUEUE = _behaviour("sa01_temporal_a2a_queue")

# Kafka
KAFKA_BOOTSTRAP_SERVERS = get_optional_env(
    "SA01_KAFKA_BOOTSTRAP_SERVERS", "", "Kafka broker for event streaming"
)
KAFKA_CONVERSATION_TOPIC = _behaviour("conversation_inbound")

# Feature Flags
FEATURE_PROFILE = _behaviour("sa01_feature_profile")

# Authentication
# VIBE SECURITY: No backdoor flags in production code. Period.
# Authentication is always required. The previous AUTH_REQUIRED flag read
# SA01_AUTH_REQUIRED and could be set to false, which is an auth bypass by
# environment variable. There is no such flag now, and there must not be one.
AUTH_REQUIRED = True

# SomaBrain (Cognitive Runtime)
# Topology boot bridge (R-TOP-01): env may supply the first value before the
# admin UI exists. Readers MUST resolve through require_service_url /
# InfrastructureConfig (R-VEN-02) — Capsule > AgentSetting > InfrastructureConfig
# > SettingsModel.service_* — never getattr with an invented host. Empty means
# unconfigured; require_service_url raises (R-TOP-02). No get_optional_env and
# no SA01_SOMA_BASE_URL alias (OPEN-07 / R-VAL-06).
SOMABRAIN_URL = (os.environ.get("SOMABRAIN_URL") or "").strip()
SOMABRAIN_BASE_URL = SOMABRAIN_URL  # Alias for compatibility
# Memory addressing partition. No default (Rule 91): empty until the operator
# sets it through Capsule.memory_pointer / AgentSetting / InfrastructureConfig.
SOMABRAIN_NAMESPACE = _behaviour("somabrain_namespace")
SOMABRAIN_MEMORY_HTTP_TOKEN = get_secret_manager().get_credential("somabrain_memory_http_token")
# Absent becomes None, never "". An empty string reads as "configured with a blank
# secret" and is then sent as `Authorization: Bearer ` — an unauthenticated call
# that fails at the far end with a 401 nobody can trace back to the missing key.
# None is the honest "not configured", and every consumer refuses to send a
# request on it (VIBE Rule 91).
SOMAFRACTALMEMORY_URL = (os.environ.get("SOMAFRACTALMEMORY_URL") or "").strip()
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
# MEMORY TOOLS / SEAM — Django settings is the authority (SOMA-STD-CONFIG-001).
# ---------------------------------------------------------------------------
# R-BEH-01 / R-VAL-01: behavioural knobs are declared on SettingsModel and
# resolved through the chain Capsule > AgentSetting > SettingsModel > schema
# default. They are NOT read from os.environ (AP-05). Env carries topology
# only (VAULT_ADDR) — never a knob, never a URL, never a secret.
#
# Schema default for dimension lives once:
# services.common.memory_contract.DEFAULT_MEM_EMBED_DIM (== SFM SOMA_VECTOR_DIM).
MEM_EMBED_DIM = _behaviour("mem_embed_dim")
MEM_HTTP_TIMEOUT = _behaviour("mem_http_timeout")
MEM_WRITE_TIMEOUT_S = _behaviour("mem_write_timeout_s")
MEM_RECALL_TIMEOUT_S = _behaviour("mem_recall_timeout_s")
MEM_HISTORY_TIMEOUT_S = _behaviour("mem_history_timeout_s")
MEM_RECALL_TOP_K = _behaviour("mem_recall_top_k")
MEM_PROXIMITY_TOP_K = _behaviour("mem_proximity_top_k")
MEM_HISTORY_LIMIT = _behaviour("mem_history_limit")
MEM_CHAT_NAMESPACE = _behaviour("mem_chat_namespace")
MEM_DEFAULT_KIND = _behaviour("mem_default_kind")
MEM_DEFAULT_SALIENCE = _behaviour("mem_default_salience")
MEM_DEFAULT_SOURCE = _behaviour("mem_default_source")
MEMORY_WAL_TOPIC = _behaviour("memory_wal_topic")
MEMORY_DEGRADED_TOPIC = _behaviour("memory_degraded_topic")
# Reward events (RewardEvent → learner) — Kafka-only reward lane (W1.5/R-04).
SOMABRAIN_TOPIC_REWARD_EVENTS = _behaviour("somabrain_topic_reward_events")
TOOL_REWARD_SUCCESS = _behaviour("tool_reward_success")
TOOL_REWARD_FAILURE = _behaviour("tool_reward_failure")
SOMABRAIN_CONTEXT_CONFIDENCE_DEFAULT = _behaviour("somabrain_context_confidence_default")

# Temporal async-cycle schedule cadence. Schema default lives on SettingsModel
# (R-VAL-01 — one number, one place).
SA01_SLEEP_CYCLE_HOURS = _behaviour("sa01_sleep_cycle_hours")
SA01_JOB_ADVANCE_SECONDS = _behaviour("sa01_job_advance_seconds")
SA01_OUTBOX_REPLAY_SECONDS = _behaviour("sa01_outbox_replay_seconds")

# LLM / HTTP / MODEL runtime tunables (Django settings authority — R-BEH-01).
LLM_CONNECT_TIMEOUT_S = _behaviour("sa01_llm_connect_timeout")
LLM_READ_TIMEOUT_S = _behaviour("sa01_llm_read_timeout")
LLM_MAX_RETRIES = _behaviour("sa01_llm_max_retries")
LLM_RETRY_BASE_DELAY_S = _behaviour("sa01_llm_retry_base_delay_s")
LLM_RETRY_BACKOFF_CAP_S = _behaviour("sa01_llm_retry_backoff_cap_s")
LLM_RETRY_AFTER_CAP_S = _behaviour("sa01_llm_retry_after_cap_s")
HTTP_CONNECT_TIMEOUT_S = _behaviour("sa01_http_connect_timeout")
HTTP_READ_TIMEOUT_S = _behaviour("sa01_http_read_timeout")
HTTP_SLOW_READ_TIMEOUT_S = _behaviour("sa01_http_slow_read_timeout")
DEFAULT_CHAT_MODEL_NAME = _behaviour("default_chat_model_name")
DEFAULT_UTIL_MODEL_NAME = _behaviour("default_util_model_name")
DEFAULT_EMBED_MODEL_NAME = _behaviour("default_embed_model_name")
CB_FAILURE_THRESHOLD = _behaviour("cb_failure_threshold")
CB_RESET_TIMEOUT_S = _behaviour("cb_reset_timeout_s")
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
# SearxNG meta-search (web_search, TOOLS-001 §5.10). Empty when unset —
# require_service_url() refuses; no localhost default.
SEARXNG_URL = get_optional_env(
    "SEARXNG_URL",
    get_optional_env("SA01_SEARXNG_URL", "", "SearxNG meta-search base URL"),
    "SearxNG meta-search base URL",
)

# LLM Service
LLM_API_URL = get_optional_env("SA01_LLM_API_URL", "", "Internal LLM chat endpoint URL")
# Absent becomes None, never "" — see the note on SOMABRAIN_MEMORY_HTTP_TOKEN.
# Consumers refuse to call the LLM with a missing key rather than sending
# `Authorization: Bearer ` and getting a 401 back.
LLM_API_KEY = get_secret_manager().get_credential("llm_api_key")
DEFAULT_VOICE_MODEL = _behaviour("sa01_default_voice_model")

# AuthN / login hardening (schema defaults on SettingsModel)
LOGIN_RATE_LIMIT = _behaviour("login_rate_limit")
LOGIN_RATE_WINDOW = _behaviour("login_rate_window")

# Voice payload ceilings and multimodal bounds (schema default on SettingsModel)
VOICE_MAX_AUDIO_BYTES = _behaviour_int("voice_max_audio_bytes", str(10 * 1024 * 1024))
VOICE_LLM_MAX_TOKENS = _behaviour("voice_llm_max_tokens")
MULTIMODAL_PROMPT_MAX_CHARS = _behaviour("multimodal_prompt_max_chars")
MULTIMODAL_IMAGE_TIMEOUT_S = _behaviour("multimodal_image_timeout_s")
MULTIMODAL_DIAGRAM_TIMEOUT_S = _behaviour("multimodal_diagram_timeout_s")


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
KEYCLOAK_REALM = _behaviour("sa01_keycloak_realm")
KEYCLOAK_CLIENT_ID = _behaviour("sa01_keycloak_client_id")
KEYCLOAK_CLIENT_SECRET = get_secret_manager().get_credential("keycloak_client_secret") or None
# Public key material — not a secret (R-SEC-01 covers credentials). Behaviour:
# administrator-managed on SettingsModel, never ENV.
KEYCLOAK_PUBLIC_KEY = _behaviour("sa01_keycloak_public_key") or ""

# JWT Settings for Keycloak
JWT_ALGORITHM = "RS256"
JWT_AUDIENCE = KEYCLOAK_CLIENT_ID
JWT_ISSUER = f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}"

# Unified JWT Settings (for Gateway & Admin)
# -----------------------------------------------------------------------------
# JWKS endpoint is derived topology from KEYCLOAK_URL + realm. An operator
# override lives on SettingsModel (service/behaviour chain), never ENV.
_jwt_jwks_override = _behaviour("sa01_jwt_jwks_url")
JWT_JWKS_URL = _jwt_jwks_override or f"{JWT_ISSUER}/protocol/openid-connect/certs"
JWT_ALGORITHMS = (_behaviour("sa01_jwt_algorithms") or "RS256").split(",")
JWT_LEEWAY = _behaviour("sa01_jwt_leeway")
# Disable issuer/audience validation for Docker dev (localhost/container hostname mismatch)
JWT_ISSUER_STRICT = (_behaviour("sa01_jwt_issuer_strict") or "true").lower() == "true"


# =============================================================================
# GOOGLE OAUTH SETTINGS (Secrets from Vault)
# =============================================================================

GOOGLE_CLIENT_ID = _behaviour("google_client_id") or ""
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
# deployments. Both resolve the backend from SettingsModel (R-BEH-01) so an
# operator can move a deployment onto Redis without editing code (D-14).
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": _behaviour("sa01_channel_layer_backend")
        or "channels_redis.core.RedisChannelLayer",
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
            ["json_console"] if (_behaviour("log_format") or "json") == "json" else ["console"]
        ),
        "level": (_behaviour("log_level") or "INFO").upper(),
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
        "admin.platform": {"handlers": ["json_console"], "level": "DEBUG", "propagate": False},
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
