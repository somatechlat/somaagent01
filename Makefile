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

build:
	@echo "Building Docker images..."
	# Expand comma-separated PROFILES into multiple --profile flags for docker compose
	docker compose -p $(COMPOSE_PROJECT_NAME) -f $(COMPOSE_FILE) $(DOCKER_PROFILES) build

up:
	@echo "Starting the stack in detached mode..."
	# Expand comma-separated PROFILES into multiple --profile flags for docker compose
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
	$(MAKE) up COMPOSE_FILE=$(DEV_COMPOSE_FILE) PROFILES=core,ui COMPOSE_PROJECT_NAME=somaagent01_dev

dev-restart-ui:
	@echo "Rebuilding developer stack with UI profile..."
	$(MAKE) rebuild COMPOSE_FILE=$(DEV_COMPOSE_FILE) PROFILES=core,ui COMPOSE_PROJECT_NAME=somaagent01_dev

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
