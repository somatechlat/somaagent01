"""Staging environment settings.

Extends base.py with staging-specific configuration.
"""
from .base import *  # noqa: F401, F403

# Staging overrides
DEBUG = False
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',') if os.environ.get('ALLOWED_HOSTS') else ['*']

# Environment marker
ENVIRONMENT = 'staging'
