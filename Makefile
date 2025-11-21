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

# When non-empty and set to 1, pre-up cleanup will force-remove any existing
# containers matching the compose project. Set to 0 to require manual cleanup
# (safer for shared/docker-host environments). Default 1 preserves prior
# behaviour to keep dev bring-ups reliable.
FORCE_CLEAN ?= 1

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

.PHONY: help build up down restart logs rebuild clean ensure-env ensure-networks

help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  help      Show this help message."
	@echo "  build     Build or rebuild the Docker images for the stack."
	@echo "  up        Create and start the containers in detached mode (ensures .env and networks)."
	@echo "  down      Stop and remove the containers (use REMOVE_VOLUMES=1 to also remove volumes)."
	@echo "  restart   Restart all services."
	@echo "  logs      Follow the logs of all services."
	@echo "  rebuild   Stop, rebuild, and restart the entire stack."
	@echo "  clean     Remove all build artifacts and Docker volumes."
	@echo ""
	@echo "Standardized stack aliases (production-friendly names):"
	@echo "  stack-start     Alias for 'up'"
	@echo "  stack-stop      Alias for 'down'"
	@echo "  stack-restart   Alias for 'restart'"
	@echo "  stack-logs      Alias for 'logs'"
	@echo ""
	@echo "Developer (lightweight) targets:"
	@echo "  dev-up                    Start minimal dev stack (docker-compose.yaml)."
	@echo "  dev-down                  Stop minimal dev stack."
	@echo "  dev-logs                  Tail logs for minimal dev stack."
	@echo "  dev-rebuild               Rebuild and restart minimal dev stack."
	@echo "  dev-down-hard             Stop dev stack and remove named volumes."
	@echo "  dev-down-clean            Stop dev stack, remove volumes, and remove dev network."

	@echo ""
	@echo "Standardized dev aliases:"
	@echo "  dev-start                 Alias for 'dev-up'"
	@echo "  dev-stop                  Alias for 'dev-down'"
	@echo "  dev-restart               Alias for 'dev-rebuild'"
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
	@echo "Quick operations:"
	@echo "  health                    Curl Gateway /v1/health"
	@echo "  ui-smoke                  Run UI smoke test"
	@echo "  test-e2e                  Run E2E pytest suite (tests/e2e)"
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
	$(MAKE) ensure-env
	$(MAKE) ensure-networks
	# Pre-up cleanup: detect any existing containers for this project and
	# either remove them automatically (default) or require manual removal
	# depending on `FORCE_CLEAN`.
	@echo "Checking for existing project-prefixed containers for $(COMPOSE_PROJECT_NAME)..."
	@# First try to find containers by the compose project label (reliable)
	@existing_ids=$$(docker ps -a --filter "label=com.docker.compose.project=$(COMPOSE_PROJECT_NAME)" -q 2>/dev/null || true); \
	# If none found via label, fallback to a case-insensitive name match (handles prior/mixed-case names)
	@if [ -z "$$existing_ids" ]; then \
		existing_ids=$$(docker ps -a --format '{{.ID}} {{.Names}}' 2>/dev/null | grep -i "$(COMPOSE_PROJECT_NAME)_" | awk '{print $$1}' || true;); \
	fi; \
	if [ -n "$$existing_ids" ]; then \
		echo "Found existing containers: $$existing_ids"; \
		if [ "$(FORCE_CLEAN)" = "1" ]; then \
			echo "FORCE_CLEAN=1: stopping and removing them to avoid name conflicts..."; \
			docker rm -f $$existing_ids >/dev/null 2>&1 || true; \
		else \
			echo "Found existing containers would block compose up."; \
			echo "Run 'make up FORCE_CLEAN=1' to allow automatic cleanup, or remove containers manually."; \
			exit 1; \
		fi; \
	else \
		echo "No existing project-prefixed containers found."; \
	fi
	# Start the compose stack
	docker compose -p $(COMPOSE_PROJECT_NAME) -f $(COMPOSE_FILE) $(DOCKER_PROFILES) up -d

down:
	@echo "Stopping and removing the stack..."
	# Use REMOVE_VOLUMES=1 to also remove named volumes; always remove orphans
	docker compose -p $(COMPOSE_PROJECT_NAME) -f $(COMPOSE_FILE) down $(if $(REMOVE_VOLUMES),-v,) --remove-orphans

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

# ---------------------------------------------------------------------------
# Testing helpers
# ---------------------------------------------------------------------------
# Run the pytest suite in the background while you continue development.
# The helper script ``run_tests_background.sh`` activates the virtual environment
# and starts ``pytest -q`` in a detached process, logging to ``pytest_background.log``.
# Use ``make test-bg`` to invoke it.
.PHONY: test-bg
test-bg:
	@chmod +x ./run_tests_background.sh
	@./run_tests_background.sh

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
	@# Optional pre-up pruning to avoid container_name conflicts from stale runs
	@# Set PRUNE_BEFORE_UP=0 to skip. Defaults to 1 for reliability.
	@PRUNE_BEFORE_UP=${PRUNE_BEFORE_UP:-1}; \
	if [ "$$PRUNE_BEFORE_UP" = "1" ]; then \
		$(MAKE) prune-soma >/dev/null 2>&1 || true; \
	fi
	$(MAKE) up COMPOSE_FILE=$(DEV_COMPOSE_FILE) PROFILES=$(DEV_PROFILES) COMPOSE_PROJECT_NAME=somaagent01_dev
	$(MAKE) health-wait

