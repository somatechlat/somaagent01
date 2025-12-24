#!/bin/bash
# ============================================================================
# Django Quick Entrypoint
# ============================================================================
# VIBE COMPLIANT - Fast startup for production
# ============================================================================

set -e

# Optional: Run migrations if requested
if [ "$RUN_MIGRATIONS" = "true" ]; then
    echo "🔄 Running migrations..."
    python manage.py migrate --noinput 2>/dev/null || echo "⚠️ Migration skipped"
fi

# Start application
echo "🚀 Starting: $@"
exec "$@"
