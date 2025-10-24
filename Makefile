# Simple docs helpers

.PHONY: docs-install docs-build docs-serve docs-verify

docs-install:
	pip install -r docs/requirements-docs.txt

docs-build:
	mkdocs build --strict

docs-serve:
	mkdocs serve -a 0.0.0.0:8001

docs-verify: docs-build
	@echo "Docs build OK"
# ==============================================================================
# Makefile for Agent Zero Development Environment
#
# Provides common commands for building, running, and managing the Docker stack.
# ==============================================================================

# Docker Compose project name
COMPOSE_PROJECT_NAME ?= somaagent01
# Docker Compose file path
# Docker Compose file path
COMPOSE_FILE ?= docker-compose.yaml
# Profiles to activate
PROFILES ?= core,dev

# Expand comma-separated PROFILES into multiple --profile flags for docker compose
# Use shell `tr` to convert commas to spaces robustly, then prefix each with --profile
DOCKER_PROFILES := $(foreach p,$(shell echo $(PROFILES) | tr ',' ' '),--profile $(p))

# Use this to export environment variables from a .env file if it exists
ifneq (,$(wildcard ./.env))
    include .env
    export
endif

.PHONY: help build up down restart logs rebuild clean

help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  help      Show this help message."
	@echo "  build     Build or rebuild the Docker images for the stack."
	@echo "  up        Create and start the containers in detached mode."
	@echo "  down      Stop and remove the containers, networks, and volumes."
	@echo "  restart   Restart all services."
	@echo "  logs      Follow the logs of all services."
	@echo "  rebuild   Stop, rebuild, and restart the entire stack."
	@echo "  clean     Remove all build artifacts and Docker volumes."
	@echo ""
	@echo "Developer (lightweight) targets:"
	@echo "  dev-up                    Start minimal dev stack (docker-compose.dev.yaml)."
	@echo "  dev-down                  Stop minimal dev stack."
	@echo "  dev-logs                  Tail logs for minimal dev stack."
	@echo "  dev-rebuild               Rebuild and restart minimal dev stack."
	@echo "  dev-build [SERVICES=...]  Build images for specific services (or all)."
	@echo "  dev-up-services SERVICES=svc1 [svc2 ...]    Start specific services."
	@echo "  dev-restart-services SERVICES=svc1 [svc2 ...]  Rebuild+start specific services."
	@echo "  dev-logs-svc SERVICES=svc1 [svc2 ...]       Tail logs for specific services."
	@echo "  dev-ps                    Show dev stack containers."
	@echo "  dev-up-ui                 Start dev stack including UI profile."
	@echo "  dev-restart-ui            Rebuild and start dev stack including UI profile."
	@echo ""
	@echo "Helm quickstart targets:"
	@echo "  helm-dev-up               Install soma-infra (dev) and soma-stack (dev) into cluster."
	@echo "  helm-dev-down             Uninstall soma and soma-infra releases from cluster."

build:
	@echo "Building Docker images..."
	# Expand comma-separated PROFILES into multiple --profile flags for docker compose
	docker compose -p $(COMPOSE_PROJECT_NAME) -f $(COMPOSE_FILE) $(DOCKER_PROFILES) build

up:
	@echo "Starting the stack in detached mode..."
	# Expand comma-separated PROFILES into multiple --profile flags for docker compose
	@docker network inspect somaagent01 >/dev/null 2>&1 || docker network create somaagent01
	docker compose -p $(COMPOSE_PROJECT_NAME) -f $(COMPOSE_FILE) $(DOCKER_PROFILES) up -d

down:
	@echo "Stopping and removing the stack..."
	docker compose -p $(COMPOSE_PROJECT_NAME) -f $(COMPOSE_FILE) down

restart: down up

logs:
	@echo "Following logs for all services..."
	docker compose -p $(COMPOSE_PROJECT_NAME) -f $(COMPOSE_FILE) $(DOCKER_PROFILES) logs -f

rebuild: down build up

clean: down
	@echo "Removing Docker volumes..."
	docker volume rm $(COMPOSE_PROJECT_NAME)_kafka_data || true
	docker volume rm $(COMPOSE_PROJECT_NAME)_redis_data || true
	docker volume rm $(COMPOSE_PROJECT_NAME)_postgres_data || true
	@echo "Cleanup complete."

# ------------------------------------------------------------------------------
# Lightweight developer stack helpers (docker-compose.dev.yaml)
# ------------------------------------------------------------------------------

DEV_COMPOSE_FILE := docker-compose.yaml
DEV_PROFILES := core,dev

# Convenience wrapper for dev docker compose
DEV_DOCKER := docker compose -p somaagent01_dev -f $(DEV_COMPOSE_FILE)

.PHONY: dev-up dev-down dev-logs dev-rebuild

dev-up:
	@echo "Starting lightweight developer stack..."
	$(MAKE) up COMPOSE_FILE=$(DEV_COMPOSE_FILE) PROFILES=$(DEV_PROFILES) COMPOSE_PROJECT_NAME=somaagent01_dev

dev-down:
	@echo "Stopping lightweight developer stack..."
	$(MAKE) down COMPOSE_FILE=$(DEV_COMPOSE_FILE) COMPOSE_PROJECT_NAME=somaagent01_dev

