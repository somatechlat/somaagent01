"""Minimal Django settings for testing."""

SECRET_KEY = "test-secret-key-for-testing-only"
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
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "somaagent",
        "USER": "soma",
        "PASSWORD": "soma",
        "HOST": "localhost",
        "PORT": "63932",
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
