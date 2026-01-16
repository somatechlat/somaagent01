# ═══════════════════════════════════════════════════════════════════════════════
# 🐳 SOMAAGENT01 STANDALONE DOCKERFILE
# ═══════════════════════════════════════════════════════════════════════════════
# Single-service container for Agent-only deployment (no Brain/Memory)
# ═══════════════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════════════
# STAGE 1: PYTHON BUILDER
# ═══════════════════════════════════════════════════════════════════════════════
FROM python:3.12-slim AS builder
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /build

# Install Build Tools
RUN pip install --upgrade pip setuptools wheel

# Copy Requirements
COPY requirements.txt /build/requirements.txt

# Install Dependencies (CPU-only PyTorch for smaller image)
RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir --default-timeout=100 --prefer-binary -r requirements.txt

# ═══════════════════════════════════════════════════════════════════════════════
# STAGE 2: RUNTIME
# ═══════════════════════════════════════════════════════════════════════════════
FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

WORKDIR /app

# System Dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    netcat-openbsd \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python Packages from Builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy Agent Source Code ONLY (no Brain/Memory)
COPY . /app

# Set PYTHONPATH for Django
ENV PYTHONPATH=/app:$PYTHONPATH
ENV DJANGO_SETTINGS_MODULE=services.gateway.settings

# Copy Startup Script
COPY infra/standalone/start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Create Non-Root User
RUN useradd --create-home --uid 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose Agent API Port
EXPOSE 9000

# Health Check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:9000/api/v1/health || exit 1

# Entrypoint
ENTRYPOINT ["/app/start.sh"]
