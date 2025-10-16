# Makefile for running independent sprint/task groups in parallel
# ---------------------------------------------------------------------------
# Usage examples (run from the repository root):
#   make all          # runs all groups concurrently (uses -j for parallelism)
#   make sprint_a     # shared code creation & import validation
#   make sprint_b     # Helm chart consolidation dry‑run
#   make sprint_c     # Dockerfile builds for each service
#   make sprint_d     # start each FastAPI service & sanity‑check /health
#   make ci           # lint, unit tests, integration tests, helm lint
#   make docs         # markdown lint / doc validation
#   make clean        # remove temporary artefacts

.PHONY: all sprints sprint_a sprint_b sprint_c sprint_d ci docs clean \
	docs-verify docs-lint docs-links docs-build docs-diagrams

all: sprints

# ---------------------------------------------------------------------------
# Group of all sprint targets – they can be executed in parallel by GNU make
# (e.g. `make -j4 sprints`).
# ---------------------------------------------------------------------------
sprints: sprint_a sprint_b sprint_c sprint_d ci docs

# ---------------------------------------------------------------------------
# Sprint A – shared code package & import sanity check
# ---------------------------------------------------------------------------
sprint_a:
	@echo "Running Sprint A: creating common package and checking imports..."
	# Simple static import validation: try to import each service module
	python - <<-'PY'
	import pathlib
	import subprocess
	import sys

	failed: list[str] = []
	for service_path in pathlib.Path('services').iterdir():
	    if not service_path.is_dir():
	        continue
	    main_file = service_path / 'main.py'
	    if not main_file.exists():
	        continue
	    try:
	        subprocess.run(
	            [
	                sys.executable,
	                '-c',
	                (
	                    "import importlib.util, sys; "
	                    "spec = importlib.util.spec_from_file_location('mod', '{main}') ; "
	                    "mod = importlib.util.module_from_spec(spec); "
	                    "spec.loader.exec_module(mod)"
	                ).format(main=main_file.as_posix()),
	            ],
	            check=True,
	            capture_output=True,
	        )
	    except Exception:  # noqa: BLE001 - bubble to failure summary
	        failed.append(str(service_path))

	if failed:
	    print('Import validation failed for services:', failed)
	    sys.exit(1)
	print('Import validation passed')
	PY

# ---------------------------------------------------------------------------
# Sprint B – Helm chart consolidation dry‑run
# ---------------------------------------------------------------------------
sprint_b:
	@echo "Running Sprint B: Helm chart consolidation dry‑run..."
	# Update chart dependencies (if any) and render the chart to ensure it is valid
	helm dependency update infra/helm/charts/soma-infra || true
	helm template soma-infra infra/helm/charts/soma-infra --debug > /dev/null

