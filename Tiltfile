# -*- mode: Python -*-
# =============================================================================
# SOMASTACK TILTFILE - MINIMAL WORKING VERSION
# =============================================================================
# Commands:
#   tilt up --port 10351
#   open http://localhost:10351
# =============================================================================

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

docker_compose(
    'docker-compose.yml',
    # VIBE: Full stack deployment per user request ("ALL OF THEM")
    profiles=['core', 'vectors', 'security', 'observability'],
)

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
# SOMA STACK SERVICES
# =============================================================================

# SomaFractalMemory (Port 10101)
# SomaFractalMemory (Port 10101) - Production-grade ASGI
local_resource(
    'somafractalmemory',
    serve_cmd='.venv/bin/uvicorn somafractalmemory.asgi:application --host 0.0.0.0 --port 10101 --reload',
    serve_dir='../somafractalmemory',
    links=['http://localhost:10101/api/v1/docs'],
    labels=['soma-stack'],
    resource_deps=['postgres'],
)

local_resource(
    'somabrain',
    serve_cmd='.venv/bin/uvicorn somabrain.asgi:application --host 0.0.0.0 --port 30101 --reload',
    serve_dir='../somabrain',
    # VIBE Rule 44: Port Sovereignty - Milvus mapped to 20530 on host
    env={'SOMABRAIN_MILVUS_PORT': '20530', 'SOMABRAIN_MILVUS_HOST': 'localhost'},
    links=['http://localhost:30101/api/v1/docs'],
    labels=['soma-stack'],
    resource_deps=['postgres', 'redis', 'somafractalmemory', 'milvus'],
)

# =============================================================================
# DJANGO API (Production ASGI Server)
# =============================================================================

local_resource(
    'django-api',
    serve_cmd='.venv/bin/uvicorn services.gateway.asgi:application --host 0.0.0.0 --port 20020 --reload',
    serve_dir='.',
    links=['http://localhost:20020/api/v2/docs'],
    labels=['backend'],
    resource_deps=['postgres', 'redis', 'kafka', 'somabrain', 'somafractalmemory'],
)
