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
    # Project Apps
    "admin.skins",
    "admin.saas",
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
