#!/bin/bash
# Django Entrypoint Script
# ============================================================================
# This script runs Django migrations and starts the application.
# Used by all Django-based services (gateway, workers).
# ============================================================================

set -e

echo "🔧 Running Django migrations..."
python manage.py migrate --noinput 2>/dev/null || echo "⚠️ Migrations skipped (DB may not be ready)"

echo "🚀 Starting: $@"
exec "$@"
