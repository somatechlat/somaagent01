"""
Django settings for SomaAgent01 SAAS Admin.

This module is used for Django management commands (makemigrations, migrate, etc.)
The runtime configuration is in django_setup.py for the gateway.
"""

import os
from pathlib import Path
import re

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get("SECRET_KEY", "django-insecure-dev-key-change-in-prod")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get("DEBUG", "True").lower() == "true"

ALLOWED_HOSTS = ["*"]

# Application definition
INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.messages",
    "ninja",
    # Project Apps - Django ORM Models
    "admin.saas",
    "admin.core",
    "admin.agents",
    "admin.chat",
    "admin.features",
]

MIDDLEWARE = [
    "django.middleware.common.CommonMiddleware",
    "django.middleware.security.SecurityMiddleware",
]

ROOT_URLCONF = "services.gateway.urls"

# Database
# Parse database DSN from environment
db_dsn = os.environ.get(
    "SA01_DB_DSN", "postgresql://soma:soma@localhost:5432/somaagent01"
)

# Parse DSN components for Django DATABASE config
db_match = re.match(
    r"postgres(?:ql)?://([^:]+):([^@]+)@([^:/]+):?(\d+)?/(.+)", db_dsn
)
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

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# =============================================================================
# SAAS ADMIN DEFAULTS (Centralized - env overridable)
# =============================================================================

# Default tenant for unauthenticated requests (development only)
SAAS_DEFAULT_TENANT_ID = os.environ.get("SAAS_DEFAULT_TENANT_ID", None)

# Default AI model for new agents
SAAS_DEFAULT_CHAT_MODEL = os.environ.get("SAAS_DEFAULT_CHAT_MODEL", "gpt-4o")

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
REDIS_URL = os.environ.get("SA01_REDIS_URL", "redis://localhost:6379/0")

# Temporal
TEMPORAL_HOST = os.environ.get("SA01_TEMPORAL_HOST", "localhost:7233")
TEMPORAL_NAMESPACE = os.environ.get("SA01_TEMPORAL_NAMESPACE", "default")
TEMPORAL_CONVERSATION_QUEUE = os.environ.get("SA01_TEMPORAL_CONVERSATION_QUEUE", "conversation")
TEMPORAL_A2A_QUEUE = os.environ.get("SA01_TEMPORAL_A2A_QUEUE", "a2a")

# Kafka
KAFKA_BOOTSTRAP_SERVERS = os.environ.get("SA01_KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_CONVERSATION_TOPIC = os.environ.get("CONVERSATION_INBOUND", "conversation.inbound")

# Feature Flags
FEATURE_PROFILE = os.environ.get("SA01_FEATURE_PROFILE", "default")

# Authentication
AUTH_REQUIRED = os.environ.get("SA01_AUTH_REQUIRED", "false").lower() == "true"

# SomaBrain
SOMABRAIN_URL = os.environ.get("SA01_SOMA_BASE_URL", "http://localhost:9696")
OPA_URL = os.environ.get("SA01_OPA_URL", "http://localhost:8181")

# =============================================================================
# KEYCLOAK SSO SETTINGS
# =============================================================================

KEYCLOAK_URL = os.environ.get("SA01_KEYCLOAK_URL", "http://localhost:20880")
KEYCLOAK_REALM = os.environ.get("SA01_KEYCLOAK_REALM", "somaagent")
KEYCLOAK_CLIENT_ID = os.environ.get("SA01_KEYCLOAK_CLIENT_ID", "somaagent-api")
KEYCLOAK_CLIENT_SECRET = os.environ.get("SA01_KEYCLOAK_CLIENT_SECRET", "")
KEYCLOAK_PUBLIC_KEY = os.environ.get("SA01_KEYCLOAK_PUBLIC_KEY", "")

# JWT Settings for Keycloak
JWT_ALGORITHM = "RS256"
JWT_AUDIENCE = KEYCLOAK_CLIENT_ID
JWT_ISSUER = f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}"

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
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "admin": {"handlers": ["console"], "level": "DEBUG", "propagate": False},
    },
}

