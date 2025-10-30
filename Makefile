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

# Local development helpers
DEPS_PROJECT_NAME := somaagent01_deps
STACK_RUNNER := scripts/runstack.py

# Use this to export environment variables from a .env file if it exists
ifneq (,$(wildcard ./.env))
	include .env
	export
endif
# Central build configuration (single source of truth for Docker variables)
ifneq (,$(wildcard ./.build.env))
	include .build.env
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
	@echo "  dev-up                    Start minimal dev stack (docker-compose.yaml)."
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
	@echo "Dependency & local runtime targets:"
	@echo "  deps-up                   Start Kafka/Redis/Postgres/OPA (core profile only)."
	@echo "  deps-down                 Stop dependency containers."
	@echo "  deps-logs                 Tail dependency container logs."
	@echo "  stack-up                  Run gateway + workers locally (Ctrl+C to stop)."
	@echo "  stack-up-reload           Same as stack-up but with uvicorn --reload."
	@echo "  stack-down                Alias for stack-up (use Ctrl+C)."
	@echo "  ui                        Run Agent UI locally (Ctrl+C to stop)."
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

.PHONY: deps-up deps-down deps-logs stack-up stack-up-reload stack-down

deps-up:
	@echo "Starting shared dependencies (Kafka/Redis/Postgres/OPA)..."
	@docker network inspect somaagent01 >/dev/null 2>&1 || docker network create somaagent01
	$(MAKE) up COMPOSE_FILE=$(COMPOSE_FILE) PROFILES=core COMPOSE_PROJECT_NAME=$(DEPS_PROJECT_NAME)

deps-down:
	@echo "Stopping dependency containers..."
	$(MAKE) down COMPOSE_FILE=$(COMPOSE_FILE) COMPOSE_PROJECT_NAME=$(DEPS_PROJECT_NAME)

deps-logs:
	@echo "Tailing dependency container logs..."
	$(MAKE) logs COMPOSE_FILE=$(COMPOSE_FILE) PROFILES=core COMPOSE_PROJECT_NAME=$(DEPS_PROJECT_NAME)

stack-up:
	@echo "Starting local runtime stack (Ctrl+C to stop)..."
	python $(STACK_RUNNER)

stack-up-reload:
	@echo "Starting local runtime stack with uvicorn --reload (Ctrl+C to stop)..."
	python $(STACK_RUNNER) --reload

stack-down:
	@echo "Local stack runs in the foreground. Use Ctrl+C in the stack-up terminal to stop it."

.PHONY: ui

ui:
	@echo "Starting Agent UI locally on http://127.0.0.1:3000 (Ctrl+C to stop)..."
	@echo "UI is served from the Gateway at http://127.0.0.1:${GATEWAY_PORT:-21016}/ui"
	@echo "To run the full stack locally: make stack-up (or see README)."

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
# Load / Soak testing helpers (Wave C)
# ------------------------------------------------------------------------------

.PHONY: load-smoke load-soak

# Quick smoke: 5 RPS for 15s, concurrency 20
load-smoke:
	@echo "Running smoke load (5 RPS x 15s) against Gateway..."
	TARGET_URL?=http://127.0.0.1:8010 ; \
	RPS=5 DURATION=15 CONCURRENCY=20 \
	python scripts/load/soak_gateway.py

# Longer soak: override RPS/DURATION/CONCURRENCY via env
load-soak:
	@echo "Running configurable soak load against Gateway..."
	python scripts/load/soak_gateway.py
 

# ------------------------------------------------------------------------------
# Canonical Docker image build/push with branch+date+sha tag
# ------------------------------------------------------------------------------

# Default image repo; override via .build.env or environment
IMAGE_REPO ?= $(IMAGE_REPO)
# Build arg for ML deps; override via .build.env or environment
INCLUDE_ML_DEPS ?= false

# Compute tag components
BRANCH := $(shell git rev-parse --abbrev-ref HEAD | tr '/' '-')
DATE := $(shell date +%y%m%d)
SHA := $(shell git rev-parse --short HEAD)
TAG := $(BRANCH)-$(DATE)-$(SHA)

.PHONY: docker-image docker-push print-tag

print-tag:
	@echo "Image tag: $(TAG)"

docker-image:
	@echo "Building image $(IMAGE_REPO):$(TAG) (INCLUDE_ML_DEPS=$(INCLUDE_ML_DEPS))"
	docker build -f Dockerfile -t $(IMAGE_REPO):$(TAG) --build-arg INCLUDE_ML_DEPS=$(INCLUDE_ML_DEPS) .

docker-push:
	@if [ -z "$(IMAGE_REPO)" ]; then echo "IMAGE_REPO is required (set in .build.env or env)"; exit 1; fi
	@echo "Pushing image $(IMAGE_REPO):$(TAG)"
	docker push $(IMAGE_REPO):$(TAG)
