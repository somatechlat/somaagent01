# ============================================================================
# SomaAgent01 Multi-Stage Docker Build
# ============================================================================
#
# This Dockerfile creates the somaagent-gateway image used by ALL core services:
#   - somaagent-gateway
#   - somaagent-conversation-worker  
#   - somaagent-tool-executor
#   - somaagent-memory-replicator
#
# BUILD STAGES:
#   1. Builder: Compiles dependencies in virtual environment
#   2. Runtime: Copies venv + application code, creates non-root user
#
# CRITICAL: By default, this uses requirements-dev.txt (lightweight)
#          Set INCLUDE_ML_DEPS=true for full ML dependencies
#
# BUILD COMMANDS:
#   Development:  docker build -t somaagent-gateway:latest .
#   Production:   docker build --build-arg INCLUDE_ML_DEPS=true -t somaagent-gateway:latest .
#
# ============================================================================

# ============================================================================
# STAGE 1: Builder - Compile Dependencies
# ============================================================================
FROM python:3.11-slim AS builder

# Build arguments for ML dependencies toggle
ARG INCLUDE_ML_DEPS="false"
ARG TORCH_VERSION="2.3.1"
ARG TORCH_VARIANT="cpu"

# Environment variables for build optimization
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    VENV_PATH="/opt/venv"

# Install build dependencies
# gcc, build-essential: Required for compiling Python packages with C extensions
# curl: For health checks and downloading files
# git: For installing packages from git repositories
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create Python virtual environment
# All dependencies will be installed here, then copied to runtime stage
RUN python -m venv "${VENV_PATH}" && \
    "${VENV_PATH}/bin/pip" install --upgrade pip setuptools wheel

# Set working directory for dependency installation
WORKDIR /opt/build

# ============================================================================
# DEPENDENCY INSTALLATION
# ============================================================================
# CRITICAL: Copy ALL requirements files to ensure correct dependency resolution
#
# Files copied:
#   - requirements.txt:          Core production dependencies
#   - requirements-dev.txt:      Lightweight dev dependencies (DEFAULT)
#   - requirements-ml.txt:       Heavy ML/document processing
#   - constraints-ml.txt:        Version constraints for ML packages
#
# ⚠️ IMPORTANT: When adding a NEW dependency:
#    1. If it's a RUNTIME dependency → Add to BOTH requirements-dev.txt AND requirements.txt
#    2. If it's DEV-ONLY (linter/test) → Add ONLY to requirements-dev.txt
#
COPY requirements.txt requirements-dev.txt requirements-ml.txt constraints-ml.txt ./

# ============================================================================
# Install Python dependencies based on build mode
# ============================================================================
#
# TWO BUILD MODES:
#
# 1. DEVELOPMENT MODE (default, INCLUDE_ML_DEPS=false):
#    - Uses: requirements-dev.txt ONLY
#    - Fast build (~10-15 min)
#    - Lightweight dependencies for rapid development
#    - Command: docker build -t somaagent-gateway:latest .
#
# 2. PRODUCTION/ML MODE (INCLUDE_ML_DEPS=true):
#    - Uses: requirements.txt + requirements-ml.txt
#    - Slow build (~30-40 min)
#    - Full ML stack (PyTorch, transformers, document processing)
#    - Command: docker build --build-arg INCLUDE_ML_DEPS=true -t somaagent-gateway:latest .
#
RUN if [ "${INCLUDE_ML_DEPS}" = "true" ]; then \
    # ============================================================
    # PRODUCTION/ML BUILD PATH
    # ============================================================
    echo "🔧 Installing FULL dependencies with ML/document-processing" && \
    # Determine PyTorch index URL based on variant (cpu/cuda)
    if [ "${TORCH_VARIANT}" = "cpu" ]; then \
    TORCH_INDEX="https://download.pytorch.org/whl/cpu"; \
    TORCH_SPEC="torch==${TORCH_VERSION}"; \
    CONSTRAINT_OPT="--constraint constraints-ml.txt"; \
    else \
    TORCH_INDEX="https://download.pytorch.org/whl/${TORCH_VARIANT}"; \
    TORCH_SPEC="torch==${TORCH_VERSION}+${TORCH_VARIANT}"; \
    CONSTRAINT_OPT=""; \
    fi; \
    PIP_COMMON="--no-cache-dir --index-url https://pypi.org/simple --extra-index-url ${TORCH_INDEX}"; \
    # Install PyTorch first (large dependency)
    "${VENV_PATH}/bin/pip" install ${PIP_COMMON} ${TORCH_SPEC} && \
    # Install core production dependencies
    "${VENV_PATH}/bin/pip" install ${PIP_COMMON} -r requirements.txt ${CONSTRAINT_OPT} && \
    # Install ML-specific dependencies
    "${VENV_PATH}/bin/pip" install ${PIP_COMMON} -r requirements-ml.txt ${CONSTRAINT_OPT}; \
    else \
    # ============================================================
    # DEVELOPMENT BUILD PATH (DEFAULT)
    # ============================================================
    echo "🚀 Installing LIGHTWEIGHT dev dependencies (INCLUDE_ML_DEPS=false)" && \
    # Determine PyTorch index URL (still install PyTorch CPU for basic usage)
    if [ "${TORCH_VARIANT}" = "cpu" ]; then \
    TORCH_INDEX="https://download.pytorch.org/whl/cpu"; \
    TORCH_SPEC="torch==${TORCH_VERSION}"; \
    CONSTRAINT_OPT="--constraint constraints-ml.txt"; \
    else \
    TORCH_INDEX="https://download.pytorch.org/whl/${TORCH_VARIANT}"; \
    TORCH_SPEC="torch==${TORCH_VERSION}+${TORCH_VARIANT}"; \
    CONSTRAINT_OPT=""; \
    fi; \
    PIP_COMMON="--no-cache-dir --index-url https://pypi.org/simple --extra-index-url ${TORCH_INDEX}"; \
    # Install basic PyTorch CPU
    "${VENV_PATH}/bin/pip" install ${PIP_COMMON} ${TORCH_SPEC} && \
    # ⚠️ CRITICAL: Install from requirements-dev.txt (NOT requirements.txt!)
    # This is the DEFAULT path for development builds
    "${VENV_PATH}/bin/pip" install ${PIP_COMMON} -r requirements-dev.txt ${CONSTRAINT_OPT}; \
    fi


# ============================================================================
# STAGE 2: Runtime - Minimal Production Image
# ============================================================================
FROM python:3.11-slim AS runtime

# Runtime environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    VENV_PATH="/opt/venv"

# Configure PATH to use virtual environment
ENV PATH="${VENV_PATH}/bin:$PATH" \
    PYTHONPATH=/app

# Install runtime system dependencies
# These are ONLY the libraries needed to RUN the application, not build it
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

# Copy compiled virtual environment from builder stage
# This contains ALL Python dependencies installed in Stage 1
COPY --from=builder /opt/venv /opt/venv

# Set application working directory
WORKDIR /app

# Copy application code
# This includes all Python modules, services, configurations, etc.
COPY . /app

# Create non-root user for security
# UID 1000 matches standard development user on many systems
RUN useradd -m -u 1000 agent && \
    chown -R agent:agent /app

# Switch to non-root user
USER agent

# Default command (can be overridden in docker-compose.yml)
CMD ["python", "-m", "services.gateway.main"]
