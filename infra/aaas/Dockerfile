FROM python:3.12-slim AS base

# =============================================================================
# SOMA AGENT-AS-A-SERVICE (AAAS) UNIFIED DOCKERFILE
# =============================================================================
# Builds a single container running Agent + Brain + Memory as ONE entity.
# SomaAgent01 is the MASTER orchestrator.
#
# Build: docker build -f infra/aaas/Dockerfile -t somastack:aaas .
# Run: docker run -p 9000:9000 somastack:aaas
# =============================================================================

LABEL maintainer="SOMA Team"
LABEL description="AAAS Unified Container - Agent + Brain + Memory"
LABEL version="2.0.0"

# Environment
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    SOMA_SINGLE_PROCESS=true \
    SOMA_AAAS_MODE=true \
    SA01_DEPLOYMENT_MODE=AAAS \
    DJANGO_SETTINGS_MODULE=infra.aaas.unified_settings

WORKDIR /app

# =============================================================================
# DEPENDENCIES
# =============================================================================

FROM base AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements from all three repos
COPY somaAgent01/requirements.txt /tmp/requirements-agent.txt
COPY somabrain/requirements.txt /tmp/requirements-brain.txt
COPY somafractalmemory/requirements.txt /tmp/requirements-memory.txt

# Merge and dedupe requirements
RUN cat /tmp/requirements-*.txt | sort | uniq > /tmp/requirements-all.txt

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r /tmp/requirements-all.txt

# =============================================================================
# PRODUCTION
# =============================================================================

FROM base AS production

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy all three repositories
COPY somaAgent01 /app/somaAgent01
COPY somabrain /app/somabrain
COPY somafractalmemory /app/somafractalmemory

# Set Python path for all repos
ENV PYTHONPATH="/app/somaAgent01:/app/somabrain:/app/somafractalmemory:/app"

# Create non-root user
RUN useradd --create-home --shell /bin/bash soma && \
    chown -R soma:soma /app
USER soma

# Copy and make startup script executable
COPY --chown=soma:soma somaAgent01/infra/aaas/start_unified.sh /app/start_unified.sh
RUN chmod +x /app/start_unified.sh

# Expose single port (all services on one port)
EXPOSE 9000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:9000/api/v2/health || exit 1

# Default entrypoint
WORKDIR /app/somaAgent01
ENTRYPOINT ["/app/start_unified.sh"]
