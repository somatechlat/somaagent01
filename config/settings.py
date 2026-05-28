"""Minimal Django settings for testing."""

import os
import secrets

SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_urlsafe(50)
DEBUG = True
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.postgres",
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
