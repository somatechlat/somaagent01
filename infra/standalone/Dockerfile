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
# T-2 shared contract lives IN-PROJECT (Operator law: no out-of-project packages)
COPY services/common/soma-memory-contract /build/soma-memory-contract

# Install Dependencies (CPU-only PyTorch for smaller image)
RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir --default-timeout=100 --prefer-binary -r requirements.txt
RUN pip install --no-cache-dir /build/soma-memory-contract

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

# Copy Startup Script + bootstrap (Channel ENV / T0 tmpfs only)
COPY infra/standalone/start.sh /app/start.sh
COPY infra/standalone/bootstrap_exec.sh /work/bootstrap_exec.sh
COPY infra/standalone/vault_unseal.py /work/vault_unseal.py
COPY infra/standalone/init_vault.py /work/init_vault.py
COPY infra/standalone/vault_scoped_tokens.py /work/vault_scoped_tokens.py
COPY infra/standalone/vault-policies /work/vault-policies
RUN chmod +x /app/start.sh /work/bootstrap_exec.sh

# Create Non-Root User
RUN useradd --create-home --uid 1000 appuser && chown -R appuser:appuser /app /work

# Ceremonial seeder runs as root (process RAM only for root); bootstrap_exec
# drops to appuser before execve of the app (SOMA-STD-SECURITY-001 §1.2).
USER root

# Expose Agent API Port
EXPOSE 9000

# Health Check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:9000/api/health/ || exit 1

# Entrypoint: ceremony (unseal/seed/mint into THIS container's private T0) then app
ENTRYPOINT ["/work/bootstrap_exec.sh", "/app/start.sh"]