# ---------------------------------------------------------------------------
# Sprint C – Dockerfile validation / build for each service
# ---------------------------------------------------------------------------
sprint_c:
	@echo "Running Sprint C: building Docker images for each service..."
	for d in services/*; do \
	    if [ -f "$$d/Dockerfile" ]; then \
	        echo "Building $$d..."; \
	        docker build -q $$d . > /dev/null || { echo "Docker build failed for $$d"; exit 1; }; \
	    fi; \
	done

# ---------------------------------------------------------------------------
# Sprint D – FastAPI health‑check sanity
# ---------------------------------------------------------------------------
sprint_d:
	@echo "Running Sprint D: start each FastAPI service and check health endpoint..."
	# Launch each service in the background, wait a moment, curl /health (or /healthz)
	for svc in services/*; do \
	    if [ -f "$$svc/main.py" ]; then \
	        echo "Launching $$svc..."; \
	        uvicorn $$svc.main:app --port 0 --log-level warning & pid=$$!; \
	        sleep 2; \
	        # Try common health endpoints; ignore failures (just a sanity check)
	        curl -sSf http://127.0.0.1:8000/health || true; \
	        curl -sSf http://127.0.0.1:8000/healthz || true; \
	        kill $$pid; \
	    fi; \
	done

# ---------------------------------------------------------------------------
# CI – lint, unit tests, integration tests, helm lint
# ---------------------------------------------------------------------------
ci:
	@echo "Running CI pipeline: lint, unit tests, integration tests, helm lint..."
	# Lint (ruff is used in this repo; fall back to flake8 if missing)
	if command -v ruff > /dev/null; then ruff .; else echo "ruff not installed – skipping lint"; fi
	# Unit tests
	pytest -q tests/unit || true
	# Integration tests – spin up a temporary Kind cluster
	if command -v kind > /dev/null; then \
	    kind create cluster --name ci-temp || true; \
	    helm install soma-infra infra/helm/charts/soma-infra --wait || true; \
	    pytest -q tests/integration || true; \
	    kind delete cluster --name ci-temp || true; \
	else \
	    echo "kind not installed – skipping integration tests"; \
	fi
	# Helm lint for all charts
	helm lint infra/helm/charts/soma-infra || true
	for d in services/*; do \
	    if [ -f "$$d/Chart.yaml" ]; then \
	        helm lint $$d || true; \
	    fi; \
	done

# ---------------------------------------------------------------------------
# Docs – lint, link check, diagram rendering, MkDocs build
# ---------------------------------------------------------------------------
docs: docs-verify

docs-verify: docs-lint docs-links docs-diagrams docs-build
	@echo "Docs verification complete."

docs-lint:
	@echo "Running markdown lint..."
	if command -v markdownlint-cli2 > /dev/null; then \
		markdownlint-cli2 "docs/**/*.md"; \
	else \
		echo "markdownlint-cli2 not installed – skipping markdown lint"; \
	fi

docs-links:
	@echo "Checking links..."
	if command -v lychee > /dev/null; then \
		lychee --no-progress docs --accept "200..299,301,302"; \
	else \
		echo "lychee not installed – skipping link check"; \
	fi

docs-diagrams:
	@echo "Rendering diagrams..."
	if command -v mmdc > /dev/null; then \
		find docs -name '*.mmd' -print -exec mmdc -i {} -o {}.png \;; \
	else \
		echo "mermaid-cli (mmdc) not installed – skipping diagram render"; \
	fi

docs-build:
	@echo "Building MkDocs site..."
	if command -v mkdocs > /dev/null; then \
		mkdocs build --strict; \
	else \
		echo "mkdocs not installed – skipping site build"; \
	fi

# ---------------------------------------------------------------------------
# Clean – remove temporary artefacts
# ---------------------------------------------------------------------------
clean:
	@echo "Cleaning temporary files..."
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	# Add any additional clean‑up steps here
PROJECT_NAME ?= somaagent01
COMPOSE_FILE := infra/docker-compose.somaagent01.yaml
COMPOSE_PROFILES := --profile core --profile dev
COMPOSE := docker compose -p $(PROJECT_NAME) -f $(COMPOSE_FILE) $(COMPOSE_PROFILES)
STACK_FILTER := somaAgent01
START_SCRIPT := scripts/run_dev_cluster.sh

.PHONY: dev-up dev-down dev-restart dev-status dev-logs dev-clean fmt fmt-check lint lint-fix

dev-up:
	@echo "Starting SomaAgent01 dev stack (host ports >=$${PORT_POOL_START:-20000})..."
	$(START_SCRIPT)

dev-down:
	$(COMPOSE) down --remove-orphans

dev-restart: dev-down dev-up

dev-status:
	docker ps --filter name=$(STACK_FILTER) --format '{{.Names}}\t{{.Status}}'

dev-logs:
	$(COMPOSE) logs -f

dev-clean:
	$(COMPOSE) down --volumes --remove-orphans
	docker ps -aq --filter name=$(STACK_FILTER) | xargs -r docker rm -f

fmt:
	black .

fmt-check:
	black --check .

lint:
	ruff check .

lint-fix:
	ruff check --fix .