dev-logs:
	@echo "Tailing logs for lightweight developer stack..."
	$(MAKE) logs COMPOSE_FILE=$(DEV_COMPOSE_FILE) PROFILES=$(DEV_PROFILES) COMPOSE_PROJECT_NAME=somaagent01_dev

dev-rebuild:
	@echo "Rebuilding lightweight developer stack..."
	$(MAKE) rebuild COMPOSE_FILE=$(DEV_COMPOSE_FILE) PROFILES=$(DEV_PROFILES) COMPOSE_PROJECT_NAME=somaagent01_dev

.PHONY: dev-up-ui dev-restart-ui

# Start core + ui profiles without editing docker files
dev-up-ui:
	@echo "Starting developer stack with UI profile..."
	$(MAKE) up COMPOSE_FILE=$(DEV_COMPOSE_FILE) PROFILES=core,dev COMPOSE_PROJECT_NAME=somaagent01_dev

dev-restart-ui:
	@echo "Rebuilding developer stack with UI profile..."
	$(MAKE) rebuild COMPOSE_FILE=$(DEV_COMPOSE_FILE) PROFILES=core,dev COMPOSE_PROJECT_NAME=somaagent01_dev

.PHONY: dev-build dev-up-services dev-restart-services dev-logs-svc dev-ps

# Build images for specific services (or all if SERVICES is empty)
dev-build:
	@echo "Building developer stack images $(if $(SERVICES),for: $(SERVICES),for all services)..."
	$(DEV_DOCKER) build $(SERVICES)

# Start specific services
dev-up-services:
	@if [ -z "$(SERVICES)" ]; then echo "SERVICES is required (e.g., make dev-up-services SERVICES=conversation-worker)"; exit 1; fi
	@echo "Starting services: $(SERVICES)"
	$(DEV_DOCKER) up -d $(SERVICES)

# Rebuild and restart specific services
dev-restart-services:
	@if [ -z "$(SERVICES)" ]; then echo "SERVICES is required (e.g., make dev-restart-services SERVICES=tool-executor)"; exit 1; fi
	@echo "Rebuilding and restarting services: $(SERVICES)"
	$(DEV_DOCKER) up -d --build $(SERVICES)

# Tail logs for specific services
dev-logs-svc:
	@if [ -z "$(SERVICES)" ]; then echo "SERVICES is required (e.g., make dev-logs-svc SERVICES=conversation-worker)"; exit 1; fi
	@echo "Tailing logs for: $(SERVICES)"
	$(DEV_DOCKER) logs -f $(SERVICES)

# Show dev containers
dev-ps:
	$(DEV_DOCKER) ps

.PHONY: helm-dev-up helm-dev-down

helm-dev-up:
	@echo "Installing Helm charts for dev (infra + app)..."
	bash scripts/bootstrap-dev.sh

helm-dev-down:
	@echo "Uninstalling Helm charts for dev (infra + app)..."
	bash scripts/destroy-dev.sh
# ------------------------------------------------------------------------------
# Slim runtime (prebuilt image) helpers
# ------------------------------------------------------------------------------

SLIM_COMPOSE_FILE := docker-compose.slim.yaml
SLIM_PROFILES := core,dev

.PHONY: slim-up slim-down slim-logs slim-rebuild

slim-up:
	@echo "Starting slim stack (prebuilt image)..."
	@docker network inspect somaagent01 >/dev/null 2>&1 || docker network create somaagent01
	docker compose -p somaagent01_slim -f $(SLIM_COMPOSE_FILE) --profile core --profile dev up -d

slim-down:
	@echo "Stopping slim stack..."
	docker compose -p somaagent01_slim -f $(SLIM_COMPOSE_FILE) down

slim-logs:
	@echo "Tailing logs for slim stack..."
	docker compose -p somaagent01_slim -f $(SLIM_COMPOSE_FILE) --profile core --profile dev logs -f

slim-rebuild: slim-down
	@echo "Recreating slim stack..."
	$(MAKE) slim-up

# ------------------------------------------------------------------------------
# Slim+Browser helpers
# ------------------------------------------------------------------------------

SLIM_BROWSER_COMPOSE_FILE := docker-compose.slim-browser.yaml

.PHONY: slim-browser-up slim-browser-down slim-browser-logs slim-browser-rebuild slim-browser-build

slim-browser-build:
	@echo "Building slim-browser image..."
	docker build -f Dockerfile -t somaagent01-slim:latest .
	docker build -f Dockerfile.slim-browser -t somaagent01-slim-browser:latest .

slim-browser-up: slim-browser-build
	@echo "Starting slim-browser stack (prebuilt image with Chromium)..."
	@docker network inspect somaagent01 >/dev/null 2>&1 || docker network create somaagent01
	docker compose -p somaagent01_slim_browser -f $(SLIM_BROWSER_COMPOSE_FILE) --profile core --profile dev up -d

slim-browser-down:
	@echo "Stopping slim-browser stack..."
	docker compose -p somaagent01_slim_browser -f $(SLIM_BROWSER_COMPOSE_FILE) down

slim-browser-logs:
	@echo "Tailing logs for slim-browser stack..."
	docker compose -p somaagent01_slim_browser -f $(SLIM_BROWSER_COMPOSE_FILE) --profile core --profile dev logs -f

slim-browser-rebuild: slim-browser-down slim-browser-up
