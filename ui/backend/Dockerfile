# Eye of God Django Backend Dockerfile
# Per Eye of God UIX Design Section 1.1
#
# VIBE COMPLIANT:
# - Production-grade multi-stage build
# - Non-root user for security
# - Health check included
# - Minimal attack surface

# =============================================================================
# Stage 1: Python Dependencies
# =============================================================================
FROM python:3.12-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# =============================================================================
# Stage 2: Production Image
# =============================================================================
FROM python:3.12-slim as production

# Security: Run as non-root
RUN groupadd -r somaagent && useradd -r -g somaagent somaagent

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY --chown=somaagent:somaagent . .

# Create necessary directories
RUN mkdir -p /app/staticfiles /app/logs && \
    chown -R somaagent:somaagent /app

# Switch to non-root user
USER somaagent

# Environment
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DJANGO_SETTINGS_MODULE=config.settings \
    PORT=8020

# Expose port
EXPOSE 8020

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8020/api/v2/health || exit 1

# Run with uvicorn for async support
CMD ["uvicorn", "config.asgi:application", "--host", "0.0.0.0", "--port", "8020", "--workers", "4"]
