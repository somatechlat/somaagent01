"""Django settings for development / local testing.

All service URLs come from environment variables.
Defaults target the local Docker Compose standalone stack.
"""

import os
import secrets
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_urlsafe(50)
DEBUG = os.environ.get("DJANGO_DEBUG", "true").lower() == "true"
ALLOWED_HOSTS = os.environ.get("SA01_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

# Deployment mode
SA01_DEPLOYMENT_MODE = os.environ.get("SA01_DEPLOYMENT_MODE", "STANDALONE")

# Keycloak
KEYCLOAK_URL = os.environ.get("KEYCLOAK_URL", "http://localhost:20880")
KEYCLOAK_REALM = os.environ.get("KEYCLOAK_REALM", "somaagent")
KEYCLOAK_CLIENT_ID = os.environ.get("KEYCLOAK_CLIENT_ID", "somaagent-api")
KEYCLOAK_CLIENT_SECRET = os.environ.get("KEYCLOAK_CLIENT_SECRET", "")
SA01_KEYCLOAK_URL = KEYCLOAK_URL

# AAAS / Multi-tenancy
AAAS_DEFAULT_TENANT_ID = os.environ.get("AAAS_DEFAULT_TENANT_ID", "cb6fc5b8-9525-4e81-8b6d-8ccf86460e9c")

# Vault
VAULT_ADDR = os.environ.get("VAULT_ADDR", "http://localhost:20882")
VAULT_TOKEN = os.environ.get("VAULT_TOKEN", "soma-root-token-2024")
VAULT_MOUNT = os.environ.get("VAULT_MOUNT", "secret")

# SomaBrain (cognitive processing + memory conditioning)
SOMABRAIN_URL = os.environ.get("SOMABRAIN_URL", "http://localhost:30101")
SOMABRAIN_MEMORY_HTTP_TOKEN = os.environ.get("SOMABRAIN_MEMORY_HTTP_TOKEN", "sfm-api-token-123")

# SomaFractalMemory (vector memory storage + semantic search)
SOMAFRACTALMEMORY_URL = os.environ.get("SOMAFRACTALMEMORY_URL", "http://localhost:10101")
SOMA_API_TOKEN = os.environ.get("SOMA_API_TOKEN", "sfm-api-token-123")

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
    "admin.chat",
    "admin.agents",
    "admin.llm",
    "admin.capsules",
    "admin.files",
    "admin.features",
    "admin.gateway",
    "admin.memory",
    "admin.multimodal",
    "admin.notifications",
    "admin.orchestrator",
    "admin.permissions",
    "admin.somabrain",
    "admin.tools",
    "admin.ui",
    "admin.utils",
    "admin.voice",
]

# Database credentials MUST come from environment - zero hardcoded passwords
# For test collection without a real DB, generate an ephemeral password
_db_name = os.environ.get("TEST_DB_NAME", "somaagent")
_db_user = os.environ.get("TEST_DB_USER", "somaagent")
_db_password = os.environ.get("TEST_DB_PASSWORD") or secrets.token_urlsafe(16)
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

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
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