dev-down:
	@echo "Stopping lightweight developer stack..."
	$(MAKE) down COMPOSE_FILE=$(DEV_COMPOSE_FILE) COMPOSE_PROJECT_NAME=somaagent01_dev REMOVE_VOLUMES=$(DEV_REMOVE_VOLUMES)
	@# Fallback: in some Docker Compose versions, containers with explicit container_name or external networks
	@# might not be removed by `compose down` reliably. Ensure the dev project containers are gone.
	@echo "Ensuring all dev containers are removed (fallback)..."
	@ids=$$(docker ps -aq --filter "label=com.docker.compose.project=somaagent01_dev"); \
	if [ -n "$$ids" ]; then \
	  echo "Forcibly removing containers: $$ids"; \
	  docker rm -f $$ids >/dev/null 2>&1 || true; \
	else \
	  echo "No leftover dev containers found."; \
	fi
	@# Additional fallback: if the stack was started without the dev project name, also clear default project containers
	@echo "Checking for default project containers (somaagent01) ...";
	@ids=$$(docker ps -aq --filter "label=com.docker.compose.project=somaagent01"); \
	if [ -n "$$ids" ]; then \
	  echo "Removing default project containers (somaagent01): $$ids"; \
	  docker rm -f $$ids >/dev/null 2>&1 || true; \
	fi
	@if [ "$(DEV_REMOVE_NETWORK)" = "1" ]; then \
	  echo "Removing dev network 'somaagent01_dev'..."; \
	  docker network rm somaagent01_dev >/dev/null 2>&1 || true; \
	  echo "Removing any orphan dev networks matching 'somaagent01_dev*'..."; \
	  for net in $$(docker network ls --format '{{.Name}}' | grep -E '^somaagent01_dev($|_)' || true); do \
	    docker network rm $$net >/dev/null 2>&1 || true; \
	  done; \
	fi

dev-logs:
	@echo "Tailing logs for lightweight developer stack..."
	$(MAKE) logs COMPOSE_FILE=$(DEV_COMPOSE_FILE) PROFILES=$(DEV_PROFILES) COMPOSE_PROJECT_NAME=somaagent01_dev

dev-rebuild:
	@echo "Rebuilding lightweight developer stack..."
	$(MAKE) rebuild COMPOSE_FILE=$(DEV_COMPOSE_FILE) PROFILES=$(DEV_PROFILES) COMPOSE_PROJECT_NAME=somaagent01_dev

.PHONY: dev-down-hard
# Forceful dev down: remove containers, orphans, and named volumes for the dev project
dev-down-hard:
	@echo "Forcefully stopping developer stack and removing volumes..."
	$(MAKE) dev-down DEV_REMOVE_VOLUMES=1

.PHONY: dev-down-clean
# Fully clean dev stack: containers, volumes, and the shared network to ensure fresh restarts
dev-down-clean:
	@echo "Fully cleaning developer stack (containers, volumes, network)..."
	$(MAKE) dev-down DEV_REMOVE_VOLUMES=1 DEV_REMOVE_NETWORK=1


.PHONY: prune-soma
# Remove any leftover containers using fixed container_name "somaAgent01_*" to avoid name conflicts
prune-soma:
	@echo "Pruning leftover somaAgent01_* containers (if any) ..."
	@ids=$$(docker ps -aq --filter "name=^somaAgent01_" 2>/dev/null || true); \
	if [ -n "$$ids" ]; then \
		echo "Removing: $$ids"; \
		docker rm -f $$ids >/dev/null 2>&1 || true; \
	else \
		echo "No leftover somaAgent01_* containers"; \
	fi



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
	@docker network inspect somaagent01_dev >/dev/null 2>&1 || docker network create somaagent01_dev
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

## Helm targets removed: keep repository Makefile focused on local dev & docker compose.
## If you need Helm integration, use the scripts in `scripts/` directly or re-add
## these targets. Removal keeps the Makefile concise for a typical developer workflow.
# ------------------------------------------------------------------------------
# Load / Soak testing helpers (Wave C)
# ------------------------------------------------------------------------------


.PHONY: load-smoke

# Quick smoke: 5 RPS for 15s, concurrency 20
load-smoke:
	@echo "Running smoke load (5 RPS x 15s) against Gateway..."
	TARGET_URL?=http://127.0.0.1:8010 ; \
	RPS=5 DURATION=15 CONCURRENCY=20 \
	python scripts/load/soak_gateway.py

# Note: the longer soak target was removed to keep the Makefile focused on
# common developer workflows. Use `scripts/load/soak_gateway.py` directly for
# more advanced soak tests.
 

