PROJECT ?= somaagent01
COMPOSE_FILE ?= infra/docker-compose.somaagent01.yaml
TAKEDOWN_SCRIPT ?= ./scripts/takedown.sh

.PHONY: takedown takedown-dry compose-down compose-down-dry remove-volumes clean-all up ps

# Stop and remove compose-managed containers and orphans (wraps the script)
takedown:
	$(TAKEDOWN_SCRIPT)

takedown-dry:
	$(TAKEDOWN_SCRIPT) --dry

# Direct docker compose down (core+dev profiles)
compose-down:
	COMPOSE_PROFILES=core,dev docker compose -f $(COMPOSE_FILE) --project-name $(PROJECT) down --volumes --remove-orphans

compose-down-dry:
	@echo "DRY: would run: COMPOSE_PROFILES=core,dev docker compose -f $(COMPOSE_FILE) --project-name $(PROJECT) down --volumes --remove-orphans"

# Remove named volumes used by the project (postgres/kafka/redis)
remove-volumes:
	@for v in postgres_data kafka_data redis_data; do \
		full="$${PROJECT}_$${v}"; \
		if docker volume ls --format '{{.Name}}' | grep -q "^$${full}$$"; then \
			echo "Removing volume: $${full}"; \
			docker volume rm "$${full}" || true; \
		else \
			echo "volume $${full} not found"; \
		fi; \
	done

clean-all: takedown remove-volumes

# Convenience: bring the stack up (core+dev)
up:
	COMPOSE_PROFILES=core,dev docker compose -f $(COMPOSE_FILE) --project-name $(PROJECT) up -d

ps:
	docker ps --filter "name=$(PROJECT)_" --format "table {{.ID}}\t{{.Names}}\t{{.Status}}"
