"""
Django URL Configuration for SomaAgent01.

This module is used for Django management commands.
Runtime URL handling is done in django_setup.py.
"""

from django.contrib import admin
from django.http import JsonResponse
from django.urls import path
from admin.api import api


def health_check(request):
    """Health check endpoint for Docker and load balancers."""
    return JsonResponse({
        "status": "ok",
        "service": "somaagent-gateway",
        "version": "1.0.0",
    })


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v2/", api.urls),
    path("api/health/", health_check),
    path("health/", health_check),  # Alternative path
]

