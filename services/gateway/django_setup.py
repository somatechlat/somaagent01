import os
import sys
from django.conf import settings

# --- 1. Minimal Django Configuration (MUST BE BEFORE IMPORTS) ---

if not settings.configured:
    settings.configure(
        DEBUG=os.environ.get("DEBUG", "False").lower() == "true",
        SECRET_KEY=os.environ.get("SECRET_KEY", "insecure-secret-key-for-dev"),
        ALLOWED_HOSTS=["*"], # VIBE: Allow all for dev gateway
        ROOT_URLCONF=__name__, # This file acts as the URL config
        INSTALLED_APPS=[
            # Core Django
            "django.contrib.contenttypes",
            "django.contrib.auth",
            # "django.contrib.admin", # Optional: Enable if needed
            "django.contrib.messages",
            "ninja", # Django Ninja
        ],
        MIDDLEWARE=[
            "django.middleware.common.CommonMiddleware",
            "django.middleware.security.SecurityMiddleware",
        ],
        DATABASES={
            # VIBE: Using dummy for now, will connect to Postgres later via env vars
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": ":memory:",
            }
        },
        TIME_ZONE="UTC",
        USE_TZ=True,
    )
    import django
    django.setup()

# --- 2. Ninja API Setup ---
from django.core.asgi import get_asgi_application
from ninja import NinjaAPI, Router

# Define the Ninja wrapper
# We mount this at the specific path in the Django URL patterns
ninja_api = NinjaAPI(
    title="SomaAgent SaaS API",
    version="1.0.0",
    description="SaaS Platform interfaces via Django Ninja",
    docs_url="/docs", # Relative to the mount point
)

# --- 3. URL Configuration (ROOT_URLCONF) ---

from django.urls import path

# We need to import routers AFTER settings are configured
# Lazy import or direct definition
# For now, we will define a temporary router here or import the refactored one
from services.gateway.routers.saas import router as saas_router

ninja_api.add_router("", saas_router) 

urlpatterns = [
    path("", ninja_api.urls),
]

# --- 4. ASGI Application ---

django_app = get_asgi_application()
