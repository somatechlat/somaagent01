"""Production environment settings.

Extends base.py with production-specific security and validation.
"""
from .base import *  # noqa: F401, F403
from .service_registry import SERVICES

# Production security
DEBUG = False
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')

# Environment marker  
ENVIRONMENT = 'production'

# Validate ALL required services are configured
missing_services = SERVICES.validate_required(ENVIRONMENT)
if missing_services:
    raise ValueError(
        f"❌ PRODUCTION STARTUP BLOCKED\n"
        f"   Missing required service configuration:\n"
        f"   {', '.join(missing_services)}\n\n"
        f"   All required services must be explicitly configured in production.\n"
        f"   See: .env.template for required environment variables"
    )
