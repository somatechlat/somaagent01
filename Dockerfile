# Canonical multi-stage build that installs the complete Agent Zero runtime.

FROM python:3.11-slim AS builder

ARG INCLUDE_ML_DEPS=true

ENV PYTHONUNBUFFERED=1 \
        PYTHONDONTWRITEBYTECODE=1 \
        VENV_PATH="/opt/venv"

ENV PATH="$VENV_PATH/bin:$PATH"

RUN apt-get update && apt-get install -y --no-install-recommends \
                build-essential \
                curl \
                git \
        && rm -rf /var/lib/apt/lists/*

RUN python -m venv "$VENV_PATH" && \
        "$VENV_PATH/bin/pip" install --upgrade pip setuptools wheel

WORKDIR /opt/build
COPY requirements.txt requirements-ml.txt ./
RUN "$VENV_PATH/bin/pip" install --no-cache-dir -r requirements.txt

# Optionally install heavy ML/document-processing dependencies.
#   docker build --build-arg INCLUDE_ML_DEPS=false -t somaagent01:slim .
RUN if [ "${INCLUDE_ML_DEPS}" = "true" ]; then \
                echo "Installing ML/document-processing deps" && \
                "$VENV_PATH/bin/pip" install --no-cache-dir -r requirements-ml.txt; \
        else \
                echo "Skipping heavy ML deps (INCLUDE_ML_DEPS=${INCLUDE_ML_DEPS})"; \
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
