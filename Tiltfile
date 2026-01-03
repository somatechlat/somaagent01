print("""
+==============================================================+
|         SOMASTACK - LOCAL DEVELOPMENT                        |
+==============================================================+
|  Dashboard:   http://localhost:10351                         |
|  WebUI:       http://localhost:20173                         |
|  Django API:  http://localhost:20020                         |
+==============================================================+
""")

# =============================================================================
# INFRASTRUCTURE - ALL CONTAINERS FROM docker-compose.yml
# PRIMARY DEPLOYMENT CONFIGURATION FOR ALL SOMA REPOS
# =============================================================================

docker_compose('docker-compose.yml')

# =============================================================================
# WEBUI DEVELOPMENT
# =============================================================================

local_resource(
    'webui-dev',
    serve_cmd='npm run dev -- --port 20173',
    serve_dir='webui',
    links=['http://localhost:20173'],
    labels=['frontend'],
)

# =============================================================================
# ORCHESTRATION: DATABASE MIGRATIONS (The "Perfect Startup" Glue)
# =============================================================================

local_resource(
    'database-migrations',
    cmd='''
        set -e
        export SA01_DEPLOYMENT_MODE=PROD
        echo "⏳ Waiting for Postgres..." && sleep 5
        echo "🔄 Migrating SomaFractalMemory (Production Mode)..."
        SOMA_DB_NAME=somafractalmemory ../somafractalmemory/.venv/bin/python ../somafractalmemory/manage.py migrate --noinput
        echo "🔄 Migrating SomaBrain..."
        ../somabrain/.venv/bin/python ../somabrain/manage.py migrate --noinput
        echo "🔄 Migrating SomaAgent01 Gateway..."
        .venv/bin/python manage.py migrate --noinput
        echo "✅ All Migrations Complete"
    ''',
    resource_deps=['postgres'],
    labels=['setup'],
)

# =============================================================================
# SOMA STACK SERVICES
# =============================================================================

# SomaFractalMemory (Port 10101) - Production-grade ASGI
local_resource(
    'somafractalmemory',
    serve_cmd='SOMA_DB_NAME=somafractalmemory .venv/bin/uvicorn somafractalmemory.asgi:application --host 0.0.0.0 --port 10101 --reload',
    serve_dir='../somafractalmemory',
    env={'SA01_DEPLOYMENT_MODE': 'PROD'},
    links=['http://localhost:10101/api/v1/docs'],
    labels=['soma-stack'],
    resource_deps=['postgres', 'database-migrations'],
)

local_resource(
    'somabrain',
    serve_cmd='.venv/bin/uvicorn somabrain.asgi:application --host 0.0.0.0 --port 30101 --reload',
    serve_dir='../somabrain',
    # VIBE Rule 44: Port Sovereignty - Milvus mapped to 20530 on host
    env={'SOMABRAIN_MILVUS_PORT': '20530', 'SOMABRAIN_MILVUS_HOST': 'localhost', 'SA01_DEPLOYMENT_MODE': 'PROD'},
    links=['http://localhost:30101/api/v1/docs'],
    labels=['soma-stack'],
    resource_deps=['postgres', 'redis', 'somafractalmemory', 'milvus', 'database-migrations'],
)

# =============================================================================
# DJANGO API (Production ASGI Server)
# =============================================================================

local_resource(
    'django-api',
    serve_cmd='.venv/bin/uvicorn services.gateway.asgi:application --host 0.0.0.0 --port 20020 --reload',
    serve_dir='.',
    env={'SA01_DEPLOYMENT_MODE': 'PROD'},
    links=['http://localhost:20020/api/v2/docs'],
    labels=['backend'],
    resource_deps=['postgres', 'redis', 'kafka', 'somabrain', 'somafractalmemory', 'database-migrations'],
)
