"""
Django URL Configuration for SomaAgent01.

This module is used for Django management commands.
Runtime URL handling is done in django_setup.py.
"""

from django.contrib import admin
from django.urls import path
from admin.api import api

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v2/", api.urls),  # Mount under api/v2 per convention or root?
]
