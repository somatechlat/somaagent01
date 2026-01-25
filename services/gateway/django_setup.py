"""Django configuration and ASGI setup for SomaAgent01.

This module:
1. Configures Django settings before any Django imports
2. Sets up the NinjaAPI with all routers
3. Provides the ASGI application

100% Django Ninja - Full Migration
"""

import os
import re

from django.conf import settings

# =============================================================================
# 1. DJANGO CONFIGURATION (must be before any Django imports)
# =============================================================================

if not settings.configured:
    # Parse database DSN from environment
    db_dsn = os.environ.get("SA01_DB_DSN", "postgresql://soma:soma@localhost:5432/somaagent01")

    # Parse DSN components for Django DATABASE config
    db_match = re.match(r"postgres(?:ql)?://([^:]+):([^@]+)@([^:/]+):?(\d+)?/(.+)", db_dsn)

    if db_match:
        db_user, db_password, db_host, db_port, db_name = db_match.groups()
        db_port = db_port or "5432"
        db_config = {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": db_name,
            "USER": db_user,
            "PASSWORD": db_password,
            "HOST": db_host,
            "PORT": db_port,
        }
    else:
        # Fallback to SQLite for testing
        db_config = {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        }

    settings.configure(
        DEBUG=os.environ.get("DEBUG", "False").lower() == "true",
        SECRET_KEY=os.environ.get("SECRET_KEY", "insecure-secret-key-for-dev"),
        ALLOWED_HOSTS=["*"],
        ROOT_URLCONF=__name__,
        INSTALLED_APPS=[
            # Core Django
            "django.contrib.contenttypes",
            "django.contrib.auth",
            "django.contrib.messages",
            # Django Ninja
            "ninja",
            "somafractalmemory",  # Monolith Integration
            # Project Apps - Existing
            "admin.aaas",
            # Project Apps - New (M1 Migration)
            "admin.core",
            "admin.agents",
            "admin.chat",
            "admin.files",
            "admin.features",
            "admin.utils",
        ],
        MIDDLEWARE=[
            "django.middleware.common.CommonMiddleware",
            "django.middleware.security.SecurityMiddleware",
        ],
        DATABASES={"default": db_config},
        TIME_ZONE="UTC",
        USE_TZ=True,
        # Logging configuration
        LOGGING={
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
                "level": os.environ.get("LOG_LEVEL", "INFO"),
            },
        },
    )

    import django

    django.setup()


# =============================================================================
# 2. URL CONFIGURATION (ROOT_URLCONF)
# =============================================================================

from django.urls import path

from admin.api import api

urlpatterns = [
    path("", api.urls),
]


# =============================================================================
# 3. ASGI APPLICATION
# =============================================================================

from django.core.asgi import get_asgi_application

django_app = get_asgi_application()


# =============================================================================
# 4. EXPORTS
# =============================================================================

__all__ = ["django_app", "api"]
