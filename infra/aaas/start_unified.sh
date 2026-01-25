#!/bin/bash
# =============================================================================
# SOMA AGENT-AS-A-SERVICE (AAAS) UNIFIED STARTUP SCRIPT
# =============================================================================
# Launches the entire SOMA Triad (Agent + Brain + Memory) as a SINGLE ENTITY.
# This is the TRUE single-process mode with direct Python calls, no HTTP.
#
# SomaAgent01 is the MASTER - it orchestrates everything.
#
# Usage:
#   ./start_unified.sh
#
# Environment:
#   SOMA_SINGLE_PROCESS=true (automatically set by this script)
#   DJANGO_SETTINGS_MODULE=infra.aaas.unified_settings
# =============================================================================

set -euo pipefail

echo "═══════════════════════════════════════════════════════════════════════════"
echo "🚀 SOMA STACK UNIFIED MODE - Single Entity Deployment"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
echo "SomaAgent01 is the MASTER orchestrator."
echo "SomaBrain and SomaFractalMemory run IN-PROCESS as libraries."
echo ""

# =============================================================================
# ENVIRONMENT SETUP
# =============================================================================

export SOMA_SINGLE_PROCESS=true
export DJANGO_SETTINGS_MODULE=infra.aaas.unified_settings
export PYTHONPATH=/app/somaAgent01:/app/somabrain:/app/somafractalmemory:/app:${PYTHONPATH:-}

# =============================================================================
# WAIT FOR INFRASTRUCTURE
# =============================================================================

echo "📡 Waiting for infrastructure services..."

wait_for_port() {
    local host=$1
    local port=$2
    local name=$3
    local max_attempts=30
    local attempt=1

    while ! nc -z "$host" "$port" 2>/dev/null; do
        echo "   ⏳ Waiting for $name ($host:$port)... attempt $attempt/$max_attempts"
        sleep 2
        attempt=$((attempt + 1))
        if [ $attempt -gt $max_attempts ]; then
            echo "   ❌ Timeout waiting for $name"
            exit 1
        fi
    done
    echo "   ✅ $name is ready"
}

# Wait for core infrastructure
wait_for_port "${SOMA_POSTGRES_HOST:-somastack_postgres}" 5432 "PostgreSQL"
wait_for_port "${SOMA_REDIS_HOST:-somastack_redis}" 6379 "Redis"
wait_for_port "${SOMA_MILVUS_HOST:-somastack_milvus}" 19530 "Milvus"

echo ""

# =============================================================================
# DATABASE MIGRATIONS - Brain-First Order (Critical for cognitive integrity)
# =============================================================================

echo "🔄 Running migrations (Brain-First order)..."

cd /app

# 1. SomaBrain migrations FIRST (source of truth for cognitive models)
echo "   📦 Migrating SomaBrain..."
python -c "
import django
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'infra.aaas.unified_settings'
django.setup()
from django.core.management import call_command
call_command('migrate', '--database=brain', '--noinput', verbosity=0)
" 2>&1 | while read line; do echo "      $line"; done
echo "   ✅ SomaBrain migrations complete"

# 2. SomaFractalMemory migrations SECOND (depends on Brain)
echo "   📦 Migrating SomaFractalMemory..."
python -c "
import django
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'infra.aaas.unified_settings'
django.setup()
from django.core.management import call_command
call_command('migrate', '--database=memory', '--noinput', verbosity=0)
" 2>&1 | while read line; do echo "      $line"; done
echo "   ✅ SomaFractalMemory migrations complete"

# 3. SomaAgent01 migrations THIRD (depends on Brain + Memory)
echo "   📦 Migrating SomaAgent01..."
python -c "
import django
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'infra.aaas.unified_settings'
django.setup()
from django.core.management import call_command
call_command('migrate', '--database=default', '--noinput', verbosity=0)
" 2>&1 | while read line; do echo "      $line"; done
echo "   ✅ SomaAgent01 migrations complete"

echo ""

# =============================================================================
# VERIFY SINGLE-PROCESS IMPORTS
# =============================================================================

echo "🔍 Verifying single-process imports..."

python -c "
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'infra.aaas.unified_settings'
os.environ['SOMA_SINGLE_PROCESS'] = 'true'

# Test Agent imports
from admin.agents.models import Agent
print('   ✅ Agent models imported')

# Test Brain imports
from somabrain.quantum import QuantumLayer, HRRConfig
from somabrain.agent_memory import encode_memory
print('   ✅ Brain cognitive core imported')

# Test Memory imports
from somafractalmemory.services import MemoryService
print('   ✅ Memory services imported')

print('')
print('   🎉 All services available for direct Python calls!')
"

echo ""

# =============================================================================
# LAUNCH UNIFIED APPLICATION
# =============================================================================

echo "═══════════════════════════════════════════════════════════════════════════"
echo "🌟 Starting UNIFIED SOMA Stack on port 9000"
echo "   Mode: SINGLE ENTITY (no HTTP between services)"
echo "   Settings: infra.aaas.unified_settings"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""

# Choose server based on environment
WORKERS=${SOMA_WORKERS:-4}
PORT=${SOMA_PORT:-9000}

if [ "${SOMA_USE_UVICORN:-false}" = "true" ]; then
    # Use uvicorn for async/WebSocket support
    echo "🚀 Launching with uvicorn (ASGI)..."
    exec uvicorn infra.aaas.unified_asgi:application \
        --host 0.0.0.0 \
        --port "$PORT" \
        --workers "$WORKERS" \
        --timeout-keep-alive 120
else
    # Use gunicorn for production (default)
    echo "🚀 Launching with gunicorn (WSGI)..."
    exec gunicorn infra.aaas.unified_wsgi:application \
        --bind "0.0.0.0:$PORT" \
        --workers "$WORKERS" \
        --timeout 120 \
        --access-logfile - \
        --error-logfile -
fi
