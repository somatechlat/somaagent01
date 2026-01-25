"""
WSGI config for Agent-as-a-Service (AAAS) Mode.

Exposes the WSGI application as `application`.

Usage:
    gunicorn infra.aaas.unified_wsgi:application --bind 0.0.0.0:9000 --workers 4
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "infra.aaas.unified_settings")
os.environ.setdefault("SOMA_SINGLE_PROCESS", "true")

application = get_wsgi_application()
