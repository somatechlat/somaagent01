# ============================================================================
# SomaAgent01 Build & Deploy Makefile
# ============================================================================
#
# VIBE COMPLIANT - Multiple deployment types for fast iteration
#
# QUICK START:
#   make dev     - Start local dev (hot reload)
#   make build   - Build all images
#   make up      - Start full stack
#   make test    - Run tests on real infra
#
# ============================================================================

.PHONY: help dev build up down test clean gateway worker ml

# Default target
help:
	@echo "SomaAgent01 Build System"
	@echo "========================"
	@echo ""
	@echo "Development:"
	@echo "  make dev          - Run gateway with hot reload (no Docker)"
	@echo "  make dev-worker   - Run worker with hot reload"
	@echo ""
	@echo "Docker Build:"
	@echo "  make build        - Build all images"
	@echo "  make build-gateway - Build gateway image only (~8 min)"
	@echo "  make build-worker  - Build worker image"
	@echo "  make build-analyzer - Build analyzer image (slow)"
	@echo ""
	@echo "Deploy:"
	@echo "  make up           - Start full stack"
	@echo "  make up-infra     - Start infrastructure only"
	@echo "  make up-core      - Start core services"
	@echo "  make down         - Stop everything"
	@echo ""
	@echo "Test:"
	@echo "  make test         - Run all tests on real infra"
	@echo "  make check        - Django system check"
	@echo ""
	@echo "Clean:"
	@echo "  make clean        - Remove all containers and images"

# ============================================================================
# DEVELOPMENT (No Docker - Hot Reload)
# ============================================================================

dev:
	@echo "🚀 Starting gateway with hot reload..."
	DJANGO_SETTINGS_MODULE=services.gateway.settings python -m uvicorn services.gateway.main:django_asgi --reload --host 0.0.0.0 --port 8010

dev-worker:
	@echo "🚀 Starting conversation worker..."
	DJANGO_SETTINGS_MODULE=services.gateway.settings python -m services.conversation_worker.main

# ============================================================================
# DOCKER BUILD
# ============================================================================

build: build-gateway build-worker
	@echo "✅ All core images built (run build-analyzer for ML)"

build-gateway:
	@echo "🔨 Building gateway image..."
	docker build -f Dockerfile.gateway -t somaagent-gateway:latest .

build-worker:
	@echo "🔨 Building worker image..."
	docker build -f Dockerfile.worker -t somaagent-worker:latest .

build-analyzer:
	@echo "🔨 Building analyzer image (CPU)..."
	docker build -f Dockerfile.analyzer -t somaagent-analyzer:latest .

build-analyzer-gpu:
	@echo "🔨 Building analyzer image (CUDA GPU)..."
	docker build -f Dockerfile.analyzer --build-arg TORCH_VARIANT=cuda -t somaagent-analyzer:gpu .

# ============================================================================
# DEPLOY
# ============================================================================

up: up-infra up-core
	@echo "✅ Full stack running"

up-infra:
	@echo "🚀 Starting infrastructure..."
	docker compose up -d postgres redis kafka

up-core:
	@echo "🚀 Starting core services..."
	docker compose --profile core up -d

down:
	@echo "🛑 Stopping all services..."
	docker compose --profile core down
	docker compose down

# ============================================================================
# TEST
# ============================================================================

test:
	@echo "🧪 Running tests on real infrastructure..."
	DJANGO_SETTINGS_MODULE=services.gateway.settings python -m pytest tests/ -v

check:
	@echo "🔍 Django system check..."
	python manage.py check

migrate:
	@echo "🔄 Running migrations..."
	python manage.py migrate

# ============================================================================
# CLEAN
# ============================================================================

clean:
	@echo "🧹 Cleaning up..."
	docker compose --profile core down -v
	docker compose down -v
	docker rmi somaagent-gateway:latest somaagent-worker:latest somaagent-analyzer:latest 2>/dev/null || true
	@echo "✅ Cleaned"

# ============================================================================
# QUICK ITERATION
# ============================================================================

# Fast rebuild and restart gateway only
restart-gateway: build-gateway
	docker compose stop gateway
	docker compose rm -f gateway
	docker compose --profile core up -d gateway

# Check health
health:
	@curl -s http://localhost:8010/api/health/ | python -m json.tool || echo "Gateway not responding"

# ============================================================================
# UTILITIES
# ============================================================================

reset-infra:
	@echo "🔄 Running resilient infrastructure reset..."
	@./scripts/reset_infrastructure.sh
