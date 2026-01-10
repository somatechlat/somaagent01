"""Pure Django ASGI Gateway Entrypoint.


All routers now use Django Ninja.

🎓 PhD Dev - Clean ASGI architecture
🔒 Security - Django middleware stack
⚡ Perf - Uvicorn ASGI server
"""

from __future__ import annotations

import os

# Django setup MUST come first
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "services.gateway.settings")

import django

django.setup()

# Import Channels-enabled ASGI app


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
    """Retrieve secret manager.
        """

    from services.gateway import providers

    return providers.get_secret_manager()


def get_event_bus():
    """Retrieve event bus.
        """

    from services.gateway import providers

    return providers.get_event_bus()


def get_session_cache():
    """Retrieve session cache.
        """

    from services.gateway import providers

    return providers.get_session_cache()


def get_session_store():
    """Retrieve session store.
        """

    from services.gateway import providers

    return providers.get_session_store()