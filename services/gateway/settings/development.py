"""Development environment settings.

Extends base.py with development-specific overrides.
"""
from .base import *  # noqa: F401, F403

# Development overrides
DEBUG = True
ALLOWED_HOSTS = ['*']

# Environment marker
ENVIRONMENT = 'development'
