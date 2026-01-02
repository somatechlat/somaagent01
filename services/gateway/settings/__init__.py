"""Django settings module selector.

Automatically loads the correct settings based on DJANGO_ENV environment variable.

Usage:
    # Development (default)
    DJANGO_SETTINGS_MODULE=services.gateway.settings
    
    # Production
    DJANGO_ENV=production DJANGO_SETTINGS_MODULE=services.gateway.settings
    
    # Staging
    DJANGO_ENV=staging DJANGO_SETTINGS_MODULE=services.gateway.settings
"""
import os

# Determine environment
ENVIRONMENT = os.environ.get('DJANGO_ENV', 'development')

# Load appropriate settings module
if ENVIRONMENT == 'production':
    from .production import *  # noqa: F401, F403
elif ENVIRONMENT == 'staging':
    from .staging import *  # noqa: F401, F403
else:
    from .development import *  # noqa: F401, F403

# Export environment for use in code
__all__ = ['ENVIRONMENT']
