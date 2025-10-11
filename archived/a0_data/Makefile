# ------------------------------------------------------------
# Soma Coder Agent Copilot – Canonical Makefile
# ------------------------------------------------------------
# Variables (override via command line or environment)
PYTHON ?= python3
PIP ?= pip3
VENV ?= .venv
REQS ?= requirements.txt

# ----------------------------------------------------------------
# Helper to activate virtual environment
define activate_venv
. $(VENV)/bin/activate
endef

# ----------------------------------------------------------------
# Primary targets (all are idempotent)
.PHONY: all init venv install deps lint format test doc clean build deploy setup ci help

all: init lint format test doc   ## Run the full local CI suite

# ----------------------------------------------------------------
# Create a clean virtual environment
init:
@echo "Creating virtual environment…"
$(PYTHON) -m venv $(VENV)
@$(call activate_venv)
$(PIP) install --upgrade pip setuptools wheel

# Install runtime & dev dependencies
install: venv
@$(call activate_venv)
$(PIP) install -r $(REQS)

# Alias for CI pipelines
deps: install

# Linting (flake8 + mypy)
lint:
@$(call activate_venv)
flake8 .
mypy .

# Code formatting (black + isort)
format:
@$(call activate_venv)
black .
isort .

# Unit / integration tests (pytest)
# Use PYTEST_ARGS to pass extra flags, e.g. make test PYTEST_ARGS="-k test_api"

test:
@$(call activate_venv)
pytest $(PYTEST_ARGS)

# Documentation generation (mkdocs)
# Repo ships with mkdocs.yml – adjust if you prefer Sphinx.

doc:
@$(call activate_venv)
mkdocs build

# Clean all generated artefacts
clean:
rm -rf $(VENV) .pytest_cache .mypy_cache .coverage htmlcov site

# Build a Docker image (optional)
# IMAGE_NAME can be overridden, default = soma-coder-agent
build:
docker build -t $(IMAGE_NAME):latest .

# Deploy to a Kubernetes cluster (helm chart assumed)
# Values can be overridden via HELM_VALUES env var.

deploy:
helm upgrade --install soma-coder-agent ./helm/soma-coder-agent \
--set image.tag=latest \
$(if $(HELM_VALUES),--values $(HELM_VALUES),)

# ----------------------------------------------------------------
# Convenience shortcuts
setup: init install deps   ## Fresh developer environment
ci: lint test doc          ## Run the CI suite locally

# Help target (optional)
help:
@grep -E '^[a-zA-Z_-]+:.*?##' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?##"} {printf "%-20s %s\n", $$1, $$2}'

# End of Makefile
