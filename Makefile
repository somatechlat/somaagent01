# ============================================================================
# SomaAgent01 Build and Deploy Makefile
# ============================================================================
# Document: SOMA-BLD-001
# Version: 2.0.0
# Date: 2026-06-15
# Status: Pre-Production
# ============================================================================

.PHONY: help dev dev-worker test check docs-check docs-register migrate build build-standalone up down clean health bootstrap verify-chat

# Interpreter for every Python recipe. `python` is not a stable name across
# machines (many distros ship only `python3`), so the interpreter is a single
# overridable variable: `make docs-check PYTHON=/path/to/venv/bin/python`.
PYTHON ?= python3

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
	@echo "  make docs-check   - ISO document control & register compliance"
	@echo "  make docs-register - Regenerate docs/iso/DOCUMENT-REGISTER.md"
	@echo "  make migrate      - Run Django migrations"
	@echo ""
	@echo "Clean:"
	@echo "  make clean        - Remove standalone containers and volumes"

# ============================================================================
# DEVELOPMENT (No Docker - Hot Reload)
# ============================================================================

dev:
	@echo "Starting gateway with hot reload..."
	DJANGO_SETTINGS_MODULE=services.gateway.settings $(PYTHON) -m uvicorn services.gateway.main:django_asgi --reload --host 0.0.0.0 --port 8010

dev-worker:
	@echo "Starting conversation worker..."
	DJANGO_SETTINGS_MODULE=services.gateway.settings $(PYTHON) -m services.conversation_worker.main

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
	@echo "Running tests against LIVE standalone infra (somaagent_net)..."
	cd infra/standalone && docker compose --profile test run --rm somaagent_tests

check:
	@echo "Running Django system check..."
	DJANGO_SETTINGS_MODULE=services.gateway.settings $(PYTHON) manage.py check

docs-check:
	@echo "Checking ISO document control & register compliance..."
	$(PYTHON) scripts/check_docs.py

docs-register:
	@echo "Regenerating document register..."
	$(PYTHON) scripts/gen_register.py

migrate:
	@echo "Running Django migrations..."
	DJANGO_SETTINGS_MODULE=services.gateway.settings $(PYTHON) manage.py migrate

# ============================================================================
# BOOTSTRAP (idempotent, fail-closed)
# ============================================================================

# Seed identity, tenant, LLM catalog, capsule, infra keys, brain settings and
# Model Roles. Pass the password on stdin (never argv):
#   echo -n "$PASSWORD" | make bootstrap BOOT_TENANT=<id> BOOT_EMAIL=<email>
# BOOT_TENANT and BOOT_EMAIL have NO default — a default IS a hardcoded value.
# Optional: BOOT_FLAGS="--dry-run"
BOOT_TENANT ?=
BOOT_EMAIL ?=
BOOT_FLAGS ?=

bootstrap:
	@test -n "$(BOOT_TENANT)" || { echo "BOOT_TENANT is required (no default)" >&2; exit 1; }
	@test -n "$(BOOT_EMAIL)" || { echo "BOOT_EMAIL is required (no default)" >&2; exit 1; }
	@echo "Running bootstrap_soma (tenant=$(BOOT_TENANT), email=$(BOOT_EMAIL))..."
	DJANGO_SETTINGS_MODULE=services.gateway.settings $(PYTHON) manage.py bootstrap_soma \
		--tenant "$(BOOT_TENANT)" \
		--sysadmin-email "$(BOOT_EMAIL)" \
		--password-stdin \
		$(BOOT_FLAGS)

# 19-assert chat-ready gate. Exits non-zero on any failure.
# Bare --check discovers scope from the settings chain / existing identity.
verify-chat:
	@echo "Running bootstrap_soma --check (verify_chat_ready)..."
	DJANGO_SETTINGS_MODULE=services.gateway.settings $(PYTHON) manage.py bootstrap_soma --check $(if $(BOOT_TENANT),--tenant "$(BOOT_TENANT)") $(if $(BOOT_EMAIL),--sysadmin-email "$(BOOT_EMAIL)")

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
	@curl -s http://localhost:20020/api/health/ | $(PYTHON) -m json.tool || echo "Gateway not responding on port 20020"

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
