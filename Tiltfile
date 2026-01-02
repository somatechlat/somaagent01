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
    profiles=['core'],  # Start with core services only
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
local_resource(
    'somafractalmemory',
    serve_cmd='.venv/bin/python manage.py runserver 0.0.0.0:10101',
    serve_dir='../somafractalmemory',
    links=['http://localhost:10101/api/v1/docs'],
    labels=['soma-stack'],
    resource_deps=['postgres'],
)

local_resource(
    'somabrain',
    serve_cmd='.venv/bin/python manage.py runserver 0.0.0.0:30101',
    serve_dir='../somabrain',
    links=['http://localhost:30101/api/v1/docs'],
    labels=['soma-stack'],
    resource_deps=['postgres', 'redis', 'somafractalmemory'],
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
