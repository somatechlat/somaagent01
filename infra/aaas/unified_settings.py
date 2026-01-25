"""
UNIFIED SETTINGS FOR AGENT-AS-A-SERVICE (AAAS) MODE
=============================================

This module merges Django settings from all three repositories:
- somaAgent01: Agent orchestration, chat, gateway
- somabrain: Cognitive core, memory processing, HRR
- somafractalmemory: Vector storage, coordinate system

VIBE Compliance:
- Rule 2: All settings from real sources, no guessing
- Rule 100: Centralized configuration
- Rule 164: Secrets from environment/Vault

Usage:
    export DJANGO_SETTINGS_MODULE=infra.aaas.unified_settings
    export SOMA_SINGLE_PROCESS=true
    gunicorn infra.aaas.unified_wsgi:application
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Ensure all three repos are on PYTHONPATH
REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
AGENT_ROOT = REPO_ROOT / "somaAgent01"
BRAIN_ROOT = REPO_ROOT / "somabrain"
MEMORY_ROOT = REPO_ROOT / "somafractalmemory"

for repo_path in [AGENT_ROOT, BRAIN_ROOT, MEMORY_ROOT]:
    if str(repo_path) not in sys.path:
        sys.path.insert(0, str(repo_path))

# Base directory for the unified app
BASE_DIR = AGENT_ROOT

# =============================================================================
# ENVIRONMENT SETUP
# =============================================================================

# Single-process mode flag - when True, all services run in one Django process
SOMA_SINGLE_PROCESS = os.environ.get("SOMA_SINGLE_PROCESS", "true").lower() == "true"

# Mode detection
SA01_DEPLOYMENT_MODE = os.environ.get("SA01_DEPLOYMENT_MODE", "AAAS").upper()
SOMA_AAAS_MODE = os.environ.get("SOMA_AAAS_MODE", "true").lower() == "true"

# Debug mode
DEBUG = os.environ.get("DEBUG", "false").lower() == "true"

# Secret keys - load from Vault in production
SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    os.environ.get(
        "DJANGO_SECRET_KEY",
        "unified-dev-secret-key-change-in-production",
    ),
)

# Allowed hosts
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "*").split(",")

# =============================================================================
# DATABASE - Unified across all three apps
# =============================================================================

# Primary database host (all services share)
POSTGRES_HOST = os.environ.get("SOMA_POSTGRES_HOST", os.environ.get("POSTGRES_HOST", "localhost"))
POSTGRES_PORT = os.environ.get("SOMA_DB_PORT", os.environ.get("POSTGRES_PORT", "5432"))
POSTGRES_USER = os.environ.get("SOMA_DB_USER", os.environ.get("POSTGRES_USER", "soma"))
POSTGRES_PASSWORD = os.environ.get("SOMA_DB_PASSWORD", os.environ.get("POSTGRES_PASSWORD", "soma"))

DATABASES = {
    # Agent database
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "somaagent"),
        "USER": POSTGRES_USER,
        "PASSWORD": POSTGRES_PASSWORD,
        "HOST": POSTGRES_HOST,
        "PORT": POSTGRES_PORT,
    },
    # Brain database
    "brain": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("SOMABRAIN_DB", "somabrain"),
        "USER": POSTGRES_USER,
        "PASSWORD": POSTGRES_PASSWORD,
        "HOST": POSTGRES_HOST,
        "PORT": POSTGRES_PORT,
    },
    # Memory database
    "memory": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("SOMA_DB_NAME", "somamemory"),
        "USER": POSTGRES_USER,
        "PASSWORD": POSTGRES_PASSWORD,
        "HOST": POSTGRES_HOST,
        "PORT": POSTGRES_PORT,
    },
}

# Database router for multi-database support
DATABASE_ROUTERS = ["infra.aaas.db_router.UnifiedDatabaseRouter"]

# =============================================================================
# INSTALLED APPS - Merged from all three repos
# =============================================================================

INSTALLED_APPS = [
    # Django core
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",  # For PostgreSQL-specific fields
    # Third party
    "ninja",  # Django Ninja for all APIs
    "channels",  # WebSocket support
    # =========================================================================
    # SOMAAGENT01 APPS
    # =========================================================================
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
    "admin.aaas",
    "admin.tools",
    "admin.ui",
    "admin.utils",
    "admin.voice",
    # =========================================================================
    # SOMABRAIN APPS
    # =========================================================================
    "somabrain",
    "somabrain.aaas",
    # =========================================================================
    # SOMAFRACTALMEMORY APPS
    # =========================================================================
    "somafractalmemory",
    "somafractalmemory.aaas",
]

# =============================================================================
# MIDDLEWARE - Unified chain
# =============================================================================

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "admin.common.middleware.SessionMiddleware",  # Agent session handling
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# =============================================================================
# URL CONFIGURATION
# =============================================================================

ROOT_URLCONF = "infra.aaas.unified_urls"
WSGI_APPLICATION = "infra.aaas.unified_wsgi.application"
ASGI_APPLICATION = "infra.aaas.unified_asgi.application"

# =============================================================================
# TEMPLATES
# =============================================================================

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

# =============================================================================
# INTERNATIONALIZATION
# =============================================================================

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# =============================================================================
# STATIC FILES
# =============================================================================

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "static"
STATICFILES_DIRS = [
    BASE_DIR / "webui" / "dist",
]
WHITENOISE_INDEX_FILE = True
WHITENOISE_ROOT = BASE_DIR / "webui" / "dist"

# =============================================================================
# DEFAULT PRIMARY KEY
# =============================================================================

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# =============================================================================
# REDIS CONFIGURATION
# =============================================================================

REDIS_HOST = os.environ.get("SOMA_REDIS_HOST", os.environ.get("REDIS_HOST", "localhost"))
REDIS_PORT = int(os.environ.get("SOMA_REDIS_PORT", os.environ.get("REDIS_PORT", "6379")))
REDIS_URL = os.environ.get(
    "REDIS_URL",
    os.environ.get("SA01_REDIS_URL", f"redis://{REDIS_HOST}:{REDIS_PORT}/0"),
)

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
    }
}

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {"hosts": [REDIS_URL]},
    }
}

# =============================================================================
# MILVUS CONFIGURATION
# =============================================================================

SOMA_MILVUS_HOST = os.environ.get(
    "SOMA_MILVUS_HOST",
    os.environ.get("MILVUS_HOST", "localhost"),
)
SOMA_MILVUS_PORT = int(
    os.environ.get(
        "SOMA_MILVUS_PORT",
        os.environ.get("MILVUS_PORT", "19530"),
    )
)

# =============================================================================
# KAFKA CONFIGURATION
# =============================================================================

KAFKA_BOOTSTRAP_SERVERS = os.environ.get(
    "KAFKA_BOOTSTRAP_SERVERS",
    os.environ.get("SA01_KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
)

# =============================================================================
# SOMABRAIN-SPECIFIC SETTINGS
# =============================================================================

# HRR Configuration
SOMABRAIN_HRR_DIM = int(os.environ.get("SOMABRAIN_HRR_DIM", "8192"))
SOMABRAIN_HRR_DTYPE = os.environ.get("SOMABRAIN_HRR_DTYPE", "float32")

# Memory settings
SOMABRAIN_MEMORY_HTTP_ENDPOINT = os.environ.get(
    "SOMABRAIN_MEMORY_HTTP_ENDPOINT",
    "http://localhost:10101",
)

# Quantum layer
SOMABRAIN_QUANTUM_DIM = int(os.environ.get("SOMABRAIN_QUANTUM_DIM", "2048"))

# Default tenant
SOMABRAIN_DEFAULT_TENANT = os.environ.get("SOMABRAIN_DEFAULT_TENANT", "default")

# =============================================================================
# SOMAFRACTALMEMORY-SPECIFIC SETTINGS
# =============================================================================

SOMA_NAMESPACE = os.environ.get("SOMA_NAMESPACE", "default")
SOMA_MEMORY_NAMESPACE = os.environ.get("SOMA_MEMORY_NAMESPACE", "api_ns")
SOMA_VECTOR_DIM = int(os.environ.get("SOMA_VECTOR_DIM", "1536"))
SOMA_API_TOKEN = os.environ.get("SOMA_API_TOKEN")

# =============================================================================
# SOMAAGENT01-SPECIFIC SETTINGS
# =============================================================================

# AAAS defaults
AAAS_DEFAULT_TENANT_ID = os.environ.get("AAAS_DEFAULT_TENANT_ID")
AAAS_DEFAULT_CHAT_MODEL = os.environ.get("AAAS_DEFAULT_CHAT_MODEL")

# Keycloak
KEYCLOAK_URL = os.environ.get("SA01_KEYCLOAK_URL", "http://localhost:8080")
KEYCLOAK_REALM = os.environ.get("SA01_KEYCLOAK_REALM", "somaagent")
KEYCLOAK_CLIENT_ID = os.environ.get("SA01_KEYCLOAK_CLIENT_ID", "somaagent-api")

# OPA
OPA_URL = os.environ.get("SA01_OPA_URL", "http://localhost:8181")

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()

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
    },
    "root": {
        "handlers": ["console"],
        "level": LOG_LEVEL,
    },
    "loggers": {
        "django": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "admin": {"handlers": ["console"], "level": "DEBUG", "propagate": False},
        "somabrain": {"handlers": ["console"], "level": "DEBUG", "propagate": False},
        "somafractalmemory": {"handlers": ["console"], "level": "DEBUG", "propagate": False},
        "services": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}

# =============================================================================
# SINGLE-PROCESS MODE INDICATOR
# =============================================================================

# This flag tells the adapters to use direct Python imports instead of HTTP
UNIFIED_SINGLE_PROCESS = SOMA_SINGLE_PROCESS

print(f"✅ AAAS Unified Settings Loaded: SINGLE_PROCESS={SOMA_SINGLE_PROCESS}, MODE={SA01_DEPLOYMENT_MODE}")
