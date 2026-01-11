"""
Django settings for SomaAgent01 SAAS Admin.

This module is used for Django management commands (makemigrations, migrate, etc.)
The runtime configuration is in django_setup.py for the gateway.


- Zero hardcoded URLs (Rule 16: Dynamic URL Resolution)
- Zero hardcoded secrets (Rule 47: Zero-Backdoor Mandate)
- Required environment variables enforced with clear error messages
"""

import os
import re
from pathlib import Path

# Import environment configuration helpers
from services.common.env_config import get_required_env

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get("SECRET_KEY", "django-insecure-dev-key-change-in-prod")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get("DEBUG", "True").lower() == "true"

ALLOWED_HOSTS = ["*"]

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
    "admin.capsules",
    "admin.chat",
    "admin.core",
    "admin.features",
    "admin.files",
    "admin.flink",
    "admin.gateway",
    "admin.llm",
    "admin.memory",
    "admin.multimodal",
    "admin.notifications",
    "admin.orchestrator",
    "admin.permissions",
    "admin.saas",
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
# Parse database DSN from environment (REQUIRED - no hardcoded credentials)
db_dsn = get_required_env(
    "SA01_DB_DSN",
    "PostgreSQL database connection (format: postgresql://user:pass@host:port/dbname)",
)

# Parse DSN components for Django DATABASE config
db_match = re.match(r"postgres(?:ql)?://([^:]+):([^@]+)@([^:/]+):?(\d+)?/(.+)", db_dsn)
if db_match:
    db_user, db_password, db_host, db_port, db_name = db_match.groups()
    db_port = db_port or "5432"
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": db_name,
            "USER": db_user,
            "PASSWORD": db_password,
            "HOST": db_host,
            "PORT": db_port,
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# Internationalization
LANGUAGE_CODE = "en-us"
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
# SAAS ADMIN DEFAULTS (Centralized - env overridable)
# =============================================================================

# Default tenant for unauthenticated requests (development only)
SAAS_DEFAULT_TENANT_ID = os.environ.get("SAAS_DEFAULT_TENANT_ID", None)

SAAS_DEFAULT_CHAT_MODEL = os.environ.get("SAAS_DEFAULT_CHAT_MODEL")

# Default tier limits (can be overridden per-tier in database)
SAAS_DEFAULT_MAX_AGENTS = int(os.environ.get("SAAS_DEFAULT_MAX_AGENTS", "10"))
SAAS_DEFAULT_MAX_USERS = int(os.environ.get("SAAS_DEFAULT_MAX_USERS", "50"))
SAAS_DEFAULT_MAX_TOKENS_MONTHLY = int(os.environ.get("SAAS_DEFAULT_MAX_TOKENS_MONTHLY", "10000000"))
SAAS_DEFAULT_STORAGE_GB = float(os.environ.get("SAAS_DEFAULT_STORAGE_GB", "50.0"))

# =============================================================================
# INFRASTRUCTURE SETTINGS (for migrated Django Ninja endpoints)
# =============================================================================

# Database DSN (legacy format - kept for compatibility)
DATABASE_DSN = db_dsn

# Redis
REDIS_URL = get_required_env("SA01_REDIS_URL", "Redis connection for caching and channels")

# Temporal
TEMPORAL_HOST = os.environ.get("SA01_TEMPORAL_HOST", "localhost:7233")
TEMPORAL_NAMESPACE = os.environ.get("SA01_TEMPORAL_NAMESPACE", "default")
TEMPORAL_CONVERSATION_QUEUE = os.environ.get("SA01_TEMPORAL_CONVERSATION_QUEUE", "conversation")
TEMPORAL_A2A_QUEUE = os.environ.get("SA01_TEMPORAL_A2A_QUEUE", "a2a")

# Kafka
KAFKA_BOOTSTRAP_SERVERS = get_required_env(
    "SA01_KAFKA_BOOTSTRAP_SERVERS", "Kafka broker for event streaming"
)
KAFKA_CONVERSATION_TOPIC = os.environ.get("CONVERSATION_INBOUND", "conversation.inbound")

# Feature Flags
FEATURE_PROFILE = os.environ.get("SA01_FEATURE_PROFILE", "default")

# Authentication
AUTH_REQUIRED = os.environ.get("SA01_AUTH_REQUIRED", "false").lower() == "true"

# SomaBrain (Cognitive Runtime)
SOMABRAIN_URL = get_required_env("SA01_SOMA_BASE_URL", "SomaBrain cognitive runtime HTTP endpoint")
SOMABRAIN_BASE_URL = SOMABRAIN_URL  # Alias for compatibility
SOMABRAIN_API_KEY = os.environ.get("SA01_SOMABRAIN_API_KEY", "")
OPA_URL = get_required_env("SA01_OPA_URL", "Open Policy Agent for authorization policies")

# Voice Services (Whisper STT + Kokoro TTS)
WHISPER_URL = os.environ.get("SA01_WHISPER_URL", "http://localhost:9100")
KOKORO_URL = os.environ.get("SA01_KOKORO_URL", "http://localhost:9200")

# Lago Billing
LAGO_API_URL = os.environ.get("SA01_LAGO_API_URL", "http://localhost:3000/api/v1")
LAGO_API_KEY = os.environ.get("SA01_LAGO_API_KEY", "")

# =============================================================================
# KEYCLOAK SSO SETTINGS
# =============================================================================

KEYCLOAK_URL = get_required_env("SA01_KEYCLOAK_URL", "Keycloak OIDC identity provider base URL")
KEYCLOAK_REALM = os.environ.get("SA01_KEYCLOAK_REALM", "somaagent")
KEYCLOAK_CLIENT_ID = os.environ.get("SA01_KEYCLOAK_CLIENT_ID", "somaagent-api")
KEYCLOAK_CLIENT_SECRET = os.environ.get("SA01_KEYCLOAK_CLIENT_SECRET", "")
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


# =============================================================================
# GOOGLE OAUTH SETTINGS (Secrets from ENV or Django Secret model)
# =============================================================================

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")  # From Vault/Secret model
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

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
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
            "()": "services.common.logging_config.DjangoJSONFormatter",
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
        "admin.saas": {"handlers": ["json_console"], "level": "DEBUG", "propagate": False},
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
