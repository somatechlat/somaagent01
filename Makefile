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

build:
	@echo "Building Docker images..."
	# Expand comma-separated PROFILES into multiple --profile flags for docker compose
	docker compose -p $(COMPOSE_PROJECT_NAME) -f $(COMPOSE_FILE) $(foreach p,$(subst ,, ,$(PROFILES)),--profile $(p)) build

up:
	@echo "Starting the stack in detached mode..."
	# Expand comma-separated PROFILES into multiple --profile flags for docker compose
	docker compose -p $(COMPOSE_PROJECT_NAME) -f $(COMPOSE_FILE) $(foreach p,$(subst ,, ,$(PROFILES)),--profile $(p)) up -d

down:
	@echo "Stopping and removing the stack..."
	docker compose -p $(COMPOSE_PROJECT_NAME) -f $(COMPOSE_FILE) down

restart: down up

logs:
	@echo "Following logs for all services..."
	docker compose -p $(COMPOSE_PROJECT_NAME) -f $(COMPOSE_FILE) logs -f

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

DEV_COMPOSE_FILE := docker-compose.dev.yaml
DEV_PROFILES := core

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

.PHONY: debug-profiles
debug-profiles:
	@echo "PROFILES='$(PROFILES)'"
	@echo "DOCKER_PROFILES='$(DOCKER_PROFILES)'"
	@echo "Direct expansion: '$(foreach p,$(shell echo $(PROFILES) | tr ',' ' '),--profile $(p))'"
