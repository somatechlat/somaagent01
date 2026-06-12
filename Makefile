# ============================================================================
# SomaAgent01 Build and Deploy Makefile
# ============================================================================
# Document: SOMA-BLD-001
# Version: 1.1.0
# Date: 2026-06-01
# Status: Pre-Production
# ============================================================================

.PHONY: help dev dev-worker test check migrate build build-standalone up down clean health

# Default target
help:
	@echo "SomaAgent01 Build System"
	@echo "========================"
	@echo ""
	@echo "Development:"
	@echo "  make dev          - Run gateway with hot reload (no Docker)"
	@echo "  make dev-worker   - Run conversation worker with hot reload"
	@echo ""
	@echo "Docker Build:"
	@echo "  make build        - Build standalone Docker image"
	@echo ""
	@echo "Deploy:"
	@echo "  make up           - Start standalone stack"
	@echo "  make down         - Stop standalone stack"
	@echo ""
	@echo "Test:"
	@echo "  make test         - Run tests"
	@echo "  make check        - Django system check"
	@echo "  make migrate      - Run Django migrations"
	@echo ""
	@echo "Clean:"
	@echo "  make clean        - Remove standalone containers and volumes"

# ============================================================================
# DEVELOPMENT (No Docker - Hot Reload)
# ============================================================================

dev:
	@echo "Starting gateway with hot reload..."
	DJANGO_SETTINGS_MODULE=services.gateway.settings python -m uvicorn services.gateway.main:django_asgi --reload --host 0.0.0.0 --port 8010

dev-worker:
	@echo "Starting conversation worker..."
	DJANGO_SETTINGS_MODULE=services.gateway.settings python -m services.conversation_worker.main

# ============================================================================
# DOCKER BUILD
# ============================================================================

build:
	@echo "Building standalone Docker image..."
	cd infra/standalone && docker compose build

# ============================================================================
# DEPLOY (Standalone Mode)
# ============================================================================

up:
	@echo "Starting standalone stack..."
	cd infra/standalone && docker compose up -d

down:
	@echo "Stopping standalone stack..."
	cd infra/standalone && docker compose down

# ============================================================================
# TEST
# ============================================================================

test:
	@echo "Running tests..."
	DJANGO_SETTINGS_MODULE=services.gateway.settings python -m pytest tests/ -v

check:
	@echo "Running Django system check..."
	DJANGO_SETTINGS_MODULE=services.gateway.settings python manage.py check

migrate:
	@echo "Running Django migrations..."
	DJANGO_SETTINGS_MODULE=services.gateway.settings python manage.py migrate

# ============================================================================
# CLEAN
# ============================================================================

clean:
	@echo "Cleaning up standalone stack..."
	cd infra/standalone && docker compose down -v
	@echo "Cleaned"

# ============================================================================
# HEALTH CHECK
# ============================================================================

health:
	@curl -s http://localhost:20020/api/health/ | python -m json.tool || echo "Gateway not responding on port 20020"

# ============================================================================
# INFRASTRUCTURE RESET
# ============================================================================

reset-infra:
	@echo "Running resilient infrastructure reset..."
	@if [ -f scripts/reset_infrastructure.sh ]; then \
		./scripts/reset_infrastructure.sh; \
	else \
		echo "Reset script not found. Running manual reset..."; \
		cd infra/standalone && docker compose down -v && docker compose up -d; \
	fi
