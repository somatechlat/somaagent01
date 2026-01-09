#!/bin/bash
set -e

# ═══════════════════════════════════════════════════════════════════════════════
# 🚀 START_SAAS.SH - CENTRALIZED STARTUP ORCHESTRATOR
# ═══════════════════════════════════════════════════════════════════════════════
# This script handles the ENTIRE initialization sequence for the SaaS Stack.
# 1. Loads Environment
# 2. Waits for Valid Infrastructure (Ports 639xx mapped internally)
# 3. Runs Django Migrations (Brain -> Memory -> Agent)
# 4. Hands over to Supervisor
# ═══════════════════════════════════════════════════════════════════════════════

echo "🐳 [SomaStack] Starting SaaS Initialization..."

# 1. WAIT FOR INFRASTRUCTURE
# --------------------------
HOSTS="${SOMA_POSTGRES_HOST}:5432 ${SOMA_REDIS_HOST}:6379 ${SOMA_KAFKA_HOST}:9092"
# Add Milvus check using curl or python script later if needed, mostly relies on etcd/minio

for host in $HOSTS; do
    h=$(echo $host | cut -d: -f1)
    p=$(echo $host | cut -d: -f2)
    echo "⏳ Waiting for $h:$p..."
    while ! nc -z $h $p; do   
      sleep 1
    done
    echo "✅ $h:$p is READY."
done

# 2. RUN MIGRATIONS (Sequential)
# ------------------------------
echo "🧠 [SomaBrain] Running Migrations..."
python manage_brain.py migrate --noinput
echo "✅ [SomaBrain] Migrations Complete."

echo "💾 [FractalMemory] Running Migrations..."
python manage_memory.py migrate --noinput
echo "✅ [FractalMemory] Migrations Complete."

echo "🕵️ [Agent01] Running Migrations..."
python manage_agent.py migrate --noinput
echo "✅ [Agent01] Migrations Complete."

# 3. START SUPERVISOR
# -------------------
echo "👮 [Supervisor] Starting Process Manager..."
exec supervisord -c /etc/supervisor/conf.d/supervisord.conf
