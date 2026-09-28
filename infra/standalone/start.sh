#!/bin/bash
set -e

# ═══════════════════════════════════════════════════════════════════════════════
# 🚀 SOMAAGENT01 STANDALONE STARTUP SCRIPT
# ═══════════════════════════════════════════════════════════════════════════════
# Handles initialization for Agent-only deployment (no Brain/Memory)
# 1. Waits for Infrastructure
# 2. Runs Django Migrations
# 3. Starts Uvicorn
# ═══════════════════════════════════════════════════════════════════════════════

echo "══════════════════════════════════════════════════════════════════"
echo "        🤖 SOMAAGENT01 STANDALONE - INITIALIZATION                "
echo "══════════════════════════════════════════════════════════════════"
echo "   ℹ️  Mode: STANDALONE (Agent + SomaBrain + SFM full triad)"
echo "   ℹ️  Brain/Memory: ENABLED"

# ─────────────────────────────────────────────────────────────────────────────────
# 1. WAIT FOR INFRASTRUCTURE
# ─────────────────────────────────────────────────────────────────────────────────
HOSTS="${POSTGRES_HOST}:${POSTGRES_PORT:-5432} ${REDIS_HOST}:${REDIS_PORT:-6379}"

for host in $HOSTS; do
    h=$(echo $host | cut -d: -f1)
    p=$(echo $host | cut -d: -f2)
    echo "⏳ Waiting for $h:$p..."
    while ! nc -z $h $p 2>/dev/null; do
        sleep 1
    done
    echo "✅ $h:$p is READY."
done

# ─────────────────────────────────────────────────────────────────────────────────
# 2. RUN MIGRATIONS
# ─────────────────────────────────────────────────────────────────────────────────
echo "🔧 [Agent01] Running Migrations..."
python manage.py migrate --noinput
echo "✅ [Agent01] Migrations Complete."

echo "🔥 [Agent01] Warming orchestrator + memory gateway..."
python - <<'PY' || echo "⚠️ warmup skipped (non-fatal)"
import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "services.gateway.settings")
django.setup()
import asyncio
from admin.core.chat_orchestrator import get_chat_orchestrator, _require_memory_gateway
_require_memory_gateway()
asyncio.run(get_chat_orchestrator())
print("✅ orchestrator + memory gateway warm")
PY

# ─────────────────────────────────────────────────────────────────────────────────
# 3. COLLECT STATIC FILES (Optional)
# ─────────────────────────────────────────────────────────────────────────────────
if [ "${COLLECT_STATIC:-false}" = "true" ]; then
    echo "📦 [Agent01] Collecting Static Files..."
    python manage.py collectstatic --noinput
    echo "✅ [Agent01] Static Files Collected."
fi

# ─────────────────────────────────────────────────────────────────────────────────
# 4. START UVICORN
# ─────────────────────────────────────────────────────────────────────────────────
echo "🚀 [Agent01] Starting Uvicorn on port ${SAGENTA_PORT:-9000}..."
exec uvicorn services.gateway.asgi:application \
    --host ${SAGENTA_HOST:-0.0.0.0} \
    --port ${SAGENTA_PORT:-9000} \
    --workers ${UVICORN_WORKERS:-1} \
    --log-level ${LOG_LEVEL:-info}
