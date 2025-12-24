"""Pure Django ASGI Gateway Entrypoint.

VIBE COMPLIANT - Migrated from FastAPI to pure Django.
All routers now use Django Ninja.

🎓 PhD Dev - Clean ASGI architecture
🔒 Security - Django middleware stack
⚡ Perf - Uvicorn ASGI server
"""

from __future__ import annotations

import os
import pathlib
import time

# Django setup MUST come first
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "services.gateway.settings")

import django

django.setup()

from django.core.asgi import get_asgi_application
from django.http import FileResponse, JsonResponse
from django.views.static import serve

# Import Django app
django_asgi = get_asgi_application()


def main() -> None:
    """Run the Django ASGI gateway with Uvicorn."""
    import uvicorn

    uvicorn.run(
        "services.gateway.main:django_asgi",
        host="0.0.0.0",
        port=8010,
        reload=False,
    )


if __name__ == "__main__":
    main()


# Compatibility exports for tests
def get_secret_manager():
    from services.gateway import providers

    return providers.get_secret_manager()


def get_event_bus():
    from services.gateway import providers

    return providers.get_event_bus()


def get_session_cache():
    from services.gateway import providers

    return providers.get_session_cache()


def get_session_store():
    from services.gateway import providers

    return providers.get_session_store()
