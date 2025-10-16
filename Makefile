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
	docker compose -p $(COMPOSE_PROJECT_NAME) -f $(COMPOSE_FILE) --profile $(PROFILES) build

up:
	@echo "Starting the stack in detached mode..."
	docker compose -p $(COMPOSE_PROJECT_NAME) -f $(COMPOSE_FILE) --profile $(PROFILES) up -d

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
