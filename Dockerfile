# Optimized multi-stage build for SomaAgent01 runtime

FROM python:3.11-slim AS builder

ARG INCLUDE_ML_DEPS=false

ENV PYTHONUNBUFFERED=1 \
        PYTHONDONTWRITEBYTECODE=1 \
        VENV_PATH="/opt/venv"

ENV PATH="$VENV_PATH/bin:$PATH"

# Install only essential build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
                build-essential \
                curl \
                git \
        && rm -rf /var/lib/apt/lists/*

RUN python -m venv "$VENV_PATH" && \
        "$VENV_PATH/bin/pip" install --upgrade pip setuptools wheel

WORKDIR /opt/build

# Copy only essential dependency files
COPY requirements.txt requirements-dev.txt requirements-ml.txt ./

# Install core dependencies for development (no ML deps by default)
RUN if [ "${INCLUDE_ML_DEPS}" = "true" ]; then \
                echo "Installing full dependencies with ML/document-processing deps" && \
                "$VENV_PATH/bin/pip" install --no-cache-dir -r requirements.txt && \
                "$VENV_PATH/bin/pip" install --no-cache-dir -r requirements-ml.txt; \
        else \
                echo "Installing essential dev dependencies (INCLUDE_ML_DEPS=${INCLUDE_ML_DEPS})" && \
                "$VENV_PATH/bin/pip" install --no-cache-dir -r requirements-dev.txt; \
        fi


FROM python:3.11-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
        PYTHONDONTWRITEBYTECODE=1 \
        VENV_PATH="/opt/venv"

ENV PATH="$VENV_PATH/bin:$PATH" \
        PYTHONPATH=/app

RUN apt-get update && apt-get install -y --no-install-recommends \
                curl \
                git \
                libpq-dev \
                libssl-dev \
                libffi-dev \
                libsasl2-dev \
                libxml2-dev \
                libxslt1-dev \
                zlib1g-dev \
                libsndfile1 \
                tesseract-ocr \
                poppler-utils \
                ffmpeg \
        && rm -rf /var/lib/apt/lists/*

COPY --from=builder "$VENV_PATH" "$VENV_PATH"

WORKDIR /app
COPY . /app

RUN useradd -m -u 1000 agent && \
        chown -R agent:agent /app

USER agent

# Health check endpoint defined in services.gateway.main
# Standardize to use port 8010 (matches docker-compose service mapping)
# NOTE: Gateway exposes /v1/health (not /health)
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
        CMD curl -f http://localhost:8010/v1/health || exit 1

EXPOSE 8010

# Default command runs preflight then the gateway on port 8010.
CMD ["bash", "-lc", "scripts/entrypoints/gateway.sh"]
