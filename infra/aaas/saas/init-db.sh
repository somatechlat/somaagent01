#!/bin/bash
set -e

# ═══════════════════════════════════════════════════════════════════════════════
# SOMA STACK AAAS - DATABASE INITIALIZATION
# ═══════════════════════════════════════════════════════════════════════════════
# This script runs on Postgres startup to ensure all 3 logical databases exist
# within the single shared instance (`somastack_postgres`).
# ═══════════════════════════════════════════════════════════════════════════════

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE DATABASE somabrain;
    CREATE DATABASE somamemory;
    CREATE DATABASE somaagent;
    
    GRANT ALL PRIVILEGES ON DATABASE somabrain TO $POSTGRES_USER;
    GRANT ALL PRIVILEGES ON DATABASE somamemory TO $POSTGRES_USER;
    GRANT ALL PRIVILEGES ON DATABASE somaagent TO $POSTGRES_USER;
EOSQL

echo "✅ SomaStack AAAS Databases Created Successfully"