# ------------------------------------------------------------------------------
# Canonical Docker image build/push with branch+date+sha tag
# ------------------------------------------------------------------------------

# Default image repo; override via .build.env or environment
# Leave blank by default to avoid recursive reference; set in .build.env or env
IMAGE_REPO ?=
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

# Ensure required local files and networks exist for compose
ensure-env:
	@# Create a minimal .env so docker compose env_file resolves; provider secrets come from the UI
	@[ -f ./.env ] || (echo "# Local development .env (minimal)" > ./.env && echo "Created .env for docker-compose env_file")

ensure-networks:
	@docker network inspect somaagent01 >/dev/null 2>&1 || docker network create somaagent01
	@docker network inspect somaagent01_dev >/dev/null 2>&1 || docker network create somaagent01_dev

# -------------------------------------------------------------
# Standardized alias targets (production-friendly naming)
# -------------------------------------------------------------
.PHONY: stack-start stack-stop stack-restart stack-logs

stack-start:
	$(MAKE) up

stack-stop:
	$(MAKE) down

stack-restart:
	$(MAKE) restart

stack-logs:
	$(MAKE) logs

.PHONY: dev-start dev-stop dev-restart

dev-start:
	$(MAKE) dev-up

dev-stop:
	$(MAKE) dev-down

dev-restart:
	$(MAKE) dev-rebuild



# -------------------------------------------------------------
# Quick operations
# -------------------------------------------------------------
.PHONY: health ui-smoke test-e2e

health:
	@echo "Checking Gateway health at http://127.0.0.1:$${GATEWAY_PORT:-21016}/v1/health ..."
	@curl -fsS -D - http://127.0.0.1:$${GATEWAY_PORT:-21016}/v1/health -o /dev/null

.PHONY: health-wait
# Wait until the Gateway health endpoint responds (with retries)
health-wait:
	@GATEWAY_PORT=$${GATEWAY_PORT:-21016}; \
	echo "Waiting for Gateway at http://127.0.0.1:$$GATEWAY_PORT/v1/health ..."; \
	retries=40; \
	until curl -fsS "http://127.0.0.1:$$GATEWAY_PORT/v1/health" -o /dev/null; do \
		retries=$$((retries-1)); \
		if [ $$retries -le 0 ]; then echo "Gateway health check failed"; exit 1; fi; \
		sleep 2; \
	done; \
	echo "Gateway is healthy"

ui-smoke:
	@echo "Running UI smoke ..."
	@WEB_UI_BASE_URL=$${WEB_UI_BASE_URL:-http://localhost:$${GATEWAY_PORT:-21016}/ui} ./scripts/ui-smoke.sh

test-e2e:
	@echo "Running E2E tests ..."
	@[ -x ./.venv/bin/python ] && ./.venv/bin/python -m pytest -q tests/e2e || pytest -q tests/e2e

.PHONY: preflight
preflight:
	@echo "Running runtime preflight (canonical env + OPA reachability) ..."
	python scripts/preflight.py

.PHONY: test-live deps-up-live

# Start dependencies + core stack, then run the entire test suite against real services
deps-up-live:
	@echo "Bringing up core dependencies for live testing (Kafka/Redis/Postgres/OPA)..."
	$(MAKE) deps-up
	@echo "Bringing up application stack (Gateway + workers) ..."
	$(MAKE) up PROFILES=core,dev
	@echo "Waiting for Gateway health ..."
	$(MAKE) health-wait

test-live:
	@echo "Running full test suite against live stack (no mocks) ..."
	$(MAKE) deps-up-live
	PYTHONDONTWRITEBYTECODE=1 pytest -vv
	@echo "All tests completed"

.PHONY: test-live-only
# Run tests against an already running live stack (skips bring-up)
test-live-only:
	@echo "Running tests against existing live stack (skipping bring-up) ..."
	$(MAKE) health-wait
	PYTHONDONTWRITEBYTECODE=1 pytest -vv

 
# ==============================================================================
# Code Quality - Single Entry Point (VIBE)
# ==============================================================================

.PHONY: quality format lint typecheck test

quality: format lint typecheck test
	@echo "✅ All quality checks passed"

format:
	@echo "Formatting code..."
	black .
	ruff check --fix .

lint:
	@echo "Linting code..."
	ruff check .

typecheck:
	@echo "Type checking..."
	mypy services/ python/ --ignore-missing-imports

test:
	@echo "Running tests..."
	pytest --cov=services --cov=python --cov-report=term-missing

.PHONY: smoke-orchestrator
smoke-orchestrator:
	@echo "Running orchestrator dry-run smoke..."
	python -m orchestrator.main --dry-run
	python - <<'PY'\nfrom fastapi.testclient import TestClient\nfrom orchestrator.main import app\nclient = TestClient(app)\nresp = client.get(\"/v1/health\")\nprint(resp.status_code, resp.json())\nassert resp.status_code == 200 and resp.json().get(\"healthy\") is True\nPY
