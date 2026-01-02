# -*- mode: Python -*-
# =============================================================================
# SOMASTACK TILTFILE - FULL INFRASTRUCTURE
# =============================================================================
# Hierarchy: SomaStack > SomaAgent01 > SomaBrain > SFM
#
# Container Naming Convention:
#   somastack_somaagent01_*     - SomaAgent01 containers
#   somastack_somabrain_*       - SomaBrain containers
#   somastack_sfm_*             - SomaFractalMemory containers
#   somastack_shared_*          - Shared services
#
# Commands:
#   tilt up --port 10351  - Start SomaStack (separate from Sercop)
#   tilt down             - Stop all services
#   open http://localhost:10351  - SomaStack Tilt dashboard
#
# Port Ranges:
#   AWS Emulation:     4566 (LocalStack), 8000 (DynamoDB)
#   SomaAgent01:       20000-20199
#   SomaFractalMemory: 21000-21099
#   SomaBrain:         30000-30199
#   Shared Services:   49000-49099
# =============================================================================

# =============================================================================
# AWS EMULATION (LocalStack + DynamoDB)
# =============================================================================

# LocalStack (S3, SQS, Lambda, etc.)
local_resource(
    'aws-localstack',
    serve_cmd='docker start localstack 2>/dev/null || docker run --rm --name localstack -p 4566:4566 localstack/localstack:latest',
    links=['http://localhost:4566/_localstack/health'],
    labels=['aws'],
)

# DynamoDB Local
local_resource(
    'aws-dynamodb',
    serve_cmd='docker start dynamodb 2>/dev/null || docker run --rm --name dynamodb -p 8000:8000 amazon/dynamodb-local:latest',
    links=['http://localhost:8000'],
    labels=['aws'],
)

# =============================================================================
# SHARED SERVICES (49xxx)
# =============================================================================

# Shared Keycloak (already running as docker container)
local_resource(
    'shared-keycloak',
    serve_cmd='docker compose -f shared/keycloak/cluster/docker-compose.yml up',
    serve_dir='.',
    links=['http://localhost:49010'],
    labels=['shared'],
    port_forwards=['49010:8080', '49011:5432'],
)

# =============================================================================
# SOMA FRACTAL MEMORY (21xxx) - Layer 1
# =============================================================================

docker_compose(
    '../somafractalmemory/docker-compose.yml',
    project_name='somafractalmemory',
    profiles=['core'],
    env_file='../somafractalmemory/.env'
)

dc_resource('somafractalmemory_api', 
    labels=['memory'], 
    port_forwards=['21000:9595'],
    resource_deps=['aws-localstack']
)
dc_resource('somafractalmemory_postgres', 
    labels=['memory'], 
    port_forwards=['21001:5432']
)
dc_resource('somafractalmemory_redis', 
    labels=['memory'], 
    port_forwards=['21002:6379']
)
dc_resource('somafractalmemory_milvus', 
    labels=['memory'], 
    port_forwards=['21003:19530', '21004:9091']
)

# =============================================================================
# SOMA BRAIN (30xxx) - Layer 2
# =============================================================================

docker_compose(
    '../somabrain/docker-compose.yml',
    project_name='somabrain',
    env_file='../somabrain/.env'
)

dc_resource('somabrain_redis', 
    labels=['brain'], 
    port_forwards=['30100:6379']
)
dc_resource('somabrain_postgres', 
    labels=['brain'], 
    port_forwards=['30106:5432']
)
dc_resource('somabrain_kafka', 
    labels=['brain'], 
    port_forwards=['30102:9094']
)
dc_resource('somabrain_app', 
    labels=['brain'], 
    port_forwards=['30101:9696'],
    resource_deps=['somafractalmemory_api', 'somabrain_redis', 'somabrain_postgres', 'somabrain_kafka']
)

# =============================================================================
# SOMA AGENT 01 (20xxx) - Layer 3
# =============================================================================

docker_compose(
    'docker-compose.yml',
    project_name='somaagent01',
    profiles=['core']
)

dc_resource('somaagent-postgres', 
    labels=['agent'], 
    port_forwards=['20432:5432']
)
dc_resource('somaagent-redis', 
    labels=['agent'], 
    port_forwards=['20379:6379']
)
dc_resource('somaagent-kafka', 
    labels=['agent'], 
    port_forwards=['20092:9092']
)

# =============================================================================
# WEBUI DEVELOPMENT (Live Reload)
# =============================================================================

local_resource(
    'webui-dev',
    serve_cmd='npm run dev -- --port 20173',
    serve_dir='webui',
    links=['http://localhost:20173'],
    labels=['agent'],
    resource_deps=['somaagent-postgres', 'somaagent-redis'],
    auto_init=False  # Manual start
)

# =============================================================================
# DJANGO API (Eye of God)
# =============================================================================

local_resource(
    'django-api',
    serve_cmd='python manage.py runserver 0.0.0.0:20020',
    serve_dir='admin',
    links=['http://localhost:20020'],
    labels=['agent'],
    resource_deps=['somaagent-postgres', 'somaagent-redis', 'somabrain_app'],
    auto_init=False  # Manual start
)

# =============================================================================
# STARTUP ORDER & LINKS
# =============================================================================
# 1. AWS Emulators (LocalStack, DynamoDB)
# 2. Shared (Keycloak)
# 3. SomaFractalMemory (Memory Layer)
# 4. SomaBrain (Cognition Layer)
# 5. SomaAgent01 (Application Layer)
# 6. WebUI / Django API
# =============================================================================
